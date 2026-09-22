"""Tests for the rainfall API endpoints."""
from __future__ import annotations

from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, patch
import pytest
from fastapi.testclient import TestClient

try:
    from backend.main import app
    from backend.app.api.rainfall import get_adapter, get_mesonet_adapter
    from backend.app.domain.rainfall.models import (
        RainfallRecord,
        RainfallSeries,
        RainfallStatus,
        SourceType,
        RainfallProvenance,
    )
except ImportError:
    from main import app
    from app.api.rainfall import get_adapter, get_mesonet_adapter
    from app.domain.rainfall.models import (
        RainfallRecord,
        RainfallSeries,
        RainfallStatus,
        SourceType,
        RainfallProvenance,
    )

client = TestClient(app)


def test_get_mumbai_rainfall_success():
    """Test successful retrieval and serialization of normalized rainfall series."""
    rec = RainfallRecord(
        timestamp=datetime(2026, 9, 5, 13, 0, tzinfo=timezone.utc),
        interval_end=datetime(2026, 9, 5, 14, 0, tzinfo=timezone.utc),
        rainfall_mm=1.5,
        source="open-meteo",
        source_type=SourceType.FORECAST,
        resolution_minutes=60,
        acquired_at=datetime(2026, 9, 5, 13, 0, tzinfo=timezone.utc),
        forecast_lead_minutes=0,
        status=RainfallStatus.LIVE,
    )
    series = RainfallSeries(records=[rec], source="open-meteo", acquired_at=rec.acquired_at)

    adapter = get_adapter()
    with patch.object(adapter, "fetch", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = series
        response = client.get("/rainfall/mumbai")

    assert response.status_code == 200
    data = response.json()
    assert data["source"] == "open-meteo"
    assert data["record_count"] == 1
    assert data["resolution_minutes"] == 60
    assert len(data["records"]) == 1

    r0 = data["records"][0]
    assert r0["rainfall_mm"] == 1.5
    assert r0["source"] == "open-meteo"
    assert r0["source_type"] == "forecast"
    assert r0["resolution_minutes"] == 60
    assert r0["status"] == "LIVE"
    assert r0["forecast_lead_minutes"] == 0


def test_get_mumbai_rainfall_status_endpoint():
    """Test the rainfall status endpoint reports fallback state accurately on startup."""
    adapter = get_adapter()
    old_data = adapter.cache._data
    old_ts = adapter.cache._timestamp
    try:
        adapter.cache._data = None
        adapter.cache._timestamp = None
        response = client.get("/rainfall/mumbai/status")
        assert response.status_code == 200
        data = response.json()
        assert data["source"] == "open-meteo"
        assert data["cache_status"] == "FALLBACK_SNAPSHOT"
        assert data["provenance"] == "FALLBACK_CACHED_FORECAST"
        assert data["available_source"] == "BUNDLED_FALLBACK_SNAPSHOT"
        assert data["has_fallback"] is True
        assert data["fallback_available"] is True
        assert data["cached_at"] is None
        assert data["fallback_acquired_at"] is not None
        assert data["is_stale"] is True
    finally:
        adapter.cache._data = old_data
        adapter.cache._timestamp = old_ts


def test_mumbai_rainfall_status_reflects_live_fresh_cache():
    """Test that /rainfall/mumbai/status reports LIVE and NWP_FALLBACK when fresh in-memory data is cached."""
    adapter = get_adapter()
    now = datetime.now(timezone.utc)
    rec = RainfallRecord(
        timestamp=now,
        interval_end=now + timedelta(hours=1),
        rainfall_mm=2.5,
        source="open-meteo",
        source_type=SourceType.FORECAST,
        resolution_minutes=60,
        acquired_at=now,
        forecast_lead_minutes=0,
        status=RainfallStatus.LIVE,
        provenance=RainfallProvenance.NWP_FALLBACK,
    )
    live_series = RainfallSeries(
        records=[rec],
        source="open-meteo",
        acquired_at=now,
        provenance=RainfallProvenance.NWP_FALLBACK,
    )

    old_data = adapter.cache._data
    old_ts = adapter.cache._timestamp
    old_status = adapter.last_live_status
    try:
        adapter.cache.set(live_series)
        adapter.last_live_status = "SUCCESS"

        response = client.get("/rainfall/mumbai/status")
        assert response.status_code == 200
        data = response.json()
        assert data["cache_status"] == "LIVE"
        assert data["provenance"] == "NWP_FALLBACK"
        assert data["available_source"] == "IN_MEMORY_FRESH_CACHE"
        assert data["cached_at"] is not None
        assert data["is_stale"] is False
        assert data["last_live_status"] == "SUCCESS"
    finally:
        adapter.cache._data = old_data
        adapter.cache._timestamp = old_ts
        adapter.last_live_status = old_status


def test_mumbai_rainfall_status_reflects_stale_memory_cache():
    """Test that /rainfall/mumbai/status reports STALE and FALLBACK_CACHED_FORECAST when in-memory cache is expired."""
    adapter = get_adapter()
    past = datetime.now(timezone.utc) - timedelta(minutes=45)
    rec = RainfallRecord(
        timestamp=past,
        interval_end=past + timedelta(hours=1),
        rainfall_mm=1.0,
        source="open-meteo",
        source_type=SourceType.FORECAST,
        resolution_minutes=60,
        acquired_at=past,
        forecast_lead_minutes=0,
        status=RainfallStatus.LIVE,
    )
    series = RainfallSeries(records=[rec], source="open-meteo", acquired_at=past)

    old_data = adapter.cache._data
    old_ts = adapter.cache._timestamp
    try:
        adapter.cache.set(series)
        # Manually backdate timestamp past TTL (30 min)
        adapter.cache._timestamp = past

        response = client.get("/rainfall/mumbai/status")
        assert response.status_code == 200
        data = response.json()
        assert data["cache_status"] == "STALE"
        assert data["provenance"] == "FALLBACK_CACHED_FORECAST"
        assert data["available_source"] == "IN_MEMORY_STALE_CACHE"
        assert data["is_stale"] is True
        assert data["cached_at"] is not None
    finally:
        adapter.cache._data = old_data
        adapter.cache._timestamp = old_ts


def test_mumbai_rainfall_status_tracks_live_rate_limit():
    """Test that status reflects RATE_LIMITED after an upstream 429 encountered during fetch."""
    adapter = get_adapter()
    mock_resp = patch("httpx.AsyncClient.get")
    old_data = adapter.cache._data
    old_ts = adapter.cache._timestamp
    old_status = adapter.last_live_status
    old_err = adapter.last_live_error
    try:
        adapter.cache._data = None
        adapter.cache._timestamp = None

        mock_obj = AsyncMock()
        mock_obj.status_code = 429
        mock_obj.text = '{"error": true, "reason": "Daily rate limit exceeded"}'

        with patch("httpx.AsyncClient.get", return_value=mock_obj):
            # Fetch engages fallback
            resp = client.get("/rainfall/mumbai")
            assert resp.status_code == 200
            assert resp.json()["provenance"] == "FALLBACK_CACHED_FORECAST"

        # Now check status endpoint
        status_resp = client.get("/rainfall/mumbai/status")
        assert status_resp.status_code == 200
        sdata = status_resp.json()
        assert sdata["cache_status"] == "FALLBACK_SNAPSHOT"
        assert sdata["provenance"] == "FALLBACK_CACHED_FORECAST"
        assert sdata["available_source"] == "BUNDLED_FALLBACK_SNAPSHOT"
        assert sdata["last_live_status"] == "RATE_LIMITED"
        assert "429" in sdata["last_live_error"]
    finally:
        adapter.cache._data = old_data
        adapter.cache._timestamp = old_ts
        adapter.last_live_status = old_status
        adapter.last_live_error = old_err


def test_mumbai_rainfall_status_empty_when_no_fallback():
    """Test that status reports EMPTY and UNAVAILABLE when neither in-memory cache nor fallback snapshot exists."""
    adapter = get_adapter()
    old_data = adapter.cache._data
    old_ts = adapter.cache._timestamp
    old_fb = adapter.cache._fallback
    try:
        adapter.cache._data = None
        adapter.cache._timestamp = None
        adapter.cache._fallback = None

        response = client.get("/rainfall/mumbai/status")
        assert response.status_code == 200
        data = response.json()
        assert data["cache_status"] == "EMPTY"
        assert data["provenance"] == "UNAVAILABLE"
        assert data["available_source"] == "UNAVAILABLE"
        assert data["has_fallback"] is False
        assert data["fallback_available"] is False
    finally:
        adapter.cache._data = old_data
        adapter.cache._timestamp = old_ts
        adapter.cache._fallback = old_fb


def test_get_mumbai_rainfall_error_returns_503():
    """Test that adapter failure returns HTTP 503."""
    adapter = get_adapter()
    with patch.object(adapter, "fetch", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.side_effect = RuntimeError("Open-Meteo unreachable")
        response = client.get("/rainfall/mumbai")

    assert response.status_code == 503
    assert "Rainfall adapter error" in response.json()["detail"]


def test_get_rainfall_bias_success():
    """Test /rainfall/bias endpoint when both sources are available."""
    t = datetime(2026, 9, 5, 12, 0, tzinfo=timezone.utc)
    mesonet_rec = RainfallRecord(
        timestamp=t,
        interval_end=datetime(2026, 9, 5, 13, 0, tzinfo=timezone.utc),
        rainfall_mm=3.0,
        source="mumbai-mesonet",
        source_type=SourceType.OBSERVATION,
        resolution_minutes=60,
        acquired_at=t,
        forecast_lead_minutes=0,
        status=RainfallStatus.LIVE,
        provenance=RainfallProvenance.MESONET,
    )
    mesonet_series = RainfallSeries(
        records=[mesonet_rec], source="mumbai-mesonet", acquired_at=t, provenance=RainfallProvenance.MESONET
    )

    nwp_rec = RainfallRecord(
        timestamp=t,
        interval_end=datetime(2026, 9, 5, 13, 0, tzinfo=timezone.utc),
        rainfall_mm=2.0,
        source="open-meteo",
        source_type=SourceType.FORECAST,
        resolution_minutes=60,
        acquired_at=t,
        forecast_lead_minutes=0,
        status=RainfallStatus.LIVE,
    )
    nwp_series = RainfallSeries(records=[nwp_rec], source="open-meteo", acquired_at=t)

    mesonet = get_mesonet_adapter()
    nwp = get_adapter()

    with patch.object(mesonet, "fetch", new_callable=AsyncMock) as mock_mesonet:
        with patch.object(nwp, "fetch", new_callable=AsyncMock) as mock_nwp:
            mock_mesonet.return_value = mesonet_series
            mock_nwp.return_value = nwp_series
            response = client.get("/rainfall/bias")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "OK"
    assert data["mesonet_available"] is True
    assert data["nwp_available"] is True
    assert data["matched_intervals"] == 1
    assert data["mean_error_mm"] == 1.0  # 3.0 - 2.0
    assert len(data["comparisons"]) == 1
    assert data["comparisons"][0]["observed_mm"] == 3.0
    assert data["comparisons"][0]["nwp_mm"] == 2.0
    assert data["comparisons"][0]["error_mm"] == 1.0


def test_get_rainfall_bias_unavailable():
    """Test /rainfall/bias endpoint when Mesonet fails."""
    mesonet = get_mesonet_adapter()
    nwp = get_adapter()

    with patch.object(mesonet, "fetch", new_callable=AsyncMock) as mock_mesonet:
        with patch.object(nwp, "fetch", new_callable=AsyncMock) as mock_nwp:
            mock_mesonet.side_effect = RuntimeError("Mesonet connection refused")
            mock_nwp.return_value = RainfallSeries(records=[], source="open-meteo")
            response = client.get("/rainfall/bias")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "UNAVAILABLE"
    assert data["mesonet_available"] is False
    assert "Mesonet connection refused" in data["mesonet_error"]

