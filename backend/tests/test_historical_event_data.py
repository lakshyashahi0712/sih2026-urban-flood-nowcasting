"""Tests for Historical Event Data Layer (Phase 2.5A).

Verifies metadata, strict provenance enforcement, rainfall forcing calibration,
derived coastal tide conditions, authoritative observed station totals, observed
flood benchmarks, and architectural protection against benchmark data leakage.
"""
from datetime import datetime, timezone
import pytest
from zoneinfo import ZoneInfo

from backend.app.domain.historical import (
    BoundaryLevelStep,
    HistoricalBoundaryCondition,
    HistoricalEvent,
    HistoricalEventMetadata,
    HistoricalProvenance,
    HistoricalRainfallForcing,
    HourlyRainfallStep,
    InundationDepthRange,
    ObservedFloodBenchmark,
    ObservedStationRainfall,
    assert_no_benchmark_leakage,
    get_mumbai_august_2017_event,
)

TZ_IST = ZoneInfo("Asia/Kolkata")


class TestHistoricalEventMetadata:
    """Verify event metadata compliance and timezone handling."""

    def test_metadata_fields(self):
        event = get_mumbai_august_2017_event()
        meta = event.metadata

        assert meta.event_id == "mumbai-2017-08-29-deluge"
        assert meta.event_name == "29 August 2017 Mumbai Deluge"
        assert meta.event_date == "2017-08-29"
        assert meta.timezone_name == "Asia/Kolkata"
        assert meta.window_start.tzinfo is not None
        assert meta.window_end.tzinfo is not None
        assert meta.window_end > meta.window_start

        # Classification verification
        assert meta.rainfall_source_classification == HistoricalProvenance.SECONDARY_REPORT
        assert meta.tide_source_classification == HistoricalProvenance.DERIVED

        # Observed validation location names
        assert len(meta.observed_validation_locations) == 4
        assert "Kurla West (LBS Marg / Bail Bazar)" in meta.observed_validation_locations
        assert "Milan Subway (Santacruz)" in meta.observed_validation_locations

        # Units and citations
        assert "rainfall_depth" in meta.units
        assert meta.units["rainfall_depth"] == "mm"
        assert "observed_rainfall" in meta.source_attribution
        assert "tide_boundary" in meta.source_attribution


class TestProvenanceEnforcement:
    """Verify strict provenance values and rejection of unauthorized or mislabeled data."""

    def test_provenance_enum_values(self):
        assert HistoricalProvenance.OBSERVED.value == "OBSERVED"
        assert HistoricalProvenance.REANALYSIS.value == "REANALYSIS"
        assert HistoricalProvenance.FORECAST.value == "FORECAST"
        assert HistoricalProvenance.DERIVED.value == "DERIVED"
        assert HistoricalProvenance.SECONDARY_REPORT.value == "SECONDARY-REPORT"

    def test_reanalysis_cannot_be_labeled_observed(self):
        """ERA5 reanalysis or Open-Meteo archive must never be accepted as OBSERVED."""
        with pytest.raises(ValueError, match="ObservedStationRainfall provenance must be OBSERVED"):
            ObservedStationRainfall(
                station_id="ERA5_GRID",
                station_name="ERA5 Reanalysis Grid Cell",
                operator="ECMWF",
                latitude=19.07,
                longitude=72.88,
                total_rainfall_mm=66.6,
                period_start=datetime(2017, 8, 29, 8, 30, tzinfo=TZ_IST),
                period_end=datetime(2017, 8, 30, 8, 30, tzinfo=TZ_IST),
                provenance=HistoricalProvenance.REANALYSIS,
                source_citation="Open-Meteo Historical Archive (ERA5)",
            )

    def test_forcing_cannot_be_falsely_labeled_observed(self):
        """Hourly series from literature cannot claim to be direct OBSERVED sensor telemetry."""
        with pytest.raises(ValueError, match="Hourly rainfall series cannot be labeled OBSERVED"):
            HistoricalRainfallForcing(
                event_id="test-event",
                timezone_name="Asia/Kolkata",
                series=[
                    HourlyRainfallStep(
                        step_start=datetime(2017, 8, 29, 8, 30, tzinfo=TZ_IST),
                        step_end=datetime(2017, 8, 29, 9, 30, tzinfo=TZ_IST),
                        rainfall_mm=10.0,
                        intensity_mm_per_hr=10.0,
                        provenance=HistoricalProvenance.SECONDARY_REPORT,
                        source_citation="Test citation",
                    )
                ],
                total_forcing_mm=10.0,
                provenance=HistoricalProvenance.OBSERVED,  # ILLEGAL!
                calibration_reference="Test calibration",
            )


