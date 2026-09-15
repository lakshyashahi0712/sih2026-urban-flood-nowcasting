"""Focused tests for the Phase 7D-11 hydraulic timestep orchestrator."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from backend.app.domain.delhi.digital_twin.hydraulic_geometry import (
    CrossSectionProfile,
    StationPoint,
)
from backend.app.domain.delhi.digital_twin.hydraulic_orchestrator import (
    advance_state_through_chain,
)
from backend.app.domain.delhi.digital_twin.hydraulic_time_state import (
    SimulationState,
    SimulationStateStatus,
    SimulationTimestep,
)
from backend.app.domain.delhi.digital_twin.models import ProvenanceStatus

OBS = ProvenanceStatus.OBSERVED
UTC = timezone.utc
T0 = datetime(2018, 7, 12, 6, 0, tzinfo=UTC)

# rect profile at stage 102: depth 2 m, width 10 m -> A ~= 20, P ~= 14,
# R ~= 20/14; Q = (1/0.015)*20*R^(2/3)*(0.005)^0.5 ~= 119.58 m3/s.
N = 0.015
S = 0.005


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
        timestamp=T0, location_id="N1",
        status=SimulationStateStatus.COMPUTED,
        stage_m=102.0, storage_m3=100.0,
        provenance=ProvenanceStatus.DERIVED,
    )
    base.update(overrides)
    return SimulationState(**base)


def ts(dt_seconds=60.0):
    return SimulationTimestep(start=T0, end=T0 + timedelta(seconds=dt_seconds))


def run_chain(**overrides):
    defaults = dict(
        state=make_state(), timestep=ts(), profile=rectangular(),
        manning_n=N, slope=S, inflow_m3_s=2.0,
    )
    defaults.update(overrides)
    return advance_state_through_chain(**defaults)


def test_known_state_profile_computes_geometry():
    """Test 1: known state + profile computes A/P/R through the chain."""
    result = run_chain()
    assert result.geometry is not None
    assert result.geometry.status == "COMPUTED"
    assert result.geometry.area.value == pytest.approx(20.0, abs=1e-2)
    assert result.geometry.perimeter.value == pytest.approx(14.0)
    assert result.bundle is not None
    assert result.bundle.status == "COMPUTED"
    assert result.bundle.stage_m == pytest.approx(102.0)
    assert result.bundle.area_m2 == pytest.approx(20.0, abs=1e-2)
    assert result.bundle.perimeter_m == pytest.approx(14.0)
    assert result.bundle.radius_m == pytest.approx(20.0 / 14.0, rel=1e-3)


def test_capacity_computed():
    """Test 2: Manning capacity is computed from the chain's bundle."""
    result = run_chain()
    assert result.capacity is not None
    assert result.capacity.status == "COMPUTED"
    q = result.capacity.capacity_m3_s
    assert q is not None
    # Hand-check: (1/0.015)*20.0*(20/14)^(2/3)*(0.005)^0.5 ~= 119.58
    assert q == pytest.approx(119.58, rel=1e-2)
    # It is a calculated/model capacity, never an observed discharge.
    assert "not an observed discharge" in result.capacity.diagnostic


def test_default_does_not_use_capacity_as_outflow():
    """Test 3: default (use_capacity_as_outflow=False) never uses capacity."""
    # Capacity is ~119.58 but the explicit outflow is 1.0: storage must
    # follow the EXPLICIT outflow, not the capacity.
    result = run_chain(
        explicit_outflow_m3_s=1.0, lateral_inflow_m3_s=0.0,
        inflow_provenance=OBS,
    )
    assert result.capacity.status == "COMPUTED"  # reported but NOT used
    assert result.next_state.status == SimulationStateStatus.COMPUTED
    assert result.next_state.storage_m3 == pytest.approx(100.0 + 60.0 * (2.0 - 1.0))
    # With no explicit outflow either, the timestep blocks — the computed
    # capacity is NOT silently substituted for it.
    result2 = run_chain(explicit_outflow_m3_s=None, lateral_inflow_m3_s=0.0)
    assert result2.capacity.status == "COMPUTED"
    assert result2.next_state.status == SimulationStateStatus.BLOCKED_MISSING_INPUT
    assert result2.next_state.storage_m3 is None


def test_explicit_capacity_as_outflow_advances_storage():
    """Test 4: explicit choice uses the computed capacity as Q_out."""
    # dt=10 so storage stays positive: 2000 + 10*(20 - Q) with Q ~= 119.58.
    result = run_chain(
        timestep=ts(10.0), state=make_state(storage_m3=2000.0),
        inflow_m3_s=20.0, use_capacity_as_outflow=True,
        inflow_provenance=OBS, lateral_inflow_m3_s=0.0,
    )
    q = result.capacity.capacity_m3_s
    assert q == pytest.approx(119.58, rel=1e-2)
    assert result.next_state.status == SimulationStateStatus.COMPUTED
    assert result.next_state.storage_m3 == pytest.approx(2000.0 + 10.0 * (20.0 - q))
    assert result.next_state.timestamp == ts(10.0).end


