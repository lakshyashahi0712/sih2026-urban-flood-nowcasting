"""Rainfall API endpoints - minimal smoke test for the adapter."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, Field

try:
    from backend.app.domain.rainfall.models import RainfallRecord, RainfallStatus, SourceType
    from backend.app.domain.rainfall.radar_models import RainfallProvenance
    from backend.app.infrastructure.rainfall.open_meteo import OpenMeteoAdapter
    from backend.app.infrastructure.rainfall.imd_radar import IMDRadarAdapter
    from backend.app.infrastructure.rainfall.composite_provider import CompositeRainfallProvider
    from backend.app.infrastructure.rainfall.mesonet import MesonetAdapter
    from backend.app.infrastructure.rainfall.nwp_comparison import NWPComparisonService, NWPBiasMetrics
except ImportError:
    from app.domain.rainfall.models import RainfallRecord, RainfallStatus, SourceType
    from app.domain.rainfall.radar_models import RainfallProvenance
    from app.infrastructure.rainfall.open_meteo import OpenMeteoAdapter
    from app.infrastructure.rainfall.imd_radar import IMDRadarAdapter
    from app.infrastructure.rainfall.composite_provider import CompositeRainfallProvider
    from app.infrastructure.rainfall.mesonet import MesonetAdapter
    from app.infrastructure.rainfall.nwp_comparison import NWPComparisonService, NWPBiasMetrics

router = APIRouter(prefix="/rainfall", tags=["rainfall"])

# Module-level adapter instances
_adapter: Optional[OpenMeteoAdapter] = None
_radar_adapter: Optional[IMDRadarAdapter] = None
_mesonet_adapter: Optional[MesonetAdapter] = None
_composite_provider: Optional[CompositeRainfallProvider] = None


def get_adapter() -> OpenMeteoAdapter:
    global _adapter
    if _adapter is None:
        _adapter = OpenMeteoAdapter()
    return _adapter


def get_radar_adapter() -> IMDRadarAdapter:
    global _radar_adapter
    if _radar_adapter is None:
        _radar_adapter = IMDRadarAdapter()
    return _radar_adapter


def get_mesonet_adapter() -> MesonetAdapter:
    global _mesonet_adapter
    if _mesonet_adapter is None:
        _mesonet_adapter = MesonetAdapter()
    return _mesonet_adapter


def get_composite_provider() -> CompositeRainfallProvider:
    global _composite_provider
    if _composite_provider is None:
        _composite_provider = CompositeRainfallProvider(
            radar_adapter=get_radar_adapter(),
            mesonet_adapter=get_mesonet_adapter(),
            nwp_adapter=get_adapter(),
        )
    return _composite_provider


async def close_adapter() -> None:
    """Close the adapter's HTTP client."""
    global _adapter, _radar_adapter, _mesonet_adapter, _composite_provider
    if _adapter is not None:
        await _adapter.close()
        _adapter = None
    if _mesonet_adapter is not None:
        await _mesonet_adapter.close()
        _mesonet_adapter = None
    _radar_adapter = None
    _composite_provider = None


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
    provenance: str = "NWP_FALLBACK"

    @classmethod
    def from_record(cls, record: RainfallRecord) -> "RainfallRecordResponse":
        prov = getattr(record, "provenance", RainfallProvenance.NWP_FALLBACK)
        prov_val = prov.value if hasattr(prov, "value") else str(prov)
        return cls(
            timestamp=record.timestamp,
            interval_end=record.interval_end,
            rainfall_mm=record.rainfall_mm,
            source=record.source,
            source_type=record.source_type.value if hasattr(record.source_type, "value") else str(record.source_type),
            resolution_minutes=record.resolution_minutes,
            acquired_at=record.acquired_at,
            forecast_lead_minutes=record.forecast_lead_minutes,
            status=record.status.value if hasattr(record.status, "value") else str(record.status),
            average_intensity_mm_per_hour=record.average_intensity_mm_per_hour,
            provenance=prov_val,
        )


class RainfallSeriesResponse(BaseModel):
    """Response model for a rainfall series."""
    source: str
    acquired_at: datetime
    record_count: int
    resolution_minutes: int
    records: list[RainfallRecordResponse]
    provenance: str = "NWP_FALLBACK"


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

    prov = getattr(series, "provenance", RainfallProvenance.NWP_FALLBACK)
    prov_val = prov.value if hasattr(prov, "value") else str(prov)

    return RainfallSeriesResponse(
        source=series.source,
        acquired_at=series.acquired_at,
        record_count=len(series),
        resolution_minutes=series.records[0].resolution_minutes if series.records else 60,
        records=[RainfallRecordResponse.from_record(r) for r in series.records],
        provenance=prov_val,
    )


