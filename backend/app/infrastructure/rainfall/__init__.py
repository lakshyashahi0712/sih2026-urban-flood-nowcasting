"""Rainfall infrastructure - Open-Meteo and IMD Doppler Radar adapters."""
from __future__ import annotations

try:
    from backend.app.infrastructure.rainfall.open_meteo import (
        OpenMeteoAdapter,
        OpenMeteoCache,
        CACHE_TTL_MINUTES,
        DEFAULT_TIMEOUT,
        FORECAST_DAYS,
        MUMBAI_LAT,
        MUMBAI_LON,
        MUMBAI_TZ,
    )
    from backend.app.infrastructure.rainfall.imd_radar import (
        IMDRadarAdapter,
        IMDRadarProbeResult,
        IMD_ENDPOINTS,
        IMD_MUMBAI_RADAR_PAGE,
        STATION_VERAVALI,
        STATION_COLABA,
        MAX_STALENESS_MINUTES,
    )
    from backend.app.infrastructure.rainfall.composite_provider import (
        CompositeRainfallProvider,
        CompositeRainfallResult,
    )
except ImportError:
    from app.infrastructure.rainfall.open_meteo import (
        OpenMeteoAdapter,
        OpenMeteoCache,
        CACHE_TTL_MINUTES,
        DEFAULT_TIMEOUT,
        FORECAST_DAYS,
        MUMBAI_LAT,
        MUMBAI_LON,
        MUMBAI_TZ,
    )
    from app.infrastructure.rainfall.imd_radar import (
        IMDRadarAdapter,
        IMDRadarProbeResult,
        IMD_ENDPOINTS,
        IMD_MUMBAI_RADAR_PAGE,
        STATION_VERAVALI,
        STATION_COLABA,
        MAX_STALENESS_MINUTES,
    )
    from app.infrastructure.rainfall.composite_provider import (
        CompositeRainfallProvider,
        CompositeRainfallResult,
    )

__all__ = [
    "OpenMeteoAdapter",
    "OpenMeteoCache",
    "CACHE_TTL_MINUTES",
    "DEFAULT_TIMEOUT",
    "FORECAST_DAYS",
    "MUMBAI_LAT",
    "MUMBAI_LON",
    "MUMBAI_TZ",
    "IMDRadarAdapter",
    "IMDRadarProbeResult",
    "IMD_ENDPOINTS",
    "IMD_MUMBAI_RADAR_PAGE",
    "STATION_VERAVALI",
    "STATION_COLABA",
    "MAX_STALENESS_MINUTES",
    "CompositeRainfallProvider",
    "CompositeRainfallResult",
]