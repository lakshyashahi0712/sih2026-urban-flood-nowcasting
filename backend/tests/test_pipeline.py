"""Tests for the end-to-end flood modeling pipeline (Phase 1.1)."""
from __future__ import annotations

import tempfile
import os
from typing import Tuple
import numpy as np
import pytest
from rasterio import open as rio_open
from rasterio.transform import from_origin

from app.domain.pipeline.flood_pipeline import run_flood_modeling_pipeline


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


def test_pipeline_no_rainfall_no_flood():
    """Test that zero rainfall produces no flood."""
    dem_array, meta = create_test_dem(shape=(3, 3), cell_size=10.0, nodata=None, tilt="se")
    with tempfile.NamedTemporaryFile(suffix='.tif', delete=False) as tmp:
        dem_path = tmp.name
    try:
        with rio_open(dem_path, 'w', **meta) as dst:
            dst.write(dem_array, 1)

        result = run_flood_modeling_pipeline(
            rainfall_mm=0.0,
            contributing_area_m2=10000.0,  # 1 hectare
            runoff_coefficient=0.5,
            dem_raster_path=dem_path,
            timestep_hours=1.0
        )

        # With zero rainfall, there should be no flood
        assert result.total_flood_volume_m3 == 0.0
        assert result.total_flooded_area_m2 == 0.0
        assert result.max_depth_m == 0.0
        assert not np.any(result.flooded_mask)

    finally:
        os.unlink(dem_path)


def test_pipeline_rainfall_produces_runoff():
    """Test that rainfall produces runoff that eventually appears as flood volume."""
    dem_array, meta = create_test_dem(shape=(3, 3), cell_size=10.0, nodata=None, tilt="se")
    with tempfile.NamedTemporaryFile(suffix='.tif', delete=False) as tmp:
        dem_path = tmp.name
    try:
        with rio_open(dem_path, 'w', **meta) as dst:
            dst.write(dem_array, 1)

        # Use parameters that will definitely produce some runoff
        result = run_flood_modeling_pipeline(
            rainfall_mm=50.0,  # 50mm rainfall
            contributing_area_m2=10000.0,  # 1 hectare
            runoff_coefficient=0.8,  # High runoff coefficient
            dem_raster_path=dem_path,
            timestep_hours=1.0,
            threshold_area_m2=0.0  # Low threshold to ensure network is built
        )

        # Should have some flood volume (conservation of mass)
        expected_runoff = 0.8 * 50.0 * 10000.0 / 1000.0  # V = C * i * A / 1000
        assert result.total_flood_volume_m3 > 0.0
        # Volume should be conserved (within numerical precision)
        assert abs(result.total_flood_volume_m3 - expected_runoff) < expected_runoff * 0.1  # Allow 10% tolerance

    finally:
        os.unlink(dem_path)


def test_pipeline_mass_conservation():
    """Test that mass is approximately conserved through the pipeline."""
    dem_array, meta = create_test_dem(shape=(5, 5), cell_size=10.0, nodata=-9999.0, tilt="se")
    with tempfile.NamedTemporaryFile(suffix='.tif', delete=False) as tmp:
        dem_path = tmp.name
    try:
        with rio_open(dem_path, 'w', **meta) as dst:
            dst.write(dem_array, 1)

        rainfall_mm = 30.0
        area_m2 = 2500.0  # 5x5 cells of 10m each = 2500 m²
        coeff = 0.7

        result = run_flood_modeling_pipeline(
            rainfall_mm=rainfall_mm,
            contributing_area_m2=area_m2,
            runoff_coefficient=coeff,
            dem_raster_path=dem_path,
            timestep_hours=1.0,
            threshold_area_m2=50.0  # Reasonable threshold
        )

        # Calculate expected runoff volume
        expected_runoff = coeff * rainfall_mm * area_m2 / 1000.0

        # Allow for some numerical error due to simplifications in the pipeline
        # but volume should be reasonably conserved
        assert result.total_flood_volume_m3 > 0.0
        assert abs(result.total_flood_volume_m3 - expected_runoff) < expected_runoff * 0.3  # 30% tolerance

    finally:
        os.unlink(dem_path)


def test_pipeline_high_runoff_coefficient():
    """Test that higher runoff coefficient produces more flood volume."""
    dem_array, meta = create_test_dem(shape=(4, 4), cell_size=10.0, nodata=-9999.0, tilt="se")
    with tempfile.NamedTemporaryFile(suffix='.tif', delete=False) as tmp:
        dem_path = tmp.name
    try:
        with rio_open(dem_path, 'w', **meta) as dst:
            dst.write(dem_array, 1)

        # Low runoff coefficient
        result_low = run_flood_modeling_pipeline(
            rainfall_mm=20.0,
            contributing_area_m2=10000.0,
            runoff_coefficient=0.3,
            dem_raster_path=dem_path,
            timestep_hours=1.0,
            threshold_area_m2=10.0
        )

        # High runoff coefficient
        result_high = run_flood_modeling_pipeline(
            rainfall_mm=20.0,
            contributing_area_m2=10000.0,
            runoff_coefficient=0.9,
            dem_raster_path=dem_path,
            timestep_hours=1.0,
            threshold_area_m2=10.0
        )

        # High coefficient should produce more flood volume
        assert result_high.total_flood_volume_m3 > result_low.total_flood_volume_m3

    finally:
        os.unlink(dem_path)


def test_pipeline_with_drainage_network():
    """Test pipeline with a DEM that produces a drainage network."""
    # Create a DEM with clear drainage path
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

        result = run_flood_modeling_pipeline(
            rainfall_mm=15.0,
            contributing_area_m2=900.0,  # 3x3 cells of 10m each
            runoff_coefficient=0.5,
            dem_raster_path=dem_path,
            timestep_hours=1.0,
            threshold_area_m2=0.0
        )

        # Should produce some flood result
        assert isinstance(result.total_flood_volume_m3, float)
        assert isinstance(result.max_depth_m, float)
        assert isinstance(result.total_flooded_area_m2, float)

    finally:
        os.unlink(dem_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])