"""Tests for Step 10 validation aggregation."""

import pytest
from .kushak_event_validation import ValidationRecord, ValidationOutcome, ValidationSourceClass, TimestampPrecision, SpatialMatch, TemporalMatch
from .kushak_validation_aggregation import aggregate_validation_records, ReachEventOutcomeSummary
from .models import ProvenanceStatus

def test_empty_input():
    assert aggregate_validation_records(()) == ()

def test_aggregation_logic():
    records = (
        ValidationRecord(
            event_id="EV-01", reach_id="OC-01",
            source_class=ValidationSourceClass.GSDL_WATERLOGGING_OCCURRENCE,
            source_provenance=ProvenanceStatus.OBSERVED,
            timestamp_precision=TimestampPrecision.DATETIME,
            spatial_match=SpatialMatch.MATCHED,
            temporal_match=TemporalMatch.MATCHED,
            model_tier="TIER_B",
            validation_result=ValidationOutcome.CONSISTENT
        ),
        ValidationRecord(
            event_id="EV-01", reach_id="OC-01",
            source_class=ValidationSourceClass.GSDL_WATERLOGGING_OCCURRENCE,
            source_provenance=ProvenanceStatus.OBSERVED,
            timestamp_precision=TimestampPrecision.DATETIME,
            spatial_match=SpatialMatch.MATCHED,
            temporal_match=TemporalMatch.MATCHED,
            model_tier="TIER_B",
            validation_result=ValidationOutcome.INCONSISTENT
        ),
        ValidationRecord(
            event_id="EV-01", reach_id="OC-02",
            source_class=ValidationSourceClass.GSDL_WATERLOGGING_OCCURRENCE,
            source_provenance=ProvenanceStatus.OBSERVED,
            timestamp_precision=TimestampPrecision.DATETIME,
            spatial_match=SpatialMatch.MATCHED,
            temporal_match=TemporalMatch.MATCHED,
            model_tier="TIER_B",
            validation_result=ValidationOutcome.UNKNOWN
        ),
    )

    results = aggregate_validation_records(records)
    assert len(results) == 2

    # Verify aggregation
    oc01 = next(r for r in results if r.reach_id == "OC-01")
    assert oc01.consistent_count == 1
    assert oc01.inconsistent_count == 1
    assert oc01.unknown_count == 0

    oc02 = next(r for r in results if r.reach_id == "OC-02")
    assert oc02.unknown_count == 1
    assert oc02.consistent_count == 0

def test_event_reach_separation():
    records = (
        ValidationRecord(
            event_id="EV-01", reach_id="OC-01",
            source_class=ValidationSourceClass.GSDL_WATERLOGGING_OCCURRENCE,
            source_provenance=ProvenanceStatus.OBSERVED,
            timestamp_precision=TimestampPrecision.DATETIME,
            spatial_match=SpatialMatch.MATCHED,
            temporal_match=TemporalMatch.MATCHED,
            model_tier="TIER_B",
            validation_result=ValidationOutcome.CONSISTENT
        ),
        ValidationRecord(
            event_id="EV-02", reach_id="OC-01",
            source_class=ValidationSourceClass.GSDL_WATERLOGGING_OCCURRENCE,
            source_provenance=ProvenanceStatus.OBSERVED,
            timestamp_precision=TimestampPrecision.DATETIME,
            spatial_match=SpatialMatch.MATCHED,
            temporal_match=TemporalMatch.MATCHED,
            model_tier="TIER_B",
            validation_result=ValidationOutcome.CONSISTENT
        ),
    )

    results = aggregate_validation_records(records)
    assert len(results) == 2
    assert all(r.consistent_count == 1 for r in results)
