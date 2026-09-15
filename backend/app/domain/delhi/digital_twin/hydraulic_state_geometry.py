"""Cross-section / state integration adapter for Phase 7D-6.

The minimal bridge between the Phase 7D-1 SimulationState and the Phase
7D-5 CrossSectionProfile: evaluates A(h), P(h), R(h) for a supplied
stage_m. No stage solving, discharge calculation, Manning routing,
timestep integration, rainfall-runoff, conduits, structures, overflow,
wave routing, replay, ML, or UI. Neither existing contract is redesigned;
neither input object is mutated.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .hydraulic_calculations import HydraulicCalculationResult
from .hydraulic_geometry import CrossSectionProfile, profile_provenance
from .hydraulic_time_state import SimulationState
from .models import ProvenanceStatus


@dataclass
class StateGeometryResult:
    """A(h)/P(h)/R(h) evaluated at a state's stage, with provenance.

    On any blocked outcome, status carries the existing hydraulic
    calculation status (BLOCKED_MISSING_INPUT / BLOCKED_INVALID_INPUT /
    BLOCKED_MISSING_GEOMETRY), the individual results are None, and
    geometry_provenance is still reported when geometry exists.
    """
    status: str
    area: Optional[HydraulicCalculationResult] = None
    perimeter: Optional[HydraulicCalculationResult] = None
    radius: Optional[HydraulicCalculationResult] = None
    geometry_provenance: Optional[ProvenanceStatus] = None
    diagnostic: Optional[str] = None


def evaluate_state_geometry(state: SimulationState,
                            profile: CrossSectionProfile) -> StateGeometryResult:
    """Evaluate A(h), P(h), R(h) at SimulationState.stage_m.

    - UNKNOWN (None) stage -> BLOCKED_MISSING_INPUT; stage is never
      inferred from discharge.
    - Geometry UNKNOWN -> BLOCKED_MISSING_GEOMETRY preserved from the
      profile's own blocked results.
    - Geometry provenance (weakest-link over the profile points) is
      preserved and attached to the result.
    - Neither input object is mutated.
    """
    geometry_provenance = profile_provenance(profile)

    if state.stage_m is None:
        return StateGeometryResult(
            status="BLOCKED_MISSING_INPUT",
            geometry_provenance=geometry_provenance,
            diagnostic=(
                f"State '{state.location_id}': stage_m is UNKNOWN (None); "
                f"geometry evaluation blocked — stage is never inferred "
                f"from discharge"
            ),
        )

    area = profile.wetted_area(state.stage_m)
    if area.status != "COMPUTED":
        # Preserves BLOCKED_MISSING_GEOMETRY (unknown geometry) and
        # BLOCKED_INVALID_INPUT (stage below minimum / non-finite).
        return StateGeometryResult(
            status=area.status,
            geometry_provenance=geometry_provenance,
            diagnostic=area.diagnostic,
        )

    perimeter = profile.wetted_perimeter(state.stage_m)
    radius = profile.hydraulic_radius(state.stage_m)
    return StateGeometryResult(
        status="COMPUTED",
        area=area,
        perimeter=perimeter,
        radius=radius,
        geometry_provenance=geometry_provenance,
    )
