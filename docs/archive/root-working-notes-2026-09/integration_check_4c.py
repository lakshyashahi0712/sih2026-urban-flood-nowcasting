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

    observations = []
    observations.extend(ingest_cwc_observations(cwc_path))
    observations.extend(ingest_dtp_observations(dtp_path))
    observations.extend(ingest_gsdl_observations(gsdl_path))

    assembler = EventQAAssembly(observations)
    report = assembler.get_qa_report()

    print(report)

if __name__ == "__main__":
    run_integration_check()
