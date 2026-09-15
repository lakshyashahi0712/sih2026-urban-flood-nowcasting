"""Storage->stage integration for Phase 7D-14.

A pure helper recomputing the next state's stage from its next storage
using an explicitly supplied StorageStageRelation (Phase 7D-13):

    SimulationState + next_storage_m3 + StorageStageRelation
    -> next SimulationState with stage_m recomputed from storage

The storage itself is NOT computed here — it comes from the existing
continuity update (the caller supplies the computed next storage). The
relation must be supplied by the caller; it is never inferred or
fabricated. Missing storage/relation blocks explicitly (never zero).
Recomputed stage is DERIVED provenance (a calculation is never
OBSERVED). Lookups never extrapolate outside the relation's domain.
No geometry-to-storage, stage solving, Manning changes, routing,
conduit hydraulics, structures, rainfall-runoff, flood depth,
calibration, replay, ML, or UI. Existing continuity, stepper,
orchestrator, and hydrograph-driver behavior is unchanged.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .hydraulic_storage_stage import StorageStageRelation
from .hydraulic_time_state import (
    SimulationState,
    SimulationStateStatus,
    SimulationTimestep,
)
from .models import ProvenanceStatus


@dataclass
class StageUpdateResult:
    """The next state plus the underlying lookup artifact.

    next_state carries the recomputed stage on success; lookup is the
    unmodified StorageStageRelation lookup result (stage_to_storage is
    not used; storage_to_stage produces the stage) so callers can inspect
    the conversion without re-running it.
    """
    next_state: SimulationState
    lookup: object = None  # HydraulicCalculationResult from storage_to_stage


def with_stage_from_storage(
    state: SimulationState,
    next_storage_m3: Optional[float],
    relation: Optional[StorageStageRelation],
    timestep: Optional[SimulationTimestep] = None,
) -> StageUpdateResult:
    """Recompute the next state's stage from its next storage.

    - next_storage_m3 comes from the existing continuity update (supplied
      by the caller, not computed here).
    - The stage is looked up in the explicit relation via
      storage_to_stage; no extrapolation outside the relation domain.
    - next_storage_m3 is None (UNKNOWN) or the relation is missing/None
      (UNKNOWN) or empty -> the result blocks explicitly; the stage is
      UNKNOWN, never zero, never inferred from anything else.
    - Recomputed stage is DERIVED provenance; the state's own provenance
      semantics are preserved (a COMPUTED state is never OBSERVED).
    - No mutation of the input state or relation.
    """
    next_timestamp = timestep.end if timestep is not None else state.timestamp

    if relation is None or not relation.has_relation:
        return StageUpdateResult(
            next_state=SimulationState(
                timestamp=next_timestamp,
                location_id=state.location_id,
                status=SimulationStateStatus.BLOCKED_MISSING_INPUT,
                storage_m3=next_storage_m3,
                stage_m=None,
                provenance=ProvenanceStatus.UNKNOWN,
                diagnostic=(
                    "Storage-stage relation is UNKNOWN (None or empty); "
                    "stage is never inferred from storage or any other source"
                ),
            ),
        )

    if next_storage_m3 is None:
        return StageUpdateResult(
            next_state=SimulationState(
                timestamp=next_timestamp,
                location_id=state.location_id,
                status=SimulationStateStatus.BLOCKED_MISSING_INPUT,
                storage_m3=None,
                stage_m=None,
                provenance=ProvenanceStatus.UNKNOWN,
                diagnostic=(
                    "Next storage is UNKNOWN (None); stage is never "
                    "inferred from storage or any other source"
                ),
            ),
        )

    lookup = relation.storage_to_stage(next_storage_m3)

    if lookup.status != "COMPUTED":
        # Outside domain or invalid: propagate explicitly (no
        # extrapolation, no clipping, no zero substitution).
        return StageUpdateResult(
            next_state=SimulationState(
                timestamp=next_timestamp,
                location_id=state.location_id,
                status=SimulationStateStatus.BLOCKED_INVALID_INPUT,
                storage_m3=next_storage_m3,
                stage_m=None,
                provenance=ProvenanceStatus.UNKNOWN,
                diagnostic=lookup.diagnostic,
            ),
            lookup=lookup,
        )

    # Recomputed stage: DERIVED provenance (a calculation is never
    # OBSERVED); the relation provenance is surfaced in the diagnostic.
    return StageUpdateResult(
        next_state=SimulationState(
            timestamp=next_timestamp,
            location_id=state.location_id,
            status=SimulationStateStatus.COMPUTED,
            storage_m3=next_storage_m3,
            stage_m=lookup.value,
            provenance=ProvenanceStatus.DERIVED,
            diagnostic=(
                f"{lookup.diagnostic} | storage provenance: {relation.provenance.value}"
            ),
        ),
        lookup=lookup,
    )
