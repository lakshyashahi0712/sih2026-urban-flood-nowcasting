"""Reach-resolved serial routing contract (Phase 8B, Step 3 — transfer
contract only, NO continuity/timestep/storage routing).

The smallest reach-to-reach serial transfer layer on top of the existing
Phase 7D/8A contracts. The critical scientific contract, enforced here:

- Q_capacity            — calculated from hydraulic geometry + Manning
                          closure (existing Phase 7D adapter); modeled
                          conveyance only, NEVER automatically actual
                          outflow.
- Q_actual_outflow      — from an explicit caller-supplied boundary/
                          outflow decision, or from the existing Phase 7D
                          capacity-as-outflow mechanism ONLY when the
                          caller explicitly opts in.
- Q_transferred_downstream — the flow actually passed from one reach to
                          the next by this layer; explicitly represented
                          and provenance-tracked (DERIVED).

No new hydraulics: Manning equation, capacity adapter, capacity-as-outflow
adapter, simulation state, provenance contracts, and the locked Step-2
reach contract are reused, not duplicated or modified.
"""

from __future__ import annotations

import enum
import math
from dataclasses import dataclass
from typing import Dict, Optional, Tuple

from .hydraulic_manning_adapter import ManningCapacityResult
from .hydraulic_capacity_outflow import map_capacity_to_flows
from .hydraulic_time_stepper import TimeStepFlowInputs
from .hydraulic_continuity import combine_provenance_weakest
from .kushak_reaches_tiered import KUSHAK_MODEL_REACHES, KushakModelReach
from .kushak_tiered_model import ModelTier, evaluate_tier_gate
from .models import ProvenanceStatus


class OutflowRule(str, enum.Enum):
    """Explicit outflow rules for a reach. There are exactly two ways a
    reach gets an actual outflow — an explicit caller-supplied value, or
    the existing Phase 7D capacity-as-outflow mechanism via explicit
    opt-in. There is NO silent capacity substitution."""

    EXPLICIT_SUPPLIED = "EXPLICIT_SUPPLIED"
    CAPACITY_OPT_IN = "CAPACITY_OPT_IN"  # explicit caller opt-in only


@dataclass(frozen=True)
class ReachOutflowDecision:
    """One caller-supplied outflow decision for one reach.

    Exactly one rule must be active:
    - EXPLICIT_SUPPLIED: `explicit_outflow_m3_s` must be a finite,
      non-negative number (existing signed-flow convention).
    - CAPACITY_OPT_IN: the caller explicitly opts into using the existing
      Phase 7D capacity-as-outflow adapter; provenance records that
      capacity was used as the outflow rule.
    - No decision (both None): the reach has no actual outflow — the
      routing layer preserves UNKNOWN/BLOCKED and never substitutes
      Q_capacity.
    """

    reach_id: str
    rule: Optional[OutflowRule] = None
    explicit_outflow_m3_s: Optional[float] = None
    explicit_outflow_provenance: ProvenanceStatus = ProvenanceStatus.ASSUMED
    # Explicit Tier-B EFFECTIVE SCENARIO declaration. Required (and only
    # meaningful) for UG-01, whose physical/as-built routing is BLOCKED:
    # without it an explicit outflow is refused, never transferred as
    # physical routing. Never implied by the outflow value, capacity,
    # provenance, or reach id alone.
    effective_scenario_declared: bool = False

    def __post_init__(self) -> None:
        if self.effective_scenario_declared and self.reach_id != "UG-01":
            raise ValueError(
                f"{self.reach_id}: effective_scenario_declared is only "
                "meaningful for UG-01 (the only physically blocked reach)"
            )
        if self.rule is OutflowRule.EXPLICIT_SUPPLIED:
            v = self.explicit_outflow_m3_s
            if v is None or not isinstance(v, (int, float)) or isinstance(v, bool) \
                    or not math.isfinite(v) or v < 0:
                raise ValueError(
                    f"{self.reach_id}: EXPLICIT_SUPPLIED requires a finite, "
                    f"non-negative outflow (got {v!r})"
                )
        if self.rule is None and self.explicit_outflow_m3_s is not None:
            raise ValueError(
                f"{self.reach_id}: outflow value supplied without an "
                "explicit rule; set rule=EXPLICIT_SUPPLIED (or "
                "CAPACITY_OPT_IN) explicitly"
            )


