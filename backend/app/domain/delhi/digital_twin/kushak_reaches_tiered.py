"""Reach-resolved effective-scenario representation for the Kushak corridor
(Phase 8B, Step 2 — representation only, NO routing).

Four model reaches in deterministic corridor order, each carrying:

- stable reach_id and finite, non-overlapping chainage span
  (from the locked Phase 8A REACH_CLASSES mapped/model corridor)
- a Tier-B EFFECTIVE SCENARIO profile reference (or, for UG-01, an
  explicit hydraulically-blocked status — its actual conduit geometry
  is UNKNOWN)
- tier and provenance from the locked Step-1 tier contract

These are EFFECTIVE SCENARIO PROFILES, NOT SURVEYED GEOMETRY. NIT52
procurement classes remain PROCUREMENT_SPECIFICATION; DMP data remains
OFFICIAL_MODEL_VALUE; unknown physical geometry stays UNKNOWN. No routing,
no flow propagation, no calibration, no rainfall changes.
"""

from __future__ import annotations

import enum
import math
from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple

from .hydraulic_geometry import CrossSectionProfile
from .kushak_evidence_model import (
    KUSHAK_HYDRAULIC_SCENARIOS,
    REACH_CLASSES,
    KushakHydraulicScenario,
    covered_effective_profile,
    open_effective_profile,
)
from .kushak_tiered_model import ModelTier
from .models import ProvenanceStatus


class ReachType(str, enum.Enum):
    """Corridor reach categories (mapped/model classification, from the
    hydraulic model contract Section 3 — not surveyed distinctions)."""

    COVERED_UNDERGROUND = "COVERED_UNDERGROUND"
    OPEN = "OPEN"
    COVERED_BAY_CONSTRAINED = "COVERED_BAY_CONSTRAINED"


@dataclass(frozen=True)
class KushakModelReach:
    """One Kushak model reach in the deterministic corridor order.

    `hydraulic_status` is explicit: UG-01 is HYDRAULICALLY_BLOCKED
    (conduit geometry UNKNOWN); Tier-B reaches carry a profile reference
    to an effective scenario profile that is NOT surveyed geometry.
    """

    reach_id: str
    start_chainage_m: float
    end_chainage_m: float
    reach_type: ReachType
    label: str
    tier: ModelTier
    provenance: ProvenanceStatus
    hydraulic_status: str
    profile_reference: Optional[str] = None  # effective profile id, or None if blocked
    note: str = ""

    def __post_init__(self) -> None:
        if not (
            math.isfinite(self.start_chainage_m)
            and math.isfinite(self.end_chainage_m)
        ):
            raise ValueError(
                f"{self.reach_id}: chainages must be finite"
            )
        if self.end_chainage_m <= self.start_chainage_m:
            raise ValueError(f"{self.reach_id}: end chainage must exceed start")


# Deterministic corridor order (upstream -> downstream). Spans copied
# exactly from the locked Phase 8A REACH_CLASSES mapped/model corridor —
# no fabricated geometry, no inferred hydraulic dimensions.
KUSHAK_MODEL_REACHES: Tuple[KushakModelReach, ...] = (
    KushakModelReach(
        reach_id="UG-01",
        start_chainage_m=0.0,
        end_chainage_m=2318.5,
        reach_type=ReachType.COVERED_UNDERGROUND,
        label="Africa Ave upstream covered/underground reach (mapped corridor)",
        tier=ModelTier.TIER_B_EFFECTIVE_SCENARIO,
        provenance=ProvenanceStatus.OFFICIAL_MODEL_VALUE,
        # UG-01 actual conduit geometry (barrel width/height/cells, surveyed
        # invert) is UNKNOWN -> hydraulically blocked, no profile reference.
        hydraulic_status="HYDRAULICALLY_BLOCKED_PHYSICAL_GEOMETRY_UNKNOWN",
        profile_reference=None,
        note="no effective profile may be invented; internal clear barrel "
             "dimensions UNKNOWN (tender drawings bidder-restricted)",
    ),
    KushakModelReach(
        reach_id="OC-01",
        start_chainage_m=2318.5,
        end_chainage_m=3700.0,
        reach_type=ReachType.OPEN,
        label="Upper open Kushak channel (mapped corridor)",
        tier=ModelTier.TIER_B_EFFECTIVE_SCENARIO,
        provenance=ProvenanceStatus.OFFICIAL_MODEL_VALUE,
        hydraulic_status="RUNNABLE_AS_SCENARIO_EFFECTIVE_PROFILE",
        profile_reference=(
            "kushak-oc01-open-INFERRED_EFFECTIVE-NOT_SURVEYED"
        ),
        note="effective scenario profile; surveyed station inverts UNKNOWN",
    ),
    KushakModelReach(
        reach_id="CD-01",
        start_chainage_m=3700.0,
        end_chainage_m=4700.0,
        reach_type=ReachType.COVERED_BAY_CONSTRAINED,
        label="Kushak Bus Depot covered-bay constrained structural reach",
        tier=ModelTier.TIER_B_EFFECTIVE_SCENARIO,
        provenance=ProvenanceStatus.OFFICIAL,
        hydraulic_status="RUNNABLE_AS_SCENARIO_EFFECTIVE_PROFILE",
        profile_reference=(
            "kushak-cd01-covered-INFERRED_EFFECTIVE-NOT_SURVEYED"
        ),
        note="NGT JIR structural bounds (50 m deck, 5 bays) are OBSERVED/"
             "OFFICIAL but indirect/bounded; hydraulic clear waterway "
             "width/height UNKNOWN",
    ),
    KushakModelReach(
        reach_id="OC-02",
        start_chainage_m=4700.0,
        end_chainage_m=5027.56,
        reach_type=ReachType.OPEN,
        label="Downstream open/confluence reach (mapped corridor)",
        tier=ModelTier.TIER_B_EFFECTIVE_SCENARIO,
        provenance=ProvenanceStatus.OFFICIAL_MODEL_VALUE,
        hydraulic_status="RUNNABLE_AS_SCENARIO_EFFECTIVE_PROFILE",
        profile_reference=(
            "kushak-oc02-open-INFERRED_EFFECTIVE-NOT_SURVEYED"
        ),
        note="effective scenario profile; downstream boundary UNKNOWN/blocked",
    ),
)

