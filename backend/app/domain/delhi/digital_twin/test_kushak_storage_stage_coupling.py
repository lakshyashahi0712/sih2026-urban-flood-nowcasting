"""Phase 8B Step-6 tests: reach storage-stage coupling contract.

The 20 focused tests required by the Step-6 specification, asserting
strictly: explicit relations produce stage; the Phase 7D interpolation is
REUSED (never duplicated); missing relations leave stage UNKNOWN; no
inference from discharge/capacity/invert; continuity-computed storage is
unchanged; explicit zero storage is valid; invalid inputs are rejected;
effective relations are scenario-level only; Tier A is never promoted;
real Kushak geometry stays blocked; the four-reach ordering is
deterministic; no continuity equation is duplicated.
"""

import inspect
import math
import pytest
from datetime import datetime, timedelta, timezone

from . import kushak_storage_stage_coupling as kssc
from .hydraulic_continuity import ContinuityUpdateInput, compute_continuity_update
from .hydraulic_geometry import CrossSectionProfile, StationPoint
from .hydraulic_stage_update import with_stage_from_storage
from .hydraulic_storage_stage import StorageStagePair, StorageStageRelation
from .hydraulic_state_geometry import evaluate_state_geometry
from .hydraulic_time_state import SimulationState, SimulationStateStatus, SimulationTimestep
from .kushak_continuity_routing import (
    CHAIN_REACH_IDS,
    ChainStepSpec,
    ChainTimestepInput,
    advance_chain_series,
    advance_chain_timestep,
)
from .kushak_reaches_tiered import KUSHAK_MODEL_REACHES
from .kushak_serial_routing import OutflowRule, ReachOutflowDecision
from .kushak_storage_stage_coupling import (
    REACH_STORAGE_STAGE_RELATIONS,
    apply_reach_storage_stage_coupling,
    couple_chain_timestep,
    reach_state_to_simulation,
)
from .kushak_tiered_model import (
    ModelTier,
    SurveyEvidenceClass,
    evaluate_tier_gate,
    load_current_tier_state,
)
from .models import ProvenanceStatus


T0 = datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc)


def _step(dt_seconds=300, start_minutes=0):
    start = T0 + timedelta(minutes=start_minutes)
    return SimulationTimestep(start=start, end=start + timedelta(seconds=dt_seconds))


def _explicit_decision(reach_id, outflow, declared=False):
    return ReachOutflowDecision(
        reach_id=reach_id,
        rule=OutflowRule.EXPLICIT_SUPPLIED,
        explicit_outflow_m3_s=outflow,
        effective_scenario_declared=declared,
    )


def _chain_decisions(outflow=5.0):
    return {
        r.reach_id: _explicit_decision(
            r.reach_id, outflow, declared=(r.reach_id == "UG-01"))
        for r in KUSHAK_MODEL_REACHES
    }


def _run_chain(storage=100.0):
    return advance_chain_timestep(ChainTimestepInput(
        timestep=_step(),
        head_flow_m3_s=5.0,
        storage_current={rid: storage for rid in CHAIN_REACH_IDS},
        laterals={rid: 1.0 for rid in CHAIN_REACH_IDS},
        decisions=_chain_decisions(),
    ))


# A synthetic caller-supplied relation used ONLY for testing (effective
# scenario, NOT surveyed, NOT as-built, NOT observed, NOT real Kushak).
def _effective_relation():
    return StorageStageRelation(
        pairs=[
            StorageStagePair(stage_m=0.0, storage_m3=0.0,
                             provenance=ProvenanceStatus.ASSUMED),
            StorageStagePair(stage_m=1.0, storage_m3=200.0,
                             provenance=ProvenanceStatus.ASSUMED),
            StorageStagePair(stage_m=2.0, storage_m3=400.0,
                             provenance=ProvenanceStatus.ASSUMED),
        ],
        provenance=ProvenanceStatus.ASSUMED,
    )


# 1. Explicit relation produces stage ---------------------------------------


def test_explicit_relation_produces_stage():
    chain = _run_chain(storage=100.0)
    coupled = couple_chain_timestep(
        chain, {"OC-01": _effective_relation()})
    r = coupled["OC-01"]
    assert r.next_state.status == SimulationStateStatus.COMPUTED
    assert r.next_state.storage_m3 == pytest.approx(400.0)
    assert r.next_state.stage_m == pytest.approx(2.0)  # top of the table


# 2. Phase 7D interpolation actually reused ---------------------------------


