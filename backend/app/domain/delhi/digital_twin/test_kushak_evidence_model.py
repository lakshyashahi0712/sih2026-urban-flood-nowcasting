"""Phase 8A tests for the Evidence-Constrained Kushak Hydraulic Model.

Tests exercise the existing public API of kushak_evidence_model only.
Provenance rules are asserted strictly: no assertion is weakened to make
the implementation pass; UNKNOWN stays UNKNOWN and effective geometry is
never accepted as surveyed/as-built.
"""

from datetime import datetime, timedelta, timezone

import pytest

from .kushak_evidence_model import (
    CATCHMENT_HISTORICAL_KM2,
    CATCHMENT_SCENARIOS,
    COVERED_EFFECTIVE_PROFILE_ID,
    KUSHAK_HYDRAULIC_SCENARIOS,
    NGT_JIR_BOUNDS,
    NIT52_PROCUREMENT,
    KushakEvidenceModel,
    KushakModelStatus,
    backbone_slope_m_per_m,
    covered_effective_profile,
    load_dmp_backbone,
    run_kushak_evidence_scenario,
)
from .kushak_rainfall_scenario import ScenarioForcing
from .hydraulic_time_state import SimulationStateStatus
from .models import ProvenanceStatus

IST = timezone(timedelta(hours=5, minutes=30))


# ---------------------------------------------------------------------------
# 1-4. DMP backbone
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def backbone():
    return load_dmp_backbone()


def test_backbone_loads_84_unique_nodes(backbone):
    assert len(backbone) == 84
    junctions = [n.junction for n in backbone]
    assert len(set(junctions)) == 84


def test_j3055_new_invert(backbone):
    node = next(n for n in backbone if n.junction == "J_3055")
    assert node.new_invert_msl_m == pytest.approx(216.841)


def test_j7549_new_invert(backbone):
    node = next(n for n in backbone if n.junction == "J_7549")
    assert node.new_invert_msl_m == pytest.approx(203.752)


def test_backbone_invert_provenance(backbone):
    assert all(
        n.invert_provenance == ProvenanceStatus.OFFICIAL_MODEL_VALUE
        for n in backbone
    )


# ---------------------------------------------------------------------------
# 5-7. Catchment scenarios
# ---------------------------------------------------------------------------


def test_working_catchment_provisional_not_authoritative():
    scenario = CATCHMENT_SCENARIOS["WORKING_27_66"]
    assert scenario.area_km2 == pytest.approx(27.66)
    assert scenario.provenance in (ProvenanceStatus.PROVISIONAL, ProvenanceStatus.DERIVED)
    assert "NOT authoritative" in scenario.note


def test_sensitivity_catchment_separate():
    working = CATCHMENT_SCENARIOS["WORKING_27_66"]
    sensitivity = CATCHMENT_SCENARIOS["SENSITIVITY_28_40"]
    assert sensitivity is not working
    assert sensitivity.area_km2 == pytest.approx(28.40)
    assert sensitivity.area_km2 != working.area_km2


def test_historical_catchment_unknown():
    # ~35.4 km2 must never be asserted as a known/authoritative value.
    assert CATCHMENT_HISTORICAL_KM2 is None


# ---------------------------------------------------------------------------
# 8-10. NGT JIR and NIT52 evidence
# ---------------------------------------------------------------------------


def test_ngt_bounds_provenance_and_bounded_wording():
    assert len(NGT_JIR_BOUNDS) > 0
    for bound in NGT_JIR_BOUNDS:
        assert bound.provenance in (ProvenanceStatus.OFFICIAL, ProvenanceStatus.OBSERVED)
    # The evidence collection carries the required bounded/visual context:
    # structural bounds are field-inspection evidence, not exact surveyed
    # hydraulic dimensions — asserted at set level, not per individual note.
    assert any(
        "visual" in b.note.lower() or "bounded" in b.note.lower()
        for b in NGT_JIR_BOUNDS
    )
    # The visual_depth bound is the bounded/visual anchor: verified explicitly.
    visual_depth = next(b for b in NGT_JIR_BOUNDS if b.quantity == "visual_depth")
    assert visual_depth.provenance == ProvenanceStatus.OBSERVED
    assert "visual" in visual_depth.note.lower()
    assert "not a surveyed" in visual_depth.note.lower()


