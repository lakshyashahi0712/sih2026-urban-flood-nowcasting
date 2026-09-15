"""Phase 8B Step-5 tests: reach-resolved continuity/storage routing.

The four-reach chain (UG-01 -> OC-01 -> CD-01 -> OC-02) is time-evolved by
connecting Step-3 serial routing to the EXISTING Phase 7D continuity engine.
Asserted strictly: the Phase 7D continuity equation is reused (never
duplicated); Q_capacity != Q_actual_outflow != Q_transferred; None is never
treated as zero; lateral inflow is caller-supplied only; UG-01 physical
routing stays blocked; OC-02 assumes no Yamuna/free-outfall boundary;
negative storage blocks and is never clipped to zero; computed storage is
DERIVED.
"""

import inspect
import pytest
from datetime import datetime, timedelta, timezone

from . import kushak_continuity_routing as kcr
from .hydraulic_manning_adapter import ManningCapacityResult
from .hydraulic_time_state import SimulationStateStatus, SimulationTimestep
from .kushak_continuity_routing import (
    CHAIN_REACH_IDS,
    ChainStepSpec,
    ChainTimestepInput,
    ReachTimestepInput,
    advance_chain_series,
    advance_chain_timestep,
    advance_reach_timestep,
)
from .kushak_reaches_tiered import KUSHAK_MODEL_REACHES
from .kushak_serial_routing import OutflowRule, ReachOutflowDecision
from .kushak_tiered_model import ModelTier, load_current_tier_state
from .models import ProvenanceStatus


T0 = datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc)


def _step(dt_seconds=300, start_minutes=0):
    # Duration is in SECONDS (SI, matching the continuity math); start is an
    # integer-minute offset from T0 so multi-step tests can be contiguous.
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


# A full chain that runs CLEANLY: head=5, lateral=1, outflow=5 per reach ->
# each non-terminal reach gains +300 m3 (dt=300s * (5+1-5)). OC-02 (terminal,
# no explicit outflow) stays blocked. Storage starts at 100 -> 400.
def _chain_input(ts=None, storage=100.0, head=5.0, laterals=None,
                 decisions=None):
    ts = ts or _step()
    return ChainTimestepInput(
        timestep=ts,
        head_flow_m3_s=head,
        head_flow_provenance=ProvenanceStatus.OFFICIAL_MODEL_VALUE,
        storage_current={rid: storage for rid in CHAIN_REACH_IDS},
        storage_provenance={rid: ProvenanceStatus.OFFICIAL for rid in CHAIN_REACH_IDS},
        laterals=laterals or {rid: 1.0 for rid in CHAIN_REACH_IDS},
        lateral_provenances={rid: ProvenanceStatus.OFFICIAL for rid in CHAIN_REACH_IDS},
        decisions=decisions if decisions is not None else _chain_decisions(),
    )


def _run_chain(ts=None, **overrides):
    inp = _chain_input(ts=ts)
    base = {k: getattr(inp, k) for k in (
        "timestep", "head_flow_m3_s", "head_flow_provenance",
        "storage_current", "storage_provenance", "stage",
        "laterals", "lateral_provenances", "decisions",
        "capacity_results", "tolerance",
    )}
    base.update(overrides)
    return advance_chain_timestep(ChainTimestepInput(**base))


# ---------------------------------------------------------------------------
# 1. One reach continuity update with explicit outflow
# ---------------------------------------------------------------------------


def test_one_reach_continuity_with_explicit_outflow():
    # V_next = 100 + 300*(2 + 1 - 2.5) = 100 + 150 = 250 (Phase 7D equation).
    for reach_id in ("OC-01", "CD-01"):
        r = advance_reach_timestep(ReachTimestepInput(
            reach_id=reach_id, timestep=_step(300), incoming_flow_m3_s=2.0,
            storage_current_m3=100.0, lateral_inflow_m3_s=1.0,
            outflow_decision=_explicit_decision(reach_id, 2.5),
        ))
        assert r.continuity.status == SimulationStateStatus.COMPUTED
        assert r.state.hydraulic_status == SimulationStateStatus.COMPUTED
        assert r.state.storage_m3 == pytest.approx(250.0)
        assert r.state.storage_m3 == pytest.approx(r.continuity.storage_next_m3)


