# Phase 8A — Evidence-Constrained Kushak Hydraulic Model

## 1. Status

- **Implementation validated**: `backend/app/domain/delhi/digital_twin/kushak_evidence_model.py` compiles, imports, and passes its full test suite.
- **Tests: 21/21 passed** (`pytest -q app/domain/delhi/digital_twin/test_kushak_evidence_model.py -p no:warnings`).
- This is a **scenario model, NOT an as-built hydraulic twin**. It is runnable as an evidence-constrained computational scenario (`KushakModelStatus.RUNNABLE_AS_SCENARIO`) while remaining explicitly blocked for any real/as-built hydraulic claim. No surveyed or as-built Kushak geometry is asserted anywhere in the implementation or its outputs.

## 2. Purpose

- Provide the first scientifically defensible, evidence-constrained representation of the Kushak drain that can run end-to-end.
- Serve as the **bridge between the acquired evidence inventory and the existing Phase 7D hydraulic engine**: every input carries explicit provenance, and the existing `run_integrated_simulation` chain is fed through `run_kushak_evidence_scenario`.

## 3. Evidence hierarchy / provenance

No new provenance categories are introduced; the existing `ProvenanceStatus` enum and hydraulic weakest-link rules are reused:

| Evidence | Provenance |
|---|---|
| DMP longitudinal invert | `OFFICIAL_MODEL_VALUE` |
| NGT Joint Inspection (structural dims) | `OBSERVED`/`OFFICIAL` — visual, bounded field evidence |
| NDMC NIT52 barrel class | `OFFICIAL` + `PROCUREMENT_SPECIFICATION` |
| Effective computational geometry | `ASSUMED` / `INFERRED_EFFECTIVE` (label) |
| Catchment areas | `DERIVED`/`PROVISIONAL` |
| Missing rainfall hours | `UNKNOWN` (None, never filled) |
| Phase 7D16 multipliers | `INFERRED_EFFECTIVE` (scenario label); engine receives `ASSUMED` |

## 4. DMP backbone

- **84 unique backbone nodes** loaded from the curated DMP 2018 Appendix XII JSON (three Kushak profiles; J_5105/J_6182 shared junctions counted once).
- **J_3055 new invert = 216.841 m** (upstream backbone head).
- **J_7549 corrected new invert = 203.752 m** (IITD corrections are flagged via `iitd_corrected`, never hidden).
- **These DMP model values are NOT current/as-built survey data.** They are official departmental-record longitudinal geometry as digitized and model-corrected by IIT Delhi — not a field survey certificate and not post-2018 desilting state.

## 5. Structural evidence

NGT Joint Inspection Report, 05-03-2025 (CEs of MCD + I&FC) — Bus Depot covered structure:

- Total structure width: **50 m** (observed)
- **5 bays** (~10 m each is derived, not quoted)
- Visual depth bounds: **3.5–4.5 m** ("as per the visual assessment" — bounds only)
- Access openings: 1.5 × 1.5 m @ ~50 m spacing (observed)
- Silt chambers: 2.50 × 1.15 m @ ~100 m spacing (observed)
- Silt depth at inspection: 1.5–3 ft in all five bays (pre-monsoon 2025; desilting occurred afterwards)

**These are not continuous surveyed hydraulic cross-sections.** They are structural/visual bounds; no hydraulic clear dimensions are inferred beyond what is documented.

## 6. NIT52 procurement evidence

- Covered barrel procurement size class: **4.0–5.0 m** (4.00 m +25%), package `work_396329.zip`, sha256-verified.
- 290 m robotic sonar silt estimation is a **future deliverable, not acquired data**.
- **This is specification only — NOT measured/as-built geometry.** The 21,406 m³ desilting quantity is an indirect procurement quantity, not geometry.

## 7. Catchment scenarios

- **27.66 km²** — working watershed, `DERIVED`/`PROVISIONAL` (D8 project watershed; working only).
- **28.40 km²** — separate sensitivity scenario (3 m burn sensitivity audit).
- **~35.4 km² historical — UNRESOLVED, represented only as UNKNOWN** (`CATCHMENT_HISTORICAL_KM2 = None`; never fabricated).
- **No authoritative Kushak-wide catchment is claimed.** No silently-chosen "true" catchment exists.

## 8. Effective hydraulic scenarios

Three distinct scenarios within the retained Phase 7D16 sampled ranges (`mult_box` 0.800–0.923, `mult_open` 0.714–0.893, `f_open_depot` 0.400–1.000):

