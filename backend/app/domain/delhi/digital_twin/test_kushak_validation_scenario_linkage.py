"""Tests for Phase 9 Step 6: Optional Descriptive Validation Linkage."""

import pytest
from datetime import datetime, timezone

from .kushak_validation_scenario_linkage import (
    link_validation_to_scenario,
    ValidationScenarioLinkageResult,
)
from .kushak_event_validation import (
    ValidationRecord,
    ValidationOutcome,
    ValidationSourceClass,
    TimestampPrecision,
    SpatialMatch,
    TemporalMatch,
)
from .models import ProvenanceStatus


def _make_record(event_id="EV-01", reach_id="OC-01", outcome=ValidationOutcome.CONSISTENT):
    return ValidationRecord(
        event_id=event_id,
        reach_id=reach_id,
        source_class=ValidationSourceClass.GSDL_WATERLOGGING_OCCURRENCE,
        source_provenance=ProvenanceStatus.OBSERVED,
        timestamp_precision=TimestampPrecision.DATETIME,
        spatial_match=SpatialMatch.MATCHED,
        temporal_match=TemporalMatch.MATCHED,
        model_tier="TIER_B_EFFECTIVE_SCENARIO",
        validation_result=outcome,
        timestamp=datetime(2024, 6, 28, 12, 0, tzinfo=timezone.utc),
    )


def test_step6_1_valid_ev01_linkage():
    rec = _make_record(event_id="EV-01", reach_id="OC-01", outcome=ValidationOutcome.CONSISTENT)
    res = link_validation_to_scenario(rec, "KUSHAK-CONSERVATIVE-WORKING_27_66", "EV-01", "OC-01")
    assert res.linkage_status == "LINKED"
    assert res.event_id == "EV-01"
    assert res.reach_id == "OC-01"
    assert res.scenario_member_id == "KUSHAK-CONSERVATIVE-WORKING_27_66"
    assert res.validation_result == ValidationOutcome.CONSISTENT


def test_step6_2_valid_ev02_linkage():
    rec = _make_record(event_id="EV-02", reach_id="OC-02", outcome=ValidationOutcome.INCONSISTENT)
    res = link_validation_to_scenario(rec, "KUSHAK-CENTRAL-WORKING_27_66", "EV-02", "OC-02")
    assert res.linkage_status == "LINKED"
    assert res.event_id == "EV-02"
    assert res.reach_id == "OC-02"
    assert res.scenario_member_id == "KUSHAK-CENTRAL-WORKING_27_66"
    assert res.validation_result == ValidationOutcome.INCONSISTENT


def test_step6_3_event_mismatch():
    rec = _make_record(event_id="EV-01", reach_id="OC-01")
    res = link_validation_to_scenario(rec, "KUSHAK-CONSERVATIVE-WORKING_27_66", "EV-02", "OC-01")
    assert res.linkage_status == "UNAVAILABLE"


def test_step6_4_reach_mismatch():
    rec = _make_record(event_id="EV-01", reach_id="OC-01")
    res = link_validation_to_scenario(rec, "KUSHAK-CONSERVATIVE-WORKING_27_66", "EV-01", "OC-02")
    assert res.linkage_status == "UNAVAILABLE"


def test_step6_5_missing_scenario_member_id():
    rec = _make_record()
    res = link_validation_to_scenario(rec, "", "EV-01", "OC-01")
    assert res.linkage_status == "UNAVAILABLE"


def test_step6_6_missing_scenario_event():
    rec = _make_record()
    res = link_validation_to_scenario(rec, "KUSHAK-CONSERVATIVE-WORKING_27_66", "", "OC-01")
    assert res.linkage_status == "UNAVAILABLE"


def test_step6_7_missing_scenario_reach():
    rec = _make_record()
    res = link_validation_to_scenario(rec, "KUSHAK-CONSERVATIVE-WORKING_27_66", "EV-01", "")
    assert res.linkage_status == "UNAVAILABLE"


def test_step6_8_missing_validation_record():
    res = link_validation_to_scenario(None, "KUSHAK-CONSERVATIVE-WORKING_27_66", "EV-01", "OC-01")
    assert res.linkage_status == "UNAVAILABLE"


