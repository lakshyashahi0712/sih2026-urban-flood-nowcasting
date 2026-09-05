"""Tests for Phase 1.6: Real Copernicus DEM GLO-30 flood modeling."""
from __future__ import annotations

import os
import pytest
import rasterio
from fastapi.testclient import TestClient

from backend.main import app
from backend.app.config import settings
from backend.app.domain.pipeline.flood_pipeline import (
    run_flood_modeling_pipeline,
    clear_topology_cache,
)

client = TestClient(app)


def test_real_dem_file_properties():
    """Verify that the Copernicus GLO-30 DEM file exists and has correct geospatial metadata."""
    assert os.path.exists(settings.dem_path), f"DEM file missing at {settings.dem_path}"

    with rasterio.open(settings.dem_path) as src:
        assert src.crs.to_string() == "EPSG:32643"
        # 30-meter cell size
        assert abs(src.transform[0]) == 30.0
        assert abs(src.transform[4]) == 30.0
        # Check non-empty dimensions
        assert src.width > 100
        assert src.height > 100
        # Check elevation range (Mumbai coastal plain: sea level to ~100m hills)
        data = src.read(1)
        valid = data[data != src.nodata] if src.nodata is not None else data
        assert valid.min() >= -10.0
        assert valid.max() <= 200.0


def test_real_dem_pipeline_zero_rain():
    """Verify that zero rainfall produces zero flood depth and volume."""
    res = run_flood_modeling_pipeline(
        rainfall_mm=0.0,
        contributing_area_m2=500000.0,
        runoff_coefficient=0.7,
        dem_raster_path=settings.dem_path,
        timestep_hours=1.0,
        threshold_area_m2=15000.0,
    )
    assert res.max_depth_m == 0.0
    assert res.total_flooded_area_m2 == 0.0
    assert res.total_flood_volume_m3 == 0.0


def test_real_dem_pipeline_heavy_rain_produces_inundation():
    """Verify that intense rainfall (50mm/h) produces spatial inundation on real topography."""
    res = run_flood_modeling_pipeline(
        rainfall_mm=50.0,
        contributing_area_m2=500000.0,
        runoff_coefficient=0.7,
        dem_raster_path=settings.dem_path,
        timestep_hours=1.0,
        threshold_area_m2=15000.0,
    )
    assert res.max_depth_m > 0.0
    assert res.total_flooded_area_m2 > 0.0
    assert res.total_flood_volume_m3 > 0.0
    # On 30m grid, flooded area must be a multiple of cell area (900 m²)
    assert res.total_flooded_area_m2 % 900.0 == pytest.approx(0.0)


def test_real_dem_model_endpoint_geojson_bounds():
    """Verify POST /flood/model returns valid GeoJSON within the Mumbai pilot bounding box."""
    response = client.post("/flood/model", json={
        "rainfall_mm": 50.0,
        "contributing_area_m2": 500000.0,
        "runoff_coefficient": 0.7,
        "timestep_hours": 1.0,
        "threshold_area_m2": 15000.0,
    })
    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "FeatureCollection"
    assert len(data["features"]) > 0

    # Verify all coordinates are within the Mumbai pilot zone bounds
    for feat in data["features"]:
        geom = feat["geometry"]
        assert geom["type"] == "Polygon"
        coords = geom["coordinates"][0]
        for lon, lat in coords:
            assert 72.84 <= lon <= 72.91, f"Longitude {lon} out of Mumbai pilot bounds"
            assert 19.04 <= lat <= 19.11, f"Latitude {lat} out of Mumbai pilot bounds"
        assert feat["properties"]["depth"] > 0.0


def test_real_dem_forecast_provenance_and_horizons():
    """Verify POST /flood/forecast returns Copernicus DEM provenance and 4 valid horizons."""
    rainfall_inputs = [0.0, 20.0, 50.0, 70.0]
    response = client.post("/flood/forecast", json={
        "contributing_area_m2": 500000.0,
        "runoff_coefficient": 0.7,
        "threshold_area_m2": 15000.0,
        "rainfall_mm_list": rainfall_inputs,
        "use_cache": True,
    })
    assert response.status_code == 200
    data = response.json()

    assert data["provenance"]["elevation"] == "Copernicus GLO-30 DSM (30m)"
    assert len(data["horizons"]) == 4

    # Horizon 0 (0.0mm) has zero inundation
    assert data["horizons"][0]["max_depth_m"] == 0.0
    assert len(data["horizons"][0]["features"]) == 0

    # Horizon 2 (50.0mm) has multi-cell inundation
    h2 = data["horizons"][2]
    assert h2["rainfall_mm"] == 50.0
    assert h2["timestep_hours"] == 1.0
    assert h2["max_depth_m"] > 0.0
    assert h2["flooded_area_m2"] > 0.0
    assert len(h2["features"]) > 1  # Spatially meaningful multi-cell flood


