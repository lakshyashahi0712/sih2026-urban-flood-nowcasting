"""Focused tests for the Phase 7D-17 rainfall-to-inflow model contract."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from backend.app.domain.delhi.digital_twin.rainfall_to_inflow import (
    rainfall_to_inflow,
)
from backend.app.domain.delhi.digital_twin.hydraulic_time_state import (
    SimulationTimestep,
)
from backend.app.domain.delhi.digital_twin.models import ProvenanceStatus

UTC = timezone.utc
T0 = datetime(2018, 7, 12, 6, 0, tzinfo=UTC)
OBS = ProvenanceStatus.OBSERVED
DERIVED = ProvenanceStatus.DERIVED


def ts_list(durations=(60.0,), count=1):
    """Fixture: consecutive SimulationTimesteps with given durations."""
    timesteps = []
    t = T0
    for i in range(count):
        dt = durations[i] if i < len(durations) else durations[-1]
        timesteps.append(SimulationTimestep(
            start=t, end=t + timedelta(seconds=dt)))
        t = timesteps[-1].end
    return timesteps


def test_zero_rainfall():
    """Explicit rainfall = 0 is valid and yields a computed Q = 0."""
    result = rainfall_to_inflow(
        timesteps=ts_list(),
        rainfall_depth_mm=[0.0],
        catchment_area_km2=5.0,
        runoff_coefficient=0.6,
        catchment_area_provenance=OBS,
        runoff_coefficient_provenance=OBS,
    )
    assert result.status == "COMPUTED"
    assert result.hydrograph is not None
    assert len(result.hydrograph.steps) == 1
    assert result.hydrograph.steps[0].discharge_m3_s == 0.0


def test_positive_rainfall():
    """Positive rainfall yields hand-checkable Q."""
    # Q = C * (P/1000) * (A_km2*1e6) / dt
    #   = 0.6 * (10/1000) * (5e6) / 60
    #   = 0.6 * 0.01 * 5e6 / 60 = 30000/60 = 500 m3/s
    result = rainfall_to_inflow(
        timesteps=ts_list(),
        rainfall_depth_mm=[10.0],
        catchment_area_km2=5.0,
        runoff_coefficient=0.6,
        catchment_area_provenance=OBS,
        runoff_coefficient_provenance=OBS,
    )
    assert result.status == "COMPUTED"
    q = result.hydrograph.steps[0].discharge_m3_s
    assert q == pytest.approx(500.0)
    # MODEL/DERIVED, never observed discharge.
    assert result.hydrograph.provenance == DERIVED
    assert "not an observed discharge" in result.diagnostics[-1]


def test_missing_rainfall():
    """None rainfall keeps that step's discharge None (never zero)."""
    result = rainfall_to_inflow(
        timesteps=ts_list(count=2),
        rainfall_depth_mm=[10.0, None],
        catchment_area_km2=5.0,
        runoff_coefficient=0.6,
    )
    assert result.status == "COMPUTED"
    steps = result.hydrograph.steps
    assert steps[0].discharge_m3_s == pytest.approx(500.0)
    # None is a preserved UNKNOWN, never zero, never interpolated.
    assert steps[1].discharge_m3_s is None
    assert any("UNKNOWN" in d for d in result.diagnostics)
    # The consumer contract preserves it: missing_step_count sees it.
    assert result.hydrograph.missing_step_count == 1


def test_invalid_area():
    """Invalid area blocks the whole conversion."""
    for bad in (None, 0.0, -1.0, float("nan"), float("inf"), "5"):
        result = rainfall_to_inflow(
            timesteps=ts_list(),
            rainfall_depth_mm=[10.0],
            catchment_area_km2=bad,
            runoff_coefficient=0.6,
        )
        assert result.status == "BLOCKED_INVALID_INPUT"
        assert result.hydrograph is None


def test_invalid_runoff_parameter():
    """Invalid runoff/loss parameter blocks the whole conversion."""
    for bad in (None, -0.1, 1.1, float("nan"), float("inf"), "0.6"):
        result = rainfall_to_inflow(
            timesteps=ts_list(),
            rainfall_depth_mm=[10.0],
            catchment_area_km2=5.0,
            runoff_coefficient=bad,
        )
        assert result.status == "BLOCKED_INVALID_INPUT"
        assert result.hydrograph is None


def test_timestep_duration_handling():
    """Timestep duration is preserved exactly per step (no assumed dt)."""
    # Two steps with different durations: 60 s and 300 s.
    # Q1 = 0.6 * 0.01 * 5e6 / 60 = 500; Q2 = 0.6*0.01*5e6/300 = 100.
    result = rainfall_to_inflow(
        timesteps=ts_list(durations=(60.0, 300.0), count=2),
        rainfall_depth_mm=[10.0, 10.0],
        catchment_area_km2=5.0,
        runoff_coefficient=0.6,
    )
    assert result.status == "COMPUTED"
    steps = result.hydrograph.steps
    assert steps[0].discharge_m3_s == pytest.approx(500.0)
    assert steps[1].discharge_m3_s == pytest.approx(100.0)
    # Timestamps are the timestep ends, in order.
    assert steps[0].timestamp == T0 + timedelta(seconds=60)
    assert steps[1].timestamp == T0 + timedelta(seconds=360)


def test_provenance():
    """Provenance: hydrograph DERIVED; parameter provenances surfaced."""
    result = rainfall_to_inflow(
        timesteps=ts_list(),
        rainfall_depth_mm=[10.0],
        catchment_area_km2=5.0,
        runoff_coefficient=0.6,
        catchment_area_provenance=OBS,
        runoff_coefficient_provenance=ProvenanceStatus.ASSUMED,
    )
    assert result.status == "COMPUTED"
    assert result.hydrograph.provenance == DERIVED
    # Parameter provenances are surfaced in the diagnostic (never
    # upgraded, never hard-coded).
    diag = result.diagnostics[-1]
    assert "OBSERVED" in diag
    assert "ASSUMED" in diag
    assert "not an observed discharge" in diag


def test_no_input_mutation():
    """Input timesteps and rainfall list are not mutated."""
    timesteps = ts_list(count=2)
    rainfall = [10.0, None]
    t_before = [(t.start, t.end) for t in timesteps]
    r_before = list(rainfall)
    rainfall_to_inflow(
        timesteps=timesteps,
        rainfall_depth_mm=rainfall,
        catchment_area_km2=5.0,
        runoff_coefficient=0.6,
    )
    assert [(t.start, t.end) for t in timesteps] == t_before
    assert rainfall == r_before


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
