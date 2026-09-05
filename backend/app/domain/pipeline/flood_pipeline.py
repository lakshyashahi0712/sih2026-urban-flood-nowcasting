"""End-to-end flood modeling pipeline.

This module orchestrates the complete flood modeling workflow:
1. Rainfall to runoff conversion (Rational Method)
2. Drainage network capacity analysis (Manning's equation)
3. Surface flood routing (D8 flow routing)
4. Structured flood result generation
"""
from __future__ import annotations

from typing import Dict, Tuple, Optional
import numpy as np

from backend.app.domain.rainfall.runoff import RunoffVolume
from backend.app.domain.drainage.models import DrainageNetwork
from backend.app.domain.drainage.capacity import (
    ChannelHydraulicParameters,
    compute_channel_capacity,
    compute_channel_excess
)
from backend.app.domain.flood.routing import route_flood_depth, FloodResult
from backend.app.infrastructure.drainage.network_builder import NetworkBuilder
from backend.app.infrastructure.drainage.raster_engine import RasterEngine


def run_flood_modeling_pipeline(
    rainfall_mm: float,
    contributing_area_m2: float,
    runoff_coefficient: float,
    dem_raster_path: str,
    timestep_hours: float = 1.0,
    threshold_area_m2: float = 0.0
) -> FloodResult:
    """Execute the complete flood modeling pipeline.

    Args:
        rainfall_mm: Accumulated rainfall depth over the timestep [mm]
        contributing_area_m2: Total contributing area for runoff calculation [m²]
        runoff_coefficient: Runoff coefficient [0, 1] (dimensionless)
        dem_raster_path: Path to DEM raster file for drainage network extraction
        timestep_hours: Duration of the timestep [hours] (default: 1.0)
        threshold_area_m2: Minimum drainage area threshold for stream initiation [m²] (default: 0.0)

    Returns:
        FloodResult containing flood depth map and summary statistics

    Note:
        This function assumes uniform rainfall coefficient and contributing area
        across the entire domain for simplicity. In a more sophisticated implementation,
        these would vary spatially based on land use, soil type, etc.

        The pipeline follows this flow:
        Rainfall → Runoff Volume → Drainage Network → Channel Capacity →
        Channel Excess (Surcharge) → Surface Flood Routing → Flood Depth
    """
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

    # Step 2: Build drainage network from DEM
    engine = RasterEngine(dem_raster_path, threshold_area_m2=threshold_area_m2)
    engine.load_and_preprocess()
    engine.condition_dem()
    engine.compute_flow_direction()
    engine.compute_flow_accumulation()
    engine.apply_threshold()

    builder = NetworkBuilder(engine)
    drainage_network = builder.build_network()

    # If no drainage network was found, all runoff becomes surface flooding
    if len(drainage_network.channels) == 0:
        # All runoff becomes excess that routes over the surface
        excess_runoff_m3 = {(0, 0): total_runoff_volume_m3}  # Place at origin for simplicity
        # We need a flow direction array - create a simple sink grid
        # In practice, we'd get this from the raster engine, but since we have no network,
        # we'll create a minimal flow direction array
        # For now, we'll route everything to a single cell
        flow_dir = np.array([[0]], dtype=np.uint8)  # Single sink cell
        cell_size = _estimate_cell_size_from_raster(engine)
        return route_flood_depth(excess_runoff_m3, flow_dir, cell_size)

    # Step 3: Compute channel capacities and excess (surcharge)
    # For simplicity, we'll use uniform hydraulic parameters for all channels
    # In practice, these would be derived from channel geometry
    uniform_params = ChannelHydraulicParameters(
        width_m=2.0,      # 2m wide channels (prototypical)
        depth_m=1.0,      # 1m deep channels (prototypical)
        manning_n=0.015,  # Concrete channel (prototypical)
        slope_m_per_m=0.001  # Mild slope (prototypical)
    )

    # Distribute runoff volume to channels based on network topology
    # For MVP, we'll assume all runoff enters at the most upstream nodes
    # and routes through the network
    channel_excess: Dict[str, float] = {}
    inflow_at_channels: Dict[str, float] = {}

    # Initialize inflow at channels (simplified: put all inflow at inlet channels)
    inlet_channels = [
        chan_id for chan_id, chan in drainage_network.channels.items()
        if drainage_network.nodes[chan.upstream_node_id].node_type.value == "inlet"
    ]

    if inlet_channels:
        # Distribute inflow equally among inlet channels (simplified approach)
        inflow_per_channel = total_runoff_volume_m3 / len(inlet_channels)
        for chan_id in inlet_channels:
            inflow_at_channels[chan_id] = inflow_per_channel

    # Compute capacity and excess for each channel
    for channel_id, channel in drainage_network.channels.items():
        inflow_volume = inflow_at_channels.get(channel_id, 0.0)

        capacity = compute_channel_capacity(
            channel=channel,
            params=uniform_params,
            timestep_hours=timestep_hours
        )

        excess = compute_channel_excess(inflow_volume, capacity)
        channel_excess[channel_id] = excess

    # Step 4: Convert channel excess to spatial excess runoff for surface routing
    # For simplicity, we'll distribute excess from each channel to its downstream node location
    excess_runoff_m3: Dict[Tuple[int, int], float] = {}

    for channel_id, excess_volume in channel_excess.items():
        if excess_volume > 0:
            channel = drainage_network.channels[channel_id]
            # Get downstream node coordinates from node ID (format: n_row_col)
            downstream_id = channel.downstream_node_id
            try:
                _, row_str, col_str = downstream_id.split('_')
                row, col = int(row_str), int(col_str)
                excess_runoff_m3[(row, col)] = excess_runoff_m3.get((row, col), 0.0) + excess_volume
            except (ValueError, IndexError):
                # If we can't parse coordinates, skip this channel's excess
                continue

    # If no excess was generated (all runoff conveyed), still need to handle potential direct rainfall excess
    # For now, if no channel excess, we'll check if there's any direct surface excess
    if not excess_runoff_m3 and total_runoff_volume_m3 > 0:
        # Simple approach: put any remaining volume at the outlet
        outlet_channels = [
            chan_id for chan_id, chan in drainage_network.channels.items()
            if drainage_network.nodes[chan.downstream_node_id].node_type.value == "outlet"
        ]
        if outlet_channels:
            channel = drainage_network.channels[outlet_channels[0]]
            _, row_str, col_str = channel.downstream_node_id.split('_')
            row, col = int(row_str), int(col_str)
            excess_runoff_m3[(row, col)] = total_runoff_volume_m3

    # Step 5: Route excess runoff over surface to compute flood depth
    flow_direction = engine.get_flow_direction()
    cell_size = _estimate_cell_size_from_raster(engine)
    nodata_mask = None  # RasterEngine doesn't expose nodata mask directly in this version
    # Note: In a more complete implementation, we would extract the nodata mask from the engine

    flood_result = route_flood_depth(
        excess_runoff_m3=excess_runoff_m3,
        flow_direction=flow_direction,
        cell_size_m=cell_size,
        nodata_mask=nodata_mask
    )

    return flood_result


def _estimate_cell_size_from_raster(engine: RasterEngine) -> float:
    """Estimate cell size from raster engine transform.

    Args:
        engine: Initialized RasterEngine instance

    Returns:
        Cell size in meters (assuming square cells)
    """
    # Extract cell size from transform (assuming square pixels)
    transform = engine.get_transform() if hasattr(engine, 'get_transform') else None
    if transform is not None:
        # For a standard geotransform, pixel width is at index 1
        return abs(transform[1])  # x pixel size
    else:
        # Fallback - this should ideally come from raster metadata
        return 10.0  # Default 10m cells


__all__ = ["run_flood_modeling_pipeline"]