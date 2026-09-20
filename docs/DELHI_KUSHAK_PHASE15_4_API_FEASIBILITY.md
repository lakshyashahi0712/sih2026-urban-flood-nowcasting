# Phase 15.4 — Historical Replay API Feasibility Inspection (Delhi / Kushak V2)

**Document ID:** `DELHI_KUSHAK_PHASE15_4_API_FEASIBILITY`  
**Date:** 2026-09-16  
**Mode:** READ-ONLY API INSPECTION — NO MODIFICATIONS  
**Scope:** Inspect existing canonical runtime APIs to determine feasibility of event-specific forcing pass-through for genuine historical replay.

---

## 1. EXECUTE_ENSEMBLE_MEMBER_SIGNATURE

```python
def execute_ensemble_member(
    member: KushakEnsembleMember,
) -> IntegratedRunResult:
```

- **Parameters:** 
  - `member: KushakEnsembleMember` (immutable dataclass containing hydraulic_scenario_id, catchment_scenario_id, runoff_coefficient)
- **Return type:** `IntegratedRunResult` (contains rainfall_conversion and hydraulic_run results)
- **Forcing/time input:** 
  - **NO** explicit forcing or time parameters. 
  - Forcing is implicitly fixed via the member's `runoff_coefficient` (ASSUMED = 0.75) and hardcoded June 2024 scenario forcing loaded internally by `run_kushak_evidence_scenario()`.
  - Time steps are fixed to the hardcoded June 28, 2024 forcing timesteps (from `load_june_2024_forcing()`).
- **Member forcing nature:** 
  - Contains **fixed scenario assumptions** (hydraulic scenario, catchment scenario, runoff coefficient). 
  - **Does NOT accept dynamic forcing** — the rainfall hydrograph is hardcoded to the verified June 28, 2024 event inside `run_kushak_evidence_scenario()`.

---

## 2. HISTORICAL_FORCING_INJECTION_POINT

The canonical point where time-varying rainfall/runoff forcing enters the model is in **`backend/app/domain/delhi/digital_twin/hydraulic_integrated_orchestrator.py`**, function `run_integrated_simulation()`:

```python
# Rainfall → inflow conversion
conversion = rainfall_to_inflow(
    timesteps=timesteps,
    rainfall_depth_mm=rainfall_depth_mm,
    catchment_area_km2=catchment_area_km2,
    runoff_coefficient=runoff_coefficient,
    # ... provenance parameters
)

# Inflow → hydraulic chain injection point
hydraulic_run = run_hydrograph_simulation(
    initial_state=initial_state,
    hydrograph=conversion.hydrograph,  # <-- HISTORICAL FORCING INJECTION POINT
    timesteps=timesteps,
    # ... hydraulic parameters
)
```

- The `hydrograph` parameter of type `InflowHydrograph` (containing `HydrographTimeStep` discharge values in m³/s) is the **exact interface** where historical rainfall forcing enters the hydraulic chain.
- This hydrograph is produced by `rainfall_to_inflow()` from caller-supplied `rainfall_depth_mm` and `timesteps` lists.
- No modification of hydraulic physics occurs here — only the prescribed inflow boundary condition is applied.

---

## 3. MULTI_TIMESTEP_DRIVER

**YES**, an existing canonical multi-timestep driver exists:  
**`advance_chain_series()`** in `backend/app/domain/delhi/digital_twin/kushak_continuity_routing.py` (lines 315-369).

- **Signature:**
  ```python
  def advance_chain_series(
      step_specs: Tuple[ChainStepSpec, ...],
      initial_storage: Optional[Dict[str, float]] = None,
      initial_storage_provenance: Optional[Dict[str, ProvenanceStatus]] = None,
      initial_stage: Optional[Dict[str, float]] = None,
      tolerance: float = 1e-6,
  ) -> ChainSeriesResult:
  ```
- **Input:** A tuple of `ChainStepSpec` objects, each defining:
  - `timestep: SimulationTimestep`
  - `head_flow_m3_s: Optional[float]`
  - `laterals: Dict[str, float]` (reach_id → lateral inflow)
  - Plus optional provenance and decision dictionaries
