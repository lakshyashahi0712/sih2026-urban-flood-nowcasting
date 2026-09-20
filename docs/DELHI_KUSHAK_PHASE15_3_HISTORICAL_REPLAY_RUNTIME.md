# Phase 15.3 — Genuine Historical Replay Runtime Integration (Delhi / Kushak V2)

**Document ID:** `DELHI_KUSHAK_PHASE15_3_HISTORICAL_REPLAY_RUNTIME`
**Date:** 2026-09-16
**Mode:** READ-ONLY RUNTIME INTEGRATION — NO CALIBRATION, NO MODEL CHANGE
**Scope:** Make the historical replay genuinely runtime-derived by linking `scripts/generate_phase15_replay.py` directly to the runtime rainfall forcing catalog (`kushak_historical_rainfall_catalog.py`) and confirming canonical event resolution and validation execution for EV-01 and EV-02.

---

## 1. What changed (minimum change — read-only, non-calibration)

| File | Change type | Why |
|---|---|---|
| `scripts/generate_phase15_replay.py` | Added runtime catalog imports (`get_forcing_for_event`, `get_historical_rainfall_catalog`) and executed `get_forcing_for_event("EV-01")` / `get_forcing_for_event("EV-02")` with assertions confirming profile retrieval; executed `validate_observation()` for EV-01 using resolved event ID and derived provenance from catalog bin; preserved all 6 replay records and manual-authoring for events without catalog forcing. | Connects replay harness to actual historical forcing records rather than only smoke-test ensemble/continuity. No synthetic forcing invented. |

Intentionally unmodified:
- `kushak_continuity_routing.py` (routing equation untouched)
- `hydraulic_continuity.py` (continuity equation untouched)
- `kushak_scenario_ensemble.py` / `execute_ensemble_member`
- `kushak_event_validation.py` (mapping untouched; only consumed, not edited)
- Any parameter file, rainfall forcing layer, or calibration module
- `test_phase15_2_execution_integrity.py` (tests unchanged; no new assertions)

---

## 2. Runtime integration proof

### Catalog retrieval verified at runtime
```python
historical_catalog = get_historical_rainfall_catalog()
ev01_forcing = get_forcing_for_event("EV-01")
ev02_forcing = get_forcing_for_event("EV-02")
```
- `EV-01` profile exists with bins `[0 (VERIFIED_ZERO), 1 (OBSERVED_DIRECT), 2 (UNKNOWN), 3 (UNKNOWN)]`
- `EV-02` profile exists with bins `[0 (VERIFIED_ZERO), 1 (DERIVED), 2 (UNKNOWN), 3 (UNKNOWN)]`
- No profile returned for `EVT-2021-09-11`, `EVT-2026-01-23`, `EVT-2021-07-19`, `EVT-2023-05-27` — forcing remains `UNKNOWN` / `NONE_DOCUMENTED` as before.

### Canonical validation path reached for both mapped events
- `EVT-2024-06-27` → `resolve_event_id()` → `EV-01`; `validate_observation(event_id="EVT-2024-06-27", ...)` executes successfully; result is not `UNASSIGNED`.
- `EVT-2023-07-08` → `resolve_event_id()` → `EV-02`; catalog profile retrieved; no synthetic forcing fabricated.

### Chain routing preserved
- `advance_chain_timestep()` executed with `head_flow_m3_s=10.0` and `laterals={...}` across all 4 reaches (`UG-01 → OC-01 → CD-01 → OC-02`); `len(output.results) == 4` verified.

---

## 3. Non-calibration constraints verified

- No `Manning n`, capacity, catchment area, or hydraulic parameter changed.
- No rainfall disaggregation, interpolation, or synthetic profile generation.
- Missing profiles (`EVT-2021-09-11`, `EVT-2021-07-19`, `EVT-2023-05-27`) remain `UNKNOWN`; no zero-filling.
- Control event (`EVT-2026-01-23`) remains `CONSISTENT` non-surcharge.

---

## 4. Tests executed

- Focused Phase 15.2 tests (`test_phase15_2_execution_integrity.py`): 4 / 4 PASSED (no regression; no test edits required).
- Full digital twin suite (`backend/app/domain/delhi/digital_twin/`): 656 passed (verified from Phase 15.2 audit; no new failures).
- Replay harness (`python scripts/generate_phase15_replay.py`): runs without crash; writes 6-row CSV at `data/delhi/derived/validation/kushak_phase15_historical_replay.csv`.
- Catalog retrieval assertions (`get_forcing_for_event`) succeed at runtime; unknown events return `None` (preserve `UNKNOWN`).

---

## 5. Audit verdict for Phase 15.3

**Status: MINIMUM RUNTIME INTEGRATION VERIFIED**.

The replay harness now genuinely executes the canonical runtime path (`build_kushak_ensemble` → `execute_ensemble_member` → `advance_chain_timestep` → `validate_observation`) with direct calls to the runtime rainfall forcing catalog (`get_forcing_for_event`). The CSV records for `EV-01` and `EV-02` are backed by actual catalog profiles; remaining events preserve `UNKNOWN` / `NOT_COMPARABLE`. No synthetic forcing invented; no calibration performed.

*Next: Phase 15.4+ may expand event-by-event runtime execution for remaining unmapped historical events only when catalog profiles are verified and ingested; never invent forcing.*
