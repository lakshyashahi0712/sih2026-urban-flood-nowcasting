"""
Pydantic schemas for Delhi/Kushak hydrologic runoff generation.
Defines data structures for rainfall, losses, and hydrographs.
"""

from typing import List, Literal, Optional
from pydantic import BaseModel, Field
from enum import Enum


class ProvenanceStatus(str, Enum):
    """Provenance status for data values."""
    OBSERVED = "OBSERVED"
    OFFICIAL = "OFFICIAL"
    DERIVED = "DERIVED"
    ASSUMED = "ASSUMED"
    UNKNOWN = "UNKNOWN"


class SoilParameters(BaseModel):
    """Hydrologic soil parameters for infiltration loss calculations."""
    ks_mm_hr: float = Field(..., description="Saturated hydraulic conductivity (mm/hr)")
    psi_mm: float = Field(..., description="Wetting front suction head (mm)")
    delta_theta: float = Field(..., description="Initial volumetric moisture deficit (m3/m3)")
    cn_pervious: float = Field(..., description="SCS Curve Number for pervious soils")
    cn_bare: float = Field(..., description="SCS Curve Number for bare soil/rock")
    cn_impervious: float = Field(default=98.0, description="SCS Curve Number for impervious surfaces")
    depression_storage_imp_mm: float = Field(default=2.0, description="Depression storage for impervious surfaces (mm)")
    depression_storage_perv_mm: float = Field(default=5.0, description="Depression storage for pervious surfaces (mm)")


class LandCoverFractions(BaseModel):
    """Land cover fractions for a subcatchment."""
    built_up_fraction: float = Field(..., description="ESA WorldCover Class 50 fraction (0.0 - 1.0)")
    eia_fraction: float = Field(default=0.70, description="Effective Impervious Area factor for built-up")
    vegetated_fraction: float = Field(..., description="Vegetation fraction (0.0 - 1.0)")
    bare_fraction: float = Field(..., description="Bare soil fraction (0.0 - 1.0)")
    water_fraction: float = Field(default=0.0, description="Water body fraction (0.0 - 1.0)")


class HyetographStep(BaseModel):
    """Single timestep of rainfall hyetograph."""
    time_minutes: float = Field(..., description="Time from start of event (minutes)")
    rainfall_intensity_mm_hr: float = Field(..., description="Rainfall intensity (mm/hr)")
    rainfall_depth_mm: float = Field(..., description="Rainfall depth for this timestep (mm)")


class LossResultStep(BaseModel):
    """Single timestep of infiltration loss results."""
    time_minutes: float = Field(..., description="Time from start of event (minutes)")
    rainfall_depth_mm: float = Field(..., description="Rainfall depth for this timestep (mm)")
    infiltration_loss_mm: float = Field(..., description="Infiltration loss (mm)")
    depression_loss_mm: float = Field(..., description="Depression storage loss (mm)")
    excess_runoff_mm: float = Field(..., description="Excess rainfall available for runoff (mm)")


class SubcatchmentLossResult(BaseModel):
    """Results of infiltration loss computation for a subcatchment."""
    subcatchment_id: str = Field(..., description="Subcatchment identifier")
    total_precipitation_mm: float = Field(..., description="Total precipitation depth (mm)")
    total_loss_mm: float = Field(..., description="Total loss (infiltration + depression) (mm)")
    total_excess_runoff_mm: float = Field(..., description="Total excess runoff depth (mm)")
    runoff_coefficient: float = Field(..., description="Ratio of excess runoff to precipitation")
    time_series: List[LossResultStep] = Field(..., description="Time series of loss results")


class HydrographStep(BaseModel):
    """Single timestep of discharge hydrograph."""
    time_minutes: float = Field(..., description="Time from start of event (minutes)")
    discharge_m3_s: float = Field(..., description="Discharge (cubic meters per second)")


class SubcatchmentHydrograph(BaseModel):
    """Overland flow hydrograph for a subcatchment."""
    subcatchment_id: str = Field(..., description="Subcatchment identifier")
    zone_id: str = Field(..., description="Lateral inflow zone identifier")
    drainage_area_km2: float = Field(..., description="Drainage area (square kilometers)")
    peak_discharge_m3_s: float = Field(..., description="Peak discharge (cubic meters per second)")
    time_to_peak_minutes: float = Field(..., description="Time to peak discharge (minutes)")
    total_volume_m3: float = Field(..., description="Total runoff volume (cubic meters)")
    hydrograph: List[HydrographStep] = Field(..., description="Time series of discharge")


class LateralCouplingAssignment(BaseModel):
    """Assignment of subcatchment hydrograph to hydraulic corridor location."""
    zone_id: str = Field(..., description="Lateral inflow zone identifier")
    subcatchment_id: str = Field(..., description="Subcatchment identifier")
    reach_id: str = Field(..., description="Hydraulic corridor reach identifier")
    chainage_start_m: float = Field(..., description="Start chainage along corridor (meters)")
    chainage_end_m: float = Field(..., description="End chainage along corridor (meters)")
    is_point_source: bool = Field(default=False, description="Whether inflow is point source or distributed")
    distributed_hydrograph: List[HydrographStep] = Field(..., description="Distributed hydrograph along corridor reach")


