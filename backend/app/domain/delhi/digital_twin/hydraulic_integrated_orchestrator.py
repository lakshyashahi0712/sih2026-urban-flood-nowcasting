"""Integrated hydraulic simulation orchestrator for the SIH2026 digital twin.

Provides a unified entry point: rainfall → inflow → hydraulic chain,
exposing consolidated results for research/analysis.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .hydraulic_geometry import CrossSectionProfile
from .hydraulic_hydrograph_driver import HydrographRunResult, run_hydrograph_simulation
from .hydraulic_time_state import SimulationState, SimulationTimestep
from .models import ProvenanceStatus
from .rainfall_to_inflow import RainfallToInflowResult, rainfall_to_inflow


@dataclass
class IntegratedRunResult:
    """Consolidated simulation result (rainfall-to-inflow + hydrograph-driven run)."""
    rainfall_conversion: RainfallToInflowResult
    hydraulic_run: Optional[HydrographRunResult] = None
    diagnostics: List[str] = field(default_factory=list)


def run_integrated_simulation(
    initial_state: SimulationState,
    timesteps: List[SimulationTimestep],
    rainfall_depth_mm: List[Optional[float]],
    catchment_area_km2: float,
    runoff_coefficient: float,
    profile: CrossSectionProfile,
    manning_n: Optional[float],
    slope: Optional[float],
    catchment_area_provenance: ProvenanceStatus = ProvenanceStatus.UNKNOWN,
    runoff_coefficient_provenance: ProvenanceStatus = ProvenanceStatus.UNKNOWN,
    use_capacity_as_outflow: bool = False,
    explicit_outflow_m3_s: Optional[float] = None,
    explicit_outflow_provenance: ProvenanceStatus = ProvenanceStatus.UNKNOWN,
    lateral_inflow_m3_s: Optional[float] = None,
    lateral_inflow_provenance: ProvenanceStatus = ProvenanceStatus.UNKNOWN,
    manning_n_provenance: ProvenanceStatus = ProvenanceStatus.ASSUMED,
    slope_provenance: ProvenanceStatus = ProvenanceStatus.ASSUMED,
    source_id: str = "integrated-simulation",
) -> IntegratedRunResult:
    """Run the consolidated chain: rainfall -> inflow -> hydraulics."""
    # 1. Rainfall to inflow
    conversion = rainfall_to_inflow(
        timesteps=timesteps,
        rainfall_depth_mm=rainfall_depth_mm,
        catchment_area_km2=catchment_area_km2,
        runoff_coefficient=runoff_coefficient,
        catchment_area_provenance=catchment_area_provenance,
        runoff_coefficient_provenance=runoff_coefficient_provenance,
        source_id=source_id,
    )

    hydraulic_run = None
    diagnostics = list(conversion.diagnostics)

    if conversion.status == "COMPUTED":
        # 2. Hydraulic chain
        hydraulic_run = run_hydrograph_simulation(
            initial_state=initial_state,
            hydrograph=conversion.hydrograph,
            timesteps=timesteps,
            profile=profile,
            manning_n=manning_n,
            slope=slope,
            use_capacity_as_outflow=use_capacity_as_outflow,
            explicit_outflow_m3_s=explicit_outflow_m3_s,
            explicit_outflow_provenance=explicit_outflow_provenance,
            lateral_inflow_m3_s=lateral_inflow_m3_s,
            lateral_inflow_provenance=lateral_inflow_provenance,
            manning_n_provenance=manning_n_provenance,
            slope_provenance=slope_provenance,
        )
        diagnostics.extend(hydraulic_run.diagnostics)
    else:
        diagnostics.append(f"Simulation blocked at rainfall conversion: {conversion.status}")

    return IntegratedRunResult(
        rainfall_conversion=conversion,
        hydraulic_run=hydraulic_run,
        diagnostics=diagnostics,
    )
