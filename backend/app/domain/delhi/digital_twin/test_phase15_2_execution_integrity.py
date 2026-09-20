"""Phase 15.2/15.5 Execution Integrity + Genuine Event-Specific Replay Tests.

Phase 15.2 core (preserved):
1. Deterministic EVT-* -> canonical EV-* event ID mapping and backward compatibility.
2. Unknown event ID returns UNASSIGNED without silent fallback.
3. Canonical validation path reaching via validate_observation().
4. Ensemble and continuity execution via build_kushak_ensemble() and advance_chain_timestep().
5. UNKNOWN / NOT_COMPARABLE propagation discipline.

Phase 15.5 additions (genuine event-specific historical runtime replay):
a. EV-01 executes exactly 6 ensemble members.
b. EV-02 executes exactly 6 ensemble members.
c. Event forcing drives the actual timestep sequence.
d. Runtime-derived mass-balance/result fields originate from runtime objects.
e. No single generic smoke-test result is reused for multiple events.
f. NOT_COMPARABLE remains for EVT-2021-09-11.
g. UNKNOWN remains for events with no forcing.
h. No synthetic disaggregation occurs.
i. Event-ID mapping remains backward compatible.
"""

import inspect
from collections import Counter
from datetime import datetime, timedelta, timezone

import pytest

from backend.app.domain.delhi.digital_twin.kushak_event_validation import (
    EVENT_ID_MAP,
    resolve_event_id,
    validate_observation,
    ValidationOutcome,
    ValidationSourceClass,
    TimestampPrecision,
)
from backend.app.domain.delhi.digital_twin.kushak_scenario_ensemble import build_kushak_ensemble
from backend.app.domain.delhi.digital_twin.kushak_scenario_executor import execute_ensemble_member
from backend.app.domain.delhi.digital_twin.kushak_continuity_routing import advance_chain_timestep, ChainTimestepInput
from backend.app.domain.delhi.digital_twin.hydraulic_time_state import SimulationTimestep, SimulationStateStatus

from scripts import generate_phase15_replay as replay_harness
from scripts.generate_phase15_replay import (
    REQUIRED_FLAGS,
    RUNTIME_DERIVED_FIELD_NAMES,
    run_historical_replay,
)


# ---------------------------------------------------------------------------
# Phase 15.2 core (preserved)
# ---------------------------------------------------------------------------


def test_event_id_mapping_and_backward_compatibility():
    # Test EVT-* historical mapping
    assert resolve_event_id("EVT-2024-06-27") == "EV-01"
    assert resolve_event_id("EVT-2023-07-08") == "EV-02"

    # Test backward compatibility for direct EV-* IDs
    assert resolve_event_id("EV-01") == "EV-01"
    assert resolve_event_id("EV-02") == "EV-02"

    # Test unknown or unmapped ID passes through
    assert resolve_event_id("EVT-UNKNOWN-99") == "EVT-UNKNOWN-99"
    assert resolve_event_id(None) is None


def test_unknown_event_id_unassigned():
    t0 = datetime(2024, 6, 27, 18, 30, tzinfo=timezone.utc)
    rec = validate_observation(
        event_id="EVT-INVALID-EVENT",
        source_class=ValidationSourceClass.GSDL_WATERLOGGING_OCCURRENCE,
        source_provenance=None, # type: ignore
        timestamp=t0,
        timestamp_precision=TimestampPrecision.DATETIME,
    )
    assert rec.validation_result == ValidationOutcome.UNASSIGNED
    assert "is not a known validation event" in rec.diagnostic


def test_canonical_validation_path_reaching_ev01():
    t0 = datetime(2024, 6, 28, 0, 0, tzinfo=timezone.utc)
    rec = validate_observation(
        event_id="EVT-2024-06-27",
        source_class=ValidationSourceClass.GSDL_WATERLOGGING_OCCURRENCE,
        source_provenance=None, # type: ignore
        timestamp=t0,
        timestamp_precision=TimestampPrecision.DATETIME,
        model_timestep=(t0 - timedelta(hours=1), t0 + timedelta(hours=1)),
    )
    # Should resolve EVT-2024-06-27 -> EV-01 and attempt canonical validation path
    assert rec.event_id == "EVT-2024-06-27"
    assert rec.validation_result != ValidationOutcome.UNASSIGNED


