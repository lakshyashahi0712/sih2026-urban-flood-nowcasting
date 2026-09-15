"""Focused tests for the Phase 7D-13 storage-stage relation contract."""

from __future__ import annotations

import pytest

from backend.app.domain.delhi.digital_twin.hydraulic_storage_stage import (
    StorageStagePair,
    StorageStageRelation,
)
from backend.app.domain.delhi.digital_twin.models import ProvenanceStatus

OBS = ProvenanceStatus.OBSERVED


def relation():
    """Fixture: hand-checkable table (monotonic storage).

    stage 100 -> 0 m3, stage 102 -> 200 m3, stage 104 -> 600 m3.
    """
    return StorageStageRelation([
        StorageStagePair(100.0, 0.0, OBS),
        StorageStagePair(102.0, 200.0, OBS),
        StorageStagePair(104.0, 600.0, OBS),
    ])


def test_valid_stage_to_storage():
    """Test 1: valid stage -> storage."""
    result = relation().stage_to_storage(102.0)
    assert result.status == "COMPUTED"
    assert result.value == pytest.approx(200.0)


def test_valid_storage_to_stage():
    """Test 2: valid storage -> stage."""
    result = relation().storage_to_stage(200.0)
    assert result.status == "COMPUTED"
    assert result.value == pytest.approx(102.0)


def test_deterministic_interpolation():
    """Test 3: interpolation is deterministic (same inputs, same output)."""
    rel = relation()
    r1 = rel.stage_to_storage(101.0)
    r2 = rel.stage_to_storage(101.0)
    assert r1.status == "COMPUTED"
    assert r1.value == pytest.approx(r2.value)
    # Hand-checked midpoint: 100 + (200-0)/2 = 100 m3 at stage 101.
    assert r1.value == pytest.approx(100.0)
    # Inverse direction midpoint: stage 103 -> between 200 and 600 -> 400.
    assert rel.stage_to_storage(103.0).value == pytest.approx(400.0)
    # Inverse: 400 m3 -> stage 103.
    inv = rel.storage_to_stage(400.0)
    assert inv.status == "COMPUTED"
    assert inv.value == pytest.approx(103.0)


def test_exact_endpoint_lookup():
    """Test 4: exact pair values return exactly the paired counterpart."""
    rel = relation()
    low = rel.stage_to_storage(100.0)
    assert low.status == "COMPUTED"
    assert low.value == pytest.approx(0.0)
    high = rel.stage_to_storage(104.0)
    assert high.status == "COMPUTED"
    assert high.value == pytest.approx(600.0)
    inv_low = rel.storage_to_stage(0.0)
    assert inv_low.status == "COMPUTED"
    assert inv_low.value == pytest.approx(100.0)
    inv_high = rel.storage_to_stage(600.0)
    assert inv_high.status == "COMPUTED"
    assert inv_high.value == pytest.approx(104.0)


def test_unknown_input_blocks():
    """Test 5: UNKNOWN (None) input blocks, never becomes zero."""
    rel = relation()
    for result in (rel.stage_to_storage(None), rel.storage_to_stage(None)):
        assert result.status == "BLOCKED_INVALID_INPUT"
        assert result.value is None
        assert "UNKNOWN" in result.diagnostic or "None" in result.diagnostic
    # An UNKNOWN (empty) relation blocks lookups explicitly.
    empty = StorageStageRelation([])
    for result in (empty.stage_to_storage(101.0), empty.storage_to_stage(50.0)):
        assert result.status == "BLOCKED_MISSING_GEOMETRY"
        assert result.value is None


def test_non_finite_input_blocks():
    """Test 6: non-finite input blocks."""
    rel = relation()
    for bad in (float("inf"), float("-inf"), float("nan")):
        assert rel.stage_to_storage(bad).status == "BLOCKED_INVALID_INPUT"
        assert rel.storage_to_stage(bad).status == "BLOCKED_INVALID_INPUT"
    # Negative stage/storage are physically invalid and block.
    assert rel.stage_to_storage(-1.0).status == "BLOCKED_INVALID_INPUT"
    assert rel.storage_to_stage(-1.0).status == "BLOCKED_INVALID_INPUT"
    # Non-numeric input blocks too (not fabricated).
    assert rel.stage_to_storage("102").status == "BLOCKED_INVALID_INPUT"


def test_outside_domain_blocks_no_extrapolation():
    """Test 7: outside-domain lookup blocks without extrapolation."""
    rel = relation()
    below = rel.stage_to_storage(99.0)
    assert below.status == "BLOCKED_INVALID_INPUT"
    assert below.value is None
    assert "outside" in below.diagnostic.lower()
    above = rel.stage_to_storage(105.0)
    assert above.status == "BLOCKED_INVALID_INPUT"
    assert "extrapolation" in above.diagnostic.lower()
    # Same for the inverse direction.
    assert rel.storage_to_stage(700.0).status == "BLOCKED_INVALID_INPUT"
    # A non-monotonic storage sequence makes the inverse ambiguous: block,
    # never guess a branch.
    weird = StorageStageRelation([
        StorageStagePair(100.0, 100.0),
        StorageStagePair(102.0, 50.0),
        StorageStagePair(104.0, 300.0),
    ])
    assert weird.stage_to_storage(101.0).status == "COMPUTED"  # forward is fine
    inv = weird.storage_to_stage(75.0)
    assert inv.status == "BLOCKED_INVALID_INPUT"
    assert "ambiguous" in inv.diagnostic.lower()


def test_provenance_preserved():
    """Test 8: provenance is preserved for the relation and results."""
    rel = relation()
    assert rel.provenance == OBS  # weakest of all OBSERVED pairs
    # Mixed provenance: weakest link wins, never upgraded.
    mixed = StorageStageRelation([
        StorageStagePair(100.0, 0.0, OBS),
        StorageStagePair(102.0, 200.0, ProvenanceStatus.ASSUMED),
    ])
    assert mixed.provenance == ProvenanceStatus.ASSUMED
    # Computed results surface the relation provenance in the diagnostic.
    result = relation().stage_to_storage(101.0)
    assert "OBSERVED" in result.diagnostic
    # A computed value is never claimed as observed data.
    assert result.status == "COMPUTED"


def test_inputs_not_mutated():
    """Test 9: relation objects are not mutated by lookups."""
    rel = relation()
    before = [(p.stage_m, p.storage_m3, p.provenance) for p in rel.pairs]
    prov_before = rel.provenance
    rel.stage_to_storage(101.0)
    rel.storage_to_stage(250.0)
    rel.stage_to_storage(None)
    rel.stage_to_storage(105.0)
    assert [(p.stage_m, p.storage_m3, p.provenance) for p in rel.pairs] == before
    assert rel.provenance == prov_before
    # Construction-time validation still rejects invalid tables.
    with pytest.raises(ValueError):
        StorageStageRelation([StorageStagePair(100.0, 0.0)])  # single pair
    with pytest.raises(ValueError):
        StorageStageRelation([
            StorageStagePair(102.0, 200.0),
            StorageStagePair(100.0, 0.0),
        ])  # backwards stages
    with pytest.raises(ValueError):
        StorageStagePair(float("nan"), 0.0)  # non-finite pair value


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
