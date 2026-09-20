import numpy as np
from typing import List
from .models import (
    LossResultStep,
    HydrographStep,
    SubcatchmentHydrograph
)

def compute_kinematic_wave(
    subcatchment_id: str,
    zone_id: str,
    loss_results: List[LossResultStep],
    drainage_area_km2: float,
    overland_length_m: float,
    overland_slope: float,
    manning_n: float
) -> SubcatchmentHydrograph:
    """
    Computes overland flow hydrograph using Kinematic Wave approximation.

    Based on the diffusion wave formulation for overland flow:
    q = (1/n) * h^(5/3) * sqrt(S)  (Manning's equation for unit width)
    where q = discharge per unit width (m^2/s/m), h = flow depth (m)

    For a subcatchment, we use the SCS unit hydrograph approach simplified:
    - Time to peak: Tp = 0.6 * (L^0.6 * S^0.3) / (i^0.4)  (empirical)
    - Or use: Tp = l^(0.6) / (0.6 * sqrt(S) * (1/n)^0.6)  (kinematic wave)

    Simplified approach for SIH V2:
    Use time-area method with kinematic wave celerity:
    c = (5/3) * (q/h) = (5/3) * v  (where v is flow velocity)
    """
    # Convert drainage area from km2 to m2
    drainage_area_m2 = drainage_area_km2 * 1e6

    # Calculate time step from loss results (assume uniform)
    if len(loss_results) < 2:
        dt_min = 5.0  # default 5 minutes
    else:
        dt_min = loss_results[1].time_minutes - loss_results[0].time_minutes

    dt_sec = dt_min * 60.0

    # Calculate flow velocity using Manning's equation for overland flow
    # Assume unit width flow and estimate depth from excess rainfall rate
    # Velocity v = (1/n) * h^(2/3) * sqrt(S)
    # For kinematic wave, we use the relationship between excess rainfall and discharge

    hydrograph_steps = []
    cumulative_volume_m3 = 0.0

    # Simple linear reservoir approach for overland flow translation
    # This is a simplified kinematic wave approximation suitable for SIH V2
    # In practice, we would solve the kinematic wave PDE, but for now:
    # Use time lag based on overland flow velocity

    # Estimate overland flow velocity (m/s)
    # Using Manning's: v = (1/n) * R^(2/3.0
    # R = h/(1+2h) for wide rectangular channel, approximated as h for small h
    # Assume characteristic flow depth from excess rainfall

    # Calculate characteristic velocity based on slope and roughness
    # v = (1/n) * sqrt(S) * h^(2/3)
    # For estimation, use a reference depth of 0.01m (1cm)
    ref_depth_m = 0.01
    velocity_ms = (1.0 / manning_n) * (ref_depth_m ** (2/3)) * np.sqrt(overland_slope)

    # Ensure minimum velocity
    velocity_ms = max(velocity_ms, 0.01)  # minimum 1 cm/s

    # Time of concentration (travel time across overland flow path)
    tc_sec = overland_length_m / velocity_ms if velocity_ms > 0 else 0.0
    tc_min = tc_sec / 60.0

    # Number of time steps for lag
    lag_steps = max(1, int(round(tc_min / dt_min)))

    # Apply lag to excess rainfall to create hydrograph
    excess_series = [step.excess_runoff_mm for step in loss_results]
    time_series = [step.time_minutes for step in loss_results]

    # Convert excess rainfall depth (mm) to volume (m3) for each time step
    # Volume = depth(m) * area(m2)
    excess_volumes_m3 = [
        (depth_mm / 1000.0) * drainage_area_m2
        for depth_mm in excess_series
    ]

    # Initialize hydrograph with zeros
    hydrograph_volumes_m3 = [0.0] * (len(excess_volumes_m3) + lag_steps)

    # Convolve excess rainfall with unit hydrograph (simple lag for now)
    for i, vol in enumerate(excess_volumes_m3):
        hydrograph_volumes_m3[i + lag_steps] += vol

    # Convert cumulative volume to discharge (m3/s)
    # Q = dV/dt, approximate as difference in cumulative volume over time step
    discharge_m3_s = [0.0] * len(hydrograph_volumes_m3)
    for i in range(1, len(hydrograph_volumes_m3)):
        discharge_m3_s[i] = (hydrograph_volumes_m3[i] - hydrograph_volumes_m3[i-1]) / dt_sec

    # Ensure non-negative discharge
    discharge_m3_s = [max(0.0, q) for q in discharge_m3_s]

    # Create hydrograph steps
    for i, (time_min, discharge) in enumerate(zip(
        [t + lag_steps * dt_min for t in time_series] +
        [time_series[-1] + (j+1) * dt_min for j in range(lag_steps)],
        discharge_m3_s
    )):
        hydrograph_steps.append(HydrographStep(
            time_minutes=time_min,
            discharge_m3_s=discharge
        ))
        cumulative_volume_m3 += discharge * dt_sec  # volume added in this timestep

    # Calculate peak discharge and time to peak
    if discharge_m3_s:
        peak_discharge = max(discharge_m3_s)
        peak_index = discharge_m3_s.index(peak_discharge)
        time_to_peak = hydrograph_steps[peak_index].time_minutes if peak_index < len(hydrograph_steps) else 0.0
    else:
        peak_discharge = 0.0
        time_to_peak = 0.0

    # Total volume is sum of all excess rainfall volumes
    total_volume_m3 = sum(excess_volumes_m3)

    return SubcatchmentHydrograph(
        subcatchment_id=subcatchment_id,
        zone_id=zone_id,
        drainage_area_km2=drainage_area_km2,
        peak_discharge_m3_s=peak_discharge,
        time_to_peak_minutes=time_to_peak,
        total_volume_m3=total_volume_m3,
        hydrograph=hydrograph_steps
    )