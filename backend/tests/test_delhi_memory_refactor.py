"""Regression tests for the production memory refactor (representation only).

These exist to prove the memory fixes changed how the Delhi structures are
STORED, never what they compute: graph topology, per-edge geometry, routing
results and V1 depth outputs must match the pre-refactor behaviour.

Floating quantities are checked with a tolerance, and digests hash values
rounded to CANONICAL_DP decimals. Lengths come from a PROJ UTM transform, and
PROJ/libm differ in the last bits of a float across platforms (Windows
CPython vs GitHub Ubuntu: observed ~1e-13 relative, i.e. sub-nanometre over a
5 km route). Integers, identifiers, orderings and counts stay exact.
"""
from __future__ import annotations

import hashlib
import json

import numpy as np
import pytest

from backend.app.domain.delhi.routing import engine
from backend.app.domain.delhi.routing.network import (
    ASSUMED_SPEEDS_KMH,
    DEFAULT_SPEED_KMH,
    SegmentEdge,
    _SegmentGeometry,
    get_road_graph,
)

ORIGIN = (77.2085, 28.5790)
DEST = (77.2380, 28.5770)

#: Relative tolerance for pinned floating measurements (see module docstring).
REL_TOL = 1e-9

#: Decimal places used when canonicalising floats before hashing.
CANONICAL_DP = 6

# Snapshot taken from the PRE-representation-change implementation (see
# scripts/mem_fingerprint.py). Any drift in these values is a behaviour
# change, not a memory change. The *_hash entries are _digest() values over
# identifier/geometry tuples from the same pre-refactor output (verified
# against fingerprint_head.json); ``edge_keys_hash`` covers key strings only.
GRAPH_SNAPSHOT = {
    "nodes": 38736,
    "edges": 75619,
    "adj_total": 75620,
    "edge_keys_hash": "75880ea59645d0f5",
    "edge_keys_head": [
        "osm-1030848849:10630:25793",
        "osm-1030848849:10630:25794",
        "osm-1030848849:25787:25788",
        "osm-1030848849:25787:3877",
        "osm-1030848849:25788:25787",
    ],
}
ROUTE_SNAPSHOT = {
    "n_edges": 153,
    "distance_m": 5483.613673448339,
    "penalty_s": 0.0,
    "travel_s": 518.5721474179904,
    "geojson_hash": "1c3b838ff64d58cf",
}
MATCH_INDEX_SNAPSHOT = {
    "row0_length_m": 44.74377095623352,
    "sampled_hash": "0c0f9cce797a6387",
}

#: Aggregate geometry measurements over the whole edge set, pinned with
#: ``REL_TOL``. Deliberately NOT a digest: hashing 300k+ rounded floats turns
#: every platform-level last-bit difference into a whole-quantum jump at a
#: rounding boundary (~6 expected flips over the full set), so an exact digest
#: of per-edge coordinate tuples can only ever match on the machine that
#: produced it. Sums keep the same last-bit differences additive, where they
#: stay ~1e-13 relative and well inside tolerance, while still collapsing any
#: real geometry change to a single detectable number.
GEOMETRY_SNAPSHOT = {
    "coords_count": 302476,
    "total_length_m": 2134800.577517532,
    "max_length_m": 742.725279003515,
    "min_length_m": 0.0097859403696877,
    "coords_sum_deg": 16000877.1285364,
}


def _canonical(obj):
    """Round every float to ``CANONICAL_DP`` so hashes are platform-stable."""
    if isinstance(obj, float):
        return round(obj, CANONICAL_DP)
    if isinstance(obj, dict):
        return {key: _canonical(value) for key, value in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_canonical(value) for value in obj]
    return obj


def _digest(obj) -> str:
    canonical = _canonical(obj)
    return hashlib.sha256(json.dumps(canonical, sort_keys=True).encode()).hexdigest()[:16]


def _edge_identifiers(graph) -> str:
    """Digest of edge keys in graph order — strings only, so platform-stable."""
    return _digest([e.edge_key for e in graph.edge_index.values()])


