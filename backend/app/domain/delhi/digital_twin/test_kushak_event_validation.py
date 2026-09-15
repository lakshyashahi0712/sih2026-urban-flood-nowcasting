"""Phase 9 focused tests: validation contract."""

import pytest
from datetime import datetime, timezone
from .kushak_event_validation import (
    validate_observation,
    event_compatibility_score,
    ValidationRecord,
    ValidationSourceClass,
    TimestampPrecision,
    SpatialMatch,
    TemporalMatch,
    ValidationOutcome,
)
from .kushak_hydraulic_state_classification import ReachHydraulicClassification
from .models import ProvenanceStatus

T0 = datetime(2024, 6, 28, 12, 0, tzinfo=timezone.utc)

def _obs(event_id="EV-01"):
    return {
        "event_id": event_id,
        "source_class": ValidationSourceClass.GSDL_WATERLOGGING_OCCURRENCE,
        "source_provenance": ProvenanceStatus.OBSERVED,
        "timestamp": T0,
        "timestamp_precision": TimestampPrecision.DATETIME,
    }

def test_event_id_invalid():
    # Test invalid event handling
    res = validate_observation(
        event_id="INVALID",
        source_class=ValidationSourceClass.GSDL_WATERLOGGING_OCCURRENCE,
        source_provenance=ProvenanceStatus.OBSERVED,
        timestamp=T0,
        timestamp_precision=TimestampPrecision.DATETIME
    )
    assert res.validation_result == ValidationOutcome.UNASSIGNED

def test_spatial_matching_deterministic():
    # Deterministic nearest-reach match
    reach_pts = {"OC-01": (28.5, 77.2)}
    # Match within 100m
    obs = _obs()
    res = validate_observation(
        event_id="EV-01",
        source_class=ValidationSourceClass.GSDL_WATERLOGGING_OCCURRENCE,
        source_provenance=ProvenanceStatus.OBSERVED,
        timestamp=T0,
        timestamp_precision=TimestampPrecision.DATETIME,
        latitude=28.5005, longitude=77.2005,
        reach_reference_points=reach_pts,
        max_match_distance_m=100.0,
        model_state=ReachHydraulicClassification.ELEVATED
    )
    assert res.spatial_match == SpatialMatch.MATCHED
    assert res.reach_id == "OC-01"

    # Out of corridor (too far)
    res_out = validate_observation(
        event_id="EV-01",
        source_class=ValidationSourceClass.GSDL_WATERLOGGING_OCCURRENCE,
        source_provenance=ProvenanceStatus.OBSERVED,
        timestamp=T0,
        timestamp_precision=TimestampPrecision.DATETIME,
        latitude=28.6, longitude=77.3,
        reach_reference_points=reach_pts,
        max_match_distance_m=100.0,
        model_state=ReachHydraulicClassification.ELEVATED
    )
    assert res_out.spatial_match == SpatialMatch.OUT_OF_CORRIDOR
    assert res_out.reach_id is None

def test_temporal_matching_deterministic():
    # Match within window
    ts = datetime(2024, 6, 28, 12, 0, tzinfo=timezone.utc)
    timestep = (datetime(2024, 6, 28, 0, 0, tzinfo=timezone.utc), datetime(2024, 6, 28, 23, 59, tzinfo=timezone.utc))

    res = validate_observation(
        event_id="EV-01",
        source_class=ValidationSourceClass.GSDL_WATERLOGGING_OCCURRENCE,
        source_provenance=ProvenanceStatus.OBSERVED,
        timestamp=ts,
        timestamp_precision=TimestampPrecision.DATETIME,
        model_timestep=timestep,
        model_state=ReachHydraulicClassification.ELEVATED
    )
    assert res.temporal_match == TemporalMatch.MATCHED

def test_scoring_event_separated():
    # Only records whose event_id equals the requested event are used
    records = (
        ValidationRecord(
            event_id="EV-01",
            source_class=ValidationSourceClass.GSDL_WATERLOGGING_OCCURRENCE,
            source_provenance=ProvenanceStatus.OBSERVED,
            timestamp_precision=TimestampPrecision.DATETIME,
            spatial_match=SpatialMatch.MATCHED,
            temporal_match=TemporalMatch.MATCHED,
            model_tier="TIER_B",
            validation_result=ValidationOutcome.CONSISTENT
        ),
        ValidationRecord(
            event_id="EV-02",
            source_class=ValidationSourceClass.GSDL_WATERLOGGING_OCCURRENCE,
            source_provenance=ProvenanceStatus.OBSERVED,
            timestamp_precision=TimestampPrecision.DATETIME,
            spatial_match=SpatialMatch.MATCHED,
            temporal_match=TemporalMatch.MATCHED,
            model_tier="TIER_B",
            validation_result=ValidationOutcome.INCONSISTENT
        ),
    )

    score_ev2 = event_compatibility_score(records, "EV-02")
    assert score_ev2.consistent_count == 0
    assert score_ev2.inconsistent_count == 1
    assert score_ev2.denominator == 1

    score_ev1 = event_compatibility_score(records, "EV-01")
    assert score_ev1.consistent_count == 1
    assert score_ev1.inconsistent_count == 0
    assert score_ev1.denominator == 1

def test_non_comparable_source_class():
    # CWC river level is not a flood observation
    res = validate_observation(
        event_id="EV-01",
        source_class=ValidationSourceClass.CWC_DOWNSTREAM_RIVER_LEVEL,
        source_provenance=ProvenanceStatus.OBSERVED,
        timestamp=T0,
        timestamp_precision=TimestampPrecision.DATETIME,
        model_state=ReachHydraulicClassification.ELEVATED
    )
    assert res.validation_result == ValidationOutcome.NOT_COMPARABLE
