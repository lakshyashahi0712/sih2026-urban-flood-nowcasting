"""Tests for the Mesonet adapter."""
from __future__ import annotations

from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, Mock, patch
import httpx
import pytest

try:
    from backend.app.infrastructure.rainfall.mesonet import (
        MesonetAdapter,
        MesonetAdapterTimeout,
        MesonetAdapterHTTPError,
        MesonetAdapterParseError,
        MesonetAdapterMissingField,
        MesonetAdapterUnitMismatch,
        MesonetAdapterInvalidTimestamp,
        MesonetAdapterNoDataAvailable,
    )
    from backend.app.domain.rainfall.models import (
        RainfallRecord,
        RainfallSeries,
        RainfallStatus,
        SourceType,
    )
except ImportError:
    from app.infrastructure.rainfall.mesonet import (
        MesonetAdapter,
        MesonetAdapterTimeout,
        MesonetAdapterHTTPError,
        MesonetAdapterParseError,
        MesonetAdapterMissingField,
        MesonetAdapterUnitMismatch,
        MesonetAdapterInvalidTimestamp,
        MesonetAdapterNoDataAvailable,
    )
    from app.domain.rainfall.models import (
        RainfallRecord,
        RainfallSeries,
        RainfallStatus,
        SourceType,
    )


@pytest.fixture
def mesonet_adapter():
    return MesonetAdapter(timeout=1.0)


@pytest.mark.asyncio
async def test_fetch_live_success(mesonet_adapter):
    """Test successful fetch and normalization of Mesonet data."""
    fresh_timestamp = (datetime.now(timezone.utc) - timedelta(minutes=10)).isoformat()
    mock_response = {
        "stations": [
            {
                "id": "STN001",
                "lat": 19.0760,
                "lon": 72.8777,
                "timestamp": fresh_timestamp,
                "units": {"precipitation": "mm"},
                "precipitation_15min": [0.0, 0.0, 0.0, 0.5],  # Last hour: 0.5 mm total
            },
            {
                "id": "STN002",
                "lat": 19.1342,
                "lon": 72.8672,
                "timestamp": fresh_timestamp,
                "units": {"precipitation": "mm"},
                "precipitation_15min": [0.2, 0.2, 0.2, 0.2],  # Last hour: 0.8 mm total
            },
        ]
    }

    mock_http_response = Mock()
    mock_http_response.status_code = 200
    mock_http_response.json.return_value = mock_response
    mock_http_response.text = str(mock_response)

    with patch.object(httpx.AsyncClient, "get", return_value=mock_http_response):
        series = await mesonet_adapter.fetch(use_cache=False)
        assert len(series.records) > 0
        assert series.source == "mumbai-mesonet"
        for rec in series.records:
            assert rec.source == "mumbai-mesonet"
            assert rec.source_type == SourceType.OBSERVATION
            assert rec.resolution_minutes == 60
            assert rec.rainfall_mm >= 0.0


@pytest.mark.asyncio
async def test_fetch_live_stale_data(mesonet_adapter):
    """Test that stale data is skipped."""
    now = datetime.now(timezone.utc)
    stale_time = now - timedelta(minutes=45)  # Older than MAX_STALENESS_MINUTES (30)
    mock_response = {
        "stations": [
            {
                "id": "STN001",
                "lat": 19.0760,
                "lon": 72.8777,
                "timestamp": stale_time.isoformat(),
                "units": {"precipitation": "mm"},
                "precipitation_15min": [1.0, 1.0, 1.0, 1.0],
            }
        ]
    }

    mock_http_response = Mock()
    mock_http_response.status_code = 200
    mock_http_response.json.return_value = mock_response
    mock_http_response.text = str(mock_response)

    with patch.object(httpx.AsyncClient, "get", return_value=mock_http_response):
        # Should raise NoDataAvailable because the only station is stale
        with pytest.raises(MesonetAdapterNoDataAvailable):
            await mesonet_adapter.fetch(use_cache=False)


@pytest.mark.asyncio
async def test_fetch_live_missing_station_id(mesonet_adapter):
    """Test handling of missing station ID."""
    mock_response = {
        "stations": [
            {
                "lat": 19.0760,
                "lon": 72.8777,
                "timestamp": "2026-09-05T13:00:00Z",
                "units": {"precipitation": "mm"},
                "precipitation_15min": [0.5, 0.5, 0.5, 0.5],
            }
        ]
    }

    mock_http_response = Mock()
    mock_http_response.status_code = 200
    mock_http_response.json.return_value = mock_response
    mock_http_response.text = str(mock_response)

    with patch.object(httpx.AsyncClient, "get", return_value=mock_http_response):
        # Should raise NoDataAvailable because no valid station ID
        with pytest.raises(MesonetAdapterNoDataAvailable):
            await mesonet_adapter.fetch(use_cache=False)


@pytest.mark.asyncio
async def test_fetch_live_invalid_units(mesonet_adapter):
    """Test handling of invalid precipitation units."""
    fresh_timestamp = (datetime.now(timezone.utc) - timedelta(minutes=10)).isoformat()
    mock_response = {
        "stations": [
            {
                "id": "STN001",
                "lat": 19.0760,
                "lon": 72.8777,
                "timestamp": fresh_timestamp,
                "units": {"precipitation": "cm"},  # Should be mm
                "precipitation_15min": [0.5, 0.5, 0.5, 0.5],
            }
        ]
    }

    mock_http_response = Mock()
    mock_http_response.status_code = 200
    mock_http_response.json.return_value = mock_response
    mock_http_response.text = str(mock_response)

    with patch.object(httpx.AsyncClient, "get", return_value=mock_http_response):
        with pytest.raises(MesonetAdapterUnitMismatch):
            await mesonet_adapter.fetch(use_cache=False)


