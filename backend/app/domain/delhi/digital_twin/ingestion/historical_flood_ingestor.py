import csv
import re
from datetime import datetime
from typing import List, Optional
from backend.app.domain.delhi.digital_twin.historical_flood import (
    HistoricalFloodObservation,
    ObservationType,
)
from backend.app.domain.delhi.digital_twin.models import ProvenanceStatus


def ingest_cwc_observations(file_path: str) -> List[HistoricalFloodObservation]:
    observations = []
    with open(file_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['water_level_m'] == 'UNKNOWN':
                continue

            obs = HistoricalFloodObservation(
                observation_id=f"cwc-{row['station_id']}-{row['date']}",
                event_id=f"cwc-{row['date']}",
                timestamp=datetime.strptime(row['date'], '%Y-%m-%d'),
                latitude=None,
                longitude=None,
                observation_type=ObservationType.RIVER_STAGE,
                value=float(row['water_level_m']),
                unit="meters",
                source=row['source_document'],
                provenance=ProvenanceStatus.OFFICIAL
            )
            observations.append(obs)
    return observations


def _parse_gsdl_date(date_str: str, year: Optional[str] = None) -> datetime:
    # Try standard YYYY-MM-DD
    try:
        return datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        pass

    # Try DD.MM.YYYY
    try:
        return datetime.strptime(date_str, '%d.%m.%Y')
    except ValueError:
        pass

    # Try just Day with Year context
    if year and date_str.isdigit() and len(date_str) <= 2:
        return datetime(int(year), 1, int(date_str))

    # Handle specific non-standard formats
    # Examples:
    # "1 1.08.2024" -> "01.08.2024"
    # "26 07.2024"  -> "26.07.2024"
    # "1 05.2023"   -> "01.05.2023"

    # Normalize patterns like "D MM.YYYY" or "DD MM.YYYY"
    # Match 1-2 digits, a space, then 1-2 digits (month), dot, 4 digits (year)
    match_with_space = re.match(r'^(\d{1,2})\s+(\d{1,2})\.(\d{4})$', date_str)
    # Match DD.MMYYYY (missing dot)
    match_missing_dot = re.match(r'^(\d{1,2})\.(\d{1,2})(\d{4})$', date_str)

    if match_with_space:
        day, month, year = match_with_space.groups()
        normalized = f"{day.zfill(2)}.{month.zfill(2)}.{year}"
    elif match_missing_dot:
        day, month, year = match_missing_dot.groups()
        normalized = f"{day.zfill(2)}.{month.zfill(2)}.{year}"
    else:
        # Fallback to existing logic if it doesn't match the expected pattern
        # Remove leading "1 " if present
        normalized = re.sub(r'^1\s+', '', date_str)
        # Now, replace any remaining spaces with dots
        normalized = normalized.replace(" ", ".")

    # Split by dots
    parts = normalized.split('.')
    if len(parts) == 1 and parts[0].isdigit() and len(parts[0]) <= 2:
        # Just a day, can't infer without more context, but let's default to something safe
        # OR, better: fail gracefully and let caller handle
        raise ValueError(f"Incomplete date format: {date_str}")
    elif len(parts) == 2:
        # We have month and year, assume day is 01
        day = "01"
        month = parts[0]
        year = parts[1]
    elif len(parts) == 3:
        day = parts[0]
        month = parts[1]
        year = parts[2]
    else:
        raise ValueError(f"Unknown date format: {date_str} (normalized: {normalized})")

    # Ensure each part is zero-padded to 2 digits for day and month, year as is
    day = day.zfill(2)
    month = month.zfill(2)
    normalized = f"{day}.{month}.{year}"

    try:
        return datetime.strptime(normalized, '%d.%m.%Y')
    except ValueError:
        raise ValueError(f"Unknown date format: {date_str} (normalized: {normalized})")

def ingest_gsdl_observations(file_path: str) -> List[HistoricalFloodObservation]:
    observations = []
    with open(file_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            obs_date = row['observation_date']
            year = row.get('year')
            # Try to parse the observation_date directly with the year context
            try:
                timestamp = _parse_gsdl_date(obs_date, year=year)
            except ValueError:
                # If that fails, try to use date_raw to get a complete date
                date_raw = row.get('date_raw')
                if date_raw:
                    # Split date_raw by commas and try to parse each part
                    for part in date_raw.split(','):
                        part = part.strip()
                        # Try to parse the part as a date (with the help of year if needed)
                        try:
                            # First, try as is
                            timestamp = _parse_gsdl_date(part, year=year)
                            break
                        except ValueError:
                            # If that fails, try to see if the part is month.year and we have a day from obs_date
                            if obs_date.isdigit() and len(obs_date) <= 2:
                                # obs_date is a day
                                if '.' in part and part.count('.') == 1:
                                    # format month.year
                                    month_str, year_str = part.split('.')
                                    if month_str.isdigit() and year_str.isdigit() and len(year_str) == 4:
                                        # We have month and year, combine with day from obs_date
                                        try:
                                            timestamp = datetime(int(year_str), int(month_str), int(obs_date))
                                            break
                                        except ValueError:
                                            pass
                    else:
                        # If we didn't break, then we didn't find a date
                        raise ValueError(f"Unable to parse date from observation_date '{obs_date}' and date_raw '{date_raw}'")
                else:
                    # If no date_raw, re-raise the original error
                    raise
            obs = HistoricalFloodObservation(
                observation_id=f"gsdl-{row['source_fid']}-{obs_date}",
                event_id=f"gsdl-{obs_date}",
                timestamp=timestamp,
                latitude=float(row['latitude']),
                longitude=float(row['longitude']),
                observation_type=ObservationType.WATERLOGGING_OCCURRENCE,
                value="occurred",
                unit="boolean",
                source=row['source_layer'],
                provenance=ProvenanceStatus.OBSERVED
            )
            observations.append(obs)
    return observations


def ingest_dtp_observations(file_path: str) -> List[HistoricalFloodObservation]:
    observations = []
    with open(file_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Simple mapping for DTP
            if "closed" in row['closure_raw'].lower():
                obs_type = ObservationType.ROAD_CLOSURE
                val = row['closure_raw']
            else:
                obs_type = ObservationType.QUALITATIVE_SEVERITY
                val = row['severity_raw']

            obs = HistoricalFloodObservation(
                observation_id=f"dtp-{row['date']}-{row['location']}",
                event_id=f"dtp-{row['date']}",
                timestamp=datetime.strptime(row['date'], '%Y-%m-%d'),
                latitude=None,
                longitude=None,
                observation_type=obs_type,
                value=val,
                unit="qualitative",
                source=row['source_document'],
                provenance=ProvenanceStatus.OFFICIAL
            )
            observations.append(obs)
    return observations