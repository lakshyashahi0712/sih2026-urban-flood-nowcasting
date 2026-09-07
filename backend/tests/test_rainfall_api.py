"""Tests for the rainfall API endpoints."""
from __future__ import annotations

from datetime import datetime, timezone
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
    """Test the rainfall status endpoint."""
    response = client.get("/rainfall/mumbai/status")
    assert response.status_code == 200
    data = response.json()
    assert "cache_status" in data
    assert "source" in data
    assert data["source"] == "open-meteo"


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

