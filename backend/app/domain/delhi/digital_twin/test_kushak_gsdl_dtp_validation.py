"""Tests for Phase 11 Step 5: GSDL / DTP Empirical Validation."""

import pytest
from datetime import datetime, timezone

from .kushak_gsdl_dtp_validation import (
    GsdloObservation,
    DtpObservation,
    load_gsdl_observations,
    load_dtp_observations,
    map_date_to_event_id,
    is_in_kushak_corridor,
    validate_gsdl_observation_item,
    validate_dtp_observation_item,
)
from .kushak_event_validation import (
    ValidationOutcome,
    SpatialMatch,
    TemporalMatch,
    ValidationSourceClass,
    TimestampPrecision,
)
from .kushak_hydraulic_state_classification import ReachHydraulicClassification
from .models import ProvenanceStatus

UTC = timezone.utc
T_EV01 = datetime(2024, 6, 28, 10, 0, tzinfo=UTC)
T_EV02 = datetime(2023, 7, 9, 12, 0, tzinfo=UTC)


def test_step5_1_ev01_gsdl_linked_to_ev01():
    """1. EV-01 GSDL evidence (2024-06-28) is correctly mapped to EV-01."""
    obs = GsdloObservation(
        source_layer="Layer 0: Water_Logging_Location2023_2024",
        source_layer_id="0",
        source_fid="12",
        observation_date="2024-06-28",
        road_name="Minto Road",
        location_raw="Minto Bridge",
        latitude=28.6367,
        longitude=77.2225,
        agency="UNKNOWN",
        year=2024,
        provenance="OFFICIAL / OBSERVED",
        observation_type="WATERLOGGING_OCCURRENCE",
    )
    assert map_date_to_event_id(obs.observation_date) == "EV-01"


def test_step5_2_ev02_gsdl_linked_to_ev02():
    """2. EV-02 GSDL evidence (2023-07-09) is correctly mapped to EV-02."""
    obs = GsdloObservation(
        source_layer="Layer 0: Water_Logging_Location2023_2024",
        source_layer_id="0",
        source_fid="193",
        observation_date="2023-07-09",
        road_name="Mathura Road",
        location_raw="Gate No. 7, Pragati Maidan",
        latitude=28.6194,
        longitude=77.2404,
        agency="UNKNOWN",
        year=2023,
        provenance="OFFICIAL / OBSERVED",
        observation_type="WATERLOGGING_OCCURRENCE",
    )
    assert map_date_to_event_id(obs.observation_date) == "EV-02"


def test_step5_3_dtp_evidence_event_specific():
    """3. DTP evidence is event-specific (EV-01 vs EV-02)."""
    dtp_ev1 = DtpObservation(
        source_url="https://twitter.com/dtptraffic/status/1806526137688170889",
        source_document="Delhi Traffic Police Alert June 28 2024",
        date="2024-06-28",
        time="08:15 IST",
        road_name="Aurobindo Marg",
        location="Under AIIMS Flyover",
        severity_raw="Severe disruption",
        depth_raw="UNKNOWN",
        closure_raw="Avoid stretch",
        duration_raw="UNKNOWN",
        evidence_type="OFFICIAL — INCIDENT/ADVISORY",
        provenance="OFFICIAL",
        notes="Kushak Nallah crossing",
    )
    dtp_ev2 = DtpObservation(
        source_url="https://twitter.com/dtptraffic/status/1677626998980841473",
        source_document="Delhi Traffic Police Alert July 8 2023",
        date="2023-07-08",
        time="15:45 IST",
        road_name="Aurobindo Marg",
        location="IIT towards PTS",
        severity_raw="Traffic affected",
        depth_raw="UNKNOWN",
        closure_raw="Impeded",
        duration_raw="UNKNOWN",
        evidence_type="OFFICIAL — INCIDENT/ADVISORY",
        provenance="OFFICIAL",
        notes="Southern arterial reach",
    )
    assert map_date_to_event_id(dtp_ev1.date) == "EV-01"
    assert map_date_to_event_id(dtp_ev2.date) == "EV-02"


def test_step5_4_gsdl_layer_0_preserved():
    """4. GSDL Layer 0 source layer identity is preserved."""
    obs = GsdloObservation(
        source_layer="Layer 0: Water_Logging_Location2023_2024",
        source_layer_id="0",
        source_fid="0",
        observation_date="2024-06-27",
        road_name="Najafgarh Road",
        location_raw="Moti Nagar",
        latitude=28.6597,
        longitude=77.1460,
        agency="UNKNOWN",
        year=2024,
        provenance="OFFICIAL / OBSERVED",
        observation_type="WATERLOGGING_OCCURRENCE",
    )
    assert "Layer 0" in obs.source_layer