@pytest.mark.asyncio
async def test_fetch_live_invalid_timestamp(mesonet_adapter):
    """Invalid timestamp on the only station -> skipped -> no valid data."""
    mock_response = {
        "stations": [
            {
                "id": "STN001",
                "lat": 19.0760,
                "lon": 72.8777,
                "timestamp": "not-a-timestamp",
                "units": {"precipitation": "mm"},
                "precipitation_15min": [0.5, 0.5, 0.5, 0.5],
            }
        ]
    }

    mock_http_response = Mock()
    mock_http_response.status_code = 200
    mock_http_response.json.return_value = mock_response
    mock_http_response.text = str(mock_response)

    with patch("httpx.AsyncClient") as mock_client:
        mock_instance = AsyncMock()
        mock_instance.get = AsyncMock(return_value=mock_http_response)
        mock_client.return_value.__aenter__.return_value = mock_instance

        with pytest.raises(MesonetAdapterNoDataAvailable):
            await mesonet_adapter.fetch(use_cache=False)

@pytest.mark.asyncio
async def test_fetch_use_cache_on_failure(mesonet_adapter):
    """Test that when use_cache=True and live fails, cached data is returned if available."""
    # First, populate the cache with some data
    cached_series = RainfallSeries(
        records=[
            RainfallRecord(
                timestamp=datetime(2026, 9, 5, 12, 0, tzinfo=timezone.utc),
                interval_end=datetime(2026, 9, 5, 13, 0, tzinfo=timezone.utc),
                rainfall_mm=1.0,
                source="mumbai-mesonet",
                source_type=SourceType.OBSERVATION,
                resolution_minutes=60,
                acquired_at=datetime(2026, 9, 5, 12, 0, tzinfo=timezone.utc),
                forecast_lead_minutes=0,
                status=RainfallStatus.LIVE,
            )
        ],
        source="mumbai-mesonet",
        acquired_at=datetime(2026, 9, 5, 12, 0, tzinfo=timezone.utc),
    )
    mesonet_adapter.cache.set(cached_series)

    # Now, make the live call fail
    with patch("httpx.AsyncClient") as mock_client:
        mock_instance = AsyncMock()
        mock_instance.get.side_effect = Exception("Network error")
        mock_client.return_value.__aenter__.return_value = mock_instance

        series = await mesonet_adapter.fetch(use_cache=True)
        expected_series = mesonet_adapter._make_stale_series(cached_series)
        assert series == expected_series
        assert series.records[0].status == RainfallStatus.STALE


@pytest.mark.asyncio
async def test_fetch_use_cache_no_cache(mesonet_adapter):
    """Test that when use_cache=True and no cache is available, the exception is propagated."""
    with patch("httpx.AsyncClient") as mock_client:
        mock_instance = AsyncMock()
        mock_instance.get.side_effect = Exception("Network error")
        mock_client.return_value.__aenter__.return_value = mock_instance

        with pytest.raises(Exception):
            await mesonet_adapter.fetch(use_cache=True)


@pytest.mark.asyncio
async def test_fetch_live_multiple_observation_windows(mesonet_adapter):
    """Test that multi-window observation parsing works (1h fallback when 15min absent)."""
    fresh_timestamp = (datetime.now(timezone.utc) - timedelta(minutes=10)).isoformat()
    mock_response = {
        "stations": [
            {
                "id": "STN001",
                "lat": 19.0760,
                "lon": 72.8777,
                "timestamp": fresh_timestamp,
                "units": {"precipitation": "mm"},
                "precipitation_1h": [1.5, 2.0, 0.5],  # 3 hours of hourly data
            }
        ]
    }

    mock_http_response = Mock()
    mock_http_response.status_code = 200
    mock_http_response.json.return_value = mock_response
    mock_http_response.text = str(mock_response)

    with patch.object(httpx.AsyncClient, "get", return_value=mock_http_response):
        series = await mesonet_adapter.fetch(use_cache=False)
        assert len(series.records) > 0
        assert series.source == "mumbai-mesonet"
        # Verify the records contain hourly data
        for rec in series.records:
            assert rec.source_type == SourceType.OBSERVATION
            assert rec.resolution_minutes == 60


@pytest.mark.asyncio
async def test_fetch_live_staleness_boundary(mesonet_adapter):
    """Test exactly at the 30-minute staleness boundary."""
    now = datetime.now(timezone.utc)
    # Just under 30 minutes old -> should be accepted (boundary is > 30)
    # Use 29m58s to avoid flakiness from microsecond clock drift
    boundary_time = now - timedelta(minutes=29, seconds=58)
    mock_response = {
        "stations": [
            {
                "id": "STN001",
                "lat": 19.0760,
                "lon": 72.8777,
                "timestamp": boundary_time.isoformat(),
                "units": {"precipitation": "mm"},
                "precipitation_15min": [0.5, 0.5, 0.5, 0.5],
            }
        ]
    }

    mock_http_response = Mock()
    mock_http_response.status_code = 200
    mock_http_response.json.return_value = mock_response
    mock_http_response.text = str(mock_response)

    with patch.object(httpx.AsyncClient, "get", return_value=mock_http_response):
        # At exactly 30 minutes, the condition is age > 30, so this should succeed
        series = await mesonet_adapter.fetch(use_cache=False)
        assert len(series.records) > 0