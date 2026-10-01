"""Tests for the modelled-state memo in the Mumbai flood router.

The contract being pinned here is narrow: the *physics* of a model run may be
reused, but nothing that describes data freshness may be. So two responses built
from different rainfall series must not share timestamps, status or provenance,
even when their rainfall depths happen to match.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

try:
    from backend.routers import flood as flood_router
    from backend.app.domain.rainfall.models import (
        RainfallProvenance,
        RainfallRecord,
        RainfallSeries,
        RainfallStatus,
        SourceType,
    )
except ImportError:
    from routers import flood as flood_router
    from app.domain.rainfall.models import (
        RainfallProvenance,
        RainfallRecord,
        RainfallSeries,
        RainfallStatus,
        SourceType,
    )


AREA = 500000.0
COEF = 0.7
THRESHOLD = 15000.0


class _CountingPipeline:
    """Wraps the real pipeline so tests can count model runs without faking physics."""

    def __init__(self):
        self.real = flood_router.run_flood_modeling_pipeline
        self.rainfalls: list[float] = []

    def __call__(self, **kwargs):
        self.rainfalls.append(float(kwargs["rainfall_mm"]))
        return self.real(**kwargs)


class _FakeAdapter:
    def __init__(self, series: RainfallSeries):
        self._series = series

    async def fetch(self, use_cache: bool = True) -> RainfallSeries:
        return self._series


def _series(rainfalls: list[float], acquired_at: datetime,
            provenance: RainfallProvenance = RainfallProvenance.NWP_CORRECTED) -> RainfallSeries:
    records = []
    for i, mm in enumerate(rainfalls):
        start = acquired_at + timedelta(hours=i)
        records.append(RainfallRecord(
            timestamp=start,
            interval_end=start + timedelta(hours=1),
            rainfall_mm=mm,
            source="open-meteo",
            source_type=SourceType.FORECAST,
            resolution_minutes=60,
            acquired_at=acquired_at,
            forecast_lead_minutes=0,
            status=RainfallStatus.LIVE,
            provenance=provenance,
        ))
    return RainfallSeries(records=records, source="open-meteo", acquired_at=acquired_at, provenance=provenance)


@pytest.fixture(autouse=True)
def _fresh_cache(monkeypatch):
    """Every test starts with an empty memo and a counted pipeline."""
    flood_router.clear_modelled_state_cache()
    counter = _CountingPipeline()
    monkeypatch.setattr(flood_router, "run_flood_modeling_pipeline", counter)
    yield counter
    flood_router.clear_modelled_state_cache()


def test_same_rainfall_value_is_modeled_once(_fresh_cache):
    counter = _fresh_cache
    first = flood_router._modelled_horizon_state(35.0, AREA, COEF, THRESHOLD)
    second = flood_router._modelled_horizon_state(35.0, AREA, COEF, THRESHOLD)

    assert counter.rainfalls == [35.0]
    assert first is second


def test_different_catchment_parameters_is_a_different_state(_fresh_cache):
    counter = _fresh_cache
    flood_router._modelled_horizon_state(35.0, AREA, COEF, THRESHOLD)
    flood_router._modelled_horizon_state(35.0, AREA, 0.9, THRESHOLD)

    assert counter.rainfalls == [35.0, 35.0]


@pytest.mark.asyncio
async def test_repeated_series_runs_the_pipeline_four_times_only(_fresh_cache, monkeypatch):
    counter = _fresh_cache
    series = _series([0.0, 15.0, 30.0, 50.0], datetime(2026, 10, 1, 12, 0, tzinfo=timezone.utc))
    monkeypatch.setattr(flood_router, "get_adapter", lambda: _FakeAdapter(series))

    first = await flood_router.compute_flood_forecast_evolution(use_cache=True)
    runs_after_first = len(counter.rainfalls)
    second = await flood_router.compute_flood_forecast_evolution(use_cache=True)

    assert runs_after_first == 4
    assert len(counter.rainfalls) == 4, "second request must not re-run the model"
    assert [h.rainfall_mm for h in second.horizons] == [0.0, 15.0, 30.0, 50.0]
    assert [h.max_depth_m for h in second.horizons] == [h.max_depth_m for h in first.horizons]


@pytest.mark.asyncio
async def test_response_freshness_fields_are_never_cached(_fresh_cache, monkeypatch):
    counter = _fresh_cache
    earlier = _series([0.0, 15.0, 30.0, 50.0], datetime(2026, 10, 1, 12, 0, tzinfo=timezone.utc))
    later = _series(
        [0.0, 15.0, 30.0, 50.0],
        datetime(2026, 10, 1, 13, 0, tzinfo=timezone.utc),
        provenance=RainfallProvenance.NWP_CLIENT_ASSISTED,
    )

    responses = []
    for series in (earlier, later):
        monkeypatch.setattr(flood_router, "get_adapter", lambda s=series: _FakeAdapter(s))
        responses.append(await flood_router.compute_flood_forecast_evolution(use_cache=True))

    stale, fresh = responses
    assert stale.acquired_at != fresh.acquired_at
    assert stale.horizons[0].timestamp != fresh.horizons[0].timestamp
    assert "client-assisted" in fresh.provenance["rainfall"]
    assert "client-assisted" not in stale.provenance["rainfall"]
    # Identical rainfall depths, so the physics was reused rather than recomputed.
    assert len(counter.rainfalls) == 4


def test_street_intelligence_is_reused_per_rainfall_and_horizon(_fresh_cache):
    counter = _fresh_cache
    first = flood_router._compute_street_intelligence_for_depth(40.0, "+1h", "+1h")
    again = flood_router._compute_street_intelligence_for_depth(40.0, "+1h", "+1h")
    other_horizon = flood_router._compute_street_intelligence_for_depth(40.0, "+2h", "+2h")

    assert len(counter.rainfalls) == 2
    assert first is again
    assert other_horizon is not first


def test_expired_entry_is_recomputed(_fresh_cache, monkeypatch):
    counter = _fresh_cache
    flood_router._modelled_horizon_state(35.0, AREA, COEF, THRESHOLD)
    monkeypatch.setattr(flood_router, "_MODELLED_STATE_TTL_S", -1.0)
    flood_router._modelled_horizon_state(35.0, AREA, COEF, THRESHOLD)

    assert counter.rainfalls == [35.0, 35.0]


def test_cache_stays_bounded(_fresh_cache):
    for mm in range(60):
        flood_router._modelled_horizon_state(float(mm), AREA, COEF, THRESHOLD)

    assert len(flood_router._modelled_state_cache) <= flood_router._MODELLED_STATE_MAX_ENTRIES
