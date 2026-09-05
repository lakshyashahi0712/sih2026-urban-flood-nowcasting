"""Flood-safe routing calculation engine using weighted Dijkstra on OSM road graph."""
from __future__ import annotations

import heapq
from typing import Any, Dict, List, Optional, Set, Tuple

try:
    from backend.app.domain.roads.models import AffectedRoad, RiskLevel
    from backend.app.domain.routing.graph import RoadGraph, EdgeData
    from backend.app.domain.routing.models import (
        RouteSafetyStatus,
        RouteSegment,
        ShortestPathComparison,
        SafeRouteResponse,
        SnappedPoint,
    )
except ImportError:
    from app.domain.roads.models import AffectedRoad, RiskLevel
    from app.domain.routing.graph import RoadGraph, EdgeData
    from app.domain.routing.models import (
        RouteSafetyStatus,
        RouteSegment,
        ShortestPathComparison,
        SafeRouteResponse,
        SnappedPoint,
    )


PROVENANCE_DISCLOSURES = {
    "road_network": "OpenStreetMap road network (Mumbai pilot area)",
    "flood_hazard": "Modelled flood depth forecast (Copernicus DEM + Manning-D8 routing)",
    "routing_engine": "Hydraulically-weighted Dijkstra pathfinder (EPSG:32643)",
    "disclaimer": (
        "Experimental flood-safe routing based on modelled flood forecasts and OSM geometry. "
        "Does NOT reflect real-time traffic, municipal road closures, BMC official diversions, "
        "or live flood observations."
    ),
}


def _run_dijkstra(
    graph: RoadGraph,
    start_node: int,
    target_node: int,
    flood_lookup: Dict[str, Tuple[float, RiskLevel]],
    exclude_high_critical: bool,
) -> Tuple[Optional[List[EdgeData]], float, float]:
    """
    Execute Dijkstra pathfinding.
    
    Args:
        graph: Topological road graph
        start_node: Origin vertex index
        target_node: Destination vertex index
        flood_lookup: Dict mapping road_id -> (flood_depth_m, risk_level)
        exclude_high_critical: If True, exclude edges with RiskLevel >= HIGH
        
    Returns:
        (path_edges, total_cost, total_distance_m) or (None, inf, 0.0) if no path found.
    """
    if start_node == target_node:
        return [], 0.0, 0.0

    dist: Dict[int, float] = {start_node: 0.0}
    prev: Dict[int, Tuple[int, EdgeData, float]] = {}
    pq: List[Tuple[float, int]] = [(0.0, start_node)]

    while pq:
        curr_cost, u = heapq.heappop(pq)
        if u == target_node:
            break
        if curr_cost > dist.get(u, float("inf")):
            continue

        for edge in graph.adj.get(u, []):
            v = edge.v
            road_id = edge.road_id
            flood_info = flood_lookup.get(road_id, (0.0, RiskLevel.NONE))
            depth_m, risk = flood_info

            # Impassability rule: HIGH and CRITICAL roads are unavailable for safe routing
            if exclude_high_critical and risk in (RiskLevel.HIGH, RiskLevel.CRITICAL):
                continue

            # Weight calculation
            length = edge.length_m
            if risk == RiskLevel.MEDIUM:
                # Heavy penalty for medium flood (0.15m to <0.30m)
                weight = length * (1.0 + 8.0 * depth_m)
            elif risk == RiskLevel.LOW:
                # Moderate penalty for low flood (>0m to <0.15m)
                weight = length * (1.0 + 2.0 * depth_m)
            else:
                # Dry / unflooded road
                weight = length

            new_cost = curr_cost + weight
            if new_cost < dist.get(v, float("inf")):
                dist[v] = new_cost
                prev[v] = (u, edge, weight)
                heapq.heappush(pq, (new_cost, v))

    if target_node not in prev:
        return None, float("inf"), 0.0

    # Reconstruct path
    curr = target_node
    path_edges: List[EdgeData] = []
    while curr in prev:
        p_node, edge, _ = prev[curr]
        path_edges.append(edge)
        curr = p_node
    path_edges.reverse()

    total_dist = sum(e.length_m for e in path_edges)
    return path_edges, dist[target_node], total_dist


def _build_merged_linestring_coords(edges: List[EdgeData]) -> List[List[float]]:
    """Merge segment coordinates into a single continuous WGS84 LineString coordinate array."""
    if not edges:
        return []
    merged: List[List[float]] = []
    for edge in edges:
        for c in edge.coords_4326:
            if not merged or merged[-1] != c:
                merged.append(c)
    return merged


