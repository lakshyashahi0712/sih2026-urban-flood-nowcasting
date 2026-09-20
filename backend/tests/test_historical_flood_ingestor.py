import pytest
from backend.app.domain.delhi.digital_twin.ingestion.historical_flood_ingestor import (
    ingest_cwc_observations,
    ingest_gsdl_observations,
    ingest_dtp_observations,
)
from backend.app.domain.delhi.digital_twin.historical_flood import ObservationType

def test_ingest_cwc():
    # Minimal fixture
    # Using a small file in the test dir instead of full path
    with open("test_cwc.csv", "w") as f:
        f.write("source_document,station_id,date,water_level_m\n")
        f.write("doc1,1008,2023-07-10,204.63\n")

    obs = ingest_cwc_observations("test_cwc.csv")
    assert len(obs) == 1
    assert obs[0].observation_type == ObservationType.RIVER_STAGE
    assert obs[0].value == 204.63
    assert obs[0].provenance == "OFFICIAL"

def test_ingest_gsdl():
    with open("test_gsdl.csv", "w") as f:
        f.write("source_layer,source_fid,observation_date,latitude,longitude\n")
        f.write("layer1,1,2024-06-28,28.65,77.14\n")

    obs = ingest_gsdl_observations("test_gsdl.csv")
    assert len(obs) == 1
    assert obs[0].observation_type == ObservationType.WATERLOGGING_OCCURRENCE
    assert obs[0].value == "occurred"
    assert obs[0].latitude == 28.65

def test_ingest_dtp():
    with open("test_dtp.csv", "w") as f:
        f.write("source_document,date,location,severity_raw,closure_raw\n")
        f.write("doc1,2024-06-28,Moolchand,severe,Closed\n")

    obs = ingest_dtp_observations("test_dtp.csv")
    assert len(obs) == 1
    assert obs[0].observation_type == ObservationType.ROAD_CLOSURE
    assert "Closed" in obs[0].value
