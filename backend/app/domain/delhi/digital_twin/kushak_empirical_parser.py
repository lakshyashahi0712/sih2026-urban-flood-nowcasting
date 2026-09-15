"""Phase 10 Step 2: Read-Only Empirical Evidence Parser and Structural Validator.

Provides read-only inspection, format recognition, structural validation, and
conservative candidate field detection for future empirical evidence packages
(CSV, JSON, XML, TXT, ZIP containers).

Strict rules:
- Files absent -> NOT_AVAILABLE / NOT_ACQUIRED (never simulated/zero-filled).
- Field presence (e.g. column 'invert', 'chainage') != verified hydraulic truth.
- Procurement package (NIT-52) remains PROCUREMENT_SPECIFICATION (never upgraded
  to OFFICIAL_SURVEY_OBSERVED or OFFICIAL_AS_BUILT).
- Zero synthetic geometry, zero synthetic observations, zero Tier-A promotion.
- No hydraulic model coupling or core model modifications.
"""

from __future__ import annotations

import csv
import hashlib
import json
import xml.etree.ElementTree as ET
import zipfile
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .kushak_empirical_evidence import (
    EvidencePackage,
    EvidenceType,
    AcquisitionStatus,
    ProvenanceEvidenceClass,
    CoverageStatus,
    load_evidence_manifest,
)


class ParseStatus(str, Enum):
    """Explicit parse status result categories."""

    NOT_AVAILABLE = "NOT_AVAILABLE"
    SUCCESS = "SUCCESS"
    MALFORMED = "MALFORMED"
    EMPTY = "EMPTY"
    ERROR = "ERROR"


@dataclass(frozen=True)
class EvidenceParseResult:
    """Immutable structured parse and structural validation result."""

    parse_status: ParseStatus
    evidence_id: str
    detected_format: str = "UNKNOWN"
    file_size_bytes: int = 0
    sha256_checksum: Optional[str] = None
    readable: bool = False
    structural_validity: bool = False
    record_count: Optional[int] = None
    column_names: Tuple[str, ...] = field(default_factory=tuple)
    sheet_names: Tuple[str, ...] = field(default_factory=tuple)
    top_level_structure: Optional[str] = None
    candidate_measurement_fields: Tuple[str, ...] = field(default_factory=tuple)
    candidate_coordinate_fields: Tuple[str, ...] = field(default_factory=tuple)
    candidate_chainage_fields: Tuple[str, ...] = field(default_factory=tuple)
    candidate_elevation_fields: Tuple[str, ...] = field(default_factory=tuple)
    candidate_timestamp_fields: Tuple[str, ...] = field(default_factory=tuple)
    declared_crs: Optional[str] = None
    declared_vertical_datum: Optional[str] = None
    explicit_survey_metadata: Dict[str, Any] = field(default_factory=dict)
    coverage_metadata: Dict[str, Any] = field(default_factory=dict)
    warnings: Tuple[str, ...] = field(default_factory=tuple)
    errors: Tuple[str, ...] = field(default_factory=tuple)
    provenance_inherited: ProvenanceEvidenceClass = ProvenanceEvidenceClass.UNKNOWN
    tier_a_evaluation_potential: bool = False
    is_procurement_material: bool = False
    diagnostic: str = ""

    def summary_string(self) -> str:
        """Deterministic summary string for audit logging."""
        lines = [
            f"PARSE_RESULT: {self.evidence_id}",
            f"  status: {self.parse_status.value}",
            f"  format: {self.detected_format}",
            f"  readable: {self.readable}",
            f"  valid: {self.structural_validity}",
            f"  records: {self.record_count}",
            f"  checksum: {self.sha256_checksum or 'NONE'}",
            f"  provenance: {self.provenance_inherited.value}",
            f"  procurement: {self.is_procurement_material}",
            f"  tier_a_potential: {self.tier_a_evaluation_potential}",
            f"  diagnostic: {self.diagnostic!r}",
        ]
        return "\n".join(lines)


# Conservative candidate field detection dictionaries
CHAINAGE_KEYWORDS = {"chainage", "chainage_m", "station", "rd", "distance", "ch"}
ELEVATION_KEYWORDS = {"invert", "invert_elevation", "bed_level", "rl", "elevation", "level", "z"}
COORDINATE_KEYWORDS = {"latitude", "longitude", "easting", "northing", "x", "y", "lat", "lon"}
TIMESTAMP_KEYWORDS = {"timestamp", "datetime", "date_time", "date", "time", "t"}
MEASUREMENT_KEYWORDS = {"stage", "water_level", "discharge", "flow", "velocity", "silt", "depth"}


