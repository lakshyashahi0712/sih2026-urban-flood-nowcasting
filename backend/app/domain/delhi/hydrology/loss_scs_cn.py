import numpy as np
from typing import List
from .models import (
    SoilParameters,
    LandCoverFractions,
    HyetographStep,
    LossResultStep,
    SubcatchmentLossResult
)

def compute_scs_cn_losses(
    subcatchment_id: str,
    rainfall_series: List[HyetographStep],
    landcover: LandCoverFractions,
    soil: SoilParameters
) -> SubcatchmentLossResult:
    """
    Computes SCS Curve Number (SCS-CN) losses.
    Standard NRCS NEH Part 630 approach.

    Equations:
    S = 25400 / CN - 254  (Potential Maximum Retention in mm)
    Ia = 0.2 * S          (Initial Abstraction in mm)
    Pe = (P - Ia)^2 / (P - Ia + S) if P > Ia else 0 (Cumulative Excess in mm)
    """

    # 1. Compute Composite Curve Number (CN)
    # We use EIA to partition the built-up area into Impervious and Pervious.
    # Total Area = Built-up + Vegetated + Bare + Water
    # Effective Impervious Area = Built-up * EIA
    # Pervious Area = Vegetated + Bare + Built-up * (1 - EIA)

    # Actually, the spec says:
    # CN_perv is for Open Space / Lawns / Parks
    # CN_bare is for Bare Rock
    # CN_imp is 98.0

    f_imp = landcover.built_up_fraction * landcover.eia_fraction
    f_perv = landcover.vegetated_fraction + landcover.built_up_fraction * (1.0 - landcover.eia_fraction)
    f_bare = landcover.bare_fraction

    # Normalize fractions to 1.0 (excluding water)
    total_f = f_imp + f_perv + f_bare
    if total_f > 0:
        f_imp /= total_f
        f_perv /= total_f
        f_bare /= total_f

    composite_cn = (f_imp * soil.cn_impervious +
                    f_perv * soil.cn_pervious +
                    f_bare * soil.cn_bare)

    # 2. Compute Retention and Initial Abstraction
    S = (25400.0 / composite_cn) - 254.0
    Ia = 0.2 * S

    results = []
    cumulative_p = 0.0
    prev_cumulative_excess = 0.0

    for step in rainfall_series:
        depth = step.rainfall_depth_mm
        cumulative_p += depth

        if cumulative_p > Ia:
            cum_excess = ((cumulative_p - Ia)**2) / (cumulative_p - Ia + S)
        else:
            cum_excess = 0.0

        incremental_excess = cum_excess - prev_cumulative_excess
        loss = depth - incremental_excess

        # In SCS-CN, the loss term includes infiltration, depression storage, interception, etc.
        # All abstractions are accounted for in Ia, so we don't separately track depression storage
        results.append(LossResultStep(
            time_minutes=step.time_minutes,
            rainfall_depth_mm=depth,
            infiltration_loss_mm=max(0.0, loss), # Combined loss (infiltration + depression storage + interception)
            depression_loss_mm=0.0, # Included in Ia/Infiltration for SCS-CN
            excess_runoff_mm=incremental_excess
        ))

        prev_cumulative_excess = cum_excess

    total_p = sum(r.rainfall_depth_mm for r in results)
    total_excess = sum(r.excess_runoff_mm for r in results)
    total_loss = total_p - total_excess

    return SubcatchmentLossResult(
        subcatchment_id=subcatchment_id,
        total_precipitation_mm=total_p,
        total_loss_mm=total_loss,
        total_excess_runoff_mm=total_excess,
        runoff_coefficient=total_excess / total_p if total_p > 0 else 0.0,
        time_series=results
    )
