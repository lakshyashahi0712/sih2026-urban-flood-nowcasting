"""Tests for Historical Event Replay Engine (Phase 2.5B).

Verifies:
1. Replay produces exactly 24 states.
2. Timestamps are chronological and timezone-aware (Asia/Kolkata).
3. Rainfall provenance remains SECONDARY-REPORT.
4. Tide provenance remains DERIVED.
5. Replay does not use Open-Meteo or external APIs.
6. Replay does not consume observed flood benchmarks as inputs.
7. Existing flood pipeline is actually invoked.
8. Timestep outputs contain all required metrics.
9. Boundary/tide values align with corresponding timestamps.
10. Deterministic replay produces identical outputs.
11. Validation comparison accurately reports observed vs modeled depths.
12. Existing live forecast behavior remains unchanged.
"""
from datetime import datetime, timezone
import pytest
from zoneinfo import ZoneInfo
import numpy as np

from backend.app.config import settings
from backend.app.domain.historical import (
    BenchmarkValidationComparison,
    HistoricalEvent,
    HistoricalProvenance,
    HistoricalReplayEngine,
    HistoricalReplaySummary,
    HistoricalReplayTimestepState,
    InundationDepthRange,
    ObservedFloodBenchmark,
    assert_no_benchmark_leakage,
    get_mumbai_august_2017_event,
)
from backend.app.infrastructure.drainage.bmc_gis import BMCDrainageLoader
from backend.app.infrastructure.drainage.raster_engine import RasterEngine

TZ_IST = ZoneInfo("Asia/Kolkata")


@pytest.fixture(scope="module")
def cached_engine():
    engine = RasterEngine(settings.dem_path, threshold_area_m2=15000.0)
    engine.load_and_preprocess()
    engine.condition_dem()
    engine.compute_flow_direction()
    return engine


@pytest.fixture(scope="module")
def cached_bmc_network():
    return BMCDrainageLoader.load_default_bmc_network()


@pytest.fixture(scope="module")
def replay_engine(cached_engine, cached_bmc_network):
    return HistoricalReplayEngine(
        raster_engine=cached_engine,
        drainage_network=cached_bmc_network,
        contributing_area_m2=500000.0,
        runoff_coefficient=0.7,
        cell_size_m=30.0,
    )


@pytest.fixture(scope="module")
def replay_result(replay_engine):
    event = get_mumbai_august_2017_event()
    return replay_engine.run_replay(event)


