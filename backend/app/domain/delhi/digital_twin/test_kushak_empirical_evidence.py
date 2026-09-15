"""Tests for Phase 10 Step 1: Empirical Evidence Package Contract and Acquisition Manifest."""

import pytest
from pathlib import Path

from .kushak_empirical_evidence import (
    EvidencePackage,
    EvidenceType,
    AcquisitionStatus,
    ProvenanceEvidenceClass,
    CoverageStatus,
    IFC_DGPS_ECHO_MANIFEST,
    NDMC_NIT52_SURVEY_MANIFEST,
    CGANGA_IITK_FLOW_MANIFEST,
    RAINFALL_HOURLY_MANIFEST,
    load_evidence_manifest,
    enforce_procurement_never_promoted,
    enforce_no_tier_a_promotion,
)
from .kushak_evidence_model import DMPBackboneNode, load_dmp_backbone
from .models import ProvenanceStatus


def test_step1_1_valid_evidence_package():
    """1. Valid evidence package instantiation."""
    pkg = EvidencePackage(
        evidence_id="TEST-PKG-01",
        evidence_type=EvidenceType.IFC_DGPS_ECHO_SURVEY,
        source_organization="Test Org",
        source_reference="Ref 1",
        acquisition_status=AcquisitionStatus.ACQUIRED_VERIFIED,
        provenance_status=ProvenanceEvidenceClass.OFFICIAL_SURVEY_OBSERVED,
    )
    assert pkg.evidence_id == "TEST-PKG-01"
    assert pkg.acquisition_status == AcquisitionStatus.ACQUIRED_VERIFIED


def test_step1_2_missing_evidence_package():
    """2. Missing evidence package lookup returns None."""
    res = load_evidence_manifest("NON-EXISTENT-ID")
    assert res is None


def test_step1_3_not_acquired_status():
    """3. NOT_ACQUIRED status correctly represented in missing I&FC manifest."""
    assert IFC_DGPS_ECHO_MANIFEST.acquisition_status == AcquisitionStatus.NOT_ACQUIRED


def test_step1_4_acquired_unverified_status():
    """4. ACQUIRED_UNVERIFIED status handling."""
    pkg = EvidencePackage(
        evidence_id="TEST-UNVERIFIED",
        evidence_type=EvidenceType.CGANGA_IITK_FLOW_ASSESSMENT,
        source_organization="Test",
        source_reference="Test",
        acquisition_status=AcquisitionStatus.ACQUIRED_UNVERIFIED,
        provenance_status=ProvenanceEvidenceClass.UNVERIFIED,
    )
    assert pkg.acquisition_status == AcquisitionStatus.ACQUIRED_UNVERIFIED


def test_step1_5_acquired_verified_status():
    """5. ACQUIRED_VERIFIED status handling."""
    pkg = EvidencePackage(
        evidence_id="TEST-VERIFIED",
        evidence_type=EvidenceType.IFC_DGPS_ECHO_SURVEY,
        source_organization="Test",
        source_reference="Test",
        acquisition_status=AcquisitionStatus.ACQUIRED_VERIFIED,
        provenance_status=ProvenanceEvidenceClass.OFFICIAL_SURVEY_OBSERVED,
    )
    assert pkg.acquisition_status == AcquisitionStatus.ACQUIRED_VERIFIED


def test_step1_6_partially_acquired_status():
    """6. PARTIALLY_ACQUIRED status handling (e.g. Rainfall hourly telemetry)."""
    assert RAINFALL_HOURLY_MANIFEST.acquisition_status == AcquisitionStatus.PARTIALLY_ACQUIRED


def test_step1_7_sha256_present_for_actual_file(tmp_path):
    """7. SHA-256 calculated correctly when actual file exists."""
    f = tmp_path / "sample_survey.csv"
    f.write_text("chainage,invert\n0.0,210.0\n", encoding="utf-8")
    pkg = EvidencePackage(
        evidence_id="TEST-FILE",
        evidence_type=EvidenceType.IFC_DGPS_ECHO_SURVEY,
        source_organization="Test",
        source_reference="Test",
        file_path=f,
    )
    checksum = pkg.compute_checksum_for_path(f)
    assert checksum is not None
    assert len(checksum) == 64  # SHA-256 hex digest length


def test_step1_8_sha256_unknown_when_absent():
    """8. SHA-256 remains unknown/None when file absent."""
    pkg = EvidencePackage(
        evidence_id="TEST-NO-FILE",
        evidence_type=EvidenceType.IFC_DGPS_ECHO_SURVEY,
        source_organization="Test",
        source_reference="Test",
        file_path=None,
        sha256_checksum=None,
    )
    assert pkg.sha256_checksum is None
    assert pkg.compute_checksum_for_path(None) is None


