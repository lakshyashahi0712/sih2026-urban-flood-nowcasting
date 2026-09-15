"""Tests for Phase 11 Step 4: Deterministic Rainfall-to-Runoff Ensemble Driver."""

import pytest
from datetime import datetime, timedelta, timezone

from .kushak_rainfall_runoff_ensemble import (
    run_kushak_rainfall_runoff_ensemble,
    KushakRainfallRunoffEnsembleResult,
)
from .kushak_historical_rainfall_catalog import (
    get_ev01_safdarjung_profile,
    get_ev02_safdarjung_profile,
)
from .kushak_scenario_ensemble import build_kushak_ensemble, SCENARIO_RUNOFF_C
from .kushak_evidence_model import CATCHMENT_SCENARIOS
from .models import ProvenanceStatus
from .hydraulic_time_state import SimulationTimestep

UTC = timezone.utc
T0 = datetime(2024, 6, 28, 5, 0, tzinfo=UTC)


def make_timesteps(count: int = 4, dt_seconds: float = 3600.0) -> list[SimulationTimestep]:
    """Helper to create test simulation timesteps."""
    timesteps = []
    t = T0
    for _ in range(count):
        timesteps.append(SimulationTimestep(start=t, end=t + timedelta(seconds=dt_seconds)))
        t = timesteps[-1].end
    return timesteps


def test_step4_1_ensemble_member_count():
    """1. Ensemble contains exactly 6 deterministic members (3 hydraulic × 2 catchment)."""
    members = build_kushak_ensemble()
    assert len(members) == 6


def test_step4_2_runoff_coefficient_is_0_75():
    """2. Runoff coefficient is strictly 0.75 across all ensemble members."""
    for m in build_kushak_ensemble():
        assert m.runoff_coefficient == SCENARIO_RUNOFF_C
        assert m.runoff_coefficient == 0.75


def test_step4_3_catchment_scenarios_present():
    """3. Catchment scenarios WORKING_27_66 and SENSITIVITY_28_40 are present and correct."""
    assert "WORKING_27_66" in CATCHMENT_SCENARIOS
    assert "SENSITIVITY_28_40" in CATCHMENT_SCENARIOS
    assert CATCHMENT_SCENARIOS["WORKING_27_66"].area_km2 == 27.66
    assert CATCHMENT_SCENARIOS["SENSITIVITY_28_40"].area_km2 == 28.40


def test_step4_4_ev01_ensemble_run_status():
    """4. EV-01 ensemble run correctly propagates overall BLOCKED_BY_UNKNOWN status."""
    profile = get_ev01_safdarjung_profile()
    timesteps = make_timesteps(len(profile.bins))
    res = run_kushak_rainfall_runoff_ensemble(profile, timesteps)
    assert res.overall_status == "BLOCKED_BY_UNKNOWN"
    assert len(res.member_runs) == 6


def test_step4_5_ev02_ensemble_run_status():
    """5. EV-02 ensemble run correctly propagates overall BLOCKED_BY_UNKNOWN status."""
    profile = get_ev02_safdarjung_profile()
    timesteps = make_timesteps(len(profile.bins))
    res = run_kushak_rainfall_runoff_ensemble(profile, timesteps)
    assert res.overall_status == "BLOCKED_BY_UNKNOWN"
    assert len(res.member_runs) == 6


def test_step4_6_computed_step_has_valid_runoff():
    """6. Computed rainfall step (t+1h for EV-01: 91.0 mm/h) produces valid numeric runoff."""
    profile = get_ev01_safdarjung_profile()
    timesteps = make_timesteps(len(profile.bins))
    res = run_kushak_rainfall_runoff_ensemble(profile, timesteps)
    for mr in res.member_runs:
        assert mr.inflow_result.status == "COMPUTED"
        steps = mr.inflow_result.hydrograph.steps
        # t+1h is index 1
        q = steps[1].discharge_m3_s
        assert q is not None
        assert q > 0.0