@dataclass(frozen=True)
class ReachTransfer:
    """One reach-to-next-reach serial transfer. The three flow quantities
    are distinct by construction and never equated:

    - capacity_m3_s:          calculated Manning capacity if available
                              (may be None = UNKNOWN); modeled conveyance
                              only.
    - actual_outflow_m3_s:    the reach's actual outflow (explicitly
                              supplied or capacity-as-outflow via opt-in);
                              None = UNKNOWN/BLOCKED — Q_capacity is never
                              silently substituted.
    - transferred_m3_s:       the flow actually passed downstream; equals
                              actual_outflow only when the outflow is
                              known, else None (UNKNOWN propagates — no
                              fabricated continuity).
    """

    upstream_reach_id: str
    downstream_reach_id: str
    incoming_flow_m3_s: Optional[float]
    capacity_m3_s: Optional[float]
    actual_outflow_m3_s: Optional[float]
    transferred_m3_s: Optional[float]
    hydraulic_status: str
    provenance: ProvenanceStatus
    diagnostic: str
    # True ONLY when the transfer is an explicitly declared Tier-B
    # EFFECTIVE SCENARIO abstraction (currently possible only for UG-01);
    # never implied by outflow, capacity, provenance, or reach id.
    tier_b_abstraction: bool = False

    def __post_init__(self) -> None:
        for name, v in (
            ("incoming_flow_m3_s", self.incoming_flow_m3_s),
            ("capacity_m3_s", self.capacity_m3_s),
            ("actual_outflow_m3_s", self.actual_outflow_m3_s),
            ("transferred_m3_s", self.transferred_m3_s),
        ):
            if v is not None and (
                isinstance(v, bool) or not isinstance(v, (int, float))
                or not math.isfinite(v) or v < 0
            ):
                raise ValueError(
                    f"{self.upstream_reach_id}->{self.downstream_reach_id}: "
                    f"{name} must be None (UNKNOWN) or finite, non-negative "
                    f"(got {v!r})"
                )


def _adjacency(
    reaches: Tuple[KushakModelReach, ...] = KUSHAK_MODEL_REACHES,
) -> Dict[str, Optional[str]]:
    """Deterministic serial adjacency from the locked Step-2 order:
    UG-01 -> OC-01 -> CD-01 -> OC-02 (OC-02 has no downstream)."""
    return {
        r.reach_id: (reaches[i + 1].reach_id if i + 1 < len(reaches) else None)
        for i, r in enumerate(reaches)
    }