def test_step5_5_gsdl_layer_1_preserved():
    """5. GSDL Layer 1 source layer identity is preserved."""
    obs = GsdloObservation(
        source_layer="Water_Logging_Locations_Dated_30042025",
        source_layer_id="1",
        source_fid="10",
        observation_date="2023-07-08",
        road_name="Aurobindo Marg",
        location_raw="AIIMS",
        latitude=28.57,
        longitude=77.21,
        agency="UNKNOWN",
        year=2023,
        provenance="OFFICIAL / OBSERVED",
        observation_type="WATERLOGGING_OCCURRENCE",
    )
    assert "Water_Logging_Locations_Dated_30042025" in obs.source_layer


def test_step5_6_gsdl_no_depth_field_treated_as_occurrence():
    """6. GSDL points without depth are treated solely as occurrence reports, not hydraulic depth."""
    obs = GsdloObservation(
        source_layer="Layer 0: Water_Logging_Location2023_2024",
        source_layer_id="0",
        source_fid="0",
        observation_date="2024-06-28",
        road_name="Minto Road",
        location_raw="Minto Bridge",
        latitude=28.6367,
        longitude=77.2225,
        agency="UNKNOWN",
        year=2024,
        provenance="OFFICIAL / OBSERVED",
        observation_type="WATERLOGGING_OCCURRENCE",
    )
    # GSDL source data does not contain depth field; validation source class is occurrence only
    rec = validate_gsdl_observation_item(obs, model_state=ReachHydraulicClassification.ELEVATED)
    assert rec.source_class == ValidationSourceClass.GSDL_WATERLOGGING_OCCURRENCE


def test_step5_7_dtp_no_coordinates_not_geocoded():
    """7. DTP records without coordinates are not spatially geocoded (spatial_match = UNKNOWN)."""
    dtp = DtpObservation(
        source_url="https://traffic.delhipolice.gov.in/",
        source_document="DTP Log",
        date="2024-06-28",
        time="07:30 IST",
        road_name="Ring Road",
        location="Moolchand Underpass",
        severity_raw="Severe waterlogging",
        depth_raw="UNKNOWN",
        closure_raw="Closed",
        duration_raw="UNKNOWN",
        evidence_type="OFFICIAL",
        provenance="OFFICIAL",
        notes="Test",
    )
    rec = validate_dtp_observation_item(dtp, model_state=ReachHydraulicClassification.ELEVATED)
    assert rec.spatial_match == SpatialMatch.UNKNOWN


def test_step5_8_unsupported_spatial_linkage_unknown():
    """8. Unsupported spatial linkage or missing reach reference points becomes UNKNOWN."""
    obs = GsdloObservation(
        source_layer="Layer 0",
        source_layer_id="0",
        source_fid="999",
        observation_date="2024-06-28",
        road_name="Unknown Road",
        location_raw="Far Outside Corridor",
        latitude=28.999,
        longitude=77.999,
        agency="UNKNOWN",
        year=2024,
        provenance="OFFICIAL / OBSERVED",
        observation_type="WATERLOGGING_OCCURRENCE",
    )
    rec = validate_gsdl_observation_item(obs, model_state=ReachHydraulicClassification.ELEVATED)
    # Outside bounding box or missing reach reference points -> spatial match UNKNOWN
    assert rec.spatial_match == SpatialMatch.UNKNOWN


def test_step5_9_temporal_mismatch_unknown():
    """9. Temporal mismatch or unknown timestamp leads to UNKNOWN/NO_MATCH state."""
    dtp = DtpObservation(
        source_url="https://traffic.delhipolice.gov.in/",
        source_document="DTP Log",
        date="2024-06-28",
        time="UNKNOWN",
        road_name="Ring Road",
        location="Moolchand",
        severity_raw="Waterlogging",
        depth_raw="UNKNOWN",
        closure_raw="Open",
        duration_raw="UNKNOWN",
        evidence_type="OFFICIAL",
        provenance="OFFICIAL",
        notes="",
    )
    timestep = (datetime(2024, 6, 28, 12, 0, tzinfo=UTC), datetime(2024, 6, 28, 13, 0, tzinfo=UTC))
    rec = validate_dtp_observation_item(dtp, model_state=ReachHydraulicClassification.ELEVATED, model_timestep=timestep)
    # UNKNOWN time => timestamp remains None with DATE_ONLY precision -> temporal UNKNOWN
    assert rec.temporal_match == TemporalMatch.UNKNOWN


