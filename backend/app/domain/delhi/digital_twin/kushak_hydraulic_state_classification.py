"""Reach hydraulic state classification contract (Phase 8B, Step 8 —
CLASSIFICATION ONLY).

Converts ALREADY-COMPUTED hydraulic state (an explicit stage from the
Step-6 coupling / Step-7 capacity pathway, plus an effective Tier-B
profile) into a transparent, deterministic reach-level MODEL-STATE
classification. This module describes the model state; it NEVER claims
observed flooding.

CORE SCIENTIFIC RULES (enforced by construction):

- state_class is the constant "MODEL_STATE" and observed_flood_event is
  always None: no observed-flood label is ever produced here.
- Classification is NEVER inferred from rainfall, catchment area, invert
  elevation, capacity, or discharge — the ONLY path to a computed
  classification is an explicit stage plus an explicit profile.
- DRY / NORMAL_CAPACITY / SURCHARGED are purely geometric (bed and crown
  of the supplied effective profile): no empirical threshold is invented.
- ELEVATED requires a caller-supplied threshold from an EXISTING
  documented threshold contract with evidence-supported provenance
  (OBSERVED / OFFICIAL). A threshold with weaker provenance leaves the
  state UNKNOWN rather than inventing one. No such contract exists
  today, so ELEVATED can never fire from Step-8 inputs alone.
- Q_capacity may be carried as a CAPACITY quantity only (informational
  echo); it is NEVER treated as actual discharge and never creates
  Q_actual_outflow or Q_transferred_downstream.
- Computed classification is DERIVED provenance, never OBSERVED;
  scenario-level effective classification is Tier-B and never promotes
  Tier-A.
- Physical/as-built (Tier-A) interpretation stays BLOCKED while
  surveyed geometry is UNKNOWN (claim_physical_as_built=True blocks);
  UG-01 conduit geometry is never invented.
- OC-02 (terminal) receives no downstream state; terminal/outfall
  uncertainty stays explicit.

Non-goals (STRICT): calibration, ML, radar, rainfall nowcasting, 2D
surface flooding, road/intersection risk, safe routing, public warnings,
street-level flood depth, observed-flood label generation, a downstream
state for the terminal reach, new empirical thresholds, new survey
geometry, new rating curves, new continuity equations.
"""

from __future__ import annotations

import enum
import math
from dataclasses import dataclass
from typing import Optional, Tuple

from .hydraulic_geometry import CrossSectionProfile
from .hydraulic_time_state import SimulationState
from .kushak_continuity_routing import CHAIN_REACH_IDS, ChainTimestepResult
from .kushak_storage_stage_coupling import reach_state_to_simulation
from .kushak_tiered_model import ModelTier
from .models import ProvenanceStatus


class ReachHydraulicClassification(str, enum.Enum):
    """Deterministic reach-level MODEL-STATE classification.

    Only states justifiable by the existing hydraulic contracts:
    - UNKNOWN / BLOCKED follow the existing blocked-status naming family.
    - DRY / NORMAL_CAPACITY / SURCHARGED are purely geometric against the
      supplied effective profile (bed / between bed and crown / above crown).
    - ELEVATED requires an evidence-supported documented threshold; with
      no such contract the state stays UNKNOWN instead.
    """

    UNKNOWN = "UNKNOWN"
    BLOCKED = "BLOCKED"
    DRY = "DRY"
    NORMAL_CAPACITY = "NORMAL_CAPACITY"
    ELEVATED = "ELEVATED"
    SURCHARGED = "SURCHARGED"


# Provenance classes that satisfy an EXISTING documented threshold
# contract. Anything weaker leaves the classification UNKNOWN (a threshold
# is never invented here).
_EVIDENCE_SUPPORTED_THRESHOLD = (ProvenanceStatus.OBSERVED, ProvenanceStatus.OFFICIAL)

_MODEL_STATE = "MODEL_STATE"


@dataclass(frozen=True)
class ReachStateClassificationResult:
    """One reach's classification outcome.

    `state_class` is always MODEL_STATE and `observed_flood_event` is
    always None: this result describes the hydraulic model state and never
    claims an observed flood event. `capacity_m3_s` is an informational
    capacity echo only — never a discharge.
    """

    reach_id: str
    classification: ReachHydraulicClassification
    status: str
    provenance: ProvenanceStatus
    tier: str
    state_class: str
    observed_flood_event: None
    stage_m: Optional[float] = None
    capacity_m3_s: Optional[float] = None  # capacity echo ONLY
    diagnostic: Optional[str] = None


