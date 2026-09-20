# Calibration Method

## Position

No calibration is performed: the objective gate found **zero** local
Tier A/B quantitative targets (stage/discharge/depth/extent) for Kushak.
"Calibrated" is therefore never used for any parameter. The framework is
complete and would run unchanged the moment a defensible observation
target exists.

## Parameter registry (with documented bounds)

| Parameter | Baseline | Bounds | Provenance |
| --- | --- | --- | --- |
| effective_conveyance_multiplier_box | 0.862 | [0.800, 0.923] | Phase 7D16 sampled ranges (INFERRED_EFFECTIVE) |
| effective_conveyance_multiplier_open | 0.804 | [0.714, 0.893] | Phase 7D16 sampled ranges |
| depot_bay_open_fraction | 0.700 | [0.400, 1.000] | 7D16 ranges; DEGRADED anchored to NGT JIR 05-03-2025 (2 of 5 bays) |
| runoff_coefficient_C | 0.750 | **none documented** | the only documented ASSUMED value; inventing bounds would be fabrication → NOT_CALIBRATABLE |

## Objective

Composable (stage/discharge/extent/occurrence/peak-timing/volume terms);
weights are ASSUMED until empirically justified. Currently
`objective_supported = NO` → no optimization, baseline (CENTRAL scenario)
preserved, `baseline_score / calibrated_score / improvement = None`.

## GLUE-style behavioral screen (executed on REAL runs)

- 10 deterministic LHS samples within the documented bounds (seed
  20260917, recorded).
- Each sample runs the genuine runtime against EV-01/EV-02/EV-03 forcing
  (verified peaks: 524.4 / 86.4 / 153.7 m³/s).
- Behavioral criterion: positive modeled corridor loading during
  documented FLOOD_YES events.
- Result: **all 10 samples behavioral → NO DISCRIMINATING POWER.
  Behavioral space equals the sampled prior. Equifinality preserved —
  no posterior skill, no uncertainty reduction, no calibrated value.**
- Explicitly GLUE-STYLE, not Bayesian (no likelihood, no posterior).

## Anti-overfitting audit (fails loudly)

Bounds respected, event separation, no future data (step-causal runtime),
seeds recorded, observation provenance preserved, reproducibility —
all verified by `audit_calibration()`; any FAIL raises instead of
continuing.
