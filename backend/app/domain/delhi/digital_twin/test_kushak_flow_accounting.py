"""Phase 8B Step-4 tests: mass-balance / flow-accounting contract.

Accounting is an audit layer, not a hydraulic engine. Asserted strictly:
mass-balance and transfer-consistency residuals are distinct; None is
never treated as zero; Q_capacity is contextual only; UG-01 physical
routing stays blocked; accounting provenance is DERIVED, never OBSERVED.
"""

import pytest

from .kushak_flow_accounting import (
    audit_reach_accounting,
    audit_chain_accounting,
)
from .kushak_serial_routing import ReachTransfer
from .kushak_tiered_model import ModelTier, load_current_tier_state
from .models import ProvenanceStatus

TOL = 1e-6


def _audit(transfer, lateral=None, tolerance=TOL):
    return audit_reach_accounting(
        transfer,
        tolerance=tolerance,
        lateral_inflow_m3_s=lateral,
    )


def _mock(reach_id="OC-01", downstream="CD-01", incoming=5.0,
          outflow=5.0, transferred=5.0, capacity=10.0, status=None):
    return ReachTransfer(
        upstream_reach_id=reach_id,
        downstream_reach_id=downstream,
        incoming_flow_m3_s=incoming,
        capacity_m3_s=capacity,
        actual_outflow_m3_s=outflow,
        transferred_m3_s=transferred,
        hydraulic_status=status or "TRANSFERRED_EXPLICIT_SUPPLIED",
        provenance=ProvenanceStatus.DERIVED,
        diagnostic="mock",
    )


# ---------------------------------------------------------------------------
# 1-2. Balanced / imbalanced reach
# ---------------------------------------------------------------------------


def test_perfectly_balanced_reach():
    # incoming 5 + lateral 2 - outflow 7 = 0
    acc = _audit(_mock(incoming=5.0, outflow=7.0, transferred=7.0), lateral=2.0)
    assert acc.status == "BALANCED"
    assert acc.balance_residual_m3_s == pytest.approx(0.0)
    assert acc.transfer_residual_m3_s == pytest.approx(0.0)
    assert "balances within tolerance" in acc.diagnostic


def test_imbalanced_reach():
    # incoming 5 + lateral 0 - outflow 7 = -2
    acc = _audit(_mock(incoming=5.0, outflow=7.0, transferred=7.0), lateral=0.0)
    assert acc.status == "IMBALANCED"
    assert acc.balance_residual_m3_s == pytest.approx(-2.0)
    assert "exceeds tolerance" in acc.diagnostic


# ---------------------------------------------------------------------------
# 3-7. Missing vs zero flow (None is NEVER zero)
# ---------------------------------------------------------------------------


def test_missing_incoming_flow_blocks():
    acc = _audit(_mock(incoming=None, outflow=5.0), lateral=0.0)
    assert acc.status == "BLOCKED_MISSING_INPUT"
    assert acc.balance_residual_m3_s is None
    assert "missing incoming_flow" in acc.diagnostic


def test_missing_actual_outflow_blocks():
    acc = _audit(_mock(incoming=5.0, outflow=None), lateral=0.0)
    assert acc.status == "BLOCKED_MISSING_INPUT"
    assert acc.balance_residual_m3_s is None
    assert "missing actual_outflow" in acc.diagnostic


def test_missing_lateral_inflow_remains_blocked_unknown():
    # No lateral supplied: NOT assumed 0 — accounting stays blocked.
    acc = _audit(_mock(), lateral=None)
    assert acc.status == "BLOCKED_MISSING_INPUT"
    assert acc.balance_residual_m3_s is None
    assert "missing lateral_inflow" in acc.diagnostic


def test_explicit_zero_lateral_inflow_is_valid():
    acc = _audit(_mock(), lateral=0.0)
    assert acc.status == "BALANCED"
    assert acc.balance_residual_m3_s == pytest.approx(0.0)


def test_zero_flow_is_valid():
    acc = _audit(_mock(incoming=0.0, outflow=0.0, transferred=0.0), lateral=0.0)
    assert acc.status == "BALANCED"
    assert acc.balance_residual_m3_s == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# 8-9. Transfer consistency vs actual outflow
# ---------------------------------------------------------------------------


def test_transfer_equals_outflow_residual_zero():
    acc = _audit(_mock(incoming=5.0, outflow=5.0, transferred=5.0), lateral=0.0)
    assert acc.status == "BALANCED"
    assert acc.transfer_residual_m3_s == pytest.approx(0.0)
    assert "transferred 5.0 == actual_outflow" in acc.diagnostic


def test_transfer_not_equal_outflow_is_transfer_inconsistent():
    acc = _audit(_mock(incoming=5.0, outflow=5.0, transferred=7.0), lateral=0.0)
    assert acc.status == "TRANSFER_INCONSISTENT"
    assert acc.transfer_residual_m3_s == pytest.approx(2.0)
    assert "transfer inconsistency reported" in acc.diagnostic


# ---------------------------------------------------------------------------
# 10. Residuals are distinct diagnostics (never conflated)
# ---------------------------------------------------------------------------


