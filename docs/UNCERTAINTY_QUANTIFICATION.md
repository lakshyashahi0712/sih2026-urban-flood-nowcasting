# Uncertainty Quantification

Decomposition per event (`uncertainty_results.csv`), all values from real
artifacts (never asserted):

| Source | Metric | EV-01 value (example) | Basis |
| --- | --- | --- | --- |
| FORCING | unknown-bin fraction | 0.500 | 2 of 4 documented bins UNKNOWN (catalog) |
| PARAMETER | peak-inflow spread across GLUE samples | 0.000 | closed-boundary scenario: inflow trajectory invariant to conveyance multipliers (honest null) |
| STRUCTURAL | spread across CONSERVATIVE/CENTRAL/DEGRADED_CAPACITY | 0.000 | same invariance; scenario spread is carried by the ensemble, not the inflow peak |
| SCENARIO_CATCHMENT | spread across 27.66/28.40 sq.km | 0.026 | two documented catchment areas moved the peak inflow by ~2.6% |
| OBSERVATION | local quantitative count | 0 | no Tier A/B local target; observation uncertainty unbounded (UNKNOWN) |

Ensembles/envelopes are never collapsed into a single authoritative
line; the operational UI shows the min/median/max envelope with member
counts. Structural uncertainty is additionally carried by the 6-member
deterministic ensemble across all operational surfaces.
