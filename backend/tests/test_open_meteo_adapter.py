"""Tests for the Open-Meteo rainfall adapter."""
from __future__ import annotations

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest

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
from app.domain.rainfall.models import RainfallStatus, SourceType
from app.infrastructure.rainfall.open_meteo import OpenMeteoAdapter, OpenMeteoCache


# Load the fixture
FIXTURE_PATH = Path(__file__).parent / "fixtures" / "open_meteo_response.json"


def load_fixture() -> dict:
    with open(FIXTURE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def fixture_data():
    return load_fixture()


@pytest.fixture
def adapter():
    return OpenMeteoAdapter(timeout=0.1)  # short timeout for tests


@pytest.mark.asyncio
async def test_happy_path(adapter, fixture_data):
    """Test normal operation with the fixture."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = fixture_data
    mock_response.text = json.dumps(fixture_data)

    with patch.object(httpx.AsyncClient, "get", return_value=mock_response):
        # Patch the specific imported names in the open_meteo module
        with patch("app.infrastructure.rainfall.open_meteo.datetime") as mock_dt, \
             patch("app.infrastructure.rainfall.open_meteo.timezone") as mock_tz, \
             patch("app.infrastructure.rainfall.open_meteo.timedelta") as mock_td:
            # Configure the mocked datetime class
            mock_dt.now.return_value = datetime(2026, 9, 3, 12, 0, 0, tzinfo=timezone.utc)
            mock_dt.fromisoformat = datetime.fromisoformat
            # Configure the mocked timezone class
            mock_tz.utc = timezone.utc
            # Configure the mocked timedelta class
            mock_td.side_effect = lambda *args, **kwargs: timedelta(*args, **kwargs)

            series = await adapter.fetch(use_cache=False)

        assert len(series.records) == 6
        assert series.source == "open-meteo"
        assert series.acquired_at is not None

        # Check first record
        rec = series.records[0]
        assert rec.timestamp.year == 2026
        assert rec.timestamp.month == 9
        assert rec.timestamp.day == 3
        assert rec.timestamp.hour == 18
        assert rec.timestamp.tzinfo == timezone.utc
        assert rec.interval_end == rec.timestamp + timedelta(hours=1)
        assert rec.rainfall_mm == 0.5
        assert rec.source == "open-meteo"
        assert rec.source_type == SourceType.FORECAST
        assert rec.resolution_minutes == 60
        assert rec.acquired_at.tzinfo == timezone.utc
        # With acquired_at at 2026-09-03 12:00:00 UTC and timestamp at 2026-09-03 18:30:00 UTC,
        # the lead time is 6 hours 30 minutes = 390 minutes.
        assert rec.forecast_lead_minutes == 390
        assert rec.status == RainfallStatus.LIVE

        # Check that the intensity is correctly derived (should be same as rainfall_mm for 1 hour)
        assert rec.average_intensity_mm_per_hour == 0.5


@pytest.mark.asyncio
async def test_cache_hit(adapter, fixture_data):
    """Test that cached data is returned on temporary failure."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = fixture_data
    mock_response.text = json.dumps(fixture_data)

    # Patch time and httpx in a scope that covers both priming and failure
    with patch("app.infrastructure.rainfall.open_meteo.datetime") as mock_dt, \
         patch("app.infrastructure.rainfall.open_meteo.timezone") as mock_tz, \
         patch("app.infrastructure.rainfall.open_meteo.timedelta") as mock_td:

        mock_dt.now.return_value = datetime(2026, 9, 3, 12, 0, 0, tzinfo=timezone.utc)
        mock_dt.fromisoformat = datetime.fromisoformat
        mock_tz.utc = timezone.utc
        mock_td.side_effect = lambda *args, **kwargs: timedelta(*args, **kwargs)

        # 1. Prime the cache
        with patch.object(httpx.AsyncClient, "get", return_value=mock_response):
            await adapter.fetch(use_cache=True)

        # 2. Simulate a failure
        with patch("httpx.AsyncClient.get", side_effect=httpx.TimeoutException("timeout")):
            series = await adapter.fetch(use_cache=True)

            # Should return stale data
            assert len(series.records) == 6
            for rec in series.records:
                assert rec.status == RainfallStatus.STALE


@pytest.mark.asyncio
async def test_timeout(adapter):
    """Test timeout raises the correct exception."""
    with patch.object(httpx.AsyncClient, "get", side_effect=httpx.TimeoutException("timeout")):
        with pytest.raises(RainfallAdapterTimeout) as excinfo:
            await adapter.fetch(use_cache=False)
        assert excinfo.value.timeout_seconds == 0.1


@pytest.mark.asyncio
async def test_http_error(adapter):
    """Test HTTP error status raises the correct exception."""
    mock_response = Mock()
    mock_response.status_code = 500
    mock_response.text = "Internal Server Error"

    with patch.object(httpx.AsyncClient, "get", return_value=mock_response):
        with pytest.raises(RainfallAdapterHTTPError) as excinfo:
            await adapter.fetch(use_cache=False)
        assert excinfo.value.status_code == 500


@pytest.mark.asyncio
async def test_parse_error(adapter):
    """Test malformed JSON raises parse error."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.side_effect = json.JSONDecodeError("Expecting value", "", 0)
    mock_response.text = "invalid json"

    with patch.object(httpx.AsyncClient, "get", return_value=mock_response):
        with pytest.raises(RainfallAdapterParseError):
            await adapter.fetch(use_cache=False)


@pytest.mark.asyncio
async def test_missing_field(adapter):
    """Test missing required field."""
    data = load_fixture()
    del data["hourly"]  # remove required field

    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = data
    mock_response.text = json.dumps(data)

    with patch.object(httpx.AsyncClient, "get", return_value=mock_response):
        with pytest.raises(RainfallAdapterMissingField) as excinfo:
            await adapter.fetch(use_cache=False)
        assert "hourly" in str(excinfo.value)


@pytest.mark.asyncio
async def test_unit_mismatch(adapter):
    """Test wrong precipitation units."""
    data = load_fixture()
    data["hourly_units"]["precipitation"] = "cm"  # wrong unit

    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = data
    mock_response.text = json.dumps(data)

    with patch.object(httpx.AsyncClient, "get", return_value=mock_response):
        with pytest.raises(RainfallAdapterUnitMismatch) as excinfo:
            await adapter.fetch(use_cache=False)
        assert "mm" in str(excinfo.value)
        assert "cm" in str(excinfo.value)


@pytest.mark.asyncio
async def test_timezone_mismatch(adapter):
    """Test unexpected timezone."""
    data = load_fixture()
    data["timezone"] = "UTC"  # wrong timezone

    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = data
    mock_response.text = json.dumps(data)

    with patch.object(httpx.AsyncClient, "get", return_value=mock_response):
        with pytest.raises(RainfallAdapterTimezoneMismatch) as excinfo:
            await adapter.fetch(use_cache=False)
        assert "Asia/Kolkata" in str(excinfo.value)
        assert "UTC" in str(excinfo.value)


@pytest.mark.asyncio
async def test_empty_forecast(adapter):
    """Test empty precipitation array."""
    data = load_fixture()
    data["hourly"]["precipitation"] = []

    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = data
    mock_response.text = json.dumps(data)

    with patch.object(httpx.AsyncClient, "get", return_value=mock_response):
        with pytest.raises(RainfallAdapterEmptyForecast):
            await adapter.fetch(use_cache=False)


@pytest.mark.asyncio
async def test_invalid_timestamp(adapter):
    """Test invalid timestamp in the response."""
    data = load_fixture()
    data["hourly"]["time"][0] = "not-a-timestamp"

    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = data
    mock_response.text = json.dumps(data)

    with patch.object(httpx.AsyncClient, "get", return_value=mock_response):
        with pytest.raises(RainfallAdapterInvalidTimestamp):
            await adapter.fetch(use_cache=False)


@pytest.mark.asyncio
async def test_cache_fresh_returns_data(adapter, fixture_data):
    """Test that fresh cache returns cached data."""
    # Populate cache with current time
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = fixture_data
    mock_response.text = json.dumps(fixture_data)

    with patch.object(httpx.AsyncClient, "get", return_value=mock_response):
        # Patch time to control cache timestamp
        with patch("app.infrastructure.rainfall.open_meteo.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2026, 9, 3, 12, 0, 0, tzinfo=timezone.utc)
            mock_dt.fromisoformat = datetime.fromisoformat
            mock_dt.timezone.utc = timezone.utc
            mock_dt.timedelta.side_effect = lambda *args, **kwargs: timedelta(*args, **kwargs)

            # Prime the cache
            await adapter.fetch(use_cache=True)

            # Immediately try to get from cache (should return fresh data)
            with patch.object(httpx.AsyncClient, "get", side_effect=httpx.TimeoutException("timeout")):
                series = await adapter.fetch(use_cache=True)
                assert len(series.records) == 6
                # Should be STALE because use_cache=True returns stale data on failure
                for rec in series.records:
                    assert rec.status == RainfallStatus.STALE


@pytest.mark.asyncio
async def test_cache_expired_returns_none(adapter, fixture_data):
    """Test that expired cache returns None."""
    # Populate cache with old time
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = fixture_data
    mock_response.text = json.dumps(fixture_data)

    with patch.object(httpx.AsyncClient, "get", return_value=mock_response):
        # Patch time to set old cache timestamp
        with patch("app.infrastructure.rainfall.open_meteo.datetime") as mock_dt:
            # Set cache time to 31 minutes ago (expired)
            mock_dt.now.return_value = datetime(2026, 9, 3, 12, 0, 0, tzinfo=timezone.utc)
            mock_dt.fromisoformat = datetime.fromisoformat
            mock_dt.timezone.utc = timezone.utc
            mock_dt.timedelta.side_effect = lambda *args, **kwargs: timedelta(*args, **kwargs)

            # Prime the cache (this sets _timestamp)
            await adapter.fetch(use_cache=True)

            # Now advance time by 31 minutes to make cache expired
            mock_dt.now.return_value = datetime(2026, 9, 3, 12, 31, 0, tzinfo=timezone.utc)

            # Try to get from cache (should return None because expired)
            cached = adapter.cache.get()
            assert cached is None


@pytest.mark.asyncio
async def test_cache_empty_returns_none(adapter):
    """Test that empty cache returns None."""
    # Cache starts empty
    cached = adapter.cache.get()
    assert cached is None


@pytest.mark.asyncio
async def test_skips_elapsed_intervals_and_handles_active_hour(adapter):
    """Test that intervals ending before acquired_at are skipped, and active hour gets lead_minutes=0."""
    data = load_fixture()
    # In fixture, timestamps are 2026-09-04T00:00, 01:00, 02:00, 03:00, 04:00, 05:00 local time
    # In Asia/Kolkata (UTC+5:30):
    # 2026-09-04T00:00 local = 2026-09-03 18:30 UTC -> interval [18:30, 19:30 UTC)
    # 2026-09-04T01:00 local = 2026-09-03 19:30 UTC -> interval [19:30, 20:30 UTC)
    # 2026-09-04T02:00 local = 2026-09-03 20:30 UTC -> interval [20:30, 21:30 UTC)
    #
    # Set acquired_at to 2026-09-03 20:00:00 UTC:
    # - Record 0: ends 19:30 <= 20:00 -> elapsed, should be SKIPPED
    # - Record 1: starts 19:30, ends 20:30 -> ACTIVE interval (19:30 <= 20:00 < 20:30), lead_minutes should be 0
    # - Record 2: starts 20:30, ends 21:30 -> FUTURE interval, lead_minutes = 30
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = data
    mock_response.text = json.dumps(data)

    with patch.object(httpx.AsyncClient, "get", return_value=mock_response):
        with patch("app.infrastructure.rainfall.open_meteo.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2026, 9, 3, 20, 0, 0, tzinfo=timezone.utc)
            mock_dt.fromisoformat = datetime.fromisoformat
            mock_dt.timezone.utc = timezone.utc
            mock_dt.timedelta.side_effect = lambda *args, **kwargs: timedelta(*args, **kwargs)

            series = await adapter.fetch(use_cache=False)

    # 1 record skipped, 5 remaining
    assert len(series.records) == 5
    # First record should now be the active hour (Record 1)
    active_rec = series.records[0]
    assert active_rec.forecast_lead_minutes == 0
    assert active_rec.timestamp == datetime(2026, 9, 3, 19, 30, 0, tzinfo=timezone.utc)
    # Next record is future
    future_rec = series.records[1]
    assert future_rec.forecast_lead_minutes == 30


@pytest.mark.asyncio
async def test_all_elapsed_records_raises_empty_forecast(adapter):
    """Test that if all records in payload have elapsed, RainfallAdapterEmptyForecast is raised."""
    data = load_fixture()
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = data
    mock_response.text = json.dumps(data)

    # Set acquired_at far in the future so all records are elapsed
    with patch.object(httpx.AsyncClient, "get", return_value=mock_response):
        with patch("app.infrastructure.rainfall.open_meteo.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2026, 9, 10, 12, 0, 0, tzinfo=timezone.utc)
            mock_dt.fromisoformat = datetime.fromisoformat
            mock_dt.timezone.utc = timezone.utc
            mock_dt.timedelta.side_effect = lambda *args, **kwargs: timedelta(*args, **kwargs)

            with pytest.raises(RainfallAdapterEmptyForecast):
                await adapter.fetch(use_cache=False)