"""Phase 8B Step-3 tests: reach-resolved serial routing contract.

The critical scientific contract is asserted strictly: Q_capacity,
Q_actual_outflow, and Q_transferred_downstream are distinct; capacity is
never silently substituted as outflow; UG-01 physical routing stays
blocked; UNKNOWN propagates — continuity is never fabricated.
"""

import pytest

from .kushak_reaches_tiered import KUSHAK_MODEL_REACHES
from .kushak_serial_routing import (
    OutflowRule,
    ReachOutflowDecision,
    ReachTransfer,
    route_reach_transfer,
    route_serial_chain,
)
from .kushak_tiered_model import ModelTier, load_current_tier_state
from .models import ProvenanceStatus


def _explicit_decisions(outflow: float = 5.0) -> dict:
    # UG-01 declares the explicit Tier-B abstraction: these tests exercise
    # transfer/propagation mechanics, not the UG-01 physical-routing guard
    # (covered separately in section 14).
    return {
        r.reach_id: ReachOutflowDecision(
            reach_id=r.reach_id,
            rule=OutflowRule.EXPLICIT_SUPPLIED,
            explicit_outflow_m3_s=outflow,
            effective_scenario_declared=(r.reach_id == "UG-01"),
        )
        for r in KUSHAK_MODEL_REACHES
    }


# ---------------------------------------------------------------------------
# 1. Four-reach serial ordering is deterministic
# ---------------------------------------------------------------------------


def test_serial_order_deterministic():
    a = route_serial_chain(3.0, _explicit_decisions())
    b = route_serial_chain(3.0, _explicit_decisions())
    assert a == b
    assert [t.upstream_reach_id for t in a] == [
        "UG-01", "OC-01", "CD-01", "OC-02"
    ]
    assert [t.downstream_reach_id for t in a[:3]] == [
        "OC-01", "CD-01", "OC-02"
    ]
    assert a[-1].downstream_reach_id is None  # terminal


# ---------------------------------------------------------------------------
# 2. Explicit actual outflow transfers correctly
# ---------------------------------------------------------------------------


def test_explicit_outflow_transfers():
    ts = route_serial_chain(3.0, _explicit_decisions(outflow=7.5))
    for t in ts:
        if t.tier_b_abstraction:
            assert t.hydraulic_status == "TRANSFERRED_EFFECTIVE_SCENARIO_ABSTRACTION"
        elif t.downstream_reach_id is not None:
            assert t.hydraulic_status == "TRANSFERRED_EXPLICIT_SUPPLIED"
            assert t.actual_outflow_m3_s == pytest.approx(7.5)


def test_transfer_chain_propagates():
    # Each reach's transferred flow becomes the next reach's incoming flow.
    ts = route_serial_chain(2.0, _explicit_decisions(outflow=4.0))
    assert ts[0].incoming_flow_m3_s == pytest.approx(2.0)
    assert ts[1].incoming_flow_m3_s == pytest.approx(4.0)
    assert ts[2].incoming_flow_m3_s == pytest.approx(4.0)


# ---------------------------------------------------------------------------
# 3. Missing actual outflow blocks rather than silently using capacity
# ---------------------------------------------------------------------------


def test_missing_outflow_blocks_and_does_not_use_capacity():
    class FakeCapacity:
        status = "COMPUTED"
        capacity_m3_s = 42.0
        geometry_provenance = ProvenanceStatus.ASSUMED
        n_provenance = ProvenanceStatus.ASSUMED
        slope_provenance = ProvenanceStatus.DERIVED
        diagnostic = "fake"

    t = route_reach_transfer("OC-01", incoming_flow_m3_s=3.0,
                             decision=None, capacity_result=FakeCapacity())
    assert t.actual_outflow_m3_s is None
    assert t.transferred_m3_s is None
    assert t.capacity_m3_s == pytest.approx(42.0)  # capacity reported, not used
    assert t.hydraulic_status == "BLOCKED_NO_OUTFLOW_RULE"
    assert "NOT substituted" in t.diagnostic
    assert t.provenance == ProvenanceStatus.UNKNOWN


# ---------------------------------------------------------------------------
# 4. Q_capacity is not automatically Q_actual_outflow
# ---------------------------------------------------------------------------


