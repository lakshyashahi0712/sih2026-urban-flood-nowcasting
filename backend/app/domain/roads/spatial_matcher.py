"""Spatial association engine coupling 2D DEM flood inundation with OSM roads and junctions."""
from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
from rasterio.warp import transform
from shapely.geometry import LineString, Point, box, shape, mapping
from shapely.strtree import STRtree

try:
    from backend.app.domain.roads.models import (
        RiskLevel,
        classify_road_risk,
        AffectedRoad,
        AffectedIntersection,
        RiskCounts,
        StreetIntelligenceSummary,
        StreetFloodIntelligence,
    )
except ImportError:
    from app.domain.roads.models import (
        RiskLevel,
        classify_road_risk,
        AffectedRoad,
        AffectedIntersection,
        RiskCounts,
        StreetIntelligenceSummary,
        StreetFloodIntelligence,
    )



class OSMRoadNetworkCache:
    """Singleton cache storing pre-loaded and projected OSM road and junction geometries."""
    _instance: Optional[OSMRoadNetworkCache] = None

    def __init__(self):
        self.roads: List[Dict[str, Any]] = []
        self.intersections: List[Dict[str, Any]] = []
        self._loaded: bool = False
        self._load_network()

    @classmethod
    def get_instance(cls) -> OSMRoadNetworkCache:
        if cls._instance is None:
            cls._instance = OSMRoadNetworkCache()
        return cls._instance

    def _load_network(self):
        if self._loaded:
            return

        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        roads_file = os.path.join(base_dir, "data", "roads", "mumbai_pilot_roads.geojson")
        intersections_file = os.path.join(base_dir, "data", "roads", "mumbai_pilot_intersections.geojson")

        if not os.path.exists(roads_file) or not os.path.exists(intersections_file):
            # Fallback relative to current working directory if running in tests or diff dir
            roads_file = os.path.abspath("backend/app/data/roads/mumbai_pilot_roads.geojson")
            intersections_file = os.path.abspath("backend/app/data/roads/mumbai_pilot_intersections.geojson")

        if not os.path.exists(roads_file) or not os.path.exists(intersections_file):
            self._loaded = True
            return

        # Load roads
        with open(roads_file, "r", encoding="utf-8") as f:
            roads_gj = json.load(f)

        for feat in roads_gj.get("features", []):
            coords_4326 = feat["geometry"]["coordinates"]
            if len(coords_4326) < 2:
                continue
            lons = [c[0] for c in coords_4326]
            lats = [c[1] for c in coords_4326]
            xs, ys = transform("EPSG:4326", "EPSG:32643", lons, lats)
            coords_32643 = list(zip(xs, ys))
            line_32643 = LineString(coords_32643)

            props = feat.get("properties", {})
            self.roads.append({
                "road_id": feat.get("id") or f"osm_way_{props.get('osm_id', 0)}",
                "osm_id": props.get("osm_id", 0),
                "name": props.get("name", "Unnamed Street"),
                "highway": props.get("highway", "unclassified"),
                "geom_4326": feat["geometry"],
                "geom_32643": line_32643,
                "geom_32643_buffered": line_32643.buffer(7.0),  # 7m half-width buffer for road corridor
                "length_m": line_32643.length,
                "oneway": props.get("oneway"),
            })

        # Load intersections
        with open(intersections_file, "r", encoding="utf-8") as f:
            intersections_gj = json.load(f)

        for feat in intersections_gj.get("features", []):
            coords_4326 = feat["geometry"]["coordinates"]
            xs, ys = transform("EPSG:4326", "EPSG:32643", [coords_4326[0]], [coords_4326[1]])
            pt_32643 = Point(xs[0], ys[0])
            props = feat.get("properties", {})

            self.intersections.append({
                "intersection_id": feat.get("id") or f"osm_node_{props.get('osm_node_id', 0)}",
                "osm_node_id": props.get("osm_node_id", 0),
                "name": props.get("name", "Junction"),
                "roads": props.get("roads", []),
                "connection_count": props.get("connection_count", 2),
                "geom_4326": feat["geometry"],
                "geom_32643": pt_32643,
                "geom_32643_buffered": pt_32643.buffer(20.0),  # 20m radius junction buffer
            })

        self._loaded = True


