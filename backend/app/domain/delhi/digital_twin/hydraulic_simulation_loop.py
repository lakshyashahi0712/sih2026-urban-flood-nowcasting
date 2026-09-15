"""Multi-step simulation loop for Phase 7D-4.

Runs the Phase 7D-3 one-step wrapper over an ordered sequence of
SimulationTimestep objects and returns the existing SimulationResult
contract. No routing, stage/depth, cross-sections, conduits, structures,
overflow, wave equations, rainfall-runoff, replay, or ML.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Sequence, Union

from .hydraulic_time_state import (
    SimulationResult,
    SimulationResultStatus,
    SimulationState,
    SimulationStateStatus,
    SimulationTimestep,
)
from .hydraulic_time_stepper import TimeStepFlowInputs, advance_state
from .models import ProvenanceStatus

# Per-step flows: either one TimeStepFlowInputs reused for every step,
# or a per-step mapping keyed by step index (0-based).
FlowInputsLike = Union[TimeStepFlowInputs, Dict[int, TimeStepFlowInputs]]


def _flows_for_step(flows: FlowInputsLike, index: int) -> Optional[TimeStepFlowInputs]:
    if isinstance(flows, dict):
        return flows.get(index)
    return flows


def validate_timesteps(timesteps: Sequence[SimulationTimestep]) -> Optional[str]:
    """Return an error message if timesteps are not strictly ordered and
    non-overlapping (each start >= previous end), else None."""
    prev_end = None
    for i, ts in enumerate(timesteps):
        if prev_end is not None and ts.start < prev_end:
            return (
                f"Timestep sequence invalid at index {i}: start {ts.start} is "
                f"before previous end {prev_end} (backwards or overlapping)"
            )
        prev_end = ts.end
    return None


def run_simulation(
    initial_state: SimulationState,
    timesteps: Sequence[SimulationTimestep],
    flows: FlowInputsLike,
) -> SimulationResult:
    """Run the one-step wrapper over ordered timesteps.

    - Timesteps must be chronologically ordered and non-overlapping;
      otherwise the result is BLOCKED before any step runs.
    - Each step reuses advance_state(); continuity arithmetic is not
      duplicated.
    - Intermediate states are retained in order.
    - A blocked step stops the loop safely: the successful states are
      retained and the result is PARTIAL (some states computed) or BLOCKED
      (the very first step failed). Failed timesteps are never silently
      skipped.
    - Inputs are never mutated.
    """
    # Validate sequence before running anything.
    sequence_error = validate_timesteps(timesteps)
    if sequence_error is not None:
        return SimulationResult(
            simulation_status=SimulationResultStatus.BLOCKED,
            diagnostics=[sequence_error],
        )

    states: List[SimulationState] = []
    diagnostics: List[str] = []
    provenance_summary: Dict[str, int] = {}

    current = initial_state
    blocked = False
    for index, timestep in enumerate(timesteps):
        step_flows = _flows_for_step(flows, index)
        if step_flows is None:
            states.append(SimulationState(
                timestamp=timestep.end,
                location_id=current.location_id,
                status=SimulationStateStatus.BLOCKED_MISSING_INPUT,
                diagnostic=f"No flow inputs supplied for timestep index {index}",
            ))
            diagnostics.append(f"Timestep {index}: missing flow inputs")
            blocked = True
            break

        next_state = advance_state(current, timestep, step_flows)
        states.append(next_state)
        if next_state.diagnostic:
            diagnostics.append(f"Timestep {index}: {next_state.diagnostic}")

        key = f"state:{next_state.status.value}"
        provenance_summary[key] = provenance_summary.get(key, 0) + 1

        if next_state.status != SimulationStateStatus.COMPUTED:
            blocked = True
            break

        current = next_state

    if blocked:
        status = (
            SimulationResultStatus.PARTIAL
            if any(s.status == SimulationStateStatus.COMPUTED for s in states)
            else SimulationResultStatus.BLOCKED
        )
        return SimulationResult(
            simulation_status=status,
            states=states,
            diagnostics=diagnostics,
            provenance_summary=provenance_summary,
        )

    return SimulationResult(
        simulation_status=SimulationResultStatus.COMPLETE,
        states=states,
        diagnostics=diagnostics,
        provenance_summary=provenance_summary,
    )
