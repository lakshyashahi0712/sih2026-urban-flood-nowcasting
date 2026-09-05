"""Tests for Phase 2.4 — IMD Doppler Radar Integration & Fallback.

Verifies:
1. IMD Doppler Radar endpoint probing and live/mock diagnostics.
2. Format classification (visual GIF recognized as non-quantitative; zero fake numbers).
3. Quantitative spatial rainfall grid creation, validation, and properties.
4. Spatial clipping to Mumbai pilot extent (EPSG:32643).
5. Non-negative rainfall enforcement and nodata filtering.
6. UTC timezone handling and data staleness detection.
7. Graceful error and timeout handling.
8. Composite provider automatic NWP fallback with strict provenance tracking.
9. Rational Method runoff volume conversion without modifying hydraulic formulas.
10. API endpoints for diagnostics and composite rainfall.
"""
from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Optional
from unittest.mock import AsyncMock, Mock, patch
import numpy as np
import pytest
from fastapi.testclient import TestClient
import httpx

try:
    from backend.main import app
    from backend.app.domain.rainfall.models import (
        RainfallRecord,
        RainfallSeries,
        RainfallStatus,
        SourceType,
    )
    from backend.app.domain.rainfall.radar_models import (
        RainfallProvenance,
        RadarProductType,
        RadarFormatType,
        RadarMetadata,
        SpatialRainfallGrid,
        MUMBAI_PILOT_BOUNDS_32643,
    )
    from backend.app.infrastructure.rainfall.imd_radar import (
        IMDRadarAdapter,
        IMDRadarProbeResult,
        IMD_ENDPOINTS,
        MAX_STALENESS_MINUTES,
    )
    from backend.app.infrastructure.rainfall.composite_provider import (
        CompositeRainfallProvider,
        CompositeRainfallResult,
    )
except ImportError:
    from main import app
    from app.domain.rainfall.models import (
        RainfallRecord,
        RainfallSeries,
        RainfallStatus,
        SourceType,
    )
    from app.domain.rainfall.radar_models import (
        RainfallProvenance,
        RadarProductType,
        RadarFormatType,
        RadarMetadata,
        SpatialRainfallGrid,
        MUMBAI_PILOT_BOUNDS_32643,
    )
    from app.infrastructure.rainfall.imd_radar import (
        IMDRadarAdapter,
        IMDRadarProbeResult,
        IMD_ENDPOINTS,
        MAX_STALENESS_MINUTES,
    )
    from app.infrastructure.rainfall.composite_provider import (
        CompositeRainfallProvider,
        CompositeRainfallResult,
    )

client = TestClient(app)


# ---------------------------------------------------------------------------
# 1. IMD Endpoint Probing & Diagnostics
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_imd_probe_endpoint_mock_success():
    """Verify endpoint probing with mock HTTP 200 GIF response."""
    adapter = IMDRadarAdapter(timeout=5.0)

    mock_resp = Mock()
    mock_resp.status_code = 200
    mock_resp.headers = {
        "content-type": "image/gif",
        "content-length": "1557166",
        "last-modified": "Sat, 05 Sep 2026 14:50:03 GMT",
    }

    mock_client = AsyncMock()
    mock_client.get.return_value = mock_resp

    res = await adapter.probe_endpoint("SRI_VRV", "https://mausam.imd.gov.in/Radar/sri_vrv.gif", client=mock_client)

    assert res.is_accessible is True
    assert res.http_status == 200
    assert res.content_type == "image/gif"
    assert res.content_length_bytes == 1557166
    assert res.last_modified is not None
    assert res.format_type == RadarFormatType.VISUAL_PALETTE_GIF
    assert res.is_quantitative is False
    assert "visual GIF" in res.diagnostic_message or "8-bit palette" in res.diagnostic_message


@pytest.mark.asyncio
async def test_imd_probe_endpoint_404_handling():
    """Verify handling of inactive/404 endpoints (e.g. Colaba station)."""
    adapter = IMDRadarAdapter(timeout=5.0)

    mock_resp = Mock()
    mock_resp.status_code = 404
    mock_resp.headers = {"content-type": "text/html"}

    mock_client = AsyncMock()
    mock_client.get.return_value = mock_resp

    res = await adapter.probe_endpoint("SRI_CLB", "https://mausam.imd.gov.in/Radar/sri_clb.gif", client=mock_client)

    assert res.is_accessible is False
    assert res.http_status == 404
    assert res.is_quantitative is False
    assert "HTTP 404" in res.diagnostic_message


