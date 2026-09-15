"""Time-step execution wrapper for Phase 7D-3.

Advances one SimulationState to the next timestep by applying the
Phase 7D-2 continuity update. No routing, stage/depth, cross-sections,
conduits, structures, overflow, wave equations, rainfall-runoff,
replay, or ML.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional

from .hydraulic_continuity import ContinuityUpdateInput, compute_continuity_update
from .hydraulic_time_state import SimulationState, SimulationStateStatus, SimulationTimestep
from .models import ProvenanceStatus


@dataclass
class TimeStepFlowInputs:
    """Flow inputs for one time step, with per-quantity provenance.

    None is a preserved UNKNOWN; explicit 0.0 is a valid zero.
    """
    inflow_m3_s: Optional[float] = None
    lateral_inflow_m3_s: Optional[float] = None
    outflow_m3_s: Optional[float] = None
    inflow_provenance: ProvenanceStatus = ProvenanceStatus.UNKNOWN
    lateral_inflow_provenance: ProvenanceStatus = ProvenanceStatus.UNKNOWN
    outflow_provenance: ProvenanceStatus = ProvenanceStatus.UNKNOWN


def advance_state(
    state: SimulationState,
    timestep: SimulationTimestep,
    flows: TimeStepFlowInputs,
) -> SimulationState:
    """Produce the next SimulationState by applying the continuity update.

    - The input state is never mutated.
    - The next state's timestamp is the timestep end (start + duration).
    - Storage comes from compute_continuity_update(); the equation is not
      duplicated here.
    - The input state's storage is the current storage; a state with
      UNKNOWN storage (None) blocks the update.
    - Calculated storage is always DERIVED provenance on a COMPUTED state;
      combined input provenance is surfaced in the diagnostic path via the
      continuity result. A blocked result carries the continuity status
      and diagnostic explicitly.
    """
    storage_current = state.storage_m3

    result = compute_continuity_update(ContinuityUpdateInput(
        dt_seconds=timestep.duration_seconds,
        storage_current_m3=storage_current,
        inflow_m3_s=flows.inflow_m3_s,
        lateral_inflow_m3_s=flows.lateral_inflow_m3_s,
        outflow_m3_s=flows.outflow_m3_s,
        provenance={
            "dt": ProvenanceStatus.OFFICIAL_MODEL_VALUE,  # simulation grid, not measured
            "storage_current": state.provenance,
            "inflow": flows.inflow_provenance,
            "lateral_inflow": flows.lateral_inflow_provenance,
            "outflow": flows.outflow_provenance,
        },
    ))

    next_timestamp = timestep.end

    if result.status == SimulationStateStatus.COMPUTED:
        return SimulationState(
            timestamp=next_timestamp,
            location_id=state.location_id,
            status=SimulationStateStatus.COMPUTED,
            storage_m3=result.storage_next_m3,
            # stage/discharge are not computed in this phase; carry the
            # input state's values if present, else remain UNKNOWN.
            stage_m=state.stage_m,
            discharge_m3_s=state.discharge_m3_s,
            provenance=ProvenanceStatus.DERIVED,
            diagnostic=(
                f"{result.diagnostic}"
                f" | input provenance: {result.input_provenance.value}"
            ),
        )

    # Blocked: propagate the continuity failure explicitly.
    return SimulationState(
        timestamp=next_timestamp,
        location_id=state.location_id,
        status=result.status,
        storage_m3=None,
        stage_m=state.stage_m,
        discharge_m3_s=state.discharge_m3_s,
        provenance=ProvenanceStatus.UNKNOWN,
        diagnostic=(
            result.diagnostic
            + (f" | input provenance: {result.input_provenance.value}"
               if result.input_provenance != ProvenanceStatus.UNKNOWN else "")
        ),
    )
