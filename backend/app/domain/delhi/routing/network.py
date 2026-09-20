"""Delhi/Kushak flood-aware routing: shared road network.

A single routing core serves LIVE nowcast routing, HISTORICAL replay
route reconstruction, and the EVIDENCE explorer. The road network is the
committed OSM-derived pilot GeoJSON (``delhi_kushak_roads.geojson``,
acquired build-time with a provenance sidecar) — never scraped at
runtime.

Graph construction follows the existing Mumbai V1 routing architecture
(``app.domain.routing.graph``) but is parameterized and Delhi-scoped.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from shapely.geometry import LineString, Point
from shapely.strtree import STRtree
from rasterio.warp import transform as rasterio_transform

_REPO_ROOT = Path(__file__).resolve().parents[5]
ROADS_PATH = _REPO_ROOT / "backend" / "app" / "data" / "roads" / "delhi_kushak_roads.geojson"
PROVENANCE_PATH = ROADS_PATH.with_suffix(".provenance.json")

# Delhi lies in UTM zone 43N (72-78 E), the same zone the Mumbai pilot uses.
_UTM_FROM_WGS84 = ("EPSG:4326", "EPSG:32643")

# Rough Delhi pilot bounding box (must contain the acquisition bbox).
DELHI_BBOX = (77.16, 28.52, 77.30, 28.62)

MAX_SNAP_DISTANCE_M = 800.0

# ASSUMED engineering travel speeds (km/h) by OSM highway class. These are
# documented assumptions for cost modeling, not observed traffic data.
ASSUMED_SPEEDS_KMH = {
    "motorway": 80, "trunk": 60, "primary": 50, "secondary": 40,
    "tertiary": 30, "residential": 25, "unclassified": 25,
    "motorway_link": 60, "trunk_link": 50, "primary_link": 40,
    "secondary_link": 35, "tertiary_link": 30, "living_street": 15,
    "service": 15,
}
DEFAULT_SPEED_KMH = 25


@dataclass(frozen=True)
class SegmentEdge:
    """One directed road segment (graph edge) with stable evidence identity."""

    edge_key: str  # stable id used for segment-level evidence lookups
    u: int
    v: int
    osm_id: int
    road_id: str
    name: str
    highway: str
    length_m: float
    coords_4326: Tuple[Tuple[float, float], Tuple[float, float]]


class DelhiRoadGraph:
    """Topological graph over the Delhi pilot network.

    Vertices are unique rounded coordinates; edges are directed segments
    honoring OSM one-way restrictions. Metric math uses UTM 43N.
    """

    def __init__(self) -> None:
        self.node_lonlat: List[Tuple[float, float]] = []
        self.node_xy: List[Tuple[float, float]] = []
        self._node_lookup: Dict[Tuple[float, float], int] = {}
        self.adj: Dict[int, List[SegmentEdge]] = {}
        self.edge_index: Dict[str, SegmentEdge] = {}
        self._tree: Optional[STRtree] = None
        self._build()

    # -- construction -----------------------------------------------------

    def _get_or_create_node(self, lon: float, lat: float, x: float, y: float) -> int:
        key = (round(lon, 6), round(lat, 6))
        if key not in self._node_lookup:
            idx = len(self.node_lonlat)
            self._node_lookup[key] = idx
            self.node_lonlat.append((lon, lat))
            self.node_xy.append((x, y))
            self.adj[idx] = []
        return self._node_lookup[key]

    def _build(self) -> None:
        data = json.loads(ROADS_PATH.read_text(encoding="utf-8"))
        for feature in data.get("features", []):
            coords = feature["geometry"]["coordinates"]
            if len(coords) < 2:
                continue
            props = feature["properties"]
            lons = [c[0] for c in coords]
            lats = [c[1] for c in coords]
            xs, ys = rasterio_transform(_UTM_FROM_WGS84[0], _UTM_FROM_WGS84[1], lons, lats)
            road_id = f"osm-{props.get('osm_id')}"
            node_ids = [
                self._get_or_create_node(lons[i], lats[i], xs[i], ys[i])
                for i in range(len(coords))
            ]
            oneway = (props.get("oneway") or "")
            for i in range(len(node_ids) - 1):
                u, v = node_ids[i], node_ids[i + 1]
                seg_len = max(math.hypot(xs[i + 1] - xs[i], ys[i + 1] - ys[i]), 0.001)
                base = dict(
                    osm_id=props.get("osm_id"),
                    road_id=road_id,
                    name=props.get("name") or "Unnamed road",
                    highway=props.get("highway") or "unclassified",
                    length_m=seg_len,
                )
                fwd = SegmentEdge(
                    edge_key=f"{road_id}:{u}:{v}", u=u, v=v,
                    coords_4326=((lons[i], lats[i]), (lons[i + 1], lats[i + 1])),
                    **base,
                )
                rev = SegmentEdge(
                    edge_key=f"{road_id}:{v}:{u}", u=v, v=u,
                    coords_4326=((lons[i + 1], lats[i + 1]), (lons[i], lats[i])),
                    **base,
                )
                if oneway == "yes":
                    self.adj[u].append(fwd)
                    self.edge_index[fwd.edge_key] = fwd
                elif oneway == "-1":
                    self.adj[v].append(rev)
                    self.edge_index[rev.edge_key] = rev
                else:
                    self.adj[u].append(fwd)
                    self.adj[v].append(rev)
                    self.edge_index[fwd.edge_key] = fwd
                    self.edge_index[rev.edge_key] = rev

        self._tree = STRtree([Point(x, y) for x, y in self.node_xy])

    # -- queries -----------------------------------------------------------

    def snap(self, lon: float, lat: float) -> Tuple[int, float, str]:
        """Snap a WGS84 point to the nearest road node.

        Returns (node_index, distance_m, road_name). Raises ValueError for
        invalid or too-distant coordinates.
        """
        if not (-180.0 <= lon <= 180.0 and -90.0 <= lat <= 90.0):
            raise ValueError(f"invalid coordinates ({lon}, {lat})")
        if not (DELHI_BBOX[0] <= lon <= DELHI_BBOX[2] and DELHI_BBOX[1] <= lat <= DELHI_BBOX[3]):
            raise ValueError(
                f"coordinates ({lon:.5f}, {lat:.5f}) are outside the Delhi "
                f"pilot network bounds"
            )
        px, py = rasterio_transform(
            _UTM_FROM_WGS84[0], _UTM_FROM_WGS84[1], [lon], [lat]
        )
        pt = Point(px[0], py[0])
        idx = int(self._tree.nearest(pt))
        dist = float(pt.distance(Point(*self.node_xy[idx])))
        if dist > MAX_SNAP_DISTANCE_M:
            raise ValueError(
                f"coordinates ({lon:.5f}, {lat:.5f}) are {dist:.0f} m from "
                f"the nearest road node (max {MAX_SNAP_DISTANCE_M:.0f} m)"
            )
        edges = self.adj.get(idx, [])
        name = edges[0].name if edges else "Unnamed road"
        return idx, dist, name

    def travel_time_s(self, edge: SegmentEdge) -> float:
        speed_kmh = ASSUMED_SPEEDS_KMH.get(edge.highway, DEFAULT_SPEED_KMH)
        return edge.length_m / (speed_kmh / 3.6)


@lru_cache(maxsize=1)
def get_road_graph() -> DelhiRoadGraph:
    """Process-wide cached graph (static network metadata)."""
    return DelhiRoadGraph()


@lru_cache(maxsize=1)
def road_network_provenance() -> dict:
    """Provenance sidecar of the committed network artifact."""
    return json.loads(PROVENANCE_PATH.read_text(encoding="utf-8"))
