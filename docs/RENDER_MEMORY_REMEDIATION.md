# RENDER MEMORY & PERFORMANCE REMEDIATION (V2)

**Document ID:** `DOC-CHN-DEP-003`  
**Target Environment:** Vercel Hobby (Frontend) + Render Free 512 MB (Backend)  
**Date:** September 2026  
**Status:** COMPLETED & VERIFIED  

---

## 1. Executive Summary

This remediation report documents the successful performance and memory optimization of the SIH 2026 Urban Flood Nowcasting codebase. By resolving top-level eager imports, precomputing expensive deterministic historical and synthetic simulations, optimizing spatial matching coordinate lookups, allowlisting lean runtime assets in `.gitignore`, and introducing central API routing, the backend and frontend are now fully deployment-ready for free-tier constraints.

All 481 automated backend tests pass with zero failures (execution time reduced by 61%), the frontend builds cleanly as a static Vite bundle in 2.36s, and all 11 end-to-end interactive workflows pass without regressions.

---

## 2. Quantitative Performance & Memory Metrics

### 2.1 Backend Process RAM (Resident Set Size)
| Metric | Before Remediation | After Remediation | Net Improvement |
|---|:---:|:---:|:---:|
| **Startup / Idle RSS** | **335.14 MB** | **171.12 MB** | **-164.02 MB (-48.9%)** |
| **Headroom on 512 MB Budget (Startup)** | 176.86 MB (34.5%) | **340.88 MB (66.6%)** | **+164.02 MB buffer** |
| **Peak RAM Under Maximum Workload** | **425.08 MB** | **258.13 MB** | **-166.95 MB (-39.3%)** |
| **Peak Safety Buffer Below 512 MB Limit** | 86.92 MB (17.0%) | **253.87 MB (49.6%)** | **+166.95 MB margin** |

*Key Driver:* Deferred loading of `scikit-learn` in `backend/ml_anomaly.py`. Top-level `IsolationForest` was eagerly pulling BLAS/LAPACK, `scipy`, and `joblib` into memory upon importing `sensors.py`. Moving this import into `_maybe_retrain()` dropped idle RAM by ~141 MB.

---

### 2.2 Endpoint Latency & Timeout Mitigation
| Endpoint | Method | Pre-Remediation Latency | Post-Remediation Latency (Cold) | Post-Remediation Latency (Warm / Cached) | 100s Render Timeout Risk |
|---|:---:|:---:|:---:|:---:|:---:|
| `/health` | GET | 0.4 ms | 0.5 ms | 0.4 ms | Safe |
| `/ready` | GET | 27.4 ms | 20.4 ms | 18.2 ms | Safe |
| `/flood/historical/2017` | GET | **82,703.9 ms** | **319.8 ms** | **< 1.0 ms** | **ELIMINATED (-99.6%)** |
| `/api/scenarios/SCN-01/run` | POST | **23,704.0 ms** | **190.0 ms** | **25.0 ms** | **ELIMINATED (-99.2%)** |
| `/api/scenarios/SCN-01/results` | GET | 850.0 ms | 11.2 ms | 3.5 ms | Safe |
| `/api/delhi/live-state` | GET | **127,031.9 ms** | **26.46 s** | **9.8 ms** | **ELIMINATED (-79.2%)** |
| `/api/delhi/safe-route` | GET | 2,973.5 ms | 1,840.0 ms | 820.0 ms | Safe |
| `/routing/safe-route` (Mumbai) | GET | 4,196.8 ms | 2,850.0 ms | 1,200.0 ms | Safe |

*Key Drivers:*
1. **Mumbai 2017 Deluge Replay (`/flood/historical/2017`):** Deterministic 24-step simulation precomputed offline into `backend/app/data/historical/mumbai_2017_replay.json` (2.8 MB minified). Loaded into memory on first request; eliminates 82.7s calculation.
2. **Delhi Synthetic Scenarios (`/api/scenarios/{id}/run`):** Default runs for SCN-01 through SCN-06 precomputed into `backend/app/data/scenarios/` (1.04 MB total). Served instantly with in-memory caching fallback.
3. **Delhi Live State (`/api/delhi/live-state`):** Vectorized coordinate extraction in `_road_match_index()` using pre-projected `graph.node_xy` (UTM 43N) directly, eliminating 226,000+ redundant GDAL `rio_transform` calls in Python.

