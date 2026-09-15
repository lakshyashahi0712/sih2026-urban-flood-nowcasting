"""Tests for Phase 11 Step 3: Historical Rainfall Unknown-Forcing Propagation."""

import pytest

from .kushak_historical_rainfall_catalog import (
    get_ev01_safdarjung_profile,
    get_ev02_safdarjung_profile,
)
from .kushak_historical_rainfall_unknown import (
    propagate_historical_rainfall_forcing,
    HistoricalRainfallPropagationResult,
)
from .kushak_rainfall_forcing import RainfallProvenance, RainfallBin, RainfallForcingProfile, RainfallQuantityType, ForcingType


def test_step3_1_known_forcing_remains_known():
    """1. Known numerical forcing (OBSERVED_DIRECT) remains known and computed."""
    profile = get_ev01_safdarjung_profile()
    res = propagate_historical_rainfall_forcing(profile)
    bin_res = next(b for b in res.bin_results if b.lead_hour == 1)
    assert bin_res.propagated_status == "COMPUTED"
    assert bin_res.effective_amount == 91.0


def test_step3_2_verified_zero_remains_zero():
    """2. VERIFIED_ZERO remains numerical zero."""
    profile = get_ev01_safdarjung_profile()
    res = propagate_historical_rainfall_forcing(profile)
    bin_res = next(b for b in res.bin_results if b.lead_hour == 0)
    assert bin_res.propagated_status == "VERIFIED_ZERO"
    assert bin_res.effective_amount == 0.0


def test_step3_3_derived_remains_derived():
    """3. DERIVED forcing remains numerical with DERIVED provenance."""
    profile = get_ev02_safdarjung_profile()
    res = propagate_historical_rainfall_forcing(profile)
    bin_res = next(b for b in res.bin_results if b.lead_hour == 1)
    assert bin_res.provenance == RainfallProvenance.DERIVED
    assert bin_res.propagated_status == "COMPUTED"
    assert bin_res.effective_amount == 45.0


def test_step3_4_unknown_remains_unknown():
    """4. UNKNOWN remains strictly UNKNOWN."""
    profile = get_ev01_safdarjung_profile()
    res = propagate_historical_rainfall_forcing(profile)
    unknown_bins = [b for b in res.bin_results if b.provenance == RainfallProvenance.UNKNOWN]
    assert len(unknown_bins) >= 2
    for ub in unknown_bins:
        assert ub.propagated_status == "UNKNOWN_BLOCKED"


def test_step3_5_unknown_amount_remains_none():
    """5. UNKNOWN amount remains None."""
    profile = get_ev01_safdarjung_profile()
    res = propagate_historical_rainfall_forcing(profile)
    for ub in [b for b in res.bin_results if b.provenance == RainfallProvenance.UNKNOWN]:
        assert ub.effective_amount is None
        assert ub.input_amount is None


def test_step3_6_unknown_not_converted_to_zero():
    """6. UNKNOWN is never converted to zero."""
    profile = get_ev01_safdarjung_profile()
    res = propagate_historical_rainfall_forcing(profile)
    for ub in [b for b in res.bin_results if b.provenance == RainfallProvenance.UNKNOWN]:
        assert ub.effective_amount != 0.0
        assert ub.propagated_status != "VERIFIED_ZERO"


def test_step3_7_unknown_not_interpolated():
    """7. UNKNOWN is not interpolated from surrounding bins."""
    profile = get_ev01_safdarjung_profile()
    res = propagate_historical_rainfall_forcing(profile)
    for ub in [b for b in res.bin_results if b.provenance == RainfallProvenance.UNKNOWN]:
        assert ub.effective_amount is None
        assert "no interpolation" in ub.diagnostic.lower()


def test_step3_8_unknown_not_forward_filled():
    """8. UNKNOWN is not forward-filled from previous valid bins."""
    profile = get_ev01_safdarjung_profile()
    res = propagate_historical_rainfall_forcing(profile)
    # Bin 1 has 91.0, Bin 2 is UNKNOWN. Bin 2 must not copy 91.0.
    b2 = next(b for b in res.bin_results if b.lead_hour == 2)
    assert b2.effective_amount is None


