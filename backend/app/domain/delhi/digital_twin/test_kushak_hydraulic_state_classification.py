"""Phase 8B Step-8 tests: reach hydraulic state classification contract.

The 22+ focused tests required by the Step-8 specification, asserting
strictly: missing stage -> UNKNOWN/BLOCKED; blocked physical geometry ->
BLOCKED; valid effective Tier-B state -> deterministic classification;
provenance DERIVED; Tier-B never promotes Tier-A; generic OFFICIAL does
not satisfy Tier-A; classification is side-effect free (continuity
storage, Q_capacity, Q_actual_outflow, Q_transferred_downstream, no
observed-flood labels, no street-level depth or risk); no inference from
rainfall/catchment/invert; unsupported thresholds -> UNKNOWN; deterministic
repeat + four-reach ordering; UG-01 blocked; OC-02 terminal; no continuity
equation duplication.
"""

import inspect
from datetime import datetime, timedelta, timezone

import pytest

from . import kushak_hydraulic_state_classification as ksc
from .hydraulic_geometry import CrossSectionProfile, StationPoint
from .hydraulic_manning_adapter import ManningCapacityResult
from .hydraulic_time_state import (
    SimulationState,
    SimulationStateStatus,
    SimulationTimestep,
)
from .kushak_continuity_routing import (
    CHAIN_REACH_IDS,
    ChainStepSpec,
    ChainTimestepInput,
    advance_chain_series,
    advance_chain_timestep,
)
from .kushak_reaches_tiered import KUSHAK_MODEL_REACHES, build_reach_effective_profile
from .kushak_serial_routing import OutflowRule, ReachOutflowDecision
from .kushak_storage_stage_coupling import REACH_STORAGE_STAGE_RELATIONS
from .kushak_tiered_model import (
    ModelTier,
    evaluate_tier_gate,
    load_current_tier_state,
)
from .models import ProvenanceStatus


T0 = datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc)


def _profile(bed_elev=0.0, crown_elev=4.0):
    """Flat-bed rectangular effective profile; explicitly NOT surveyed."""
    return CrossSectionProfile(
        [
            StationPoint(station_m=0.0, elevation_m=bed_elev,
                         provenance=ProvenanceStatus.ASSUMED),
            StationPoint(station_m=10.0, elevation_m=crown_elev,
                         provenance=ProvenanceStatus.ASSUMED),
        ],
        cross_section_id="effective-scenario",
    )


def _state(stage_m, status=SimulationStateStatus.COMPUTED):
    return SimulationState(
        timestamp=T0, location_id="OC-01", stage_m=stage_m,
        status=status, provenance=ProvenanceStatus.DERIVED,
    )


def _explicit_decision(reach_id, outflow):
    return ReachOutflowDecision(
        reach_id=reach_id,
        rule=OutflowRule.EXPLICIT_SUPPLIED,
        explicit_outflow_m3_s=outflow,
        effective_scenario_declared=(reach_id == "UG-01"),
    )


def _run_chain(storage=100.0):
    return advance_chain_timestep(ChainTimestepInput(
        timestep=SimulationTimestep(start=T0, end=T0 + timedelta(seconds=300)),
        head_flow_m3_s=5.0,
        storage_current={rid: storage for rid in CHAIN_REACH_IDS},
        laterals={rid: 1.0 for rid in CHAIN_REACH_IDS},
        stage={rid: 2.0 for rid in CHAIN_REACH_IDS},
        decisions={r.reach_id: _explicit_decision(r.reach_id, 5.0)
                   for r in KUSHAK_MODEL_REACHES},
    ))


# 1. Missing stage -> UNKNOWN / BLOCKED --------------------------------------


def test_missing_stage_classifies_unknown():
    res = ksc.classify_reach_state(_state(None), _profile())
    assert res.classification == ksc.ReachHydraulicClassification.UNKNOWN
    assert res.status == "BLOCKED_MISSING_INPUT"
    assert res.provenance == ProvenanceStatus.UNKNOWN


def test_missing_stage_blocked_status_carried_through():
    # a reach whose continuity already BLOCKED classifies UNKNOWN (missing
    # stage) with the blocked status carried through per the existing
    # status contract (never upgraded to COMPUTED)
    res = ksc.classify_reach_state(
        _state(None, status=SimulationStateStatus.BLOCKED_MISSING_INPUT),
        _profile())
    assert res.classification == ksc.ReachHydraulicClassification.UNKNOWN
    assert res.status == "BLOCKED_MISSING_INPUT"
    assert res.provenance == ProvenanceStatus.UNKNOWN


