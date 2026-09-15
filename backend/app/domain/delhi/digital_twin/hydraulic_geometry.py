"""Cross-section geometry contract for Phase 7D-5.

Represents an ordered station-elevation cross-section profile with
piecewise-linear geometry, and provides only the geometry primitives
needed later: wetted area A(h), wetted perimeter P(h), hydraulic radius
R(h). h is the absolute water-surface elevation (stage).

No discharge, Manning flow, stage solving, timestep integration,
conduits, structures, overflow, rainfall-runoff, or ML. No synthetic
geometry is ever created: profiles are built only from supplied
station/elevation points; an empty profile stays UNKNOWN and every
geometry query on it returns an explicit blocked result.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Optional, Tuple

from .hydraulic_calculations import (
    HydraulicCalculationResult,
    HydraulicRadiusInput,
    calculate_hydraulic_radius,
)
from .models import ProvenanceStatus
from .hydraulic_contract import ProvenancedValue

# Weakest-link ordering (matches the conservative combination used by the
# 7C/7D-2 modules).
_PROV_WEAKNESS_ORDER = [
    ProvenanceStatus.UNKNOWN, ProvenanceStatus.PROVISIONAL,
    ProvenanceStatus.ASSUMED, ProvenanceStatus.DERIVED,
    ProvenanceStatus.OFFICIAL_MODEL_VALUE,
    ProvenanceStatus.OFFICIAL, ProvenanceStatus.OBSERVED,
]


def _weakest(provenances) -> ProvenanceStatus:
    return min(provenances, key=lambda p: _PROV_WEAKNESS_ORDER.index(p))


def _is_finite_number(v) -> bool:
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        return False
    return math.isfinite(v)


@dataclass
class StationPoint:
    """One measured station-elevation point with provenance."""
    station_m: float
    elevation_m: float
    provenance: ProvenanceStatus = ProvenanceStatus.UNKNOWN

    def __post_init__(self):
        # Validate at construction so a bad point never enters a profile.
        if not _is_finite_number(self.station_m):
            raise ValueError(
                f"station_m must be a finite number (got {self.station_m!r})"
            )
        if not _is_finite_number(self.elevation_m):
            raise ValueError(
                f"elevation_m must be a finite number (got {self.elevation_m!r})"
            )


class CrossSectionProfile:
    """An ordered cross-section profile of station-elevation points.

    Piecewise-linear interpretation. Stations must be strictly increasing
    (duplicates and backwards stations rejected); at least 2 points
    required. No regularization, interpolation, or invention of missing
    geometry. Interpolation is used ONLY to locate the exact intersection
    of the bed profile with a supplied water level.

    An empty profile represents UNKNOWN geometry: every geometry query
    returns an explicit blocked result.
    """

    def __init__(self, points: Optional[List[StationPoint]] = None,
                 cross_section_id: str = "unnamed"):
        self.cross_section_id = cross_section_id
        self.points: List[StationPoint] = list(points) if points else []
        self._validate()

    def _validate(self) -> None:
        if not self.points:
            return  # UNKNOWN geometry; queries will block explicitly
        if len(self.points) < 2:
            raise ValueError(
                f"Cross-section '{self.cross_section_id}' requires at least "
                f"2 points (got {len(self.points)})"
            )
        for p in self.points:
            if not _is_finite_number(p.station_m):
                raise ValueError(
                    f"station_m must be a finite number (got {p.station_m!r})"
                )
            if not _is_finite_number(p.elevation_m):
                raise ValueError(
                    f"elevation_m must be a finite number (got {p.elevation_m!r})"
                )
        stations = [p.station_m for p in self.points]
        for a, b in zip(stations, stations[1:]):
            if b <= a:
                raise ValueError(
                    "stations must be strictly increasing "
                    "(duplicate or backwards station rejected)"
                )

    @property
    def has_geometry(self) -> bool:
        return bool(self.points)

    @property
    def min_elevation_m(self) -> Optional[float]:
        if not self.points:
            return None
        return min(p.elevation_m for p in self.points)

    @property
    def max_elevation_m(self) -> Optional[float]:
        if not self.points:
            return None
        return max(p.elevation_m for p in self.points)

    def _blocked(self, quantity: str, reason: str) -> HydraulicCalculationResult:
        return HydraulicCalculationResult(
            status="BLOCKED_MISSING_GEOMETRY",
            diagnostic=(
                f"Cross-section '{self.cross_section_id}': {quantity} "
                f"unavailable — {reason}"
            ),
        )

    def _wetted_segments(self, h: float) -> List[Tuple[float, float, float, float]]:
        """Sub-segments of the bed profile with elevation < h, clipped to
        the water surface. Returns (x1, z1, x2, z2) tuples. The only
        interpolation is the exact crossing with the supplied water level.
        """
        segments = []
        for p1, p2 in zip(self.points, self.points[1:]):
            x1, z1, x2, z2 = p1.station_m, p1.elevation_m, p2.station_m, p2.elevation_m
            below1, below2 = z1 < h, z2 < h
            if not below1 and not below2:
                continue
            if below1 and below2:
                segments.append((x1, z1, x2, z2))
                continue
            t = (h - z1) / (z2 - z1)
            xc = x1 + t * (x2 - x1)
            if below1:
                segments.append((x1, z1, xc, h))
            else:
                segments.append((xc, h, x2, z2))
        return segments

    def _validate_water_level(self, h) -> Optional[HydraulicCalculationResult]:
        if h is None:
            return self._blocked("wetted geometry", "water level not supplied")
        if not _is_finite_number(h):
            return HydraulicCalculationResult(
                status="BLOCKED_INVALID_INPUT",
                diagnostic=f"Water level must be a finite number (got {h!r})",
            )
        if not self.has_geometry:
            return self._blocked("wetted geometry", "geometry is UNKNOWN (no points)")
        if h < self.min_elevation_m:
            return HydraulicCalculationResult(
                status="BLOCKED_INVALID_INPUT",
                diagnostic=(
                    f"Water level {h} is below the profile minimum elevation "
                    f"{self.min_elevation_m} (dry section); not silently "
                    f"treated as zero"
                ),
            )
        return None

    def wetted_area(self, h: float) -> HydraulicCalculationResult:
        """Wetted area A(h) [m²] below water-surface elevation h."""
        blocked = self._validate_water_level(h)
        if blocked:
            return blocked
        area = 0.0
        for x1, z1, x2, z2 in self._wetted_segments(h):
            area += ((h - z1) + (h - z2)) / 2.0 * (x2 - x1)
        return HydraulicCalculationResult(status="COMPUTED", value=area)

    def wetted_perimeter(self, h: float) -> HydraulicCalculationResult:
        """Wetted perimeter P(h) [m]: bed length below h plus vertical
        walls at the outer section ends where submerged. No walls are
        invented above the supplied profile extent."""
        blocked = self._validate_water_level(h)
        if blocked:
            return blocked
        perimeter = 0.0
        for x1, z1, x2, z2 in self._wetted_segments(h):
            perimeter += math.hypot(x2 - x1, z2 - z1)
        first, last = self.points[0], self.points[-1]
        if first.elevation_m < h:
            perimeter += h - first.elevation_m
        if last.elevation_m < h:
            perimeter += h - last.elevation_m
        return HydraulicCalculationResult(status="COMPUTED", value=perimeter)

    def hydraulic_radius(self, h: float) -> HydraulicCalculationResult:
        """Hydraulic radius R(h) = A(h) / P(h), reusing the Phase 7A primitive."""
        area_result = self.wetted_area(h)
        if area_result.status != "COMPUTED":
            return area_result
        perimeter_result = self.wetted_perimeter(h)
        if perimeter_result.status != "COMPUTED":
            return perimeter_result
        return calculate_hydraulic_radius(HydraulicRadiusInput(
            area=area_result.value,
            wetted_perimeter=perimeter_result.value,
        ))


def profile_provenance(profile: CrossSectionProfile) -> ProvenanceStatus:
    """Weakest-link provenance of a profile's supplied points.

    A profile with no points is UNKNOWN. Provenance is never upgraded:
    any UNKNOWN point makes the whole profile UNKNOWN.
    """
    if not profile.has_geometry:
        return ProvenanceStatus.UNKNOWN
    return _weakest([p.provenance for p in profile.points])


def provenanced_station(station_m: ProvenancedValue,
                        elevation_m: ProvenancedValue) -> StationPoint:
    """Build a StationPoint from ProvenancedValues, rejecting UNKNOWN values.

    UNKNOWN station/elevation cannot become geometry; the caller should
    leave the profile empty (UNKNOWN) instead.
    """
    if not isinstance(station_m, ProvenancedValue) or not isinstance(elevation_m, ProvenancedValue):
        raise ValueError("station and elevation must be ProvenancedValue")
    if station_m.value is None or elevation_m.value is None:
        raise ValueError(
            "UNKNOWN station/elevation values cannot become geometry; "
            "leave the profile empty (UNKNOWN) instead"
        )
    return StationPoint(
        station_m=float(station_m.value),
        elevation_m=float(elevation_m.value),
        provenance=_weakest([station_m.provenance, elevation_m.provenance]),
    )
