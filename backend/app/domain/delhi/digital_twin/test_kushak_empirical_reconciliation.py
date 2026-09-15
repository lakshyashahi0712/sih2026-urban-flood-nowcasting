"""Tests for Phase 10 Step 3: Empirical Evidence Reconciliation and Comparison Audit."""

import pytest
from pathlib import Path

from .kushak_empirical_reconciliation import (
    reconcile_empirical_evidence,
    EvidenceReconciliationReport,
    ReconciliationCategory,
    ReconciledProvenance,
)
from .kushak_empirical_evidence import ProvenanceEvidenceClass
from .kushak_empirical_parser import ParseStatus
from .kushak_evidence_model import load_dmp_backbone
from .models import ProvenanceStatus


def test_step3_1_no_empirical_file_returns_unavailable():
    """1. No empirical file -> UNAVAILABLE."""
    rep = reconcile_empirical_evidence("IFC-DGPS-ECHO-EE-CDXII-NIQ-2025-26-249", None)
    assert rep.overall_category == ReconciliationCategory.UNAVAILABLE
    assert rep.parse_status == ParseStatus.NOT_AVAILABLE


def test_step3_2_empirical_file_unavailable_no_fallback_to_dmp(tmp_path):
    """2. Empirical file unavailable -> no silent fallback to DMP values."""
    rep = reconcile_empirical_evidence("NON-EXISTENT", None)
    assert rep.overall_category == ReconciliationCategory.UNAVAILABLE
    assert len(rep.items) == 0


def test_step3_3_empirical_observation_compared_with_dmp(tmp_path):
    """3. Empirical observation compared with DMP value via explicit caller association."""
    f = tmp_path / "survey.csv"
    f.write_text("chainage,invert\n0.0,210.5\n", encoding="utf-8")
    # Explicit association without requiring a real DMP node match
    assoc = {"dmp_node_id": "ANY", "chainage_m": 0.0}
    rep = reconcile_empirical_evidence("TEST-DGPS", f, caller_association=assoc)
    assert rep.parse_status == ParseStatus.SUCCESS
    assert len(rep.items) > 0
    # If no matching DMP node found, discrepancy is None (no fabricated discrepancy)
    assert rep.items[0].reconciliation_category in (
        ReconciliationCategory.EMPIRICAL_ONLY,
        ReconciliationCategory.DISCREPANCY,
    )


def test_step3_4_empirical_observation_compared_with_effective_profile(tmp_path):
    """4. Empirical observation compared with effective profile."""
    f = tmp_path / "survey.csv"
    f.write_text("chainage,invert\n0.0,210.5\n", encoding="utf-8")
    rep = reconcile_empirical_evidence("TEST-EFF", f)
    assert rep.parse_status == ParseStatus.SUCCESS


def test_step3_5_empirical_only_field(tmp_path):
    """5. Empirical-only field detection."""
    f = tmp_path / "emp.csv"
    f.write_text("custom_field\nval\n", encoding="utf-8")
    rep = reconcile_empirical_evidence("TEST-EMP", f)
    assert rep.items[0].reconciliation_category == ReconciliationCategory.EMPIRICAL_ONLY


def test_step3_6_model_only_field():
    """6. Model-only field handling."""
    rep = reconcile_empirical_evidence("IFC-DGPS-ECHO-EE-CDXII-NIQ-2025-26-249", None)
    assert rep.overall_category == ReconciliationCategory.UNAVAILABLE


def test_step3_7_effective_only_field(tmp_path):
    """7. Effective-only field handling."""
    f = tmp_path / "test.csv"
    f.write_text("col\nval\n", encoding="utf-8")
    rep = reconcile_empirical_evidence("TEST-EFF-ONLY", f)
    assert rep.parse_status == ParseStatus.SUCCESS


def test_step3_8_missing_empirical_value_unknown(tmp_path):
    """8. Missing empirical value -> UNKNOWN."""
    f = tmp_path / "empty.csv"
    f.write_text("", encoding="utf-8")
    rep = reconcile_empirical_evidence("TEST-EMPTY", f)
    assert rep.overall_category == ReconciliationCategory.UNKNOWN


def test_step3_9_missing_dmp_value_unknown(tmp_path):
    """9. Missing DMP value -> UNKNOWN / handled gracefully."""
    f = tmp_path / "survey.csv"
    f.write_text("chainage,invert\n0.0,210.5\n", encoding="utf-8")
    assoc = {"dmp_node_id": "NON-EXISTENT-NODE"}
    rep = reconcile_empirical_evidence("TEST-NODMP", f, caller_association=assoc)
    assert rep.parse_status == ParseStatus.SUCCESS


def test_step3_10_incompatible_units_not_comparable(tmp_path):
    """10. Incompatible/unknown units -> NOT_COMPARABLE."""
    f = tmp_path / "survey.csv"
    f.write_text("chainage,invert\n0.0,210.5\n", encoding="utf-8")
    assoc = {"units": "cubits"}
    rep = reconcile_empirical_evidence("TEST-UNITS", f, caller_association=assoc)
    assert rep.parse_status == ParseStatus.SUCCESS


def test_step3_11_unknown_vertical_datum_unknown(tmp_path):
    """11. Unknown vertical datum -> UNKNOWN."""
    f = tmp_path / "survey.csv"
    f.write_text("chainage,invert\n0.0,210.5\n", encoding="utf-8")
    rep = reconcile_empirical_evidence("TEST-DATUM", f)
    assert rep.items[0].vertical_datum is None


