"""Machine-readable observation registry (audit of ALL historical evidence).

Every observation carries: observation_id, event_id, variable, value,
unit, timestamp, duration, coordinates (if any), source, source_tier,
provenance, spatial/temporal accuracy, quality, usability flags and the
reason when not usable.

Tier hierarchy (defensible quantitative-data criteria):
- TIER_A_DIRECT_MEASUREMENT  measured rainfall/stage/depth/discharge/extent
- TIER_B_HIGH_CONFIDENCE_DERIVED  documented derivation + uncertainty
- TIER_C_INDIRECT_CONTEXT    qualitative/occurrence/context evidence
- UNKNOWN                    provenance/quality insufficient

Usability is per-purpose: an observation may be usable for forcing QC
yet unusable for calibration of a Kushak parameter (e.g. downstream CWC
stage), and occurrence context is never promoted to a numeric target.
"""

from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Optional

_REPO_ROOT = Path(__file__).resolve().parents[5]
_DATA = _REPO_ROOT / "data" / "delhi" / "derived"
SCIENCE_DIR = _DATA / "science"

TIER_A = "TIER_A_DIRECT_MEASUREMENT"
TIER_B = "TIER_B_HIGH_CONFIDENCE_DERIVED"
TIER_C = "TIER_C_INDIRECT_CONTEXT"
TIER_UNKNOWN = "UNKNOWN"


@dataclass
class ObservationRecord:
    observation_id: str
    event_id: str  # catalogue id (EVT-*) or UNASSIGNED
    variable: str  # RAINFALL_DEPTH | RAINFALL_RATE | STAGE | FLOOD_OCCURRENCE | ROAD_CLOSURE | ...
    value: Optional[float]
    unit: str
    timestamp: Optional[str]  # ISO when documented; None stays None
    duration_hours: Optional[float]
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    source: str = ""
    source_tier: str = TIER_UNKNOWN
    provenance: str = ""
    spatial_accuracy: str = "UNKNOWN"
    temporal_accuracy: str = "UNKNOWN"
    quality: str = "UNKNOWN"
    usable_for_calibration: bool = False
    usable_for_validation: bool = False
    usable_for_forcing_qc: bool = False
    reason_if_not_usable: str = ""
    notes: str = ""


def _tier_for_rainfall_classification(classification: str) -> str:
    c = (classification or "").upper()
    if c in ("VERIFIED_ZERO", "OBSERVED_DIRECT", "OBSERVED"):
        return TIER_A
    if "DERIVED" in c:
        return TIER_B
    return TIER_UNKNOWN


