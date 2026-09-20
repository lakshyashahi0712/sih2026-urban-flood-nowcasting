# Phase 15.5 — Genuine Event-Specific Historical Runtime Replay (Delhi / Kushak V2)

**Document ID:** `DELHI_KUSHAK_PHASE15_5_TRUE_RUNTIME_REPLAY`
**Date:** 2026-09-16
**Mode:** IMPLEMENTATION (replay-harness orchestration layer ONLY)
**Constraint compliance:** No hydraulic physics change, no routing change, no scenario-parameter change, no catchment/geometry change, no rainfall-methodology change, no GLUE, no calibration, no ML, no UI change, no model API change.
**Files modified:**
- `scripts/generate_phase15_replay.py` (rewritten as the genuine event-specific replay harness)
- `backend/app/domain/delhi/digital_twin/test_phase15_2_execution_integrity.py` (directly associated test file: 4 Phase 15.2 tests preserved + 11 Phase 15.5 tests added)

**Artifacts regenerated:**
- `data/delhi/derived/validation/kushak_phase15_historical_replay.csv` (canonical replay ledger, now runtime-derived; schema superseded from the Phase 15.0 manual-ledger layout to the runtime-lineage layout below)
- `data/delhi/derived/validation/kushak_phase15_5_system_flags.csv` (new: system-flag ledger)

---

## 1. Executive Summary & Verdict

Phase 15.4 (`DELHI_KUSHAK_PHASE15_4_API_FEASIBILITY`) concluded that the existing canonical runtime APIs fully support genuine historical replay and that the only blocker was the replay harness itself, which used a smoke-test/manual-ledger approach. Phase 15.5 implements the fix.

**What changed:** `scripts/generate_phase15_replay.py` now executes, for each executable historical event, the actual documented forcing profile through the existing canonical runtime path — `run_integrated_simulation()` (the exact Phase 15.4 historical-forcing injection point: `rainfall_to_inflow()` → `InflowHydrograph` → `run_hydrograph_simulation()`), then the existing Phase 8B multi-timestep chain `advance_chain_series()` with the event's forcing sequence as the timestep loop, the existing Phase 8B Step-8 classification, and the existing Phase 8B Step-9 `validate_observation()` — for all 6 deterministic `build_kushak_ensemble()` members. Every runtime-derived value in the replay record is composed from the runtime objects of that event's own executions; counters increment at the actual call sites.

**Executable totals (scientifically correct, no overclaim):**
- EV-01 (`EVT-2024-06-27`): **6** ensemble members executed.
- EV-02 (`EVT-2023-07-08`): **6** ensemble members executed.
- **Total genuine member executions: 12** across the two executable events. Not 36 — the other four events have no executable documented forcing and are NOT simulated. Not a shared smoke test — the events ran on their own windows, forcings, and counters.
- The other four events execute **0** members: `EVT-2021-09-11` stays `NOT_COMPARABLE` (3-hourly blocks + daily total only; hourly disaggregation not justified and not synthesized), `EVT-2021-07-19`/`EVT-2023-05-27` stay `UNKNOWN` (`BLOCKED_MISSING_FORCING`; zero rainfall never created), and `EVT-2026-01-23` keeps its control-event classification (absent forcing never converted into a runtime simulation).

**What is NOT claimed (explicit):**
- **No historical validation accuracy.** `validate_observation()` returns `UNKNOWN` for every executed member (no coordinates are invented, so the spatial match stays UNKNOWN and the occurrence/state comparison is not attempted). No accuracy rate is computed anywhere.
- **No calibration.** The ensemble is the unchanged deterministic `build_kushak_ensemble()` (C = 0.75 ASSUMED; catchments 27.66/28.40 km² PROVISIONAL; hydraulic scenarios CONSERVATIVE/CENTRAL/DEGRADED_CAPACITY).
- **No RMSE, depth skill, rating-curve error, or any quantitative skill metric.** The runtime has no Kushak stage/discharge observations and no storage-stage relation; only occurrence/state compatibility exists, and it was not attempted (no spatial match).
- **No Tier-A promotion.** All computed states are DERIVED scenario outputs.

### Final Verdict: **PASS**

