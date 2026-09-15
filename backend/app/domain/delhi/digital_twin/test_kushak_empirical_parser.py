"""Tests for Phase 10 Step 2: Read-Only Empirical Evidence Parser and Structural Validator."""

import pytest
from pathlib import Path

from .kushak_empirical_parser import (
    parse_evidence_file,
    EvidenceParseResult,
    ParseStatus,
)
from .kushak_empirical_evidence import (
    ProvenanceEvidenceClass,
    NDMC_NIT52_SURVEY_MANIFEST,
)


def test_step2_1_missing_file_returns_not_available():
    """1. Missing file returns NOT_AVAILABLE without fabrication."""
    res = parse_evidence_file("IFC-DGPS-ECHO-EE-CDXII-NIQ-2025-26-249", None)
    assert res.parse_status == ParseStatus.NOT_AVAILABLE
    assert res.readable is False
    assert res.structural_validity is False
    assert res.sha256_checksum is None


def test_step2_2_empty_file_is_empty(tmp_path):
    """2. Empty file (0 bytes) returns EMPTY status."""
    f = tmp_path / "empty.csv"
    f.write_text("", encoding="utf-8")
    res = parse_evidence_file("TEST-EMPTY", f)
    assert res.parse_status == ParseStatus.EMPTY
    assert res.file_size_bytes == 0
    assert res.structural_validity is False


def test_step2_3_csv_valid_structural_parse(tmp_path):
    """3. Valid CSV parses successfully with candidate fields detected."""
    f = tmp_path / "survey.csv"
    f.write_text("chainage_m,invert_elevation,diameter_mm\n0.0,210.5,1200\n10.0,210.2,1200\n", encoding="utf-8")
    res = parse_evidence_file("TEST-CSV", f)
    assert res.parse_status == ParseStatus.SUCCESS
    assert res.detected_format == "CSV"
    assert res.structural_validity is True
    assert res.record_count == 2
    assert "chainage_m" in res.candidate_chainage_fields
    assert "invert_elevation" in res.candidate_elevation_fields


def test_step2_4_csv_malformed_empty_header(tmp_path):
    """4. Malformed CSV handled safely."""
    f = tmp_path / "bad.csv"
    f.write_text("", encoding="utf-8")  # empty is caught as EMPTY
    # test zero-byte or broken CSV
    res = parse_evidence_file("TEST-BAD-CSV", f)
    assert res.parse_status == ParseStatus.EMPTY


def test_step2_5_json_valid(tmp_path):
    """5. Valid JSON parsed successfully."""
    f = tmp_path / "flow.json"
    f.write_text('[{"timestamp": "2024-06-28T12:00:00", "discharge_cumecs": 15.5}]', encoding="utf-8")
    res = parse_evidence_file("TEST-JSON", f)
    assert res.parse_status == ParseStatus.SUCCESS
    assert res.detected_format == "JSON"
    assert res.record_count == 1
    assert "timestamp" in res.candidate_timestamp_fields


def test_step2_6_json_malformed(tmp_path):
    """6. Malformed JSON returns MALFORMED status."""
    f = tmp_path / "malformed.json"
    f.write_text("{not valid json", encoding="utf-8")
    res = parse_evidence_file("TEST-MALFORMED-JSON", f)
    assert res.parse_status == ParseStatus.MALFORMED
    assert res.structural_validity is False


def test_step2_7_xml_valid(tmp_path):
    """7. Valid XML parsed successfully."""
    f = tmp_path / "data.xml"
    f.write_text("<root><station id='1'/><station id='2'/></root>", encoding="utf-8")
    res = parse_evidence_file("TEST-XML", f)
    assert res.parse_status == ParseStatus.SUCCESS
    assert res.detected_format == "XML"
    assert res.record_count == 2


def test_step2_8_xml_malformed(tmp_path):
    """8. Malformed XML returns MALFORMED status."""
    f = tmp_path / "bad.xml"
    f.write_text("<root><unclosed>", encoding="utf-8")
    res = parse_evidence_file("TEST-BAD-XML", f)
    assert res.parse_status == ParseStatus.MALFORMED


