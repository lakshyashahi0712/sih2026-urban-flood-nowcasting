# FREE DEPLOYMENT COMPATIBILITY AUDIT (V2)

**Document ID:** `DOC-CHN-DEP-001`  
**Target Architecture:**  
- **Frontend:** Vercel Hobby (Static Vite deployment)  
- **Backend:** Render Free Web Service (512 MB RAM, 0.1 shared vCPU, public HTTPS URL)  
**Date:** September 2026  
**Audit Status:** COMPLETE  

---

## 1. Overall Deployment Status

### **NOT READY (Without Critical Remediation)**

The current V2 application **CANNOT be successfully deployed in its current state** on Vercel Hobby + Render Free due to three fatal blockers:
1. **Repository / Dataset Missingness on Git Clone:** The `/ready` probe and core V2 routes (`/api/delhi/events`, `/api/delhi/surface`, `/api/delhi/nowcast`) require specific derived files in `data/delhi/derived/`. However, `.gitignore` excludes `/data/` entirely (610 MB of research docs, raw GeoTIFFs, and logs). When Render clones the repository from GitHub, the `data/` directory does not exist, causing `/ready` to report `NOT_READY` and endpoints to fail.
2. **512 MB RAM Ceiling vs 335 MB Idle Footprint:** The backend's idle memory footprint upon startup is **335.1 MB** (65.4% of Render's 512 MB total budget). A single request to `/flood/historical/2017` or `/api/delhi/live-state` drives process RAM to **404–425+ MB** (83% of limit). Any concurrent traffic or minor buffer spike will trigger Linux OOM Killer (`SIGKILL`).
3. **HTTP 100-Second Gateway Timeout:** Render Free enforces a hard **100-second HTTP request timeout**. Under local multi-core testing, `GET /api/delhi/live-state` takes **127.0 seconds** and `GET /flood/historical/2017` takes **82.7 seconds**. On Render Free's throttle of **0.1 vCPU**, these computations will take 3 to 10 minutes, guaranteeing **504 Gateway Timeouts**.
4. **Frontend Relative URL Disconnect:** The frontend API client in `frontend/src/api/delhi.ts` and `FloodMap.tsx` makes relative requests (`/api/...`, `/flood/...`), which rely on Vite's development proxy (`vite.config.ts`). On a static Vercel deployment, requests go to the Vercel domain instead of the Render backend URL unless a rewrite proxy or base URL environment variable is configured.

**Path to "READY WITH OPTIMIZATION":**  
The application can be made deployable on free tiers by bundling only the small runtime data assets (<15 MB), precomputing deterministic offline simulations (such as the 2017 historical replay and synthetic scenario runs), and configuring an environment variable for the backend URL.

---

## 2. Detailed Technical Audit (Questions 1 – 23)

### 1. Exact Frontend Build Command
```bash
npm run build
```
Defined in `frontend/package.json`: `"build": "tsc -b && vite build"`.  
On Vercel:
- **Root Directory:** `frontend`
- **Build Command:** `npm run build`
- **Output Directory:** `dist`
- **Install Command:** `npm install`
- **Build Timing:** ~2.5 seconds (verified locally).

### 2. Exact Backend Start Command
On Render (from repository root):
```bash
uvicorn backend.main:app --host 0.0.0.0 --port $PORT
```
*Note:* Render dynamically assigns a port via the `$PORT` environment variable (typically 10000). If running with Root Directory set to `backend`, the command is `uvicorn main:app --host 0.0.0.0 --port $PORT`.

### 3. Exact FastAPI Entrypoint
```python
backend.main:app
```
(Defined in `backend/main.py` as `app = FastAPI(...)`).

### 4. All Localhost URLs in Codebase
- `frontend/vite.config.ts` (Line 5):  
  `const API_TARGET = process.env.VITE_API_TARGET || 'http://localhost:8000'`
- `backend/main.py` (Lines 78–81):  
  `"http://localhost:5173"`, `"http://127.0.0.1:5173"`, `"http://localhost:4173"`, `"http://127.0.0.1:4173"`