def match_flood_to_streets(
    flood_depth_m: np.ndarray,
    flooded_mask: np.ndarray,
    cell_w: float = 30.0,
    cell_h: float = 30.0,
    origin_x: float = 0.0,
    origin_y: float = 0.0,
    horizon: str = "+1h",
    lead_time: str = "+1h",
    rainfall_mm: float = 0.0,
) -> StreetFloodIntelligence:
    """
    Spatially match 2D DEM flood inundation cells with OSM road segments and junctions.
    
    Spatial analysis is executed in computation CRS (EPSG:32643, metric UTM) and
    results are returned in standard GeoJSON (EPSG:4326, WGS84).
    """
    cache = OSMRoadNetworkCache.get_instance()
    provenance = {
        "roads": "OpenStreetMap contributors (ODbL)",
        "elevation": "Copernicus GLO-30 DSM (30m)",
        "flood_depth": "Modelled (2D surface routing)",
        "disclaimer": "Experimental model coupling; OSM road geometries overlaid with modeled flood depths. Not real-time municipal observations.",
    }

    empty_summary = StreetIntelligenceSummary(
        total_affected_roads=0,
        total_affected_intersections=0,
        max_street_depth_m=0.0,
        total_flooded_road_length_m=0.0,
        risk_counts=RiskCounts(),
    )
    empty_roads_gj = {"type": "FeatureCollection", "features": []}
    empty_ints_gj = {"type": "FeatureCollection", "features": []}

    # Handle dry or empty flood case
    if flood_depth_m is None or flooded_mask is None or not np.any(flooded_mask):
        return StreetFloodIntelligence(
            horizon=horizon,
            lead_time=lead_time,
            rainfall_mm=rainfall_mm,
            summary=empty_summary,
            affected_roads=[],
            affected_intersections=[],
            roads_geojson=empty_roads_gj,
            intersections_geojson=empty_ints_gj,
            provenance=provenance,
        )

    # Extract all flooded cells in EPSG:32643
    rows, cols = flood_depth_m.shape
    flooded_boxes: List[box] = []
    flooded_depths: List[float] = []

    for r in range(rows):
        for c in range(cols):
            if flooded_mask[r, c]:
                depth = float(flood_depth_m[r, c])
                if depth > 0.001:
                    x_min = origin_x + c * cell_w
                    y_max = origin_y - r * cell_h
                    x_max = x_min + cell_w
                    y_min = y_max - cell_h
                    flooded_boxes.append(box(x_min, y_min, x_max, y_max))
                    flooded_depths.append(depth)

    if not flooded_boxes:
        return StreetFloodIntelligence(
            horizon=horizon,
            lead_time=lead_time,
            rainfall_mm=rainfall_mm,
            summary=empty_summary,
            affected_roads=[],
            affected_intersections=[],
            roads_geojson=empty_roads_gj,
            intersections_geojson=empty_ints_gj,
            provenance=provenance,
        )

    # Build spatial index using STRtree
    tree = STRtree(flooded_boxes)

    affected_roads: List[AffectedRoad] = []
    road_features: List[Dict[str, Any]] = []
    total_flooded_len_m = 0.0
    max_overall_street_depth = 0.0

    risk_counts_dict = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}

    # 1. Match Roads
    for r_data in cache.roads:
        matching_cell_indices = tree.query(r_data["geom_32643_buffered"])
        if len(matching_cell_indices) > 0:
            depths = [flooded_depths[idx] for idx in matching_cell_indices]
            max_d = float(np.max(depths))
            mean_d = float(np.mean(depths))
            risk = classify_road_risk(max_d)

            if risk == RiskLevel.NONE:
                continue

            # Compute flooded length intersecting the cell boxes
            sub_len = 0.0
            r_geom = r_data["geom_32643"]
            for idx in matching_cell_indices:
                cell_poly = flooded_boxes[idx]
                inter = r_geom.intersection(cell_poly)
                if not inter.is_empty:
                    sub_len += inter.length

            if sub_len == 0.0:
                # If touched by buffer, assign a conservative 15m segment
                sub_len = min(15.0, r_data["length_m"])

            total_flooded_len_m += sub_len
            max_overall_street_depth = max(max_overall_street_depth, max_d)
            risk_counts_dict[risk.value] += 1

            aff_road = AffectedRoad(
                road_id=r_data["road_id"],
                osm_id=r_data["osm_id"],
                name=r_data["name"],
                highway=r_data["highway"],
                max_depth_m=round(max_d, 3),
                mean_depth_m=round(mean_d, 3),
                flooded_length_m=round(sub_len, 1),
                risk_level=risk,
                geometry=r_data["geom_4326"],
            )
            affected_roads.append(aff_road)

            road_features.append({
                "type": "Feature",
                "id": aff_road.road_id,
                "properties": {
                    "road_id": aff_road.road_id,
                    "name": aff_road.name,
                    "highway": aff_road.highway,
                    "max_depth_m": aff_road.max_depth_m,
                    "mean_depth_m": aff_road.mean_depth_m,
                    "flooded_length_m": aff_road.flooded_length_m,
                    "risk_level": aff_road.risk_level.value,
                    "risk_color": _get_risk_hex_color(aff_road.risk_level),
                    "horizon": horizon,
                },
                "geometry": aff_road.geometry,
            })

    # 2. Match Intersections
    affected_intersections: List[AffectedIntersection] = []
    intersection_features: List[Dict[str, Any]] = []

    for i_data in cache.intersections:
        matching_cell_indices = tree.query(i_data["geom_32643_buffered"])
        if len(matching_cell_indices) > 0:
            depths = [flooded_depths[idx] for idx in matching_cell_indices]
            max_d = float(np.max(depths))
            risk = classify_road_risk(max_d)

            if risk == RiskLevel.NONE:
                continue

            max_overall_street_depth = max(max_overall_street_depth, max_d)

            aff_int = AffectedIntersection(
                intersection_id=i_data["intersection_id"],
                osm_node_id=i_data["osm_node_id"],
                name=i_data["name"],
                roads=i_data["roads"],
                max_depth_m=round(max_d, 3),
                risk_level=risk,
                connection_count=i_data["connection_count"],
                geometry=i_data["geom_4326"],
            )
            affected_intersections.append(aff_int)

            intersection_features.append({
                "type": "Feature",
                "id": aff_int.intersection_id,
                "properties": {
                    "intersection_id": aff_int.intersection_id,
                    "name": aff_int.name,
                    "roads": aff_int.roads,
                    "roads_display": " & ".join(aff_int.roads) if aff_int.roads else aff_int.name,
                    "max_depth_m": aff_int.max_depth_m,
                    "risk_level": aff_int.risk_level.value,
                    "risk_color": _get_risk_hex_color(aff_int.risk_level),
                    "connection_count": aff_int.connection_count,
                    "horizon": horizon,
                },
                "geometry": aff_int.geometry,
            })

    # Sort roads and intersections descending by flood severity
    affected_roads.sort(key=lambda r: (-r.max_depth_m, -r.flooded_length_m))
    affected_intersections.sort(key=lambda i: -i.max_depth_m)

    summary = StreetIntelligenceSummary(
        total_affected_roads=len(affected_roads),
        total_affected_intersections=len(affected_intersections),
        max_street_depth_m=round(max_overall_street_depth, 3),
        total_flooded_road_length_m=round(total_flooded_len_m, 1),
        risk_counts=RiskCounts(
            CRITICAL=risk_counts_dict["CRITICAL"],
            HIGH=risk_counts_dict["HIGH"],
            MEDIUM=risk_counts_dict["MEDIUM"],
            LOW=risk_counts_dict["LOW"],
        ),
    )

    roads_geojson = {
        "type": "FeatureCollection",
        "features": road_features,
    }
    intersections_geojson = {
        "type": "FeatureCollection",
        "features": intersection_features,
    }

    return StreetFloodIntelligence(
        horizon=horizon,
        lead_time=lead_time,
        rainfall_mm=rainfall_mm,
        summary=summary,
        affected_roads=affected_roads,
        affected_intersections=affected_intersections,
        roads_geojson=roads_geojson,
        intersections_geojson=intersections_geojson,
        provenance=provenance,
    )


def _get_risk_hex_color(risk: RiskLevel) -> str:
    if risk == RiskLevel.CRITICAL:
        return "#991b1b"  # Deep red
    elif risk == RiskLevel.HIGH:
        return "#ea580c"  # Vivid orange
    elif risk == RiskLevel.MEDIUM:
        return "#ca8a04"  # Amber
    elif risk == RiskLevel.LOW:
        return "#0284c7"  # Sky blue
    return "#64748b"      # Slate