def calculate_flood_safe_route(
    start_lon: float,
    start_lat: float,
    end_lon: float,
    end_lat: float,
    horizon: str = "+1h",
    affected_roads: Optional[List[AffectedRoad]] = None,
) -> SafeRouteResponse:
    """
    Calculate an optimal flood-safe route between origin and destination coordinates.
    
    1. Snaps origin and destination to the nearest nodes in the Mumbai pilot road network.
    2. Builds the flood penalty lookup from Phase 1.8 affected roads.
    3. Computes the baseline (unconstrained) direct shortest path.
    4. Computes the flood-safe path, excluding roads >= HIGH risk and penalizing LOW/MEDIUM roads.
    5. Identifies flooded roads avoided by taking the detour.
    6. Returns structured response with safety status, distance, travel cost, and GeoJSON geometry.
    """
    graph = RoadGraph.get_instance()

    # 1. Snap coordinates to network
    start_node, start_snap = graph.snap_coordinate(start_lon, start_lat)
    end_node, end_snap = graph.snap_coordinate(end_lon, end_lat)

    # 2. Build flood depth & risk lookup
    flood_lookup: Dict[str, Tuple[float, RiskLevel]] = {}
    flooded_road_names_all: Dict[str, str] = {}  # road_id -> name
    if affected_roads:
        for aff in affected_roads:
            flood_lookup[aff.road_id] = (aff.max_depth_m, aff.risk_level)
            flooded_road_names_all[aff.road_id] = aff.name

    # 3. Compute baseline unconstrained shortest path (no flood penalties)
    direct_edges, _, direct_dist = _run_dijkstra(
        graph=graph,
        start_node=start_node,
        target_node=end_node,
        flood_lookup={},
        exclude_high_critical=False,
    )

    if direct_edges is None:
        return SafeRouteResponse(
            status=RouteSafetyStatus.NO_PATH_FOUND,
            total_distance_m=0.0,
            estimated_travel_cost=float("inf"),
            max_predicted_flood_depth_m=0.0,
            roads_avoided=[],
            route_geometry=None,
            segments=[],
            shortest_path_comparison=None,
            horizon=horizon,
            start_snapped_to=start_snap,
            end_snapped_to=end_snap,
            provenance=PROVENANCE_DISCLOSURES,
        )

    # Analyze direct path flood impact
    direct_max_depth = 0.0
    direct_flooded_road_ids: Set[str] = set()
    for e in direct_edges:
        depth, _ = flood_lookup.get(e.road_id, (0.0, RiskLevel.NONE))
        if depth > direct_max_depth:
            direct_max_depth = depth
        if depth > 0.001:
            direct_flooded_road_ids.add(e.road_id)

    shortest_comparison = ShortestPathComparison(
        distance_m=round(direct_dist, 1),
        max_flood_depth_m=round(direct_max_depth, 3),
        has_flooded_roads=len(direct_flooded_road_ids) > 0,
        flooded_road_count=len(direct_flooded_road_ids),
    )

    # 4. Compute flood-safe route (HIGH & CRITICAL roads excluded; MEDIUM & LOW penalized)
    safe_edges, safe_cost, safe_dist = _run_dijkstra(
        graph=graph,
        start_node=start_node,
        target_node=end_node,
        flood_lookup=flood_lookup,
        exclude_high_critical=True,
    )

    # If no safe route exists without traversing >= HIGH risk roads
    if safe_edges is None:
        # Find which high/critical roads blocked the direct route
        blocked_names = set()
        for e in direct_edges:
            depth, risk = flood_lookup.get(e.road_id, (0.0, RiskLevel.NONE))
            if risk in (RiskLevel.HIGH, RiskLevel.CRITICAL):
                blocked_names.add(e.name)

        return SafeRouteResponse(
            status=RouteSafetyStatus.UNAVAILABLE,
            total_distance_m=0.0,
            estimated_travel_cost=float("inf"),
            max_predicted_flood_depth_m=round(direct_max_depth, 3),
            roads_avoided=sorted(list(blocked_names)),
            route_geometry=None,
            segments=[],
            shortest_path_comparison=shortest_comparison,
            horizon=horizon,
            start_snapped_to=start_snap,
            end_snapped_to=end_snap,
            provenance=PROVENANCE_DISCLOSURES,
        )

    # 5. Build route segments and calculate metrics
    max_route_depth = 0.0
    safe_road_ids: Set[str] = set()
    segments: List[RouteSegment] = []

    for e in safe_edges:
        safe_road_ids.add(e.road_id)
        depth, risk = flood_lookup.get(e.road_id, (0.0, RiskLevel.NONE))
        if depth > max_route_depth:
            max_route_depth = depth

        segments.append(
            RouteSegment(
                road_id=e.road_id,
                osm_id=e.osm_id,
                name=e.name,
                highway=e.highway,
                length_m=round(e.length_m, 1),
                flood_depth_m=round(depth, 3),
                risk_level=risk.value if isinstance(risk, RiskLevel) else str(risk),
                geometry={"type": "LineString", "coordinates": e.coords_4326},
            )
        )

    # Identify roads avoided: flooded roads on direct path that were bypassed
    avoided_names: Set[str] = set()
    for rid in direct_flooded_road_ids:
        if rid not in safe_road_ids:
            name = flooded_road_names_all.get(rid)
            if name:
                avoided_names.add(name)

    # Determine safety status
    if max_route_depth <= 0.001:
        safety_status = RouteSafetyStatus.SAFE
    else:
        safety_status = RouteSafetyStatus.CAUTION

    # Complete route geometry
    merged_coords = _build_merged_linestring_coords(safe_edges)
    route_geom = {"type": "LineString", "coordinates": merged_coords}

    return SafeRouteResponse(
        status=safety_status,
        total_distance_m=round(safe_dist, 1),
        estimated_travel_cost=round(safe_cost, 1),
        max_predicted_flood_depth_m=round(max_route_depth, 3),
        roads_avoided=sorted(list(avoided_names)),
        route_geometry=route_geom,
        segments=segments,
        shortest_path_comparison=shortest_comparison,
        horizon=horizon,
        start_snapped_to=start_snap,
        end_snapped_to=end_snap,
        provenance=PROVENANCE_DISCLOSURES,
    )