assert [r.reach_id for r in KUSHAK_MODEL_REACHES] == ["UG-01", "OC-01", "CD-01", "OC-02"]


def validate_reach_ordering(
    reaches: Tuple[KushakModelReach, ...] = KUSHAK_MODEL_REACHES,
) -> None:
    """Deterministic ordering with no silent overlaps or gaps: each reach
    must start exactly where the previous one ends. Raises on violation;
    returns None (no output) on success."""
    for prev, nxt in zip(reaches, reaches[1:]):
        if nxt.start_chainage_m != prev.end_chainage_m:
            raise ValueError(
                f"reach ordering violation: {nxt.reach_id} starts at "
                f"{nxt.start_chainage_m} but {prev.reach_id} ends at "
                f"{prev.end_chainage_m}"
            )


# ---------------------------------------------------------------------------
# Reach-resolved effective profiles (Tier-B scenario representations only)
# ---------------------------------------------------------------------------

# Reach-specific effective profile references. Every id carries
# INFERRED_EFFECTIVE + NOT_SURVEYED: these are EFFECTIVE SCENARIO
# PROFILES, never surveyed/as-built geometry.
REACH_PROFILE_REFERENCES: Dict[str, str] = {
    r.reach_id: r.profile_reference
    for r in KUSHAK_MODEL_REACHES
    if r.profile_reference is not None
}


def build_reach_effective_profile(
    reach_id: str,
    scenario: KushakHydraulicScenario,
    backbone=None,
) -> Tuple[CrossSectionProfile, Dict[str, object]]:
    """Build the effective scenario profile for a Tier-B reach, reusing the
    locked Phase 8A profile builders (never retyped).

    - OC-01 / OC-02 reuse `open_effective_profile` (DMP Part II invert bed,
      shape ASSUMED).
    - CD-01 reuses `covered_effective_profile` (DMP J_3055 invert bed,
      NIT52 class midpoint width, JIR visual depth midpoint) — the
      NIT52 class remains PROCUREMENT_SPECIFICATION, never measured geometry.
    - UG-01 is NOT buildable: its conduit geometry is UNKNOWN; calling
      with UG-01 raises (the reach stays HYDRAULICALLY_BLOCKED).
    """
    if reach_id == "UG-01":
        raise ValueError(
            "UG-01 effective profile cannot be built: actual conduit "
            "geometry is UNKNOWN (hydraulically blocked; no profile may "
            "be invented)"
        )
    if reach_id in ("OC-01", "OC-02"):
        profile, meta = open_effective_profile(scenario, backbone)
        meta["reach_id"] = reach_id
        meta["profile_reference"] = REACH_PROFILE_REFERENCES[reach_id]
    elif reach_id == "CD-01":
        profile, meta = covered_effective_profile(scenario, backbone)
        meta["reach_id"] = reach_id
        meta["profile_reference"] = REACH_PROFILE_REFERENCES[reach_id]
    else:
        raise ValueError(f"unknown reach_id: {reach_id}")
    # Every reach profile is explicitly non-surveyed, non-as-built.
    meta["is_surveyed"] = False
    meta["is_as_built"] = False
    meta["tier"] = ModelTier.TIER_B_EFFECTIVE_SCENARIO.value
    return profile, meta


# ---------------------------------------------------------------------------
# Per-reach provenance ledger (deterministic; no invented citations)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class LedgerEntry:
    """One provenance ledger record: reach_id + quantity + value/reference
    + evidence class + tier + source + status + limitation note."""

    reach_id: str
    quantity: str
    value: Optional[str]  # value or value reference; None = UNKNOWN
    provenance_class: str
    tier: str
    source: str
    status: str
    note: str


