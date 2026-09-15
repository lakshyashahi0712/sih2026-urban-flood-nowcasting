"""Phase 10 Step 4: Tier-A Structural Gap Evaluation and Gated Eligibility Audit.

Provides a deterministic, evidence-gated evaluator that determines whether current
empirical evidence satisfies structural requirements for Tier-A evaluation of the
Kushak hydraulic model.

Strict rules:
- EVALUATION/GATE layer only. Zero model mutation, zero Tier-A promotion, zero synthesis.
- Requirement-by-requirement evaluation across structural categories.
- Preserves evidence coverage, reach IDs, chainage, and UNKNOWN/UNAVAILABLE statuses.
- Output provenance is ProvenanceStatus.DERIVED.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Set

from .kushak_empirical_evidence import ProvenanceEvidenceClass, load_evidence_manifest
from .kushak_empirical_parser import parse_evidence_file, EvidenceParseResult, ParseStatus
from .kushak_empirical_reconciliation import reconcile_empirical_evidence, EvidenceReconciliationReport, ReconciliationCategory
from .models import ProvenanceStatus


class StructuralRequirementId(str, Enum):
    """Explicit structural requirements for Tier-A evaluation."""

    LONGITUDINAL_PROFILE = "LONGITUDINAL_PROFILE"
    OPEN_REACH_CROSS_SECTIONS = "OPEN_REACH_CROSS_SECTIONS"
    COVERED_CONDUIT_GEOMETRY = "COVERED_CONDUIT_GEOMETRY"
    STRUCTURE_OPENINGS = "STRUCTURE_OPENINGS"
    VERTICAL_DATUM_CONTROL = "VERTICAL_DATUM_CONTROL"
    LATERAL_CONNECTIONS = "LATERAL_CONNECTIONS"
    DOWNSTREAM_BOUNDARY = "DOWNSTREAM_BOUNDARY"
    HYDRAULIC_OBSERVATIONS = "HYDRAULIC_OBSERVATIONS"


class RequirementStatus(str, Enum):
    """Deterministic requirement status."""

    SATISFIED = "SATISFIED"
    PARTIALLY_SATISFIED = "PARTIALLY_SATISFIED"
    MISSING = "MISSING"
    UNKNOWN = "UNKNOWN"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class TierADecision(str, Enum):
    """Top-level tier-A evaluation decision."""

    TIER_A_BLOCKED = "TIER_A_BLOCKED"
    TIER_A_PARTIAL = "TIER_A_PARTIAL"
    TIER_A_ELIGIBLE_FOR_REVIEW = "TIER_A_ELIGIBLE_FOR_REVIEW"


@dataclass(frozen=True)
class RequirementEvaluationItem:
    """Evaluation result for a single structural requirement."""

    requirement_id: StructuralRequirementId
    status: RequirementStatus
    evidence_ids: Tuple[str, ...] = field(default_factory=tuple)
    evidence_classes: Tuple[str, ...] = field(default_factory=tuple)
    reach_ids: Tuple[str, ...] = field(default_factory=tuple)
    covered_reaches: Tuple[str, ...] = field(default_factory=tuple)
    uncovered_reaches: Tuple[str, ...] = field(default_factory=tuple)
    covered_chainage_m: Tuple[float, ...] = field(default_factory=tuple)
    diagnostic: str = ""
    provenance_result: ProvenanceStatus = ProvenanceStatus.DERIVED


@dataclass(frozen=True)
class TierAEvaluationReport:
    """Comprehensive Tier-A structural gap evaluation report."""

    scope: Tuple[str, ...]
    overall_decision: TierADecision
    requirements: Tuple[RequirementEvaluationItem, ...]
    provenance_result: ProvenanceStatus = ProvenanceStatus.DERIVED
    diagnostic: str = ""

    def summary_string(self) -> str:
        """Deterministic summary string."""
        lines = [
            f"TIER_A_EVALUATION_REPORT: scope={self.scope}",
            f"  decision: {self.overall_decision.value}",
            f"  provenance: {self.provenance_result.value}",
            f"  diagnostic: {self.diagnostic!r}",
        ]
        for req in self.requirements:
            lines.append(f"  - {req.requirement_id.value}: {req.status.value} (reaches: {req.covered_reaches})")
        return "\n".join(lines)


def evaluate_tier_a_readiness(
    scope: Optional[List[str]] = None,
    evidence_packages: Optional[Dict[str, Optional[Path]]] = None,
    caller_associations: Optional[Dict[str, Dict[str, Any]]] = None,
) -> TierAEvaluationReport:
    """Evaluate whether available empirical evidence satisfies Tier-A structural requirements.

    Read-only evaluation layer. Never modifies hydraulic models, never promotes to Tier A automatically,
    never fabricates missing data or infers unassociated chainage.
    """
    scope_tuple = tuple(scope) if scope else ("KUSHAK_MAIN_CORRIDOR",)
    evidence_packages = evidence_packages or {}
    caller_associations = caller_associations or {}

    req_ids = [
        StructuralRequirementId.LONGITUDINAL_PROFILE,
        StructuralRequirementId.OPEN_REACH_CROSS_SECTIONS,
        StructuralRequirementId.COVERED_CONDUIT_GEOMETRY,
        StructuralRequirementId.STRUCTURE_OPENINGS,
        StructuralRequirementId.VERTICAL_DATUM_CONTROL,
        StructuralRequirementId.LATERAL_CONNECTIONS,
        StructuralRequirementId.DOWNSTREAM_BOUNDARY,
        StructuralRequirementId.HYDRAULIC_OBSERVATIONS,
    ]

    items: List[RequirementEvaluationItem] = []
    satisfied_count = 0
    partial_count = 0
    total_evaluated = len(req_ids)

    # Inspect each requirement against provided empirical evidence
    for r_id in req_ids:
        matching_evidence_ids = []
        matching_classes = []
        covered_reaches_set: Set[str] = set()
        status = RequirementStatus.MISSING
        diagnostic_msg = f"Requirement {r_id.value} is missing required evidence."

        for ev_id, path in evidence_packages.items():
            # Parse or reconcile
            parse_res = parse_evidence_file(ev_id, path)
            if parse_res.parse_status == ParseStatus.SUCCESS:
                matching_evidence_ids.append(ev_id)
                provenance_cls = parse_res.provenance_inherited
                matching_classes.append(provenance_cls.value)

                # Check strict survey / as-built classes
                if provenance_cls in (
                    ProvenanceEvidenceClass.OFFICIAL_SURVEY_OBSERVED,
                    ProvenanceEvidenceClass.OFFICIAL_AS_BUILT,
                ):
                    # Check scope association if supplied
                    assoc = caller_associations.get(ev_id, {})
                    reaches = assoc.get("reach_ids", scope_tuple)
                    for r in reaches:
                        covered_reaches_set.add(str(r))

                    if covered_reaches_set:
                        if len(covered_reaches_set) >= len(scope_tuple):
                            status = RequirementStatus.SATISFIED
                            diagnostic_msg = f"Requirement {r_id.value} fully satisfied by OFFICIAL survey/as-built evidence {ev_id}."
                        else:
                            status = RequirementStatus.PARTIALLY_SATISFIED
                            diagnostic_msg = f"Requirement {r_id.value} partially satisfied across reaches {sorted(covered_reaches_set)}."
                elif provenance_cls == ProvenanceEvidenceClass.PROCUREMENT_SPECIFICATION:
                    # Procurement spec never satisfies physical geometry
                    if status not in (RequirementStatus.SATISFIED, RequirementStatus.PARTIALLY_SATISFIED):
                        status = RequirementStatus.MISSING
                        diagnostic_msg = f"Requirement {r_id.value} has procurement evidence {ev_id}, which is insufficient for physical geometry."
                else:
                    if status not in (RequirementStatus.SATISFIED, RequirementStatus.PARTIALLY_SATISFIED):
                        status = RequirementStatus.UNKNOWN
                        diagnostic_msg = f"Requirement {r_id.value} has evidence {ev_id} with non-survey class {provenance_cls.value}."

        # Specific handling for Datum / Boundary / Observations if needed
        if r_id == StructuralRequirementId.VERTICAL_DATUM_CONTROL and status == RequirementStatus.MISSING:
            status = RequirementStatus.UNKNOWN
            diagnostic_msg = "Vertical datum control not explicitly established in empirical evidence."

        if status == RequirementStatus.SATISFIED:
            satisfied_count += 1
        elif status == RequirementStatus.PARTIALLY_SATISFIED:
            partial_count += 1

        uncovered = tuple(r for r in scope_tuple if r not in covered_reaches_set)
        covered = tuple(sorted(covered_reaches_set))

        items.append(
            RequirementEvaluationItem(
                requirement_id=r_id,
                status=status,
                evidence_ids=tuple(matching_evidence_ids),
                evidence_classes=tuple(matching_classes),
                reach_ids=scope_tuple,
                covered_reaches=covered,
                uncovered_reaches=uncovered,
                diagnostic=diagnostic_msg,
                provenance_result=ProvenanceStatus.DERIVED,
            )
        )

    # Determine top-level decision
    # If any required structural requirement is missing or unknown and real evidence is absent, blocked.
    if satisfied_count == total_evaluated:
        decision = TierADecision.TIER_A_ELIGIBLE_FOR_REVIEW
        top_diag = "All structural requirements satisfied by verified empirical evidence. Eligible for review."
    elif satisfied_count > 0 or partial_count > 0:
        decision = TierADecision.TIER_A_PARTIAL
        top_diag = f"Partial structural satisfaction ({satisfied_count} satisfied, {partial_count} partial). Tier-A review blocked."
    else:
        decision = TierADecision.TIER_A_BLOCKED
        top_diag = "Required empirical evidence absent or insufficient. Tier-A evaluation blocked."

    return TierAEvaluationReport(
        scope=scope_tuple,
        overall_decision=decision,
        requirements=tuple(items),
        provenance_result=ProvenanceStatus.DERIVED,
        diagnostic=top_diag,
    )