def test_step5_10_matching_evidence_consistent():
    """10. Matching evidence with elevated model state produces CONSISTENT."""
    reach_pts = {"reach_kushak_1": (28.58, 77.21)}
    obs = GsdloObservation(
        source_layer="Layer 0",
        source_layer_id="0",
        source_fid="1",
        observation_date="2024-06-28",
        road_name="Aurobindo Marg",
        location_raw="AIIMS",
        latitude=28.58,
        longitude=77.21,
        agency="UNKNOWN",
        year=2024,
        provenance="OFFICIAL / OBSERVED",
        observation_type="WATERLOGGING_OCCURRENCE",
    )
    timestep = (datetime(2024, 6, 28, 0, 0, tzinfo=UTC), datetime(2024, 6, 28, 23, 59, tzinfo=UTC))

    from .kushak_event_validation import validate_observation
    rec = validate_observation(
        event_id="EV-01",
        source_class=ValidationSourceClass.GSDL_WATERLOGGING_OCCURRENCE,
        source_provenance=ProvenanceStatus.OBSERVED,
        timestamp=T_EV01,
        timestamp_precision=TimestampPrecision.DATETIME,
        latitude=28.58,
        longitude=77.21,
        reach_reference_points=reach_pts,
        max_match_distance_m=500.0,
        model_state=ReachHydraulicClassification.ELEVATED,
        model_timestep=timestep,
    )
    assert rec.spatial_match == SpatialMatch.MATCHED
    assert rec.temporal_match == TemporalMatch.MATCHED
    assert rec.validation_result == ValidationOutcome.CONSISTENT


def test_step5_11_genuine_contradiction_inconsistent():
    """11. Occurrence observation with normal model state produces INCONSISTENT."""
    reach_pts = {"reach_kushak_1": (28.58, 77.21)}
    timestep = (datetime(2024, 6, 28, 0, 0, tzinfo=UTC), datetime(2024, 6, 28, 23, 59, tzinfo=UTC))

    from .kushak_event_validation import validate_observation
    rec = validate_observation(
        event_id="EV-01",
        source_class=ValidationSourceClass.GSDL_WATERLOGGING_OCCURRENCE,
        source_provenance=ProvenanceStatus.OBSERVED,
        timestamp=T_EV01,
        timestamp_precision=TimestampPrecision.DATETIME,
        latitude=28.58,
        longitude=77.21,
        reach_reference_points=reach_pts,
        max_match_distance_m=500.0,
        model_state=ReachHydraulicClassification.NORMAL_CAPACITY,
        model_timestep=timestep,
    )
    assert rec.spatial_match == SpatialMatch.MATCHED
    assert rec.temporal_match == TemporalMatch.MATCHED
    assert rec.validation_result == ValidationOutcome.INCONSISTENT


def test_step5_12_insufficient_evidence_unknown():
    """12. Insufficient evidence / missing match produces UNKNOWN."""
    obs = GsdloObservation(
        source_layer="Layer 0",
        source_layer_id="0",
        source_fid="1",
        observation_date="2024-06-28",
        road_name="Test Road",
        location_raw="Test",
        latitude=None,
        longitude=None,
        agency="UNKNOWN",
        year=2024,
        provenance="OFFICIAL",
        observation_type="WATERLOGGING_OCCURRENCE",
    )
    rec = validate_gsdl_observation_item(obs, model_state=None)
    assert rec.validation_result == ValidationOutcome.UNKNOWN


def test_step5_13_incompatible_quantities_not_comparable():
    """13. Incompatible quantities (e.g. non-comparable source classes) produce NOT_COMPARABLE."""
    from .kushak_event_validation import validate_observation
    rec = validate_observation(
        event_id="EV-01",
        source_class=ValidationSourceClass.CWC_DOWNSTREAM_RIVER_LEVEL,
        source_provenance=ProvenanceStatus.OBSERVED,
        timestamp=T_EV01,
        timestamp_precision=TimestampPrecision.DATETIME,
        model_state=ReachHydraulicClassification.ELEVATED,
    )
    assert rec.validation_result == ValidationOutcome.NOT_COMPARABLE


def test_step5_14_no_accuracy_metric_calculated():
    """14. No accuracy metrics (RMSE, accuracy, precision, F1, etc.) are calculated or returned."""
    # Verify validation records contain only discrete validation outcomes, not numerical error metrics.
    rec = validate_gsdl_observation_item(
        GsdloObservation("Layer 0", "0", "1", "2024-06-28", "Road", "Loc", 28.6, 77.2, "UN", 2024, "OFF", "OCC")
    )
    assert not hasattr(rec, "rmse")
    assert not hasattr(rec, "accuracy")
    assert not hasattr(rec, "precision")
    assert not hasattr(rec, "f1")


