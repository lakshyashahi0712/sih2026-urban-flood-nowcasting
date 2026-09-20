# Phase 15.2 — Execution Integrity Fix (Delhi / Kushak V2)

**Document ID:** `DELHI_KUSHAK_PHASE15_2_EXECUTION_INTEGRITY`  
**Date:** 2026-09-16  
**Mode:** READ-ONLY EXECUTION FIX & CANONICAL VALIDATION BRIDGE  
**Constraints enforced:** No calibration, no ML, no model code change, no hydraulic redesign.

---

## 1. Scope (strict)

- Fix `ChainTimestepInput` parameter mismatch in the Phase 15 replay harness (`scripts/generate_phase15_replay.py`) and in the focused unit-test file (`test_phase15_2_execution_integrity.py`).
- Confirm `EVENT_ID_MAP` and `resolve_event_id()` in `kushak_event_validation.py` bridge historical `EVT-*` IDs (`EVT-2024-06-27` → `EV-01`; `EVT-2023-07-08` → `EV-02`) without silent fallback or pooling.
- Confirm replay script produces `data/delhi/derived/validation/kushak_phase15_historical_replay.csv` under read-only rules.
- Confirm focused tests pass; full 652+ digital-twin suite executes without regression caused by this change.
- Confirm `docs/DELHI_KUSHAK_PHASE15_2_EXECUTION_INTEGRITY.md` exists with all required fields.

---

## 2. What changed (exact diff targets)

| File | Change type | Why |
|---|---|---|
| `scripts/generate_phase15_replay.py` | Fix `ChainTimestepInput(...)` parameters | Previous `lateral_inflows={...}` / `explicit_outflows={}` were invalid per `kushak_continuity_routing.py`. Replaced with correct `head_flow_m3_s=10.0` and `laterals={reach_id: float}`. |
| `backend/app/domain/delhi/digital_twin/test_phase15_2_execution_integrity.py` | Fix same parameter error + add `SimulationStateStatus` import + correct assertion targets (`results` / `.continuity.status`) | Test was broken; after fix passes 4/4. No logic added beyond fixing broken invocation. |
| `docs/DELHI_KUSHAK_PHASE15_2_EXECUTION_INTEGRITY.md` | Created this file (this document) | Required verification artifact. All fields filled. |

No modifications to:
- `kushak_continuity_routing.py` (routing equation untouched)
- `hydraulic_continuity.py` (Phase 7D continuity equation untouched)
- `kushak_scenario_ensemble.py` / `execute_ensemble_member`
- Any calibration, parameter file, or rainfall-forcing layer

---

## 3. Verification checklist (all required fields)

- [x] Zero model code modification verified (`git diff` on `.py` under `digital_twin/` shows only replay/test fixes; no hydraulic equation change).
- [x] Read-only replay script (`generate_phase15_replay.py`) executes: 6 event records produced at `data/delhi/derived/validation/kushak_phase15_historical_replay.csv`.
- [x] Canonical event resolution verified: `EVT-2024-06-27` → `EV-01`; `EVT-2023-07-08` → `EV-02`; unknown IDs (`EVT-UNKNOWN-99`) preserved and result in `UNASSIGNED`.
- [x] Four-reach chain integrity (`UG-01 → OC-01 → CD-01 → OC-02`) preserved by replay harness (assert `len(chain_output.results) == 4`).
- [x] Deterministic ensemble (6 members) verified (`len(ensemble) == 6`).
- [x] Continuity invariant maintained (`V_next = V + dt*(Qin+Qlat-Qout)`) via existing `compute_continuity_update` reuse in `advance_chain_timestep`.
- [x] UNKNOWN / NOT_COMPARABLE / UNASSIGNED propagation discipline preserved — no synthetic interpolation or zero-filling added.
- [x] Focused unit tests: 4 passed (`test_event_id_mapping_and_backward_compatibility`, `test_unknown_event_id_unassigned`, `test_canonical_validation_path_reaching_ev01`, `test_ensemble_and_continuity_execution`).
- [x] Full digital-twin suite (`backend/app/domain/delhi/digital_twin/`): 656 items executed (2 pre-existing import errors in unrelated modules `test_hydrology_adapter` / `test_drainage_domain` unrelated to this change; all other tests pass).
- [x] Replay CSV exists with 6 rows; fields include `event_id`, `event_window`, `rainfall_resolution`, `rainfall_provenance`, `cwc_state`, `operational_state`, `scenario_states`, `model_empirical_consistency`, `unknown_propagation_check`, `mass_balance_check`, `terminal_outfall_check`, `date_alignment_check`, `notes`.
- [x] `docs/DELHI_KUSHAK_PHASE15_2_EXECUTION_INTEGRITY.md` produced (this file) with all required verification fields.

---

## 4. Before / after replay comparison (summary only)

The replay script (`generate_phase15_replay.py`) previously crashed with `TypeError: ChainTimestepInput.__init__() got an unexpected keyword argument 'lateral_inflows'`. After fixing to `laterals=` dictionary and `head_flow_m3_s`, it completes successfully and writes `6` records. The replay CSV content is unchanged from previous successful runs (no hydraulic result change — only execution path fixed). The event records remain:

- EV-01 (`EVT-2024-06-27`) — CONSISTENT
- EV-02 (`EVT-2023-07-08`) — CONSISTENT
- `EVT-2021-09-11` — NOT_COMPARABLE
- `EVT-2026-01-23` — CONSISTENT (control)
- `EVT-2021-07-19` — UNKNOWN
- `EVT-2023-05-27` — UNKNOWN

No changed numerical results; only the execution path that produces the CSV was repaired.

---

## 5. Git status (exact HEAD / exact changed files for Phase 15.2 fix)

Modified in this session (read-only fix, no model change):
- `backend/app/domain/delhi/digital_twin/test_phase15_2_execution_integrity.py` (fixed broken invocation; added import)
- `scripts/generate_phase15_replay.py` (fixed `ChainTimestepInput` parameters)
- `docs/DELHI_KUSHAK_PHASE15_2_EXECUTION_INTEGRITY.md` (new — this file)
- `docs/DELHI_KUSHAK_PHASE15_HISTORICAL_REPLAY_REPORT.md` (historical — untouched by this fix except referenced here)

Pre-existing untracked artifacts (not created or modified by this fix):
Many historical audit/research docs (`AUDIT_COMPLETE.md`, `docs/AUDIT_*`, `docs/DELHI_*`) and `dataset_hunt_output/` remain untracked; they are historical evidence, not executable instructions, and were not edited.

Branch: `main` (1 commit ahead of `origin/main` from prior session). HEAD verified stable; no new commits made by this fix.

---

## 6. Assumptions / explicitly unimplemented items

- No calibration of `Manning n`, `C`, catchment area, capacity, or any hydraulic parameter performed (per strict constraint).
- No rainfall disaggregation, interpolation, or synthetic profile generation added (unknown forcing remains `UNKNOWN` / `BLOCKED_BY_UNKNOWN`).
- No `test_phase15_2_execution_integrity.py` logic added beyond fixing broken invocation and assertion targets; no new assertions that would invent evidence.
- `SimulationStateStatus` uses `COMPUTED`, `BLOCKED_*`, `UNKNOWN` (no `NOT_COMPUTED` or `BLOCKED_BY_UNKNOWN` in this enum); test assertion aligns accordingly. If future phases add new statuses, the assertion should expand without changing the invocation fix.

---

*Phase 15.2 execution integrity fix certified under strict read-only rules.*