def test_one_reach_continuity_reuses_phase7d_equation():
    # The continuity result IS the reused Phase 7D compute_continuity_update
    # (identical object semantics), never a re-implemented balance.
    from .hydraulic_continuity import (
        ContinuityUpdateInput, compute_continuity_update,
    )
    expected = compute_continuity_update(ContinuityUpdateInput(
        dt_seconds=300.0, storage_current_m3=100.0,
        inflow_m3_s=2.0, lateral_inflow_m3_s=1.0, outflow_m3_s=2.5, provenance={},
    ))
    r = advance_reach_timestep(ReachTimestepInput(
        reach_id="OC-01", timestep=_step(300), incoming_flow_m3_s=2.0,
        storage_current_m3=100.0, lateral_inflow_m3_s=1.0,
        outflow_decision=_explicit_decision("OC-01", 2.5),
    ))
    assert r.continuity.storage_next_m3 == expected.storage_next_m3
    assert r.continuity.mass_balance_m3 == expected.mass_balance_m3


# ---------------------------------------------------------------------------
# 2. Four-reach serial timestep
# ---------------------------------------------------------------------------


def test_four_reach_serial_timestep():
    res = _run_chain()
    assert res.reach_ids() == ("UG-01", "OC-01", "CD-01", "OC-02")
    assert len(res.results) == 4


# ---------------------------------------------------------------------------
# 3. Storage changes according to the existing continuity implementation
# ---------------------------------------------------------------------------


def test_storage_changes_via_existing_continuity():
    res = _run_chain()
    for r in res.results[:-1]:  # OC-02 terminal has no explicit outflow
        assert r.continuity.status == SimulationStateStatus.COMPUTED
        assert r.state.storage_m3 == pytest.approx(400.0)
        assert r.continuity.mass_balance_m3 == pytest.approx(300.0)  # dt*(5+1-5)


# ---------------------------------------------------------------------------
# 4. Explicit zero inflow/outflow works
# ---------------------------------------------------------------------------


def test_explicit_zero_flows_work():
    decisions = {
        rid: _explicit_decision(rid, 0.0, declared=(rid == "UG-01"))
        for rid in CHAIN_REACH_IDS
    }
    res = _run_chain(head_flow_m3_s=0.0,
                     laterals={rid: 0.0 for rid in CHAIN_REACH_IDS},
                     decisions=decisions)
    for r in res.results[:-1]:
        assert r.continuity.status == SimulationStateStatus.COMPUTED
        assert r.state.storage_m3 == pytest.approx(100.0)  # zero net change


# ---------------------------------------------------------------------------
# 5. Missing lateral inflow blocks; never assumed zero
# ---------------------------------------------------------------------------


def test_missing_lateral_inflow_blocks_not_assumed_zero():
    r = advance_reach_timestep(ReachTimestepInput(
        reach_id="OC-01", timestep=_step(300), incoming_flow_m3_s=2.0,
        storage_current_m3=100.0, lateral_inflow_m3_s=None,  # NOT assumed 0
        outflow_decision=_explicit_decision("OC-01", 2.5),
    ))
    assert r.continuity.status == SimulationStateStatus.BLOCKED_MISSING_INPUT
    assert r.state.storage_m3 is None
    assert r.accounting.status == "BLOCKED_MISSING_INPUT"
    assert "lateral" in r.continuity.diagnostic


# ---------------------------------------------------------------------------
# 6. Missing actual outflow blocks; capacity is not substituted
# ---------------------------------------------------------------------------


def test_missing_actual_outflow_blocks_capacity_not_substituted():
    cap = ManningCapacityResult(
        status="COMPUTED", capacity_m3_s=42.0,
        geometry_provenance=ProvenanceStatus.ASSUMED,
        n_provenance=ProvenanceStatus.ASSUMED,
        slope_provenance=ProvenanceStatus.DERIVED,
    )
    # No outflow decision: capacity 42.0 is present but never substituted.
    r = advance_reach_timestep(ReachTimestepInput(
        reach_id="OC-01", timestep=_step(300), incoming_flow_m3_s=3.0,
        storage_current_m3=100.0, lateral_inflow_m3_s=0.0,
        outflow_decision=None, capacity_result=cap,
    ))
    assert r.transfer.actual_outflow_m3_s is None           # capacity not used
    assert r.transfer.capacity_m3_s == pytest.approx(42.0)  # reported, contextual
    assert r.continuity.status == SimulationStateStatus.BLOCKED_MISSING_INPUT
    assert r.state.storage_m3 is None


# ---------------------------------------------------------------------------
# 7. Explicit capacity-as-outflow opt-in works only via the canonical adapter
# ---------------------------------------------------------------------------


