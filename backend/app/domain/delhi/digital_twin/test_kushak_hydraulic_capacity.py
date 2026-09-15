"""Phase 8B Step-7 tests: reach-level stage-discharge capacity contract.

The 20 focused tests required by the Step-7 specification, asserting
strictly: explicit effective profile + known stage produce a DERIVED
informational Q_capacity via the REUSED Phase 7D machinery; missing
stage/profile/dimensions leave capacity BLOCKED/UNKNOWN; explicit zero
stage is valid where the Phase 7D contract permits it; non-finite inputs
are rejected; Tier A is never promoted and generic OFFICIAL provenance
never satisfies the survey gate; Q_capacity never populates
Q_actual_outflow or Q_transferred_downstream (the Step-3 explicit
decision remains the only path); physical Kushak/NIT52 geometry stays
blocked; no observation, continuity equation, or downstream boundary is
created here.
"""

import math
from datetime import datetime, timezone

import pytest

from . import kushak_hydraulic_capacity as khc
from .hydraulic_geometry import CrossSectionProfile, StationPoint
from .hydraulic_manning_adapter import ManningCapacityResult
from .hydraulic_time_state import SimulationState
from .kushak_continuity_routing import ReachTimestepInput
from .kushak_evidence_model import KUSHAK_HYDRAULIC_SCENARIOS
from .kushak_reaches_tiered import build_reach_effective_profile
from .kushak_serial_routing import OutflowRule, ReachOutflowDecision
from .kushak_tiered_model import evaluate_tier_gate, load_current_tier_state
from .models import ProvenanceStatus


T0 = datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc)

N = 0.035
SLOPE = 0.001


def _profile(bed_elev=0.0):
    """Flat-bed rectangular profile; bed_elev -1.0 permits explicit zero stage."""
    return CrossSectionProfile([
        StationPoint(station_m=0.0, elevation_m=bed_elev),
        StationPoint(station_m=10.0, elevation_m=bed_elev),
    ], cross_section_id="effective-scenario")


def _state(stage_m):
    return SimulationState(
        timestamp=T0, location_id="OC-01", stage_m=stage_m
    )


def _capacity(stage_m=2.0, profile=None, n=N, slope=SLOPE):
    return khc.evaluate_reach_capacity(
        _state(stage_m),
        _profile() if profile is None else profile,
        n, slope,
    )


# 1. valid explicit effective profile + known stage -> COMPUTED capacity
def test_valid_profile_and_stage_compute_capacity():
    res = _capacity()
    assert res.status == "COMPUTED"
    assert res.capacity_m3_s is not None and res.capacity_m3_s > 0.0
    assert res.manning_result is not None


# 2. missing stage -> capacity UNKNOWN/BLOCKED
def test_missing_stage_blocked():
    res = _capacity(stage_m=None)
    assert res.status == "BLOCKED_MISSING_INPUT"
    assert res.capacity_m3_s is None


# 3. missing profile -> capacity UNKNOWN/BLOCKED
def test_missing_profile_blocked():
    res = khc.evaluate_reach_capacity(_state(2.0), None, N, SLOPE)
    assert res.status == "BLOCKED_MISSING_INPUT"
    assert res.capacity_m3_s is None


# 4. missing hydraulic dimensions (n / slope) -> BLOCKED/UNKNOWN
def test_missing_hydraulic_dimensions_blocked():
    res_n = _capacity(n=None)
    assert res_n.status == "BLOCKED_MISSING_INPUT"
    assert res_n.capacity_m3_s is None
    res_s = _capacity(slope=None)
    assert res_s.status == "BLOCKED_MISSING_INPUT"
    assert res_s.capacity_m3_s is None


# 5. explicit zero stage is valid where the Phase 7D contract permits it
#    (bed elevation below 0, so a zero water level is a wetted section)
def test_explicit_zero_stage_valid_when_permitted():
    res = _capacity(stage_m=0.0, profile=_profile(bed_elev=-1.0))
    assert res.status == "COMPUTED"
    assert res.capacity_m3_s is not None and res.capacity_m3_s > 0.0


