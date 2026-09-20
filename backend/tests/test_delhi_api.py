"""Tests for the Delhi/Kushak V2 API surface and the nowcast service.

The replay endpoints execute the genuine deterministic runtime (the same
Phase 15.5 harness), so they are slower but assert real scientific
invariants. The nowcast fetch is exercised with an injected fake client —
no network access is required or permitted in tests.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from backend.main import app


IST = timezone(timedelta(hours=5, minutes=30))


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


# ---------------------------------------------------------------------------
# Health / readiness
# ---------------------------------------------------------------------------


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_ready_reports_component_checks(client):
    r = client.get("/ready")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] in ("READY", "NOT_READY")
    assert "delhi_router_import" in body["checks"]
    assert "delhi_event_catalog" in body["checks"]


# ---------------------------------------------------------------------------
# Status / ensemble / network — static contract surfaces
# ---------------------------------------------------------------------------


def test_delhi_status_exposes_non_claims(client):
    r = client.get("/api/delhi/status")
    assert r.status_code == 200
    body = r.json()
    assert body["components"]["ensemble"]["member_count"] == 6
    assert body["components"]["reach_chain"]["reach_ids"] == [
        "UG-01", "OC-01", "CD-01", "OC-02"
    ]
    # The system must state what it does NOT claim.
    non_claims = " ".join(body["explicit_non_claims"]).lower()
    assert "depth" in non_claims
    assert "calibrat" in non_claims


def test_ensemble_is_deterministic_six_members(client):
    r1 = client.get("/api/delhi/ensemble").json()
    r2 = client.get("/api/delhi/ensemble").json()
    assert r1["member_count"] == 6
    assert [m["member_id"] for m in r1["members"]] == [m["member_id"] for m in r2["members"]]
    for m in r1["members"]:
        assert m["runoff_coefficient"]["provenance"] == "ASSUMED"
        assert m["catchment_scenario"]["provenance"] == "PROVISIONAL"


def test_network_preserves_terminal_and_separation(client):
    body = client.get("/api/delhi/network").json()
    assert body["terminal_reach"] == "OC-02"
    ids = body["order"]
    assert ids == ["UG-01", "OC-01", "CD-01", "OC-02"]
    # Non-overlapping monotonic chainage.
    reaches = body["reaches"]
    for prev, nxt in zip(reaches, reaches[1:]):
        assert nxt["start_chainage_m"] == prev["end_chainage_m"]
    # Qudesia separation must be stated, never implied merged.
    assert "Qudesia" in body["catchment_note"]
    # UG-01 must be flagged as hydraulically blocked (geometry UNKNOWN).
    ug01 = next(r for r in reaches if r["reach_id"] == "UG-01")
    assert "BLOCKED" in ug01["hydraulic_status"]


# ---------------------------------------------------------------------------
# Event catalogue + replay
# ---------------------------------------------------------------------------


def test_events_catalogue_lists_executable_events(client):
    body = client.get("/api/delhi/events").json()
    assert body["catalog_size"] >= 6
    assert set(body["executable_event_ids"]) == {"EVT-2024-06-27", "EVT-2023-07-08"}


def test_replay_ev01_executes_full_runtime(client):
    r = client.get("/api/delhi/events/EVT-2024-06-27/replay")
    assert r.status_code == 200
    body = r.json()
    assert body["runtime_status"] == "EXECUTED"
    assert body["ensemble_size"] == 6
    assert len(body["members"]) == 6

    # Forcing resolution preserved: catalog bins -> timesteps 1:1.
    assert body["forcing"]["resolution_preserved"] is True

    # UNKNOWN bins must remain UNKNOWN (None) in the inflow series —
    # the 91 mm/h observed hour is followed by two UNKNOWN hours.
    m0 = body["members"][0]
    discharges = [s["discharge_m3_s"] for s in m0["inflow_steps"]]
    assert discharges[1] is not None and discharges[1] > 0
    assert discharges[2] is None and discharges[3] is None

    # Classification must stay UNKNOWN (no stage may be invented).
    cls = m0["chain_steps"][0]["classifications"]
    assert all(c["classification"] == "UNKNOWN" for c in cls)

    # Validation is DERIVED, never OBSERVED.
    assert m0["validation"]["result_provenance"] == "DERIVED"


def test_replay_is_cached_deterministic(client):
    a = client.get("/api/delhi/events/EVT-2023-07-08/replay").json()
    b = client.get("/api/delhi/events/EVT-2023-07-08/replay").json()
    assert a["members"][0]["inflow_steps"] == b["members"][0]["inflow_steps"]


def test_replay_non_executable_event_preserves_unknown(client):
    body = client.get("/api/delhi/events/EVT-2021-07-19/replay").json()
    assert body["runtime_status"] == "NOT_EXECUTED"
    assert "BLOCKED_MISSING_FORCING" in body["reason"]
    assert body["members"] == []


def test_replay_partial_event_executes_defensible_portion(client):
    """EVT-2021-09-11 (EV-03): only the documented 3-hour block runs, at
    native resolution, with the remainder explicitly UNKNOWN."""
    body = client.get("/api/delhi/events/EVT-2021-09-11/replay").json()
    assert body["runtime_status"] == "PARTIAL_EXECUTED"
    assert body["replay_status"] == "PARTIAL"
    assert body["ensemble_size"] == 6
    bins = body["forcing"]["bins"]
    assert bins[0]["depth_mm"] == 80.0 and bins[0]["provenance"] == "OBSERVED_DIRECT"
    assert bins[1]["depth_mm"] is None and bins[1]["provenance"] == "UNKNOWN"
    m0 = body["members"][0]
    assert m0["inflow_steps"][0]["discharge_m3_s"] is not None
    assert m0["inflow_steps"][1]["discharge_m3_s"] is None


def test_event_artifact_endpoint(client):
    r = client.get("/api/delhi/events/EVT-2024-06-27/artifact")
    assert r.status_code == 200
    body = r.json()
    assert body["runtime_status"] == "EXECUTED"
    for field in ("event_id", "resolved_event_id", "forcing_source",
                  "forcing_timesteps", "hydraulic_states", "routing_states",
                  "uncertainty_states", "unknown_intervals",
                  "blocked_intervals", "repository_revision"):
        assert field in body


def test_replay_unknown_event_404(client):
    r = client.get("/api/delhi/events/EVT-DOES-NOT-EXIST/replay")
    assert r.status_code == 404


def test_replay_summary_pass(client):
    body = client.get("/api/delhi/replay/summary").json()
    assert body["verdict"] == "PASS"
    for rec in body["records"]:
        if rec["event_id"] in ("EVT-2024-06-27", "EVT-2023-07-08"):
            assert rec["runtime_executed"] == "YES"
            assert rec["ensemble_members_executed"] == 6


# ---------------------------------------------------------------------------
# Nowcast service (deterministic, injected forecast — no network)
# ---------------------------------------------------------------------------


def _fake_fetch(depths=(0.0, 5.2, 12.0, 3.1)):
    from backend.app.domain.delhi.nowcast import DelhiForecastFetch, ForecastBin

    now = datetime.now(timezone.utc)
    h0 = now.astimezone(IST).replace(minute=0, second=0, microsecond=0)
    bins = tuple(
        ForecastBin(
            time_start=h0 + timedelta(hours=i),
            time_end=h0 + timedelta(hours=i + 1),
            depth_mm=depths[i],
            provenance="DERIVED" if depths[i] is not None else "UNKNOWN",
        )
        for i in range(len(depths))
    )
    return DelhiForecastFetch(
        status="COMPUTED",
        reference_point="test",
        latitude=28.5862,
        longitude=77.2090,
        acquired_at=now,
        bins=bins,
    )


def test_nowcast_service_executes_and_is_deterministic():
    from backend.app.domain.delhi.nowcast import run_nowcast

    result = run_nowcast(_fake_fetch())
    assert result.status == "COMPUTED"
    assert len(result.members) == 6
    again = run_nowcast(_fake_fetch())
    for a, b in zip(result.members, again.members):
        assert [q for _, q in a.inflow_steps] == [q for _, q in b.inflow_steps]


def test_nowcast_unknown_bin_propagates_as_none():
    from backend.app.domain.delhi.nowcast import run_nowcast

    result = run_nowcast(_fake_fetch(depths=(None, 5.2, 12.0, 3.1)))
    m0 = result.members[0]
    # The missing hour stays UNKNOWN; later hours are computed from their
    # own documented forecast values (per-step UNKNOWN preservation).
    assert m0.inflow_steps[0][1] is None
    assert m0.inflow_steps[2][1] is not None


def test_nowcast_unavailable_forecast_blocks_never_fabricates():
    from backend.app.domain.delhi.nowcast import DelhiForecastFetch, run_nowcast

    fetch = DelhiForecastFetch(
        status="UNAVAILABLE",
        reference_point="test",
        latitude=28.5862,
        longitude=77.2090,
        acquired_at=None,
        bins=(),
        diagnostics=["forced failure"],
    )
    result = run_nowcast(fetch)
    assert result.status == "BLOCKED_MISSING_FORCING"
    assert result.members == ()


def test_nowcast_endpoint_with_injected_client(client, monkeypatch):
    from backend.app.domain.delhi import nowcast as nc

    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            now = datetime.now(timezone.utc).astimezone(IST)
            h0 = now.replace(minute=0, second=0, microsecond=0)
            # Build a two-day series so the window lookup has anchors.
            start = h0 - timedelta(hours=24)
            times = [
                (start + timedelta(hours=i)).strftime("%Y-%m-%dT%H:%M")
                for i in range(72)
            ]
            precip = [1.0 * (i % 5) for i in range(72)]
            return {"hourly": {"time": times, "precipitation": precip}}

    def fake_http_get(url, timeout):
        return FakeResponse()

    monkeypatch.setattr(nc, "_http_get", fake_http_get)
    monkeypatch.setattr(
        "backend.routers.delhi.fetch_delhi_rainfall_forecast",
        lambda use_cache=True, client=None: nc.fetch_delhi_rainfall_forecast(
            use_cache=False
        ),
    )
    r = client.get("/api/delhi/nowcast?refresh=true")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "COMPUTED"
    assert len(body["forecast"]["bins"]) == 4
    assert len(body["members"]) == 6
    # Every bin must carry DERIVED forecast provenance (model value).
    assert all(b["provenance"] == "DERIVED" for b in body["forecast"]["bins"])


def test_nowcast_endpoint_degrades_without_network(client, monkeypatch):
    from backend.app.domain.delhi import nowcast as nc

    def boom(url, timeout):
        raise ConnectionError("no network in test")

    monkeypatch.setattr(nc, "_http_get", boom)
    monkeypatch.setattr(
        "backend.routers.delhi.fetch_delhi_rainfall_forecast",
        lambda use_cache=True, client=None: nc.fetch_delhi_rainfall_forecast(
            use_cache=False
        ),
    )
    r = client.get("/api/delhi/nowcast?refresh=true")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "BLOCKED_MISSING_FORCING"
    assert body["forecast"]["status"] == "UNAVAILABLE"
    assert body["members"] == []


# ---------------------------------------------------------------------------
# Geo layers
# ---------------------------------------------------------------------------


def test_geo_layers_allowlist(client):
    body = client.get("/api/delhi/layers").json()
    ids = {l["layer_id"] for l in body["layers"]}
    assert {"corridor_centerline", "watershed", "gsdl_occurrences"} <= ids


def test_geo_layer_unknown_404(client):
    assert client.get("/api/delhi/geo/not_a_layer").status_code == 404


def test_geo_layer_watershed_served_with_provenance(client):
    body = client.get("/api/delhi/geo/watershed").json()
    assert body["feature_count"] >= 1
    assert "PROVISIONAL" in body["provenance"]
    geo = body["geojson"]
    assert geo["type"] == "FeatureCollection"
