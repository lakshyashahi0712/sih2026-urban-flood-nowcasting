"""Client-assisted NWP ingest: the visitor's own connection supplies the forecast when our
server's shared cloud egress IP is rate-limited by Open-Meteo (HTTP 429)."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

try:
    from backend.main import app
    from backend.app.api import rainfall as rainfall_api
    from backend.app.domain.rainfall.models import RainfallProvenance, RainfallStatus
    from backend.app.infrastructure.rainfall.open_meteo import (
        OpenMeteoAdapter,
        OpenMeteoCache,
        client_assisted_series_from_hourly_mm,
    )
except ImportError:
    from main import app
    from app.api import rainfall as rainfall_api
    from app.domain.rainfall.models import RainfallProvenance, RainfallStatus
    from app.infrastructure.rainfall.open_meteo import (
        OpenMeteoAdapter,
        OpenMeteoCache,
        client_assisted_series_from_hourly_mm,
    )

client = TestClient(app)
IST = timezone(timedelta(hours=5, minutes=30))


def _empty_adapter() -> OpenMeteoAdapter:
    return OpenMeteoAdapter(cache=OpenMeteoCache(fallback_path=None))


def test_ingest_builds_live_ist_aligned_series():
    series = client_assisted_series_from_hourly_mm([0.4, 1.2, 0.0, 3.7])

    assert series.provenance == RainfallProvenance.NWP_CLIENT_ASSISTED
    assert len(series.records) == 4
    assert [r.rainfall_mm for r in series.records] == [0.4, 1.2, 0.0, 3.7]
    for record in series.records:
        assert record.status == RainfallStatus.LIVE
        assert record.provenance == RainfallProvenance.NWP_CLIENT_ASSISTED
        # Requested in Asia/Kolkata, so the bins must sit on full IST hours.
        assert record.timestamp.astimezone(IST).minute == 0
        assert record.forecast_lead_minutes >= 0
    assert series.records[1].timestamp - series.records[0].timestamp == timedelta(hours=1)
    assert series.records[0].forecast_lead_minutes == 0


@pytest.mark.parametrize(
    "values",
    [
        [1.0, 2.0, 3.0],
        [1.0, 2.0, 3.0, -1.0],
        [1.0, 2.0, 3.0, 501.0],
        [1.0, 2.0, 3.0, float("nan")],
    ],
    ids=["three-hours", "negative", "implausible", "nan"],
)
def test_ingest_rejects_unusable_values(values):
    with pytest.raises(ValueError):
        client_assisted_series_from_hourly_mm(values)


@pytest.mark.asyncio
async def test_fresh_client_assisted_cache_is_served_without_a_network_attempt():
    adapter = _empty_adapter()
    adapter.ingest_client_forecast([0.5, 0.5, 0.5, 0.5])

    attempts = []

    async def _no_network():
        attempts.append(1)
        raise AssertionError("must not re-ask Open-Meteo for an ingested window")

    adapter._fetch_live = _no_network
    served = await adapter.fetch(use_cache=True)

    assert attempts == []
    assert served.records[0].status == RainfallStatus.LIVE


@pytest.mark.asyncio
async def test_expired_client_assisted_cache_is_marked_stale_not_fallback():
    adapter = _empty_adapter()
    adapter.ingest_client_forecast([0.5, 0.5, 0.5, 0.5])
    adapter.cache._timestamp = datetime.now(timezone.utc) - timedelta(hours=2)

    async def _rate_limited():
        raise RuntimeError("HTTP 429 Daily API request limit exceeded")

    adapter._fetch_live = _rate_limited
    served = await adapter.fetch(use_cache=True)

    assert served.records[0].status == RainfallStatus.STALE
    assert served.provenance == RainfallProvenance.NWP_CLIENT_ASSISTED


@pytest.mark.asyncio
async def test_server_live_fetch_wins_over_a_client_ingest():
    adapter = _empty_adapter()
    ours = client_assisted_series_from_hourly_mm([1.0, 1.0, 1.0, 1.0]).model_copy(
        update={"provenance": RainfallProvenance.NWP_CORRECTED}
    )
    adapter.cache.set(ours)

    served = adapter.ingest_client_forecast([9.0, 9.0, 9.0, 9.0])

    assert served.provenance == RainfallProvenance.NWP_CORRECTED
    assert served.records[0].rainfall_mm == 1.0


def test_nwp_ingest_endpoint_accepts_four_hours(monkeypatch):
    adapter = _empty_adapter()
    monkeypatch.setattr(rainfall_api, "_adapter", adapter)

    response = client.post("/flood/nwp-ingest", json={"rainfall_mm": [0.6, 1.1, 0.0, 0.2]})

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ACCEPTED"
    assert body["provenance"] == RainfallProvenance.NWP_CLIENT_ASSISTED.value
    assert len(body["horizon_starts_utc"]) == 4
    assert adapter.cache.get(allow_stale=False) is not None


@pytest.mark.parametrize(
    "values",
    [[0.6, 1.1, 0.0], [0.6, 1.1, 0.0, -2.0], [0.6, 1.1, 0.0, 4000.0]],
    ids=["three-hours", "negative", "implausible"],
)
def test_nwp_ingest_endpoint_rejects_bad_payload(monkeypatch, values):
    adapter = _empty_adapter()
    monkeypatch.setattr(rainfall_api, "_adapter", adapter)

    response = client.post("/flood/nwp-ingest", json={"rainfall_mm": values})

    assert response.status_code in (422, 400)
    assert adapter.cache.get(allow_stale=True) is None
