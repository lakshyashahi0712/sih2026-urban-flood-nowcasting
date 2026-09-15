"""Phase 8B Step-2 tests: reach-resolved effective profiles + ledger.

Representation-only tests — no routing exists. Provenance rules asserted
strictly: effective profiles are never surveyed/as-built, UG-01 stays
hydraulically blocked, UNKNOWN stays UNKNOWN, and no generic OFFICIAL
provenance can promote a reach to Tier A.
"""

import pytest

from .kushak_evidence_model import (
    KUSHAK_HYDRAULIC_SCENARIOS,
    NIT52_PROCUREMENT,
)
from .kushak_reaches_tiered import (
    KUSHAK_MODEL_REACHES,
    REACH_PROFILE_REFERENCES,
    LedgerEntry,
    KushakModelReach,
    ReachType,
    build_provenance_ledger,
    build_reach_effective_profile,
    validate_reach_ordering,
)
from .kushak_tiered_model import ModelTier, SurveyEvidenceClass, evaluate_tier_gate
from .hydraulic_geometry import profile_provenance
from .models import ProvenanceStatus


CENTRAL = KUSHAK_HYDRAULIC_SCENARIOS["CENTRAL"]


# ---------------------------------------------------------------------------
# 1. All four reaches exist in deterministic order
# ---------------------------------------------------------------------------


def test_four_reaches_in_deterministic_order():
    assert [r.reach_id for r in KUSHAK_MODEL_REACHES] == [
        "UG-01", "OC-01", "CD-01", "OC-02"
    ]


def test_reach_chainages_valid_and_contiguous():
    for r in KUSHAK_MODEL_REACHES:
        assert r.end_chainage_m > r.start_chainage_m >= 0.0
    # No silent overlaps/gaps: contiguous corridor, upstream -> downstream.
    validate_reach_ordering()  # raises on violation
    assert KUSHAK_MODEL_REACHES[0].start_chainage_m == 0.0
    assert KUSHAK_MODEL_REACHES[-1].end_chainage_m == pytest.approx(5027.56)


def test_reach_ordering_validator_rejects_gap():
    gapped = (
        KUSHAK_MODEL_REACHES[0],
        KushakModelReach(
            reach_id="OC-01",
            start_chainage_m=KUSHAK_MODEL_REACHES[0].end_chainage_m + 10.0,
            end_chainage_m=3700.0,
            reach_type=ReachType.OPEN,
            label="gapped",
            tier=ModelTier.TIER_B_EFFECTIVE_SCENARIO,
            provenance=ProvenanceStatus.OFFICIAL_MODEL_VALUE,
            hydraulic_status="RUNNABLE_AS_SCENARIO_EFFECTIVE_PROFILE",
        ),
    )
    with pytest.raises(ValueError, match="ordering violation"):
        validate_reach_ordering(gapped)


def test_reach_rejects_non_finite_and_reversed_chainages():
    with pytest.raises(ValueError, match="finite"):
        KushakModelReach(
            reach_id="X", start_chainage_m=float("nan"), end_chainage_m=10.0,
            reach_type=ReachType.OPEN, label="x",
            tier=ModelTier.TIER_B_EFFECTIVE_SCENARIO,
            provenance=ProvenanceStatus.OFFICIAL_MODEL_VALUE,
            hydraulic_status="RUNNABLE_AS_SCENARIO_EFFECTIVE_PROFILE",
        )
    with pytest.raises(ValueError, match="exceed"):
        KushakModelReach(
            reach_id="X", start_chainage_m=10.0, end_chainage_m=10.0,
            reach_type=ReachType.OPEN, label="x",
            tier=ModelTier.TIER_B_EFFECTIVE_SCENARIO,
            provenance=ProvenanceStatus.OFFICIAL_MODEL_VALUE,
            hydraulic_status="RUNNABLE_AS_SCENARIO_EFFECTIVE_PROFILE",
        )


# ---------------------------------------------------------------------------
# 2. Effective profiles are explicitly non-surveyed (Tier-B only)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("reach_id", ["OC-01", "CD-01", "OC-02"])
def test_reach_effective_profiles_explicitly_non_surveyed(reach_id):
    profile, meta = build_reach_effective_profile(reach_id, CENTRAL)
    assert meta["is_surveyed"] is False
    assert meta["is_as_built"] is False
    assert meta["tier"] == ModelTier.TIER_B_EFFECTIVE_SCENARIO.value
    assert "INFERRED_EFFECTIVE" in meta["profile_reference"]
    assert "NOT_SURVEYED" in meta["profile_reference"]
    assert meta["profile_reference"] == REACH_PROFILE_REFERENCES[reach_id]
    # Aggregate profile provenance stays below survey grade.
    assert profile_provenance(profile) is ProvenanceStatus.ASSUMED


def test_ug01_profile_cannot_be_built():
    with pytest.raises(ValueError, match="UNKNOWN"):
        build_reach_effective_profile("UG-01", CENTRAL)


def test_ug01_remains_hydraulically_blocked():
    ug01 = KUSHAK_MODEL_REACHES[0]
    assert ug01.reach_id == "UG-01"
    assert ug01.hydraulic_status == "HYDRAULICALLY_BLOCKED_PHYSICAL_GEOMETRY_UNKNOWN"
    assert ug01.profile_reference is None


# ---------------------------------------------------------------------------
# 3. Tier A cannot be inferred from effective profiles
# ---------------------------------------------------------------------------


