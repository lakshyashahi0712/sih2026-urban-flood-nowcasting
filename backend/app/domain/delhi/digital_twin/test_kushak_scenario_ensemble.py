"""Tests for Phase 9 scenario ensemble contract."""

import pytest
from .kushak_scenario_ensemble import build_kushak_ensemble, KushakEnsembleMember

def test_ensemble_construction():
    ensemble = build_kushak_ensemble()

    # 3 hydraulic scenarios * 2 catchment scenarios = 6 ensemble members
    assert len(ensemble) == 6

    # Verify deterministic ordering (based on iteration order in build_kushak_ensemble)
    assert ensemble[0].member_id == "KUSHAK-CONSERVATIVE-WORKING_27_66"
    assert ensemble[5].member_id == "KUSHAK-DEGRADED_CAPACITY-SENSITIVITY_28_40"

    # Verify provenance/parameters
    for member in ensemble:
        assert isinstance(member, KushakEnsembleMember)
        assert member.runoff_coefficient == 0.75
