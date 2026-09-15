"""Hydrograph-driven orchestrated simulation for Phase 7D-12.

Thin multi-timestep driver connecting the existing HydrographTimeStep /
Q(t) contract (InflowHydrograph) to the Phase 7D-11 orchestrator:

    HydrographTimeStep sequence
    -> explicit timestep-by-timestep inflow
    -> advance_state_through_chain(...)   (hydraulic_orchestrator, 7D-11)
    -> sequence of SimulationState results

No continuity, Manning, geometry, or timestep arithmetic is duplicated.
Each timestep's inflow comes directly from the supplied hydrograph; a
missing/UNKNOWN discharge stays UNKNOWN and blocks that timestep (never
zero). Stage stays explicit on each SimulationState and is never inferred
from discharge, hydrograph, capacity, or storage. Capacity remains
distinct from Q_out (explicit opt-in only). The loop stops after the
first blocked timestep and reports PARTIAL/BLOCKED using the existing
result semantics. Single-location / single-cross-section only.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .hydraulic_geometry import CrossSectionProfile
from .hydraulic_orchestrator import OrchestrationStepResult, advance_state_through_chain
from .hydraulic_simulation_loop import validate_timesteps
from .hydraulic_time_state import (
    InflowHydrograph,
    SimulationResultStatus,
    SimulationState,
    SimulationTimestep,
)
from .models import ProvenanceStatus


@dataclass
class HydrographRunResult:
    """Outcome of a hydrograph-driven run.

    simulation_status follows the existing result semantics (COMPLETE /
    PARTIAL / BLOCKED). states are the per-timestep SimulationState
    results in order; step_results are the 7D-11 orchestration artifacts
    (geometry / bundle / capacity) so callers can inspect the chain per
    timestep without re-running it.
    """
    simulation_status: SimulationResultStatus
    states: List[SimulationState] = field(default_factory=list)
    step_results: List[OrchestrationStepResult] = field(default_factory=list)
    diagnostics: List[str] = field(default_factory=list)
    provenance_summary: Dict[str, int] = field(default_factory=dict)


def run_hydrograph_simulation(
    initial_state: SimulationState,
    hydrograph: InflowHydrograph,
    timesteps: List[SimulationTimestep],
    profile: CrossSectionProfile,
    manning_n: Optional[float],
    slope: Optional[float],
    use_capacity_as_outflow: bool = False,
    explicit_outflow_m3_s: Optional[float] = None,
    explicit_outflow_provenance: ProvenanceStatus = ProvenanceStatus.UNKNOWN,
    lateral_inflow_m3_s: Optional[float] = None,
    lateral_inflow_provenance: ProvenanceStatus = ProvenanceStatus.UNKNOWN,
    manning_n_provenance: ProvenanceStatus = ProvenanceStatus.ASSUMED,
    slope_provenance: ProvenanceStatus = ProvenanceStatus.ASSUMED,
) -> HydrographRunResult:
    """Run the 7D-11 orchestrator over the hydrograph, timestep by timestep.

    - Timesteps must be chronologically ordered (existing
      validate_timesteps); otherwise BLOCKED before any step runs.
    - Timestep i's inflow is hydrograph.steps[i].discharge_m3_s directly;
      a missing step or UNKNOWN (None) discharge is passed through as
      UNKNOWN and blocks that timestep — never substituted with zero.
    - Stage stays explicit on each SimulationState (carried by the
      orchestrator/stepper); never inferred from Q or anything else.
    - use_capacity_as_outflow is the explicit capacity-as-Q_out opt-in
      (default False); a blocked capacity propagates when enabled.
    - Stops after the first blocked timestep; the successful states are
      retained and the result is PARTIAL (some computed) or BLOCKED (the
      very first step failed).
    - Inputs (hydrograph, initial state, profile) are never mutated.
    """
    sequence_error = validate_timesteps(timesteps)
    if sequence_error is not None:
        return HydrographRunResult(
            simulation_status=SimulationResultStatus.BLOCKED,
            diagnostics=[sequence_error],
        )

    states: List[SimulationState] = []
    step_results: List[OrchestrationStepResult] = []
    diagnostics: List[str] = []
    provenance_summary: Dict[str, int] = {}

    current = initial_state
    blocked = False
    for index, timestep in enumerate(timesteps):
        # Inflow comes directly from the hydrograph; out-of-range steps
        # and None discharge are UNKNOWN (never zero).
        if index < len(hydrograph.steps):
            inflow = hydrograph.steps[index].discharge_m3_s
        else:
            inflow = None

        step = advance_state_through_chain(
            state=current,
            timestep=timestep,
            profile=profile,
            manning_n=manning_n,
            slope=slope,
            inflow_m3_s=inflow,
            inflow_provenance=hydrograph.provenance,
            use_capacity_as_outflow=use_capacity_as_outflow,
            explicit_outflow_m3_s=explicit_outflow_m3_s,
            explicit_outflow_provenance=explicit_outflow_provenance,
            lateral_inflow_m3_s=lateral_inflow_m3_s,
            lateral_inflow_provenance=lateral_inflow_provenance,
            manning_n_provenance=manning_n_provenance,
            slope_provenance=slope_provenance,
        )
        step_results.append(step)
        states.append(step.next_state)
        if step.next_state.diagnostic:
            diagnostics.append(f"Timestep {index}: {step.next_state.diagnostic}")

        key = f"state:{step.next_state.status.value}"
        provenance_summary[key] = provenance_summary.get(key, 0) + 1

        if step.next_state.status != "COMPUTED":
            blocked = True
            break

        current = step.next_state

    if blocked:
        status = (
            SimulationResultStatus.PARTIAL
            if any(s.status == "COMPUTED" for s in states)
            else SimulationResultStatus.BLOCKED
        )
    else:
        status = SimulationResultStatus.COMPLETE

    return HydrographRunResult(
        simulation_status=status,
        states=states,
        step_results=step_results,
        diagnostics=diagnostics,
        provenance_summary=provenance_summary,
    )
