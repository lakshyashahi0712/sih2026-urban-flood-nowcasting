"""Reach-level mass-balance / flow-accounting contract (Phase 8B, Step 4 —
ACCOUNTING diagnostic only, NOT a hydraulic routing engine).

The accounting layer OBSERVES quantities already supplied by the caller
(Step-3 ReachTransfer records + explicitly supplied lateral inflow) and
determines whether they are BALANCED, IMBALANCED, blocked, or invalid.
It never creates, infers, or modifies flow, and never manufactures
missing flow from capacity or continuity.

Two distinct diagnostics, never conflated:

- mass-balance residual     = incoming_flow + lateral_inflow - actual_outflow
                              (transferred_downstream is NOT used in place
                              of actual_outflow)
- transfer-consistency      = transferred_downstream - actual_outflow
  residual                    (checked separately; a transfer inconsistency
                              is never hidden inside the balance residual)

Q_capacity is contextual information only: never actual outflow, never
transferred flow, never a filler for missing outflow, never a measured
discharge. Tolerance is an explicit caller-supplied parameter — no
scientific tolerance is hard-coded for Kushak and none is claimed to be
physically justified. None means UNKNOWN/MISSING and is never silently
converted to zero; zero is a valid explicit quantity.

Supplied-quantity provenance is preserved, never weakened: explicit
supplied flow keeps its caller provenance, transferred flow keeps the
Step-3 DERIVED/UNKNOWN provenance on the ReachTransfer itself, lateral
inflow provenance is carried explicitly on the record, and the accounting
result (residuals/status/diagnostic) is DERIVED — never OBSERVED.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, Optional, Tuple

from .kushak_serial_routing import ReachTransfer
from .models import ProvenanceStatus


def _is_valid_flow(v) -> bool:
    """Existing signed-flow convention: finite, non-negative, non-bool
    numbers are valid; None means UNKNOWN/MISSING (checked separately)."""
    return (
        v is not None
        and not isinstance(v, bool)
        and isinstance(v, (int, float))
        and math.isfinite(v)
        and v >= 0
    )


@dataclass(frozen=True)
class ReachAccountingRecord:
    """One reach-level accounting record. All flow fields follow the
    existing signed-flow convention (None = UNKNOWN/MISSING, never
    silently zero-filled). `capacity_m3_s` is contextual only."""

    reach_id: str
    incoming_flow_m3_s: Optional[float]
    actual_outflow_m3_s: Optional[float]
    transferred_downstream_m3_s: Optional[float]
    lateral_inflow_m3_s: Optional[float]
    lateral_inflow_provenance: ProvenanceStatus
    capacity_m3_s: Optional[float]  # contextual only — never in the balance
    balance_residual_m3_s: Optional[float]
    transfer_residual_m3_s: Optional[float]
    status: str
    provenance: ProvenanceStatus
    diagnostic: str

    def __post_init__(self) -> None:
        for name, v in (
            ("balance_residual_m3_s", self.balance_residual_m3_s),
            ("transfer_residual_m3_s", self.transfer_residual_m3_s),
        ):
            if v is not None and (
                isinstance(v, bool) or not isinstance(v, (int, float))
                or not math.isfinite(v)
            ):
                raise ValueError(
                    f"{self.reach_id}: {name} must be None (UNKNOWN) or "
                    f"finite (got {v!r})"
                )


@dataclass(frozen=True)
class ChainAccountingSummary:
    """Aggregate chain diagnostics. Deliberately carries NO chain-wide
    mass balance: a chain mass balance is not computed when required
    quantities are missing, and blocked/UNKNOWN is never treated as zero."""

    n_reaches: int
    n_balanced: int
    n_imbalanced: int
    n_blocked: int  # BLOCKED_* statuses
    n_transfer_inconsistent: int
    fully_auditable: bool  # True only when EVERY reach is BALANCED


def audit_reach_accounting(
    transfer: ReachTransfer,
    tolerance: float,
    lateral_inflow_m3_s: Optional[float] = None,
    lateral_inflow_provenance: ProvenanceStatus = ProvenanceStatus.ASSUMED,
) -> ReachAccountingRecord:
    """Audit one reach's supplied quantities against the accounting
    equation. Tolerance is explicit caller-supplied (finite, non-negative;
    0 is valid; invalid tolerance raises). Invalid supplied quantities are
    recorded as BLOCKED_INVALID_INPUT; missing required quantities
    (incoming, actual_outflow, or an explicitly-unset lateral inflow) as
    BLOCKED_MISSING_INPUT — never inferred, never zero-filled.

    Status precedence (documented): TRANSFER_INCONSISTENT > IMBALANCED >
    BALANCED; both residuals remain separate fields so neither diagnostic
    hides the other. Blocked records carry UNKNOWN provenance (nothing was
    derived); computed records carry DERIVED (never OBSERVED).
    """
    reach_id = transfer.upstream_reach_id

    if isinstance(tolerance, bool) or not isinstance(tolerance, (int, float)) \
            or not math.isfinite(tolerance) or tolerance < 0:
        raise ValueError(
            f"{reach_id}: tolerance must be finite and non-negative "
            f"(got {tolerance!r}); no tolerance is hard-coded for Kushak"
        )

    incoming = transfer.incoming_flow_m3_s
    outflow = transfer.actual_outflow_m3_s
    transferred = transfer.transferred_m3_s
    # Q_capacity: contextual only. Retained on the record; NEVER used as
    # outflow, transferred flow, or a filler for missing quantities.
    capacity = transfer.capacity_m3_s

    for name, v in (
        ("incoming_flow", incoming),
        ("actual_outflow", outflow),
        ("transferred_downstream", transferred),
        ("lateral_inflow", lateral_inflow_m3_s),
    ):
        if v is not None and not _is_valid_flow(v):
            return ReachAccountingRecord(
                reach_id=reach_id,
                incoming_flow_m3_s=incoming,
                actual_outflow_m3_s=outflow,
                transferred_downstream_m3_s=transferred,
                lateral_inflow_m3_s=lateral_inflow_m3_s,
                lateral_inflow_provenance=lateral_inflow_provenance,
                capacity_m3_s=capacity,
                balance_residual_m3_s=None,
                transfer_residual_m3_s=None,
                status="BLOCKED_INVALID_INPUT",
                provenance=ProvenanceStatus.UNKNOWN,
                diagnostic=(
                    f"{reach_id}: invalid {name} {v!r} — accounting "
                    "blocked, nothing inferred or fabricated"
                ),
            )

    missing = [
        name for name, v in (
            ("incoming_flow", incoming),
            ("actual_outflow", outflow),
            ("lateral_inflow", lateral_inflow_m3_s),  # None != explicit 0
        ) if v is None
    ]
    if missing:
        return ReachAccountingRecord(
            reach_id=reach_id,
            incoming_flow_m3_s=incoming,
            actual_outflow_m3_s=outflow,
            transferred_downstream_m3_s=transferred,
            lateral_inflow_m3_s=lateral_inflow_m3_s,
            lateral_inflow_provenance=lateral_inflow_provenance,
            capacity_m3_s=capacity,
            balance_residual_m3_s=None,
            transfer_residual_m3_s=None,
            status="BLOCKED_MISSING_INPUT",
            provenance=ProvenanceStatus.UNKNOWN,
            diagnostic=(
                f"{reach_id}: missing {', '.join(missing)} — accounting "
                "blocked; UNKNOWN not treated as zero, capacity not used "
                "as outflow, no continuity inferred"
            ),
        )

    balance_residual = float(incoming) + float(lateral_inflow_m3_s) - float(outflow)
    transfer_residual = (
        float(transferred) - float(outflow) if transferred is not None else None
    )

    if transfer_residual is not None and abs(transfer_residual) > tolerance:
        status = "TRANSFER_INCONSISTENT"
        why = (
            f"transferred {transferred} != actual_outflow {outflow} beyond "
            f"tolerance {tolerance} — transfer inconsistency reported "
            "separately, not hidden in the balance residual"
        )
    elif abs(balance_residual) > tolerance:
        status = "IMBALANCED"
        why = (
            f"|incoming {incoming} + lateral {lateral_inflow_m3_s} - "
            f"outflow {outflow}| = {abs(balance_residual)} exceeds "
            f"tolerance {tolerance}"
        )
    else:
        status = "BALANCED"
        why = (
            f"incoming {incoming} + lateral {lateral_inflow_m3_s} - "
            f"outflow {outflow} balances within tolerance {tolerance}"
            + (
                f"; transferred {transferred} == actual_outflow"
                if transfer_residual is not None else
                "; transferred_downstream UNKNOWN — transfer consistency "
                "not audited"
            )
        )

    return ReachAccountingRecord(
        reach_id=reach_id,
        incoming_flow_m3_s=incoming,
        actual_outflow_m3_s=outflow,
        transferred_downstream_m3_s=transferred,
        lateral_inflow_m3_s=lateral_inflow_m3_s,
        lateral_inflow_provenance=lateral_inflow_provenance,
        capacity_m3_s=capacity,
        balance_residual_m3_s=balance_residual,
        transfer_residual_m3_s=transfer_residual,
        status=status,
        provenance=ProvenanceStatus.DERIVED,  # accounting result: never OBSERVED
        diagnostic=f"{reach_id}: {why}",
    )


def audit_chain_accounting(
    transfers: Tuple[ReachTransfer, ...],
    tolerance: float,
    lateral_inflows: Optional[Dict[str, float]] = None,
    lateral_provenances: Optional[Dict[str, ProvenanceStatus]] = None,
) -> Tuple[Tuple[ReachAccountingRecord, ...], ChainAccountingSummary]:
    """Deterministic four-reach chain accounting (locked Step-2 order
    preserved as supplied; one record per reach, each evaluated
    independently). Lateral inflows are ONLY explicitly supplied
    accounting quantities (never estimated; unsupplied stays blocked).
    No chain-wide mass balance is computed and missing quantities are
    never fabricated — the summary counts states only."""
    lateral_inflows = lateral_inflows or {}
    lateral_provenances = lateral_provenances or {}
    records = tuple(
        audit_reach_accounting(
            t,
            tolerance=tolerance,
            lateral_inflow_m3_s=lateral_inflows.get(t.upstream_reach_id),
            lateral_inflow_provenance=lateral_provenances.get(
                t.upstream_reach_id, ProvenanceStatus.ASSUMED
            ),
        )
        for t in transfers
    )
    summary = ChainAccountingSummary(
        n_reaches=len(records),
        n_balanced=sum(r.status == "BALANCED" for r in records),
        n_imbalanced=sum(r.status == "IMBALANCED" for r in records),
        n_blocked=sum(r.status.startswith("BLOCKED_") for r in records),
        n_transfer_inconsistent=(
            sum(r.status == "TRANSFER_INCONSISTENT" for r in records)
        ),
        fully_auditable=(
            len(records) > 0
            and all(r.status == "BALANCED" for r in records)
        ),
    )
    return records, summary