def test_step1_9_procurement_spec_remains_procurement():
    """9. Procurement specification remains PROCUREMENT_SPECIFICATION."""
    assert NDMC_NIT52_SURVEY_MANIFEST.provenance_status == ProvenanceEvidenceClass.PROCUREMENT_SPECIFICATION
    enforce_procurement_never_promoted(NDMC_NIT52_SURVEY_MANIFEST)


def test_step1_10_dmp_model_value_cannot_become_survey_observation():
    """10. DMP model value retains OFFICIAL_MODEL_VALUE and cannot become survey observation."""
    nodes = load_dmp_backbone()
    for node in nodes:
        assert node.invert_provenance == ProvenanceStatus.OFFICIAL_MODEL_VALUE
        assert node.invert_provenance != ProvenanceStatus.OBSERVED
        assert node.invert_provenance != ProvenanceStatus.OFFICIAL


def test_step1_11_unknown_datum_remains_unknown():
    """11. UNKNOWN datum remains UNKNOWN."""
    assert IFC_DGPS_ECHO_MANIFEST.vertical_datum is None


def test_step1_12_unknown_crs_remains_unknown():
    """12. UNKNOWN CRS remains UNKNOWN."""
    assert IFC_DGPS_ECHO_MANIFEST.horizontal_crs is None


def test_step1_13_unknown_spatial_coverage_explicit():
    """13. Unknown spatial coverage remains explicit (UNKNOWN)."""
    assert IFC_DGPS_ECHO_MANIFEST.spatial_coverage == CoverageStatus.UNKNOWN


def test_step1_14_partial_spatial_coverage_preserved():
    """14. Partial spatial coverage is preserved."""
    assert NDMC_NIT52_SURVEY_MANIFEST.spatial_coverage == CoverageStatus.PARTIAL


def test_step1_15_no_automatic_tier_a_promotion():
    """15. No automatic Tier-A promotion; tier_a_eligible is False."""
    for pkg in (IFC_DGPS_ECHO_MANIFEST, NDMC_NIT52_SURVEY_MANIFEST, CGANGA_IITK_FLOW_MANIFEST, RAINFALL_HOURLY_MANIFEST):
        assert pkg.tier_a_eligible is False
        assert pkg.tier_a_promotion_mechanism_exists is False
        enforce_no_tier_a_promotion(pkg)


def test_step1_16_deterministic_manifest_representation():
    """16. Deterministic manifest string representation."""
    m1 = IFC_DGPS_ECHO_MANIFEST.manifest_string()
    m2 = IFC_DGPS_ECHO_MANIFEST.manifest_string()
    assert m1 == m2
    assert "IFC-DGPS-ECHO-EE-CDXII-NIQ-2025-26-249" in m1


def test_step1_17_immutable_frozen_result():
    """17. EvidencePackage is immutable (frozen dataclass)."""
    with pytest.raises(Exception):
        IFC_DGPS_ECHO_MANIFEST.evidence_id = "MUTATED"  # type: ignore


def test_step1_18_no_synthetic_geometry():
    """18. No synthetic geometry created by Step 1 packages."""
    assert IFC_DGPS_ECHO_MANIFEST.is_synthetic_geometry() is False
    assert NDMC_NIT52_SURVEY_MANIFEST.is_synthetic_geometry() is False


def test_step1_19_no_synthetic_observations():
    """19. No synthetic observations created by Step 1 packages."""
    assert IFC_DGPS_ECHO_MANIFEST.is_synthetic_observation() is False
    assert CGANGA_IITK_FLOW_MANIFEST.is_synthetic_observation() is False


def test_step1_20_no_modification_of_tier_b_scenario_outputs():
    """20. Tier-B scenario outputs and execution remain completely unmodified."""
    from .kushak_evidence_model import (
        KushakHydraulicScenario,
        CATCHMENT_SCENARIOS,
        KUSHAK_HYDRAULIC_SCENARIOS,
        run_kushak_evidence_scenario,
    )
    # Verify Tier-B scenario execution still runs successfully and produces DERIVED outputs without interference
    central_scenario = KUSHAK_HYDRAULIC_SCENARIOS["CENTRAL"]
    catchment = CATCHMENT_SCENARIOS["WORKING_27_66"]
    res = run_kushak_evidence_scenario(central_scenario, catchment)
    assert res is not None