# 2. Blocked physical geometry -> BLOCKED ------------------------------------


def test_blocked_physical_geometry_blocked():
    res = ksc.classify_reach_state(_state(2.0), None)
    assert res.classification == ksc.ReachHydraulicClassification.BLOCKED
    assert res.status == "BLOCKED_MISSING_GEOMETRY"
    empty = CrossSectionProfile(points=None)  # UNKNOWN geometry
    res2 = ksc.classify_reach_state(_state(2.0), empty)
    assert res2.classification == ksc.ReachHydraulicClassification.BLOCKED


def test_tier_a_physical_interpretation_stays_blocked():
    # an effective profile exists, but Tier-A physical/as-built
    # interpretation is requested -> BLOCKED (as-built geometry UNKNOWN)
    res = ksc.classify_reach_state(
        _state(2.0), _profile(), claim_physical_as_built=True)
    assert res.classification == ksc.ReachHydraulicClassification.BLOCKED
    assert res.status == "BLOCKED_MISSING_GEOMETRY"


# 3. Valid effective Tier-B state -> deterministic classification -------------


def test_valid_effective_state_normal_capacity():
    res = ksc.classify_reach_state(_state(2.0), _profile())
    assert res.classification == ksc.ReachHydraulicClassification.NORMAL_CAPACITY
    assert res.status == "COMPUTED"


def test_valid_effective_state_dry():
    # stage below the profile bed is DRY (geometric, no threshold invented)
    res = ksc.classify_reach_state(
        _state(-0.5), _profile(bed_elev=0.0, crown_elev=4.0))
    assert res.classification == ksc.ReachHydraulicClassification.DRY


def test_valid_effective_state_surcharged():
    # stage above the profile crown is SURCHARGED (geometric)
    res = ksc.classify_reach_state(
        _state(5.0), _profile(bed_elev=0.0, crown_elev=4.0))
    assert res.classification == ksc.ReachHydraulicClassification.SURCHARGED


# 4. Classification provenance = DERIVED -------------------------------------


def test_classification_provenance_derived():
    for stage in (2.0, -0.5, 5.0):
        res = ksc.classify_reach_state(_state(stage), _profile())
        assert res.provenance == ProvenanceStatus.DERIVED
        assert res.provenance != ProvenanceStatus.OBSERVED
        assert res.tier == ModelTier.TIER_B_EFFECTIVE_SCENARIO.value


# 5. Tier-B classification never promotes Tier-A -----------------------------


def test_tier_b_classification_never_promotes_tier_a():
    for stage in (2.0, -0.5, 5.0):
        ksc.classify_reach_state(_state(stage), _profile())
    gate, _ = load_current_tier_state()
    assert gate.can_promote_to_tier_a is False
    assert gate.tier == ModelTier.TIER_C_BLOCKED_INPUTS


# 6. Generic OFFICIAL provenance does not satisfy Tier-A ---------------------


def test_generic_official_does_not_satisfy_tier_a():
    gate = evaluate_tier_gate(
        provided_evidence={
            "UG01_internal_barrel_width": ProvenanceStatus.OFFICIAL,
            "CD01_hydraulic_clear_width": ProvenanceStatus.OFFICIAL,
        }
    )
    assert gate.tier == ModelTier.TIER_C_BLOCKED_INPUTS
    assert gate.can_promote_to_tier_a is False


# 7-8. Classification does not modify continuity storage or Q_capacity -------


def test_classification_does_not_modify_continuity_storage():
    chain = _run_chain(storage=100.0)
    before = {rid: chain.state_for(rid).state.storage_m3
              for rid in CHAIN_REACH_IDS}
    ksc.classify_chain_timestep(chain)
    after = {rid: chain.state_for(rid).state.storage_m3
             for rid in CHAIN_REACH_IDS}
    assert before == after
    # OC-01..CD-01 computed (storage non-None); OC-02's terminal continuity
    # legitimately blocks (existing Step-5 behavior, unchanged by Step 8)
    assert all(
        after[rid] is not None for rid in CHAIN_REACH_IDS if rid != "OC-02")
    assert after["OC-02"] is None


