"""Event-separated model-observation validation contract (Phase 8B,
Step 9 — VALIDATION ONLY).

A deterministic, evidence-constrained way to compare ALREADY-COMPUTED
model outputs (Step-8 reach hydraulic classification) against available
real-world waterlogging/flood evidence, WITHOUT converting observations
into unsupported hydraulic measurements.

CORE PRINCIPLE (enforced by construction):

- Validation evidence and hydraulic model inputs remain SEPARATE. An
  observed waterlogging/flood report is NEVER converted into discharge,
  stage, water depth, Manning n, hydraulic capacity, storage, or a
  calibration target. This module writes nothing back into the model.
- Validation is EVENT-SCOPED: EV-01 (June 28, 2024) and EV-02 (July
  8-10, 2023) keep separate identities and are never pooled into one
  score. An observation carries an explicit event_id; an unknown/absent
  event_id leaves the result UNKNOWN/UNASSIGNED — never silently
  attached to an event.
- Observation classes preserve source identity and evidentiary meaning:
  GSDL waterlogging occurrence (occurrence only), DTP operational
  observation (impact evidence, coordinates may be UNKNOWN), CWC
  downstream river level (downstream context ONLY — never Kushak
  stage), rainfall observation (forcing/event evidence, never a flood
  observation), and external flood extent (used only if an
  already-ingested provenance-controlled product is supplied;
  otherwise unavailable).
- SPATIAL matching never invents coordinates: no coordinates ->
  spatial_match UNKNOWN; coordinates + caller-supplied reach reference
  points -> deterministic nearest-reach rule within a caller-supplied
  maximum distance; outside the corridor -> OUT_OF_CORRIDOR (never
  force-matched). Text mentions of nearby roads/places never assign a
  reach.
- TEMPORAL matching never invents times: date-only observations keep
  DATE_ONLY precision and cannot match a model timestep (no arbitrary
  timestep); an unknown timestamp stays UNKNOWN.
- COMPARISON is occurrence/state compatibility only. No depth RMSE,
  discharge RMSE, stage RMSE, rating-curve error, or calibration error
  is created. Result categories: CONSISTENT / INCONSISTENT / UNKNOWN /
  NOT_COMPARABLE (plus UNASSIGNED for unknown events).
- SCORING never invents a numerical accuracy score the evidence cannot
  support: the optional event-separated compatibility rate uses only
  observations with valid spatial AND temporal matches, reports the
  denominator/count, and never counts UNKNOWN as a negative.
- Validation output is DERIVED provenance, never OBSERVED. Comparing
  Tier-B effective-scenario outputs against observations does NOT
  promote the model to Tier-A; validation success is never as-built
  validation.

Non-goals (STRICT): calibration (Manning n, runoff coefficient,
catchment area, effective profile multipliers, storage-stage relations,
capacity parameters, thresholds), ML, radar, nowcasting, 2D surface
flooding, road/intersection risk, safe routing, public warnings,
street-level depth, fabricated discharge/stage observations, empirical
threshold fitting, parameter optimization, a Yamuna boundary, and any
automatic ingestion or modification of existing GSDL/DTP datasets.
"""

from __future__ import annotations

import enum
import math
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional, Tuple

from .kushak_hydraulic_state_classification import ReachHydraulicClassification
from .kushak_tiered_model import ModelTier
from .models import ProvenanceStatus


# ---------------------------------------------------------------------------
# Events (explicit, separate identities; never pooled)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ValidationEvent:
    """One explicit validation event identity with its date window."""

    event_id: str
    label: str
    window_start: datetime
    window_end: datetime


# Required events plus the partial-forcing event EV-03. Separate
# identities; observations are never pooled across them.
VALIDATION_EVENTS: Tuple[ValidationEvent, ...] = (
    ValidationEvent(
        event_id="EV-01",
        label="June 28, 2024",
        window_start=datetime(2024, 6, 28),
        window_end=datetime(2024, 6, 29),
    ),
    ValidationEvent(
        event_id="EV-02",
        label="July 8-10, 2023",
        window_start=datetime(2023, 7, 8),
        window_end=datetime(2023, 7, 11),
    ),
    ValidationEvent(
        event_id="EV-03",
        label="September 11, 2021 (partial forcing: documented "
        "05:30-08:30 IST 3-hour block)",
        window_start=datetime(2021, 9, 11),
        window_end=datetime(2021, 9, 12),
    ),
)

