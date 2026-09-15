"""Hydraulic geometry input bundle for Phase 7D-7.

Converts the Phase 7D-6 cross-section / state evaluation
(StateGeometryResult) into a validated hydraulic geometry input bundle
for later Manning calculations (not implemented here). Reuses the
existing A(h), P(h), R(h) calculations — no geometry mathematics is
duplicated. No Manning equation, discharge, stage solving, routing,
timestep integration, cross-sections themselves, conduits, structures,
overflow, rainfall-runoff, wave routing, replay, ML, or UI. Neither
SimulationState nor CrossSectionProfile is modified, and no geometry is
fabricated or attached to any reach.
"""

from __future__ import annotations

import math
from typing import Optional

from pydantic import BaseModel, validator

from .hydraulic_calculations import HydraulicCalculationResult
from .hydraulic_geometry import CrossSectionProfile
from .hydraulic_state_geometry import StateGeometryResult, evaluate_state_geometry
from .hydraulic_time_state import SimulationState
from .models import ProvenanceStatus


def _is_positive_finite(v: Optional[float]) -> bool:
    if v is None or isinstance(v, bool) or not isinstance(v, (int, float)):
        return False
    return math.isfinite(v) and v > 0


class HydraulicGeometryBundle(BaseModel):
    """Validated geometry input bundle for a later Manning calculation.

    All three A/P/R quantities must be COMPUTED and physically valid
    (finite, positive) for a COMPUTED bundle; otherwise the bundle is an
    explicit blocked result carrying the upstream status/diagnostic and
    the geometry provenance. No quantity is ever inferred to fill a gap.
    """
    status: str
    stage_m: Optional[float] = None
    area_m2: Optional[float] = None
    perimeter_m: Optional[float] = None
    radius_m: Optional[float] = None
    geometry_provenance: ProvenanceStatus = ProvenanceStatus.UNKNOWN
    diagnostic: Optional[str] = None

    @validator('stage_m')
    def stage_finite(cls, v):
        if v is not None and (isinstance(v, bool) or not isinstance(v, (int, float))
                              or not math.isfinite(v)):
            raise ValueError(f"stage_m must be a finite number (got {v!r})")
        return v

    @property
    def is_valid(self) -> bool:
        return self.status == "COMPUTED"


def build_geometry_bundle(result: StateGeometryResult,
                          stage_m: Optional[float]) -> HydraulicGeometryBundle:
    """Convert a cross-section geometry evaluation into a validated bundle.

    - Blocked/UNKNOWN upstream states are preserved explicitly (status,
      diagnostic, geometry provenance); no values are filled in.
    - A COMPUTED evaluation is accepted only if all three A/P/R results
      are present, COMPUTED, finite and physically valid (positive);
      otherwise the bundle is BLOCKED_INVALID_INPUT — nothing is inferred.
    - No mutation of any input object.
    """
    if result.status != "COMPUTED":
        return HydraulicGeometryBundle(
            status=result.status,
            stage_m=stage_m,
            geometry_provenance=result.geometry_provenance or ProvenanceStatus.UNKNOWN,
            diagnostic=result.diagnostic,
        )

    missing = [name for name, r in (("area", result.area),
                                    ("perimeter", result.perimeter),
                                    ("radius", result.radius))
               if r is None or r.status != "COMPUTED"]
    if missing:
        return HydraulicGeometryBundle(
            status="BLOCKED_MISSING_INPUT",
            stage_m=stage_m,
            geometry_provenance=result.geometry_provenance or ProvenanceStatus.UNKNOWN,
            diagnostic=(
                f"Geometry evaluation incomplete — {', '.join(missing)} "
                f"not COMPUTED; missing quantities are never inferred"
            ),
        )

    values = {
        "area_m2": result.area.value,
        "perimeter_m": result.perimeter.value,
        "radius_m": result.radius.value,
    }
    invalid = [name for name, v in values.items() if not _is_positive_finite(v)]
    if invalid:
        return HydraulicGeometryBundle(
            status="BLOCKED_INVALID_INPUT",
            stage_m=stage_m,
            geometry_provenance=result.geometry_provenance or ProvenanceStatus.UNKNOWN,
            diagnostic=(
                f"Geometry values not physically valid (finite and positive): "
                f"{', '.join(f'{n}={values[n]!r}' for n in invalid)}; "
                f"nothing is inferred"
            ),
        )

    return HydraulicGeometryBundle(
        status="COMPUTED",
        stage_m=stage_m,
        area_m2=values["area_m2"],
        perimeter_m=values["perimeter_m"],
        radius_m=values["radius_m"],
        geometry_provenance=result.geometry_provenance or ProvenanceStatus.UNKNOWN,
        diagnostic=(
            f"Geometry bundle validated: A={values['area_m2']} m², "
            f"P={values['perimeter_m']} m, R={values['radius_m']} m at "
            f"stage {stage_m}"
        ),
    )


def bundle_from_state(state: SimulationState,
                      profile: CrossSectionProfile) -> HydraulicGeometryBundle:
    """Convenience: evaluate_state_geometry + build_geometry_bundle.

    Reuses the existing A(h)/P(h)/R(h) calculations end to end; neither
    input object is mutated.
    """
    result = evaluate_state_geometry(state, profile)
    return build_geometry_bundle(result, state.stage_m)