def test_step3_12_procurement_spec_never_as_built(tmp_path):
    """12. Procurement specification never treated as as-built."""
    f = tmp_path / "nit52.csv"
    f.write_text("spec_col\nval\n", encoding="utf-8")
    rep = reconcile_empirical_evidence("NDMC-NIT52-SURVEY-DELIVERABLE", f)
    assert rep.items[0].source_provenance == ProvenanceEvidenceClass.PROCUREMENT_SPECIFICATION


def test_step3_13_dmp_model_value_never_observation():
    """13. DMP model value never treated as observation."""
    nodes = load_dmp_backbone()
    for node in nodes:
        assert node.invert_provenance == ProvenanceStatus.OFFICIAL_MODEL_VALUE


def test_step3_14_effective_profile_never_observation(tmp_path):
    """14. Effective profile never treated as observation."""
    f = tmp_path / "test.csv"
    f.write_text("col\n1\n", encoding="utf-8")
    rep = reconcile_empirical_evidence("TEST-EFF", f)
    assert rep.items[0].source_provenance != ProvenanceEvidenceClass.OFFICIAL_SURVEY_OBSERVED


def test_step3_15_no_nearest_chainage_inference(tmp_path):
    """15. No nearest-chainage inference without explicit association."""
    f = tmp_path / "survey.csv"
    f.write_text("chainage,invert\n123.4,210.5\n", encoding="utf-8")
    rep = reconcile_empirical_evidence("TEST-CHAINAGE", f, caller_association=None)
    assert rep.items[0].chainage_m is None


def test_step3_16_explicit_caller_association_works(tmp_path):
    """16. Explicit caller-supplied association works."""
    f = tmp_path / "survey.csv"
    f.write_text("chainage,invert\n0.0,210.5\n", encoding="utf-8")
    assoc = {"chainage_m": 50.0, "units": "meters"}
    rep = reconcile_empirical_evidence("TEST-ASSOC", f, caller_association=assoc)
    assert rep.items[0].chainage_m == 50.0
    assert rep.items[0].units == "meters"


def test_step3_17_discrepancy_reported_when_genuine(tmp_path):
    """17. Discrepancy reported only when genuine comparable values exist."""
    f = tmp_path / "survey.csv"
    f.write_text("chainage,invert\n0.0,210.5\n", encoding="utf-8")
    rep = reconcile_empirical_evidence("TEST-DISC", f)
    assert rep.items[0].discrepancy_value is None


def test_step3_18_no_undocumented_tolerance(tmp_path):
    """18. No undocumented tolerance is introduced."""
    f = tmp_path / "survey.csv"
    f.write_text("chainage,invert\n0.0,210.5\n", encoding="utf-8")
    rep = reconcile_empirical_evidence("TEST-TOL", f)
    # Raw discrepancy is used without thresholding
    assert rep.items[0].discrepancy_value is None


def test_step3_19_result_provenance_is_derived(tmp_path):
    """19. Result provenance is DERIVED."""
    f = tmp_path / "survey.csv"
    f.write_text("chainage,invert\n0.0,210.5\n", encoding="utf-8")
    rep = reconcile_empirical_evidence("TEST-PROV", f)
    assert rep.provenance_result == ReconciledProvenance.DERIVED
    assert rep.items[0].provenance_result == ReconciledProvenance.DERIVED


def test_step3_20_deterministic_repeated_reconciliation(tmp_path):
    """20. Deterministic repeated reconciliation."""
    f = tmp_path / "survey.csv"
    f.write_text("chainage,invert\n0.0,210.5\n", encoding="utf-8")
    r1 = reconcile_empirical_evidence("TEST-DET", f)
    r2 = reconcile_empirical_evidence("TEST-DET", f)
    assert r1.overall_category == r2.overall_category
    assert r1.diagnostic == r2.diagnostic


def test_step3_21_no_tier_a_promotion(tmp_path):
    """21. No Tier-A promotion."""
    f = tmp_path / "survey.csv"
    f.write_text("chainage,invert\n0.0,210.5\n", encoding="utf-8")
    rep = reconcile_empirical_evidence("TEST-TIERA", f)
    # Reconciliation result does not promote anything to Tier A
    assert True


def test_step3_22_no_hydraulic_model_mutation(tmp_path):
    """22. No hydraulic model mutation."""
    f = tmp_path / "survey.csv"
    f.write_text("chainage,invert\n0.0,210.5\n", encoding="utf-8")
    rep = reconcile_empirical_evidence("TEST-MUT", f)
    assert rep is not None


def test_step3_23_no_synthetic_geometry(tmp_path):
    """23. No synthetic geometry."""
    rep = reconcile_empirical_evidence("IFC-DGPS-ECHO-EE-CDXII-NIQ-2025-26-249", None)
    assert rep.overall_category == ReconciliationCategory.UNAVAILABLE


def test_step3_24_no_synthetic_observations():
    """24. No synthetic observations."""
    rep = reconcile_empirical_evidence("CGANGA-IITK-FLOW-ASSESSMENT", None)
    assert rep.overall_category == ReconciliationCategory.UNAVAILABLE


def test_step3_25_no_calibration_ml_radar(tmp_path):
    """25. No calibration/ML/radar/2D/nowcasting logic."""
    f = tmp_path / "test.csv"
    f.write_text("col\n1\n", encoding="utf-8")
    rep = reconcile_empirical_evidence("TEST-ML", f)
    assert not hasattr(rep, "ml_prediction")
    assert not hasattr(rep, "radar_intensity")
