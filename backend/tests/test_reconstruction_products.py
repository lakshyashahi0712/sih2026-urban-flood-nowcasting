"""Tests for the reconstruction products: DERIVED drainage graph,
per-node loading, estimated-depth layer, 2D surface pass, and the Delhi
radar composite (provenance discipline preserved throughout).

Critical invariants:
- POTENTIAL_OVERLOAD is a capacity-class breach, never a depth claim.
- UNKNOWN model state is UNKNOWN loading, never NO_LOADING.
- Depth estimates are labeled ESTIMATED_UNDER_ASSUMED_GEOMETRY, never
  observed, and carry a caveat.
- The surface pass never runs on UNKNOWN forcing (never zero-fills).
- Open-Meteo is never called radar; visual GIFs are never quantitative.
"""

from __future__ import annotations

import math

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.app.domain.delhi.drainage.graph import (
    build_drainage_graph,
    get_drainage_graph,
    graph_to_geojson,
)
from backend.app.domain.delhi.drainage.loading import (
    channel_depth_estimate_cm,
    depth_estimates_for_reach_states,
    edge_loading_for_reach_states,
)
from backend.app.domain.delhi.radar import (
    DelhiRadarProbeResult,
    any_quantitative_delhi_radar,
    delhi_rainfall_composite,
)
from backend.app.domain.delhi.surface import get_surface_structure
from backend.app.domain.delhi.routing.state_source import (
    get_historical_reach_states,
    get_live_reach_states,
)


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


# ---------------------------------------------------------------------------
# Drainage graph: structure + provenance
# ---------------------------------------------------------------------------


def test_graph_structure_and_provenance():
    g = get_drainage_graph()
    assert len(g.nodes) == 9  # corridor origin + 7 cross-sections + confluence
    assert len(g.edges) == 8
    # Chainage-ordered, contiguous, upstream -> downstream.
    for prev, nxt in zip(g.edges, g.edges[1:]):
        assert nxt.chainage_start_m == pytest.approx(prev.chainage_end_m)
    # Every edge carries a documented capacity range + provenance.
    for e in g.edges:
        assert 0 < e.capacity_min_m3_s <= e.capacity_max_m3_s
        assert "INFERRED_EFFECTIVE" in e.capacity_provenance
        assert e.dimension_basis
        assert len(e.geometry_wgs84) >= 2
    # Node provenance says DERIVED, never surveyed.
    for n in g.nodes:
        assert "DERIVED" in n.provenance or "documented" in n.evidence.lower()


def test_graph_capacity_is_physically_plausible():
    """After the backbone-slope selection fix, capacities must be in the
    tens-of-m3/s class, not thousands (the old 1.02 m/m slope artifact)."""
    g = get_drainage_graph()
    for e in g.edges:
        assert e.capacity_max_m3_s < 600.0, (
            f"{e.edge_id} capacity {e.capacity_max_m3_s} is implausibly large"
        )
    ug = next(e for e in g.edges if e.reach_id == "UG-01")
    assert ug.capacity_min_m3_s > 50.0  # 4 m x 3.5 m box at documented slope


def test_graph_geojson_shape():
    gj = graph_to_geojson()
    assert len(gj["nodes"]["features"]) == 9
    assert len(gj["edges"]["features"]) == 8
    node = gj["nodes"]["features"][0]
    assert abs(node["geometry"]["coordinates"][0]) < 78.0  # WGS84 lon (Delhi)


# ---------------------------------------------------------------------------
# Per-node loading (critical: UNKNOWN -> UNKNOWN, never NO_LOADING)
# ---------------------------------------------------------------------------


def test_loading_unknown_state_is_never_no_loading():
    states = get_historical_reach_states("EVT-2024-06-27", 2)  # UNKNOWN hour
    edges = edge_loading_for_reach_states(states)
    by_id = {e.edge_id: e for e in edges}
    # UG-01 head reach is blocked at the UNKNOWN hour -> UNKNOWN loading.
    assert by_id["E00"].status == "UNKNOWN"
    assert "blocked" in by_id["E00"].reason.lower() or "unknown" in by_id["E00"].reason.lower()


