"""Focused tests for the Phase 7D-5 cross-section geometry contract."""

from __future__ import annotations

import pytest

from backend.app.domain.delhi.digital_twin.hydraulic_geometry import (
    CrossSectionProfile,
    StationPoint,
    profile_provenance,
    provenanced_station,
)
from backend.app.domain.delhi.digital_twin.hydraulic_contract import ProvenancedValue
from backend.app.domain.delhi.digital_twin.models import ProvenanceStatus

OBS = ProvenanceStatus.OBSERVED


def rectangular():
    """Rectangular section: bed z=100 across ±5 m, near-vertical walls to
    z=104 (0.001 m station offset — vertical walls would need duplicate
    stations, which the contract rejects)."""
    return CrossSectionProfile([
        StationPoint(-5.001, 104.0, OBS),
        StationPoint(-5.0, 100.0, OBS),
        StationPoint(5.0, 100.0, OBS),
        StationPoint(5.001, 104.0, OBS),
        StationPoint(10.0, 104.0, OBS),
    ], cross_section_id="rect")


def test_valid_profile_creation():
    """Test 1: valid profile creation."""
    p = rectangular()
    assert p.has_geometry
    assert p.min_elevation_m == 100.0
    assert p.max_elevation_m == 104.0


def test_invalid_and_duplicate_stations():
    """Test 2: duplicate/backwards stations and non-finite values rejected."""
    with pytest.raises(ValueError, match="strictly increasing"):
        CrossSectionProfile([
            StationPoint(0.0, 104.0, OBS),
            StationPoint(5.0, 102.0, OBS),
            StationPoint(5.0, 100.0, OBS),  # duplicate station
        ])
    with pytest.raises(ValueError, match="strictly increasing"):
        CrossSectionProfile([
            StationPoint(5.0, 104.0, OBS),
            StationPoint(0.0, 100.0, OBS),  # backwards
        ])
    with pytest.raises(ValueError, match="finite"):
        StationPoint(float("nan"), 100.0, OBS)
    with pytest.raises(ValueError, match="finite"):
        StationPoint(0.0, float("inf"), OBS)


def test_insufficient_points():
    """Test 3: fewer than 2 points rejected (empty = UNKNOWN, allowed)."""
    with pytest.raises(ValueError, match="at least 2 points"):
        CrossSectionProfile([StationPoint(0.0, 100.0, OBS)])
    empty = CrossSectionProfile([])
    assert not empty.has_geometry


def test_rectangular_and_trapezoidal_area():
    """Test 4: rectangular/trapezoidal profile area (hand-checked)."""
    p = rectangular()
    # h = 102 -> depth 2 m, width 10 m -> A = 20 m² (near-vertical walls add
    # a negligible sliver; hand-checked to within 0.001 m²)
    assert p.wetted_area(102.0).status == "COMPUTED"
    assert p.wetted_area(102.0).value == pytest.approx(20.0, abs=1e-2)
    # h = 101 -> A = 10 m² (same wall sliver, same tolerance)
    assert p.wetted_area(101.0).value == pytest.approx(10.0, abs=1e-2)

    # Trapezoid: bed 4 m wide at z=100, banks rising to z=102 at ±4 m.
    trap = CrossSectionProfile([
        StationPoint(-4.0, 102.0, OBS),
        StationPoint(-2.0, 100.0, OBS),
        StationPoint(2.0, 100.0, OBS),
        StationPoint(4.0, 102.0, OBS),
    ])
    # h = 101: 2:1 side slopes -> top width 6, A = (4+6)/2*1 = 5 m²
    assert trap.wetted_area(101.0).value == pytest.approx(5.0)


def test_wetted_perimeter():
    """Test 5: wetted perimeter (hand-checked)."""
    p = rectangular()
    # h = 102: bed 10 m + two vertical walls of 2 m = 14 m
    assert p.wetted_perimeter(102.0).value == pytest.approx(14.0)
    # h = 101: bed 10 m + walls 1 m each = 12 m
    assert p.wetted_perimeter(101.0).value == pytest.approx(12.0)


def test_hydraulic_radius():
    """Test 6: hydraulic radius R = A/P (hand-checked)."""
    p = rectangular()
    r = p.hydraulic_radius(102.0)
    assert r.status == "COMPUTED"
    # A/P (near-vertical wall slope makes P a hair over 14 m; rel 1e-3)
    assert r.value == pytest.approx(20.0 / 14.0, rel=1e-3)


def test_water_level_below_minimum():
    """Test 7: water level below profile minimum is explicit, not zero."""
    p = rectangular()
    for query in (p.wetted_area(99.0), p.wetted_perimeter(99.0),
                  p.hydraulic_radius(99.0)):
        assert query.status == "BLOCKED_INVALID_INPUT"
        assert "below the profile minimum" in query.diagnostic


def test_unknown_or_insufficient_geometry():
    """Test 8: UNKNOWN/insufficient geometry returns explicit blocked results."""
    empty = CrossSectionProfile([])
    for query in (empty.wetted_area(102.0), empty.wetted_perimeter(102.0),
                  empty.hydraulic_radius(102.0)):
        assert query.status == "BLOCKED_MISSING_GEOMETRY"
        assert "UNKNOWN" in query.diagnostic
    p = rectangular()
    # Missing water level.
    assert p.wetted_area(None).status == "BLOCKED_MISSING_GEOMETRY"
    # Non-finite water level.
    assert p.wetted_area(float("nan")).status == "BLOCKED_INVALID_INPUT"


def test_provenance_preservation():
    """Test 9: provenance preserved per point and weakest-link per profile."""
    p = rectangular()
    assert profile_provenance(p) == OBS
    # One UNKNOWN point downgrades the whole profile.
    mixed = CrossSectionProfile([
        StationPoint(0.0, 104.0, OBS),
        StationPoint(5.0, 100.0, ProvenanceStatus.UNKNOWN),
    ])
    assert profile_provenance(mixed) == ProvenanceStatus.UNKNOWN
    assert profile_provenance(CrossSectionProfile([])) == ProvenanceStatus.UNKNOWN
    # provenanced_station propagates the weaker of the two values.
    sp = provenanced_station(
        ProvenancedValue(value=1.0, provenance=OBS),
        ProvenancedValue(value=100.0, provenance=ProvenanceStatus.OFFICIAL),
    )
    # OFFICIAL is weaker than OBSERVED in the ladder -> weaker wins.
    assert sp.provenance == ProvenanceStatus.OFFICIAL


def test_no_fabricated_geometry():
    """Test 10: no synthetic geometry from UNKNOWN values or assumptions."""
    # UNKNOWN ProvenancedValues cannot become geometry.
    with pytest.raises(ValueError, match="cannot become geometry"):
        provenanced_station(
            ProvenancedValue(value=None, provenance=ProvenanceStatus.UNKNOWN),
            ProvenancedValue(value=100.0, provenance=OBS),
        )
    # The profile stays UNKNOWN instead of assuming width/depth/DEM values.
    empty = CrossSectionProfile([])
    assert not empty.has_geometry
    assert empty.wetted_area(102.0).status == "BLOCKED_MISSING_GEOMETRY"
    # Interpolation happens only at the exact water-level crossing; the
    # trapezoid hand-check in test 4 (A = 5 m² exactly) verifies the
    # piecewise-linear interpretation is faithful to the supplied points.


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