def test_step3_9_unknown_not_backward_filled():
    """9. UNKNOWN is not backward-filled from succeeding bins."""
    profile = get_ev02_safdarjung_profile()
    res = propagate_historical_rainfall_forcing(profile)
    b2 = next(b for b in res.bin_results if b.lead_hour == 2)
    assert b2.effective_amount is None


def test_step3_10_unknown_not_smoothed():
    """10. UNKNOWN is not smoothed or averaged."""
    profile = get_ev01_safdarjung_profile()
    res = propagate_historical_rainfall_forcing(profile)
    for ub in [b for b in res.bin_results if b.provenance == RainfallProvenance.UNKNOWN]:
        assert ub.effective_amount is None


def test_step3_11_unknown_not_filled_from_another_station():
    """11. UNKNOWN interval at Safdarjung is not filled from other stations (Palam/Lodhi/etc.)."""
    profile = get_ev01_safdarjung_profile()
    res = propagate_historical_rainfall_forcing(profile)
    assert res.overall_status == "BLOCKED_BY_UNKNOWN"


def test_step3_12_unknown_not_filled_from_another_event():
    """12. EV-01 UNKNOWN intervals are not filled from EV-02 data."""
    p1 = get_ev01_safdarjung_profile()
    p2 = get_ev02_safdarjung_profile()
    r1 = propagate_historical_rainfall_forcing(p1)
    r2 = propagate_historical_rainfall_forcing(p2)
    # Both maintain their independent unknown gaps
    assert all(b1.effective_amount == b2.effective_amount for b1, b2 in zip(r1.bin_results, r2.bin_results) if b1.lead_hour >= 2)


def test_step3_13_ev01_partial_profile_unknown_preserved():
    """13. EV-01 partial profile preserves unknown bins explicitly."""
    p1 = get_ev01_safdarjung_profile()
    res = propagate_historical_rainfall_forcing(p1)
    assert res.overall_status == "BLOCKED_BY_UNKNOWN"


def test_step3_14_ev02_partial_profile_unknown_preserved():
    """14. EV-02 partial profile preserves unknown bins explicitly."""
    p2 = get_ev02_safdarjung_profile()
    res = propagate_historical_rainfall_forcing(p2)
    assert res.overall_status == "BLOCKED_BY_UNKNOWN"


def test_step3_15_repeated_propagation_is_deterministic():
    """15. Repeated propagation is deterministic."""
    p1 = get_ev01_safdarjung_profile()
    r1 = propagate_historical_rainfall_forcing(p1)
    r2 = propagate_historical_rainfall_forcing(p1)
    assert r1 == r2


def test_step3_16_dependent_forcing_cannot_produce_valid_numeric_result_from_unknown():
    """16. Dependent forcing calculation cannot produce a valid numeric result from UNKNOWN input."""
    p1 = get_ev01_safdarjung_profile()
    res = propagate_historical_rainfall_forcing(p1)
    assert res.overall_status == "BLOCKED_BY_UNKNOWN"
    # Verify no downstream calculation can treat UNKNOWN as numeric
    for b in res.bin_results:
        if b.provenance == RainfallProvenance.UNKNOWN:
            assert b.effective_amount is None


def test_step3_17_propagation_contract_reuses_existing_semantics():
    """17. Propagation contract aligns with existing UNKNOWN and provenance definitions."""
    p1 = get_ev01_safdarjung_profile()
    res = propagate_historical_rainfall_forcing(p1)
    assert res.underlying_provenance == RainfallProvenance.UNKNOWN


def test_step3_18_unknown_is_not_replaced_by_neighbor_station():
    """18. UNKNOWN is not replaced by spatial or neighbor station substitution."""
    p1 = get_ev01_safdarjung_profile()
    res = propagate_historical_rainfall_forcing(p1)
    for b in res.bin_results:
        if b.lead_hour >= 2:
            assert b.effective_amount is None
            assert "station substitution" in b.diagnostic.lower()
