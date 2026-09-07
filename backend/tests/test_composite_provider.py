"""Tests for the composite rainfall provider."""
from __future__ import annotations

from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, patch
import pytest

try:
    from backend.app.infrastructure.rainfall.composite_provider import (
        CompositeRainfallProvider,
        CompositeRainfallResult,
    )
    from backend.app.infrastructure.rainfall.imd_radar import IMDRadarProbeResult
    from backend.app.domain.rainfall.models import (
        RainfallRecord,
        RainfallSeries,
        RainfallStatus,
        SourceType,
    )
    from backend.app.domain.rainfall.radar_models import (
        RainfallProvenance,
        SpatialRainfallGrid,
    )
except ImportError:
    from app.infrastructure.rainfall.composite_provider import (
        CompositeRainfallProvider,
        CompositeRainfallResult,
    )
    from app.infrastructure.rainfall.imd_radar import IMDRadarProbeResult
    from app.domain.rainfall.models import (
        RainfallRecord,
        RainfallSeries,
        RainfallStatus,
        SourceType,
    )
    from app.domain.rainfall.radar_models import (
        RainfallProvenance,
        SpatialRainfallGrid,
    )


@pytest.fixture
def composite_provider():
    return CompositeRainfallProvider()


@pytest.fixture
def sample_nwp_series():
    """Create a sample NWP series for testing."""
    rec = RainfallRecord(
        timestamp=datetime(2026, 9, 5, 12, 0, tzinfo=timezone.utc),
        interval_end=datetime(2026, 9, 5, 13, 0, tzinfo=timezone.utc),
        rainfall_mm=2.0,
        source="open-meteo",
        source_type=SourceType.FORECAST,
        resolution_minutes=60,
        acquired_at=datetime(2026, 9, 5, 12, 0, tzinfo=timezone.utc),
        forecast_lead_minutes=0,
        status=RainfallStatus.LIVE,
        provenance=RainfallProvenance.NWP_FALLBACK,  # Will be overridden
    )
    return RainfallSeries(records=[rec], source="open-meteo", acquired_at=rec.acquired_at)


@pytest.fixture
def sample_mesonet_series():
    """Create a sample Mesonet series for testing."""
    rec = RainfallRecord(
        timestamp=datetime(2026, 9, 5, 12, 0, tzinfo=timezone.utc),
        interval_end=datetime(2026, 9, 5, 13, 0, tzinfo=timezone.utc),
        rainfall_mm=3.0,  # 1.0 mm more than NWP
        source="mumbai-mesonet",
        source_type=SourceType.OBSERVATION,
        resolution_minutes=60,
        acquired_at=datetime(2026, 9, 5, 12, 0, tzinfo=timezone.utc),
        forecast_lead_minutes=0,
        status=RainfallStatus.LIVE,
        provenance=RainfallProvenance.MESONET,  # Will be overridden
    )
    return RainfallSeries(
        records=[rec],
        source="mumbai-mesonet",
        acquired_at=rec.acquired_at,
        provenance=RainfallProvenance.MESONET,
    )


@pytest.mark.asyncio
async def test_apply_bounded_correction_within_bounds(composite_provider, sample_nwp_series, sample_mesonet_series):
    """Test that correction is applied when error is within bounds."""
    corrected = composite_provider._apply_bounded_correction(sample_nwp_series, sample_mesonet_series)

    assert len(corrected.records) == 1
    rec = corrected.records[0]
    # NWP: 2.0, Observed: 3.0, Error: 1.0, Correction: 1.0 (within 20.0 bound)
    # Corrected: 2.0 + 1.0 = 3.0
    assert rec.rainfall_mm == 3.0
    assert rec.provenance == RainfallProvenance.NWP_CORRECTED
    assert corrected.provenance == RainfallProvenance.NWP_CORRECTED


@pytest.mark.asyncio
async def test_apply_bounded_correction_exceeds_bounds(composite_provider, sample_nwp_series):
    """Test that correction is bounded when error exceeds max_correction."""
    # Create an observed series with large error
    obs_rec = sample_nwp_series.records[0].model_copy(
        update={
            "rainfall_mm": 50.0,  # Error of 48.0 mm, exceeds 20.0 bound
            "provenance": RainfallProvenance.MESONET
        }
    )
    obs_series = RainfallSeries(
        records=[obs_rec],
        source="mumbai-mesonet",
        acquired_at=obs_rec.acquired_at
    )

    corrected = composite_provider._apply_bounded_correction(sample_nwp_series, obs_series)

    assert len(corrected.records) == 1
    rec = corrected.records[0]
    # NWP: 2.0, Observed: 50.0, Error: 48.0, Correction: clamped to 20.0
    # Corrected: 2.0 + 20.0 = 22.0
    assert rec.rainfall_mm == 22.0
    assert rec.provenance == RainfallProvenance.NWP_CORRECTED


