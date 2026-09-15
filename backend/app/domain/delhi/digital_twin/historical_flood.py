from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, model_validator

from backend.app.domain.delhi.digital_twin.models import ProvenanceStatus


class ObservationType(str, Enum):
    FLOOD_EXTENT = "FLOOD_EXTENT"
    WATERLOGGING_OCCURRENCE = "WATERLOGGING_OCCURRENCE"
    ROAD_CLOSURE = "ROAD_CLOSURE"
    QUALITATIVE_SEVERITY = "QUALITATIVE_SEVERITY"
    RIVER_STAGE = "RIVER_STAGE"


class HistoricalFloodObservation(BaseModel):
    observation_id: str
    event_id: str
    timestamp: datetime
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    observation_type: ObservationType
    value: float | str
    unit: str
    source: str
    provenance: ProvenanceStatus = ProvenanceStatus.UNKNOWN
    uncertainty: Optional[float] = None
    notes: Optional[str] = None

    @model_validator(mode='after')
    def validate_scientific_constraints(self) -> HistoricalFloodObservation:
        # Validate latitude and longitude if provided
        if self.latitude is not None:
            if self.latitude < -90 or self.latitude > 90:
                raise ValueError("latitude must be between -90 and 90")
        if self.longitude is not None:
            if self.longitude < -180 or self.longitude > 180:
                raise ValueError("longitude must be between -180 and 180")

        # Strict scientific rules for value types
        if self.observation_type == ObservationType.QUALITATIVE_SEVERITY:
            if not isinstance(self.value, str):
                raise ValueError("QUALITATIVE_SEVERITY must have a string value")
        elif self.observation_type == ObservationType.RIVER_STAGE:
            if not isinstance(self.value, (int, float)):
                raise ValueError(f"{self.observation_type} must have a numeric value")
        elif self.observation_type in [ObservationType.WATERLOGGING_OCCURRENCE, ObservationType.ROAD_CLOSURE]:
            if not isinstance(self.value, str):
                raise ValueError(f"{self.observation_type} must have a string value")
        # FLOOD_EXTENT accepts numeric or string

        # Provenance enforcement
        if self.provenance != ProvenanceStatus.UNKNOWN and not self.source:
            raise ValueError("Source required for known provenance")

        return self