def test_loading_zero_inflow_is_no_loading():
    states = get_historical_reach_states("EVT-2024-06-27", 0)  # verified-zero hour
    edges = edge_loading_for_reach_states(states)
    by_id = {e.edge_id: e for e in edges}
    assert by_id["E00"].status == "NO_LOADING"
    assert by_id["E00"].inflow_m3_s == 0.0


def test_peak_hour_overloads_the_box_conduit():
    """The 91 mm/h hour pushes 538 m3/s into a ~76-142 m3/s full-bore class:
    the documented lower bound is breached -> POTENTIAL_OVERLOAD, with a
    reason that never claims observed flooding or depth."""
    states = get_historical_reach_states("EVT-2024-06-27", 1)
    edges = edge_loading_for_reach_states(states)
    by_id = {e.edge_id: e for e in edges}
    assert by_id["E00"].status == "POTENTIAL_OVERLOAD"
    assert by_id["E00"].inflow_m3_s > by_id["E00"].capacity_min_m3_s
    reason = by_id["E00"].reason.lower()
    assert "not observed" in reason and "depth" in reason


def test_loading_reasons_carry_every_field():
    states = get_historical_reach_states("EVT-2024-06-27", 1)
    e = edge_loading_for_reach_states(states)[0]
    for field in ("edge_id", "node_id", "reach_id", "inflow_m3_s",
                  "capacity_min_m3_s", "capacity_max_m3_s", "status", "reason"):
        assert field in e.__dict__


# ---------------------------------------------------------------------------
# Estimated-depth layer (honest labels; range not point)
# ---------------------------------------------------------------------------


def test_depth_estimate_unknown_storage():
    est = channel_depth_estimate_cm(get_drainage_graph().edges[0], storage_m3=None)
    assert est["depth_min_cm"] is None and est["depth_max_cm"] is None
    assert est["status"] == "UNKNOWN"


def test_depth_estimate_range_and_labels():
    edge = next(e for e in get_drainage_graph().edges if e.reach_id == "UG-01")
    est = channel_depth_estimate_cm(edge, storage_m3=10000.0 + 50000.0)
    assert est["status"] == "ESTIMATED"
    assert est["depth_max_cm"] is not None and est["depth_min_cm"] is not None
    # Range (min width -> max depth): max depth uses the MIN width.
    assert est["depth_max_cm"] >= est["depth_min_cm"]
    assert "ESTIMATED_UNDER_ASSUMED_GEOMETRY" in (
        depth_estimates_for_reach_states(get_live_reach_states(0))
    )["E00"]["provenance"]


def test_depth_estimates_from_mode_states_have_caveats():
    estimates = depth_estimates_for_reach_states(get_historical_reach_states("EVT-2024-06-27", 1))
    for edge_id, est in estimates.items():
        assert est["provenance"] == "ESTIMATED_UNDER_ASSUMED_GEOMETRY"
        assert est["caveat"]
        if est["status"] == "UNKNOWN":
            assert est["reason"]


# ---------------------------------------------------------------------------
# Surface pass (honest DEM proxy; never zero-fills UNKNOWN)
# ---------------------------------------------------------------------------


def test_surface_structure_builds():
    s = get_surface_structure()
    assert s.cell_flat_idx.size > 1000
    assert s.cell_area_m2 == pytest.approx(900.0)


def test_surface_pass_skips_unknown_forcing():
    from backend.app.domain.delhi.surface import surface_pass

    r = surface_pass([None, 0.0], [1.0, 1.0])
    assert r["timesteps"][0]["status"] == "UNKNOWN_FORCING_SKIPPED"
    assert r["timesteps"][0]["peak_surface_cm"] is None
    assert r["timesteps"][1]["peak_surface_cm"] == 0.0
    assert "MODEL-DERIVED" in r["method"] and "DSM" in r["method"]
    assert "never" in r["caveat"].lower()


