"""Rainfall domain models and exceptions."""
from __future__ import annotations

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