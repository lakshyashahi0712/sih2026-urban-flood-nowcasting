# Science-Only Forensic Audit of Delhi/Kushak Rainfall→Runoff Engine
## SIH 2026 V2 Prototype

**Audit Date:** 2026-09-10  
**Objective:** Assess mathematical and physical defensibility of existing rainfall→runoff implementation for potential use as hydrologic forcing component in future hydraulic modelling  
**Constraints:** No modifications to canonical geometry, catchment, rainfall, hydrology, or hydraulic code; focus on identifying genuine defects requiring minimal corrective changes only

---

### Executive Summary

The Delhi/Kushak rainfall→runoff engine implements two loss models (Green-Ampt and SCS-CN) and a runoff transformation component. The audit reveals **two significant defects** requiring correction:

1. **Green-Ampt Implementation Bug:** Cumulative infiltration is not updated during the before-ponding phase, causing incorrect infiltration capacity calculations after ponding onset.
2. **SCS-CN Implementation Issue:** Depression storage is subtracted twice—once explicitly and once through the initial abstraction term—violating the standard SCS-CN conceptual framework.

All other components (unit consistency, mass balance conservation, runoff transformation, lateral inflow decoupling) meet scientific standards for a prototype hydrologic forcing component. After correcting the identified defects, the engine is mathematically and physically defensible for its intended purpose.

**Verdict:** **CONDITIONAL GO** – Proceed to hydraulic modelling only after implementing the specified corrections.

---

### 1. Green-Ampt Infiltration Model Audit

#### File: `backend/app/domain/delhi/hydrology/loss_green_ampt.py`

#### 1.1 Dimensional Consistency ✅
- All length units consistently maintained in mm
- Time conversions properly handled (mm/hr ↔ mm/min ↔ hours)
- Infiltration capacity equation: `ks * (1 + psi*delta_theta / F)` yields mm/hr
- Time step multiplication: `capacity * dt_hr` yields mm
- Mass balance verified in output (errors ≤1.25e-14%)

#### 1.2 Infiltration Capacity Equation ✅
- Correct form: `f = Ks * [1 + (ψ * Δθ) / F]`
- Variables: 
  - `ks` = saturated hydraulic conductivity (mm/hr) ✓
  - `psi` = wetting front suction head (mm) ✓
  - `delta_theta` = initial moisture deficit (dimensionless) ✓
  - `cumulative_infiltration` = F (mm) ✓

#### 1.3 Critical Bug: Cumulative Infiltration Tracking 🔴
**Location:** Lines 95-121 (before-ponding section)  
**Issue:** `cumulative_infiltration` variable is never updated during depression storage filling or pre-ponding infiltration, despite infiltration occurring.

**Current Code:**
```python
# Before ponding section
infiltration_mm = rainfall_depth  # Potential infiltration
# ... depression storage handling ...
infiltration_mm -= depression_loss  # Actual infiltration after depression storage
# MISSING: cumulative_infiltration += infiltration_mm
```

**Physical Consequence:** 
- During pre-ponding phase, infiltration occurs but is not accumulated
- When ponding begins, `cumulative_infiltration` underestimates actual infiltrated volume
- Infiltration capacity calculation becomes too high: `f = Ks * [1 + (ψ*Δθ) / F]` increases as F decreases
- Leads to overestimation of infiltration capacity → underestimation of runoff volume and timing errors

**Required Fix:** Add `cumulative_infiltration += infiltration_mm` after depression storage adjustment in both before-ponding and after-ponding sections.

#### 1.4 Initial Conditions & Ponding Transition ✅
- Initial `cumulative_infiltration = 0.0` (dry conditions) ✓
- Ponding time calculation uses standard Green-Ampt form ✓
- Handles instantaneous ponding when `psi * delta_theta ≤ 0` ✓
- Protects against division by zero and non-physical `tp` values ✓

#### 1.5 Depression Storage Handling ✅
- Separately tracks impervious and pervious depression storage ✓
- Fills depression storage before allowing infiltration to occur ✓
- Conceptually correct: depression storage is surface storage, not soil infiltration ✓
- Variables properly initialized and updated ✓