def test_blocked_geometry_blocks_timestep():
    """Test 5: UNKNOWN cross-section geometry blocks capacity and the timestep."""
    empty = CrossSectionProfile([], cross_section_id="missing")
    # With capacity-as-outflow explicitly chosen, the blocked geometry
    # propagates to the timestep (Q_out stays UNKNOWN, never zero).
    result = run_chain(
        profile=empty, use_capacity_as_outflow=True, inflow_m3_s=2.0,
        lateral_inflow_m3_s=0.0,
    )
    assert result.geometry.status == "BLOCKED_MISSING_GEOMETRY"
    assert result.bundle.status == "BLOCKED_MISSING_GEOMETRY"
    assert result.capacity.status == "BLOCKED_MISSING_GEOMETRY"
    assert result.capacity.capacity_m3_s is None
    assert result.next_state.status != SimulationStateStatus.COMPUTED
    assert result.next_state.storage_m3 is None
    # In the DEFAULT path with an explicit outflow, the blocked capacity is
    # informational: the timestep still advances on the explicit flows.
    result2 = run_chain(
        profile=empty, explicit_outflow_m3_s=1.0, lateral_inflow_m3_s=0.0,
    )
    assert result2.capacity.status == "BLOCKED_MISSING_GEOMETRY"
    assert result2.next_state.status == SimulationStateStatus.COMPUTED
    assert result2.next_state.storage_m3 == pytest.approx(160.0)


def test_unknown_stage_blocks_timestep():
    """Test 6: UNKNOWN (None) stage blocks capacity and the timestep."""
    # Stage is never inferred from discharge or any other source.
    result = run_chain(
        state=make_state(stage_m=None), use_capacity_as_outflow=True,
        inflow_m3_s=2.0, lateral_inflow_m3_s=0.0,
    )
    assert result.geometry.status == "BLOCKED_MISSING_INPUT"
    assert result.bundle.status == "BLOCKED_MISSING_INPUT"
    assert result.bundle.stage_m is None
    assert result.capacity.status == "BLOCKED_MISSING_INPUT"
    assert result.capacity.capacity_m3_s is None
    assert result.next_state.status != SimulationStateStatus.COMPUTED
    assert result.next_state.storage_m3 is None


def test_unknown_n_or_slope_blocks_capacity():
    """Test 7: UNKNOWN n/slope blocks capacity — no silent substitution."""
    for kwargs in ({"manning_n": None}, {"slope": None}):
        result = run_chain(**kwargs, lateral_inflow_m3_s=0.0)
        assert result.capacity.status == "BLOCKED_MISSING_INPUT"
        assert result.capacity.capacity_m3_s is None
        assert result.next_state.status == SimulationStateStatus.BLOCKED_MISSING_INPUT
        assert result.next_state.storage_m3 is None
        # Even with capacity-as-outflow explicitly chosen, a blocked
        # capacity leaves Q_out UNKNOWN — never zero.
        result2 = run_chain(**kwargs, use_capacity_as_outflow=True,
                            lateral_inflow_m3_s=0.0)
        assert result2.next_state.status == SimulationStateStatus.BLOCKED_MISSING_INPUT
        assert result2.next_state.storage_m3 is None


def test_provenance_survives_chain():
    """Test 8: provenance survives the full chain into the next state."""
    result = run_chain(
        explicit_outflow_m3_s=1.0, lateral_inflow_m3_s=0.0,
        inflow_provenance=OBS, lateral_inflow_provenance=OBS,
        explicit_outflow_provenance=OBS,
    )
    # Geometry provenance follows the profile (OBSERVED points).
    assert result.geometry.geometry_provenance == OBS
    assert result.bundle.geometry_provenance == OBS
    assert result.capacity.geometry_provenance == OBS
    assert result.capacity.n_provenance == ProvenanceStatus.ASSUMED
    # The stepper's diagnostic surfaces the combined input provenance
    # (weakest of OFFICIAL dt / DERIVED state / OBSERVED flows = DERIVED),
    # so input provenance survives the chain into the next state.
    assert result.next_state.diagnostic is not None
    assert "input provenance: DERIVED" in result.next_state.diagnostic


def test_inputs_not_mutated():
    """Test 9: SimulationState and CrossSectionProfile are not mutated."""
    state = make_state()
    profile = rectangular()
    state_before = (
        state.timestamp, state.location_id, state.stage_m, state.storage_m3,
        state.status, state.provenance, state.diagnostic,
    )
    points_before = [(p.station_m, p.elevation_m, p.provenance) for p in profile.points]
    run_chain(state=state, profile=profile)
    assert (
        state.timestamp, state.location_id, state.stage_m, state.storage_m3,
        state.status, state.provenance, state.diagnostic,
    ) == state_before
    assert [(p.station_m, p.elevation_m, p.provenance) for p in profile.points] == points_before


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