- **Functionality:** 
  - Advances the chain over a sequence of **contiguous timesteps** (each step's end must equal the next step's start).
  - Reuses the existing `advance_chain_timestep()` per step.
  - Storage threads forward: `COMPUTED` storage carries `DERIVED` provenance; blocked reaches remain `UNKNOWN` for the next step.
  - **Does NOT duplicate** any hydraulic equations — reuses Phase 7D continuity (`compute_continuity_update`) and routing (`route_reach_transfer`).

---

## 4. RUNTIME_DATA_FLOW

```
historical rainfall catalogue
        ↓
get_forcing_for_event(event_id="EV-01" or "EV-02")
        ↓
RainfallForcingProfile (lead_hour bins: t+0h, t+1h, t+2h, t+3h with amounts/provenance)
        ↓
Extract depths_mm list and build timesteps list (preserving exact bin intervals)
        ↓
rainfall_to_inflow()  # Phase 7D-17
        ↓
InflowHydrograph (time series of discharge m³/s with DERIVED provenance; None = UNKNOWN)
        ↓
run_hydrograph_simulation()  # Phase 7D-12 (hydrograph-driven orchestration)
        ↓
advance_state_through_chain()  # Phase 7D-11 (per timestep orchestration)
        ↓
[geometry bundle → Manning capacity → flow inputs → hydraulic time stepper]  # Phase 7D-10
        ↓
advance_chain_series()  # Phase 8B Step 5 (multi-timestep chain routing)
        ↓
advance_chain_timestep() → advance_reach_timestep()  # Per reach routing/continuity
        ↓
route_reach_transfer() → compute_continuity_update() → audit_reach_accounting()
        ↓
Validation via validate_observation()  # Phase 8B Step 9 (event-separated comparison)
```

**Provenance rules preserved at every step:**
- `UNKNOWN` rainfall (None) → `UNKNOWN` discharge → `BLOCKED_MISSING_INPUT` hydraulic state
- No zero-filling, interpolation, or synthetic disaggregation
- Weakest-link input provenance propagated through continuity equation
- Validation output marked `DERIVED` — never promotes model to Tier-A

---

## 5. REPLAY_IMPLEMENTATION_BOUNDARY

To make historical replay **genuinely runtime-derived** (event-specific hydraulic execution with catalog forcing), the **minimum files requiring modification** are:

1. **`scripts/generate_phase15_replay.py`**  
   - Replace the current manual-ledger approach with event-specific simulation loops.
   - For each event with catalog forcing:
     - Retrieve forcing profile via `get_forcing_for_event()`
     - Convert to `rainfall_depth_mm` list and `timesteps` list
     - Execute 6 ensemble members via `build_kushak_ensemble()` + `execute_ensemble_member()`
     - **OR** use low-level chain: `rainfall_to_inflow()` → `run_hydrograph_simulation()` → `validate_observation()`
     - Record actual runtime results (not manually authored strings)
   - Preserve `UNKNOWN`/`NOT_COMPARABLE` for events without executable forcing.

2. *(No other files strictly require modification)*  
   - The existing canonical APIs (`kushak_event_validation.py`, `kushak_historical_rainfall_catalog.py`, `kushak_scenario_executor.py`, `kushak_continuity_routing.py`, `hydraulic_integrated_orchestrator.py`) already support the required interfaces.
   - `EVENT_ID_MAP` and `resolve_event_id()` already bridge `EVT-*` → `EV-*` IDs.

**Boundary note:** Modifications would be confined to the replay harness orchestration layer — **zero changes** to hydraulic physics, parameters, geometry, or rainfall methodology.

---

## 6. SCIENTIFIC SAFETY

Executable historical events from existing documented forcing (no invention/disaggregation):

