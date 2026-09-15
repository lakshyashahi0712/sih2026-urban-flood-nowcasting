"""Focused tests for the Phase 7D-10 capacity-as-outflow adapter."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from backend.app.domain.delhi.digital_twin.hydraulic_capacity_outflow import (
    map_capacity_to_flows,
)
from backend.app.domain.delhi.digital_twin.hydraulic_manning_adapter import (
    ManningCapacityResult,
)
from backend.app.domain.delhi.digital_twin.hydraulic_time_state import (
    SimulationState,
    SimulationStateStatus,
    SimulationTimestep,
)
from backend.app.domain.delhi.digital_twin.hydraulic_time_stepper import (
    advance_state,
)
from backend.app.domain.delhi.digital_twin.models import ProvenanceStatus

UTC = timezone.utc
T0 = datetime(2018, 7, 12, 6, 0, tzinfo=UTC)


def computed_capacity(q=50.0):
    return ManningCapacityResult(
        status="COMPUTED",
        capacity_m3_s=q,
        geometry_provenance=ProvenanceStatus.OBSERVED,
        n_provenance=ProvenanceStatus.OFFICIAL,
        slope_provenance=ProvenanceStatus.ASSUMED,
    )


def make_state(**overrides):
    base = dict(
        timestamp=T0, location_id="N1",
        status=SimulationStateStatus.COMPUTED,
        storage_m3=100.0,
        provenance=ProvenanceStatus.DERIVED,
    )
    base.update(overrides)
    return SimulationState(**base)


def ts(dt_seconds=60.0):
    from datetime import timedelta
    return SimulationTimestep(start=T0, end=T0 + timedelta(seconds=dt_seconds))


def test_computed_capacity_used_as_outflow():
    """Test 1: computed capacity explicitly used as outflow."""
    flows = map_capacity_to_flows(
        computed_capacity(50.0), inflow_m3_s=20.0, lateral_inflow_m3_s=0.0,
        inflow_provenance=ProvenanceStatus.OBSERVED,
    )
    assert flows.outflow_m3_s == pytest.approx(50.0)
    nxt = advance_state(make_state(storage_m3=2000.0), ts(), flows)
    assert nxt.status == SimulationStateStatus.COMPUTED


def test_storage_decreases_from_outflow():
    """Test 2: storage decreases correctly from the capacity outflow."""
    # V_next = 100 + 60*(20 - 50) = 100 - 1800 < 0 -> blocked; use a
    # hand-checkable combination instead: V=2000, Q_in=20, Q_out=50.
    flows = map_capacity_to_flows(
        computed_capacity(50.0), inflow_m3_s=20.0, lateral_inflow_m3_s=0.0,
        inflow_provenance=ProvenanceStatus.OBSERVED,
    )
    nxt = advance_state(make_state(storage_m3=2000.0), ts(), flows)
    assert nxt.status == SimulationStateStatus.COMPUTED
    assert nxt.storage_m3 == pytest.approx(2000.0 + 60.0 * (20.0 - 50.0))
    assert nxt.storage_m3 == pytest.approx(200.0)


def test_blocked_capacity_stays_unknown():
    """Test 3: UNKNOWN/blocked capacity never becomes zero outflow."""
    blocked = ManningCapacityResult(
        status="BLOCKED_MISSING_GEOMETRY",
        capacity_m3_s=None,
        geometry_provenance=ProvenanceStatus.UNKNOWN,
    )
    flows = map_capacity_to_flows(blocked, inflow_m3_s=20.0, lateral_inflow_m3_s=0.0)
    assert flows.outflow_m3_s is None  # UNKNOWN, NOT 0.0
    nxt = advance_state(make_state(), ts(), flows)
    assert nxt.status == SimulationStateStatus.BLOCKED_MISSING_INPUT
    assert nxt.storage_m3 is None
    # A None capacity result behaves the same.
    flows3 = map_capacity_to_flows(
        ManningCapacityResult(status="BLOCKED_INVALID_INPUT"), inflow_m3_s=20.0, lateral_inflow_m3_s=0.0)
    assert flows3.outflow_m3_s is None


def test_explicit_zero_outflow_remains_zero():
    """Test 4: explicit zero outflow remains zero (distinct from UNKNOWN)."""
    flows = map_capacity_to_flows(
        computed_capacity(0.0), inflow_m3_s=20.0, lateral_inflow_m3_s=0.0,
        inflow_provenance=ProvenanceStatus.OBSERVED,
    )
    # A COMPUTED capacity of 0.0 is an explicit zero, not UNKNOWN.
    assert flows.outflow_m3_s == 0.0
    nxt = advance_state(make_state(), ts(), flows)
    assert nxt.status == SimulationStateStatus.COMPUTED
    assert nxt.storage_m3 == pytest.approx(100.0 + 60.0 * 20.0)


def test_capacity_provenance_preserved():
    """Test 5: capacity provenance is preserved and combined (weakest link)."""
    flows = map_capacity_to_flows(
        computed_capacity(50.0), inflow_m3_s=20.0, lateral_inflow_m3_s=0.0,
        inflow_provenance=ProvenanceStatus.OBSERVED,
        lateral_inflow_provenance=ProvenanceStatus.OBSERVED,
    )
    # Weakest of (OBSERVED geometry, OFFICIAL n, ASSUMED slope) = ASSUMED.
    assert flows.outflow_provenance == ProvenanceStatus.ASSUMED
    nxt = advance_state(make_state(storage_m3=2000.0), ts(), flows)
    # The outflow provenance is surfaced in the timestep diagnostic.
    assert nxt.diagnostic is not None
    assert "ASSUMED" in nxt.diagnostic


def test_no_automatic_capacity_outflow_conversion():
    """Test 6: no automatic capacity->outflow conversion."""
    # The adapter only sets Q_out when the caller passes the capacity
    # result; a caller who does not supply it gets UNKNOWN outflow.
    flows = map_capacity_to_flows(
        ManningCapacityResult(status="BLOCKED_MISSING_GEOMETRY"),
        inflow_m3_s=20.0,
    )
    assert flows.outflow_m3_s is None
    # And the adapter never invents a value: with no COMPUTED capacity the
    # outflow field stays None even though inflow is known.
    blocked = ManningCapacityResult(status="UNRESOLVED_FLOW_SPLIT")
    assert map_capacity_to_flows(blocked).outflow_m3_s is None
    # The distinction between Q_capacity and Q_out is structural: the
    # adapter copies capacity_m3_s into outflow_m3_s only on COMPUTED.
    cap = computed_capacity(50.0)
    flows2 = map_capacity_to_flows(cap)
    assert cap.capacity_m3_s == pytest.approx(50.0)
    assert flows2.outflow_m3_s == pytest.approx(50.0)


def test_existing_timestep_behavior_unchanged():
    """Test 7: existing timestep behavior remains unchanged."""
    # advance_state is reused directly; a plain TimeStepFlowInputs built
    # without the adapter behaves exactly as before (7D-3 tests).
    from backend.app.domain.delhi.digital_twin.hydraulic_time_stepper import (
        TimeStepFlowInputs,
    )
    flows = TimeStepFlowInputs(
        inflow_m3_s=2.0, lateral_inflow_m3_s=0.0, outflow_m3_s=1.0,
        inflow_provenance=ProvenanceStatus.DERIVED,
        lateral_inflow_provenance=ProvenanceStatus.OBSERVED,
        outflow_provenance=ProvenanceStatus.DERIVED,
    )
    nxt = advance_state(make_state(), ts(), flows)
    assert nxt.status == SimulationStateStatus.COMPUTED
    assert nxt.storage_m3 == pytest.approx(160.0)  # 100 + 60*(2-1)
    assert nxt.timestamp > T0
    # The adapter-produced inputs run through the same unmodified path.
    adapted = map_capacity_to_flows(
        computed_capacity(1.0), inflow_m3_s=2.0, lateral_inflow_m3_s=0.0,
        inflow_provenance=ProvenanceStatus.DERIVED,
    )
    nxt2 = advance_state(make_state(), ts(), adapted)
    assert nxt2.status == SimulationStateStatus.COMPUTED
    assert nxt2.storage_m3 == pytest.approx(160.0)  # same arithmetic


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
