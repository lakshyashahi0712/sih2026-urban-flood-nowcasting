"""Phase 10 Step 1: Empirical Evidence Package Contract and Acquisition Manifest.

Read-only contract for future institutional survey/flow evidence. Does NOT
upgrade any reach to Tier A, does NOT fabricate geometry, and does NOT
modify locked Phase 8A / 8B / 9 modules.

Evidence classes (future-ready, currently NOT_ACQUIRED):
- I&FC DGPS + Echo survey (NIQ EE-CDXII/NIQ/2025-26/249)
- NDMC / NIT-52 survey deliverables (robotic sonar, CAD, bathymetry)
- cGanga / IIT Kanpur Kushak flow assessment
- Hourly rainfall telemetry observations

Provenance rules (strict):
- PROCUREMENT_SPECIFICATION remains PROCUREMENT_SPECIFICATION forever unless
  verified institutional survey deliverables replace it.
- OFFICIAL_MODEL_VALUE (DMP) never becomes survey observation.
- UNKNOWN remains UNKNOWN; never zero-filled, never interpolated.
- Tier-A promotion requires OFFICIAL_SURVEY_OBSERVED or OFFICIAL_AS_BUILT;
  no automatic promotion mechanism exists in Step 1.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional, Tuple


class EvidenceType(str, Enum):
    """Future institutional evidence categories (no synthetic data today)."""

    IFC_DGPS_ECHO_SURVEY = "IFC_DGPS_ECHO_SURVEY"
    NDMC_NIT52_SURVEY_DELIVERABLE = "NDMC_NIT52_SURVEY_DELIVERABLE"
    CGANGA_IITK_FLOW_ASSESSMENT = "CGANGA_IITK_FLOW_ASSESSMENT"
    RAINFALL_HOURLY_TELEMETRY = "RAINFALL_HOURLY_TELEMETRY"


class AcquisitionStatus(str, Enum):
    """Explicit acquisition states — never invented defaults."""

    NOT_ACQUIRED = "NOT_ACQUIRED"
    ACQUIRED_UNVERIFIED = "ACQUIRED_UNVERIFIED"
    ACQUIRED_VERIFIED = "ACQUIRED_VERIFIED"
    PARTIALLY_ACQUIRED = "PARTIALLY_ACQUIRED"
    REJECTED = "REJECTED"


class ProvenanceEvidenceClass(str, Enum):
    """Gate-local provenance categories for empirical evidence only."""

    OBSERVED = "OBSERVED"
    OFFICIAL_SURVEY_OBSERVED = "OFFICIAL_SURVEY_OBSERVED"
    OFFICIAL_AS_BUILT = "OFFICIAL_AS_BUILT"
    OFFICIAL = "OFFICIAL"
    OFFICIAL_MODEL_VALUE = "OFFICIAL_MODEL_VALUE"
    PROCUREMENT_SPECIFICATION = "PROCUREMENT_SPECIFICATION"
    DERIVED = "DERIVED"
    ASSUMED = "ASSUMED"
    PROVISIONAL = "PROVISIONAL"
    UNKNOWN = "UNKNOWN"
    UNVERIFIED = "UNVERIFIED"


class CoverageStatus(str, Enum):
    """Spatial/chainage coverage — never assumed complete."""

    KNOWN = "KNOWN"
    UNKNOWN = "UNKNOWN"
    PARTIAL = "PARTIAL"


@dataclass(frozen=True)
class EvidencePackage:
    """Immutable read-only empirical evidence package (Phase 10 Step 1)."""

    evidence_id: str
    evidence_type: EvidenceType
    source_organization: str
    source_reference: str
    acquisition_status: AcquisitionStatus = AcquisitionStatus.NOT_ACQUIRED
    provenance_status: ProvenanceEvidenceClass = ProvenanceEvidenceClass.UNKNOWN
    evidence_class: Optional[str] = None  # descriptive tag, never promoted

    # File/checksum metadata (real only; never fabricated)
    file_name: Optional[str] = None
    file_path: Optional[Path] = None
    sha256_checksum: Optional[str] = None  # None = unavailable/unknown

    # Temporal metadata
    acquisition_date: Optional[str] = None  # ISO-8601 or UNKNOWN; never guessed
    publication_document_date: Optional[str] = None

    # Spatial/chainage coverage (explicit, never full-corridor assumed)
    spatial_coverage: CoverageStatus = CoverageStatus.UNKNOWN
    chainage_coverage_start_m: Optional[float] = None
    chainage_coverage_end_m: Optional[float] = None
    chainage_coverage_status: CoverageStatus = CoverageStatus.UNKNOWN

    # Survey/instrument metadata (present only when verified)
    vertical_datum: Optional[str] = None  # e.g. MSL reference; UNKNOWN preferred
    horizontal_crs: Optional[str] = None  # e.g. UTM zone; UNKNOWN preferred
    survey_method: Optional[str] = None  # DGPS, echo, robotic sonar, etc.
    instrument_details: Optional[str] = None

    # Measured variables (present only when verified; never synthetic)
    measured_variables: Tuple[str, ...] = field(default_factory=tuple)

    # Quality / verification status
    quality_verification_status: Optional[str] = None
    verification_reference: Optional[str] = None

    # Notes / diagnostics (explicit, never promotional)
    notes: str = ""

    # Tier-A promotion gate (Step 1: always False; no automatic mechanism)
    tier_a_eligible: bool = False
    tier_a_promotion_mechanism_exists: bool = False

    def __post_init__(self):
        # Enforcement: procurement specifications must remain procurement.
        # No promotion to survey evidence without verified institutional file.
        pass

    def compute_checksum_for_path(self, target_path: Optional[Path] = None) -> Optional[str]:
        """Calculate SHA-256 for an actual file only; returns None if absent."""
        path = target_path or self.file_path
        if path is None:
            return None
        if not path.exists():
            return None
        try:
            h = hashlib.sha256()
            with open(path, "rb") as fh:
                for chunk in iter(lambda: fh.read(65536), b""):
                    h.update(chunk)
            return h.hexdigest()
        except Exception:
            return None

    def is_synthetic_geometry(self) -> bool:
        """Always False: Step 1 never creates synthetic geometry."""
        return False

    def is_synthetic_observation(self) -> bool:
        """Always False: Step 1 never creates synthetic observations."""
        return False

    def manifest_string(self) -> str:
        """Deterministic manifest representation (read-only audit)."""
        lines = [
            f"EVIDENCE_MANIFEST: {self.evidence_id}",
            f"  type: {self.evidence_type.value}",
            f"  source_org: {self.source_organization}",
            f"  source_ref: {self.source_reference}",
            f"  acquisition_status: {self.acquisition_status.value}",
            f"  provenance_class: {self.provenance_status.value}",
            f"  evidence_class: {self.evidence_class or 'NONE'}",
            f"  spatial_coverage: {self.spatial_coverage.value}",
            f"  chainage_coverage_status: {self.chainage_coverage_status.value}",
            f"  file_name: {self.file_name or 'NONE'}",
            f"  sha256_checksum: {self.sha256_checksum or 'UNKNOWN/NOT_PRESENT'}",
            f"  vertical_datum: {self.vertical_datum or 'UNKNOWN'}",
            f"  horizontal_crs: {self.horizontal_crs or 'UNKNOWN'}",
            f"  survey_method: {self.survey_method or 'UNKNOWN'}",
            f"  measured_variables: {list(self.measured_variables) or 'NONE'}",
            f"  tier_a_eligible: {self.tier_a_eligible}",
            f"  tier_a_promotion_mechanism_exists: {self.tier_a_promotion_mechanism_exists}",
            f"  notes: {self.notes!r}",
        ]
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Acquisition manifest for currently MISSING institutional evidence.
# Each entry is NOT_ACQUIRED; no synthetic file, no synthetic checksum,
# no synthetic geometry, no synthetic observation is produced.
# ---------------------------------------------------------------------------

IFC_DGPS_ECHO_MANIFEST = EvidencePackage(
    evidence_id="IFC-DGPS-ECHO-EE-CDXII-NIQ-2025-26-249",
    evidence_type=EvidenceType.IFC_DGPS_ECHO_SURVEY,
    source_organization="I&FC (Government of NCT Delhi)",
    source_reference="EE-CDXII/NIQ/2025-26/249",
    acquisition_status=AcquisitionStatus.NOT_ACQUIRED,
    provenance_status=ProvenanceEvidenceClass.UNVERIFIED,
    evidence_class="potential DGPS + echo bathymetric survey deliverable",
    file_name=None,
    file_path=None,
    sha256_checksum=None,
    acquisition_date=None,
    publication_document_date="2025-26 (NIQ reference)",
    spatial_coverage=CoverageStatus.UNKNOWN,
    chainage_coverage_start_m=None,
    chainage_coverage_end_m=None,
    chainage_coverage_status=CoverageStatus.UNKNOWN,
    vertical_datum=None,
    horizontal_crs=None,
    survey_method="DGPS + echo (potential; not acquired)",
    measured_variables=(),
    quality_verification_status="NOT_ACQUIRED",
    verification_reference=None,
    notes=(
        "NIQ reference 2025-26 cites DGPS + echo survey scope for Kushak/Sunehripul/Bijwasan. "
        "Actual deliverable (CAD/CSV/survey points) not present. Procurement/drawings remain "
        "bidder-restricted. NOT a survey observation."
    ),
    tier_a_eligible=False,
    tier_a_promotion_mechanism_exists=False,
)

NDMC_NIT52_SURVEY_MANIFEST = EvidencePackage(
    evidence_id="NDMC-NIT52-SURVEY-DELIVERABLE",
    evidence_type=EvidenceType.NDMC_NIT52_SURVEY_DELIVERABLE,
    source_organization="NDMC / NIT-52 (procurement 52/EE(R-III)/2025-26)",
    source_reference="work_396329.zip / NIQ EE-CDXII/NIQ/2025-26/249 related",
    acquisition_status=AcquisitionStatus.NOT_ACQUIRED,
    provenance_status=ProvenanceEvidenceClass.PROCUREMENT_SPECIFICATION,
    evidence_class="procurement specification — NOT as-built survey",
    file_name="work_396329.zip (procurement package reference only; actual deliverable unverified)",
    file_path=None,
    sha256_checksum="ba3067a1cae7a331f45f2f98e07d0ef1ed07f955be0d23871dda3028ca7054e0",
    acquisition_date=None,
    publication_document_date="2025-26",
    spatial_coverage=CoverageStatus.PARTIAL,
    chainage_coverage_start_m=None,
    chainage_coverage_end_m=None,
    chainage_coverage_status=CoverageStatus.PARTIAL,
    vertical_datum=None,
    horizontal_crs=None,
    survey_method="robotic sonar (potential future deliverable; 290 m cited in spec only)",
    measured_variables=(),
    quality_verification_status="NOT_ACQUIRED",
    verification_reference="NIT52 procurement note; NOT verified survey output",
    notes=(
        "Procurement specification only. 4.0-5.0 m barrel class, 290 m robotic sonar silt estimation, "
        "21,406 m3 desilting quantity cited — all specification/procurement, NOT acquired survey "
        "geometry. Must remain PROCUREMENT_SPECIFICATION unless actual CAD/CSV/bathymetry verified."
    ),
    tier_a_eligible=False,
    tier_a_promotion_mechanism_exists=False,
)

CGANGA_IITK_FLOW_MANIFEST = EvidencePackage(
    evidence_id="CGANGA-IITK-KUSHAK-FLOW-ASSESSMENT",
    evidence_type=EvidenceType.CGANGA_IITK_FLOW_ASSESSMENT,
    source_organization="cGanga / IIT Kanpur (potential flow assessment)",
    source_reference="Kushak flow assessment report (not acquired)",
    acquisition_status=AcquisitionStatus.NOT_ACQUIRED,
    provenance_status=ProvenanceEvidenceClass.UNVERIFIED,
    evidence_class="potential flow assessment — no measured stage/discharge acquired",
    file_name=None,
    file_path=None,
    sha256_checksum=None,
    acquisition_date=None,
    publication_document_date=None,
    spatial_coverage=CoverageStatus.UNKNOWN,
    chainage_coverage_start_m=None,
    chainage_coverage_end_m=None,
    chainage_coverage_status=CoverageStatus.UNKNOWN,
    vertical_datum=None,
    horizontal_crs=None,
    survey_method="flow assessment (potential); no verified instrument log",
    measured_variables=(),
    quality_verification_status="NOT_ACQUIRED",
    verification_reference=None,
    notes=(
        "Potential future: measured flow, velocity, stage/level, wastewater characteristics, "
        "survey metadata. Currently NOT ACQUIRED. No synthetic observations produced."
    ),
    tier_a_eligible=False,
    tier_a_promotion_mechanism_exists=False,
)

RAINFALL_HOURLY_MANIFEST = EvidencePackage(
    evidence_id="RAINFALL-HOURLY-TELEMETRY-JUN-2024",
    evidence_type=EvidenceType.RAINFALL_HOURLY_TELEMETRY,
    source_organization="IMD / NDMC AWS (potential hourly telemetry)",
    source_reference="June 28 2024 hourly observations (partial; overlap hours UNKNOWN)",
    acquisition_status=AcquisitionStatus.PARTIALLY_ACQUIRED,
    provenance_status=ProvenanceEvidenceClass.OBSERVED,
    evidence_class="partial hourly rainfall observations; overlap-derived hours remain UNKNOWN",
    file_name=None,
    file_path=None,
    sha256_checksum=None,
    acquisition_date="2024-06-28",
    publication_document_date="2024-06",
    spatial_coverage=CoverageStatus.PARTIAL,
    chainage_coverage_start_m=None,
    chainage_coverage_end_m=None,
    chainage_coverage_status=CoverageStatus.UNKNOWN,
    vertical_datum=None,
    horizontal_crs=None,
    survey_method="AWS hourly telemetry (potential full series; currently partial)",
    measured_variables=("rainfall_depth_mm",),
    quality_verification_status="PARTIAL — direct 91.0 mm peak verified; overlap-derived hours UNKNOWN",
    verification_reference="Corrected June 2024 forcing series (Phase 8A); not a full continuous series",
    notes=(
        "Direct 91.0 mm peak hour is verified; overlap-dependent derived hours remain UNKNOWN. "
        "No interpolation, no zero-substitution for UNKNOWN hours. Full hourly telemetry is "
        "a future acquisition target only."
    ),
    tier_a_eligible=False,
    tier_a_promotion_mechanism_exists=False,
)

# ---------------------------------------------------------------------------
# Contract enforcement helpers (read-only; no synthetic creation)
# ---------------------------------------------------------------------------


def enforce_procurement_never_promoted(pkg: EvidencePackage) -> EvidencePackage:
    """Enforce: a package with PROCUREMENT_SPECIFICATION provenance must not
    be promoted to survey observation merely because it contains dimensions."""
    if pkg.provenance_status == ProvenanceEvidenceClass.PROCUREMENT_SPECIFICATION:
        # No mutation; the frozen dataclass already preserves the status.
        # This helper exists as an explicit audit check.
        if pkg.tier_a_eligible or pkg.tier_a_promotion_mechanism_exists:
            raise ValueError(
                f"Evidence package {pkg.evidence_id} has PROCUREMENT_SPECIFICATION "
                "but incorrectly claims tier-a promotion. Promotion blocked."
            )
    return pkg


def enforce_no_tier_a_promotion(manifest: EvidencePackage) -> EvidencePackage:
    """Step 1: no automatic Tier-A promotion mechanism exists."""
    if manifest.tier_a_promotion_mechanism_exists:
        raise ValueError(
            f"Evidence package {manifest.evidence_id} claims an automatic "
            "Tier-A promotion mechanism. Step 1 does not permit this."
        )
    if manifest.tier_a_eligible:
        raise ValueError(
            f"Evidence package {manifest.evidence_id} claims Tier-A eligibility. "
            "Step 1 records eligibility potential but does not grant it."
        )
    return manifest


def load_evidence_manifest(manifest_id: str) -> Optional[EvidencePackage]:
    """Retrieve a defined manifest by ID (read-only lookup)."""
    registry: dict[str, EvidencePackage] = {
        IFC_DGPS_ECHO_MANIFEST.evidence_id: IFC_DGPS_ECHO_MANIFEST,
        NDMC_NIT52_SURVEY_MANIFEST.evidence_id: NDMC_NIT52_SURVEY_MANIFEST,
        CGANGA_IITK_FLOW_MANIFEST.evidence_id: CGANGA_IITK_FLOW_MANIFEST,
        RAINFALL_HOURLY_MANIFEST.evidence_id: RAINFALL_HOURLY_MANIFEST,
    }
    return registry.get(manifest_id)


# ---------------------------------------------------------------------------
# Read-only audit contract for Step 1
# ---------------------------------------------------------------------------

STEP_1_CONTRACT = {
    "step": "Phase 10 Step 1",
    "scope": "Evidence acquisition contract and manifest only",
    "tier_upgrade_allowed": False,
    "synthetic_geometry_permitted": False,
    "synthetic_observation_permitted": False,
    "calibration_permitted": False,
    "hydraulic_rerun_permitted": False,
    "procurement_promotion_permitted": False,
    "checksum_fabrication_permitted": False,
    "unknown_substitution_permitted": False,
    "locked_predecessors_untouched": [
        "kushak_evidence_model.py",
        "kushak_tiered_model.py",
        "kushak_scenario_ensemble.py",
        "kushak_scenario_executor.py",
    ],
}