def test_capacity_opt_in_runs_through_canonical_adapter():
    cap = ManningCapacityResult(
        status="COMPUTED", capacity_m3_s=42.0,
        geometry_provenance=ProvenanceStatus.ASSUMED,
        n_provenance=ProvenanceStatus.ASSUMED,
        slope_provenance=ProvenanceStatus.DERIVED,
    )
    decision = ReachOutflowDecision(reach_id="OC-01", rule=OutflowRule.CAPACITY_OPT_IN)
    r = advance_reach_timestep(ReachTimestepInput(
        reach_id="OC-01", timestep=_step(300), incoming_flow_m3_s=3.0,
        storage_current_m3=100.0, lateral_inflow_m3_s=0.0,
        outflow_decision=decision, capacity_result=cap,
    ))
    assert r.transfer.hydraulic_status == "TRANSFERRED_CAPACITY_OPT_IN"
    assert r.state.actual_outflow_m3_s == pytest.approx(42.0)
    assert "capacity-as-outflow" in r.transfer.diagnostic
    assert "never observed" in r.transfer.diagnostic


# ---------------------------------------------------------------------------
# 8. Transfer from reach i becomes incoming for reach i+1
# ---------------------------------------------------------------------------


def test_transfer_becomes_next_incoming():
    res = _run_chain()
    for prev, nxt in zip(res.results, res.results[1:]):
        assert prev.transfer.downstream_reach_id == nxt.state.reach_id
        assert nxt.state.incoming_flow_m3_s == prev.transfer.transferred_m3_s


# ---------------------------------------------------------------------------
# 9. Missing intermediate transfer propagates UNKNOWN downstream
# ---------------------------------------------------------------------------


def test_missing_intermediate_transfer_propagates_unknown():
    decisions = {"UG-01": _explicit_decision("UG-01", 5.0, declared=True)}
    res = _run_chain(laterals={rid: 0.0 for rid in CHAIN_REACH_IDS},
                     decisions=decisions)
    ug, oc1, cd1, oc2 = res.results
    assert ug.transfer.transferred_m3_s == pytest.approx(5.0)
    assert oc1.transfer.transferred_m3_s is None            # no rule -> UNKNOWN
    assert cd1.state.incoming_flow_m3_s is None             # UNKNOWN downstream
    assert cd1.continuity.status == SimulationStateStatus.BLOCKED_MISSING_INPUT
    assert oc2.state.incoming_flow_m3_s is None


# ---------------------------------------------------------------------------
# 10. Negative resulting storage blocks
# ---------------------------------------------------------------------------


def test_negative_storage_blocks():
    for reach_id in ("OC-01", "CD-01"):
        r = advance_reach_timestep(ReachTimestepInput(
            reach_id=reach_id, timestep=_step(300), incoming_flow_m3_s=0.0,
            storage_current_m3=10.0, lateral_inflow_m3_s=0.0,
            outflow_decision=_explicit_decision(reach_id, 20.0),
        ))
        assert r.continuity.status == SimulationStateStatus.BLOCKED_INVALID_INPUT
        assert r.state.storage_m3 is None


# ---------------------------------------------------------------------------
# 11. No storage clipping to zero
# ---------------------------------------------------------------------------


def test_no_storage_clipping():
    r = advance_reach_timestep(ReachTimestepInput(
        reach_id="OC-01", timestep=_step(300), incoming_flow_m3_s=0.0,
        storage_current_m3=10.0, lateral_inflow_m3_s=0.0,
        outflow_decision=_explicit_decision("OC-01", 20.0),
    ))
    assert r.continuity.status == SimulationStateStatus.BLOCKED_INVALID_INPUT
    assert r.state.storage_m3 is None            # NEVER clipped to 0.0
    assert "not clipped to zero" in r.continuity.diagnostic


# ---------------------------------------------------------------------------
# 12. Provenance remains DERIVED for computed storage
# ---------------------------------------------------------------------------


def test_computed_storage_provenance_derived():
    res = _run_chain()
    for r in res.results[:-1]:
        assert r.state.provenance == ProvenanceStatus.DERIVED
        assert r.state.provenance != ProvenanceStatus.OBSERVED
        assert r.continuity.provenance == ProvenanceStatus.DERIVED
    assert res.results[3].state.provenance == ProvenanceStatus.UNKNOWN  # blocked


# ---------------------------------------------------------------------------
# 13. UG-01 physical/as-built routing remains blocked
# ---------------------------------------------------------------------------


