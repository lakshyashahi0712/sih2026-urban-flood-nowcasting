"""Deterministic ensemble executor (Phase 9, Step 2).

Executes the ensemble over the locked Phase 8B chain.
"""

from __future__ import annotations

from typing import Dict, Optional

from .hydraulic_integrated_orchestrator import IntegratedRunResult
from .kushak_evidence_model import (
    run_kushak_evidence_scenario,
    CATCHMENT_SCENARIOS,
    KUSHAK_HYDRAULIC_SCENARIOS,
)
from .kushak_scenario_ensemble import KushakEnsembleMember


def execute_ensemble_member(
    member: KushakEnsembleMember,
) -> IntegratedRunResult:
    """Execute one ensemble member through the locked Phase 8B chain.
    """

    # 1. Prepare inputs
    h_scenario = KUSHAK_HYDRAULIC_SCENARIOS[member.hydraulic_scenario_id]
    c_scenario = CATCHMENT_SCENARIOS[member.catchment_scenario_id]
    # 2. Execute via the existing 8B engine
    return run_kushak_evidence_scenario(
        hydraulic_scenario=h_scenario,
        catchment=c_scenario,
        runoff_coefficient=member.runoff_coefficient,
    )