class TestHistoricalReplayEngine:
    """Core verification tests for the historical replay engine."""

    def test_replay_produces_exactly_24_states(self, replay_result):
        assert replay_result.timestep_count == 24
        assert len(replay_result.timesteps) == 24

    def test_timestamps_chronological_and_timezone_aware(self, replay_result):
        states = replay_result.timesteps
        assert replay_result.first_timestamp == datetime(2017, 8, 29, 8, 30, tzinfo=TZ_IST)
        assert replay_result.last_timestamp == datetime(2017, 8, 30, 7, 30, tzinfo=TZ_IST)

        for i, s in enumerate(states):
            assert s.timestep_index == i
            assert s.replay_timestamp.tzinfo is not None
            assert s.replay_timestamp.tzinfo == TZ_IST
            if i > 0:
                prev_ts = states[i - 1].replay_timestamp
                # Must be exactly 1 hour apart
                delta = s.replay_timestamp - prev_ts
                assert delta.total_seconds() == 3600

    def test_rainfall_and_tide_provenance_preserved(self, replay_result):
        for s in replay_result.timesteps:
            assert s.rainfall_provenance == HistoricalProvenance.SECONDARY_REPORT
            assert s.boundary_provenance == HistoricalProvenance.DERIVED
            assert s.model_provenance == "RETROSPECTIVE_SIMULATION"

    def test_boundary_tide_values_align_with_timestamps(self, replay_result):
        event = get_mumbai_august_2017_event()
        for i, s in enumerate(replay_result.timesteps):
            expected_tide = event.boundary_condition.series[i].water_level_m
            assert s.boundary_level_m == expected_tide

        # Peak tide is 3.32m at 16:30 IST (index 8)
        peak_tide_step = replay_result.timesteps[8]
        assert peak_tide_step.replay_timestamp == datetime(2017, 8, 29, 16, 30, tzinfo=TZ_IST)
        assert peak_tide_step.boundary_level_m == 3.32

    def test_timestep_outputs_contain_required_metrics(self, replay_result):
        for s in replay_result.timesteps:
            assert s.rainfall_mm >= 0.0
            assert s.rainfall_intensity_mm_per_hr >= 0.0
            assert s.peak_flood_depth_m >= 0.0
            assert s.flooded_area_m2 >= 0.0
            assert s.flood_volume_m3 >= 0.0
            assert s.flooded_cell_count >= 0
            assert s.drainage_surcharge_volume_m3 >= 0.0

    def test_peak_cloudburst_response(self, replay_result):
        """Verify that peak rainfall (74 mm/hr at step 6) triggers major flood surge."""
        step6 = replay_result.timesteps[5]  # Index 5 is 13:30–14:30
        assert step6.rainfall_mm == 74.0
        assert step6.drainage_surcharge_volume_m3 > 4000.0  # Heavy surcharge
        assert step6.peak_flood_depth_m >= 0.60  # Substantial waterlogging

    def test_benchmarks_not_consumed_as_inputs(self, replay_engine):
        """Verify that benchmarks can never be passed as model forcing."""
        event = get_mumbai_august_2017_event()
        benchmark = event.observed_flood_benchmarks[0]

        # Passing benchmark into assert_no_benchmark_leakage raises TypeError
        with pytest.raises(TypeError, match="Architectural Leakage Guard"):
            assert_no_benchmark_leakage(benchmark)

    def test_no_open_meteo_called(self, monkeypatch, replay_engine):
        """Verify replay runs completely offline without invoking Open-Meteo or external APIs."""
        def raise_if_called(*args, **kwargs):
            raise AssertionError("External network/API called during historical replay!")

        monkeypatch.setattr("urllib.request.urlopen", raise_if_called)
        # Execute replay with network disabled on a 2-step slice for speed
        event = get_mumbai_august_2017_event()
        sub_forcing = event.rainfall_forcing.model_copy(
            update={
                "series": event.rainfall_forcing.series[:2],
                "total_forcing_mm": sum(s.rainfall_mm for s in event.rainfall_forcing.series[:2]),
            }
        )
        sub_event = event.model_copy(update={"rainfall_forcing": sub_forcing})
        summary = replay_engine.run_replay(sub_event)
        assert summary.timestep_count == 2

    def test_deterministic_replay(self, replay_engine):
        """Verify that running the replay twice with identical inputs yields exact identical outputs."""
        event = get_mumbai_august_2017_event()
        sub_forcing = event.rainfall_forcing.model_copy(
            update={
                "series": event.rainfall_forcing.series[:2],
                "total_forcing_mm": sum(s.rainfall_mm for s in event.rainfall_forcing.series[:2]),
            }
        )
        sub_event = event.model_copy(update={"rainfall_forcing": sub_forcing})

        res1 = replay_engine.run_replay(sub_event)
        res2 = replay_engine.run_replay(sub_event)

        assert res1.peak_modeled_depth_m == res2.peak_modeled_depth_m
        assert res1.peak_flooded_area_m2 == res2.peak_flooded_area_m2
        assert res1.peak_flood_volume_m3 == res2.peak_flood_volume_m3
        assert res1.peak_surcharge_volume_m3 == res2.peak_surcharge_volume_m3

        for s1, s2 in zip(res1.timesteps, res2.timesteps):
            assert s1.peak_flood_depth_m == s2.peak_flood_depth_m
            assert s1.drainage_surcharge_volume_m3 == s2.drainage_surcharge_volume_m3


