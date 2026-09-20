import pytest
from datetime import datetime
from backend.app.domain.delhi.digital_twin.historical_flood import HistoricalFloodObservation, ObservationType
from backend.app.domain.delhi.digital_twin.models import ProvenanceStatus
from backend.app.domain.delhi.digital_twin.historical_flood_event_assembly import EventQAAssembly


def create_obs(obs_id, ts, lat=None, lon=None, obs_type=ObservationType.RIVER_STAGE, value=1.0, source="src", provenance=ProvenanceStatus.OFFICIAL, event_id="N/A"):
    return HistoricalFloodObservation(
        observation_id=obs_id,
        event_id=event_id,
        timestamp=ts,
        latitude=lat,
        longitude=lon,
        observation_type=obs_type,
        value=value,
        unit="m",
        source=source,
        provenance=provenance
    )


def test_assignment_and_qa():
    obs = [
        # EV-01 window (2024-06-28) -> event_id="EV-01"
        create_obs("ev1", datetime(2024, 6, 28, 12, 0), event_id="EV-01"),
        # EV-02 window (2023-07-09) -> event_id="EV-02"
        create_obs("ev2", datetime(2023, 7, 9, 12, 0), event_id="EV-02"),
        # Outside windows -> unassigned: using default event_id="N/A"
        create_obs("un1", datetime(2024, 1, 1, 12, 0)),
        create_obs("un2", datetime(2023, 6, 1, 12, 0)),
        # None coordinates (should be valid)
        create_obs("coord_none", datetime(2024, 1, 1, 12, 0), lat=None, lon=None),
        # Unknown provenance
        create_obs("prov", datetime(2024, 1, 1, 12, 0), provenance=ProvenanceStatus.UNKNOWN),
        # Duplicates (2 observations with same ID)
        create_obs("dup", datetime(2024, 1, 1, 12, 0)),
        create_obs("dup", datetime(2024, 1, 1, 12, 0)),
        # Qualitative severity (string value)
        create_obs("qual", datetime(2024, 1, 1, 12, 0), obs_type=ObservationType.QUALITATIVE_SEVERITY, value="heavy"),
    ]

    assembler = EventQAAssembly(obs)
    report = assembler.get_qa_report()

    # Basic counts
    assert report["total"] == 9
    assert report["EV-01"] == 1   # ev1
    assert report["EV-02"] == 1   # ev2
    assert report["N/A"] == 7      # un1, un2, coord_none, prov, dup, dup, qual

    # Duplicate count: 2 observations with ID "dup" => 1 duplicate
    assert report["duplicate_observation_ids"] == 1

    # None coordinates should not be invalid
    assert report["invalid_coordinates"] == 0

    # Unknown provenance should be detected
    assert report["missing_provenance"] == 1

    # Qualitative severity value preserved as string
    qual_obs = [o for o in assembler.observations if o.observation_type == ObservationType.QUALITATIVE_SEVERITY][0]
    assert qual_obs.value == "heavy"
    assert isinstance(qual_obs.value, str)

    # Source counts
    assert report["by_source"]["src"] == 9  # 9 observations with source="src"
    assert report["by_source"].get("different_source", 0) == 0  # Not used in this test

    # Observation type counts
    assert report["by_observation_type"][str(ObservationType.RIVER_STAGE)] == 8  # ev1, ev2, un1, un2, coord_none, prov, dup, dup
    assert report["by_observation_type"][str(ObservationType.QUALITATIVE_SEVERITY)] == 1

    # Repeat assembly should produce identical results
    assembler2 = EventQAAssembly(obs)
    report2 = assembler2.get_qa_report()
    assert report == report2


def test_missing_coordinates_not_invalid():
    """Test that None/None coordinates are not counted as invalid."""
    obs = [
        create_obs("obs1", datetime(2024, 6, 28), lat=None, lon=None),
    ]
    assembler = EventQAAssembly(obs)
    report = assembler.get_qa_report()
    assert report["invalid_coordinates"] == 0
    assert report["total"] == 1


