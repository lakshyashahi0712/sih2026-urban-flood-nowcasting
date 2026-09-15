"""Focused tests for Phase 7D-14 storage->stage integration."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from backend.app.domain.delhi.digital_twin.hydraulic_storage_stage import (
    StorageStagePair,
    StorageStageRelation,
)
from backend.app.domain.delhi.digital_twin.hydraulic_stage_update import (
    with_stage_from_storage,
)
from backend.app.domain.delhi.digital_twin.hydraulic_time_state import (
    SimulationState,
    SimulationStateStatus,
)
from backend.app.domain.delhi.digital_twin.models import ProvenanceStatus

OBS = ProvenanceStatus.OBSERVED
UTC = timezone.utc
T0 = datetime(2018, 7, 12, 6, 0, tzinfo=UTC)


def relation():
    """Fixture: hand-checkable monotonic table.

    stage 100 -> 0 m3, stage 102 -> 200 m3, stage 104 -> 600 m3.
    """
    return StorageStageRelation([
        StorageStagePair(100.0, 0.0, OBS),
        StorageStagePair(102.0, 200.0, OBS),
        StorageStagePair(104.0, 600.0, OBS),
    ])


def make_state(**overrides):
    base = dict(
        timestamp=T0, location_id="N1",
        status=SimulationStateStatus.COMPUTED,
        stage_m=101.0, storage_m3=100.0,
        provenance=ProvenanceStatus.DERIVED,
    )
    base.update(overrides)
    return SimulationState(**base)


def ts():
    return None  # timestep optional; timestamp carried from state


def test_storage_to_stage_integration():
    """Test 1: next storage -> recomputed stage on the next state."""
    result = with_stage_from_storage(make_state(), 200.0, relation())
    assert result.next_state.status == SimulationStateStatus.COMPUTED
    assert result.next_state.stage_m == pytest.approx(102.0)
    assert result.next_state.storage_m3 == pytest.approx(200.0)
    assert result.lookup is not None
    assert result.lookup.status == "COMPUTED"


def test_exact_relation_endpoint():
    """Test 2: exact relation endpoints return exactly the paired stage."""
    result = with_stage_from_storage(make_state(), 600.0, relation())
    assert result.next_state.status == SimulationStateStatus.COMPUTED
    assert result.next_state.stage_m == pytest.approx(104.0)
    result2 = with_stage_from_storage(make_state(), 0.0, relation())
    assert result2.next_state.status == SimulationStateStatus.COMPUTED
    assert result2.next_state.stage_m == pytest.approx(100.0)


def test_interpolation():
    """Test 3: interpolation is deterministic (hand-checked)."""
    result = with_stage_from_storage(make_state(), 400.0, relation())
    assert result.next_state.status == SimulationStateStatus.COMPUTED
    assert result.next_state.stage_m == pytest.approx(103.0)


def test_unknown_storage_blocks():
    """Test 4: UNKNOWN (None) storage blocks, never becomes zero."""
    result = with_stage_from_storage(make_state(), None, relation())
    assert result.next_state.status == SimulationStateStatus.BLOCKED_MISSING_INPUT
    assert result.next_state.stage_m is None
    assert result.next_state.storage_m3 is None
    assert "UNKNOWN" in result.next_state.diagnostic


def test_unknown_relation_blocks():
    """Test 5: UNKNOWN (None or empty) relation blocks."""
    for rel in (None, StorageStageRelation([])):
        result = with_stage_from_storage(make_state(), 200.0, rel)
        assert result.next_state.status == SimulationStateStatus.BLOCKED_MISSING_INPUT
        assert result.next_state.stage_m is None
        assert "UNKNOWN" in result.next_state.diagnostic


def test_outside_domain_storage_blocks():
    """Test 6: outside-domain storage blocks without extrapolation."""
    result = with_stage_from_storage(make_state(), 700.0, relation())
    assert result.next_state.status == SimulationStateStatus.BLOCKED_INVALID_INPUT
    assert result.next_state.stage_m is None
    assert "outside" in result.next_state.diagnostic.lower()
    assert "extrapolation" in result.next_state.diagnostic.lower()


def test_derived_stage_provenance():
    """Test 7: recomputed stage is DERIVED, never OBSERVED."""
    result = with_stage_from_storage(make_state(), 200.0, relation())
    assert result.next_state.status == SimulationStateStatus.COMPUTED
    assert result.next_state.provenance == ProvenanceStatus.DERIVED
    # Even with an OBSERVED relation, the computed stage stays DERIVED.
    assert result.next_state.diagnostic is not None
    assert "OBSERVED" in result.next_state.diagnostic  # relation provenance surfaced


def test_inputs_not_mutated():
    """Test 8: input state and relation are not mutated."""
    state = make_state()
    rel = relation()
    state_before = (
        state.timestamp, state.location_id, state.status, state.stage_m,
        state.storage_m3, state.provenance, state.diagnostic,
    )
    pairs_before = [(p.stage_m, p.storage_m3, p.provenance) for p in rel.pairs]
    prov_before = rel.provenance
    with_stage_from_storage(state, 200.0, rel)
    with_stage_from_storage(state, None, rel)
    with_stage_from_storage(state, 700.0, rel)
    assert (
        state.timestamp, state.location_id, state.status, state.stage_m,
        state.storage_m3, state.provenance, state.diagnostic,
    ) == state_before
    assert [(p.stage_m, p.storage_m3, p.provenance) for p in rel.pairs] == pairs_before
    assert rel.provenance == prov_before


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
