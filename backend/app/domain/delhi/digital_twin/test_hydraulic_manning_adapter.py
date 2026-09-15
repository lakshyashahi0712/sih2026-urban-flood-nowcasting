"""Focused tests for the Phase 7D-8 Manning discharge adapter."""

from __future__ import annotations

import pytest

from backend.app.domain.delhi.digital_twin.hydraulic_manning_adapter import (
    ManningCapacityResult,
    calculate_capacity_from_bundle,
)
from backend.app.domain.delhi.digital_twin.hydraulic_geometry_input import (
    HydraulicGeometryBundle,
)
from backend.app.domain.delhi.digital_twin.models import ProvenanceStatus

OBS = ProvenanceStatus.OBSERVED


def make_bundle(**overrides):
    """Valid bundle factory."""
    base = dict(
        status="COMPUTED",
        stage_m=102.0,
        area_m2=20.0,
        perimeter_m=14.0,
        radius_m=20.0 / 14.0,
        geometry_provenance=OBS,
    )
    base.update(overrides)
    return HydraulicGeometryBundle(**base)


def test_valid_manning_calculation():
    """Test 1 & 2: Valid Manning calculation and hand-checked arithmetic."""
    bundle = make_bundle()
    # Q = (1/0.015) * 20 * (20/14)^(2/3) * (0.005)^0.5
    # R ≈ 1.42857 -> R^(2/3) ≈ 1.2684
    # S^0.5 ≈ 0.07071
    # Q ≈ 66.666 * 20 * 1.2684 * 0.07071 ≈ 119.58 m3/s
    res = calculate_capacity_from_bundle(
        bundle, n=0.015, slope=0.005,
        n_provenance=ProvenanceStatus.OFFICIAL,
        slope_provenance=ProvenanceStatus.OFFICIAL
    )
    assert res.status == "COMPUTED"
    assert res.capacity_m3_s == pytest.approx(119.58, rel=1e-3)


def test_blocked_geometry_propagation():
    """Test 3 & 10: UNKNOWN/Blocked geometry propagation."""
    blocked_bundle = make_bundle(status="BLOCKED_MISSING_GEOMETRY", area_m2=None)
    res = calculate_capacity_from_bundle(blocked_bundle, n=0.015, slope=0.005)
    assert res.status == "BLOCKED_MISSING_GEOMETRY"
    assert res.capacity_m3_s is None


def test_missing_inputs():
    """Test 4 & 5: Missing roughness or slope."""
    bundle = make_bundle()
    assert calculate_capacity_from_bundle(bundle, n=None, slope=0.005).status == "BLOCKED_MISSING_INPUT"
    assert calculate_capacity_from_bundle(bundle, n=0.015, slope=None).status == "BLOCKED_MISSING_INPUT"


def test_invalid_inputs():
    """Test 6, 7 & 8: Invalid roughness, slope, or non-finite inputs."""
    bundle = make_bundle()
    assert calculate_capacity_from_bundle(bundle, n=0, slope=0.005).status == "BLOCKED_INVALID_INPUT"
    assert calculate_capacity_from_bundle(bundle, n=-0.015, slope=0.005).status == "BLOCKED_INVALID_INPUT"
    assert calculate_capacity_from_bundle(bundle, n=0.015, slope=-0.005).status == "BLOCKED_INVALID_INPUT"
    assert calculate_capacity_from_bundle(bundle, n=float("nan"), slope=0.005).status == "BLOCKED_INVALID_INPUT"
    assert calculate_capacity_from_bundle(bundle, n=0.015, slope=float("inf")).status == "BLOCKED_INVALID_INPUT"


def test_provenance_preservation():
    """Test 9: Provenance preservation."""
    bundle = make_bundle(geometry_provenance=ProvenanceStatus.ASSUMED)
    res = calculate_capacity_from_bundle(
        bundle, n=0.015, slope=0.005,
        n_provenance=ProvenanceStatus.OFFICIAL,
        slope_provenance=ProvenanceStatus.PROVISIONAL
    )
    assert res.geometry_provenance == ProvenanceStatus.ASSUMED
    assert res.n_provenance == ProvenanceStatus.OFFICIAL
    assert res.slope_provenance == ProvenanceStatus.PROVISIONAL
    # The result itself is not claimed as OBSERVED.
    assert res.status == "COMPUTED"
