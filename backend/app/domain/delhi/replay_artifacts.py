"""Reproducible historical replay artifacts (28C).

Builds the per-event replay artifact for every catalogued event: a
self-describing JSON document containing the forcing reconstruction,
runtime outputs, uncertainty/unknown/blocked intervals, validation
outcomes, and the revision identity needed to reproduce the run.

Artifacts are clearly separated from operational forecast outputs: they
are written ONLY under ``data/delhi/derived/replay_artifacts/``. Nothing
in the operational nowcast path reads or writes them.

An artifact exists for NON-executable events too (runtime_status
NOT_EXECUTED with the preserved classification) so every event in the
catalogue has a reproducible record of WHAT is missing and WHY the
runtime refused — never a fabricated simulation.
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

_REPO_ROOT = Path(__file__).resolve().parents[4]
_SCRIPTS_DIR = _REPO_ROOT / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

import generate_phase15_replay as replay_harness  # noqa: E402

from backend.app.domain.delhi.digital_twin.kushak_scenario_ensemble import (  # noqa: E402
    build_kushak_ensemble,
)

ARTIFACTS_DIR = _REPO_ROOT / "data" / "delhi" / "derived" / "replay_artifacts"


def repository_revision() -> str:
    """Best-effort repository revision for reproducibility metadata."""
    try:
        return (
            subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=str(_REPO_ROOT),
                capture_output=True,
                text=True,
                timeout=10,
                check=True,
            ).stdout.strip()
        )
    except Exception:
        return "unknown (git unavailable)"


def _forcing_resolution_label(declaration) -> str:
    base = declaration.forcing_resolution
    if declaration.executable_status == "PARTIALLY_EXECUTABLE":
        return (
            f"{base} (PARTIAL: only the documented defensible portion is "
            "executable at its native interval; remainder UNKNOWN)"
        )
    if declaration.executable_status.startswith("NON_EXECUTABLE"):
        return f"{base} (no executable forcing)"
    return base


def _interval_intervals(series) -> List[Dict[str, Any]]:
    """Per-timestep records with depth + provenance (resolution preserved)."""
    steps = []
    for i, ts in enumerate(series.timesteps):
        depth = series.depths_mm[i]
        bin_ = series.forcing_profile.bins[i]
        steps.append({
            "index": i,
            "time_start": ts.start.isoformat(),
            "time_end": ts.end.isoformat(),
            "duration_hours": (ts.end - ts.start).total_seconds() / 3600.0,
            "depth_mm": depth,
            "provenance": bin_.provenance.value,
        })
    return steps


def build_replay_artifact(event_id: str) -> Dict[str, Any]:
    """Build (deterministically) the replay artifact for one event."""
    declaration = replay_harness.get_declaration(event_id)
    rows = replay_harness._load_event_catalog_rows()
    catalog_row = rows[event_id]
    meta = replay_harness._catalog_metadata_fields(catalog_row, event_id)

    artifact: Dict[str, Any] = {
        "artifact_schema": "kushak-replay-artifact/1.0",
        "event_id": event_id,
        "resolved_event_id": declaration.canonical_event_id or "UNRESOLVED",
        "event_window": meta["event_window"],
        "forcing_source": declaration.forcing_source,
        "forcing_resolution": _forcing_resolution_label(declaration),
        "forcing_provenance": meta["rainfall_resolution"],
        "ensemble_members": [m.member_id for m in build_kushak_ensemble()],
        "runtime_status": "NOT_EXECUTED",
        "forcing_timesteps": [],
        "hydraulic_states": {},
        "routing_states": {},
        "uncertainty_states": {},
        "validation_status": {},
        "observation_matches": [],
        "unknown_intervals": [],
        "blocked_intervals": [],
        "generation_timestamp": datetime.now(timezone.utc).isoformat(),
        "repository_revision": repository_revision(),
        "replay_claim": declaration.replay_claim,
        "declaration": {
            "forcing_availability": declaration.forcing_availability,
            "forcing_resolution": declaration.forcing_resolution,
            "spatial_attribution_status": declaration.spatial_attribution_status,
            "observation_status": declaration.observation_status,
            "executable_status": declaration.executable_status,
            "evidence_notes": declaration.evidence_notes,
        },
    }

    forcing_profile = (
        replay_harness.get_forcing_for_event(declaration.canonical_event_id)
        if declaration.canonical_event_id else None
    )
    if forcing_profile is None:
        artifact["reason"] = replay_harness.PRESERVED_FINAL_CLASSIFICATION[event_id]
        return artifact

    forcing_series = replay_harness.build_event_forcing_series(
        catalog_event_id=event_id,
        canonical_event_id=declaration.canonical_event_id,
        forcing_profile=forcing_profile,
    )
    counters = replay_harness.EventRuntimeCounters()
    ensemble = build_kushak_ensemble()
    member_executions = [
        replay_harness.execute_member_for_event(m, forcing_series, counters)
        for m in ensemble
    ]

    artifact["runtime_status"] = (
        "EXECUTED" if declaration.executable_status == "EXECUTABLE"
        else "PARTIAL_EXECUTED"
    )
    artifact["forcing_timesteps"] = _interval_intervals(forcing_series)
    artifact["forcing_provenance"] = [
        {
            "lead_hour": b.lead_hour,
            "amount": b.amount,
            "units": b.units,
            "provenance": b.provenance.value,
            "source_reference": b.source_reference,
        }
        for b in forcing_profile.bins
    ]

    unknown_intervals: List[Dict[str, Any]] = []
    blocked_intervals: List[Dict[str, Any]] = []
    for i, ts in enumerate(forcing_series.timesteps):
        if forcing_series.depths_mm[i] is None:
            unknown_intervals.append({
                "time_start": ts.start.isoformat(),
                "time_end": ts.end.isoformat(),
                "reason": "documented forcing absent; UNKNOWN preserved",
            })

    hydraulic_states: Dict[str, Any] = {}
    routing_states: Dict[str, Any] = {}
    validation_status: Dict[str, Any] = {}
    observation_matches: List[Dict[str, Any]] = []

    for ex in member_executions:
        member_id = ex.member_id
        per_reach: Dict[str, List[Dict[str, Any]]] = {}
        routing_per_reach: Dict[str, List[Dict[str, Any]]] = {}
        for step_idx, step in enumerate(ex.chain.steps):
            for r in step.results:
                rid = r.state.reach_id
                per_reach.setdefault(rid, []).append({
                    "time_start": r.state.timestep.start.isoformat(),
                    "time_end": r.state.timestep.end.isoformat(),
                    "status": r.state.hydraulic_status.value,
                    "storage_m3": r.state.storage_m3,
                    "stage_m": r.state.stage_m,
                    "incoming_flow_m3_s": r.state.incoming_flow_m3_s,
                })
                routing_per_reach.setdefault(rid, []).append({
                    "time_start": r.state.timestep.start.isoformat(),
                    "actual_outflow_m3_s": r.transfer.actual_outflow_m3_s,
                    "transferred_m3_s": r.transfer.transferred_m3_s,
                    "capacity_m3_s": r.transfer.capacity_m3_s,
                    "balance_residual_m3_s": r.accounting.balance_residual_m3_s,
                })
                if r.state.hydraulic_status.value.startswith("BLOCKED"):
                    blocked_intervals.append({
                        "member_id": member_id,
                        "reach_id": rid,
                        "time_start": r.state.timestep.start.isoformat(),
                        "time_end": r.state.timestep.end.isoformat(),
                        "status": r.state.hydraulic_status.value,
                    })
        hydraulic_states[member_id] = per_reach
        routing_states[member_id] = routing_per_reach

        v = ex.validation
        validation_status[member_id] = {
            "validation_result": v.validation_result.value,
            "temporal_match": v.temporal_match.value,
            "spatial_match": v.spatial_match.value,
            "result_provenance": v.result_provenance.value,
        }
        observation_matches.append({
            "member_id": member_id,
            "source_class": v.source_class.value,
            "source_provenance": v.source_provenance.value,
            "validation_result": v.validation_result.value,
            "temporal_match": v.temporal_match.value,
            "spatial_match": v.spatial_match.value,
            "note": (
                "Occurrence-class evidence only; observations are never "
                "used as model inputs or depth targets."
            ),
        })

    # Ensemble uncertainty envelope over head-reach inflow per timestep.
    envelope = []
    for i, ts in enumerate(forcing_series.timesteps):
        values = [
            ex.integrated.rainfall_conversion.hydrograph.steps[i].discharge_m3_s
            for ex in member_executions
            if ex.integrated.rainfall_conversion.hydrograph is not None
            and i < len(ex.integrated.rainfall_conversion.hydrograph.steps)
        ]
        known = [v for v in values if v is not None]
        envelope.append({
            "time_start": ts.start.isoformat(),
            "time_end": ts.end.isoformat(),
            "min_m3_s": min(known) if known else None,
            "median_m3_s": sorted(known)[len(known) // 2] if known else None,
            "max_m3_s": max(known) if known else None,
            "computed_members": len(known),
            "unknown_members": len(values) - len(known),
        })

    artifact["hydraulic_states"] = hydraulic_states
    artifact["routing_states"] = routing_states
    artifact["uncertainty_states"] = {
        "envelope_inflow": envelope,
        "note": (
            "min/median/max across the deterministic members; UNKNOWN "
            "members are counted, never zero-filled into the envelope."
        ),
    }
    artifact["validation_status"] = validation_status
    artifact["observation_matches"] = observation_matches
    artifact["unknown_intervals"] = unknown_intervals
    artifact["blocked_intervals"] = blocked_intervals
    artifact["counters"] = {
        "ensemble_members_executed": counters.ensemble_members_executed,
        "forcing_bins_executed": counters.forcing_bins_executed,
        "chain_timesteps_executed": counters.chain_timesteps_executed,
        "chain_reach_timesteps_executed": counters.chain_reach_timesteps_executed,
        "validation_calls": counters.validation_calls,
    }
    artifact["integrity_checks"] = {
        "mass_balance": replay_harness._derive_mass_balance_check(member_executions),
        "terminal_outfall": replay_harness._derive_terminal_outfall_check(member_executions),
        "unknown_propagation": replay_harness._derive_unknown_propagation_check(
            forcing_series, member_executions
        ),
        "runtime_consistency": replay_harness._derive_runtime_consistency_check(member_executions),
    }
    return artifact


def write_artifact(event_id: str, out_dir: Path = ARTIFACTS_DIR) -> Path:
    """Write one event's artifact JSON; returns the written path."""
    artifact = build_replay_artifact(event_id)
    out_dir.mkdir(parents=True, exist_ok=True, mode=0o755)
    path = out_dir / f"{event_id}.json"
    path.write_text(
        json.dumps(artifact, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return path


def write_all_artifacts(out_dir: Path = ARTIFACTS_DIR) -> List[Path]:
    """Write artifacts for every declared replay event."""
    paths = []
    for event_id in replay_harness.REPLAY_EVENT_IDS:
        paths.append(write_artifact(event_id, out_dir))
    return paths


if __name__ == "__main__":
    for p in write_all_artifacts():
        print(f"wrote {p}")
