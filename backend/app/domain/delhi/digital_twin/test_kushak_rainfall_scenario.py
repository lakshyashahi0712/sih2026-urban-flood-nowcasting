"""Focused tests for Phase 7D-19: June 28, 2024 real-event scenario.

OVERLAP CORRECTION: the derived hourly allocations in the source CSV
overlap the directly observed 91.0 mm peak hour, so they are UNKNOWN in
the usable forcing series (never fabricated, never double-counted).
Synthetic/test-only geometry; no calibration of any parameter.
"""

from __future__ import annotations

import pytest

from backend.app.domain.delhi.digital_twin.kushak_rainfall_scenario import (
    BLOCK_OBSERVATIONS,
    FORCING_CSV,
    load_june_2024_forcing,
    run_june_2024_scenario,
)
from backend.app.domain.delhi.digital_twin.models import ProvenanceStatus
from backend.app.domain.delhi.digital_twin.hydraulic_time_state import (
    SimulationResultStatus,
    SimulationState,
    SimulationStateStatus,
)

DERIVED = ProvenanceStatus.DERIVED


def test_overlap_not_double_counted():
    """Test 1: overlapping block + direct peak cannot be double-counted.

    The usable series contains ONLY the direct 91.0 mm hour as non-zero
    rainfall; the CSV's derived allocations (which overlap the direct
    hour or its parent block) are excluded, so no fabricated hourly sum
    can arise.
    """
    forcing = load_june_2024_forcing()
    # Usable non-zero rainfall = the direct hour, exactly once.
    nonzero = [v for v in forcing.depths_mm if v is not None and v > 0]
    assert nonzero == [91.0]
    # The documented CSV column is preserved verbatim but NOT the forcing.
    assert forcing.documented_hourly_sum_mm == pytest.approx(228.1)
    usable_sum = sum(v for v in forcing.depths_mm if v is not None)
    assert usable_sum == pytest.approx(91.0)  # not 228.1, not 91+block


def test_direct_observation_provenance_preserved():
    """Test 2: the direct 91 mm observation retains OBSERVED provenance."""
    forcing = load_june_2024_forcing()
    # 05:00 IST row is the directly observed peak hour.
    assert forcing.timesteps[5].start.isoformat().startswith(
        "2024-06-28T05:00:00+05:30")
    assert forcing.depths_mm[5] == pytest.approx(91.0)
    # It is NOT among the excluded (unusable) rows.
    assert len(forcing.unusable_labels) == 5
    assert forcing.depths_mm[5] is not None
    # The block observations preserve the source classifications.
    direct = [b for b in BLOCK_OBSERVATIONS if b.depth_mm == 91.0]
    assert len(direct) == 1
    assert "OBSERVED_DIRECT" in direct[0].note


def test_unresolved_rainfall_remains_unknown():
    """Test 3: overlap-dependent hours stay UNKNOWN, never fabricated."""
    forcing = load_june_2024_forcing()
    # Derived block-allocation/residual hours: 02:00, 03:00, 04:00,
    # 06:00, 07:00 IST -> UNKNOWN in the usable series.
    for i in (2, 3, 4, 6, 7):
        assert forcing.depths_mm[i] is None, f"hour {i} must stay UNKNOWN"
        # The documented value is preserved verbatim (never destroyed).
        assert forcing.documented_mm[i] is not None
    # Each excluded row carried a "DERIVED SCENARIO — NOT OBSERVED
    # HOURLY RAINFALL" flag, preserved for transparency.
    assert all("DERIVED" in label for label in forcing.unusable_labels)


def test_zero_observations_remain_valid_zero():
    """Test 4: verified zero hours remain valid zeros in the usable series."""
    forcing = load_june_2024_forcing()
    assert len(forcing.depths_mm) == 24
    for i in (0, 1, 8, 12, 23):  # verified-zero hours
        assert forcing.depths_mm[i] == 0.0
        assert forcing.timesteps[i].start.tzinfo is not None


