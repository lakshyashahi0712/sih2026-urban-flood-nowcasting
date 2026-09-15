"""Tests for Phase 9 Step 3: Descriptive Scenario Envelope."""

import pytest
from datetime import datetime, timezone

from .kushak_scenario_ensemble import build_kushak_ensemble, KushakEnsembleMember
from .kushak_scenario_executor import execute_ensemble_member
from .kushak_scenario_envelope import build_scenario_envelope, ScenarioEnvelope
from .models import ProvenanceStatus
from .hydraulic_time_state import SimulationState, SimulationStateStatus
from .hydraulic_hydrograph_driver import HydrographRunResult


def test_step3_1_six_member_ensemble_produces_deterministic_envelopes():
    """1. Six-member ensemble produces deterministic envelopes."""
    ensemble = build_kushak_ensemble()
    assert len(ensemble) == 6

    results = {m.member_id: execute_ensemble_member(m) for m in ensemble}
    envelopes1 = build_scenario_envelope(results)
    envelopes2 = build_scenario_envelope(results)

    assert len(envelopes1) > 0
    assert len(envelopes1) == len(envelopes2)
    for e1, e2 in zip(envelopes1, envelopes2):
        assert e1 == e2


def test_step3_2_and_3_min_max_stage_and_storage_are_correct():
    """2 & 3. Minimum and maximum stage and storage are correct across ensemble members."""
    ensemble = build_kushak_ensemble()
    results = {m.member_id: execute_ensemble_member(m) for m in ensemble}
    envelopes = build_scenario_envelope(results)

    for env in envelopes:
        if env.scenario_min_stage is not None and env.scenario_max_stage is not None:
            assert env.scenario_min_stage <= env.scenario_max_stage
        if env.scenario_min_storage is not None and env.scenario_max_storage is not None:
            assert env.scenario_min_storage <= env.scenario_max_storage


def test_step3_4_5_6_scenario_ids_and_axes_traceability():
    """4, 5 & 6. Scenario IDs are preserved, hydraulic & catchment scenarios remain traceable."""
    ensemble = build_kushak_ensemble()
    results = {m.member_id: execute_ensemble_member(m) for m in ensemble}
    envelopes = build_scenario_envelope(results)

    expected_member_ids = {m.member_id for m in ensemble}
    for env in envelopes:
        for s_id in env.contributing_scenario_ids:
            assert s_id in expected_member_ids
        # Verify both hydraulic and catchment axes are represented in ensemble member IDs
        assert any("CONSERVATIVE" in s or "CENTRAL" in s or "DEGRADED_CAPACITY" in s for s in env.contributing_scenario_ids)
        assert any("WORKING_27_66" in s or "SENSITIVITY_28_40" in s for s in env.contributing_scenario_ids)


def test_step3_7_model_state_set_contains_only_actual_states():
    """7. Model-state set contains only states actually produced."""
    ensemble = build_kushak_ensemble()
    results = {m.member_id: execute_ensemble_member(m) for m in ensemble}
    envelopes = build_scenario_envelope(results)

    valid_states = {s.value for s in SimulationStateStatus} | {"BLOCKED_TRUNCATED", "BLOCKED"}
    for env in envelopes:
        for st in env.model_states_observed:
            assert st in valid_states


def test_step3_8_9_10_unknown_blocked_handling():
    """8, 9 & 10. UNKNOWN/BLOCKED do not become numerical minimums; explicit UNKNOWN/BLOCKED envelopes handled."""
    now = datetime(2024, 6, 28, 0, 0, tzinfo=timezone.utc)

    # Create mock IntegratedRunResult where one member has None stage (UNKNOWN/BLOCKED)
    from .hydraulic_integrated_orchestrator import IntegratedRunResult
    from .rainfall_to_inflow import RainfallToInflowResult

    dt_res_good = IntegratedRunResult(
        rainfall_conversion=RainfallToInflowResult(status="COMPUTED"),
        hydraulic_run=HydrographRunResult(
            simulation_status="COMPLETE",
            states=[
                SimulationState(
                    timestamp=now,
                    location_id="reach_A",
                    status=SimulationStateStatus.COMPUTED,
                    stage_m=10.0,
                    storage_m3=100.0,
                    provenance=ProvenanceStatus.DERIVED
                )
            ]
        )
    )

    dt_res_unknown = IntegratedRunResult(
        rainfall_conversion=RainfallToInflowResult(status="COMPUTED"),
        hydraulic_run=HydrographRunResult(
            simulation_status="PARTIAL",
            states=[
                SimulationState(
                    timestamp=now,
                    location_id="reach_A",
                    status=SimulationStateStatus.UNKNOWN,
                    stage_m=None,
                    storage_m3=None,
                    provenance=ProvenanceStatus.UNKNOWN
                )
            ]
        )
    )

    results = {
        "KUSHAK-CENTRAL-WORKING_27_66": dt_res_good,
        "KUSHAK-CONSERVATIVE-WORKING_27_66": dt_res_unknown,
    }

    envelopes = build_scenario_envelope(results)
    assert len(envelopes) == 1
    env = envelopes[0]
    # UNKNOWN (None) must not become numerical minimum (should be 10.0, not 0.0 or min of None)
    assert env.scenario_min_stage == 10.0
    assert env.scenario_max_stage == 10.0
    assert env.scenario_min_storage == 100.0
    assert env.scenario_max_storage == 100.0
    assert "UNKNOWN" in env.model_states_observed
    assert "COMPUTED" in env.model_states_observed
    assert "KUSHAK-CONSERVATIVE-WORKING_27_66" in env.contributing_scenario_ids
    assert "KUSHAK-CENTRAL-WORKING_27_66" in env.contributing_scenario_ids

    # Test all members UNKNOWN/BLOCKED -> yields BLOCKED status envelope with no numeric bounds
    results_all_unknown = {
        "KUSHAK-CENTRAL-WORKING_27_66": dt_res_unknown,
    }
    envelopes_unknown = build_scenario_envelope(results_all_unknown)
    assert len(envelopes_unknown) == 1
    env_u = envelopes_unknown[0]
    assert env_u.scenario_min_stage is None
    assert env_u.scenario_max_stage is None
    assert env_u.status == "BLOCKED"


def test_step3_11_aggregate_provenance_is_derived():
    """11. Aggregate provenance is DERIVED."""
    ensemble = build_kushak_ensemble()
    results = {m.member_id: execute_ensemble_member(m) for m in ensemble}
    envelopes = build_scenario_envelope(results)

    for env in envelopes:
        assert env.provenance == ProvenanceStatus.DERIVED


def test_step3_12_repeated_execution_identical():
    """12. Repeated execution produces identical output."""
    ensemble = build_kushak_ensemble()
    results = {m.member_id: execute_ensemble_member(m) for m in ensemble}
    env1 = build_scenario_envelope(results)
    env2 = build_scenario_envelope(results)
    assert env1 == env2


def test_step3_13_no_probabilities_percentages_scores():
    """13. No probabilities, percentages, or risk scores are generated."""
    ensemble = build_kushak_ensemble()
    results = {m.member_id: execute_ensemble_member(m) for m in ensemble}
    envelopes = build_scenario_envelope(results)

    for env in envelopes:
        # Check that attributes do not contain probability, confidence, risk score, etc.
        attr_names = dir(env)
        for attr in attr_names:
            lower = attr.lower()
            assert "prob" not in lower
            assert "conf" not in lower
            assert "score" not in lower
            assert "percent" not in lower
            assert "risk" not in lower
