"""Flood modeling API router."""

from __future__ import annotations

import tempfile
import os
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional
import numpy as np
from rasterio import open as rio_open
from rasterio.transform import from_origin
from rasterio.warp import transform

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field, validator

try:
    from backend.app.config import settings
    from backend.app.domain.pipeline.flood_pipeline import run_flood_modeling_pipeline
    from backend.app.api.rainfall import get_adapter
    from backend.app.domain.roads.models import StreetFloodIntelligence
    from backend.app.domain.roads.spatial_matcher import match_flood_to_streets
except ImportError:
    from app.config import settings
    from app.domain.pipeline.flood_pipeline import run_flood_modeling_pipeline
    from app.api.rainfall import get_adapter
    from app.domain.roads.models import StreetFloodIntelligence
    from app.domain.roads.spatial_matcher import match_flood_to_streets



router = APIRouter(prefix="/flood", tags=["flood"])


class FloodModelRequest(BaseModel):
    """Request parameters for flood modeling."""
    rainfall_mm: float = Field(..., ge=0, description="Rainfall depth [mm]")
    contributing_area_m2: float = Field(..., gt=0, description="Contributing area [m²]")
    runoff_coefficient: float = Field(..., ge=0, le=1, description="Runoff coefficient [0,1]")
    timestep_hours: float = Field(1.0, gt=0, description="Timestep [hours]")
    threshold_area_m2: float = Field(0.0, ge=0, description="Stream initiation threshold [m²]")

    @validator('rainfall_mm')
    def rainfall_must_be_non_negative(cls, v):
        if v < 0:
            raise ValueError('Rainfall must be non-negative')
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


def _get_dem_path_and_meta() -> tuple[str, dict, bool]:
    """
    Get the DEM raster path and metadata for flood modeling.
    Uses real Copernicus DEM GLO-30 (30m) for the Mumbai pilot zone if available,
    falling back to synthetic DEM if the file is absent.

    Returns:
        (dem_path, meta, is_temp)
    """
    dem_file = getattr(settings, "dem_path", None)
    if dem_file and os.path.exists(dem_file):
        with rio_open(dem_file) as src:
            meta = src.meta.copy()
        return dem_file, meta, False

    # Fallback to synthetic DEM
    dem_array, meta = _create_synthetic_dem_mumbai_bbox()
    with tempfile.NamedTemporaryFile(suffix='.tif', delete=False) as tmp:
        tmp_path = tmp.name
    with rio_open(tmp_path, 'w', **meta) as dst:
        dst.write(dem_array, 1)
    return tmp_path, meta, True


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
            "total_runoff_volume_m3": float(getattr(flood_result, "total_runoff_volume_m3", 0.0)),
            "conveyed_drainage_volume_m3": float(getattr(flood_result, "conveyed_drainage_volume_m3", 0.0)),
            "surface_flood_volume_m3": float(getattr(flood_result, "surface_flood_volume_m3", flood_result.total_flood_volume_m3)),
            "provenance": flood_result.provenance
        }
    }
    return geojson


@router.post("/model")
async def run_flood_model(request: FloodModelRequest):
    """
    Run flood modeling pipeline and return results as GeoJSON.

    Uses real Copernicus GLO-30 DSM (30m) for the Mumbai pilot zone.
    """
    dem_path, meta, is_temp = _get_dem_path_and_meta()
    try:
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

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Flood modeling failed: {str(e)}")
    finally:
        if is_temp and os.path.exists(dem_path):
            os.unlink(dem_path)


class HorizonState(BaseModel):
    """Independently modeled flood state for a single forecast horizon."""
    horizon: str = Field(..., description="Forecast horizon label: NOW, +1h, +2h, +3h")
    lead_time: str = Field(..., description="Lead time string: 0h, +1h, +2h, +3h")
    timestamp: str = Field(..., description="Start of accumulation interval (ISO UTC)")
    interval_end: str = Field(..., description="End of accumulation interval (ISO UTC)")
    rainfall_mm: float = Field(..., ge=0, description="1-hour rainfall depth for this horizon [mm]")
    timestep_hours: float = Field(1.0, description="Model simulation timestep (strictly 1.0 hour)")
    max_depth_m: float = Field(..., ge=0, description="Peak flood depth [m]")
    flooded_area_m2: float = Field(..., ge=0, description="Flooded area [m²]")
    total_flooded_area_m2: float = Field(..., ge=0, description="Total flooded area [m²]")
    flood_volume_m3: float = Field(..., ge=0, description="Total flood volume [m³]")
    total_flood_volume_m3: float = Field(..., ge=0, description="Total flood volume [m³]")
    total_runoff_volume_m3: float = Field(0.0, ge=0, description="Total catchment runoff volume [m³]")
    conveyed_drainage_volume_m3: float = Field(0.0, ge=0, description="Runoff safely conveyed by drainage [m³]")
    surface_flood_volume_m3: float = Field(0.0, ge=0, description="Surcharge volume routed over surface [m³]")
    features: List[Dict[str, Any]] = Field(..., description="GeoJSON flood polygon features")
    geojson: Dict[str, Any] = Field(..., description="GeoJSON FeatureCollection for this horizon")