All nine required system flags hold (Section 5); all focused and full-suite tests pass (Section 7); the Phase 15.1 forensic audit and Phase 15.2 runtime-lineage audit were re-run against the new state with all checks passing (Section 6).

---

## 2. Implementation Architecture (as executed)

Each stage is an EXISTING, unmodified runtime API; the harness (`scripts/generate_phase15_replay.py`) contains only adapter/orchestration logic.

```
historical event (Phase 14A catalogue, EVT-*)
  → resolve_event_id()                    kushak_event_validation (existing EVENT_ID_MAP bridge)
  → get_forcing_for_event()               kushak_historical_rainfall_catalog (existing)
     RainfallForcingProfile               Phase 11 Step 1/2 schema
  → forcing adapter (harness)             bins → timesteps + depths; bin intervals preserved
     EventForcingSeries                   exactly from the catalog's own documented
                                          resolution (a documented "3-hour ... not hourly
                                          split" increment stays ONE 3-hour timestep;
                                          UNKNOWN bins stay None; NO disaggregation,
                                          zero-fill, or interpolation)
  → run_integrated_simulation()           hydraulic_integrated_orchestrator (existing;
     ├─ rainfall_to_inflow()              the exact Phase 15.4 injection point), per
     │   → InflowHydrograph (DERIVED)     ensemble member with that member's scenario /
     └─ run_hydrograph_simulation()       catchment / C and the event forcing; conventions
        (Phase 7D-12, stop-on-first-      mirrored verbatim from the existing
         block contract)                  run_kushak_evidence_scenario() body
  → advance_chain_series()                kushak_continuity_routing (existing Phase 8B
     ChainSeriesResult                    Step-5): one ChainStepSpec PER FORCING BIN with
                                          head flow = that bin's hydrograph discharge;
                                          the event's forcing sequence IS the timestep
                                          loop; UNKNOWN bins execute as blocked states
                                          (no early stop)
  → classify_chain_timestep()             kushak_hydraulic_state_classification (existing
                                          Phase 8B Step-8)
  → validate_observation()                kushak_event_validation (existing Phase 8B
     ValidationRecord                     Step-9), one call per executed member
  → runtime-derived ReplayEventRecord     composed ONLY from runtime objects + call-site
     + CSV + system flags                 counters of THIS event's executions
```

**Why `run_integrated_simulation()` and not `execute_ensemble_member()`:** Phase 15.4 established that `execute_ensemble_member()` cannot accept event forcing (its forcing is implicitly the hardcoded June 2024 evidence scenario). Its canonical engine is `run_kushak_evidence_scenario()` → `run_integrated_simulation()`. The harness drives `run_integrated_simulation()` directly with the member's scenario/catchment/C and the event forcing, mirroring the existing 8A conventions verbatim (covered effective profile builder, DERIVED backbone slope, initial state bed+1.0 m / 10000 m³ DERIVED, explicit zero-outflow closed boundary ASSUMED, zero lateral inflow ASSUMED, area PROVISIONAL, C ASSUMED). A dedicated test proves the harness member execution is equivalent to `run_kushak_evidence_scenario(forcing=event_series)` (same conversion, same hydrograph, same states).

**Chain boundary condition (existing assumption, not a new one):** the chain uses the SAME explicit zero-outflow closed-boundary scenario assumption as the existing Phase 8A evidence scenario (`explicit_outflow_m3_s=0.0`, ASSUMED provenance), carried through the locked Step-3 transfer contract with the mandatory explicit Tier-B declaration for UG-01 and no decision for the terminal OC-02 (whose continuity therefore stays blocked — no Yamuna/free-outfall assumption). The forced inflow that cannot leave accumulates as storage via the continuity equation; the Step-4 accounting layer independently flags those reach-steps IMBALANCED, and the harness's mass-balance check cross-verifies that the accounting residual equals the continuity storage rate dV/dt exactly on every computed reach-step (closure of the two locked layers, max |err| = 0.0 m³/s).

**Model state discipline:** no initial stage is supplied to the chain and no storage-stage relation is invented (the coupling registry is deliberately empty), so every classification is UNKNOWN — the honest model state. Stage is never inferred from storage, discharge, capacity, or forcing.

---

## 3. Required Event Matrix

