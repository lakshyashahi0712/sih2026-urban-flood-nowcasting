"""Deterministic hydraulic calculation primitives for Phase 7A.

Provides fundamental hydraulic equations (Manning, hydraulic radius) with
explicit handling of missing or invalid inputs. No geometry assumptions
are made; callers must supply required parameters.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class HydraulicCalculationResult:
    """Result of a hydraulic calculation with status and diagnostic."""
    status: str  # "COMPUTED", "BLOCKED_MISSING_GEOMETRY", "BLOCKED_INVALID_INPUT"
    value: Optional[float] = None
    diagnostic: Optional[str] = None


@dataclass
class HydraulicRadiusInput:
    """Inputs for hydraulic radius calculation."""
    area: Optional[float] = None
    wetted_perimeter: Optional[float] = None


@dataclass
class ManningDischargeInput:
    """Inputs for Manning discharge calculation."""
    area: Optional[float] = None
    hydraulic_radius: Optional[float] = None
    slope: Optional[float] = None
    manning_n: Optional[float] = None


def calculate_hydraulic_radius(input: HydraulicRadiusInput) -> HydraulicCalculationResult:
    """Calculate hydraulic radius R = A / P.

    Args:
        input: HydraulicRadiusInput with area and wetted_perimeter.

    Returns:
        HydraulicCalculationResult with status and computed value or diagnostic.
    """
    # Check for missing inputs
    if input.area is None:
        return HydraulicCalculationResult(
            status="BLOCKED_MISSING_GEOMETRY",
            diagnostic="Missing cross-sectional area (A)"
        )
    if input.wetted_perimeter is None:
        return HydraulicCalculationResult(
            status="BLOCKED_MISSING_GEOMETRY",
            diagnostic="Missing wetted perimeter (P)"
        )

    # Validate numeric values
    if input.area <= 0:
        return HydraulicCalculationResult(
            status="BLOCKED_INVALID_INPUT",
            diagnostic="Cross-sectional area must be positive"
        )
    if input.wetted_perimeter <= 0:
        return HydraulicCalculationResult(
            status="BLOCKED_INVALID_INPUT",
            diagnostic="Wetted perimeter must be positive"
        )

    # Calculate hydraulic radius
    hydraulic_radius = input.area / input.wetted_perimeter
    return HydraulicCalculationResult(
        status="COMPUTED",
        value=hydraulic_radius
    )


def calculate_manning_discharge(input: ManningDischargeInput) -> HydraulicCalculationResult:
    """Calculate Manning discharge Q = (1/n) * A * R^(2/3) * S^(1/2).

    Args:
        input: ManningDischargeInput with area, hydraulic_radius, slope, and manning_n.

    Returns:
        HydraulicCalculationResult with status and computed value or diagnostic.
    """
    # Check for missing inputs
    if input.area is None:
        return HydraulicCalculationResult(
            status="BLOCKED_MISSING_GEOMETRY",
            diagnostic="Missing cross-sectional area (A)"
        )
    if input.hydraulic_radius is None:
        return HydraulicCalculationResult(
            status="BLOCKED_MISSING_GEOMETRY",
            diagnostic="Missing hydraulic radius (R)"
        )
    if input.slope is None:
        return HydraulicCalculationResult(
            status="BLOCKED_MISSING_GEOMETRY",
            diagnostic="Missing slope (S)"
        )
    if input.manning_n is None:
        return HydraulicCalculationResult(
            status="BLOCKED_MISSING_GEOMETRY",
            diagnostic="Missing Manning's roughness coefficient (n)"
        )

    # Validate numeric values
    if input.area <= 0:
        return HydraulicCalculationResult(
            status="BLOCKED_INVALID_INPUT",
            diagnostic="Cross-sectional area must be positive"
        )
    if input.hydraulic_radius <= 0:
        return HydraulicCalculationResult(
            status="BLOCKED_INVALID_INPUT",
            diagnostic="Hydraulic radius must be positive"
        )
    if input.slope < 0:
        return HydraulicCalculationResult(
            status="BLOCKED_INVALID_INPUT",
            diagnostic="Slope must be non-negative"
        )
    if input.manning_n <= 0:
        return HydraulicCalculationResult(
            status="BLOCKED_INVALID_INPUT",
            diagnostic="Manning's roughness coefficient must be positive"
        )

    # Calculate Manning discharge
    # Q = (1/n) * A * R^(2/3) * S^(1/2)
    try:
        term1 = 1.0 / input.manning_n
        term2 = input.area
        term3 = input.hydraulic_radius ** (2.0 / 3.0)
        term4 = input.slope ** 0.5
        discharge = term1 * term2 * term3 * term4
    except (OverflowError, ZeroDivisionError) as e:
        return HydraulicCalculationResult(
            status="BLOCKED_INVALID_INPUT",
            diagnostic=f"Numerical error in calculation: {str(e)}"
        )

    return HydraulicCalculationResult(
        status="COMPUTED",
        value=discharge
    )