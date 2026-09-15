from datetime import datetime
from typing import List, Optional, Dict
from collections import defaultdict
from backend.app.domain.delhi.digital_twin.historical_flood import (
    HistoricalFloodObservation,
    ObservationType,
)


class HistoricalFloodEvent:
    def __init__(self, event_id: Optional[str], start_time: datetime, end_time: datetime):
        self.event_id = event_id
        self.start_time = start_time
        self.end_time = end_time
        self.observation_ids: List[str] = []
        self.sources: List[str] = []

    def add_observation(self, obs: HistoricalFloodObservation):
        self.observation_ids.append(obs.observation_id)
        if obs.source not in self.sources:
            self.sources.append(obs.source)


class EventQAAssembly:
    def __init__(self, observations: List[HistoricalFloodObservation]):
        self.observations = observations
        self.events: Dict[Optional[str], HistoricalFloodEvent] = {}
        self._assemble()

    def _assemble(self):
        # Group observations by event_id
        grouped: Dict[Optional[str], List[HistoricalFloodObservation]] = defaultdict(list)
        for obs in self.observations:
            grouped[obs.event_id].append(obs)

        # Create an event for each event_id
        for event_id, obs_list in grouped.items():
            # Compute the time range for the event
            start_time = min(obs.timestamp for obs in obs_list)
            end_time = max(obs.timestamp for obs in obs_list)
            event = HistoricalFloodEvent(event_id, start_time, end_time)
            for obs in obs_list:
                event.add_observation(obs)
            self.events[event_id] = event

    def get_qa_report(self) -> dict:
        total = len(self.observations)

        # QA metrics
        # We'll build a dictionary for the events counts
        events_counts = {}
        for event_id, event in self.events.items():
            # Use the event_id as the key
            events_counts[event_id] = len(event.observation_ids)

        # Duplicates: count occurrences of duplicated IDs
        id_counts = {}
        duplicate_count = 0
        for obs in self.observations:
            oid = obs.observation_id
            id_counts[oid] = id_counts.get(oid, 0) + 1
        for count in id_counts.values():
            if count > 1:
                duplicate_count += count - 1

        # Invalid Coordinates:
        invalid_coord_count = 0
        for obs in self.observations:
            if obs.latitude is not None:
                if not (-90 <= obs.latitude <= 90):
                    invalid_coord_count += 1
            if obs.longitude is not None:
                if not (-180 <= obs.longitude <= 180):
                    invalid_coord_count += 1

        # Missing Provenance:
        from backend.app.domain.delhi.digital_twin.models import ProvenanceStatus
        missing_provenance_count = sum(1 for obs in self.observations if obs.provenance == ProvenanceStatus.UNKNOWN)

        # Invalid Timestamps:
        # Timestamp is guaranteed to be a valid datetime by the HistoricalFloodObservation model,
        # so invalid timestamps are structurally impossible.
        invalid_timestamp_count = sum(1 for obs in self.observations if obs.timestamp is None)

        # Source counts
        source_counts = {}
        for obs in self.observations:
            source_counts[obs.source] = source_counts.get(obs.source, 0) + 1

        # Type counts
        type_counts = {}
        for obs in self.observations:
            type_key = str(obs.observation_type)
            type_counts[type_key] = type_counts.get(type_key, 0) + 1

        # Build the report
        report = {
            "total": total,
            "duplicate_observation_ids": duplicate_count,
            "invalid_coordinates": invalid_coord_count,
            "missing_provenance": missing_provenance_count,
            "invalid_timestamp": invalid_timestamp_count,
            "by_source": source_counts,
            "by_observation_type": type_counts
        }
        # Add the events counts
        for event_id, count in events_counts.items():
            report[event_id] = count

        return report