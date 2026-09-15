"""End-to-end integration tests: rainfall -> inflow -> hydraulic chain.

Connects the existing Phase 7D-17 rainfall_to_inflow conversion to the
Phase 7D-12 hydrograph driver (which drives the Phase 7D-11 orchestrator
chain). Synthetic/test-only cross-section geometry; no real Kushak
geometry or parameters. No calibration, GLUE, ML, routing enhancements,
or production integration.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from backend.app.domain.delhi.digital_twin.hydraulic_geometry import (
    CrossSectionProfile,
    StationPoint,
)
from backend.app.domain.delhi.digital_twin.hydraulic_hydrograph_driver import (
    run_hydrograph_simulation,
)
from backend.app.domain.delhi.digital_twin.hydraulic_time_state import (
    SimulationResultStatus,
    SimulationState,
    SimulationStateStatus,
    SimulationTimestep,
)
from backend.app.domain.delhi.digital_twin.rainfall_to_inflow import (
    rainfall_to_inflow,
)
from backend.app.domain.delhi.digital_twin.models import ProvenanceStatus

UTC = timezone.utc
T0 = datetime(2018, 7, 12, 6, 0, tzinfo=UTC)
OBS = ProvenanceStatus.OBSERVED

# Synthetic parameters (test-only, hand-checkable):
# Q = C * (P/1000) * (A_km2*1e6) / dt with C=0.6, A=5 km2, dt=60 s:
#   P=10 mm -> 500 m3/s;  P=0 mm -> 0.0 (valid zero).
C = 0.6
A_KM2 = 5.0


def ts_list(count=1, dt=60.0):
    """Consecutive SimulationTimesteps."""
    timesteps = []
    t = T0
    for _ in range(count):
        timesteps.append(SimulationTimestep(
            start=t, end=t + timedelta(seconds=dt)))
        t = timesteps[-1].end
    return timesteps


def synthetic_profile():
    """Synthetic 10 m wide rectangular channel (test-only geometry)."""
    return CrossSectionProfile([
        StationPoint(-5.001, 104.0, OBS),
        StationPoint(-5.0, 100.0, OBS),
        StationPoint(5.0, 100.0, OBS),
        StationPoint(5.001, 104.0, OBS),
    ], cross_section_id="synthetic-rect")


def make_state(storage=10000.0):
    return SimulationState(
        timestamp=T0, location_id="N1",
        status=SimulationStateStatus.COMPUTED,
        stage_m=102.0, storage_m3=storage,
        provenance=ProvenanceStatus.DERIVED,
    )


def run_chain(rainfall):
    """Full chain: rainfall -> Q(t) -> hydraulic states."""
    timesteps = ts_list(count=len(rainfall))
    converted = rainfall_to_inflow(
        timesteps=timesteps, rainfall_depth_mm=rainfall,
        catchment_area_km2=A_KM2, runoff_coefficient=C,
        catchment_area_provenance=OBS,
        runoff_coefficient_provenance=ProvenanceStatus.ASSUMED,
    )
    if converted.status != "COMPUTED":
        return converted, None
    result = run_hydrograph_simulation(
        initial_state=make_state(),
        timesteps=timesteps,
        hydrograph=converted.hydrograph,
        profile=synthetic_profile(),
        manning_n=0.015, slope=0.005,
        explicit_outflow_m3_s=0.0,
        lateral_inflow_m3_s=0.0,
        lateral_inflow_provenance=OBS,
    )
    return converted, result


def test_positive_rainfall_propagates_to_states():
    """Positive rainfall: values + provenance propagate to the states."""
    converted, result = run_chain([10.0, 10.0])
    assert converted.status == "COMPUTED"
    assert result.simulation_status == SimulationResultStatus.COMPLETE
    assert len(result.states) == 2
    # Rainfall value -> inflow value -> continuity arithmetic:
    # Q_in = 500 each step, Q_out = 0:
    # V1 = 10000 + 60*(500 - 0) = 40000; V2 = 40000 + 60*500 = 70000.
    assert result.states[0].storage_m3 == pytest.approx(40000.0)
    assert result.states[1].storage_m3 == pytest.approx(70000.0)
    # Inflow provenance (hydrograph DERIVED) survives into the states.
    for state in result.states:
        assert state.status == SimulationStateStatus.COMPUTED
        assert state.provenance == ProvenanceStatus.DERIVED
        assert state.diagnostic is not None
    # The inflow value used per step is visible in the continuity diagnostic.
    assert "500" in result.states[0].diagnostic


def test_missing_rainfall_blocks_not_zero():
    """Missing rainfall blocks that timestep, never becomes zero."""
    converted, result = run_chain([10.0, None])
    assert converted.status == "COMPUTED"  # partial hydrograph
    assert converted.hydrograph.steps[1].discharge_m3_s is None
    assert result.simulation_status == SimulationResultStatus.PARTIAL
    # Step 0 computed on the real inflow; step 1 blocked on UNKNOWN inflow.
    assert result.states[0].status == SimulationStateStatus.COMPUTED
    assert result.states[0].storage_m3 == pytest.approx(40000.0)
    assert result.states[1].status == SimulationStateStatus.BLOCKED_MISSING_INPUT
    assert result.states[1].storage_m3 is None


def test_zero_rainfall_remains_valid_zero():
    """Zero rainfall is a valid computed zero (Q=0), not a block."""
    converted, result = run_chain([0.0])
    assert converted.status == "COMPUTED"
    assert converted.hydrograph.steps[0].discharge_m3_s == 0.0
    assert result.simulation_status == SimulationResultStatus.COMPLETE
    assert result.states[0].status == SimulationStateStatus.COMPUTED
    # Q_in = 0, Q_out = 0: storage unchanged.
    assert result.states[0].storage_m3 == pytest.approx(10000.0)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