def test_step4_7_unknown_step_stays_none():
    """7. UNKNOWN rainfall bins produce None discharge (never zero) across all members."""
    profile = get_ev01_safdarjung_profile()
    timesteps = make_timesteps(len(profile.bins))
    res = run_kushak_rainfall_runoff_ensemble(profile, timesteps)
    for mr in res.member_runs:
        steps = mr.inflow_result.hydrograph.steps
        # t+2h and t+3h are UNKNOWN
        assert steps[2].discharge_m3_s is None
        assert steps[3].discharge_m3_s is None


def test_step4_8_verified_zero_step_is_zero():
    """8. VERIFIED_ZERO rainfall bin produces 0.0 discharge."""
    profile = get_ev01_safdarjung_profile()
    timesteps = make_timesteps(len(profile.bins))
    res = run_kushak_rainfall_runoff_ensemble(profile, timesteps)
    for mr in res.member_runs:
        steps = mr.inflow_result.hydrograph.steps
        # t+0h is VERIFIED_ZERO
        assert steps[0].discharge_m3_s == 0.0


def test_step4_9_sensitivity_catchment_higher_inflow():
    """9. Sensitivity catchment (28.40 km²) produces higher inflow than working catchment (27.66 km²)."""
    profile = get_ev01_safdarjung_profile()
    timesteps = make_timesteps(len(profile.bins))
    res = run_kushak_rainfall_runoff_ensemble(profile, timesteps)

    # Find a working member and its corresponding sensitivity member
    working_runs = [mr for mr in res.member_runs if "WORKING_27_66" in mr.member.member_id]
    sens_runs = [mr for mr in res.member_runs if "SENSITIVITY_28_40" in mr.member.member_id]

    assert len(working_runs) == 3
    assert len(sens_runs) == 3

    for wr, sr in zip(working_runs, sens_runs):
        q_work = wr.inflow_result.hydrograph.steps[1].discharge_m3_s
        q_sens = sr.inflow_result.hydrograph.steps[1].discharge_m3_s
        assert q_sens > q_work
        # Ratio should equal 28.40 / 27.66
        assert q_sens / q_work == pytest.approx(28.40 / 27.66)


def test_step4_10_ev02_derived_runoff():
    """10. EV-02 derived 3-hour increment (45.0 mm) produces valid numeric runoff across members."""
    profile = get_ev02_safdarjung_profile()
    timesteps = make_timesteps(len(profile.bins))
    res = run_kushak_rainfall_runoff_ensemble(profile, timesteps)
    for mr in res.member_runs:
        q = mr.inflow_result.hydrograph.steps[1].discharge_m3_s
        assert q is not None
        assert q > 0.0


def test_step4_11_repeated_ensemble_run_is_deterministic():
    """11. Repeated ensemble runs are deterministic and produce identical results."""
    profile = get_ev01_safdarjung_profile()
    timesteps = make_timesteps(len(profile.bins))
    res1 = run_kushak_rainfall_runoff_ensemble(profile, timesteps)
    res2 = run_kushak_rainfall_runoff_ensemble(profile, timesteps)
    assert res1 == res2


def test_step4_12_hydrograph_provenance_is_derived():
    """12. Inflow hydrograph provenance is explicitly DERIVED."""
    profile = get_ev01_safdarjung_profile()
    timesteps = make_timesteps(len(profile.bins))
    res = run_kushak_rainfall_runoff_ensemble(profile, timesteps)
    for mr in res.member_runs:
        assert mr.inflow_result.hydrograph.provenance == ProvenanceStatus.DERIVED


def test_step4_13_member_ids_naming_convention():
    """13. Ensemble member IDs follow the KUSHAK-<hydraulic>-<catchment> convention."""
    members = build_kushak_ensemble()
    for m in members:
        assert m.member_id.startswith("KUSHAK-")
        assert any(h in m.member_id for h in ("CONSERVATIVE", "CENTRAL", "DEGRADED_CAPACITY"))
        assert any(c in m.member_id for c in ("WORKING_27_66", "SENSITIVITY_28_40"))


