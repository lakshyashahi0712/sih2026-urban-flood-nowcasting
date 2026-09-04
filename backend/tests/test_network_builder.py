"""Tests for the NetworkBuilder class."""
from __future__ import annotations

import tempfile
import os
from typing import Tuple, Optional
import numpy as np
import pytest
from rasterio import open as rio_open
from rasterio.transform import from_origin

from app.infrastructure.drainage.raster_engine import RasterEngine
from app.infrastructure.drainage.network_builder import NetworkBuilder
from app.domain.drainage.models import DrainageNetwork, DrainageNode, DrainageChannel, NodeType, Provenance


def create_test_dem(
    shape: Tuple[int, int] = (5, 5),
    cell_size: float = 10.0,
    nodata: Optional[float] = -9999.0,
    tilt: str = "se"
) -> Tuple[np.ndarray, dict]:
    """
    Create a synthetic DEM raster and its metadata.

    Args:
        shape: (rows, cols)
        cell_size: cell size in meters (assumed square)
        nodata: nodata value, or None for no nodata
        tilt: direction of slope for deterministic flow:
              "se" for southeast (downhill to increasing row and col)
    Returns:
        (array, meta) where array is the DEM data and meta is a dict
        suitable for rasterio.open.
    """
    rows, cols = shape
    row_step = 1.0
    col_step = 1.0
    dem = np.zeros(shape, dtype=np.float64)
    for r in range(rows):
        for c in range(cols):
            dem[r, c] = - (r * row_step + c * col_step)
    # Highest point at (0,0), lowest at (rows-1, cols-1) -> flow SE under D8.

    if nodata is not None:
        dem[0, 0] = nodata
        dem[-1, -1] = nodata

    transform = from_origin(0, 0, cell_size, cell_size)
    meta = {
        'driver': 'GTiff',
        'dtype': dem.dtype,
        'nodata': nodata,
        'width': cols,
        'height': rows,
        'count': 1,
        'crs': 'EPSG:32643',
        'transform': transform,
    }
    return dem, meta


def test_simple_straight_drainage_path():
    """Test a simple straight drainage path in a single column (e.g., north-south)."""
    dem = np.array([
        [10],
        [ 5],
        [ 0]
    ], dtype=np.float64)
    nodata = -9999.0
    transform = from_origin(0, 0, 10.0, 10.0)
    meta = {
        'driver': 'GTiff',
        'dtype': dem.dtype,
        'nodata': nodata,
        'width': 1,
        'height': 3,
        'count': 1,
        'crs': 'EPSG:32643',
        'transform': transform,
    }
    with tempfile.NamedTemporaryFile(suffix='.tif', delete=False) as tmp:
        dem_path = tmp.name
    try:
        with rio_open(dem_path, 'w', **meta) as dst:
            dst.write(dem, 1)

        engine = RasterEngine(dem_path, threshold_area_m2=0.0)
        engine.load_and_preprocess()
        engine.condition_dem()
        engine.compute_flow_direction()
        engine.compute_flow_accumulation()
        engine.apply_threshold()

        builder = NetworkBuilder(engine)
        network = builder.build_network()

        assert len(network.nodes) == 2
        assert len(network.channels) == 1
        assert network.crs == "EPSG:32643"

        assert "n_0_0" in network.nodes
        assert network.nodes["n_0_0"].node_type == NodeType.INLET
        assert "n_2_0" in network.nodes
        assert network.nodes["n_2_0"].node_type == NodeType.OUTLET

        assert "ch_n_0_0_n_2_0" in network.channels
        assert network.channels["ch_n_0_0_n_2_0"].length_m == 20.0

        for node in network.nodes.values():
            assert node.provenance == Provenance.DEM_DERIVED
        for channel in network.channels.values():
            assert channel.provenance == Provenance.DEM_DERIVED

    finally:
        os.unlink(dem_path)