@router.get("/mumbai/status")
async def get_rainfall_status() -> dict:
    """Get adapter cache status without fetching."""
    adapter = get_adapter()
    cached = adapter.cache.get()
    return {
        "cache_status": "LIVE" if cached else "EMPTY",
        "cached_at": adapter.cache._timestamp.isoformat() if adapter.cache._timestamp else None,
        "cache_ttl_minutes": 30,  # from open_meteo module
        "source": "open-meteo",
        "source_type": "forecast",
        "resolution_minutes": 60,
        "provenance": "NWP_FALLBACK",
    }


@router.get("/radar/diagnostics")
async def get_radar_diagnostics() -> dict:
    """Run live diagnostic health-check on official IMD Mumbai Doppler Weather Radar feeds.

    Inspects endpoint availability, HTTP headers, data staleness, format classification,
    and documents institutional access pathways.
    """
    radar = get_radar_adapter()
    try:
        return await radar.check_live_status()
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Failed to probe IMD radar endpoints: {e}")


@router.get("/composite")
async def get_composite_rainfall(
    use_cache: bool = Query(default=True, description="Allow cached/stale data on fallback failure"),
) -> dict:
    """Fetch composite rainfall prioritizing IMD Doppler Radar with Open-Meteo NWP fallback.

    Returns precipitation data stamped with strict data provenance (RADAR vs NWP_FALLBACK).
    """
    provider = get_composite_provider()
    res = await provider.fetch_rainfall(use_cache=use_cache)

    response_data: dict = {
        "provenance": res.provenance.value,
        "status": res.status.value,
        "is_fallback": res.is_fallback,
        "fallback_reason": res.fallback_reason,
        "source_name": res.source_name,
        "acquired_at": res.acquired_at.isoformat(),
        "radar_diagnostics": res.radar_diagnostics,
    }

    if res.series is not None:
        response_data["record_count"] = len(res.series)
        response_data["records"] = [
            RainfallRecordResponse.from_record(r).model_dump() for r in res.series.records
        ]
    elif res.spatial_grid is not None:
        response_data["spatial_grid"] = {
            "mean_rainfall_mm": res.spatial_grid.mean_rainfall_mm(),
            "max_rainfall_mm": res.spatial_grid.max_rainfall_mm(),
            "bounds_32643": res.spatial_grid.bounds_32643,
            "resolution_m": res.spatial_grid.resolution_m,
            "duration_hours": res.spatial_grid.duration_hours,
        }

    return response_data


@router.get("/bias")
async def get_rainfall_bias(
    use_cache: bool = Query(default=True, description="Allow cached/stale data on failure"),
) -> dict:
    """Compare observed Mesonet rainfall against NWP forecast and return bias metrics.

    Fetches both Mesonet observations and NWP forecast, matches them by timestamp,
    and computes per-interval error and aggregated bias statistics.

    Returns NWPBiasMetrics including mean error, MAE, max error, and per-interval comparisons.
    """
    mesonet = get_mesonet_adapter()
    nwp = get_adapter()

    mesonet_series = None
    nwp_series = None
    mesonet_error = None
    nwp_error = None

    try:
        mesonet_series = await mesonet.fetch(use_cache=use_cache)
    except Exception as e:
        mesonet_error = str(e)

    try:
        nwp_series = await nwp.fetch(use_cache=use_cache)
    except Exception as e:
        nwp_error = str(e)

    if mesonet_series is None or nwp_series is None:
        return {
            "status": "UNAVAILABLE",
            "mesonet_available": mesonet_series is not None,
            "nwp_available": nwp_series is not None,
            "mesonet_error": mesonet_error,
            "nwp_error": nwp_error,
            "message": "Both Mesonet observations and NWP forecast are required for bias comparison.",
        }

    # Determine if correction was applied by checking composite provider state
    provider = get_composite_provider()
    metrics = NWPComparisonService.compare(
        observed=mesonet_series,
        nwp=nwp_series,
        correction_bound_mm=provider.max_correction_mm_per_hour,
        correction_applied=False,  # This endpoint reports raw bias, not correction status
    )

    return {
        "status": "OK",
        "mesonet_available": True,
        "nwp_available": True,
        "matched_intervals": metrics.matched_intervals,
        "mean_error_mm": metrics.mean_error_mm,
        "mean_absolute_error_mm": metrics.mean_absolute_error_mm,
        "max_error_mm": metrics.max_error_mm,
        "correction_bound_mm": metrics.correction_bound_mm,
        "comparisons": [
            {
                "timestamp": c.timestamp.isoformat(),
                "observed_mm": c.observed_mm,
                "nwp_mm": c.nwp_mm,
                "error_mm": c.error_mm,
                "relative_error": c.relative_error,
            }
            for c in metrics.comparisons
        ],
    }


# Import constant for status endpoint
try:
    from backend.app.infrastructure.rainfall.open_meteo import CACHE_TTL_MINUTES
except ImportError:
    from app.infrastructure.rainfall.open_meteo import CACHE_TTL_MINUTES