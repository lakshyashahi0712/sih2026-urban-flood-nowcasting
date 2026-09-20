"""
Green-Ampt infiltration loss engine for Delhi/Kushak hydrologic runoff generation.
Implements physics-based Darcy flow into wetting front for time-varying rainfall.
"""

import math
from typing import List, Literal
from .models import (
    SoilParameters,
    LandCoverFractions,
    HyetographStep,
    LossResultStep,
    SubcatchmentLossResult
)


def compute_subcatchment_losses(
    subcatchment_id: str,
    rainfall_series: List[HyetographStep],
    landcover: LandCoverFractions,
    soil: SoilParameters,
    loss_method: Literal["green_ampt", "scs_cn"] = "green_ampt"
) -> SubcatchmentLossResult:
    """
    Computes time-varying infiltration, depression storage, and rainfall excess
    for a given subcatchment using Green-Ampt or SCS-CN method.

    Args:
        subcatchment_id: Identifier for the subcatchment
        rainfall_series: Time series of rainfall hyetograph steps
        landcover: Land cover fractions for the subcatchment
        soil: Soil parameters for infiltration calculations
        loss_method: Infiltration method to use ("green_ampt" or "scs_cn")

    Returns:
        SubcatchmentLossResult containing loss computation results
    """
    if loss_method == "green_ampt":
        return _compute_green_ampt_losses(subcatchment_id, rainfall_series, landcover, soil)
    elif loss_method == "scs_cn":
        return _compute_scs_cn_losses(subcatchment_id, rainfall_series, landcover, soil)
    else:
        raise ValueError(f"Unsupported loss method: {loss_method}")


def _compute_green_ampt_losses(
    subcatchment_id: str,
    rainfall_series: List[HyetographStep],
    landcover: LandCoverFractions,
    soil: SoilParameters
) -> SubcatchmentLossResult:
    """
    Green-Ampt infiltration loss computation.
    Based on physics-based Darcy flow into wetting front.
    """
    # Initialize variables
    time_series = []
    cumulative_infiltration = 0.0  # mm
    cumulative_rainfall = 0.0      # mm
    ponding_time = None            # minutes when ponding occurs
    psi = soil.psi_mm              # wetting front suction head (mm)
    delta_theta = soil.delta_theta # initial moisture deficit (m3/m3)
    ks = soil.ks_mm_hr             # saturated hydraulic conductivity (mm/hr)

    # Depression storage losses
    imp_area = landcover.built_up_fraction * landcover.eia_fraction
    perv_area = landcover.vegetated_fraction + landcover.bare_fraction
    depression_storage_imp = soil.depression_storage_imp_mm * imp_area
    depression_storage_perv = soil.depression_storage_perv_mm * perv_area
    total_depression_storage = depression_storage_imp + depression_storage_perv

    # Track depression storage fulfillment
    depression_storage_filled = 0.0

    prev_time_min = 0.0  # time of previous step, start at 0
    for i, step in enumerate(rainfall_series):
        time_minutes = step.time_minutes
        rainfall_intensity = step.rainfall_intensity_mm_hr  # mm/hr
        rainfall_depth = step.rainfall_depth_mm             # mm

        # Calculate time step duration in hours
        if i == 0:
            dt_min = time_minutes - prev_time_min
        else:
            dt_min = time_minutes - rainfall_series[i-1].time_minutes
        dt_hr = dt_min / 60.0  # convert to hours

        # Convert intensity to mm/hour for consistency with ks
        intensity_mm_per_hr = rainfall_intensity  # already in mm/hr

        cumulative_rainfall += rainfall_depth

        # Calculate infiltration based on ponding status
        if ponding_time is None:
            # Before ponding: infiltration limited by rainfall intensity
            # Check if rainfall intensity exceeds infiltration capacity
            if intensity_mm_per_hr > ks:
                # Potential for ponding - calculate time to ponding
                # Using Green-Ampt equation for time to ponding
                if psi * delta_theta > 0:
                    tp = (psi * delta_theta * ks) / (intensity_mm_per_hr * (intensity_mm_per_hr - ks))
                    if tp <= 0 or math.isinf(tp) or math.isnan(tp):
                        tp = 0  # Immediate ponding
                    ponding_time = time_minutes + tp * 60.0  # convert tp from hours to minutes
                else:
                    ponding_time = time_minutes  # Immediate ponding if no suction deficit

            # Infiltration before ponding equals rainfall intensity (no runoff yet)
            infiltration_mm = rainfall_depth
            depression_loss = 0.0

            # Fill depression storage first
            if depression_storage_filled < total_depression_storage:
                available_depression = total_depression_storage - depression_storage_filled
                depression_loss = min(rainfall_depth, available_depression)
                depression_storage_filled += depression_loss
                infiltration_mm -= depression_loss
            else:
                depression_loss = 0.0

            # Update cumulative infiltration with actual infiltration that occurred
            cumulative_infiltration += infiltration_mm

        else:
            # After ponding: infiltration governed by Green-Ampt equation
            # f = Ks * (1 + (psi * delta_theta) / F)
            # where F is cumulative infiltration
            if cumulative_infiltration > 0:
                infiltration_capacity = ks * (1.0 + (psi * delta_theta) / cumulative_infiltration)
            else:
                infiltration_capacity = float('inf')  # Initially infinite capacity

            # Actual infiltration is minimum of capacity and available water
            # Infiltration capacity is in mm/hr, multiply by dt_hr to get mm for the time step
            max_possible_infiltration = infiltration_capacity * dt_hr
            infiltration_mm = min(rainfall_depth, max_possible_infiltration)

            # Ensure infiltration doesn't go negative
            infiltration_mm = max(0.0, infiltration_mm)

            # Depression storage is already filled after ponding
            depression_loss = 0.0

            # Update cumulative infiltration
            cumulative_infiltration += infiltration_mm

        # Calculate excess rainfall (available for runoff)
        excess_runoff_mm = rainfall_depth - infiltration_mm - depression_loss
        excess_runoff_mm = max(0.0, excess_runoff_mm)  # Ensure non-negative

        # Create loss result step
        loss_step = LossResultStep(
            time_minutes=time_minutes,
            rainfall_depth_mm=rainfall_depth,
            infiltration_loss_mm=infiltration_mm,
            depression_loss_mm=depression_loss,
            excess_runoff_mm=excess_runoff_mm
        )
        time_series.append(loss_step)

        # Update previous time for next iteration
        prev_time_min = time_minutes

    # Calculate totals
    total_precipitation_mm = cumulative_rainfall
    total_loss_mm = sum(step.infiltration_loss_mm + step.depression_loss_mm for step in time_series)
    total_excess_runoff_mm = sum(step.excess_runoff_mm for step in time_series)

    # Avoid division by zero
    runoff_coefficient = total_excess_runoff_mm / total_precipitation_mm if total_precipitation_mm > 0 else 0.0

    # Create and return result
    result = SubcatchmentLossResult(
        subcatchment_id=subcatchment_id,
        total_precipitation_mm=total_precipitation_mm,
        total_loss_mm=total_loss_mm,
        total_excess_runoff_mm=total_excess_runoff_mm,
        runoff_coefficient=runoff_coefficient,
        time_series=time_series
    )

    return result


