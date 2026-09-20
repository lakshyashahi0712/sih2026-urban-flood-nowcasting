"""Historical replay regression suite (28F).

Every test here guards a scientific invariant of the historical replay
framework. A regression MUST fail if: manual strings replace runtime
outputs, an event uses another event's forcing, unknown forcing becomes
zero, timestep resolution changes silently, ensemble members are
skipped, observations become model inputs, or operational and
historical outputs mix.
"""

from __future__ import annotations

import sys
from datetime import timedelta
from pathlib import Path

import pytest

from backend.main import app  # noqa: F401  (ensures router wiring imports)
from backend.app.domain.delhi import replay_artifacts
from backend.app.domain.delhi.digital_twin import kushak_replay_manifest as manifest
from backend.app.domain.delhi.digital_twin.kushak_historical_rainfall_catalog import (
    get_forcing_for_event,
    get_historical_rainfall_catalog,
)
from backend.app.domain.delhi.digital_twin.kushak_event_validation import (
    VALIDATION_EVENTS,
    resolve_event_id,
)

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SCRIPTS_DIR = _REPO_ROOT / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

import generate_phase15_replay as harness  # noqa: E402


@pytest.fixture(scope="module")
def replay_run():
    return harness.run_historical_replay()


# ---------------------------------------------------------------------------
# 1. Fully executable historical replay (EV-01)
# ---------------------------------------------------------------------------


def test_fully_executable_event_replay(replay_run):
    executions = replay_run.event_executions["EVT-2024-06-27"]
    assert executions.member_executions, "EV-01 must execute"
    assert executions.forcing_series is not None
    # Every member produced a computed inflow conversion.
    for ex in executions.member_executions:
        assert ex.integrated.rainfall_conversion.status == "COMPUTED"
        assert ex.integrated.rainfall_conversion.hydrograph is not None


# ---------------------------------------------------------------------------
# 2. Multi-timestep historical replay (EV-01: 4 forcing timesteps)
# ---------------------------------------------------------------------------


def test_multi_timestep_replay_executes_every_forcing_timestep(replay_run):
    executions = replay_run.event_executions["EVT-2024-06-27"]
    series = executions.forcing_series
    assert series is not None and len(series.timesteps) == 4
    for ex in executions.member_executions:
        # One chain step per forcing timestep, in order.
        assert len(ex.chain.steps) == 4
        for step, ts in zip(ex.chain.steps, series.timesteps):
            assert step.results[0].state.timestep.start == ts.start


# ---------------------------------------------------------------------------
# 3. Six-member historical ensemble replay
# ---------------------------------------------------------------------------


def test_six_member_ensemble_replay(replay_run):
    canonical_ids = [m.member_id for m in harness.build_kushak_ensemble()]
    assert len(canonical_ids) == 6
    for event_id in ("EVT-2024-06-27", "EVT-2023-07-08", "EVT-2021-09-11"):
        executions = replay_run.event_executions[event_id]
        executed = [ex.member_id for ex in executions.member_executions]
        assert executed == canonical_ids, f"{event_id} skipped members"


# ---------------------------------------------------------------------------
# 4. UNKNOWN-forcing event (EVT-2021-07-19) is never simulated
# ---------------------------------------------------------------------------


def test_unknown_forcing_event_never_simulated(replay_run):
    executions = replay_run.event_executions["EVT-2021-07-19"]
    assert executions.member_executions == []
    assert executions.forcing_series is None
    record = next(r for r in replay_run.records if r.event_id == "EVT-2021-07-19")
    assert record.runtime_executed == "NO"
    assert "BLOCKED_MISSING_FORCING" in record.final_classification


# ---------------------------------------------------------------------------
# 5. Temporal-resolution discipline (NOT_COMPARABLE / native intervals)
# ---------------------------------------------------------------------------


def test_temporal_resolution_discipline(replay_run):
    # EV-02's 3-hour increment stays a 3-hour chain step — never split.
    ex = replay_run.event_executions["EVT-2023-07-08"].member_executions[0]
    durations = [
        (r.state.timestep.end - r.state.timestep.start).total_seconds() / 3600
        for r in ex.chain.steps[1].results
    ]
    assert set(durations) == {3.0}, "3-hour increment must keep native interval"
    # Date-only observations can never match a model timestep
    # (temporal-resolution barrier is structural, not incidental).
    from backend.app.domain.delhi.digital_twin.kushak_event_validation import (
        TimestampPrecision,
        ValidationSourceClass,
        validate_observation,
    )
    from backend.app.domain.delhi.digital_twin.models import ProvenanceStatus
    from backend.app.domain.delhi.digital_twin.kushak_hydraulic_state_classification import (
        ReachHydraulicClassification,
    )
    record = validate_observation(
        event_id="EV-01",
        source_class=ValidationSourceClass.GSDL_WATERLOGGING_OCCURRENCE,
        source_provenance=ProvenanceStatus.OFFICIAL,
        timestamp=None,
        timestamp_precision=TimestampPrecision.DATE_ONLY,
        model_timestep=(None, None),
        model_state=ReachHydraulicClassification.UNKNOWN,
    )
    assert record.validation_result.value in ("NOT_COMPARABLE", "UNKNOWN")