@pytest.mark.asyncio
async def test_imd_probe_endpoint_timeout_handling():
    """Verify timeout handling returns clean diagnostic probe."""
    adapter = IMDRadarAdapter(timeout=1.0)

    mock_client = AsyncMock()
    mock_client.get.side_effect = httpx.TimeoutException("Connection timed out")

    res = await adapter.probe_endpoint("SRI_VRV", "https://mausam.imd.gov.in/Radar/sri_vrv.gif", client=mock_client)

    assert res.is_accessible is False
    assert res.http_status == 504
    assert "timed out" in res.diagnostic_message


# ---------------------------------------------------------------------------
# 2. Format Classification & Zero Fake Numbers Policy
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_format_classification_visual_gif_zero_fake_numbers():
    """Verify that visual GIF endpoints never fabricate quantitative precipitation numbers."""
    adapter = IMDRadarAdapter()

    mock_resp = Mock()
    mock_resp.status_code = 200
    mock_resp.headers = {
        "content-type": "image/gif",
        "content-length": "1637236",
        "last-modified": "Sat, 05 Sep 2026 14:50:04 GMT",
    }
    mock_client = AsyncMock()
    mock_client.get.return_value = mock_resp

    grid, probe = await adapter.fetch_radar_grid(client=mock_client)

    # Grid must be None because data is non-quantitative visual GIF
    assert grid is None
    assert probe.is_quantitative is False
    assert probe.format_type == RadarFormatType.VISUAL_PALETTE_GIF
    assert "NWP fallback" in probe.diagnostic_message


@pytest.mark.asyncio
async def test_check_live_status_full_report_structure():
    """Verify check_live_status returns structured diagnostic report."""
    adapter = IMDRadarAdapter()

    with patch.object(adapter, "probe_endpoint") as mock_probe:
        mock_probe.return_value = IMDRadarProbeResult(
            endpoint_key="SRI_VRV",
            endpoint_url="https://mausam.imd.gov.in/Radar/sri_vrv.gif",
            http_status=200,
            content_type="image/gif",
            content_length_bytes=1557166,
            last_modified=datetime(2026, 9, 5, 14, 50, tzinfo=timezone.utc),
            age_minutes=15.0,
            is_accessible=True,
            format_type=RadarFormatType.VISUAL_PALETTE_GIF,
            is_quantitative=False,
            diagnostic_message="Visual palette GIF",
        )

        status_report = await adapter.check_live_status()

    assert "radar_network" in status_report
    assert "stations" in status_report
    assert "VRV" in status_report["stations"]
    assert "CLB" in status_report["stations"]
    assert "format_assessment" in status_report
    assert status_report["format_assessment"]["is_quantitative_precipitation"] is False
    assert "institutional_data_gateway" in status_report
    assert "system_behavior" in status_report
    assert status_report["system_behavior"]["operational_mode"] == "NWP_FALLBACK_ACTIVE"


# ---------------------------------------------------------------------------
# 3. Quantitative Spatial Rainfall Grid & Pilot Alignment
# ---------------------------------------------------------------------------

def test_spatial_rainfall_grid_properties_and_mean():
    """Verify creation, validation, and statistics of SpatialRainfallGrid."""
    # 3x3 grid with known values and one nodata cell (-9999.0)
    data = [
        [10.0, 20.0, 30.0],
        [40.0, -9999.0, 50.0],
        [60.0, 70.0, 80.0],
    ]
    bounds = (274000.0, 2108000.0, 274090.0, 2108090.0)
    ts = datetime(2026, 9, 5, 12, 0, tzinfo=timezone.utc)

    grid = SpatialRainfallGrid(
        values=data,
        bounds_32643=bounds,
        resolution_m=30.0,
        timestamp=ts,
        duration_hours=1.0,
        provenance=RainfallProvenance.RADAR,
    )

    assert grid.rows == 3
    assert grid.cols == 3
    assert grid.provenance == RainfallProvenance.RADAR

    # Mean excluding -9999.0: (10 + 20 + 30 + 40 + 50 + 60 + 70 + 80) / 8 = 360 / 8 = 45.0
    assert pytest.approx(grid.mean_rainfall_mm(), abs=1e-5) == 45.0
    assert pytest.approx(grid.max_rainfall_mm(), abs=1e-5) == 80.0


