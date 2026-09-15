"""Focused tests for the Phase 7D-3 time-step execution wrapper."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from backend.app.domain.delhi.digital_twin.hydraulic_time_stepper import (
    TimeStepFlowInputs,
    advance_state,
)
from backend.app.domain.delhi.digital_twin.hydraulic_time_state import (
    SimulationState,
    SimulationStateStatus,
    SimulationTimestep,
)
from backend.app.domain.delhi.digital_twin.models import ProvenanceStatus

UTC = timezone.utc
T0 = datetime(2018, 7, 12, 6, 0, tzinfo=UTC)
T1 = datetime(2018, 7, 12, 6, 5, tzinfo=UTC)


def make_state(**overrides):
    base = dict(
        timestamp=T0, location_id="N1",
        status=SimulationStateStatus.COMPUTED,
        storage_m3=100.0,
        provenance=ProvenanceStatus.DERIVED,
    )
    base.update(overrides)
    return SimulationState(**base)


def make_flows(**overrides):
    base = dict(
        inflow_m3_s=2.0,
        lateral_inflow_m3_s=0.0,
        outflow_m3_s=1.0,
        inflow_provenance=ProvenanceStatus.DERIVED,
        lateral_inflow_provenance=ProvenanceStatus.OBSERVED,
        outflow_provenance=ProvenanceStatus.DERIVED,
    )
    base.update(overrides)
    return TimeStepFlowInputs(**base)


def test_successful_one_step_advance():
    """Test 1: successful one-step state advance."""
    nxt = advance_state(make_state(), SimulationTimestep(start=T0, end=T1), make_flows())
    assert nxt.status == SimulationStateStatus.COMPUTED
    # dt = 300 s -> 100 + 300*(2 + 0 - 1) = 400
    assert nxt.storage_m3 == pytest.approx(400.0)


def test_timestamp_advancement():
    """Test 2: next state advances to the timestep end."""
    nxt = advance_state(make_state(), SimulationTimestep(start=T0, end=T1), make_flows())
    assert nxt.timestamp == T1
    assert nxt.timestamp > make_state().timestamp


def test_storage_update():
    """Test 3: storage uses the continuity update (not duplicated)."""
    # dt = 60 s, V=100, Q_in=2, Q_lat=0, Q_out=1 -> 100 + 60*1 = 160
    ts = SimulationTimestep(
        start=T0, end=datetime(2018, 7, 12, 6, 1, tzinfo=UTC)
    )
    nxt = advance_state(make_state(), ts, make_flows())
    assert nxt.status == SimulationStateStatus.COMPUTED
    assert nxt.storage_m3 == pytest.approx(160.0)


def test_unknown_input_propagation():
    """Test 4: UNKNOWN (None) flow input blocks the next state."""
    nxt = advance_state(
        make_state(), SimulationTimestep(start=T0, end=T1),
        make_flows(inflow_m3_s=None),
    )
    assert nxt.status == SimulationStateStatus.BLOCKED_MISSING_INPUT
    assert nxt.storage_m3 is None
    assert nxt.timestamp == T1
    # UNKNOWN storage on the input state also blocks.
    nxt2 = advance_state(
        make_state(storage_m3=None), SimulationTimestep(start=T0, end=T1), make_flows()
    )
    assert nxt2.status == SimulationStateStatus.BLOCKED_MISSING_INPUT
    assert nxt2.storage_m3 is None


def test_invalid_continuity_result_propagation():
    """Test 5: failed continuity propagates as an explicit blocked state."""
    # Negative resulting storage: 10 + 60*(0-2) < 0.
    ts = SimulationTimestep(
        start=T0, end=datetime(2018, 7, 12, 6, 1, tzinfo=UTC)
    )
    nxt = advance_state(
        make_state(storage_m3=10.0), ts,
        make_flows(inflow_m3_s=0.0, lateral_inflow_m3_s=0.0, outflow_m3_s=2.0),
    )
    assert nxt.status == SimulationStateStatus.BLOCKED_INVALID_INPUT
    assert nxt.storage_m3 is None
    assert "not clipped to zero" in nxt.diagnostic


def test_input_state_not_mutated():
    """Test 6: the input state is not mutated."""
    state = make_state()
    before = (state.timestamp, state.storage_m3, state.status, state.provenance)
    advance_state(state, SimulationTimestep(start=T0, end=T1), make_flows())
    after = (state.timestamp, state.storage_m3, state.status, state.provenance)
    assert before == after


def test_provenance_preservation():
    """Test 7: computed storage is DERIVED, never OBSERVED."""
    nxt = advance_state(make_state(), SimulationTimestep(start=T0, end=T1), make_flows())
    assert nxt.provenance == ProvenanceStatus.DERIVED
    assert nxt.provenance != ProvenanceStatus.OBSERVED
    # A blocked state keeps UNKNOWN provenance.
    blocked = advance_state(
        make_state(), SimulationTimestep(start=T0, end=T1),
        make_flows(inflow_m3_s=None),
    )
    assert blocked.provenance == ProvenanceStatus.UNKNOWN


def test_diagnostic_propagation():
    """Test 8: diagnostics/mass-balance information is available."""
    nxt = advance_state(make_state(), SimulationTimestep(start=T0, end=T1), make_flows())
    # The continuity diagnostic (formula + result) plus combined input provenance.
    assert nxt.diagnostic is not None
    assert "V_next" in nxt.diagnostic
    assert "input provenance" in nxt.diagnostic
    blocked = advance_state(
        make_state(), SimulationTimestep(start=T0, end=T1),
        make_flows(inflow_m3_s=None),
    )
    assert blocked.diagnostic is not None
    assert "UNKNOWN" in blocked.diagnostic


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
