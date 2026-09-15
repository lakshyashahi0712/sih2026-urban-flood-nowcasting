"""Focused tests for the Phase 7D-7 hydraulic geometry input bundle."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from backend.app.domain.delhi.digital_twin.hydraulic_calculations import (
    HydraulicCalculationResult,
)
from backend.app.domain.delhi.digital_twin.hydraulic_geometry import (
    CrossSectionProfile,
    StationPoint,
)
from backend.app.domain.delhi.digital_twin.hydraulic_geometry_input import (
    HydraulicGeometryBundle,
    build_geometry_bundle,
    bundle_from_state,
)
from backend.app.domain.delhi.digital_twin.hydraulic_state_geometry import (
    StateGeometryResult,
    evaluate_state_geometry,
)
from backend.app.domain.delhi.digital_twin.hydraulic_time_state import (
    SimulationState,
    SimulationStateStatus,
)
from backend.app.domain.delhi.digital_twin.models import ProvenanceStatus

OBS = ProvenanceStatus.OBSERVED
UTC = timezone.utc


def rectangular():
    return CrossSectionProfile([
        StationPoint(-5.001, 104.0, OBS),
        StationPoint(-5.0, 100.0, OBS),
        StationPoint(5.0, 100.0, OBS),
        StationPoint(5.001, 104.0, OBS),
        StationPoint(10.0, 104.0, OBS),
    ], cross_section_id="rect")


def make_state(**overrides):
    base = dict(
        timestamp=datetime(2018, 7, 12, 6, 0, tzinfo=UTC),
        location_id="N1",
        status=SimulationStateStatus.COMPUTED,
        stage_m=102.0,
        provenance=ProvenanceStatus.DERIVED,
    )
    base.update(overrides)
    return SimulationState(**base)


def computed_result():
    """A computed StateGeometryResult (matching the rect profile at h=102)."""
    state = make_state()
    return evaluate_state_geometry(state, rectangular())


def test_valid_bundle():
    """Test 1: valid hydraulic geometry bundle from a computed evaluation."""
    result = computed_result()
    bundle = build_geometry_bundle(result, 102.0)
    assert bundle.status == "COMPUTED"
    assert bundle.is_valid
    assert bundle.stage_m == 102.0
    assert bundle.area_m2 is not None and bundle.perimeter_m is not None
    assert bundle.radius_m is not None
    assert bundle.diagnostic is not None


def test_apr_values_correct():
    """Test 2: correct A/P/R values (hand-checked, 7D-5/7D-6 conventions)."""
    bundle = build_geometry_bundle(computed_result(), 102.0)
    assert bundle.area_m2 == pytest.approx(20.0, abs=1e-2)
    assert bundle.perimeter_m == pytest.approx(14.0)
    assert bundle.radius_m == pytest.approx(20.0 / 14.0, rel=1e-3)
    # End-to-end convenience wrapper produces the same bundle.
    e2e = bundle_from_state(make_state(), rectangular())
    assert e2e.area_m2 == pytest.approx(bundle.area_m2, abs=1e-2)
    assert e2e.radius_m == pytest.approx(bundle.radius_m, rel=1e-3)


def test_unknown_stage():
    """Test 3: UNKNOWN stage yields an explicit blocked bundle."""
    bundle = bundle_from_state(make_state(stage_m=None), rectangular())
    assert bundle.status == "BLOCKED_MISSING_INPUT"
    assert not bundle.is_valid
    assert bundle.area_m2 is None and bundle.radius_m is None
    assert bundle.stage_m is None
    assert "UNKNOWN" in bundle.diagnostic


def test_unknown_geometry():
    """Test 4: UNKNOWN geometry preserves the blocked status."""
    bundle = bundle_from_state(
        make_state(), CrossSectionProfile([], cross_section_id="missing"))
    assert bundle.status == "BLOCKED_MISSING_GEOMETRY"
    assert not bundle.is_valid
    assert bundle.area_m2 is None
    assert bundle.geometry_provenance == ProvenanceStatus.UNKNOWN


def test_invalid_geometry_result():
    """Test 5: invalid/non-finite geometry results are rejected."""
    # Missing perimeter/radius on a nominally computed result.
    partial = StateGeometryResult(
        status="COMPUTED",
        area=HydraulicCalculationResult(status="COMPUTED", value=20.0),
    )
    bundle = build_geometry_bundle(partial, 102.0)
    assert bundle.status == "BLOCKED_MISSING_INPUT"
    assert "never inferred" in bundle.diagnostic
    # Non-physical (zero/negative/non-finite) values rejected.
    for bad in (0.0, -1.0, float("nan"), float("inf")):
        bad_area = StateGeometryResult(
            status="COMPUTED",
            area=HydraulicCalculationResult(status="COMPUTED", value=bad),
            perimeter=HydraulicCalculationResult(status="COMPUTED", value=14.0),
            radius=HydraulicCalculationResult(status="COMPUTED", value=1.0),
        )
        b = build_geometry_bundle(bad_area, 102.0)
        assert b.status == "BLOCKED_INVALID_INPUT"
        assert b.area_m2 is None and b.radius_m is None


def test_provenance_preservation():
    """Test 6: geometry provenance preserved on computed and blocked bundles."""
    bundle = build_geometry_bundle(computed_result(), 102.0)
    assert bundle.geometry_provenance == OBS
    mixed = CrossSectionProfile([
        StationPoint(-5.0, 100.0, OBS),
        StationPoint(5.0, 100.0, ProvenanceStatus.UNKNOWN),
    ])
    mixed_bundle = bundle_from_state(make_state(), mixed)
    assert mixed_bundle.geometry_provenance == ProvenanceStatus.UNKNOWN
    # A blocked bundle still carries the geometry provenance when known.
    low = bundle_from_state(make_state(stage_m=99.0), rectangular())
    assert low.status == "BLOCKED_INVALID_INPUT"
    assert low.geometry_provenance == OBS


def test_blocked_result_propagation():
    """Test 7: blocked upstream results propagate with status + diagnostic."""
    blocked = StateGeometryResult(
        status="BLOCKED_MISSING_GEOMETRY",
        diagnostic="geometry is UNKNOWN",
    )
    bundle = build_geometry_bundle(blocked, 102.0)
    assert bundle.status == "BLOCKED_MISSING_GEOMETRY"
    assert bundle.diagnostic == "geometry is UNKNOWN"
    assert bundle.area_m2 is None
    assert bundle.geometry_provenance == ProvenanceStatus.UNKNOWN
    # An upstream BLOCKED_INVALID_INPUT (e.g. stage below minimum) passes
    # through verbatim.
    low = bundle_from_state(make_state(stage_m=99.0), rectangular())
    assert low.status == "BLOCKED_INVALID_INPUT"
    assert low.diagnostic is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
