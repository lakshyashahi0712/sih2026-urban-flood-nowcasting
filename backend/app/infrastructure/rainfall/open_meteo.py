from __future__ import annotations

from datetime import datetime, timezone, timedelta
import json
from pathlib import Path
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
    from app.domain.rainfall.models import RainfallRecord, RainfallSeries, RainfallStatus, RainfallProvenance, SourceType
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
    from backend.app.domain.rainfall.models import RainfallRecord, RainfallSeries, RainfallStatus, RainfallProvenance, SourceType


# Constants
MUMBAI_TZ = "Asia/Kolkata"
MUMBAI_LAT = 19.086115
MUMBAI_LON = 72.85291
FORECAST_DAYS = 2  # Assuming default forecast days, adjust if needed
DEFAULT_TIMEOUT = 10.0
CACHE_TTL_MINUTES = 30
DEFAULT_FALLBACK_PATH = Path(__file__).resolve().parents[2] / "data" / "rainfall" / "mumbai_open_meteo_cached.json"


class OpenMeteoCache:
    """In-memory cache with bundled verified snapshot fallback for Open-Meteo responses."""

    def __init__(self, fallback_path: Optional[Path | str] = DEFAULT_FALLBACK_PATH) -> None:
        self._data: Optional[RainfallSeries] = None
        self._timestamp: Optional[datetime] = None
        self._fallback: Optional[RainfallSeries] = None
        self.fallback_path: Optional[Path] = Path(fallback_path) if fallback_path else None
        if self.fallback_path and self.fallback_path.exists():
            self._fallback = self._load_fallback_from_file(self.fallback_path)

    @property
    def has_fallback(self) -> bool:
        """Whether a verified fallback snapshot is loaded."""
        return self._fallback is not None

    def _load_fallback_from_file(self, file_path: Path) -> Optional[RainfallSeries]:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return self._parse_fallback_data(data)
        except Exception:
            return None

    def _parse_fallback_data(self, data: dict) -> RainfallSeries:
        required_fields = ["hourly", "hourly_units", "timezone"]
        for field in required_fields:
            if field not in data:
                raise RainfallAdapterMissingField(field)

        if data["timezone"] != MUMBAI_TZ:
            raise RainfallAdapterTimezoneMismatch(data["timezone"], MUMBAI_TZ)

        units = data["hourly_units"]
        if units.get("precipitation") != "mm":
            raise RainfallAdapterUnitMismatch(units.get("precipitation", "unknown"))

        hourly = data["hourly"]
        times = hourly.get("time", [])
        precipitation = hourly.get("precipitation", [])
        if not times or not precipitation or len(times) != len(precipitation):
            raise RainfallAdapterEmptyForecast()

        kolkata_tz = ZoneInfo(MUMBAI_TZ)
        records = []
        first_local_dt = datetime.fromisoformat(times[0])
        acquired_at = first_local_dt.replace(tzinfo=kolkata_tz).astimezone(timezone.utc)

        for i, (time_str, rain_mm) in enumerate(zip(times, precipitation)):
            local_dt = datetime.fromisoformat(time_str)
            utc_dt = local_dt.replace(tzinfo=kolkata_tz).astimezone(timezone.utc)
            interval_end = utc_dt + timedelta(hours=1)
            record = RainfallRecord(
                timestamp=utc_dt,
                interval_end=interval_end,
                rainfall_mm=float(rain_mm),
                source="open-meteo",
                source_type=SourceType.FORECAST,
                resolution_minutes=60,
                acquired_at=acquired_at,
                forecast_lead_minutes=i * 60,
                status=RainfallStatus.STALE,
                provenance=getattr(RainfallProvenance, "FALLBACK_CACHED_FORECAST", RainfallProvenance.NWP_FALLBACK),
            )
            records.append(record)

        return RainfallSeries(
            records=records,
            source="open-meteo",
            acquired_at=acquired_at,
            provenance=getattr(RainfallProvenance, "FALLBACK_CACHED_FORECAST", RainfallProvenance.NWP_FALLBACK),
        )

    def set(self, data: RainfallSeries) -> None:
        """Cache the response data."""
        self._data = data
        self._timestamp = datetime.now(timezone.utc)

    def get(self, allow_stale: bool = False) -> Optional[RainfallSeries]:
        """Retrieve cached data.

        If allow_stale is False: Returns fresh in-memory live data if not expired (< 30 min).
        If allow_stale is True: Returns in-memory data (even if expired) or the bundled fallback snapshot.
        """
        if not allow_stale:
            if self._data is None or self._timestamp is None:
                return None

            # Check if cache has expired
            now = datetime.now(timezone.utc)
            if now - self._timestamp > timedelta(minutes=CACHE_TTL_MINUTES):
                return None

            return self._data
        else:
            if self._data is not None:
                return self._data
            return self._fallback

    def get_stale(self) -> Optional[RainfallSeries]:
        """Retrieve stale cached data or fallback snapshot."""
        return self.get(allow_stale=True)

    @property
    def has_fresh_cache(self) -> bool:
        """Whether a valid in-memory cache is present and within TTL."""
        if self._data is None or self._timestamp is None:
            return False
        now = datetime.now(timezone.utc)
        return (now - self._timestamp) <= timedelta(minutes=CACHE_TTL_MINUTES)

    @property
    def has_stale_cache(self) -> bool:
        """Whether an in-memory cache is present but expired beyond TTL."""
        if self._data is None or self._timestamp is None:
            return False
        return not self.has_fresh_cache

    def get_status(self) -> dict:
        """Return diagnostic status of the cache and currently available data."""
        if self.has_fresh_cache:
            cache_status = "LIVE"
            provenance = getattr(self._data, "provenance", RainfallProvenance.NWP_FALLBACK)
            prov_val = provenance.value if hasattr(provenance, "value") else str(provenance)
            available_source = "IN_MEMORY_FRESH_CACHE"
            is_stale = False
        elif self.has_stale_cache:
            cache_status = "STALE"
            prov_val = getattr(RainfallProvenance, "FALLBACK_CACHED_FORECAST", RainfallProvenance.NWP_FALLBACK)
            prov_val = prov_val.value if hasattr(prov_val, "value") else str(prov_val)
            available_source = "IN_MEMORY_STALE_CACHE"
            is_stale = True
        elif self.has_fallback:
            cache_status = "FALLBACK_SNAPSHOT"
            prov_val = getattr(RainfallProvenance, "FALLBACK_CACHED_FORECAST", RainfallProvenance.NWP_FALLBACK)
            prov_val = prov_val.value if hasattr(prov_val, "value") else str(prov_val)
            available_source = "BUNDLED_FALLBACK_SNAPSHOT"
            is_stale = True
        else:
            cache_status = "EMPTY"
            prov_val = getattr(RainfallProvenance, "UNAVAILABLE", RainfallProvenance.NWP_FALLBACK)
            prov_val = prov_val.value if hasattr(prov_val, "value") else str(prov_val)
            available_source = "UNAVAILABLE"
            is_stale = False

        cached_at_iso = self._timestamp.isoformat() if self._timestamp else None
        fallback_iso = (
            self._fallback.acquired_at.isoformat()
            if self._fallback and self._fallback.acquired_at
            else None
        )

        return {
            "cache_status": cache_status,
            "cached_at": cached_at_iso,
            "fallback_acquired_at": fallback_iso,
            "effective_acquired_at": cached_at_iso or fallback_iso,
            "cache_ttl_minutes": CACHE_TTL_MINUTES,
            "has_fallback": self.has_fallback,
            "fallback_available": self.has_fallback,
            "available_source": available_source,
            "provenance": prov_val,
            "is_stale": is_stale,
        }


