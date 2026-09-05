"""Tests for the flood modeling API endpoint."""
from __future__ import annotations

import tempfile
import os
from typing import Tuple
import numpy as np
import pytest
from rasterio import open as rio_open
from rasterio.transform import from_origin

from fastapi.testclient import TestClient

from backend.main import app


client = TestClient(app)


def create_test_dem(
    shape: Tuple[int, int] = (5, 5),
    cell_size: float = 10.0,
    nodata: float | None = -9999.0,
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


def test_flood_model_no_rainfall():
    """Test flood model endpoint with zero rainfall (should succeed with zero inundation)."""
    response = client.post("/flood/model", json={
        "rainfall_mm": 0.0,
        "contributing_area_m2": 10000.0,
        "runoff_coefficient": 0.5,
        "timestep_hours": 1.0,
        "threshold_area_m2": 0.0
    })

    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "FeatureCollection"
    assert len(data["features"]) == 0
    assert data["summary"]["max_depth_m"] == 0.0
    assert data["summary"]["total_flooded_area_m2"] == 0.0
    assert data["summary"]["total_flood_volume_m3"] == 0.0


def test_flood_model_valid_request():
    """Test flood model endpoint with valid parameters."""
    response = client.post("/flood/model", json={
        "rainfall_mm": 25.0,
        "contributing_area_m2": 5000.0,
        "runoff_coefficient": 0.7,
        "timestep_hours": 1.0,
        "threshold_area_m2": 10.0
    })

    # Should succeed (200) or give detailed error about internal processing
    # Since we're using synthetic DEM, it should work
    assert response.status_code == 200

    data = response.json()
    assert data["type"] == "FeatureCollection"
    assert "features" in data
    assert "summary" in data

    # Check summary statistics
    summary = data["summary"]
    assert "max_depth_m" in summary
    assert "total_flooded_area_m2" in summary
    assert "total_flood_volume_m3" in summary
    assert "provenance" in summary
    assert summary["provenance"] == "MODELLED/DERIVED"


def test_flood_model_high_rainfall():
    """Test flood model endpoint with high rainfall."""
    response = client.post("/flood/model", json={
        "rainfall_mm": 100.0,
        "contributing_area_m2": 20000.0,
        "runoff_coefficient": 0.9,
        "timestep_hours": 2.0,
        "threshold_area_m2": 5.0
    })

    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "FeatureCollection"

    # Higher rainfall should generally produce more flood volume
    summary = data["summary"]
    assert summary["total_flood_volume_m3"] >= 0  # Non-negative


def test_flood_model_invalid_parameters():
    """Test flood model endpoint with invalid parameters."""
    # Test negative rainfall
    response = client.post("/flood/model", json={
        "rainfall_mm": -5.0,
        "contributing_area_m2": 10000.0,
        "runoff_coefficient": 0.5,
        "timestep_hours": 1.0
    })
    assert response.status_code == 422

    # Test runoff coefficient > 1
    response = client.post("/flood/model", json={
        "rainfall_mm": 25.0,
        "contributing_area_m2": 10000.0,
        "runoff_coefficient": 1.5,
        "timestep_hours": 1.0
    })
    assert response.status_code == 422

    # Test negative area
    response = client.post("/flood/model", json={
        "rainfall_mm": 25.0,
        "contributing_area_m2": -1000.0,
        "runoff_coefficient": 0.5,
        "timestep_hours": 1.0
    })
    assert response.status_code == 422


if __name__ == "__main__":
    pytest.main([__file__, "-v"])