def build_provenance_ledger(
    scenario_id: str = "CENTRAL",
) -> Tuple[LedgerEntry, ...]:
    """Deterministic provenance ledger for the required corridor
    quantities. Sources reference only already-acquired evidence
    (Phase 8A constants/records); no citations, survey IDs, or documents
    are invented."""
    scenario = KUSHAK_HYDRAULIC_SCENARIOS[scenario_id]
    tier_b = ModelTier.TIER_B_EFFECTIVE_SCENARIO.value
    return (
        # DMP longitudinal backbone -> OFFICIAL_MODEL_VALUE
        LedgerEntry(
            reach_id="UG-01", quantity="dmp_longitudinal_backbone_invert",
            value="J_3055 new invert 216.841 m (upstream backbone head)",
            provenance_class=ProvenanceStatus.OFFICIAL_MODEL_VALUE.value,
            tier=tier_b,
            source="DMP 2018 Appendix XII curated JSON (Phase 8A load_dmp_backbone)",
            status="USABLE_MODEL_VALUE",
            note="official departmental-record geometry; NOT surveyed, NOT as-built",
        ),
        # NGT JIR bounded structural observations -> OBSERVED/OFFICIAL, bounded
        LedgerEntry(
            reach_id="CD-01", quantity="structural_bounds",
            value="50 m total width; 5 bays; 3.5-4.5 m visual depth; 1.5-3 ft silt",
            provenance_class="OBSERVED/OFFICIAL (indirect, bounded)",
            tier=tier_b,
            source="NGT Joint Inspection Report 05-03-2025 (Phase 8A NGT_JIR_BOUNDS)",
            status="USABLE_AS_SCENARIO_BOUNDS",
            note="visual/bounded field evidence; never hydraulic clear dimensions",
        ),
        # NIT52 -> PROCUREMENT_SPECIFICATION only
        LedgerEntry(
            reach_id="CD-01", quantity="covered_barrel_size_class",
            value="4.0-5.0 m (4.00 m +25%)",
            provenance_class="PROCUREMENT_SPECIFICATION",
            tier=tier_b,
            source="NDMC NIT52 (52/EE(R-III)/2025-26), work_396329.zip, sha256-verified (Phase 8A NIT52_PROCUREMENT)",
            status="SPECIFICATION_ONLY",
            note="procurement spec, NOT measured/as-built geometry; never a measured input",
        ),
        # Effective profile multipliers -> INFERRED_EFFECTIVE / ASSUMED
        LedgerEntry(
            reach_id="OC-01", quantity="effective_manning_multiplier",
            value=f"mult_box={scenario.mult_box}, mult_open={scenario.mult_open} (ranges retained: {scenario.mult_box_range}, {scenario.mult_open_range})",
            provenance_class="INFERRED_EFFECTIVE / ASSUMED at engine boundary",
            tier=tier_b,
            source="Phase 7D16 sampled ranges (Phase 8A KUSHAK_HYDRAULIC_SCENARIOS)",
            status="SCENARIO_PARAMETER",
            note="NOT calibrated, NOT observed; engine receives ASSUMED",
        ),
        # Provisional catchment -> DERIVED/PROVISIONAL
        LedgerEntry(
            reach_id="CORRIDOR", quantity="catchment_area",
            value="27.66 km2 (WORKING_27_66)",
            provenance_class="DERIVED/PROVISIONAL",
            tier=tier_b,
            source="D8 project watershed (Phase 8A CATCHMENT_SCENARIOS)",
            status="PROVISIONAL_SCENARIO",
            note="working watershed; NOT authoritative Kushak catchment; "
                 "historical ~35.4 km2 remains UNKNOWN (never fabricated)",
        ),
        # Unknown UG-01 physical geometry -> UNKNOWN / blocked
        LedgerEntry(
            reach_id="UG-01", quantity="internal_barrel_geometry",
            value=None,  # UNKNOWN — never filled
            provenance_class=ProvenanceStatus.UNKNOWN.value,
            tier=ModelTier.TIER_C_BLOCKED_INPUTS.value,
            source="no acquired evidence (tender drawings bidder-restricted)",
            status="BLOCKED_MISSING_GEOMETRY",
            note="barrel width/height/cell count and surveyed invert UNKNOWN; "
                 "reach HYDRAULICALLY_BLOCKED; UNKNOWN stays UNKNOWN",
        ),
        # Unknown downstream boundary -> UNKNOWN / blocked
        LedgerEntry(
            reach_id="OC-02", quantity="downstream_boundary_stage",
            value=None,  # UNKNOWN — never filled
            provenance_class=ProvenanceStatus.UNKNOWN.value,
            tier=ModelTier.TIER_C_BLOCKED_INPUTS.value,
            source="no acquired evidence (Kushak-Barapullah confluence stage-flow "
                   "relationship unavailable; CWC Yamuna stage is downstream context only)",
            status="BLOCKED_MISSING_OBSERVATION",
            note="no invented stage; free-outfall/normal-depth would be an ASSUMED "
                 "scenario in a later step, never an observed boundary",
        ),
    )
