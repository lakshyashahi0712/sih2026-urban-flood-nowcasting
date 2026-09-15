"""Phase 11 Step 4: Deterministic Rainfall-to-Runoff Ensemble Driver.

Connects Phase 11 historical rainfall forcing (with Step 3 UNKNOWN propagation)
to existing rainfall-to-inflow conversion (rainfall_to_inflow.py), preserving:
- C = 0.75 (SCENARIO_RUNOFF_C, ASSUMED)
- 27.66 km² working catchment (WORKING_27_66, PROVISIONAL)
- 28.40 km² sensitivity scenario (SENSITIVITY_28_40, PROVISIONAL)
- 6 deterministic ensemble members (3 hydraulic scenarios × 2 catchment scenarios)
- Strict UNKNOWN/blocked propagation (None rainfall remains None discharge / blocked).
- No new hydrologic theory, calibration, or ML.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from .kushak_rainfall_forcing import RainfallForcingProfile
from .kushak_historical_rainfall_unknown import (
    propagate_historical_rainfall_forcing,
    HistoricalRainfallPropagationResult,
)
from .kushak_scenario_ensemble import build_kushak_ensemble, KushakEnsembleMember
from .kushak_evidence_model import CATCHMENT_SCENARIOS
from .rainfall_to_inflow import rainfall_to_inflow, RainfallToInflowResult
from .hydraulic_time_state import SimulationTimestep
from .models import ProvenanceStatus


@dataclass(frozen=True)
class KushakEnsembleMemberRunResult:
    """Run result for a single ensemble member."""
    member: KushakEnsembleMember
    propagation_result: HistoricalRainfallPropagationResult
    inflow_result: RainfallToInflowResult
    diagnostic: str


@dataclass(frozen=True)
class KushakRainfallRunoffEnsembleResult:
    """Ensemble run result across all 6 deterministic members for a given rainfall profile."""
    event_id: str
    forcing_id: str
    member_runs: Tuple[KushakEnsembleMemberRunResult, ...]
    overall_status: str  # "COMPUTED" or "BLOCKED_BY_UNKNOWN"
    diagnostics: Tuple[str, ...]


def run_kushak_rainfall_runoff_ensemble(
    profile: RainfallForcingProfile,
    timesteps: List[SimulationTimestep],
) -> KushakRainfallRunoffEnsembleResult:
    """Run the 6 deterministic ensemble members for a given historical rainfall forcing profile.

    1. Propagates historical rainfall forcing through Step 3 UNKNOWN rules.
    2. Builds the 6 deterministic ensemble members (3 hydraulic × 2 catchment).
    3. Runs rainfall_to_inflow for each member using its catchment area and C=0.75.
    4. Preserves strict UNKNOWN propagation (None amounts remain None discharge).
    """
    prop_res = propagate_historical_rainfall_forcing(profile)
    rainfall_depths = [b.effective_amount for b in prop_res.bin_results]

    ensemble_members = build_kushak_ensemble()
    assert len(ensemble_members) == 6, f"Expected 6 ensemble members, got {len(ensemble_members)}"

    member_runs: List[KushakEnsembleMemberRunResult] = []
    diagnostics: List[str] = [
        f"Ensemble run for event {profile.event_id} ({profile.forcing_id}) across {len(ensemble_members)} members."
    ]

    for member in ensemble_members:
        catchment_scenario = CATCHMENT_SCENARIOS[member.catchment_scenario_id]
        area_km2 = catchment_scenario.area_km2

        inflow_res = rainfall_to_inflow(
            timesteps=timesteps,
            rainfall_depth_mm=rainfall_depths,
            catchment_area_km2=area_km2,
            runoff_coefficient=member.runoff_coefficient,
            catchment_area_provenance=catchment_scenario.provenance,
            runoff_coefficient_provenance=ProvenanceStatus.ASSUMED,
            source_id=f"ensemble-{member.member_id}-{profile.event_id}",
        )

        member_runs.append(
            KushakEnsembleMemberRunResult(
                member=member,
                propagation_result=prop_res,
                inflow_result=inflow_res,
                diagnostic=f"Member {member.member_id}: area={area_km2}km2, C={member.runoff_coefficient}, status={inflow_res.status}"
            )
        )

    overall_status = prop_res.overall_status
    diagnostics.append(f"Ensemble overall status: {overall_status} (propagated from Step 3).")

    return KushakRainfallRunoffEnsembleResult(
        event_id=profile.event_id,
        forcing_id=profile.forcing_id,
        member_runs=tuple(member_runs),
        overall_status=overall_status,
        diagnostics=tuple(diagnostics),
    )
