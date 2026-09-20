# FINAL SCIENTIFIC MODEL PERFORMANCE REPORT

**FINAL_STATUS: COMPLETE_WITH_DOCUMENTED_DATA_LIMITATIONS** — every
capability that the available evidence can support is implemented,
computed, and verified; every capability the evidence cannot support is
implemented as a complete, future-proof framework and honestly reported
NOT_COMPUTABLE / BLOCKED_BY_DATA. The physics-only operational system is
unchanged and production-ready.

## 1. Baseline physics performance

Deterministic 6-member ensemble through the canonical runtime
(rainfall -> runoff -> hydraulic chain -> state classification -> event-
separated validation). Mass-balance closure verified on every computed
reach-step (residual == continuity dV/dt). This is implementation
correctness, never claimed as real-world accuracy.

## 2. Calibration methodology

Bounded, deterministic, event-separated framework over the Phase 7D16
documented parameter ranges; objective composable (stage/discharge/
extent/occurrence/timing/volume); GLUE-style behavioral screen executed
on genuine runs (seed 20260917). Objective gate: NOT COMPUTABLE (no
local quantitative target) -> **NO calibration performed**; baseline
(CENTRAL) preserved; anti-overfitting audit PASS.

## 3. Calibrated parameter ranges

None. Calibrated_parameters = None. See 4.

## 4. Identifiability

All three conveyance multipliers: NON_IDENTIFIABLE — their influence
channel (Manning capacity echo) is not computed under current contracts
(stage UNKNOWN), so they are inert in the runtime; occurrence-only
evidence additionally gives the GLUE screen zero discriminating power.
C: NOT_CALIBRATABLE (no documented range). No parameter value is
reported as calibrated.

## 5. Event split

CALIBRATION/HELD_OUT/TRAIN: none (nothing consumed). Evaluation pool:
EVT-2024-06-27, EVT-2023-07-08, EVT-2021-09-11 (unsplit). Control:
EVT-2026-01-23 (reserved). Missing-forcing: EVT-2021-07-19,
EVT-2023-05-27 (non-executable).

## 6-7. Quantitative + held-out metrics

Computed: forcing-reproduction MAE/RMSE/bias per event (data-consistency
QC, not skill). NOT_COMPUTABLE with reasons: all stage/discharge/extent/
occurrence families (23 metric rows). No held-out metrics exist because
no model was trained or calibrated.

## 8. Uncertainty

Per-event decomposition (forcing 0.5 unknown-fraction for EV-01,
parameter/structural 0.0 — honest null of the closed-boundary scenario,
catchment-scenario 0.026). Observation uncertainty unbounded (UNKNOWN).
Envelopes never collapsed.

## 9-12. ML methodology / dataset / event split / performance

Residual + occurrence-probability augmentation; strictly physics-guided.
Dataset: residual target NOT_CONSTRUCTABLE; occurrence labels 3 pos /
1 neg (UNKNOWN-label events excluded). Event-grouped LOEO gate FAIL
(>=2 events/class required for non-degenerate training folds). No ML
performance reported. Pipeline validated on explicitly-labeled synthetic
fixtures (machinery only).

## 13. Physics-vs-ML comparison

Not applicable (ML not trained). Physics-only is the product; the
fallback contract (ml unavailable -> combined = physics) is tested.

## 14. Leakage audit

assert_no_future_features in force; LOEO only; seeds recorded; step-
causal runtime by contract; no feature uses future bins/events; the
single negative event is also the reserved control, so ML cannot
consume it.

## 15. Production gating decision

production_mode = PHYSICS_ONLY; ml_status = RESEARCH_ONLY_NOT_DEPLOYED;
no ML/calibrated component may influence operational nowcast, replay, or
routing (surfaced in /status and safe-route provenance as
PHYSICS_ONLY).

## 16-17. Safe-routing + replay impact

Routing consumes physics risk only (model_mode = PHYSICS_ONLY in every
route provenance). Replay unchanged; events remain evaluation pool /
control / non-executable as declared.

## 18. Limitations

No local stage/discharge/depth/extent observations; occurrence-only
evidence cannot discriminate parameters (equifinality); conveyance
multipliers inert under current contracts; C has no documented range;
ML datasets insufficient.

## 19. Unavailable measurements

Local Kushak stage, discharge, depth, surveyed extent: absent. Monthly
or event CWC downstream context exists but is non-local. Sub-hour
rainfall resolution: absent (3-hourly blocks only; never disaggregated).

## 20. Exact reproducibility commands

```
python scripts/run_scientific_evaluation.py     # all CSVs + registry
python -m pytest backend/tests/test_scientific_framework.py -q
python -m pytest backend/app/domain/delhi backend/tests -q   # full suite
```