### 5. All Hardcoded Local Filesystem Paths
No machine-specific absolute paths (e.g. `C:\Users\...`) exist in active code. However, multiple modules construct paths relative to `_REPO_ROOT = Path(__file__).resolve().parents[N]` expecting an on-disk `data/` folder:
- `backend/database.py`: `DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "water_monitor.db")`
- `backend/app/config.py`: `dem_path = ... / "data" / "dem" / "mumbai_pilot_dem_30m.tif"`
- `backend/main.py`: lines 138, 146, 154 check:
  - `data/delhi/derived/validation/kushak_historical_events.csv`
  - `data/delhi/derived/hydraulic/kushak_corridor_centerline.geojson`
  - `backend/app/data/dem/mumbai_pilot_dem_30m.tif`
- `backend/routers/delhi.py`: `DATA_DIR = _REPO_ROOT / "data" / "delhi" / "derived"`
- `backend/app/domain/delhi/surface.py`: `DEM_PATH = _REPO_ROOT / "data" / "delhi" / "derived" / "dem" / "kushak_enforced_dem_burn1m.tif"`
- `backend/app/domain/delhi/scenarios/engine.py`: `_SCENARIO_RUN_ROOT = ... / "data" / "delhi" / "derived" / "scenarios"`
- `backend/app/domain/delhi/replay_artifacts.py`: `ARTIFACTS_DIR = ... / "data" / "delhi" / "derived" / "reconstruction" / "historical"`

### 6. All Required Environment Variables
#### Backend (Render Free)
| Variable | Required? | Default / Example | Purpose |
|---|:---:|---|---|
| `PORT` | Auto | Provided by Render (`10000`) | Web server listening port |
| `FLOOD_EXTRA_ORIGINS` | **CRITICAL** | `https://your-frontend.vercel.app` | Grants CORS permission to the Vercel frontend |
| `PYTHONPATH` | Recommended | `.` | Ensures `backend` package is resolvable |
| `OPEN_METEO_TIMEOUT` | Optional | `10.0` | Inflow forecast API timeout |
| `OPEN_METEO_CACHE_TTL_MINUTES` | Optional | `30` | Inflow forecast cache duration |
| `DEBUG` | Optional | `False` | Verbose logging toggle |

#### Frontend (Vercel Hobby)
| Variable | Required? | Default / Example | Purpose |
|---|:---:|---|---|
| `VITE_API_BASE_URL` | **CRITICAL** | `https://your-backend.onrender.com` | Base URL for cross-origin backend requests |

### 7. Complete Python Dependency List
From `backend/requirements.txt`:
1. `fastapi>=0.111,<1.0`
2. `uvicorn[standard]>=0.30,<1.0`
3. `sqlalchemy>=2.0,<3.0`
4. `pydantic>=2.7,<3.0`
5. `pydantic-settings>=2.0,<3.0`
6. `numpy>=2.1,<3.0`
7. `scikit-learn>=1.5,<2.0`
8. `pandas>=2.2,<3.0`
9. `websockets>=12`
10. `python-dotenv>=1.0`
11. `httpx>=0.27,<1.0`
12. `pytest>=8.0,<9.0`
13. `pytest-asyncio>=0.23,<1.0`
14. `shapely>=2.0,<3.0`
15. `rasterio>=1.3,<2.0`

### 8. Approximate Backend Startup RAM Usage
- **Base Python Runtime:** 15.40 MB
- **After Importing `backend.main`:** **333.07 MB** (+317.67 MB)
- **After FastAPI Lifespan Initialization:** **335.14 MB** (+2.07 MB)
- **Primary Drivers:** Heavy scientific libraries (`scikit-learn`, `rasterio` / GDAL, `pandas`, `shapely`, `numpy`) loaded eagerly into memory at import time.

### 9. Approximate RAM Usage for Largest Flood-Model Request
- **`/flood/historical/2017`:** Process RAM expands to **425.08 MB** (+35.0 MB working set allocation).
- **`/api/delhi/live-state`:** Process RAM expands to **404.20 MB** (+137.9 MB working set allocation).
- **Total Headroom Remaining on Render 512 MB Free Tier:** Only **~86.9 MB** (16.9% safety margin).

### 10. Most Expensive Computation Endpoints
1. `GET /api/delhi/live-state`: Full hydrologic-to-hydraulic chain, reach state propagation, live D8 surface routing pass with DEM raster manipulation across the corridor window.
2. `GET /flood/historical/2017`: Multi-hour continuous dynamic flood routing simulation across the 30m Mumbai DEM grid.
3. `POST /api/scenarios/{scenario_id}/run`: Multi-step synthetic storm hydrograph routing with D8 depression storage tracking.
4. `GET /flood/forecast`: 2D DEM overland flow propagation.

