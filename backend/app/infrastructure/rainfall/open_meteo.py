from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Optional
from zoneinfo import ZoneInfo

import httpx
from pydantic import ValidationError

try:
    from app.domain.rainfall.exceptions import (
        RainfallAdapterTimeout,
        RainfallAdapterHTTPError,
        RainfallAdapterParseError,
        RainfallAdapterMissingField,
        RainfallAdapterUnitMismatch,
        RainfallAdapterTimezoneMismatch,
        RainfallAdapterEmptyForecast,
        RainfallAdapterInvalidTimestamp,
    )
    from app.domain.rainfall.models import RainfallRecord, RainfallSeries, RainfallStatus, SourceType
except ImportError:
    from backend.app.domain.rainfall.exceptions import (
        RainfallAdapterTimeout,
        RainfallAdapterHTTPError,
        RainfallAdapterParseError,
        RainfallAdapterMissingField,
        RainfallAdapterUnitMismatch,
        RainfallAdapterTimezoneMismatch,
        RainfallAdapterEmptyForecast,
        RainfallAdapterInvalidTimestamp,
    )
    from backend.app.domain.rainfall.models import RainfallRecord, RainfallSeries, RainfallStatus, SourceType


# Constants
MUMBAI_TZ = "Asia/Kolkata"
MUMBAI_LAT = 19.086115
MUMBAI_LON = 72.85291
FORECAST_DAYS = 2  # Assuming default forecast days, adjust if needed
DEFAULT_TIMEOUT = 10.0
CACHE_TTL_MINUTES = 30


class OpenMeteoCache:
    """Simple in-memory cache for Open-Meteo responses."""

    def __init__(self) -> None:
        self._data: Optional[RainfallSeries] = None
        self._timestamp: Optional[datetime] = None

    def set(self, data: RainfallSeries) -> None:
        """Cache the response data."""
        self._data = data
        self._timestamp = datetime.now(timezone.utc)

    def get(self) -> Optional[RainfallSeries]:
        """Retrieve cached data if available and not expired, otherwise None."""
        if self._data is None or self._timestamp is None:
            return None

        # Check if cache has expired
        now = datetime.now(timezone.utc)
        if now - self._timestamp > timedelta(minutes=CACHE_TTL_MINUTES):
            return None

        return self._data


