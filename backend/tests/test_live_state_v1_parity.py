"""V1-parity live-state tests (Delhi window).

Covers:
- Per-horizon independent flood states (NOW/+1h/+2h/+3h) via the shared
  V1-reference depth model.
- Street & intersection intelligence coherence with the depth grid.
- The labeled SYNTHETIC_FALLBACK rainfall path (deterministic; never
  presented as observed or forecast weather).
- WHAT-IF scenario states: real computation, labeled MODEL_SCENARIO.
- Depth-derived road-risk override (hazard/exclusion thresholds).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.app.domain.delhi import live_state as ls
from backend.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


# ---------------------------------------------------------------------------
# Rainfall fallback
# ---------------------------------------------------------------------------


def test_synthetic_fallback_is_labeled_and_bounded():
    fb = ls.synthetic_fallback_forecast()
    assert fb.status == "SYNTHETIC_FALLBACK"
    assert len(fb.bins) == 4
    for b in fb.bins:
        assert b.provenance == "SYNTHETIC_FALLBACK"
        assert 0 <= b.depth_mm <= 50  # physically bounded demo series
    assert any("NOT observed" in d for d in fb.diagnostics)


def test_synthetic_fallback_is_deterministic():
    a = ls.synthetic_fallback_forecast()
    b = ls.synthetic_fallback_forecast()
    assert [x.depth_mm for x in a.bins] == [x.depth_mm for x in b.bins]


def test_fetch_forecast_with_fallback_never_returns_empty(monkeypatch):
    """Even when NWP is unavailable the system serves a labeled series."""

    from backend.app.domain.delhi.nowcast import DelhiForecastFetch

    def _unavailable(use_cache=True):
        return DelhiForecastFetch(
            status="UNAVAILABLE",
            reference_point="x",
            latitude=0.0,
            longitude=0.0,
            acquired_at=None,
            bins=(),
            diagnostics=["nwp down"],
        )

    monkeypatch.setattr(ls, "fetch_delhi_rainfall_forecast", _unavailable)
    fetch = ls.fetch_forecast_with_fallback()
    assert fetch.status == "SYNTHETIC_FALLBACK"
    assert len(fetch.bins) == 4
    assert any("nwp down" in d for d in fetch.diagnostics)  # original reason preserved


# ---------------------------------------------------------------------------
# Road-risk classification (V1 tiers)
# ---------------------------------------------------------------------------


def test_classify_road_risk_v1_tiers():
    assert ls.classify_road_risk(None) == "UNKNOWN"
    assert ls.classify_road_risk(0.0) == "NONE"
    assert ls.classify_road_risk(0.05) == "LOW"
    assert ls.classify_road_risk(0.2) == "MEDIUM"
    assert ls.classify_road_risk(0.35) == "HIGH"
    assert ls.classify_road_risk(0.7) == "CRITICAL"


# ---------------------------------------------------------------------------
# WHAT-IF scenario states (shared depth model; real computation)
# ---------------------------------------------------------------------------


def test_what_if_dose_response_monotonic():
    small = ls.build_what_if_state(20.0)
    big = ls.build_what_if_state(70.0)
    # V1 demo behavior: 20 mm/h fully conveyed; 70 mm/h surcharges.
    assert small["max_depth_m"] < big["max_depth_m"]
    assert big["max_depth_m"] > 0.0
    assert small["scenario"]["label"] == "WHAT-IF"
    assert "NOT live weather" in small["scenario"]["note"]


def test_what_if_rejects_out_of_range():
    with pytest.raises(ValueError):
        ls.build_what_if_state(999.0)


def test_what_if_streets_are_coherent():
    s = ls.build_what_if_state(70.0)
    st = s["streets"]
    assert st["summary"]["total_affected_roads"] > 0
    assert st["summary"]["max_street_depth_m"] <= s["max_depth_m"] + 1e-9
    assert st["provenance"]["depth"].startswith("MODELLED")
    # every affected road inherits simulated provenance
    for r in st["affected_roads"][:3]:
        assert "SIMULATED_MODEL_OUTPUT" in r["provenance"]


def test_what_if_edge_depths_and_override():
    depths = ls.get_cached_what_if_edge_depths(70.0)
    assert len(depths) > 0
    override = ls.road_risk_override_from_depths(depths)
    assert len(override) == len(depths)
    states = [v[0] for v in override.values()]
    assert any(s == "BLOCKED" for s in states)  # 70 mm/h must exclude deep roads
    assert any(s in ("LOW_RISK", "ELEVATED_RISK") for s in states)
    # UNKNOWN for unsampled segments
    partial = ls.road_risk_override_from_depths({"edge-x": None})
    assert partial["edge-x"][0] == "UNKNOWN"


# ---------------------------------------------------------------------------
# Cached builders
# ---------------------------------------------------------------------------


def test_what_if_cache_is_deterministic():
    a = ls.get_cached_what_if(50.0)
    b = ls.get_cached_what_if(50.0)
    assert a is b  # same object: cached


def test_live_states_build_from_fallback(monkeypatch):
    """The full live-state build works against the labeled fallback series."""

    monkeypatch.setattr(ls, "fetch_forecast_with_fallback", lambda use_cache=True: ls.synthetic_fallback_forecast())
    states = ls.build_live_states(ls.synthetic_fallback_forecast(), include_geo=False)
    assert states["rainfall_status"] == "SYNTHETIC_FALLBACK"
    assert len(states["horizons"]) == 4
    for h in states["horizons"]:
        assert h["status"] == "COMPUTED"
        assert h["rainfall_provenance"] == "SYNTHETIC_FALLBACK"
        assert h["streets"] is not None
    assert states["claim_policy"].startswith("MODELLED")


# ---------------------------------------------------------------------------
# API surface
# ---------------------------------------------------------------------------


class TestLiveStateAPI:
    def test_all_horizons(self, client):
        r = client.get("/api/delhi/live-state")
        assert r.status_code == 200
        body = r.json()
        assert body["rainfall_status"] in ("COMPUTED", "STALE", "SYNTHETIC_FALLBACK")
        assert len(body["horizons"]) == 4
        assert body["claim_policy"].startswith("MODELLED")

    def test_single_horizon(self, client):
        r = client.get("/api/delhi/live-state?horizon=%2B2h")
        assert r.status_code == 200
        body = r.json()
        assert body["horizon"] == "+2h"

    def test_bad_horizon(self, client):
        r = client.get("/api/delhi/live-state?horizon=NOPE")
        assert r.status_code == 400

    def test_what_if_endpoint(self, client):
        r = client.get("/api/delhi/scenario/what-if?rainfall_mm_h=40")
        assert r.status_code == 200
        body = r.json()
        assert body["scenario"]["kind"] == "MODEL_SCENARIO"
        assert body["status"] == "COMPUTED"

    def test_what_if_rejects_out_of_range(self, client):
        r = client.get("/api/delhi/scenario/what-if?rainfall_mm_h=999")
        assert r.status_code == 422

    def test_what_if_presets(self, client):
        r = client.get("/api/delhi/scenario/what-if/presets")
        assert r.status_code == 200
        assert r.json()["presets_mm_h"] == [20.0, 40.0, 50.0, 70.0]

    def test_scenario_safe_route(self, client):
        r = client.get(
            "/api/delhi/scenario/safe-route"
            "?origin_lon=77.21&origin_lat=28.565&dest_lon=77.24&dest_lat=28.575&rainfall_mm_h=70"
        )
        assert r.status_code == 200
        body = r.json()
        assert body["mode"] == "SCENARIO"
        assert body["scenario"]["label"] == "WHAT-IF"
        assert body["recommended_route"]["geometry"]["type"] == "Feature"
        assert body["claim_policy"].startswith("MODEL SCENARIO")