def test_residuals_distinct_transfer_inconsistency_not_hidden():
    # Balance is fine (5+0-5=0) but transferred != outflow: the balance
    # residual stays 0 while the transfer inconsistency is reported
    # separately — it is never hidden inside the balance residual.
    acc = _audit(_mock(incoming=5.0, outflow=5.0, transferred=6.5), lateral=0.0)
    assert acc.balance_residual_m3_s == pytest.approx(0.0)
    assert acc.transfer_residual_m3_s == pytest.approx(1.5)
    assert acc.status == "TRANSFER_INCONSISTENT"


# ---------------------------------------------------------------------------
# 11-12. Explicit tolerance (no hard-coded scientific tolerance)
# ---------------------------------------------------------------------------


def test_tolerance_controls_balanced_vs_imbalanced():
    t = _mock(incoming=5.0, outflow=5.0, transferred=5.0)
    # residual |0.05|: balanced under a loose tolerance, imbalanced under
    # a tight one — the tolerance is entirely caller-supplied.
    loose = _audit(t, lateral=0.05, tolerance=0.1)
    tight = _audit(t, lateral=0.05, tolerance=0.01)
    assert loose.status == "BALANCED"
    assert tight.status == "IMBALANCED"
    assert "tolerance 0.1" in loose.diagnostic
    assert "tolerance 0.01" in tight.diagnostic


def test_zero_tolerance_is_valid():
    acc = _audit(_mock(incoming=5.0, outflow=5.0, transferred=5.0),
                 lateral=0.0, tolerance=0)
    assert acc.status == "BALANCED"
    imbal = _audit(_mock(incoming=5.0, outflow=5.0, transferred=5.0),
                   lateral=1e-9, tolerance=0)
    assert imbal.status == "IMBALANCED"


def test_invalid_tolerance_rejected_and_invalid_flows_blocked():
    t = _mock()
    for bad in (-1.0, -0.0 - 1e-9, float("nan"), float("inf"), True, "0.1"):
        with pytest.raises(ValueError):
            audit_reach_accounting(t, tolerance=bad, lateral_inflow_m3_s=0.0)
    # Invalid supplied FLOW values are recorded, not raised: accounting
    # blocks with nothing inferred or fabricated. ReachTransfer.__post_init__
    # already rejects such values at construction, so inject via
    # object.__setattr__ to exercise the accounting-side validator.
    for bad in (-1.0, float("nan"), float("inf"), True):
        t = _mock(incoming=None, outflow=5.0)
        object.__setattr__(t, "incoming_flow_m3_s", bad)
        acc = _audit(t, lateral=0.0)
        assert acc.status == "BLOCKED_INVALID_INPUT"
        assert acc.balance_residual_m3_s is None
        assert acc.provenance == ProvenanceStatus.UNKNOWN
        assert "invalid incoming_flow" in acc.diagnostic
    acc = _audit(_mock(incoming=5.0, outflow=5.0), lateral=-2.0)
    assert acc.status == "BLOCKED_INVALID_INPUT"
    assert "invalid lateral_inflow" in acc.diagnostic


# ---------------------------------------------------------------------------
# 14. Q_capacity is contextual only — never outflow, never a filler
# ---------------------------------------------------------------------------


def test_capacity_is_contextual_only():
    # Capacity 42.0 is carried on the record but never enters the balance,
    # never substitutes for a missing outflow, and never becomes flow.
    acc = _audit(_mock(incoming=None, outflow=None, transferred=None,
                       capacity=42.0), lateral=0.0)
    assert acc.status == "BLOCKED_MISSING_INPUT"
    assert acc.capacity_m3_s == pytest.approx(42.0)  # reported, contextual
    assert acc.balance_residual_m3_s is None         # never fabricated
    assert acc.actual_outflow_m3_s is None           # never capacity-filled
    assert acc.transferred_downstream_m3_s is None
    assert "capacity not used" in acc.diagnostic
    # And in a balanced audit, capacity never appears in the equation.
    bal = _audit(_mock(incoming=5.0, outflow=5.0, transferred=5.0,
                       capacity=42.0), lateral=0.0)
    assert bal.status == "BALANCED"
    assert bal.balance_residual_m3_s == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# 15. UG-01 physical-routing block remains blocked in accounting
# ---------------------------------------------------------------------------


def test_ug01_physical_block_remains_blocked():
    from .kushak_serial_routing import (
        OutflowRule, ReachOutflowDecision, route_reach_transfer,
    )

    decision = ReachOutflowDecision(
        reach_id="UG-01",
        rule=OutflowRule.EXPLICIT_SUPPLIED,
        explicit_outflow_m3_s=5.0,
        effective_scenario_declared=False,  # physical routing -> blocked
    )
    t = route_reach_transfer("UG-01", 3.0, decision)
    assert t.hydraulic_status == "BLOCKED_UG01_PHYSICAL_GEOMETRY_UNKNOWN"
    # Accounting observes the blocked transfer as-is: no continuity
    # inference, no zero conversion, no Tier-A promotion.
    acc = _audit(t, lateral=0.0)
    assert acc.status == "BLOCKED_MISSING_INPUT"
    assert acc.balance_residual_m3_s is None
    assert acc.provenance == ProvenanceStatus.UNKNOWN
    gate, _ = load_current_tier_state()
    assert gate.tier == ModelTier.TIER_C_BLOCKED_INPUTS


