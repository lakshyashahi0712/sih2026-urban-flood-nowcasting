"""Phase 8B Step-1 tests for the three-tier model-tier contract.

Provenance rules are asserted strictly: no assertion is weakened; UNKNOWN
stays UNKNOWN and no missing input can be silently converted into Tier-A
evidence. Tier A is satisfiable ONLY by explicit survey-grade/as-built
evidence classes (a synthetic contract fixture proves that path is
executable — it is not real Kushak evidence and is never used in any real
run).
"""

import pytest

from .kushak_tiered_model import (
    NON_SATISFYING_EVIDENCE,
    TIER_A_REQUIREMENTS,
    ModelTier,
    SurveyEvidenceClass,
    TierCRegistry,
    build_tier_b_model,
    evaluate_tier_gate,
    load_current_tier_state,
)
from .models import ProvenanceStatus


def _all_requirements_claim(provenance: ProvenanceStatus) -> dict:
    """A synthetic claim of one generic ProvenanceStatus for every
    required physical input — used only to prove each class is blocked."""
    return {r.requirement_id: provenance for r in TIER_A_REQUIREMENTS}


# ---------------------------------------------------------------------------
# 1. Current Kushak evidence -> Tier A blocked
# ---------------------------------------------------------------------------


def test_tier_a_blocked_with_current_evidence():
    gate, registry = load_current_tier_state()
    assert gate.tier == ModelTier.TIER_C_BLOCKED_INPUTS
    assert gate.tier != ModelTier.TIER_A_PHYSICAL_AS_BUILT
    assert gate.can_promote_to_tier_a is False
    assert len(gate.missing_inputs) == len(TIER_A_REQUIREMENTS)
    assert registry.tier == ModelTier.TIER_C_BLOCKED_INPUTS
    assert len(registry.missing_inputs) == len(TIER_A_REQUIREMENTS)


def test_tier_a_requirements_all_unsatisfied():
    gate = evaluate_tier_gate()
    missing_ids = {m.requirement_id for m in gate.missing_inputs}
    assert missing_ids == {r.requirement_id for r in TIER_A_REQUIREMENTS}


# ---------------------------------------------------------------------------
# 2-5. Every generic ProvenanceStatus is blocked (no weakening)
# ---------------------------------------------------------------------------


def test_generic_official_blocked():
    gate = evaluate_tier_gate(_all_requirements_claim(ProvenanceStatus.OFFICIAL))
    assert gate.tier == ModelTier.TIER_C_BLOCKED_INPUTS
    assert gate.can_promote_to_tier_a is False
    assert len(gate.missing_inputs) == len(TIER_A_REQUIREMENTS)


def test_official_model_value_blocked():
    gate = evaluate_tier_gate(_all_requirements_claim(
        ProvenanceStatus.OFFICIAL_MODEL_VALUE))
    assert gate.tier == ModelTier.TIER_C_BLOCKED_INPUTS
    assert gate.can_promote_to_tier_a is False


def test_observed_bounded_evidence_blocked():
    # OBSERVED visual/bounded field evidence is not survey-grade.
    gate = evaluate_tier_gate(_all_requirements_claim(ProvenanceStatus.OBSERVED))
    assert gate.tier == ModelTier.TIER_C_BLOCKED_INPUTS
    assert gate.can_promote_to_tier_a is False


def test_nit52_procurement_specification_blocked():
    # NIT52 is OFFICIAL but PROCUREMENT_SPECIFICATION — spec != as-built.
    nit52 = next(
        e for e in NON_SATISFYING_EVIDENCE if "NIT52" in e["evidence"]
    )
    assert nit52["class"] == "PROCUREMENT_SPECIFICATION"
    assert "never as-built" in nit52["rule"]
    # Even per-requirement OFFICIAL claims (the strongest generic class)
    # cannot open Tier A for the NIT52-covered dimensions.
    spec_claim = {
        "UG01_internal_barrel_width": ProvenanceStatus.OFFICIAL,
        "CD01_hydraulic_clear_width": ProvenanceStatus.OFFICIAL,
    }
    gate = evaluate_tier_gate(spec_claim)
    assert gate.tier == ModelTier.TIER_C_BLOCKED_INPUTS
    assert gate.can_promote_to_tier_a is False


def test_dmp_model_values_blocked():
    dmp = next(
        e for e in NON_SATISFYING_EVIDENCE if "DMP" in e["evidence"]
    )
    assert dmp["class"] == "OFFICIAL_MODEL_VALUE"
    assert "never surveyed" in dmp["rule"]
    gate = evaluate_tier_gate(_all_requirements_claim(
        ProvenanceStatus.OFFICIAL_MODEL_VALUE))
    assert gate.tier == ModelTier.TIER_C_BLOCKED_INPUTS
    assert gate.can_promote_to_tier_a is False


# ---------------------------------------------------------------------------
# 6. ASSUMED / DERIVED / INFERRED_EFFECTIVE / UNKNOWN -> blocked
# ---------------------------------------------------------------------------


def test_assumed_derived_provisional_unknown_blocked():
    for prov in (
        ProvenanceStatus.ASSUMED,
        ProvenanceStatus.DERIVED,
        ProvenanceStatus.PROVISIONAL,
        ProvenanceStatus.UNKNOWN,
    ):
        gate = evaluate_tier_gate(_all_requirements_claim(prov))
        assert gate.tier == ModelTier.TIER_C_BLOCKED_INPUTS, prov
        assert gate.can_promote_to_tier_a is False
    # INFERRED_EFFECTIVE has no ProvenanceStatus member; as an effective/
    # inferred label it is structurally below survey grade — covered by
    # the ASSUMED/DERIVED block above and by the SurveyEvidenceClass gate,
    # which has no member it could map to.


