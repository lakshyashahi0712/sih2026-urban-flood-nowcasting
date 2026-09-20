# Scientific Performance Report (summary)

Full detail: `docs/FINAL_SCIENTIFIC_MODEL_PERFORMANCE_REPORT.md` and
`docs/FINAL_MODEL_READINESS_MATRIX.md`.

- **Physics baseline**: operational and preserved; deterministic
  6-member ensemble; mass-balance closure verified (implementation
  correctness - never claimed as real-world accuracy).
- **Quantitative validation**: framework complete; computed rows are
  forcing-reproduction QC only; stage/discharge/extent/occurrence
  metrics are NOT_COMPUTABLE with documented reasons.
- **Calibration**: gated OFF (no local quantitative target); GLUE screen
  executed on real runs and honestly reports NO DISCRIMINATING POWER
  (equifinality).
- **Identifiability**: conveyance multipliers inert/non-identifiable
  under current contracts; C non-calibratable (no documented range).
- **Uncertainty**: forcing/parameter/structural/scenario/observation
  decomposition computed from real runs.
- **ML**: pipeline implemented and tested (synthetic fixtures only);
  real-data status BLOCKED_BY_DATA; production_mode = PHYSICS_ONLY.