def test_real_dem_non_surcharged_drainage_conveys_safely():
    """Verify non-surcharged rainfall (20mm/h) is fully conveyed without artificial single-cell ponding."""
    res = run_flood_modeling_pipeline(
        rainfall_mm=20.0,
        contributing_area_m2=500000.0,
        runoff_coefficient=0.7,
        dem_raster_path=settings.dem_path,
        timestep_hours=1.0,
        threshold_area_m2=15000.0,
    )
    # Total runoff: 0.7 * 20 * 500000 / 1000 = 7000 m³
    expected_runoff = 7000.0
    assert res.total_runoff_volume_m3 == pytest.approx(expected_runoff)
    # Channel network capacity is ~10512 m³, so all 7000 m³ is conveyed
    assert res.conveyed_drainage_volume_m3 == pytest.approx(expected_runoff)
    assert res.surface_flood_volume_m3 == 0.0
    assert res.total_flood_volume_m3 == 0.0
    assert res.max_depth_m == 0.0
    assert res.total_flooded_area_m2 == 0.0
    assert not res.flooded_mask.any()

    # Verify mass conservation: conveyed + surface flood == total runoff
    assert res.conveyed_drainage_volume_m3 + res.surface_flood_volume_m3 == pytest.approx(res.total_runoff_volume_m3)


def test_real_dem_monotonic_rainfall_response():
    """Verify strictly monotonic flood response across [0.6, 20, 40, 50, 70] mm/h with zero mass error."""
    rainfall_levels = [0.6, 20.0, 40.0, 50.0, 70.0]
    results = []

    for rain in rainfall_levels:
        res = run_flood_modeling_pipeline(
            rainfall_mm=rain,
            contributing_area_m2=500000.0,
            runoff_coefficient=0.7,
            dem_raster_path=settings.dem_path,
            timestep_hours=1.0,
            threshold_area_m2=15000.0,
        )
        results.append(res)
        # Verify strict mass balance at each level
        mass_error = abs(res.total_runoff_volume_m3 - (res.conveyed_drainage_volume_m3 + res.surface_flood_volume_m3))
        assert mass_error < 1e-4, f"Mass balance violation at {rain} mm/h: {mass_error}"

    # Verify non-surcharged conditions (0.6 and 20 mm/h)
    assert results[0].max_depth_m == 0.0
    assert results[1].max_depth_m == 0.0
    assert results[0].surface_flood_volume_m3 == 0.0
    assert results[1].surface_flood_volume_m3 == 0.0

    # Verify surcharge conditions (40, 50, 70 mm/h)
    assert results[2].max_depth_m > 0.0
    assert results[3].max_depth_m > results[2].max_depth_m
    assert results[4].max_depth_m > results[3].max_depth_m

    # Verify monotonic surface flood volume: 0 == 0 < 3487 < 6987 < 13987
    volumes = [r.surface_flood_volume_m3 for r in results]
    for i in range(len(volumes) - 1):
        assert volumes[i] <= volumes[i + 1], f"Non-monotonic volume: {volumes[i]} > {volumes[i+1]}"

    # Verify monotonic max depth: 0 == 0 < 0.144 < 0.288 < 0.576
    depths = [r.max_depth_m for r in results]
    for i in range(len(depths) - 1):
        assert depths[i] <= depths[i + 1], f"Non-monotonic depth: {depths[i]} > {depths[i+1]}"


def test_real_dem_mass_balance_in_api():
    """Verify POST /flood/model and POST /flood/forecast expose mass balance fields."""
    # Test /flood/model
    resp = client.post("/flood/model", json={
        "rainfall_mm": 50.0,
        "contributing_area_m2": 500000.0,
        "runoff_coefficient": 0.7,
        "timestep_hours": 1.0,
        "threshold_area_m2": 15000.0,
    })
    assert resp.status_code == 200
    summary = resp.json()["summary"]
    assert "total_runoff_volume_m3" in summary
    assert "conveyed_drainage_volume_m3" in summary
    assert "surface_flood_volume_m3" in summary
    assert summary["total_runoff_volume_m3"] == pytest.approx(17500.0)
    assert summary["conveyed_drainage_volume_m3"] + summary["surface_flood_volume_m3"] == pytest.approx(17500.0)

    # Test /flood/forecast
    resp_fc = client.post("/flood/forecast", json={
        "contributing_area_m2": 500000.0,
        "runoff_coefficient": 0.7,
        "threshold_area_m2": 15000.0,
        "rainfall_mm_list": [0.6, 20.0, 40.0, 50.0],
        "use_cache": True,
    })
    assert resp_fc.status_code == 200
    horizons = resp_fc.json()["horizons"]
    for h in horizons:
        assert "total_runoff_volume_m3" in h
        assert "conveyed_drainage_volume_m3" in h
        assert "surface_flood_volume_m3" in h
        assert h["conveyed_drainage_volume_m3"] + h["surface_flood_volume_m3"] == pytest.approx(h["total_runoff_volume_m3"], abs=1e-3)