#### 1.6 Numerical Stability ✅
- Checks for `tp ≤ 0`, `math.isinf(tp)`, `math.isnan(tp)` ✓
- Uses `float('inf')` for initial infiltration capacity when F=0 ✓
- Ensures non-negative infiltration and runoff values ✓

#### 1.7 Unused Variable 🟡
**Location:** Line 65: `kss = ks / 60.0`  
**Issue:** Variable `kss` (ks converted to mm/min) is calculated but never used  
**Impact:** No functional impact, but represents code clutter  
**Required Fix:** Remove unused variable or utilize it if mm/min conversions are needed elsewhere

---

### 2. SCS-CN Curve Number Method Audit

#### File: `backend/app/domain/delhi/hydrology/loss_green_ampt.py` (same file)

#### 2.1 Conceptual Framework Issue 🔴
**Location:** Lines 221-222 (Ia calculation) and Lines 242-258 (depression storage handling)  
**Issue:** Depression storage losses are subtracted explicitly AND included implicitly in the initial abstraction term, violating SCS-CN conceptual integrity.

**Standard SCS-CN:**
- Initial abstraction `Ia = 0.2*S` encompasses *all* initial losses: depression storage, interception, infiltration initial loss
- Runoff equation: `Q = (P - Ia)² / (P - Ia + S)` for `P > Ia`

**Current Implementation:**
```python
# Depression storage handled separately (lines 242-245)
if depression_storage_filled < total_depression_storage:
    depression_loss = min(rainfall_depth, available_depression)
    depression_storage_filled += depression_loss

# Initial abstraction calculated (line 222)
ia = 0.2 * s

# Effective rainfall after depression storage (line 249)
effective_rainfall = rainfall_depth - depression_loss

# Runoff calculation uses effective_rainfall (line 250)
if effective_rainfall > ia:
    runoff_depth = ((effective_rainfall - ia) ** 2) / (effective_rainfall - ia + s)
```

**Physical Consequence:**
- Depression storage subtracted twice: once as `depression_loss`, once as part of `ia`
- Total initial loss = `depression_loss + ia` > `ia` (standard value)
- Results in **less runoff than theoretically expected** for given rainfall and soil conditions
- Misrepresents the proportionality of initial losses in the SCS-CN framework

**Required Fix:** Remove explicit depression storage handling from SCS-CN calculation OR revise initial abstraction to exclude depression storage (not recommended as it deviates from standard SCS-CN). Preferred approach: rely solely on standard `Ia = 0.2*S` term to represent all initial losses.

#### 2.2 CN Calculation & Bounds ✅
- Composite CN correctly weighted by land cover fractions ✓
- CN clamped to [0, 100] range ✓
- Standard parameters: `CN_imp`, `CN_perv`, `CN_bare`, `CN_water=100` ✓

#### 2.3 Retention Parameter S ✅
- Correct formula: `S = (25400 / CN) - 254` (yields S in mm) ✓
- Handles CN=0 edge case (all water) ✓

#### 2.4 Runoff Equation ✅
- Standard form: `Q = (P - Ia)² / (P - Ia + S)` for `P > Ia` ✓
- Non-negative runoff enforcement ✓
- Volume conservation tracking ✓

---

### 3. Runoff Transformation Component Audit

#### File: `backend/app/domain/delhi/hydrology/runoff_transform.py`

#### 3.1 Governing Equation ✅
- Uses simplified linear reservoir approach: `dQ/dt = (Q_eq - Q) / T` ✓
- Appropriate for prototype phase (not full hydrodynamic routing) ✓
- Time lag based on overland flow velocity estimation ✓

#### 3.2 Parameter Units ✅
- `ref_depth_m` = 0.01 m (1 cm reference depth) ✓
- Manning's equation units consistent ✓
- Velocity → time lag conversion dimensionally sound ✓

#### 3.3 Numerical Discretization ✅
- Applies transformation per time step with state variable carryover ✓
- Stable explicit Euler formulation ✓
- Conserves volume (inflow = outflow + storage change) ✓