def test_step2_9_zip_inspected_not_promoted(tmp_path):
    """9. ZIP archive container inspected without Tier-A promotion."""
    import zipfile
    f = tmp_path / "work_396329.zip"
    with zipfile.ZipFile(f, "w") as zf:
        zf.writestr("nit_spec.txt", "NIT-52 specification text")
    res = parse_evidence_file("NDMC-NIT52-SURVEY-DELIVERABLE", f)
    assert res.parse_status == ParseStatus.SUCCESS
    assert res.detected_format == "ZIP"
    assert res.tier_a_evaluation_potential is False
    assert res.is_procurement_material is True


def test_step2_10_checksum_computed_for_real_file(tmp_path):
    """10. SHA-256 checksum computed only for actual file."""
    f = tmp_path / "data.txt"
    f.write_text("sample content", encoding="utf-8")
    res = parse_evidence_file("TEST-CHECKSUM", f)
    assert res.sha256_checksum is not None
    assert len(res.sha256_checksum) == 64


def test_step2_11_checksum_none_for_missing():
    """11. Checksum is None when file missing."""
    res = parse_evidence_file("TEST-MISSING", None)
    assert res.sha256_checksum is None


def test_step2_12_procurement_flag_preserved(tmp_path):
    """12. Procurement material flag preserved and never promoted."""
    f = tmp_path / "spec.csv"
    f.write_text("chainage,invert\n0.0,210.0\n", encoding="utf-8")
    res = parse_evidence_file("NDMC-NIT52-SURVEY-DELIVERABLE", f)
    assert res.is_procurement_material is True
    assert res.provenance_inherited == ProvenanceEvidenceClass.PROCUREMENT_SPECIFICATION


def test_step2_13_no_hydraulic_output_mutation(tmp_path):
    """13. Parser results do not contain or mutate hydraulic outputs (stage/storage)."""
    f = tmp_path / "test.csv"
    f.write_text("col1\nval1\n", encoding="utf-8")
    res = parse_evidence_file("TEST-MUTATION", f)
    assert not hasattr(res, "stage_m")
    assert not hasattr(res, "storage_m3")
    assert not hasattr(res, "discharge_m3_s")


def test_step2_14_no_synthetic_geometry(tmp_path):
    """14. Parser never fabricates geometry or coordinates."""
    f = tmp_path / "test.csv"
    f.write_text("col1\nval1\n", encoding="utf-8")
    res = parse_evidence_file("TEST-GEO", f)
    assert res.candidate_coordinate_fields == ()
    assert res.candidate_elevation_fields == ()


def test_step2_15_no_tier_a_promotion_for_procurement(tmp_path):
    """15. Tier-A promotion potential is False for procurement material."""
    f = tmp_path / "spec.csv"
    f.write_text("chainage,invert\n0.0,210.0\n", encoding="utf-8")
    res = parse_evidence_file("NDMC-NIT52-SURVEY-DELIVERABLE", f)
    assert res.tier_a_evaluation_potential is False


def test_step2_16_diagnostic_explicit_for_not_available():
    """16. Diagnostic message is explicit when file not available."""
    res = parse_evidence_file("MISSING-PKG", None)
    assert "not present" in res.diagnostic.lower() or "not available" in res.diagnostic.lower()


def test_step2_17_structural_validity_false_for_bad_format(tmp_path):
    """17. Structural validity is False for malformed/empty files."""
    f = tmp_path / "empty.csv"
    f.write_text("", encoding="utf-8")
    res = parse_evidence_file("TEST-EMPTY", f)
    assert res.structural_validity is False


def test_step2_18_coverage_metadata_not_fabricated(tmp_path):
    """18. Coverage metadata is not fabricated or assumed."""
    f = tmp_path / "test.csv"
    f.write_text("col\n1\n", encoding="utf-8")
    res = parse_evidence_file("TEST-COV", f)
    assert res.coverage_metadata == {}


def test_step2_19_explicit_survey_metadata_empty_for_missing():
    """19. Survey metadata remains empty/default when file missing."""
    res = parse_evidence_file("TEST-MISSING", None)
    assert res.explicit_survey_metadata == {}
    assert res.declared_crs is None
    assert res.declared_vertical_datum is None


def test_step2_20_summary_string_deterministic(tmp_path):
    """20. Summary string is deterministic and non-empty."""
    f = tmp_path / "test.csv"
    f.write_text("col\n1\n", encoding="utf-8")
    res = parse_evidence_file("TEST-SUMMARY", f)
    s1 = res.summary_string()
    s2 = res.summary_string()
    assert s1 == s2
    assert "PARSE_RESULT: TEST-SUMMARY" in s1