def test_phase7d_interpolation_actually_reused():
    # The coupling delegates to with_stage_from_storage, whose lookup is the
    # Phase 7D-13 relation's own storage_to_stage (piecewise-linear).
    src = inspect.getsource(kssc.apply_reach_storage_stage_coupling)
    assert "with_stage_from_storage" in src
    assert "_interp" not in src  # no interpolation duplicated here
    # Same inputs -> identical result to calling the Phase 7D helper directly.
    chain = _run_chain(storage=100.0)
    state = chain.state_for("OC-01").state
    direct = with_stage_from_storage(
        reach_state_to_simulation(state), state.storage_m3, _effective_relation())
    coupled = apply_reach_storage_stage_coupling(
        state, _effective_relation())
    assert coupled.next_state.stage_m == direct.next_state.stage_m
    assert coupled.next_state.status == direct.next_state.status
    assert coupled.lookup.status == direct.lookup.status
    # And the lookup IS the relation's own method output semantics.
    assert coupled.lookup.value == _effective_relation().storage_to_stage(
        state.storage_m3).value


# 3. Missing relation leaves stage UNKNOWN/None ------------------------------


def test_missing_relation_leaves_stage_unknown():
    chain = _run_chain(storage=100.0)
    coupled = couple_chain_timestep(chain)  # no relations at all
    for rid in CHAIN_REACH_IDS:
        r = coupled[rid]
        assert r.next_state.stage_m is None
        assert r.next_state.status == SimulationStateStatus.BLOCKED_MISSING_INPUT
    # And the module registry itself is empty (no Kushak curve exists).
    assert REACH_STORAGE_STAGE_RELATIONS == {}


# 4. No inference from discharge --------------------------------------------


def test_no_inference_from_discharge():
    chain = _run_chain(storage=100.0)
    coupled = couple_chain_timestep(chain)
    for rid in CHAIN_REACH_IDS:
        r = coupled[rid]
        state = chain.state_for(rid).state
        # Discharge (actual outflow) is known for some reaches, yet with no
        # relation the stage stays UNKNOWN — never inferred from discharge.
        assert state.actual_outflow_m3_s is not None or rid == "OC-02"
        assert r.next_state.stage_m is None


# 5. No inference from Manning capacity / invert -----------------------------


def test_no_inference_from_capacity_or_invert():
    # A reach whose routing carries a Manning capacity result still gets NO
    # stage without an explicit relation.
    chain = _run_chain(storage=100.0)
    coupled = couple_chain_timestep(chain)
    for rid in CHAIN_REACH_IDS:
        r = coupled[rid]
        assert r.next_state.stage_m is None
        assert "never inferred" in (r.next_state.diagnostic or "")


# 6. Continuity-computed storage unchanged ----------------------------------


def test_continuity_computed_storage_unchanged():
    chain = _run_chain(storage=100.0)
    coupled = couple_chain_timestep(chain, {
        rid: _effective_relation() for rid in CHAIN_REACH_IDS})
    for rid in CHAIN_REACH_IDS:
        r = coupled[rid]
        state = chain.state_for(rid).state
        assert r.next_state.storage_m3 == state.storage_m3


# 7. Explicit zero storage is valid -----------------------------------------


def test_explicit_zero_storage_is_valid():
    chain = _run_chain(storage=0.0)
    coupled = couple_chain_timestep(chain, {"OC-01": _effective_relation()})
    r = coupled["OC-01"]
    assert r.next_state.storage_m3 is not None  # 0 + inflow, valid zero
    assert r.next_state.stage_m is not None
    assert r.next_state.status == SimulationStateStatus.COMPUTED
    # And an exact zero lookup hits the table exactly (no blocking).
    direct = _effective_relation().storage_to_stage(0.0)
    assert direct.status == "COMPUTED"
    assert direct.value == 0.0


# 8. Negative / non-finite storage rejected ---------------------------------


def test_negative_storage_rejected():
    # The Step-5 continuity itself blocks negative storage (never clipped);
    # here a fabricated negative storage can never enter a SimulationState.
    with pytest.raises(Exception):
        SimulationState(
            timestamp=T0, location_id="OC-01",
            status=SimulationStateStatus.COMPUTED,
            storage_m3=-1.0, provenance=ProvenanceStatus.DERIVED,
        )


def test_nonfinite_storage_rejected():
    with pytest.raises(Exception):
        SimulationState(
            timestamp=T0, location_id="OC-01",
            status=SimulationStateStatus.COMPUTED,
            storage_m3=math.nan, provenance=ProvenanceStatus.DERIVED,
        )


# 9. Invalid relation rejected ----------------------------------------------


def test_invalid_relation_duplicate_stage_rejected():
    with pytest.raises(ValueError):
        StorageStageRelation(pairs=[
            StorageStagePair(stage_m=0.0, storage_m3=0.0),
            StorageStagePair(stage_m=0.0, storage_m3=50.0),  # duplicate stage
        ])


