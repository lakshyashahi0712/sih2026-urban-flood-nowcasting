"""Comprehensive test suite for Phase 1.9 — Flood-Safe Routing API."""
import time
import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.app.domain.roads.models import AffectedRoad, RiskLevel
from backend.app.domain.routing.graph import RoadGraph
from backend.app.domain.routing.models import RouteSafetyStatus, SafeRouteResponse
from backend.app.domain.routing.router import calculate_flood_safe_route


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


@pytest.fixture(scope="module")
def graph():
    return RoadGraph.get_instance()


def test_road_graph_construction_and_oneway(graph):
    """Verify graph builds from real Mumbai pilot roads and respects one-way rules."""
    assert len(graph.node_list) > 2000
    total_edges = sum(len(edges) for edges in graph.adj.values())
    assert total_edges > 3000

    # Verify at least one one-way forward and reverse edge configuration exists
    has_oneway = False
    for node, edges in graph.adj.items():
        for e in edges:
            if e.oneway:
                has_oneway = True
                break
        if has_oneway:
            break
    assert has_oneway, "Road graph should preserve OSM one-way restrictions"


def test_coordinate_snapping_valid_and_bounds(graph):
    """Verify coordinate snapping within pilot area and rejection of out-of-bounds coords."""
    # Valid point in Mumbai pilot area
    lon, lat = 72.8945, 19.0541
    node_idx, snapped = graph.snap_coordinate(lon, lat)
    assert node_idx >= 0
    assert snapped.distance_to_road_m < 200.0
    assert snapped.nearest_road_name is not None
    assert len(snapped.snapped_coords) == 2

    # Coordinate outside pilot bounding box -> ValueError
    with pytest.raises(ValueError, match="outside the Mumbai pilot area bounds"):
        graph.snap_coordinate(72.5000, 19.0500)

    # Coordinate far away in ocean or hills -> ValueError
    with pytest.raises(ValueError, match="outside the Mumbai pilot area bounds"):
        graph.snap_coordinate(72.8000, 18.9000)

    # Invalid latitude/longitude -> ValueError
    with pytest.raises(ValueError, match="Invalid geographic coordinates"):
        graph.snap_coordinate(200.0, 95.0)


def test_no_flood_safe_route():
    """When no roads are flooded (dry conditions), route should be SAFE and match direct shortest path."""
    # Two connected coordinates in the pilot area
    start_lon, start_lat = 72.8945, 19.0541
    end_lon, end_lat = 72.9000, 19.0650

    res = calculate_flood_safe_route(
        start_lon=start_lon,
        start_lat=start_lat,
        end_lon=end_lon,
        end_lat=end_lat,
        horizon="+1h",
        affected_roads=[],
    )

    assert res.status == RouteSafetyStatus.SAFE
    assert res.total_distance_m > 0
    assert res.max_predicted_flood_depth_m == 0.0
    assert len(res.roads_avoided) == 0
    assert res.route_geometry is not None
    assert res.route_geometry["type"] == "LineString"
    assert len(res.route_geometry["coordinates"]) > 1
    assert res.shortest_path_comparison is not None
    assert res.shortest_path_comparison.distance_m == res.total_distance_m


def test_flooded_shortest_path_detour():
    """When the direct shortest path intersects a HIGH/CRITICAL flooded road, a safe detour is taken."""
    start_lon, start_lat = 72.8945, 19.0541
    end_lon, end_lat = 72.9000, 19.0650

    # 1. First find the unflooded baseline
    base = calculate_flood_safe_route(
        start_lon=start_lon,
        start_lat=start_lat,
        end_lon=end_lon,
        end_lat=end_lat,
        horizon="+1h",
        affected_roads=[],
    )
    assert len(base.segments) >= 2
    # Select an intermediate road from the direct path to block
    road_to_flood = base.segments[1]

    # Create mock HIGH risk flood on this road
    mock_affected = [
        AffectedRoad(
            road_id=road_to_flood.road_id,
            osm_id=road_to_flood.osm_id,
            name=road_to_flood.name,
            highway=road_to_flood.highway,
            max_depth_m=0.45,  # HIGH risk (0.30 - 0.60 m)
            mean_depth_m=0.40,
            flooded_length_m=road_to_flood.length_m,
            risk_level=RiskLevel.HIGH,
            geometry=road_to_flood.geometry,
        )
    ]

    res = calculate_flood_safe_route(
        start_lon=start_lon,
        start_lat=start_lat,
        end_lon=end_lon,
        end_lat=end_lat,
        horizon="+1h",
        affected_roads=mock_affected,
    )

    if res.status in (RouteSafetyStatus.SAFE, RouteSafetyStatus.CAUTION):
        # Successfully found an alternative detour around the flooded road
        assert res.max_predicted_flood_depth_m < 0.30  # No HIGH risk roads traversed
        traversed_ids = {s.road_id for s in res.segments}
        assert road_to_flood.road_id not in traversed_ids, "Safe route must NOT traverse the HIGH-risk flooded road"
        assert road_to_flood.name in res.roads_avoided
    else:
        # If no alternative existed, status must be UNAVAILABLE
        assert res.status == RouteSafetyStatus.UNAVAILABLE
        assert road_to_flood.name in res.roads_avoided