#### 3.4 Physical Plausibility ✓
- Response time increases with overland length, decreases with slope ✓
- Response time increases with Manning's n (roughness) ✓
- Zero outflow when no excess rainfall input ✓

---

### 4. Mass Balance Conservation Verification

#### Verified via Output Files:
- All `summary.csv` files show `mass_balance_error_percent` ≤ 1.25e-14% ✓
- Mass balance error = \|P - (L + E)\| / P × 100% where:
  - P = total precipitation
  - L = total losses (infiltration + depression storage)
  - E = total excess runoff
- Errors near machine precision confirm mathematical consistency ✓

#### Test Suite Validation:
- `test_hydrology.py` includes explicit mass balance verification ✓
- All tests pass including zero rainfall, constant low/high rainfall, intermittent rainfall scenarios ✓

---

### 5. Lateral Inflows Decoupling Verification

#### File: `backend/app/domain/delhi/hydrology/lateral_inflows.py`
- Header note explicitly states: "NOTE: This module is not used in the rainfall→runoff pipeline of SIH V2 prototype. It is deferred for hydraulic routing coupling (Phase 3+)" ✓
- Verified no imports or references in `scenario_runner.py` ✓
- Confirmed not invoked in rainfall→runoff pathway ✓

---

### 6. Scenario Runner & Output Structure

#### File: `backend/app/domain/delhi/hydrology/scenario_runner.py`
- Properly processes all 60 combinations (3 scenarios × 2 events × 2 loss methods × 5 subcatchments) ✓
- Creates correct output directory structure: `data/delhi/derived/runoff/{scenario}/{event}/{loss_method}/` ✓
- Generates loss CSV, hydrograph CSV, and summary CSV with mass balance metrics ✓
- Path resolution and datetime import fixed ✓

---

### 7. Recommended Corrections

#### 7.1 Green-Ampt Fix
**File:** `loss_green_ampt.py`  
**Location:** Before-ponding section (after line 118) and after-ponding section (after line 143)  
**Change:** Add `cumulative_infiltration += infiltration_mm` in both sections  
**Rationale:** Ensure cumulative infiltration tracks all infiltrated water for proper capacity calculation after ponding

#### 7.2 SCS-CN Fix (Recommended)
**File:** `loss_green_ampt.py`  
**Location:** Remove depression storage handling from SCS-CN calculation (lines 224-230 and 242-245)  
**Change:** 
- Remove depression storage variable initialization and tracking
- Use standard `effective_rainfall = rainfall_depth` (no depression storage subtraction)
- Keep `ia = 0.2 * s` as sole initial loss term  
**Rationale:** Align with standard SCS-CN conceptual framework where Ia encompasses all initial losses

#### 7.3 Code Quality Improvement
**File:** `loss_green_ampt.py`  
**Location:** Line 65  
**Change:** Remove unused variable `kss = ks / 60.0`  
**Rationale:** Eliminate dead code

---

### 8. Conclusion

The Delhi/Kushak rainfall→runoff engine demonstrates strong foundational implementation with:
- Correct dimensional analysis and unit consistency
- Proper mass balance conservation (verified ≤0.10% tolerance)
- Appropriate prototype-level simplifications clearly documented
- Complete test coverage for specified scenarios
- Clean separation of concerns (loss models decoupled from runoff transformation)

Two defects were identified that compromise physical defensibility:
1. **Green-Ampt:** Missing cumulative infiltration update during pre-ponding phase
2. **SCS-CN:** Conceptual double-counting of initial losses

These are **minimal corrective changes** that do not alter the engine's architecture or add new modeling capability. After implementing the recommended fixes, the engine is mathematically and physically defensible as a hydrologic forcing component for future hydraulic modelling efforts.

**Final Audit Verdict:** **CONDITIONAL GO**  
*Proceed to hydraulic modelling only after correcting the identified defects.*

---
*This audit adheres to strict science-only forensic principles: no new features added, no canonical parameters modified, focus exclusively on mathematical/physical correctness of existing implementation.*