def test_spatial_clipping_to_mumbai_pilot_extent():
    """Verify spatial clipping of regional grid to Mumbai pilot extent (EPSG:32643)."""
    # Create regional grid enclosing Mumbai pilot bounds:
    # Pilot is [274271.486, 2108306.785, 278531.486, 2112116.785]
    # Regional: min_x=270000, max_x=285000, min_y=2105000, max_y=2115000 (res=100m)
    res = 100.0
    reg_min_x, reg_max_x = 270000.0, 285000.0  # 15,000m -> 150 cols
    reg_min_y, reg_max_y = 2105000.0, 2115000.0  # 10,000m -> 100 rows

    rows = int((reg_max_y - reg_min_y) / res)
    cols = int((reg_max_x - reg_min_x) / res)

    # Gradient rainfall across region
    data = np.full((rows, cols), 25.0, dtype=float)

    grid = SpatialRainfallGrid(
        values=data,
        bounds_32643=(reg_min_x, reg_min_y, reg_max_x, reg_max_y),
        resolution_m=res,
        timestamp=datetime.now(timezone.utc),
        duration_hours=1.0,
        provenance=RainfallProvenance.RADAR,
    )

    clipped = grid.clip_to_bounds(MUMBAI_PILOT_BOUNDS_32643)

    c_min_x, c_min_y, c_max_x, c_max_y = clipped.bounds_32643
    p_min_x, p_min_y, p_max_x, p_max_y = MUMBAI_PILOT_BOUNDS_32643

    # Clipped bounds should tightly cover the pilot extent within 1 resolution cell
    assert c_min_x <= p_min_x
    assert c_max_x >= p_max_x
    assert c_min_y <= p_min_y
    assert c_max_y >= p_max_y
    assert clipped.mean_rainfall_mm() == 25.0


def test_spatial_clipping_disjoint_bounds_raises_error():
    """Verify clipping to disjoint bounding box raises clear error."""
    grid = SpatialRainfallGrid(
        values=[[5.0]],
        bounds_32643=(100.0, 100.0, 200.0, 200.0),
        resolution_m=100.0,
        timestamp=datetime.now(timezone.utc),
    )
    disjoint_bounds = (500.0, 500.0, 600.0, 600.0)

    with pytest.raises(ValueError, match="do not intersect"):
        grid.clip_to_bounds(disjoint_bounds)


# ---------------------------------------------------------------------------
# 4. Non-Negative Rainfall & Validation Rules
# ---------------------------------------------------------------------------

def test_negative_rainfall_raises_value_error():
    """Verify negative rainfall values raise ValueError."""
    data = [[10.0, -2.5], [5.0, 0.0]]
    with pytest.raises(ValueError, match="Precipitation values cannot be negative"):
        SpatialRainfallGrid(
            values=data,
            bounds_32643=(0.0, 0.0, 20.0, 20.0),
            resolution_m=10.0,
            timestamp=datetime.now(timezone.utc),
        )


def test_invalid_bounds_raises_value_error():
    """Verify invalid bounds (max <= min) raise ValueError."""
    with pytest.raises(ValueError, match="greater than"):
        SpatialRainfallGrid(
            values=[[5.0]],
            bounds_32643=(100.0, 100.0, 50.0, 200.0),  # max_x < min_x
            resolution_m=10.0,
            timestamp=datetime.now(timezone.utc),
        )


def test_empty_grid_raises_value_error():
    """Verify empty grid array is rejected."""
    with pytest.raises(ValueError, match="cannot be empty"):
        SpatialRainfallGrid(
            values=[],
            bounds_32643=(0.0, 0.0, 10.0, 10.0),
            resolution_m=10.0,
            timestamp=datetime.now(timezone.utc),
        )


# ---------------------------------------------------------------------------
# 5. Staleness & Timestamps
# ---------------------------------------------------------------------------

def test_timestamp_utc_enforcement():
    """Verify timezone-naive string timestamps are handled or converted."""
    grid = SpatialRainfallGrid(
        values=[[1.0]],
        bounds_32643=(0.0, 0.0, 10.0, 10.0),
        resolution_m=10.0,
        timestamp="2026-09-05T12:00:00Z",
    )
    assert grid.timestamp.tzinfo == timezone.utc