class OpenMeteoAdapter:
    """Adapter for fetching rainfall data from Open-Meteo API."""

    def __init__(
        self,
        timeout: float = DEFAULT_TIMEOUT,
        fallback_path: Optional[Path | str] = DEFAULT_FALLBACK_PATH,
        cache: Optional[OpenMeteoCache] = None,
    ) -> None:
        self.timeout = timeout
        self.cache = cache if cache is not None else OpenMeteoCache(fallback_path=fallback_path)
        self.last_live_status: Optional[str] = None
        self.last_live_error: Optional[str] = None
        self.last_live_acquired_at: Optional[datetime] = None

    def get_status(self) -> dict:
        """Return diagnostic status of the adapter, cache, and fallback state."""
        status = self.cache.get_status()
        status.update({
            "source": "open-meteo",
            "source_type": SourceType.FORECAST.value if hasattr(SourceType.FORECAST, "value") else str(SourceType.FORECAST),
            "resolution_minutes": 60,
            "last_live_status": self.last_live_status,
            "last_live_error": self.last_live_error,
            "last_live_acquired_at": self.last_live_acquired_at.isoformat() if self.last_live_acquired_at else None,
        })
        return status

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
                self.last_live_status = "SUCCESS"
                self.last_live_error = None
                self.last_live_acquired_at = live_data.acquired_at
                # Update cache with fresh live data
                self.cache.set(live_data)
                return live_data
            except Exception as e:
                self.last_live_status = "RATE_LIMITED" if getattr(e, "status_code", None) == 429 else "FAILED"
                self.last_live_error = str(e)
                # Live failed, try to return cached data or bundled verified snapshot
                cached = self.cache.get(allow_stale=True)
                if cached is not None:
                    # Return cached data marked as STALE
                    return self._make_stale_series(cached)
                # No cache available, re-raise the exception
                raise
        else:
            try:
                live_data = await self._fetch_live()
                self.last_live_status = "SUCCESS"
                self.last_live_error = None
                self.last_live_acquired_at = live_data.acquired_at
                return live_data
            except Exception as e:
                self.last_live_status = "RATE_LIMITED" if getattr(e, "status_code", None) == 429 else "FAILED"
                self.last_live_error = str(e)
                raise

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
            new_record = record.model_copy(update={
                "status": RainfallStatus.STALE,
                "provenance": getattr(RainfallProvenance, "FALLBACK_CACHED_FORECAST", RainfallProvenance.NWP_FALLBACK),
            })
            new_records.append(new_record)
        return RainfallSeries(
            records=new_records,
            source=series.source,
            acquired_at=series.acquired_at,
            provenance=getattr(RainfallProvenance, "FALLBACK_CACHED_FORECAST", RainfallProvenance.NWP_FALLBACK),
        )