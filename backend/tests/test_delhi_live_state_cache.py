"""Delhi V2 live-state cache regression tests.

Pins the invariant that made /api/delhi/live-state rebuild the depth model on
every request in production: the cache key carried the forecast's acquisition
timestamp, and the SYNTHETIC_FALLBACK / client-assisted paths stamp that with
datetime.now(). The MODELLED physics may be reused; the freshness and
provenance fields may never be.
"""

from __future__ import annotations

import dataclasses
import itertools
import sys
import threading
import time
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


def test_cold_stampede_builds_once(monkeypatch, fallback_forecast):
    """A boot warm-up and a first visitor must not build the same window twice.

    This is the concurrency half of the fix: the memo is a plain dict, so
    without the build lock every thread that arrives at a cold cache runs a
    full depth-model step. Two parallel 18 s builds was the measured failure.
    """
    builds = []
    real_build = ls.build_live_states

    def slow_build(fetch, include_geo=True):
        # Long enough that every other caller is parked on the lock before the
        # first build finishes; with no lock all four would run this body.
        time.sleep(0.3)
        builds.append(fetch.status)
        return real_build(fetch, include_geo=include_geo)

    monkeypatch.setattr(ls, "build_live_states", slow_build)

    now = datetime.now(timezone.utc)
    counter = itertools.count()
    stamp_lock = threading.Lock()

    def stub(use_cache=True):
        fetch = ls.synthetic_fallback_forecast()
        fetch.bins = fallback_forecast.bins
        with stamp_lock:
            i = next(counter)
        # Same physics, a fresh acquisition stamp per call — production churn.
        fetch.acquired_at = now + timedelta(seconds=90 * i)
        return fetch

    monkeypatch.setattr(ls, "fetch_forecast_with_fallback", stub)

    results = {}

    def run(idx):
        results[idx] = ls.get_cached_live_states()

    threads = [threading.Thread(target=run, args=(i,)) for i in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=60)

    assert len(builds) == 1, f"cold cache ran {len(builds)} builds"
    assert len(results) == 4
    assert {r["rainfall_acquired_at"] for r in results.values()} == {
        (now + timedelta(seconds=90 * i)).isoformat() for i in range(4)
    }, "a concurrent response was served another request's timestamp"


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
