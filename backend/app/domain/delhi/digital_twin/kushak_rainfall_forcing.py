"""Phase 11 Step 1: 0-3 Hour Rainfall Forcing Schema and Provenance Contract.

Provides a deterministic, provenance-aware schema for 0-3 hour rainfall forcing profiles
across t+0h, t+1h, t+2h, and t+3h bins.

Strict rules:
- DATA CONTRACT ONLY. Does NOT claim these values are forecasts.
- Uses existing repository provenance states: OBSERVED_DIRECT, VERIFIED_ZERO, DERIVED, UNKNOWN.
- Reuses existing ProvenanceStatus where compatible.
- Explicitly distinguishes depth (mm) from intensity (mm/h).
- UNKNOWN is a first-class state: never zero-filled, never interpolated, never forward/back-filled.
- Rejects negative lead hours, duplicate lead hours, non-finite rainfall, invalid units, and out-of-order timesteps.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple, Union

from .models import ProvenanceStatus


class RainfallProvenance(str, Enum):
    """Permitted rainfall forcing provenance states."""

    OBSERVED_DIRECT = "OBSERVED_DIRECT"
    VERIFIED_ZERO = "VERIFIED_ZERO"
    DERIVED = "DERIVED"
    UNKNOWN = "UNKNOWN"


class RainfallQuantityType(str, Enum):
    """Explicitly distinguish rainfall depth from rainfall intensity."""

    DEPTH_MM = "DEPTH_MM"
    INTENSITY_MM_H = "INTENSITY_MM_H"


class ForcingType(str, Enum):
    """Classification of forcing profile basis."""

    HISTORICAL_EVENT = "HISTORICAL_EVENT"
    FORECAST_FORCING = "FORECAST_FORCING"
    DERIVED_SCENARIO = "DERIVED_SCENARIO"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class RainfallBin:
    """Immutable single bin representing rainfall at a specific relative lead hour (t+0h, t+1h, etc.)."""

    lead_hour: int  # 0, 1, 2, 3, etc.
    amount: Optional[float]  # None if UNKNOWN; non-negative finite float if known
    quantity_type: RainfallQuantityType
    units: str  # "mm" for DEPTH_MM, "mm/h" for INTENSITY_MM_H
    provenance: RainfallProvenance
    source_reference: Optional[str] = None

    def __post_init__(self) -> None:
        if self.lead_hour < 0:
            raise ValueError(f"Lead hour cannot be negative (got {self.lead_hour})")
        if self.units not in ("mm", "mm/h"):
            raise ValueError(f"Invalid units {self.units!r}. Must be 'mm' or 'mm/h'.")
        if self.quantity_type == RainfallQuantityType.DEPTH_MM and self.units != "mm":
            raise ValueError("Quantity type DEPTH_MM requires units 'mm'")
        if self.quantity_type == RainfallQuantityType.INTENSITY_MM_H and self.units != "mm/h":
            raise ValueError("Quantity type INTENSITY_MM_H requires units 'mm/h'")

        if self.provenance == RainfallProvenance.UNKNOWN:
            if self.amount is not None:
                raise ValueError("UNKNOWN provenance bin must have amount=None (no fabricated values)")
        else:
            if self.amount is None:
                raise ValueError(f"Non-UNKNOWN provenance {self.provenance} requires a non-null amount")
            if not isinstance(self.amount, (int, float)) or not (self.amount == self.amount) or self.amount == float("inf") or self.amount == float("-inf"):
                raise ValueError(f"Rainfall amount must be a finite numeric value (got {self.amount})")
            if self.amount < 0:
                raise ValueError(f"Rainfall amount cannot be negative (got {self.amount})")


@dataclass(frozen=True)
class RainfallForcingProfile:
    """Immutable 0-3 hour rainfall forcing profile containing ordered lead-hour bins."""

    event_id: str
    forcing_id: str
    forcing_type: ForcingType
    bins: Tuple[RainfallBin, ...]
    source_reference: Optional[str] = None
    diagnostic: str = ""

    def __post_init__(self) -> None:
        if not self.bins:
            raise ValueError("Forcing profile must contain at least one rainfall bin")

        seen_hours = set()
        prev_hour = -1
        for b in self.bins:
            if b.lead_hour in seen_hours:
                raise ValueError(f"Duplicate lead hour {b.lead_hour} found in profile")
            seen_hours.add(b.lead_hour)
            if b.lead_hour <= prev_hour and prev_hour != -1:
                # Timesteps must be strictly ordered
                raise ValueError(f"Timesteps must be in strictly increasing order (got {b.lead_hour} after {prev_hour})")
            prev_hour = b.lead_hour

    def summary_string(self) -> str:
        """Deterministic summary string."""
        lines = [
            f"RAINFALL_FORCING_PROFILE: event={self.event_id}, id={self.forcing_id}, type={self.forcing_type.value}",
            f"  bins count: {len(self.bins)}",
        ]
        for b in self.bins:
            amt = f"{b.amount}" if b.amount is not None else "UNKNOWN"
            lines.append(f"  - t+{b.lead_hour}h: {amt} {b.units} ({b.provenance.value})")
        return "\n".join(lines)
