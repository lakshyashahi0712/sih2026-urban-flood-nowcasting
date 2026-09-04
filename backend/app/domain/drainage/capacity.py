"""Hydraulic capacity model for drainage channels using Manning's equation.

This prototype model assigns synthetic hydraulic parameters to DrainageChannel
instances to conveyance capacity. All capacity values are explicitly
prototypical and not representative of real BMC infrastructure.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict
from pydantic import BaseModel, Field, field_validator

from app.domain.drainage.models import DrainageChannel, Provenance


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
    """Computed channel capacity and provenance.

    Attributes:
        channel_id: Identifier of the DrainageChannel
        capacity_m3_per_s: Flow capacity [m³/s] via Manning's equation
        capacity_volume_m3: Volume capacity over a timestep [m³]
        hydraulic_params: The prototype parameters used
        provenance: Source of the capacity calculation (always PROTOTYPE)
    """
    channel_id: str
    capacity_m3_per_s: float = Field(..., ge=0.0)
    capacity_volume_m3: float = Field(..., ge=0.0)
    hydraulic_params: ChannelHydraulicParameters
    provenance: Provenance = Field(default=Provenance.DEM_DERIVED)

    @field_validator('capacity_m3_per_s', 'capacity_volume_m3')
    @classmethod
    def non_negative(cls, v: float) -> float:
        if v < 0:
            raise ValueError("Capacity cannot be negative")
        return v


def compute_channel_capacity(
    channel: DrainageChannel,
    params: ChannelHydraulicParameters,
    timestep_hours: float
) -> ChannelCapacity:
    """Compute channel capacity using Manning's equation for a rectangular open channel.

    Args:
        channel: The DrainageChannel instance (ID used for provenance)
        params: Hydraulic parameters (width, depth, Manning's n, slope)
        timestep_hours: Duration over which to compute volume capacity [hours]

    Returns:
        ChannelCapacity containing flow rate and volume capacities
    """
    # Validate timestep
    if timestep_hours <= 0:
        raise ValueError("Timestep must be positive")

    # Manning's equation for rectangular channel
    # Q = (1/n) * A * R^(2/3) * S^(1/2)
    area = params.width_m * params.depth_m
    wetted_perimeter = params.width_m + 2 * params.depth_m
    hydraulic_radius = area / wetted_perimeter if wetted_perimeter > 0 else 0.0

    # Avoid division by zero or negative values (already validated)
    capacity_m3_per_s = (
        (1.0 / params.manning_n)
        * area
        * (hydraulic_radius ** (2/3))
        * (params.slope_m_per_m ** 0.5)
    )

    # Convert flow rate to volume over timestep
    timestep_seconds = timestep_hours * 3600.0
    capacity_volume_m3 = capacity_m3_per_s * timestep_seconds

    return ChannelCapacity(
        channel_id=channel.id,
        capacity_m3_per_s=max(0.0, capacity_m3_per_s),
        capacity_volume_m3=max(0.0, capacity_volume_m3),
        hydraulic_params=params,
        provenance=Provenance.DEM_DERIVED  # Derived from DEM-based network but prototype params
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