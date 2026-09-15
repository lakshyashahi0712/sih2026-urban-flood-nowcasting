"""Reach-resolved continuity/storage routing (Phase 8B, Step 5).

Introduces TIME EVOLUTION for the four-reach effective-scenario chain
UG-01 -> OC-01 -> CD-01 -> OC-02 by connecting the Step-3 reach-resolved
serial transfer layer to the EXISTING Phase 7D continuity/time-step
machinery. This module is a thin ORCHESTRATOR only — it reuses, never
duplicates, the locked layers:

- Step-3 serial routing     `route_reach_transfer` decides the actual
                            outflow / transferred flow.
- Phase 7D continuity       `compute_continuity_update` computes the single
                            storage balance V_next = V + dt*(Qin+Qlat-Qout).
                            NO continuity equation is re-written here.
- Phase 7D timestep/state   `SimulationTimestep`, `SimulationStateStatus`.
- Step-4 accounting         `audit_reach_accounting` emits one independent,
                            auditable record per reach (the accounting and
                            continuity equations stay separate).

Scientific invariants preserved exactly:

- Q_capacity != Q_actual_outflow != Q_transferred: only EXPLICIT_SUPPLIED
  or an explicit CAPACITY_OPT_IN (via the canonical Phase 7D adapter)
  may supply actual outflow; capacity is never silently substituted.
- None stays UNKNOWN/BLOCKED; explicit 0.0 is a valid zero.
- Lateral inflow is caller-supplied ONLY — never estimated, never derived
  from rainfall, never zero-filled: None blocks.
- A negative resulting storage stays BLOCKED_INVALID_INPUT and is never
  clipped to zero.
- Computed storage is DERIVED provenance; weakest-link input provenance is
  preserved.
- A missing intermediate transfer propagates UNKNOWN downstream and the
  downstream reach's continuity blocks unless its required quantities are
  explicitly available.
- UG-01 physical/as-built routing stays BLOCKED (conduit geometry UNKNOWN);
  only an EXPLICIT Tier-B effective-scenario declaration may abstract it,
  and it never promotes Tier A.
- OC-02 (terminal) never assumes a Yamuna / free-outfall boundary: without
  an explicit actual outflow its continuity update remains blocked.

Non-goals (STRICT): no rainfall forcing, no rainfall-runoff, no 2D routing,
no overtopping, no road flooding, no downstream Yamuna boundary, no new
hydraulic equations, no inferred lateral inflow, no surveyed/underground
conduit geometry, no UI/API.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Optional, Tuple

from .hydraulic_continuity import (
    ContinuityUpdateInput,
    ContinuityUpdateResult,
    compute_continuity_update,
)
from .hydraulic_manning_adapter import ManningCapacityResult
from .hydraulic_time_state import SimulationStateStatus, SimulationTimestep
from .kushak_flow_accounting import (
    ReachAccountingRecord,
    audit_reach_accounting,
)
from .kushak_reaches_tiered import KUSHAK_MODEL_REACHES
from .kushak_serial_routing import (
    ReachOutflowDecision,
    ReachTransfer,
    route_reach_transfer,
)
from .models import ProvenanceStatus

# Locked Step-2 corridor order (upstream -> downstream). Deterministic.
CHAIN_REACH_IDS: Tuple[str, ...] = tuple(r.reach_id for r in KUSHAK_MODEL_REACHES)


# ---------------------------------------------------------------------------
# A) Reach state
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ReachContinuityState:
    """Smallest reach-resolved time-evolution state carried by the chain.

    `stage_m` is optional and NEVER invented: it is carried forward only
    when already supplied (there is no explicit storage-stage relation here).
    `storage_m3` None = UNKNOWN/BLOCKED, never zero; explicit 0.0 is valid.
    """

    reach_id: str
    timestep: SimulationTimestep
    timestamp: datetime
    hydraulic_status: SimulationStateStatus
    storage_m3: Optional[float] = None
    stage_m: Optional[float] = None
    incoming_flow_m3_s: Optional[float] = None
    actual_outflow_m3_s: Optional[float] = None
    lateral_inflow_m3_s: Optional[float] = None
    provenance: ProvenanceStatus = ProvenanceStatus.UNKNOWN
    diagnostic: Optional[str] = None


@dataclass(frozen=True)
class ReachTimestepInput:
    """Inputs for one reach's timestep. All flow quantities are Optional:
    None is a preserved UNKNOWN (blocked), explicit 0.0 is a valid zero.
    Lateral inflow is caller-supplied ONLY."""

    reach_id: str
    timestep: SimulationTimestep
    incoming_flow_m3_s: Optional[float]
    incoming_flow_provenance: ProvenanceStatus = ProvenanceStatus.DERIVED
    storage_current_m3: Optional[float] = None
    storage_current_provenance: ProvenanceStatus = ProvenanceStatus.UNKNOWN
    stage_m: Optional[float] = None  # carried forward only, never invented
    lateral_inflow_m3_s: Optional[float] = None  # None BLOCKS; 0.0 valid
    lateral_inflow_provenance: ProvenanceStatus = ProvenanceStatus.ASSUMED
    outflow_decision: Optional[ReachOutflowDecision] = None
    capacity_result: Optional[ManningCapacityResult] = None
    tolerance: float = 1e-6  # accounting tolerance, caller-supplied


@dataclass(frozen=True)
class ReachTimestepResult:
    """One reach's complete timestep outcome. Exposes, independently:
    the reach state, the Step-3 transfer decision, the Phase 7D continuity
    result, and the Step-4 accounting record. The accounting and continuity
    equations are separate locked layers and are never conflated."""

    state: ReachContinuityState
    transfer: ReachTransfer
    continuity: ContinuityUpdateResult
    accounting: ReachAccountingRecord


# ---------------------------------------------------------------------------
# B) single-reach advance — REUSES the Phase 7D continuity equation
# ---------------------------------------------------------------------------


def advance_reach_timestep(inp: ReachTimestepInput) -> ReachTimestepResult:
    """Advance one reach by one timestep.

    1. Step-3 serial routing decides actual_outflow / transferred flow
       (capacity is never silently substituted; a blocked reach yields an
       UNKNOWN actual outflow).
    2. The existing Phase 7D continuity equation V_next = V + dt*(Qin+Qlat-Qout)
       is applied via compute_continuity_update — it is REUSED, not rewritten.
    3. Step-4 accounting records the reach independently.

    A COMPUTED reach produces a DERIVED reach state; a blocked reach produces
    an UNKNOWN reach state (storage None) whose continuity/accounting status
    and diagnostic are surfaced explicitly.
    """
    reach_id = inp.reach_id

    transfer = route_reach_transfer(
        reach_id=reach_id,
        incoming_flow_m3_s=inp.incoming_flow_m3_s,
        decision=inp.outflow_decision,
        capacity_result=inp.capacity_result,
    )
    # Actual outflow comes ONLY from the Step-3 decision path. None here
    # (no rule, blocked capacity, or UG-01 physical block) keeps continuity
    # blocked — Q_capacity is never substituted as outflow.
    outflow_m3_s = transfer.actual_outflow_m3_s

    continuity = compute_continuity_update(ContinuityUpdateInput(
        dt_seconds=inp.timestep.duration_seconds,
        storage_current_m3=inp.storage_current_m3,
        inflow_m3_s=inp.incoming_flow_m3_s,
        lateral_inflow_m3_s=inp.lateral_inflow_m3_s,
        outflow_m3_s=outflow_m3_s,
        provenance={
            "dt": ProvenanceStatus.OFFICIAL_MODEL_VALUE,
            "storage_current": inp.storage_current_provenance,
            "inflow": inp.incoming_flow_provenance,
            "lateral_inflow": inp.lateral_inflow_provenance,
            "outflow": transfer.provenance,
        },
    ))

    accounting = audit_reach_accounting(
        transfer,
        tolerance=inp.tolerance,
        lateral_inflow_m3_s=inp.lateral_inflow_m3_s,
        lateral_inflow_provenance=inp.lateral_inflow_provenance,
    )

    computed = continuity.status == SimulationStateStatus.COMPUTED
    state = ReachContinuityState(
        reach_id=reach_id,
        timestep=inp.timestep,
        timestamp=inp.timestep.end,
        hydraulic_status=continuity.status,
        storage_m3=continuity.storage_next_m3 if computed else None,
        stage_m=inp.stage_m,  # carried, never invented
        incoming_flow_m3_s=inp.incoming_flow_m3_s,
        actual_outflow_m3_s=outflow_m3_s,
        lateral_inflow_m3_s=inp.lateral_inflow_m3_s,
        provenance=(
            ProvenanceStatus.DERIVED if computed else ProvenanceStatus.UNKNOWN
        ),
        diagnostic=continuity.diagnostic,
    )
    return ReachTimestepResult(
        state=state, transfer=transfer,
        continuity=continuity, accounting=accounting,
    )


# ---------------------------------------------------------------------------
# F) Multi-reach serial timestep (single timestep over all four reaches)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ChainTimestepInput:
    """Inputs for one timestep across the whole four-reach chain."""

    timestep: SimulationTimestep
    head_flow_m3_s: Optional[float]  # external flow entering UG-01
    head_flow_provenance: ProvenanceStatus = ProvenanceStatus.DERIVED
    storage_current: Dict[str, float] = field(default_factory=dict)
    storage_provenance: Dict[str, ProvenanceStatus] = field(default_factory=dict)
    stage: Dict[str, float] = field(default_factory=dict)  # carried, never invented
    laterals: Dict[str, float] = field(default_factory=dict)  # reach_id -> lateral
    lateral_provenances: Dict[str, ProvenanceStatus] = field(default_factory=dict)
    decisions: Dict[str, ReachOutflowDecision] = field(default_factory=dict)
    capacity_results: Dict[str, ManningCapacityResult] = field(default_factory=dict)
    tolerance: float = 1e-6  # accounting tolerance, caller-supplied


@dataclass(frozen=True)
class ChainTimestepResult:
    """One timestep over all four reaches in deterministic locked order.

    Threads each reach's transferred flow into the next reach's incoming
    flow; a missing intermediate transfer propagates UNKNOWN downstream and
    that reach's continuity blocks unless its quantities are explicit."""

    results: Tuple[ReachTimestepResult, ...]

    def reach_ids(self) -> Tuple[str, ...]:
        return tuple(r.state.reach_id for r in self.results)

    def state_for(self, reach_id: str) -> ReachTimestepResult:
        for r in self.results:
            if r.state.reach_id == reach_id:
                return r
        raise KeyError(f"no result for reach {reach_id}")