def _edge_geometry_aggregates(graph) -> dict:
    edges = list(graph.edge_index.values())
    lengths = [e.length_m for e in edges]
    coords = [v for e in edges for point in e.coords_4326 for v in point]
    return {
        "coords_count": len(coords),
        "total_length_m": sum(lengths),
        "max_length_m": max(lengths),
        "min_length_m": min(lengths),
        "coords_sum_deg": sum(coords),
    }


def test_graph_topology_counts_unchanged():
    graph = get_road_graph()
    assert len(graph.node_lonlat) == GRAPH_SNAPSHOT["nodes"]
    assert len(graph.edge_index) == GRAPH_SNAPSHOT["edges"]
    assert sum(len(v) for v in graph.adj.values()) == GRAPH_SNAPSHOT["adj_total"]
    assert sorted(graph.edge_index)[:5] == GRAPH_SNAPSHOT["edge_keys_head"]


def test_every_edge_geometry_unchanged():
    """Shared-geometry representation produces identical per-edge tuples.

    Identifiers, ordering and coordinate count are exact; the measured
    geometry is checked as aggregates with ``REL_TOL`` (see
    ``GEOMETRY_SNAPSHOT``).
    """
    graph = get_road_graph()
    assert _edge_identifiers(graph) == GRAPH_SNAPSHOT["edge_keys_hash"]

    actual = _edge_geometry_aggregates(graph)
    assert actual["coords_count"] == GEOMETRY_SNAPSHOT["coords_count"]
    for key in ("total_length_m", "max_length_m", "min_length_m", "coords_sum_deg"):
        assert actual[key] == pytest.approx(GEOMETRY_SNAPSHOT[key], rel=REL_TOL)


def test_forward_and_reverse_share_one_geometry_object():
    graph = get_road_graph()
    geoms = [id(e.geometry) for e in graph.edge_index.values()]
    # 75,619 edges must not hold 75,619 coordinate representations.
    assert len(set(geoms)) < len(geoms)
    fwd = next(e for e in graph.edge_index.values() if not e.reverse)
    rev = graph.edge_index.get(f"{fwd.road_id}:{fwd.v}:{fwd.u}")
    if rev is not None and rev.geometry is fwd.geometry:
        assert rev.coords_4326 == tuple(reversed(fwd.coords_4326))
        assert rev.u == fwd.v and rev.v == fwd.u
        assert rev.length_m == fwd.length_m


def test_edges_are_slots_backed_and_immutable():
    edge = next(iter(get_road_graph().edge_index.values()))
    assert not hasattr(edge, "__dict__")
    assert isinstance(edge.geometry, _SegmentGeometry)
    try:
        edge.length_m = 1.0
    except Exception:
        pass
    else:
        raise AssertionError("SegmentEdge must stay frozen")
    assert isinstance(edge, SegmentEdge)


def test_dijkstra_route_outputs_unchanged():
    graph = get_road_graph()
    src, _, _ = graph.snap(*ORIGIN)
    dst, _, _ = graph.snap(*DEST)
    risk = {k: ("LOW_RISK", "") for k in graph.edge_index}
    edges = engine._dijkstra(graph, src, dst, risk)
    cand = engine._build_candidate(edges, risk)
    assert len(edges) == ROUTE_SNAPSHOT["n_edges"]
    assert cand.total_distance_m == pytest.approx(ROUTE_SNAPSHOT["distance_m"], rel=REL_TOL)
    assert cand.risk_penalty_s == ROUTE_SNAPSHOT["penalty_s"]
    assert cand.travel_time_s == pytest.approx(ROUTE_SNAPSHOT["travel_s"], rel=REL_TOL)
    assert _digest(engine._route_geojson(edges)) == ROUTE_SNAPSHOT["geojson_hash"]