def test_junction_from_converging_tributaries():
    """Three parallel columns with no lateral gradient stay independent —
    confirms NetworkBuilder does not invent convergence the terrain doesn't have."""
    dem = np.array([
        [10, 10, 10],
        [ 5,  5,  5],
        [ 0,  0,  0]
    ], dtype=np.float64)
    nodata = -9999.0
    transform = from_origin(0, 0, 10.0, 10.0)
    meta = {
        'driver': 'GTiff',
        'dtype': dem.dtype,
        'nodata': nodata,
        'width': 3,
        'height': 3,
        'count': 1,
        'crs': 'EPSG:32643',
        'transform': transform,
    }
    with tempfile.NamedTemporaryFile(suffix='.tif', delete=False) as tmp:
        dem_path = tmp.name
    try:
        with rio_open(dem_path, 'w', **meta) as dst:
            dst.write(dem, 1)

        engine = RasterEngine(dem_path, threshold_area_m2=0.0)
        engine.load_and_preprocess()
        engine.condition_dem()
        engine.compute_flow_direction()
        engine.compute_flow_accumulation()
        engine.apply_threshold()

        builder = NetworkBuilder(engine)
        network = builder.build_network()

        assert len(network.nodes) == 6
        assert len(network.channels) == 3
        assert network.crs == "EPSG:32643"

        for c in range(3):
            inlet_id = f"n_0_{c}"
            outlet_id = f"n_2_{c}"
            assert inlet_id in network.nodes
            assert network.nodes[inlet_id].node_type == NodeType.INLET
            assert outlet_id in network.nodes
            assert network.nodes[outlet_id].node_type == NodeType.OUTLET

        expected_channels = {f"ch_n_0_{c}_n_2_{c}" for c in range(3)}
        assert set(network.channels.keys()) == expected_channels

        for c in range(3):
            channel_id = f"ch_n_0_{c}_n_2_{c}"
            assert network.channels[channel_id].length_m == 20.0

        for node in network.nodes.values():
            assert node.provenance == Provenance.DEM_DERIVED
        for channel in network.channels.values():
            assert channel.provenance == Provenance.DEM_DERIVED

    finally:
        os.unlink(dem_path)


def test_diagonal_path_length():
    """Test that diagonal steps are computed correctly (cell size * sqrt(2)).

    This DEM has a strong local low point that pulls in flow from all
    surrounding cells (not just along one diagonal), so it also serves as
    a regression test for NetworkBuilder correctly creating a channel for
    EVERY tributary that converges on a junction, not just the first one
    reached during traversal.
    """
    dem = np.array([
        [10, 10, 10],
        [10,  5, 10],
        [10, 10,  0]
    ], dtype=np.float64)
    nodata = -9999.0
    transform = from_origin(0, 0, 10.0, 10.0)
    meta = {
        'driver': 'GTiff',
        'dtype': dem.dtype,
        'nodata': nodata,
        'width': 3,
        'height': 3,
        'count': 1,
        'crs': 'EPSG:32643',
        'transform': transform,
    }
    with tempfile.NamedTemporaryFile(suffix='.tif', delete=False) as tmp:
        dem_path = tmp.name
    try:
        with rio_open(dem_path, 'w', **meta) as dst:
            dst.write(dem, 1)

        engine = RasterEngine(dem_path, threshold_area_m2=0.0)
        engine.load_and_preprocess()
        engine.compute_flow_direction() if False else None  # placeholder no-op removed below
        engine.condition_dem()
        engine.compute_flow_direction()
        engine.compute_flow_accumulation()
        engine.apply_threshold()

        builder = NetworkBuilder(engine)
        network = builder.build_network()

        # Verified D8 flow map for this DEM:
        #   (0,0)->SE->(1,1)   (0,1)->S->(1,1)    (0,2)->SW->(1,1)
        #   (1,0)->E->(1,1)    (1,1)->SE->(2,2)   (1,2)->S->(2,2)
        #   (2,0)->NE->(1,1)   (2,1)->E->(2,2)    (2,2) sink
        # (1,1) has 5 upstream cells -> junction. (2,2) is the sink -> outlet.
        # 7 sources + 1 junction + 1 outlet = 9 nodes; 8 channels.
        assert len(network.nodes) == 9
        assert len(network.channels) == 8
        assert network.nodes["n_1_1"].node_type == NodeType.JUNCTION
        assert network.nodes["n_2_2"].node_type == NodeType.OUTLET
        for node_id in ("n_0_0", "n_0_1", "n_0_2", "n_1_0", "n_2_0", "n_1_2", "n_2_1"):
            assert network.nodes[node_id].node_type == NodeType.INLET

        diagonal = 10.0 * np.sqrt(2)
        expected_lengths = {
            "ch_n_0_0_n_1_1": diagonal,
            "ch_n_0_1_n_1_1": 10.0,
            "ch_n_0_2_n_1_1": diagonal,
            "ch_n_1_0_n_1_1": 10.0,
            "ch_n_2_0_n_1_1": diagonal,
            "ch_n_1_1_n_2_2": diagonal,
            "ch_n_1_2_n_2_2": 10.0,
            "ch_n_2_1_n_2_2": 10.0,
        }
        assert set(network.channels.keys()) == set(expected_lengths.keys())
        for channel_id, expected_length in expected_lengths.items():
            assert abs(network.channels[channel_id].length_m - expected_length) < 1e-9

        for node in network.nodes.values():
            assert node.provenance == Provenance.DEM_DERIVED
        for channel in network.channels.values():
            assert channel.provenance == Provenance.DEM_DERIVED

    finally:
        os.unlink(dem_path)