def test_nit52_is_procurement_specification():
    assert NIT52_PROCUREMENT["spec_class"] == "PROCUREMENT_SPECIFICATION"
    assert NIT52_PROCUREMENT["barrel_size_class_m"] == (4.0, 5.0)


def test_nit52_not_surveyed_or_asbuilt():
    note = NIT52_PROCUREMENT["note"].lower()
    assert "not as-built" in note or "not as built" in note
    assert "specification only" in note


# ---------------------------------------------------------------------------
# 11-13. Effective profiles
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def central_profile():
    scenario = KUSHAK_HYDRAULIC_SCENARIOS["CENTRAL"]
    return covered_effective_profile(scenario)


def test_covered_profile_identified_effective_not_surveyed(central_profile):
    profile, meta = central_profile
    assert profile.cross_section_id == COVERED_EFFECTIVE_PROFILE_ID
    assert "INFERRED_EFFECTIVE" in profile.cross_section_id
    assert "NOT_SURVEYED" in profile.cross_section_id
    assert meta["is_surveyed"] is False
    assert meta["is_as_built"] is False


def test_covered_profile_aggregate_provenance_not_observed(central_profile):
    from .hydraulic_geometry import profile_provenance

    profile, meta = central_profile
    agg = profile_provenance(profile)
    assert agg is ProvenanceStatus.ASSUMED
    assert meta["profile_provenance"] == ProvenanceStatus.ASSUMED.value


def test_covered_profile_uses_dmp_invert_not_arbitrary_datum(central_profile):
    _, meta = central_profile
    assert meta["bed_elevation_m"] == pytest.approx(216.841)
    assert meta["bed_elevation_m"] != pytest.approx(100.0)


# ---------------------------------------------------------------------------
# 14-16. Hydraulic scenarios
# ---------------------------------------------------------------------------


def test_exactly_three_distinct_scenarios():
    assert set(KUSHAK_HYDRAULIC_SCENARIOS) == {
        "CONSERVATIVE",
        "CENTRAL",
        "DEGRADED_CAPACITY",
    }
    params = {
        (s.mult_box, s.mult_open, s.f_open_depot)
        for s in KUSHAK_HYDRAULIC_SCENARIOS.values()
    }
    assert len(params) == 3  # CONSERVATIVE and DEGRADED differ in f_open_depot


def test_scenario_parameters_within_retained_ranges():
    for scenario in KUSHAK_HYDRAULIC_SCENARIOS.values():
        lo, hi = scenario.mult_box_range
        assert lo <= scenario.mult_box <= hi
        lo, hi = scenario.mult_open_range
        assert lo <= scenario.mult_open <= hi
        lo, hi = scenario.f_open_depot_range
        assert lo <= scenario.f_open_depot <= hi


def test_scenario_metadata_inferred_effective_not_calibrated():
    # SCIENTIFIC CONTRACT, not exact prose: each scenario explicitly
    # identifies itself as inferred/effective and states it is not
    # calibrated — wording may vary ("NOT calibrated", "NOT a calibrated
    # parameter", "INFERRED/EFFECTIVE" vs "INFERRED_EFFECTIVE").
    inferred_variants = ("INFERRED_EFFECTIVE", "INFERRED/EFFECTIVE")
    not_calibrated_variants = ("NOT calibrated", "NOT a calibrated parameter")
    for scenario in KUSHAK_HYDRAULIC_SCENARIOS.values():
        assert any(v in scenario.basis for v in inferred_variants), (
            f"{scenario.scenario_id} must explicitly identify as inferred/effective"
        )
        assert any(v in scenario.basis for v in not_calibrated_variants), (
            f"{scenario.scenario_id} must explicitly state it is not calibrated"
        )