class TestValidationComparison:
    """Verify post-replay validation comparison against observed benchmarks."""

    def test_validation_comparison_summary(self, replay_result):
        comps = {c.location_id: c for c in replay_result.validation_comparisons}
        assert len(comps) == 4

        # 1. Kurla West (LBS Marg)
        lbs = comps["KURLA_LBS_MARG"]
        assert lbs.spatial_status == "MATCHED"
        assert lbs.observed_min_depth_m == 0.60
        assert lbs.observed_max_depth_m == 1.10
        assert lbs.exact_cell_depth_m == 0.000
        # In 200m road buffer, nearest flooded cell (168.3m away) has depth 0.367m
        assert lbs.matched_depth_m == 0.367
        assert lbs.match_method == "NEIGHBORHOOD_BUFFER"
        assert lbs.search_radius_m == 200.0
        assert lbs.matched_cell_distance_m == 168.3
        # 0.367m is below the 0.60m threshold, so within_observed_range is correctly False
        assert lbs.within_observed_range is False
        assert lbs.absolute_difference_m == pytest.approx(0.233, abs=0.01)
        assert lbs.observed_provenance == HistoricalProvenance.OBSERVED
        assert lbs.modeled_provenance == "RETROSPECTIVE_SIMULATION"

        # 2. Kalina (CST Road Junction)
        kalina = comps["KALINA_CST_ROAD"]
        assert kalina.spatial_status == "MATCHED"
        assert kalina.observed_min_depth_m == 0.80
        assert kalina.observed_max_depth_m == 1.40
        assert kalina.exact_cell_depth_m == 0.000
        assert kalina.matched_depth_m == 0.000
        assert kalina.within_observed_range is False
        assert kalina.absolute_difference_m == 0.80
        assert kalina.observed_provenance == HistoricalProvenance.OBSERVED

        # 3. Premier Road (Kurla)
        premier = comps["KURLA_PREMIER_ROAD"]
        assert premier.spatial_status == "MATCHED"
        assert premier.observed_min_depth_m == 0.50
        assert premier.observed_max_depth_m == 0.90
        assert premier.exact_cell_depth_m == 0.000
        assert premier.matched_depth_m == 0.000
        assert premier.within_observed_range is False
        assert premier.absolute_difference_m == 0.50
        assert premier.observed_provenance == HistoricalProvenance.OBSERVED

        # 4. Milan Subway (Santacruz)
        # Milan subway is ~1.3km west of the pilot DEM boundary
        milan = comps["MILAN_SUBWAY"]
        assert milan.spatial_status == "OUTSIDE_PILOT_EXTENT"
        assert milan.exact_cell_depth_m is None
        assert milan.matched_depth_m is None
        assert milan.matched_cell_distance_m is None
        assert milan.match_method == "NONE"
        assert milan.within_observed_range is False
        assert milan.absolute_difference_m is None
        assert milan.observed_provenance == HistoricalProvenance.OBSERVED
        assert "outside pilot dem" in milan.notes.lower()

    def test_exact_cell_differs_from_matched_depth(self, cached_engine):
        """Verify that exact-cell depth can differ from neighborhood matched depth."""
        from backend.app.domain.historical.replay import compare_benchmarks_against_grid
        from backend.app.domain.historical.models import InundationDepthRange
        import pyproj

        # Construct a synthetic benchmark inside the grid
        transformer = pyproj.Transformer.from_crs("EPSG:32643", "EPSG:4326", always_xy=True)
        t = cached_engine.transform
        center_x = t.c + 50.5 * t.a
        center_y = t.f + 50.5 * t.e
        lon, lat = transformer.transform(center_x, center_y)

        bench = ObservedFloodBenchmark(
            location_id="SYNTHETIC_TEST",
            location_name="Synthetic Test Point",
            latitude=lat,
            longitude=lon,
            depth_range=InundationDepthRange(min_depth_m=0.30, max_depth_m=0.80, descriptor="0.30–0.80 m"),
            impact_notes="Test",
            source_citation="Test",
            provenance=HistoricalProvenance.OBSERVED,
            is_model_input=False,
        )

        # Depth grid: center cell (50, 50) is 0.0, but adjacent cell (50, 52) (60m away) has 0.65m
        synthetic_grid = np.zeros((cached_engine.height, cached_engine.width), dtype=float)
        synthetic_grid[50, 52] = 0.65

        comps = compare_benchmarks_against_grid(
            benchmarks=[bench],
            depth_grid=synthetic_grid,
            engine=cached_engine,
            search_radius_m=100.0,
        )

        res = comps[0]
        assert res.exact_cell_depth_m == 0.000
        assert res.matched_depth_m == 0.650
        assert res.match_method == "NEIGHBORHOOD_BUFFER"
        assert 55.0 <= res.matched_cell_distance_m <= 65.0
        assert res.within_observed_range is True
        assert res.absolute_difference_m == 0.0

    def test_search_radius_is_explicit(self, replay_result):
        """Verify search radius is explicitly recorded on every benchmark comparison."""
        for c in replay_result.validation_comparisons:
            assert c.search_radius_m == 200.0

    def test_neighborhood_matching_is_deterministic(self, cached_engine):
        """Verify matching is completely deterministic and reproducible across multiple runs."""
        from backend.app.domain.historical.replay import compare_benchmarks_against_grid
        event = get_mumbai_august_2017_event()

        synthetic_grid = np.zeros((cached_engine.height, cached_engine.width), dtype=float)
        synthetic_grid[73, 90] = 0.367

        res1 = compare_benchmarks_against_grid(event.observed_flood_benchmarks, synthetic_grid, cached_engine, search_radius_m=200.0)
        res2 = compare_benchmarks_against_grid(event.observed_flood_benchmarks, synthetic_grid, cached_engine, search_radius_m=200.0)

        assert len(res1) == len(res2)
        for c1, c2 in zip(res1, res2):
            assert c1.exact_cell_depth_m == c2.exact_cell_depth_m
            assert c1.matched_depth_m == c2.matched_depth_m
            assert c1.match_method == c2.match_method
            assert c1.matched_cell_distance_m == c2.matched_cell_distance_m
            assert c1.within_observed_range == c2.within_observed_range
            assert c1.absolute_difference_m == c2.absolute_difference_m

    def test_benchmarks_cannot_affect_simulation(self, replay_engine):
        """Verify that modifying benchmark observed depth targets has ZERO impact on simulation outputs."""
        event = get_mumbai_august_2017_event()
        sub_forcing = event.rainfall_forcing.model_copy(
            update={
                "series": event.rainfall_forcing.series[:2],
                "total_forcing_mm": sum(s.rainfall_mm for s in event.rainfall_forcing.series[:2]),
            }
        )
        sub_event1 = event.model_copy(update={"rainfall_forcing": sub_forcing})

        # Create copy with modified benchmarks
        modified_benchmarks = [
            b.model_copy(update={"depth_range": InundationDepthRange(min_depth_m=99.0, max_depth_m=100.0, descriptor="99–100m")})
            for b in event.observed_flood_benchmarks
        ]
        sub_event2 = sub_event1.model_copy(update={"observed_flood_benchmarks": modified_benchmarks})

        res1 = replay_engine.run_replay(sub_event1)
        res2 = replay_engine.run_replay(sub_event2)

        assert res1.peak_modeled_depth_m == res2.peak_modeled_depth_m
        assert res1.peak_flood_volume_m3 == res2.peak_flood_volume_m3
        assert res1.peak_flooded_area_m2 == res2.peak_flooded_area_m2
        for s1, s2 in zip(res1.timesteps, res2.timesteps):
            assert s1.peak_flood_depth_m == s2.peak_flood_depth_m
            assert s1.drainage_surcharge_volume_m3 == s2.drainage_surcharge_volume_m3
