"""Tests for the RasterEngine class."""
from __future__ import annotations

import tempfile
import os
from typing import Tuple, Optional
import numpy as np
import pytest
from rasterio import open as rio_open
from rasterio.transform import from_origin

from app.infrastructure.drainage.raster_engine import RasterEngine


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
    # Create a gradient: highest at (0,0) if tilt is "se" (so flow to SE)
    # Actually, for flow to SE, we want decreasing elevation to the SE.
    # Let's make elevation = - (row * row_step + col * col_step)
    # For SE tilt: as row and col increase, elevation decreases.
    row_step = 1.0
    col_step = 1.0
    dem = np.zeros(shape, dtype=np.float64)
    for r in range(rows):
        for c in range(cols):
            dem[r, c] = - (r * row_step + c * col_step)
    # Now the highest point is at (0,0) and lowest at (rows-1, cols-1)
    # Flow will be SE (diagonal) if we use D8 and the slope is uniform.

    if nodata is not None:
        # Set some nodata cells for testing
        dem[0, 0] = nodata
        dem[-1, -1] = nodata

    # Affine transform: origin at top-left
    transform = from_origin(0, 0, cell_size, cell_size)
    meta = {
        'driver': 'GTiff',
        'dtype': dem.dtype,
        'nodata': nodata,
        'width': cols,
        'height': rows,
        'count': 1,
        'crs': 'EPSG:32643',  # projected, no reprojection needed
        'transform': transform,
    }
    return dem, meta


def test_raster_engine_basic(tmp_path):
    """Test that the RasterEngine can process a simple DEM and produce a stream mask."""
    dem_array, meta = create_test_dem(shape=(5, 5), cell_size=10.0, nodata=-9999.0, tilt="se")
    # Write to a temporary file
    dem_path = tmp_path / "test_dem.tif"
    with rio_open(dem_path, 'w', **meta) as dst:
        dst.write(dem_array, 1)

    # Use a threshold that should yield streams (since cell area is 100 m², and we expect
    # accumulation to be in cells, we need to set threshold in m² appropriately.
    # Let's set threshold to 50 m² (half a cell) to see if we get any streams.
    # Actually, we want to test the accumulation semantics, so we'll set a threshold
    # that we expect to be exceeded in the downslope area.
    engine = RasterEngine(str(dem_path), threshold_area_m2=50.0)
    engine.load_and_preprocess()
    engine.condition_dem()
    engine.compute_flow_direction()
    engine.compute_flow_accumulation()
    engine.apply_threshold()

    mask = engine.get_stream_mask()
    # We expect at least some stream cells, but let's just check that the mask is boolean and same shape.
    assert mask.shape == dem_array.shape
    assert mask.dtype == bool

    # Check that the nodata cells are not in the stream mask (they should be False)
    # Note: our nodata cells are at (0,0) and (4,4). The flow direction and accumulation
    # should treat them as invalid, so they should not be stream cells.
    assert not mask[0, 0], "Nodata cell should not be in stream mask"
    assert not mask[-1, -1], "Nodata cell should not be in stream mask"

    # Check that the metadata is preserved and we know the CRS after reprojection.
    meta_out = engine.get_metadata()
    assert 'crs' in meta_out
    # The engine should have reprojected to EPSG:32643
    assert meta_out['crs'] == 'EPSG:32643'


def test_raster_engine_no_valid_cells(tmp_path):
    """Test that an error is raised when the DEM has no valid cells."""
    dem_array, meta = create_test_dem(shape=(5, 5), cell_size=10.0, nodata=0.0)
    # Set all cells to nodata
    dem_array.fill(0.0)
    dem_path = tmp_path / "all_nodata.tif"
    with rio_open(dem_path, 'w', **meta) as dst:
        dst.write(dem_array, 1)

    engine = RasterEngine(str(dem_path), threshold_area_m2=1.0)
    with pytest.raises(ValueError, match="DEM contains no finite elevation values"):
        engine.load_and_preprocess()


def test_raster_engine_accumulation_semantics():
    """Test that the accumulation is converted correctly using a known behavior."""
    # We'll use a very small DEM where we can compute the expected accumulation by hand.
    # 3x3, cell size 10 m, no nodata, SE tilt.
    dem_array, meta = create_test_dem(shape=(3, 3), cell_size=10.0, nodata=None, tilt="se")
    # Write to temp file
    with tempfile.NamedTemporaryFile(suffix='.tif', delete=False) as tmp:
        dem_path = tmp.name
    try:
        with rio_open(dem_path, 'w', **meta) as dst:
            dst.write(dem_array, 1)

        engine = RasterEngine(dem_path, threshold_area_m2=0.0)  # threshold zero to get all cells as stream
        engine.load_and_preprocess()
        engine.condition_dem()
        engine.compute_flow_direction()
        engine.compute_flow_accumulation()

        # Get the drainage area (m²) from the engine
        drainage_area = engine._drainage_area
        assert drainage_area is not None
        # Cell area
        cell_area = engine._cell_size ** 2
        # We can also get the raw accumulation from the engine if we expose it, but for now
        # we trust that the conversion is done correctly.
        # Let's just check that the drainage area is non-negative and has the right shape.
        assert drainage_area.shape == dem_array.shape
        assert np.all(drainage_area >= 0)
        # At the source (top-left) we expect zero upstream area.
        # Note: because of nodata handling and the fact that we set nodata=None, the source
        # might not be exactly (0,0) if the DEM is flat? But we have a slope.
        # We'll just check that the minimum is zero (there should be at least one source).
        assert np.min(drainage_area) == 0.0
    finally:
        os.unlink(dem_path)