def test_capacity_not_automatically_outflow():
    class FakeCapacity:
        status = "COMPUTED"
        capacity_m3_s = 42.0
        geometry_provenance = ProvenanceStatus.ASSUMED
        n_provenance = ProvenanceStatus.ASSUMED
        slope_provenance = ProvenanceStatus.DERIVED
        diagnostic = "fake"

    t = route_reach_transfer("OC-01", 3.0, None, FakeCapacity())
    # The three quantities remain distinct.
    assert t.capacity_m3_s == pytest.approx(42.0)
    assert t.actual_outflow_m3_s is None
    assert t.transferred_m3_s is None
    assert t.capacity_m3_s != t.actual_outflow_m3_s
    assert t.transferred_m3_s != t.capacity_m3_s


# ---------------------------------------------------------------------------
# 5. Explicit capacity-as-outflow opt-in works through the canonical adapter
# ---------------------------------------------------------------------------


def test_capacity_opt_in_uses_canonical_adapter():
    from .hydraulic_manning_adapter import ManningCapacityResult

    cap = ManningCapacityResult(
        status="COMPUTED",
        capacity_m3_s=42.0,
        geometry_provenance=ProvenanceStatus.ASSUMED,
        n_provenance=ProvenanceStatus.ASSUMED,
        slope_provenance=ProvenanceStatus.DERIVED,
    )
    decision = ReachOutflowDecision(
        reach_id="OC-01", rule=OutflowRule.CAPACITY_OPT_IN)
    t = route_reach_transfer("OC-01", 3.0, decision, cap)
    assert t.actual_outflow_m3_s == pytest.approx(42.0)
    assert t.transferred_m3_s == pytest.approx(42.0)
    assert t.hydraulic_status == "TRANSFERRED_CAPACITY_OPT_IN"
    assert "capacity-as-outflow" in t.diagnostic
    assert "never observed" in t.diagnostic


def test_capacity_opt_in_with_blocked_capacity_stays_unknown():
    from .hydraulic_manning_adapter import ManningCapacityResult

    cap = ManningCapacityResult(
        status="BLOCKED_MISSING_INPUT",
        diagnostic="n UNKNOWN",
    )
    decision = ReachOutflowDecision(
        reach_id="OC-01", rule=OutflowRule.CAPACITY_OPT_IN)
    t = route_reach_transfer("OC-01", 3.0, decision, cap)
    assert t.actual_outflow_m3_s is None
    assert t.transferred_m3_s is None
    assert t.hydraulic_status == "BLOCKED_CAPACITY_NOT_COMPUTED"


# ---------------------------------------------------------------------------
# 6-8. Transferred distinct from capacity; no duplication, no splitting
# ---------------------------------------------------------------------------


def test_transferred_distinct_from_capacity_and_no_splitting():
    class FakeCapacity:
        status = "COMPUTED"
        capacity_m3_s = 42.0
        geometry_provenance = ProvenanceStatus.ASSUMED
        n_provenance = ProvenanceStatus.ASSUMED
        slope_provenance = ProvenanceStatus.DERIVED
        diagnostic = "fake"

    # One decision per reach: no duplicate transfer, no branch splitting —
    # serial chain only, exactly one transfer per reach pair.
    ts = route_serial_chain(3.0, _explicit_decisions(), capacity_results={
        "OC-01": FakeCapacity()})
    assert len(ts) == 4
    pairs = [(t.upstream_reach_id, t.downstream_reach_id) for t in ts]
    assert len(set(pairs)) == 4  # no duplicate transfer
    # UG-01's capacity (None here) never becomes outflow; OC-01's capacity
    # is reported but its explicit decision governs.
    assert ts[1].capacity_m3_s == pytest.approx(42.0)
    assert ts[1].actual_outflow_m3_s == pytest.approx(5.0)


# ---------------------------------------------------------------------------
# 9. UG-01 physical/as-built routing remains blocked
# ---------------------------------------------------------------------------


