"""Tests for Phase 11 Step 1: 0-3 Hour Rainfall Forcing Schema and Provenance Contract."""

import pytest
from dataclasses import FrozenInstanceError

from .kushak_rainfall_forcing import (
    RainfallBin,
    RainfallForcingProfile,
    RainfallProvenance,
    RainfallQuantityType,
    ForcingType,
)


def test_step1_1_valid_four_bin_profile():
    """1. Valid four-bin 0-3h profile constructs correctly."""
    profile = RainfallForcingProfile(
        event_id="EV-2024-06-28",
        forcing_id="FC-01",
        forcing_type=ForcingType.HISTORICAL_EVENT,
        bins=(
            RainfallBin(lead_hour=0, amount=0.0, quantity_type=RainfallQuantityType.DEPTH_MM, units="mm", provenance=RainfallProvenance.VERIFIED_ZERO),
            RainfallBin(lead_hour=1, amount=91.0, quantity_type=RainfallQuantityType.DEPTH_MM, units="mm", provenance=RainfallProvenance.OBSERVED_DIRECT),
            RainfallBin(lead_hour=2, amount=None, quantity_type=RainfallQuantityType.DEPTH_MM, units="mm", provenance=RainfallProvenance.UNKNOWN),
            RainfallBin(lead_hour=3, amount=None, quantity_type=RainfallQuantityType.DEPTH_MM, units="mm", provenance=RainfallProvenance.UNKNOWN),
        ),
    )
    assert len(profile.bins) == 4
    assert profile.bins[1].amount == 91.0
    assert profile.bins[2].amount is None
    assert profile.bins[2].provenance == RainfallProvenance.UNKNOWN


def test_step1_2_valid_observed_forcing():
    """2. Valid observed forcing bin constructs correctly."""
    b = RainfallBin(lead_hour=0, amount=15.5, quantity_type=RainfallQuantityType.DEPTH_MM, units="mm", provenance=RainfallProvenance.OBSERVED_DIRECT)
    assert b.amount == 15.5
    assert b.provenance == RainfallProvenance.OBSERVED_DIRECT


def test_step1_3_valid_derived_forcing():
    """3. Valid derived forcing bin constructs correctly."""
    b = RainfallBin(lead_hour=1, amount=25.0, quantity_type=RainfallQuantityType.INTENSITY_MM_H, units="mm/h", provenance=RainfallProvenance.DERIVED)
    assert b.amount == 25.0
    assert b.provenance == RainfallProvenance.DERIVED


def test_step1_4_valid_verified_zero_forcing():
    """4. Valid verified zero forcing bin constructs correctly."""
    b = RainfallBin(lead_hour=0, amount=0.0, quantity_type=RainfallQuantityType.DEPTH_MM, units="mm", provenance=RainfallProvenance.VERIFIED_ZERO)
    assert b.amount == 0.0
    assert b.provenance == RainfallProvenance.VERIFIED_ZERO


def test_step1_5_explicit_unknown_bin():
    """5. Explicit UNKNOWN bin has amount=None and UNKNOWN provenance."""
    b = RainfallBin(lead_hour=2, amount=None, quantity_type=RainfallQuantityType.DEPTH_MM, units="mm", provenance=RainfallProvenance.UNKNOWN)
    assert b.amount is None
    assert b.provenance == RainfallProvenance.UNKNOWN


def test_step1_6_negative_lead_hour_rejected():
    """6. Negative lead hour is rejected."""
    with pytest.raises(ValueError):
        RainfallBin(lead_hour=-1, amount=10.0, quantity_type=RainfallQuantityType.DEPTH_MM, units="mm", provenance=RainfallProvenance.OBSERVED_DIRECT)


def test_step1_7_duplicate_lead_hour_rejected():
    """7. Duplicate lead hours in a profile are rejected."""
    with pytest.raises(ValueError):
        RainfallForcingProfile(
            event_id="EV-DUP",
            forcing_id="FC-DUP",
            forcing_type=ForcingType.HISTORICAL_EVENT,
            bins=(
                RainfallBin(lead_hour=0, amount=0.0, quantity_type=RainfallQuantityType.DEPTH_MM, units="mm", provenance=RainfallProvenance.VERIFIED_ZERO),
                RainfallBin(lead_hour=0, amount=10.0, quantity_type=RainfallQuantityType.DEPTH_MM, units="mm", provenance=RainfallProvenance.OBSERVED_DIRECT),
            ),
        )