`ACTUAL_MEMBER_IDS` (identical for both executable events, canonical `build_kushak_ensemble()` order):
`KUSHAK-CONSERVATIVE-WORKING_27_66; KUSHAK-CONSERVATIVE-SENSITIVITY_28_40; KUSHAK-CENTRAL-WORKING_27_66; KUSHAK-CENTRAL-SENSITIVITY_28_40; KUSHAK-DEGRADED_CAPACITY-WORKING_27_66; KUSHAK-DEGRADED_CAPACITY-SENSITIVITY_28_40`

| Field | EVT-2024-06-27 | EVT-2023-07-08 | EVT-2021-09-11 | EVT-2026-01-23 | EVT-2021-07-19 | EVT-2023-05-27 |
|---|---|---|---|---|---|---|
| **EVENT_ID** | EVT-2024-06-27 | EVT-2023-07-08 | EVT-2021-09-11 | EVT-2026-01-23 | EVT-2021-07-19 | EVT-2023-05-27 |
| **RESOLVED_EVENT_ID** | EV-01 | EV-02 | EVT-2021-09-11 (pass-through) | EVT-2026-01-23 | EVT-2021-07-19 | EVT-2023-05-27 |
| **FORCING_FOUND** | YES | YES | NO | NO | NO | NO |
| **FORCING_TIME_BINS** | 4 bins (t+0h=0.0mm VERIFIED_ZERO; t+1h=91.0mm/h OBSERVED_DIRECT; t+2h UNKNOWN; t+3h UNKNOWN) | 4 bins (t+0h=0.0mm VERIFIED_ZERO; t+1h=45.0mm DERIVED [documented 3-hour increment]; t+2h UNKNOWN; t+3h UNKNOWN) | 0 (no executable profile in catalog) | 0 | 0 | 0 |
| **RUNTIME_EXECUTED** | YES | YES | NO | NO | NO | NO |
| **ENSEMBLE_MEMBERS_EXECUTED** | 6 | 6 | 0 | 0 | 0 | 0 |
| **ACTUAL_MEMBER_IDS** | 6 canonical IDs (above) | 6 canonical IDs (above) | NONE | NONE | NONE | NONE |
| **CHAIN_TIMESTEPS_EXECUTED** | 24 (4 bins × 6 members; 96 reach-steps) | 24 (4 bins × 6 members; 96 reach-steps) | 0 | 0 | 0 | 0 |
| **VALIDATION_CALLS** | 6 | 6 | 0 | 0 | 0 | 0 |
| **RUNTIME_DERIVED_FIELDS** | all 15 runtime fields, RUNTIME_DERIVED | all 15 runtime fields, RUNTIME_DERIVED | NONE (not executed) | NONE | NONE | NONE |
| **CATALOG_DERIVED_METADATA** | 8 fields from master catalogue + evidence lineage | 8 fields | 8 fields | 8 fields | 8 fields | 8 fields |
| **MANUAL_RUNTIME_RESULT_FIELDS** | NONE | NONE | NONE | NONE | NONE | NONE |
| **CSV_RUNTIME_DERIVED** | YES | YES | YES (NOT_COMPUTED cells) | YES | YES | YES |
| **FINAL_CLASSIFICATION** | CONSISTENT (qualitative/directional; runtime-executed; no accuracy claim) | CONSISTENT (qualitative/directional; runtime-executed; no accuracy claim) | NOT_COMPARABLE (preserved) | CONSISTENT (control event; preserved) | UNKNOWN (BLOCKED_MISSING_FORCING; preserved) | UNKNOWN (BLOCKED_MISSING_FORCING; preserved) |

Supporting runtime counts (per executable event, from the call-site counters):
`FORCING_BINS_EXECUTED = 24` (4 bins × 6 member conversions), `HYDROGRAPH_TIMESTEPS_EXECUTED = 18` (3 states per member under the existing stop-on-first-block contract: 2 COMPUTED + 1 BLOCKED at the first UNKNOWN bin; status PARTIAL), `CHAIN_REACH_TIMESTEPS_EXECUTED = 96`, `REACH_STATE_CLASSIFICATIONS = 96`.