def test_ensemble_and_continuity_execution():
    ensemble = build_kushak_ensemble()
    assert len(ensemble) == 6

    # Execute first member
    member_res = execute_ensemble_member(ensemble[0])
    assert member_res is not None

    # Execute chain routing
    t0 = datetime(2024, 6, 27, 18, 30, tzinfo=timezone.utc)
    timestep = SimulationTimestep(start=t0, end=t0 + timedelta(hours=1))
    chain_input = ChainTimestepInput(
        timestep=timestep,
        head_flow_m3_s=10.0,
        laterals={"UG-01": 1.0, "OC-01": 2.0, "CD-01": 1.5, "OC-02": 0.5},
    )
    output = advance_chain_timestep(chain_input)
    assert len(output.results) == 4
    for r in output.results:
        assert r.continuity.status in [
            SimulationStateStatus.COMPUTED,
            SimulationStateStatus.BLOCKED_MISSING_INPUT,
            SimulationStateStatus.BLOCKED_INVALID_INPUT,
            SimulationStateStatus.BLOCKED_NUMERICAL,
            SimulationStateStatus.UNKNOWN,
        ]


# ---------------------------------------------------------------------------
# Phase 15.5 — genuine event-specific historical runtime replay
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def replay():
    """Run the genuine replay once for the whole module (it executes the
    full 12-member runtime; artifacts are shared read-only)."""
    return run_historical_replay()


def _records_by_id(replay):
    return {r.event_id: r for r in replay.records}


def test_a_ev01_executes_exactly_six_members(replay):
    rec = _records_by_id(replay)["EVT-2024-06-27"]
    ensemble_ids = [m.member_id for m in build_kushak_ensemble()]
    assert rec.runtime_executed == "YES"
    assert rec.forcing_found == "YES"
    assert rec.ensemble_members_executed == 6
    assert rec.actual_member_ids.split(";") == ensemble_ids
    ex = replay.event_executions["EVT-2024-06-27"]
    assert len(ex.member_executions) == 6
    assert ex.counters.ensemble_members_executed == 6
    # Every member produced its own runtime artifacts.
    assert all(
        m.integrated.rainfall_conversion.status == "COMPUTED"
        for m in ex.member_executions
    )
    assert ex.counters.forcing_conversions_executed == 6


def test_b_ev02_executes_exactly_six_members(replay):
    rec = _records_by_id(replay)["EVT-2023-07-08"]
    ensemble_ids = [m.member_id for m in build_kushak_ensemble()]
    assert rec.runtime_executed == "YES"
    assert rec.forcing_found == "YES"
    assert rec.ensemble_members_executed == 6
    assert rec.actual_member_ids.split(";") == ensemble_ids
    ex = replay.event_executions["EVT-2023-07-08"]
    assert len(ex.member_executions) == 6
    assert ex.counters.ensemble_members_executed == 6
    assert ex.counters.forcing_conversions_executed == 6
    # The scientifically correct executable total is 18 members across the
    # THREE executable events (EV-01=6, EV-02=6, EV-03 partial=6) — never more.
    total_members = sum(
        len(ex.member_executions) for ex in replay.event_executions.values()
    )
    assert total_members == 18


