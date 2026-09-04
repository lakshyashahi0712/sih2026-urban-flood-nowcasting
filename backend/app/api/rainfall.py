"""Rainfall API endpoints - minimal smoke test for the adapter."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, Field

from app.domain.rainfall.models import RainfallRecord, RainfallStatus, SourceType
from app.infrastructure.rainfall.open_meteo import OpenMeteoAdapter

router = APIRouter(prefix="/rainfall", tags=["rainfall"])

# Module-level adapter instance
_adapter: Optional[OpenMeteoAdapter] = None


def get_adapter() -> OpenMeteoAdapter:
    global _adapter
    if _adapter is None:
        _adapter = OpenMeteoAdapter()
    return _adapter


async def close_adapter() -> None:
    """Close the adapter's HTTP client."""
    global _adapter
    if _adapter is not None:
        await _adapter.close()
        _adapter = None


class RainfallRecordResponse(BaseModel):
    """Response model for a rainfall record."""
    timestamp: datetime
    interval_end: datetime
    rainfall_mm: float
    source: str
    source_type: str
    resolution_minutes: int
    acquired_at: datetime
    forecast_lead_minutes: int
    status: str
    average_intensity_mm_per_hour: float

    @classmethod
    def from_record(cls, record: RainfallRecord) -> "RainfallRecordResponse":
        return cls(
            timestamp=record.timestamp,
            interval_end=record.interval_end,
            rainfall_mm=record.rainfall_mm,
            source=record.source,
            source_type=record.source_type.value,
            resolution_minutes=record.resolution_minutes,
            acquired_at=record.acquired_at,
            forecast_lead_minutes=record.forecast_lead_minutes,
            status=record.status.value,
            average_intensity_mm_per_hour=record.average_intensity_mm_per_hour,
        )


class RainfallSeriesResponse(BaseModel):
    """Response model for a rainfall series."""
    source: str
    acquired_at: datetime
    record_count: int
    resolution_minutes: int
    records: list[RainfallRecordResponse]


@router.get("/mumbai", response_model=RainfallSeriesResponse)
async def get_mumbai_rainfall(
    request: Request,
    use_cache: bool = Query(default=True, description="Allow cached/stale data on failure"),
) -> RainfallSeriesResponse:
    """Fetch and return Mumbai precipitation forecast from Open-Meteo.

    Returns normalized rainfall records with metadata for verification.
    """
    adapter = get_adapter()
    try:
        series = await adapter.fetch(use_cache=use_cache)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Rainfall adapter error: {e}")

    return RainfallSeriesResponse(
        source=series.source,
        acquired_at=series.acquired_at,
        record_count=len(series),
        resolution_minutes=series.records[0].resolution_minutes if series.records else 60,
        records=[RainfallRecordResponse.from_record(r) for r in series.records],
    )


@router.get("/mumbai/status")
async def get_rainfall_status() -> dict:
    """Get adapter cache status without fetching."""
    adapter = get_adapter()
    cached = adapter.cache.get()
    return {
        "cache_status": "LIVE" if cached else "EMPTY",
        "cached_at": adapter.cache._cached_at.isoformat() if adapter.cache._cached_at else None,
        "cache_ttl_minutes": 30,  # from open_meteo module
        "source": "open-meteo",
        "source_type": "forecast",
        "resolution_minutes": 60,
    }


# Import constant for status endpoint
from app.infrastructure.rainfall.open_meteo import CACHE_TTL_MINUTES