def _load_csv(path: Path) -> List[dict]:
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def build_observation_registry() -> List[ObservationRecord]:
    """Build the registry from the existing evidence tree (no new claims)."""
    records: List[ObservationRecord] = []

    # --- 1. Event inventory: documented rainfall totals / peak intensities.
    inventory = _load_csv(_DATA / "rainfall" / "kushak_event_inventory.csv")
    for i, row in enumerate(inventory):
        event_id = row.get("event_id", f"INV-{i}")
        total_raw = (row.get("peak_rainfall_mm") or "").strip()
        if total_raw:
            try:
                value = float(total_raw.split()[0])
            except (ValueError, IndexError):
                value = None
            provenance = (row.get("scientific_provenance") or "").upper()
            tier = TIER_A if "OBSERVED" in provenance else (
                TIER_B if "DERIVED" in provenance else TIER_UNKNOWN
            )
            records.append(ObservationRecord(
                observation_id=f"RAINTOT-{event_id}",
                event_id=event_id,
                variable="RAINFALL_DEPTH_24H",
                value=value,
                unit="mm",
                timestamp=row.get("date_start"),
                duration_hours=float(row["duration_hours"]) if row.get("duration_hours") else None,
                source=row.get("data_source", ""),
                source_tier=tier,
                provenance=provenance or "UNKNOWN",
                temporal_accuracy="EVENT_TOTAL (intra-event timing per interval rows)",
                quality="DOCUMENTED",
                usable_for_calibration=False,
                usable_for_validation=True,
                usable_for_forcing_qc=True,
                reason_if_not_usable=(
                    "" if value is not None else "value not parseable from inventory"
                ),
            ))

    # --- 2. Forcing hyetographs: per-interval observed/derived rainfall.
    hyetographs = {
        "EVT-2024-06-27": _DATA / "rainfall" / "kushak_forcing_hyetograph_20240628_safdarjung.csv",
        "EVT-2023-07-08": _DATA / "rainfall" / "kushak_forcing_hyetograph_20230708_10_safdarjung.csv",
    }
    for event_id, path in hyetographs.items():
        for i, row in enumerate(_load_csv(path)):
            classification = row.get("observation_classification", "")
            tier = _tier_for_rainfall_classification(classification)
            value_raw = (row.get("rainfall_mm") or "").strip()
            value: Optional[float]
            if row.get("missing_flag", "").strip().lower() == "true" or value_raw == "":
                value = None
            else:
                try:
                    value = float(value_raw)
                except ValueError:
                    value = None
            records.append(ObservationRecord(
                observation_id=f"RAINT-{event_id}-{i:03d}",
                event_id=event_id,
                variable="RAINFALL_DEPTH_INTERVAL",
                value=value,
                unit="mm",
                timestamp=row.get("timestamp_ist") or None,
                duration_hours=1.0,
                source=row.get("source_station", ""),
                source_tier=tier,
                provenance=classification or "UNKNOWN",
                temporal_accuracy="HOURLY (documented interval)",
                spatial_accuracy="STATION_POINT (Safdarjung)",
                quality=row.get("quality_flag", "UNKNOWN"),
                usable_for_calibration=False,
                usable_for_validation=True,
                usable_for_forcing_qc=True,
                reason_if_not_usable=(
                    "" if tier in (TIER_A, TIER_B) and value is not None
                    else "interval UNKNOWN or provenance insufficient"
                ),
                notes=(row.get("derivation_basis") or "")[:200],
            ))

    # --- 3. GSDL waterlogging occurrences: OFFICIAL, occurrence context.
    gsdl = _load_csv(
        _DATA / "validation" / "gsdl_waterlogging" / "gsdl_waterlogging_normalized_occurrences.csv"
    )
    for i, row in enumerate(gsdl):
        lat = row.get("latitude") or None
        lon = row.get("longitude") or None
        records.append(ObservationRecord(
            observation_id=f"GSDL-{row.get('source_fid', i)}",
            event_id="UNASSIGNED",  # occurrence ledger; event attribution is separate
            variable="FLOOD_OCCURRENCE",
            value=None,  # categorical occurrence; never a numeric target
            unit="boolean",
            timestamp=row.get("observation_date") or None,
            duration_hours=None,
            latitude=float(lat) if lat else None,
            longitude=float(lon) if lon else None,
            source=str(row.get("agency", "GSDL")),
            source_tier=TIER_C,
            provenance=str(row.get("provenance", "OFFICIAL")),
            spatial_accuracy="ROAD/LOCATION LABEL (varying precision)",
            temporal_accuracy="DATE_ONLY",
            quality="OFFICIAL_LEDGER",
            usable_for_calibration=False,
            usable_for_validation=False,
            usable_for_forcing_qc=False,
            reason_if_not_usable=(
                "occurrence context only: categorical, date-only attribution; "
                "never a numeric hydraulic target and never FLOOD_NO evidence"
            ),
        ))

    # --- 4. DTP operational waterlogging: OFFICIAL advisories.
    dtp = _load_csv(
        _DATA / "validation" / "dtp_waterlogging" / "dtp_waterlogging_severity_normalized.csv"
    )
    for i, row in enumerate(dtp):
        depth_raw = (row.get("depth_raw") or "").strip()
        records.append(ObservationRecord(
            observation_id=f"DTP-{i:03d}",
            event_id="UNASSIGNED",
            variable="ROAD_CLOSURE_OCCURRENCE",
            value=None,
            unit="boolean",
            timestamp=row.get("date") or None,
            duration_hours=None,
            source="Delhi Traffic Police",
            source_tier=TIER_C,
            provenance=str(row.get("provenance", "OFFICIAL")),
            spatial_accuracy="LOCATION LABEL",
            temporal_accuracy="TIME_OF_DAY (date + advisory time)",
            quality="OFFICIAL_ADVISORY",
            usable_for_calibration=False,
            usable_for_validation=False,
            usable_for_forcing_qc=False,
            reason_if_not_usable=(
                "operational context: qualitative severity/closure text; "
                "no defensible depth value"
                + ("; depth field present but UNSTRUCTURED text" if depth_raw and depth_raw != "UNKNOWN" else "")
            ),
            notes=(row.get("notes") or "")[:200],
        ))

    # --- 5. CWC downstream stage: DIRECT measurement, but DOWNSTREAM context.
    cwc_dir = _DATA / "validation" / "cwc_downstream"
    for path in sorted(cwc_dir.glob("*.csv")):
        for i, row in enumerate(_load_csv(path)):
            level_raw = (row.get("water_level_m") or "").strip()
            value: Optional[float] = None
            if level_raw and level_raw.upper() != "UNKNOWN":
                try:
                    value = float(level_raw)
                except ValueError:
                    value = None
            records.append(ObservationRecord(
                observation_id=f"CWC-{path.stem}-{i:03d}",
                event_id="UNASSIGNED",
                variable="STAGE_DOWNSTREAM_YAMUNA",
                value=value,
                unit="m",
                timestamp=(row.get("date") or "") + (
                    " " + row["time"] if row.get("time") else ""
                ) or None,
                duration_hours=None,
                source=f"{row.get('station_name', 'CWC')} ({row.get('station_id', '')})",
                source_tier=TIER_A,
                provenance=str(row.get("provenance", "OFFICIAL")),
                spatial_accuracy="GAUGE_POINT (Delhi Railway Bridge, Yamuna)",
                temporal_accuracy="DAILY_BULLETIN",
                quality="OFFICIAL_HYDROMETRIC",
                usable_for_calibration=False,
                usable_for_validation=False,
                usable_for_forcing_qc=False,
                reason_if_not_usable=(
                    "downstream Yamuna/Barapullah boundary CONTEXT: not a "
                    "Kushak-reach observation; never attached to event-day "
                    "Kushak forcing per the CWC separation audit"
                ),
            ))

    return records


