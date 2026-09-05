"""Road network topology and spatial snapping for flood-safe routing."""
from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from shapely.geometry import Point
from shapely.strtree import STRtree
from rasterio.warp import transform

try:
    from backend.app.domain.roads.spatial_matcher import OSMRoadNetworkCache
    from backend.app.domain.routing.models import SnappedPoint
except ImportError:
    from app.domain.roads.spatial_matcher import OSMRoadNetworkCache
    from app.domain.routing.models import SnappedPoint


@dataclass
class EdgeData:
    """Directed segment edge between two consecutive road vertices."""
    u: int
    v: int
    road_id: str
    osm_id: int
    name: str
    highway: str
    length_m: float
    coords_4326: List[List[float]]
    oneway: bool = False


class RoadGraph:
    """
    Topological road graph constructed from the OSM Mumbai pilot road network.
    
    Vertices represent unique geographic coordinates along road alignments.
    Edges represent directed road segments respecting OSM one-way restrictions.
    Calculations are performed in EPSG:32643 (metric UTM Zone 43N).
    """
    _instance: Optional[RoadGraph] = None

    def __init__(self):
        self.node_list: List[Tuple[float, float, float, float]] = []  # (lon, lat, x_32643, y_32643)
        self.node_lookup: Dict[Tuple[float, float], int] = {}
        self.adj: Dict[int, List[EdgeData]] = {}
        self.edge_by_road: Dict[str, List[EdgeData]] = {}
        self._tree: Optional[STRtree] = None
        self._node_points_32643: List[Point] = []
        self._build_graph()

    @classmethod
    def get_instance(cls) -> RoadGraph:
        if cls._instance is None:
            cls._instance = RoadGraph()
        return cls._instance

    def _get_or_create_node(self, lon: float, lat: float, x: float, y: float) -> int:
        key = (round(lon, 6), round(lat, 6))
        if key not in self.node_lookup:
            idx = len(self.node_list)
            self.node_lookup[key] = idx
            self.node_list.append((lon, lat, x, y))
            self.adj[idx] = []
        return self.node_lookup[key]

    def _build_graph(self):
        cache = OSMRoadNetworkCache.get_instance()
        for r in cache.roads:
            c4326 = r["geom_4326"]["coordinates"]
            if len(c4326) < 2:
                continue

            lons = [c[0] for c in c4326]
            lats = [c[1] for c in c4326]
            xs, ys = transform("EPSG:4326", "EPSG:32643", lons, lats)

            node_ids = [
                self._get_or_create_node(lons[i], lats[i], xs[i], ys[i])
                for i in range(len(c4326))
            ]

            road_id = r["road_id"]
            if road_id not in self.edge_by_road:
                self.edge_by_road[road_id] = []

            oneway = r.get("oneway")
            is_oneway_fwd = (oneway == "yes")
            is_oneway_rev = (oneway == "-1")

            for i in range(len(node_ids) - 1):
                u = node_ids[i]
                v = node_ids[i + 1]
                dx = xs[i + 1] - xs[i]
                dy = ys[i + 1] - ys[i]
                seg_len = math.hypot(dx, dy)
                if seg_len < 0.001:
                    seg_len = 0.001

                fwd_edge = EdgeData(
                    u=u,
                    v=v,
                    road_id=road_id,
                    osm_id=r["osm_id"],
                    name=r["name"],
                    highway=r["highway"],
                    length_m=seg_len,
                    coords_4326=[c4326[i], c4326[i + 1]],
                    oneway=is_oneway_fwd,
                )
                rev_edge = EdgeData(
                    u=v,
                    v=u,
                    road_id=road_id,
                    osm_id=r["osm_id"],
                    name=r["name"],
                    highway=r["highway"],
                    length_m=seg_len,
                    coords_4326=[c4326[i + 1], c4326[i]],
                    oneway=is_oneway_rev,
                )

                if is_oneway_fwd:
                    self.adj[u].append(fwd_edge)
                    self.edge_by_road[road_id].append(fwd_edge)
                elif is_oneway_rev:
                    self.adj[v].append(rev_edge)
                    self.edge_by_road[road_id].append(rev_edge)
                else:
                    self.adj[u].append(fwd_edge)
                    self.adj[v].append(rev_edge)
                    self.edge_by_road[road_id].append(fwd_edge)
                    self.edge_by_road[road_id].append(rev_edge)

        # Build spatial index on metric node positions
        self._node_points_32643 = [Point(n[2], n[3]) for n in self.node_list]
        self._tree = STRtree(self._node_points_32643)

    def snap_coordinate(self, lon: float, lat: float, max_dist_m: float = 1500.0) -> Tuple[int, SnappedPoint]:
        """
        Snap an input WGS84 coordinate to the nearest road network node.
        
        Validates coordinate ranges and spatial distance to the Mumbai pilot network.
        Raises ValueError if invalid or exceeding maximum allowable snapping distance.
        """
        if not (-180.0 <= lon <= 180.0 and -90.0 <= lat <= 90.0):
            raise ValueError(f"Invalid geographic coordinates: ({lon}, {lat}). Latitude must be in [-90, 90] and longitude in [-180, 180].")

        # Check rough Mumbai pilot bounding box
        if not (72.82 <= lon <= 72.94 and 19.02 <= lat <= 19.12):
            raise ValueError(
                f"Coordinates ({lon:.5f}, {lat:.5f}) are outside the Mumbai pilot area bounds "
                f"(approx. [72.85-72.91E, 19.04-19.10N])."
            )

        # Project query point to EPSG:32643
        xs, ys = transform("EPSG:4326", "EPSG:32643", [lon], [lat])
        pt_32643 = Point(xs[0], ys[0])

        nearest_idx = int(self._tree.nearest(pt_32643))
        nearest_node = self.node_list[nearest_idx]
        dist_m = float(pt_32643.distance(self._node_points_32643[nearest_idx]))

        if dist_m > max_dist_m:
            raise ValueError(
                f"Coordinates ({lon:.5f}, {lat:.5f}) are {dist_m:.0f}m away from the nearest road network node "
                f"(maximum allowable snapping threshold is {max_dist_m:.0f}m)."
            )

        # Identify closest road name
        connected_edges = self.adj.get(nearest_idx, [])
        nearest_road_name = connected_edges[0].name if connected_edges else "Unnamed Street"

        snapped = SnappedPoint(
            original_coords=[round(lon, 6), round(lat, 6)],
            snapped_coords=[round(nearest_node[0], 6), round(nearest_node[1], 6)],
            distance_to_road_m=round(dist_m, 1),
            nearest_road_name=nearest_road_name,
        )
        return nearest_idx, snapped
