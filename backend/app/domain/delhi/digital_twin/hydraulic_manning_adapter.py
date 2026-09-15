"""Manning discharge adapter for Phase 7D-8.

Takes a Phase 7D-7 HydraulicGeometryBundle, Manning roughness n and
channel slope S, and computes discharge using the existing Phase 7A
Manning primitive (calculate_manning_discharge) — the equation is not
duplicated. The result is a calculated/model capacity only, never an
observed discharge. No stage solving, normal-depth solving, routing,
timestep integration, rainfall-runoff, calibration, conduit hydraulics,
structures, overflow, replay, ML, or UI.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional

from .hydraulic_calculations import (
    ManningDischargeInput,
    calculate_manning_discharge,
)
from .hydraulic_geometry_input import HydraulicGeometryBundle
from .models import ProvenanceStatus


def _is_finite_number(v) -> bool:
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        return False
    return math.isfinite(v)


@dataclass
class ManningCapacityResult:
    """Manning discharge from a geometry bundle, with provenance.

    status follows the existing hydraulic calculation semantics
    ("COMPUTED", "BLOCKED_*"). capacity_m3_s is None unless COMPUTED.
    geometry_provenance (from the bundle) is kept distinct from the
    n/slope provenance (supplied by the caller). A COMPUTED capacity is a
    calculated/model value only, never an observed discharge.
    """
    status: str
    capacity_m3_s: Optional[float] = None
    geometry_provenance: Optional[ProvenanceStatus] = None
    n_provenance: Optional[ProvenanceStatus] = None
    slope_provenance: Optional[ProvenanceStatus] = None
    diagnostic: Optional[str] = None


def calculate_capacity_from_bundle(
    bundle: HydraulicGeometryBundle,
    n: Optional[float],
    slope: Optional[float],
    n_provenance: ProvenanceStatus = ProvenanceStatus.ASSUMED,
    slope_provenance: ProvenanceStatus = ProvenanceStatus.ASSUMED,
) -> ManningCapacityResult:
    """Compute Manning capacity Q = (1/n)·A·R^(2/3)·S^(1/2).

    - Requires a COMPUTED/valid geometry bundle; blocked/UNKNOWN bundles
      propagate their status explicitly (no discharge, no substitution).
    - n and S must be supplied finite numbers; None (UNKNOWN) is never
      silently substituted. Non-positive roughness and negative slope are
      rejected — the Phase 7A primitive's own validation applies and its
      status/diagnostic propagate.
    - Provenance: geometry provenance (bundle) is reported separately
      from n/slope provenance; the result is never claimed OBSERVED.
    - No mutation of the bundle.
    """
    if not bundle.is_valid or bundle.status != "COMPUTED":
        return ManningCapacityResult(
            status=bundle.status,
            geometry_provenance=bundle.geometry_provenance,
            n_provenance=n_provenance,
            slope_provenance=slope_provenance,
            diagnostic=(
                f"Geometry bundle not COMPUTED (status: {bundle.status}); "
                f"no discharge calculated — {bundle.diagnostic}"
            ),
        )

    # Reject UNKNOWN n / S before the primitive so the diagnostic is
    # explicit about which parameter is missing (no silent substitution).
    if n is None:
        return ManningCapacityResult(
            status="BLOCKED_MISSING_INPUT",
            geometry_provenance=bundle.geometry_provenance,
            n_provenance=n_provenance,
            slope_provenance=slope_provenance,
            diagnostic="Manning roughness n is UNKNOWN (None); no value substituted",
        )
    if slope is None:
        return ManningCapacityResult(
            status="BLOCKED_MISSING_INPUT",
            geometry_provenance=bundle.geometry_provenance,
            n_provenance=n_provenance,
            slope_provenance=slope_provenance,
            diagnostic="Slope S is UNKNOWN (None); no value substituted",
        )
    if not _is_finite_number(n) or not _is_finite_number(slope):
        return ManningCapacityResult(
            status="BLOCKED_INVALID_INPUT",
            geometry_provenance=bundle.geometry_provenance,
            n_provenance=n_provenance,
            slope_provenance=slope_provenance,
            diagnostic=(
                f"n and slope must be finite numbers (got n={n!r}, S={slope!r})"
            ),
        )

    result = calculate_manning_discharge(ManningDischargeInput(
        area=bundle.area_m2,
        hydraulic_radius=bundle.radius_m,
        slope=float(slope),
        manning_n=float(n),
    ))

    if result.status != "COMPUTED":
        # Phase 7A validation rejected the inputs (non-positive n, negative
        # slope, etc.) — propagate its status and diagnostic verbatim.
        return ManningCapacityResult(
            status=result.status,
            geometry_provenance=bundle.geometry_provenance,
            n_provenance=n_provenance,
            slope_provenance=slope_provenance,
            diagnostic=result.diagnostic,
        )

    # Calculated/model capacity only.
    return ManningCapacityResult(
        status="COMPUTED",
        capacity_m3_s=result.value,
        geometry_provenance=bundle.geometry_provenance,
        n_provenance=n_provenance,
        slope_provenance=slope_provenance,
        diagnostic=(
            f"Manning capacity Q={result.value} m3/s from bundle "
            f"(A={bundle.area_m2} m2, R={bundle.radius_m} m, S={slope}, "
            f"n={n}); geometry provenance: {bundle.geometry_provenance.value}; "
            f"n provenance: {n_provenance.value}; "
            f"slope provenance: {slope_provenance.value}; "
            f"calculated/model capacity only, not an observed discharge"
        ),
    )