def test_tier_a_cannot_be_inferred_from_effective_profiles():
    # Even with every reach profile built, the Tier-A gate sees no survey
    # evidence: effective/ASSUMED geometry can never promote to Tier A.
    for reach_id in ("OC-01", "CD-01", "OC-02"):
        _, meta = build_reach_effective_profile(reach_id, CENTRAL)
        gate = evaluate_tier_gate(provided_survey_evidence={})
        assert gate.tier == ModelTier.TIER_C_BLOCKED_INPUTS
        assert gate.can_promote_to_tier_a is False
        assert meta["is_surveyed"] is False


def test_no_generic_official_provenance_promotes_reach_to_tier_a():
    # A full generic-OFFICIAL claim across all requirements leaves Tier A
    # blocked — only explicit SurveyEvidenceClass can open it.
    from .kushak_tiered_model import TIER_A_REQUIREMENTS

    generic_official = {
        r.requirement_id: ProvenanceStatus.OFFICIAL
        for r in TIER_A_REQUIREMENTS
    }
    gate = evaluate_tier_gate(provided_evidence=generic_official)
    assert gate.tier == ModelTier.TIER_C_BLOCKED_INPUTS
    assert gate.can_promote_to_tier_a is False


def test_current_real_model_remains_tier_c():
    from .kushak_tiered_model import load_current_tier_state

    gate, _ = load_current_tier_state()
    assert gate.tier == ModelTier.TIER_C_BLOCKED_INPUTS
    assert gate.can_promote_to_tier_a is False
    # All Tier-B reach profiles are still explicitly effective-scenario.
    for r in KUSHAK_MODEL_REACHES:
        if r.profile_reference is not None:
            assert r.tier == ModelTier.TIER_B_EFFECTIVE_SCENARIO


# ---------------------------------------------------------------------------
# 4. UNKNOWN physical geometry remains UNKNOWN
# ---------------------------------------------------------------------------


def test_unknown_ug01_geometry_stays_unknown():
    ledger = build_provenance_ledger()
    entry = next(
        e for e in ledger
        if e.reach_id == "UG-01" and e.quantity == "internal_barrel_geometry"
    )
    assert entry.value is None  # UNKNOWN — never filled
    assert entry.provenance_class == ProvenanceStatus.UNKNOWN.value
    assert entry.tier == ModelTier.TIER_C_BLOCKED_INPUTS.value
    assert "BLOCKED" in entry.status


def test_unknown_downstream_boundary_stays_unknown():
    ledger = build_provenance_ledger()
    entry = next(
        e for e in ledger
        if e.quantity == "downstream_boundary_stage"
    )
    assert entry.value is None
    assert entry.provenance_class == ProvenanceStatus.UNKNOWN.value
    assert "BLOCKED" in entry.status


# ---------------------------------------------------------------------------
# 5. Provenance ledger is complete for required quantities
# ---------------------------------------------------------------------------


def test_ledger_is_deterministic_and_complete():
    a = build_provenance_ledger()
    b = build_provenance_ledger()
    assert a == b  # deterministic
    quantities = {(e.reach_id, e.quantity) for e in a}
    # Required minimum coverage:
    assert ("UG-01", "dmp_longitudinal_backbone_invert") in quantities
    assert ("CD-01", "structural_bounds") in quantities
    assert ("CD-01", "covered_barrel_size_class") in quantities
    assert ("OC-01", "effective_manning_multiplier") in quantities
    assert ("CORRIDOR", "catchment_area") in quantities
    assert ("UG-01", "internal_barrel_geometry") in quantities
    assert ("OC-02", "downstream_boundary_stage") in quantities
    for e in a:
        assert isinstance(e, LedgerEntry)
        assert e.source  # no fabricated citations: every entry carries a source
        assert e.note


def test_ledger_distinguishes_evidence_classes():
    ledger = build_provenance_ledger()
    by_key = {(e.reach_id, e.quantity): e for e in ledger}
    assert by_key[("UG-01", "dmp_longitudinal_backbone_invert")].provenance_class == \
        ProvenanceStatus.OFFICIAL_MODEL_VALUE.value
    assert "OBSERVED/OFFICIAL" in by_key[("CD-01", "structural_bounds")].provenance_class
    assert by_key[("CD-01", "covered_barrel_size_class")].provenance_class == \
        "PROCUREMENT_SPECIFICATION"
    assert "INFERRED_EFFECTIVE" in by_key[("OC-01", "effective_manning_multiplier")].provenance_class
    assert by_key[("CORRIDOR", "catchment_area")].provenance_class == "DERIVED/PROVISIONAL"


def test_catchment_note_preserves_historical_unknown():
    ledger = build_provenance_ledger()
    entry = next(e for e in ledger if e.quantity == "catchment_area")
    assert "UNKNOWN" in entry.note


# ---------------------------------------------------------------------------
# 6. NIT52 remains procurement specification only
# ---------------------------------------------------------------------------


def test_nit52_untouched_and_spec_only():
    assert NIT52_PROCUREMENT["spec_class"] == "PROCUREMENT_SPECIFICATION"
    entry = next(
        e for e in build_provenance_ledger()
        if e.quantity == "covered_barrel_size_class"
    )
    assert entry.provenance_class == "PROCUREMENT_SPECIFICATION"
    assert "NOT measured" in entry.note or "NOT measured/as-built" in entry.note
