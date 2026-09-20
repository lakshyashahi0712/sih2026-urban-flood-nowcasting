"""
Scenario runner for Delhi/Kushak rainfall-to-runoff engine.
Processes rainfall events through loss models and runoff transformation to generate subcatchment hydrographs.
"""

import os
import csv
import math
from datetime import datetime
from typing import List, Dict, Any
from .models import (
    HyetographStep,
    LandCoverFractions,
    SoilParameters,
    LossResultStep,
    HydrographStep
)
from .loss_green_ampt import compute_subcatchment_losses as compute_green_ampt_losses
from .loss_scs_cn import compute_scs_cn_losses
from .runoff_transform import compute_kinematic_wave

# Paths to data files
# Go up 6 levels from this file to reach the project root (sih2026)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))))
DATA_DIR = os.path.join(PROJECT_ROOT, 'data')
DELHI_DATA_DIR = os.path.join(DATA_DIR, 'delhi')
DERIVED_HYDROLOGY_DIR = os.path.join(DELHI_DATA_DIR, 'derived', 'hydrology')
DERIVED_RAINFALL_DIR = os.path.join(DELHI_DATA_DIR, 'derived', 'rainfall')
DERIVED_RUNOFF_DIR = os.path.join(DELHI_DATA_DIR, 'derived', 'runoff')

# Event files
EVENT_FILES = {
    'EV-01': os.path.join(DERIVED_RAINFALL_DIR, 'kushak_forcing_hyetograph_20240628_safdarjung.csv'),
    'EV-02': os.path.join(DERIVED_RAINFALL_DIR, 'kushak_forcing_hyetograph_20230708_10_safdarjung.csv')
}