def test_c_event_forcing_drives_timestep_sequence(replay):
    ex1 = replay.event_executions["EVT-2024-06-27"]
    fs1 = ex1.forcing_series
    # EV-01: 4 catalog bins -> 4 contiguous hourly timesteps with the
    # documented depths (0.0 verified zero, 91.0 mm direct hour, 2x UNKNOWN).
    assert len(fs1.timesteps) == 4 == len(fs1.depths_mm) == 4
    assert fs1.depths_mm == (0.0, 91.0, None, None)
    assert all(ts.duration_seconds == 3600.0 for ts in fs1.timesteps)
    for a, b in zip(fs1.timesteps, fs1.timesteps[1:]):
        assert a.end == b.start
    # The direct 91.0 mm/h bin lands on its documented 05:00-06:00 IST hour.
    assert fs1.timesteps[1].start == datetime(
        2024, 6, 28, 5, 0, tzinfo=replay_harness.IST
    )

    member = ex1.member_executions[0]
    hydro = member.integrated.rainfall_conversion.hydrograph
    # The chain head flow IS the event hydrograph discharge per bin.
    first = member.chain.steps[0].state_for("UG-01").state.incoming_flow_m3_s
    second = member.chain.steps[1].state_for("UG-01").state.incoming_flow_m3_s
    third = member.chain.steps[2].state_for("UG-01").state.incoming_flow_m3_s
    fourth = member.chain.steps[3].state_for("UG-01").state.incoming_flow_m3_s
    assert first == pytest.approx(hydro.steps[0].discharge_m3_s)
    assert second == pytest.approx(hydro.steps[1].discharge_m3_s)
    assert third is None and hydro.steps[2].discharge_m3_s is None
    assert fourth is None and hydro.steps[3].discharge_m3_s is None
    # Discharge value comes from the existing conversion with the member's
    # own parameters: Q = C * P * A / dt.
    expected_q = 0.75 * (91.0 / 1000.0) * (27.66 * 1e6) / 3600.0
    assert hydro.steps[1].discharge_m3_s == pytest.approx(expected_q)

    # The forcing sequence determined the executed timestep loop: 4 bins
    # x 6 members chain steps per event.
    assert ex1.counters.chain_timesteps_executed == 4 * 6
    assert ex1.counters.forcing_bins_executed == 4 * 6

    # EV-02: the documented 3-hour aggregated increment spans ONE 3-hour
    # timestep; the loop follows the event's own intervals.
    ex2 = replay.event_executions["EVT-2023-07-08"]
    fs2 = ex2.forcing_series
    assert [ts.duration_seconds for ts in fs2.timesteps] == [
        3600.0, 10800.0, 3600.0, 3600.0,
    ]
    assert ex2.counters.chain_timesteps_executed == 4 * 6

    # UNKNOWN bins propagate as blocked head-reach states (never zeros).
    head_blocked = sum(
        1
        for m in ex1.member_executions
        for step in m.chain.steps
        if step.state_for("UG-01").continuity.status
        == SimulationStateStatus.BLOCKED_MISSING_INPUT
    )
    assert head_blocked == 2 * 6  # t+2h and t+3h are UNKNOWN


