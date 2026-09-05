"""Tests for Street & Intersection Flood Intelligence."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.app.config import settings
from backend.app.domain.roads.models import RiskLevel, classify_road_risk
from backend.app.domain.roads.spatial_matcher import (
    OSMRoadNetworkCache,
    match_flood_to_streets,
)
from backend.app.domain.pipeline.flood_pipeline import run_flood_modeling_pipeline
import rasterio

client = TestClient(app)


def test_risk_classification_boundaries():
    """Verify operational risk tiers based on flood depth [m]."""
    assert classify_road_risk(0.0) == RiskLevel.NONE
    assert classify_road_risk(-0.05) == RiskLevel.NONE
    assert classify_road_risk(0.05) == RiskLevel.LOW
    assert classify_road_risk(0.14) == RiskLevel.LOW
    assert classify_road_risk(0.15) == RiskLevel.MEDIUM
    assert classify_road_risk(0.29) == RiskLevel.MEDIUM
    assert classify_road_risk(0.30) == RiskLevel.HIGH
    assert classify_road_risk(0.59) == RiskLevel.HIGH
    assert classify_road_risk(0.60) == RiskLevel.CRITICAL
    assert classify_road_risk(1.20) == RiskLevel.CRITICAL


def test_osm_cache_loads_real_mumbai_network():
    """Verify that real OSM roads and intersections are cached."""
    cache = OSMRoadNetworkCache.get_instance()
    assert len(cache.roads) > 500
    assert len(cache.intersections) > 500

    # Verify famous Mumbai arterial roads exist in dataset
    names = {r["name"] for r in cache.roads}
    assert any("Lal Bahadur Shastri Marg" in n for n in names)
    assert any("Santa Cruz" in n or "Chembur" in n for n in names)


def test_empty_no_flood_case():
    """Verify zero rainfall or non-surcharged runoff produces 0 affected roads/intersections."""
    # 0 mm rainfall
    f_res_zero = run_flood_modeling_pipeline(
        rainfall_mm=0.0,
        contributing_area_m2=500000.0,
        runoff_coefficient=0.7,
        dem_raster_path=settings.dem_path,
        timestep_hours=1.0,
        threshold_area_m2=15000.0,
    )
    with rasterio.open(settings.dem_path) as src:
        intel_zero = match_flood_to_streets(
            flood_depth_m=f_res_zero.flood_depth_m,
            flooded_mask=f_res_zero.flooded_mask,
            cell_w=src.transform[0],
            cell_h=abs(src.transform[4]),
            origin_x=src.transform[2],
            origin_y=src.transform[5],
            horizon="NOW",
            lead_time="0h",
            rainfall_mm=0.0,
        )

    assert intel_zero.summary.total_affected_roads == 0
    assert intel_zero.summary.total_affected_intersections == 0
    assert intel_zero.summary.max_street_depth_m == 0.0
    assert intel_zero.summary.total_flooded_road_length_m == 0.0
    assert len(intel_zero.affected_roads) == 0
    assert len(intel_zero.affected_intersections) == 0
    assert len(intel_zero.roads_geojson["features"]) == 0
    assert len(intel_zero.intersections_geojson["features"]) == 0

    # Non-surcharged 20 mm rainfall
    f_res_20 = run_flood_modeling_pipeline(
        rainfall_mm=20.0,
        contributing_area_m2=500000.0,
        runoff_coefficient=0.7,
        dem_raster_path=settings.dem_path,
        timestep_hours=1.0,
        threshold_area_m2=15000.0,
    )
    with rasterio.open(settings.dem_path) as src:
        intel_20 = match_flood_to_streets(
            flood_depth_m=f_res_20.flood_depth_m,
            flooded_mask=f_res_20.flooded_mask,
            cell_w=src.transform[0],
            cell_h=abs(src.transform[4]),
            origin_x=src.transform[2],
            origin_y=src.transform[5],
            horizon="+1h",
            lead_time="+1h",
            rainfall_mm=20.0,
        )

    assert intel_20.summary.total_affected_roads == 0
    assert intel_20.summary.total_affected_intersections == 0


def test_spatial_matching_surcharged_flood():
    """Verify intense rainfall (50 mm/h and 70 mm/h) spatially associates with real roads."""
    with rasterio.open(settings.dem_path) as src:
        w, h, ox, oy = src.transform[0], abs(src.transform[4]), src.transform[2], src.transform[5]

    # 50 mm/h
    f_res_50 = run_flood_modeling_pipeline(
        rainfall_mm=50.0,
        contributing_area_m2=500000.0,
        runoff_coefficient=0.7,
        dem_raster_path=settings.dem_path,
        timestep_hours=1.0,
        threshold_area_m2=15000.0,
    )
    intel_50 = match_flood_to_streets(
        flood_depth_m=f_res_50.flood_depth_m,
        flooded_mask=f_res_50.flooded_mask,
        cell_w=w, cell_h=h, origin_x=ox, origin_y=oy,
        horizon="+1h", lead_time="+1h", rainfall_mm=50.0,
    )

    assert intel_50.summary.total_affected_roads > 0
    assert intel_50.summary.total_affected_intersections > 0
    assert intel_50.summary.max_street_depth_m > 0.15
    assert intel_50.summary.total_flooded_road_length_m > 100.0

    # Verify road geometries are valid WGS84 coordinates in Mumbai pilot bbox
    for feat in intel_50.roads_geojson["features"]:
        geom = feat["geometry"]
        assert geom["type"] == "LineString"
        for lon, lat in geom["coordinates"]:
            assert 72.84 <= lon <= 72.91
            assert 19.04 <= lat <= 19.11
        assert feat["properties"]["max_depth_m"] > 0
        assert feat["properties"]["risk_level"] in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]

    # Verify intersection geometries are valid WGS84 Points in Mumbai pilot bbox
    for feat in intel_50.intersections_geojson["features"]:
        geom = feat["geometry"]
        assert geom["type"] == "Point"
        lon, lat = geom["coordinates"]
        assert 72.84 <= lon <= 72.91
        assert 19.04 <= lat <= 19.11

    # 70 mm/h: depth and risk should increase monotonically
    f_res_70 = run_flood_modeling_pipeline(
        rainfall_mm=70.0,
        contributing_area_m2=500000.0,
        runoff_coefficient=0.7,
        dem_raster_path=settings.dem_path,
        timestep_hours=1.0,
        threshold_area_m2=15000.0,
    )
    intel_70 = match_flood_to_streets(
        flood_depth_m=f_res_70.flood_depth_m,
        flooded_mask=f_res_70.flooded_mask,
        cell_w=w, cell_h=h, origin_x=ox, origin_y=oy,
        horizon="+2h", lead_time="+2h", rainfall_mm=70.0,
    )

    assert intel_70.summary.max_street_depth_m > intel_50.summary.max_street_depth_m
    assert intel_70.summary.risk_counts.HIGH > 0


def test_api_get_streets_dry_and_scenario():
    """Verify GET /flood/streets with scenario rainfall and dry rainfall."""
    # Scenario: 0 mm/h
    resp_zero = client.get("/flood/streets?rainfall_mm=0.0")
    assert resp_zero.status_code == 200
    data_zero = resp_zero.json()
    assert data_zero["summary"]["total_affected_roads"] == 0
    assert data_zero["summary"]["total_affected_intersections"] == 0
    assert data_zero["provenance"]["roads"] == "OpenStreetMap contributors (ODbL)"
    assert "not real-time municipal observations" in data_zero["provenance"]["disclaimer"].lower()

    # Scenario: 40 mm/h
    resp_40 = client.get("/flood/streets?rainfall_mm=40.0&horizon=+1h")
    assert resp_40.status_code == 200
    data_40 = resp_40.json()
    assert data_40["horizon"] == "+1h"
    assert data_40["rainfall_mm"] == 40.0
    assert data_40["summary"]["total_affected_roads"] > 0
    assert len(data_40["affected_roads"]) > 0
    assert len(data_40["roads_geojson"]["features"]) > 0


def test_api_post_streets():
    """Verify POST /flood/streets custom scenario calculation."""
    resp = client.post("/flood/streets", json={
        "rainfall_mm": 50.0,
        "horizon": "+2h",
        "contributing_area_m2": 500000.0,
        "runoff_coefficient": 0.7,
        "threshold_area_m2": 15000.0,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["horizon"] == "+2h"
    assert data["rainfall_mm"] == 50.0
    assert data["summary"]["total_affected_roads"] > 0
    assert data["summary"]["max_street_depth_m"] > 0.0


def test_api_get_streets_forecast():
    """Verify GET /flood/streets/forecast returns 4 chronological horizons."""
    resp = client.get("/flood/streets/forecast?use_cache=true")
    assert resp.status_code == 200
    data = resp.json()
    assert "horizons" in data
    assert len(data["horizons"]) == 4
    for h in data["horizons"]:
        assert h["horizon"] in ["NOW", "+1h", "+2h", "+3h"]
        assert "summary" in h
        assert "roads_geojson" in h
        assert "intersections_geojson" in h
        assert "provenance" in h