def test_step5_15_no_calibration_parameter_modified():
    """15. Validation does not modify calibration parameters (Manning n, C, catchment area remain untouched)."""
    from .kushak_scenario_ensemble import SCENARIO_RUNOFF_C
    from .kushak_evidence_model import CATCHMENT_SCENARIOS
    assert SCENARIO_RUNOFF_C == 0.75
    assert CATCHMENT_SCENARIOS["WORKING_27_66"].area_km2 == 27.66
    # Running validation does not alter these constants or modify model parameters.
    validate_gsdl_observation_item(
        GsdloObservation("Layer 0", "0", "1", "2024-06-28", "Road", "Loc", 28.6, 77.2, "UN", 2024, "OFF", "OCC")
    )
    assert SCENARIO_RUNOFF_C == 0.75
    assert CATCHMENT_SCENARIOS["WORKING_27_66"].area_km2 == 27.66


def test_step5_16_no_cross_event_substitution():
    """16. EV-01 evidence is never used to validate EV-02 and vice versa (event separation)."""
    # EV-01 evidence date
    obs_ev1 = GsdloObservation("Layer 0", "0", "1", "2024-06-28", "Road", "Loc", 28.6, 77.2, "UN", 2024, "OFF", "OCC")
    rec = validate_gsdl_observation_item(obs_ev1)
    assert rec.event_id == "EV-01"
    assert rec.event_id != "EV-02"

    # EV-02 evidence date
    obs_ev2 = GsdloObservation("Layer 0", "0", "193", "2023-07-09", "Road", "Loc", 28.6, 77.2, "UN", 2023, "OFF", "OCC")
    rec2 = validate_gsdl_observation_item(obs_ev2)
    assert rec2.event_id == "EV-02"
    assert rec2.event_id != "EV-01"


def test_step5_17_provenance_preserved():
    """17. Provenance is preserved (result_provenance is DERIVED, source provenance is OBSERVED)."""
    obs = GsdloObservation("Layer 0", "0", "1", "2024-06-28", "Road", "Loc", 28.6, 77.2, "UN", 2024, "OFFICIAL / OBSERVED", "OCC")
    rec = validate_gsdl_observation_item(obs)
    assert rec.result_provenance == ProvenanceStatus.DERIVED
    assert rec.source_provenance == ProvenanceStatus.OBSERVED


def test_step5_18_evidence_source_identity_preserved():
    """18. Evidence source identity and source classes are preserved."""
    obs = GsdloObservation("Layer 0: Water_Logging_Location2023_2024", "0", "1", "2024-06-28", "Road", "Loc", 28.6, 77.2, "UN", 2024, "OFF", "OCC")
    rec = validate_gsdl_observation_item(obs)
    assert rec.source_class == ValidationSourceClass.GSDL_WATERLOGGING_OCCURRENCE


def test_step5_19_repeated_validation_deterministic():
    """19. Repeated validation runs are deterministic and produce identical outcomes."""
    obs = GsdloObservation("Layer 0", "0", "1", "2024-06-28", "Road", "Loc", 28.6367, 77.2225, "UN", 2024, "OFF", "OCC")
    rec1 = validate_gsdl_observation_item(obs, model_state=ReachHydraulicClassification.ELEVATED)
    rec2 = validate_gsdl_observation_item(obs, model_state=ReachHydraulicClassification.ELEVATED)
    assert rec1 == rec2


def test_step5_20_validation_vocabulary_reused():
    """20. Existing Phase 8B validation vocabulary (CONSISTENT, INCONSISTENT, UNKNOWN, NOT_COMPARABLE) is reused."""
    assert ValidationOutcome.CONSISTENT.value == "CONSISTENT"
    assert ValidationOutcome.INCONSISTENT.value == "INCONSISTENT"
    assert ValidationOutcome.UNKNOWN.value == "UNKNOWN"
    assert ValidationOutcome.NOT_COMPARABLE.value == "NOT_COMPARABLE"
    assert ValidationOutcome.UNASSIGNED.value == "UNASSIGNED"


def test_step5_21_corridor_vs_broader_delhi():
    """Additional test: Corridor vs broader Delhi coordinate check."""
    # Within corridor approx bounding box
    assert is_in_kushak_corridor(28.58, 77.21) is True
    # Outside corridor (e.g. Rohini / outer Delhi)
    assert is_in_kushak_corridor(28.75, 77.10) is False


def test_step5_22_dataset_loading():
    """Additional test: GSDL and DTP normalized datasets load successfully without exception."""
    gsdl_items = load_gsdl_observations()
    dtp_items = load_dtp_observations()
    # Confirm records were loaded from the actual derived files
    assert len(gsdl_items) > 0
    assert len(dtp_items) > 0
