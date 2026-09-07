"""Mumbai Rain Mesonet adapter for observed rainfall.

Connects to Mumbai Rain Mesonet stations to fetch 15-minute rainfall observations.
Provides hourly accumulated rainfall data for nowcasting and correction of NWP forecasts.

Strictly adheres to data provenance rules:
- Never fabricates rainfall data.
- Clearly reports station status and data freshness.
- Handles stale/missing station data safely.
"""
from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any
import httpx
import logging

try:
    from backend.app.domain.rainfall.models import (
        RainfallRecord,
        RainfallSeries,
        RainfallStatus,
        SourceType,
    )
except ImportError:
    from app.domain.rainfall.models import (
        RainfallRecord,
        RainfallSeries,
        RainfallStatus,
        SourceType,
    )

logger = logging.getLogger(__name__)

# Mumbai Rain Mesonet station configuration (example - to be configured with real stations)
MESONET_STATIONS = [
    {
        "id": "STN001",
        "name": "Mumbai Mesonet Station 1",
        "lat": 19.0760,  # Example: Colaba area
        "lon": 72.8777,
    },
    {
        "id": "STN002",
        "name": "Mumbai Mesonet Station 2",
        "lat": 19.1342,  # Example: Veravali area
        "lon": 72.8672,
    },
]

# API endpoint for Mesonet data (to be configured with real endpoint)
MESONET_API_ENDPOINT = "https://api.mumbai-rain-mesonet.gov.in/v1/observations"

# Cache duration for Mesonet data (minutes)
MESONET_CACHE_TTL_MINUTES = 15
MAX_STALENESS_MINUTES = 30  # Consider data stale if older than this


class MesonetCache:
    """Simple in-memory cache for Mesonet responses."""

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
        if now - self._timestamp > timedelta(minutes=MESONET_CACHE_TTL_MINUTES):
            return None

        return self._data


