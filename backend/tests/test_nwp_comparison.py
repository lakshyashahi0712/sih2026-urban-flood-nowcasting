"""Tests for NWP comparison service."""
from __future__ import annotations

from datetime import datetime, timezone, timedelta
import pytest

try:
    from backend.app.infrastructure.rainfall.nwp_comparison import (
        NWPComparisonService,
        NWPBiasMetrics,
        NWPComparisonResult,
    )
    from backend.app.domain.rainfall.models import (
        RainfallRecord,
        RainfallSeries,
        RainfallStatus,
        SourceType,
    )
except ImportError:
    from app.infrastructure.rainfall.nwp_comparison import (
        NWPComparisonService,
        NWPBiasMetrics,
        NWPComparisonResult,
    )
    from app.domain.rainfall.models import (
        RainfallRecord,
        RainfallSeries,
        RainfallStatus,
        SourceType,
    )


def _make_record(
    timestamp: datetime,
    rainfall_mm: float,
    source: str = "test",
    source_type: SourceType = SourceType.FORECAST,
) -> RainfallRecord:
    """Helper to create a rainfall record for testing."""
    return RainfallRecord(
        timestamp=timestamp,
        interval_end=timestamp + timedelta(hours=1),
        rainfall_mm=rainfall_mm,
        source=source,
        source_type=source_type,
        resolution_minutes=60,
        acquired_at=datetime.now(timezone.utc),
        forecast_lead_minutes=0,
        status=RainfallStatus.LIVE,
    )


def _make_series(records: list[RainfallRecord], source: str = "test") -> RainfallSeries:
    """Helper to create a rainfall series for testing."""
    return RainfallSeries(
        records=records,
        source=source,
        acquired_at=datetime.now(timezone.utc),
    )


class TestNWPComparisonService:
    """Tests for NWPComparisonService.compare()."""

    def test_compare_matching_intervals(self):
        """Test bias calculation when timestamps match."""
        t1 = datetime(2026, 9, 5, 12, 0, tzinfo=timezone.utc)
        t2 = datetime(2026, 9, 5, 13, 0, tzinfo=timezone.utc)

        observed = _make_series([
            _make_record(t1, 3.0, source="mesonet", source_type=SourceType.OBSERVATION),
            _make_record(t2, 5.0, source="mesonet", source_type=SourceType.OBSERVATION),
        ])
        nwp = _make_series([
            _make_record(t1, 2.0),
            _make_record(t2, 4.0),
        ])

        metrics = NWPComparisonService.compare(observed, nwp)

        assert metrics.matched_intervals == 2
        # Error: (3-2) + (5-4) = 1 + 1, mean = 1.0
        assert metrics.mean_error_mm == 1.0
        assert metrics.mean_absolute_error_mm == 1.0
        assert metrics.max_error_mm == 1.0
        assert len(metrics.comparisons) == 2
        assert metrics.comparisons[0].error_mm == 1.0
        assert metrics.comparisons[1].error_mm == 1.0

    def test_compare_no_matching_intervals(self):
        """Test when no timestamps match between observed and NWP."""
        t1 = datetime(2026, 9, 5, 12, 0, tzinfo=timezone.utc)
        t2 = datetime(2026, 9, 5, 14, 0, tzinfo=timezone.utc)  # Different hour

        observed = _make_series([
            _make_record(t1, 3.0, source="mesonet", source_type=SourceType.OBSERVATION),
        ])
        nwp = _make_series([
            _make_record(t2, 2.0),
        ])

        metrics = NWPComparisonService.compare(observed, nwp)

        assert metrics.matched_intervals == 0
        assert metrics.mean_error_mm == 0.0
        assert metrics.mean_absolute_error_mm == 0.0
        assert metrics.max_error_mm == 0.0
        assert len(metrics.comparisons) == 0

    def test_compare_partial_overlap(self):
        """Test when only some timestamps match."""
        t1 = datetime(2026, 9, 5, 12, 0, tzinfo=timezone.utc)
        t2 = datetime(2026, 9, 5, 13, 0, tzinfo=timezone.utc)
        t3 = datetime(2026, 9, 5, 14, 0, tzinfo=timezone.utc)

        observed = _make_series([
            _make_record(t1, 3.0, source="mesonet", source_type=SourceType.OBSERVATION),
            _make_record(t2, 5.0, source="mesonet", source_type=SourceType.OBSERVATION),
        ])
        nwp = _make_series([
            _make_record(t2, 4.0),  # Matches t2 only
            _make_record(t3, 6.0),  # No match
        ])

        metrics = NWPComparisonService.compare(observed, nwp)

        assert metrics.matched_intervals == 1
        # Only t2 matches: error = 5.0 - 4.0 = 1.0
        assert metrics.mean_error_mm == 1.0
        assert len(metrics.comparisons) == 1
        assert metrics.comparisons[0].timestamp == t2

    def test_bias_metrics_positive_bias(self):
        """Test when NWP consistently underestimates (positive mean error)."""
        t1 = datetime(2026, 9, 5, 12, 0, tzinfo=timezone.utc)

        observed = _make_series([
            _make_record(t1, 10.0, source="mesonet", source_type=SourceType.OBSERVATION),
        ])
        nwp = _make_series([
            _make_record(t1, 2.0),
        ])

        metrics = NWPComparisonService.compare(observed, nwp)

        assert metrics.matched_intervals == 1
        assert metrics.mean_error_mm == 8.0  # 10 - 2 = 8, positive = underestimates
        assert metrics.comparisons[0].relative_error == 4.0  # 8 / 2

    def test_bias_metrics_negative_bias(self):
        """Test when NWP consistently overestimates (negative mean error)."""
        t1 = datetime(2026, 9, 5, 12, 0, tzinfo=timezone.utc)

        observed = _make_series([
            _make_record(t1, 1.0, source="mesonet", source_type=SourceType.OBSERVATION),
        ])
        nwp = _make_series([
            _make_record(t1, 5.0),
        ])

        metrics = NWPComparisonService.compare(observed, nwp)

        assert metrics.matched_intervals == 1
        assert metrics.mean_error_mm == -4.0  # 1 - 5 = -4, negative = overestimates
        assert metrics.mean_absolute_error_mm == 4.0
        assert metrics.comparisons[0].relative_error == -0.8  # -4 / 5


if __name__ == "__main__":
    pytest.main([__file__])