def test_invalid_relation_backwards_stage_rejected():
    with pytest.raises(ValueError):
        StorageStageRelation(pairs=[
            StorageStagePair(stage_m=1.0, storage_m3=0.0),
            StorageStagePair(stage_m=0.0, storage_m3=50.0),  # backwards
        ])


def test_invalid_relation_nonfinite_pair_rejected():
    with pytest.raises(ValueError):
        StorageStagePair(stage_m=math.nan, storage_m3=0.0)
    with pytest.raises(ValueError):
        StorageStagePair(stage_m=0.0, storage_m3=math.inf)


# 10. Effective Tier-B relation is scenario-level ----------------------------


def test_effective_relation_is_scenario_level_not_surveyed():
    rel = _effective_relation()
    assert rel.provenance == ProvenanceStatus.ASSUMED  # NOT surveyed/observed
    # An ASSUMED relation never masquerades as geometry evidence: the gate
    # maps generic provenance to NOT_SURVEY_GRADE.
    gate = evaluate_tier_gate(
        provided_evidence={"any": ProvenanceStatus.ASSUMED})
    assert gate.tier == ModelTier.TIER_C_BLOCKED_INPUTS
    assert gate.can_promote_to_tier_a is False


# 11. Effective relation does not promote Tier A -----------------------------


def test_effective_relation_does_not_promote_tier_a():
    # Even declaring the effective relation for EVERY reach cannot open the
    # Tier-A gate: only SurveyEvidenceClass evidence can.
    survey_attempt = {
        req.requirement_id: SurveyEvidenceClass.OFFICIAL_SURVEY_OBSERVED
        for req in ()  # no real survey evidence exists — nothing supplied
    }
    gate = evaluate_tier_gate(
        provided_evidence={rid: ProvenanceStatus.ASSUMED
                           for rid in CHAIN_REACH_IDS},
        provided_survey_evidence=survey_attempt,
    )
    assert gate.tier == ModelTier.TIER_C_BLOCKED_INPUTS
    assert gate.can_promote_to_tier_a is False


# 12. Generic OFFICIAL cannot promote Tier A --------------------------------


def test_generic_official_cannot_promote_tier_a():
    gate = evaluate_tier_gate(
        provided_evidence={req.requirement_id: ProvenanceStatus.OFFICIAL
                           for req in load_current_tier_state()[0].missing_inputs
                           } if False else
        {"UG01_internal_barrel_width": ProvenanceStatus.OFFICIAL,
         "CD01_hydraulic_clear_width": ProvenanceStatus.OFFICIAL},
    )
    assert gate.tier == ModelTier.TIER_C_BLOCKED_INPUTS
    assert gate.can_promote_to_tier_a is False
    # OFFICIAL even on every requirement id is still structurally
    # non-satisfying (the gate never consults generic provenance).
    from .kushak_tiered_model import TIER_A_REQUIREMENTS
    gate2 = evaluate_tier_gate(
        provided_evidence={req.requirement_id: ProvenanceStatus.OFFICIAL
                           for req in TIER_A_REQUIREMENTS})
    assert gate2.tier == ModelTier.TIER_C_BLOCKED_INPUTS
    assert gate2.can_promote_to_tier_a is False


# 13. Real Kushak physical model remains Tier C ------------------------------


def test_real_kushak_remains_tier_c():
    gate, registry = load_current_tier_state()
    assert gate.tier == ModelTier.TIER_C_BLOCKED_INPUTS
    assert gate.can_promote_to_tier_a is False
    assert len(registry.missing_inputs) == 15  # full UNKNOWN ledger
    assert all(m.value is None for m in registry.missing_inputs)


# 14. Geometry stays blocked without cross-section ---------------------------


def test_geometry_remains_blocked_without_cross_section():
    chain = _run_chain(storage=100.0)
    coupled = couple_chain_timestep(chain, {"OC-01": _effective_relation()})
    state = coupled["OC-01"].next_state
    assert state.stage_m is not None  # stage exists...
    empty = CrossSectionProfile(points=None)  # ...but real geometry UNKNOWN
    geom = evaluate_state_geometry(state, empty)
    assert geom.status == "BLOCKED_MISSING_GEOMETRY"
    assert geom.area is None and geom.perimeter is None


# 15. Geometry evaluated only when BOTH stage and profile exist --------------