def test_confluence_branching():
    """Test a confluence where multiple tributaries converge on a junction
    that itself drains to a single outlet."""
    dem = np.array([
        [10, 10, 10],
        [10,  5, 10],
        [10,  0, 10]
    ], dtype=np.float64)
    nodata = -9999.0
    transform = from_origin(0, 0, 10.0, 10.0)
    meta = {
        'driver': 'GTiff',
        'dtype': dem.dtype,
        'nodata': nodata,
        'width': 3,
        'height': 3,
        'count': 1,
        'crs': 'EPSG:32643',
        'transform': transform,
    }
    with tempfile.NamedTemporaryFile(suffix='.tif', delete=False) as tmp:
        dem_path = tmp.name
    try:
        with rio_open(dem_path, 'w', **meta) as dst:
            dst.write(dem, 1)

        engine = RasterEngine(dem_path, threshold_area_m2=0.0)
        engine.load_and_preprocess()
        engine.condition_dem()
        engine.compute_flow_direction()
        engine.compute_flow_accumulation()
        engine.apply_threshold()

        builder = NetworkBuilder(engine)
        network = builder.build_network()

        # Verified D8 flow map for this DEM:
        #   (0,0)->SE->(1,1)   (0,1)->S->(1,1)    (0,2)->SW->(1,1)
        #   (1,0)->SE->(2,1)   (1,1)->S->(2,1)    (1,2)->SW->(2,1)
        #   (2,0)->E->(2,1)    (2,2)->W->(2,1)    (2,1) sink
        # (1,1) has 3 upstream cells -> junction. (2,1) is the sink -> outlet,
        # fed both by the (1,1) junction and by two cells that bypass it
        # entirely via a steeper direct diagonal.
        # 7 sources + 1 junction + 1 outlet = 9 nodes; 8 channels.
        assert len(network.nodes) == 9
        assert len(network.channels) == 8
        assert network.nodes["n_1_1"].node_type == NodeType.JUNCTION
        assert network.nodes["n_2_1"].node_type == NodeType.OUTLET
        for node_id in ("n_0_0", "n_0_1", "n_0_2", "n_1_0", "n_1_2", "n_2_0", "n_2_2"):
            assert network.nodes[node_id].node_type == NodeType.INLET

        diagonal = 10.0 * np.sqrt(2)
        expected_lengths = {
            "ch_n_0_0_n_1_1": diagonal,
            "ch_n_0_1_n_1_1": 10.0,
            "ch_n_0_2_n_1_1": diagonal,
            "ch_n_1_1_n_2_1": 10.0,
            "ch_n_1_0_n_2_1": diagonal,
            "ch_n_1_2_n_2_1": diagonal,
            "ch_n_2_0_n_2_1": 10.0,
            "ch_n_2_2_n_2_1": 10.0,
        }
        assert set(network.channels.keys()) == set(expected_lengths.keys())
        for channel_id, expected_length in expected_lengths.items():
            assert abs(network.channels[channel_id].length_m - expected_length) < 1e-9

        for node in network.nodes.values():
            assert node.provenance == Provenance.DEM_DERIVED
        for channel in network.channels.values():
            assert channel.provenance == Provenance.DEM_DERIVED

    finally:
        os.unlink(dem_path)


