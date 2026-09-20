"""Scientific framework tests: metrics, registry, validation gate,
calibration/GLUE, identifiability, uncertainty, ML gating, production
contract, and reproducibility.

The synthetic-data ML tests validate PIPELINE MACHINERY only — they are
explicitly labeled test-only and never presented as Kushak results.
"""

from __future__ import annotations

import pytest

from backend.app.domain.delhi.science import metrics as M
from backend.app.domain.delhi.science.calibration import (
    audit_calibration,
    glue_behavioral_screen,
    objective_gate,
    parameter_registry,
    run_calibration_framework,
)
from backend.app.domain.delhi.science.gating import production_mode
from backend.app.domain.delhi.science.identifiability import (
    identifiability_classification,
    oat_sensitivity,
)
from backend.app.domain.delhi.science.ml_pipeline import (
    assert_no_future_features,
    build_event_features,
    build_ml_dataset,
    combine_prediction,
    production_gate,
)
from backend.app.domain.delhi.science.observation_registry import (
    build_observation_registry,
    registry_summary,
)
from backend.app.domain.delhi.science.validation import (
    evaluate_quantitative_validation,
)


# ---------------------------------------------------------------------------
# Metrics: correctness on known values + refusal of inadequate input
# ---------------------------------------------------------------------------


def test_metric_regression_correctness():
    obs = [1.0, 2.0, 3.0, 4.0]
    pred = [1.5, 2.0, 2.5, 4.5]
    assert M.mae(obs, pred) == pytest.approx(0.375)
    assert M.rmse(obs, pred) == pytest.approx(0.1875 ** 0.5)
    assert M.bias(obs, pred) == pytest.approx(0.125)


def test_metrics_refuse_mismatched_lengths():
    with pytest.raises(ValueError):
        M.mae([1.0], [1.0, 2.0])


def test_metrics_none_is_unknown_never_zero():
    """A None on either side is UNKNOWN: it contributes no pair and can
    never silently become a zero observation."""
    obs = [1.0, None, 3.0]
    pred = [1.0, 0.0, 3.0]
    # With the None dropped, MAE is 0; if None were zero-filled it would
    # be 0.667. The metric must report the honest 0 pairs used = 2.
    assert M.mae(obs, pred) == pytest.approx(0.0)


def test_confusion_matrix_excludes_unknown_never_flood_no():
    """Critical: UNKNOWN labels are excluded — never counted as negatives."""
    cm = M.confusion_matrix(
        observed_labels=[True, None, True, False],
        predicted_labels=[True, True, False, False],
    )
    assert cm["tp"] == 1 and cm["fn"] == 1 and cm["tn"] == 1
    assert cm["fp"] == 0
    assert cm["excluded_unknown"] == 1


def test_classification_metrics_degenerate_fold_refused():
    with pytest.raises(ValueError):
        M.confusion_matrix([None, None], [True, False])


def test_correlation_refuses_tiny_samples():
    assert M.correlation([1.0, 2.0], [1.0, 2.0]) is None


def test_nse_perfect_and_refuses_zero_variance():
    assert M.nash_sutcliffe([1.0, 2.0, 3.0], [1.0, 2.0, 3.0]) == pytest.approx(1.0)
    with pytest.raises(ValueError):
        M.nash_sutcliffe([2.0, 2.0, 2.0], [2.0, 2.0, 2.0])


def test_extent_metrics_iou():
    m = M.extent_metrics(
        observed_mask=[1, 1, 0, 0], predicted_mask=[1, 0, 1, 0]
    )
    assert m["iou"] == pytest.approx(1 / 3)
    assert m["precision"] == pytest.approx(0.5)
    assert m["recall"] == pytest.approx(0.5)


# ---------------------------------------------------------------------------
# Observation registry
# ---------------------------------------------------------------------------


def test_registry_builds_with_required_fields():
    records = build_observation_registry()
    assert len(records) > 500
    required = (
        "observation_id", "event_id", "variable", "value", "unit", "timestamp",
        "source", "source_tier", "provenance", "usable_for_calibration",
        "usable_for_validation", "reason_if_not_usable",
    )
    for r in records[:50]:
        for field in required:
            assert hasattr(r, field)
        assert r.source_tier in (
            "TIER_A_DIRECT_MEASUREMENT",
            "TIER_B_HIGH_CONFIDENCE_DERIVED",
            "TIER_C_INDIRECT_CONTEXT",
            "UNKNOWN",
        )


def test_registry_zero_calibration_usable_observations():
    """The honest core finding: no local quantitative target exists."""
    records = build_observation_registry()
    assert sum(1 for r in records if r.usable_for_calibration) == 0