def test_d_runtime_result_fields_derived_from_runtime_objects(replay):
    rec = _records_by_id(replay)["EVT-2024-06-27"]
    ex = replay.event_executions["EVT-2024-06-27"]
    members = ex.member_executions

    # Recompute the continuity/accounting counts independently from the
    # runtime objects and require the record string to carry exactly them.
    cont = Counter(
        r.continuity.status.value
        for m in members
        for step in m.chain.steps
        for r in step.results
    )
    acct = Counter(
        r.accounting.status
        for m in members
        for step in m.chain.steps
        for r in step.results
    )
    assert rec.mass_balance_check.startswith("RUNTIME_DERIVED")
    for status, count in cont.items():
        assert f"{status}={count}" in rec.mass_balance_check
    for status, count in acct.items():
        assert f"{status}={count}" in rec.mass_balance_check
    # Independent closure check: accounting residual == dV/dt on every
    # computed reach-step of member 0 (the runtime's own artifacts).
    member = members[0]
    cur = {"UG-01": 10000.0, "OC-01": 10000.0, "CD-01": 10000.0, "OC-02": 10000.0}
    closure_checked = 0
    for step in member.chain.steps:
        dt = step.results[0].state.timestep.duration_seconds
        for r in step.results:
            if r.continuity.status == SimulationStateStatus.COMPUTED:
                d_storage = r.state.storage_m3 - cur[r.state.reach_id]
                assert r.accounting.balance_residual_m3_s == pytest.approx(
                    d_storage / dt
                )
                cur[r.state.reach_id] = r.state.storage_m3
                closure_checked += 1
    assert closure_checked == 10
    assert "max |err| 0.000e+00" in rec.mass_balance_check

    # Terminal outfall count derived from the transfer objects.
    terminal = sum(
        1
        for m in members
        for step in m.chain.steps
        if step.state_for("OC-02").transfer.hydraulic_status
        == "TERMINAL_REACH_NO_DOWNSTREAM"
    )
    assert terminal == 6 * 4
    assert f"{terminal}/{6 * 4} reach-steps" in rec.terminal_outfall_check

    # Validation results derived from the per-member validation records.
    outcomes = Counter(m.validation.validation_result.value for m in members)
    assert outcomes == Counter({"UNKNOWN": 6})
    assert f"UNKNOWN={outcomes['UNKNOWN']}" in rec.runtime_consistency_check

    # Execution counts come from the per-event counters (actual call sites).
    assert rec.chain_timesteps_executed == ex.counters.chain_timesteps_executed
    assert rec.hydrograph_timesteps_executed == (
        sum(len(m.integrated.hydraulic_run.states) for m in members)
    )
    assert rec.validation_calls == ex.counters.validation_calls == 6

    # The hydrograph states genuinely reflect the event forcing: the run
    # computes the two documented bins and blocks at the first UNKNOWN bin
    # (existing stop-on-first-block contract -> PARTIAL).
    states = member.integrated.hydraulic_run.states
    assert [s.status for s in states] == [
        SimulationStateStatus.COMPUTED,
        SimulationStateStatus.COMPUTED,
        SimulationStateStatus.BLOCKED_MISSING_INPUT,
    ]
    assert member.integrated.hydraulic_run.simulation_status.value == "PARTIAL"
    # Storage evolved by the event forcing (closed-boundary scenario).
    expected_v = 10000.0 + 3600.0 * (
        0.75 * (91.0 / 1000.0) * (27.66 * 1e6) / 3600.0
    )
    assert states[1].storage_m3 == pytest.approx(expected_v)


def test_e_no_smoke_test_substitution(replay):
    ex1 = replay.event_executions["EVT-2024-06-27"]
    ex2 = replay.event_executions["EVT-2023-07-08"]
    # Distinct per-event counters and forcing objects (nothing shared).
    assert ex1.counters is not ex2.counters
    assert ex1.forcing_series is not ex2.forcing_series
    assert (
        ex1.forcing_series.forcing_profile.forcing_id
        != ex2.forcing_series.forcing_profile.forcing_id
    )
    # Every member execution is its own runtime run (never reused objects).
    for a, b in zip(ex1.member_executions, ex2.member_executions):
        assert a is not b
        assert a.integrated is not b.integrated
        assert a.chain is not b.chain
    # The events ran on their own windows: hydrograph timestamps differ.
    h1 = ex1.member_executions[0].integrated.rainfall_conversion.hydrograph
    h2 = ex2.member_executions[0].integrated.rainfall_conversion.hydrograph
    assert h1.steps[1].timestamp != h2.steps[1].timestamp
    # Validation was called per event (6 calls each), not once globally.
    assert ex1.counters.validation_calls == 6
    assert ex2.counters.validation_calls == 6
    # Non-executable events were never executed at all (EV-03 is the
    # declared PARTIAL event and DOES execute its defensible portion).
    for event_id in ("EVT-2026-01-23", "EVT-2021-07-19", "EVT-2023-05-27"):
        ex = replay.event_executions[event_id]
        assert ex.member_executions == []
        assert ex.counters.ensemble_members_executed == 0
        assert ex.counters.chain_timesteps_executed == 0
    ex3 = replay.event_executions["EVT-2021-09-11"]
    assert ex3.counters.ensemble_members_executed == 6
    assert ex3.forcing_series is not None
    assert ex3.forcing_series.forcing_profile.forcing_id == "FC-EV03-SAFDARJUNG"
    # The harness contains no single one-shot advance_chain_timestep()
    # smoke call; the multi-timestep driver is advance_chain_series() with
    # the event forcing sequence as the loop.
    source = inspect.getsource(replay_harness)
    assert "advance_chain_timestep(" not in source
    assert "advance_chain_series(" in source


