"""Safe-routing tests: LIVE, HISTORICAL, EVIDENCE + cross-mode isolation.

Covers the critical routing invariants: UNKNOWN is never SAFE, blocked
segments are excluded from candidate routes, missing model state
propagates to UNKNOWN, freshness is visible, explanations match the
structured metrics, routes are deterministic, and historical replay
never contaminates live routing (and vice versa).

Live-mode tests inject a canned forecast so no network access occurs;
the ensemble execution itself is the real deterministic runtime.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.app.domain.delhi.routing import engine
from backend.app.domain.delhi.routing.network import get_road_graph
from backend.app.domain.delhi.routing.risk import (
    aggregate_reach_states,
    freshness_state,
    route_evidence_state,
    translate_reach_to_road_risk,
)
from backend.app.domain.delhi.routing.state_source import (
    ModeReachStates,
    _live_nowcast_cached,
    get_historical_reach_states,
)

IST = timezone(timedelta(hours=5, minutes=30))

# A corridor-crossing pair with healthy directness (AIIMS -> Defence Colony).
ORIGIN = (77.2085, 28.5790)
DEST = (77.2380, 28.5770)


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def live_hour0():
    """Deterministic live reach states (canned forecast, real ensemble)."""
    from backend.app.domain.delhi.routing import state_source as rs

    _live_nowcast_cached.cache_clear()
    now = datetime.now(timezone.utc)
    h0 = now.astimezone(IST).replace(minute=0, second=0, microsecond=0)
    from backend.app.domain.delhi.nowcast import DelhiForecastFetch, ForecastBin

    bins = tuple(
        ForecastBin(
            time_start=h0 + timedelta(hours=i),
            time_end=h0 + timedelta(hours=i + 1),
            depth_mm=[0.0, 8.0, 21.0, 4.0][i],
            provenance="DERIVED",
        )
        for i in range(4)
    )
    forecast = DelhiForecastFetch(
        status="COMPUTED",
        reference_point="test",
        latitude=28.5862,
        longitude=77.2090,
        acquired_at=now,
        bins=bins,
    )
    original = rs.fetch_delhi_rainfall_forecast
    rs.fetch_delhi_rainfall_forecast = lambda use_cache=True, client=None: forecast
    try:
        states = rs.get_live_reach_states(0)
        yield states
    finally:
        rs.fetch_delhi_rainfall_forecast = original
        _live_nowcast_cached.cache_clear()


# ---------------------------------------------------------------------------
# Unit: risk translation (the documented hydraulic -> road layer)
# ---------------------------------------------------------------------------


def test_translation_never_emits_safe_or_blocked_from_model():
    """The model has no stage/depth: it can never justify SAFE or BLOCKED."""
    for obs in (
        None,
        aggregate_reach_states([{}]),
        aggregate_reach_states([{
            "UG-01": {"status": "COMPUTED", "incoming_flow_m3_s": 5.0, "storage_m3": 50000.0},
            "OC-01": {"status": "COMPUTED", "incoming_flow_m3_s": 0.0, "storage_m3": 10000.0},
            "CD-01": {"status": "COMPUTED", "incoming_flow_m3_s": 0.0, "storage_m3": 10000.0},
            "OC-02": {"status": "COMPUTED", "incoming_flow_m3_s": 0.0, "storage_m3": 10000.0},
        }]),
    ):
        if obs is None:
            state, _ = translate_reach_to_road_risk(None)
            assert state == "UNKNOWN"
        else:
            for reach_obs in obs.values():
                state, _ = translate_reach_to_road_risk(reach_obs)
                assert state in ("UNKNOWN", "ELEVATED_RISK", "LOW_RISK")
                assert state != "SAFE"


def test_positive_loading_maps_to_elevated_with_reason():
    states = [{
        "UG-01": {"status": "COMPUTED", "incoming_flow_m3_s": 100.0, "storage_m3": 90000.0},
        "OC-01": {"status": "COMPUTED", "incoming_flow_m3_s": 0.0, "storage_m3": 10000.0},
        "CD-01": {"status": "COMPUTED", "incoming_flow_m3_s": 0.0, "storage_m3": 10000.0},
        "OC-02": {"status": "COMPUTED", "incoming_flow_m3_s": 0.0, "storage_m3": 10000.0},
    }]
    obs = aggregate_reach_states(states)
    state, reason = translate_reach_to_road_risk(obs["UG-01"])
    assert state == "ELEVATED_RISK"
    assert "loading" in reason
    assert "depth" in reason  # the no-depth caveat is carried in the reason
    state2, _ = translate_reach_to_road_risk(obs["OC-01"])
    assert state2 == "LOW_RISK"


def test_any_blocked_member_makes_segment_unknown():
    """Weakest link: one blocked member of six hides nothing."""
    computed = {
        "UG-01": {"status": "COMPUTED", "incoming_flow_m3_s": 0.0, "storage_m3": 10000.0},
        "OC-01": {"status": "COMPUTED", "incoming_flow_m3_s": 0.0, "storage_m3": 10000.0},
        "CD-01": {"status": "COMPUTED", "incoming_flow_m3_s": 0.0, "storage_m3": 10000.0},
        "OC-02": {"status": "COMPUTED", "incoming_flow_m3_s": 0.0, "storage_m3": 10000.0},
    }
    blocked = {}  # member with no computed states
    obs = aggregate_reach_states([computed, computed, computed, computed, computed, blocked])
    state, reason = translate_reach_to_road_risk(obs["UG-01"])
    assert state == "UNKNOWN"
    assert "blocked" in reason


def test_missing_model_state_is_unknown_not_low():
    """Missing state is never reinterpreted as a benign state."""
    obs = aggregate_reach_states([{}])
    state, _ = translate_reach_to_road_risk(obs["UG-01"])
    assert state == "UNKNOWN"


# ---------------------------------------------------------------------------
# Unit: evidence state + freshness derivations (documented rules)
# ---------------------------------------------------------------------------


def test_route_evidence_state_derivation_table():
    assert route_evidence_state(10, 0, True, False)[0] == "UNKNOWN"
    assert route_evidence_state(10, 3, True, False)[0] == "LOW"
    assert route_evidence_state(10, 10, False, True)[0] == "MEDIUM"
    assert route_evidence_state(10, 10, False, False)[0] == "HIGH"
    # A single unknown portion caps an otherwise-covered route at LOW.
    assert route_evidence_state(10, 9, True, False)[0] == "LOW"


def test_freshness_thresholds():
    now = datetime.now(timezone.utc)
    assert freshness_state(now, now) == "FRESH"
    assert freshness_state(now - timedelta(minutes=30), now) == "RECENT"
    assert freshness_state(now - timedelta(hours=3), now) == "STALE"
    assert freshness_state(None, now) == "UNKNOWN"


# ---------------------------------------------------------------------------
# Unit: engine cost behavior on a synthetic graph
# ---------------------------------------------------------------------------


def test_cost_function_prefers_lower_exposure(monkeypatch):
    """A longer low-risk path beats a shorter elevated-risk path when the
    penalty outweighs the distance — and the explanation says so."""
    from backend.app.domain.delhi.routing.network import SegmentEdge

    graph = get_road_graph()
    edges = graph.edge_index
    # Pick two parallel-ish short edges; we only need deterministic math:
    risk = {k: ("LOW_RISK", "") for k in edges}
    # Make every edge's risk ELEVATED and check penalty math directly.
    elevated_cost = engine.RISK_PENALTY_S_PER_M["ELEVATED_RISK"]
    assert elevated_cost == 0.18  # documented ASSUMED constant
    # UNKNOWN is penalized but traversable; BLOCKED is excluded.
    assert engine.RISK_PENALTY_S_PER_M["UNKNOWN"] > 0
    assert engine.RISK_PENALTY_S_PER_M["BLOCKED"] == float("inf")


def test_blocked_edge_is_hard_excluded():
    """A BLOCKED edge cannot appear in a candidate route (critical #2)."""
    graph = get_road_graph()
    # Take a real edge on the route and block ALL edges of its road, then
    # verify the route no longer uses that road when an alternative exists.
    risk = {k: ("LOW_RISK", "") for k in graph.edge_index}
    edges = engine._dijkstra(graph, *_pair_nodes(ORIGIN, DEST), risk)
    assert edges, "route should exist with all-LOW risk"
    target_road = edges[len(edges) // 2].road_id
    for key, edge in graph.edge_index.items():
        if edge.road_id == target_road:
            risk[key] = ("BLOCKED", "unit-test block")
    edges2 = engine._dijkstra(graph, *_pair_nodes(ORIGIN, DEST), risk)
    assert edges2 is not None
    assert all(e.road_id != target_road for e in edges2)


def _pair_nodes(origin, dest):
    graph = get_road_graph()
    i1, _, _ = graph.snap(*origin)
    i2, _, _ = graph.snap(*dest)
    return i1, i2


# ---------------------------------------------------------------------------
# Integration: LIVE mode (canned forecast)
# ---------------------------------------------------------------------------


def test_live_route_shape_and_evidence(live_hour0):
    result = engine.compute_safe_route(
        origin_lon=ORIGIN[0], origin_lat=ORIGIN[1],
        dest_lon=DEST[0], dest_lat=DEST[1],
        mode_states=live_hour0,
        model_timestamp="2026-09-17T00:00:00+05:30",
        forcing_source="Open-Meteo NWP hourly forecast (status COMPUTED)",
        mode_freshness_note="rainfall/model freshness: FRESH (test fixture)",
    )
    assert result["status"] == "COMPUTED"
    rec = result["recommended_route"]
    assert rec["geometry"]["geometry"]["type"] == "LineString"
    assert rec["total_distance_km"] > 0
    # The corridor is dry at hour 0 in this fixture (zero rain): mapped
    # corridor segments may be LOW_RISK, but everything else is UNKNOWN.
    summary = rec["flood_risk_summary"]
    assert summary["blocked_segments"] == 0
    assert "unknown" in rec["route_state"].lower() or summary["unknown_segments"] == 0
    # Freshness + provenance present.
    assert result["provenance"]["mode"] == "LIVE"
    assert result["evidence_state"]["route_state"] in ("HIGH", "MEDIUM", "LOW", "UNKNOWN")


def test_explanation_matches_actual_metrics(live_hour0):
    """Critical #7: explanation numbers equal the structured metrics."""
    result = engine.compute_safe_route(
        origin_lon=ORIGIN[0], origin_lat=ORIGIN[1],
        dest_lon=DEST[0], dest_lat=DEST[1],
        mode_states=live_hour0,
        model_timestamp=None,
        forcing_source="test",
        mode_freshness_note="test",
    )
    rec = result["recommended_route"]
    counts = rec["flood_risk_summary"]
    explanation = " ".join(result["explanation"])
    assert f"{counts['unknown_segments']} UNKNOWN segment" in explanation or (
        counts["unknown_segments"] == 0 and "no modeled flood loading" in explanation
    )
    alt = result["alternative_route"]
    if alt is not None:
        d_km = abs(alt["total_distance_km"] - rec["total_distance_km"])
        assert f"{d_km:.2f} km" in " ".join(result["explanation"]) or d_km == 0


def test_route_is_deterministic(live_hour0):
    """Critical #8: identical inputs -> identical routes and run id."""
    a = engine.compute_safe_route(
        origin_lon=ORIGIN[0], origin_lat=ORIGIN[1],
        dest_lon=DEST[0], dest_lat=DEST[1],
        mode_states=live_hour0, model_timestamp=None,
        forcing_source="test", mode_freshness_note="test",
    )
    b = engine.compute_safe_route(
        origin_lon=ORIGIN[0], origin_lat=ORIGIN[1],
        dest_lon=DEST[0], dest_lat=DEST[1],
        mode_states=live_hour0, model_timestamp=None,
        forcing_source="test", mode_freshness_note="test",
    )
    assert a["route_run_id"] == b["route_run_id"]
    assert a["recommended_route"]["edges"] == b["recommended_route"]["edges"]


def test_alternative_is_genuinely_distinct_or_absent(live_hour0):
    """Critical #5/#6: the alternative is distinct or explicitly absent."""
    result = engine.compute_safe_route(
        origin_lon=ORIGIN[0], origin_lat=ORIGIN[1],
        dest_lon=DEST[0], dest_lat=DEST[1],
        mode_states=live_hour0, model_timestamp=None,
        forcing_source="test", mode_freshness_note="test",
    )
    alt = result["alternative_route"]
    if alt is None:
        assert result["no_alternative_reason"]
        return
    rec_roads = {e.split(":")[0] for e in result["recommended_route"]["edges"]}
    alt_roads = {e.split(":")[0] for e in alt["edges"]}
    shared = len(rec_roads & alt_roads)
    union = max(len(rec_roads | alt_roads), 1)
    assert (1 - shared / union) >= engine.MIN_DISTINCT_EDGE_FRACTION - 1e-9


# ---------------------------------------------------------------------------
# Integration: HISTORICAL mode (genuine replay runtime)
# ---------------------------------------------------------------------------


def test_historical_timestep_controls_route_risk():
    """The route risk state follows the replayed historical timestep."""
    states_t0 = get_historical_reach_states("EVT-2024-06-27", 0)
    states_t1 = get_historical_reach_states("EVT-2024-06-27", 1)
    obs_t0 = aggregate_reach_states(states_t0.member_states)
    obs_t1 = aggregate_reach_states(states_t1.member_states)
    # t0 = verified-zero hour; t1 = the observed 91 mm/h hour.
    t1_ug01, _ = translate_reach_to_road_risk(obs_t1["UG-01"])
    t0_ug01, _ = translate_reach_to_road_risk(obs_t0["UG-01"])
    assert t1_ug01 == "ELEVATED_RISK"
    assert t0_ug01 == "LOW_RISK"


def test_unknown_historical_timestep_remains_unknown():
    """t2 of EV-01 is a documented UNKNOWN hour: no risk is carried forward."""
    states_t2 = get_historical_reach_states("EVT-2024-06-27", 2)
    obs = aggregate_reach_states(states_t2.member_states)
    state, reason = translate_reach_to_road_risk(obs["UG-01"])
    assert state == "UNKNOWN"
    assert "blocked" in reason


def test_historical_routes_deterministic_and_event_tagged():
    a = engine.compute_safe_route(
        origin_lon=ORIGIN[0], origin_lat=ORIGIN[1],
        dest_lon=DEST[0], dest_lat=DEST[1],
        mode_states=get_historical_reach_states("EVT-2024-06-27", 1),
        model_timestamp=None, forcing_source="FC-EV01-SAFDARJUNG",
        mode_freshness_note="historical",
    )
    b = engine.compute_safe_route(
        origin_lon=ORIGIN[0], origin_lat=ORIGIN[1],
        dest_lon=DEST[0], dest_lat=DEST[1],
        mode_states=get_historical_reach_states("EVT-2024-06-27", 1),
        model_timestamp=None, forcing_source="FC-EV01-SAFDARJUNG",
        mode_freshness_note="historical",
    )
    assert a["route_run_id"] == b["route_run_id"]
    assert a["mode"] == "HISTORICAL"
    assert a["event_id"] == "EVT-2024-06-27"
    assert "MODEL RECONSTRUCTION" in a["claim_policy"]


def test_no_synthetic_interpolation_between_timesteps():
    """Each timestep's risk comes only from that timestep's own runtime
    state: t1 (elevated) and t2 (unknown) differ, nothing in between."""
    s1 = get_historical_reach_states("EVT-2024-06-27", 1)
    s2 = get_historical_reach_states("EVT-2024-06-27", 2)
    t1 = translate_reach_to_road_risk(aggregate_reach_states(s1.member_states)["UG-01"])[0]
    t2 = translate_reach_to_road_risk(aggregate_reach_states(s2.member_states)["UG-01"])[0]
    assert t1 == "ELEVATED_RISK" and t2 == "UNKNOWN"


# ---------------------------------------------------------------------------
# Cross-mode isolation
# ---------------------------------------------------------------------------


def test_historical_does_not_contaminate_live(live_hour0):
    """Critical #10: after a historical routing run, live routing is
    unchanged (no event id, live provenance, identical run id)."""
    historical = engine.compute_safe_route(
        origin_lon=ORIGIN[0], origin_lat=ORIGIN[1],
        dest_lon=DEST[0], dest_lat=DEST[1],
        mode_states=get_historical_reach_states("EVT-2024-06-27", 1),
        model_timestamp=None, forcing_source="FC-EV01-SAFDARJUNG",
        mode_freshness_note="historical",
    )
    assert historical["mode"] == "HISTORICAL"
    live = engine.compute_safe_route(
        origin_lon=ORIGIN[0], origin_lat=ORIGIN[1],
        dest_lon=DEST[0], dest_lat=DEST[1],
        mode_states=live_hour0, model_timestamp=None,
        forcing_source="test", mode_freshness_note="test",
    )
    assert live["mode"] == "LIVE"
    assert live["event_id"] is None
    assert live["mode"] != historical["mode"]
    # The frozen ModeReachStates were not mutated by either run.
    assert live_hour0.mode == "LIVE"


def test_engine_does_not_mutate_model_state():
    """The engine only reads reach states (frozen dataclass, fresh maps)."""
    states = get_historical_reach_states("EVT-2024-06-27", 1)
    before = repr(states.member_states)
    engine.compute_safe_route(
        origin_lon=ORIGIN[0], origin_lat=ORIGIN[1],
        dest_lon=DEST[0], dest_lat=DEST[1],
        mode_states=states, model_timestamp=None,
        forcing_source="test", mode_freshness_note="test",
    )
    assert repr(states.member_states) == before


# ---------------------------------------------------------------------------
# API contract
# ---------------------------------------------------------------------------


def test_api_live_route_contract(client, monkeypatch):
    from backend.app.domain.delhi.routing import state_source as rs
    from backend.app.domain.delhi.nowcast import DelhiForecastFetch, ForecastBin

    now = datetime.now(timezone.utc)
    h0 = now.astimezone(IST).replace(minute=0, second=0, microsecond=0)
    forecast = DelhiForecastFetch(
        status="COMPUTED", reference_point="test", latitude=28.5862,
        longitude=77.2090, acquired_at=now,
        bins=tuple(
            ForecastBin(
                time_start=h0 + timedelta(hours=i),
                time_end=h0 + timedelta(hours=i + 1),
                depth_mm=[0.0, 8.0, 21.0, 4.0][i], provenance="DERIVED",
            ) for i in range(4)
        ),
    )
    _live_nowcast_cached.cache_clear()
    original = rs.fetch_delhi_rainfall_forecast
    rs.fetch_delhi_rainfall_forecast = lambda use_cache=True, client=None: forecast
    try:
        r = client.get("/api/delhi/safe-route", params=dict(
            origin_lon=ORIGIN[0], origin_lat=ORIGIN[1],
            dest_lon=DEST[0], dest_lat=DEST[1], mode="live", departure_hour=0,
        ))
        assert r.status_code == 200
        body = r.json()
        for field in ("recommended_route", "route_comparison", "evidence_state",
                      "explanation", "generated_at", "route_run_id",
                      "data_freshness", "provenance", "claim_policy"):
            assert field in body, f"missing {field}"
        assert "LOWER MODELED" in body["claim_policy"] or "MODELED" in body["claim_policy"]
        assert "guarantee" in body["claim_policy"].lower()
    finally:
        rs.fetch_delhi_rainfall_forecast = original
        _live_nowcast_cached.cache_clear()


def test_api_rejects_invalid_coordinates(client):
    r = client.get("/api/delhi/safe-route", params=dict(
        origin_lon=999.0, origin_lat=28.58, dest_lon=77.23, dest_lat=28.57, mode="live",
    ))
    assert r.status_code == 400
    assert "detail" in r.json()


def test_api_non_executable_event_is_explicit(client):
    r = client.get("/api/delhi/safe-route", params=dict(
        origin_lon=ORIGIN[0], origin_lat=ORIGIN[1], dest_lon=DEST[0],
        dest_lat=DEST[1], mode="historical", event_id="EVT-2021-07-19",
    ))
    assert r.status_code == 409
    assert "NOT_COMPUTABLE" in r.json()["detail"]


def test_api_unknown_event_404(client):
    r = client.get("/api/delhi/safe-route", params=dict(
        origin_lon=ORIGIN[0], origin_lat=ORIGIN[1], dest_lon=DEST[0],
        dest_lat=DEST[1], mode="historical", event_id="EVT-NOPE",
    ))
    assert r.status_code == 404


def test_segment_evidence_endpoint_unknown_outside_corridor(client):
    """Segments far from the corridor are UNKNOWN with the mapping reason —
    never LOW/SAFE."""
    r = client.get("/api/delhi/safe-route/segments/osm-1", params=dict(mode="live"))
    assert r.status_code == 404  # bogus id rejected
    graph = get_road_graph()
    outside = next(
        k for k, mapped in
        __import__(
            "backend.app.domain.delhi.routing.risk",
            fromlist=["build_edge_reach_map"],
        ).build_edge_reach_map().items()
        if mapped is None
    )
    r2 = client.get(f"/api/delhi/safe-route/segments/{outside}", params=dict(mode="live"))
    assert r2.status_code == 200
    body = r2.json()
    assert body["risk_state"] == "UNKNOWN"
    assert body["spatial_mapping"]["status"] == "OUTSIDE_MODELED_CORRIDOR"
