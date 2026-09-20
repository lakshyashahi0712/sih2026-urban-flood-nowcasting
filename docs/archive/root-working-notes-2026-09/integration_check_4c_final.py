from datetime import datetime
from backend.app.domain.delhi.digital_twin.historical_flood_event_assembly import EventQAAssembly
from backend.app.domain.delhi.digital_twin.ingestion.historical_flood_ingestor import (
    ingest_cwc_observations,
    ingest_dtp_observations,
    ingest_gsdl_observations,
)

def run_integration_check():
    cwc_path = "data/delhi/derived/validation/cwc_downstream/cwc_old_railway_bridge_event.csv"
    dtp_path = "data/delhi/derived/validation/dtp_waterlogging/dtp_waterlogging_severity_normalized.csv"
    gsdl_path = "data/delhi/derived/validation/gsdl_waterlogging/gsdl_waterlogging_normalized_occurrences.csv"

    cwc = ingest_cwc_observations(cwc_path)
    dtp = ingest_dtp_observations(dtp_path)
    gsdl = ingest_gsdl_observations(gsdl_path)

    observations = []
    observations.extend(cwc)
    observations.extend(dtp)
    observations.extend(gsdl)

    print(f"CWC observations: {len(cwc)}")
    print(f"DTP observations: {len(dtp)}")
    print(f"GSDL observations: {len(gsdl)}")
    print(f"Total observations: {len(observations)}")

    assembler = EventQAAssembly(observations)
    report = assembler.get_qa_report()

    print("\n=== EVENT QA REPORT ===")
    print(f"Total: {report['total']}")
    print(f"EV-01 (2024-06-28): {report['EV-01']}")
    print(f"EV-02 (2023-07-08 to 2023-07-10): {report['EV-02']}")
    print(f"Unassigned: {report['unassigned']}")
    print(f"Duplicate observation IDs: {report['duplicate_observation_ids']}")
    print(f"Invalid timestamps: {report['invalid_timestamp']}")
    print(f"Invalid coordinates: {report['invalid_coordinates']}")
    print(f"Missing provenance: {report['missing_provenance']}")

    print("\n=== BY SOURCE ===")
    for source, count in sorted(report['by_source'].items()):
        print(f"{source}: {count}")

    print("\n=== BY OBSERVATION TYPE ===")
    for obs_type, count in sorted(report['by_observation_type'].items()):
        print(f"{obs_type}: {count}")

if __name__ == "__main__":
    run_integration_check()