class TestAuthoritativeObservedRainfallTotals:
    """Verify official station observations are preserved and hourly data is not fabricated."""

    def test_four_authoritative_station_totals(self):
        event = get_mumbai_august_2017_event()
        totals = {s.station_id: s for s in event.observed_rainfall_totals}

        assert len(totals) == 4

        # 1. Santacruz IMD: 331.4 mm / 24h
        santacruz = totals["IMD_SANTACRUZ"]
        assert santacruz.total_rainfall_mm == 331.4
        assert santacruz.provenance == HistoricalProvenance.OBSERVED
        assert santacruz.duration_hours == 24.0

        # 2. Kurla / L-Ward BMC: 320.0 mm / 24h
        kurla = totals["BMC_KURLA_LWARD"]
        assert kurla.total_rainfall_mm == 320.0
        assert kurla.provenance == HistoricalProvenance.OBSERVED
        assert kurla.duration_hours == 24.0

        # 3. Vikhroli BMC: 468.0 mm / 24h
        vikhroli = totals["BMC_VIKHROLI"]
        assert vikhroli.total_rainfall_mm == 468.0
        assert vikhroli.provenance == HistoricalProvenance.OBSERVED
        assert vikhroli.duration_hours == 24.0

        # 4. Colaba IMD: 111.0 mm / 24h
        colaba = totals["IMD_COLABA"]
        assert colaba.total_rainfall_mm == 111.0
        assert colaba.provenance == HistoricalProvenance.OBSERVED
        assert colaba.duration_hours == 24.0

    def test_observed_totals_have_no_subdaily_fabrication(self):
        """Ensure station totals represent single 24-hour intervals, without fabricated sub-daily arrays."""
        event = get_mumbai_august_2017_event()
        for station in event.observed_rainfall_totals:
            delta = station.period_end - station.period_start
            assert delta.total_seconds() == 24 * 3600
            assert hasattr(station, "hourly_series") is False


class TestRainfallForcingValidation:
    """Verify published hourly rainfall forcing properties."""

    def test_forcing_series_continuity_and_calibration(self):
        event = get_mumbai_august_2017_event()
        forcing = event.rainfall_forcing

        assert forcing.provenance == HistoricalProvenance.SECONDARY_REPORT
        assert forcing.total_forcing_mm == 320.0
        assert len(forcing.series) == 24
        assert forcing.is_model_input is True

        # Check non-negative and sum matches
        total_sum = 0.0
        for i, step in enumerate(forcing.series):
            assert step.rainfall_mm >= 0.0
            assert step.intensity_mm_per_hr >= 0.0
            assert step.step_start.tzinfo is not None
            assert step.step_end > step.step_start
            assert step.provenance == HistoricalProvenance.SECONDARY_REPORT
            total_sum += step.rainfall_mm
            if i > 0:
                # Contiguous steps
                assert step.step_start == forcing.series[i - 1].step_end

        assert round(total_sum, 2) == 320.0

    def test_peak_cloudburst_rate_is_captured(self):
        """Literature-calibrated series must capture the cloudburst (peak 74 mm/hr), unlike ERA5 (9.1 mm/hr)."""
        event = get_mumbai_august_2017_event()
        max_step = max(event.rainfall_forcing.series, key=lambda s: s.rainfall_mm)
        assert max_step.rainfall_mm == 74.0
        assert max_step.step_start.hour == 13
        assert max_step.step_start.minute == 30

    def test_negative_rainfall_rejected(self):
        with pytest.raises(ValueError):
            HourlyRainfallStep(
                step_start=datetime(2017, 8, 29, 8, 30, tzinfo=TZ_IST),
                step_end=datetime(2017, 8, 29, 9, 30, tzinfo=TZ_IST),
                rainfall_mm=-5.0,  # ILLEGAL
                intensity_mm_per_hr=-5.0,
                provenance=HistoricalProvenance.SECONDARY_REPORT,
                source_citation="Test",
            )