@pytest.mark.asyncio
async def test_apply_bounded_correction_negative_error(composite_provider, sample_nwp_series):
    """Test correction when observed is less than NWP (negative error)."""
    # Create an observed series with less rainfall than NWP
    obs_rec = sample_nwp_series.records[0].model_copy(
        update={
            "rainfall_mm": 0.5,  # Error of -1.5 mm
            "provenance": RainfallProvenance.MESONET
        }
    )
    obs_series = RainfallSeries(
        records=[obs_rec],
        source="mumbai-mesonet",
        acquired_at=obs_rec.acquired_at
    )

    corrected = composite_provider._apply_bounded_correction(sample_nwp_series, obs_series)

    assert len(corrected.records) == 1
    rec = corrected.records[0]
    # NWP: 2.0, Observed: 0.5, Error: -1.5, Correction: -1.5 (within -20.0 bound)
    # Corrected: 2.0 + (-1.5) = 0.5
    assert rec.rainfall_mm == 0.5
    assert rec.provenance == RainfallProvenance.NWP_CORRECTED


@pytest.mark.asyncio
async def test_apply_bounded_correction_empty_series(composite_provider, sample_nwp_series):
    """Test correction when one series is empty."""
    empty_series = RainfallSeries(records=[], source="test", acquired_at=datetime.now(timezone.utc))

    # Test with empty observed series
    corrected = composite_provider._apply_bounded_correction(sample_nwp_series, empty_series)
    assert len(corrected.records) == 1
    assert corrected.records[0].provenance == RainfallProvenance.NWP_CORRECTED
    # Should be unchanged from original NWP
    assert corrected.records[0].rainfall_mm == sample_nwp_series.records[0].rainfall_mm

    # Test with empty NWP series
    corrected = composite_provider._apply_bounded_correction(empty_series, sample_nwp_series)
    assert len(corrected.records) == 0  # No records to correct


@pytest.mark.asyncio
async def test_fetch_rainfall_radar_success(composite_provider):
    """Test that radar data is returned when available and quantitative."""
    # Mock radar adapter to return quantitative data
    mock_grid = SpatialRainfallGrid(
        values=[[1.0, 2.0], [3.0, 4.0]],
        bounds_32643=(270000.0, 2110000.0, 280000.0, 2120000.0),
        resolution_m=1000.0,
        timestamp=datetime.now(timezone.utc),
        duration_hours=1.0,
    )
    mock_probe_result = IMDRadarProbeResult(
        endpoint_key="SRI_VRV",
        endpoint_url="https://mausam.imd.gov.in/Radar/sri_vrv.gif",
        http_status=200,
        is_quantitative=True,
        diagnostic_message="Radar data available",
        content_length_bytes=1024,
    )

    with patch.object(composite_provider.radar_adapter, 'fetch_radar_grid',
                      return_value=(mock_grid, mock_probe_result)):
        result = await composite_provider.fetch_rainfall()

        assert result.provenance == RainfallProvenance.RADAR
        assert result.status == RainfallStatus.LIVE
        assert result.is_fallback == False
        assert result.source_name == "IMD Doppler Weather Radar (Veravali)"
        assert result.spatial_grid == mock_grid


@pytest.mark.asyncio
async def test_fetch_rainfall_mesonet_success_with_correction(composite_provider, sample_nwp_series, sample_mesonet_series):
    """Test that when radar fails, Mesonet is used and NWP correction is applied."""
    # Mock radar to fail
    with patch.object(composite_provider.radar_adapter, 'fetch_radar_grid',
                      side_effect=Exception("Radar unavailable")):
        # Mock Mesonet to return data
        with patch.object(composite_provider.mesonet_adapter, 'fetch',
                          return_value=sample_mesonet_series):
            # Mock NWP to return data
            with patch.object(composite_provider.nwp_adapter, 'fetch',
                              return_value=sample_nwp_series):
                result = await composite_provider.fetch_rainfall()

                # Should return NWP_CORRECTED provenance
                assert result.provenance == RainfallProvenance.NWP_CORRECTED
                assert result.is_fallback == True  # Fallback from radar
                assert "Corrected with Mumbai Rain Mesonet" in result.source_name
                assert result.series is not None
                assert result.series.provenance == RainfallProvenance.NWP_CORRECTED
                # The corrected series should have the corrected value (3.0 in our test case)
                assert len(result.series.records) == 1
                assert result.series.records[0].rainfall_mm == 3.0  # NWP 2.0 + correction 1.0
                assert result.series.records[0].provenance == RainfallProvenance.NWP_CORRECTED


