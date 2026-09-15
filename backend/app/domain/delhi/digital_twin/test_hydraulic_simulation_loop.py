"""Focused tests for the Phase 7D-4 multi-step simulation loop."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from backend.app.domain.delhi.digital_twin.hydraulic_simulation_loop import (
    run_simulation,
    validate_timesteps,
)
from backend.app.domain.delhi.digital_twin.hydraulic_time_state import (
    SimulationResultStatus,
    SimulationState,
    SimulationStateStatus,
    SimulationTimestep,
)
from backend.app.domain.delhi.digital_twin.hydraulic_time_stepper import (
    TimeStepFlowInputs,
)
from backend.app.domain.delhi.digital_twin.models import ProvenanceStatus

UTC = timezone.utc


def ts(i):
    """1-minute timestep starting at 06:0{i}."""
    return SimulationTimestep(
        start=datetime(2018, 7, 12, 6, i, tzinfo=UTC),
        end=datetime(2018, 7, 12, 6, i + 1, tzinfo=UTC),
    )


def make_state(**overrides):
    base = dict(
        timestamp=datetime(2018, 7, 12, 6, 0, tzinfo=UTC),
        location_id="N1",
        status=SimulationStateStatus.COMPUTED,
        storage_m3=100.0,
        provenance=ProvenanceStatus.DERIVED,
    )
    base.update(overrides)
    return SimulationState(**base)


def make_flows(inflow=2.0, outflow=1.0):
    return TimeStepFlowInputs(
        inflow_m3_s=inflow, lateral_inflow_m3_s=0.0, outflow_m3_s=outflow,
        inflow_provenance=ProvenanceStatus.DERIVED,
        lateral_inflow_provenance=ProvenanceStatus.OBSERVED,
        outflow_provenance=ProvenanceStatus.DERIVED,
    )


def test_two_step_successful_simulation():
    """Test 1: two-step successful simulation."""
    result = run_simulation(make_state(), [ts(0), ts(1)], make_flows())
    assert result.simulation_status == SimulationResultStatus.COMPLETE
    assert len(result.states) == 2
    # dt = 60 s, net +1 m3/s -> storage 100 -> 160 -> 220
    assert result.states[0].storage_m3 == pytest.approx(160.0)
    assert result.states[1].storage_m3 == pytest.approx(220.0)


def test_multiple_sequential_states():
    """Test 2: multiple sequential states, each chained from the last."""
    result = run_simulation(make_state(), [ts(0), ts(1), ts(2), ts(3)], make_flows())
    assert result.simulation_status == SimulationResultStatus.COMPLETE
    assert len(result.states) == 4
    assert [s.storage_m3 for s in result.states] == pytest.approx([160.0, 220.0, 280.0, 340.0])
    assert all(s.status == SimulationStateStatus.COMPUTED for s in result.states)


def test_chronological_timestamps():
    """Test 3: timestamps advance chronologically."""
    result = run_simulation(make_state(), [ts(0), ts(1), ts(2)], make_flows())
    stamps = [s.timestamp for s in result.states]
    assert stamps == sorted(stamps)
    assert all(a < b for a, b in zip(stamps, stamps[1:]))
    # Each state's timestamp is its timestep end.
    assert stamps[0] == ts(0).end
    assert stamps[1] == ts(1).end


def test_blocked_timestep_produces_partial():
    """Test 4: a blocked timestep stops safely with an explicit status."""
    # Step 1 drives storage negative -> blocked.
    flows = {
        0: make_flows(),
        1: make_flows(inflow=0.0, outflow=300.0),  # 160 - 60*300 < 0
        2: make_flows(),
    }
    result = run_simulation(make_state(), [ts(0), ts(1), ts(2)], flows)
    assert result.simulation_status == SimulationResultStatus.PARTIAL
    assert len(result.states) == 2  # step 2 never ran (no silent skip)
    assert result.states[0].status == SimulationStateStatus.COMPUTED
    assert result.states[1].status == SimulationStateStatus.BLOCKED_INVALID_INPUT
    assert any("not clipped" in d for d in result.diagnostics)


def test_successful_states_retained_before_blocked_step():
    """Test 5: successful states are retained before a blocked step."""
    # First step itself blocks -> BLOCKED with no computed states.
    result = run_simulation(
        make_state(storage_m3=None), [ts(0), ts(1)], make_flows()
    )
    assert result.simulation_status == SimulationResultStatus.BLOCKED
    assert len(result.states) == 1
    assert result.states[0].status == SimulationStateStatus.BLOCKED_MISSING_INPUT


def test_unknown_flow_remains_unknown():
    """Test 6: UNKNOWN (None) flow remains UNKNOWN, never zero."""
    result = run_simulation(
        make_state(), [ts(0)], make_flows(inflow=None)
    )
    assert result.simulation_status == SimulationResultStatus.BLOCKED
    assert result.states[0].status == SimulationStateStatus.BLOCKED_MISSING_INPUT
    assert result.states[0].storage_m3 is None
    # A missing per-step entry in a mapping is also UNKNOWN, not zero.
    result2 = run_simulation(make_state(), [ts(0), ts(1)], {1: make_flows()})
    assert result2.simulation_status == SimulationResultStatus.BLOCKED
    assert "No flow inputs supplied" in result2.states[0].diagnostic


def test_non_ordered_timestep_sequence():
    """Test 7: invalid/non-ordered timestep sequence is rejected."""
    result = run_simulation(make_state(), [ts(1), ts(0)], make_flows())
    assert result.simulation_status == SimulationResultStatus.BLOCKED
    assert len(result.states) == 0  # nothing ran
    assert "before previous end" in result.diagnostics[0]
    # validate_timesteps directly: overlap is also invalid.
    assert validate_timesteps([ts(0), ts(0)]) is not None
    assert validate_timesteps([ts(0), ts(1)]) is None


def test_inputs_not_mutated():
    """Test 8: input state and timesteps are not mutated."""
    state = make_state()
    timesteps = [ts(0), ts(1)]
    stamps_before = [(t.start, t.end) for t in timesteps]
    state_before = (state.timestamp, state.storage_m3, state.status)
    run_simulation(state, timesteps, make_flows())
    assert (state.timestamp, state.storage_m3, state.status) == state_before
    assert [(t.start, t.end) for t in timesteps] == stamps_before


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
