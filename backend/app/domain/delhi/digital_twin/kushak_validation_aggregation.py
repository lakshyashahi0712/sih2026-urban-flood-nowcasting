"""Event-separated validation aggregation contract (Phase 8B, Step 10).

Produces a deterministic, descriptive summary of Step-9 validation outcomes
(ValidationRecord) grouped strictly by (event_id, reach_id).

CORE SCIENTIFIC RULES:
- Deterministic, descriptive aggregation ONLY (counts per outcome).
- No percentages, rates, scores, or flood-proneness indices.
- EV-01 and EV-02 remain distinct; different reaches remain distinct.
- UNKNOWN, NOT_COMPARABLE, and UNASSIGNED are explicitly counted; never
  dropped or treated as negative evidence.
- Aggregate provenance is ALWAYS DERIVED.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple

from .kushak_event_validation import ValidationOutcome, ValidationRecord
from .models import ProvenanceStatus


@dataclass(frozen=True)
class ReachEventOutcomeSummary:
    """Descriptive, immutable aggregation record."""
    event_id: str
    reach_id: str
    consistent_count: int = 0
    inconsistent_count: int = 0
    unknown_count: int = 0
    not_comparable_count: int = 0
    unassigned_count: int = 0
    result_provenance: ProvenanceStatus = ProvenanceStatus.DERIVED


def aggregate_validation_records(
    records: Tuple[ValidationRecord, ...],
) -> Tuple[ReachEventOutcomeSummary, ...]:
    """Aggregate Step-9 records grouped by (event_id, reach_id).

    Fails explicitly if any record is missing required grouping keys.
    Preserves zero counts for all outcome types.
    """
    if not records:
        return ()

    # Grouping structure: (event_id, reach_id) -> summary
    groups: Dict[Tuple[str, str], ReachEventOutcomeSummary] = {}

    for r in records:
        if r.event_id is None or r.reach_id is None:
            raise ValueError(
                f"ValidationRecord missing grouping key: event_id={r.event_id}, "
                f"reach_id={r.reach_id}"
            )

        key = (r.event_id, r.reach_id)
        current = groups.get(key, ReachEventOutcomeSummary(
            event_id=r.event_id, reach_id=r.reach_id
        ))

        # Build updated summary (dataclass is frozen, so replace)
        updates = {}
        if r.validation_result == ValidationOutcome.CONSISTENT:
            updates["consistent_count"] = current.consistent_count + 1
        elif r.validation_result == ValidationOutcome.INCONSISTENT:
            updates["inconsistent_count"] = current.inconsistent_count + 1
        elif r.validation_result == ValidationOutcome.UNKNOWN:
            updates["unknown_count"] = current.unknown_count + 1
        elif r.validation_result == ValidationOutcome.NOT_COMPARABLE:
            updates["not_comparable_count"] = current.not_comparable_count + 1
        elif r.validation_result == ValidationOutcome.UNASSIGNED:
            updates["unassigned_count"] = current.unassigned_count + 1

        groups[key] = current.__class__(**{**current.__dict__, **updates})

    return tuple(groups.values())