def test_zero_stage_below_bed_blocked_not_silently_zero():
    # bed at 0.0: a zero water level is dry — the Phase 7D contract blocks
    # it rather than silently treating it as zero-area capacity
    res = _capacity(stage_m=-0.1, profile=_profile(bed_elev=0.0))
    assert res.status == "BLOCKED_INVALID_INPUT"
    assert res.capacity_m3_s is None


# 6. non-finite inputs rejected
def test_non_finite_inputs_rejected():
    for kwargs in ({"n": float("nan")}, {"n": float("inf")},
                   {"slope": float("nan")}, {"slope": float("inf")}):
        res = _capacity(**kwargs)
        assert res.status == "BLOCKED_INVALID_INPUT", kwargs
        assert res.capacity_m3_s is None


# 7. Tier-B scenario capacity provenance is DERIVED, never OBSERVED
def test_tier_b_capacity_provenance_derived():
    res = _capacity()
    assert res.provenance == ProvenanceStatus.DERIVED
    assert res.provenance != ProvenanceStatus.OBSERVED


# 8. effective scenario capacity does not promote Tier A
def test_effective_capacity_does_not_promote_tier_a():
    _capacity()  # a successful Tier-B calculation changes nothing upstream
    gate, _ = load_current_tier_state()
    assert gate.can_promote_to_tier_a is False


# 9. generic OFFICIAL provenance does not satisfy survey/as-built evidence
def test_generic_official_does_not_satisfy_survey_gate():
    gate = evaluate_tier_gate(
        provided_evidence={
            "UG01_internal_barrel_width": ProvenanceStatus.OFFICIAL,
            "CD01_hydraulic_clear_width": ProvenanceStatus.OFFICIAL_MODEL_VALUE,
        }
    )
    assert gate.tier.value == "TIER_C_BLOCKED_INPUTS"
    assert gate.can_promote_to_tier_a is False


# 10. Q_capacity does not populate Q_actual_outflow
def test_capacity_does_not_populate_actual_outflow():
    res = _capacity()
    cap = ManningCapacityResult(
        status="COMPUTED", capacity_m3_s=res.capacity_m3_s,
        n_provenance=ProvenanceStatus.ASSUMED,
        slope_provenance=ProvenanceStatus.ASSUMED,
    )
    from .hydraulic_continuity import compute_continuity_update  # noqa: F401
    from .kushak_continuity_routing import advance_reach_timestep
    from .hydraulic_time_state import SimulationTimestep
    from datetime import timedelta
    step = SimulationTimestep(start=T0, end=T0 + timedelta(seconds=300))
    out = advance_reach_timestep(ReachTimestepInput(
        reach_id="OC-01", timestep=step, incoming_flow_m3_s=1.0,
        lateral_inflow_m3_s=0.0, capacity_result=cap,
    ))
    # capacity supplied, but NO outflow decision -> no actual outflow
    assert out.state.actual_outflow_m3_s is None
    assert out.state.storage_m3 is None  # continuity stays blocked


# 11. Q_capacity does not populate Q_transferred_downstream
def test_capacity_does_not_populate_transferred():
    res = _capacity()
    cap = ManningCapacityResult(
        status="COMPUTED", capacity_m3_s=res.capacity_m3_s,
        n_provenance=ProvenanceStatus.ASSUMED,
        slope_provenance=ProvenanceStatus.ASSUMED,
    )
    from .hydraulic_time_state import SimulationTimestep
    from datetime import timedelta
    from .kushak_continuity_routing import advance_reach_timestep
    step = SimulationTimestep(start=T0, end=T0 + timedelta(seconds=300))
    out = advance_reach_timestep(ReachTimestepInput(
        reach_id="OC-01", timestep=step, incoming_flow_m3_s=1.0,
        lateral_inflow_m3_s=0.0, capacity_result=cap,
    ))
    assert out.transfer.transferred_m3_s is None


