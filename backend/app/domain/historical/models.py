"""Domain models for historical event replays and observed validation benchmarks.

Provides provider-independent structures for historical weather/flood events with
rigorous provenance tracking and validation safeguard separation.
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from zoneinfo import ZoneInfo
from pydantic import BaseModel, Field, field_validator, model_validator


class HistoricalProvenance(str, Enum):
    """Authoritative provenance tracking for historical event data.

    Values match SIH requirements exactly:
    - OBSERVED: Direct physical field measurements (e.g. rain gauge, level sensor).
    - REANALYSIS: Coarse-grid assimilation products (e.g. ECMWF ERA5 via Open-Meteo).
    - FORECAST: Numerical Weather Prediction model output.
    - DERIVED: Calculated from mathematical/astronomical formulations (e.g. tide tables).
    - SECONDARY-REPORT: Figures documented in literature, disaster reviews, or papers.
    """
    OBSERVED = "OBSERVED"
    REANALYSIS = "REANALYSIS"
    FORECAST = "FORECAST"
    DERIVED = "DERIVED"
    SECONDARY_REPORT = "SECONDARY-REPORT"


def _ensure_timezone_aware(dt: datetime | str) -> datetime:
    """Ensure datetime is timezone-aware. Defaults to Asia/Kolkata if parsed as naive."""
    if isinstance(dt, str):
        parsed = datetime.fromisoformat(dt)
    elif isinstance(dt, datetime):
        parsed = dt
    else:
        raise ValueError(f"Expected datetime or ISO string, got {type(dt)}")

    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=ZoneInfo("Asia/Kolkata"))
    return parsed


class ObservedStationRainfall(BaseModel):
    """Official observed rainfall measurement from an authoritative station.

    Preserves official 24-hour observational totals without fabricating missing
    sub-daily / hourly readings.
    """
    station_id: str = Field(..., description="Unique station identifier, e.g. IMD_SANTACRUZ")
    station_name: str = Field(..., description="Human-readable station name")
    operator: str = Field(..., description="Operating agency (e.g. IMD, BMC)")
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Latitude (EPSG:4326)")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Longitude (EPSG:4326)")
    total_rainfall_mm: float = Field(..., ge=0.0, description="Total observed rainfall depth in millimeters")
    duration_hours: float = Field(default=24.0, gt=0.0, description="Observational period duration in hours")
    period_start: datetime = Field(..., description="Start of observational window (timezone-aware)")
    period_end: datetime = Field(..., description="End of observational window (timezone-aware)")
    provenance: HistoricalProvenance = Field(
        default=HistoricalProvenance.OBSERVED,
        description="Must be OBSERVED for real station measurements"
    )
    source_citation: str = Field(..., description="Authoritative publication or archival citation")

    @field_validator("period_start", "period_end", mode="before")
    @classmethod
    def validate_tz(cls, v: datetime | str) -> datetime:
        return _ensure_timezone_aware(v)

    @field_validator("provenance")
    @classmethod
    def validate_provenance(cls, v: HistoricalProvenance) -> HistoricalProvenance:
        if v != HistoricalProvenance.OBSERVED:
            raise ValueError(
                f"ObservedStationRainfall provenance must be OBSERVED, got {v.value}. "
                "Do not store reanalysis or estimates in this model."
            )
        return v

    @model_validator(mode="after")
    def validate_times(self) -> "ObservedStationRainfall":
        if self.period_end <= self.period_start:
            raise ValueError(f"period_end ({self.period_end}) must be after period_start ({self.period_start})")
        return self


class HourlyRainfallStep(BaseModel):
    """A single discrete rainfall time-step for model forcing."""
    step_start: datetime = Field(..., description="Start of hourly interval (timezone-aware)")
    step_end: datetime = Field(..., description="End of hourly interval (timezone-aware)")
    rainfall_mm: float = Field(..., ge=0.0, description="Incremental rainfall depth in millimeters (>= 0.0)")
    intensity_mm_per_hr: float = Field(..., ge=0.0, description="Average intensity in mm/hr")
    provenance: HistoricalProvenance = Field(
        ...,
        description="Source classification: SECONDARY-REPORT for literature, REANALYSIS for ERA5"
    )
    source_citation: str = Field(..., description="Specific citation or dataset reference")

    @field_validator("step_start", "step_end", mode="before")
    @classmethod
    def validate_tz(cls, v: datetime | str) -> datetime:
        return _ensure_timezone_aware(v)

    @model_validator(mode="after")
    def validate_step(self) -> "HourlyRainfallStep":
        if self.step_end <= self.step_start:
            raise ValueError(f"step_end ({self.step_end}) must be after step_start ({self.step_start})")
        return self


class HistoricalRainfallForcing(BaseModel):
    """Time-series rainfall forcing for historical simulation.

    Explicitly separates literature-calibrated secondary reports from raw
    observations or reanalysis products.
    """
    event_id: str = Field(..., description="Historical event identifier")
    timezone_name: str = Field(default="Asia/Kolkata", description="Primary local timezone")
    series: List[HourlyRainfallStep] = Field(..., min_length=1, description="Sequential hourly rainfall intervals")
    total_forcing_mm: float = Field(..., ge=0.0, description="Sum of rainfall depths over the series [mm]")
    provenance: HistoricalProvenance = Field(
        ...,
        description="Authoritative provenance of the hourly series (e.g. SECONDARY-REPORT)"
    )
    calibration_reference: str = Field(..., description="Documentation of calibration methodology and source papers")
    is_model_input: bool = Field(default=True, description="Flag designating this as valid simulation input")

    @model_validator(mode="after")
    def validate_forcing(self) -> "HistoricalRainfallForcing":
        computed_total = sum(step.rainfall_mm for step in self.series)
        if abs(computed_total - self.total_forcing_mm) > 0.05:
            raise ValueError(
                f"total_forcing_mm ({self.total_forcing_mm}) does not match sum of series steps ({computed_total:.2f})"
            )
        if self.provenance == HistoricalProvenance.OBSERVED:
            raise ValueError(
                "Hourly rainfall series cannot be labeled OBSERVED unless unaggregated, continuous "
                "primary sensor logger data is genuinely present. Use SECONDARY-REPORT for literature profiles."
            )
        return self


class BoundaryLevelStep(BaseModel):
    """Discrete downstream coastal/tidal water level condition at time t."""
    timestamp: datetime = Field(..., description="Timestamp of boundary condition (timezone-aware)")
    water_level_m: float = Field(..., description="Downstream boundary water level [m above specified datum]")
    provenance: HistoricalProvenance = Field(
        default=HistoricalProvenance.DERIVED,
        description="DERIVED for astronomical tide calculations, OBSERVED for coastal radar tide gauges"
    )
    source_citation: str = Field(..., description="Tide table or gauge source citation")

    @field_validator("timestamp", mode="before")
    @classmethod
    def validate_tz(cls, v: datetime | str) -> datetime:
        return _ensure_timezone_aware(v)


class HistoricalBoundaryCondition(BaseModel):
    """Time-varying downstream coastal boundary condition for outfall hydraulic modeling."""
    event_id: str = Field(..., description="Historical event identifier")
    boundary_name: str = Field(..., description="Boundary name, e.g. Mahim_Creek_Mithi_Outfall")
    datum: str = Field(default="Mumbai Chart Datum (CD)", description="Vertical elevation datum")
    provenance: HistoricalProvenance = Field(
        default=HistoricalProvenance.DERIVED,
        description="Must be DERIVED for astronomical harmonic tide table calculations"
    )
    series: List[BoundaryLevelStep] = Field(..., min_length=1, description="Time series of boundary water levels")
    peak_level_m: float = Field(..., description="Peak tide / boundary stage in meters")
    peak_time: datetime = Field(..., description="Timestamp of peak boundary stage (timezone-aware)")
    source_citation: str = Field(..., description="Official tide table or oceanographic source citation")
    is_model_input: bool = Field(default=True, description="Flag designating this as valid simulation input")

    @field_validator("peak_time", mode="before")
    @classmethod
    def validate_tz(cls, v: datetime | str) -> datetime:
        return _ensure_timezone_aware(v)

    @field_validator("provenance")
    @classmethod
    def validate_tide_provenance(cls, v: HistoricalProvenance) -> HistoricalProvenance:
        if v == HistoricalProvenance.OBSERVED:
            raise ValueError(
                "Astronomical tide table values cannot be classified as OBSERVED. "
                "Must be classified as DERIVED."
            )
        return v


class InundationDepthRange(BaseModel):
    """Documented waterlogging depth range observed at a specific hotspot."""
    min_depth_m: float = Field(..., ge=0.0, description="Minimum observed inundation depth in meters")
    max_depth_m: Optional[float] = Field(None, ge=0.0, description="Maximum observed inundation depth in meters (None if unbounded)")
    descriptor: str = Field(..., description="Human-readable text descriptor, e.g. '0.60–1.10 m' or '>2.20 m'")

    @model_validator(mode="after")
    def validate_bounds(self) -> "InundationDepthRange":
        if self.max_depth_m is not None and self.max_depth_m < self.min_depth_m:
            raise ValueError(f"max_depth_m ({self.max_depth_m}) cannot be less than min_depth_m ({self.min_depth_m})")
        return self


class ObservedFloodBenchmark(BaseModel):
    """Independently documented flood inundation benchmark for post-simulation validation.

    CRITICAL SAFEGUARD:
    This model represents ground-truth validation targets ONLY.
    Under NO circumstances may instances of this class be injected into the simulation
    engine or used as hydraulic inputs.
    """
    location_id: str = Field(..., description="Unique landmark/hotspot identifier")
    location_name: str = Field(..., description="Location name, e.g. Kurla West (LBS Marg / Bail Bazar)")
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Latitude (EPSG:4326)")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Longitude (EPSG:4326)")
    depth_range: InundationDepthRange = Field(..., description="Documented waterlogging depth range [m]")
    observed_window_start: Optional[datetime] = Field(None, description="Start of waterlogging period")
    observed_window_end: Optional[datetime] = Field(None, description="End of waterlogging period")
    impact_notes: str = Field(..., description="Documented infrastructure impact, subway closure, traffic halt")
    source_citation: str = Field(..., description="Official government report, fire brigade log, or survey citation")
    provenance: HistoricalProvenance = Field(
        default=HistoricalProvenance.OBSERVED,
        description="OBSERVED field disaster management / survey records"
    )
    is_model_input: bool = Field(
        default=False,
        description="STRICT IMMUTABLE SAFEGUARD: Observed benchmarks can NEVER be model inputs"
    )

    @field_validator("observed_window_start", "observed_window_end", mode="before")
    @classmethod
    def validate_tz(cls, v: Optional[datetime | str]) -> Optional[datetime]:
        if v is None:
            return None
        return _ensure_timezone_aware(v)

    @field_validator("is_model_input")
    @classmethod
    def reject_model_input(cls, v: bool) -> bool:
        if v is True:
            raise ValueError(
                "CRITICAL ERROR: ObservedFloodBenchmark.is_model_input CANNOT be True! "
                "Observed flood validation benchmarks must never be used as hydraulic or rainfall inputs."
            )
        return False


def assert_no_benchmark_leakage(candidate_input: Any) -> None:
    """Architectural guard function: Rejects observed benchmark objects if accidentally passed as model input."""
    if isinstance(candidate_input, ObservedFloodBenchmark):
        raise TypeError(
            "Architectural Leakage Guard: ObservedFloodBenchmark cannot be used as a simulation input! "
            "Benchmarks are strictly reserved for post-run accuracy assessment."
        )
    if getattr(candidate_input, "is_model_input", None) is False:
        raise ValueError(
            f"Object {candidate_input} has is_model_input=False and cannot be accepted into the simulation pipeline."
        )


class HistoricalEventMetadata(BaseModel):
    """Metadata describing the historical flood event."""
    event_id: str = Field(..., description="Unique event slug, e.g. mumbai-2017-08-29-deluge")
    event_name: str = Field(..., description="Formal event name")
    event_date: str = Field(..., description="Event date string (YYYY-MM-DD)")
    timezone_name: str = Field(default="Asia/Kolkata", description="Timezone name")
    window_start: datetime = Field(..., description="Start of historical event simulation window (timezone-aware)")
    window_end: datetime = Field(..., description="End of historical event simulation window (timezone-aware)")
    rainfall_source_classification: HistoricalProvenance = Field(
        ...,
        description="Classification of rainfall forcing used (SECONDARY-REPORT for literature profile)"
    )
    tide_source_classification: HistoricalProvenance = Field(
        ...,
        description="Classification of tide boundary condition (DERIVED for astronomical tide)"
    )
    observed_validation_locations: List[str] = Field(
        ...,
        description="List of verified geographic landmarks with observed flood depth records"
    )
    source_attribution: Dict[str, str] = Field(
        ...,
        description="Formal citations for each component of the historical dataset"
    )
    units: Dict[str, str] = Field(
        default_factory=lambda: {
            "rainfall_depth": "mm",
            "rainfall_intensity": "mm/hr",
            "boundary_water_level": "m above Chart Datum (CD)",
            "inundation_depth": "m",
            "coordinates": "EPSG:4326 (WGS84) and EPSG:32643 (UTM 43N)"
        },
        description="Explicit measurement units for all data dimensions"
    )

    @field_validator("window_start", "window_end", mode="before")
    @classmethod
    def validate_tz(cls, v: datetime | str) -> datetime:
        return _ensure_timezone_aware(v)


class HistoricalEvent(BaseModel):
    """Complete, self-contained container for an historical flood event."""
    metadata: HistoricalEventMetadata
    observed_rainfall_totals: List[ObservedStationRainfall]
    rainfall_forcing: HistoricalRainfallForcing
    boundary_condition: HistoricalBoundaryCondition
    observed_flood_benchmarks: List[ObservedFloodBenchmark]
