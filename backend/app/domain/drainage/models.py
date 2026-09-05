"""Domain models for drainage network."""
from __future__ import annotations

import math
from pydantic import BaseModel, Field, validator
from enum import Enum
from typing import Any, Dict, Optional, Tuple


class NodeType(str, Enum):
    INLET = "inlet"
    JUNCTION = "junction"
    OUTLET = "outlet"


class Provenance(str, Enum):
    OSM = "osm"
    DEM_DERIVED = "dem_derived"
    BMC = "bmc"


class SlopeStatus(str, Enum):
    POSITIVE = "POSITIVE"    # Forward gravity slope (US_INVERT > DS_INVERT)
    FLAT = "FLAT"            # Zero slope (US_INVERT == DS_INVERT)
    ADVERSE = "ADVERSE"      # Adverse slope (US_INVERT < DS_INVERT)
    MISSING = "MISSING"      # Missing or invalid inverts / length


class HydraulicAttributeSource(str, Enum):
    BMC_AUTHORITATIVE = "BMC_AUTHORITATIVE"
    ASSUMED = "ASSUMED"
    UNAVAILABLE = "UNAVAILABLE"


class DrainageNode(BaseModel):
    id: str
    x: float
    y: float
    elevation_m: float
    node_type: NodeType
    provenance: Provenance
    ground_level_m: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        json_encoders = {
            # For datetime handling if needed later
        }


class DrainageChannel(BaseModel):
    id: str
    upstream_node_id: str
    downstream_node_id: str
    length_m: float = Field(..., gt=0)
    provenance: Provenance
    us_invert_m: Optional[float] = None
    ds_invert_m: Optional[float] = None
    shape: Optional[str] = None
    conduit_width_mm: Optional[float] = None
    conduit_height_mm: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None

    def compute_longitudinal_slope(self) -> Optional[float]:
        """Compute longitudinal slope from (us_invert_m - ds_invert_m) / length_m.

        Returns None if either invert is missing or length <= 0.
        Authoritative US_NODE_ID -> DS_NODE_ID direction is strictly preserved (never reversed).
        """
        if self.us_invert_m is not None and self.ds_invert_m is not None and self.length_m > 0:
            return (self.us_invert_m - self.ds_invert_m) / self.length_m
        return None

    def get_slope_status(self) -> SlopeStatus:
        """Get physical status of invert-derived longitudinal slope."""
        slope = self.compute_longitudinal_slope()
        if slope is None:
            return SlopeStatus.MISSING
        if slope > 0:
            return SlopeStatus.POSITIVE
        elif slope == 0:
            return SlopeStatus.FLAT
        else:
            return SlopeStatus.ADVERSE

    def compute_hydraulic_geometry(self) -> Tuple[Optional[float], Optional[float], Optional[float], bool]:
        """Compute hydraulic geometry (area_m2, wetted_perimeter_m, hydraulic_radius_m, is_supported).

        Supports RECT, OREC, and CIRC using actual BMC dimensions:
        - RECT (box conduit): Area = W * H, Wetted Perimeter = W + 2H, R = A / P
        - OREC (open rectangular channel): Area = W * H, Wetted Perimeter = W + 2H, R = A / P
        - CIRC (circular pipe): Area = pi * D^2 / 4, Wetted Perimeter = pi * D, R = D / 4
        Other shapes (or missing/non-positive dimensions) return (None, None, None, False).

        Returns:
            (area_m2, wetted_perimeter_m, hydraulic_radius_m, is_supported)
        """
        if self.shape in ("RECT", "OREC") and self.conduit_width_mm and self.conduit_height_mm:
            w = self.conduit_width_mm / 1000.0
            h = self.conduit_height_mm / 1000.0
            if w > 0 and h > 0:
                a = w * h
                p = w + 2.0 * h
                r = a / p if p > 0 else 0.0
                return a, p, r, True
        elif self.shape == "CIRC" and self.conduit_width_mm:
            d = self.conduit_width_mm / 1000.0
            if d > 0:
                a = math.pi * (d ** 2) / 4.0
                p = math.pi * d
                r = d / 4.0
                return a, p, r, True

        return None, None, None, False

    class Config:
        json_encoders = {
            # For datetime handling if needed later
        }


class DrainageNetwork(BaseModel):
    nodes: Dict[str, DrainageNode]
    channels: Dict[str, DrainageChannel]
    crs: str
    provenance: Provenance = Provenance.BMC

    @validator('channels')
    def validate_channel_references(cls, v, values):
        """Validate that channel references point to existing nodes."""
        if 'nodes' not in values:
            return v

        node_ids = set(values['nodes'].keys())
        for channel_id, channel in v.items():
            if channel.upstream_node_id not in node_ids:
                raise ValueError(
                    f"Channel {channel_id} references non-existent upstream node "
                    f"{channel.upstream_node_id}"
                )
            if channel.downstream_node_id not in node_ids:
                raise ValueError(
                    f"Channel {channel_id} references non-existent downstream node "
                    f"{channel.downstream_node_id}"
                )
        return v

    class Config:
        json_encoders = {
            # For datetime handling if needed later
        }