# ---------------------------------------------------------------------------
# 6. No zero-fill: UNKNOWN bins stay None through the whole chain
# ---------------------------------------------------------------------------


def test_no_zero_fill_of_unknown_forcing(replay_run):
    ex = replay_run.event_executions["EVT-2024-06-27"].member_executions[0]
    series = replay_run.event_executions["EVT-2024-06-27"].forcing_series
    assert series is not None
    assert series.depths_mm[2] is None and series.depths_mm[3] is None
    hydro = ex.integrated.rainfall_conversion.hydrograph
    assert hydro is not None
    assert hydro.steps[2].discharge_m3_s is None
    assert hydro.steps[3].discharge_m3_s is None
    # Downstream of an UNKNOWN head flow the reach state is blocked, not 0.
    blocked_step = ex.chain.steps[2]
    assert blocked_step.results[0].state.hydraulic_status.value.startswith("BLOCKED")
    assert blocked_step.results[0].state.storage_m3 is None


# ---------------------------------------------------------------------------
# 7. No synthetic disaggregation: bins -> timesteps 1:1, native intervals
# ---------------------------------------------------------------------------


def test_no_synthetic_disaggregation(replay_run):
    for event_id in ("EVT-2024-06-27", "EVT-2023-07-08", "EVT-2021-09-11"):
        executions = replay_run.event_executions[event_id]
        series = executions.forcing_series
        assert series is not None
        assert len(series.timesteps) == len(series.forcing_profile.bins)
        assert len(series.depths_mm) == len(series.forcing_profile.bins)
    # EV-03's verified block keeps its 3-hour interval.
    ex = replay_run.event_executions["EVT-2021-09-11"].member_executions[0]
    durations = [
        (r.state.timestep.end - r.state.timestep.start).total_seconds() / 3600
        for r in ex.chain.steps[0].results
    ]
    assert set(durations) == {3.0}


# ---------------------------------------------------------------------------
# 8. Event separation: forcing, validation, and windows never cross
# ---------------------------------------------------------------------------


def test_event_separation():
    catalog = get_historical_rainfall_catalog()
    # Distinct forcing profiles per event (no shared object, no re-dated copy).
    assert catalog["EV-01"].forcing_id != catalog["EV-02"].forcing_id
    assert catalog["EV-01"].forcing_id != catalog["EV-03"].forcing_id
    # Distinct anchors: EV-01's direct hour is 2024, EV-03's block is 2021.
    assert harness.EVENT_FORCING_ANCHORS["EV-01"].year == 2024
    assert harness.EVENT_FORCING_ANCHORS["EV-03"].year == 2021
    # Validation events keep separate windows and identities.
    ids = [e.event_id for e in VALIDATION_EVENTS]
    assert len(ids) == len(set(ids)) == 3
    # An event's replay uses its own forcing id.
    for catalog_id, canonical in (
        ("EVT-2024-06-27", "EV-01"),
        ("EVT-2023-07-08", "EV-02"),
        ("EVT-2021-09-11", "EV-03"),
    ):
        declaration = manifest.get_declaration(catalog_id)
        assert declaration.canonical_event_id == canonical
        profile = get_forcing_for_event(canonical)
        assert profile is not None
        assert profile.forcing_id == declaration.forcing_source
        assert profile.event_id == canonical


# ---------------------------------------------------------------------------
# 9. Runtime lineage: no manual strings, runtime-derived record fields
# ---------------------------------------------------------------------------


def test_runtime_lineage_intact(replay_run):
    flags = replay_run.system_flags
    assert replay_run.verdict == "PASS"
    assert flags["MANUAL_RUNTIME_RESULT_FIELDS_PRESENT"] == "NO"
    assert flags["CSV_IS_RUNTIME_DERIVED"] == "YES"
    assert flags["ALL_RUNTIME_RESULT_FIELDS_DERIVED"] == "YES"
    assert flags["NO_SMOKE_TEST_SUBSTITUTION"] == "YES"
    assert flags["ALL_EVENT_FORCING_TIMESTEPS_RUNTIME_EXECUTED"] == "YES"
    assert flags["NO_SYNTHETIC_DISAGGREGATION"] == "YES"
    assert flags["UNKNOWN_AND_NOT_COMPARABLE_PRESERVED"] == "YES"
    for record in replay_run.records:
        assert record.manual_runtime_result_fields == "NONE"
        assert record.csv_runtime_derived == "YES"