def test_adapter_parses_quantitative_grid_with_staleness_check():
    """Verify parse_quantitative_grid handles fresh vs stale timestamps."""
    adapter = IMDRadarAdapter()

    fresh_ts = datetime.now(timezone.utc) - timedelta(minutes=15)
    stale_ts = datetime.now(timezone.utc) - timedelta(minutes=90)

    # Fresh parsing
    grid_fresh = adapter.parse_quantitative_grid(
        data_2d=np.ones((10, 10)) * 12.0,
        bounds_32643=(270000.0, 2100000.0, 280000.0, 2110000.0),
        resolution_m=1000.0,
        timestamp=fresh_ts,
    )
    assert grid_fresh.mean_rainfall_mm() == 12.0

    # Stale parsing logs warning but succeeds
    grid_stale = adapter.parse_quantitative_grid(
        data_2d=np.ones((10, 10)) * 5.0,
        bounds_32643=(270000.0, 2100000.0, 280000.0, 2110000.0),
        resolution_m=1000.0,
        timestamp=stale_ts,
        max_age_minutes=60,
    )
    assert grid_stale.mean_rainfall_mm() == 5.0


# ---------------------------------------------------------------------------
# 6. Composite Provider & Provenance Tracking
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_composite_provider_falls_back_to_nwp_when_radar_is_visual():
    """Verify composite provider triggers NWP fallback when radar is visual GIF only."""
    # Mock radar adapter returning non-quantitative visual GIF
    mock_radar = Mock(spec=IMDRadarAdapter)
    mock_probe = IMDRadarProbeResult(
        endpoint_key="SRI_VRV",
        endpoint_url="https://mausam.imd.gov.in/Radar/sri_vrv.gif",
        http_status=200,
        content_type="image/gif",
        format_type=RadarFormatType.VISUAL_PALETTE_GIF,
        is_quantitative=False,
        diagnostic_message="Public visual GIF only; triggering NWP fallback",
    )
    mock_radar.fetch_radar_grid = AsyncMock(return_value=(None, mock_probe))

    # Mock NWP adapter returning valid series
    rec = RainfallRecord(
        timestamp=datetime.now(timezone.utc),
        interval_end=datetime.now(timezone.utc) + timedelta(hours=1),
        rainfall_mm=14.5,
        source="open-meteo",
        source_type=SourceType.FORECAST,
        resolution_minutes=60,
        acquired_at=datetime.now(timezone.utc),
        forecast_lead_minutes=0,
        status=RainfallStatus.LIVE,
    )
    nwp_series = RainfallSeries(records=[rec], source="open-meteo", acquired_at=rec.acquired_at)

    mock_nwp = Mock()
    mock_nwp.fetch = AsyncMock(return_value=nwp_series)

    provider = CompositeRainfallProvider(radar_adapter=mock_radar, nwp_adapter=mock_nwp)
    result: CompositeRainfallResult = await provider.fetch_rainfall()

    assert result.provenance == RainfallProvenance.NWP_FALLBACK
    assert result.is_fallback is True
    assert "visual GIF" in result.fallback_reason
    assert result.series is not None
    assert len(result.series.records) == 1
    # Every record must have provenance NWP_FALLBACK
    assert result.series.records[0].provenance == RainfallProvenance.NWP_FALLBACK
    assert result.series.provenance == RainfallProvenance.NWP_FALLBACK


@pytest.mark.asyncio
async def test_composite_provider_uses_radar_when_quantitative():
    """Verify composite provider uses radar grid and tags RADAR provenance when quantitative grid is available."""
    grid = SpatialRainfallGrid(
        values=[[22.5]],
        bounds_32643=(274000.0, 2108000.0, 274100.0, 2108100.0),
        resolution_m=100.0,
        timestamp=datetime.now(timezone.utc),
        duration_hours=1.0,
        provenance=RainfallProvenance.RADAR,
    )
    mock_probe = IMDRadarProbeResult(
        endpoint_key="SRI_VRV",
        endpoint_url="https://api.imd.gov.in/radar/sri",
        http_status=200,
        content_type="application/x-netcdf",
        format_type=RadarFormatType.NETCDF4,
        is_quantitative=True,
        diagnostic_message="Quantitative radar feed",
    )

    mock_radar = Mock(spec=IMDRadarAdapter)
    mock_radar.fetch_radar_grid = AsyncMock(return_value=(grid, mock_probe))

    mock_nwp = Mock()
    mock_nwp.fetch = AsyncMock()  # should not be called

    provider = CompositeRainfallProvider(radar_adapter=mock_radar, nwp_adapter=mock_nwp)
    result = await provider.fetch_rainfall()

    assert result.provenance == RainfallProvenance.RADAR
    assert result.is_fallback is False
    assert result.fallback_reason is None
    assert result.spatial_grid is not None
    assert result.spatial_grid.mean_rainfall_mm() == 22.5
    # NWP was never called
    mock_nwp.fetch.assert_not_called()