class TestTideBoundaryCondition:
    """Verify coastal boundary condition classification and peak tide value."""

    def test_peak_astronomical_tide(self):
        event = get_mumbai_august_2017_event()
        tide = event.boundary_condition

        assert tide.provenance == HistoricalProvenance.DERIVED
        assert tide.peak_level_m == 3.32
        assert tide.peak_time == datetime(2017, 8, 29, 16, 30, tzinfo=TZ_IST)
        assert tide.datum == "Mumbai Chart Datum (CD)"
        assert tide.is_model_input is True

    def test_astronomical_tide_cannot_be_labeled_observed(self):
        with pytest.raises(ValueError, match="Astronomical tide table values cannot be classified as OBSERVED"):
            HistoricalBoundaryCondition(
                event_id="test",
                boundary_name="Mahim_Creek",
                datum="Mumbai Chart Datum",
                provenance=HistoricalProvenance.OBSERVED,  # ILLEGAL!
                series=[
                    BoundaryLevelStep(
                        timestamp=datetime(2017, 8, 29, 16, 30, tzinfo=TZ_IST),
                        water_level_m=3.32,
                        provenance=HistoricalProvenance.DERIVED,
                        source_citation="Test",
                    )
                ],
                peak_level_m=3.32,
                peak_time=datetime(2017, 8, 29, 16, 30, tzinfo=TZ_IST),
                source_citation="Test citation",
            )


class TestObservedFloodBenchmarksAndSafeguards:
    """Verify observed flood benchmarks and leakage prevention safeguards."""

    def test_four_observed_benchmarks_exist(self):
        event = get_mumbai_august_2017_event()
        benchmarks = {b.location_id: b for b in event.observed_flood_benchmarks}

        assert len(benchmarks) == 4

        # 1. LBS Marg / Bail Bazar: 0.60–1.10 m
        lbs = benchmarks["KURLA_LBS_MARG"]
        assert lbs.depth_range.min_depth_m == 0.60
        assert lbs.depth_range.max_depth_m == 1.10
        assert lbs.provenance == HistoricalProvenance.OBSERVED
        assert lbs.is_model_input is False

        # 2. Kalina / CST Road Junction: 0.80–1.40 m
        kalina = benchmarks["KALINA_CST_ROAD"]
        assert kalina.depth_range.min_depth_m == 0.80
        assert kalina.depth_range.max_depth_m == 1.40
        assert kalina.provenance == HistoricalProvenance.OBSERVED
        assert kalina.is_model_input is False

        # 3. Premier Road, Kurla: 0.50–0.90 m
        premier = benchmarks["KURLA_PREMIER_ROAD"]
        assert premier.depth_range.min_depth_m == 0.50
        assert premier.depth_range.max_depth_m == 0.90
        assert premier.provenance == HistoricalProvenance.OBSERVED
        assert premier.is_model_input is False

        # 4. Milan Subway: >2.20 m
        milan = benchmarks["MILAN_SUBWAY"]
        assert milan.depth_range.min_depth_m == 2.20
        assert milan.depth_range.max_depth_m is None
        assert milan.depth_range.descriptor == ">2.20 m"
        assert milan.provenance == HistoricalProvenance.OBSERVED
        assert milan.is_model_input is False

    def test_benchmarks_cannot_have_is_model_input_true(self):
        """Observed benchmarks must NEVER be allowed to serve as simulation inputs."""
        with pytest.raises(ValueError, match="ObservedFloodBenchmark.is_model_input CANNOT be True"):
            ObservedFloodBenchmark(
                location_id="TEST_HOTSPOT",
                location_name="Test Inundation Point",
                latitude=19.07,
                longitude=72.88,
                depth_range=InundationDepthRange(min_depth_m=0.5, max_depth_m=1.0, descriptor="0.5–1.0 m"),
                impact_notes="Test impact",
                source_citation="Test citation",
                provenance=HistoricalProvenance.OBSERVED,
                is_model_input=True,  # STRICTLY REJECTED!
            )

    def test_assert_no_benchmark_leakage_guard(self):
        """Guard function raises TypeError if an ObservedFloodBenchmark is submitted as model input."""
        event = get_mumbai_august_2017_event()
        benchmark = event.observed_flood_benchmarks[0]

        with pytest.raises(TypeError, match="Architectural Leakage Guard"):
            assert_no_benchmark_leakage(benchmark)

        # But valid model forcing passes
        assert_no_benchmark_leakage(event.rainfall_forcing)
        assert_no_benchmark_leakage(event.boundary_condition)


class TestTimezoneHandling:
    """Verify timezone conversions and awareness."""

    def test_ist_to_utc_conversion(self):
        event = get_mumbai_august_2017_event()
        peak_tide_ist = event.boundary_condition.peak_time
        assert peak_tide_ist.tzinfo == TZ_IST
        assert peak_tide_ist.hour == 16
        assert peak_tide_ist.minute == 30

        # Convert to UTC: 16:30 IST is 11:00 UTC
        peak_tide_utc = peak_tide_ist.astimezone(timezone.utc)
        assert peak_tide_utc.hour == 11
        assert peak_tide_utc.minute == 0
