"""Runoff domain model for Rational Method calculations.

Implements the Rational Method: V = C × i × A × dt / 1000
where:
- V = runoff volume (m³)
- C = runoff coefficient (dimensionless, 0-1)
- i = rainfall intensity (mm/hr)
- A = contributing area (m²)
- dt = timestep (hours)

Note: When rainfall_mm is provided as accumulated depth over the timestep,
i × dt = rainfall_mm, simplifying to V = C × rainfall_mm × A / 1000
"""
from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class RunoffVolume(BaseModel):
    """Runoff volume calculated via Rational Method.

    Attributes:
        rainfall_mm: Accumulated rainfall depth over the timestep [mm]
        contributing_area_m2: Area contributing to runoff [m²]
        runoff_coefficient: Runoff coefficient [0, 1]
        timestep_hours: Duration of the timestep [hours] (> 0)
    """

    rainfall_mm: float = Field(..., ge=0.0, description="Accumulated rainfall depth over the timestep [mm]")
    contributing_area_m2: float = Field(..., ge=0.0, description="Contributing area [m²]")
    runoff_coefficient: float = Field(..., ge=0.0, le=1.0, description="Runoff coefficient [0, 1]")
    timestep_hours: float = Field(..., gt=0.0, description="Timestep duration [hours]")

    @field_validator("timestep_hours")
    @classmethod
    def timestep_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Timestep must be positive")
        return v

    @property
    def volume_m3(self) -> float:
        """Runoff volume calculated via Rational Method [m³].

        Uses the formula: V = C × rainfall_mm × A / 1000
        where rainfall_mm is accumulated depth over the timestep.
        """
        return (
            self.runoff_coefficient
            * self.rainfall_mm
            * self.contributing_area_m2
            / 1000.0
        )


__all__ = ["RunoffVolume"]