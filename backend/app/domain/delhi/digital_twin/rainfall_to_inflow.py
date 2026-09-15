"""Rainfall-to-inflow model contract for Phase 7D-17.

A transparent, research-only component converting an ordered rainfall
sequence into an inflow Q(t) that the existing hydraulic_hydrograph_driver
can consume. Simple, explicit event-water-balance formulation ONLY —
no sophisticated hydrology model, no calibration, no GLUE, no ML, no
infiltration model, no spatial rainfall interpolation, no routing, no
production integration.

Exact equation (SI, transparent):

    Q(t) = C * (P_mm / 1000) * (A_km2 * 1e6) / dt_seconds

where C is the explicitly supplied runoff/loss parameter (dimensionless,
caller-supplied, never hard-coded), P_mm the rainfall depth in the
timestep (caller-supplied), A_km2 the caller-supplied catchment area
(provenance-labelled; the Kushak area is NEVER hard-coded here), and
dt_seconds the timestep duration (preserved exactly).

Conventions carried over from the existing hydraulic contracts:
- None/missing rainfall or invalid inputs BLOCK explicitly, never zero.
- Explicit rainfall = 0 is valid (Q = 0 is a computed zero).
- Timestep duration is preserved exactly; missing rainfall is never
  invented or interpolated.
- Results are MODEL/DERIVED, never observed discharge.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import List, Optional

from .hydraulic_time_state import (
    HydrographTimeStep,
    InflowHydrograph,
    SimulationTimestep,
)
from .models import ProvenanceStatus


def _is_finite_number(v) -> bool:
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        return False
    return math.isfinite(v)


@dataclass
class RainfallToInflowResult:
    """Outcome of the rainfall-to-inflow conversion.

    status follows the existing semantics ("COMPUTED", "BLOCKED_*").
    hydrograph is an InflowHydrograph with DERIVED provenance and
    HydrographTimeStep discharge values in m3/s; a step with missing or
    invalid rainfall keeps discharge_m3_s = None (preserved UNKNOWN,
    never zero). The result is MODEL/DERIVED, never observed discharge.
    """
    status: str
    hydrograph: Optional[InflowHydrograph] = None
    diagnostics: List[str] = field(default_factory=list)


def rainfall_to_inflow(
    timesteps: List[SimulationTimestep],
    rainfall_depth_mm: List[Optional[float]],
    catchment_area_km2: Optional[float],
    runoff_coefficient: Optional[float],
    catchment_area_provenance: ProvenanceStatus = ProvenanceStatus.UNKNOWN,
    runoff_coefficient_provenance: ProvenanceStatus = ProvenanceStatus.UNKNOWN,
    source_id: str = "rainfall-runoff",
) -> RainfallToInflowResult:
    """Convert an ordered rainfall sequence into an inflow hydrograph.

    - timesteps and rainfall_depth_mm must be parallel lists (same
      length, in order); rainfall is NEVER invented or interpolated.
    - catchment_area_km2 must be a positive finite caller-supplied
      number with provenance; it is NEVER hard-coded.
    - runoff_coefficient must be a finite caller-supplied number in
      [0, 1] with provenance; it is NEVER hard-coded or calibrated here.
    - None/invalid global inputs -> BLOCKED result (no hydrograph).
    - Per-step None rainfall -> that step's discharge stays None
      (UNKNOWN, blocks downstream, never zero). Explicit 0.0 rainfall is
      valid and yields Q = 0. Negative rainfall is invalid -> step None.
    - Timestep duration is preserved exactly (dt from each
      SimulationTimestep.duration_seconds).
    """
    # Global validation: any invalid global input blocks the whole
    # conversion (no partial hydrograph, no substitution).
    if not _is_finite_number(catchment_area_km2) or catchment_area_km2 <= 0:
        return RainfallToInflowResult(
            status="BLOCKED_INVALID_INPUT",
            diagnostics=(
                [f"catchment_area_km2 must be a positive finite "
                 f"caller-supplied number (got {catchment_area_km2!r})"]
            ),
        )
    if not _is_finite_number(runoff_coefficient) or not (
        0.0 <= runoff_coefficient <= 1.0
    ):
        return RainfallToInflowResult(
            status="BLOCKED_INVALID_INPUT",
            diagnostics=(
                [f"runoff_coefficient must be a finite caller-supplied "
                 f"number in [0, 1] (got {runoff_coefficient!r})"]
            ),
        )
    if len(timesteps) != len(rainfall_depth_mm):
        return RainfallToInflowResult(
            status="BLOCKED_INVALID_INPUT",
            diagnostics=[
                f"timesteps ({len(timesteps)}) and rainfall_depth_mm "
                f"({len(rainfall_depth_mm)}) must be parallel lists of "
                f"the same length"
            ],
        )
    if not timesteps:
        return RainfallToInflowResult(
            status="BLOCKED_INVALID_INPUT",
            diagnostics=["no rainfall timesteps supplied"],
        )

    steps: List[HydrographTimeStep] = []
    diagnostics: List[str] = []
    area_m2 = catchment_area_km2 * 1e6

    for i, (timestep, depth_mm) in enumerate(zip(timesteps, rainfall_depth_mm)):
        # Timestep duration is preserved exactly from the SimulationTimestep.
        dt_seconds = timestep.duration_seconds
        if depth_mm is None:
            # Missing rainfall: preserved UNKNOWN, never zero, never
            # interpolated.
            steps.append(HydrographTimeStep(
                timestamp=timestep.end, discharge_m3_s=None))
            diagnostics.append(
                f"Timestep {i}: rainfall UNKNOWN (None); discharge stays "
                f"UNKNOWN (never zero, never interpolated)")
            continue
        if not _is_finite_number(depth_mm) or depth_mm < 0:
            steps.append(HydrographTimeStep(
                timestamp=timestep.end, discharge_m3_s=None))
            diagnostics.append(
                f"Timestep {i}: rainfall invalid ({depth_mm!r}); "
                f"discharge stays UNKNOWN")
            continue

        # Transparent event water balance:
        # Q = C * (P_mm/1000) * A_m2 / dt_s
        q_m3_s = runoff_coefficient * (depth_mm / 1000.0) * area_m2 / dt_seconds
        steps.append(HydrographTimeStep(
            timestamp=timestep.end, discharge_m3_s=q_m3_s))

    hydrograph = InflowHydrograph(
        source_id=source_id,
        steps=steps,
        provenance=ProvenanceStatus.DERIVED,
    )
    diagnostics.append(
        f"MODEL/DERIVED inflow from event water balance "
        f"Q = C * P * A / dt (C={runoff_coefficient}, "
        f"A={catchment_area_km2} km2, area provenance: "
        f"{catchment_area_provenance.value}, C provenance: "
        f"{runoff_coefficient_provenance.value}); "
        f"calculated/model inflow only, not an observed discharge"
    )
    return RainfallToInflowResult(
        status="COMPUTED",
        hydrograph=hydrograph,
        diagnostics=diagnostics,
    )