def _is_finite(v) -> bool:
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        return False
    return math.isfinite(v)


def _unknown_result(
    reach_id: str,
    status: str,
    diagnostic: str,
    stage_m: Optional[float] = None,
    capacity_m3_s: Optional[float] = None,
) -> ReachStateClassificationResult:
    return ReachStateClassificationResult(
        reach_id=reach_id,
        classification=ReachHydraulicClassification.UNKNOWN,
        status=status,
        provenance=ProvenanceStatus.UNKNOWN,
        tier=ModelTier.TIER_C_BLOCKED_INPUTS.value,
        state_class=_MODEL_STATE,
        observed_flood_event=None,
        stage_m=stage_m,
        capacity_m3_s=capacity_m3_s,
        diagnostic=diagnostic,
    )


def _blocked_result(
    reach_id: str,
    status: str,
    diagnostic: str,
    stage_m: Optional[float] = None,
    capacity_m3_s: Optional[float] = None,
) -> ReachStateClassificationResult:
    return ReachStateClassificationResult(
        reach_id=reach_id,
        classification=ReachHydraulicClassification.BLOCKED,
        status=status,
        provenance=ProvenanceStatus.UNKNOWN,
        tier=ModelTier.TIER_C_BLOCKED_INPUTS.value,
        state_class=_MODEL_STATE,
        observed_flood_event=None,
        stage_m=stage_m,
        capacity_m3_s=capacity_m3_s,
        diagnostic=diagnostic,
    )