_EVENT_IDS = frozenset(e.event_id for e in VALIDATION_EVENTS)

# Historical event ID mapping table bridging Phase 14A catalogue IDs (EVT-*)
# to canonical validation IDs (EV-*). Preserves backward compatibility.
EVENT_ID_MAP: Dict[str, str] = {
    "EVT-2024-06-27": "EV-01",
    "EVT-2023-07-08": "EV-02",
    "EVT-2021-09-11": "EV-03",
    "EV-01": "EV-01",
    "EV-02": "EV-02",
    "EV-03": "EV-03",
}


def resolve_event_id(event_id: Optional[str]) -> Optional[str]:
    """Deterministically map historical event ID (EVT-*) or canonical EV-* to canonical event ID."""
    if event_id is None:
        return None
    return EVENT_ID_MAP.get(event_id.strip(), event_id.strip())


# ---------------------------------------------------------------------------
# Observation classes / matching enums
# ---------------------------------------------------------------------------


class ValidationSourceClass(str, enum.Enum):
    """Source classes preserving evidentiary meaning (never conflated)."""

    GSDL_WATERLOGGING_OCCURRENCE = "GSDL_WATERLOGGING_OCCURRENCE"
    DTP_OPERATIONAL_OBSERVATION = "DTP_OPERATIONAL_OBSERVATION"
    CWC_DOWNSTREAM_RIVER_LEVEL = "CWC_DOWNSTREAM_RIVER_LEVEL"
    RAINFALL_OBSERVATION = "RAINFALL_OBSERVATION"
    EXTERNAL_FLOOD_EXTENT = "EXTERNAL_FLOOD_EXTENT"


class TimestampPrecision(str, enum.Enum):
    """Preserved observation-time precision; never upgraded."""

    DATE_ONLY = "DATE_ONLY"
    DATETIME = "DATETIME"
    UNKNOWN = "UNKNOWN"


class SpatialMatch(str, enum.Enum):
    MATCHED = "MATCHED"
    OUT_OF_CORRIDOR = "OUT_OF_CORRIDOR"
    UNKNOWN = "UNKNOWN"  # no coordinates, or no deterministic rule inputs


class TemporalMatch(str, enum.Enum):
    MATCHED = "MATCHED"
    NO_MATCH = "NO_MATCH"
    UNKNOWN = "UNKNOWN"  # unknown timestamp, DATE_ONLY, or no timestep


class ValidationOutcome(str, enum.Enum):
    CONSISTENT = "CONSISTENT"
    INCONSISTENT = "INCONSISTENT"
    UNKNOWN = "UNKNOWN"
    NOT_COMPARABLE = "NOT_COMPARABLE"
    UNASSIGNED = "UNASSIGNED"


# Source classes whose occurrence evidence may be compared against the
# model state. CWC (downstream context), rainfall (forcing), and external
# extent (unavailable unless ingested) are NOT flood observations and are
# never compared.
_COMPARABLE_CLASSES = (
    ValidationSourceClass.GSDL_WATERLOGGING_OCCURRENCE,
    ValidationSourceClass.DTP_OPERATIONAL_OBSERVATION,
)

# Model states consistent with an observed waterlogging occurrence.
_ELEVATED_STATES = (
    ReachHydraulicClassification.ELEVATED,
    ReachHydraulicClassification.SURCHARGED,
)


# ---------------------------------------------------------------------------
# Validation record
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ValidationRecord:
    """One event-separated validation outcome.

    Retains event_id, source_class, source provenance, observation-time
    precision, spatial/temporal match status, model tier, model state,
    and the validation result. `result_provenance` is always DERIVED —
    validation output is never marked OBSERVED.
    """

    event_id: Optional[str]
    source_class: ValidationSourceClass
    source_provenance: ProvenanceStatus
    timestamp_precision: TimestampPrecision
    spatial_match: SpatialMatch
    temporal_match: TemporalMatch
    model_tier: str
    validation_result: ValidationOutcome
    result_provenance: ProvenanceStatus = ProvenanceStatus.DERIVED
    timestamp: Optional[datetime] = None
    reach_id: Optional[str] = None  # set ONLY on a deterministic match
    model_state: Optional[ReachHydraulicClassification] = None
    diagnostic: str = ""


def _is_finite(v) -> bool:
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        return False
    return math.isfinite(v)