def test_unknown_provenance_preserved():
    """Test that UNKNOWN provenance is preserved and reported correctly."""
    obs = [
        create_obs("obs1", datetime(2024, 6, 28), event_id="temp",
                   lat=None, lon=None,
                   obs_type=ObservationType.RIVER_STAGE,
                   value=1.0,
                   source="test_source",
                   provenance=ProvenanceStatus.UNKNOWN)
    ]
    assembler = EventQAAssembly(obs)
    report = assembler.get_qa_report()
    assert report["missing_provenance"] == 1
    # Verify the provenance is still UNKNOWN in the observation
    assert assembler.observations[0].provenance == ProvenanceStatus.UNKNOWN


def test_duplicate_counting():
    """Test that duplicate observation IDs are counted correctly without removal."""
    obs = [
        create_obs("same_id", datetime(2024, 6, 28), event_id="N/A"),
        create_obs("same_id", datetime(2024, 6, 28, 1, 0), event_id="N/A"),
        create_obs("same_id", datetime(2024, 6, 28, 2, 0), event_id="N/A"),  # 3 total
        create_obs("unique_id", datetime(2024, 6, 28), event_id="N/A"),
    ]
    assembler = EventQAAssembly(obs)
    report = assembler.get_qa_report()
    # 3 observations with ID "same_id" => 2 duplicates (3-1=2)
    assert report["duplicate_observation_ids"] == 2
    assert report["total"] == 4
    # Verify observations are not removed
    assert len(assembler.observations) == 4


def test_source_and_type_counts():
    """Test that source and observation type counts are correct."""
    obs = [
        create_obs("src1", datetime(2024, 6, 28), source="source_A", event_id="N/A"),
        create_obs("src2", datetime(2024, 6, 28), source="source_A", event_id="N/A"),
        create_obs("src3", datetime(2024, 6, 28), source="source_B", obs_type=ObservationType.WATERLOGGING_OCCURRENCE, value="occurred", event_id="N/A"),
        create_obs("type1", datetime(2024, 6, 28), obs_type=ObservationType.RIVER_STAGE, event_id="N/A"),
        create_obs("type2", datetime(2024, 6, 28), obs_type=ObservationType.WATERLOGGING_OCCURRENCE, value="occurred", event_id="N/A"),
    ]
    assembler = EventQAAssembly(obs)
    report = assembler.get_qa_report()

    # Source counts
    assert report["by_source"]["source_A"] == 2
    assert report["by_source"]["source_B"] == 1
    assert report["by_source"]["src"] == 2  # type1 and type2 use default source "src"

    # Observation type counts - using string keys as returned by the assembly
    assert report["by_observation_type"][str(ObservationType.RIVER_STAGE)] == 3  # src1, src2, type1
    assert report["by_observation_type"][str(ObservationType.WATERLOGGING_OCCURRENCE)] == 2  # src3, type2
    assert report["by_observation_type"].get(str(ObservationType.QUALITATIVE_SEVERITY), 0) == 0
    assert report["by_observation_type"].get(str(ObservationType.ROAD_CLOSURE), 0) == 0
    assert report["by_observation_type"].get(str(ObservationType.FLOOD_EXTENT), 0) == 0


def test_qualitative_severity_preserved():
    """Test that qualitative severity values remain strings and are not converted."""
    obs = [
        create_obs("qual1", datetime(2024, 6, 28),
                  obs_type=ObservationType.QUALITATIVE_SEVERITY, value="heavy", event_id="N/A"),
        create_obs("qual2", datetime(2024, 6, 28),
                  obs_type=ObservationType.QUALITATIVE_SEVERITY, value="moderate", event_id="N/A"),
        create_obs("numeric", datetime(2024, 6, 28),
                  obs_type=ObservationType.RIVER_STAGE, value=1.5, event_id="N/A"),
    ]
    assembler = EventQAAssembly(obs)
    report = assembler.get_qa_report()

    # Check values are preserved
    qual_values = [obs.value for obs in assembler.observations
                   if obs.observation_type == ObservationType.QUALITATIVE_SEVERITY]
    assert "heavy" in qual_values
    assert "moderate" in qual_values
    assert all(isinstance(v, str) for v in qual_values)

    # Check numeric value unchanged
    numeric_obs = [obs for obs in assembler.observations
                   if obs.observation_type == ObservationType.RIVER_STAGE][0]
    assert numeric_obs.value == 1.5
    assert isinstance(numeric_obs.value, float)


