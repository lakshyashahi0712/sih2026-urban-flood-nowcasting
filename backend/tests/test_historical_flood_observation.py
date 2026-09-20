import pytest
from datetime import datetime
from backend.app.domain.delhi.digital_twin.historical_flood import (
    HistoricalFloodObservation,
    ObservationType,
)
from backend.app.domain.delhi.digital_twin.models import ProvenanceStatus
from pydantic import ValidationError

def test_historical_flood_observation_valid():
    # Verify valid observation
    obs = HistoricalFloodObservation(
        observation_id="obs-1",
        event_id="evt-1",
        timestamp=datetime.now(),
        latitude=28.6139,
        longitude=77.2090,
        observation_type=ObservationType.RIVER_STAGE,
        value=1.5,
        unit="meters",
        source="sensor-1"
    )
    assert obs.observation_id == "obs-1"
    assert obs.provenance == ProvenanceStatus.UNKNOWN

def test_historical_flood_observation_invalid_coordinates():
    # Verify coordinate validation
    with pytest.raises(ValidationError):
        HistoricalFloodObservation(
            observation_id="obs-1",
            event_id="evt-1",
            timestamp=datetime.now(),
            latitude=95.0,
            longitude=77.0,
            observation_type=ObservationType.RIVER_STAGE,
            value=1.5,
            unit="meters",
            source="sensor-1"
        )

def test_historical_flood_observation_provenance_constraint():
    # Invalid: known provenance but no source
    with pytest.raises(ValidationError, match="Source required for known provenance"):
        HistoricalFloodObservation(
            observation_id="t5",
            event_id="e5",
            timestamp=datetime.now(),
            latitude=28.0,
            longitude=77.0,
            observation_type=ObservationType.RIVER_STAGE,
            value=1.0,
            unit="m",
            source="",
            provenance=ProvenanceStatus.OFFICIAL
        )

def test_historical_flood_observation_types():
    # Test all 5 types
    base = {
        "observation_id": "obs-1",
        "event_id": "evt-1",
        "timestamp": datetime.now(),
        "latitude": 28.6139,
        "longitude": 77.2090,
        "unit": "meters",
        "source": "sensor-1"
    }

    # RIVER_STAGE (numeric)
    HistoricalFloodObservation(**base, observation_type=ObservationType.RIVER_STAGE, value=1.5)
    with pytest.raises(ValidationError, match="must have a numeric value"):
        HistoricalFloodObservation(**base, observation_type=ObservationType.RIVER_STAGE, value="high")

    # QUALITATIVE_SEVERITY (string)
    HistoricalFloodObservation(**base, observation_type=ObservationType.QUALITATIVE_SEVERITY, value="high")
    with pytest.raises(ValidationError, match="must have a string value"):
        HistoricalFloodObservation(**base, observation_type=ObservationType.QUALITATIVE_SEVERITY, value=1.5)

    # WATERLOGGING_OCCURRENCE (string)
    HistoricalFloodObservation(**base, observation_type=ObservationType.WATERLOGGING_OCCURRENCE, value="occurred")
    with pytest.raises(ValidationError, match="must have a string value"):
        HistoricalFloodObservation(**base, observation_type=ObservationType.WATERLOGGING_OCCURRENCE, value=1.0)

    # ROAD_CLOSURE (string)
    HistoricalFloodObservation(**base, observation_type=ObservationType.ROAD_CLOSURE, value="yes")
    with pytest.raises(ValidationError, match="must have a string value"):
        HistoricalFloodObservation(**base, observation_type=ObservationType.ROAD_CLOSURE, value=1.0)

    # FLOOD_EXTENT
    HistoricalFloodObservation(**base, observation_type=ObservationType.FLOOD_EXTENT, value=100.5)
    HistoricalFloodObservation(**base, observation_type=ObservationType.FLOOD_EXTENT, value="large")

def test_missing_unknown_values_not_zero():
    # Ensure missing value is not accepted as 0
    with pytest.raises(ValidationError):
        HistoricalFloodObservation(
            observation_id="obs-1",
            event_id="evt-1",
            timestamp=datetime.now(),
            latitude=28.6139,
            longitude=77.2090,
            observation_type=ObservationType.RIVER_STAGE,
            value=None, # Should fail
            unit="meters",
            source="sensor-1"
        )

def test_provenance_preservation_and_unknown():
    # UNKNOWN provenance
    obs = HistoricalFloodObservation(
        observation_id="obs-1",
        event_id="evt-1",
        timestamp=datetime.now(),
        latitude=28.0,
        longitude=77.0,
        observation_type=ObservationType.RIVER_STAGE,
        value=1.5,
        unit="m",
        source="", # Allowed if provenance is UNKNOWN
        provenance=ProvenanceStatus.UNKNOWN
    )
    assert obs.provenance == ProvenanceStatus.UNKNOWN

    # KNOWN provenance requires source
    with pytest.raises(ValidationError, match="Source required for known provenance"):
        HistoricalFloodObservation(
            observation_id="obs-2",
            event_id="evt-2",
            timestamp=datetime.now(),
            latitude=28.0,
            longitude=77.0,
            observation_type=ObservationType.RIVER_STAGE,
            value=1.5,
            unit="m",
            source="",
            provenance=ProvenanceStatus.OFFICIAL
        )

def test_latitude_longitude_can_be_none():
    # latitude and longitude can be None
    obs = HistoricalFloodObservation(
        observation_id="obs-none",
        event_id="evt-none",
        timestamp=datetime.now(),
        latitude=None,
        longitude=None,
        observation_type=ObservationType.RIVER_STAGE,
        value=1.5,
        unit="meters",
        source="sensor-1"
    )
    assert obs.latitude is None
    assert obs.longitude is None

def test_valid_latitude_longitude_still_passes():
    # valid coordinates still work
    obs = HistoricalFloodObservation(
        observation_id="obs-valid",
        event_id="evt-valid",
        timestamp=datetime.now(),
        latitude=0.0,
        longitude=0.0,
        observation_type=ObservationType.RIVER_STAGE,
        value=1.5,
        unit="meters",
        source="sensor-1"
    )
    assert obs.latitude == 0.0
    assert obs.longitude == 0.0

def test_invalid_latitude_fails():
    with pytest.raises(ValidationError):
        HistoricalFloodObservation(
            observation_id="obs-invalid-lat",
            event_id="evt-invalid-lat",
            timestamp=datetime.now(),
            latitude=95.0,  # invalid
            longitude=0.0,
            observation_type=ObservationType.RIVER_STAGE,
            value=1.5,
            unit="meters",
            source="sensor-1"
        )

def test_invalid_longitude_fails():
    with pytest.raises(ValidationError):
        HistoricalFloodObservation(
            observation_id="obs-invalid-lon",
            event_id="evt-invalid-lon",
            timestamp=datetime.now(),
            latitude=0.0,
            longitude=200.0,  # invalid
            observation_type=ObservationType.RIVER_STAGE,
            value=1.5,
            unit="meters",
            source="sensor-1"
        )

def test_missing_coordinates_not_converted_to_zero():
    # Ensure None coordinates are not turned into 0.0
    obs = HistoricalFloodObservation(
        observation_id="obs-none-zero",
        event_id="evt-none-zero",
        timestamp=datetime.now(),
        latitude=None,
        longitude=None,
        observation_type=ObservationType.RIVER_STAGE,
        value=1.5,
        unit="meters",
        source="sensor-1"
    )
    assert obs.latitude is None
    assert obs.longitude is None
    # Explicitly check they are not zero
    assert obs.latitude != 0.0
    assert obs.longitude != 0.0