def test_surface_pass_produces_hotspots_and_corridor_inflow():
    from backend.app.domain.delhi.surface import surface_pass

    r = surface_pass([40.0], [1.0])
    ts = r["timesteps"][0]
    assert ts["status"] == "COMPUTED"
    assert ts["peak_surface_cm"] is not None and ts["peak_surface_cm"] > 0
    assert len(ts["hotspots"]) > 0
    # WGS84 coordinates.
    assert 77.0 < ts["hotspots"][0]["lon"] < 77.5
    # Per-reach inflow proxy keys cover the model reaches.
    assert set(ts["per_reach_surface_inflow_m3_s"].keys()) == {
        "UG-01", "OC-01", "CD-01", "OC-02"
    }


# ---------------------------------------------------------------------------
# Radar composite (provenance discipline)
# ---------------------------------------------------------------------------


def test_radar_classification_gif_never_quantitative():
    gif = DelhiRadarProbeResult(
        endpoint_key="SRI_DLI", endpoint_url="https://mausam.imd.gov.in/Radar/sri_dli.gif",
        http_status=200, content_type="image/gif", content_length_bytes=1000,
        is_accessible=True, is_quantitative=False,
        diagnostic_message="visual palette product; quantitative decoding refused",
    )
    assert not any_quantitative_delhi_radar([gif])


def test_radar_quantitative_grid_detected():
    nc = DelhiRadarProbeResult(
        endpoint_key="GRID", endpoint_url="https://x/ffg_dli.nc",
        http_status=200, content_type="application/x-netcdf", content_length_bytes=5000,
        is_accessible=True, is_quantitative=True,
        diagnostic_message="Quantitative gridded product detected",
    )
    assert any_quantitative_delhi_radar([nc])


def test_composite_nwp_fallback_never_called_radar():
    result = delhi_rainfall_composite(
        nwp_status="COMPUTED",
        nwp_acquired_at=None,
        radar_results=[
            DelhiRadarProbeResult(
                endpoint_key="SRI_DLI", endpoint_url="x.gif", http_status=200,
                content_type="image/gif", is_accessible=True, is_quantitative=False,
                diagnostic_message="visual product",
            )
        ],
    )
    assert result["provenance"] == "NWP_FALLBACK"
    assert result["is_fallback"] is True
    assert "open-meteo" in result["source_name"].lower()
    assert "never decoded" in result["fallback_reason"].lower()
    assert "never decoded" in result["fallback_reason"].lower()


def test_composite_unavailable_without_nwp():
    result = delhi_rainfall_composite(nwp_status="UNAVAILABLE", nwp_acquired_at=None, radar_results=[])
    assert result["provenance"] == "UNAVAILABLE"


# ---------------------------------------------------------------------------
# API integration
# ---------------------------------------------------------------------------


def test_api_drainage_graph(client):
    r = client.get("/api/delhi/drainage-graph")
    assert r.status_code == 200
    body = r.json()
    assert body["n_nodes"] == 9 and body["n_edges"] == 8
    assert "DERIVED" in body["provenance"]


def test_api_drainage_loading_historical(client):
    r = client.get("/api/delhi/drainage-graph/loading", params=dict(
        mode="historical", event_id="EVT-2024-06-27", timestep_index=1,
    ))
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "COMPUTED"
    assert "E00" in body["overloaded_edges"]


def test_api_drainage_loading_unknown_event_409(client):
    r = client.get("/api/delhi/drainage-graph/loading", params=dict(
        mode="historical", event_id="EVT-2021-07-19", timestep_index=0,
    ))
    assert r.status_code == 409


def test_api_surface_live(client):
    r = client.get("/api/delhi/surface", params=dict(mode="live"))
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "COMPUTED"
    assert all(t["status"].startswith(("COMPUTED", "UNKNOWN")) for t in body["timesteps"])


def test_api_radar_composite(client):
    r = client.get("/api/delhi/rainfall/composite")
    assert r.status_code == 200
    body = r.json()
    assert body["provenance"] in ("RADAR", "NWP_FALLBACK", "UNAVAILABLE")
    assert body["is_fallback"] == (body["provenance"] != "RADAR")


def test_nowcast_includes_reconstruction_products(client, monkeypatch):
    """The nowcast payload carries loading/depth/surface and degrades
    gracefully rather than breaking the physics when unavailable."""
    r = client.get("/api/delhi/nowcast")
    assert r.status_code == 200
    body = r.json()
    assert "drainage_loading" in body and "depth_estimates" in body and "surface" in body