class FloodForecastResponse(BaseModel):
    """0-3 hour flood evolution response with 4 independently modeled horizon states."""
    source: str = Field(..., description="Rainfall provider identifier")
    source_type: str = Field("forecast", description="Classification of data source")
    acquired_at: Optional[str] = Field(None, description="When forecast was fetched (UTC)")
    status: str = Field("LIVE", description="Rainfall data freshness status: LIVE, STALE, or UNAVAILABLE")
    provenance: Dict[str, str] = Field(..., description="Provenance metadata for model components")
    horizons: List[HorizonState] = Field(..., description="Four chronological modeled forecast states")


class FloodForecastRequest(BaseModel):
    """Request parameters for generating 0-3 hour flood evolution."""
    contributing_area_m2: float = Field(500000.0, gt=0, description="Contributing area [m²]")
    runoff_coefficient: float = Field(0.7, ge=0, le=1, description="Runoff coefficient [0,1]")
    threshold_area_m2: float = Field(15000.0, ge=0, description="Stream initiation threshold [m²]")
    rainfall_mm_list: Optional[List[float]] = Field(None, description="Optional override list of 4 hourly rainfall values [mm]")
    use_cache: bool = Field(True, description="Allow cached rainfall forecast")

    @validator('rainfall_mm_list')
    def validate_rainfall_list(cls, v):
        if v is not None:
            if len(v) != 4:
                raise ValueError("rainfall_mm_list must contain exactly 4 hourly values")
            for val in v:
                if val < 0:
                    raise ValueError("Rainfall values must be non-negative")
        return v


async def compute_flood_forecast_evolution(
    contributing_area_m2: float = 500000.0,
    runoff_coefficient: float = 0.7,
    threshold_area_m2: float = 15000.0,
    rainfall_mm_list: Optional[List[float]] = None,
    use_cache: bool = True,
) -> FloodForecastResponse:
    """
    Generate four independently modeled flood states for NOW, +1h, +2h, +3h.

    Each horizon:
    - uses ONLY its own single hour's rainfall_mm
    - uses strictly timestep_hours = 1.0
    - executes the flood modeling pipeline independently
    - never sums rainfall across horizons
    """
    labels = ["NOW", "+1h", "+2h", "+3h"]
    lead_times = ["0h", "+1h", "+2h", "+3h"]

    if rainfall_mm_list is not None:
        source = "manual/test-override"
        acquired_at_str = datetime.now(timezone.utc).isoformat()
        status_str = "LIVE"
        now_dt = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
        records_meta = []
        for i, val in enumerate(rainfall_mm_list):
            t_start = now_dt + timedelta(hours=i)
            t_end = t_start + timedelta(hours=1)
            records_meta.append({
                "rainfall_mm": float(val),
                "timestamp": t_start.isoformat(),
                "interval_end": t_end.isoformat(),
                "lead_time": lead_times[i]
            })
    else:
        adapter = get_adapter()
        try:
            series = await adapter.fetch(use_cache=use_cache)
        except Exception as e:
            raise HTTPException(status_code=503, detail=f"Rainfall forecast unavailable: {str(e)}")

        if len(series.records) < 4:
            raise HTTPException(status_code=503, detail="Fewer than 4 hourly records available from rainfall provider")

        source = series.source or "open-meteo"
        acquired_at_str = series.acquired_at.isoformat() if series.acquired_at else None
        status_str = series.records[0].status.value if series.records else "LIVE"

        records_meta = []
        for i in range(4):
            rec = series.records[i]
            records_meta.append({
                "rainfall_mm": float(rec.rainfall_mm),
                "timestamp": rec.timestamp.isoformat(),
                "interval_end": rec.interval_end.isoformat(),
                "lead_time": lead_times[i]
            })

    # Load DEM raster path and metadata (real Copernicus DEM GLO-30 or fallback)
    dem_path, meta, is_temp = _get_dem_path_and_meta()

    try:
        horizon_states: List[HorizonState] = []
        for i in range(4):
            meta_item = records_meta[i]
            rain_mm = meta_item["rainfall_mm"]

            # Independent simulation strictly using 1-hour timestep
            result = run_flood_modeling_pipeline(
                rainfall_mm=rain_mm,
                contributing_area_m2=contributing_area_m2,
                runoff_coefficient=runoff_coefficient,
                dem_raster_path=dem_path,
                timestep_hours=1.0,  # Strictly 1.0 hour
                threshold_area_m2=threshold_area_m2
            )

            geojson_result = _flood_result_to_geojson(
                flood_result=result,
                cell_size=meta['transform'][0],
                origin_x=meta['transform'][2],
                origin_y=meta['transform'][5]
            )

            max_d = float(result.max_depth_m)
            area_m2 = float(result.total_flooded_area_m2)
            vol_m3 = float(result.total_flood_volume_m3)
            features = geojson_result.get("features", [])

            state = HorizonState(
                horizon=labels[i],
                lead_time=meta_item["lead_time"],
                timestamp=meta_item["timestamp"],
                interval_end=meta_item["interval_end"],
                rainfall_mm=rain_mm,
                timestep_hours=1.0,
                max_depth_m=max_d,
                flooded_area_m2=area_m2,
                total_flooded_area_m2=area_m2,
                flood_volume_m3=vol_m3,
                total_flood_volume_m3=vol_m3,
                total_runoff_volume_m3=float(result.total_runoff_volume_m3),
                conveyed_drainage_volume_m3=float(result.conveyed_drainage_volume_m3),
                surface_flood_volume_m3=float(result.surface_flood_volume_m3),
                features=features,
                geojson=geojson_result,
            )
            horizon_states.append(state)

        elevation_label = "Copernicus GLO-30 DSM (30m)" if not is_temp else "Synthetic DEM (sloping plane prototype)"
        return FloodForecastResponse(
            source=source,
            source_type="forecast",
            acquired_at=acquired_at_str,
            status=status_str,
            provenance={
                "rainfall": "Weather forecast (Open-Meteo hourly NWP)",
                "elevation": elevation_label,
                "runoff": "rainfall\u2013runoff",
                "drainage": "drainage capacity",
                "surface_routing": "surface routing",
                "model_status": "MODELLED / DERIVED"
            },
            horizons=horizon_states
        )
    finally:
        if is_temp and os.path.exists(dem_path):
            os.unlink(dem_path)