def registry_summary(records: List[ObservationRecord]) -> dict:
    """Counts by variable x tier x usability — the gate inputs."""
    summary: dict = {}
    for r in records:
        key = r.variable
        entry = summary.setdefault(key, {
            "count": 0,
            "tiers": {},
            "usable_for_calibration": 0,
            "usable_for_validation": 0,
            "usable_for_forcing_qc": 0,
        })
        entry["count"] += 1
        entry["tiers"][r.source_tier] = entry["tiers"].get(r.source_tier, 0) + 1
        entry["usable_for_calibration"] += int(r.usable_for_calibration)
        entry["usable_for_validation"] += int(r.usable_for_validation)
        entry["usable_for_forcing_qc"] += int(r.usable_for_forcing_qc)
    return summary


def write_registry(
    records: List[ObservationRecord],
    out_dir: Path = SCIENCE_DIR,
) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True, mode=0o755)
    payload = {
        "registry_schema": "kushak-observation-registry/1.0",
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "record_count": len(records),
        "summary": registry_summary(records),
        "records": [asdict(r) for r in records],
    }
    path = out_dir / "observation_registry.json"
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    csv_path = out_dir / "observation_registry.csv"
    with open(csv_path, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(asdict(records[0]).keys()))
        writer.writeheader()
        for r in records:
            writer.writerow(asdict(r))
    return path
