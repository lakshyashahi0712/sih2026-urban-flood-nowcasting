"""Unit tests for hydraulic calculation primitives."""

from __future__ import annotations

import pytest

from backend.app.domain.delhi.digital_twin.hydraulic_calculations import (
    HydraulicCalculationResult,
    HydraulicRadiusInput,
    ManningDischargeInput,
    calculate_hydraulic_radius,
    calculate_manning_discharge,
)


def test_hydraulic_radius_valid_inputs():
    """Test hydraulic radius calculation with valid inputs."""
    input_data = HydraulicRadiusInput(area=10.0, wetted_perimeter=5.0)
    result = calculate_hydraulic_radius(input_data)

    assert result.status == "COMPUTED"
    assert result.value == 2.0  # 10.0 / 5.0
    assert result.diagnostic is None


def test_hydraulic_radius_missing_area():
    """Test hydraulic radius calculation with missing area."""
    input_data = HydraulicRadiusInput(area=None, wetted_perimeter=5.0)
    result = calculate_hydraulic_radius(input_data)

    assert result.status == "BLOCKED_MISSING_GEOMETRY"
    assert "Missing cross-sectional area (A)" in result.diagnostic
    assert result.value is None


def test_hydraulic_radius_missing_perimeter():
    """Test hydraulic radius calculation with missing wetted perimeter."""
    input_data = HydraulicRadiusInput(area=10.0, wetted_perimeter=None)
    result = calculate_hydraulic_radius(input_data)

    assert result.status == "BLOCKED_MISSING_GEOMETRY"
    assert "Missing wetted perimeter (P)" in result.diagnostic
    assert result.value is None


def test_hydraulic_radius_zero_area():
    """Test hydraulic radius calculation with zero area."""
    input_data = HydraulicRadiusInput(area=0.0, wetted_perimeter=5.0)
    result = calculate_hydraulic_radius(input_data)

    assert result.status == "BLOCKED_INVALID_INPUT"
    assert "Cross-sectional area must be positive" in result.diagnostic
    assert result.value is None


def test_hydraulic_radius_negative_area():
    """Test hydraulic radius calculation with negative area."""
    input_data = HydraulicRadiusInput(area=-2.0, wetted_perimeter=5.0)
    result = calculate_hydraulic_radius(input_data)

    assert result.status == "BLOCKED_INVALID_INPUT"
    assert "Cross-sectional area must be positive" in result.diagnostic
    assert result.value is None


def test_hydraulic_radius_zero_perimeter():
    """Test hydraulic radius calculation with zero wetted perimeter."""
    input_data = HydraulicRadiusInput(area=10.0, wetted_perimeter=0.0)
    result = calculate_hydraulic_radius(input_data)

    assert result.status == "BLOCKED_INVALID_INPUT"
    assert "Wetted perimeter must be positive" in result.diagnostic
    assert result.value is None


def test_hydraulic_radius_negative_perimeter():
    """Test hydraulic radius calculation with negative wetted perimeter."""
    input_data = HydraulicRadiusInput(area=10.0, wetted_perimeter=-2.0)
    result = calculate_hydraulic_radius(input_data)

    assert result.status == "BLOCKED_INVALID_INPUT"
    assert "Wetted perimeter must be positive" in result.diagnostic
    assert result.value is None


def test_manning_discharge_valid_inputs():
    """Test Manning discharge calculation with valid inputs."""
    # Q = (1/n) * A * R^(2/3) * S^(1/2)
    # With A=4.0, R=2.0, S=0.01, n=0.02
    # Q = (1/0.02) * 4.0 * (2.0)^(2/3) * (0.01)^(1/2)
    # Q = 50 * 4.0 * 1.5874 * 0.1
    # Q = 50 * 4.0 * 0.15874 = 31.748
    input_data = ManningDischargeInput(
        area=4.0,
        hydraulic_radius=2.0,
        slope=0.01,
        manning_n=0.02
    )
    result = calculate_manning_discharge(input_data)

    assert result.status == "COMPUTED"
    assert result.value is not None
    # Expected value approximately 31.748
    assert abs(result.value - 31.748) < 0.001
    assert result.diagnostic is None


def test_manning_discharge_missing_area():
    """Test Manning discharge calculation with missing area."""
    input_data = ManningDischargeInput(
        area=None,
        hydraulic_radius=2.0,
        slope=0.01,
        manning_n=0.02
    )
    result = calculate_manning_discharge(input_data)

    assert result.status == "BLOCKED_MISSING_GEOMETRY"
    assert "Missing cross-sectional area (A)" in result.diagnostic
    assert result.value is None


