"""Tests for Historical Replay API endpoint (Phase 2.6)."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

try:
    from backend.main import app
    from backend.routers.flood import _HISTORICAL_2017_CACHE
except ImportError:
    from main import app
    from routers.flood import _HISTORICAL_2017_CACHE


client = TestClient(app)


def test_get_historical_2017_replay_structure():
    """Test that GET /flood/historical/2017 returns complete 24-step replay with valid structure."""
    response = client.get("/flood/historical/2017")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    data = response.json()

    # 1. Event Metadata
    assert data["event_id"] == "mumbai-2017-08-29-deluge"
    assert data["event_date"] == "2017-08-29"
    assert data["mode_label"] == "RETROSPECTIVE EVENT REPLAY"
    assert data["event_subtitle"] == "29 AUG 2017 — MUMBAI DELUGE"
    assert data["timestep_count"] == 24
    assert len(data["timesteps"]) == 24

    # 2. Strict Peak Values & Timestep Occurrences
    assert data["peak_modeled_depth_m"] == 0.741
    assert data["peak_surcharge_volume_m3"] == 4645.0
    assert data["peak_flood_volume_m3"] == 6488.8
    assert data["peak_flooded_area_m2"] == 81000.0

    summary = data["event_summary"]
    assert summary["peak_depth"]["value"] == 0.741
    assert summary["peak_depth"]["timestep_index"] == 5  # Step 6 (13:30 IST)
    assert summary["peak_surcharge"]["value"] == 4645.0
    assert summary["peak_surcharge"]["timestep_index"] == 5
    assert summary["peak_surface_volume"]["value"] == 6488.8
    assert summary["peak_surface_volume"]["timestep_index"] == 5
    assert summary["peak_flooded_area"]["value"] == 81000.0
    assert summary["peak_flooded_area"]["timestep_index"] == 1  # Step 2 (09:30 IST) - distinct timestep!

    # 3. Provenance Integrity
    provenance = data["provenance"]
    assert "SECONDARY-REPORT" in provenance["rainfall"]
    assert "DERIVED" in provenance["tide"]
    assert provenance["flood"] == "RETROSPECTIVE SIMULATION"
    assert "OBSERVED" in provenance["benchmarks"]
    assert "observed" not in provenance["rainfall"].lower()

    # 4. Observed Benchmarks GeoJSON
    benchmarks_fc = data["benchmarks_geojson"]
    assert benchmarks_fc["type"] == "FeatureCollection"
    assert len(benchmarks_fc["features"]) == 4
    for feat in benchmarks_fc["features"]:
        assert feat["type"] == "Feature"
        assert feat["geometry"]["type"] == "Point"
        assert len(feat["geometry"]["coordinates"]) == 2
        props = feat["properties"]
        assert props["provenance"] == "OBSERVED"
        assert "observed_min_depth_m" in props
        assert "descriptor" in props
        assert "observed_depth_range" in props
        assert "minimum" in props
        assert "maximum" in props
        assert "is_model_input" in props
        assert props["is_model_input"] is False

    # 5. Truthful Validation Comparison Records & Contract
    comps = data["validation_comparisons"]
    assert len(comps) == 4
    comp_map = {c["location_id"]: c for c in comps}

    # Kurla West (LBS Marg / Bail Bazar): 0.60–1.10 m -> modeled 0.367 m (Outside Range)
    lbs = comp_map["KURLA_LBS_MARG"]
    assert lbs["location_name"] == "Kurla West (LBS Marg / Bail Bazar)"
    assert lbs["observed_depth_range"] == "0.60–1.10 m"
    assert lbs["minimum"] == 0.60
    assert lbs["maximum"] == 1.10
    assert lbs["observed_provenance"] == "OBSERVED"
    assert lbs["is_model_input"] is False
    assert lbs["matched_depth_m"] == 0.367
    assert lbs["within_observed_range"] is False
    assert lbs["spatial_status"] == "MATCHED"

    # Kalina (CST Road Junction): 0.80–1.40 m -> modeled 0.000 m (Dry Cell)
    kalina = comp_map["KALINA_CST_ROAD"]
    assert kalina["location_name"] == "Kalina (CST Road Junction)"
    assert kalina["observed_depth_range"] == "0.80–1.40 m"
    assert kalina["minimum"] == 0.80
    assert kalina["maximum"] == 1.40
    assert kalina["observed_provenance"] == "OBSERVED"
    assert kalina["is_model_input"] is False
    assert kalina["matched_depth_m"] == 0.000
    assert kalina["within_observed_range"] is False
    assert kalina["spatial_status"] == "MATCHED"

    # Premier Road (Kurla): 0.50–0.90 m -> modeled 0.000 m (Dry Cell)
    premier = comp_map["KURLA_PREMIER_ROAD"]
    assert premier["location_name"] == "Premier Road (Kurla)"
    assert premier["observed_depth_range"] == "0.50–0.90 m"
    assert premier["minimum"] == 0.50
    assert premier["maximum"] == 0.90
    assert premier["observed_provenance"] == "OBSERVED"
    assert premier["is_model_input"] is False
    assert premier["matched_depth_m"] == 0.000
    assert premier["within_observed_range"] is False
    assert premier["spatial_status"] == "MATCHED"

    # Milan Subway (Santacruz): >2.20 m -> outside pilot extent (null matched depth)
    milan = comp_map["MILAN_SUBWAY"]
    assert milan["location_name"] == "Milan Subway (Santacruz)"
    assert milan["observed_depth_range"] == ">2.20 m"
    assert milan["minimum"] == 2.20
    assert milan["maximum"] is None
    assert milan["observed_provenance"] == "OBSERVED"
    assert milan["is_model_input"] is False
    assert milan["matched_depth_m"] is None
    assert milan["within_observed_range"] is False
    assert milan["spatial_status"] == "OUTSIDE_PILOT_EXTENT"

    # 6. Timestep sequence & synchronous GeoJSON
    timesteps = data["timesteps"]
    for idx, ts in enumerate(timesteps):
        assert ts["timestep_index"] == idx
        assert "IST" in ts["time_display"]
        assert ts["rainfall_mm"] >= 0.0
        assert ts["cumulative_rainfall_mm"] >= 0.0
        assert ts["geojson"]["type"] == "FeatureCollection"

    # Peak timestep is Step 5 (13:30 IST) with 74.0 mm/hr
    peak_ts = timesteps[5]
    assert peak_ts["rainfall_mm"] == 74.0
    assert peak_ts["peak_flood_depth_m"] == 0.741
    assert len(peak_ts["features"]) > 0


def test_get_historical_2017_replay_cache():
    """Verify that cached replay response is returned immediately on subsequent calls."""
    response1 = client.get("/flood/historical/2017?use_cache=true")
    assert response1.status_code == 200

    response2 = client.get("/flood/historical/2017?use_cache=true")
    assert response2.status_code == 200
    assert response1.json() == response2.json()


def test_historical_replay_road_and_intersection_layers():
    """Verify that historical replay includes road and intersection flood layers per timestep."""
    response = client.get("/flood/historical/2017")
    assert response.status_code == 200
    data = response.json()
    timesteps = data["timesteps"]

    # 1. Every timestep has roads_geojson, intersections_geojson, and street_risk
    for ts in timesteps:
        assert "roads_geojson" in ts
        assert "intersections_geojson" in ts
        assert "street_risk" in ts
        assert ts["roads_geojson"]["type"] == "FeatureCollection"
        assert ts["intersections_geojson"]["type"] == "FeatureCollection"
        assert ts["street_risk"] is not None

    # 2. Early step (Step 0: 08:30 IST, 2 mm/h) has only LOW risk ponding
    step_0 = timesteps[0]
    risk_summary_0 = step_0["street_risk"]["summary"]
    assert risk_summary_0["total_affected_roads"] > 0
    assert risk_summary_0["risk_counts"]["CRITICAL"] == 0
    assert risk_summary_0["risk_counts"]["HIGH"] == 0

    # 3. Peak cloudburst step (Step 5: 13:30 IST, 74 mm/h) has escalated road risk
    peak_step = timesteps[5]
    peak_summary = peak_step["street_risk"]["summary"]
    assert peak_summary["total_affected_roads"] > risk_summary_0["total_affected_roads"]
    assert peak_summary["total_affected_intersections"] > 0
    assert peak_summary["risk_counts"]["CRITICAL"] > 0
    assert peak_summary["risk_counts"]["HIGH"] > 0
    assert peak_summary["max_street_depth_m"] >= 0.50

    # 4. Check road GeoJSON feature properties
    peak_roads_fc = peak_step["roads_geojson"]
    assert len(peak_roads_fc["features"]) > 0
    first_road = peak_roads_fc["features"][0]
    assert first_road["geometry"]["type"] in ["LineString", "MultiLineString"]
    assert "risk_level" in first_road["properties"]
    assert first_road["properties"]["risk_level"] in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]

    # 5. Check intersection GeoJSON feature properties
    peak_ints_fc = peak_step["intersections_geojson"]
    assert len(peak_ints_fc["features"]) > 0
    first_int = peak_ints_fc["features"][0]
    assert first_int["geometry"]["type"] == "Point"
    assert "risk_level" in first_int["properties"]

    # 6. Provenance explicitly separates modelled road impact from observed benchmarks
    prov = peak_step["street_risk"]["provenance"]
    assert "Modelled Retrospective Impact" in prov.get("classification", "")
    assert "Not historical road observations" in prov.get("disclaimer", "")

    # 7. Observed benchmarks remain untouched and separate
    assert len(data["benchmarks_geojson"]["features"]) == 4
    for b in data["benchmarks_geojson"]["features"]:
        assert b["properties"]["provenance"] == "OBSERVED"

