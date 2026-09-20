# Physics-Guided ML Method

## Design

ML is an optional augmentation layer; the physics digital twin remains
the authoritative, independently-runnable model.

    RAIN/FORCING -> PHYSICS HYDROLOGY -> HYDRAULIC TWIN -> ENSEMBLE
        -> [ML AUGMENTOR: residual / occurrence probability] -> PRODUCT
    (ml unavailable -> combined = physics; ml_status = UNAVAILABLE)

Implemented strategies: **MODEL_RESIDUAL_LEARNING** (predicts
`observed − physics`) and event-level **flood-occurrence probability**.
The physics prediction is always exposed (`physics_prediction` field),
and `combine_prediction()` returns physics-only when no ML correction is
validated.

## Features (causality guarded)

Per-timestep: `forcing_depth_mm`, `antecedent_forcing_mm`,
`model_inflow_m3_s`. `assert_no_future_features()` enforces that hour-h
rows use only bins ≤ h; the runtime is step-causal by contract.

## Dataset reality (the honest gate)

- Residual target: **NOT_CONSTRUCTABLE** — the observation registry holds
  no local quantitative observation to difference against the physics
  prediction.
- Occurrence target: 4 usable events (3 FLOOD_YES, 1 control; UNKNOWN
  label events excluded, never converted to negatives).
- Event-grouped CV (leave-one-event-out): **FAIL** — LOEO requires ≥ 2
  events per class so every training fold retains both classes; with
  3/1 the fold holding the single negative would train on one class.
  The single negative is also the reserved control event.

## Gating

`production_gate()` → `production_mode = PHYSICS_ONLY`,
`ml_status = RESEARCH_ONLY_NOT_DEPLOYED`. The complete pipeline
(features, targets, event-grouped evaluation machinery, metrics,
registry, fallback contract) is implemented and exercised in tests with
**explicitly-labeled synthetic data** — machinery validation only, never
presented as a Kushak result. A model becomes production-eligible only
after data sufficiency, event separation, validation, leakage checks,
reproducibility, and the calibration audit all PASS.