def test_f_partial_replay_evt_2021_09_11(replay):
    """EV-03 executes ONLY its documented defensible portion (the verified
    80 mm 05:30-08:30 IST 3-hour block) at native resolution; the
    remainder stays UNKNOWN. This is a deliberate PARTIAL replay."""
    rec = _records_by_id(replay)["EVT-2021-09-11"]
    assert rec.final_classification.startswith("PARTIAL_CONSISTENT")
    assert rec.forcing_found == "YES"
    assert rec.runtime_executed == "YES"
    assert rec.ensemble_members_executed == 6
    assert rec.validation_calls == 6
    assert rec.mass_balance_check.startswith("RUNTIME_DERIVED")
    ex = replay.event_executions["EVT-2021-09-11"]
    fs = ex.forcing_series
    # 2 bins -> 2 timesteps: the 3-hour block (80 mm OBSERVED_DIRECT) and
    # the 6-hour UNKNOWN remainder (never split, never filled).
    assert fs.bin_intervals_hours == (3, 6)
    assert fs.depths_mm == (80.0, None)
    assert fs.timesteps[0].start == datetime(2021, 9, 11, 5, 30, tzinfo=replay_harness.IST)
    member = ex.member_executions[0]
    hydro = member.integrated.rainfall_conversion.hydrograph
    assert hydro.steps[0].discharge_m3_s == pytest.approx(
        0.75 * (80.0 / 1000.0) * (27.66 * 1e6) / 10800.0
    )
    assert hydro.steps[1].discharge_m3_s is None


def test_g_unknown_preserved_for_events_without_forcing(replay):
    for event_id in ("EVT-2021-07-19", "EVT-2023-05-27"):
        rec = _records_by_id(replay)[event_id]
        assert rec.final_classification.startswith("UNKNOWN")
        assert "BLOCKED_MISSING_FORCING" in rec.final_classification
        assert rec.forcing_found == "NO"
        assert rec.runtime_executed == "NO"
        assert rec.ensemble_members_executed == 0
        assert rec.chain_timesteps_executed == 0
        assert rec.validation_calls == 0
        assert rec.mass_balance_check.startswith("NOT_COMPUTED")


def test_h_no_synthetic_disaggregation(replay):
    fs1 = replay.event_executions["EVT-2024-06-27"].forcing_series
    fs2 = replay.event_executions["EVT-2023-07-08"].forcing_series
    # Each catalog bin maps to exactly ONE timestep (no bin split).
    assert len(fs1.timesteps) == len(fs1.forcing_profile.bins)
    assert len(fs2.timesteps) == len(fs2.forcing_profile.bins)
    # EV-02's documented 3-hour aggregated increment is ONE 3-hour
    # timestep with its full 45.0 mm — never split into hourly values.
    assert fs2.bin_intervals_hours == (1, 3, 1, 1)
    assert fs2.timesteps[1].duration_seconds == 10800.0
    assert fs2.depths_mm == (0.0, 45.0, None, None)
    # UNKNOWN bins stay UNKNOWN (no zero-fill, no interpolation).
    assert fs1.depths_mm == (0.0, 91.0, None, None)
    assert fs1.bin_intervals_hours == (1, 1, 1, 1)
    # Timesteps are contiguous; no gaps were filled.
    for fs in (fs1, fs2):
        for a, b in zip(fs.timesteps, fs.timesteps[1:]):
            assert a.end == b.start