def advance_chain_timestep(inp: ChainTimestepInput) -> ChainTimestepResult:
    """Process all four reaches for one timestep, in order:

    1. UG-01 -> 2. OC-01 -> 3. CD-01 -> 4. OC-02.
    Each reach's transferred downstream flow becomes the next reach's
    incoming flow; storage is updated per reach via the existing Phase 7D
    continuity, and a Step-4 accounting record is produced per reach.
    """
    results = []
    flow = inp.head_flow_m3_s
    flow_prov = inp.head_flow_provenance
    for reach_id in CHAIN_REACH_IDS:
        r = advance_reach_timestep(ReachTimestepInput(
            reach_id=reach_id,
            timestep=inp.timestep,
            incoming_flow_m3_s=flow,
            incoming_flow_provenance=flow_prov,
            storage_current_m3=inp.storage_current.get(reach_id),
            storage_current_provenance=inp.storage_provenance.get(
                reach_id, ProvenanceStatus.UNKNOWN),
            stage_m=inp.stage.get(reach_id),
            lateral_inflow_m3_s=inp.laterals.get(reach_id),
            lateral_inflow_provenance=inp.lateral_provenances.get(
                reach_id, ProvenanceStatus.ASSUMED),
            outflow_decision=inp.decisions.get(reach_id),
            capacity_result=inp.capacity_results.get(reach_id),
            tolerance=inp.tolerance,
        ))
        results.append(r)
        # Transferred flow from reach i becomes incoming flow for reach i+1.
        flow = r.transfer.transferred_m3_s
        flow_prov = r.transfer.provenance
    return ChainTimestepResult(results=tuple(results))


