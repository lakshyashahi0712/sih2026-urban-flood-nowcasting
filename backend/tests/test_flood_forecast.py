"""Tests for the 0–3 hour flood evolution forecast endpoints."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def test_flood_forecast_post_deterministic_evolution():
    """Verify POST /flood/forecast returns 4 distinct horizon states with exact hourly rainfall."""
    rainfall_inputs = [0.0, 15.0, 30.0, 50.0]
    payload = {
        "contributing_area_m2": 500000.0,
        "runoff_coefficient": 0.7,
        "threshold_area_m2": 15000.0,
        "rainfall_mm_list": rainfall_inputs,
        "use_cache": True
    }

    response = client.post("/flood/forecast", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert "horizons" in data
    assert len(data["horizons"]) == 4

    expected_labels = ["NOW", "+1h", "+2h", "+3h"]
    expected_lead_times = ["0h", "+1h", "+2h", "+3h"]

    for i, h in enumerate(data["horizons"]):
        assert h["horizon"] == expected_labels[i]
        assert h["lead_time"] == expected_lead_times[i]
        assert h["rainfall_mm"] == rainfall_inputs[i]
        # Timestep must strictly be 1.0 hour for all horizons
        assert h["timestep_hours"] == 1.0
        assert "geojson" in h
        assert h["geojson"]["type"] == "FeatureCollection"
        # Mass balance: conveyed + surface == total runoff
        assert h["conveyed_drainage_volume_m3"] + h["surface_flood_volume_m3"] == pytest.approx(h["total_runoff_volume_m3"], abs=1e-3)

    # Horizon 0 has 0.0 mm rainfall -> 0 inundation and empty features
    now_state = data["horizons"][0]
    assert now_state["max_depth_m"] == 0.0
    assert now_state["flooded_area_m2"] == 0.0
    assert now_state["flood_volume_m3"] == 0.0
    assert len(now_state["features"]) == 0
    assert len(now_state["geojson"]["features"]) == 0

    # Horizon 1 (15mm) -> safely conveyed inside drainage network
    h1_state = data["horizons"][1]
    assert h1_state["rainfall_mm"] == 15.0
    assert h1_state["conveyed_drainage_volume_m3"] == pytest.approx(5250.0)
    assert h1_state["surface_flood_volume_m3"] == 0.0
    assert h1_state["max_depth_m"] == 0.0
    assert len(h1_state["features"]) == 0

    # Horizon 3 (50mm) -> exceeds drainage capacity -> positive inundation
    h3_state = data["horizons"][3]
    assert h3_state["rainfall_mm"] == 50.0
    assert h3_state["max_depth_m"] > 0.0
    assert h3_state["flooded_area_m2"] > 0.0
    assert len(h3_state["features"]) > 0

    # Provenance assertions
    prov = data["provenance"]
    assert prov["rainfall"] == "Weather forecast (Open-Meteo hourly NWP)"
    assert prov["runoff"] == "rainfall–runoff"
    assert prov["drainage"] == "drainage capacity"
    assert prov["surface_routing"] == "surface routing"
    assert prov["model_status"] == "MODELLED / DERIVED"


def test_flood_forecast_does_not_sum_rainfall_across_horizons():
    """Verify that horizon +1h evaluates ONLY that hour's rainfall, not cumulative rainfall."""
    rainfall_inputs = [10.0, 50.0, 30.0, 40.0]
    payload = {
        "contributing_area_m2": 500000.0,
        "runoff_coefficient": 0.7,
        "threshold_area_m2": 15000.0,
        "rainfall_mm_list": rainfall_inputs,
    }

    forecast_res = client.post("/flood/forecast", json=payload)
    assert forecast_res.status_code == 200
    forecast_data = forecast_res.json()

    # Compare Horizon +1h (50.0 mm) against a standalone /flood/model run of 50.0 mm with timestep=1.0
    direct_res = client.post("/flood/model", json={
        "rainfall_mm": 50.0,
        "contributing_area_m2": 500000.0,
        "runoff_coefficient": 0.7,
        "timestep_hours": 1.0,
        "threshold_area_m2": 15000.0
    })
    assert direct_res.status_code == 200
    direct_data = direct_res.json()

    h1_state = forecast_data["horizons"][1]
    assert h1_state["rainfall_mm"] == 50.0
    assert h1_state["max_depth_m"] == pytest.approx(direct_data["summary"]["max_depth_m"], rel=1e-4)
    assert h1_state["flooded_area_m2"] == pytest.approx(direct_data["summary"]["total_flooded_area_m2"], rel=1e-4)
    assert h1_state["flood_volume_m3"] == pytest.approx(direct_data["summary"]["total_flood_volume_m3"], rel=1e-4)


def test_flood_forecast_validation_errors():
    """Verify validation on rainfall_mm_list (must be exactly 4 non-negative floats)."""
    # 3 items instead of 4
    res_short = client.post("/flood/forecast", json={
        "rainfall_mm_list": [10.0, 20.0, 30.0]
    })
    assert res_short.status_code == 422

    # 5 items instead of 4
    res_long = client.post("/flood/forecast", json={
        "rainfall_mm_list": [10.0, 20.0, 30.0, 40.0, 50.0]
    })
    assert res_long.status_code == 422

    # Negative rainfall
    res_neg = client.post("/flood/forecast", json={
        "rainfall_mm_list": [10.0, -5.0, 30.0, 40.0]
    })
    assert res_neg.status_code == 422


def test_flood_forecast_get_endpoint():
    """Verify GET /flood/forecast returns 4 valid horizon states using the rainfall adapter."""
    response = client.get("/flood/forecast?use_cache=true")
    # In test environment or live, it either succeeds (200) with 4 horizons or 503 if network unavailable
    if response.status_code == 200:
        data = response.json()
        assert len(data["horizons"]) == 4
        labels = [h["horizon"] for h in data["horizons"]]
        assert labels == ["NOW", "+1h", "+2h", "+3h"]
        for h in data["horizons"]:
            assert h["timestep_hours"] == 1.0
            assert "geojson" in h
            assert h["geojson"]["type"] == "FeatureCollection"
    else:
        assert response.status_code == 503