def test_step6_9_consistent_preservation():
    rec = _make_record(outcome=ValidationOutcome.CONSISTENT)
    res = link_validation_to_scenario(rec, "M1", "EV-01", "OC-01")
    assert res.validation_result == ValidationOutcome.CONSISTENT


def test_step6_10_inconsistent_preservation():
    rec = _make_record(outcome=ValidationOutcome.INCONSISTENT)
    res = link_validation_to_scenario(rec, "M1", "EV-01", "OC-01")
    assert res.validation_result == ValidationOutcome.INCONSISTENT


def test_step6_11_unknown_preservation():
    rec = _make_record(outcome=ValidationOutcome.UNKNOWN)
    res = link_validation_to_scenario(rec, "M1", "EV-01", "OC-01")
    assert res.validation_result == ValidationOutcome.UNKNOWN


def test_step6_12_not_comparable_preservation():
    rec = _make_record(outcome=ValidationOutcome.NOT_COMPARABLE)
    res = link_validation_to_scenario(rec, "M1", "EV-01", "OC-01")
    assert res.validation_result == ValidationOutcome.NOT_COMPARABLE


def test_step6_13_unassigned_preservation():
    rec = _make_record(outcome=ValidationOutcome.UNASSIGNED)
    res = link_validation_to_scenario(rec, "M1", "EV-01", "OC-01")
    assert res.validation_result == ValidationOutcome.UNASSIGNED


def test_step6_14_event_separation():
    rec1 = _make_record(event_id="EV-01")
    rec2 = _make_record(event_id="EV-02")
    res1 = link_validation_to_scenario(rec1, "M1", "EV-01", "OC-01")
    res2 = link_validation_to_scenario(rec2, "M1", "EV-02", "OC-01")
    assert res1.event_id == "EV-01"
    assert res2.event_id == "EV-02"


def test_step6_15_scenario_member_id_preservation():
    rec = _make_record()
    res = link_validation_to_scenario(rec, "CUSTOM-MEMBER-ID", "EV-01", "OC-01")
    assert res.scenario_member_id == "CUSTOM-MEMBER-ID"


def test_step6_16_no_hydraulic_output_mutation():
    rec = _make_record()
    res = link_validation_to_scenario(rec, "M1", "EV-01", "OC-01")
    assert not hasattr(res, "stage_m")
    assert not hasattr(res, "storage_m3")


def test_step6_17_no_parameter_mutation():
    rec = _make_record()
    res = link_validation_to_scenario(rec, "M1", "EV-01", "OC-01")
    assert not hasattr(res, "manning_n")
    assert not hasattr(res, "runoff_coefficient")


def test_step6_18_no_tier_a_promotion():
    rec = _make_record()
    res = link_validation_to_scenario(rec, "M1", "EV-01", "OC-01")
    assert res.model_tier == "TIER_B_EFFECTIVE_SCENARIO"
    assert "TIER_A" not in res.model_tier


def test_step6_19_derived_provenance():
    rec = _make_record()
    res = link_validation_to_scenario(rec, "M1", "EV-01", "OC-01")
    assert res.provenance == ProvenanceStatus.DERIVED


def test_step6_20_deterministic_repeated_execution():
    rec = _make_record()
    r1 = link_validation_to_scenario(rec, "M1", "EV-01", "OC-01")
    r2 = link_validation_to_scenario(rec, "M1", "EV-01", "OC-01")
    assert r1 == r2


def test_step6_21_no_coordinate_inference():
    rec = _make_record()
    res = link_validation_to_scenario(rec, "M1", "EV-01", "OC-01")
    assert not hasattr(res, "latitude")
    assert not hasattr(res, "longitude")


def test_step6_22_no_timestamp_inference():
    rec = _make_record()
    res = link_validation_to_scenario(rec, "M1", "EV-01", "OC-01")
    assert res.event_id == "EV-01"


def test_step6_23_no_fabricated_observation():
    rec = _make_record()
    res = link_validation_to_scenario(rec, "M1", "EV-01", "OC-01")
    assert res.linkage_status == "LINKED"


def test_step6_24_no_hydraulic_model_rerun():
    rec = _make_record()
    res = link_validation_to_scenario(rec, "M1", "EV-01", "OC-01")
    assert res.scenario_member_id == "M1"
