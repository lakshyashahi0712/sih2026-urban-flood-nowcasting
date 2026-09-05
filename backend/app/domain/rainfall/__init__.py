"""Rainfall domain models and exceptions."""
from __future__ import annotations

try:
    from backend.app.domain.rainfall.models import (
        RainfallRecord,
        RainfallSeries,
        RainfallStatus,
        SourceType,
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