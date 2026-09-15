"""Phase 11 Step 2: Historical Event Rainfall Forcing Catalog.

Binds existing verified rainfall evidence (EV-01: June 28, 2024; EV-02: July 8-10, 2023)
to the Phase 11 Step 1 Rainfall Forcing schema.

Strict rules:
- Authoritative evidence only (Safdarjung 228.1 mm/24h for EV-01, 153 mm/24h for EV-02).
- Preserves explicit provenance: OBSERVED_DIRECT, VERIFIED_ZERO, DERIVED, UNKNOWN.
- Temporal discipline: Documented 3-hour increments remain 3-hour intervals (no fabricated hourly splitting).
- Event separation: EV-01 and EV-02 remain strictly separated (no pooling, no cross-event substitution).
- Station discipline: Safdarjung station identity preserved (no cross-station substitution, no spatial interpolation).
- Unknown gaps: Unresolved intervals remain explicitly UNKNOWN (no zero-fill, no interpolation, no forward/back-fill).
- NOT FORECASTS: Catalog records are HISTORICAL_EVENT.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from .kushak_rainfall_forcing import (
    RainfallBin,
    RainfallForcingProfile,
    RainfallProvenance,
    RainfallQuantityType,
    ForcingType,
)


def get_ev01_safdarjung_profile() -> RainfallForcingProfile:
    """Get authoritative historical rainfall forcing profile for EV-01 (June 28, 2024).

    Safdarjung 228.1 mm / 24h event evidence with direct hourly observation (91.0 mm/h at t+1h),
    derived 3-hour increments, and explicit UNKNOWN gaps.
    """
    return RainfallForcingProfile(
        event_id="EV-01",
        forcing_id="FC-EV01-SAFDARJUNG",
        forcing_type=ForcingType.HISTORICAL_EVENT,
        bins=(
            RainfallBin(
                lead_hour=0,
                amount=0.0,
                quantity_type=RainfallQuantityType.DEPTH_MM,
                units="mm",
                provenance=RainfallProvenance.VERIFIED_ZERO,
                source_reference="Safdarjung IMD Station - Baseline pre-event zero (June 28, 2024)"
            ),
            RainfallBin(
                lead_hour=1,
                amount=91.0,
                quantity_type=RainfallQuantityType.INTENSITY_MM_H,
                units="mm/h",
                provenance=RainfallProvenance.OBSERVED_DIRECT,
                source_reference="Safdarjung IMD Station - Direct 05:00-06:00 observation (91.0 mm/h)"
            ),
            RainfallBin(
                lead_hour=2,
                amount=None,
                quantity_type=RainfallQuantityType.DEPTH_MM,
                units="mm",
                provenance=RainfallProvenance.UNKNOWN,
                source_reference="Unresolved temporal gap - preserved as UNKNOWN (no interpolation)"
            ),
            RainfallBin(
                lead_hour=3,
                amount=None,
                quantity_type=RainfallQuantityType.DEPTH_MM,
                units="mm",
                provenance=RainfallProvenance.UNKNOWN,
                source_reference="Unresolved temporal gap - preserved as UNKNOWN (no interpolation)"
            ),
        ),
        source_reference="Safdarjung 228.1 mm / 24h IMD event evidence and audit matrix",
        diagnostic="EV-01 Safdarjung historical rainfall forcing profile with direct and UNKNOWN bins."
    )


def get_ev02_safdarjung_profile() -> RainfallForcingProfile:
    """Get authoritative historical rainfall forcing profile for EV-02 (July 8-10, 2023).

    Safdarjung 153 mm / 24h event evidence with derived/observed intervals and UNKNOWN gaps.
    """
    return RainfallForcingProfile(
        event_id="EV-02",
        forcing_id="FC-EV02-SAFDARJUNG",
        forcing_type=ForcingType.HISTORICAL_EVENT,
        bins=(
            RainfallBin(
                lead_hour=0,
                amount=0.0,
                quantity_type=RainfallQuantityType.DEPTH_MM,
                units="mm",
                provenance=RainfallProvenance.VERIFIED_ZERO,
                source_reference="Safdarjung IMD Station - Baseline pre-event zero (July 8, 2023)"
            ),
            RainfallBin(
                lead_hour=1,
                amount=45.0,
                quantity_type=RainfallQuantityType.DEPTH_MM,
                units="mm",
                provenance=RainfallProvenance.DERIVED,
                source_reference="Safdarjung IMD Station - Derived 3-hour aggregated increment (not hourly split)"
            ),
            RainfallBin(
                lead_hour=2,
                amount=None,
                quantity_type=RainfallQuantityType.DEPTH_MM,
                units="mm",
                provenance=RainfallProvenance.UNKNOWN,
                source_reference="Unresolved temporal gap - preserved as UNKNOWN"
            ),
            RainfallBin(
                lead_hour=3,
                amount=None,
                quantity_type=RainfallQuantityType.DEPTH_MM,
                units="mm",
                provenance=RainfallProvenance.UNKNOWN,
                source_reference="Unresolved temporal gap - preserved as UNKNOWN"
            ),
        ),
        source_reference="Safdarjung 153 mm / 24h IMD event evidence and audit matrix",
        diagnostic="EV-02 Safdarjung historical rainfall forcing profile with derived and UNKNOWN bins."
    )


def get_historical_rainfall_catalog() -> Dict[str, RainfallForcingProfile]:
    """Retrieve the complete deterministic historical rainfall forcing catalog."""
    return {
        "EV-01": get_ev01_safdarjung_profile(),
        "EV-02": get_ev02_safdarjung_profile(),
    }


def get_forcing_for_event(event_id: str) -> Optional[RainfallForcingProfile]:
    """Retrieve rainfall forcing profile for a specific event ID."""
    return get_historical_rainfall_catalog().get(event_id)
