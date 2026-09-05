"""Provider-independent rainfall domain models.

All timestamps are stored in UTC. Source data in local time (e.g., Asia/Kolkata)
must be converted by the adapter before constructing these records.
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class SourceType(str, Enum):
    """Classification of the rainfall data source."""
    FORECAST = "forecast"
    OBSERVATION = "observation"
    NOWCAST = "nowcast"


class RainfallProvenance(str, Enum):
    """Authoritative provenance tracking for precipitation inputs.

    Never label NWP forecast as radar observation.
    """
    RADAR = "RADAR"
    NWP_FALLBACK = "NWP_FALLBACK"
    UNAVAILABLE = "UNAVAILABLE"


class RainfallStatus(str, Enum):
    """Status of the rainfall data at retrieval time."""
    LIVE = "LIVE"
    STALE = "STALE"
    UNAVAILABLE = "UNAVAILABLE"


class RainfallRecord(BaseModel):
    """Normalized rainfall record - provider independent.

    All timestamps are timezone-aware UTC.
    rainfall_mm = accumulated depth over the interval [timestamp, interval_end)
    """
    timestamp: datetime = Field(..., description="Start of accumulation interval (UTC)")
    interval_end: datetime = Field(..., description="End of accumulation interval (UTC)")
    rainfall_mm: float = Field(..., ge=0.0, description="Accumulated precipitation depth over the interval [mm]")
    source: str = Field(..., description="Provider identifier, e.g., 'open-meteo'")
    source_type: SourceType = Field(..., description="forecast | observation | nowcast")
    resolution_minutes: int = Field(..., gt=0, description="Temporal resolution of the source data")
    acquired_at: datetime = Field(..., description="When this record was fetched from the provider (UTC)")
    forecast_lead_minutes: int = Field(..., ge=0, description="Lead time from acquired_at to timestamp")
    status: RainfallStatus = Field(default=RainfallStatus.LIVE, description="Data freshness status")
    provenance: RainfallProvenance = Field(
        default=RainfallProvenance.NWP_FALLBACK,
        description="Authoritative source provenance (RADAR, NWP_FALLBACK, UNAVAILABLE)"
    )

    @field_validator("timestamp", "interval_end", "acquired_at", mode="before")
    @classmethod
    def ensure_utc(cls, v: datetime | str) -> datetime:
        if isinstance(v, str):
            v = datetime.fromisoformat(v.replace("Z", "+00:00"))
        if v.tzinfo is None:
            raise ValueError("Timestamps must be timezone-aware")
        return v.astimezone(timezone.utc)

    @field_validator("interval_end")
    @classmethod
    def interval_after_timestamp(cls, v: datetime, info) -> datetime:
        if "timestamp" in info.data and v <= info.data["timestamp"]:
            raise ValueError("interval_end must be after timestamp")
        return v

    @property
    def duration_hours(self) -> float:
        """Duration of the accumulation interval in hours."""
        return (self.interval_end - self.timestamp).total_seconds() / 3600.0

    @property
    def average_intensity_mm_per_hour(self) -> float:
        """Average intensity over the interval [mm/h].

        This is a DERIVED quantity. Open-Meteo hourly precipitation is already
        accumulated mm over 1 hour, so numerically equal but semantically distinct.
        """
        if self.duration_hours <= 0:
            return 0.0
        return self.rainfall_mm / self.duration_hours


class RainfallSeries(BaseModel):
    """A time-ordered series of rainfall records from a single acquisition."""
    records: list[RainfallRecord] = Field(default_factory=list)
    source: str = Field(default="")
    acquired_at: Optional[datetime] = None
    provenance: RainfallProvenance = Field(
        default=RainfallProvenance.NWP_FALLBACK,
        description="Authoritative source provenance"
    )

    def __len__(self) -> int:
        return len(self.records)

    def __iter__(self):
        return iter(self.records)

    def __getitem__(self, idx):
        return self.records[idx]