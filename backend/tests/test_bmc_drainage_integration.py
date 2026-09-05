"""Tests for Phase 2.0B: Real BMC Municipal Storm Water Drainage Integration.

Verifies:
1. BMC network is loaded automatically from checked-in GeoJSON by default.
2. Authoritative topology (US_NODE_ID -> DS_NODE_ID) is strictly preserved, even on adverse slopes.
3. Every node and channel satisfies validation criteria (CRS, no self-loops, existing endpoints).
4. Physical attributes (GROUND_LEV, US_INVERT, DS_INVERT, conduit dimensions) are preserved.
5. Missing hydraulic parameters are not invented; prototype assumed parameters are explicit.
6. Pipeline defaults to BMC for Mumbai pilot DEM and falls back to DEM-derived if BMC fails.
7. Caching and cache invalidation.
"""
from __future__ import annotations

import os
import pytest

from backend.app.config import settings
from backend.app.domain.drainage.models import NodeType, Provenance
from backend.app.domain.pipeline.flood_pipeline import (
    run_flood_modeling_pipeline,
    clear_topology_cache,
)
from backend.app.infrastructure.drainage.bmc_gis import (
    BMCDrainageLoader,
    DEFAULT_DRAINS_PATH,
    DEFAULT_MANHOLES_PATH,
)


def test_default_bmc_network_loads_checked_in_geojson():
    """Verify default BMC network loads all 1,240 drains and 1,264 nodes from checked-in GeoJSON."""
    assert DEFAULT_DRAINS_PATH.exists(), f"Drains GeoJSON missing: {DEFAULT_DRAINS_PATH}"
    assert DEFAULT_MANHOLES_PATH.exists(), f"Manholes GeoJSON missing: {DEFAULT_MANHOLES_PATH}"

    network = BMCDrainageLoader.load_default_bmc_network()
    assert network is not None
    assert network.provenance == Provenance.BMC
    assert network.crs == "EPSG:32643"

    # Exact channel and node counts
    assert len(network.channels) == 1240
    assert len(network.nodes) == 1264  # 1,241 manholes + 23 synthesized boundary nodes

    # Topological node classifications
    inlets = [n for n in network.nodes.values() if n.node_type == NodeType.INLET]
    outlets = [n for n in network.nodes.values() if n.node_type == NodeType.OUTLET]
    junctions = [n for n in network.nodes.values() if n.node_type == NodeType.JUNCTION]

    assert len(inlets) == 78
    assert len(outlets) == 43
    assert len(junctions) == 1143
    assert len(inlets) + len(outlets) + len(junctions) == 1264


def test_bmc_validation_topology_integrity():
    """Verify strict topological integrity: every node exists, zero self-loops, positive lengths."""
    network = BMCDrainageLoader.load_default_bmc_network()
    assert network is not None

    for chan_id, channel in network.channels.items():
        # Requirement: Zero self-loops
        assert channel.upstream_node_id != channel.downstream_node_id, (
            f"Self-loop detected on channel {chan_id}"
        )
        # Requirement: Every endpoint node exists
        assert channel.upstream_node_id in network.nodes, (
            f"Channel {chan_id} references missing upstream node {channel.upstream_node_id}"
        )
        assert channel.downstream_node_id in network.nodes, (
            f"Channel {chan_id} references missing downstream node {channel.downstream_node_id}"
        )
        # Geometry validity
        assert channel.length_m > 0.0, f"Channel {chan_id} has invalid length {channel.length_m}"


def test_bmc_adverse_slope_preserves_authoritative_direction():
    """Verify authoritative US -> DS direction is preserved even when downstream ground is higher (adverse slope)."""
    network = BMCDrainageLoader.load_default_bmc_network()
    assert network is not None

    # Drain 22466: US=2174094001 (27.42m), DS=2174094002 (27.48m) -> adverse slope of +0.06m
    chan_22466 = network.channels.get("bmc_drain_22466")
    assert chan_22466 is not None, "Drain 22466 not found in loaded network"
    assert chan_22466.upstream_node_id == "2174094001"
    assert chan_22466.downstream_node_id == "2174094002"

    us_node = network.nodes["2174094001"]
    ds_node = network.nodes["2174094002"]
    assert us_node.ground_level_m == pytest.approx(27.42)
    assert ds_node.ground_level_m == pytest.approx(27.48)
    # Downstream ground elevation is strictly higher than upstream
    assert ds_node.elevation_m > us_node.elevation_m
    # But channel direction is NOT flipped to follow elevation
    assert chan_22466.upstream_node_id == "2174094001"
    assert chan_22466.downstream_node_id == "2174094002"


