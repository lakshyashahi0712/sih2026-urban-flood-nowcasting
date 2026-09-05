"""Radar rainfall domain models.

Defines provenance types, radar product metadata, and spatial rainfall grid structures
for quantitative Doppler Weather Radar ingestion and alignment.
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
from pydantic import BaseModel, ConfigDict, Field, field_validator

try:
    from backend.app.domain.rainfall.models import RainfallStatus, RainfallProvenance
    from backend.app.domain.rainfall.runoff import RunoffVolume
except ImportError:
    from app.domain.rainfall.models import RainfallStatus, RainfallProvenance
    from app.domain.rainfall.runoff import RunoffVolume


# Mumbai Pilot Extent in EPSG:32643 (UTM Zone 43N)
# Derived from pilot DEM: mumbai_pilot_dem_30m.tif
MUMBAI_PILOT_BOUNDS_32643: Tuple[float, float, float, float] = (
    274271.486,   # min_x (west)
    2108306.785,  # min_y (south)
    278531.486,   # max_x (east)
    2112116.785,  # max_y (north)
)


class RadarProductType(str, Enum):
    """IMD Doppler Weather Radar product types."""
    SRI = "SRI"        # Surface Rainfall Intensity [mm/h]
    PAC = "PAC"        # Precipitation Accumulation [mm]
    MAX_Z = "MAX_Z"    # Maximum Reflectivity [dBZ]
    PPI = "PPI"        # Plan Position Indicator reflectivity


class RadarFormatType(str, Enum):
    """Data encoding and container formats for radar products."""
    VISUAL_PALETTE_GIF = "VISUAL_PALETTE_GIF"  # Rendered 8-bit palette image; non-quantitative without calibration
    GEOTIFF = "GEOTIFF"                        # Georeferenced raster with embedded floating point data
    NETCDF4 = "NETCDF4"                        # Gridded multidimensional scientific data
    NUMERIC_GRID = "NUMERIC_GRID"              # Clean 2D array of precipitation values with geospatial transform


class RadarMetadata(BaseModel):
    """Metadata describing a radar acquisition from IMD or test fixture."""
    station_id: str = Field(..., description="Station code, e.g., 'VRV' (Veravali) or 'CLB' (Colaba)")
    station_name: str = Field(..., description="Full station name")
    station_lat: float = Field(..., description="Radar latitude")
    station_lon: float = Field(..., description="Radar longitude")
    product: RadarProductType = Field(..., description="Product type (SRI, PAC, etc.)")
    acquisition_time: datetime = Field(..., description="Observation timestamp (UTC)")
    valid_time: Optional[datetime] = Field(None, description="Valid time of accumulation window (UTC)")
    crs: str = Field(default="EPSG:32643", description="Coordinate reference system")
    spatial_resolution_m: Optional[float] = Field(None, gt=0, description="Spatial resolution in meters")
    bounds: Optional[Tuple[float, float, float, float]] = Field(None, description="Spatial bounds (min_x, min_y, max_x, max_y)")
    units: str = Field(default="mm/h", description="Physical unit of values")
    is_quantitative: bool = Field(default=False, description="True if numeric grid, False if rendered visual cartography")
    format_type: RadarFormatType = Field(default=RadarFormatType.VISUAL_PALETTE_GIF, description="Source format")
    status: RainfallStatus = Field(default=RainfallStatus.LIVE, description="Freshness status")

    @field_validator("acquisition_time", "valid_time", mode="before")
    @classmethod
    def ensure_utc(cls, v: Optional[Union[datetime, str]]) -> Optional[datetime]:
        if v is None:
            return None
        if isinstance(v, str):
            v = datetime.fromisoformat(v.replace("Z", "+00:00"))
        if v.tzinfo is None:
            raise ValueError("Timestamps must be timezone-aware")
        return v.astimezone(timezone.utc)


class SpatialRainfallGrid(BaseModel):
    """2D spatial grid of rainfall accumulation/intensity in projected coordinates (EPSG:32643).

    Handles clipping to pilot extent, nodata masking, and Rational Method runoff volume conversion.
    """
    model_config = ConfigDict(arbitrary_types_allowed=True)

    values: Union[List[List[float]], np.ndarray] = Field(..., description="2D array of rainfall values (shape: rows x cols)")
    bounds_32643: Tuple[float, float, float, float] = Field(
        ..., description="Projected bounding box (min_x, min_y, max_x, max_y) in EPSG:32643"
    )
    resolution_m: float = Field(..., gt=0.0, description="Grid cell size in meters")
    timestamp: datetime = Field(..., description="Start of observation/accumulation period (UTC)")
    duration_hours: float = Field(default=1.0, gt=0.0, description="Accumulation/intensity interval duration in hours")
    provenance: RainfallProvenance = Field(default=RainfallProvenance.RADAR, description="Source provenance")
    nodata_value: float = Field(default=-9999.0, description="Value representing masked/nodata cells")

    @field_validator("timestamp", mode="before")
    @classmethod
    def ensure_utc_ts(cls, v: Union[datetime, str]) -> datetime:
        if isinstance(v, str):
            v = datetime.fromisoformat(v.replace("Z", "+00:00"))
        if v.tzinfo is None:
            raise ValueError("Timestamp must be timezone-aware")
        return v.astimezone(timezone.utc)

    @field_validator("bounds_32643")
    @classmethod
    def validate_bounds(cls, v: Tuple[float, float, float, float]) -> Tuple[float, float, float, float]:
        min_x, min_y, max_x, max_y = v
        if max_x <= min_x:
            raise ValueError(f"max_x ({max_x}) must be greater than min_x ({min_x})")
        if max_y <= min_y:
            raise ValueError(f"max_y ({max_y}) must be greater than min_y ({min_y})")
        return v

    @field_validator("values")
    @classmethod
    def validate_values(cls, v: Union[List[List[float]], np.ndarray], info) -> np.ndarray:
        arr = np.asarray(v, dtype=float)
        if arr.size == 0:
            raise ValueError("Grid values array cannot be empty")
        if arr.ndim != 2:
            raise ValueError(f"Grid values must be a 2D array, got {arr.ndim}D")

        nodata = -9999.0
        if "nodata_value" in info.data:
            nodata = info.data["nodata_value"]

        valid_mask = ~np.isclose(arr, nodata) & ~np.isnan(arr)
        if np.any(valid_mask):
            if np.any(arr[valid_mask] < 0.0):
                raise ValueError("Precipitation values cannot be negative")
        return arr

    @property
    def array(self) -> np.ndarray:
        """Return values as a 2D numpy float array."""
        return np.asarray(self.values, dtype=float)

    @property
    def rows(self) -> int:
        return self.array.shape[0]

    @property
    def cols(self) -> int:
        return self.array.shape[1]

    def get_valid_mask(self) -> np.ndarray:
        """Mask of valid (non-nodata, non-NaN) cells."""
        arr = self.array
        return ~np.isclose(arr, self.nodata_value) & ~np.isnan(arr)

    def mean_rainfall_mm(self) -> float:
        """Compute the spatial mean rainfall depth over all valid cells [mm]."""
        arr = self.array
        mask = self.get_valid_mask()
        if not np.any(mask):
            return 0.0
        return float(np.mean(arr[mask]))

    def max_rainfall_mm(self) -> float:
        """Compute the maximum rainfall depth over all valid cells [mm]."""
        arr = self.array
        mask = self.get_valid_mask()
        if not np.any(mask):
            return 0.0
        return float(np.max(arr[mask]))

    def clip_to_bounds(
        self,
        target_bounds: Tuple[float, float, float, float],
    ) -> SpatialRainfallGrid:
        """Clip this grid to a target bounding box in EPSG:32643.

        Args:
            target_bounds: (min_x, min_y, max_x, max_y)

        Returns:
            New clipped SpatialRainfallGrid aligned with the target bounding box.
        """
        arr = self.array
        src_min_x, src_min_y, src_max_x, src_max_y = self.bounds_32643
        tgt_min_x, tgt_min_y, tgt_max_x, tgt_max_y = target_bounds

        # Compute overlap
        int_min_x = max(src_min_x, tgt_min_x)
        int_min_y = max(src_min_y, tgt_min_y)
        int_max_x = min(src_max_x, tgt_max_x)
        int_max_y = min(src_max_y, tgt_max_y)

        if int_max_x <= int_min_x or int_max_y <= int_min_y:
            raise ValueError(
                f"Target bounds {target_bounds} do not intersect grid bounds {self.bounds_32643}"
            )

        import math
        res = self.resolution_m
        # Slicing: row 0 is at top (src_max_y), decreasing downwards
        row_start = max(0, int(math.floor((src_max_y - int_max_y) / res)))
        row_end = min(self.rows, int(math.ceil((src_max_y - int_min_y) / res)))

        col_start = max(0, int(math.floor((int_min_x - src_min_x) / res)))
        col_end = min(self.cols, int(math.ceil((int_max_x - src_min_x) / res)))

        clipped_values = arr[row_start:row_end, col_start:col_end]
        if clipped_values.size == 0:
            raise ValueError("Clipped grid resulted in an empty slice")

        clipped_bounds = (
            src_min_x + col_start * res,
            src_max_y - row_end * res,
            src_min_x + col_end * res,
            src_max_y - row_start * res,
        )

        return SpatialRainfallGrid(
            values=clipped_values,
            bounds_32643=clipped_bounds,
            resolution_m=self.resolution_m,
            timestamp=self.timestamp,
            duration_hours=self.duration_hours,
            provenance=self.provenance,
            nodata_value=self.nodata_value,
        )

    def to_runoff_volume(
        self,
        contributing_area_m2: float,
        runoff_coefficient: float,
    ) -> RunoffVolume:
        """Convert spatial rainfall grid to Rational Method runoff volume.

        V = C * mean_rainfall_mm * A / 1000.0

        Args:
            contributing_area_m2: Catchment contributing area [m²]
            runoff_coefficient: Runoff coefficient [0, 1]

        Returns:
            RunoffVolume instance
        """
        mean_p = self.mean_rainfall_mm()
        return RunoffVolume(
            rainfall_mm=mean_p,
            contributing_area_m2=contributing_area_m2,
            runoff_coefficient=runoff_coefficient,
            timestep_hours=self.duration_hours,
        )


__all__ = [
    "RainfallProvenance",
    "RadarProductType",
    "RadarFormatType",
    "RadarMetadata",
    "SpatialRainfallGrid",
    "MUMBAI_PILOT_BOUNDS_32643",
]
