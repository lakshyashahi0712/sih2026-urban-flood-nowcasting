"""Hydraulic timestep orchestration for Phase 7D-11.

Connects the existing chain in one reusable function:

    SimulationState + CrossSectionProfile
    -> geometry bundle          (hydraulic_state_geometry / hydraulic_geometry_input)
    -> Manning capacity         (hydraulic_manning_adapter)
    -> OPTIONAL explicit capacity-as-outflow  (hydraulic_capacity_outflow)
    -> next SimulationState     (hydraulic_time_stepper)

No equation is duplicated. Stage comes only from SimulationState.stage_m;
geometry only from the CrossSectionProfile; n and slope only from the
explicit caller inputs. Capacity remains distinct from the actual outflow:
the default never uses capacity as Q_out, and a non-computed capacity is
never substituted with zero. No stage solving, normal-depth solving,
rating curves, routing, rainfall-runoff, conduit hydraulics, structures,
overflow, calibration, replay, ML, or UI.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .hydraulic_capacity_outflow import map_capacity_to_flows
from .hydraulic_geometry import CrossSectionProfile
from .hydraulic_geometry_input import HydraulicGeometryBundle, build_geometry_bundle
from .hydraulic_manning_adapter import (
    ManningCapacityResult,
    calculate_capacity_from_bundle,
)
from .hydraulic_state_geometry import StateGeometryResult, evaluate_state_geometry
from .hydraulic_time_state import SimulationState, SimulationTimestep
from .hydraulic_time_stepper import TimeStepFlowInputs, advance_state
from .models import ProvenanceStatus


@dataclass
class OrchestrationStepResult:
    """The next state plus the intermediate chain artifacts.

    geometry / bundle / capacity are the unmodified intermediate results so
    callers can inspect the chain without re-running it. next_state carries
    the existing stepper's status/diagnostic/provenance semantics.
    """
    next_state: SimulationState
    geometry: Optional[StateGeometryResult] = None
    bundle: Optional[HydraulicGeometryBundle] = None
    capacity: Optional[ManningCapacityResult] = None


def advance_state_through_chain(
    state: SimulationState,
    timestep: SimulationTimestep,
    profile: CrossSectionProfile,
    manning_n: Optional[float],
    slope: Optional[float],
    inflow_m3_s: Optional[float],
    inflow_provenance: ProvenanceStatus = ProvenanceStatus.UNKNOWN,
    use_capacity_as_outflow: bool = False,
    explicit_outflow_m3_s: Optional[float] = None,
    explicit_outflow_provenance: ProvenanceStatus = ProvenanceStatus.UNKNOWN,
    lateral_inflow_m3_s: Optional[float] = None,
    lateral_inflow_provenance: ProvenanceStatus = ProvenanceStatus.UNKNOWN,
    manning_n_provenance: ProvenanceStatus = ProvenanceStatus.ASSUMED,
    slope_provenance: ProvenanceStatus = ProvenanceStatus.ASSUMED,
) -> OrchestrationStepResult:
    """Run the full chain for one timestep.

    - Stage from state.stage_m; geometry from profile; n and slope from the
      explicit caller inputs (None blocks capacity — never substituted).
    - use_capacity_as_outflow is the explicit choice: the DEFAULT (False)
      never uses capacity as Q_out — the outflow comes only from
      explicit_outflow_m3_s (which may be None = UNKNOWN, blocking the
      timestep). With True, a COMPUTED capacity is supplied as Q_out via
      map_capacity_to_flows; a blocked capacity leaves Q_out UNKNOWN,
      never zero.
    - UNKNOWN/blocked states propagate explicitly through the chain; the
      stepper/continuity layer reports the block with full diagnostics.
    - No mutation of state, profile, or any result object.
    """
    # 1. Geometry: A(h)/P(h)/R(h) at the state's stage.
    geometry = evaluate_state_geometry(state, profile)
    bundle = build_geometry_bundle(geometry, state.stage_m)

    # 2. Manning capacity from the bundle (blocked bundles propagate).
    capacity = calculate_capacity_from_bundle(
        bundle, n=manning_n, slope=slope,
        n_provenance=manning_n_provenance,
        slope_provenance=slope_provenance,
    )

    # 3. Flow inputs: capacity is used as Q_out ONLY on the explicit choice.
    if use_capacity_as_outflow:
        flows = map_capacity_to_flows(
            capacity,
            inflow_m3_s=inflow_m3_s,
            inflow_provenance=inflow_provenance,
            lateral_inflow_m3_s=lateral_inflow_m3_s,
            lateral_inflow_provenance=lateral_inflow_provenance,
        )
    else:
        # Default: outflow comes only from the explicit input (None =
        # UNKNOWN); capacity is reported but NOT used as Q_out.
        flows = TimeStepFlowInputs(
            inflow_m3_s=inflow_m3_s,
            lateral_inflow_m3_s=lateral_inflow_m3_s,
            outflow_m3_s=explicit_outflow_m3_s,
            inflow_provenance=inflow_provenance,
            lateral_inflow_provenance=lateral_inflow_provenance,
            outflow_provenance=explicit_outflow_provenance,
        )

    # 4. Advance via the existing stepper (continuity not duplicated).
    next_state = advance_state(state, timestep, flows)
    return OrchestrationStepResult(
        next_state=next_state,
        geometry=geometry,
        bundle=bundle,
        capacity=capacity,
    )