def test_step4_14_hydraulic_scenario_differences_recorded():
    """14. Hydraulic scenarios are correctly recorded on members."""
    members = build_kushak_ensemble()
    hyd_ids = {m.hydraulic_scenario_id for m in members}
    assert hyd_ids == {"CONSERVATIVE", "CENTRAL", "DEGRADED_CAPACITY"}


def test_step4_15_catchment_scenario_provenance_survives():
    """15. Catchment scenario provenance (PROVISIONAL) survives into conversion inputs."""
    profile = get_ev01_safdarjung_profile()
    timesteps = make_timesteps(len(profile.bins))
    res = run_kushak_rainfall_runoff_ensemble(profile, timesteps)
    for mr in res.member_runs:
        diag = mr.inflow_result.diagnostics[-1]
        assert "PROVISIONAL" in diag or "area provenance" in diag


def test_step4_16_runoff_coefficient_provenance_survives():
    """16. Runoff coefficient provenance (ASSUMED) survives into conversion diagnostics."""
    profile = get_ev01_safdarjung_profile()
    timesteps = make_timesteps(len(profile.bins))
    res = run_kushak_rainfall_runoff_ensemble(profile, timesteps)
    for mr in res.member_runs:
        diag = mr.inflow_result.diagnostics[-1]
        assert "ASSUMED" in diag


def test_step4_17_timestep_durations_preserved():
    """17. Timestep durations are preserved exactly; shorter dt yields larger Q (inverse dt)."""
    profile = get_ev01_safdarjung_profile()
    # 1800 s is shorter than default 3600 s; Q should scale by 2.
    res_1800 = run_kushak_rainfall_runoff_ensemble(profile, make_timesteps(len(profile.bins), dt_seconds=1800.0))
    res_3600 = run_kushak_rainfall_runoff_ensemble(profile, make_timesteps(len(profile.bins), dt_seconds=3600.0))
    for mr_1800, mr_3600 in zip(res_1800.member_runs, res_3600.member_runs):
        q_1800 = mr_1800.inflow_result.hydrograph.steps[1].discharge_m3_s
        q_3600 = mr_3600.inflow_result.hydrograph.steps[1].discharge_m3_s
        # Q is inversely proportional to dt: 1800s -> 2x the 3600s value.
        assert q_1800 == pytest.approx(q_3600 * 2.0)


def test_step4_18_no_mutation_of_input_profile():
    """18. Input rainfall profile and timesteps are not mutated during ensemble execution."""
    profile = get_ev01_safdarjung_profile()
    timesteps = make_timesteps(len(profile.bins))
    profile_before = profile
    ts_before = list(timesteps)
    run_kushak_rainfall_runoff_ensemble(profile, timesteps)
    assert profile == profile_before
    assert timesteps == ts_before


def test_step4_19_ensemble_diagnostics_present():
    """19. Ensemble result contains meaningful diagnostics."""
    profile = get_ev01_safdarjung_profile()
    timesteps = make_timesteps(len(profile.bins))
    res = run_kushak_rainfall_runoff_ensemble(profile, timesteps)
    assert len(res.diagnostics) >= 2
    assert profile.event_id in res.diagnostics[0]


def test_step4_20_all_six_members_produce_independent_results():
    """20. All 6 members produce distinct run objects in member_runs."""
    profile = get_ev01_safdarjung_profile()
    timesteps = make_timesteps(len(profile.bins))
    res = run_kushak_rainfall_runoff_ensemble(profile, timesteps)
    member_ids = {mr.member.member_id for mr in res.member_runs}
    assert len(member_ids) == 6
    assert member_ids == {
        "KUSHAK-CONSERVATIVE-WORKING_27_66",
        "KUSHAK-CONSERVATIVE-SENSITIVITY_28_40",
        "KUSHAK-CENTRAL-WORKING_27_66",
        "KUSHAK-CENTRAL-SENSITIVITY_28_40",
        "KUSHAK-DEGRADED_CAPACITY-WORKING_27_66",
        "KUSHAK-DEGRADED_CAPACITY-SENSITIVITY_28_40",
    }
