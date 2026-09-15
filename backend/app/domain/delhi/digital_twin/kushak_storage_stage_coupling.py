"""Reach storage-stage coupling contract (Phase 8B, Step 6 — COUPLING ONLY).

The smallest reach-level coupling that lets a reach state obtain stage from
storage WHEN, AND ONLY WHEN, an explicit storage-stage relation is supplied
by the caller. Everything else is REUSED, never duplicated:

- Phase 7D-13  `StorageStageRelation` — the explicit relation table
               (piecewise-linear interpolation, inverse lookup, domain
               blocking, input validation all live there).
- Phase 7D-14  `with_stage_from_storage` — the stage update itself
               (blocked handling, DERIVED provenance, no mutation).
- Step 5       `kushak_continuity_routing` — the reach state and chain
               results. The continuity calculation is NOT modified and is
               NOT duplicated here.

CORE SCIENTIFIC RULES (enforced by construction):

- NO storage-stage relation exists for real Kushak and NO Kushak
  storage-stage curve is created, inferred, or fabricated here. The
  module-level relation registry starts EMPTY and stays empty.
- No storage-stage relation supplied -> stage remains UNKNOWN (None) and
  downstream geometry evaluation stays blocked.
- Stage is NEVER inferred from discharge, capacity, invert, Manning
  geometry, rainfall, catchment area, or effective profile dimensions —
  the ONLY path to stage is storage through an explicitly supplied
  relation.
- Computed stage is DERIVED provenance, never OBSERVED. The relation's
  own provenance is retained (an effective-scenario relation stays
  ASSUMED / scenario-level and can never promote Tier A).
- Blocked/missing-relation outcomes carry UNKNOWN provenance (conservative).
- Invalid inputs are rejected, never repaired: non-finite/negative
  storage, invalid relation tables, malformed/unknown reach IDs.

Non-goals (STRICT): no downstream/Yamuna boundary, no terminal outfall
solving, no backwater, no rainfall, no calibration, no ML, no flood depth
or street flooding, no new Manning/continuity equations, no timestep
engine, no physical conduit geometry, no surveyed cross-sections, no UI/API.
"""

from __future__ import annotations

from typing import Dict, Optional

from .hydraulic_stage_update import StageUpdateResult, with_stage_from_storage
from .hydraulic_storage_stage import StorageStageRelation
from .hydraulic_time_state import SimulationState, SimulationTimestep
from .kushak_continuity_routing import (
    CHAIN_REACH_IDS,
    ChainTimestepResult,
    ReachContinuityState,
)
from .models import ProvenanceStatus

# The reach-level relation registry. DELIBERATELY EMPTY: there is no
# Kushak storage-stage curve, and none is created here. A caller may
# supply an explicit relation per reach (e.g. an effective-scenario
# relation for testing); without it, stage stays UNKNOWN.
REACH_STORAGE_STAGE_RELATIONS: Dict[str, StorageStageRelation] = {}


def _require_chain_reach(reach_id: str) -> None:
    """Reject malformed/unknown reach IDs; never silently accept them."""
    if reach_id not in CHAIN_REACH_IDS:
        raise ValueError(
            f"unknown reach_id: {reach_id!r} (locked chain order is "
            f"{CHAIN_REACH_IDS})"
        )


def reach_state_to_simulation(
    state: ReachContinuityState,
    timestep: Optional[SimulationTimestep] = None,
) -> SimulationState:
    """Bridge a Step-5 ReachContinuityState to the Phase 7D-1 SimulationState.

    Pure projection: storage, status, provenance and diagnostic are carried
    through unchanged; nothing is computed, filled, or repaired here.
    """
    return SimulationState(
        timestamp=timestep.end if timestep is not None else state.timestamp,
        location_id=state.reach_id,
        status=state.hydraulic_status,
        storage_m3=state.storage_m3,
        stage_m=state.stage_m,
        discharge_m3_s=state.actual_outflow_m3_s,
        provenance=state.provenance,
        diagnostic=state.diagnostic,
    )


def apply_reach_storage_stage_coupling(
    state: ReachContinuityState,
    relation: Optional[StorageStageRelation] = None,
    timestep: Optional[SimulationTimestep] = None,
) -> StageUpdateResult:
    """Obtain one reach's stage from its storage via an EXPLICIT relation.

    - relation None/empty -> the result blocks explicitly and stage remains
      UNKNOWN (None): no relation, no stage — never inferred from
      discharge, capacity, invert, Manning, rainfall, or catchment.
    - relation supplied -> stage = the existing Phase 7D-14
      `with_stage_from_storage` lookup (piecewise-linear inside the
      relation's domain, no extrapolation, computed stage DERIVED).
    - The reach's computed storage is preserved unchanged.
    - The relation is never mutated; nothing is fabricated.
    """
    _require_chain_reach(state.reach_id)
    # Storage->stage is valid ONLY through the explicit relation; the
    # Phase 7D-14 helper owns all blocked/DERIVED semantics.
    return with_stage_from_storage(
        reach_state_to_simulation(state, timestep),
        state.storage_m3,
        relation,
        timestep=timestep,
    )


def couple_chain_timestep(
    chain_result: ChainTimestepResult,
    relations: Optional[Dict[str, StorageStageRelation]] = None,
) -> Dict[str, StageUpdateResult]:
    """Couple stage for every reach of one chain timestep, deterministically,
    in the locked Step-2 order (UG-01 -> OC-01 -> CD-01 -> OC-02).

    `relations` is the caller-supplied reach_id -> StorageStageRelation
    mapping (deterministic; keys must be valid chain reach IDs). With no
    relations (the default, and the real Kushak state) every reach's stage
    remains UNKNOWN and downstream geometry evaluation stays blocked.
    """
    relations = relations or {}
    for rid in relations:
        _require_chain_reach(rid)
    return {
        r.state.reach_id: apply_reach_storage_stage_coupling(
            r.state, relations.get(r.state.reach_id)
        )
        for r in chain_result.results
    }