### 11. Execution Time of Endpoints (Measured Locally)
| Endpoint | Method | Local Latency | Estimated on 0.1 vCPU Render | Status / Risk |
|---|:---:|:---:|:---:|---|
| `/health` | GET | 0.4 ms | < 5 ms | Safe |
| `/ready` | GET | 27.4 ms | < 50 ms | Safe (if files exist) |
| `/api/delhi/status` | GET | 203.4 ms | ~ 500 ms | Safe |
| `/api/delhi/network` | GET | 7.5 ms | < 20 ms | Safe |
| `/api/delhi/events` | GET | 29.2 ms | < 50 ms | Safe |
| `/api/delhi/nowcast` | GET | 2,097.4 ms | 4 – 8 s | Safe (Open-Meteo network dependent) |
| `/routing/safe-route` | GET | 2,973.5 ms | 5 – 10 s | Safe |
| `/flood/streets/forecast` | GET | 4,147.8 ms | 8 – 15 s | Moderate |
| `/flood/forecast` | GET | 10,014.5 ms | 20 – 40 s | High risk |
| `POST /api/scenarios/SCN-01/run` | POST | 23,704.0 ms | 45 – 90 s | High risk |
| `GET /flood/historical/2017` | GET | **82,703.9 ms** | **150 – 300 s** | **CRITICAL: TIMEOUT (100s limit)** |
| `GET /api/delhi/live-state` | GET | **127,031.9 ms** | **250 – 500 s** | **CRITICAL: TIMEOUT (100s limit)** |

### 12. Computations That Can Be Cached / Precomputed
- **`/flood/historical/2017`:** 100% historical and deterministic. Can be precomputed once offline into a static JSON payload (~150 KB), reducing response time from 83s to <10ms and saving ~35 MB of RAM.
- **`POST /api/scenarios/{scenario_id}/run`:** Scenarios have fixed seeds and deterministic inputs. All 6 scenarios (SCN-01 to SCN-06) can be pre-generated into `sim-{id}.json` files, making run and retrieval instantaneous.
- **`/api/delhi/live-state`:** The D8 surface flow structure is already cached via `@lru_cache(maxsize=1)`. The response payload can be cached in memory with a 15-minute TTL tied to Open-Meteo forecast updates.
- **GeoJSON Layers (`/api/delhi/geo/{layer_id}`):** Static files; can be cached in memory on first read.

### 13. Largest Bundled Data Files
Total `/data/` directory size: **609.96 MB** (772 files).
- **Not Needed at Runtime (Exclude from Git/Deployment):**
  - Raw PDF reports: `ndmc_council_meeting_...pdf` (118.2 MB), `appendixxii.pdf` (40.5 MB), `iitd_dmp_...pdf` (13.0 MB).
  - Unused large rasters: `ESA_WorldCover_...Map.tif` (86.9 MB), `Copernicus_DSM_...DEM.tif` (39.8 MB), `kushak_dsm_utm44n.tif` (49.5 MB).
  - Raw research tables: `sampled_evaluations_2024.csv` (12.2 MB), `behavioral_sets_2024.csv` (12.2 MB).
- **Runtime-Critical Data Files (Must Be Bundled, Total < 10 MB):**
  - `data/delhi/derived/dem/kushak_enforced_dem_burn1m.tif` (**1.14 MB**)
  - `backend/app/data/dem/mumbai_pilot_dem_30m.tif` (**1.21 MB**)
  - `data/delhi/derived/hydraulic/kushak_corridor_centerline.geojson` (**10 KB**)
  - `data/delhi/derived/hydraulic/kushak_cross_sections.geojson` (**22 KB**)
  - `data/delhi/derived/watershed/kushak_watershed.geojson` (**12 KB**)
  - `data/delhi/derived/validation/kushak_historical_events.csv` (**2 KB**)
  - `data/delhi/derived/validation/gsdl_waterlogging/gsdl_waterlogging_normalized_occurrences.geojson` (**44 KB**)
  - `data/delhi/derived/hydraulic/historical_reconciliation/kushak_historical_landmarks.geojson` (**18 KB**)
  - `data/roads/mumbai_pilot_roads.geojson` (**480 KB**)

### 14. Frontend Static Vite Site Compatibility
- **YES.** `npm run build` outputs pure static HTML, CSS, and JS chunks to `frontend/dist/`.
- Vercel Hobby serves this natively with zero server-side Node runtime requirement.
- However, relative URLs currently hardcoded in `delhi.ts` and `FloodMap.tsx` require either `vercel.json` rewrites or a `VITE_API_BASE_URL` configuration.