@router.get("/forecast", response_model=FloodForecastResponse)
async def get_flood_forecast(
    use_cache: bool = Query(True, description="Allow cached rainfall forecast")
):
    """
    Get 0-3 hour flood evolution with four independently modeled horizon states.
    Uses live/cached Open-Meteo hourly forecast.
    """
    return await compute_flood_forecast_evolution(use_cache=use_cache)


@router.post("/forecast", response_model=FloodForecastResponse)
async def post_flood_forecast(request: FloodForecastRequest):
    """
    Generate 0-3 hour flood evolution with four independently modeled horizon states,
    with customizable catchment parameters and optional rainfall override for testing.
    """
    return await compute_flood_forecast_evolution(
        contributing_area_m2=request.contributing_area_m2,
        runoff_coefficient=request.runoff_coefficient,
        threshold_area_m2=request.threshold_area_m2,
        rainfall_mm_list=request.rainfall_mm_list,
        use_cache=request.use_cache
    )


class StreetForecastResponse(BaseModel):
    """Street & Intersection Flood Intelligence across all forecast horizons."""
    source: str = Field("open-meteo", description="Rainfall provider identifier")
    status: str = Field("LIVE", description="Rainfall data freshness status")
    horizons: List[StreetFloodIntelligence] = Field(..., description="Chronological street intelligence horizons")


class StreetModelRequest(BaseModel):
    """Request parameters for street flood intelligence."""
    rainfall_mm: float = Field(..., ge=0, description="Rainfall depth [mm]")
    horizon: str = Field("+1h", description="Forecast horizon label")
    contributing_area_m2: float = Field(500000.0, gt=0, description="Contributing area [m²]")
    runoff_coefficient: float = Field(0.7, ge=0, le=1, description="Runoff coefficient [0,1]")
    threshold_area_m2: float = Field(15000.0, ge=0, description="Stream initiation threshold [m²]")


