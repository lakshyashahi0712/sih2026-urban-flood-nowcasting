"""Tests for Phase 11 Step 2: Historical Event Rainfall Forcing Catalog."""

import pytest
from dataclasses import FrozenInstanceError

from .kushak_historical_rainfall_catalog import (
    get_historical_rainfall_catalog,
    get_forcing_for_event,
    get_ev01_safdarjung_profile,
    get_ev02_safdarjung_profile,
)
from .kushak_rainfall_forcing import (
    RainfallBin,
    RainfallForcingProfile,
    RainfallProvenance,
    RainfallQuantityType,
    ForcingType,
)


def test_step2_1_ev01_catalog_presence():
    """1. EV-01 is present in the historical rainfall catalog."""
    catalog = get_historical_rainfall_catalog()
    assert "EV-01" in catalog
    profile = catalog["EV-01"]
    assert profile.event_id == "EV-01"


def test_step2_2_ev02_catalog_presence():
    """2. EV-02 is present in the historical rainfall catalog."""
    catalog = get_historical_rainfall_catalog()
    assert "EV-02" in catalog
    profile = catalog["EV-02"]
    assert profile.event_id == "EV-02"


def test_step2_3_event_separation():
    """3. EV-01 and EV-02 remain strictly separate event records."""
    p1 = get_ev01_safdarjung_profile()
    p2 = get_ev02_safdarjung_profile()
    assert p1.event_id != p2.event_id
    assert p1.forcing_id != p2.forcing_id
    assert p1 != p2


def test_step2_4_station_identity_preservation():
    """4. Safdarjung station identity is explicitly preserved in catalog references."""
    p1 = get_ev01_safdarjung_profile()
    p2 = get_ev02_safdarjung_profile()
    assert "Safdarjung" in p1.bins[0].source_reference or "Safdarjung" in p1.source_reference
    assert "Safdarjung" in p2.bins[0].source_reference or "Safdarjung" in p2.source_reference


def test_step2_5_safdarjung_evidence_ev01():
    """5. EV-01 contains Safdarjung authoritative evidence (e.g. 91.0 mm/h direct observation)."""
    p1 = get_ev01_safdarjung_profile()
    has_direct_91 = any(
        b.amount == 91.0 and b.provenance == RainfallProvenance.OBSERVED_DIRECT
        for b in p1.bins
    )
    assert has_direct_91


def test_step2_6_safdarjung_evidence_ev02():
    """6. EV-02 contains Safdarjung evidence (e.g. derived/observed intervals)."""
    p2 = get_ev02_safdarjung_profile()
    has_derived = any(
        b.amount == 45.0 and b.provenance == RainfallProvenance.DERIVED
        for b in p2.bins
    )
    assert has_derived


def test_step2_7_direct_observation_provenance():
    """7. OBSERVED_DIRECT provenance is correctly assigned and preserved."""
    p1 = get_ev01_safdarjung_profile()
    bin_direct = next(b for b in p1.bins if b.lead_hour == 1)
    assert bin_direct.provenance == RainfallProvenance.OBSERVED_DIRECT
    assert bin_direct.amount == 91.0


def test_step2_8_derived_three_hour_provenance():
    """8. DERIVED provenance is correctly assigned to aggregated/derived intervals."""
    p2 = get_ev02_safdarjung_profile()
    bin_derived = next(b for b in p2.bins if b.lead_hour == 1)
    assert bin_derived.provenance == RainfallProvenance.DERIVED
    assert bin_derived.amount == 45.0


def test_step2_9_verified_zero_provenance():
    """9. VERIFIED_ZERO provenance is correctly assigned to baseline zero bins."""
    p1 = get_ev01_safdarjung_profile()
    bin_zero = next(b for b in p1.bins if b.lead_hour == 0)
    assert bin_zero.provenance == RainfallProvenance.VERIFIED_ZERO
    assert bin_zero.amount == 0.0


def test_step2_10_unknown_interval_preservation():
    """10. Unresolved intervals remain explicitly UNKNOWN with amount=None."""
    p1 = get_ev01_safdarjung_profile()
    unknown_bins = [b for b in p1.bins if b.provenance == RainfallProvenance.UNKNOWN]
    assert len(unknown_bins) >= 2
    for ub in unknown_bins:
        assert ub.amount is None


def test_step2_11_no_hourly_splitting_of_three_hour_totals():
    """11. Documented aggregates are not fabricated into artificial hourly values."""
    p2 = get_ev02_safdarjung_profile()
    # Lead hour 1 is a 3-hour aggregated interval value (45.0 mm), not split into three 15mm bins
    bin_agg = next(b for b in p2.bins if b.lead_hour == 1)
    assert bin_agg.amount == 45.0
    # No lead_hour 2 or 3 has fabricated split amounts (they are UNKNOWN)
    assert p2.bins[2].amount is None
    assert p2.bins[3].amount is None


def test_step2_12_no_cross_station_substitution():
    """12. Station identities are distinct and not cross-substituted."""
    p1 = get_ev01_safdarjung_profile()
    assert "Palam" not in p1.forcing_id
    assert "SAFDARJUNG" in p1.forcing_id


def test_step2_13_no_cross_event_substitution():
    """13. EV-01 and EV-02 data are not cross-substituted or pooled."""
    catalog = get_historical_rainfall_catalog()
    assert catalog["EV-01"] != catalog["EV-02"]


def test_step2_14_temporal_resolution_preservation():
    """14. Temporal resolution metadata and lead hours travel correctly with bins."""
    p1 = get_ev01_safdarjung_profile()
    hours = [b.lead_hour for b in p1.bins]
    assert hours == [0, 1, 2, 3]


def test_step2_15_historical_forcing_cannot_silently_become_forecast():
    """15. Historical forcing type is explicitly HISTORICAL_EVENT and never forecast."""
    p1 = get_ev01_safdarjung_profile()
    p2 = get_ev02_safdarjung_profile()
    assert p1.forcing_type == ForcingType.HISTORICAL_EVENT
    assert p2.forcing_type == ForcingType.HISTORICAL_EVENT
    assert p1.forcing_type != ForcingType.FORECAST_FORCING


def test_step2_16_deterministic_catalog_construction():
    """16. Catalog construction is deterministic and consistent across calls."""
    cat1 = get_historical_rainfall_catalog()
    cat2 = get_historical_rainfall_catalog()
    assert cat1["EV-01"] == cat2["EV-01"]
    assert cat1["EV-02"] == cat2["EV-02"]


def test_step2_17_source_reference_preservation():
    """17. Source and evidence references are preserved on catalog items."""
    p1 = get_ev01_safdarjung_profile()
    assert p1.source_reference is not None
    assert len(p1.source_reference) > 0


def test_step2_18_repeated_construction_identical():
    """18. Repeated profile retrieval produces identical profiles."""
    p1_a = get_ev01_safdarjung_profile()
    p1_b = get_ev01_safdarjung_profile()
    assert p1_a == p1_b


def test_step2_19_retrieval_by_event_id():
    """19. get_forcing_for_event correctly retrieves valid events and returns None for unknown."""
    assert get_forcing_for_event("EV-01") is not None
    assert get_forcing_for_event("EV-02") is not None
    assert get_forcing_for_event("EV-999") is None
