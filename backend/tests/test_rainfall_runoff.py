"""Tests for the runoff domain model implementing Rational Method."""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.domain.rainfall.runoff import RunoffVolume


def test_zero_inputs_produce_zero_runoff():
    """Zero rainfall, area, or coefficient should yield zero runoff volume."""
    # Zero rainfall
    runoff = RunoffVolume(
        rainfall_mm=0.0,
        contributing_area_m2=1000.0,
        runoff_coefficient=0.5,
        timestep_hours=1.0
    )
    assert runoff.volume_m3 == 0.0

    # Zero area
    runoff = RunoffVolume(
        rainfall_mm=10.0,
        contributing_area_m2=0.0,
        runoff_coefficient=0.5,
        timestep_hours=1.0
    )
    assert runoff.volume_m3 == 0.0

    # Zero coefficient
    runoff = RunoffVolume(
        rainfall_mm=10.0,
        contributing_area_m2=1000.0,
        runoff_coefficient=0.0,
        timestep_hours=1.0
    )
    assert runoff.volume_m3 == 0.0


def test_runoff_coefficient_of_one():
    """When C=1, runoff volume should be (rainfall_mm * area) / 1000."""
    runoff = RunoffVolume(
        rainfall_mm=20.0,  # mm
        contributing_area_m2=5000.0,  # m²
        runoff_coefficient=1.0,
        timestep_hours=1.0
    )
    expected = (20.0 * 5000.0) / 1000.0  # 100.0 m³
    assert runoff.volume_m3 == expected


def test_known_numerical_calculation():
    """Test a known calculation from the Rational Method."""
    # Example: C=0.3, i=25 mm/hr, A=2 ha (20000 m²), dt=1 hr
    # V = 0.3 * 25 * 20000 * 1 / 1000 = 150 m³
    runoff = RunoffVolume(
        rainfall_mm=25.0,
        contributing_area_m2=20000.0,
        runoff_coefficient=0.3,
        timestep_hours=1.0
    )
    expected = 0.3 * 25.0 * 20000.0 / 1000.0
    assert runoff.volume_m3 == expected


def test_validation_rejects_invalid_inputs():
    """Validation should reject negative rainfall, negative area, invalid C, non-positive timestep."""
    # Negative rainfall
    with pytest.raises(ValidationError):
        RunoffVolume(
            rainfall_mm=-1.0,
            contributing_area_m2=1000.0,
            runoff_coefficient=0.5,
            timestep_hours=1.0
        )

    # Negative area
    with pytest.raises(ValidationError):
        RunoffVolume(
            rainfall_mm=10.0,
            contributing_area_m2=-1.0,
            runoff_coefficient=0.5,
            timestep_hours=1.0
        )

    # Coefficient > 1
    with pytest.raises(ValidationError):
        RunoffVolume(
            rainfall_mm=10.0,
            contributing_area_m2=1000.0,
            runoff_coefficient=1.5,
            timestep_hours=1.0
        )

    # Coefficient < 0
    with pytest.raises(ValidationError):
        RunoffVolume(
            rainfall_mm=10.0,
            contributing_area_m2=1000.0,
            runoff_coefficient=-0.1,
            timestep_hours=1.0
        )

    # Zero timestep
    with pytest.raises(ValidationError):
        RunoffVolume(
            rainfall_mm=10.0,
            contributing_area_m2=1000.0,
            runoff_coefficient=0.5,
            timestep_hours=0.0
        )

    # Negative timestep
    with pytest.raises(ValidationError):
        RunoffVolume(
            rainfall_mm=10.0,
            contributing_area_m2=1000.0,
            runoff_coefficient=0.5,
            timestep_hours=-1.0
        )


def test_multiple_catchments_independence():
    """Runoff calculations for different catchments should be independent."""
    area1 = 1000.0
    area2 = 2000.0
    rainfall = 10.0
    C = 0.5
    dt = 1.0

    runoff1 = RunoffVolume(
        rainfall_mm=rainfall,
        contributing_area_m2=area1,
        runoff_coefficient=C,
        timestep_hours=dt
    )
    runoff2 = RunoffVolume(
        rainfall_mm=rainfall,
        contributing_area_m2=area2,
        runoff_coefficient=C,
        timestep_hours=dt
    )

    # Volumes should be proportional to area
    assert runoff1.volume_m3 == (C * rainfall * area1) / 1000.0
    assert runoff2.volume_m3 == (C * rainfall * area2) / 1000.0
    assert runoff2.volume_m3 == 2 * runoff1.volume_m3  # area2 is double area1


def test_conservation_of_total_runoff():
    """Total runoff from sub-catchments should equal runoff from combined catchment."""
    # Two sub-catchments
    area1 = 3000.0  # m²
    area2 = 2000.0  # m²
    total_area = area1 + area2
    rainfall = 15.0  # mm
    C = 0.4
    dt = 2.0  # hours

    runoff1 = RunoffVolume(
        rainfall_mm=rainfall,
        contributing_area_m2=area1,
        runoff_coefficient=C,
        timestep_hours=dt
    )
    runoff2 = RunoffVolume(
        rainfall_mm=rainfall,
        contributing_area_m2=area2,
        runoff_coefficient=C,
        timestep_hours=dt
    )
    combined = RunoffVolume(
        rainfall_mm=rainfall,
        contributing_area_m2=total_area,
        runoff_coefficient=C,
        timestep_hours=dt
    )

    # Due to linearity, the sum of parts should equal the whole
    assert abs((runoff1.volume_m3 + runoff2.volume_m3) - combined.volume_m3) < 1e-9