### 15. CORS Configuration for Vercel
- **YES.** `backend/main.py` uses `CORSMiddleware` with `_EXTRA_ORIGINS = os.environ.get("FLOOD_EXTRA_ORIGINS", "").split(",")`.
- Configuring `FLOOD_EXTRA_ORIGINS=https://<your-vercel-domain>.vercel.app` on Render allows the Vercel app to make cross-origin requests.
- `allow_credentials=True` is enabled; credentials work because specific origins are passed (not wildcard `*`).

### 16. WebSockets / Socket.IO Requirements
- **NO.**
- While `backend/main.py` defines a legacy `@app.websocket("/ws")` route from an earlier sensor prototype, **zero frontend components connect to it**.
- Neither `DelhiApp.tsx` nor `FloodMap.tsx` imports or initiates WebSocket connections. The application is entirely HTTP REST.

### 17. Local Filesystem Write Operations
- `POST /api/scenarios/{scenario_id}/run` writes JSON simulation results to `data/delhi/derived/scenarios/{run_id}.json`.
- `backend/database.py` creates and writes to `water_monitor.db` (SQLite).
- *Render Free Reality:* Disk storage is ephemeral. Any file written to disk is erased when the container spins down or redeploys.

### 18. SQLite / Local Database Usage
- `backend/database.py` defines SQLite (`water_monitor.db`).
- It is initialized at startup via `init_db()`.
- However, the flood nowcasting engine, routing engine, and Delhi V2 digital twin do **not** query `water_monitor.db`. It is a legacy leftover from the AquaSense IoT demo.

### 19. Persistent Local Storage Assumptions
- The application does not assume persistent storage for its core read-only nowcasting operations.
- Dynamic scenario runs assume result files persist across requests; on Render Free, in-memory caching or precomputation is required.

### 20. Likelihood of Backend Fitting in Render 512 MB RAM
- **HIGH FAILURE RISK.**
- Baseline consumption is **335 MB** (65% of RAM).
- Peak single-request consumption hits **425 MB** (83% of RAM).
- Any concurrent traffic or memory fragmentation under Linux glibc will trigger an instantaneous OOM crash.

### 21. Linux Deployment Issues with Dependencies
- `rasterio` and `shapely`: Both provide binary `manylinux` wheels with pre-compiled GDAL and GEOS C-libraries. They install cleanly on Render without requiring system package manager (`apt-get install gdal-bin`).
- However, `rasterio` wheels are large (~45 MB), increasing cold-start build times.

### 22. Can Current Application Work Without Docker?
- **YES.** Render provides a native Python 3 runtime.
- Build command: `pip install -r backend/requirements.txt`
- Start command: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
- Native Python execution avoids Docker storage layer overhead.

### 23. Background Worker Requirements
- **NOT ARCHITECTURALLY REQUIRED, BUT TIMEOUTS DEMAND MITIGATION.**
- If live simulations (`/api/delhi/live-state` at 127s, `/flood/historical/2017` at 83s) are triggered on demand, they exceed Render's 100s request timeout and would require asynchronous Celery/Redis workers.
- Since Render Free does not offer background workers or Redis, **precomputing and caching these responses as static JSON completely eliminates the need for background workers**.

---

## 3. Risk Matrices

### MEMORY RISKS
| Risk | Severity | Impact | Mitigation |
|---|:---:|---|---|
| **Eager Heavy Imports** | HIGH | Startup consumes 335 MB (65% of RAM) just importing `scikit-learn`, `rasterio`, `pandas`. | Lazy-import heavy science/ML modules only when specific routes are called. |
| **Grid Allocations in Live State** | CRITICAL | 2D D8 raster processing allocates NumPy arrays that spike RAM by +138 MB, reaching 404–425 MB. | Precompute static live-state presets or downsample grid resolution. |
| **Linux glibc Memory Fragmentation** | HIGH | Python heap does not immediately return free memory to the OS on Linux. | Call `malloc_trim(0)` via `ctypes` after heavy computations, or run with single-worker `uvicorn`. |

### CPU RISKS
| Risk | Severity | Impact | Mitigation |
|---|:---:|---|---|
| **Render 0.1 vCPU Throttling** | CRITICAL | 127-second local computation extends to 5–10 minutes, causing instant 100s Gateway Timeout. | Precompute historical events and scenario runs. |
| **Cold Starts** | MEDIUM | Render Free spins down after 15 minutes of inactivity; spin-up takes 50–90 seconds. | Frontend must show friendly loading/wake-up status instead of hard error. |

