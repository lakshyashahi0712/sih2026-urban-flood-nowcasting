"""Rainfall domain models and exceptions."""
from __future__ import annotations

try:
    from backend.app.domain.rainfall.models import (
        RainfallRecord,
        RainfallSeries,
        RainfallStatus,
        SourceType,
    )
    from backend.app.domain.rainfall.radar_models import (
        RainfallProvenance,
        RadarProductType,
        RadarFormatType,
        RadarMetadata,
        SpatialRainfallGrid,
        MUMBAI_PILOT_BOUNDS_32643,
    )
    from backend.app.domain.rainfall.exceptions import (
        RainfallAdapterError,
        RainfallAdapterTimeout,
        RainfallAdapterHTTPError,
        RainfallAdapterParseError,
        RainfallAdapterMissingField,
        RainfallAdapterUnitMismatch,
        RainfallAdapterTimezoneMismatch,
        RainfallAdapterEmptyForecast,
        RainfallAdapterInvalidTimestamp,
        RainfallAdapterCacheError,
    )
except ImportError:
    from app.domain.rainfall.models import (
        RainfallRecord,
        RainfallSeries,
        RainfallStatus,
        SourceType,
    )
    from app.domain.rainfall.radar_models import (
        RainfallProvenance,
        RadarProductType,
        RadarFormatType,
        RadarMetadata,
        SpatialRainfallGrid,
        MUMBAI_PILOT_BOUNDS_32643,
    )
    from app.domain.rainfall.exceptions import (
        RainfallAdapterError,
        RainfallAdapterTimeout,
        RainfallAdapterHTTPError,
        RainfallAdapterParseError,
        RainfallAdapterMissingField,
        RainfallAdapterUnitMismatch,
        RainfallAdapterTimezoneMismatch,
        RainfallAdapterEmptyForecast,
        RainfallAdapterInvalidTimestamp,
        RainfallAdapterCacheError,
    )

__all__ = [
    "RainfallRecord",
    "RainfallSeries",
    "RainfallStatus",
    "SourceType",
    "RainfallProvenance",
    "RadarProductType",
    "RadarFormatType",
    "RadarMetadata",
    "SpatialRainfallGrid",
    "MUMBAI_PILOT_BOUNDS_32643",
    "RainfallAdapterError",
    "RainfallAdapterTimeout",
    "RainfallAdapterHTTPError",
    "RainfallAdapterParseError",
    "RainfallAdapterMissingField",
    "RainfallAdapterUnitMismatch",
    "RainfallAdapterTimezoneMismatch",
    "RainfallAdapterEmptyForecast",
    "RainfallAdapterInvalidTimestamp",
    "RainfallAdapterCacheError",
]