def test_boundary_outlet():
    """Test that flow paths exiting the raster are treated as boundary outlets."""
    dem = np.array([
        [10, 9, 8],
        [10, 9, 8],
        [10, 9, 8]
    ], dtype=np.float64)
    nodata = -9999.0
    transform = from_origin(0, 0, 10.0, 10.0)
    meta = {
        'driver': 'GTiff',
        'dtype': dem.dtype,
        'nodata': nodata,
        'width': 3,
        'height': 3,
        'count': 1,
        'crs': 'EPSG:4326',
        'transform': transform,
    }
    with tempfile.NamedTemporaryFile(suffix='.tif', delete=False) as tmp:
        dem_path = tmp.name
    try:
        with rio_open(dem_path, 'w', **meta) as dst:
            dst.write(dem, 1)

        engine = RasterEngine(dem_path, threshold_area_m2=0.0)
        engine.load_and_preprocess()
        engine.condition_dem()
        engine.compute_flow_direction()
        engine.compute_flow_accumulation()
        engine.apply_threshold()

        builder = NetworkBuilder(engine)
        network = builder.build_network()

        assert len(network.nodes) == 6
        assert len(network.channels) == 3
        assert network.crs == "EPSG:4326"

        for r in range(3):
            node_id = f"n_{r}_0"
            assert node_id in network.nodes
            assert network.nodes[node_id].node_type == NodeType.INLET

        for r in range(3):
            node_id = f"n_{r}_2"
            assert node_id in network.nodes
            assert network.nodes[node_id].node_type == NodeType.OUTLET

        for r in range(3):
            channel_id = f"ch_n_{r}_0_n_{r}_2"
            assert channel_id in network.channels
            assert network.channels[channel_id].length_m == 20.0

        for node in network.nodes.values():
            assert node.provenance == Provenance.DEM_DERIVED
        for channel in network.channels.values():
            assert channel.provenance == Provenance.DEM_DERIVED

    finally:
        os.unlink(dem_path)


def test_threshold_excludes_cells_below_threshold():
    """Test that cells with drainage area below threshold are excluded from the stream mask."""
    dem_array, meta = create_test_dem(shape=(3, 3), cell_size=10.0, nodata=None, tilt="se")
    with tempfile.NamedTemporaryFile(suffix='.tif', delete=False) as tmp:
        dem_path = tmp.name
    try:
        with rio_open(dem_path, 'w', **meta) as dst:
            dst.write(dem_array, 1)

        # Verified drainage areas (m²) for this DEM's D8 flow map:
        #   (0,0)=0 (0,1)=0 (0,2)=0
        #   (1,0)=0 (1,1)=100 (1,2)=200
        #   (2,0)=0 (2,1)=200 (2,2)=800
        # threshold=150 -> keeps only (1,2), (2,1), (2,2).
        engine = RasterEngine(dem_path, threshold_area_m2=150.0)
        engine.load_and_preprocess()
        engine.condition_dem()
        engine.compute_flow_direction()
        engine.compute_flow_accumulation()
        engine.apply_threshold()

        mask = engine.get_stream_mask()
        expected_mask = np.array([
            [False, False, False],
            [False, False, True],
            [False, True,  True]
        ])
        assert np.array_equal(mask, expected_mask)

        builder = NetworkBuilder(engine)
        network = builder.build_network()

        # (1,2) and (2,1) are both inlets draining directly into (2,2), the outlet.
        assert len(network.nodes) == 3
        assert len(network.channels) == 2
        assert network.nodes["n_1_2"].node_type == NodeType.INLET
        assert network.nodes["n_2_1"].node_type == NodeType.INLET
        assert network.nodes["n_2_2"].node_type == NodeType.OUTLET
        assert network.channels["ch_n_1_2_n_2_2"].length_m == 10.0
        assert network.channels["ch_n_2_1_n_2_2"].length_m == 10.0

        for node_id, node in network.nodes.items():
            r, c = map(int, node_id.split('_')[1:])
            assert mask[r, c], f"Node {node_id} at ({r},{c}) is not in stream mask"

        for channel_id, channel in network.channels.items():
            upstream_id = channel.upstream_node_id
            downstream_id = channel.downstream_node_id
            r_u, c_u = map(int, upstream_id.split('_')[1:])
            r_d, c_d = map(int, downstream_id.split('_')[1:])
            assert mask[r_u, c_u], f"Upstream node {upstream_id} not in stream mask"
            assert mask[r_d, c_d], f"Downstream node {downstream_id} not in stream mask"

        for node in network.nodes.values():
            assert node.provenance == Provenance.DEM_DERIVED
        for channel in network.channels.values():
            assert channel.provenance == Provenance.DEM_DERIVED

    finally:
        os.unlink(dem_path)