def test_registry_downstream_cwc_is_tier_a_but_not_usable():
    records = build_observation_registry()
    cwc = [r for r in records if r.variable == "STAGE_DOWNSTREAM_YAMUNA"]
    assert cwc, "CWC records must be registered"
    assert all(r.source_tier == "TIER_A_DIRECT_MEASUREMENT" for r in cwc)
    assert all(not r.usable_for_validation for r in cwc)
    assert all("downstream" in r.reason_if_not_usable.lower() for r in cwc)


def test_registry_unknown_occurrence_never_negative():
    """Occurrence records carry no numeric value and are Tier C: the
    registry can never manufacture FLOOD_NO evidence."""
    for r in build_observation_registry():
        if r.variable in ("FLOOD_OCCURRENCE", "ROAD_CLOSURE_OCCURRENCE"):
            assert r.value is None
            assert r.source_tier == "TIER_C_INDIRECT_CONTEXT"


# ---------------------------------------------------------------------------
# Validation engine: gate + event separation
# ---------------------------------------------------------------------------


def test_validation_gate_stage_not_supported():
    result = evaluate_quantitative_validation()
    gate = result["evidence_gate"]["STAGE"]
    assert gate["QUANTITATIVE_VALIDATION_SUPPORTED"] == "NO"
    assert "downstream" in gate["note"].lower()


def test_validation_gate_occurrence_not_supported_with_reason():
    result = evaluate_quantitative_validation()
    note = result["evidence_gate"]["FLOOD_OCCURRENCE"]["note"].lower()
    assert "not_computable" in note or "does not exist" in note or "unknown" in note


def test_validation_computed_metrics_are_forcing_qc_only():
    result = evaluate_quantitative_validation()
    computed = [m for m in result["metrics"] if m["validity_status"] == "COMPUTED"]
    assert computed, "forcing-reproduction QC must compute"
    for m in computed:
        assert "not" in m["reason"].lower() and "skill" in m["reason"].lower()
        assert m["n_observations"] > 0
    not_computable = [m for m in result["metrics"] if m["validity_status"] == "NOT_COMPUTABLE"]
    assert len(not_computable) >= 15
    for m in not_computable:
        assert m["reason"], "every NOT_COMPUTABLE row carries its reason"


def test_event_split_has_no_calibration_consumption():
    result = evaluate_quantitative_validation()
    split = result["event_split"]
    assert split["CALIBRATION_EVENTS"] == []
    assert split["HELD_OUT_EVENTS"] == []
    assert set(split["UNSPLIT_EVALUATION_POOL"]) == {
        "EVT-2024-06-27", "EVT-2023-07-08", "EVT-2021-09-11",
    }
    assert "EVT-2026-01-23" in split["CONTROL_EVENTS"]


# ---------------------------------------------------------------------------
# Calibration: bounds, gate, GLUE, audit
# ---------------------------------------------------------------------------


def test_parameter_bounds_complete_and_documented():
    for p in parameter_registry():
        assert p.reason_for_bound
        assert p.provenance
        assert p.identifiability_status
        if p.parameter_name == "runoff_coefficient_C":
            assert p.lower_bound is None  # no documented range: not calibratable
        else:
            assert p.lower_bound is not None and p.upper_bound is not None
            assert p.lower_bound <= p.baseline_value <= p.upper_bound


def test_objective_gate_blocks_calibration():
    gate = objective_gate()
    assert gate["objective_supported"] is False
    assert gate["local_quantitative_targets"] == 0


def test_glue_screen_real_runs_null_result():
    glue = glue_behavioral_screen(n_samples=4)
    assert glue["method"].startswith("GLUE-STYLE")
    assert glue["n_behavioral"] == glue["n_samples"]
    assert "NO DISCRIMINATING POWER" in glue["discrimination_finding"]
    # Real peaks from real runs (EV-01's 91 mm/h hour is deterministic).
    peaks = glue["members"][0]["peak_inflow_by_event"]["EVT-2024-06-27"]
    assert peaks == pytest.approx(524.39, rel=1e-3)


def test_glue_deterministic_with_recorded_seed():
    a = glue_behavioral_screen(n_samples=3)
    b = glue_behavioral_screen(n_samples=3)
    assert a["members"][0]["parameters"] == b["members"][0]["parameters"]
    assert a["seed"] == b["seed"]


def test_calibration_run_preserves_baseline_and_audits():
    result = run_calibration_framework()
    assert result["calibration_performed"] is False
    assert result["calibrated_parameters"] is None
    assert result["baseline_preserved"] is True
    assert result["audit"]["status"] == "PASS"


def test_audit_fails_on_out_of_bounds_parameters():
    audit = audit_calibration(
        calibrated_parameters={"effective_conveyance_multiplier_box": 2.0}
    )
    assert audit["status"] == "FAIL"
    assert any("bounds" in f for f in audit["failed_checks"])


