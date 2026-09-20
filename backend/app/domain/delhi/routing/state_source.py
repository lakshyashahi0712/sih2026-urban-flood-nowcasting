"""Model-state adapters for the safe-routing engine.

ONE routing core, TWO state sources (28 architecture):

- LIVE: the current deterministic 6-member nowcast (cached forecast →
  ensemble through the canonical runtime), at the departure hour.
- HISTORICAL: the genuine event replay runtime (Phase 15.5 harness) at
  the selected event + timestep.

Both adapters emit the SAME structure — per-member per-reach states — so
the risk translation layer is mode-agnostic. Historical adapters never
touch live state and vice versa (cross-mode isolation is test-enforced).
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from ..nowcast import DelhiForecastFetch, fetch_delhi_rainfall_forecast, run_nowcast

_REPO_ROOT = Path(__file__).resolve().parents[5]
_SCRIPTS_DIR = _REPO_ROOT / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

import generate_phase15_replay as replay_harness  # noqa: E402

from backend.app.domain.delhi.digital_twin.kushak_replay_manifest import (  # noqa: E402
    get_declaration,
)

CHAIN_REACH_IDS: Tuple[str, ...] = ("UG-01", "OC-01", "CD-01", "OC-02")


@dataclass(frozen=True)
class ModeReachStates:
    """Aggregated reach states + provenance for one routing mode."""

    mode: str  # LIVE | HISTORICAL
    status: str  # COMPUTED | NOT_EXECUTED | BLOCKED_MISSING_FORCING
    # member_states[m][reach_id] = {status, incoming_flow_m3_s, storage_m3}
    member_states: List[Dict[str, Dict[str, Optional[float]]]]
    model_timestamp: Optional[str]
    forcing_source: Optional[str]
    event_id: Optional[str]
    timestep_index: Optional[int]
    diagnostics: List[str]
    # LIVE: forecast acquisition timestamp; HISTORICAL: the event's own
    # documented forcing anchor (evidence timestamp, NOT wall-clock age).
    data_timestamp_utc: Optional[datetime]


# ---------------------------------------------------------------------------
# LIVE
# ---------------------------------------------------------------------------


@lru_cache(maxsize=1)
def _live_nowcast_cached():
    """The deterministic nowcast for the currently cached forecast.

    The forecast itself carries the backend's 15-minute freshness cache;
    the ensemble execution is deterministic for a given forecast, so the
    result is cached per forecast acquisition timestamp.
    """
    forecast = fetch_delhi_rainfall_forecast(use_cache=True)
    result = run_nowcast(forecast)
    return forecast.acquired_at, result


def get_live_reach_states(departure_hour: int) -> ModeReachStates:
    """Reach states from the current nowcast at the departure hour."""
    if not 0 <= departure_hour <= 3:
        raise ValueError("departure_hour must be within the 0-3h horizon")

    acquired_at, result = _live_nowcast_cached()

    if result.status != "COMPUTED" or not result.members:
        return ModeReachStates(
            mode="LIVE",
            status=result.status,
            member_states=[],
            model_timestamp=None,
            forcing_source=None,
            event_id=None,
            timestep_index=departure_hour,
            diagnostics=list(result.diagnostics),
            data_timestamp_utc=acquired_at,
        )

    member_states: List[Dict[str, Dict[str, Optional[float]]]] = []
    for member in result.members:
        if member.inflow_status != "COMPUTED":
            member_states.append({})  # blocked member -> weakest-link UNKNOWN
            continue
        states: Dict[str, Dict[str, Optional[float]]] = {}
        for reach_id in CHAIN_REACH_IDS:
            steps = member.reach_states.get(reach_id, [])
            if not steps:
                continue
            idx = departure_hour if departure_hour < len(steps) else len(steps) - 1
            s = steps[idx]
            states[reach_id] = {
                "status": s["hydraulic_status"],
                "incoming_flow_m3_s": s["incoming_flow_m3_s"],
                "storage_m3": s["storage_m3"],
            }
        member_states.append(states)

    model_ts = (
        result.timesteps[departure_hour].start.isoformat()
        if departure_hour < len(result.timesteps)
        else None
    )
    return ModeReachStates(
        mode="LIVE",
        status="COMPUTED",
        member_states=member_states,
        model_timestamp=model_ts,
        forcing_source=result.forecast.source,
        event_id=None,
        timestep_index=departure_hour,
        diagnostics=list(result.diagnostics),
        data_timestamp_utc=acquired_at,
    )


# ---------------------------------------------------------------------------
# HISTORICAL
# ---------------------------------------------------------------------------


@lru_cache(maxsize=16)
def _historical_replay_cached(
    event_id: str,
) -> Tuple[
    str,  # EXECUTED | NOT_EXECUTED
    str,  # resolved id or refusal reason
    Tuple[Tuple[Dict[str, Dict[str, Optional[float]]], ...], ...],  # [t][m][reach]
    Optional[datetime],  # documented forcing anchor
    Tuple[str, ...],  # timestep ISO starts
    Tuple[str, ...],  # diagnostics/notes
]:
    """Execute the genuine event replay once per event (deterministic)."""
    declaration = get_declaration(event_id)
    resolved = declaration.canonical_event_id
    forcing_profile = (
        replay_harness.get_forcing_for_event(resolved) if resolved else None
    )
    if forcing_profile is None:
        reason = replay_harness.PRESERVED_FINAL_CLASSIFICATION[event_id]
        return ("NOT_EXECUTED", reason, (), None, (), (declaration.replay_claim,))

    forcing_series = replay_harness.build_event_forcing_series(
        catalog_event_id=event_id,
        canonical_event_id=resolved,
        forcing_profile=forcing_profile,
    )
    counters = replay_harness.EventRuntimeCounters()
    ensemble = replay_harness.build_kushak_ensemble()
    member_executions = [
        replay_harness.execute_member_for_event(member, forcing_series, counters)
        for member in ensemble
    ]

    per_timestep: List[Tuple[Dict[str, Dict[str, Optional[float]]], ...]] = []
    timestep_starts: List[str] = []
    for t_idx, ts in enumerate(forcing_series.timesteps):
        timestep_starts.append(ts.start.isoformat())
        member_tuple: List[Dict[str, Dict[str, Optional[float]]]] = []
        for ex in member_executions:
            states: Dict[str, Dict[str, Optional[float]]] = {}
            if t_idx < len(ex.chain.steps):
                for r in ex.chain.steps[t_idx].results:
                    states[r.state.reach_id] = {
                        "status": r.state.hydraulic_status.value,
                        "incoming_flow_m3_s": r.state.incoming_flow_m3_s,
                        "storage_m3": r.state.storage_m3,
                    }
            member_tuple.append(states)
        per_timestep.append(tuple(member_tuple))

    return (
        "EXECUTED",
        resolved or "UNRESOLVED",
        tuple(per_timestep),
        forcing_series.anchor_start,
        tuple(timestep_starts),
        (declaration.replay_claim,),
    )


def get_historical_timestep_count(event_id: str) -> int:
    status, _, per_timestep, _, _, _ = _historical_replay_cached(event_id)
    return 0 if status == "NOT_EXECUTED" else len(per_timestep)


def get_historical_reach_states(event_id: str, timestep_index: int) -> ModeReachStates:
    """Reach states from the historical replay at event + timestep."""
    declaration = get_declaration(event_id)
    status, reason_or_resolved, per_timestep, anchor, starts, notes = (
        _historical_replay_cached(event_id)
    )

    if status == "NOT_EXECUTED":
        return ModeReachStates(
            mode="HISTORICAL",
            status="NOT_EXECUTED",
            member_states=[],
            model_timestamp=None,
            forcing_source=None,
            event_id=event_id,
            timestep_index=timestep_index,
            diagnostics=[reason_or_resolved, *notes],
            data_timestamp_utc=None,
        )

    if not 0 <= timestep_index < len(per_timestep):
        raise ValueError(
            f"timestep_index must be in [0, {len(per_timestep) - 1}] for {event_id}"
        )

    return ModeReachStates(
        mode="HISTORICAL",
        status="EXECUTED",
        member_states=list(per_timestep[timestep_index]),
        model_timestamp=starts[timestep_index],
        forcing_source=declaration.forcing_source,
        event_id=event_id,
        timestep_index=timestep_index,
        diagnostics=list(notes),
        data_timestamp_utc=anchor,
    )


def now_utc() -> datetime:
    return datetime.now(timezone.utc)
