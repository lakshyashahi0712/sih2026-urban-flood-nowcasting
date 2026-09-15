"""Focused tests for the Phase 7D-1 time-state / timestep contract."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from backend.app.domain.delhi.digital_twin.hydraulic_time_state import (
    HydrographTimeStep,
    InflowHydrograph,
    SimulationResult,
    SimulationResultStatus,
    SimulationState,
    SimulationStateStatus,
    SimulationTimestep,
)
from backend.app.domain.delhi.digital_twin.models import ProvenanceStatus

UTC = timezone.utc
T0 = datetime(2018, 7, 12, 6, 0, tzinfo=UTC)
T1 = datetime(2018, 7, 12, 6, 5, tzinfo=UTC)


def test_valid_timezone_aware_timestep():
    """Test 1: valid timezone-aware timestep."""
    ts = SimulationTimestep(start=T0, end=T1)
    assert ts.duration_seconds == 300.0


def test_naive_datetime_rejected():
    """Test 2: naive datetime rejected."""
    naive = datetime(2018, 7, 12, 6, 0)  # no tzinfo
    with pytest.raises(ValidationError, match="timezone-aware"):
        SimulationTimestep(start=naive, end=T1)
    with pytest.raises(ValidationError, match="timezone-aware"):
        SimulationState(timestamp=naive, location_id="N1")
    with pytest.raises(ValidationError, match="timezone-aware"):
        HydrographTimeStep(timestamp=naive)


def test_zero_timestep_rejected():
    """Test 3: zero-duration timestep rejected."""
    with pytest.raises(ValidationError, match="strictly after"):
        SimulationTimestep(start=T0, end=T0)


def test_negative_timestep_rejected():
    """Test 4: negative timestep rejected."""
    with pytest.raises(ValidationError, match="strictly after"):
        SimulationTimestep(start=T1, end=T0)


def test_backwards_time_hydrograph_rejected():
    """Test 5: backwards time in ordered structures rejected."""
    with pytest.raises(ValidationError, match="time-ordered"):
        InflowHydrograph(source_id="S1", steps=[
            HydrographTimeStep(timestamp=T1, discharge_m3_s=1.0),
            HydrographTimeStep(timestamp=T0, discharge_m3_s=2.0),
        ])


def test_valid_state_with_zero_storage():
    """Test 6: valid state with zero storage (distinct from UNKNOWN)."""
    state = SimulationState(
        timestamp=T0, location_id="N1", status=SimulationStateStatus.COMPUTED,
        storage_m3=0.0, provenance=ProvenanceStatus.DERIVED,
    )
    assert state.storage_m3 == 0.0


def test_unknown_storage_represented_as_none():
    """Test 7: UNKNOWN storage is None, not zero."""
    state = SimulationState(timestamp=T0, location_id="N1")
    assert state.storage_m3 is None
    assert SimulationState(timestamp=T0, location_id="N1", storage_m3=0.0).storage_m3 == 0.0
    # None and 0.0 must remain distinct.
    assert SimulationState(timestamp=T0, location_id="N1").storage_m3 is not 0.0


def test_negative_storage_rejected():
    """Test 8: invalid negative storage rejected."""
    with pytest.raises(ValidationError, match="non-negative"):
        SimulationState(timestamp=T0, location_id="N1", storage_m3=-1.0)


def test_valid_explicit_hydrograph():
    """Test 9: valid explicit hydrograph."""
    h = InflowHydrograph(source_id="S1", steps=[
        HydrographTimeStep(timestamp=T0, discharge_m3_s=10.0),
        HydrographTimeStep(timestamp=T1, discharge_m3_s=15.0),
    ])
    assert h.units == "m3/s"
    assert h.missing_step_count == 0


def test_hydrograph_unknown_discharge_preserved():
    """Test 10: UNKNOWN discharge preserved as None, not filled."""
    h = InflowHydrograph(source_id="S1", steps=[
        HydrographTimeStep(timestamp=T0, discharge_m3_s=10.0),
        HydrographTimeStep(timestamp=T1, discharge_m3_s=None),
    ])
    assert h.steps[1].discharge_m3_s is None
    assert h.missing_step_count == 1  # contract exposes the gap


def test_naive_hydrograph_timestamp_rejected():
    """Test 11: naive hydrograph timestamp rejected."""
    with pytest.raises(ValidationError, match="timezone-aware"):
        InflowHydrograph(source_id="S1", steps=[
            HydrographTimeStep(timestamp=datetime(2018, 7, 12, 6, 0))
        ])


def test_provenance_preserved():
    """Test 12: provenance preserved per quantity."""
    state = SimulationState(
        timestamp=T0, location_id="N1", status=SimulationStateStatus.COMPUTED,
        provenance=ProvenanceStatus.DERIVED,
    )
    assert state.provenance == ProvenanceStatus.DERIVED
    h = InflowHydrograph(source_id="S1", provenance=ProvenanceStatus.OBSERVED)
    assert h.provenance == ProvenanceStatus.OBSERVED
    # Distinct provenance classes are not collapsed into a boolean.
    assert ProvenanceStatus.DERIVED != ProvenanceStatus.OFFICIAL_MODEL_VALUE
    assert ProvenanceStatus.ASSUMED != ProvenanceStatus.UNKNOWN


def test_computed_state_cannot_be_observed():
    """Test 13: computed state cannot be labelled OBSERVED."""
    with pytest.raises(ValidationError, match="cannot be labelled OBSERVED"):
        SimulationState(
            timestamp=T0, location_id="N1", status=SimulationStateStatus.COMPUTED,
            provenance=ProvenanceStatus.OBSERVED,
        )


def test_blocked_simulation_result_explicit():
    """Test 14: blocked/partial simulation result represented explicitly."""
    blocked = SimulationResult(
        simulation_status=SimulationResultStatus.BLOCKED,
        diagnostics=["missing cross-section geometry"],
    )
    assert blocked.simulation_status == SimulationResultStatus.BLOCKED
    partial = SimulationResult(
        simulation_status=SimulationResultStatus.PARTIAL,
        states=[SimulationState(
            timestamp=T0, location_id="N1",
            status=SimulationStateStatus.BLOCKED_MISSING_INPUT,
            diagnostic="no A(h) available",
        )],
    )
    assert partial.simulation_status == SimulationResultStatus.PARTIAL
    assert partial.states[0].status == SimulationStateStatus.BLOCKED_MISSING_INPUT


def test_existing_7b_7c_tests_pass():
    """Test 15: existing Phase 7B/7C suite still passes (run via pytest)."""
    import subprocess
    import sys
    result = subprocess.run(
        [sys.executable, "-m", "pytest",
         "backend/app/domain/delhi/digital_twin/test_hydraulic_network_solver.py",
         "-q", "--no-header"],
        capture_output=True, text=True, timeout=120,
    )
    assert result.returncode == 0, result.stdout + result.stderr


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