class OpenMeteoAdapter:
    """Adapter for fetching rainfall data from Open-Meteo API."""

    def __init__(self, timeout: float = DEFAULT_TIMEOUT) -> None:
        self.timeout = timeout
        self.cache = OpenMeteoCache()

    async def fetch(self, use_cache: bool = False) -> RainfallSeries:
        """Fetch rainfall data from Open-Meteo API.

        Args:
            use_cache: If True, return cached data on live request failure.

        Returns:
            RainfallSeries: Normalized rainfall data.

        Raises:
            RainfallAdapterTimeout: If the request times out.
            RainfallAdapterHTTPError: If the API returns an HTTP error.
            RainfallAdapterParseError: If the response is not valid JSON.
            RainfallAdapterMissingField: If a required field is missing.
            RainfallAdapterUnitMismatch: If precipitation units are not 'mm'.
            RainfallAdapterTimezoneMismatch: If the response timezone is not Asia/Kolkata.
            RainfallAdapterEmptyForecast: If the precipitation array is empty.
            RainfallAdapterInvalidTimestamp: If a timestamp cannot be parsed.
        """
        if use_cache:
            # Try to get live data first
            try:
                live_data = await self._fetch_live()
                # Update cache with fresh live data
                self.cache.set(live_data)
                return live_data
            except Exception:
                # Live failed, try to return cached data (if available)
                cached = self.cache.get()
                if cached is not None:
                    # Return cached data marked as STALE
                    return self._make_stale_series(cached)
                # No cache available, re-raise the exception
                raise
        else:
            return await self._fetch_live()

    async def _fetch_live(self) -> RainfallSeries:
        """Fetch live data from the API."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    "https://api.open-meteo.com/v1/forecast",
                    params={
                        "latitude": MUMBAI_LAT,
                        "longitude": MUMBAI_LON,
                        "hourly": "precipitation",
                        "timezone": MUMBAI_TZ,
                    },
                )
        except httpx.TimeoutException as e:
            raise RainfallAdapterTimeout(self.timeout) from e
        except httpx.RequestError as e:
            raise RainfallAdapterHTTPError(status_code=503, body=f"Network error: {e}") from e

        if response.status_code != 200:
            raise RainfallAdapterHTTPError(
                status_code=response.status_code,
                body=response.text[:200],
            )

        try:
            data = response.json()
        except ValueError as e:
            raise RainfallAdapterParseError("Failed to parse JSON response") from e

        acquired_at = datetime.now(timezone.utc)
        return self._normalize_response(data, acquired_at)

    def _normalize_response(self, data: dict, acquired_at: datetime) -> RainfallSeries:
        """Validate and normalize Open-Meteo response to RainfallSeries."""
        # Validate required top-level fields
        required_fields = ["hourly", "hourly_units", "timezone"]
        for field in required_fields:
            if field not in data:
                raise RainfallAdapterMissingField(field)

        # Validate timezone
        if data["timezone"] != MUMBAI_TZ:
            raise RainfallAdapterTimezoneMismatch(data["timezone"], MUMBAI_TZ)

        # Validate units
        units = data["hourly_units"]
        if units.get("precipitation") != "mm":
            raise RainfallAdapterUnitMismatch(units.get("precipitation", "unknown"))

        hourly = data["hourly"]
        times = hourly.get("time")
        precipitation = hourly.get("precipitation")

        # First check for missing keys (None)
        if times is None or precipitation is None:
            raise RainfallAdapterMissingField("hourly.time or hourly.precipitation")

        # Then check for empty arrays
        if len(times) == 0 or len(precipitation) == 0:
            raise RainfallAdapterEmptyForecast()

        # Finally check length mismatch
        if len(times) != len(precipitation):
            raise RainfallAdapterMissingField("time/precipitation length mismatch")

        # Parse timestamps and build records
        records = []

        for i, (time_str, rain_mm) in enumerate(zip(times, precipitation)):
            try:
                # Parse as naive datetime (assumed to be in Asia/Kolkata timezone)
                local_dt = datetime.fromisoformat(time_str)
                # Convert to UTC by treating as Asia/Kolkata time
                kolkata_tz = ZoneInfo(MUMBAI_TZ)
                utc_dt = local_dt.replace(tzinfo=kolkata_tz).astimezone(timezone.utc)
                interval_end = utc_dt + timedelta(hours=1)

                # Skip intervals that have already ended
                if interval_end <= acquired_at:
                    continue

                # Calculate forecast lead time
                if utc_dt <= acquired_at < interval_end:
                    # Currently active hourly interval
                    lead_minutes = 0
                else:
                    lead_minutes = int((utc_dt - acquired_at).total_seconds() / 60)

                record = RainfallRecord(
                    timestamp=utc_dt,
                    interval_end=interval_end,
                    rainfall_mm=float(rain_mm),
                    source="open-meteo",
                    source_type=SourceType.FORECAST,
                    resolution_minutes=60,
                    acquired_at=acquired_at,
                    forecast_lead_minutes=lead_minutes,
                    status=RainfallStatus.LIVE,
                )
                records.append(record)
            except (ValueError, TypeError) as e:
                raise RainfallAdapterInvalidTimestamp(time_str, str(e)) from e

        if len(records) == 0:
            raise RainfallAdapterEmptyForecast()

        return RainfallSeries(records=records, source="open-meteo", acquired_at=acquired_at)

    async def close(self) -> None:
        """Close resources if any."""
        pass

    def _make_stale_series(self, series: RainfallSeries) -> RainfallSeries:
        """Return a new series with the same data but status set to STALE."""
        new_records = []
        for record in series.records:
            new_record = record.model_copy(update={"status": RainfallStatus.STALE})
            new_records.append(new_record)
        return RainfallSeries(
            records=new_records,
            source=series.source,
            acquired_at=series.acquired_at,
        )