def _compute_scs_cn_losses(
    subcatchment_id: str,
    rainfall_series: List[HyetographStep],
    landcover: LandCoverFractions,
    soil: SoilParameters
) -> SubcatchmentLossResult:
    """
    SCS-CN empirical runoff volume loss computation.
    Based on the Curve Number method: Q = (P - Ia)^2 / (P - Ia + S) for P > Ia
    """
    # Initialize variables
    time_series = []
    cumulative_rainfall = 0.0      # mm

    # Calculate composite Curve Number for the subcatchment
    # CN = (built_up * EIA * CN_imp) + (vegetated * CN_perv) + (bare * CN_bare) + (water * CN_water)
    cn_imp = soil.cn_impervious
    cn_perv = soil.cn_pervious
    cn_bare = soil.cn_bare
    cn_water = 100.0  # Water bodies produce no infiltration

    built_up_cn = landcover.built_up_fraction * landcover.eia_fraction * cn_imp
    vegetated_cn = landcover.vegetated_fraction * cn_perv
    bare_cn = landcover.bare_fraction * cn_bare
    water_cn = landcover.water_fraction * cn_water

    composite_cn = built_up_cn + vegetated_cn + bare_cn + water_cn

    # Ensure CN is within valid bounds
    composite_cn = max(0.0, min(100.0, composite_cn))

    # Calculate potential maximum retention S (in mm)
    # S = (25400 / CN) - 254
    if composite_cn > 0:
        s = (25400.0 / composite_cn) - 254.0
    else:
        s = 0.0  # No retention if CN=0 (all water)

    # Initial abstraction Ia = 0.2 * S
    ia = 0.2 * s

    for step in rainfall_series:
        time_minutes = step.time_minutes
        rainfall_depth = step.rainfall_depth_mm

        cumulative_rainfall += rainfall_depth

        # Calculate runoff using SCS-CN method
        # Initial abstraction Ia encompasses all initial losses (depression storage, interception, etc.)
        if rainfall_depth > ia:
            # Runoff occurs: Q = (P - Ia)^2 / (P - Ia + S)
            runoff_depth = ((rainfall_depth - ia) ** 2) / (rainfall_depth - ia + s)
            runoff_depth = max(0.0, runoff_depth)  # Ensure non-negative
            infiltration_loss = rainfall_depth - runoff_depth
        else:
            # No runoff yet - all rainfall goes to initial losses
            runoff_depth = 0.0
            infiltration_loss = rainfall_depth

        # Ensure infiltration loss doesn't go negative
        infiltration_loss = max(0.0, infiltration_loss)

        # Create loss result step
        loss_step = LossResultStep(
            time_minutes=time_minutes,
            rainfall_depth_mm=rainfall_depth,
            infiltration_loss_mm=infiltration_loss,
            depression_loss_mm=0.0,  # Depression storage included in Ia term
            excess_runoff_mm=runoff_depth
        )
        time_series.append(loss_step)

    # Calculate totals
    total_precipitation_mm = cumulative_rainfall
    total_loss_mm = sum(step.infiltration_loss_mm + step.depression_loss_mm for step in time_series)
    total_excess_runoff_mm = sum(step.excess_runoff_mm for step in time_series)

    # Avoid division by zero
    runoff_coefficient = total_excess_runoff_mm / total_precipitation_mm if total_precipitation_mm > 0 else 0.0

    # Create and return result
    result = SubcatchmentLossResult(
        subcatchment_id=subcatchment_id,
        total_precipitation_mm=total_precipitation_mm,
        total_loss_mm=total_loss_mm,
        total_excess_runoff_mm=total_excess_runoff_mm,
        runoff_coefficient=runoff_coefficient,
        time_series=time_series
    )

    return result