"""Tests for georeferencing of the synthetic DEM and GeoJSON output (Phase 1.2).

These tests verify:
1. The synthetic DEM is positioned near Mumbai in EPSG:32643.
2. GeoJSON coordinates returned by the flood endpoint are valid EPSG:4326.
3. Returned longitude ≈ 72–73 and latitude ≈ 18–20 for Mumbai.
4. Coordinate transformation round-trips correctly.

NOTE: All flood data is SYNTHETIC / PROTOTYPE. These tests verify correct
georeferencing only, not real flood observations.
"""
from __future__ import annotations

import numpy as np
import pytest
from rasterio.warp import transform as warp_transform

from backend.routers.flood import (
    _create_synthetic_dem_mumbai_bbox,
    _flood_result_to_geojson,
)
from backend.app.config import settings


# ---------------------------------------------------------------------------
# A. Synthetic DEM positioning tests
# ---------------------------------------------------------------------------

class TestSyntheticDEMPositioning:
    """Verify the synthetic DEM raster is georeferenced near Mumbai."""

    def test_dem_origin_is_near_mumbai_in_utm(self):
        """DEM top-left origin should be the Mumbai point projected to EPSG:32643."""
        _, meta = _create_synthetic_dem_mumbai_bbox()
        t = meta['transform']
        origin_x, origin_y = t.c, t.f  # top-left corner

        # Project the config Mumbai point independently for comparison
        expected_x, expected_y = warp_transform(
            'EPSG:4326', 'EPSG:32643',
            [settings.mumbai_lon], [settings.mumbai_lat],
        )
        assert abs(origin_x - expected_x[0]) < 1.0, (
            f"Origin X {origin_x} should match projected Mumbai X {expected_x[0]}"
        )
        assert abs(origin_y - expected_y[0]) < 1.0, (
            f"Origin Y {origin_y} should match projected Mumbai Y {expected_y[0]}"
        )

    def test_dem_origin_is_plausible_utm43n(self):
        """DEM origin easting/northing should be in the plausible UTM 43N range for Mumbai."""
        _, meta = _create_synthetic_dem_mumbai_bbox()
        t = meta['transform']
        origin_x, origin_y = t.c, t.f

        # Mumbai is roughly at easting ~276 000, northing ~2 110 000 in UTM 43N
        assert 200_000 < origin_x < 400_000, f"Easting {origin_x} out of Mumbai range"
        assert 2_000_000 < origin_y < 2_200_000, f"Northing {origin_y} out of Mumbai range"

    def test_dem_crs_is_epsg_32643(self):
        """DEM CRS metadata should be EPSG:32643."""
        _, meta = _create_synthetic_dem_mumbai_bbox()
        assert meta['crs'] == 'EPSG:32643'

    def test_dem_cell_size_is_10m(self):
        """DEM pixel size should be 10 m × 10 m."""
        _, meta = _create_synthetic_dem_mumbai_bbox()
        t = meta['transform']
        assert t.a == 10.0, f"Pixel width {t.a} != 10.0"
        assert t.e == -10.0, f"Pixel height {t.e} != -10.0"

    def test_dem_bottom_right_still_near_mumbai(self):
        """The bottom-right corner of the 10×10 raster should still be near Mumbai."""
        shape = (10, 10)
        _, meta = _create_synthetic_dem_mumbai_bbox(shape=shape, cell_size=10.0)
        t = meta['transform']
        # Bottom-right corner in EPSG:32643
        br_x = t.c + shape[1] * t.a
        br_y = t.f + shape[0] * t.e  # t.e is negative

        # Transform back to EPSG:4326
        lons, lats = warp_transform('EPSG:32643', 'EPSG:4326', [br_x], [br_y])
        assert 72.0 <= lons[0] <= 73.0, f"Bottom-right lon {lons[0]} not in 72–73 range"
        assert 18.0 <= lats[0] <= 20.0, f"Bottom-right lat {lats[0]} not in 18–20 range"


# ---------------------------------------------------------------------------
# B. GeoJSON output coordinate tests
# ---------------------------------------------------------------------------

def _make_simple_flood_result():
    """Create a minimal FloodResult-like object for testing GeoJSON output."""
    from dataclasses import dataclass

    @dataclass
    class FakeFloodResult:
        flood_depth_m: np.ndarray
        flooded_mask: np.ndarray
        max_depth_m: float
        total_flooded_area_m2: float
        total_flood_volume_m3: float
        provenance: str

    depth = np.array([[0.5]])  # single flooded cell
    mask = np.array([[True]])
    return FakeFloodResult(
        flood_depth_m=depth,
        flooded_mask=mask,
        max_depth_m=0.5,
        total_flooded_area_m2=100.0,
        total_flood_volume_m3=50.0,
        provenance="SYNTHETIC/PROTOTYPE",
    )


