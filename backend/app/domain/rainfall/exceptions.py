"""Rainfall adapter exceptions."""
from __future__ import annotations


class RainfallAdapterError(Exception):
    """Base exception for rainfall adapter errors."""
    pass


class RainfallAdapterTimeout(RainfallAdapterError):
    """Raised when the provider request times out."""
    def __init__(self, timeout_seconds: float):
        self.timeout_seconds = timeout_seconds
        super().__init__(f"Request timed out after {timeout_seconds}s")


class RainfallAdapterHTTPError(RainfallAdapterError):
    """Raised when the provider returns an HTTP error status."""
    def __init__(self, status_code: int, body: str = ""):
        self.status_code = status_code
        self.body = body
        super().__init__(f"HTTP {status_code}: {body[:200]}")


class RainfallAdapterParseError(RainfallAdapterError):
    """Raised when the response body is not valid JSON."""
    def __init__(self, message: str = "Failed to parse JSON response"):
        super().__init__(message)


class RainfallAdapterMissingField(RainfallAdapterError):
    """Raised when a required field is missing from the response."""
    def __init__(self, field: str):
        self.field = field
        super().__init__(f"Missing required field: {field}")


class RainfallAdapterUnitMismatch(RainfallAdapterError):
    """Raised when precipitation units are not 'mm'."""
    def __init__(self, actual: str):
        self.actual = actual
        super().__init__(f"Expected precipitation units 'mm', got '{actual}'")


class RainfallAdapterTimezoneMismatch(RainfallAdapterError):
    """Raised when the response timezone is not the expected one."""
    def __init__(self, actual: str, expected: str = "Asia/Kolkata"):
        self.actual = actual
        self.expected = expected
        super().__init__(f"Expected timezone '{expected}', got '{actual}'")


class RainfallAdapterEmptyForecast(RainfallAdapterError):
    """Raised when the forecast array is empty."""
    def __init__(self):
        super().__init__("Empty precipitation forecast array")


class RainfallAdapterInvalidTimestamp(RainfallAdapterError):
    """Raised when a timestamp cannot be parsed."""
    def __init__(self, timestamp_str: str, error: str):
        self.timestamp_str = timestamp_str
        super().__init__(f"Invalid timestamp '{timestamp_str}': {error}")


class RainfallAdapterCacheError(RainfallAdapterError):
    """Raised for cache-related errors."""
    pass