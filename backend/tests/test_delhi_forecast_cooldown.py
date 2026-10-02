"""Delhi NWP acquisition-failure cooldown tests.

Render's cloud egress is per-IP rate limited. Before the cooldown existed, a
failed Open-Meteo attempt was not cached at all, so every single request paid
a fresh doomed call before the live-state memo was even consulted.
"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.app.domain.delhi import nowcast as nc


class _FailingClient:
    """Transport double that counts attempts and always raises (like a 429)."""

    def __init__(self, error="HTTP 429 rate limited"):
        self.calls = 0
        self.error = error

    def get(self, url, timeout=None):
        self.calls += 1
        raise RuntimeError(self.error)


class _Attempted(BaseException):
    """Raised by a transport double that must NOT run.

    A BaseException, because the acquisition path wraps its egress in a broad
    ``except Exception`` for the honest degraded state — a normal exception
    raised here would be swallowed and the test would pass by accident.
    """


class _NeverCalledClient:
    def get(self, url, timeout=None):  # pragma: no cover - must not run
        raise _Attempted("attempt made while the failure was cooling off")


def _ok_client():
    """A transport double returning a well-formed Open-Meteo payload.

    Hourly timestamps use the provider's ``YYYY-MM-DDTHH:MM`` form; any other
    shape parses to zero bins and yields UNAVAILABLE, which is a payload bug
    in the double, not a product bug.
    """
    now = datetime.now(timezone.utc).astimezone(nc.IST)
    hours = [
        (now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=i)).strftime(
            "%Y-%m-%dT%H:%M"
        )
        for i in range(6)
    ]

    class _Ok:
        def __init__(self):
            self.calls = 0

        def get(self, url, timeout=None):
            self.calls += 1

            class _R:
                def raise_for_status(self):
                    return None

                def json(self):
                    return {
                        "hourly": {
                            "time": hours,
                            "precipitation": [1.0, 2.0, 3.0, 4.0, 0.0, 0.0],
                        }
                    }

            return _R()

    return _Ok()


@pytest.fixture(autouse=True)
def reset_cache():
    nc._CACHE.__init__()
    yield
    nc._CACHE.__init__()


def test_failure_is_recorded_and_honest():
    client = _FailingClient()
    fetch = nc.fetch_delhi_rainfall_forecast(use_cache=True, client=client)
    assert fetch.status == "UNAVAILABLE"
    assert client.calls == 1
    assert any("acquisition failed" in d for d in fetch.diagnostics)


def test_next_request_inside_cooldown_makes_no_attempt():
    failing = _FailingClient()
    nc.fetch_delhi_rainfall_forecast(use_cache=True, client=failing)
    assert failing.calls == 1

    silent = _NeverCalledClient()
    fetch = nc.fetch_delhi_rainfall_forecast(use_cache=True, client=silent)

    assert fetch.status == "UNAVAILABLE"
    assert any("attempt skipped" in d and "429" in d for d in fetch.diagnostics), (
        fetch.diagnostics
    )


def test_cooldown_expiry_retries():
    failing = _FailingClient()
    nc.fetch_delhi_rainfall_forecast(use_cache=True, client=failing)
    # Age the failure past the cooldown instead of waiting for it.
    nc._CACHE._failed_at -= timedelta(seconds=nc.FAILURE_COOLDOWN_SECONDS + 1)

    nc.fetch_delhi_rainfall_forecast(use_cache=True, client=failing)
    assert failing.calls == 2


def test_refresh_bypasses_the_cooldown():
    """An explicit ?refresh=true is an operator asking for a real attempt."""
    failing = _FailingClient()
    nc.fetch_delhi_rainfall_forecast(use_cache=True, client=failing)

    ok = _ok_client()
    fetch = nc.fetch_delhi_rainfall_forecast(use_cache=False, client=ok)
    assert ok.calls == 1
    assert fetch.status == "COMPUTED"


def test_a_success_clears_the_cooldown():
    failing = _FailingClient()
    nc.fetch_delhi_rainfall_forecast(use_cache=True, client=failing)
    assert nc._CACHE._failed_at is not None

    # The attempt that succeeds must be an explicit refresh: while a failure
    # is cooling off, the cached path deliberately makes no attempt at all.
    fetch = nc.fetch_delhi_rainfall_forecast(use_cache=False, client=_ok_client())
    assert fetch.status == "COMPUTED"
    assert nc._CACHE._failed_at is None
    assert nc._CACHE._failure is None

    silent = _NeverCalledClient()
    after = nc.fetch_delhi_rainfall_forecast(use_cache=True, client=silent)
    assert after.status == "COMPUTED"  # served from the fresh cache, no egress


def test_cooldown_still_serves_the_last_good_fetch_as_stale():
    """Cooling off must not erase real data: it degrades to STALE, not blank."""
    first = nc.fetch_delhi_rainfall_forecast(use_cache=False, client=_ok_client())
    assert first.status == "COMPUTED"

    # Expire the freshness window, then fail one attempt.
    nc._CACHE._acquired -= timedelta(minutes=nc.CACHE_TTL_MINUTES + 1)
    nc.fetch_delhi_rainfall_forecast(use_cache=True, client=_FailingClient())

    cooling = nc.fetch_delhi_rainfall_forecast(use_cache=True, client=_NeverCalledClient())
    assert cooling.status == "STALE"
    assert cooling.bins == first.bins
    assert any("attempt skipped" in d for d in cooling.diagnostics)