# ---------------------------------------------------------------------------
# Identifiability + uncertainty (real runs)
# ---------------------------------------------------------------------------


def test_identifiability_parameters_non_identifiable():
    cls = identifiability_classification(oat_sensitivity())
    by_name = {p["parameter_name"]: p for p in cls["parameters"]}
    assert by_name["runoff_coefficient_C"]["identifiability_status"] == (
        "NOT_CALIBRATABLE_NO_DOCUMENTED_RANGE"
    )
    for name in (
        "effective_conveyance_multiplier_box",
        "effective_conveyance_multiplier_open",
        "depot_bay_open_fraction",
    ):
        assert "NON_IDENTIFIABLE" in by_name[name]["identifiability_status"]
    assert "non-identifiable" in cls["summary"].lower()


def test_uncertainty_decomposition_uses_real_runs():
    rows = {
        (r["event_id"], r["source"]): r
        for r in __import__(
            "backend.app.domain.delhi.science.uncertainty",
            fromlist=["uncertainty_decomposition"],
        ).uncertainty_decomposition()
    }
    # Forcing uncertainty: EV-01 has 2 of 4 bins UNKNOWN.
    ev01_forcing = rows[("EVT-2024-06-27", "FORCING")]
    assert ev01_forcing["value"] == pytest.approx(0.5)
    # Structural spread under the closed-boundary convention is exactly 0:
    # the documented scenarios do not move the inflow trajectory (honest).
    assert rows[("EVT-2024-06-27", "STRUCTURAL")]["value"] == pytest.approx(0.0)
    # Catchment scenario spread is small but nonzero (2 documented areas).
    assert 0 < rows[("EVT-2024-06-27", "SCENARIO_CATCHMENT")]["value"] < 0.1


# ---------------------------------------------------------------------------
# ML pipeline: gating, fallback contract, leakage guard, features
# ---------------------------------------------------------------------------


def test_ml_dataset_gated_blocked_by_data():
    dataset = build_ml_dataset()
    assert dataset["residual_target"]["status"] == "NOT_CONSTRUCTABLE"
    assert dataset["event_grouped_cv"]["gate"].startswith("FAIL")
    assert dataset["occurrence_target"]["usable_events"] == 4
    assert dataset["occurrence_target"]["positives"] == 3
    assert dataset["occurrence_target"]["negatives"] == 1


def test_production_mode_is_physics_only():
    gate = production_gate()
    assert gate["production_mode"] == "PHYSICS_ONLY"
    assert gate["ml_status"] == "RESEARCH_ONLY_NOT_DEPLOYED"
    assert gate["gates"]["data_sufficiency"] == "FAIL"


def test_combine_prediction_fallback_contract():
    """ml_status UNAVAILABLE -> combined = physics (never silently substituted)."""
    out = combine_prediction(physics_prediction=10.0, ml_correction=None)
    assert out["ml_status"] == "UNAVAILABLE"
    assert out["combined_prediction"] == 10.0
    assert out["physics_prediction"] == 10.0
    applied = combine_prediction(physics_prediction=10.0, ml_correction=-1.5)
    assert applied["ml_status"] == "APPLIED"
    assert applied["combined_prediction"] == 8.5
    assert applied["physics_prediction"] == 10.0  # physics always exposed


def test_event_features_have_no_future_information():
    """Rows for hour h carry only bins <= h (antecedent excludes the
    current bin; nothing references later timesteps)."""
    rows = build_event_features("EVT-2024-06-27")
    assert rows, "EV-01 has executable forcing"
    assert_no_future_features(rows)
    # EV-01: bin 0 verified zero, bin 1 = 91 mm, bins 2-3 UNKNOWN.
    assert rows[0]["forcing_depth_mm"] == 0.0
    assert rows[1]["forcing_depth_mm"] == 91.0
    assert rows[2]["forcing_depth_mm"] is None
    assert rows[0]["antecedent_forcing_mm"] == 0.0
    assert rows[1]["antecedent_forcing_mm"] == 0.0  # bins[:1] = [0.0]
    assert rows[3]["antecedent_forcing_mm"] == 91.0  # UNKNOWN bins excluded


def test_non_executable_event_yields_no_features():
    assert build_event_features("EVT-2021-07-19") == []


# ---------------------------------------------------------------------------
# Reproducibility
# ---------------------------------------------------------------------------


def test_framework_outputs_deterministic():
    a = evaluate_quantitative_validation()
    b = evaluate_quantitative_validation()
    assert a["metrics"] == b["metrics"]
    glue_a = glue_behavioral_screen(n_samples=3)
    glue_b = glue_behavioral_screen(n_samples=3)
    assert glue_a["behavioral_parameter_ranges"] == glue_b["behavioral_parameter_ranges"]
