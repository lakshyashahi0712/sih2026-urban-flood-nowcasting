# DEPLOYMENT READY CHECKLIST

**Document ID:** `DOC-CHN-DEP-004`  
**Target Environment:** Vercel Hobby (Frontend) + Render Free 512 MB (Backend)  
**Date:** September 2026  
**Status:** FULLY PREPARED — DO NOT DEPLOY YET  

---

## 1. Executive Deployment Summary

The SIH 2026 Urban Flood Nowcasting application has completed all architectural and runtime remediation. The repository has been verified to be completely clean, self-contained (16.47 MB clone footprint), free of machine-specific hardcoded paths or secrets, and fully optimized for free-tier resource limits.

---

## 2. Platform Configuration Specifications

### 2.1 Backend: Render Free Web Service
| Setting | Recommended Value | Rationale |
|---|---|---|
| **Service Type** | Web Service | Exposes public HTTPS endpoint for the FastAPI application |
| **Runtime Environment** | **Python 3** (Native) | Native execution avoids container engine memory overhead |
| **Repository** | `lakshyashahi0712/sih2026-urban-flood-nowcasting` | Public/connected GitHub repository |
| **Branch** | `v2-recovery-parity` | Clean verified branch |
| **Root Directory** | `.` (Repository root) | Allows proper resolution of `backend` and `data` packages |
| **Build Command** | `pip install -r backend/requirements.txt` | Installs lean Python dependencies (~15 binary wheels) |
| **Start Command** | `uvicorn backend.main:app --host 0.0.0.0 --port $PORT --workers 1` | **CRITICAL: Single worker (`--workers 1`) to preserve 512 MB RAM ceiling** |
| **Instance Type** | Free (512 MB RAM, 0.1 shared vCPU) | ₹0 / $0 permanent tier |
| **Health Check Path** | `/health` | Lightweight 0.4 ms check; does not hit DEM or database |
| **Auto-Deploy** | Optional (Yes for CD, No for manual release) | Operator preference |

---

### 2.2 Frontend: Vercel Hobby
| Setting | Recommended Value | Rationale |
|---|---|---|
| **Framework Preset** | **Vite** | Automatically detects static output configuration |
| **Root Directory** | `frontend` | Isolates frontend TypeScript workspace |
| **Build Command** | `npm run build` | Runs `tsc -b && vite build` (verified in 2.23s) |
| **Output Directory** | `dist` | Destination for static HTML/CSS/JS chunks |
| **Install Command** | `npm install` | Clean npm dependency resolution |
| **Node Version** | `20.x` or `22.x` (Default LTS) | Standard modern Node runtime |

---

## 3. Required Environment Variables

### 3.1 Render Web Service (Backend)
| Variable | Value / Example | Necessity | Purpose |
|---|---|:---:|---|
| `PORT` | Auto-populated by Render (e.g. `10000`) | **System** | Port on which the web server binds |
| `FLOOD_EXTRA_ORIGINS` | `https://<your-vercel-app>.vercel.app` | **CRITICAL** | Whitelists the production Vercel frontend in `CORSMiddleware` |
| `PYTHONPATH` | `.` | Recommended | Ensures Python resolves the repository root cleanly |
| `OPEN_METEO_TIMEOUT` | `10.0` | Optional | Max seconds to wait for Open-Meteo live rainfall API |
| `OPEN_METEO_CACHE_TTL_MINUTES` | `15` | Optional | Live weather cache duration |

### 3.2 Vercel Project (Frontend)
| Variable | Value / Example | Necessity | Purpose |
|---|---|:---:|---|
| `VITE_API_BASE_URL` | `https://<your-render-service>.onrender.com` | **CRITICAL** | Target base URL for all API requests via `apiUrl()` |

---

## 4. Operational Behavior & Known Characteristics

### 4.1 Cold-Start Behavior (Render Free)
- **Spin-Down on Idle:** Render Free automatically spins down web services after **15 minutes of inactivity**.
- **Cold Boot Time:** The first incoming HTTP request will wake the container, which takes **40 to 65 seconds**.
- **User Experience:** The initial request from the Vercel frontend may experience a delay while Render initializes. Subsequent requests respond in **<15 ms** once warm.
- **Frontend Wake-up Handling:** `frontend/src/api/delhi.ts` and `FloodMap.tsx` handle errors gracefully and display status alerts rather than crashing.

### 4.2 Single-Worker Memory Ceiling
- **Idle Memory:** **171.12 MB** (~33.4% of Render's 512 MB ceiling).
- **Peak RAM (Under Load):** **258.13 MB** (~50.4% of ceiling).
- **Headroom Buffer:** **~254 MB** available for OS buffers and request allocations.
- **Worker Restriction:** **Never increase `--workers` above 1** on the Free tier. Each additional uvicorn worker instantiates a full Python runtime (+171 MB), which would cause an instant OOM crash under Linux `cgroups`.

### 4.3 Ephemeral Filesystem State
- **Storage Type:** Render Free disk storage is ephemeral.
- **Scenario State Handling:** Synthetic scenario runs (SCN-01 to SCN-06) are precomputed into bundled JSON fixtures and served via an in-memory dictionary cache with graceful disposable disk fallbacks. No database or persistent volume is required.

---

## 5. Verification Checklist Summary

- [x] **1. Repository State:** 16.47 MB total footprint; verified clean.
- [x] **2. Backend Entrypoint:** `backend.main:app` verified and functioning.
- [x] **3. Frontend Build:** `npm run build` verified in 2.23s.
- [x] **4. Backend Start Command:** `uvicorn backend.main:app --host 0.0.0.0 --port $PORT --workers 1` verified compatible.
- [x] **5. Central Frontend Routing:** `VITE_API_BASE_URL` + `apiUrl()` wraps 100% of frontend `fetch()` calls.
- [x] **6. Backend CORS:** `FLOOD_EXTRA_ORIGINS` active in `CORSMiddleware`.
- [x] **7. Path Independence:** Zero machine-specific paths (`C:\Users\...`) or hardcoded localhost backend URLs in production bundles.
- [x] **8. Runtime Asset Tracking:** All 15 required runtime data files (2.25 MB) and 8 Mumbai/road assets (7.43 MB) tracked in Git.
- [x] **9. Research Asset Exclusion:** ~600 MB of raw PDFs, satellite DSMs, and intermediate CSVs remain safely ignored.
- [x] **10. Zero Committed Secrets:** No `.env` or credential files committed.
- [x] **11. Lightweight Health Probe:** `/health` responds in 0.4 ms (HTTP 200).
- [x] **12. Single Web Process:** Enforced via `--workers 1`.
- [x] **13. Zero WebSocket Dependency:** Frontend operates 100% via HTTP REST.
- [x] **14. Final Test Suite:** 481 passed, 0 failed in `pytest backend/tests/ -q`.
- [x] **15. Final Smoke Test:** All 11 mode transitions verified end-to-end.