# 12. explicit actual-outflow decision remains the only mechanism
def test_explicit_decision_establishes_actual_outflow():
    from .hydraulic_time_state import SimulationTimestep
    from datetime import timedelta
    from .kushak_continuity_routing import advance_reach_timestep
    step = SimulationTimestep(start=T0, end=T0 + timedelta(seconds=300))
    decision = ReachOutflowDecision(
        reach_id="OC-01", rule=OutflowRule.EXPLICIT_SUPPLIED,
        explicit_outflow_m3_s=0.5,
    )
    out = advance_reach_timestep(ReachTimestepInput(
        reach_id="OC-01", timestep=step, incoming_flow_m3_s=1.0,
        lateral_inflow_m3_s=0.0, outflow_decision=decision,
    ))
    assert out.state.actual_outflow_m3_s == 0.5


# 13. explicit transfer semantics unchanged: transferred == actual outflow
def test_explicit_transfer_semantics_unchanged():
    from .hydraulic_time_state import SimulationTimestep
    from datetime import timedelta
    from .kushak_continuity_routing import advance_reach_timestep
    step = SimulationTimestep(start=T0, end=T0 + timedelta(seconds=300))
    decision = ReachOutflowDecision(
        reach_id="OC-01", rule=OutflowRule.EXPLICIT_SUPPLIED,
        explicit_outflow_m3_s=0.5,
    )
    out = advance_reach_timestep(ReachTimestepInput(
        reach_id="OC-01", timestep=step, incoming_flow_m3_s=1.0,
        lateral_inflow_m3_s=0.0, outflow_decision=decision,
    ))
    assert out.transfer.transferred_m3_s == out.state.actual_outflow_m3_s


# 14. physical Kushak geometry remains blocked (UG-01 profile unbuildable)
def test_physical_kushak_geometry_blocked():
    scenario = KUSHAK_HYDRAULIC_SCENARIOS["CONSERVATIVE"]
    with pytest.raises(ValueError):
        build_reach_effective_profile("UG-01", scenario)


# 15. NIT52 procurement dimensions cannot create physical capacity
def test_nit52_procurement_not_physical():
    gate, _ = load_current_tier_state()
    assert gate.can_promote_to_tier_a is False
    scenario = KUSHAK_HYDRAULIC_SCENARIOS["CONSERVATIVE"]
    profile, meta = build_reach_effective_profile("CD-01", scenario)
    assert meta["is_surveyed"] is False
    assert meta["is_as_built"] is False
    assert meta["tier"] == "TIER_B_EFFECTIVE_SCENARIO"


# 16. no discharge observation is created by capacity calculation
def test_no_discharge_observation_created():
    state = _state(2.0)
    res = _capacity(state.stage_m)
    assert res.status == "COMPUTED"
    # the input state is not mutated and no observation/discharge is attached
    assert state.discharge_m3_s is None
    assert state.storage_m3 is None
    assert not hasattr(res, "observation")


# 17. deterministic reach-to-profile mapping
def test_deterministic_reach_to_profile_mapping():
    scenario = KUSHAK_HYDRAULIC_SCENARIOS["CONSERVATIVE"]
    p1, m1 = build_reach_effective_profile("OC-01", scenario)
    p2, m2 = build_reach_effective_profile("OC-01", scenario)
    assert [(s.station_m, s.elevation_m) for s in p1.points] == \
           [(s.station_m, s.elevation_m) for s in p2.points]
    assert m1 == m2


# 18. deterministic repeated calculation
def test_deterministic_repeated_calculation():
    a = _capacity()
    b = _capacity()
    assert a.status == b.status
    assert a.capacity_m3_s == b.capacity_m3_s
    assert a.provenance == b.provenance
    assert a.diagnostic == b.diagnostic


# 19. no continuity equation duplication in the Step-7 module
def test_no_continuity_equation_duplication():
    import inspect
    src = inspect.getsource(khc)
    assert "storage_next" not in src
    assert "dt *" not in src
    assert "V +" not in src
    # Manning equation itself is NOT retyped — it lives in the Phase 7D
    # adapter and Phase 7A primitive only
    assert "R **" not in src
    assert "(1 / n)" not in src


# 20. no downstream/Yamuna boundary is introduced
def test_no_downstream_boundary_introduced():
    import inspect
    src = inspect.getsource(khc)
    assert "YAMUNA" not in src.upper()
    assert "DownstreamBoundary" not in src
    assert "boundary" not in src.lower()