def route_reach_transfer(
    reach_id: str,
    incoming_flow_m3_s: Optional[float],
    decision: Optional[ReachOutflowDecision] = None,
    capacity_result: Optional[ManningCapacityResult] = None,
    reaches: Tuple[KushakModelReach, ...] = KUSHAK_MODEL_REACHES,
) -> ReachTransfer:
    """Route one reach's serial transfer to the declared adjacent
    downstream reach.

    - Transfer only between declared adjacent reaches (locked Step-2
      order); no splitting, no duplication, no parallel branches.
    - Explicit actual outflow: passed through as transferred downstream
      flow with its own provenance.
    - CAPACITY_OPT_IN: capacity becomes the actual outflow ONLY via the
      existing Phase 7D capacity-as-outflow mechanism
      (`map_capacity_to_flows`), and only when that adapter emits COMPUTED;
      provenance shows capacity was used as the outflow rule (never
      relabeled observed).
    - No explicit outflow and no opt-in: DO NOT silently use Q_capacity —
      the state stays UNKNOWN/BLOCKED and transferred flow is None.
    - UG-01 physical/as-built routing stays blocked: its conduit geometry
      is UNKNOWN; only a Tier-B effective-scenario abstraction may
      describe its behavior, never physical routing.
    """
    capacity_m3_s = (
        capacity_result.capacity_m3_s if capacity_result is not None else None
    )
    adjacency = _adjacency(reaches)
    if reach_id not in adjacency:
        raise ValueError(f"unknown reach_id: {reach_id}")
    downstream = adjacency[reach_id]
    if downstream is None:
        # Terminal reach (OC-02): no downstream transfer exists. Capacity
        # (if computed) is reported but nothing is transferred — no
        # fabricated continuation beyond the corridor.
        if decision is not None and decision.reach_id != reach_id:
            raise ValueError(
                f"decision for {decision.reach_id} cannot be applied to {reach_id}"
            )
        return ReachTransfer(
            upstream_reach_id=reach_id,
            downstream_reach_id=None,
            incoming_flow_m3_s=incoming_flow_m3_s,
            capacity_m3_s=capacity_m3_s,
            actual_outflow_m3_s=None,
            transferred_m3_s=None,
            hydraulic_status="TERMINAL_REACH_NO_DOWNSTREAM",
            provenance=ProvenanceStatus.DERIVED,
            diagnostic=(
                f"{reach_id}: terminal corridor reach — no declared "
                "downstream; nothing transferred beyond the corridor"
            ),
        )

    # Reject invalid incoming flow (finite, non-negative, or None).
    if incoming_flow_m3_s is not None and (
        isinstance(incoming_flow_m3_s, bool)
        or not isinstance(incoming_flow_m3_s, (int, float))
        or not math.isfinite(incoming_flow_m3_s)
        or incoming_flow_m3_s < 0
    ):
        raise ValueError(
            f"{reach_id}: incoming flow must be None (UNKNOWN) or finite, "
            f"non-negative (got {incoming_flow_m3_s!r})"
        )

    capacity_m3_s = (
        capacity_result.capacity_m3_s if capacity_result is not None else None
    )
    adjacency = _adjacency(reaches)
    actual_outflow: Optional[float] = None
    outflow_prov = ProvenanceStatus.UNKNOWN
    tier_b = False
    status = "BLOCKED_NO_OUTFLOW_RULE"
    diagnostic = (
        f"{reach_id}: no explicit outflow rule; Q_capacity "
        f"({capacity_m3_s if capacity_m3_s is not None else 'UNKNOWN'} m3/s) "
        "NOT substituted as outflow — state preserved UNKNOWN/BLOCKED"
    )

    if decision is not None:
        if decision.reach_id != reach_id:
            raise ValueError(
                f"decision for {decision.reach_id} cannot be applied to {reach_id}"
            )
        if decision.rule is OutflowRule.EXPLICIT_SUPPLIED:
            if reach_id == "UG-01" and not decision.effective_scenario_declared:
                # Physical/as-built UG-01 routing is BLOCKED: conduit
                # geometry is UNKNOWN. An explicit outflow value alone can
                # never manufacture physical routing — Tier-B effective
                # abstraction must be declared explicitly.
                status = "BLOCKED_UG01_PHYSICAL_GEOMETRY_UNKNOWN"
                diagnostic = (
                    f"{reach_id}: physical/as-built routing BLOCKED — "
                    "conduit geometry UNKNOWN; explicit outflow "
                    f"{decision.explicit_outflow_m3_s} m3/s NOT transferred "
                    "as physical routing. To use a Tier-B effective-scenario "
                    "abstraction, declare it explicitly "
                    "(effective_scenario_declared=True)"
                )
            elif decision.effective_scenario_declared:
                # Explicit Tier-B EFFECTIVE SCENARIO abstraction (UG-01
                # only): clearly marked as an effective/scenario
                # representation, never physical/as-built routing, and
                # never relabeled observed.
                actual_outflow = float(decision.explicit_outflow_m3_s)
                outflow_prov = decision.explicit_outflow_provenance
                status = "TRANSFERRED_EFFECTIVE_SCENARIO_ABSTRACTION"
                diagnostic = (
                    f"{reach_id}: EXPLICIT Tier-B effective-scenario "
                    f"abstraction (declared, NOT physical/as-built): "
                    f"effective outflow {actual_outflow} m3/s transferred "
                    f"downstream ({downstream}); provenance "
                    f"{outflow_prov.value} — effective scenario value, "
                    "never observed or physically measured"
                )
                tier_b = True
            else:
                actual_outflow = float(decision.explicit_outflow_m3_s)
                outflow_prov = decision.explicit_outflow_provenance
                status = "TRANSFERRED_EXPLICIT_SUPPLIED"
                diagnostic = (
                    f"{reach_id}: explicit caller-supplied outflow "
                    f"{actual_outflow} m3/s transferred downstream "
                    f"({downstream}); provenance {outflow_prov.value} "
                    "(explicit supplied decision, never observed)"
                )
        elif decision.rule is OutflowRule.CAPACITY_OPT_IN:
            # Explicit caller opt-in: the existing Phase 7D
            # capacity-as-outflow adapter decides — capacity becomes the
            # outflow ONLY if the adapter emits COMPUTED; blocked capacity
            # preserves UNKNOWN outflow. Provenance records the rule.
            flow_inputs = map_capacity_to_flows(capacity_result) \
                if capacity_result is not None else None
            if flow_inputs is not None and flow_inputs.outflow_m3_s is not None:
                actual_outflow = flow_inputs.outflow_m3_s
                outflow_prov = flow_inputs.outflow_provenance
                status = "TRANSFERRED_CAPACITY_OPT_IN"
                diagnostic = (
                    f"{reach_id}: caller opted into capacity-as-outflow "
                    f"(Phase 7D map_capacity_to_flows); capacity "
                    f"{actual_outflow} m3/s used as outflow — calculated/"
                    f"model rule, never observed or physically measured"
                )
            else:
                status = "BLOCKED_CAPACITY_NOT_COMPUTED"
                diagnostic = (
                    f"{reach_id}: capacity-as-outflow opted in but capacity "
                    "is not COMPUTED — outflow preserved UNKNOWN, no "
                    "substitution"
                )

    transferred = actual_outflow  # None propagates as UNKNOWN downstream
    return ReachTransfer(
        upstream_reach_id=reach_id,
        downstream_reach_id=downstream,
        incoming_flow_m3_s=incoming_flow_m3_s,
        capacity_m3_s=capacity_m3_s,
        actual_outflow_m3_s=actual_outflow,
        transferred_m3_s=transferred,
        hydraulic_status=status,
        provenance=(
            ProvenanceStatus.DERIVED if transferred is not None else ProvenanceStatus.UNKNOWN
        ),
        diagnostic=diagnostic,
        tier_b_abstraction=tier_b,
    )


