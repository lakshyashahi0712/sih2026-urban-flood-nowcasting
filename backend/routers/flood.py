"""Flood modeling API router."""

from __future__ import annotations

import tempfile
import os
from typing import Any, Dict, List
import numpy as np
from rasterio import open as rio_open
from rasterio.transform import from_origin
from rasterio.warp import transform

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, validator

from backend.app.config import settings
from backend.app.domain.pipeline.flood_pipeline import run_flood_modeling_pipeline


router = APIRouter(prefix="/flood", tags=["flood"])


class FloodModelRequest(BaseModel):
    """Request parameters for flood modeling."""
    rainfall_mm: float = Field(..., gt=0, description="Rainfall depth [mm]")
    contributing_area_m2: float = Field(..., gt=0, description="Contributing area [m²]")
    runoff_coefficient: float = Field(..., ge=0, le=1, description="Runoff coefficient [0,1]")
    timestep_hours: float = Field(1.0, gt=0, description="Timestep [hours]")
    threshold_area_m2: float = Field(0.0, ge=0, description="Stream initiation threshold [m²]")

    @validator('rainfall_mm')
    def rainfall_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError('Rainfall must be positive')
        return v

    @validator('contributing_area_m2')
    def area_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError('Contributing area must be positive')
        return v


def _create_synthetic_dem_mumbai_bbox(
    shape: tuple[int, int] = (10, 10),
    cell_size: float = 10.0,
    nodata: float | None = -9999.0,
) -> tuple[np.ndarray, dict]:
    """
    Create a SYNTHETIC DEM centred on Mumbai (placeholder / prototype).

    WARNING: This is NOT a real measured DEM. The elevation values are
    fabricated as a simple sloping plane for pipeline integration testing.
    Do not interpret the resulting flood depths as real observations or
    street-level predictions.

    The raster is positioned so that its top-left corner coincides with the
    configured Mumbai point (settings.mumbai_lon / mumbai_lat) after
    projecting to the computation CRS (EPSG:32643, UTM zone 43N).
    Cell size is in metres.
    """
    rows, cols = shape
    # Create a simple slope from northwest to southeast
    dem = np.zeros(shape, dtype=np.float64)
    for r in range(rows):
        for c in range(cols):
            dem[r, c] = 10.0 - (r * 0.5 + c * 0.3)  # Gentle slope

    # Set some nodata values at corners if needed
    if nodata is not None:
        dem[0, 0] = nodata
        dem[-1, -1] = nodata

    # Convert Mumbai EPSG:4326 point → EPSG:32643 (UTM 43N)
    # This becomes the top-left corner of the synthetic raster.
    mumbai_lon, mumbai_lat = settings.mumbai_lon, settings.mumbai_lat
    origin_x, origin_y = transform(
        'EPSG:4326', 'EPSG:32643',
        [mumbai_lon], [mumbai_lat]
    )
    origin_x, origin_y = origin_x[0], origin_y[0]

    # from_origin(west, north, xsize, ysize) — top-left corner convention
    raster_transform = from_origin(origin_x, origin_y, cell_size, cell_size)
    meta = {
        'driver': 'GTiff',
        'dtype': dem.dtype,
        'nodata': nodata,
        'width': cols,
        'height': rows,
        'count': 1,
        'crs': 'EPSG:32643',
        'transform': raster_transform,
    }
    return dem, meta


def _flood_result_to_geojson(
    flood_result: Any,
    cell_size: float = 10.0,
    origin_x: float = 0.0,
    origin_y: float = 0.0,
) -> Dict[str, Any]:
    """
    Convert FloodResult to GeoJSON FeatureCollection (EPSG:4326).

    Polygon vertices are computed in the computation CRS (EPSG:32643) and
    then reprojected to EPSG:4326 [longitude, latitude] as required by
    the GeoJSON specification (RFC 7946 §4).

    NOTE: The resulting coordinates reflect the SYNTHETIC prototype DEM,
    not real flood observations.
    """

    flood_depth = flood_result.flood_depth_m
    flooded_mask = flood_result.flooded_mask

    if flood_depth is None or flooded_mask is None:
        return {"type": "FeatureCollection", "features": []}

    rows, cols = flood_depth.shape
    features: List[Dict] = []

    for r in range(rows):
        for c in range(cols):
            if flooded_mask[r, c]:
                depth = float(flood_depth[r, c])
                # Skip very shallow flooding (optional threshold)
                if depth < 0.001:
                    continue

                # Calculate polygon coordinates for this cell in EPSG:32643
                # Assuming origin at top-left, y increases downward (rasterio convention)
                x_min = origin_x + c * cell_size
                y_max = origin_y - r * cell_size  # Top of cell
                x_max = x_min + cell_size
                y_min = y_max - cell_size  # Bottom of cell (negative because y increases downward)

                # Transform coordinates from EPSG:32643 to EPSG:4326 for GeoJSON
                xs = [x_min, x_max, x_max, x_min, x_min]
                ys = [y_max, y_max, y_min, y_min, y_max]
                lon_lats = transform('EPSG:32643', 'EPSG:4326', xs, ys)
                lons, lats = lon_lats

                # Reconstruct polygon in EPSG:4326
                polygon = [
                    [lons[0], lats[0]],  # Top-left
                    [lons[1], lats[1]],  # Top-right
                    [lons[2], lats[2]],  # Bottom-right
                    [lons[3], lats[3]],  # Bottom-left
                    [lons[4], lats[4]]   # Close polygon
                ]

                feature = {
                    "type": "Feature",
                    "properties": {
                        "depth": depth,
                        "cell_row": r,
                        "cell_col": c
                    },
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [polygon]
                    }
                }
                features.append(feature)

    geojson = {
        "type": "FeatureCollection",
        "features": features,
        # Summary statistics as top-level properties (non-standard but useful)
        "summary": {
            "max_depth_m": float(flood_result.max_depth_m),
            "total_flooded_area_m2": float(flood_result.total_flooded_area_m2),
            "total_flood_volume_m3": float(flood_result.total_flood_volume_m3),
            "provenance": flood_result.provenance
        }
    }
    return geojson


@router.post("/model")
async def run_flood_model(request: FloodModelRequest):
    """
    Run flood modeling pipeline and return results as GeoJSON.

    Uses synthetic DEM for Mumbai region (placeholder for MVP).
    """
    try:
        # Create synthetic DEM in temporary file
        dem_array, meta = _create_synthetic_dem_mumbai_bbox()

        with tempfile.NamedTemporaryFile(suffix='.tif', delete=False) as tmp:
            dem_path = tmp.name

        try:
            with rio_open(dem_path, 'w', **meta) as dst:
                dst.write(dem_array, 1)

            # Run the pipeline
            result = run_flood_modeling_pipeline(
                rainfall_mm=request.rainfall_mm,
                contributing_area_m2=request.contributing_area_m2,
                runoff_coefficient=request.runoff_coefficient,
                dem_raster_path=dem_path,
                timestep_hours=request.timestep_hours,
                threshold_area_m2=request.threshold_area_m2
            )

            # Convert to GeoJSON
            geojson_result = _flood_result_to_geojson(
                flood_result=result,
                cell_size=meta['transform'][0],  # pixel width
                origin_x=meta['transform'][2],   # top-left x
                origin_y=meta['transform'][5]    # top-left y
            )

            return geojson_result

        finally:
            # Clean up temporary file
            if os.path.exists(dem_path):
                os.unlink(dem_path)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Flood modeling failed: {str(e)}")