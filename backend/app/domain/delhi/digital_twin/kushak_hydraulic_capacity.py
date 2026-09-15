"""Reach-level hydraulic capacity contract (Phase 8B, Step 7 — CAPACITY ONLY).

The reach-level bridge to evaluate hydraulic capacity using the existing
Phase 7D hydraulic machinery, based on an explicitly supplied stage and
effective Tier-B hydraulic profile.

CORE SCIENTIFIC RULES (enforced by construction):

- Stage is REQUIRED (not inferred from discharge, capacity, or rainfall).
- Tier-B effective hydraulic profile is REQUIRED (not inferred from survey data
  that doesn't exist).
- Q_capacity is strictly informational/capacity output; it is NOT actual outflow
  and is NOT automatically transferred downstream.
- Actual outflow continues to require the explicit Step-3 decision contract;
  transferred flow requires the Step-3 transfer semantics.
- Provenance: successful Tier-B capacity is DERIVED; missing/blocked inputs yield
  UNKNOWN/BLOCKED; no Tier-A promotion occurs.
- No Kushak-specific geometry/Manning/calibration data is fabricated.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .hydraulic_geometry import CrossSectionProfile
from .hydraulic_manning_adapter import ManningCapacityResult, calculate_capacity_from_bundle
from .hydraulic_geometry_input import bundle_from_state
from .hydraulic_time_state import SimulationState
from .models import ProvenanceStatus


@dataclass
class CapacityUpdateResult:
    """The capacity evaluation result, with the underlying Manning result."""
    status: str
    capacity_m3_s: Optional[float] = None
    provenance: ProvenanceStatus = ProvenanceStatus.UNKNOWN
    diagnostic: Optional[str] = None
    manning_result: Optional[ManningCapacityResult] = None


def evaluate_reach_capacity(
    state: SimulationState,
    profile: Optional[CrossSectionProfile],
    n: Optional[float],
    slope: Optional[float],
    n_provenance: ProvenanceStatus = ProvenanceStatus.ASSUMED,
    slope_provenance: ProvenanceStatus = ProvenanceStatus.ASSUMED,
) -> CapacityUpdateResult:
    """Evaluate reach-level Manning capacity from a stage + effective profile.

    - If stage is UNKNOWN (None) or profile is None -> BLOCKED/UNKNOWN.
    - If required dimensions/n/S are None -> BLOCKED/UNKNOWN.
    - Capacity provenance: DERIVED for Tier-B calculation.
    """
    if state.stage_m is None:
        return CapacityUpdateResult(
            status="BLOCKED_MISSING_INPUT",
            diagnostic="State stage_m is UNKNOWN; capacity not evaluated"
        )
    if profile is None:
        return CapacityUpdateResult(
            status="BLOCKED_MISSING_INPUT",
            diagnostic="Hydraulic profile is UNKNOWN; capacity not evaluated"
        )

    # 1. Bundle geometry + stage
    bundle = bundle_from_state(state, profile)

    # 2. Compute Manning
    manning_result = calculate_capacity_from_bundle(
        bundle, n, slope, n_provenance, slope_provenance
    )

    # 3. Map to Result
    if manning_result.status != "COMPUTED":
        return CapacityUpdateResult(
            status=manning_result.status,
            diagnostic=manning_result.diagnostic,
            manning_result=manning_result
        )

    return CapacityUpdateResult(
        status="COMPUTED",
        capacity_m3_s=manning_result.capacity_m3_s,
        provenance=ProvenanceStatus.DERIVED,  # Tier-B scenario is DERIVED
        diagnostic=manning_result.diagnostic,
        manning_result=manning_result
    )