def test_ug01_physical_routing_remains_blocked():
    # UG-01 has no capacity result and no geometry — a capacity opt-in
    # cannot manufacture physical routing for it.
    from .hydraulic_manning_adapter import ManningCapacityResult

    cap = ManningCapacityResult(status="BLOCKED_MISSING_INPUT",
                                diagnostic="UG-01 geometry UNKNOWN")
    decision = ReachOutflowDecision(reach_id="UG-01",
                                    rule=OutflowRule.CAPACITY_OPT_IN)
    t = route_reach_transfer("UG-01", 3.0, decision, cap)
    assert t.actual_outflow_m3_s is None
    assert t.transferred_m3_s is None
    assert t.hydraulic_status == "BLOCKED_CAPACITY_NOT_COMPUTED"
    # And the current real evidence gate stays Tier C: no Tier-A physical
    # routing path exists.
    gate, _ = load_current_tier_state()
    assert gate.tier == ModelTier.TIER_C_BLOCKED_INPUTS


# ---------------------------------------------------------------------------
# 10. Effective Tier-B abstraction cannot promote Tier A
# ---------------------------------------------------------------------------


def test_tier_b_abstraction_cannot_promote_tier_a():
    # Routing transfers carry DERIVED provenance only — never survey/as-built
    # evidence; the tier gate stays closed.
    ts = route_serial_chain(3.0, _explicit_decisions())
    for t in ts:
        assert t.provenance in (ProvenanceStatus.DERIVED, ProvenanceStatus.UNKNOWN)
        assert t.provenance != ProvenanceStatus.OBSERVED
    gate, _ = load_current_tier_state()
    assert gate.tier == ModelTier.TIER_C_BLOCKED_INPUTS
    assert gate.can_promote_to_tier_a is False


# ---------------------------------------------------------------------------
# 11. Provenance preserved/derived correctly
# ---------------------------------------------------------------------------


def test_provenance_preserved():
    ts = route_serial_chain(3.0, _explicit_decisions())
    for t in ts[:3]:
        assert t.provenance == ProvenanceStatus.DERIVED  # transferred flow
    assert ts[0].incoming_flow_m3_s == pytest.approx(3.0)  # head flow preserved


def test_unknown_incoming_flow_propagates_as_unknown():
    ts = route_serial_chain(None, _explicit_decisions())
    assert ts[0].incoming_flow_m3_s is None
    # With no rule at all, the whole chain stays UNKNOWN — no fabricated
    # continuity.
    ts2 = route_serial_chain(None, {})
    for t in ts2:
        assert t.transferred_m3_s is None
        if t.downstream_reach_id is not None:
            # Non-terminal reaches with no rule: UNKNOWN, no fabricated
            # continuity.
            assert t.provenance == ProvenanceStatus.UNKNOWN
        else:
            # Terminal reach: a status diagnostic (nothing transferred
            # beyond the corridor), never a fabricated flow.
            assert t.hydraulic_status == "TERMINAL_REACH_NO_DOWNSTREAM"
            assert t.actual_outflow_m3_s is None


# ---------------------------------------------------------------------------
# 12. Invalid/negative/nonfinite flows rejected
# ---------------------------------------------------------------------------


def test_invalid_incoming_flow_rejected():
    for bad in (-1.0, float("nan"), float("inf"), True):
        with pytest.raises(ValueError):
            route_reach_transfer("OC-01", incoming_flow_m3_s=bad)


def test_invalid_decision_outflow_rejected():
    for bad in (-1.0, None, float("nan")):
        with pytest.raises(ValueError):
            ReachOutflowDecision(
                reach_id="OC-01",
                rule=OutflowRule.EXPLICIT_SUPPLIED,
                explicit_outflow_m3_s=bad,
            )


def test_outflow_value_without_rule_rejected():
    with pytest.raises(ValueError, match="explicit rule"):
        ReachOutflowDecision(reach_id="OC-01", rule=None,
                             explicit_outflow_m3_s=5.0)


def test_invalid_transfer_fields_rejected():
    with pytest.raises(ValueError):
        ReachTransfer(
            upstream_reach_id="OC-01", downstream_reach_id="CD-01",
            incoming_flow_m3_s=-5.0, capacity_m3_s=None,
            actual_outflow_m3_s=None, transferred_m3_s=None,
            hydraulic_status="X", provenance=ProvenanceStatus.UNKNOWN,
            diagnostic="x",
        )


# ---------------------------------------------------------------------------
# 13. Missing intermediate transfer blocks downstream reaches
# ---------------------------------------------------------------------------


