"""Integration tests for the consolidated rainfall-to-inflow-to-hydraulic chain."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from backend.app.domain.delhi.digital_twin.hydraulic_geometry import (
    CrossSectionProfile,
    StationPoint,
)
from backend.app.domain.delhi.digital_twin.hydraulic_integrated_orchestrator import (
    run_integrated_simulation,
)
from backend.app.domain.delhi.digital_twin.hydraulic_time_state import (
    SimulationResultStatus,
    SimulationState,
    SimulationStateStatus,
    SimulationTimestep,
)
from backend.app.domain.delhi.digital_twin.models import ProvenanceStatus

UTC = timezone.utc
T0 = datetime(2018, 7, 12, 6, 0, tzinfo=UTC)
OBS = ProvenanceStatus.OBSERVED
DERIVED = ProvenanceStatus.DERIVED

def ts_list(count=1, dt=60.0):
    timesteps = []
    t = T0
    for _ in range(count):
        timesteps.append(SimulationTimestep(
            start=t, end=t + timedelta(seconds=dt)))
        t = timesteps[-1].end
    return timesteps

def synthetic_profile():
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
        provenance=DERIVED,
    )

def test_full_integrated_chain():
    """Verify integrated rainfall -> inflow -> hydraulic chain."""
    rainfall = [10.0, 10.0]
    result = run_integrated_simulation(
        initial_state=make_state(),
        timesteps=ts_list(count=2),
        rainfall_depth_mm=rainfall,
        catchment_area_km2=5.0,
        runoff_coefficient=0.6,
        profile=synthetic_profile(),
        manning_n=0.015,
        slope=0.005,
        explicit_outflow_m3_s=0.0,
        lateral_inflow_m3_s=0.0,
        catchment_area_provenance=OBS,
        runoff_coefficient_provenance=ProvenanceStatus.ASSUMED,
    )
    assert result.rainfall_conversion.status == "COMPUTED"
    assert result.hydraulic_run.simulation_status == SimulationResultStatus.COMPLETE
    assert result.hydraulic_run.states[1].storage_m3 == pytest.approx(70000.0)

def test_missing_rainfall_blocks_integrated():
    """Missing rainfall blocks the integrated chain correctly."""
    rainfall = [10.0, None]
    result = run_integrated_simulation(
        initial_state=make_state(),
        timesteps=ts_list(count=2),
        rainfall_depth_mm=rainfall,
        catchment_area_km2=5.0,
        runoff_coefficient=0.6,
        profile=synthetic_profile(),
        manning_n=0.015,
        slope=0.005,
        explicit_outflow_m3_s=0.0,
        lateral_inflow_m3_s=0.0,
    )
    assert result.rainfall_conversion.status == "COMPUTED"
    # Debug:
    print(f"\nStates status: {[s.status for s in result.hydraulic_run.states]}")
    assert result.hydraulic_run.simulation_status == SimulationResultStatus.PARTIAL
    assert result.hydraulic_run.states[1].status == SimulationStateStatus.BLOCKED_MISSING_INPUT
    assert result.hydraulic_run.states[1].storage_m3 is None

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
