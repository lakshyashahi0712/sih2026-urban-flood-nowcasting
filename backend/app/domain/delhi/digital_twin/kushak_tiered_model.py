"""Three-tier model-tier contract for the Kushak drainage corridor
(Phase 8B, Step 1 — the safety boundary before any reach routing exists).

Machine-checkable separation of:

- TIER_A_PHYSICAL_AS_BUILT   — a physical/as-built hydraulic model.
                               Requires survey-grade (OFFICIAL_SURVEY_OBSERVED)
                               or as-built (OFFICIAL_AS_BUILT) hydraulic
                               geometry evidence. Unreachable with the
                               current Kushak evidence inventory.
- TIER_B_EFFECTIVE_SCENARIO  — the existing Phase 8A evidence-constrained
                               effective-scenario tier. RUNNABLE_AS_SCENARIO;
                               never promotable to Tier A.
- TIER_C_BLOCKED_INPUTS      — the registry/diagnostic ledger of missing
                               physical inputs. Not a hydraulic model;
                               UNKNOWN stays UNKNOWN, never filled.

No provenance enums are duplicated: the existing ProvenanceStatus is
reused. NIT52 procurement dimensions are PROCUREMENT_SPECIFICATION, not
as-built evidence; DMP longitudinal inverts are OFFICIAL_MODEL_VALUE, not
surveyed geometry — neither satisfies the Tier-A gate, by construction.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Optional, Tuple

from .models import ProvenanceStatus


class SurveyEvidenceClass(str, Enum):
    """Explicit survey/as-built evidence classes for the Tier-A gate.

    These are GATE-LOCAL classifications, deliberately separate from the
    shared ProvenanceStatus enum (which is used across Mumbai V1 and the
    hydraulic weakest-link rules and must not gain hydraulic-geometry
    members). They exist ONLY so that future acquired survey/as-built
    evidence can satisfy the Tier-A gate — no survey/as-built Kushak
    evidence exists today, and none is claimed.

    Every existing ProvenanceStatus value (OFFICIAL, OFFICIAL_MODEL_VALUE,
    PROCUREMENT_SPECIFICATION spec classes, OBSERVED visual bounds, ASSUMED,
    DERIVED, INFERRED_EFFECTIVE, UNKNOWN) is structurally non-satisfying:
    the gate maps any ProvenanceStatus input to NOT_SURVEY_GRADE.
    """

    OFFICIAL_SURVEY_OBSERVED = "OFFICIAL_SURVEY_OBSERVED"
    OFFICIAL_AS_BUILT = "OFFICIAL_AS_BUILT"


class ModelTier(str, Enum):
    """The three-tier model-status contract.

    Tier membership is decided ONLY by the evidence gate in
    evaluate_tier_gate — never by intent, labeling, or convenience.
    """

    TIER_A_PHYSICAL_AS_BUILT = "TIER_A_PHYSICAL_AS_BUILT"
    TIER_B_EFFECTIVE_SCENARIO = "TIER_B_EFFECTIVE_SCENARIO"
    TIER_C_BLOCKED_INPUTS = "TIER_C_BLOCKED_INPUTS"


@dataclass(frozen=True)
class PhysicalEvidenceRequirement:
    """One physical/as-built hydraulic input Tier A would require.

    `allowed_survey_classes` is the exhaustive list of gate-local
    SurveyEvidenceClass values that can satisfy this requirement. Generic
    ProvenanceStatus evidence (OFFICIAL, OFFICIAL_MODEL_VALUE, spec classes,
    OBSERVED visual bounds, ASSUMED, DERIVED, INFERRED_EFFECTIVE, UNKNOWN)
    is structurally incapable of satisfying it — see the ProvenanceStatus
    mapping in the gate.
    """

    requirement_id: str
    description: str
    allowed_survey_classes: Tuple[SurveyEvidenceClass, ...] = (
        SurveyEvidenceClass.OFFICIAL_SURVEY_OBSERVED,
        SurveyEvidenceClass.OFFICIAL_AS_BUILT,
    )


@dataclass(frozen=True)
class MissingInput:
    """One missing/unavailable physical input (Tier-C registry entry).

    A missing input carries `value=None` — UNKNOWN stays UNKNOWN. It is
    never zero, never interpolated, never fabricated. `can_satisfy` is
    always False: a missing input cannot be silently converted into
    Tier-A evidence.
    """

    requirement_id: str
    description: str
    value: Optional[float] = None  # UNKNOWN — never zero-filled
    can_satisfy: bool = False


# The exhaustive Tier-A physical-evidence requirements for the Kushak
# corridor, from the hydraulic model contract (Sections 4-5). Every one of
# these is currently UNKNOWN — this list is the machine-checkable record of
# exactly which physical inputs a future implementation must acquire.
TIER_A_REQUIREMENTS: Tuple[PhysicalEvidenceRequirement, ...] = (
    PhysicalEvidenceRequirement(
        requirement_id="UG01_internal_barrel_width",
        description="Africa Ave tunnel internal clear barrel width (UNKNOWN; tender drawings bidder-restricted)",
    ),
    PhysicalEvidenceRequirement(
        requirement_id="UG01_internal_barrel_height",
        description="Africa Ave tunnel internal clear barrel height (UNKNOWN)",
    ),
    PhysicalEvidenceRequirement(
        requirement_id="UG01_barrel_cell_count",
        description="Africa Ave tunnel barrel cell count (UNKNOWN)",
    ),
    PhysicalEvidenceRequirement(
        requirement_id="UG01_surveyed_invert",
        description="Africa Ave tunnel surveyed longitudinal bed invert (UNKNOWN)",
    ),
    PhysicalEvidenceRequirement(
        requirement_id="UG01_surveyed_bed_slope",
        description="Africa Ave tunnel surveyed longitudinal bed slope (UNKNOWN)",
    ),
    PhysicalEvidenceRequirement(
        requirement_id="CD01_hydraulic_clear_width",
        description="Bus Depot reach hydraulic clear waterway width (UNKNOWN; 50 m deck width is structural, not hydraulic)",
    ),
    PhysicalEvidenceRequirement(
        requirement_id="CD01_hydraulic_clear_height",
        description="Bus Depot reach hydraulic clear vertical height (UNKNOWN)",
    ),
    PhysicalEvidenceRequirement(
        requirement_id="CD01_soffit_elevation",
        description="Bus Depot deck underside/soffit elevation (UNKNOWN)",
    ),
    PhysicalEvidenceRequirement(
        requirement_id="CD01_pier_open_area_ratio",
        description="Bus Depot pier open-area ratio (UNKNOWN)",
    ),
    PhysicalEvidenceRequirement(
        requirement_id="DC01_cross_section",
        description="Defence Colony tributary cross-section (UNKNOWN; zero published transects)",
    ),
    PhysicalEvidenceRequirement(
        requirement_id="DC01_invert_profile",
        description="Defence Colony tributary invert profile (UNKNOWN)",
    ),
    PhysicalEvidenceRequirement(
        requirement_id="KUSHAK_stage_discharge_observations",
        description="Kushak stage/discharge observations (none exist)",
    ),
    PhysicalEvidenceRequirement(
        requirement_id="KUSHAK_certified_vertical_datum",
        description="Certified vertical datum/control for the corridor (absent)",
    ),
    PhysicalEvidenceRequirement(
        requirement_id="OC_reach_surveyed_inverts",
        description="Open-reach (OC-01/OC-02) surveyed station invert elevations (UNKNOWN)",
    ),
    PhysicalEvidenceRequirement(
        requirement_id="OC_reach_bridge_clearances",
        description="Open-reach bridge/culvert hydraulic clearances (UNKNOWN)",
    ),
)


# Current Kushak evidence inventory classes that must NEVER satisfy the
# Tier-A gate, recorded explicitly so the exclusion is machine-checkable.
NON_SATISFYING_EVIDENCE: Tuple[Dict[str, str], ...] = (
    {
        "evidence": "NIT52 covered barrel procurement class 4.0-5.0 m",
        "class": "PROCUREMENT_SPECIFICATION",
        "rule": "specification only — never as-built geometry",
    },
    {
        "evidence": "DMP 2018 Appendix XII longitudinal inverts",
        "class": "OFFICIAL_MODEL_VALUE",
        "rule": "official model values — never surveyed geometry",
    },
    {
        "evidence": "NGT JIR 05-03-2025 structural bounds (50 m deck, 5 bays, 3.5-4.5 m visual depth)",
        "class": "OBSERVED/OFFICIAL (visual, bounded)",
        "rule": "structural/visual bounds — never hydraulic clear dimensions",
    },
    {
        "evidence": "Effective computational scenario profiles",
        "class": "ASSUMED / INFERRED_EFFECTIVE",
        "rule": "scenario profiles — never physical geometry",
    },
    {
        "evidence": "Derived DEM bank-offset bed levels",
        "class": "DERIVED",
        "rule": "remote-sensing derived — never surveyed invert",
    },
)


@dataclass(frozen=True)
class TierGateResult:
    """Deterministic gate result.

    `tier` is TIER_C when any required physical input is missing, and
    TIER_B is reachable only as the effective-scenario tier — never as a
    promotion path toward Tier A.
    """

    tier: ModelTier
    blocked_reasons: Tuple[str, ...] = field(default_factory=tuple)
    missing_inputs: Tuple[MissingInput, ...] = field(default_factory=tuple)
    can_promote_to_tier_a: bool = False


def evaluate_tier_gate(
    provided_evidence: Optional[Dict[str, ProvenanceStatus]] = None,
    provided_survey_evidence: Optional[Dict[str, SurveyEvidenceClass]] = None,
) -> TierGateResult:
    """Deterministic, machine-testable Tier-A evidence gate.

    Tier A requires every entry in TIER_A_REQUIREMENTS to be satisfied by
    explicit survey-grade (OFFICIAL_SURVEY_OBSERVED) or as-built
    (OFFICIAL_AS_BUILT) evidence via `provided_survey_evidence`.

    Generic ProvenanceStatus inputs via `provided_evidence` are mapped to
    NOT_SURVEY_GRADE and can NEVER satisfy the gate — OFFICIAL,
    OFFICIAL_MODEL_VALUE, PROCUREMENT_SPECIFICATION spec classes, OBSERVED
    bounded/visual evidence, ASSUMED, DERIVED, INFERRED_EFFECTIVE, and
    UNKNOWN are all structurally non-satisfying. The current Kushak
    evidence inventory therefore leaves the gate at TIER_C with the full
    missing-input ledger. UNKNOWN inputs stay UNKNOWN (value=None) —
    never zero, never fabricated.
    """
    provided_survey = provided_survey_evidence or {}
    # `provided_evidence` (generic ProvenanceStatus) is accepted for API
    # compatibility only and is deliberately never consulted: no generic
    # provenance value can certify a surveyed/as-built hydraulic dimension.
    _ = provided_evidence
    missing: list = []
    satisfied: list = []
    for req in TIER_A_REQUIREMENTS:
        survey_class = provided_survey.get(req.requirement_id)
        if survey_class is not None and survey_class in req.allowed_survey_classes:
            satisfied.append(req.requirement_id)
        else:
            missing.append(MissingInput(
                requirement_id=req.requirement_id,
                description=req.description,
                value=None,  # UNKNOWN — never zero-filled
                can_satisfy=False,
            ))
    if missing:
        return TierGateResult(
            tier=ModelTier.TIER_C_BLOCKED_INPUTS,
            blocked_reasons=tuple(
                f"missing physical/as-built evidence: {m.requirement_id}"
                for m in missing
            ),
            missing_inputs=tuple(missing),
            can_promote_to_tier_a=False,
        )
    # All requirements satisfied — Tier A becomes constructible (this
    # branch is unreachable with the current evidence inventory).
    return TierGateResult(
        tier=ModelTier.TIER_A_PHYSICAL_AS_BUILT,
        can_promote_to_tier_a=True,
    )


@dataclass(frozen=True)
class TierBScenarioModel:
    """The Tier-B handle on the existing Phase 8A evidence-constrained
    scenario model. RUNNABLE_AS_SCENARIO by construction; promotion to
    Tier A is structurally impossible (no path exists)."""

    tier: ModelTier = ModelTier.TIER_B_EFFECTIVE_SCENARIO
    status: str = "RUNNABLE_AS_SCENARIO"
    model_id: str = "kushak-evidence-constrained"
    is_physical_as_built: bool = False
    is_surveyed: bool = False


def build_tier_b_model() -> TierBScenarioModel:
    """Return the Tier-B effective-scenario handle on the locked Phase 8A
    model. The Phase 8A module is imported by callers; this contract never
    modifies it."""
    return TierBScenarioModel()


@dataclass(frozen=True)
class TierCRegistry:
    """The Tier-C missing/unavailable physical inputs ledger.

    A registry/diagnostic state, not a hydraulic model. Every entry keeps
    value=None (UNKNOWN): no missing input becomes zero merely because it
    is unavailable.
    """

    tier: ModelTier = ModelTier.TIER_C_BLOCKED_INPUTS
    missing_inputs: Tuple[MissingInput, ...] = field(default_factory=tuple)

    @classmethod
    def from_gate(cls, gate: TierGateResult) -> "TierCRegistry":
        return cls(missing_inputs=gate.missing_inputs)


def load_current_tier_state() -> Tuple[TierGateResult, TierCRegistry]:
    """Evaluate the gate against the current Kushak evidence inventory.

    Deterministic: the same call always returns the same result —
    TIER_C with the full UNKNOWN ledger, because no physical/as-built
    hydraulic evidence exists for any requirement.
    """
    gate = evaluate_tier_gate()  # no evidence provided -> all requirements unsatisfied
    return gate, TierCRegistry.from_gate(gate)