@pytest.mark.asyncio
async def test_fetch_rainfall_mesonet_success_nwp_fails_fallback_to_raw_mesonet(composite_provider, sample_mesonet_series):
    """Test that when Mesonet is available but NWP fails for correction, we fall back to raw Mesonet."""
    # Mock radar to fail
    with patch.object(composite_provider.radar_adapter, 'fetch_radar_grid',
                      side_effect=Exception("Radar unavailable")):
        # Mock Mesonet to return data
        with patch.object(composite_provider.mesonet_adapter, 'fetch',
                          return_value=sample_mesonet_series):
            # Mock NWP to fail
            with patch.object(composite_provider.nwp_adapter, 'fetch',
                              side_effect=Exception("NWP unavailable")):
                result = await composite_provider.fetch_rainfall()

                # Should fall back to raw Mesonet
                assert result.provenance == RainfallProvenance.MESONET
                assert result.is_fallback == True
                assert result.source_name == "Mumbai Rain Mesonet"
                assert result.series == sample_mesonet_series


@pytest.mark.asyncio
async def test_fetch_rainfall_all_sources_fail(composite_provider):
    """Test that when all sources fail, we return UNAVAILABLE."""
    # Mock all adapters to fail
    with patch.object(composite_provider.radar_adapter, 'fetch_radar_grid',
                      side_effect=Exception("Radar failed")):
        with patch.object(composite_provider.mesonet_adapter, 'fetch',
                          side_effect=Exception("Mesonet failed")):
            with patch.object(composite_provider.nwp_adapter, 'fetch',
                              side_effect=Exception("NWP failed")):
                result = await composite_provider.fetch_rainfall()

                assert result.provenance == RainfallProvenance.UNAVAILABLE
                assert result.status == RainfallStatus.UNAVAILABLE
                assert result.is_fallback == True
                assert result.source_name == "None"


@pytest.mark.asyncio
async def test_correction_never_extrapolates_sparse_gauge(composite_provider, sample_nwp_series):
    """Test that NWP records without matching observation are returned unchanged."""
    # Observed series at a different timestamp than NWP
    obs_rec = RainfallRecord(
        timestamp=datetime(2026, 9, 5, 14, 0, tzinfo=timezone.utc),  # Different hour
        interval_end=datetime(2026, 9, 5, 15, 0, tzinfo=timezone.utc),
        rainfall_mm=10.0,
        source="mumbai-mesonet",
        source_type=SourceType.OBSERVATION,
        resolution_minutes=60,
        acquired_at=datetime(2026, 9, 5, 14, 0, tzinfo=timezone.utc),
        forecast_lead_minutes=0,
        status=RainfallStatus.LIVE,
        provenance=RainfallProvenance.MESONET,
    )
    obs_series = RainfallSeries(
        records=[obs_rec],
        source="mumbai-mesonet",
        acquired_at=obs_rec.acquired_at,
    )

    corrected = composite_provider._apply_bounded_correction(sample_nwp_series, obs_series)

    # NWP record at 12:00 has no matching observation -> should be unchanged
    assert len(corrected.records) == 1
    assert corrected.records[0].rainfall_mm == sample_nwp_series.records[0].rainfall_mm
    assert corrected.records[0].provenance == RainfallProvenance.NWP_CORRECTED


@pytest.mark.asyncio
async def test_correction_preserves_zero_floor(composite_provider):
    """Test that corrected values never go below 0.0 mm."""
    t = datetime(2026, 9, 5, 12, 0, tzinfo=timezone.utc)

    nwp_rec = RainfallRecord(
        timestamp=t,
        interval_end=t + timedelta(hours=1),
        rainfall_mm=0.5,  # Low NWP value
        source="open-meteo",
        source_type=SourceType.FORECAST,
        resolution_minutes=60,
        acquired_at=t,
        forecast_lead_minutes=0,
        status=RainfallStatus.LIVE,
    )
    nwp_series = RainfallSeries(records=[nwp_rec], source="open-meteo", acquired_at=t)

    obs_rec = RainfallRecord(
        timestamp=t,
        interval_end=t + timedelta(hours=1),
        rainfall_mm=0.0,  # Observed zero -> error = -0.5
        source="mumbai-mesonet",
        source_type=SourceType.OBSERVATION,
        resolution_minutes=60,
        acquired_at=t,
        forecast_lead_minutes=0,
        status=RainfallStatus.LIVE,
    )
    obs_series = RainfallSeries(records=[obs_rec], source="mumbai-mesonet", acquired_at=t)

    corrected = composite_provider._apply_bounded_correction(nwp_series, obs_series)

    # Corrected: 0.5 + (-0.5) = 0.0 (floored at 0, not negative)
    assert corrected.records[0].rainfall_mm == 0.0
    assert corrected.records[0].provenance == RainfallProvenance.NWP_CORRECTED


if __name__ == "__main__":
    pytest.main([__file__])