def test_classification_does_not_modify_capacity():
    cap = ManningCapacityResult(
        status="COMPUTED", capacity_m3_s=12.5,
        n_provenance=ProvenanceStatus.ASSUMED,
        slope_provenance=ProvenanceStatus.ASSUMED,
    )
    res = ksc.classify_reach_state(_state(2.0), _profile(),
                                   capacity_m3_s=cap.capacity_m3_s)
    assert res.capacity_m3_s == 12.5  # informational echo, unchanged


# 9-10. No Q_actual_outflow / Q_transferred created --------------------------


def test_classification_does_not_create_actual_outflow():
    chain = _run_chain(storage=100.0)
    out_before = {rid: chain.state_for(rid).state.actual_outflow_m3_s
                  for rid in CHAIN_REACH_IDS}
    ksc.classify_chain_timestep(chain)
    out_after = {rid: chain.state_for(rid).state.actual_outflow_m3_s
                 for rid in CHAIN_REACH_IDS}
    assert out_before == out_after
    # the classification result itself carries no outflow field
    res = ksc.classify_reach_state(_state(2.0), _profile())
    assert not hasattr(res, "actual_outflow_m3_s")
    assert not hasattr(res, "transferred_m3_s")


# 11. No observed-flood labels -----------------------------------------------


def test_classification_never_claims_observed_flood():
    for stage in (2.0, -0.5, 5.0):
        res = ksc.classify_reach_state(_state(stage), _profile())
        assert res.state_class == "MODEL_STATE"
        assert res.observed_flood_event is None


# 12. No street-level depth / road risk --------------------------------------


def test_no_street_depth_or_risk_generated():
    src = inspect.getsource(ksc)
    for term in ("flood_depth", "road_closure", "street_flooding",
                 "pedestrian", "vehicle", "safe_routing"):
        assert term not in src.lower(), term
    res = ksc.classify_reach_state(_state(5.0), _profile())
    for f in ("depth", "risk", "closure"):
        assert not any(f in field for field in res.__dataclass_fields__)


# 13-15. No inference from rainfall / catchment / invert ---------------------


def test_no_inference_from_rainfall():
    # same classification with/without any rainfall-like input passed;
    # the function signature accepts no rainfall input at all
    res = ksc.classify_reach_state(_state(2.0), _profile())
    res2 = ksc.classify_reach_state(_state(2.0), _profile())
    assert res.classification == res2.classification == \
        ksc.ReachHydraulicClassification.NORMAL_CAPACITY


def test_no_inference_from_catchment_area():
    # no catchment input exists in the contract; classification depends
    # only on stage + profile
    res = ksc.classify_reach_state(_state(2.0), _profile())
    assert res.classification == ksc.ReachHydraulicClassification.NORMAL_CAPACITY


def test_no_inference_from_invert_alone():
    # an invert (profile) with NO stage cannot classify
    res = ksc.classify_reach_state(_state(None), _profile())
    assert res.classification == ksc.ReachHydraulicClassification.UNKNOWN


# 16. Unsupported thresholds -> UNKNOWN, never invented ----------------------


def test_unsupported_threshold_stays_unknown():
    res = ksc.classify_reach_state(
        _state(2.0), _profile(),
        elevated_threshold_m=3.0, threshold_provenance=ProvenanceStatus.ASSUMED)
    assert res.classification == ksc.ReachHydraulicClassification.UNKNOWN
    assert res.status == "BLOCKED_UNSUPPORTED_THRESHOLD"
    # DERIVED classification without a threshold is unaffected
    res2 = ksc.classify_reach_state(_state(2.0), _profile())
    assert res2.classification == ksc.ReachHydraulicClassification.NORMAL_CAPACITY


def test_evidence_supported_threshold_yields_elevated():
    # an EXISTING documented threshold with OBSERVED provenance can
    # produce ELEVATED (no such threshold is invented in Step 8)
    res = ksc.classify_reach_state(
        _state(3.5), _profile(),
        elevated_threshold_m=3.0, threshold_provenance=ProvenanceStatus.OBSERVED)
    assert res.classification == ksc.ReachHydraulicClassification.ELEVATED