def _compute_street_intelligence_for_depth(
    rainfall_mm: float,
    horizon: str,
    lead_time: str,
    contributing_area_m2: float = 500000.0,
    runoff_coefficient: float = 0.7,
    threshold_area_m2: float = 15000.0,
) -> StreetFloodIntelligence:
    """Run flood model pipeline and spatially associate with OSM streets/intersections."""
    dem_path, meta, is_temp = _get_dem_path_and_meta()
    try:
        pipeline_res = run_flood_modeling_pipeline(
            rainfall_mm=rainfall_mm,
            contributing_area_m2=contributing_area_m2,
            runoff_coefficient=runoff_coefficient,
            dem_raster_path=dem_path,
            timestep_hours=1.0,
            threshold_area_m2=threshold_area_m2,
        )

        return match_flood_to_streets(
            flood_depth_m=pipeline_res.flood_depth_m,
            flooded_mask=pipeline_res.flooded_mask,
            cell_w=meta['transform'][0],
            cell_h=abs(meta['transform'][4]),
            origin_x=meta['transform'][2],
            origin_y=meta['transform'][5],
            horizon=horizon,
            lead_time=lead_time,
            rainfall_mm=rainfall_mm,
        )
    finally:
        if is_temp and os.path.exists(dem_path):
            os.unlink(dem_path)


@router.get("/streets", response_model=StreetFloodIntelligence)
async def get_street_flood_intelligence(
    horizon: str = Query("+1h", description="Forecast horizon: NOW, +1h, +2h, +3h"),
    rainfall_mm: Optional[float] = Query(None, ge=0, description="Optional override/scenario rainfall depth [mm]"),
    use_cache: bool = Query(True, description="Allow cached rainfall forecast"),
):
    """
    Get Street & Intersection Flood Intelligence for a forecast horizon or scenario.
    Spatially associates 2D modelled flood depths with real OpenStreetMap road corridors.
    """
    horizon_map = {"NOW": 0, "+1h": 1, "+2h": 2, "+3h": 3}
    lead_times = {"NOW": "0h", "+1h": "+1h", "+2h": "+2h", "+3h": "+3h"}
    h_label = horizon if horizon in horizon_map else "+1h"
    lead_time = lead_times.get(h_label, "+1h")

    if rainfall_mm is not None:
        return _compute_street_intelligence_for_depth(
            rainfall_mm=rainfall_mm,
            horizon=h_label,
            lead_time=lead_time,
        )

    # Fetch live/cached rainfall
    adapter = get_adapter()
    try:
        series = await adapter.fetch(use_cache=use_cache)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Rainfall forecast unavailable: {str(e)}")

    if len(series.records) < 4:
        raise HTTPException(status_code=503, detail="Fewer than 4 hourly records available")

    idx = horizon_map.get(h_label, 1)
    rec = series.records[idx]
    rain_val = float(rec.rainfall_mm)

    return _compute_street_intelligence_for_depth(
        rainfall_mm=rain_val,
        horizon=h_label,
        lead_time=lead_time,
    )


@router.get("/streets/forecast", response_model=StreetForecastResponse)
async def get_streets_forecast(
    use_cache: bool = Query(True, description="Allow cached rainfall forecast"),
):
    """
    Get Street & Intersection Flood Intelligence across all 4 chronological horizons (NOW, +1h, +2h, +3h).
    """
    adapter = get_adapter()
    try:
        series = await adapter.fetch(use_cache=use_cache)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Rainfall forecast unavailable: {str(e)}")

    if len(series.records) < 4:
        raise HTTPException(status_code=503, detail="Fewer than 4 hourly records available")

    labels = ["NOW", "+1h", "+2h", "+3h"]
    lead_times = ["0h", "+1h", "+2h", "+3h"]
    horizon_intelligences: List[StreetFloodIntelligence] = []

    for i in range(4):
        rec = series.records[i]
        rain_val = float(rec.rainfall_mm)
        intel = _compute_street_intelligence_for_depth(
            rainfall_mm=rain_val,
            horizon=labels[i],
            lead_time=lead_times[i],
        )
        horizon_intelligences.append(intel)

    return StreetForecastResponse(
        source=series.source or "open-meteo",
        status=series.records[0].status.value if series.records else "LIVE",
        horizons=horizon_intelligences,
    )


@router.post("/streets", response_model=StreetFloodIntelligence)
async def post_street_flood_intelligence(request: StreetModelRequest):
    """
    Calculate Street & Intersection Flood Intelligence for custom catchment and rainfall conditions.
    """
    lead_times = {"NOW": "0h", "+1h": "+1h", "+2h": "+2h", "+3h": "+3h"}
    lead_time = lead_times.get(request.horizon, "+1h")
    return _compute_street_intelligence_for_depth(
        rainfall_mm=request.rainfall_mm,
        horizon=request.horizon,
        lead_time=lead_time,
        contributing_area_m2=request.contributing_area_m2,
        runoff_coefficient=request.runoff_coefficient,
        threshold_area_m2=request.threshold_area_m2,
    )