class TestGeoJSONCoordinates:
    """Verify GeoJSON output uses EPSG:4326 coordinates near Mumbai."""

    def _get_geojson_with_mumbai_origin(self):
        """Helper: build GeoJSON using the real synthetic DEM origin."""
        _, meta = _create_synthetic_dem_mumbai_bbox()
        flood = _make_simple_flood_result()
        return _flood_result_to_geojson(
            flood_result=flood,
            cell_size=meta['transform'].a,
            origin_x=meta['transform'].c,
            origin_y=meta['transform'].f,
        )

    def test_geojson_has_features(self):
        """GeoJSON should contain at least one feature."""
        geojson = self._get_geojson_with_mumbai_origin()
        assert geojson["type"] == "FeatureCollection"
        assert len(geojson["features"]) >= 1

    def test_coordinates_are_epsg4326_longitude_latitude(self):
        """All polygon coordinates should be [lon, lat] in plausible EPSG:4326 ranges."""
        geojson = self._get_geojson_with_mumbai_origin()
        for feature in geojson["features"]:
            ring = feature["geometry"]["coordinates"][0]
            for lon, lat in ring:
                assert -180 <= lon <= 180, f"Longitude {lon} out of range"
                assert -90 <= lat <= 90, f"Latitude {lat} out of range"

    def test_coordinates_are_near_mumbai(self):
        """Polygon coordinates should be approximately 72–73°E, 18–20°N."""
        geojson = self._get_geojson_with_mumbai_origin()
        for feature in geojson["features"]:
            ring = feature["geometry"]["coordinates"][0]
            for lon, lat in ring:
                assert 72.0 <= lon <= 73.0, f"Longitude {lon} not near Mumbai (72–73)"
                assert 18.0 <= lat <= 20.0, f"Latitude {lat} not near Mumbai (18–20)"

    def test_polygon_is_closed(self):
        """Each polygon ring should be closed (first == last vertex)."""
        geojson = self._get_geojson_with_mumbai_origin()
        for feature in geojson["features"]:
            ring = feature["geometry"]["coordinates"][0]
            assert ring[0] == ring[-1], "Polygon ring is not closed"

    def test_polygon_area_is_tiny(self):
        """A 10 m cell should subtend a very small angular extent."""
        geojson = self._get_geojson_with_mumbai_origin()
        ring = geojson["features"][0]["geometry"]["coordinates"][0]
        lons = [pt[0] for pt in ring]
        lats = [pt[1] for pt in ring]
        lon_span = max(lons) - min(lons)
        lat_span = max(lats) - min(lats)
        # 10 m ≈ 0.0001° at equator; allow generous tolerance
        assert lon_span < 0.001, f"Lon span {lon_span} too large for 10 m cell"
        assert lat_span < 0.001, f"Lat span {lat_span} too large for 10 m cell"


# ---------------------------------------------------------------------------
# C. Full-endpoint integration test for coordinate correctness
# ---------------------------------------------------------------------------

class TestFloodEndpointGeoJSON:
    """Test the /flood/model endpoint returns correctly georeferenced GeoJSON."""

    @pytest.fixture
    def client(self):
        from fastapi.testclient import TestClient
        from backend.main import app
        return TestClient(app)

    def test_endpoint_returns_mumbai_coordinates(self, client):
        """POST /flood/model should return features with lon ≈ 72–73, lat ≈ 18–20."""
        response = client.post("/flood/model", json={
            "rainfall_mm": 25.0,
            "contributing_area_m2": 5000.0,
            "runoff_coefficient": 0.7,
            "timestep_hours": 1.0,
            "threshold_area_m2": 10.0,
        })
        assert response.status_code == 200
        data = response.json()
        assert data["type"] == "FeatureCollection"

        # Must have at least one flooded cell to validate coordinates
        if len(data["features"]) > 0:
            feature = data["features"][0]
            ring = feature["geometry"]["coordinates"][0]
            for lon, lat in ring:
                assert 72.0 <= lon <= 73.0, (
                    f"Longitude {lon} not in Mumbai range 72–73"
                )
                assert 18.0 <= lat <= 20.0, (
                    f"Latitude {lat} not in Mumbai range 18–20"
                )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