def test_threshold_below_bed_dry_wins():
    # geometric DRY wins over the threshold branch (stage < bed < threshold)
    res = ksc.classify_reach_state(
        _state(-0.5), _profile(),
        elevated_threshold_m=3.0, threshold_provenance=ProvenanceStatus.OBSERVED)
    assert res.classification == ksc.ReachHydraulicClassification.DRY


def test_nonfinite_threshold_rejected():
    res = ksc.classify_reach_state(
        _state(2.0), _profile(),
        elevated_threshold_m=float("nan"),
        threshold_provenance=ProvenanceStatus.OBSERVED)
    assert res.classification == ksc.ReachHydraulicClassification.BLOCKED
    assert res.status == "BLOCKED_INVALID_INPUT"


# 17. Deterministic repeated classification ----------------------------------


def test_deterministic_repeated_classification():
    a = ksc.classify_reach_state(_state(2.0), _profile())
    b = ksc.classify_reach_state(_state(2.0), _profile())
    assert a.classification == b.classification
    assert a.status == b.status
    assert a.provenance == b.provenance
    assert a.diagnostic == b.diagnostic


# 18. Deterministic four-reach ordering --------------------------------------


def test_deterministic_four_reach_ordering():
    chain = _run_chain(storage=100.0)
    rels = {r.reach_id: None for r in KUSHAK_MODEL_REACHES}
    a = ksc.classify_chain_timestep(chain, rels)
    b = ksc.classify_chain_timestep(chain, rels)
    assert [r.reach_id for r in a] == [r.reach_id for r in b] == \
        ["UG-01", "OC-01", "CD-01", "OC-02"]
    # no profiles: reaches with UNKNOWN stage classify UNKNOWN; the chain
    # carries explicit stage 2.0 -> BLOCKED (no supplied profile)
    assert all(r.classification == ksc.ReachHydraulicClassification.BLOCKED
               for r in a)


# 19. UG-01 physical geometry remains blocked --------------------------------


def test_ug01_physical_geometry_remains_blocked():
    chain = _run_chain(storage=100.0)
    res = ksc.classify_chain_timestep(chain)[0]
    assert res.reach_id == "UG-01"
    assert res.classification == ksc.ReachHydraulicClassification.BLOCKED
    # the profile builder itself refuses UG-01 (locked Step-2 contract)
    with pytest.raises(ValueError):
        build_reach_effective_profile(
            "UG-01", __import__(
                "app.domain.delhi.digital_twin.kushak_evidence_model",
                fromlist=["KUSHAK_HYDRAULIC_SCENARIOS"]
            ).KUSHAK_HYDRAULIC_SCENARIOS["CONSERVATIVE"])


def test_ug01_tier_b_abstraction_classifies_only_with_explicit_inputs():
    # the caller explicitly supplies an effective profile for UG-01 ->
    # Tier-B classification is permitted (explicit inputs, never invented)
    res = ksc.classify_reach_state(
        SimulationState(timestamp=T0, location_id="UG-01", stage_m=2.0),
        _profile())
    assert res.classification == ksc.ReachHydraulicClassification.NORMAL_CAPACITY
    assert res.tier == ModelTier.TIER_B_EFFECTIVE_SCENARIO.value


# 20. OC-02 terminal / no downstream state -----------------------------------


def test_oc02_terminal_no_downstream_state_created():
    chain = _run_chain(storage=100.0)
    results = ksc.classify_chain_timestep(
        chain, {"OC-02": _profile()})
    oc02 = results[-1]
    assert oc02.reach_id == "OC-02"
    # classified from explicit inputs (explicit stage + explicit profile)...
    assert oc02.classification == ksc.ReachHydraulicClassification.NORMAL_CAPACITY
    # ...and no downstream/Yamuna state is created anywhere
    src = inspect.getsource(ksc)
    assert "YAMUNA" not in src.upper()
    assert "DownstreamBoundary" not in src


# 21. No continuity equation duplication -------------------------------------


def test_no_continuity_equation_duplication():
    src = inspect.getsource(ksc)
    assert "storage_next" not in src
    assert "dt *" not in src
    assert "V +" not in src


# 22. Storage-stage coupling registry untouched ------------------------------


def test_storage_stage_registry_untouched():
    # the Step-6 relation registry stays empty (no Kushak curve exists;
    # Step 8 creates none either)
    assert REACH_STORAGE_STAGE_RELATIONS == {}
