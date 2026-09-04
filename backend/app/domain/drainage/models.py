"""Domain models for drainage network."""
from __future__ import annotations

from pydantic import BaseModel, Field, validator
from enum import Enum
from typing import Dict, Optional


class NodeType(str, Enum):
    INLET = "inlet"
    JUNCTION = "junction"
    OUTLET = "outlet"


class Provenance(str, Enum):
    OSM = "osm"
    DEM_DERIVED = "dem_derived"


class DrainageNode(BaseModel):
    id: str
    x: float
    y: float
    elevation_m: float
    node_type: NodeType
    provenance: Provenance

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

    class Config:
        json_encoders = {
            # For datetime handling if needed later
        }


class DrainageNetwork(BaseModel):
    nodes: Dict[str, DrainageNode]
    channels: Dict[str, DrainageChannel]
    crs: str

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