| Scenario | mult_box | mult_open | f_open_depot |
|---|---|---|---|
| CONSERVATIVE | 0.800 | 0.714 | 0.700 |
| CENTRAL | 0.862 | 0.804 | 0.700 |
| DEGRADED_CAPACITY | 0.800 | 0.714 | 0.400 |

- These are **effective scenario assumptions derived from the Phase 7D16 sampled ranges — NOT calibrated parameters and NOT observed values**. Each scenario retains its source ranges alongside the selected value.
- Effective Manning n is derived as `n_base / multiplier` from DMP model values (RCC box 0.012, irregular open drain 0.025).
- `DEGRADED_CAPACITY`'s `f_open_depot = 0.400` is linked explicitly to the NGT JIR observed condition (flow through 2 of 5 bays = 0.4, with 1.5–3 ft silt) — observed evidence used as a scenario bound, not a calibrated parameter.

## 9. Rainfall handling

- The June 2024 forcing is **reused** from `kushak_rainfall_scenario.load_june_2024_forcing` (never retyped).
- Overlap-dependent derived hours are **UNKNOWN (None) — no interpolation, no zero filling, never fabricated**.
- The direct observed 91.0 mm hour (OBSERVED_DIRECT) and verified zeros pass through as the only usable values.
- The first UNKNOWN timestep **blocks the hydraulic chain with `BLOCKED_MISSING_INPUT`**; discharge stays UNKNOWN, never zero or interpolated.
- **No reconstructed hourly 228.1 mm series is claimed.** Event mass balance refers only to the actual source block observations (148.5 mm block, 91.0 mm direct hour, 79.6 mm residual block), never to any hourly sum.

## 10. Phase 7D integration

- The tests exercise the **existing Phase 7D integrated chain** (`rainfall_to_inflow` → `run_hydrograph_simulation` via `run_integrated_simulation`) with:
  - the covered COMPUTATIONAL EFFECTIVE SCENARIO PROFILE (bed at DMP J_3055 invert 216.841 m),
  - the scenario's effective Manning n (INFERRED_EFFECTIVE; ASSUMED at the engine boundary),
  - the DERIVED backbone slope from DMP inverts and digitized chainages (returns None/UNKNOWN if chainages are unresolved),
  - explicit zero outflow/lateral inflow, ASSUMED provenance at the engine boundary.
- With an all-usable forcing the run reaches `COMPUTED`; with the real June 2024 forcing it blocks at the first UNKNOWN timestep.
- **Scenario execution is distinct from validated real-world prediction**: resulting states are DERIVED scenario outputs, never observed Kushak hydraulic states.

## 11. What Phase 8A can and cannot claim

**CAN:**
- Execute an evidence-constrained computational scenario end-to-end.
- Preserve provenance at every input (no fabrication, no silent filling).
- Expose uncertainty/unknowns explicitly (UNKNOWN stays UNKNOWN).
- Exercise the existing Phase 7D computational chain.

**CANNOT:**
- Claim surveyed or as-built Kushak geometry.
- Claim calibrated Kushak hydraulics.
- Claim validated street-level flood depth.
- Claim continuous Kushak stage/discharge observations (none exist).
- Claim operational nowcasting accuracy.

## 12. Remaining P0 blockers

- Current longitudinal invert/bathymetry (Nov-2024 I&FC survey output not public).
- Measured cross-sections (NIT-52 drawings bidder-restricted; no instrumented sections).
- Africa Avenue conduit geometry (as-built clear hydraulic dimensions UNKNOWN post-2018).
- Bridge/culvert apertures (no surveyed hydraulic apertures).
- Certified vertical datum/control.
- Continuous rainfall/stage/discharge observations (Kushak has none; CWC Yamuna stage is downstream context only).
- Downstream boundary/backwater calibration.

## 13. Intentionally unimplemented

- Calibration (no parameter fitting anywhere in this phase).
- ML (no learned components).
- Network routing (single effective profile chain only).
- Surface/overtopping (no 2D surface flow).
- Road-risk (no street-level risk mapping).
- Operational warnings (no nowcasting product).
- Real-world validation (no observed Kushak data exists to validate against).

## 14. Validation

```
pytest -q app/domain/delhi/digital_twin/test_kushak_evidence_model.py -p no:warnings
```

Result: **21 passed, 0 failed, 0 errors.**

## 15. Provenance rule

**"No computational output from Phase 8A should be interpreted as observed Kushak hydraulic truth."**
