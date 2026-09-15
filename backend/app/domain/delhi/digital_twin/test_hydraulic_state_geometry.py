"""Focused tests for the Phase 7D-6 cross-section / state integration adapter."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from backend.app.domain.delhi.digital_twin.hydraulic_geometry import (
    CrossSectionProfile,
    StationPoint,
)
from backend.app.domain.delhi.digital_twin.hydraulic_state_geometry import (
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


def test_known_stage_known_profile():
    """Test 1: known stage + known profile computes."""
    result = evaluate_state_geometry(make_state(), rectangular())
    assert result.status == "COMPUTED"
    assert result.area is not None and result.perimeter is not None and result.radius is not None


def test_apr_values_correct():
    """Test 2: A/P/R values are returned correctly (hand-checked)."""
    result = evaluate_state_geometry(make_state(), rectangular())
    # h = 102 -> depth 2 m, width 10 m -> A = 20 m² (near-vertical wall
    # sliver, same tolerance as the geometry tests), P = 14 m, R = A/P.
    assert result.area.value == pytest.approx(20.0, abs=1e-2)
    assert result.perimeter.value == pytest.approx(14.0)
    assert result.radius.value == pytest.approx(20.0 / 14.0, rel=1e-3)
    # The underlying results keep the Phase 7A status semantics.
    assert result.area.status == "COMPUTED"
    assert result.perimeter.status == "COMPUTED"
    assert result.radius.status == "COMPUTED"


def test_unknown_stage():
    """Test 3: UNKNOWN (None) stage returns an explicit blocked result."""
    result = evaluate_state_geometry(make_state(stage_m=None), rectangular())
    assert result.status == "BLOCKED_MISSING_INPUT"
    assert result.area is None and result.radius is None
    assert "UNKNOWN" in result.diagnostic or "None" in result.diagnostic
    # Stage below the profile minimum also blocks explicitly.
    low = evaluate_state_geometry(make_state(stage_m=99.0), rectangular())
    assert low.status == "BLOCKED_INVALID_INPUT"


def test_unknown_cross_section():
    """Test 4: UNKNOWN cross-section preserves the blocked status."""
    empty = CrossSectionProfile([], cross_section_id="missing")
    result = evaluate_state_geometry(make_state(), empty)
    assert result.status == "BLOCKED_MISSING_GEOMETRY"
    assert result.area is None and result.radius is None


def test_provenance_preservation():
    """Test 5: geometry provenance is preserved and made available."""
    result = evaluate_state_geometry(make_state(), rectangular())
    assert result.geometry_provenance == OBS
    mixed = CrossSectionProfile([
        StationPoint(-5.0, 100.0, OBS),
        StationPoint(5.0, 100.0, ProvenanceStatus.UNKNOWN),
    ])
    result2 = evaluate_state_geometry(make_state(), mixed)
    assert result2.geometry_provenance == ProvenanceStatus.UNKNOWN
    # UNKNOWN geometry still reports UNKNOWN provenance.
    empty = CrossSectionProfile([])
    result3 = evaluate_state_geometry(make_state(), empty)
    assert result3.geometry_provenance == ProvenanceStatus.UNKNOWN


def test_inputs_not_mutated():
    """Test 6: SimulationState and CrossSectionProfile are not mutated."""
    state = make_state()
    profile = rectangular()
    state_before = (
        state.timestamp, state.stage_m, state.storage_m3, state.status,
        state.provenance, state.diagnostic,
    )
    points_before = [(p.station_m, p.elevation_m, p.provenance) for p in profile.points]
    evaluate_state_geometry(state, profile)
    assert (
        state.timestamp, state.stage_m, state.storage_m3, state.status,
        state.provenance, state.diagnostic,
    ) == state_before
    assert [(p.station_m, p.elevation_m, p.provenance) for p in profile.points] == points_before


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