def test_synthetic_relation_with_synthetic_profile_reaches_geometry_path():
    # A synthetic relation + a synthetic (clearly effective-scenario)
    # profile reaches the EXISTING geometry evaluation path — proving the
    # coupling plugs into it — without inventing any Kushak geometry.
    chain = _run_chain(storage=100.0)
    coupled = couple_chain_timestep(chain, {"OC-01": _effective_relation()})
    state = coupled["OC-01"].next_state
    synthetic_profile = CrossSectionProfile(points=[
        StationPoint(station_m=0.0, elevation_m=0.0,
                     provenance=ProvenanceStatus.ASSUMED),
        StationPoint(station_m=10.0, elevation_m=3.0,
                     provenance=ProvenanceStatus.ASSUMED),
    ])
    geom = evaluate_state_geometry(state, synthetic_profile)
    assert geom.status == "COMPUTED"
    assert geom.geometry_provenance == ProvenanceStatus.ASSUMED  # never upgraded


# 16. Computed stage provenance is DERIVED ----------------------------------


def test_computed_stage_provenance_derived():
    chain = _run_chain(storage=100.0)
    coupled = couple_chain_timestep(chain, {"OC-01": _effective_relation()})
    assert coupled["OC-01"].next_state.provenance == ProvenanceStatus.DERIVED
    # Never OBSERVED, even with an OFFICIAL-provenance relation.
    official_rel = StorageStageRelation(
        pairs=[StorageStagePair(stage_m=0.0, storage_m3=0.0, provenance=ProvenanceStatus.OFFICIAL),
               StorageStagePair(stage_m=4.0, storage_m3=400.0, provenance=ProvenanceStatus.OFFICIAL)],
        provenance=ProvenanceStatus.OFFICIAL)
    state = chain.state_for("OC-01").state
    r = apply_reach_storage_stage_coupling(state, official_rel)
    assert r.next_state.provenance == ProvenanceStatus.DERIVED
    assert r.next_state.provenance != ProvenanceStatus.OBSERVED


# 17. Missing-relation provenance is conservative ----------------------------


def test_missing_relation_provenance_conservative():
    chain = _run_chain(storage=100.0)
    coupled = couple_chain_timestep(chain)
    for rid in CHAIN_REACH_IDS:
        r = coupled[rid]
        assert r.next_state.provenance == ProvenanceStatus.UNKNOWN
        assert r.next_state.stage_m is None


# 18. Deterministic reach mapping -------------------------------------------


def test_deterministic_reach_mapping():
    chain = _run_chain(storage=100.0)
    rels = {rid: _effective_relation() for rid in CHAIN_REACH_IDS}
    a = couple_chain_timestep(chain, rels)
    b = couple_chain_timestep(chain, rels)
    assert list(a.keys()) == list(b.keys()) == list(CHAIN_REACH_IDS)
    for rid in CHAIN_REACH_IDS:
        assert a[rid].next_state.stage_m == b[rid].next_state.stage_m
        assert a[rid].next_state.status == b[rid].next_state.status


# 19. Four-reach chain ordering deterministic --------------------------------


def test_four_reach_ordering_deterministic():
    chain = _run_chain(storage=100.0)
    assert chain.reach_ids() == CHAIN_REACH_IDS
    assert CHAIN_REACH_IDS == ("UG-01", "OC-01", "CD-01", "OC-02")
    series = advance_chain_series((
        ChainStepSpec(timestep=_step(300, 0), head_flow_m3_s=5.0,
                      laterals={rid: 1.0 for rid in CHAIN_REACH_IDS},
                      decisions=_chain_decisions()),
        ChainStepSpec(timestep=_step(300, 5), head_flow_m3_s=5.0,
                      laterals={rid: 1.0 for rid in CHAIN_REACH_IDS},
                      decisions=_chain_decisions()),
    ), initial_storage={rid: 100.0 for rid in CHAIN_REACH_IDS})
    assert [s.reach_ids() for s in series.steps] == \
        [CHAIN_REACH_IDS, CHAIN_REACH_IDS]


# 20. No continuity equation duplicated -------------------------------------


def test_no_continuity_equation_duplicated():
    # The coupling module never re-implements the continuity balance; the
    # Step-5 module is the sole orchestrator of compute_continuity_update.
    src = inspect.getsource(kssc)
    assert "compute_continuity_update" not in src
    assert "storage_next" not in src
    # And the Phase 7D continuity result itself is untouched by coupling:
    chain = _run_chain(storage=100.0)
    continuity = chain.state_for("OC-01").continuity
    expected = compute_continuity_update(ContinuityUpdateInput(
        dt_seconds=300.0, storage_current_m3=100.0,
        inflow_m3_s=5.0, lateral_inflow_m3_s=1.0, outflow_m3_s=5.0,
        provenance={},
    ))
    assert continuity.storage_next_m3 == expected.storage_next_m3
    assert continuity.status == expected.status