# Canonical Digital-Twin Domain Types for Phase 1


class Catchment(BaseModel):
    """Canonical representation of a catchment with provenance tracking."""
    id: str = Field(..., description="Unique identifier for the catchment")
    name: Optional[str] = Field(None, description="Name of the catchment")
    area_km2: Optional[float] = Field(None, description="Area of the catchment in square kilometers")
    area_provenance: ProvenanceStatus = Field(ProvenanceStatus.UNKNOWN, description="Provenance of the area value")
    centroid_lat: Optional[float] = Field(None, description="Latitude of centroid in decimal degrees")
    centroid_lat_provenance: ProvenanceStatus = Field(ProvenanceStatus.UNKNOWN, description="Provenance of centroid latitude")
    centroid_lon: Optional[float] = Field(None, description="Longitude of centroid in decimal degrees")
    centroid_lon_provenance: ProvenanceStatus = Field(ProvenanceStatus.UNKNOWN, description="Provenance of centroid longitude")


class DrainageReach(BaseModel):
    """Canonical representation of a drainage reach with provenance tracking."""
    id: str = Field(..., description="Unique identifier for the drainage reach")
    length_m: Optional[float] = Field(None, description="Length of the reach in meters")
    length_provenance: ProvenanceStatus = Field(ProvenanceStatus.UNKNOWN, description="Provenance of the length value")
    slope_m_per_m: Optional[float] = Field(None, description="Slope of the reach (m/m)")
    slope_provenance: ProvenanceStatus = Field(ProvenanceStatus.UNKNOWN, description="Provenance of the slope value")
    manning_n: Optional[float] = Field(None, description="Manning's roughness coefficient")
    manning_n_provenance: ProvenanceStatus = Field(ProvenanceStatus.UNKNOWN, description="Provenance of Manning's n")
    # Cross-sectional properties (simplified)
    shape: Optional[Literal["rectangular", "trapezoidal", "circular", "irregular"]] = Field(None, description="Cross-sectional shape")
    shape_provenance: ProvenanceStatus = Field(ProvenanceStatus.UNKNOWN, description="Provenance of the shape")
    width_m: Optional[float] = Field(None, description="Width of the cross-section (m) for rectangular/trapezoidal")
    width_provenance: ProvenanceStatus = Field(ProvenanceStatus.UNKNOWN, description="Provenance of width")
    height_m: Optional[float] = Field(None, description="Height of the cross-section (m) for rectangular/trapezoidal/circular")
    height_provenance: ProvenanceStatus = Field(ProvenanceStatus.UNKNOWN, description="Provenance of height")
    bottom_width_m: Optional[float] = Field(None, description="Bottom width (m) for trapezoidal channels")
    bottom_width_provenance: ProvenanceStatus = Field(ProvenanceStatus.UNKNOWN, description="Provenance of bottom width")
    side_slope_z: Optional[float] = Field(None, description="Side slope (z) for trapezoidal channels (H:V)")
    side_slope_z_provenance: ProvenanceStatus = Field(ProvenanceStatus.UNKNOWN, description="Provenance of side slope")


class HydraulicParameters(BaseModel):
    """Hydraulic parameters for flow calculations with provenance tracking."""
    manning_n: Optional[float] = Field(None, description="Manning's roughness coefficient")
    manning_n_provenance: ProvenanceStatus = Field(ProvenanceStatus.UNKNOWN, description="Provenance of Manning's n")
    # Additional hydraulic parameters can be added as needed


class RainfallEvent(BaseModel):
    """Canonical representation of a rainfall event with provenance tracking."""
    id: str = Field(..., description="Unique identifier for the rainfall event")
    start_time_minutes: float = Field(..., description="Start time of event in minutes from reference")
    end_time_minutes: float = Field(..., description="End time of event in minutes from reference")
    total_depth_mm: Optional[float] = Field(None, description="Total rainfall depth in mm")
    total_depth_provenance: ProvenanceStatus = Field(ProvenanceStatus.UNKNOWN, description="Provenance of total depth")
    max_intensity_mm_hr: Optional[float] = Field(None, description="Maximum rainfall intensity in mm/hr")
    max_intensity_provenance: ProvenanceStatus = Field(ProvenanceStatus.UNKNOWN, description="Provenance of max intensity")
    hyetograph: List[HyetographStep] = Field(..., description="Time series of rainfall hyetograph steps")


class BoundaryCondition(BaseModel):
    """Canonical representation of a boundary condition with provenance tracking."""
    id: str = Field(..., description="Unique identifier for the boundary condition")
    type: Literal["inflow", "outflow", "water_level"] = Field(..., description="Type of boundary condition")
    # For inflow/outflow: value is flow rate (m3/s); for water_level: value is stage (m)
    value: Optional[float] = Field(None, description="Value of the boundary condition")
    value_provenance: ProvenanceStatus = Field(ProvenanceStatus.UNKNOWN, description="Provenance of the value")
    # Time series of values (optional, for time-varying boundaries)
    time_series: List[HyetographStep] = Field(default_factory=list, description="Time series of boundary condition values (reusing HyetographStep for time-value pairs)")