def test_ug01_physical_routing_remains_blocked():
    r = advance_reach_timestep(ReachTimestepInput(
        reach_id="UG-01", timestep=_step(300), incoming_flow_m3_s=3.0,
        storage_current_m3=100.0, lateral_inflow_m3_s=0.0,
        outflow_decision=_explicit_decision("UG-01", 5.0),  # NOT declared
    ))
    assert r.transfer.hydraulic_status == "BLOCKED_UG01_PHYSICAL_GEOMETRY_UNKNOWN"
    assert r.state.actual_outflow_m3_s is None
    assert r.continuity.status == SimulationStateStatus.BLOCKED_MISSING_INPUT
    assert r.state.storage_m3 is None


# ---------------------------------------------------------------------------
# 14. Explicit Tier-B UG-01 abstraction runs only when declared
# ---------------------------------------------------------------------------


def test_ug01_tier_b_abstraction_runs_when_declared():
    # Net-zero flows: 100 + 300*(3 + 1 - 4) = 100 exactly; COMPUTED, never
    # clipped, and stays scenario-level DERIVED.
    r = advance_reach_timestep(ReachTimestepInput(
        reach_id="UG-01", timestep=_step(300), incoming_flow_m3_s=3.0,
        storage_current_m3=100.0, lateral_inflow_m3_s=1.0,
        outflow_decision=_explicit_decision("UG-01", 4.0, declared=True),
    ))
    assert r.transfer.hydraulic_status == "TRANSFERRED_EFFECTIVE_SCENARIO_ABSTRACTION"
    assert r.state.actual_outflow_m3_s == pytest.approx(4.0)
    assert r.continuity.status == SimulationStateStatus.COMPUTED
    assert r.state.storage_m3 == pytest.approx(100.0)  # 100 + 300*(3+1-4)
    assert r.state.provenance == ProvenanceStatus.DERIVED  # scenario-level, never observed


# ---------------------------------------------------------------------------
# 15. Tier-B execution cannot promote Tier A
# ---------------------------------------------------------------------------


def test_tier_b_execution_cannot_promote_tier_a():
    res = _run_chain()
    for r in res.results:
        if r.state.provenance != ProvenanceStatus.UNKNOWN:
            assert r.state.provenance == ProvenanceStatus.DERIVED
            assert r.state.provenance != ProvenanceStatus.OBSERVED
    gate, _ = load_current_tier_state()
    assert gate.tier == ModelTier.TIER_C_BLOCKED_INPUTS
    assert gate.can_promote_to_tier_a is False


# ---------------------------------------------------------------------------
# 16. OC-02 does not assume a Yamuna/free-outfall boundary
# ---------------------------------------------------------------------------


def test_oc02_no_yamuna_or_free_outfall():
    res = _run_chain()
    oc2 = res.results[3]
    assert oc2.state.reach_id == "OC-02"
    assert oc2.state.actual_outflow_m3_s is None            # no invented outflow
    assert oc2.transfer.hydraulic_status == "TERMINAL_REACH_NO_DOWNSTREAM"
    assert oc2.continuity.status == SimulationStateStatus.BLOCKED_MISSING_INPUT
    assert oc2.state.storage_m3 is None                     # no free-outfall update
    assert oc2.accounting.status == "BLOCKED_MISSING_INPUT"
    # It updates ONLY when an actual outflow is explicitly declared. NOTE:
    # through the LOCKED Step-3 transfer layer a terminal reach never emits
    # an actual outflow (its early-return branch preserves actual_outflow
    # None for every decision), so OC-02's continuity update REMAINS BLOCKED
    # here — the conservative contract. No Yamuna/free-outfall assumption
    # is ever manufactured to unblock it.
    decisions = _chain_decisions(5.0)
    decisions["OC-02"] = _explicit_decision("OC-02", 5.0)
    res2 = _run_chain(decisions=decisions)
    oc2b = res2.state_for("OC-02")
    assert oc2b.state.actual_outflow_m3_s is None
    assert oc2b.continuity.status == SimulationStateStatus.BLOCKED_MISSING_INPUT
    assert oc2b.state.storage_m3 is None


# ---------------------------------------------------------------------------
# 17. Multi-timestep ordering is deterministic
# ---------------------------------------------------------------------------


def test_multi_timestep_ordering_deterministic():
    specs = (
        ChainStepSpec(timestep=_step(300, 0), head_flow_m3_s=5.0,
                      laterals={rid: 1.0 for rid in CHAIN_REACH_IDS},
                      decisions=_chain_decisions(5.0)),
        ChainStepSpec(timestep=_step(300, 5), head_flow_m3_s=5.0,
                      laterals={rid: 1.0 for rid in CHAIN_REACH_IDS},
                      decisions=_chain_decisions(5.0)),
    )
    storage = {rid: 100.0 for rid in CHAIN_REACH_IDS}
    a = advance_chain_series(specs, initial_storage=storage)
    b = advance_chain_series(specs, initial_storage=storage)
    assert a == b                                            # deterministic
    assert len(a.steps) == 2
    assert all(st.reach_ids() == CHAIN_REACH_IDS for st in a.steps)
    # Storage threads across steps: OC-01 100 -> 400 (step1) -> 700 (step2).
    assert a.steps[0].state_for("OC-01").state.storage_m3 == pytest.approx(400.0)
    assert a.steps[1].state_for("OC-01").state.storage_m3 == pytest.approx(700.0)