def test_no_false_hourly_event_total():
    """Test 5: the scenario cannot silently produce a false 228.1 mm sum.

    The forcing's usable series sums to the direct observation only; the
    228.1 mm column sum is exposed ONLY as documented_mm (labelled not a
    valid event total), and the mass-balance basis refers to the source
    block observations.
    """
    forcing = load_june_2024_forcing()
    assert forcing.documented_hourly_sum_mm == pytest.approx(228.1)
    usable_sum = sum(v for v in forcing.depths_mm if v is not None)
    assert usable_sum != pytest.approx(228.1)
    assert usable_sum == pytest.approx(91.0)
    run = run_june_2024_scenario()
    # The run stops transparently at the first UNKNOWN timestep (PARTIAL);
    # no full-event hydraulic accumulation from a partial forcing.
    assert run.hydraulic is not None
    assert run.hydraulic.simulation_status == SimulationResultStatus.PARTIAL
    # No 228.1 mm event volume accumulates: only hours before the first
    # UNKNOWN step (00:00, 01:00 — valid zeros) are computed, so the last
    # computed state's storage is unchanged (Q=0, outflow=0); the blocked
    # state carries storage None per contract.
    assert run.hydraulic.states[-1].storage_m3 is None
    assert run.hydraulic.states[1].storage_m3 == pytest.approx(10000.0)
    # Mass-balance basis names the source observations, not hourly sums.
    assert "148.5" in run.scenario_parameters["rainfall_basis"]
    assert "91.0" in run.scenario_parameters["rainfall_basis"]
    assert "79.6" in run.scenario_parameters["rainfall_basis"]


def test_conversion_unchanged_and_blocks_transparently():
    """Test 6: the 7D-17 conversion is unchanged; UNKNOWN hours block.

    The corrected forcing drives the existing rainfall_to_inflow: the
    direct hour computes Q, verified zeros compute Q=0, UNKNOWN hours
    yield None discharge, and downstream the missing hours block
    transparently (never zero-filled).
    """
    from backend.app.domain.delhi.digital_twin.rainfall_to_inflow import (
        rainfall_to_inflow,
    )
    from backend.app.domain.delhi.digital_twin.hydraulic_hydrograph_driver import (
        run_hydrograph_simulation,
    )
    from backend.app.domain.delhi.digital_twin.kushak_rainfall_scenario import (
        synthetic_scenario_profile,
    )

    forcing = load_june_2024_forcing()
    conversion = rainfall_to_inflow(
        timesteps=forcing.timesteps,
        rainfall_depth_mm=forcing.depths_mm,
        catchment_area_km2=27.66,
        runoff_coefficient=0.75,
    )
    assert conversion.status == "COMPUTED"
    assert conversion.hydrograph.provenance == DERIVED
    # Direct hour computes the only non-zero Q (91 mm over 3600 s).
    assert conversion.hydrograph.steps[5].discharge_m3_s == pytest.approx(
        0.75 * 0.091 * 27.66e6 / 3600.0)
    # UNKNOWN hours yield None discharge (never zero, never fabricated).
    for i in (2, 3, 4, 6, 7):
        assert conversion.hydrograph.steps[i].discharge_m3_s is None
    assert conversion.hydrograph.missing_step_count == 5
    # Downstream, the first UNKNOWN hour blocks its timestep.
    initial = SimulationState(
        timestamp=forcing.timesteps[0].start,
        location_id="SCENARIO",
        status=SimulationStateStatus.COMPUTED,
        stage_m=102.0, storage_m3=10000.0,
        provenance=DERIVED,
    )
    result = run_hydrograph_simulation(
        initial_state=initial,
        timesteps=forcing.timesteps,
        hydrograph=conversion.hydrograph,
        profile=synthetic_scenario_profile(),
        manning_n=0.015, slope=0.005,
        explicit_outflow_m3_s=0.0,
        lateral_inflow_m3_s=0.0,
    )
    # Hours 0-1 (valid zeros) and 2 (UNKNOWN): step 2 is the first block.
    assert result.simulation_status == SimulationResultStatus.PARTIAL
    assert result.states[2].status == SimulationStateStatus.BLOCKED_MISSING_INPUT
    assert result.states[2].storage_m3 is None


def test_documentation_of_uncertainty():
    """Scenario parameters disclose the remaining rainfall uncertainty."""
    run = run_june_2024_scenario()
    basis = run.scenario_parameters["rainfall_basis"]
    assert "UNKNOWN" in basis
    assert "uniquely allocated" in basis


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
