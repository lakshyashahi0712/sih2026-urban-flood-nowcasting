"""Canonical Digital-Twin domain models for Phase 1A.

Data contracts only; no computational logic. Unknown values remain None
with UNKNOWN provenance and are never fabricated or defaulted.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional, Union

from pydantic import BaseModel, Field


class ProvenanceStatus(str, Enum):
    OBSERVED = "OBSERVED"
    OFFICIAL = "OFFICIAL"
    OFFICIAL_MODEL_VALUE = "OFFICIAL_MODEL_VALUE"
    DERIVED = "DERIVED"
    ASSUMED = "ASSUMED"
    PROVISIONAL = "PROVISIONAL"
    UNKNOWN = "UNKNOWN"


class Catchment(BaseModel):
    id: str
    name: str
    area_km2: Optional[float] = None
    area_provenance: ProvenanceStatus = ProvenanceStatus.UNKNOWN
    area_uncertainty_km2: Optional[float] = None
    notes: Optional[str] = None


class DrainageReach(BaseModel):
    id: str
    name: str
    length_m: Optional[float] = None
    length_provenance: ProvenanceStatus = ProvenanceStatus.UNKNOWN
    slope_m_per_m: Optional[float] = None
    slope_provenance: ProvenanceStatus = ProvenanceStatus.UNKNOWN
    width_m: Optional[float] = None
    width_provenance: ProvenanceStatus = ProvenanceStatus.UNKNOWN
    depth_m: Optional[float] = None
    depth_provenance: ProvenanceStatus = ProvenanceStatus.UNKNOWN
    notes: Optional[str] = None


class HydraulicParameters(BaseModel):
    manning_n: Optional[float] = None
    manning_n_provenance: ProvenanceStatus = ProvenanceStatus.UNKNOWN
    manning_n_uncertainty: Optional[float] = None
    notes: Optional[str] = None


class RainfallEvent(BaseModel):
    id: str
    start_time: datetime
    end_time: datetime
    source: str
    provenance: ProvenanceStatus
    values: Optional[Union[list[float], dict[str, float]]] = None
    uncertainty: Optional[Union[list[float], dict[str, float]]] = None
    notes: Optional[str] = None


class BoundaryCondition(BaseModel):
    id: str
    type: str
    value: Optional[float] = None
    provenance: ProvenanceStatus = ProvenanceStatus.UNKNOWN
    uncertainty: Optional[float] = None
    notes: Optional[str] = None