def classify_reach_state(
    state: SimulationState,
    profile: Optional[CrossSectionProfile],
    elevated_threshold_m: Optional[float] = None,
    threshold_provenance: ProvenanceStatus = ProvenanceStatus.UNKNOWN,
    claim_physical_as_built: bool = False,
    capacity_m3_s: Optional[float] = None,
) -> ReachStateClassificationResult:
    """Classify one reach's already-computed hydraulic state.

    Deterministic mapping (no inference, no invented thresholds):

    - claim_physical_as_built -> BLOCKED (Tier-A physical interpretation
      requires surveyed as-built geometry, which is UNKNOWN).
    - stage UNKNOWN (None) -> UNKNOWN per the existing status contract.
    - profile None / geometry UNKNOWN -> BLOCKED.
    - a supplied threshold with non-evidence-supported provenance ->
      UNKNOWN (the threshold is never invented here).
    - stage < profile bed elevation -> DRY.
    - stage above the profile crown -> SURCHARGED.
    - stage >= an evidence-supported documented threshold -> ELEVATED.
    - otherwise (between bed and crown) -> NORMAL_CAPACITY.

    A computed classification is DERIVED provenance, Tier-B, and always
    state_class=MODEL_STATE with observed_flood_event=None.
    """
    reach_id = state.location_id

    # Tier-A physical interpretation stays BLOCKED while as-built
    # geometry is UNKNOWN — never classified from effective scenarios.
    if claim_physical_as_built:
        return _blocked_result(
            reach_id,
            status="BLOCKED_MISSING_GEOMETRY",
            diagnostic=(
                "Tier-A physical/as-built interpretation requires surveyed "
                "as-built geometry, which is UNKNOWN; classification "
                "remains BLOCKED (effective scenarios are not as-built)"
            ),
            stage_m=state.stage_m,
            capacity_m3_s=capacity_m3_s,
        )

    # Missing stage -> UNKNOWN per the existing status contract.
    if state.stage_m is None:
        status = (
            state.status.value
            if state.status.value.startswith("BLOCKED")
            else "BLOCKED_MISSING_INPUT"
        )
        return _unknown_result(
            reach_id,
            status=status,
            diagnostic=(
                "stage_m is UNKNOWN; classification is never inferred from "
                "discharge, capacity, rainfall, catchment, or invert alone"
            ),
            stage_m=None,
            capacity_m3_s=capacity_m3_s,
        )
    if not _is_finite(state.stage_m):
        return _blocked_result(
            reach_id,
            status="BLOCKED_INVALID_INPUT",
            diagnostic=f"stage_m must be finite (got {state.stage_m!r})",
            capacity_m3_s=capacity_m3_s,
        )

    # Physical/as-built geometry unavailable -> BLOCKED.
    if profile is None or not profile.has_geometry:
        return _blocked_result(
            reach_id,
            status="BLOCKED_MISSING_GEOMETRY",
            diagnostic=(
                "hydraulic profile is UNKNOWN (no geometry); classification "
                "remains BLOCKED"
            ),
            stage_m=state.stage_m,
            capacity_m3_s=capacity_m3_s,
        )

    stage = float(state.stage_m)

    # A threshold is accepted ONLY from an existing documented contract
    # with evidence-supported provenance; otherwise the state stays
    # UNKNOWN rather than inventing a threshold.
    threshold: Optional[float] = None
    if elevated_threshold_m is not None:
        if not _is_finite(elevated_threshold_m):
            return _blocked_result(
                reach_id,
                status="BLOCKED_INVALID_INPUT",
                diagnostic=(
                    f"elevated_threshold_m must be finite "
                    f"(got {elevated_threshold_m!r})"
                ),
                stage_m=stage,
                capacity_m3_s=capacity_m3_s,
            )
        if threshold_provenance not in _EVIDENCE_SUPPORTED_THRESHOLD:
            return _unknown_result(
                reach_id,
                status="BLOCKED_UNSUPPORTED_THRESHOLD",
                diagnostic=(
                    "threshold provenance "
                    f"({threshold_provenance.value}) is not evidence-"
                    "supported by an existing documented threshold contract; "
                    "state remains UNKNOWN rather than inventing a threshold"
                ),
                stage_m=stage,
                capacity_m3_s=capacity_m3_s,
            )
        threshold = float(elevated_threshold_m)

    # Purely geometric classification against the supplied profile.
    bed = profile.min_elevation_m
    crown = profile.max_elevation_m
    if stage < bed:
        classification = ReachHydraulicClassification.DRY
    elif stage > crown:
        classification = ReachHydraulicClassification.SURCHARGED
    elif threshold is not None and stage >= threshold:
        classification = ReachHydraulicClassification.ELEVATED
    else:
        classification = ReachHydraulicClassification.NORMAL_CAPACITY

    return ReachStateClassificationResult(
        reach_id=reach_id,
        classification=classification,
        status="COMPUTED",
        provenance=ProvenanceStatus.DERIVED,  # never OBSERVED
        tier=ModelTier.TIER_B_EFFECTIVE_SCENARIO.value,
        state_class=_MODEL_STATE,
        observed_flood_event=None,
        stage_m=stage,
        capacity_m3_s=capacity_m3_s,
        diagnostic=(
            f"model-state classification {classification.value} from explicit "
            f"stage {stage} m against effective profile "
            f"'{profile.cross_section_id}' (bed {bed} m, crown {crown} m); "
            "MODEL_STATE only — never an observed flood event"
        ),
    )


def classify_chain_timestep(
    chain_result: ChainTimestepResult,
    profiles: Optional[dict] = None,
    elevated_threshold_m: Optional[float] = None,
    threshold_provenance: ProvenanceStatus = ProvenanceStatus.UNKNOWN,
) -> Tuple[ReachStateClassificationResult, ...]:
    """Classify every reach of one chain timestep, deterministically, in
    the locked Step-2 order (UG-01 -> OC-01 -> CD-01 -> OC-02).

    `profiles` is the caller-supplied reach_id -> CrossSectionProfile
    mapping (effective Tier-B scenario profiles). Reaches without a
    profile (the real Kushak state, and UG-01 in particular) classify as
    BLOCKED; reaches whose stage is UNKNOWN classify as UNKNOWN. No
    downstream state is created for the terminal reach.
    """
    profiles = profiles or {}
    return tuple(
        classify_reach_state(
            reach_state_to_simulation(chain_result.state_for(rid).state),
            profiles.get(rid),
            elevated_threshold_m=elevated_threshold_m,
            threshold_provenance=threshold_provenance,
        )
        for rid in CHAIN_REACH_IDS
    )
