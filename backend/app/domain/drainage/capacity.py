"""Hydraulic capacity model for drainage channels using Manning's equation.

Integrates authoritative BMC engineering attributes (conduit shape, width,
height, length, invert levels) with explicit provenance tracking:
- BMC_AUTHORITATIVE: Surveyed dimensions and invert-derived slopes
- ASSUMED: Prototypical assumptions (e.g. Manning's n=0.018, fallback gutter geometry)
- UNAVAILABLE: Missing or unsupported attributes without fabrication
"""
from __future__ import annotations

import math
from typing import Dict, Optional, Tuple
from pydantic import BaseModel, Field, field_validator

try:
    from backend.app.domain.drainage.models import (
        DrainageChannel,
        Provenance,
        SlopeStatus,
        HydraulicAttributeSource,
    )
except ImportError:
    from app.domain.drainage.models import (
        DrainageChannel,
        Provenance,
        SlopeStatus,
        HydraulicAttributeSource,
    )


class ChannelHydraulicParameters(BaseModel):
    """Hydraulic parameters for Manning's equation (prototypical assumptions).

    All values must be positive. These represent prototype assumptions,
    not real infrastructure data.
    """
    width_m: float = Field(..., gt=0.0, description="Channel width [m]")
    depth_m: float = Field(..., gt=0.0, description="Channel depth [m]")
    manning_n: float = Field(..., gt=0.0, description="Manning's roughness coefficient")
    slope_m_per_m: float = Field(..., gt=0.0, description="Channel slope [m/m]")


class ChannelCapacity(BaseModel):
    """Computed channel capacity and hydraulic provenance.

    Attributes:
        channel_id: Identifier of the DrainageChannel
        capacity_m3_per_s: Flow capacity [m³/s] via Manning's equation
        capacity_volume_m3: Volume capacity over a timestep [m³]
        hydraulic_params: The prototype parameters used (or None if purely authoritative)
        provenance: Drainage network provenance (BMC vs DEM_DERIVED)
        shape: Channel cross-section shape (e.g. RECT, CIRC, OREC)
        area_m2: Cross-sectional flow area [m²]
        wetted_perimeter_m: Wetted perimeter [m]
        hydraulic_radius_m: Hydraulic radius R = A / P [m]
        slope: Longitudinal hydraulic slope [m/m]
        slope_status: Status of hydraulic slope (POSITIVE, FLAT, ADVERSE, ASSUMED, MISSING)
        geometry_source: Provenance of dimensions (BMC_AUTHORITATIVE vs ASSUMED vs UNAVAILABLE)
        slope_source: Provenance of slope (BMC_AUTHORITATIVE vs ASSUMED vs UNAVAILABLE)
        roughness_source: Provenance of Manning's n (always ASSUMED)
    """
    channel_id: str
    capacity_m3_per_s: float = Field(..., ge=0.0)
    capacity_volume_m3: float = Field(..., ge=0.0)
    hydraulic_params: Optional[ChannelHydraulicParameters] = None
    provenance: Provenance = Field(default=Provenance.DEM_DERIVED)
    shape: Optional[str] = None
    area_m2: Optional[float] = None
    wetted_perimeter_m: Optional[float] = None
    hydraulic_radius_m: Optional[float] = None
    slope: Optional[float] = None
    slope_status: Optional[str] = None
    geometry_source: str = "ASSUMED"
    slope_source: str = "ASSUMED"
    roughness_source: str = "ASSUMED"

    @field_validator('capacity_m3_per_s', 'capacity_volume_m3')
    @classmethod
    def non_negative(cls, v: float) -> float:
        if v < 0:
            raise ValueError("Capacity cannot be negative")
        return v


