"""Domain models and response schemas for Flood-Safe Routing."""
from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class RouteSafetyStatus(str, Enum):
    """Operational safety classification of a calculated route."""
    SAFE = "SAFE"                      # Completely dry route (0.0 m depth throughout)
    CAUTION = "CAUTION"                # Passable with caution (ponding < 0.30 m; no HIGH/CRITICAL segments)
    UNAVAILABLE = "UNAVAILABLE"        # No route available without crossing >= HIGH risk water barriers
    NO_PATH_FOUND = "NO_PATH_FOUND"    # Origin and destination are topologically disconnected


class RouteSegment(BaseModel):
    """A road segment forming part of a calculated route."""
    road_id: str = Field(..., description="Unique road identifier (e.g. osm_way_12345)")
    osm_id: int = Field(..., description="OpenStreetMap way ID")
    name: str = Field(..., description="Road name")
    highway: str = Field(..., description="OSM highway tag")
    length_m: float = Field(..., ge=0, description="Segment length in meters")
    flood_depth_m: float = Field(0.0, ge=0, description="Modelled flood depth on this segment [m]")
    risk_level: str = Field("NONE", description="Operational flood risk tier (NONE, LOW, MEDIUM, HIGH, CRITICAL)")
    geometry: Dict[str, Any] = Field(..., description="GeoJSON LineString (EPSG:4326)")


class ShortestPathComparison(BaseModel):
    """Summary comparison with the unconstrained (direct) shortest path."""
    distance_m: float = Field(..., ge=0, description="Unconstrained direct distance in meters")
    max_flood_depth_m: float = Field(0.0, ge=0, description="Peak flood depth along direct shortest path [m]")
    has_flooded_roads: bool = Field(False, description="True if direct shortest path traverses flooded roads")
    flooded_road_count: int = Field(0, description="Number of flooded road segments on direct shortest path")


class SnappedPoint(BaseModel):
    """Origin or destination point snapped to the closest road network node."""
    original_coords: List[float] = Field(..., description="[longitude, latitude] requested")
    snapped_coords: List[float] = Field(..., description="[longitude, latitude] on road network")
    distance_to_road_m: float = Field(..., ge=0, description="Distance snapped in meters")
    nearest_road_name: Optional[str] = Field(None, description="Name of closest road segment")


class SafeRouteResponse(BaseModel):
    """Complete flood-safe routing evaluation response."""
    status: RouteSafetyStatus = Field(..., description="Route safety evaluation status")
    total_distance_m: float = Field(0.0, ge=0, description="Total travel distance along route in meters")
    estimated_travel_cost: float = Field(0.0, ge=0, description="Weighted travel cost accounting for flood depth penalties")
    max_predicted_flood_depth_m: float = Field(0.0, ge=0, description="Maximum flood depth along calculated route [m]")
    roads_avoided: List[str] = Field(default_factory=list, description="Names of flooded roads bypassed by this route")
    route_geometry: Optional[Dict[str, Any]] = Field(None, description="GeoJSON LineString of the complete route (EPSG:4326)")
    segments: List[RouteSegment] = Field(default_factory=list, description="Ordered sequence of road segments")
    shortest_path_comparison: Optional[ShortestPathComparison] = Field(None, description="Comparison against unconstrained direct route")
    horizon: str = Field("+1h", description="Forecast horizon used for flood hazard evaluation")
    start_snapped_to: Optional[SnappedPoint] = Field(None, description="Snapped start point metadata")
    end_snapped_to: Optional[SnappedPoint] = Field(None, description="Snapped destination point metadata")
    provenance: Dict[str, str] = Field(..., description="Explicit provenance and methodological disclosures")