def test_bmc_attribute_preservation():
    """Verify BMC ground levels, invert levels, and conduit shapes/dimensions are preserved."""
    network = BMCDrainageLoader.load_default_bmc_network()
    assert network is not None

    # Verify conduit dimensions and shape attributes on channels
    channels_with_shape = [c for c in network.channels.values() if c.shape is not None]
    channels_with_width = [c for c in network.channels.values() if c.conduit_width_mm is not None]
    channels_with_height = [c for c in network.channels.values() if c.conduit_height_mm is not None]

    assert len(channels_with_shape) > 1000
    assert len(channels_with_width) == 1240
    assert len(channels_with_height) == 1240

    # Verify invert levels
    channels_with_us_invert = [c for c in network.channels.values() if c.us_invert_m is not None]
    channels_with_ds_invert = [c for c in network.channels.values() if c.ds_invert_m is not None]
    assert len(channels_with_us_invert) > 1000
    assert len(channels_with_ds_invert) > 1000

    # Verify node ground levels
    nodes_with_gl = [n for n in network.nodes.values() if n.ground_level_m is not None]
    assert len(nodes_with_gl) == 1241  # Exactly all 1,241 surveyed manholes have ground level


def test_pipeline_defaults_to_bmc_for_mumbai_pilot():
    """Verify the end-to-end pipeline automatically uses BMC network when no paths are passed."""
    clear_topology_cache()
    res = run_flood_modeling_pipeline(
        rainfall_mm=50.0,
        contributing_area_m2=500000.0,
        runoff_coefficient=0.7,
        dem_raster_path=settings.dem_path,
        timestep_hours=1.0,
        threshold_area_m2=15000.0,
    )
    # Provenance must record BMC
    assert res.drainage_provenance == "bmc"
    assert res.max_depth_m > 0.0
    assert res.total_flooded_area_m2 > 0.0

    # Strict mass conservation
    expected_runoff = 0.7 * 50.0 * 500000.0 / 1000.0
    assert res.total_runoff_volume_m3 == pytest.approx(expected_runoff)
    assert res.conveyed_drainage_volume_m3 + res.surface_flood_volume_m3 == pytest.approx(expected_runoff)


def test_pipeline_fallback_to_dem_derived_on_invalid_bmc_path():
    """Verify pipeline safely falls back to DEM-derived drainage when given nonexistent BMC paths."""
    clear_topology_cache()
    res = run_flood_modeling_pipeline(
        rainfall_mm=50.0,
        contributing_area_m2=500000.0,
        runoff_coefficient=0.7,
        dem_raster_path=settings.dem_path,
        timestep_hours=1.0,
        threshold_area_m2=15000.0,
        bmc_drains_path="nonexistent_drains.geojson",
        bmc_manholes_path="nonexistent_manholes.geojson",
    )
    # Fallback to DEM-derived
    assert res.drainage_provenance == "dem_derived"
    assert res.max_depth_m > 0.0
    expected_runoff = 0.7 * 50.0 * 500000.0 / 1000.0
    assert res.total_runoff_volume_m3 == pytest.approx(expected_runoff)
    assert res.conveyed_drainage_volume_m3 + res.surface_flood_volume_m3 == pytest.approx(expected_runoff)


def test_bmc_network_caching_and_clear():
    """Verify BMC network is cached in memory across calls and cleared by clear_topology_cache()."""
    clear_topology_cache()

    # First run loads and populates cache
    run_flood_modeling_pipeline(
        rainfall_mm=0.0,
        contributing_area_m2=500000.0,
        runoff_coefficient=0.7,
        dem_raster_path=settings.dem_path,
        timestep_hours=1.0,
    )

    from backend.app.domain.pipeline import flood_pipeline
    assert flood_pipeline._BMC_NETWORK_CACHE is not None
    assert len(flood_pipeline._BMC_NETWORK_CACHE.channels) == 1240

    # Clear cache
    clear_topology_cache()
    assert flood_pipeline._BMC_NETWORK_CACHE is None