def route_serial_chain(
    incoming_head_flow_m3_s: Optional[float],
    decisions: Dict[str, ReachOutflowDecision],
    capacity_results: Optional[Dict[str, ManningCapacityResult]] = None,
    reaches: Tuple[KushakModelReach, ...] = KUSHAK_MODEL_REACHES,
) -> Tuple[ReachTransfer, ...]:
    """Route the full serial chain UG-01 -> OC-01 -> CD-01 -> OC-02.

    The head flow enters UG-01; each reach's transferred flow becomes the
    next reach's incoming flow. A missing intermediate transfer (None =
    UNKNOWN/BLOCKED) propagates: downstream reaches receive UNKNOWN
    incoming flow and, without their own explicit rule, stay blocked —
    continuity is never fabricated. Deterministic: same inputs, same
    transfers, in locked Step-2 order.
    """
    capacity_results = capacity_results or {}
    transfers = []
    flow = incoming_head_flow_m3_s
    for reach in reaches:
        transfer = route_reach_transfer(
            reach_id=reach.reach_id,
            incoming_flow_m3_s=flow,
            decision=decisions.get(reach.reach_id),
            capacity_result=capacity_results.get(reach.reach_id),
            reaches=reaches,
        )
        transfers.append(transfer)
        flow = transfer.transferred_m3_s
    return tuple(transfers)