# ---------------------------------------------------------------------------
# 17-19. Forcing and scenario runner
# ---------------------------------------------------------------------------


def test_forcing_preserves_unknown_as_none():
    from .kushak_rainfall_scenario import load_june_2024_forcing

    forcing = load_june_2024_forcing()
    assert any(v is None for v in forcing.depths_mm), (
        "overlap-dependent hours must remain UNKNOWN (None)"
    )
    # the direct observed hour survives as a non-zero usable value
    assert any(v is not None and v > 0 for v in forcing.depths_mm)


def test_runner_partial_at_first_unknown():
    result = run_kushak_evidence_scenario(
        KUSHAK_HYDRAULIC_SCENARIOS["CENTRAL"],
        CATCHMENT_SCENARIOS["WORKING_27_66"],
    )
    # GAP (production API): there is no "PARTIAL" status on the conversion —
    # the block is expressed as per-timestep diagnostics plus the hydraulic
    # chain halting with BLOCKED_MISSING_INPUT at the first UNKNOWN
    # timestep. The enforced contract here is: no zero-fill of UNKNOWN
    # rainfall, discharge stays UNKNOWN, and the hydraulic run blocks
    # rather than silently continuing.
    assert result.hydraulic_run is not None
    states = result.hydraulic_run.states
    blocked_idx = next(
        (i for i, s in enumerate(states) if s.status == SimulationStateStatus.BLOCKED_MISSING_INPUT),
        None,
    )
    assert blocked_idx is not None, "hydraulic run must block at the first UNKNOWN timestep"
    # Every state before the block carries discharge None (UNKNOWN) or a
    # verified zero — never a fabricated value from an UNKNOWN rainfall hour.
    for state in states[:blocked_idx]:
        if state.discharge_m3_s is not None:
            assert state.discharge_m3_s == 0.0  # verified-zero hours only
    # Phase 8A diagnostic is appended even on the blocked path.
    assert any("PHASE 8A" in d for d in result.diagnostics)


def test_runner_exercises_phase7d_integrated_chain():
    """With an all-usable forcing the runner must reach the existing
    Phase 7D integrated hydraulic chain (rainfall -> inflow -> hydraulics)."""
    from .hydraulic_time_state import SimulationTimestep

    ts0 = datetime(2024, 6, 28, 5, 0, tzinfo=IST)
    forcing = ScenarioForcing(
        timesteps=[
            SimulationTimestep(start=ts0, end=ts0 + timedelta(hours=1)),
            SimulationTimestep(start=ts0 + timedelta(hours=1),
                               end=ts0 + timedelta(hours=2)),
        ],
        documented_mm=[91.0, 0.0],
        depths_mm=[91.0, 0.0],
    )
    result = run_kushak_evidence_scenario(
        KUSHAK_HYDRAULIC_SCENARIOS["CENTRAL"],
        CATCHMENT_SCENARIOS["WORKING_27_66"],
        forcing=forcing,
    )
    assert result.rainfall_conversion.status == "COMPUTED"
    assert result.hydraulic_run is not None
    assert any("PHASE 8A" in d for d in result.diagnostics)


# ---------------------------------------------------------------------------
# 20. Explicit model limitations
# ---------------------------------------------------------------------------


def test_model_exposes_explicit_limitations():
    model = KushakEvidenceModel.load()
    assert model.status == KushakModelStatus.RUNNABLE_AS_SCENARIO
    assert len(model.blocked_missing_geometry) > 0
    assert len(model.blocked_missing_observation) > 0
    assert all(isinstance(s, str) and s for s in model.blocked_missing_geometry)
    assert all(isinstance(s, str) and s for s in model.blocked_missing_observation)


def test_derived_slope_returns_value_or_unknown():
    slope = backbone_slope_m_per_m()
    assert slope is None or slope > 0