def test_medium_and_low_flood_penalization():
    """Verify MEDIUM and LOW flood risks increase travel cost without hard-blocking edges."""
    start_lon, start_lat = 72.8945, 19.0541
    end_lon, end_lat = 72.8960, 19.0570

    # Baseline dry
    base = calculate_flood_safe_route(
        start_lon=start_lon,
        start_lat=start_lat,
        end_lon=end_lon,
        end_lat=end_lat,
        horizon="+1h",
        affected_roads=[],
    )
    assert base.status == RouteSafetyStatus.SAFE

    if base.segments:
        r0 = base.segments[0]
        # Shallow flood on r0 (LOW risk: 0.10m)
        mock_affected = [
            AffectedRoad(
                road_id=r0.road_id,
                osm_id=r0.osm_id,
                name=r0.name,
                highway=r0.highway,
                max_depth_m=0.10,
                mean_depth_m=0.08,
                flooded_length_m=r0.length_m,
                risk_level=RiskLevel.LOW,
                geometry=r0.geometry,
            )
        ]
        res = calculate_flood_safe_route(
            start_lon=start_lon,
            start_lat=start_lat,
            end_lon=end_lon,
            end_lat=end_lat,
            horizon="+1h",
            affected_roads=mock_affected,
        )
        # Should be passable with CAUTION
        assert res.status in (RouteSafetyStatus.CAUTION, RouteSafetyStatus.SAFE)
        # Travel cost should be higher than dry distance due to penalty
        if res.max_predicted_flood_depth_m > 0:
            assert res.estimated_travel_cost >= res.total_distance_m


def test_no_safe_route_when_completely_blocked(graph):
    """When all adjacent edges to the destination are CRITICAL, UNAVAILABLE is returned."""
    start_lon, start_lat = 72.8945, 19.0541
    end_lon, end_lat = 72.9000, 19.0650

    end_idx, _ = graph.snap_coordinate(end_lon, end_lat)
    # Block all incoming edges to the destination node
    mock_affected = []
    for u, edges in graph.adj.items():
        for e in edges:
            if e.v == end_idx:
                mock_affected.append(
                    AffectedRoad(
                        road_id=e.road_id,
                        osm_id=e.osm_id,
                        name=e.name,
                        highway=e.highway,
                        max_depth_m=0.85,
                        mean_depth_m=0.80,
                        flooded_length_m=e.length_m,
                        risk_level=RiskLevel.CRITICAL,
                        geometry={"type": "LineString", "coordinates": e.coords_4326},
                    )
                )

    res = calculate_flood_safe_route(
        start_lon=start_lon,
        start_lat=start_lat,
        end_lon=end_lon,
        end_lat=end_lat,
        horizon="+1h",
        affected_roads=mock_affected,
    )

    assert res.status == RouteSafetyStatus.UNAVAILABLE
    assert res.route_geometry is None
    assert res.total_distance_m == 0.0
    assert len(res.roads_avoided) > 0


def test_api_safe_route_endpoint_success(client):
    """Test GET /routing/safe-route returns HTTP 200 with schema compliance."""
    resp = client.get(
        "/routing/safe-route",
        params={
            "start_lon": 72.8945,
            "start_lat": 19.0541,
            "end_lon": 72.9000,
            "end_lat": 19.0650,
            "horizon": "+1h",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] in ["SAFE", "CAUTION", "UNAVAILABLE"]
    assert "total_distance_m" in data
    assert "estimated_travel_cost" in data
    assert "max_predicted_flood_depth_m" in data
    assert "roads_avoided" in data
    assert "provenance" in data
    assert "OpenStreetMap" in data["provenance"]["road_network"]
    assert "Modelled" in data["provenance"]["flood_hazard"]


def test_api_safe_route_scenario_70mm(client):
    """Test GET /routing/safe-route with scenario rainfall override (70 mm/h)."""
    resp = client.get(
        "/routing/safe-route",
        params={
            "start_lon": 72.8945,
            "start_lat": 19.0541,
            "end_lon": 72.9000,
            "end_lat": 19.0650,
            "horizon": "+1h",
            "rainfall_scenario_mm": 70.0,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] in ["SAFE", "CAUTION", "UNAVAILABLE"]
    assert "roads_avoided" in data


def test_api_out_of_bounds_coordinates(client):
    """Test GET /routing/safe-route rejects out-of-bounds coordinates with HTTP 400."""
    resp = client.get(
        "/routing/safe-route",
        params={
            "start_lon": 72.0000,  # Far outside pilot area
            "start_lat": 19.0541,
            "end_lon": 72.9000,
            "end_lat": 19.0650,
        },
    )
    assert resp.status_code == 400
    assert "outside the Mumbai pilot area bounds" in resp.json()["detail"]


def test_routing_latency_benchmark():
    """Benchmark route calculation latency (target: fast execution <50 ms)."""
    start_lon, start_lat = 72.8945, 19.0541
    end_lon, end_lat = 72.9000, 19.0650

    times = []
    for _ in range(10):
        t0 = time.perf_counter()
        calculate_flood_safe_route(
            start_lon=start_lon,
            start_lat=start_lat,
            end_lon=end_lon,
            end_lat=end_lat,
            horizon="+1h",
            affected_roads=[],
        )
        times.append((time.perf_counter() - t0) * 1000)

    avg_ms = sum(times) / len(times)
    print(f"\nAverage routing latency: {avg_ms:.2f} ms")
    assert avg_ms < 100.0, f"Routing latency ({avg_ms:.2f}ms) should be fast"
