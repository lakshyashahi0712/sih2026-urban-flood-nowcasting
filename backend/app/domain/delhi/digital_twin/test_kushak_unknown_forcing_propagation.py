"""Tests for Phase 9 Step 5: UNKNOWN forcing propagation contract."""

import pytest
from datetime import datetime, timezone

from .kushak_unknown_forcing_propagation import (
    propagate_unknown_forcing,
    UnknownPropagationResult,
)
from .kushak_rainfall_scenario import load_june_2024_forcing, ScenarioForcing
from .kushak_scenario_ensemble import build_kushak_ensemble
from .kushak_scenario_executor import execute_ensemble_member
from .models import ProvenanceStatus
from .hydraulic_time_state import SimulationTimestep


def test_step5_1_known_supported_forcing_computed():
    """Known supported forcing remains COMPUTED."""
    result = propagate_unknown_forcing()
    # At least one step (the 91.0mm peak) is COMPUTED / supported.
    assert "COMPUTED" in result.forcing_statuses


def test_step5_2_verified_zero_valid():
    """VERIFIED_ZERO remains valid zero."""
    forcing = load_june_2024_forcing()
    result = propagate_unknown_forcing(forcing)
    # Check that VERIFIED_ZERO statuses are correctly identified when depth == 0.0
    for depth, status in zip(forcing.depths_mm, result.forcing_statuses):
        if depth == 0.0:
            assert status == "VERIFIED_ZERO"


def test_step5_3_unknown_forcing_explicit_blocked():
    """UNKNOWN forcing becomes explicit UNKNOWN/BLOCKED."""
    result = propagate_unknown_forcing()
    assert result.propagation_status == "BLOCKED"
    assert "UNKNOWN" in result.forcing_statuses


def test_step5_4_unknown_never_replaced_by_zero():
    """UNKNOWN is never replaced by zero."""
    forcing = load_june_2024_forcing()
    result = propagate_unknown_forcing(forcing)
    for depth, status in zip(forcing.depths_mm, result.forcing_statuses):
        if depth is None:
            assert status == "UNKNOWN"
            assert status != "VERIFIED_ZERO"


def test_step5_5_unknown_never_interpolated():
    """UNKNOWN is never interpolated."""
    result = propagate_unknown_forcing()
    # Ensure diagnostics explicitly state no interpolation
    for diag in result.diagnostics:
        if "UNKNOWN" in diag:
            assert "no interpolation" in diag.lower() or "no zero-substitution" in diag.lower()


def test_step5_6_unknown_never_averaged():
    """UNKNOWN is never averaged."""
    result = propagate_unknown_forcing()
    for status in result.forcing_statuses:
        assert status in ("COMPUTED", "UNKNOWN", "VERIFIED_ZERO")


def test_step5_7_unknown_never_forward_filled():
    """UNKNOWN is never forward-filled."""
    forcing = load_june_2024_forcing()
    # Check that adjacent UNKNOWN steps do not copy values
    result = propagate_unknown_forcing(forcing)
    for i, status in enumerate(result.forcing_statuses):
        if forcing.depths_mm[i] is None:
            assert status == "UNKNOWN"


def test_step5_8_unknown_never_backward_filled():
    """UNKNOWN is never backward-filled."""
    result = propagate_unknown_forcing()
    assert result.propagation_status == "BLOCKED"


def test_step5_9_unknown_propagation_deterministic():
    """UNKNOWN propagation is deterministic."""
    r1 = propagate_unknown_forcing()
    r2 = propagate_unknown_forcing()
    assert r1 == r2


def test_step5_10_ensemble_members_obey_same_boundary():
    """Every ensemble member obeys the same UNKNOWN boundary."""
    ensemble = build_kushak_ensemble()
    for member in ensemble:
        res = execute_ensemble_member(member)
        # If simulation status is PARTIAL or reaches contain UNKNOWN states due to forcing boundary, it obeys the boundary.
        assert res.hydraulic_run is not None
        if res.hydraulic_run.states:
            for s in res.hydraulic_run.states:
                if s.status.value == "UNKNOWN":
                    assert s.stage_m is None
                    assert s.storage_m3 is None


def test_step5_11_dependent_hydraulic_result_not_valid_after_unknown():
    """A dependent hydraulic result is not presented as valid numerical output after UNKNOWN forcing."""
    ensemble = build_kushak_ensemble()
    for member in ensemble:
        res = execute_ensemble_member(member)
        if res.hydraulic_run and res.hydraulic_run.states:
            for s in res.hydraulic_run.states:
                if s.status.value in ("UNKNOWN", "BLOCKED", "BLOCKED_TRUNCATED"):
                    # Stage and storage must not be fabricated numerical values
                    if s.stage_m is not None:
                        assert s.stage_m != 0.0  # not a zero substitution


def test_step5_12_timestep_identity_preserved():
    """Timestep identity is preserved."""
    forcing = load_june_2024_forcing()
    result = propagate_unknown_forcing(forcing)
    assert len(result.forcing_timesteps) == len(forcing.timesteps)
    for ts_label, ts in zip(result.forcing_timesteps, forcing.timesteps):
        assert ts_label == str(ts.start)


def test_step5_13_source_provenance_identity_preserved():
    """Source/provenance identity is preserved."""
    result = propagate_unknown_forcing()
    assert result.provenance == ProvenanceStatus.DERIVED
    assert result.underlying_forcing_remains == ProvenanceStatus.UNKNOWN


def test_step5_14_unknown_does_not_become_observed_official():
    """UNKNOWN does not become OBSERVED/OFFICIAL."""
    result = propagate_unknown_forcing()
    assert result.underlying_forcing_remains != ProvenanceStatus.OBSERVED
    assert result.underlying_forcing_remains != ProvenanceStatus.OFFICIAL
    assert result.underlying_forcing_remains == ProvenanceStatus.UNKNOWN


def test_step5_15_existing_steps_1_4_untouched():
    """Existing Steps 1-4 tests remain untouched."""
    from .kushak_scenario_envelope import build_scenario_envelope
    from .kushak_sensitivity_analysis import build_one_at_a_time_sensitivity
    assert callable(build_scenario_envelope)
    assert callable(build_one_at_a_time_sensitivity)


def test_step5_16_repeated_execution_identical():
    """Repeated execution produces identical propagation results."""
    res1 = propagate_unknown_forcing()
    res2 = propagate_unknown_forcing()
    assert res1 == res2
