"""Minimal hydraulic inflow interface for Phase 2D.

Represents a discharge time series intended for hydraulic simulation.
This is a standalone simulation-interface contract, not a Digital-Twin entity.
"""

from typing import List, Optional
from pydantic import BaseModel, Field, validator
from .digital_twin.models import ProvenanceStatus


class HydraulicInflowStep(BaseModel):
    """Single timestep of discharge hydrograph for hydraulic inflow."""
    time_minutes: float = Field(..., description="Elapsed time from event start (minutes)")
    discharge_m3_s: float = Field(..., description="Discharge (cubic meters per second)")

    @validator('time_minutes')
    def time_non_negative(cls, v):
        if v < 0:
            raise ValueError('time_minutes must be non-negative')
        return v

    @validator('discharge_m3_s')
    def discharge_non_negative(cls, v):
        if v < 0:
            raise ValueError('discharge_m3_s must be non-negative')
        return v


class HydraulicInflow(BaseModel):
    """Discharge time series for hydraulic inflow boundary."""
    source_id: str = Field(..., description="Identifier of the inflow source (e.g., subcatchment or zone)")
    steps: List[HydraulicInflowStep] = Field(..., description="Time-ordered sequence of discharge steps")
    provenance: ProvenanceStatus = Field(..., description="Provenance of the inflow data")
    uncertainty: Optional[object] = Field(None, description="Quantitative uncertainty if available (e.g., ± value)")
    notes: Optional[str] = Field(None, description="Additional notes or caveats")

    @validator('source_id')
    def source_id_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('source_id must be non-empty')
        return v

    @validator('steps')
    def steps_must_be_time_ordered(cls, v):
        if len(v) < 2:
            return v
        for i in range(1, len(v)):
            if v[i].time_minutes < v[i-1].time_minutes:
                raise ValueError('steps must be in non-decreasing time order')
        return v