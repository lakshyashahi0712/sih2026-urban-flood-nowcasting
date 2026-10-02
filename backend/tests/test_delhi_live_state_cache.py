"""Delhi V2 live-state cache regression tests.

Pins the invariant that made /api/delhi/live-state rebuild the depth model on
every request in production: the cache key carried the forecast's acquisition
timestamp, and the SYNTHETIC_FALLBACK / client-assisted paths stamp that with
datetime.now(). The MODELLED physics may be reused; the freshness and
provenance fields may never be.
"""

from __future__ import annotations

import dataclasses
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.app.domain.delhi import live_state as ls


@pytest.fixture(autouse=True)
def clean_cache():
    ls._LIVE_STATES_CACHE.clear()
    yield
    ls._LIVE_STATES_CACHE.clear()


@pytest.fixture(scope="module")
def fallback_forecast():
    """One pinned fallback fetch — its hour window never moves in a test."""
    return ls.synthetic_fallback_forecast()


def _stub_fetch(monkeypatch, pinned, acquired_at):
    """Serve the pinned window with an acquisition stamp that churns per call."""
    holder = {"i": 0}

    def stub(use_cache=True):
        fetch = ls.synthetic_fallback_forecast()
        fetch.bins = pinned.bins
        fetch.acquired_at = acquired_at + timedelta(seconds=90 * holder["i"])
        holder["i"] += 1
        return fetch

    monkeypatch.setattr(ls, "fetch_forecast_with_fallback", stub)
    return stub


def test_cache_key_ignores_acquisition_timestamp(fallback_forecast):
    same_window = ls.synthetic_fallback_forecast()
    same_window.acquired_at = fallback_forecast.acquired_at + timedelta(seconds=37)
    assert same_window.acquired_at != fallback_forecast.acquired_at
    assert ls._live_states_cache_key(same_window, True) == ls._live_states_cache_key(
        fallback_forecast, True
    )


def test_cache_key_carries_every_input_that_changes_the_output(fallback_forecast):
    key = ls._live_states_cache_key(fallback_forecast, True)
    assert fallback_forecast.status in key
    assert fallback_forecast.bins[0].time_start.strftime("%Y%m%d%H") in key

    wetter = dataclasses.replace(fallback_forecast.bins[0], depth_mm=99.0)
    changed = dataclasses.replace(
        fallback_forecast, bins=(wetter,) + fallback_forecast.bins[1:]
    )
    assert ls._live_states_cache_key(changed, True) != key
    assert ls._live_states_cache_key(changed, False) != ls._live_states_cache_key(
        changed, True
    )


def test_cached_hit_reuses_physics_but_never_serves_a_stale_timestamp(monkeypatch,
                                                                       fallback_forecast):
    builds = []
    real_build = ls.build_live_states

    def counted(fetch, include_geo=True):
        builds.append(fetch)
        return real_build(fetch, include_geo=include_geo)

    monkeypatch.setattr(ls, "build_live_states", counted)
    now = datetime.now(timezone.utc)
    _stub_fetch(monkeypatch, fallback_forecast, now)

    first = ls.get_cached_live_states()
    second = ls.get_cached_live_states()

    assert len(builds) == 1, "cache missed on identical physics inputs"
    assert first["peak"] == second["peak"]
    assert first["horizons"][0]["max_depth_m"] == second["horizons"][0]["max_depth_m"]

    expected = (now + timedelta(seconds=90)).isoformat()
    assert second["rainfall_acquired_at"] == expected
    assert first["rainfall_acquired_at"] != second["rainfall_acquired_at"]
    assert second["rainfall_status"] == "SYNTHETIC_FALLBACK"
    assert any("NOT observed" in d for d in second["diagnostics"])

    stored = ls._LIVE_STATES_CACHE[next(iter(ls._LIVE_STATES_CACHE))]
    assert stored["rainfall_acquired_at"] == first["rainfall_acquired_at"], (
        "the cached entry was mutated by a response"
    )


def test_client_assisted_variant_does_not_evict_the_server_variant(monkeypatch,
                                                                   fallback_forecast):
    """Production boots BOTH variants; a single-slot cache thrashed them."""
    builds = []
    real_build = ls.build_live_states

    def counted(fetch, include_geo=True):
        builds.append(fetch.status)
        return real_build(fetch, include_geo=include_geo)

    monkeypatch.setattr(ls, "build_live_states", counted)
    _stub_fetch(monkeypatch, fallback_forecast, datetime.now(timezone.utc))

    server = ls.get_cached_live_states()
    client = ls.get_cached_live_states(client_rainfall_mm=[2.5, 12.0, 18.0, 8.0])
    again = ls.get_cached_live_states()

    assert builds == ["SYNTHETIC_FALLBACK", "COMPUTED"], f"got {builds}"
    assert server["rainfall_status"] == "SYNTHETIC_FALLBACK"
    assert client["rainfall_status"] == "COMPUTED"
    assert again["peak"] == server["peak"]
    assert len(ls._LIVE_STATES_CACHE) == 2


def test_cache_is_bounded(monkeypatch):
    """Same window, different depths = a new key each hour roll-over; never unbounded."""
    monkeypatch.setattr(
        ls, "build_live_states",
        lambda fetch, include_geo=True: {"horizons": [], "rainfall_status": fetch.status},
    )
    base = ls.synthetic_fallback_forecast()
    for i in range(ls._LIVE_STATES_CACHE_MAX + 4):
        fetch = dataclasses.replace(
            base,
            bins=tuple(
                dataclasses.replace(b, depth_mm=float(i)) for b in base.bins
            ),
        )
        monkeypatch.setattr(
            ls, "fetch_forecast_with_fallback",
            lambda use_cache=True, f=fetch: f,
        )
        ls.get_cached_live_states()
    assert len(ls._LIVE_STATES_CACHE) == ls._LIVE_STATES_CACHE_MAX
