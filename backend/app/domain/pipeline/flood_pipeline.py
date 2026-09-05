"""End-to-end flood modeling pipeline.

This module orchestrates the complete flood modeling workflow:
1. Rainfall to runoff conversion (Rational Method)
2. Drainage network capacity analysis (Manning's equation)
3. Surface flood routing (D8 flow routing)
4. Structured flood result generation
"""
from __future__ import annotations

import logging
import os
from typing import Dict, Tuple, Optional
import numpy as np

logger = logging.getLogger(__name__)

try:
    from backend.app.domain.rainfall.runoff import RunoffVolume
    from backend.app.domain.drainage.models import DrainageNetwork, Provenance
    from backend.app.domain.drainage.capacity import (
        ChannelHydraulicParameters,
        compute_channel_capacity,
        compute_channel_excess
    )
    from backend.app.domain.flood.routing import route_flood_depth, FloodResult
    from backend.app.infrastructure.drainage.network_builder import NetworkBuilder
    from backend.app.infrastructure.drainage.raster_engine import RasterEngine
    from backend.app.infrastructure.drainage.bmc_gis import BMCDrainageLoader
except ImportError:
    from app.domain.rainfall.runoff import RunoffVolume
    from app.domain.drainage.models import DrainageNetwork, Provenance
    from app.domain.drainage.capacity import (
        ChannelHydraulicParameters,
        compute_channel_capacity,
        compute_channel_excess
    )
    from app.domain.flood.routing import route_flood_depth, FloodResult
    from app.infrastructure.drainage.network_builder import NetworkBuilder
    from app.infrastructure.drainage.raster_engine import RasterEngine
    from app.infrastructure.drainage.bmc_gis import BMCDrainageLoader


_TOPOLOGY_CACHE: Dict[Tuple[str, float], Tuple[RasterEngine, DrainageNetwork]] = {}
_BMC_NETWORK_CACHE: Optional[DrainageNetwork] = None


def clear_topology_cache() -> None:
    """Clear cached DEM topologies and drainage networks."""
    global _BMC_NETWORK_CACHE
    _TOPOLOGY_CACHE.clear()
    _BMC_NETWORK_CACHE = None


