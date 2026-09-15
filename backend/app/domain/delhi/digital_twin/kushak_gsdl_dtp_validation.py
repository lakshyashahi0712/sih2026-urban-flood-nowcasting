"""Phase 11 Step 5: GSDL / DTP Empirical Validation Module.

DESCRIPTIVE EMPIRICAL VALIDATION ONLY.
Connects the existing deterministic rainfall/runoff ensemble and Kushak hydraulic
model outputs to already-acquired empirical flood evidence:
1. GSDL waterlogging observations (Layer 0 and Layer 1).
2. Delhi Traffic Police (DTP) waterlogging records.

Strict Scientific Scope:
- Answers: "Is the model output temporally/spatially consistent with documented waterlogging evidence?"
- Does NOT claim prediction accuracy, calibration accuracy, street-level depth accuracy,
  discharge accuracy, probability of flooding, statistical confidence, ML performance, or forecast skill.
- GSDL points carry occurrence evidence only; they do NOT provide hydraulic depth or discharge.
- DTP records provide temporal/event occurrence evidence; coordinates are absent in normalized DTP
  evidence, so spatial match is strictly UNKNOWN (never geocoded or invented).
- Reuses Phase 8B validation vocabulary: CONSISTENT, INCONSISTENT, UNKNOWN, NOT_COMPARABLE.
- Strict event separation: EV-01 (June 28, 2024) and EV-02 (July 8-10, 2023) are never pooled or cross-substituted.
- Zero calibration: Manning n, runoff coefficients, catchment areas, and hydraulic multipliers are NEVER tuned against GSDL/DTP evidence.
- Zero accuracy metrics (RMSE, MAE, F1, accuracy, etc.).
"""

from __future__ import annotations

import csv
import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

from .models import ProvenanceStatus
from .kushak_event_validation import (
    ValidationOutcome,
    SpatialMatch,
    TemporalMatch,
    ValidationSourceClass,
    TimestampPrecision,
    ValidationRecord,
    validate_observation,
    VALIDATION_EVENTS,
)
from .kushak_hydraulic_state_classification import ReachHydraulicClassification

# Paths to existing normalized empirical evidence
_GSDL_CSV = (
    Path(__file__).resolve().parents[5]
    / "data" / "delhi" / "derived" / "validation" / "gsdl_waterlogging"
    / "gsdl_waterlogging_normalized_occurrences.csv"
)
_DTP_CSV = (
    Path(__file__).resolve().parents[5]
    / "data" / "delhi" / "derived" / "validation" / "dtp_waterlogging"
    / "dtp_waterlogging_severity_normalized.csv"
)

# Known Kushak corridor bounding box or reference points (approximate envelope for corridor linkage)
# Corridor reaches span approximately 5027m along Kushak Nallah from South Ext / Aurobindo Marg outfall to Barapullah.
# Latitude range ~28.53 to ~28.63, Longitude range ~77.19 to ~77.26 (approximate corridor boundary).
KUSHAK_CORRIDOR_LAT_RANGE = (28.52, 28.64)
KUSHAK_CORRIDOR_LON_RANGE = (77.17, 77.27)


@dataclass(frozen=True)
class GsdloObservation:
    """Loaded GSDL waterlogging occurrence observation."""
    source_layer: str
    source_layer_id: str
    source_fid: str
    observation_date: str
    road_name: str
    location_raw: str
    latitude: Optional[float]
    longitude: Optional[float]
    agency: str
    year: int
    provenance: str
    observation_type: str


@dataclass(frozen=True)
class DtpObservation:
    """Loaded DTP waterlogging incident record."""
    source_url: str
    source_document: str
    date: str
    time: str
    road_name: str
    location: str
    severity_raw: str
    depth_raw: str
    closure_raw: str
    duration_raw: str
    evidence_type: str
    provenance: str
    notes: str