def compute_channel_capacity(
    channel: DrainageChannel,
    params: Optional[ChannelHydraulicParameters] = None,
    timestep_hours: float = 1.0,
    assumed_manning_n: float = 0.018,
    assumed_slope: float = 0.0006,
    assumed_width_m: float = 0.45,
    assumed_depth_m: float = 0.25,
) -> ChannelCapacity:
    """Compute channel capacity using Manning's equation, integrating BMC engineering attributes where valid.

    Hydraulic modeling rules (Phase 2.1):
    1. Channel hydraulic geometry is computed from authoritative BMC shape/dimensions where supported:
       - RECT: Area = W * H, Wetted Perimeter = W + 2H (open rectangular / box drain), R = A / P
       - CIRC: Area = pi * D^2 / 4, Wetted Perimeter = pi * D, R = D / 4
       - Other shapes (e.g. OREC or unknown) are preserved as unsupported/unavailable unless fallback
         params are provided.
    2. Longitudinal slope is computed from (US_INVERT - DS_INVERT) / conduit_length when both invert
       values are present.
    3. Authoritative US_NODE_ID -> DS_NODE_ID direction is strictly preserved (never reversed).
    4. Flat (slope == 0) and adverse (slope < 0) slopes are handled explicitly with capacity = 0.0 m³/s.
       Physical slopes are NOT silently fabricated.
    5. Manning's n is always recorded as an explicitly assumed prototype roughness.
    6. Missing dimensions are not invented.
    7. All hydraulic attributes explicitly record their provenance: BMC_AUTHORITATIVE vs ASSUMED.
    """
    if timestep_hours <= 0:
        raise ValueError("Timestep must be positive")

    # Step 1: Roughness (always ASSUMED prototype)
    manning_n = params.manning_n if params is not None else assumed_manning_n
    roughness_source = HydraulicAttributeSource.ASSUMED.value

    # Step 2: Channel Geometry
    shape_str = channel.shape
    area: Optional[float] = None
    wetted_perimeter: Optional[float] = None
    hydraulic_radius: Optional[float] = None
    geometry_source: str = HydraulicAttributeSource.ASSUMED.value

    # Try authoritative BMC geometry
    if hasattr(channel, "compute_hydraulic_geometry"):
        b_area, b_perim, b_rad, is_supported = channel.compute_hydraulic_geometry()
        if is_supported and b_area is not None and b_area > 0:
            area = b_area
            wetted_perimeter = b_perim
            hydraulic_radius = b_rad
            geometry_source = HydraulicAttributeSource.BMC_AUTHORITATIVE.value
            shape_str = channel.shape

    # Fallback / unavailable geometry handling
    if area is None:
        if channel.provenance == Provenance.BMC:
            # Phase 2.1A: Do NOT replace unsupported shapes with arbitrary 0.45 x 0.25 m geometry.
            # If the exact geometry cannot be represented from the available BMC fields,
            # mark its hydraulic capacity as explicitly unavailable rather than fabricating dimensions.
            area = 0.0
            wetted_perimeter = 0.0
            hydraulic_radius = 0.0
            geometry_source = HydraulicAttributeSource.UNAVAILABLE.value
            shape_str = channel.shape
        elif params is not None:
            # DEM-derived channel uses prototype parameters
            area = params.width_m * params.depth_m
            wetted_perimeter = params.width_m + 2.0 * params.depth_m
            hydraulic_radius = area / wetted_perimeter if wetted_perimeter > 0 else 0.0
            geometry_source = HydraulicAttributeSource.ASSUMED.value
            shape_str = channel.shape or "RECT"
        else:
            area = 0.0
            wetted_perimeter = 0.0
            hydraulic_radius = 0.0
            geometry_source = HydraulicAttributeSource.UNAVAILABLE.value

    # Step 3: Longitudinal Slope
    slope: Optional[float] = None
    slope_status: str = SlopeStatus.MISSING.value
    slope_source: str = HydraulicAttributeSource.ASSUMED.value

    # Try invert-derived slope
    inv_slope = channel.compute_longitudinal_slope() if hasattr(channel, "compute_longitudinal_slope") else None
    if inv_slope is not None:
        slope = inv_slope
        slope_source = HydraulicAttributeSource.BMC_AUTHORITATIVE.value
        if slope > 0:
            slope_status = SlopeStatus.POSITIVE.value
        elif slope == 0:
            slope_status = SlopeStatus.FLAT.value
        else:
            slope_status = SlopeStatus.ADVERSE.value
    elif channel.provenance == Provenance.BMC:
        # BMC channel with missing inverts: explicitly UNAVAILABLE
        slope = 0.0
        slope_source = HydraulicAttributeSource.UNAVAILABLE.value
        slope_status = SlopeStatus.MISSING.value
    elif params is not None:
        slope = params.slope_m_per_m
        slope_source = HydraulicAttributeSource.ASSUMED.value
        slope_status = (
            SlopeStatus.POSITIVE.value if slope > 0
            else (SlopeStatus.FLAT.value if slope == 0 else SlopeStatus.ADVERSE.value)
        )
    else:
        slope = 0.0
        slope_source = HydraulicAttributeSource.UNAVAILABLE.value
        slope_status = SlopeStatus.MISSING.value

    # Step 4: Flow Rate via Manning's Equation
    # If slope is flat (0.0), adverse (< 0.0), or geometry unavailable, capacity is 0.0
    if (
        slope is not None
        and slope > 0
        and area is not None
        and area > 0
        and hydraulic_radius is not None
        and hydraulic_radius > 0
        and manning_n > 0
    ):
        capacity_m3_per_s = (
            (1.0 / manning_n)
            * area
            * (hydraulic_radius ** (2.0 / 3.0))
            * (slope ** 0.5)
        )
    else:
        capacity_m3_per_s = 0.0

    timestep_seconds = timestep_hours * 3600.0
    capacity_volume_m3 = capacity_m3_per_s * timestep_seconds

    return ChannelCapacity(
        channel_id=channel.id,
        capacity_m3_per_s=max(0.0, capacity_m3_per_s),
        capacity_volume_m3=max(0.0, capacity_volume_m3),
        hydraulic_params=params,
        provenance=channel.provenance,
        shape=shape_str,
        area_m2=area,
        wetted_perimeter_m=wetted_perimeter,
        hydraulic_radius_m=hydraulic_radius,
        slope=slope,
        slope_status=slope_status,
        geometry_source=geometry_source,
        slope_source=slope_source,
        roughness_source=roughness_source,
    )


def compute_channel_excess(
    inflow_volume_m3: float,
    capacity: ChannelCapacity
) -> float:
    """Compute excess volume for a channel given inflow and capacity.

    Args:
        inflow_volume_m3: Inflow volume [m³] from upstream catchment
        capacity: Precomputed ChannelCapacity for the timestep

    Returns:
        Excess volume [m³] that cannot be conveyed (non-negative)
    """
    if inflow_volume_m3 < 0:
        raise ValueError("Inflow volume cannot be negative")
    excess = max(0.0, inflow_volume_m3 - capacity.capacity_volume_m3)
    return excess


__all__ = [
    "ChannelHydraulicParameters",
    "ChannelCapacity",
    "compute_channel_capacity",
    "compute_channel_excess"
]