# ---------------------------------------------------------------------------
# 16. Tier-B effective transfer audited as DERIVED, never promoted
# ---------------------------------------------------------------------------


def test_tier_b_transfer_audited_derived_without_promotion():
    from .kushak_serial_routing import (
        OutflowRule, ReachOutflowDecision, route_reach_transfer,
    )

    decision = ReachOutflowDecision(
        reach_id="UG-01",
        rule=OutflowRule.EXPLICIT_SUPPLIED,
        explicit_outflow_m3_s=5.0,
        effective_scenario_declared=True,  # Tier-B abstraction declared
    )
    t = route_reach_transfer("UG-01", 3.0, decision)
    assert t.tier_b_abstraction is True
    acc = _audit(t, lateral=2.0)  # 3 + 2 - 5 = 0
    assert acc.status == "BALANCED"
    # The accounting result is DERIVED (scenario-level), never OBSERVED,
    # and the tier gate stays closed — no Tier-A promotion.
    assert acc.provenance == ProvenanceStatus.DERIVED
    assert acc.provenance != ProvenanceStatus.OBSERVED
    gate, _ = load_current_tier_state()
    assert gate.tier == ModelTier.TIER_C_BLOCKED_INPUTS
    assert gate.can_promote_to_tier_a is False


# ---------------------------------------------------------------------------
# 17-18. Chain accounting: deterministic order + counts
# ---------------------------------------------------------------------------


def _chain_transfers():
    from .kushak_serial_routing import (
        OutflowRule, ReachOutflowDecision, route_serial_chain,
    )
    from .kushak_reaches_tiered import KUSHAK_MODEL_REACHES

    decisions = {
        r.reach_id: ReachOutflowDecision(
            reach_id=r.reach_id,
            rule=OutflowRule.EXPLICIT_SUPPLIED,
            explicit_outflow_m3_s=5.0,
            effective_scenario_declared=(r.reach_id == "UG-01"),
        )
        for r in KUSHAK_MODEL_REACHES
    }
    return route_serial_chain(3.0, decisions)


def test_chain_deterministic_order_and_records():
    laterals = {"UG-01": 2.0, "OC-01": 0.0, "CD-01": 0.0, "OC-02": 0.0}
    recs1, sum1 = audit_chain_accounting(_chain_transfers(), TOL, laterals)
    recs2, sum2 = audit_chain_accounting(_chain_transfers(), TOL, laterals)
    assert recs1 == recs2
    assert sum1 == sum2
    # One record per reach, locked Step-2 order preserved.
    assert [r.reach_id for r in recs1] == ["UG-01", "OC-01", "CD-01", "OC-02"]
    # Terminal OC-02 has no actual_outflow -> accounting stays blocked.
    assert recs1[3].status == "BLOCKED_MISSING_INPUT"


def test_chain_counts():
    laterals = {"UG-01": 2.0, "OC-01": 0.0, "CD-01": 0.0, "OC-02": 0.0}
    recs, s = audit_chain_accounting(_chain_transfers(), TOL, laterals)
    assert s.n_reaches == 4
    assert s.n_balanced == 3
    assert s.n_blocked == 1  # OC-02 terminal: actual_outflow UNKNOWN
    assert s.n_imbalanced == 0
    assert s.n_transfer_inconsistent == 0
    assert s.fully_auditable is False  # one reach is blocked


# ---------------------------------------------------------------------------
# 19. No fabricated chain-wide aggregate when quantities are missing
# ---------------------------------------------------------------------------


def test_no_fabricated_aggregate_when_missing():
    # No laterals supplied at all: every reach blocked, every residual
    # UNKNOWN — the summary counts states only, never computes a chain
    # mass balance from missing quantities.
    recs, s = audit_chain_accounting(_chain_transfers(), TOL)
    assert len(recs) == 4
    for r in recs:
        assert r.status == "BLOCKED_MISSING_INPUT"
        assert r.balance_residual_m3_s is None
        assert r.provenance == ProvenanceStatus.UNKNOWN
    assert s.n_blocked == 4
    assert s.n_balanced == 0
    assert s.fully_auditable is False


# ---------------------------------------------------------------------------
# 20. Accounting provenance is DERIVED, never OBSERVED
# ---------------------------------------------------------------------------


def test_accounting_provenance_derived_never_observed():
    laterals = {"UG-01": 2.0, "OC-01": 0.0, "CD-01": 0.0}
    recs, _ = audit_chain_accounting(_chain_transfers(), TOL, laterals)
    for r in recs:
        if r.status == "BALANCED":
            assert r.provenance == ProvenanceStatus.DERIVED
        assert r.provenance != ProvenanceStatus.OBSERVED
    # Blocked records carry UNKNOWN provenance (nothing was derived).
    assert recs[3].provenance == ProvenanceStatus.UNKNOWN
