"""Phase 11 Step 3: Historical Rainfall Unknown-Forcing Propagation.

Connects the Phase 11 historical rainfall catalog (`RainfallForcingProfile` / `RainfallBin`)
to UNKNOWN forcing semantics, reusing existing Phase 9 UNKNOWN propagation concepts
while strictly enforcing historical event and station boundaries.

Strict Rules:
- KNOWN numerical forcing remains numerical.
- VERIFIED_ZERO remains numerical zero.
- DERIVED remains numerical with DERIVED provenance.
- UNKNOWN remains strictly UNKNOWN (amount=None).
- UNKNOWN never becomes zero, interpolated, forward/backward-filled, smoothed,
  station-substituted (Palam, Lodhi, Ayanagar, Ridge), event-substituted (EV-01 vs EV-02),
  ERA5-derived, or model-inferred.
- Dependent forcing calculations or runoff conversions cannot produce valid numeric results from UNKNOWN input.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from .kushak_rainfall_forcing import (
    RainfallBin,
    RainfallForcingProfile,
    RainfallProvenance,
    RainfallQuantityType,
    ForcingType,
)
from .kushak_historical_rainfall_catalog import (
    get_historical_rainfall_catalog,
    get_forcing_for_event,
)


@dataclass(frozen=True)
class HistoricalRainfallPropagationBinResult:
    """Immutable propagation result for a single historical rainfall bin."""

    lead_hour: int
    input_amount: Optional[float]
    provenance: RainfallProvenance
    propagated_status: str  # "COMPUTED", "VERIFIED_ZERO", "DERIVED", or "UNKNOWN_BLOCKED"
    effective_amount: Optional[float]  # None if UNKNOWN_BLOCKED; numeric if known/zero/derived
    diagnostic: str


@dataclass(frozen=True)
class HistoricalRainfallPropagationResult:
    """Immutable propagation result for an entire historical rainfall forcing profile."""

    event_id: str
    forcing_id: str
    forcing_type: ForcingType
    bin_results: Tuple[HistoricalRainfallPropagationBinResult, ...]
    overall_status: str  # "COMPUTED" or "BLOCKED_BY_UNKNOWN"
    diagnostics: Tuple[str, ...]
    underlying_provenance: RainfallProvenance = RainfallProvenance.UNKNOWN


def propagate_historical_rainfall_forcing(
    profile: RainfallForcingProfile,
) -> HistoricalRainfallPropagationResult:
    """Propagate historical rainfall forcing profile through UNKNOWN propagation rules.

    Guarantees that:
    1. OBSERVED_DIRECT, DERIVED, and VERIFIED_ZERO retain their numerical values.
    2. UNKNOWN bins strictly retain amount=None and propagated_status="UNKNOWN_BLOCKED".
    3. No cross-station or cross-event substitution occurs.
    4. If any bin is UNKNOWN, overall_status becomes "BLOCKED_BY_UNKNOWN".
    """
    bin_results: List[HistoricalRainfallPropagationBinResult] = []
    diagnostics: List[str] = []
    has_unknown = False

    for b in profile.bins:
        if b.provenance == RainfallProvenance.UNKNOWN:
            has_unknown = True
            bin_results.append(
                HistoricalRainfallPropagationBinResult(
                    lead_hour=b.lead_hour,
                    input_amount=None,
                    provenance=RainfallProvenance.UNKNOWN,
                    propagated_status="UNKNOWN_BLOCKED",
                    effective_amount=None,
                    diagnostic=f"t+{b.lead_hour}h: UNKNOWN preserved (amount=None). No interpolation, zero-fill, or station substitution."
                )
            )
            diagnostics.append(f"Bin t+{b.lead_hour}h is UNKNOWN; blocked from numerical propagation.")
        elif b.provenance == RainfallProvenance.VERIFIED_ZERO:
            bin_results.append(
                HistoricalRainfallPropagationBinResult(
                    lead_hour=b.lead_hour,
                    input_amount=0.0,
                    provenance=RainfallProvenance.VERIFIED_ZERO,
                    propagated_status="VERIFIED_ZERO",
                    effective_amount=0.0,
                    diagnostic=f"t+{b.lead_hour}h: VERIFIED_ZERO maintained as numerical zero."
                )
            )
        elif b.provenance in (RainfallProvenance.OBSERVED_DIRECT, RainfallProvenance.DERIVED):
            bin_results.append(
                HistoricalRainfallPropagationBinResult(
                    lead_hour=b.lead_hour,
                    input_amount=b.amount,
                    provenance=b.provenance,
                    propagated_status="COMPUTED",
                    effective_amount=b.amount,
                    diagnostic=f"t+{b.lead_hour}h: {b.provenance.value} amount={b.amount} {b.units} propagated successfully."
                )
            )
        else:
            raise ValueError(f"Unrecognized rainfall provenance: {b.provenance}")

    overall_status = "BLOCKED_BY_UNKNOWN" if has_unknown else "COMPUTED"
    diagnostics.insert(0, f"Profile {profile.event_id} ({profile.forcing_id}) propagation status: {overall_status}")

    return HistoricalRainfallPropagationResult(
        event_id=profile.event_id,
        forcing_id=profile.forcing_id,
        forcing_type=profile.forcing_type,
        bin_results=tuple(bin_results),
        overall_status=overall_status,
        diagnostics=tuple(diagnostics),
        underlying_provenance=RainfallProvenance.UNKNOWN if has_unknown else RainfallProvenance.OBSERVED_DIRECT,
    )