def test_assembly_uses_phase4b_and_preserves_fields():
    """Test that the assembly uses the Phase 4B ingestor output and preserves fields."""
    # Create a small set of observations mimicking Phase 4B output for GSDL, DTP, CWC
    obs_list = []
    # GSDL observations (2 samples)
    obs_list.append(create_obs("gsdl1", datetime(2024, 6, 1, 12, 0),
                               lat=28.6, lon=77.2, obs_type=ObservationType.WATERLOGGING_OCCURRENCE,
                               value="occurred", source="GSDL", event_id="GSDL-EVENT-1"))
    obs_list.append(create_obs("gsdl2", datetime(2024, 6, 2, 15, 30),
                               lat=28.7, lon=77.3, obs_type=ObservationType.WATERLOGGING_OCCURRENCE,
                               value="occurred", source="GSDL", event_id="GSDL-EVENT-1"))
    # DTP observations (2 samples)
    obs_list.append(create_obs("dtp1", datetime(2024, 5, 15, 9, 0),
                               lat=None, lon=None, obs_type=ObservationType.RIVER_STAGE,
                               value=1.2, source="DTP", event_id="DTP-EVENT-1"))
    obs_list.append(create_obs("dtp2", datetime(2024, 5, 16, 10, 0),
                               lat=None, lon=None, obs_type=ObservationType.RIVER_STAGE,
                               value=1.3, source="DTP", event_id="DTP-EVENT-1"))
    # CWC observations (2 samples)
    obs_list.append(create_obs("cwc1", datetime(2024, 4, 10, 8, 0),
                               lat=28.5, lon=77.1, obs_type=ObservationType.RIVER_STAGE,
                               value=0.8, source="CWC", event_id="CWC-EVENT-1"))
    obs_list.append(create_obs("cwc2", datetime(2024, 4, 11, 9, 0),
                               lat=None, lon=None, obs_type=ObservationType.RIVER_STAGE,
                               value=0.9, source="CWC", event_id="CWC-EVENT-1"))

    assembler = EventQAAssembly(obs_list)
    report = assembler.get_qa_report()

    # Verify total count
    assert report["total"] == 6

    # Verify source counts are preserved (no invention)
    assert report["by_source"]["GSDL"] == 2
    assert report["by_source"]["DTP"] == 2
    assert report["by_source"]["CWC"] == 2

    # Verify observation type counts
    assert report["by_observation_type"][str(ObservationType.WATERLOGGING_OCCURRENCE)] == 2  # gsdl1, gsdl2
    assert report["by_observation_type"][str(ObservationType.RIVER_STAGE)] == 4  # dtp1, dtp2, cwc1, cwc2

    # Verify events are grouped by event_id
    assert "GSDL-EVENT-1" in report
    assert report["GSDL-EVENT-1"] == 2
    assert "DTP-EVENT-1" in report
    assert report["DTP-EVENT-1"] == 2
    assert "CWC-EVENT-1" in report
    assert report["CWC-EVENT-1"] == 2

    # Verify that coordinates are not invented for DTP and CWC where they are None
    # Check that the observations in the assembly retain their original coordinates
    for obs in assembler.observations:
        if obs.source == "DTP":
            assert obs.latitude is None
            assert obs.longitude is None
        if obs.source == "CWC" and obs.observation_id == "cwc2":
            assert obs.latitude is None
            assert obs.longitude is None
        # GSDL coordinates should be preserved exactly
        if obs.source == "GSDL":
            if obs.observation_id == "gsdl1":
                assert obs.latitude == 28.6
                assert obs.longitude == 77.2
            if obs.observation_id == "gsdl2":
                assert obs.latitude == 28.7
                assert obs.longitude == 77.3

    # Verify that no coordinates were invented (i.e., we don't have any observation with lat/lon that wasn't in the input)
    # We already checked the specific ones above; the assembly does not modify coordinates.

    # Verify that the assembly does not discard observations based on missing coordinates
    # All 6 observations should be present in the assembly
    assert len(assembler.observations) == 6