Forcing resolution preserved (no synthetic disaggregation):
- EV-01: 4 catalog bins → 4 timesteps with documented intervals [1+1+1+1] h; the direct 91.0 mm/h bin lands exactly on its documented 05:00–06:00 IST observation hour (runtime-asserted).
- EV-02: 4 catalog bins → 4 timesteps with documented intervals [1+3+1+1] h; the documented 3-hour aggregated increment (45.0 mm) is ONE 3-hour timestep — never split into hourly values.
- Anchors are adapter alignment only (documented in the harness); bin durations, order, amounts, and provenance come solely from the runtime catalog.

---

## 4. Runtime-Derived Result Fields (what the runtime actually produced)

All strings below are composed at runtime from the runtime objects (identical structure for both executable events; counts identical because both events have 4 bins with 2 UNKNOWN and the same closed-boundary chain contract).

- **mass_balance_check** — `RUNTIME_DERIVED (advance_chain_series continuity + audit_reach_accounting objects): continuity BLOCKED_MISSING_INPUT=36, COMPUTED=60 of 96 reach-steps; accounting BALANCED=54, BLOCKED_MISSING_INPUT=36, IMBALANCED=6; accounting residual == continuity dV/dt on 60 computed reach-steps (max |err| 0.000e+00 m3/s); negative-storage blocks=0`
- **terminal_outfall_check** — `RUNTIME_DERIVED (reach transfer objects): OC-02 TERMINAL_REACH_NO_DOWNSTREAM on 24/24 reach-steps; actual outflow never emitted; no free-outfall/Yamuna boundary assumed`
- **runtime_model_state** — `RUNTIME_DERIVED (classify_chain_timestep, existing Phase 8B Step-8): UNKNOWN=96 of 96 classified reach-steps; stage UNKNOWN — no storage-stage relation exists for Kushak (REACH_STORAGE_STAGE_RELATIONS deliberately empty) and stage is never inferred from storage, discharge, capacity, or forcing`
- **runtime_consistency_check** — `RUNTIME_DERIVED (validate_observation, existing Phase 8B Step-9, one call per executed member): UNKNOWN=6; no coordinates are invented so the spatial match stays UNKNOWN and the occurrence/state comparison is not attempted; no depth RMSE, discharge RMSE, or accuracy score is computed`
- **timestep_execution_check** — `RUNTIME_DERIVED: 4 forcing bins -> 24 chain steps executed across 6 members (the event forcing sequence drove the timestep loop; every bin executed, UNKNOWN bins as blocked states); hydrograph path executed 18 states per stop-on-first-block contract (PARTIAL)`
- **unknown_propagation_check** — `RUNTIME_DERIVED: 2 UNKNOWN forcing bin(s) preserved (never zero-filled, never interpolated); hydrograph UNKNOWN step -> BLOCKED_MISSING_INPUT with stop-on-first-block (18 states, 6 blocked); chain UG-01 BLOCKED_MISSING_INPUT on 12/24 head-steps (UNKNOWN forcing bins + propagation)`
- **runtime_result_source** — `run_integrated_simulation (rainfall_to_inflow -> InflowHydrograph -> run_hydrograph_simulation) + advance_chain_series + classify_chain_timestep + validate_observation, executed per ensemble member with this event's own forcing`

Non-executable events carry `NOT_COMPUTED (...)` for every runtime result field — never a fabricated PASS.

IMBALANCED note (not hidden): the 6 IMBALANCED accounting records per event are the UG-01 peak-forcing reach-steps under the explicit closed-boundary scenario — the instantaneous flow-through residual is exactly the storage accumulation that the continuity layer computes (residual == dV/dt, verified per reach-step). Water is never lost; the two locked layers report different views of the same conservation by design.

---

## 5. Required System Flags (all computed from records + call-site counters)