def _compute_sha256(path: Path) -> Optional[str]:
    """Safely compute SHA-256 for a real file."""
    if not path.exists() or not path.is_file():
        return None
    try:
        h = hashlib.sha256()
        with open(path, "rb") as fh:
            for chunk in iter(lambda: fh.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return None


def parse_evidence_file(
    evidence_id: str,
    file_path: Optional[Path] = None,
) -> EvidenceParseResult:
    """Read-only structural parser for an empirical evidence package.

    If file_path is None or does not exist, returns NOT_AVAILABLE / NOT_ACQUIRED
    without fabricating any substitute data, coordinates, or geometry.
    """
    # 1. Lookup package manifest if available
    pkg = load_evidence_manifest(evidence_id)
    provenance = pkg.provenance_status if pkg else ProvenanceEvidenceClass.UNKNOWN
    is_procurement = (
        provenance == ProvenanceEvidenceClass.PROCUREMENT_SPECIFICATION
        or "nit" in evidence_id.lower()
        or "procurement" in evidence_id.lower()
    )

    if file_path is None or not file_path.exists():
        # Fallback to pkg.file_path if present
        if pkg and pkg.file_path and pkg.file_path.exists():
            file_path = pkg.file_path
        else:
            return EvidenceParseResult(
                parse_status=ParseStatus.NOT_AVAILABLE,
                evidence_id=evidence_id,
                provenance_inherited=provenance,
                is_procurement_material=is_procurement,
                diagnostic=(
                    f"Evidence file for {evidence_id} is not present or path is None. "
                    "Status: NOT_AVAILABLE / NOT_ACQUIRED. No data fabricated."
                ),
            )

    # 2. Inspect file basic properties
    try:
        size_bytes = file_path.stat().st_size
    except Exception as e:
        return EvidenceParseResult(
            parse_status=ParseStatus.ERROR,
            evidence_id=evidence_id,
            readable=False,
            provenance_inherited=provenance,
            is_procurement_material=is_procurement,
            errors=(str(e),),
            diagnostic=f"Failed to stat file {file_path}: {e}",
        )

    if size_bytes == 0:
        return EvidenceParseResult(
            parse_status=ParseStatus.EMPTY,
            evidence_id=evidence_id,
            file_size_bytes=0,
            sha256_checksum=_compute_sha256(file_path),
            readable=True,
            structural_validity=False,
            provenance_inherited=provenance,
            is_procurement_material=is_procurement,
            diagnostic=f"Evidence file {file_path.name} is empty (0 bytes).",
        )

    checksum = _compute_sha256(file_path)
    suffix = file_path.suffix.lower()

    # 3. Format-specific parsing & validation
    if suffix == ".csv" or suffix == ".txt":
        return _parse_csv_file(evidence_id, file_path, size_bytes, checksum, provenance, is_procurement)
    elif suffix == ".json":
        return _parse_json_file(evidence_id, file_path, size_bytes, checksum, provenance, is_procurement)
    elif suffix == ".xml":
        return _parse_xml_file(evidence_id, file_path, size_bytes, checksum, provenance, is_procurement)
    elif suffix == ".zip":
        return _parse_zip_file(evidence_id, file_path, size_bytes, checksum, provenance, is_procurement)
    else:
        # Generic binary or unsupported text inspect
        return _parse_generic_file(evidence_id, file_path, size_bytes, checksum, provenance, is_procurement, suffix)


def _detect_fields(headers: List[str]) -> Tuple[Tuple[str, ...], Tuple[str, ...], Tuple[str, ...], Tuple[str, ...], Tuple[str, ...]]:
    """Conservative candidate field detection from headers."""
    chainage, elevation, coords, timestamp, measurements = [], [], [], [], []
    for h in headers:
        clean_h = h.strip().lower()
        if any(k in clean_h for k in CHAINAGE_KEYWORDS):
            chainage.append(h)
        if any(k in clean_h for k in ELEVATION_KEYWORDS):
            elevation.append(h)
        if any(k in clean_h for k in COORDINATE_KEYWORDS):
            coords.append(h)
        if any(k in clean_h for k in TIMESTAMP_KEYWORDS):
            timestamp.append(h)
        if any(k in clean_h for k in MEASUREMENT_KEYWORDS):
            measurements.append(h)
    return (
        tuple(measurements),
        tuple(coords),
        tuple(chainage),
        tuple(elevation),
        tuple(timestamp),
    )


def _parse_csv_file(
    evidence_id: str,
    file_path: Path,
    size_bytes: int,
    checksum: Optional[str],
    provenance: ProvenanceEvidenceClass,
    is_procurement: bool,
) -> EvidenceParseResult:
    """Parse and structurally validate a CSV file."""
    warnings_list: List[str] = []
    errors_list: List[str] = []
    headers: List[str] = []
    record_count = 0

    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as fh:
            sample = fh.read(2048)
            fh.seek(0)
            try:
                dialect = csv.Sniffer().sniff(sample)
            except Exception:
                dialect = csv.excel  # type: ignore

            reader = csv.reader(fh, dialect=dialect)
            try:
                header_row = next(reader, None)
            except Exception as e:
                return EvidenceParseResult(
                    parse_status=ParseStatus.MALFORMED,
                    evidence_id=evidence_id,
                    detected_format="CSV",
                    file_size_bytes=size_bytes,
                    sha256_checksum=checksum,
                    readable=True,
                    structural_validity=False,
                    provenance_inherited=provenance,
                    is_procurement_material=is_procurement,
                    errors=(str(e),),
                    diagnostic=f"Malformed CSV header: {e}",
                )

            if header_row:
                headers = [str(c).strip() for c in header_row]

            # Count rows & check row length consistency
            first_row_len = len(headers)
            for r_idx, row in enumerate(reader, start=1):
                record_count += 1
                if len(row) != first_row_len and first_row_len > 0:
                    warnings_list.append(f"Row {r_idx} column count ({len(row)}) differs from header ({first_row_len}).")

    except Exception as e:
        return EvidenceParseResult(
            parse_status=ParseStatus.MALFORMED,
            evidence_id=evidence_id,
            detected_format="CSV",
            file_size_bytes=size_bytes,
            sha256_checksum=checksum,
            readable=True,
            structural_validity=False,
            provenance_inherited=provenance,
            is_procurement_material=is_procurement,
            errors=(str(e),),
            diagnostic=f"Error reading CSV file: {e}",
        )

    measurements, coords, chainage, elevation, timestamp = _detect_fields(headers)
    valid = len(errors_list) == 0 and record_count >= 0

    return EvidenceParseResult(
        parse_status=ParseStatus.SUCCESS if valid else ParseStatus.MALFORMED,
        evidence_id=evidence_id,
        detected_format="CSV",
        file_size_bytes=size_bytes,
        sha256_checksum=checksum,
        readable=True,
        structural_validity=valid,
        record_count=record_count,
        column_names=tuple(headers),
        candidate_measurement_fields=measurements,
        candidate_coordinate_fields=coords,
        candidate_chainage_fields=chainage,
        candidate_elevation_fields=elevation,
        candidate_timestamp_fields=timestamp,
        warnings=tuple(warnings_list),
        errors=tuple(errors_list),
        provenance_inherited=provenance,
        tier_a_evaluation_potential=not is_procurement and valid,
        is_procurement_material=is_procurement,
        diagnostic=f"Successfully parsed CSV with {record_count} records and {len(headers)} columns.",
    )


def _parse_json_file(
    evidence_id: str,
    file_path: Path,
    size_bytes: int,
    checksum: Optional[str],
    provenance: ProvenanceEvidenceClass,
    is_procurement: bool,
) -> EvidenceParseResult:
    """Parse and validate a JSON file."""
    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as fh:
            data = json.load(fh)
    except Exception as e:
        return EvidenceParseResult(
            parse_status=ParseStatus.MALFORMED,
            evidence_id=evidence_id,
            detected_format="JSON",
            file_size_bytes=size_bytes,
            sha256_checksum=checksum,
            readable=True,
            structural_validity=False,
            provenance_inherited=provenance,
            is_procurement_material=is_procurement,
            errors=(str(e),),
            diagnostic=f"Malformed JSON: {e}",
        )

    top_struct = type(data).__name__
    record_count = None
    keys: List[str] = []

    if isinstance(data, list):
        record_count = len(data)
        if record_count > 0 and isinstance(data[0], dict):
            keys = list(data[0].keys())
    elif isinstance(data, dict):
        keys = list(data.keys())
        # Check if there's a list inside
        for k, v in data.items():
            if isinstance(v, list):
                record_count = len(v)
                if record_count > 0 and isinstance(v[0], dict):
                    keys = list(v[0].keys())
                break

    measurements, coords, chainage, elevation, timestamp = _detect_fields(keys)

    return EvidenceParseResult(
        parse_status=ParseStatus.SUCCESS,
        evidence_id=evidence_id,
        detected_format="JSON",
        file_size_bytes=size_bytes,
        sha256_checksum=checksum,
        readable=True,
        structural_validity=True,
        record_count=record_count,
        column_names=tuple(keys),
        top_level_structure=top_struct,
        candidate_measurement_fields=measurements,
        candidate_coordinate_fields=coords,
        candidate_chainage_fields=chainage,
        candidate_elevation_fields=elevation,
        candidate_timestamp_fields=timestamp,
        provenance_inherited=provenance,
        tier_a_evaluation_potential=not is_procurement,
        is_procurement_material=is_procurement,
        diagnostic=f"Successfully parsed JSON structure ({top_struct}).",
    )


def _parse_xml_file(
    evidence_id: str,
    file_path: Path,
    size_bytes: int,
    checksum: Optional[str],
    provenance: ProvenanceEvidenceClass,
    is_procurement: bool,
) -> EvidenceParseResult:
    """Parse and validate an XML file."""
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
    except Exception as e:
        return EvidenceParseResult(
            parse_status=ParseStatus.MALFORMED,
            evidence_id=evidence_id,
            detected_format="XML",
            file_size_bytes=size_bytes,
            sha256_checksum=checksum,
            readable=True,
            structural_validity=False,
            provenance_inherited=provenance,
            is_procurement_material=is_procurement,
            errors=(str(e),),
            diagnostic=f"Malformed XML: {e}",
        )

    root_tag = root.tag
    children_tags = [c.tag for c in root]

    return EvidenceParseResult(
        parse_status=ParseStatus.SUCCESS,
        evidence_id=evidence_id,
        detected_format="XML",
        file_size_bytes=size_bytes,
        sha256_checksum=checksum,
        readable=True,
        structural_validity=True,
        record_count=len(children_tags) if children_tags else 1,
        column_names=tuple(set(children_tags)),
        top_level_structure=f"XML root: {root_tag}",
        provenance_inherited=provenance,
        tier_a_evaluation_potential=not is_procurement,
        is_procurement_material=is_procurement,
        diagnostic=f"Successfully parsed XML with root tag '{root_tag}'.",
    )


def _parse_zip_file(
    evidence_id: str,
    file_path: Path,
    size_bytes: int,
    checksum: Optional[str],
    provenance: ProvenanceEvidenceClass,
    is_procurement: bool,
) -> EvidenceParseResult:
    """Inspect a ZIP container / package."""
    file_list: List[str] = []
    try:
        with zipfile.ZipFile(file_path, "r") as zf:
            file_list = zf.namelist()
    except Exception as e:
        return EvidenceParseResult(
            parse_status=ParseStatus.MALFORMED,
            evidence_id=evidence_id,
            detected_format="ZIP",
            file_size_bytes=size_bytes,
            sha256_checksum=checksum,
            readable=True,
            structural_validity=False,
            provenance_inherited=provenance,
            is_procurement_material=is_procurement,
            errors=(str(e),),
            diagnostic=f"Malformed or unreadable ZIP archive: {e}",
        )

    valid = len(file_list) > 0
    return EvidenceParseResult(
        parse_status=ParseStatus.SUCCESS if valid else ParseStatus.EMPTY,
        evidence_id=evidence_id,
        detected_format="ZIP",
        file_size_bytes=size_bytes,
        sha256_checksum=checksum,
        readable=True,
        structural_validity=valid,
        record_count=len(file_list),
        column_names=tuple(file_list),
        top_level_structure="ZIP Archive Container",
        provenance_inherited=provenance,
        tier_a_evaluation_potential=False,  # archive container, not direct survey table
        is_procurement_material=is_procurement or "nit" in evidence_id.lower() or "396329" in file_path.name,
        diagnostic=f"Successfully inspected ZIP container with {len(file_list)} files inside.",
    )


def _parse_generic_file(
    evidence_id: str,
    file_path: Path,
    size_bytes: int,
    checksum: Optional[str],
    provenance: ProvenanceEvidenceClass,
    is_procurement: bool,
    suffix: str,
) -> EvidenceParseResult:
    """Fallback reader for generic text or binary files."""
    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as fh:
            lines = [fh.readline() for _ in range(10)]
        readable = True
    except Exception:
        readable = False

    return EvidenceParseResult(
        parse_status=ParseStatus.SUCCESS if readable else ParseStatus.MALFORMED,
        evidence_id=evidence_id,
        detected_format=suffix.upper() or "BINARY",
        file_size_bytes=size_bytes,
        sha256_checksum=checksum,
        readable=readable,
        structural_validity=readable,
        provenance_inherited=provenance,
        tier_a_evaluation_potential=False,
        is_procurement_material=is_procurement,
        diagnostic=f"Generic inspect for format {suffix}: readable={readable}.",
    )
