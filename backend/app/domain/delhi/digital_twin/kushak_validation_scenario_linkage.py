"""Phase 9 Step 6: Optional Descriptive Validation Linkage.

Links an already-established Step 9 ValidationRecord to an explicitly supplied
Tier-B scenario member identifier, without nearest-match inference, spatial/temporal
interpolation, hydraulic model rerun, or numerical score calculation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .kushak_event_validation import ValidationRecord, ValidationOutcome
from .models import ProvenanceStatus


@dataclass(frozen=True)
class ValidationScenarioLinkageResult:
    """Immutable record linking a ValidationRecord to a scenario member."""

    event_id: Optional[str]
    reach_id: Optional[str]
    scenario_member_id: Optional[str]
    validation_result: ValidationOutcome
    linkage_status: str  # "LINKED" or "UNAVAILABLE"
    provenance: ProvenanceStatus = ProvenanceStatus.DERIVED
    model_tier: str = "TIER_B_EFFECTIVE_SCENARIO"
    diagnostic: str = ""


def link_validation_to_scenario(
    validation_record: Optional[ValidationRecord],
    scenario_member_id: str,
    scenario_event_id: str,
    scenario_reach_id: str,
) -> ValidationScenarioLinkageResult:
    """Link a ValidationRecord to an explicit scenario member using caller-supplied identifiers.

    Rules (strict):
    - Caller must explicitly provide scenario_member_id, scenario_event_id, and scenario_reach_id.
    - No spatial, temporal, or nearest-neighbor inference.
    - Event separation enforced: validation_record.event_id must match scenario_event_id.
    - Reach separation enforced: validation_record.reach_id must match scenario_reach_id.
    - Missing or mismatched identifiers result in an UNAVAILABLE linkage status.
    - Provenance is DERIVED; model tier is Tier B; model states and hydraulic outputs are unchanged.
    """
    if not validation_record or not scenario_member_id or not scenario_event_id or not scenario_reach_id:
        return ValidationScenarioLinkageResult(
            event_id=getattr(validation_record, "event_id", None) if validation_record else None,
            reach_id=getattr(validation_record, "reach_id", None) if validation_record else None,
            scenario_member_id=scenario_member_id if scenario_member_id else None,
            validation_result=validation_record.validation_result if validation_record else ValidationOutcome.UNKNOWN,
            linkage_status="UNAVAILABLE",
            diagnostic="Missing required validation record or explicit scenario association identifiers."
        )

    # Event separation check
    if validation_record.event_id != scenario_event_id:
        return ValidationScenarioLinkageResult(
            event_id=validation_record.event_id,
            reach_id=validation_record.reach_id,
            scenario_member_id=scenario_member_id,
            validation_result=validation_record.validation_result,
            linkage_status="UNAVAILABLE",
            diagnostic=(
                f"Event mismatch: validation event_id ({validation_record.event_id!r}) "
                f"does not match supplied scenario event_id ({scenario_event_id!r}); "
                "event separation strictly enforced."
            )
        )

    # Reach matching check
    if validation_record.reach_id != scenario_reach_id:
        return ValidationScenarioLinkageResult(
            event_id=validation_record.event_id,
            reach_id=validation_record.reach_id,
            scenario_member_id=scenario_member_id,
            validation_result=validation_record.validation_result,
            linkage_status="UNAVAILABLE",
            diagnostic=(
                f"Reach mismatch: validation reach_id ({validation_record.reach_id!r}) "
                f"does not match supplied scenario reach_id ({scenario_reach_id!r})."
            )
        )

    return ValidationScenarioLinkageResult(
        event_id=validation_record.event_id,
        reach_id=validation_record.reach_id,
        scenario_member_id=scenario_member_id,
        validation_result=validation_record.validation_result,
        linkage_status="LINKED",
        provenance=ProvenanceStatus.DERIVED,
        model_tier=validation_record.model_tier,
        diagnostic=(
            f"Explicitly linked validation record for event {validation_record.event_id} "
            f"reach {validation_record.reach_id} to scenario member {scenario_member_id} "
            f"with result {validation_record.validation_result.value}; no model rerun or inference."
        )
    )