def test_blocked_edge_still_hard_excluded():
    graph = get_road_graph()
    src, _, _ = graph.snap(*ORIGIN)
    dst, _, _ = graph.snap(*DEST)
    risk = {k: ("LOW_RISK", "") for k in graph.edge_index}
    edges = engine._dijkstra(graph, src, dst, risk)
    target_road = edges[len(edges) // 2].road_id
    for key, edge in graph.edge_index.items():
        if edge.road_id == target_road:
            risk[key] = ("BLOCKED", "regression block")
    edges2 = engine._dijkstra(graph, src, dst, risk)
    assert edges2 is not None
    assert all(e.road_id != target_road for e in edges2)


def test_snap_and_travel_time_unchanged():
    graph = get_road_graph()
    assert graph.snap(*ORIGIN)[0] == 15261
    assert graph.snap(*DEST)[0] == 25157
    edge = next(iter(graph.edge_index.values()))
    assert graph.travel_time_s(edge) == edge.length_m / (
        ASSUMED_SPEEDS_KMH.get(edge.highway, DEFAULT_SPEED_KMH) / 3.6
    )


def test_v1_depth_output_unchanged():
    from backend.app.domain.delhi.scenarios.depth_v1 import v1_depth_step_for_intensity

    step = v1_depth_step_for_intensity(depth_mm=40.0, dt_h=1.0, timestep_index=0)
    assert step.flooded_cells == 1008
    assert step.max_depth_m == pytest.approx(0.644480055005848, rel=REL_TOL)
    assert step.conveyed_volume_m3 == pytest.approx(690711.6877442293, rel=REL_TOL)
    assert step.surcharged_volume_m3 == pytest.approx(602885.3122557707, rel=REL_TOL)
    assert np.count_nonzero(step.depth_m) >= 0


# ---------------------------------------------------------------------------
# Fix 1: the columnar road match index must answer exactly like the old
# per-segment dict/list structure did.
# ---------------------------------------------------------------------------


def test_road_match_index_content_matches_pre_refactor_snapshot():
    """The index content (order, keys, cells, coords) is what it always was.

    Pinned against the pre-refactor row-wise structure (scripts/
    mem_fingerprint.py: the old dict-list output hashed identical to these
    rows across all 75,619 segments, modulo the platform-tolerant
    canonicalisation in _digest).
    """
    from backend.app.domain.delhi.live_state import _road_match_index

    index, junctions = _road_match_index()
    assert len(index) == 75619
    assert index.cells_flat.size == 594112
    assert int(index.cell_offsets[0]) == 0
    assert int(index.cell_offsets[-1]) == index.cells_flat.size
    assert len(junctions) == 58
    row0 = index.row(0)
    length_m = row0.pop("length_m")
    assert row0 == {
        "edge_key": "osm-23138288:0:1",
        "road_id": "osm-23138288",
        "name": "Lala Lajpat Rai Path",
        "highway": "secondary",
        "osm_id": 23138288,
        "cells": [7601, 7602, 7857, 7858, 7857, 7858, 8115, 8116, 8115, 8116, 8374],
        "coords": [[77.2405059, 28.5954457], [77.2404086, 28.5950513]],
    }
    assert length_m == pytest.approx(MATCH_INDEX_SNAPSHOT["row0_length_m"], rel=REL_TOL)
    sampled = [index.row(i) for i in range(0, len(index), 997)]
    assert _digest(sampled) == MATCH_INDEX_SNAPSHOT["sampled_hash"]
    # Cell lists keep the documented endpoint + midpoint + endpoint order.
    assert any(row["cells"] is None for row in sampled)


def test_segmented_max_depth_equals_rowwise_max():
    """``max_depth`` == ``max(depth_m[c] for c in cells)`` per segment."""
    from backend.app.domain.delhi.live_state import _road_match_index
    from backend.app.domain.delhi.scenarios.depth_v1 import v1_depth_step_for_intensity

    index, _ = _road_match_index()
    depth_m = v1_depth_step_for_intensity(40.0).depth_m
    vectorised = index.max_depth(depth_m)
    assert vectorised.size == len(index)
    for i in range(0, len(index), 503):
        cells = index.row(i)["cells"]
        got = vectorised[i]
        if cells is None:
            assert np.isnan(got), f"segment {i} has no cells but depth {got}"
        else:
            assert float(got) == float(max(depth_m[c] for c in cells))


def test_street_intelligence_matches_rowwise_reference():
    """The vectorised street loop and the old per-dict loop agree exactly."""
    from backend.app.domain.delhi.live_state import (
        _road_match_index,
        _street_intelligence,
        classify_road_risk,
    )
    from backend.app.domain.delhi.scenarios.depth_v1 import v1_depth_step_for_intensity
    from backend.app.domain.delhi.surface import get_surface_structure

    index, junctions = _road_match_index()
    structure = get_surface_structure()
    step = v1_depth_step_for_intensity(40.0)
    actual = _street_intelligence(step, structure, "TEST-H")

    # Reference: the pre-refactor implementation, verbatim.
    depth_m = step.depth_m
    roads_features, affected_roads = [], []
    risk_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
    flooded_length = 0.0
    max_street_depth = 0.0
    for seg in (index.row(i) for i in range(len(index))):
        cells = seg["cells"]
        depth = None if not cells else float(max(depth_m[c] for c in cells))
        risk = classify_road_risk(depth)
        if depth is not None and depth > 0.001:
            flooded_length += seg["length_m"]
            max_street_depth = max(max_street_depth, depth)
            if risk in risk_counts:
                risk_counts[risk] += 1
        if depth is not None and depth > 0.015:
            props = {
                "road_id": seg["road_id"],
                "osm_id": seg["osm_id"],
                "name": seg["name"],
                "highway": seg["highway"],
                "max_depth_m": round(depth, 3),
                "flooded_length_m": round(seg["length_m"], 1),
                "risk_level": risk,
                "provenance": "SIMULATED_MODEL_OUTPUT (V1 reference depth grid)",
            }
            roads_features.append({
                "type": "Feature",
                "properties": props,
                "geometry": {"type": "LineString", "coordinates": seg["coords"]},
            })
            affected_roads.append(props)
    affected_roads.sort(key=lambda r: r["max_depth_m"], reverse=True)

    assert actual["summary"]["risk_counts"] == risk_counts
    assert actual["summary"]["total_affected_roads"] == len(affected_roads)
    assert actual["summary"]["max_street_depth_m"] == round(max_street_depth, 3)
    assert actual["summary"]["total_flooded_road_length_m"] == round(flooded_length, 1)
    assert actual["affected_roads"] == affected_roads[:12]
    assert _digest(actual["roads_geojson"]) == _digest(
        {"type": "FeatureCollection", "features": roads_features[:500]}
    )
    # Payloads must stay plain JSON types (no numpy scalars leaking out).
    json.dumps(actual)


def test_what_if_edge_depths_match_rowwise_reference():
    from backend.app.domain.delhi.live_state import (
        _road_match_index,
        what_if_edge_depths,
    )

    got = what_if_edge_depths(40.0)
    index, _ = _road_match_index()
    from backend.app.domain.delhi.scenarios.depth_v1 import v1_depth_step_for_intensity

    depth_m = v1_depth_step_for_intensity(40.0).depth_m
    reference = {}
    for i in range(len(index)):
        row = index.row(i)
        reference[row["edge_key"]] = (
            None if not row["cells"] else float(max(depth_m[c] for c in row["cells"]))
        )
    assert got == reference
    assert list(got)[:2] == list(reference)[:2]


# ---------------------------------------------------------------------------
# Fix 3: single-flight cold builds
# ---------------------------------------------------------------------------


def test_single_flight_runs_builder_once_under_concurrency():
    import threading
    import time

    from backend.app.domain.delhi.single_flight import single_flight_cached

    calls = []
    lock = threading.Lock()

    @single_flight_cached
    def slow_builder():
        with lock:
            calls.append(threading.current_thread().name)
        time.sleep(0.2)
        return object()

    slow_builder.cache_clear()
    results = []
    threads = [threading.Thread(target=lambda: results.append(slow_builder())) for _ in range(12)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert len(calls) == 1, f"cold build ran {len(calls)}x - concurrent builds are back"
    assert len(results) == 12
    assert all(r is results[0] for r in results)
    info = slow_builder.cache_info()
    assert info.currsize == 1 and info.misses == 1


def test_single_flight_warm_path_never_blocks():
    from backend.app.domain.delhi.single_flight import single_flight_cached

    @single_flight_cached
    def builder():
        return {"built": 1}

    first = builder()
    assert builder() is first
    assert builder.cache_info().hits >= 1
    assert builder.cache_parameters()["maxsize"] == 1
    builder.cache_clear()
    assert builder() is not first


def test_single_flight_nested_builders_do_not_deadlock():
    """Outer builders call inner ones on the same thread while holding their
    own lock; locks are reentrant and the builder DAG is acyclic."""
    import threading

    from backend.app.domain.delhi.single_flight import single_flight_cached

    @single_flight_cached
    def inner():
        return "inner"

    @single_flight_cached
    def outer():
        return ("outer", inner())

    seen = []
    threads = [threading.Thread(target=lambda: seen.append(outer())) for _ in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=10)
    assert all(not t.is_alive() for t in threads), "single-flight nested build deadlocked"
    assert len(seen) == 8


def test_real_builders_are_single_flight_wrapped():
    from backend.app.domain.delhi.live_state import _road_match_index
    from backend.app.domain.delhi.routing.network import get_road_graph
    from backend.app.domain.delhi.scenarios.depth_v1 import inlet_cell_indices
    from backend.app.domain.delhi.surface import get_surface_structure

    for builder in (get_road_graph, get_surface_structure, inlet_cell_indices, _road_match_index):
        assert hasattr(builder, "cache_info"), f"{builder.__name__} lost its cache surface"
        assert hasattr(builder, "cache_clear")
        assert builder.cache_parameters()["maxsize"] == 1


# ---------------------------------------------------------------------------
# Fix 4: the depth polygon layer honours the existing max_cells convention
# (deepest-first), and every retained feature is untouched.
# ---------------------------------------------------------------------------


def test_depth_polygons_capped_to_the_deepest_cells():
    from backend.app.domain.delhi.scenarios.depth_v1 import (
        depth_polygons_from_v1,
        v1_depth_step_for_intensity,
    )
    from backend.app.domain.delhi.surface import get_surface_structure

    structure = get_surface_structure()
    step = v1_depth_step_for_intensity(70.0)
    uncapped = depth_polygons_from_v1(step, structure, max_cells=10 ** 9)
    capped = depth_polygons_from_v1(step, structure)

    assert step.flooded_cells > 320
    assert len(uncapped["features"]) == step.flooded_cells
    assert len(capped["features"]) == 320

    # Deterministic and a strict subset in the original cell order.
    assert capped == depth_polygons_from_v1(step, structure)
    positions = [
        uncapped["features"].index(f) for f in capped["features"]
    ]
    assert positions == sorted(positions)

    # Kept = the deepest ones: nothing deeper was ever dropped.
    kept = [f["properties"]["depth_cm"] for f in capped["features"]]
    dropped = [
        f["properties"]["depth_cm"]
        for i, f in enumerate(uncapped["features"])
        if i not in set(positions)
    ]
    assert min(kept) >= max(dropped)
    assert max(kept) == max(f["properties"]["depth_cm"] for f in uncapped["features"])


def test_depth_polygons_unchanged_below_the_cap():
    from backend.app.domain.delhi.scenarios.depth_v1 import (
        depth_polygons_from_v1,
        v1_depth_step_for_intensity,
    )
    from backend.app.domain.delhi.surface import get_surface_structure

    structure = get_surface_structure()
    step = v1_depth_step_for_intensity(20.0)
    assert step.flooded_cells == 0
    assert depth_polygons_from_v1(step, structure) == {
        "type": "FeatureCollection", "features": []
    }
