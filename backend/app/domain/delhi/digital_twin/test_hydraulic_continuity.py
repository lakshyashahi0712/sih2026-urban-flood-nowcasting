"""Focused tests for the Phase 7D-2 continuity/storage update."""

from __future__ import annotations

import pytest

from backend.app.domain.delhi.digital_twin.hydraulic_continuity import (
    ContinuityUpdateInput,
    compute_continuity_update,
)
from backend.app.domain.delhi.digital_twin.hydraulic_time_state import (
    SimulationStateStatus,
)
from backend.app.domain.delhi.digital_twin.models import ProvenanceStatus


def make_input(**overrides):
    base = dict(
        dt_seconds=10.0,
        storage_current_m3=100.0,
        inflow_m3_s=2.0,
        lateral_inflow_m3_s=0.0,
        outflow_m3_s=1.0,
        provenance={
            "dt": ProvenanceStatus.OBSERVED,
            "storage_current": ProvenanceStatus.OBSERVED,
            "inflow": ProvenanceStatus.DERIVED,
            "lateral_inflow": ProvenanceStatus.OBSERVED,
            "outflow": ProvenanceStatus.DERIVED,
        },
    )
    base.update(overrides)
    return ContinuityUpdateInput(**base)


def test_normal_storage_update():
    """Test 1: normal storage update."""
    r = compute_continuity_update(make_input())
    assert r.status == SimulationStateStatus.COMPUTED
    # V_next = 100 + 10*(2 + 0 - 1) = 110
    assert r.storage_next_m3 == pytest.approx(110.0)
    assert r.mass_balance_m3 == pytest.approx(10.0)


def test_zero_inflow():
    """Test 2: explicit zero inflow is valid and distinct from UNKNOWN."""
    r = compute_continuity_update(make_input(inflow_m3_s=0.0))
    assert r.status == SimulationStateStatus.COMPUTED
    assert r.storage_next_m3 == pytest.approx(100.0 + 10.0 * (0.0 - 1.0))


def test_multiple_inflows():
    """Test 3: multiple inflows sum into the update (caller combines)."""
    # Caller sums upstream inflows; combined inflow 3.0 + 1.5 = 4.5.
    r = compute_continuity_update(make_input(inflow_m3_s=3.0 + 1.5))
    assert r.status == SimulationStateStatus.COMPUTED
    assert r.storage_next_m3 == pytest.approx(100.0 + 10.0 * (4.5 - 1.0))


def test_outflow():
    """Test 4: outflow subtracts."""
    r = compute_continuity_update(make_input(outflow_m3_s=3.0))
    assert r.status == SimulationStateStatus.COMPUTED
    assert r.storage_next_m3 == pytest.approx(100.0 + 10.0 * (2.0 - 3.0))


def test_unknown_inflow():
    """Test 5: UNKNOWN (None) inflow is blocked, never treated as zero."""
    r = compute_continuity_update(make_input(inflow_m3_s=None))
    assert r.status == SimulationStateStatus.BLOCKED_MISSING_INPUT
    assert r.storage_next_m3 is None
    assert "UNKNOWN" in r.diagnostic


def test_unknown_outflow():
    """Test 6: UNKNOWN (None) outflow is blocked, never treated as zero."""
    r = compute_continuity_update(make_input(outflow_m3_s=None))
    assert r.status == SimulationStateStatus.BLOCKED_MISSING_INPUT
    assert r.storage_next_m3 is None


def test_negative_resulting_storage():
    """Test 7: negative resulting storage is an explicit failure, not clipped."""
    r = compute_continuity_update(
        make_input(storage_current_m3=5.0, inflow_m3_s=0.0,
                   lateral_inflow_m3_s=0.0, outflow_m3_s=2.0, dt_seconds=10.0)
    )
    # 5 + 10*(0 + 0 - 2) = -15
    assert r.status == SimulationStateStatus.BLOCKED_INVALID_INPUT
    assert r.storage_next_m3 is None
    assert "not clipped to zero" in r.diagnostic


def test_invalid_timestep():
    """Test 8: invalid (zero/negative/non-finite) timestep rejected."""
    for bad in (0.0, -5.0, float("nan"), float("inf")):
        r = compute_continuity_update(make_input(dt_seconds=bad))
        assert r.status == SimulationStateStatus.BLOCKED_INVALID_INPUT, bad
    r = compute_continuity_update(make_input(dt_seconds=None))
    assert r.status == SimulationStateStatus.BLOCKED_MISSING_INPUT


def test_provenance_preservation():
    """Test 9: computed storage is DERIVED; combined input provenance kept."""
    r = compute_continuity_update(make_input())
    assert r.provenance == ProvenanceStatus.DERIVED
    # Mixed inputs (OBSERVED + DERIVED) combine to the weakest: DERIVED.
    assert r.input_provenance == ProvenanceStatus.DERIVED
    # A single UNKNOWN input propagates UNKNOWN as the combined input provenance.
    r2 = compute_continuity_update(make_input(inflow_m3_s=1.0, provenance={
        "dt": ProvenanceStatus.OBSERVED, "storage_current": ProvenanceStatus.OBSERVED,
        "inflow": ProvenanceStatus.UNKNOWN, "lateral_inflow": ProvenanceStatus.OBSERVED,
        "outflow": ProvenanceStatus.DERIVED,
    }))
    # Note: inflow value is supplied here; only its provenance is UNKNOWN.
    assert r2.status == SimulationStateStatus.COMPUTED
    assert r2.input_provenance == ProvenanceStatus.UNKNOWN


def test_exact_mass_balance_arithmetic():
    """Test 10: exact mass-balance arithmetic, hand-checkable."""
    # 200 + 60*(5 + 2 - 4) = 200 + 180 = 380
    r = compute_continuity_update(make_input(
        dt_seconds=60.0, storage_current_m3=200.0,
        inflow_m3_s=5.0, lateral_inflow_m3_s=2.0, outflow_m3_s=4.0,
    ))
    assert r.status == SimulationStateStatus.COMPUTED
    assert r.mass_balance_m3 == pytest.approx(180.0)
    assert r.storage_next_m3 == pytest.approx(380.0)
    # Conservation identity: V_next - V = dt*(Qin + Qlat - Qout)
    assert (r.storage_next_m3 - 200.0) == pytest.approx(60.0 * (5.0 + 2.0 - 4.0))


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
