"""BMC Storm Water GIS Integration for Drainage Network.

Loads authoritative BMC Storm Water Drains and Storm Water Manholes GIS data
as the default drainage network for the Mumbai pilot area.
"""
from __future__ import annotations

import json
import logging
import os
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    from backend.app.domain.drainage.models import (
        DrainageChannel,
        DrainageNode,
        DrainageNetwork,
        NodeType,
        Provenance,
    )
    from backend.app.infrastructure.drainage.raster_engine import RasterEngine
except ImportError:
    from app.domain.drainage.models import (
        DrainageChannel,
        DrainageNode,
        DrainageNetwork,
        NodeType,
        Provenance,
    )
    from app.infrastructure.drainage.raster_engine import RasterEngine

logger = logging.getLogger(__name__)

# Default checked-in BMC GeoJSON paths
DEFAULT_BMC_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "drainage" / "bmc"
DEFAULT_DRAINS_PATH = DEFAULT_BMC_DIR / "storm_water_drains_pilot.geojson"
DEFAULT_MANHOLES_PATH = DEFAULT_BMC_DIR / "storm_water_manholes_pilot.geojson"


class BMCDrainageLoader:
    """Loads, validates, and constructs DrainageNetwork from authoritative BMC Storm Water GIS data."""

    def __init__(
        self,
        dem_raster_path: Optional[str] = None,
        filled_dem: Optional[Any] = None,
        transform: Optional[Any] = None,
    ):
        self.dem_raster_path = dem_raster_path
        self.filled_dem = filled_dem
        self.transform = transform

    @classmethod
    def load_default_bmc_network(cls) -> Optional[DrainageNetwork]:
        """Load and validate the default checked-in BMC drainage network."""
        if not DEFAULT_DRAINS_PATH.exists() or not DEFAULT_MANHOLES_PATH.exists():
            logger.warning(
                f"Default BMC GeoJSON files not found at {DEFAULT_BMC_DIR}. Falling back to DEM-derived."
            )
            return None
        loader = cls()
        return loader.load_bmc_network(str(DEFAULT_DRAINS_PATH), str(DEFAULT_MANHOLES_PATH))

    def load_bmc_network(
        self,
        drains_path: str,
        manholes_path: str,
    ) -> Optional[DrainageNetwork]:
        """
        Load and validate BMC Storm Water Drains and Manholes GIS data.

        Requirements:
        1. CRS must be EPSG:32643.
        2. Geometries must be valid Point (manholes) and LineString (drains).
        3. Every US_NODE_ID and DS_NODE_ID must exist.
        4. Zero self-loops (US_NODE_ID != DS_NODE_ID).
        5. Authoritative US -> DS direction strictly preserved (never inverted by elevation).
        6. BMC attributes preserved: GROUND_LEV, US_INVERT, DS_INVERT, SHAPE_1, CONDUIT_WI, CONDUIT_HE.
        """
        try:
            if not os.path.exists(drains_path) or not os.path.exists(manholes_path):
                logger.error(f"BMC file paths do not exist: drains={drains_path}, manholes={manholes_path}")
                return None

            with open(manholes_path, "r", encoding="utf-8") as f:
                mh_data = json.load(f)
            with open(drains_path, "r", encoding="utf-8") as f:
                dr_data = json.load(f)

            # 1. Validate CRS
            crs_mh = str(mh_data.get("crs", {}))
            crs_dr = str(dr_data.get("crs", {}))
            if "32643" not in crs_mh or "32643" not in crs_dr:
                logger.error(f"Invalid BMC CRS. Expected EPSG:32643, got manholes: {crs_mh}, drains: {crs_dr}")
                return None

            # 2. Process Manholes -> Nodes
            nodes: Dict[str, DrainageNode] = {}
            for idx, feat in enumerate(mh_data.get("features", [])):
                props = feat.get("properties", {})
                geom = feat.get("geometry", {})
                if not geom or geom.get("type") != "Point" or len(geom.get("coordinates", [])) < 2:
                    logger.warning(f"Manhole at index {idx} has invalid geometry: {geom}")
                    continue

                node_id = str(props.get("NODE_ID") or props.get("OBJECTID") or f"mh_{idx}")
                coords = geom["coordinates"]
                x, y = float(coords[0]), float(coords[1])
                gl = props.get("GROUND_LEV")
                elev = float(gl) if gl is not None else 0.0

                nodes[node_id] = DrainageNode(
                    id=node_id,
                    x=x,
                    y=y,
                    elevation_m=elev,
                    ground_level_m=elev if gl is not None else None,
                    node_type=NodeType.JUNCTION,  # refined by degree below
                    provenance=Provenance.BMC,
                    metadata={"objectid": props.get("OBJECTID")},
                )

            if not nodes:
                logger.error("No valid manholes loaded from BMC dataset")
                return None

            # 3. Create boundary/outfall nodes for drains with unlisted endpoints
            for idx, feat in enumerate(dr_data.get("features", [])):
                props = feat.get("properties", {})
                geom = feat.get("geometry", {})
                coords = geom.get("coordinates", [])
                if not geom or geom.get("type") != "LineString" or len(coords) < 2:
                    continue

                us_id = str(props.get("US_NODE_ID"))
                ds_id = str(props.get("DS_NODE_ID"))

                if us_id not in nodes:
                    us_inv = props.get("US_INVERT")
                    elev = float(us_inv) if us_inv is not None else 0.0
                    nodes[us_id] = DrainageNode(
                        id=us_id,
                        x=float(coords[0][0]),
                        y=float(coords[0][1]),
                        elevation_m=elev,
                        ground_level_m=None,
                        node_type=NodeType.INLET,
                        provenance=Provenance.BMC,
                        metadata={"source": "drain_boundary_endpoint"},
                    )

                if ds_id not in nodes:
                    ds_inv = props.get("DS_INVERT")
                    elev = float(ds_inv) if ds_inv is not None else 0.0
                    nodes[ds_id] = DrainageNode(
                        id=ds_id,
                        x=float(coords[-1][0]),
                        y=float(coords[-1][1]),
                        elevation_m=elev,
                        ground_level_m=None,
                        node_type=NodeType.OUTLET,
                        provenance=Provenance.BMC,
                        metadata={"source": "drain_boundary_endpoint"},
                    )

            # 4. Process Drains -> Channels
            channels: Dict[str, DrainageChannel] = {}
            in_deg = Counter()
            out_deg = Counter()

            for idx, feat in enumerate(dr_data.get("features", [])):
                props = feat.get("properties", {})
                geom = feat.get("geometry", {})
                coords = geom.get("coordinates", [])

                # Validate geometry
                if not geom or geom.get("type") != "LineString" or len(coords) < 2:
                    logger.error(f"Drain at index {idx} has invalid geometry: {geom}")
                    return None

                us_id = str(props.get("US_NODE_ID"))
                ds_id = str(props.get("DS_NODE_ID"))

                # Validate no self-loops
                if us_id == ds_id:
                    logger.error(f"Drain {idx} has self-loop: US {us_id} == DS {ds_id}")
                    return None

                # Validate node existence
                if us_id not in nodes:
                    logger.error(f"Drain {idx} references non-existent US_NODE_ID: {us_id}")
                    return None
                if ds_id not in nodes:
                    logger.error(f"Drain {idx} references non-existent DS_NODE_ID: {ds_id}")
                    return None

                obj_id = props.get("OBJECTID")
                chan_id = f"bmc_drain_{obj_id}" if obj_id else f"bmc_drain_{idx}"
                length_m = float(props.get("CONDUIT_LE") or props.get("SHAPE.LEN") or 1.0)
                if length_m <= 0:
                    length_m = 1.0

                channels[chan_id] = DrainageChannel(
                    id=chan_id,
                    upstream_node_id=us_id,      # Authoritative US_NODE_ID preserved
                    downstream_node_id=ds_id,    # Authoritative DS_NODE_ID preserved
                    length_m=length_m,
                    provenance=Provenance.BMC,
                    us_invert_m=float(props["US_INVERT"]) if props.get("US_INVERT") is not None else None,
                    ds_invert_m=float(props["DS_INVERT"]) if props.get("DS_INVERT") is not None else None,
                    shape=str(props.get("SHAPE_1")) if props.get("SHAPE_1") else None,
                    conduit_width_mm=float(props["CONDUIT_WI"]) if props.get("CONDUIT_WI") is not None else None,
                    conduit_height_mm=float(props["CONDUIT_HE"]) if props.get("CONDUIT_HE") is not None else None,
                    metadata={
                        "objectid": obj_id,
                        "user_text2": props.get("USER_TEXT2"),
                        "conduit_le": props.get("CONDUIT_LE"),
                    },
                )
                out_deg[us_id] += 1
                in_deg[ds_id] += 1

            if not channels:
                logger.error("No valid drains loaded from BMC dataset")
                return None

            # 5. Refine Node Types based on topological degree
            for nid, node in nodes.items():
                if in_deg[nid] == 0 and out_deg[nid] > 0:
                    node.node_type = NodeType.INLET
                elif out_deg[nid] == 0 and in_deg[nid] > 0:
                    node.node_type = NodeType.OUTLET
                else:
                    node.node_type = NodeType.JUNCTION

            logger.info(
                f"Successfully loaded BMC drainage network: {len(nodes)} nodes "
                f"({sum(1 for n in nodes.values() if n.node_type == NodeType.INLET)} inlets, "
                f"{sum(1 for n in nodes.values() if n.node_type == NodeType.OUTLET)} outlets), "
                f"{len(channels)} channels (authoritative connectivity)"
            )

            return DrainageNetwork(
                nodes=nodes,
                channels=channels,
                crs="EPSG:32643",
                provenance=Provenance.BMC,
            )

        except Exception as e:
            logger.error(f"Failed to load BMC GIS data: {e}", exc_info=True)
            return None