# ---------------------------------------------------------------------------
# F) Minimal multi-timestep series (reuses the single-timestep function)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ChainStepSpec:
    """One step of a multi-timestep run."""

    timestep: SimulationTimestep
    head_flow_m3_s: Optional[float]
    head_flow_provenance: ProvenanceStatus = ProvenanceStatus.DERIVED
    laterals: Dict[str, float] = field(default_factory=dict)
    lateral_provenances: Dict[str, ProvenanceStatus] = field(default_factory=dict)
    decisions: Dict[str, ReachOutflowDecision] = field(default_factory=dict)
    capacity_results: Dict[str, ManningCapacityResult] = field(default_factory=dict)


@dataclass(frozen=True)
class ChainSeriesResult:
    """Deterministic multi-timestep run: one ChainTimestepResult per step in
    order. Each reach's computed storage threads into the next step; a
    blocked step leaves that reach's storage UNKNOWN for the next step."""

    steps: Tuple[ChainTimestepResult, ...]


def advance_chain_series(
    step_specs: Tuple[ChainStepSpec, ...],
    initial_storage: Optional[Dict[str, float]] = None,
    initial_storage_provenance: Optional[Dict[str, ProvenanceStatus]] = None,
    initial_stage: Optional[Dict[str, float]] = None,
    tolerance: float = 1e-6,
) -> ChainSeriesResult:
    """Advance the chain over a sequence of contiguous timesteps.

    Requires strictly ordered, contiguous timesteps (each step's end equals
    the next step's start). This is the ONLY multi-timestep engine; the
    existing Phase 7D `SimulationTimestep` contract is reused and the storage
    balance is computed solely by the reused Phase 7D continuity update.
    """
    for a, b in zip(step_specs, step_specs[1:]):
        if a.timestep.end != b.timestep.start:
            raise ValueError(
                "step timesteps must be contiguous: a step must end exactly "
                "where the next one starts"
            )

    cur_storage = dict(initial_storage or {})
    cur_prov = dict(initial_storage_provenance or {})
    stage = dict(initial_stage or {})
    step_results = []

    for spec in step_specs:
        res = advance_chain_timestep(ChainTimestepInput(
            timestep=spec.timestep,
            head_flow_m3_s=spec.head_flow_m3_s,
            head_flow_provenance=spec.head_flow_provenance,
            storage_current=cur_storage,
            storage_provenance=cur_prov,
            stage=stage,
            laterals=spec.laterals,
            lateral_provenances=spec.lateral_provenances,
            decisions=spec.decisions,
            capacity_results=spec.capacity_results,
            tolerance=tolerance,
        ))
        step_results.append(res)
        for r in res.results:
            rid = r.state.reach_id
            # Storage threads forward: COMPUTED storage carries DERIVED
            # provenance; a blocked reach stays UNKNOWN for the next step.
            if r.state.storage_m3 is not None:
                cur_storage[rid] = r.state.storage_m3
                cur_prov[rid] = r.state.provenance
            else:
                cur_storage[rid] = None
                cur_prov[rid] = ProvenanceStatus.UNKNOWN
            # Stage is carried forward unmodified (never invented).
            stage[rid] = r.state.stage_m

    return ChainSeriesResult(steps=tuple(step_results))