def test_step1_8_non_finite_rainfall_rejected():
    """8. Non-finite rainfall amounts (NaN, Inf) are rejected."""
    with pytest.raises(ValueError):
        RainfallBin(lead_hour=0, amount=float("nan"), quantity_type=RainfallQuantityType.DEPTH_MM, units="mm", provenance=RainfallProvenance.OBSERVED_DIRECT)
    with pytest.raises(ValueError):
        RainfallBin(lead_hour=0, amount=float("inf"), quantity_type=RainfallQuantityType.DEPTH_MM, units="mm", provenance=RainfallProvenance.OBSERVED_DIRECT)


def test_step1_9_invalid_unit_rejected():
    """9. Invalid units are rejected."""
    with pytest.raises(ValueError):
        RainfallBin(lead_hour=0, amount=10.0, quantity_type=RainfallQuantityType.DEPTH_MM, units="inches", provenance=RainfallProvenance.OBSERVED_DIRECT)


def test_step1_10_missing_provenance_requirement():
    """10. Non-UNKNOWN bin without amount or UNKNOWN bin with amount are rejected."""
    with pytest.raises(ValueError):
        RainfallBin(lead_hour=0, amount=None, quantity_type=RainfallQuantityType.DEPTH_MM, units="mm", provenance=RainfallProvenance.OBSERVED_DIRECT)
    with pytest.raises(ValueError):
        RainfallBin(lead_hour=0, amount=10.0, quantity_type=RainfallQuantityType.DEPTH_MM, units="mm", provenance=RainfallProvenance.UNKNOWN)


def test_step1_11_unknown_is_not_converted_to_zero():
    """11. UNKNOWN remains None (not converted to zero)."""
    b = RainfallBin(lead_hour=2, amount=None, quantity_type=RainfallQuantityType.DEPTH_MM, units="mm", provenance=RainfallProvenance.UNKNOWN)
    assert b.amount is None
    assert b.provenance != RainfallProvenance.VERIFIED_ZERO


def test_step1_12_unknown_is_not_interpolated():
    """12. Schema requires explicit bins and does not perform silent interpolation."""
    profile = RainfallForcingProfile(
        event_id="EV-GAP",
        forcing_id="FC-GAP",
        forcing_type=ForcingType.HISTORICAL_EVENT,
        bins=(
            RainfallBin(lead_hour=0, amount=10.0, quantity_type=RainfallQuantityType.DEPTH_MM, units="mm", provenance=RainfallProvenance.OBSERVED_DIRECT),
            RainfallBin(lead_hour=1, amount=None, quantity_type=RainfallQuantityType.DEPTH_MM, units="mm", provenance=RainfallProvenance.UNKNOWN),
            RainfallBin(lead_hour=2, amount=15.0, quantity_type=RainfallQuantityType.DEPTH_MM, units="mm", provenance=RainfallProvenance.OBSERVED_DIRECT),
        ),
    )
    assert profile.bins[1].amount is None  # no interpolation occurred


def test_step1_13_depth_intensity_semantics_distinct():
    """13. Depth (mm) and intensity (mm/h) semantics remain distinct and validated."""
    b_depth = RainfallBin(lead_hour=0, amount=10.0, quantity_type=RainfallQuantityType.DEPTH_MM, units="mm", provenance=RainfallProvenance.OBSERVED_DIRECT)
    b_intensity = RainfallBin(lead_hour=0, amount=10.0, quantity_type=RainfallQuantityType.INTENSITY_MM_H, units="mm/h", provenance=RainfallProvenance.OBSERVED_DIRECT)
    assert b_depth.quantity_type != b_intensity.quantity_type

    with pytest.raises(ValueError):
        RainfallBin(lead_hour=0, amount=10.0, quantity_type=RainfallQuantityType.DEPTH_MM, units="mm/h", provenance=RainfallProvenance.OBSERVED_DIRECT)


def test_step1_14_deterministic_summary_string():
    """14. Summary string generates deterministic output."""
    profile = RainfallForcingProfile(
        event_id="EV-SUM",
        forcing_id="FC-SUM",
        forcing_type=ForcingType.HISTORICAL_EVENT,
        bins=(
            RainfallBin(lead_hour=0, amount=5.0, quantity_type=RainfallQuantityType.DEPTH_MM, units="mm", provenance=RainfallProvenance.OBSERVED_DIRECT),
        ),
    )
    s1 = profile.summary_string()
    s2 = profile.summary_string()
    assert s1 == s2
    assert "EV-SUM" in s1
    assert "t+0h" in s1