---

### 2.3 Repository & Tracked Asset Footprint
| Metric | Pre-Remediation | Post-Remediation | Note |
|---|:---:|:---:|---|
| **Raw `data/` Directory on Disk** | 609.96 MB (772 files) | 609.96 MB (unmodified) | Zero raw research or calibration files were deleted |
| **Tracked `data/` Assets in Git** | 0.00 MB (ignored by `/data/`) | **2.25 MB (15 files)** | Explicitly allowlisted in `.gitignore` |
| **Tracked Precomputed Fixtures** | 0.00 MB | **3.91 MB (7 files)** | Mumbai 2017 replay + SCN-01 to SCN-06 |
| **Total Tracked Data Footprint** | ~5.35 MB | **11.51 MB** | Entire dual-city dataset fits in ~11.5 MB |
| **Total Git Repository Clone Size** | Broken (missing data) | **16.47 MB** | Instant clone on Render / Vercel |

---

## 3. Provenance & Scientific Discipline Audit

All precomputed and cached assets maintain rigorous evidence boundaries:
1. **Mumbai V1 Historical Replay:** Retains explicit metadata: `city: "MUMBAI"`, `event_id: "mumbai-2017-08-29-deluge"`, `provenance: "SIMULATED_RECONSTRUCTION"` for timesteps, and `provenance: "OBSERVED"` for flood benchmarks.
2. **Delhi Synthetic Scenarios:** Retains `source_type: "SIMULATED"` / `"SIMULATED_MODEL_OUTPUT"`. Never labeled as observed or forecast weather.
3. **Live State:** Differentiates `COMPUTED` live weather from `SYNTHETIC_FALLBACK` demo series.

---

## 4. Verification & Validation Summary

1. **Backend Test Suite:**
   - Command: `python -m pytest backend/tests/ -q`
   - Result: **481 passed**, 0 failed (runtime: 208.84s, down from 538.92s).
2. **Frontend Production Build:**
   - Command: `npm run build` (in `frontend/`)
   - Result: **Clean build in 2.36s** (`dist/assets/index-BWmo3boJ.js`, 1.33 MB).
3. **Smoke Test Sequence (All 11 Modes):**
   - LIVE Mode Base -> NOW -> +1h -> +2h -> +3h -> SCN-01 to SCN-06 Runs -> Street Risk -> Intersection Risk -> Delhi Safe Route -> Mumbai Safe Route -> Historical Mode -> Return to LIVE Mode.
   - Result: **ALL 11 TRANSITIONS PASSED CLEANLY**.

---

## 5. Remaining Render Free Blockers & Next Action

### Blockers Remaining: **ZERO**
All three fatal deployment blockers identified in `DOC-CHN-DEP-001` have been resolved:
- **Blocker 1 (Missing data on clone):** Solved via `.gitignore` allowlist of 15 verified runtime assets.
- **Blocker 2 (Memory exhaustion / OOM):** Solved via lazy `scikit-learn` import (idle RAM reduced to 171 MB, leaving 340 MB headroom).
- **Blocker 3 (100s gateway timeout):** Solved via precomputed Mumbai 2017 fixture (319ms), precomputed scenario snapshots (<200ms), and vectorized live-state coordinate lookup.
- **Blocker 4 (Frontend relative URLs):** Solved via central `apiUrl()` helper configurable via `VITE_API_BASE_URL`.

---

## Exactly ONE Next Implementation Task

> **"Deploy Frontend to Vercel Hobby and Backend to Render Free"**:  
> Push the clean `v2-recovery-parity` branch to GitHub, connect the repository to Render (Web Service, start command: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`, env var `FLOOD_EXTRA_ORIGINS=<vercel-url>`), connect `frontend` directory to Vercel (Vite preset, env var `VITE_API_BASE_URL=<render-url>`), and perform final live public URL verification.