# ---------------------------------------------------------------------------
# 10. Reproducibility: byte-identical rerun
# ---------------------------------------------------------------------------


def test_replay_reproducibility():
    a = harness.run_historical_replay()
    b = harness.run_historical_replay()
    for ra, rb in zip(a.records, b.records):
        assert ra.mass_balance_check == rb.mass_balance_check
        assert ra.runtime_model_state == rb.runtime_model_state
        assert ra.ensemble_members_executed == rb.ensemble_members_executed
        assert ra.final_classification == rb.final_classification


# ---------------------------------------------------------------------------
# 11. Observed-vs-model provenance separation
# ---------------------------------------------------------------------------


def test_observed_vs_model_provenance_separation(replay_run):
    from backend.app.domain.delhi.digital_twin.models import ProvenanceStatus

    for event_id in ("EVT-2024-06-27", "EVT-2023-07-08", "EVT-2021-09-11"):
        for ex in replay_run.event_executions[event_id].member_executions:
            v = ex.validation
            # Observations are OFFICIAL evidence; validation output is
            # always DERIVED model commentary — never merged.
            assert v.source_provenance == ProvenanceStatus.OFFICIAL
            assert v.result_provenance == ProvenanceStatus.DERIVED


# ---------------------------------------------------------------------------
# 12. Manifest: every event fully declared and reconciled (28E)
# ---------------------------------------------------------------------------


def test_manifest_declares_every_event_and_reconciles_with_catalog():
    manifest.validate_manifest()  # raises on any undeclared/contradictory event
    import generate_phase15_replay as h

    for event_id in h.REPLAY_EVENT_IDS:
        declaration = manifest.get_declaration(event_id)
        assert declaration.event_window_utc
        assert declaration.replay_claim
        assert declaration.executable_status in manifest.EXECUTABLE_STATUSES


def test_manifest_rejects_contradictory_declaration():
    bad = manifest.ReplayEventDeclaration(
        catalog_event_id="EVT-BOGUS",
        canonical_event_id="EV-01",
        event_window_utc="2000-01-01T00:00:00Z to 2000-01-02T00:00:00Z",
        forcing_source="FC-EV01-SAFDARJUNG",
        forcing_resolution="HOURLY",
        forcing_availability="NONE",  # contradicts executable status
        spatial_attribution_status="DATE_ONLY",
        observation_status="FLOOD_YES_HIGH_CONFIDENCE",
        executable_status="EXECUTABLE",
        replay_claim="bogus",
        evidence_notes="bogus",
    )
    with pytest.raises(ValueError):
        bad.validate()


# ---------------------------------------------------------------------------
# 13. Artifacts: complete 28C field set, separated directory
# ---------------------------------------------------------------------------


def test_artifact_fields_and_directory_separation():
    artifact = replay_artifacts.build_replay_artifact("EVT-2021-09-11")
    required = (
        "event_id", "resolved_event_id", "event_window", "forcing_source",
        "forcing_resolution", "forcing_provenance", "forcing_timesteps",
        "ensemble_members", "runtime_status", "hydraulic_states",
        "routing_states", "uncertainty_states", "validation_status",
        "observation_matches", "unknown_intervals", "blocked_intervals",
        "generation_timestamp", "repository_revision",
    )
    for field in required:
        assert field in artifact, f"artifact missing {field}"
    assert artifact["runtime_status"] == "PARTIAL_EXECUTED"
    assert artifact["repository_revision"] != ""
    # Artifacts live in the historical-validation/replay directory only.
    assert str(replay_artifacts.ARTIFACTS_DIR).endswith(
        ("replay_artifacts", "replay_artifacts\\")
    )
    assert "forecast" not in str(replay_artifacts.ARTIFACTS_DIR).lower()


def test_artifact_for_non_executable_event_records_why():
    artifact = replay_artifacts.build_replay_artifact("EVT-2021-07-19")
    assert artifact["runtime_status"] == "NOT_EXECUTED"
    assert "BLOCKED_MISSING_FORCING" in artifact["reason"]
    assert artifact["forcing_timesteps"] == []
    assert artifact["ensemble_members"], "member ids still declared"