def _haversine_m(lat1, lon1, lat2, lon2) -> float:
    """Great-circle distance in metres (deterministic; standard formula)."""
    r = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = (
        math.sin(dp / 2) ** 2
        + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    )
    return 2 * r * math.asin(math.sqrt(a))


# ---------------------------------------------------------------------------
# Single-observation validation
# ---------------------------------------------------------------------------


def validate_observation(
    event_id: Optional[str],
    source_class: ValidationSourceClass,
    source_provenance: ProvenanceStatus,
    timestamp: Optional[datetime],
    timestamp_precision: TimestampPrecision,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    reach_reference_points: Optional[Dict[str, Tuple[float, float]]] = None,
    max_match_distance_m: Optional[float] = None,
    model_state: Optional[ReachHydraulicClassification] = None,
    model_tier: str = ModelTier.TIER_B_EFFECTIVE_SCENARIO.value,
    model_timestep: Optional[Tuple[datetime, datetime]] = None,
) -> ValidationRecord:
    """Validate one observation against the current model state.

    Deterministic, event-separated, and non-mutating:

    - event_id not exactly a known event -> UNASSIGNED/UNKNOWN (never
      silently attached to an event, never pooled).
    - no coordinates -> spatial_match UNKNOWN (no reach assignment; text
      mentions never assign a reach).
    - coordinates + caller-supplied reach reference points + max
      distance -> deterministic nearest-reach match within the distance;
      beyond it -> OUT_OF_CORRIDOR (never force-matched).
    - unknown timestamp or DATE_ONLY precision -> temporal_match UNKNOWN
      (no invented timestep; DATE_ONLY precision is preserved).
    - occurrence observation + valid spatial AND temporal match ->
      CONSISTENT (model elevated/surcharged), INCONSISTENT (model
      normal/dry), NOT_COMPARABLE (model unknown/blocked).
    - CWC / rainfall / external-extent observations are context or
      forcing evidence, never compared -> NOT_COMPARABLE.
    """
    # 1. Event separation — mandatory explicit identity; resolve bridge first.
    resolved = resolve_event_id(event_id) if event_id is not None else None
    # Preserve backward compatibility: original EV-* IDs remain recognized.
    canonical_id = resolved if resolved in _EVENT_IDS else event_id
    if canonical_id not in _EVENT_IDS:
        return ValidationRecord(
            event_id=event_id,
            source_class=source_class,
            source_provenance=source_provenance,
            timestamp_precision=timestamp_precision,
            spatial_match=SpatialMatch.UNKNOWN,
            temporal_match=TemporalMatch.UNKNOWN,
            model_tier=model_tier,
            validation_result=ValidationOutcome.UNASSIGNED,
            timestamp=timestamp,
            diagnostic=(
                f"event_id {event_id!r} is not a known validation event "
                f"(known: {sorted(_EVENT_IDS)}); result UNASSIGNED — never "
                "silently attached to an event"
            ),
        )

    # 2. Spatial matching — coordinates only; never invented.
    spatial = SpatialMatch.UNKNOWN
    reach_id: Optional[str] = None
    has_coords = latitude is not None or longitude is not None
    if has_coords:
        if not (_is_finite(latitude) and _is_finite(longitude)):
            return ValidationRecord(
                event_id=event_id,
                source_class=source_class,
                source_provenance=source_provenance,
                timestamp_precision=timestamp_precision,
                spatial_match=SpatialMatch.UNKNOWN,
                temporal_match=TemporalMatch.UNKNOWN,
                model_tier=model_tier,
                validation_result=ValidationOutcome.UNKNOWN,
                timestamp=timestamp,
                diagnostic=(
                    f"non-finite coordinates (lat={latitude!r}, "
                    f"lon={longitude!r}); no coordinates invented"
                ),
            )
        if reach_reference_points and max_match_distance_m is not None:
            best_id, best_d = None, None
            for rid, (rlat, rlon) in reach_reference_points.items():
                d = _haversine_m(latitude, longitude, rlat, rlon)
                if best_d is None or d < best_d:
                    best_id, best_d = rid, d
            if best_d is not None and best_d <= max_match_distance_m:
                spatial, reach_id = SpatialMatch.MATCHED, best_id
            else:
                spatial = SpatialMatch.OUT_OF_CORRIDOR
        # no reference points / max distance -> stays UNKNOWN (no rule
        # inputs supplied; nothing invented)

    # 3. Temporal matching — explicit times only; never invented.
    temporal = TemporalMatch.UNKNOWN
    if timestamp is not None and timestamp_precision == TimestampPrecision.DATETIME:
        if model_timestep is not None:
            start, end = model_timestep
            temporal = (
                TemporalMatch.MATCHED if start <= timestamp <= end
                else TemporalMatch.NO_MATCH
            )
        # no model timestep supplied -> stays UNKNOWN (no arbitrary timestep)
    # DATE_ONLY precision is preserved; it can never match a timestep.

    # 4. Occurrence/state compatibility (the ONLY comparison made here).
    if source_class not in _COMPARABLE_CLASSES:
        result = ValidationOutcome.NOT_COMPARABLE
        diagnostic = (
            f"{source_class.value} is context/forcing evidence, not a "
            "flood observation; not compared against the model state"
        )
    elif spatial != SpatialMatch.MATCHED or temporal != TemporalMatch.MATCHED:
        result = ValidationOutcome.UNKNOWN
        diagnostic = (
            f"no valid spatial/temporal match (spatial={spatial.value}, "
            f"temporal={temporal.value}); comparison not attempted"
        )
    elif model_state in _ELEVATED_STATES:
        result = ValidationOutcome.CONSISTENT
        diagnostic = (
            "observed waterlogging occurrence + model "
            f"{model_state.value} state -> consistent (occurrence/state "
            "compatibility only)"
        )
    elif model_state in (
        ReachHydraulicClassification.NORMAL_CAPACITY,
        ReachHydraulicClassification.DRY,
    ):
        result = ValidationOutcome.INCONSISTENT
        diagnostic = (
            "observed waterlogging occurrence + model "
            f"{model_state.value} state -> inconsistent"
        )
    else:
        result = ValidationOutcome.NOT_COMPARABLE
        diagnostic = (
            f"model state {model_state} is not a comparable hydraulic "
            "state; occurrence/state compatibility not applicable"
        )

    return ValidationRecord(
        event_id=event_id,
        source_class=source_class,
        source_provenance=source_provenance,
        timestamp_precision=timestamp_precision,
        spatial_match=spatial,
        temporal_match=temporal,
        model_tier=model_tier,
        validation_result=result,
        timestamp=timestamp,
        reach_id=reach_id,
        model_state=model_state,
        diagnostic=diagnostic,
    )