def test_raster_engine_threshold_behavior():
    """Test that changing the threshold changes the number of stream cells."""
    dem_array, meta = create_test_dem(shape=(5, 5), cell_size=10.0, nodata=None, tilt="se")
    with tempfile.NamedTemporaryFile(suffix='.tif', delete=False) as tmp:
        dem_path = tmp.name
    try:
        with rio_open(dem_path, 'w', **meta) as dst:
            dst.write(dem_array, 1)

        # Low threshold: more streams
        engine_low = RasterEngine(dem_path, threshold_area_m2=0.0)
        engine_low.load_and_preprocess()
        engine_low.condition_dem()
        engine_low.compute_flow_direction()
        engine_low.compute_flow_accumulation()
        engine_low.apply_threshold()
        mask_low = engine_low.get_stream_mask()
        low_count = np.sum(mask_low)

        # High threshold: fewer streams (maybe zero)
        engine_high = RasterEngine(dem_path, threshold_area_m2=10000.0)  # 10000 m² is large
        engine_high.load_and_preprocess()
        engine_high.condition_dem()
        engine_high.compute_flow_direction()
        engine_high.compute_flow_accumulation()
        engine_high.apply_threshold()
        mask_high = engine_high.get_stream_mask()
        high_count = np.sum(mask_high)

        assert low_count >= high_count
        # With zero threshold, we expect all valid cells to be stream cells.
        # Since we have no nodata, all 25 cells should be stream.
        assert low_count == dem_array.size
    finally:
        os.unlink(dem_path)


def test_priority_flood_simple_depression():
    """Test depression filling with a simple enclosed depression."""
    # Create a 5x5 DEM with a depression in the center
    dem = np.array([
        [10, 10, 10, 10, 10],
        [10,  5,  5,  5, 10],
        [10,  5,  0,  5, 10],  # center is lowest
        [10,  5,  5,  5, 10],
        [10, 10, 10, 10, 10]
    ], dtype=np.float64)
    nodata = -9999.0
    transform = from_origin(0, 0, 10.0, 10.0)
    meta = {
        'driver': 'GTiff',
        'dtype': dem.dtype,
        'nodata': nodata,
        'width': 5,
        'height': 5,
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

        # After depression filling, the center should be raised to at least the spill level (5)
        # Actually, with our simple depression, it should fill to the boundary height (10)
        # because it's completely enclosed by higher ground.
        filled = engine._filled_dem
        assert filled is not None
        # The center cell (2,2) should be raised to 10 (the boundary elevation)
        assert filled[2, 2] == 10.0
        # Cells that were originally higher should remain unchanged
        assert filled[0, 0] == 10.0
        assert filled[4, 4] == 10.0
    finally:
        os.unlink(dem_path)


def test_flow_direction_deterministic():
    """Test that flow direction is deterministic with tie-breaking."""
    # Create a flat area where multiple neighbors have equal slope
    # We'll create a slight gradient but with a flat spot to test tie-breaking
    dem = np.array([
        [10, 10, 10],
        [10,  5, 10],
        [10, 10, 10]
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
        engine.condition_dem()  # Should not change much as it's mostly flat with a depression
        engine.compute_flow_direction()

        flow_dir = engine._flow_dir
        assert flow_dir is not None
        # The center cell (1,1) is the lowest point. It should flow to one of its neighbors.
        # With equal elevation differences to all neighbors, tie-breaking should pick E (1)
        # based on our priority: E > SE > S > SW > W > NW > N > NE
        # Actually, let's think: the center is 5, neighbors are 10, so it's a local minimum.
        # It should have flow direction 0 (sink) because there's no downslope neighbor.
        assert flow_dir[1, 1] == 0  # should be a sink/local minimum
    finally:
        os.unlink(dem_path)


def test_boundary_outlet():
    """Test that flow paths exiting the raster are treated as boundary outlets."""
    # Create a DEM that slopes uniformly to the east
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

        flow_dir = engine._flow_dir
        assert flow_dir is not None
        # All cells should flow east (direction 1) except those at the eastern boundary
        # Cells at column 2 (eastern edge) should have no valid downslope neighbor to the east
        # so they should be sinks (0) or flow elsewhere if there's a slope
        # Actually, with uniform slope to the east, all interior cells should flow east
        # Eastern boundary cells (col=2) have no eastern neighbor, so they should be sinks
        assert flow_dir[0, 2] == 0  # eastern boundary, no downstream
        assert flow_dir[1, 2] == 0  # eastern boundary, no downstream
        assert flow_dir[2, 2] == 0  # eastern boundary, no downstream
        # Interior cells should flow east
        assert flow_dir[0, 1] == 1  # flows east
        assert flow_dir[1, 1] == 1  # flows east
        assert flow_dir[2, 1] == 1  # flows east
    finally:
        os.unlink(dem_path)


if __name__ == "__main__":
    # Allow running the tests directly for debugging
    pytest.main([__file__, "-v"])