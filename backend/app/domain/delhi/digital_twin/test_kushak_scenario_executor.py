"""Tests for Phase 9 ensemble executor."""

import pytest
from .kushak_scenario_ensemble import build_kushak_ensemble
from .kushak_scenario_executor import execute_ensemble_member
from .hydraulic_integrated_orchestrator import IntegratedRunResult
from .hydraulic_integrated_orchestrator import IntegratedRunResult

def test_ensemble_execution():
    ensemble = build_kushak_ensemble()

    # Run all members
    for member in ensemble:
        result = execute_ensemble_member(member)
        assert isinstance(result, IntegratedRunResult)
        assert result.rainfall_conversion.status == "COMPUTED"
        if result.hydraulic_run:
            assert result.hydraulic_run.simulation_status in ["COMPLETE", "PARTIAL"]