def test_manning_discharge_missing_hydraulic_radius():
    """Test Manning discharge calculation with missing hydraulic radius."""
    input_data = ManningDischargeInput(
        area=4.0,
        hydraulic_radius=None,
        slope=0.01,
        manning_n=0.02
    )
    result = calculate_manning_discharge(input_data)

    assert result.status == "BLOCKED_MISSING_GEOMETRY"
    assert "Missing hydraulic radius (R)" in result.diagnostic
    assert result.value is None


def test_manning_discharge_missing_slope():
    """Test Manning discharge calculation with missing slope."""
    input_data = ManningDischargeInput(
        area=4.0,
        hydraulic_radius=2.0,
        slope=None,
        manning_n=0.02
    )
    result = calculate_manning_discharge(input_data)

    assert result.status == "BLOCKED_MISSING_GEOMETRY"
    assert "Missing slope (S)" in result.diagnostic
    assert result.value is None


def test_manning_discharge_missing_manning_n():
    """Test Manning discharge calculation with missing Manning's n."""
    input_data = ManningDischargeInput(
        area=4.0,
        hydraulic_radius=2.0,
        slope=0.01,
        manning_n=None
    )
    result = calculate_manning_discharge(input_data)

    assert result.status == "BLOCKED_MISSING_GEOMETRY"
    assert "Missing Manning's roughness coefficient (n)" in result.diagnostic
    assert result.value is None


def test_manning_discharge_negative_area():
    """Test Manning discharge calculation with negative area."""
    input_data = ManningDischargeInput(
        area=-4.0,
        hydraulic_radius=2.0,
        slope=0.01,
        manning_n=0.02
    )
    result = calculate_manning_discharge(input_data)

    assert result.status == "BLOCKED_INVALID_INPUT"
    assert "Cross-sectional area must be positive" in result.diagnostic
    assert result.value is None


def test_manning_discharge_zero_area():
    """Test Manning discharge calculation with zero area."""
    input_data = ManningDischargeInput(
        area=0.0,
        hydraulic_radius=2.0,
        slope=0.01,
        manning_n=0.02
    )
    result = calculate_manning_discharge(input_data)

    assert result.status == "BLOCKED_INVALID_INPUT"
    assert "Cross-sectional area must be positive" in result.diagnostic
    assert result.value is None


def test_manning_discharge_negative_hydraulic_radius():
    """Test Manning discharge calculation with negative hydraulic radius."""
    input_data = ManningDischargeInput(
        area=4.0,
        hydraulic_radius=-2.0,
        slope=0.01,
        manning_n=0.02
    )
    result = calculate_manning_discharge(input_data)

    assert result.status == "BLOCKED_INVALID_INPUT"
    assert "Hydraulic radius must be positive" in result.diagnostic
    assert result.value is None


def test_manning_discharge_zero_hydraulic_radius():
    """Test Manning discharge calculation with zero hydraulic radius."""
    input_data = ManningDischargeInput(
        area=4.0,
        hydraulic_radius=0.0,
        slope=0.01,
        manning_n=0.02
    )
    result = calculate_manning_discharge(input_data)

    assert result.status == "BLOCKED_INVALID_INPUT"
    assert "Hydraulic radius must be positive" in result.diagnostic
    assert result.value is None


def test_manning_discharge_negative_slope():
    """Test Manning discharge calculation with negative slope."""
    input_data = ManningDischargeInput(
        area=4.0,
        hydraulic_radius=2.0,
        slope=-0.01,
        manning_n=0.02
    )
    result = calculate_manning_discharge(input_data)

    assert result.status == "BLOCKED_INVALID_INPUT"
    assert "Slope must be non-negative" in result.diagnostic
    assert result.value is None


def test_manning_discharge_negative_manning_n():
    """Test Manning discharge calculation with negative Manning's n."""
    input_data = ManningDischargeInput(
        area=4.0,
        hydraulic_radius=2.0,
        slope=0.01,
        manning_n=-0.02
    )
    result = calculate_manning_discharge(input_data)

    assert result.status == "BLOCKED_INVALID_INPUT"
    assert "Manning's roughness coefficient must be positive" in result.diagnostic
    assert result.value is None


def test_manning_discharge_zero_manning_n():
    """Test Manning discharge calculation with zero Manning's n."""
    input_data = ManningDischargeInput(
        area=4.0,
        hydraulic_radius=2.0,
        slope=0.01,
        manning_n=0.0
    )
    result = calculate_manning_discharge(input_data)

    assert result.status == "BLOCKED_INVALID_INPUT"
    assert "Manning's roughness coefficient must be positive" in result.diagnostic
    assert result.value is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])