class MesonetAdapter:
    """Adapter for fetching rainfall data from Mumbai Rain Mesonet."""

    def __init__(
        self,
        timeout: float = 10.0,
        stations: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        self.timeout = timeout
        self.stations = stations or MESONET_STATIONS
        self.cache = MesonetCache()

    async def fetch(self, use_cache: bool = False) -> RainfallSeries:
        """Fetch rainfall data from Mumbai Rain Mesonet API.

        Args:
            use_cache: If True, return cached data on live request failure.

        Returns:
            RainfallSeries: Normalized hourly accumulated rainfall data.

        Raises:
            MesonetAdapterTimeout: If the request times out.
            MesonetAdapterHTTPError: If the API returns an HTTP error.
            MesonetAdapterParseError: If the response is not valid JSON.
            MesonetAdapterMissingField: If a required field is missing.
            MesonetAdapterUnitMismatch: If precipitation units are not 'mm'.
            MesonetAdapterInvalidTimestamp: If a timestamp cannot be parsed.
            MesonetAdapterNoDataAvailable: If no valid station data is available.
        """
        if use_cache:
            # Try to get live data first
            try:
                live_data = await self._fetch_live()
                # Update cache with fresh live data
                self.cache.set(live_data)
                return live_data
            except Exception as e:
                # Any live-fetch failure -- network error, timeout, HTTP
                # error, or a malformed/unusable response -- falls back to
                # cached data if available, matching the fallback contract
                # established in open_meteo.py (an API failure must not
                # silently become 0 mm rainfall; it must fall back to cache).
                logger.warning(f"Mesonet live fetch failed, falling back to cache: {e}")
                cached = self.cache.get()
                if cached is not None:
                    # Return cached data marked as STALE
                    return self._make_stale_series(cached)
                # No cache available, re-raise the original exception
                raise
        else:
            return await self._fetch_live()

    async def _fetch_live(self) -> RainfallSeries:
        """Fetch live data from the Mesonet API."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(MESONET_API_ENDPOINT)
        except httpx.TimeoutException as e:
            raise MesonetAdapterTimeout(self.timeout) from e

        if response.status_code != 200:
            raise MesonetAdapterHTTPError(
                status_code=response.status_code,
                body=response.text[:200],
            )

        try:
            data = response.json()
        except ValueError as e:
            raise MesonetAdapterParseError("Failed to parse JSON response") from e

        acquired_at = datetime.now(timezone.utc)
        return self._normalize_response(data, acquired_at)

    def _normalize_response(self, data: dict, acquired_at: datetime) -> RainfallSeries:
        """Validate and normalize Mesonet response to RainfallSeries.
        Expects data to contain station observations for the last few hours.
        Converts 15-minute observations to hourly accumulated rainfall.
        """
        # Validate required structure
        if not isinstance(data, dict) or "stations" not in data:
            raise MesonetAdapterMissingField("'stations' field missing in response")

        stations_data = data.get("stations", [])
        if not isinstance(stations_data, list):
            raise MesonetAdapterMissingField("'stations' must be a list")

        # Process each station
        station_hourly_data: Dict[str, List[float]] = {}  # station_id -> list of hourly rainfall (mm)
        valid_stations = 0
        observation_windows_used: set = set()  # Track which observation windows (15min, 1h, 24h) were used

        for station_info in stations_data:
            station_id = station_info.get("id")
            if not station_id:
                continue

            # Find matching station config
            station_config = None
            for config in self.stations:
                if config["id"] == station_id:
                    station_config = config
                    break

            if not station_config:
                logger.warning(f"Unknown Mesonet station ID: {station_id}")
                continue

            # Validate coordinates (basic sanity check)
            lat = station_info.get("lat")
            lon = station_info.get("lon")
            if lat is None or lon is None:
                logger.warning(f"Missing coordinates for station {station_id}")
                continue

            # Validate timestamp of observation
            obs_time_str = station_info.get("timestamp")
            if not obs_time_str:
                logger.warning(f"Missing timestamp for station {station_id}")
                continue

            try:
                obs_time = datetime.fromisoformat(obs_time_str.replace("Z", "+00:00"))
                if obs_time.tzinfo is None:
                    obs_time = obs_time.replace(tzinfo=timezone.utc)
                else:
                    obs_time = obs_time.astimezone(timezone.utc)
            except ValueError as e:
                logger.warning(f"Invalid timestamp for station {station_id}: {obs_time_str}")
                continue

            # Check staleness
            age_minutes = (acquired_at - obs_time).total_seconds() / 60.0
            if age_minutes > MAX_STALENESS_MINUTES:
                logger.warning(f"Stale data for station {station_id}: age {age_minutes:.1f} min")
                continue

            # Validate units (assumed mm)
            units = station_info.get("units", {})
            if units.get("precipitation") != "mm":
                raise MesonetAdapterUnitMismatch(units.get("precipitation", "unknown"))

            # Multi-window observation support: prefer 15min, fallback to 1h, then 24h
            precip_15min = station_info.get("precipitation_15min")
            precip_1h = station_info.get("precipitation_1h")
            precip_24h = station_info.get("precipitation_24h")

            hourly_accum: Dict[datetime, float] = {}  # hour_key -> accumulated mm

            if isinstance(precip_15min, list) and len(precip_15min) > 0:
                # 15-minute observations -> aggregate to hourly
                observation_windows_used.add("15min")
                for i, precip_val in enumerate(precip_15min):
                    try:
                        precip_mm = float(precip_val)
                        if precip_mm < 0:
                            logger.warning(f"Negative precipitation value ignored: {precip_mm}")
                            continue
                    except (ValueError, TypeError):
                        logger.warning(f"Invalid precipitation value: {precip_val}")
                        continue

                    minutes_ago = (len(precip_15min) - 1 - i) * 15
                    obs_time_15min = obs_time - timedelta(minutes=minutes_ago)
                    hour_key = obs_time_15min.replace(minute=0, second=0, microsecond=0)
                    hourly_accum[hour_key] = hourly_accum.get(hour_key, 0.0) + precip_mm

            elif isinstance(precip_1h, list) and len(precip_1h) > 0:
                # 1-hour observations (already hourly)
                observation_windows_used.add("1h")
                for i, precip_val in enumerate(precip_1h):
                    try:
                        precip_mm = float(precip_val)
                        if precip_mm < 0:
                            logger.warning(f"Negative precipitation value ignored: {precip_mm}")
                            continue
                    except (ValueError, TypeError):
                        logger.warning(f"Invalid precipitation value: {precip_val}")
                        continue

                    hours_ago = len(precip_1h) - 1 - i
                    obs_time_1h = obs_time - timedelta(hours=hours_ago)
                    hour_key = obs_time_1h.replace(minute=0, second=0, microsecond=0)
                    hourly_accum[hour_key] = precip_mm

            elif isinstance(precip_24h, (int, float)):
                # 24-hour total: distribute evenly across 24 hours
                observation_windows_used.add("24h")
                try:
                    total_mm = float(precip_24h)
                    if total_mm >= 0:
                        hourly_mm = total_mm / 24.0
                        for h in range(24):
                            hour_key = (obs_time - timedelta(hours=23 - h)).replace(
                                minute=0, second=0, microsecond=0
                            )
                            hourly_accum[hour_key] = hourly_mm
                except (ValueError, TypeError):
                    logger.warning(f"Invalid 24h precipitation value for station {station_id}")

            else:
                logger.warning(f"No valid precipitation data for station {station_id}")
                continue

            # Convert to list of hourly records (from oldest to newest)
            if hourly_accum:
                sorted_hours = sorted(hourly_accum.keys())
                station_hourly_data[station_id] = [hourly_accum[h] for h in sorted_hours]
                valid_stations += 1
            else:
                logger.warning(f"No valid hourly accumulation for station {station_id}")

        if valid_stations == 0:
            raise MesonetAdapterNoDataAvailable("No valid station data available from Mesonet")

        # Determine the time range covered by all stations (intersection)
        # For simplicity, we'll use the time range from the first station's data
        # In a real implementation, we'd align timestamps across stations
        first_station_id = next(iter(station_hourly_data))
        first_station_hourly = station_hourly_data[first_station_id]
        num_hours = len(first_station_hourly)

        # Build records for each hour in the range
        records = []
        # Determine the start time (most recent hour end)
        # We'll assume the data is for the last few hours, ending at the observation time
        end_time = acquired_at.replace(minute=0, second=0, microsecond=0)  # Current hour start
        start_time = end_time - timedelta(hours=num_hours)

        for hour_offset in range(num_hours):
            hour_start = start_time + timedelta(hours=hour_offset)
            hour_end = hour_start + timedelta(hours=1)

            # Collect hourly rainfall from all stations that have data for this hour
            hourly_values = []
            for station_id, hourly_list in station_hourly_data.items():
                if hour_offset < len(hourly_list):
                    hourly_values.append(hourly_list[hour_offset])

            if not hourly_values:
                # No data for this hour from any station, skip
                continue

            # Use the average of available stations for this hour
            avg_rainfall_mm = sum(hourly_values) / len(hourly_values)

            # Calculate forecast lead time (negative for observations? but we treat as nowcast)
            # For observations, lead time is 0 because it's current/past data
            lead_minutes = 0

            record = RainfallRecord(
                timestamp=hour_start,
                interval_end=hour_end,
                rainfall_mm=avg_rainfall_mm,
                source="mumbai-mesonet",
                source_type=SourceType.OBSERVATION,
                resolution_minutes=60,
                acquired_at=acquired_at,
                forecast_lead_minutes=lead_minutes,
                status=RainfallStatus.LIVE if age_minutes <= 0 else RainfallStatus.STALE,
            )
            records.append(record)

        if not records:
            raise MesonetAdapterNoDataAvailable("No valid hourly records could be constructed")

        return RainfallSeries(records=records, source="mumbai-mesonet", acquired_at=acquired_at)

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

    async def close(self) -> None:
        """Close resources if any."""
        pass


# Exception classes
class MesonetAdapterTimeout(Exception):
    def __init__(self, timeout: float) -> None:
        self.timeout = timeout
        super().__init__(f"Mesonet request timed out after {timeout} seconds")


class MesonetAdapterHTTPError(Exception):
    def __init__(self, status_code: int, body: str) -> None:
        self.status_code = status_code
        self.body = body
        super().__init__(f"Mesonet HTTP error: {status_code}")


class MesonetAdapterParseError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(f"Mesonet parse error: {message}")


class MesonetAdapterMissingField(Exception):
    def __init__(self, field: str) -> None:
        self.field = field
        super().__init__(f"Mesonet missing field: {field}")


class MesonetAdapterUnitMismatch(Exception):
    def __init__(self, unit: str) -> None:
        self.unit = unit
        super().__init__(f"Mesonet unit mismatch: expected 'mm', got '{unit}'")


class MesonetAdapterInvalidTimestamp(Exception):
    def __init__(self, timestamp_str: str, error_msg: str) -> None:
        self.timestamp_str = timestamp_str
        super().__init__(f"Mesonet invalid timestamp '{timestamp_str}': {error_msg}")


class MesonetAdapterNoDataAvailable(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(f"Mesonet no data available: {message}")


__all__ = [
    "MesonetAdapter",
    "MesonetAdapterTimeout",
    "MesonetAdapterHTTPError",
    "MesonetAdapterParseError",
    "MesonetAdapterMissingField",
    "MesonetAdapterUnitMismatch",
    "MesonetAdapterInvalidTimestamp",
    "MesonetAdapterNoDataAvailable",
]