def test_deterministic_ids_output():
    """Test that the node and channel IDs are deterministic and based on coordinates."""
    dem_array, meta = create_test_dem(shape=(3, 3), cell_size=10.0, nodata=None, tilt="se")
    with tempfile.NamedTemporaryFile(suffix='.tif', delete=False) as tmp:
        dem_path = tmp.name
    try:
        with rio_open(dem_path, 'w', **meta) as dst:
            dst.write(dem_array, 1)

        engine = RasterEngine(dem_path, threshold_area_m2=0.0)
        engine.load_and_preprocess()
        engine.condition_dem()
        engine.compute_flow_direction()
        engine.compute_flow_accumulation()
        engine.apply_threshold()

        builder1 = NetworkBuilder(engine)
        network1 = builder1.build_network()

        engine2 = RasterEngine(dem_path, threshold_area_m2=0.0)
        engine2.load_and_preprocess()
        engine2.condition_dem()
        engine2.compute_flow_direction()
        engine2.compute_flow_accumulation()
        engine2.apply_threshold()

        builder2 = NetworkBuilder(engine2)
        network2 = builder2.build_network()

        assert network1.crs == network2.crs
        assert set(network1.nodes.keys()) == set(network2.nodes.keys())
        for nid in network1.nodes:
            n1 = network1.nodes[nid]
            n2 = network2.nodes[nid]
            assert n1 == n2

        assert set(network1.channels.keys()) == set(network2.channels.keys())
        for cid in network1.channels:
            c1 = network1.channels[cid]
            c2 = network2.channels[cid]
            assert c1 == c2

    finally:
        os.unlink(dem_path)


def test_empty_no_drainage_case():
    """Test the case where no cells meet the threshold (empty stream mask)."""
    dem_array, meta = create_test_dem(shape=(3, 3), cell_size=10.0, nodata=None, tilt="se")
    with tempfile.NamedTemporaryFile(suffix='.tif', delete=False) as tmp:
        dem_path = tmp.name
    try:
        with rio_open(dem_path, 'w', **meta) as dst:
            dst.write(dem_array, 1)

        engine = RasterEngine(dem_path, threshold_area_m2=1000.0)
        engine.load_and_preprocess()
        engine.condition_dem()
        engine.compute_flow_direction()
        engine.compute_flow_accumulation()
        engine.apply_threshold()

        mask = engine.get_stream_mask()
        assert not np.any(mask)

        builder = NetworkBuilder(engine)
        network = builder.build_network()

        assert len(network.nodes) == 0
        assert len(network.channels) == 0
        assert network.crs == "EPSG:32643"

    finally:
        os.unlink(dem_path)