def read_rainfall_hyetograph(file_path: str) -> List[HyetographStep]:
    """
    Reads a rainfall hyetograph CSV file and returns a list of HyetographStep.
    Assumes the file has a header and columns: timestamp_ist, rainfall_mm, rainfall_rate_mm_h, ...
    We use rainfall_mm as the depth for the timestep and rainfall_rate_mm_h as the intensity.
    """
    hyetograph = []
    with open(file_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # We assume the timestep is 1 hour (as per the data) but we don't have the time step in the file.
            # The timestamp is hourly, so we can use the hour as the time step.
            # However, we don't have the start time of the event? We can use the timestamp to compute minutes from start.
            # For simplicity, we will assume the first row is at time 0 and each subsequent row is +60 minutes.
            # But the file might not start at 0? We'll compute the time difference from the first row.
            pass  # We'll implement below

    # Instead, we can use the timestamp to compute the time in minutes from the start of the event.
    # We'll parse the timestamp and compute the difference from the first timestamp.

    # Let's redo: read all rows, then compute time steps.
    with open(file_path, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if not rows:
        return hyetograph

    # Parse the first timestamp to get the base time
    from datetime import datetime
    base_time = datetime.fromisoformat(rows[0]['timestamp_ist'].replace('Z', '+00:00'))

    for i, row in enumerate(rows):
        current_time = datetime.fromisoformat(row['timestamp_ist'].replace('Z', '+00:00'))
        time_minutes = (current_time - base_time).total_seconds() / 60.0
        rainfall_depth_mm = float(row['rainfall_mm'])
        rainfall_rate_mm_hr = float(row['rainfall_rate_mm_h'])
        hyetograph.append(HyetographStep(
            time_minutes=time_minutes,
            rainfall_intensity_mm_hr=rainfall_rate_mm_hr,
            rainfall_depth_mm=rainfall_depth_mm
        ))

    return hyetograph

def read_scenarios() -> List[Dict[str, Any]]:
    """Reads the scenarios CSV and returns a list of dictionaries."""
    scenarios = []
    with open(os.path.join(DERIVED_HYDROLOGY_DIR, 'kushak_runoff_scenarios.csv'), 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            scenarios.append(row)
    return scenarios

def read_subcatchment_inventory() -> List[Dict[str, Any]]:
    """Reads the subcatchment inventory CSV and returns a list of dictionaries."""
    subcatchments = []
    with open(os.path.join(DERIVED_HYDROLOGY_DIR, 'kushak_subcatchment_inventory.csv'), 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert percentages to fractions
            row['built_up_percent'] = float(row['built_up_percent']) / 100.0
            # Use total_vegetated_percent for vegetated fraction
            row['vegetated_percent'] = float(row['total_vegetated_percent']) / 100.0
            row['bare_soil_rock_percent'] = float(row['bare_soil_rock_percent']) / 100.0
            row['open_water_percent'] = float(row['open_water_percent']) / 100.0
            # Note: tree_cover_percent is not needed for our land cover fractions.
            subcatchments.append(row)
    return subcatchments

def run_scenario(scenario: Dict[str, Any], event_id: str, loss_method: str) -> None:
    """
    Runs a single scenario for a given event and loss method.
    """
    print(f"Running scenario {scenario['scenario_id']}, event {event_id}, loss method {loss_method}")

    # Read rainfall hyetograph for the event
    hyetograph_path = EVENT_FILES[event_id]
    rainfall_series = read_rainfall_hyetograph(hyetograph_path)

    # Read subcatchment inventory
    subcatchments = read_subcatchment_inventory()

    # Prepare output directory
    output_dir = os.path.join(DERIVED_RUNOFF_DIR, scenario['scenario_id'], event_id, loss_method)
    os.makedirs(output_dir, exist_ok=True)

    # Summary data for this scenario/event/loss method
    summary_rows = []

    for sub in subcatchments:
        subcatchment_id = sub['subcatchment_id']

        # Extract land cover fractions (already converted to fraction in read_subcatchment_inventory)
        landcover = LandCoverFractions(
            built_up_fraction=sub['built_up_percent'],
            eia_fraction=float(scenario['eia_fraction_builtup']),  # from scenario
            vegetated_fraction=sub['vegetated_percent'],
            bare_fraction=sub['bare_soil_rock_percent'],
            water_fraction=sub['open_water_percent']
        )

        # Extract soil parameters from scenario
        soil = SoilParameters(
            ks_mm_hr=float(scenario['green_ampt_ks_mm_hr']),
            psi_mm=float(scenario['green_ampt_psi_mm']),
            delta_theta=float(scenario['green_ampt_delta_theta']),
            cn_pervious=float(scenario['scs_cn_pervious']),
            cn_bare=float(scenario['scs_cn_bare']),
            cn_impervious=float(scenario['scs_cn_impervious']),
            depression_storage_imp_mm=float(scenario['depression_storage_imp_mm']),
            depression_storage_perv_mm=float(scenario['depression_storage_perv_mm'])
        )

        # Compute losses
        if loss_method == 'green_ampt':
            loss_result = compute_green_ampt_losses(
                subcatchment_id=subcatchment_id,
                rainfall_series=rainfall_series,
                landcover=landcover,
                soil=soil
            )
        elif loss_method == 'scs_cn':
            loss_result = compute_scs_cn_losses(
                subcatchment_id=subcatchment_id,
                rainfall_series=rainfall_series,
                landcover=landcover,
                soil=soil
            )
        else:
            raise ValueError(f"Unknown loss method: {loss_method}")

        # Check mass balance
        p = loss_result.total_precipitation_mm
        loss = loss_result.total_loss_mm
        excess = loss_result.total_excess_runoff_mm
        mass_balance_error = abs(p - (loss + excess)) / p * 100.0 if p > 0 else 0.0
        if mass_balance_error > 0.10:
            print(f"  WARNING: Mass balance error for {subcatchment_id} is {mass_balance_error:.4f}% (>0.10%)")

        # Compute hydrograph using kinematic wave
        # We need overland flow parameters: we'll estimate from subcatchment inventory
        drainage_area_km2 = float(sub['drainage_area_km2'])
        # Estimate overland length as the square root of the area (in m) - characteristic length
        overland_length_m = math.sqrt(drainage_area_km2 * 1e6)  # convert km2 to m2 and take sqrt
        # Assume a slope of 0.01 (1%) as a default
        overland_slope = 0.01
        # Assume Manning's n for impervious surface (0.013) as a default
        manning_n = 0.013

        hydrograph = compute_kinematic_wave(
            subcatchment_id=subcatchment_id,
            zone_id=sub['zone_id'],
            loss_results=loss_result.time_series,
            drainage_area_km2=drainage_area_km2,
            overland_length_m=overland_length_m,
            overland_slope=overland_slope,
            manning_n=manning_n
        )

        # Write loss results to CSV
        loss_file = os.path.join(output_dir, f"{subcatchment_id}_loss.csv")
        with open(loss_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['time_minutes', 'rainfall_depth_mm', 'infiltration_loss_mm', 'depression_loss_mm', 'excess_runoff_mm'])
            for step in loss_result.time_series:
                writer.writerow([step.time_minutes, step.rainfall_depth_mm, step.infiltration_loss_mm, step.depression_loss_mm, step.excess_runoff_mm])

        # Write hydrograph to CSV
        hydro_file = os.path.join(output_dir, f"{subcatchment_id}_hydrograph.csv")
        with open(hydro_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['time_minutes', 'discharge_m3_s'])
            for step in hydrograph.hydrograph:
                writer.writerow([step.time_minutes, step.discharge_m3_s])

        # Add to summary
        summary_rows.append({
            'subcatchment_id': subcatchment_id,
            'total_precipitation_mm': loss_result.total_precipitation_mm,
            'total_loss_mm': loss_result.total_loss_mm,
            'total_excess_runoff_mm': loss_result.total_excess_runoff_mm,
            'runoff_coefficient': loss_result.runoff_coefficient,
            'peak_discharge_m3_s': hydrograph.peak_discharge_m3_s,
            'time_to_peak_minutes': hydrograph.time_to_peak_minutes,
            'total_volume_m3': hydrograph.total_volume_m3,
            'mass_balance_error_percent': mass_balance_error
        })

    # Write summary CSV
    summary_file = os.path.join(output_dir, 'summary.csv')
    with open(summary_file, 'w', newline='') as f:
        fieldnames = ['subcatchment_id', 'total_precipitation_mm', 'total_loss_mm', 'total_excess_runoff_mm',
                      'runoff_coefficient', 'peak_discharge_m3_s', 'time_to_peak_minutes', 'total_volume_m3',
                      'mass_balance_error_percent']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(summary_rows)

    print(f"  Completed. Output in {output_dir}")

def main():
    """Main function to run all scenarios for both events and both loss methods."""
    print("Starting Delhi/Kushak rainfall-to-runoff scenario runner...")

    # Ensure output directory exists
    os.makedirs(DERIVED_RUNOFF_DIR, exist_ok=True)

    scenarios = read_scenarios()
    event_ids = ['EV-01', 'EV-02']
    loss_methods = ['green_ampt', 'scs_cn']

    for scenario in scenarios:
        for event_id in event_ids:
            for loss_method in loss_methods:
                try:
                    run_scenario(scenario, event_id, loss_method)
                except Exception as e:
                    print(f"ERROR running scenario {scenario['scenario_id']}, event {event_id}, loss method {loss_method}: {e}")

    print("Scenario runner completed.")

if __name__ == '__main__':
    main()