"""Domain models and risk classification for Street & Intersection Flood Intelligence."""
from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class RiskLevel(str, Enum):
    """
    Flood impassability and traffic risk classification.
    
    Thresholds:
    - CRITICAL: >= 0.60 m (Deep flood; impassable for all standard vehicles; structural/rescue hazard)
    - HIGH: 0.30 m to < 0.60 m (Exhaust pipe level; passenger cars stall; severe traffic disruption)
    - MEDIUM: 0.15 m to < 0.30 m (Waterlogging; dangerous for 2-wheelers; curb overflow)
    - LOW: > 0.00 m to < 0.15 m (Shallow surface ponding; passable with caution)
    - NONE: 0.00 m (No surface ponding; road dry / safe conveyance)
    """
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    NONE = "NONE"


def classify_road_risk(depth_m: float) -> RiskLevel:
    """Classify street flood depth into an operational risk tier."""
    if depth_m >= 0.60:
        return RiskLevel.CRITICAL
    elif depth_m >= 0.30:
        return RiskLevel.HIGH
    elif depth_m >= 0.15:
        return RiskLevel.MEDIUM
    elif depth_m > 0.001:
        return RiskLevel.LOW
    return RiskLevel.NONE


class AffectedRoad(BaseModel):
    """An OSM street segment impacted by modelled flood inundation."""
    road_id: str = Field(..., description="Unique road identifier (e.g. osm_way_12345)")
    osm_id: int = Field(..., description="OpenStreetMap way ID")
    name: str = Field(..., description="Street or avenue name")
    highway: str = Field(..., description="OSM highway classification (primary, secondary, etc.)")
    max_depth_m: float = Field(..., ge=0, description="Peak modelled inundation depth on street [m]")
    mean_depth_m: float = Field(..., ge=0, description="Average modelled inundation depth on street [m]")
    flooded_length_m: float = Field(..., ge=0, description="Approximate flooded corridor length [m]")
    risk_level: RiskLevel = Field(..., description="Operational risk classification")
    geometry: Dict[str, Any] = Field(..., description="GeoJSON LineString in EPSG:4326")


class AffectedIntersection(BaseModel):
    """A road intersection or topological junction impacted by modelled flood inundation."""
    intersection_id: str = Field(..., description="Unique junction identifier (e.g. osm_node_12345)")
    osm_node_id: int = Field(..., description="OpenStreetMap node ID")
    name: str = Field(..., description="Intersection name (e.g. 'Lal Bahadur Shastri Marg & CST Road')")
    roads: List[str] = Field(default_factory=list, description="Names of intersecting roads")
    max_depth_m: float = Field(..., ge=0, description="Peak modelled inundation depth at junction [m]")
    risk_level: RiskLevel = Field(..., description="Operational risk classification")
    connection_count: int = Field(..., description="Number of intersecting road segments")
    geometry: Dict[str, Any] = Field(..., description="GeoJSON Point in EPSG:4326")


class RiskCounts(BaseModel):
    """Breakdown of affected entities by risk tier."""
    CRITICAL: int = 0
    HIGH: int = 0
    MEDIUM: int = 0
    LOW: int = 0


class StreetIntelligenceSummary(BaseModel):
    """Summary metrics of street and intersection flood impact."""
    total_affected_roads: int = 0
    total_affected_intersections: int = 0
    max_street_depth_m: float = 0.0
    total_flooded_road_length_m: float = 0.0
    risk_counts: RiskCounts = Field(default_factory=RiskCounts)


class StreetFloodIntelligence(BaseModel):
    """Complete Street & Intersection Flood Intelligence assessment."""
    horizon: str = Field(..., description="Forecast horizon label: NOW, +1h, +2h, +3h")
    lead_time: str = Field(..., description="Lead time: 0h, +1h, +2h, +3h")
    rainfall_mm: float = Field(..., description="1-hour rainfall input for this horizon [mm]")
    summary: StreetIntelligenceSummary = Field(..., description="Summary impact statistics")
    affected_roads: List[AffectedRoad] = Field(default_factory=list, description="Impacted street segments")
    affected_intersections: List[AffectedIntersection] = Field(default_factory=list, description="Impacted junctions")
    roads_geojson: Dict[str, Any] = Field(..., description="GeoJSON FeatureCollection of affected streets (EPSG:4326)")
    intersections_geojson: Dict[str, Any] = Field(..., description="GeoJSON FeatureCollection of affected junctions (EPSG:4326)")
    provenance: Dict[str, str] = Field(..., description="Explicit provenance disclosures")