def test_multi_timestep_rejects_non_contiguous_steps():
    gap = SimulationTimestep(start=T0 + timedelta(minutes=9),  # 4-min gap
                             end=T0 + timedelta(minutes=14))
    specs = (ChainStepSpec(timestep=_step(5, 0), head_flow_m3_s=3.0),
             ChainStepSpec(timestep=gap, head_flow_m3_s=4.0))
    with pytest.raises(ValueError, match="contiguous"):
        advance_chain_series(specs, initial_storage={})


# ---------------------------------------------------------------------------
# 18. Accounting is produced for each successfully evaluated reach
# ---------------------------------------------------------------------------


def test_accounting_produced_per_reach():
    # Fully explicit chain including a declared OC-02 outflow; balances to 0
    # per reach (incoming==outflow, lateral 0). Through the locked Step-3
    # transfer layer OC-02 (terminal) never emits an actual outflow, so its
    # record is BLOCKED_MISSING_INPUT — an auditable record is still produced.
    decisions = _chain_decisions(5.0)
    decisions["OC-02"] = _explicit_decision("OC-02", 5.0)
    res = _run_chain(laterals={rid: 0.0 for rid in CHAIN_REACH_IDS},
                     decisions=decisions)
    assert len(res.results) == 4
    for r in res.results[:-1]:
        assert r.accounting.reach_id == r.state.reach_id
        assert r.accounting.provenance == ProvenanceStatus.DERIVED
        assert r.accounting.status == "BALANCED"
        assert r.accounting.balance_residual_m3_s == pytest.approx(0.0)
    oc2 = res.results[3]
    assert oc2.accounting.reach_id == "OC-02"  # record produced, auditable
    assert oc2.accounting.status == "BLOCKED_MISSING_INPUT"  # terminal: no outflow


# ---------------------------------------------------------------------------
# 19. Capacity remains distinct from actual outflow and transferred flow
# ---------------------------------------------------------------------------


def test_capacity_distinct_from_outflow_and_transferred():
    cap = ManningCapacityResult(
        status="COMPUTED", capacity_m3_s=42.0,
        geometry_provenance=ProvenanceStatus.ASSUMED,
        n_provenance=ProvenanceStatus.ASSUMED,
        slope_provenance=ProvenanceStatus.DERIVED,
    )
    r = advance_reach_timestep(ReachTimestepInput(
        reach_id="OC-01", timestep=_step(300), incoming_flow_m3_s=3.0,
        storage_current_m3=100.0, lateral_inflow_m3_s=0.0,
        outflow_decision=_explicit_decision("OC-01", 7.5), capacity_result=cap,
    ))
    assert r.transfer.capacity_m3_s == pytest.approx(42.0)
    assert r.transfer.actual_outflow_m3_s == pytest.approx(7.5)
    assert r.transfer.transferred_m3_s == pytest.approx(7.5)
    assert r.transfer.capacity_m3_s != r.transfer.actual_outflow_m3_s
    assert r.transfer.capacity_m3_s != r.transfer.transferred_m3_s


# ---------------------------------------------------------------------------
# 20. No rainfall-derived lateral inflow is introduced
# ---------------------------------------------------------------------------


def test_lateral_inflow_passes_through_untouched_no_rainfall():
    laterals = {"UG-01": 2.5, "OC-01": 0.0, "CD-01": 1.5, "OC-02": 0.0}
    res = _run_chain(
        laterals=laterals,
        lateral_provenances={rid: ProvenanceStatus.OFFICIAL for rid in CHAIN_REACH_IDS},
    )
    for rid in CHAIN_REACH_IDS:
        # The exact caller-supplied value is carried into the state unchanged.
        assert res.state_for(rid).state.lateral_inflow_m3_s == laterals[rid]
    # The module imports no rainfall-runoff module and defines no estimator
    # (laterals are caller-supplied only).
    assert not any(n in kcr.__dict__ for n in
                   ("rainfall_to_inflow", "rainfall_runoff", "estimate_lateral"))
    assert "rainfall_to_inflow" not in inspect.getsource(kcr)