def test_step1_15_immutable_object_behavior():
    """15. RainfallBin and RainfallForcingProfile are immutable (frozen)."""
    b = RainfallBin(lead_hour=0, amount=5.0, quantity_type=RainfallQuantityType.DEPTH_MM, units="mm", provenance=RainfallProvenance.OBSERVED_DIRECT)
    with pytest.raises(FrozenInstanceError):
        b.amount = 10.0  # type: ignore

    profile = RainfallForcingProfile(
        event_id="EV-IMMUT",
        forcing_id="FC-IMMUT",
        forcing_type=ForcingType.HISTORICAL_EVENT,
        bins=(b,),
    )
    with pytest.raises(FrozenInstanceError):
        profile.event_id = "OTHER"  # type: ignore


def test_step1_16_invalid_timestep_ordering_rejected():
    """16. Out-of-order lead hours are rejected."""
    with pytest.raises(ValueError):
        RainfallForcingProfile(
            event_id="EV-ORDER",
            forcing_id="FC-ORDER",
            forcing_type=ForcingType.HISTORICAL_EVENT,
            bins=(
                RainfallBin(lead_hour=2, amount=5.0, quantity_type=RainfallQuantityType.DEPTH_MM, units="mm", provenance=RainfallProvenance.OBSERVED_DIRECT),
                RainfallBin(lead_hour=1, amount=5.0, quantity_type=RainfallQuantityType.DEPTH_MM, units="mm", provenance=RainfallProvenance.OBSERVED_DIRECT),
            ),
        )


def test_step1_17_incomplete_profile_represented_explicitly():
    """17. Incomplete 0-3h profile is represented explicitly without padding or completion."""
    profile = RainfallForcingProfile(
        event_id="EV-INCOMP",
        forcing_id="FC-INCOMP",
        forcing_type=ForcingType.HISTORICAL_EVENT,
        bins=(
            RainfallBin(lead_hour=0, amount=10.0, quantity_type=RainfallQuantityType.DEPTH_MM, units="mm", provenance=RainfallProvenance.OBSERVED_DIRECT),
            RainfallBin(lead_hour=1, amount=None, quantity_type=RainfallQuantityType.DEPTH_MM, units="mm", provenance=RainfallProvenance.UNKNOWN),
        ),
    )
    assert len(profile.bins) == 2
    assert profile.bins[-1].provenance == RainfallProvenance.UNKNOWN


def test_step1_18_repeated_construction_identical():
    """18. Repeated identical construction produces identical results."""
    bins = (
        RainfallBin(lead_hour=0, amount=1.0, quantity_type=RainfallQuantityType.DEPTH_MM, units="mm", provenance=RainfallProvenance.OBSERVED_DIRECT),
        RainfallBin(lead_hour=1, amount=2.0, quantity_type=RainfallQuantityType.DEPTH_MM, units="mm", provenance=RainfallProvenance.OBSERVED_DIRECT),
    )
    p1 = RainfallForcingProfile(event_id="E", forcing_id="F", forcing_type=ForcingType.HISTORICAL_EVENT, bins=bins)
    p2 = RainfallForcingProfile(event_id="E", forcing_id="F", forcing_type=ForcingType.HISTORICAL_EVENT, bins=bins)
    assert p1 == p2


def test_step1_19_no_forecast_claim_from_historical_forcing():
    """19. Historical forcing type does not imply or claim forecast status."""
    profile = RainfallForcingProfile(
        event_id="EV-HIST",
        forcing_id="FC-HIST",
        forcing_type=ForcingType.HISTORICAL_EVENT,
        bins=(
            RainfallBin(lead_hour=0, amount=10.0, quantity_type=RainfallQuantityType.DEPTH_MM, units="mm", provenance=RainfallProvenance.OBSERVED_DIRECT),
        ),
    )
    assert profile.forcing_type == ForcingType.HISTORICAL_EVENT
    assert profile.forcing_type != ForcingType.FORECAST_FORCING


def test_step1_20_provenance_survives_construction():
    """20. Provenance states survive construction precisely."""
    b = RainfallBin(lead_hour=0, amount=12.3, quantity_type=RainfallQuantityType.DEPTH_MM, units="mm", provenance=RainfallProvenance.DERIVED)
    assert b.provenance == RainfallProvenance.DERIVED