### FILESYSTEM RISKS
| Risk | Severity | Impact | Mitigation |
|---|:---:|---|---|
| **Missing `data/` Directory on Git Clone** | CRITICAL | `.gitignore` ignores `/data/`, so critical GeoJSON/DEM files will not exist on Render. | Un-ignore and commit only the essential runtime files (<10 MB) into `backend/app/data/`. |
| **Ephemeral Disk Wipes** | LOW | Scenario outputs in `/derived/scenarios/` will be wiped on restart. | Pre-generate scenario runs or store in memory cache. |

### NETWORK / API RISKS
| Risk | Severity | Impact | Mitigation |
|---|:---:|---|---|
| **CORS Rejection** | HIGH | Frontend on Vercel blocked by browser from calling Render backend. | Set `FLOOD_EXTRA_ORIGINS` to the Vercel domain in Render dashboard. |
| **Vercel Hobby Proxy Timeout** | HIGH | Vercel rewrites timeout after 10–15 seconds; cold start of Render backend causes 504 error. | Use direct cross-origin calls via `VITE_API_BASE_URL` with health-probe polling. |

---

## 4. Platform Deployment Requirements

### Frontend (Vercel Hobby)
1. **Framework Preset:** Vite
2. **Root Directory:** `frontend`
3. **Build Command:** `npm run build`
4. **Output Directory:** `dist`
5. **Environment Variable:** `VITE_API_BASE_URL=https://<your-render-service>.onrender.com`
6. **Code Adjustment Needed:** Update `frontend/src/api/delhi.ts` and `FloodMap.tsx` to prepend `import.meta.env.VITE_API_BASE_URL || ''` to fetch URLs.

### Backend (Render Free Web Service)
1. **Environment:** Python 3
2. **Root Directory:** Repository root (`.`)
3. **Build Command:** `pip install -r backend/requirements.txt`
4. **Start Command:** `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
5. **Environment Variables:**
   - `FLOOD_EXTRA_ORIGINS=https://<your-vercel-app>.vercel.app`
   - `PYTHONPATH=.`
6. **Instance Type:** Free (512 MB RAM, 0.1 CPU)

---

## 5. Cache & Precomputation Opportunities

1. **Precompute Mumbai 2017 Historical Replay:**  
   Serialize the output of `/flood/historical/2017` to a static JSON file (`mumbai_2017_replay.json`, ~150 KB). Serve it directly in `routers/flood.py`. Reduces execution from **82.7s to 2ms**, cuts peak RAM by **35 MB**.
2. **Precompute Delhi Synthetic Scenarios (SCN-01 to SCN-06):**  
   Run all 6 scenarios offline and commit their output JSONs to `backend/app/data/scenarios/`. The `/api/scenarios/{id}/run` and `results` endpoints immediately serve the precomputed run.
3. **Precompute Live State Baseline Profiles:**  
   Cache the D8 surface elevation structure and baseline flood states in-memory with a 15-minute TTL.

---

## 6. Critical Blockers Summary

1. **BLOCKER 1:** `.gitignore` ignores all of `/data/`, leaving the backend without its required DEM and GeoJSON layers upon fresh clone on Render.
2. **BLOCKER 2:** Execution times of `/api/delhi/live-state` (127s) and `/flood/historical/2017` (83s) guarantee 100% failure via Render's 100s gateway timeout.
3. **BLOCKER 3:** Frontend fetch calls assume same-origin relative URLs (`/api/...`), which fail on static Vercel hosting unless configured with a backend base URL.
4. **BLOCKER 4:** Baseline 335 MB idle memory leaves inadequate buffer (<90 MB) for on-the-fly 2D hydrodynamic calculations under Render's 512 MB limit.

---

## Exactly ONE Next Implementation Task

To make the current V2 deployable on Vercel + Render Free, the single most critical, high-leverage implementation task is:

> **"Create a Lean Runtime Asset & Precomputed Snapshot Package"**:  
> Bundle the 8 essential runtime GeoJSON/DEM files (<10 MB total) into `backend/app/data/`, precompute the deterministic 2017 Mumbai replay and 6 synthetic scenario runs into static JSON fixtures, and update `frontend/src/api/delhi.ts` to consume a configurable `VITE_API_BASE_URL`.