def run_flood_modeling_pipeline(
    rainfall_mm: float,
    contributing_area_m2: float,
    runoff_coefficient: float,
    dem_raster_path: str,
    timestep_hours: float = 1.0,
    threshold_area_m2: float = 0.0,
    bmc_drains_path: Optional[str] = None,
    bmc_manholes_path: Optional[str] = None,
) -> FloodResult:
    """Execute the complete flood modeling pipeline.

    Args:
        rainfall_mm: Accumulated rainfall depth over the timestep [mm]
        contributing_area_m2: Total contributing area for runoff calculation [m²]
        runoff_coefficient: Runoff coefficient [0, 1] (dimensionless)
        dem_raster_path: Path to DEM raster file for drainage network extraction
        timestep_hours: Duration of the timestep [hours] (default: 1.0)
        threshold_area_m2: Minimum drainage area threshold for stream initiation [m²] (default: 0.0)
        bmc_drains_path: Path to BMC Storm Water Drains (lines) GIS file (optional)
        bmc_manholes_path: Path to BMC Storm Water Manholes (points) GIS file (optional)

    Returns:
        FloodResult containing flood depth map and summary statistics

    Note:
        This function assumes uniform rainfall coefficient and contributing area
        across the entire domain for simplicity.

        The pipeline follows this flow:
        Rainfall → Runoff Volume → Drainage Network → Channel Capacity →
        Channel Excess (Surcharge) → Surface Flood Routing → Flood Depth

        BMC Municipal Storm Water Network is the DEFAULT drainage network for the
        Mumbai pilot. If BMC data loading or validation fails, a DEM-derived network
        is used as fallback.
    """
    global _BMC_NETWORK_CACHE

    # Validate inputs
    if rainfall_mm < 0:
        raise ValueError("Rainfall depth cannot be negative")
    if contributing_area_m2 < 0:
        raise ValueError("Contributing area cannot be negative")
    if not 0 <= runoff_coefficient <= 1:
        raise ValueError("Runoff coefficient must be between 0 and 1")
    if timestep_hours <= 0:
        raise ValueError("Timestep must be positive")

    # Step 1: Convert rainfall to runoff volume using Rational Method
    runoff = RunoffVolume(
        rainfall_mm=rainfall_mm,
        contributing_area_m2=contributing_area_m2,
        runoff_coefficient=runoff_coefficient,
        timestep_hours=timestep_hours
    )
    total_runoff_volume_m3 = runoff.volume_m3

    # Step 2: Initialize RasterEngine for elevation, flow directions, and affine transform
    cache_key = (dem_raster_path, float(threshold_area_m2))
    dem_network_cached: Optional[DrainageNetwork] = None
    if cache_key in _TOPOLOGY_CACHE:
        engine, dem_network_cached = _TOPOLOGY_CACHE[cache_key]
    else:
        engine = RasterEngine(dem_raster_path, threshold_area_m2=threshold_area_m2)
        engine.load_and_preprocess()
        engine.condition_dem()
        engine.compute_flow_direction()
        engine.compute_flow_accumulation()
        engine.apply_threshold()

    # Step 2b: Determine Drainage Network (authoritative BMC as default; DEM-derived as fallback)
    use_bmc = False
    drainage_network: Optional[DrainageNetwork] = None

    # Case A: Explicit caller-provided BMC paths
    if bmc_drains_path is not None or bmc_manholes_path is not None:
        if bmc_drains_path and bmc_manholes_path and os.path.exists(bmc_drains_path) and os.path.exists(bmc_manholes_path):
            try:
                loader = BMCDrainageLoader(
                    dem_raster_path=dem_raster_path,
                    filled_dem=engine.filled_dem,
                    transform=engine.transform
                )
                loaded_net = loader.load_bmc_network(bmc_drains_path, bmc_manholes_path)
                if loaded_net is not None:
                    use_bmc = True
                    drainage_network = loaded_net
                    logger.info("Successfully loaded specified BMC drainage network")
                else:
                    logger.warning("BMC loader returned None for specified paths, falling back to DEM-derived network")
            except Exception as e:
                logger.warning(f"Failed to load BMC network from specified paths: {e}, falling back to DEM-derived")
        else:
            logger.warning("Specified BMC GIS paths do not exist or are incomplete, falling back to DEM-derived")

    # Case B: Default - Load authoritative BMC network automatically for Mumbai pilot
    if not use_bmc and bmc_drains_path is None and bmc_manholes_path is None:
        # Check if DEM raster intersects Mumbai pilot bounding box (EPSG:32643)
        transform = engine.transform
        h, w = engine.height, engine.width
        xs = [transform.c, transform.c + w * transform.a]
        ys = [transform.f, transform.f + h * transform.e]
        dem_xmin, dem_xmax = min(xs), max(xs)
        dem_ymin, dem_ymax = min(ys), max(ys)
        is_mumbai_pilot = (dem_xmin <= 278530 and dem_xmax >= 274270 and
                           dem_ymin <= 2112120 and dem_ymax >= 2108300)

        if is_mumbai_pilot:
            if _BMC_NETWORK_CACHE is not None:
                drainage_network = _BMC_NETWORK_CACHE
                use_bmc = True
            else:
                try:
                    default_net = BMCDrainageLoader.load_default_bmc_network()
                    if default_net is not None:
                        _BMC_NETWORK_CACHE = default_net
                        drainage_network = default_net
                        use_bmc = True
                        logger.info("Successfully loaded default checked-in BMC drainage network")
                    else:
                        logger.warning("Default BMC drainage network could not be loaded, falling back to DEM-derived")
                except Exception as e:
                    logger.warning(f"Exception loading default BMC network: {e}, falling back to DEM-derived")
        else:
            logger.info("DEM raster bounds outside Mumbai pilot extent; using DEM-derived drainage network")

    # Fallback to DEM-derived network if BMC not used or failed validation/loading
    if not use_bmc or drainage_network is None:
        if dem_network_cached is not None:
            drainage_network = dem_network_cached
        else:
            builder = NetworkBuilder(engine)
            drainage_network = builder.build_network()
            _TOPOLOGY_CACHE[cache_key] = (engine, drainage_network)
        logger.info("Using DEM-derived drainage network (fallback)")
    else:
        # Cache engine in _TOPOLOGY_CACHE if not present
        if cache_key not in _TOPOLOGY_CACHE:
            _TOPOLOGY_CACHE[cache_key] = (engine, dem_network_cached)

    # If no drainage network was found, all runoff becomes surface flooding
    if len(drainage_network.channels) == 0:
        excess_runoff_m3 = {(0, 0): total_runoff_volume_m3}
        flow_dir = np.array([[0]], dtype=np.uint8)
        cell_size = _estimate_cell_size_from_raster(engine)
        return route_flood_depth(
            excess_runoff_m3=excess_runoff_m3,
            flow_direction=flow_dir,
            cell_size_m=cell_size,
            total_runoff_volume_m3=total_runoff_volume_m3,
            conveyed_drainage_volume_m3=0.0,
            drainage_provenance=drainage_network.provenance.value if hasattr(drainage_network, 'provenance') else "DEM_DERIVED"
        )

    # Step 3: Compute channel capacities and excess (surcharge)
    # Distinguish authoritative BMC network vs DEM-derived fallback with assumed hydraulic parameters
    if drainage_network.provenance == Provenance.BMC:
        uniform_params = ChannelHydraulicParameters(
            width_m=0.45,     # Assumed roadside curb-and-gutter inlet width for BMC network
            depth_m=0.25,     # Assumed roadside gutter depth
            manning_n=0.018,  # Urban masonry/concrete roadside drain (assumed prototype)
            slope_m_per_m=0.0006  # Assumed coastal gradient
        )
    else:
        uniform_params = ChannelHydraulicParameters(
            width_m=0.5,      # 0.5m wide roadside gutter (assumed prototype for DEM-derived)
            depth_m=0.3,      # 0.3m deep (assumed prototype)
            manning_n=0.018,  # Urban masonry/concrete roadside drain (assumed prototype)
            slope_m_per_m=0.0006  # Assumed coastal gradient
        )

    # Step 3: Compute channel capacities and excess (surcharge)
    # Pre-compute capacities for all channels in the network
    channel_caps: Dict[str, ChannelCapacity] = {}
    for channel_id, channel in drainage_network.channels.items():
        channel_caps[channel_id] = compute_channel_capacity(
            channel=channel,
            params=uniform_params,
            timestep_hours=timestep_hours
        )

    # Distribute runoff volume to inlet channels
    channel_excess: Dict[str, float] = {}
    channel_conveyed: Dict[str, float] = {}
    inflow_at_channels: Dict[str, float] = {}

    # Surface curb-and-gutter inlet opening intake capacity (governs street surface capture)
    if drainage_network.provenance == Provenance.BMC:
        curb_area = uniform_params.width_m * uniform_params.depth_m
        curb_perim = uniform_params.width_m + 2.0 * uniform_params.depth_m
        curb_radius = curb_area / curb_perim if curb_perim > 0 else 0.0
        curb_q = (1.0 / uniform_params.manning_n) * curb_area * (curb_radius ** (2.0 / 3.0)) * (uniform_params.slope_m_per_m ** 0.5)
        curb_inlet_capacity = curb_q * (timestep_hours * 3600.0)
    else:
        curb_inlet_capacity = float("inf")

    # Identify inlet channels and their effective intake capacity
    all_inlet_channels = [
        chan_id for chan_id, chan in drainage_network.channels.items()
        if drainage_network.nodes[chan.upstream_node_id].node_type.value == "inlet"
    ]
    eff_inlet_caps = {
        cid: min(curb_inlet_capacity, channel_caps[cid].capacity_volume_m3)
        for cid in all_inlet_channels
    }
    gravity_inlet_channels = [
        cid for cid in all_inlet_channels
        if eff_inlet_caps[cid] > 0
    ]
    # Fallback to all inlet channels if none have positive capacity (e.g. synthetic flat network)
    inlet_channels = gravity_inlet_channels if gravity_inlet_channels else all_inlet_channels

    if inlet_channels and total_runoff_volume_m3 > 0:
        base_inflow = total_runoff_volume_m3 / len(inlet_channels)
        inflow = {cid: base_inflow for cid in inlet_channels}
        excess = {cid: max(0.0, inflow[cid] - eff_inlet_caps[cid]) for cid in inlet_channels}
        total_excess = sum(excess.values())
        spare = {cid: max(0.0, eff_inlet_caps[cid] - inflow[cid]) for cid in inlet_channels}
        total_spare = sum(spare.values())

        # For non-surcharged design storms (<= 20 mm/h standard), surface runoff drains
        # to adjacent gravity inlets with spare capacity rather than creating artificial street ponding
        if rainfall_mm <= 20.0 and total_spare >= total_excess:
            for cid in inlet_channels:
                channel_excess[cid] = 0.0
                channel_conveyed[cid] = inflow[cid]
            if total_excess > 0:
                for cid in inlet_channels:
                    if excess[cid] > 0:
                        channel_conveyed[cid] = eff_inlet_caps[cid]
                remaining_to_add = total_excess
                for cid in inlet_channels:
                    if spare[cid] > 0 and remaining_to_add > 0:
                        add = min(spare[cid], remaining_to_add)
                        channel_conveyed[cid] += add
                        remaining_to_add -= add
        else:
            for cid in inlet_channels:
                channel_excess[cid] = excess[cid]
                channel_conveyed[cid] = min(inflow[cid], eff_inlet_caps[cid])
    else:
        for cid in drainage_network.channels.keys():
            channel_excess[cid] = 0.0
            channel_conveyed[cid] = 0.0

    # Ensure all other non-inlet channels have records
    for channel_id in drainage_network.channels.keys():
        if channel_id not in channel_excess:
            channel_excess[channel_id] = 0.0
            channel_conveyed[channel_id] = 0.0

    # Step 4: Convert channel excess (surcharge) to spatial excess runoff for surface routing
    # Surcharge from each channel is placed at its downstream node location
    excess_runoff_m3: Dict[Tuple[int, int], float] = {}

    for channel_id, excess_volume in channel_excess.items():
        if excess_volume > 0:
            channel = drainage_network.channels[channel_id]
            downstream_id = channel.downstream_node_id
            try:
                if downstream_id.startswith('n_') and downstream_id.count('_') == 2:
                    # DEM-derived format: n_row_col
                    _, row_str, col_str = downstream_id.split('_')
                    row, col = int(row_str), int(col_str)
                else:
                    # BMC or custom format: project coordinates onto raster grid
                    node = drainage_network.nodes[downstream_id]
                    inv_transform = ~engine.transform
                    col_f, row_f = inv_transform * (node.x, node.y)
                    col_int = int(col_f + 0.5)
                    row_int = int(row_f + 0.5)
                    # Check bounds with edge snapping for boundary nodes
                    if -5 <= row_int < engine.height + 5 and -5 <= col_int < engine.width + 5:
                        row = max(0, min(engine.height - 1, row_int))
                        col = max(0, min(engine.width - 1, col_int))
                    else:
                        logger.warning(
                            f"BMC node {downstream_id} at ({node.x}, {node.y}) maps to raster "
                            f"({row_int}, {col_int}) which is out of bounds. Skipping channel excess."
                        )
                        continue
                excess_runoff_m3[(row, col)] = excess_runoff_m3.get((row, col), 0.0) + excess_volume
            except (ValueError, IndexError) as e:
                logger.warning(
                    f"Could not parse downstream node ID {downstream_id} for channel {channel_id}: {e}. "
                    f"Skipping channel excess."
                )
                continue

    # Note: When runoff <= drainage capacity, all runoff is safely conveyed inside
    # the drainage network (excess_runoff_m3 is empty). Runoff is NOT dumped onto
    # surface cells, preventing artificial single-cell pond spikes.
    total_conveyed_volume_m3 = sum(channel_conveyed.values())

    # Step 5: Route excess runoff over surface to compute flood depth
    flow_direction = engine.get_flow_direction()
    cell_size = _estimate_cell_size_from_raster(engine)
    nodata_mask = None

    flood_result = route_flood_depth(
        excess_runoff_m3=excess_runoff_m3,
        flow_direction=flow_direction,
        cell_size_m=cell_size,
        nodata_mask=nodata_mask,
        total_runoff_volume_m3=total_runoff_volume_m3,
        conveyed_drainage_volume_m3=total_conveyed_volume_m3,
        drainage_provenance=drainage_network.provenance.value if hasattr(drainage_network, 'provenance') else "BMC"
    )

    return flood_result


def _estimate_cell_size_from_raster(engine: RasterEngine) -> float:
    """Estimate cell size from raster engine.

    Args:
        engine: Initialized RasterEngine instance

    Returns:
        Cell size in meters (assuming square cells)
    """
    if hasattr(engine, "get_cell_size"):
        cs = engine.get_cell_size()
        if cs > 0:
            return float(cs)

    # Extract cell size from transform (assuming square pixels)
    transform = engine.get_transform() if hasattr(engine, 'get_transform') else None
    if transform is not None:
        # In affine transform, pixel width is at index 0 (a)
        width = abs(transform[0])
        if width > 0:
            return float(width)

    # Fallback default
    return 30.0


__all__ = ["run_flood_modeling_pipeline", "clear_topology_cache"]