def test_missing_intermediate_transfer_blocks_downstream():
    # OC-01 has no rule -> its transfer is None -> CD-01 and OC-02 receive
    # UNKNOWN incoming flow and, without their own rules, stay blocked.
    decisions = {
        "UG-01": ReachOutflowDecision(
            reach_id="UG-01", rule=OutflowRule.EXPLICIT_SUPPLIED,
            explicit_outflow_m3_s=5.0,
            effective_scenario_declared=True),
    }
    ts = route_serial_chain(3.0, decisions)
    assert ts[0].transferred_m3_s == pytest.approx(5.0)
    assert ts[1].transferred_m3_s is None  # OC-01 blocked
    assert ts[1].incoming_flow_m3_s == pytest.approx(5.0)
    assert ts[2].incoming_flow_m3_s is None  # CD-01 gets UNKNOWN
    assert ts[2].transferred_m3_s is None    # CD-01 blocked, no fabrication
    assert ts[2].hydraulic_status == "BLOCKED_NO_OUTFLOW_RULE"
    assert ts[3].incoming_flow_m3_s is None


# ---------------------------------------------------------------------------
# 14. UG-01 physical-routing guard (Step-3 surgical guard)
# ---------------------------------------------------------------------------


def test_ug01_physical_routing_blocked_even_with_explicit_outflow():
    # Physical UG-01 remains blocked even if an explicit outflow is supplied,
    # unless it is explicitly declared as an effective-scenario abstraction.
    decision = ReachOutflowDecision(
        reach_id="UG-01",
        rule=OutflowRule.EXPLICIT_SUPPLIED,
        explicit_outflow_m3_s=5.0,
        effective_scenario_declared=False,  # default
    )
    t = route_reach_transfer("UG-01", 3.0, decision)
    assert t.actual_outflow_m3_s is None
    assert t.transferred_m3_s is None
    assert t.hydraulic_status == "BLOCKED_UG01_PHYSICAL_GEOMETRY_UNKNOWN"
    assert "routing BLOCKED" in t.diagnostic
    assert t.tier_b_abstraction is False


def test_ug01_effective_abstraction_transfers_on_explicit_declaration():
    # UG-01 may only transfer if explicitly declared as a Tier-B abstraction.
    decision = ReachOutflowDecision(
        reach_id="UG-01",
        rule=OutflowRule.EXPLICIT_SUPPLIED,
        explicit_outflow_m3_s=5.0,
        effective_scenario_declared=True,
    )
    t = route_reach_transfer("UG-01", 3.0, decision)
    assert t.actual_outflow_m3_s == pytest.approx(5.0)
    assert t.transferred_m3_s == pytest.approx(5.0)
    assert t.hydraulic_status == "TRANSFERRED_EFFECTIVE_SCENARIO_ABSTRACTION"
    assert "effective-scenario abstraction" in t.diagnostic
    assert t.tier_b_abstraction is True
    # Provenance remains DERIVED, never OBSERVED.
    assert t.provenance == ProvenanceStatus.DERIVED


def test_other_reaches_transfer_without_explicit_abstraction_declaration():
    # OC-01/CD-01/OC-02 behavior remains unchanged: no declaration required.
    for reach_id in ("OC-01", "CD-01"):
        decision = ReachOutflowDecision(
            reach_id=reach_id,
            rule=OutflowRule.EXPLICIT_SUPPLIED,
            explicit_outflow_m3_s=7.5,
        )
        t = route_reach_transfer(reach_id, 4.0, decision)
        assert t.actual_outflow_m3_s == pytest.approx(7.5)
        assert t.transferred_m3_s == pytest.approx(7.5)
        assert t.tier_b_abstraction is False  # default


def test_ug01_capacity_opt_in_still_blocked_without_geometry():
    # Regression: CAPACITY_OPT_IN on UG-01 still blocks because geometry is UNKNOWN.
    from .hydraulic_manning_adapter import ManningCapacityResult
    cap = ManningCapacityResult(status="BLOCKED_MISSING_INPUT", diagnostic="...")
    decision = ReachOutflowDecision(
        reach_id="UG-01", rule=OutflowRule.CAPACITY_OPT_IN)
    t = route_reach_transfer("UG-01", 3.0, decision, cap)
    assert t.actual_outflow_m3_s is None
    assert t.hydraulic_status == "BLOCKED_CAPACITY_NOT_COMPUTED"