def load_gsdl_observations(csv_path: Path = _GSDL_CSV) -> List[GsdloObservation]:
    """Load normalized GSDL observations from CSV."""
    if not csv_path.exists():
        return []
    obs = []
    with open(csv_path, encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            lat_raw = row.get("latitude")
            lon_raw = row.get("longitude")
            lat = float(lat_raw) if lat_raw and lat_raw.strip() and lat_raw.strip().upper() != "UNKNOWN" else None
            lon = float(lon_raw) if lon_raw and lon_raw.strip() and lon_raw.strip().upper() != "UNKNOWN" else None
            obs.append(
                GsdloObservation(
                    source_layer=row.get("source_layer", ""),
                    source_layer_id=row.get("source_layer_id", ""),
                    source_fid=row.get("source_fid", ""),
                    observation_date=row.get("observation_date", ""),
                    road_name=row.get("road_name", ""),
                    location_raw=row.get("location_raw", ""),
                    latitude=lat,
                    longitude=lon,
                    agency=row.get("agency", "UNKNOWN"),
                    year=int(row.get("year", 2024)),
                    provenance=row.get("provenance", "OFFICIAL / OBSERVED"),
                    observation_type=row.get("observation_type", "WATERLOGGING_OCCURRENCE"),
                )
            )
    return obs


def load_dtp_observations(csv_path: Path = _DTP_CSV) -> List[DtpObservation]:
    """Load normalized DTP observations from CSV."""
    if not csv_path.exists():
        return []
    obs = []
    with open(csv_path, encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            obs.append(
                DtpObservation(
                    source_url=row.get("source_url", ""),
                    source_document=row.get("source_document", ""),
                    date=row.get("date", ""),
                    time=row.get("time", "UNKNOWN"),
                    road_name=row.get("road_name", ""),
                    location=row.get("location", ""),
                    severity_raw=row.get("severity_raw", "UNKNOWN"),
                    depth_raw=row.get("depth_raw", "UNKNOWN"),
                    closure_raw=row.get("closure_raw", "UNKNOWN"),
                    duration_raw=row.get("duration_raw", "UNKNOWN"),
                    evidence_type=row.get("evidence_type", ""),
                    provenance=row.get("provenance", "OFFICIAL"),
                    notes=row.get("notes", ""),
                )
            )
    return obs


def map_date_to_event_id(date_str: str) -> Optional[str]:
    """Map observation date string to explicit validation event ID (EV-01 or EV-02).

    EV-01 = June 28, 2024 (2024-06-28)
    EV-02 = July 8-10, 2023 (2023-07-08 to 2023-07-10)
    Returns None if date does not match either benchmark event window.
    """
    if not date_str:
        return None
    d = date_str.strip()
    if d.startswith("2024-06-28"):
        return "EV-01"
    elif d.startswith("2023-07-08") or d.startswith("2023-07-09") or d.startswith("2023-07-10"):
        return "EV-02"
    return None


def is_in_kushak_corridor(lat: Optional[float], lon: Optional[float]) -> bool:
    """Check if lat/lon falls within approximate Kushak corridor bounding box."""
    if lat is None or lon is None:
        return False
    return (
        KUSHAK_CORRIDOR_LAT_RANGE[0] <= lat <= KUSHAK_CORRIDOR_LAT_RANGE[1]
        and KUSHAK_CORRIDOR_LON_RANGE[0] <= lon <= KUSHAK_CORRIDOR_LON_RANGE[1]
    )


@dataclass(frozen=True)
class EmpiricalValidationRunResult:
    """Result container for GSDL/DTP empirical validation run."""
    event_id: str
    total_records_evaluated: int
    consistent_count: int
    inconsistent_count: int
    unknown_count: int
    not_comparable_count: int
    records: Tuple[ValidationRecord, ...]
    diagnostic: str


def validate_gsdl_observation_item(
    obs: GsdloObservation,
    model_state: Optional[ReachHydraulicClassification] = None,
    reach_reference_points: Optional[Dict[str, Tuple[float, float]]] = None,
    max_match_distance_m: Optional[float] = None,
    model_timestep: Optional[Tuple[datetime, datetime]] = None,
) -> ValidationRecord:
    """Validate a single GSDL observation item against model state using Phase 8B rules."""
    event_id = map_date_to_event_id(obs.observation_date)

    # Check if point is within corridor
    in_corridor = is_in_kushak_corridor(obs.latitude, obs.longitude)

    # Parse date for timestamp
    ts = None
    try:
        ts = datetime.fromisoformat(obs.observation_date.replace("Z", "+00:00"))
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
    except Exception:
        pass

    timestamp_precision = TimestampPrecision.DATETIME if ts is not None else TimestampPrecision.DATE_ONLY

    # If event_id is None, it won't match valid event IDs -> UNASSIGNED
    res = validate_observation(
        event_id=event_id,
        source_class=ValidationSourceClass.GSDL_WATERLOGGING_OCCURRENCE,
        source_provenance=ProvenanceStatus.OBSERVED,
        timestamp=ts,
        timestamp_precision=timestamp_precision,
        latitude=obs.latitude,
        longitude=obs.longitude,
        reach_reference_points=reach_reference_points,
        max_match_distance_m=max_match_distance_m,
        model_state=model_state,
        model_timestep=model_timestep,
    )
    return res


def validate_dtp_observation_item(
    obs: DtpObservation,
    model_state: Optional[ReachHydraulicClassification] = None,
    model_timestep: Optional[Tuple[datetime, datetime]] = None,
) -> ValidationRecord:
    """Validate a single DTP observation item against model state.

    DTP records have no coordinates -> spatial match is UNKNOWN (never geocoded).
    """
    event_id = map_date_to_event_id(obs.date)
    # DTP evidence with UNKNOWN time: strictly preserve UNKNOWN; no timestamp, DATE_ONLY
    if obs.time and obs.time.strip().upper() == "UNKNOWN":
        ts = None
        timestamp_precision = TimestampPrecision.DATE_ONLY
    else:
        ts = None
        if obs.time and obs.time.strip():
            try:
                dt_str = f"{obs.date.strip()}T{obs.time.strip()[:5]}"
                ts = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=timezone.utc)
            except Exception:
                ts = None
        if ts is None and obs.date and obs.date.strip():
            try:
                ts = datetime.fromisoformat(obs.date.strip().replace("Z", "+00:00"))
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=timezone.utc)
            except Exception:
                ts = None
        timestamp_precision = TimestampPrecision.DATETIME if (ts is not None and obs.time and obs.time.strip().upper() != "UNKNOWN") else TimestampPrecision.DATE_ONLY

    res = validate_observation(
        event_id=event_id,
        source_class=ValidationSourceClass.DTP_OPERATIONAL_OBSERVATION,
        source_provenance=ProvenanceStatus.OBSERVED,
        timestamp=ts,
        timestamp_precision=timestamp_precision,
        latitude=None,  # DTP normalized evidence lacks coordinates
        longitude=None,
        model_state=model_state,
        model_timestep=model_timestep,
    )
    return res
