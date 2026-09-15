"""Phase 9: Descriptive scenario envelope (deterministic, evidence-constrained).

Aggregates ensemble member results into descriptive scenario bounds
per reach and timestep, preserving provenance and traceability.

CORE SCIENTIFIC RULES:
- Deterministic descriptive envelope ONLY.
- NOT probabilistic uncertainty, confidence intervals, prediction intervals,
  calibration, accuracy metrics, or risk scoring.
- UNKNOWN / BLOCKED outputs never participate in numerical min/max and are
  never fabricated, interpolated, or replaced with zero.
- Scenario IDs and contributing states are fully preserved and traceable.
- Aggregate provenance is DERIVED.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple

from .hydraulic_integrated_orchestrator import IntegratedRunResult
from .models import ProvenanceStatus


@dataclass(frozen=True)
class ScenarioEnvelope:
    """Immutable descriptive envelope for a specific reach and timestep,
    bounding ensemble member outputs without probabilities or calibration.
    """
    reach_id: str
    timestep_index: int
    timestamp: datetime
    scenario_min_stage: Optional[float]
    scenario_max_stage: Optional[float]
    scenario_min_storage: Optional[float]
    scenario_max_storage: Optional[float]
    model_states_observed: Tuple[str, ...]
    contributing_scenario_ids: Tuple[str, ...]
    status: str = "COMPUTED"
    provenance: ProvenanceStatus = ProvenanceStatus.DERIVED


def build_scenario_envelope(
    results: Dict[str, IntegratedRunResult]
) -> List[ScenarioEnvelope]:
    """Aggregate multiple ensemble member results into descriptive scenario envelopes.

    Consumes actual ensemble-member results (`results` map: member_id -> IntegratedRunResult).
    Preserves scenario traceability, model states, and enforces strict UNKNOWN/BLOCKED handling
    (non-numerical states never participate in min/max).
    """
    if not results:
        return []

    # Identify valid runs with hydraulic results
    valid_runs = {
        m_id: res for m_id, res in results.items()
        if res.hydraulic_run and res.hydraulic_run.states
    }
    if not valid_runs:
        return []

    # Use first valid run to establish timeline and reach topology
    first_id = next(iter(valid_runs))
    first_hydraulic = valid_runs[first_id].hydraulic_run
    num_timesteps = len(first_hydraulic.states)

    # Collect reach IDs across timesteps from the first run
    reach_ids_per_timestep: List[List[str]] = []
    timestamps_per_timestep: List[datetime] = []
    for s in first_hydraulic.states:
        timestamps_per_timestep.append(s.timestamp)
        reach_ids_per_timestep.append([s.location_id])

    envelopes: List[ScenarioEnvelope] = []

    for t_idx in range(num_timesteps):
        timestamp = timestamps_per_timestep[t_idx]
        # Gather unique reach IDs present at this timestep across any run
        timestep_reach_ids: Set[str] = set()
        for res in valid_runs.values():
            if t_idx < len(res.hydraulic_run.states):
                timestep_reach_ids.add(res.hydraulic_run.states[t_idx].location_id)

        for reach_id in sorted(timestep_reach_ids):
            stages: List[float] = []
            storages: List[float] = []
            states: Set[str] = set()
            contributors: Set[str] = set()

            for m_id, res in results.items():
                if not res.hydraulic_run or t_idx >= len(res.hydraulic_run.states):
                    # Member is blocked or truncated at this timestep
                    contributors.add(m_id)
                    states.add("BLOCKED_TRUNCATED")
                    continue

                state = res.hydraulic_run.states[t_idx]
                if state.location_id != reach_id:
                    continue

                contributors.add(m_id)
                if state.status:
                    states.add(state.status.value if hasattr(state.status, "value") else str(state.status))

                # Strict UNKNOWN/BLOCKED handling: only finite numerical outputs participate in min/max
                if state.stage_m is not None:
                    try:
                        val = float(state.stage_m)
                        if val == val and val not in (float("inf"), float("-inf")):
                            stages.append(val)
                    except (TypeError, ValueError):
                        pass

                if state.storage_m3 is not None:
                    try:
                        val = float(state.storage_m3)
                        if val == val and val not in (float("inf"), float("-inf")):
                            storages.append(val)
                    except (TypeError, ValueError):
                        pass

            if not stages and not storages:
                # No valid numerical scenario output exists for this reach/timestep:
                # explicitly represent as BLOCKED/UNKNOWN without fabricating numbers.
                envelopes.append(ScenarioEnvelope(
                    reach_id=reach_id,
                    timestep_index=t_idx,
                    timestamp=timestamp,
                    scenario_min_stage=None,
                    scenario_max_stage=None,
                    scenario_min_storage=None,
                    scenario_max_storage=None,
                    model_states_observed=tuple(sorted(states)) if states else ("BLOCKED",),
                    contributing_scenario_ids=tuple(sorted(contributors)),
                    status="BLOCKED",
                    provenance=ProvenanceStatus.DERIVED,
                ))
            else:
                envelopes.append(ScenarioEnvelope(
                    reach_id=reach_id,
                    timestep_index=t_idx,
                    timestamp=timestamp,
                    scenario_min_stage=min(stages) if stages else None,
                    scenario_max_stage=max(stages) if stages else None,
                    scenario_min_storage=min(storages) if storages else None,
                    scenario_max_storage=max(storages) if storages else None,
                    model_states_observed=tuple(sorted(states)),
                    contributing_scenario_ids=tuple(sorted(contributors)),
                    status="COMPUTED",
                    provenance=ProvenanceStatus.DERIVED,
                ))

    return envelopes