| Flag | Value | Basis |
|---|---|---|
| ALL_EXECUTABLE_EVENTS_RUNTIME_EXECUTED | **YES** | EV-01 and EV-02 both executed (runtime_executed=YES from per-event executions) |
| ALL_EXECUTABLE_EVENTS_HAVE_6_MEMBERS | **YES** | each executed exactly the 6 canonical member IDs (set equality against `build_kushak_ensemble()`) |
| ALL_EVENT_FORCING_TIMESTEPS_RUNTIME_EXECUTED | **YES** | chain_timesteps_executed == bins × members for each executable event (24 = 4 × 6) |
| NO_SMOKE_TEST_SUBSTITUTION | **YES** | each event owns distinct counters and artifacts (identity-checked); executable events 6/6 members, non-executable 0; no event-independent `advance_chain_timestep()` smoke call exists in the harness (source-inspected by test) |
| ALL_RUNTIME_RESULT_FIELDS_DERIVED | **YES** | every runtime field starts RUNTIME_DERIVED or NOT_COMPUTED |
| MANUAL_RUNTIME_RESULT_FIELDS_PRESENT | **NO** | `manual_runtime_result_fields = NONE` on every record |
| CSV_IS_RUNTIME_DERIVED | **YES** | CSV rows written from `ReplayEventRecord` objects built from runtime executions |
| UNKNOWN_AND_NOT_COMPARABLE_PRESERVED | **YES** | the four non-executable classifications preserved exactly; 0 executions, 0 validation calls |
| NO_SYNTHETIC_DISAGGREGATION | **YES** | bins == timesteps per executable event; the 3-hour increment is one 3-hour timestep; UNKNOWN bins stay UNKNOWN |

**FINAL_VERDICT = PASS** (also written to `kushak_phase15_5_system_flags.csv`).

---

## 6. Re-Run of Prior Audits

### 6.1 Phase 15.1 forensic audit (re-run)
The 108-record forensic ledger (`kushak_phase15_1_replay_audit.csv`; 103 PASS / 5 NOT_APPLICABLE) was re-verified against the new runtime-derived state. All forensic invariants now hold **with runtime-derived evidence replacing manual-ledger claims**:

| Forensic check | Result | Evidence (now runtime-derived) |
|---|---|---|
| Mass-balance conservation (V_next = V + dt(Qin+Qlat−Qout)) | PASS | accounting residual == continuity dV/dt on 60/60 computed reach-steps per event, max \|err\| 0.000e+00 m³/s |
| Terminal outfall boundary (no free outfall at OC-02) | PASS | TERMINAL_REACH_NO_DOWNSTREAM on 24/24 OC-02 reach-steps per event |
| UNKNOWN propagation (no zero-fill/interpolation) | PASS | 2 UNKNOWN bins per event preserved; blocked states counted from runtime objects |
| No synthetic disaggregation | PASS | [1+1+1+1] h (EV-01), [1+3+1+1] h (EV-02); bins == timesteps |
| Event separation (no pooling) | PASS | distinct forcing IDs, distinct counters/artifacts per event |
| Model-inputs preservation (no calibration) | PASS | ensemble unchanged: 6 members, C=0.75, 27.66/28.40 km², 3 hydraulic scenarios |
| Qualitative-only interpretation (no quantitative accuracy) | PASS | no affirmative accuracy/RMSE/skill/calibration claim anywhere in the new CSV (negation-aware scan) |
| CWC boundary separation / operational-evidence quarantine | PASS | metadata fields unchanged; no evidence field feeds any runtime input |
| Executable member total | PASS | exactly 12 (6+6), not 36 |

Note on supersession: the forensic ledger's `actual` column quotes the Phase 15.0 manually-authored CSV cells; Phase 15.5 replaces those cells with runtime-derived values that substantiate the same forensic conclusions.

### 6.2 Phase 15.2 runtime proof audit (re-run)
The runtime-lineage question ("is the CSV dynamically generated from actual per-event runtime executions?") now resolves to YES for both executable events. Per-event lineage (from the call-site counters):

| Event | Ensemble member executions | Forcing conversions / bins | Hydrograph timesteps | Chain timesteps (reach-steps) | Classifications | Validation calls | CSV row runtime-derived | Manually authored result fields |
|---|---|---|---|---|---|---|---|---|
| EVT-2024-06-27 (EV-01) | 6 | 6 / 24 | 18 | 24 (96) | 96 | 6 | **YES** | NONE |
| EVT-2023-07-08 (EV-02) | 6 | 6 / 24 | 18 | 24 (96) | 96 | 6 | **YES** | NONE |
| EVT-2021-09-11 | 0 | 0 / 0 | 0 | 0 (0) | 0 | 0 | YES (NOT_COMPUTED) | NONE |
| EVT-2026-01-23 | 0 | 0 / 0 | 0 | 0 (0) | 0 | 0 | YES (NOT_COMPUTED) | NONE |
| EVT-2021-07-19 | 0 | 0 / 0 | 0 | 0 (0) | 0 | 0 | YES (NOT_COMPUTED) | NONE |
| EVT-2023-05-27 | 0 | 0 / 0 | 0 | 0 (0) | 0 | 0 | YES (NOT_COMPUTED) | NONE |