# ---------------------------------------------------------------------------
# Event-separated scoring (optional; never invented beyond the evidence)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class EventCompatibilityScore:
    """Occurrence/state compatibility rate for ONE event.

    Uses only observations with valid spatial AND temporal matches;
    reports the denominator/count explicitly; UNKNOWN and UNASSIGNED are
    never counted as negatives. rate is None when the denominator is 0
    (no numerical score is invented the evidence cannot support).
    """

    event_id: str
    consistent_count: int
    inconsistent_count: int
    denominator: int
    rate: Optional[float]
    diagnostic: str


def event_compatibility_score(
    records: Tuple[ValidationRecord, ...],
    event_id: str,
) -> EventCompatibilityScore:
    """Score ONE event's occurrence/state compatibility.

    Event-separated: only records whose event_id equals the requested
    event are used; observations from other events are never pooled in.
    Only CONSISTENT/INCONSISTENT (matched) records enter the denominator.
    """
    consistent = sum(
        1 for r in records
        if r.event_id == event_id
        and r.validation_result == ValidationOutcome.CONSISTENT
    )
    inconsistent = sum(
        1 for r in records
        if r.event_id == event_id
        and r.validation_result == ValidationOutcome.INCONSISTENT
    )
    denominator = consistent + inconsistent
    rate = (consistent / denominator) if denominator > 0 else None
    return EventCompatibilityScore(
        event_id=event_id,
        consistent_count=consistent,
        inconsistent_count=inconsistent,
        denominator=denominator,
        rate=rate,
        diagnostic=(
            f"event {event_id}: {consistent} consistent / "
            f"{inconsistent} inconsistent (denominator {denominator}); "
            + (
                f"rate {rate:.3f}"
                if rate is not None
                else "no rate — evidence cannot support a numerical score"
            )
            + "; UNKNOWN/UNASSIGNED never counted as negatives; other "
            "events never pooled in"
        ),
    )