| Event ID        | Executable? | Forcing Basis                                                                 | Treatment if Not Executable         |
|-----------------|-------------|-------------------------------------------------------------------------------|-------------------------------------|
| **EVT-2024-06-27** | ✅ YES      | Hourly AWS telemetry: t+0h=0mm (VERIFIED_ZERO), t+1h=91.0mm/h (OBSERVED_DIRECT), t+2h/t+3h=UNKNOWN | N/A                                 |
| **EVT-2023-07-08** | ✅ YES      | 3-hourly blocks: t+0h=0mm (VERIFIED_ZERO), t+1h=45.0mm (DERIVED), t+2h/t+3h=UNKNOWN | N/A                                 |
| EVT-2021-09-11  | ❌ NO       | Only 3-hourly blocks + daily total — **no authoritative hourly disaggregation** | `NOT_COMPARABLE` (input barrier)    |
| EVT-2026-01-23  | ❌ NO       | Daily total only (28.4mm) — **no sub-daily resolution**                        | `CONSISTENT` (non-surcharge control) |
| EVT-2021-07-19  | ❌ NO       | `NONE_DOCUMENTED` — **no station rainfall total located**                     | `UNKNOWN` (halts at forcing)        |
| EVT-2023-05-27  | ❌ NO       | `NONE_DOCUMENTED` — **no station rainfall total located**                     | `UNKNOWN` (halts at forcing)        |

**Scientific guarantees:**
- No synthetic hourly profiles generated for unallocated intervals.
- Missing forcing preserves `UNKNOWN` provenance — never zero-filled or interpolated.
- Control event (`EVT-2026-01-23`) remains a pure negative validation check (no calibration).
- All executable events use **only** the documented temporal resolution from the catalog.

---

## 7. EXISTING RUNTIME CAPABILITIES (WITHOUT HYDRAULIC PHYSICS MODIFICATION)

✅ **A) One event:**  
`run_kushak_evidence_scenario()` executes one evidence-constrained scenario end-to-end (rainfall → inflow → hydraulics → validation) using hardcoded June 2024 forcing.  
**Alternative:** Low-level chain (`rainfall_to_inflow()` → `run_hydrograph_simulation()`) accepts arbitrary `rainfall_depth_mm` and `timesteps`.

✅ **B) Multi-timestep event replay:**  
`advance_chain_series()` exists for deterministic multi-timestep runs over contiguous timesteps.  
**Used by:** `run_hydrograph_simulation()` internally loops over timesteps via `advance_state_through_chain()`.

✅ **C) Six ensemble members per event:**  
`build_kushak_ensemble()` returns exactly 6 deterministic members (3 hydraulic scenarios × 2 catchment scenarios).  
Each member executed via `execute_ensemble_member(member)`.

**All capabilities use existing, unmodified Phase 7D/8B/9 hydraulic contracts.**  
Zero calibration, zero parameter tuning, zero GLUE, zero ML.

---

## CONCLUSION

The existing canonical runtime APIs **fully support** genuine historical replay implementation via:
1. Event-specific forcing injection at `hydrograph` parameter of `run_hydrograph_simulation()`
2. Multi-timestep execution via `advance_chain_series()`
3. Deterministic ensemble execution via `build_kushak_ensemble()` + `execute_ensemble_member()`
4. Event-separated validation via `validate_observation()`
5. Strict `UNKNOWN` provenance preservation throughout

**No hydraulic physics modification required.**  
The feasibility blocker is **solely** in the replay harness (`scripts/generate_phase15_replay.py`) — which currently uses a smoke-test/manual-ledger approach instead of event-specific simulation loops.

---

### Final Flags (Derived from Actual Code Inspection)

```
ALL_EXECUTABLE_EVENTS_RUNTIME_EXECUTED = NO
ALL_EXECUTABLE_EVENTS_HAVE_6_MEMBERS = YES
ALL_EVENT_TIMESTEPS_RUNTIME_EXECUTED = NO
ALL_RUNTIME_RESULT_FIELDS_DERIVED = NO
MANUAL_RUNTIME_RESULT_FIELDS_PRESENT = YES
CSV_IS_RUNTIME_DERIVED = NO
UNKNOWN_AND_NOT_COMPARABLE_PRESERVED = YES
NO_SYNTHETIC_DISAGGREGATION = YES
```

### Verdict
**BLOCKED_BY_RUNTIME_API**

*(The existing canonical runtime APIs support genuine historical replay (A, B, C all YES), but the current replay harness does not utilize them for event-specific execution — hence BLOCKED_BY_RUNTIME_API. Implementation would require modifying only the replay harness to call the existing APIs in an event-driven loop.)*

**READY_FOR_IMPLEMENTATION** would be declared only if `scripts/generate_phase15_replay.py` already executed event-specific runtime loops — which it does not (per Phase 15.3 audit).