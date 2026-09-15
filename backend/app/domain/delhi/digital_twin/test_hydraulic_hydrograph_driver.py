"""Focused tests for Phase 7D-12 hydrograph-driven orchestration driver."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import List, Optional

import pytest

from backend.app.domain.delhi.digital_twin.hydraulic_geometry import (
    CrossSectionProfile,
    StationPoint,
)
from backend.app.domain.delhi.digital_twin.hydraulic_hydrograph_driver import (
    run_hydrograph_simulation,
)
from backend.app.domain.delhi.digital_twin.hydraulic_time_state import (
    HydrographTimeStep,
    InflowHydrograph,
    SimulationResultStatus,
    SimulationState,
    SimulationStateStatus,
    SimulationTimestep,
)
from backend.app.domain.delhi.digital_twin.models import ProvenanceStatus

UTC = timezone.utc
T0 = datetime(2018, 7, 12, 6, 0, tzinfo=UTC)
OBS = ProvenanceStatus.OBSERVED


def rectangular():
    """Fixture: 10m wide rectangular channel with near-vertical walls."""
    return CrossSectionProfile([
        StationPoint(-5.001, 104.0, OBS),
        StationPoint(-5.0, 100.0, OBS),
        StationPoint(5.0, 100.0, OBS),
        StationPoint(5.001, 104.0, OBS),
    ], cross_section_id="rect")


def make_state(timestamp=T0, stage=102.0, storage=10000.0, **overrides):
    """Fixture: standard simulation state."""
    base = dict(
        timestamp=timestamp,
        location_id="N1",
        status=SimulationStateStatus.COMPUTED,
        stage_m=stage,
        storage_m3=storage,
        provenance=ProvenanceStatus.DERIVED,
    )
    base.update(overrides)
    return SimulationState(**base)


def make_hydrograph(discharges: List[Optional[float]], start=T0, dt_sec=60):
    """Fixture: simple hydrograph."""
    steps = []
    for i, q in enumerate(discharges):
        steps.append(HydrographTimeStep(
            timestamp=start + timedelta(seconds=i * dt_sec),
            discharge_m3_s=q
        ))
    return InflowHydrograph(
        source_id="H1",
        steps=steps,
        provenance=OBS
    )


def ts(start, dt_sec=60):
    """Fixture: single timestep."""
    return SimulationTimestep(start=start, end=start + timedelta(seconds=dt_sec))


def test_two_step_hydrograph_produces_computed_states():
    """Test 1: two-step hydrograph produces two computed states."""
    hg = make_hydrograph([10.0, 15.0])
    # To run 2 steps, we need 2 SimulationTimestep objects.
    timesteps = [ts(T0), ts(T0 + timedelta(seconds=60))]

    result = run_hydrograph_simulation(
        initial_state=make_state(),
        timesteps=timesteps,
        hydrograph=hg,
        profile=rectangular(),
        manning_n=0.015,
        slope=0.005,
        explicit_outflow_m3_s=5.0,  # constant outflow
        lateral_inflow_m3_s=0.0,
    )

    assert result.simulation_status == SimulationResultStatus.COMPLETE
    assert len(result.states) == 2
    assert result.states[0].status == SimulationStateStatus.COMPUTED
    assert result.states[1].status == SimulationStateStatus.COMPUTED
    # Storage check: V1 = 10000 + 60*(10 - 5) = 10300
    # V2 = 10300 + 60*(15 - 5) = 10900
    assert result.states[0].storage_m3 == pytest.approx(10300.0)
    assert result.states[1].storage_m3 == pytest.approx(10900.0)


def test_hydrograph_inflow_used_exactly():
    """Test 2: hydrograph inflow is used exactly for each timestep."""
    # Step 0: Q=10. Step 1: Q=20.
    hg = make_hydrograph([10.0, 20.0])
    timesteps = [ts(T0), ts(T0 + timedelta(seconds=60))]

    result = run_hydrograph_simulation(
        initial_state=make_state(),
        timesteps=timesteps,
        hydrograph=hg,
        profile=rectangular(),
        manning_n=0.015,
        slope=0.005,
        explicit_outflow_m3_s=0.0,
        lateral_inflow_m3_s=0.0,
    )

    # Check diagnostics to prove Q_in came from hydrograph
    assert "10.0" in result.states[0].diagnostic
    assert "20.0" in result.states[1].diagnostic


def test_missing_hydrograph_discharge_blocks():
    """Test 3: missing discharge (None) blocks that timestep and does not become zero."""
    hg = make_hydrograph([10.0, None, 20.0])
    timesteps = [ts(T0), ts(T0 + timedelta(seconds=60)), ts(T0 + timedelta(seconds=120))]

    result = run_hydrograph_simulation(
        initial_state=make_state(),
        timesteps=timesteps,
        hydrograph=hg,
        profile=rectangular(),
        manning_n=0.015,
        slope=0.005,
        explicit_outflow_m3_s=0.0,
        lateral_inflow_m3_s=0.0,
    )

    # Stops at index 1
    assert result.simulation_status == SimulationResultStatus.PARTIAL
    assert len(result.states) == 2
    assert result.states[0].status == SimulationStateStatus.COMPUTED
    assert result.states[1].status == SimulationStateStatus.BLOCKED_MISSING_INPUT
    # The blocked diagnostic names the missing inflow input explicitly.
    assert "inflow" in result.states[1].diagnostic.lower()
    assert "UNKNOWN" in result.states[1].diagnostic


def test_stage_remains_explicit_never_inferred():
    """Test 4: stage remains explicit and is never inferred from Q."""
    # Even with huge Q, stage stays what the initial_state said (or what the sequence of states says).
    # Since we carry forward stage from current state to next state (in advance_state),
    # and we don't have a mechanism to update stage in this driver (no solver),
    # stage should remain constant if not modified externally between calls.
    hg = make_hydrograph([1000.0])
    timesteps = [ts(T0)]

    initial_stage = 102.5
    result = run_hydrograph_simulation(
        initial_state=make_state(stage=initial_stage),
        timesteps=timesteps,
        hydrograph=hg,
        profile=rectangular(),
        manning_n=0.015,
        slope=0.005,
        explicit_outflow_m3_s=0.0,
        lateral_inflow_m3_s=0.0,
    )

    assert result.states[0].status == SimulationStateStatus.COMPUTED
    assert result.states[0].stage_m == initial_stage
    # If it was inferred from Q=1000 (Manning), it would be much higher.


def test_capacity_as_outflow_requires_explicit_opt_in():
    """Test 5: capacity-as-outflow still requires explicit opt-in."""
    hg = make_hydrograph([10.0])
    timesteps = [ts(T0)]

    # 1. Default (False): outflow is explicit_outflow_m3_s
    res1 = run_hydrograph_simulation(
        initial_state=make_state(storage=10000.0),
        timesteps=timesteps,
        hydrograph=hg,
        profile=rectangular(),
        manning_n=0.015,
        slope=0.005,
        explicit_outflow_m3_s=5.0,
        use_capacity_as_outflow=False,
        lateral_inflow_m3_s=0.0,
    )
    # V = 10000 + 60*(10 - 5) = 10300
    assert res1.states[0].storage_m3 == pytest.approx(10300.0)

    # 2. Explicit opt-in (True): outflow is Manning capacity (~119.6)
    res2 = run_hydrograph_simulation(
        initial_state=make_state(storage=10000.0),
        timesteps=timesteps,
        hydrograph=hg,
        profile=rectangular(),
        manning_n=0.015,
        slope=0.005,
        use_capacity_as_outflow=True,
        lateral_inflow_m3_s=0.0,
    )
    # V = 10000 + 60*(10 - capacity); capacity ~= 119.6 for this profile
    # at stage 102, n=0.015, S=0.005.
    q_cap = res2.step_results[0].capacity.capacity_m3_s
    assert q_cap == pytest.approx(119.6, rel=1e-2)
    assert res2.states[0].storage_m3 == pytest.approx(10000.0 + 60.0 * (10.0 - q_cap))


def test_blocked_capacity_propagates_when_opted_in():
    """Test 6: blocked capacity propagates when capacity-as-outflow is enabled."""
    hg = make_hydrograph([10.0])
    timesteps = [ts(T0)]
    empty_profile = CrossSectionProfile([], cross_section_id="missing")

    result = run_hydrograph_simulation(
        initial_state=make_state(),
        timesteps=timesteps,
        hydrograph=hg,
        profile=empty_profile,
        manning_n=0.015,
        slope=0.005,
        use_capacity_as_outflow=True,
        lateral_inflow_m3_s=0.0,
    )

    assert result.simulation_status == SimulationResultStatus.BLOCKED
    # The capacity artifact is blocked on geometry; the timestep itself
    # blocks on the UNKNOWN outflow (SimulationStateStatus has no
    # geometry-specific status — continuity reports the missing input).
    assert result.step_results[0].capacity.status == "BLOCKED_MISSING_GEOMETRY"
    assert result.step_results[0].capacity.capacity_m3_s is None
    assert result.states[0].status == SimulationStateStatus.BLOCKED_MISSING_INPUT


def test_provenance_survives_multi_step():
    """Test 7: provenance survives across multiple timesteps."""
    hg = make_hydrograph([10.0, 15.0])
    timesteps = [ts(T0), ts(T0 + timedelta(seconds=60))]

    result = run_hydrograph_simulation(
        initial_state=make_state(),
        timesteps=timesteps,
        hydrograph=hg,
        profile=rectangular(),
        manning_n=0.015,
        slope=0.005,
        explicit_outflow_m3_s=5.0,
        explicit_outflow_provenance=ProvenanceStatus.OFFICIAL,
        lateral_inflow_m3_s=0.0,
        lateral_inflow_provenance=OBS,
    )

    # Input provenance: weakest of (OFFICIAL dt, DERIVED state, OBSERVED inflow, OFFICIAL outflow) = DERIVED
    # So next_state.diagnostic should contain "input provenance: DERIVED"
    assert "input provenance: DERIVED" in result.states[0].diagnostic
    assert "input provenance: DERIVED" in result.states[1].diagnostic


def test_inputs_remain_unchanged():
    """Test 8: inputs remain unchanged."""
    hg = make_hydrograph([10.0, 20.0])
    timesteps = [ts(T0), ts(T0 + timedelta(seconds=60))]
    profile = rectangular()
    state = make_state()

    hg_before = hg.model_dump()
    profile_points_before = [(p.station_m, p.elevation_m, p.provenance) for p in profile.points]
    state_before = state.model_dump()

    run_hydrograph_simulation(
        initial_state=state,
        timesteps=timesteps,
        hydrograph=hg,
        profile=profile,
        manning_n=0.015,
        slope=0.005,
        explicit_outflow_m3_s=0.0,
        lateral_inflow_m3_s=0.0,
    )

    assert hg.model_dump() == hg_before
    assert [(p.station_m, p.elevation_m, p.provenance) for p in profile.points] == profile_points_before
    assert state.model_dump() == state_before


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