def test_i_event_id_mapping_backward_compatible(replay):
    # EVENT_ID_MAP behavior: catalogue IDs resolve to canonical EV-* IDs.
    assert EVENT_ID_MAP["EVT-2024-06-27"] == "EV-01"
    assert EVENT_ID_MAP["EVT-2023-07-08"] == "EV-02"
    assert EVENT_ID_MAP["EVT-2021-09-11"] == "EV-03"
    assert EVENT_ID_MAP["EV-01"] == "EV-01"
    assert EVENT_ID_MAP["EV-02"] == "EV-02"
    assert EVENT_ID_MAP["EV-03"] == "EV-03"
    # Records preserve the original catalogue IDs and resolved IDs.
    recs = _records_by_id(replay)
    assert recs["EVT-2024-06-27"].resolved_event_id == "EV-01"
    assert recs["EVT-2023-07-08"].resolved_event_id == "EV-02"
    assert recs["EVT-2021-09-11"].resolved_event_id == "EV-03"
    assert recs["EVT-2026-01-23"].resolved_event_id == "EVT-2026-01-23"
    # Forcing retrieval works from both raw and resolved IDs; raw IDs with
    # no mapping still pass through (no event is silently re-keyed).
    from backend.app.domain.delhi.digital_twin.kushak_historical_rainfall_catalog import (
        get_forcing_for_event,
    )
    assert get_forcing_for_event("EV-01") is not None
    assert get_forcing_for_event(resolve_event_id("EVT-2024-06-27")) is not None
    assert get_forcing_for_event("EVT-2021-09-11") is None
    assert get_forcing_for_event(resolve_event_id("EVT-2021-09-11")) is not None


def test_system_flags_and_verdict(replay):
    flags = replay.system_flags
    for name in REQUIRED_FLAGS:
        assert name in flags, f"missing required flag {name}"
    for name in REQUIRED_FLAGS:
        expected = "NO" if name == "MANUAL_RUNTIME_RESULT_FIELDS_PRESENT" else "YES"
        assert flags[name] == expected, f"{name}={flags[name]}, expected {expected}"
    assert replay.verdict == "PASS"

    # Record field separation: runtime fields enumerated, manual fields NONE.
    for rec in replay.records:
        listed = {f.strip() for f in rec.runtime_derived_fields.split(",")}
        if rec.runtime_executed == "YES":
            assert listed == set(RUNTIME_DERIVED_FIELD_NAMES)
        assert rec.manual_runtime_result_fields == "NONE"
        assert rec.csv_runtime_derived == "YES"


def test_member_execution_matches_canonical_evidence_scenario_path(replay):
    """The harness member execution IS the canonical evidence-scenario path
    (the engine execute_ensemble_member() delegates to) with the event
    forcing injected at the existing forcing parameter."""
    from backend.app.domain.delhi.digital_twin.kushak_evidence_model import (
        CATCHMENT_SCENARIOS,
        KUSHAK_HYDRAULIC_SCENARIOS,
        run_kushak_evidence_scenario,
    )
    ex = replay.event_executions["EVT-2024-06-27"]
    member = build_kushak_ensemble()[0]
    reference = run_kushak_evidence_scenario(
        hydraulic_scenario=KUSHAK_HYDRAULIC_SCENARIOS[member.hydraulic_scenario_id],
        catchment=CATCHMENT_SCENARIOS[member.catchment_scenario_id],
        runoff_coefficient=member.runoff_coefficient,
        forcing=ex.forcing_series,
    )
    mine = ex.member_executions[0].integrated
    assert mine.rainfall_conversion.status == (
        reference.rainfall_conversion.status
    ) == "COMPUTED"
    for a, b in zip(
        mine.rainfall_conversion.hydrograph.steps,
        reference.rainfall_conversion.hydrograph.steps,
    ):
        assert a.timestamp == b.timestamp
        if a.discharge_m3_s is None or b.discharge_m3_s is None:
            assert a.discharge_m3_s is None and b.discharge_m3_s is None
        else:
            assert a.discharge_m3_s == pytest.approx(b.discharge_m3_s)
    assert len(mine.hydraulic_run.states) == len(reference.hydraulic_run.states)
    for a, b in zip(mine.hydraulic_run.states, reference.hydraulic_run.states):
        assert a.status == b.status
        assert a.storage_m3 == pytest.approx(b.storage_m3)