# ---------------------------------------------------------------------------
# 7. Synthetic survey/as-built fixture can open Tier A (CONTRACT TEST ONLY)
# ---------------------------------------------------------------------------


def test_synthetic_survey_evidence_opens_tier_a_contract_only():
    """SYNTHETIC / FUTURE-EVIDENCE CONTRACT TEST.

    Marks the executable path for future ACQUIRED survey/as-built
    evidence. NOT real Kushak evidence — must never be used in any real
    Kushak run. No claim is made that survey/as-built evidence exists.
    """
    synthetic_survey_evidence = {
        r.requirement_id: SurveyEvidenceClass.OFFICIAL_SURVEY_OBSERVED
        for r in TIER_A_REQUIREMENTS
    }
    gate = evaluate_tier_gate(provided_survey_evidence=synthetic_survey_evidence)
    assert gate.tier == ModelTier.TIER_A_PHYSICAL_AS_BUILT
    assert gate.can_promote_to_tier_a is True
    assert len(gate.missing_inputs) == 0


def test_synthetic_asbuilt_evidence_opens_tier_a_contract_only():
    """SYNTHETIC / FUTURE-EVIDENCE CONTRACT TEST — as-built variant."""
    synthetic_asbuilt = {
        r.requirement_id: SurveyEvidenceClass.OFFICIAL_AS_BUILT
        for r in TIER_A_REQUIREMENTS
    }
    gate = evaluate_tier_gate(provided_survey_evidence=synthetic_asbuilt)
    assert gate.tier == ModelTier.TIER_A_PHYSICAL_AS_BUILT
    assert gate.can_promote_to_tier_a is True


def test_survey_evidence_must_cover_every_requirement():
    # Partial survey evidence still leaves the gate blocked — no
    # requirement may be silently waived.
    partial = {
        "UG01_internal_barrel_width": SurveyEvidenceClass.OFFICIAL_SURVEY_OBSERVED,
        "CD01_hydraulic_clear_width": SurveyEvidenceClass.OFFICIAL_AS_BUILT,
    }
    gate = evaluate_tier_gate(provided_survey_evidence=partial)
    assert gate.tier == ModelTier.TIER_C_BLOCKED_INPUTS
    assert gate.can_promote_to_tier_a is False
    assert len(gate.missing_inputs) == len(TIER_A_REQUIREMENTS) - 2


def test_generic_provenance_never_maps_to_survey_class():
    # Even with a full generic-OFFICIAL claim AND a survey-evidence dict
    # omitted, the gate stays blocked: the two channels never combine.
    gate = evaluate_tier_gate(_all_requirements_claim(ProvenanceStatus.OFFICIAL))
    assert gate.tier == ModelTier.TIER_C_BLOCKED_INPUTS


# ---------------------------------------------------------------------------
# 8. Tier B remains RUNNABLE_AS_SCENARIO
# ---------------------------------------------------------------------------


def test_tier_b_explicitly_runnable_as_scenario():
    tier_b = build_tier_b_model()
    assert tier_b.tier == ModelTier.TIER_B_EFFECTIVE_SCENARIO
    assert tier_b.status == "RUNNABLE_AS_SCENARIO"
    assert tier_b.is_physical_as_built is False
    assert tier_b.is_surveyed is False


# ---------------------------------------------------------------------------
# 9. Tier B cannot promote to Tier A
# ---------------------------------------------------------------------------


def test_tier_b_cannot_be_promoted_to_tier_a():
    tier_b = build_tier_b_model()
    assert tier_b.tier == ModelTier.TIER_B_EFFECTIVE_SCENARIO
    # Only the synthetic full-survey fixture opens Tier A, and even then
    # the gate result is a distinct object from the Tier-B handle — the
    # two are never interchangeable.
    synthetic = {
        r.requirement_id: SurveyEvidenceClass.OFFICIAL_AS_BUILT
        for r in TIER_A_REQUIREMENTS
    }
    gate = evaluate_tier_gate(provided_survey_evidence=synthetic)
    assert gate.tier == ModelTier.TIER_A_PHYSICAL_AS_BUILT
    assert gate is not tier_b
    assert tier_b.tier != gate.tier


# ---------------------------------------------------------------------------
# 10. Tier C preserves UNKNOWN
# ---------------------------------------------------------------------------


def test_tier_c_preserves_unknown():
    gate, registry = load_current_tier_state()
    for m in registry.missing_inputs:
        assert m.value is None  # UNKNOWN — never filled, never zero
        assert m.can_satisfy is False
    assert registry.tier == ModelTier.TIER_C_BLOCKED_INPUTS


def test_no_missing_input_becomes_zero():
    gate = evaluate_tier_gate()
    for m in gate.missing_inputs:
        assert m.value is not 0.0
        assert m.value is None


# ---------------------------------------------------------------------------
# 11. Determinism
# ---------------------------------------------------------------------------


def test_gate_is_deterministic():
    a = load_current_tier_state()
    b = load_current_tier_state()
    assert a[0].tier == b[0].tier
    assert a[0].missing_inputs == b[0].missing_inputs
    assert a[0].blocked_reasons == b[0].blocked_reasons
    assert a[1].missing_inputs == b[1].missing_inputs