@pytest.mark.asyncio
async def test_composite_provider_both_fail_returns_unavailable():
    """Verify failure of both radar and NWP returns UNAVAILABLE status without crashing."""
    mock_radar = Mock(spec=IMDRadarAdapter)
    mock_radar.fetch_radar_grid = AsyncMock(side_effect=Exception("Network down"))

    mock_nwp = Mock()
    mock_nwp.fetch = AsyncMock(side_effect=Exception("NWP 503 error"))

    provider = CompositeRainfallProvider(radar_adapter=mock_radar, nwp_adapter=mock_nwp)
    result = await provider.fetch_rainfall()

    assert result.provenance == RainfallProvenance.UNAVAILABLE
    assert result.status == RainfallStatus.UNAVAILABLE
    assert result.is_fallback is True
    assert "NWP fallback failed" in result.fallback_reason


# ---------------------------------------------------------------------------
# 7. Runoff Volume Integration (Rational Method)
# ---------------------------------------------------------------------------

def test_radar_spatial_grid_to_runoff_volume():
    """Verify that SpatialRainfallGrid converts to RunoffVolume using Rational Method: V = C * P * A / 1000."""
    # Mean rainfall = 50.0 mm
    data = [[40.0, 60.0], [50.0, 50.0]]
    grid = SpatialRainfallGrid(
        values=data,
        bounds_32643=(0.0, 0.0, 200.0, 200.0),
        resolution_m=100.0,
        timestamp=datetime.now(timezone.utc),
        duration_hours=1.0,
    )

    area_m2 = 10000.0  # 1 hectare
    c = 0.8            # Impervious urban surface

    runoff = grid.to_runoff_volume(contributing_area_m2=area_m2, runoff_coefficient=c)

    # Expected: 0.8 * 50.0 * 10000.0 / 1000.0 = 400.0 m³
    assert pytest.approx(runoff.rainfall_mm, abs=1e-5) == 50.0
    assert pytest.approx(runoff.volume_m3, abs=1e-5) == 400.0
    assert runoff.timestep_hours == 1.0


# ---------------------------------------------------------------------------
# 8. API Endpoints: Diagnostics & Composite
# ---------------------------------------------------------------------------

def test_api_radar_diagnostics_endpoint():
    """Verify /rainfall/radar/diagnostics endpoint returns full diagnostic report."""
    response = client.get("/rainfall/radar/diagnostics")
    assert response.status_code == 200
    data = response.json()

    assert "radar_network" in data
    assert "stations" in data
    assert "format_assessment" in data
    assert "institutional_data_gateway" in data
    assert data["format_assessment"]["is_quantitative_precipitation"] is False


def test_api_composite_rainfall_endpoint():
    """Verify /rainfall/composite endpoint returns provenance and fallback metadata."""
    response = client.get("/rainfall/composite")
    assert response.status_code == 200
    data = response.json()

    assert "provenance" in data
    assert data["provenance"] in ["RADAR", "NWP_FALLBACK", "UNAVAILABLE"]
    assert "is_fallback" in data
    assert "source_name" in data
    assert "acquired_at" in data


def test_api_mumbai_endpoint_provenance_backward_compatibility():
    """Verify existing /rainfall/mumbai endpoint includes provenance field."""
    response = client.get("/rainfall/mumbai")
    assert response.status_code == 200
    data = response.json()

    assert "provenance" in data
    assert data["provenance"] == "NWP_FALLBACK"
    if data["records"]:
        assert data["records"][0]["provenance"] == "NWP_FALLBACK"