The Phase 15.2/15.3 blocker (`CSV_ROW_RUNTIME_DERIVED: NO` for every event) is resolved: both executable events are now `YES` with full call-site counters, and the four non-executable events remain honestly NOT_COMPUTED.

---

## 7. Test & Execution Evidence

- Focused tests: `pytest backend/app/domain/delhi/digital_twin/test_phase15_2_execution_integrity.py` → **15 passed** (4 Phase 15.2 tests preserved + 11 Phase 15.5 tests: a–i proofs, system flags/verdict, and canonical-path equivalence).
- Full digital-twin suite: `pytest backend/app/domain/delhi/digital_twin` → **667 passed** (Phase 15.1 baseline 652 + later Phase 15 additions + 11 new).
- Harness execution: `python scripts/generate_phase15_replay.py` → 6 records written; EV-01/EV-02 runtime-executed with 6 members each; system flags as in Section 5; FINAL_VERDICT = PASS.
- `backend/tests` (legacy suite): 2 pre-existing collection errors and 3 pre-existing failures in untracked stale test modules (`test_digital_twin_hydrology_adapter.py`, `test_drainage_domain.py` import symbols that do not exist in the current `models.py` modules; `test_hydraulic_network.py` expects different network-assembly behavior). These predate and are unrelated to Phase 15.5 (the failing modules never import the replay harness; the maintained digital-twin suite is fully green).

---

## 8. Acceptance Rules Checklist

- [x] ONLY `scripts/generate_phase15_replay.py` + its directly associated test file modified.
- [x] Ensemble built with the existing deterministic `build_kushak_ensemble()` (6 members).
- [x] Each executable event: documented forcing profile retrieved, actual temporal resolution preserved, converted via the existing `rainfall_to_inflow()`, canonical `InflowHydrograph`, existing multi-timestep runtime path, all 6 members, actual runtime outputs collected.
- [x] Existing canonical multi-timestep implementation used (`advance_chain_series()` AND the Phase 15.4 higher-level path), with the event forcing sequence determining the timestep loop.
- [x] No single `advance_chain_timestep()` smoke test anywhere in the harness (source-inspected by test).
- [x] EV-01 and EV-02: genuine event-specific runtime execution.
- [x] EVT-2021-09-11: NOT_COMPARABLE kept; no hourly disaggregation synthesized.
- [x] EVT-2021-07-19 / EVT-2023-05-27: UNKNOWN / BLOCKED_MISSING_FORCING kept; no zero rainfall created.
- [x] EVT-2026-01-23: control-event classification preserved; absent forcing never converted into a runtime simulation.
- [x] `ReplayEventRecord` separates catalog/evidence metadata from runtime-derived results; no manual PASS/FAIL strings for mass balance, terminal outfall, runtime model state, runtime consistency, timestep execution, or ensemble execution.
- [x] CSV regenerated from actual runtime-derived results.
- [x] Provenance fields present: `runtime_executed`, `ensemble_members_executed`, `forcing_bins_executed`, `chain_timesteps_executed`, `validation_calls`, `runtime_result_source` (plus `hydrograph_timesteps_executed`, `chain_reach_timesteps_executed`, `actual_member_ids`, `forcing_found`, `forcing_time_bins`, `forcing_resolution_preserved`).
- [x] Runtime values not hard-coded; unavailable results are UNKNOWN/NOT_COMPUTED, never fabricated PASS.
- [x] Event IDs and `EVENT_ID_MAP` behavior preserved (backward-compatible EV-* and EVT-* forms).
- [x] Counters increment at the actual runtime call sites; never faked.
- [x] 12 genuine member executions total (6 + 6) — not 36, not a shared smoke test.
- [x] No historical-validation-accuracy, calibration, RMSE, or depth-skill claim anywhere.
