# FINAL MODEL READINESS MATRIX

Generated `2026-09-17` from the executable framework
(`python scripts/run_scientific_evaluation.py`). Statuses follow the
mandate vocabulary: IMPLEMENTED != COMPUTED != VALIDATED != CALIBRATED !=
ML-TRAINED != DEPLOYED.

| Capability | Evidence Available | Implemented | Computed | Validated | Production Eligible | Limitation |
| --- | --- | --- | --- | --- | --- | --- |
| Physics baseline | Yes (documented forcing + evidence) | Yes (operational runtime) | Yes | No (no quantitative targets) | Yes | no stage/depth; occurrence-consistent only |
| Quantitative validation framework | Partial (rainfall A/B; no local hydraulic) | Yes | Forcing QC only | No | Yes (as QC) | stage/discharge/extent metrics NOT_COMPUTABLE |
| Calibration framework | No local targets | Yes | No (gated) | No | No | objective_supported = NO |
| GLUE behavioral screen | Occurrence-only | Yes | Yes (null result) | No | No | no discriminating power; equifinality |
| Identifiability | Documented bounds + occurrence | Yes | Yes | n/a | n/a | multipliers inert; C no range |
| Uncertainty framework | Real forcing/model artifacts | Yes | Yes | n/a | Yes | observation term unbounded (UNKNOWN) |
| Physics-guided ML | Insufficient (3 pos / 1 neg events; no residual target) | Yes | No | No | No | BLOCKED_BY_DATA; NOT_DEPLOYED |
| Production mode | - | - | - | - | **PHYSICS_ONLY** | ML gated; no fabricated enhancements |
