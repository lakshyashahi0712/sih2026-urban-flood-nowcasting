# SIH 2026 — Project Implementation Status

## 1. Project Overview
The SIH 2026 Project Statement 26085 aims to build an **Urban Flood Nowcasting System** that predicts where streets and intersections will flood and how deep, 0–3 hours ahead, by coupling rainfall nowcasting with drainage network modeling. The system ingests rainfall forecasts, converts them to runoff, simulates flow through the drainage network to detect surcharges, and routes excess water over the surface to predict flood depths.

Current technical approach:
- **Rainfall nowcasting**: Uses the Open-Meteo API to fetch hourly precipitation forecasts for Mumbai (latitude/longitude from config). The adapter interprets timestamps as Asia/Kolkata local time, converts them to UTC, enforces a 30-minute cache TTL, and rejects negative lead times (forecasts from the past).
- **Drainage network**: Placeholder infrastructure exists; no hydraulic modeling or network topology implemented yet.
- **API layer**: Provides REST endpoints to retrieve the latest rainfall nowcast and cache status.
- **Other systems**: A separate water quality monitoring system (AquaSense) is present in the repository, handling sensor ingestion, anomaly detection, and alerts, but it is not directly part of the flood nowcasting coupling described in the problem statement.

Major system components that exist:
- **Rainfall ingestion layer** (`backend/app/infrastructure/rainfall/open_meteo.py`)
- **Rainfall domain models & exceptions** (`backend/app/domain/rainfall/*`)
- **Rainfall API** (`backend/app/api/rainfall.py`)
- **Drainage infrastructure stub** (`backend/app/infrastructure/drainage/__init__.py`)
- **Water quality monitoring** (sensor APIs, ML anomaly detection, WebSocket streams) — likely a separate project.

## 2. Current Architecture
The current architecture for the flood nowcasting portion is as follows:

1. **API Layer** (`backend/app/api/rainfall.py`):
   - Exposes `GET /rainfall/mumbai` (returns normalized rainfall series) and `GET /rainfall/mumbai/status` (cache status).
   - Uses a module-level `OpenMeteoAdapter` instance.

2. **Domain Layer** (`backend/app/domain/rainfall/`):
   - Pydantic models (`RainfallRecord`, `RainfallSeries`, enums for `SourceType`, `RainfallStatus`).
   - Custom exception types for various failure modes (timeout, HTTP error, parse error, missing field, unit mismatch, timezone mismatch, empty forecast, invalid timestamp).

3. **Infrastructure Layer** (`backend/app/infrastructure/rainfall/open_meteo.py`):
   - `OpenMeteoAdapter` class that fetches data from Open-Meteo API, handles errors, caches responses (30-minute TTL), and normalizes the response.
   - `OpenMeteoCache` simple in-memory cache with TTL enforcement.
   - Normalization interprets timestamps as Asia/Kolkata, converts to UTC, computes lead minutes, validates against negative values.

4. **Drainage Network** (`backend/app/infrastructure/drainage/`):
   - Only an empty `__init__.py` file exists. No models, no simulation logic.

Data flow (for rainfall only):
- Client calls `/rainfall/mumbai` → API calls `adapter.fetch(use_cache=True)` → Adapter attempts live fetch; on success, updates cache and returns live data; on failure (timeout/HTTP error), returns cached data if available (marked STALE); otherwise raises exception.
- Cache is checked for freshness (≤30 minutes) before returning.

No data currently flows into a drainage network model because none is implemented.

## 3. ✅ Implemented

### Rainfall Nowcasting (Open-Meteo Adapter)
- **What was implemented**: A fully functional adapter for the Open-Meteo API that retrieves hourly precipitation forecasts for Mumbai.
- **Important functionality**:
  - Correctly treats input timestamps as Asia/Kolkata local time and converts them to UTC.
  - Enforces a 30-minute cache TTL: cached data older than 30 minutes is ignored.
  - Rejects forecasts with negative lead time (i.e., timestamps earlier than the acquisition time) by raising `RainfallAdapterInvalidTimestamp`.
  - Comprehensive error handling: timeout, HTTP errors, JSON parsing, missing fields, unit mismatches, timezone mismatches, empty forecast, invalid timestamps.
  - Returns `RainfallSeries` objects with metadata (acquired_at, lead minutes, status LIVE/STALE).
- **Relevant files**:
  - `backend/app/infrastructure/rainfall/open_meteo.py`
  - `backend/app/domain/rainfall/models.py`
  - `backend/app/domain/rainfall/exceptions.py`
  - `backend/app/api/rainfall.py` (API endpoints)
- **Tests available**: `backend/tests/test_open_meteo_adapter.py` (14 test cases covering happy path, all error conditions, cache behavior, negative lead time).
- **Current status**: All tests pass (14/14). Verified by running `python -m pytest backend/tests/test_open_meteo_adapter.py`.

### Rainfall API
- **What was implemented**: FastAPI endpoints to expose the rainfall nowcast.
- **Important functionality**:
  - `/rainfall/mumbai` returns JSON with source, acquisition time, record count, resolution, and array of rainfall records (each with timestamp, interval_end, rainfall_mm, etc.).
  - `/rainfall/mumbai/status` returns cache status (LIVE/EMPTY), cached timestamp, TTL, etc.
  - Proper error handling: adapter exceptions are caught and returned as HTTP 503.
- **Relevant files**:
  - `backend/app/api/rainfall.py`
  - `backend/app/config.py` (provides Mumbai coordinates and cache TTL)
- **Tests available**: No dedicated API tests; coverage relies on the adapter tests and manual verification.
- **Current status**: Endpoints are functional and integrated with the tested adapter.

### Domain Models & Exceptions
- **What was implemented**: Provider-independent domain models for rainfall data and a comprehensive exception hierarchy.
- **Important functionality**:
  - `RainfallRecord` includes fields for timestamp (UTC), interval_end, rainfall_mm, source, source_type, resolution, acquired_at, forecast_lead_minutes, status, and derived average intensity.
  - `RainfallSeries` holds a list of records and metadata.
  - Enums for `SourceType` (FORECAST, OBSERVATION, NOWCAST) and `RainfallStatus` (LIVE, STALE, UNAVAILABLE).
  - Exceptions for every anticipated failure mode, each with informative messages.
- **Relevant files**:
  - `backend/app/domain/rainfall/models.py`
  - `backend/app/domain/rainfall/exceptions.py`
- **Tests available**: Indirectly tested via the adapter tests (which use the models and exceptions).
- **Current status**: Models are used by the adapter and API; no separate unit tests but integration verified.

### Configuration
- **What was implemented**: Centralized configuration for the flood nowcasting subsystem.
- **Important functionality**:
  - Settings for Open-Meteo timeout, cache TTL, and Mumbai coordinates.
  - Loads from environment variables via `pydantic-settings`.
- **Relevant files**: `backend/app/config.py`
- **Tests available**: None specific; used by the adapter and API.
- **Current status**: Configuration is functional and imported where needed.

## 4. 🟡 Partially Implemented

### Drainage Network Coupling
- **Current implementation**: A directory `backend/app/infrastructure/drainage/` with only an `__init__.py` file. No models, no simulation logic, no integration with rainfall data.
- **What's missing**:
  - Domain models for drainage network components (nodes, pipes, junctions, outlets).
  - Service to convert rainfall excess to network inflow (requires terrain, imperviousness, catchment delineation).
  - Hydraulic simulation to compute flow through the network, detect surcharges, and compute excess volume.
  - 2D surface routing to predict flood depths on streets/intersections.
  - API endpoints to expose flood nowcast predictions (depth, timing, uncertainty).
  - Integration tests coupling rainfall forecasts to flood predictions.
- **Relevant files**:
  - `backend/app/infrastructure/drainage/__init__.py` (placeholder)
  - Expected future files: `backend/app/domain/drainage/models.py`, `backend/app/infrastructure/drainage/network.py`, `backend/app/api/flood.py`, etc.
- **What needs to be done**: Implement the drainage network domain models, then the network simulator, then couple with rainfall runoff, then expose via API.

### Water Quality Monitoring System (AquaSense)
- **Note**: This system appears to be a complete, separate application for monitoring water quality (pH, temperature, turbidity, etc.) with anomaly detection and WebSocket streaming. It is not referenced in the flood nowcasting main.py or configuration, and its purpose (sensor anomaly detection) does not directly contribute to flood depth prediction. However, it could be considered as a potential data source for water quality in drains if the project scope were extended.
- **Current implementation**: Fully implemented set of APIs, ML anomaly detection (Isolation Forest), database models, and WebSocket endpoints.
- **What's missing for flood nowcasting**: None, as it is outside the current scope. If the project intended to include water quality monitoring as part of flood risk assessment, then integration would be needed (e.g., correlating contamination with flood events). No such links exist.
- **Relevant files**:
  - `backend/main.py` (AquaSense FastAPI app)
  - `backend/models.py` (SQLAlchemy models for SensorReading, Alert, Device)
  - `backend/schemas.py` (Pydantic schemas for readings/alerts)
  - `backend/routers/*` (sensors, alerts, devices, dashboard)
  - `backend/service.py` (anomaly detection and ingestion logic)
  - `backend/database.py`, `backend/ml_anomaly.py`, `backend/websocket_manager.py`, `backend/seed_data.py`
- **What needs to be done**: Nothing for the flood nowcasting scope; if required, integrate its outputs (e.g., alert status) into the flood nowcasting API or dashboard.

## 5. ❌ Not Yet Implemented

### Drainage Network Domain Models
- **Purpose**: Provide a provider-independent representation of the drainage network topology and capacity.
- **Why it is needed**: To simulate flow, detect surcharges, and route excess water; forms the core of the rainfall-drainage coupling.
- **Expected inputs**: Node elevations, pipe diameters/connections (from city asset data or prototypes).
- **Expected outputs**: A structured graph that can be used by a hydraulic solver.
- **Dependencies**: None (standalone domain layer).
- **Suggested implementation order**: First, before any simulation logic.

### Runoff Generation
- **Purpose**: Convert rainfall excess (rainfall minus losses) into volumetric inflow into the drainage network per catchment.
- **Why it is needed**: Rainfall nowcast provides intensity; only the portion that becomes runoff enters the network.
- **Expected inputs**: Rainfall nowcast (mm/h), catchment areas, imperviousness/runoff coefficients, time step.
- **Expected outputs**: Time series of inflow volumes (m³/s) at each network inlet node.
- **Dependencies**: Requires rainfall nowcast output; requires terrain/imperviousness data (prototype or real).
- **Suggested implementation order**: After drainage network models, before network simulation.

### Network Hydraulic Simulation
- **Purpose**: Simulate flow through the drainage network, compute water levels, detect surcharge (when inflow exceeds pipe capacity), and compute excess volume that exits the system onto the surface.
- **Why it is needed**: To determine when and where the network overflows, which drives surface flooding.
- **Expected inputs**: Network topology, pipe capacities (e.g., from Manning's equation), inflow time series from runoff generation, boundary conditions (outlet water levels).
- **Expected outputs**: Node water levels, pipe flow rates, surcharge flags, excess outflow time series at surcharge points.
- **Dependencies**: Requires drainage network models and runoff generation outputs.
- **Suggested implementation order**: After runoff generation.

### 2D Surface Routing & Flood Depth Prediction
- **Purpose**: Route excess water from network surcharges over the street grid using terrain gradients to predict flood depth at streets and intersections.
- **Why it is needed**: This produces the user-facing prediction (where and how deep water will pool).
- **Expected inputs**: Topography (DEM), surface roughness, excess outflow locations/time series from network simulation, time step.
- **Expected outputs**: Flood depth maps (e.g., per street segment/intersection) at lead times 0–3 hours.
- **Dependencies**: Requires network simulation outputs and terrain data.
- **Suggested implementation order**: Final step before API exposure.

### Flood Nowcast API
- **Purpose**: Expose the predicted flood depths and metadata via REST endpoints.
- **Why it is needed**: To allow the frontend/dashboard to query predictions for visualization and alerting.
- **Expected inputs**: Outputs from surface routing (flood depth grids, timestamps, lead times).
- **Expected outputs**: JSON (or similar) with flood depth per location, validity timestamps, uncertainty estimates.
- **Dependencies**: All upstream components (rainfall → runoff → network → surface).
- **Suggested implementation order**: After surface routing is functional.

### Integration & End-to-End Testing
- **Purpose**: Validate that the chain from rainfall forecast to flood prediction works correctly and produces sensible outputs.
- **Why it is needed**: To ensure correctness and build confidence in the nowcasts.
- **Expected inputs**: Sample rainfall forecasts, known terrain/network data.
- **Expected outputs**: Predicted flood depths that pass sanity checks (mass balance, non-negative depths, etc.).
- **Dependencies**: All components implemented.
- **Suggested implementation order**: After all components are in place; use synthetic or prototype data.

## 6. 🗺️ Recommended Remaining Implementation Roadmap

**Phase 1 — Rainfall Nowcasting (Open-Meteo Adapter)**
- Status: **COMPLETE**
- Objective: Provide accurate, cached, and validated rainfall nowcasts for Mumbai.
- Main components/files: `open_meteo.py`, domain models/exceptions, API endpoints, config.
- Dependencies: None external (uses public API).
- Acceptance criteria: All adapter tests pass; API returns correct data; cache TTL and negative lead time work.

**Phase 2 — Drainage Network Domain Models**
- Status: **NOT STARTED**
- Objective: Define the drainage network as a graph of nodes and pipes with elevations and capacities.
- Main components/files: `backend/app/domain/drainage/models.py` (proposed).
- Dependencies: None.
- Acceptance criteria: Can instantiate a `DrainageNetwork` with nodes and pipes; validation ensures referential integrity and positive capacities.

**Phase 3 — Runoff Generation Service**
- Status: **NOT STARTED**
- Objective: Convert rainfall nowcast to volumetric inflow at network nodes using catchment characteristics.
- Main components/files: `backend/app/infrastructure/drainage/runoff.py` (proposed).
- Dependencies: Phase 2 (network models), rainfall nowcast output.
- Acceptance criteria: Given a rainfall nowcast and catchment parameters, produces inflow time series; unit checks (mm/h × m² → m³/s).

**Phase 4 — Network Hydraulic Simulation**
- Status: **NOT STARTED**
- Objective: Simulate steady-state or dynamic flow through the network to detect surcharges and compute excess outflow.
- Main components/files: `backend/app/infrastructure/drainage/network_simulator.py` (proposed).
- Dependencies: Phase 2 and Phase 3.
- Acceptance criteria: For a simple network, computes correct flow distribution; flags surcharge when inflow > capacity; conserves volume.

**Phase 5 — 2D Surface Routing & Flood Depth Prediction**
- Status: **NOT STARTED**
- Objective: Route excess water over terrain to predict flood depth at streets/intersections.
- Main components/files: `backend/app/infrastructure/drainage/surface_routing.py` (proposed).
- Dependencies: Phase 4 (excess outflow), terrain data (prototype DEM).
- Acceptance criteria: Given excess outflow locations, produces non-negative flood depths that decrease with distance from source; mass balance check (volume in ≈ volume routed + storage).

**Phase 6 — Flood Nowcast API**
- Status: **NOT STARTED**
- Objective: Expose flood nowcast predictions via REST endpoints.
- Main components/files: `backend/app/api/flood.py` (proposed).
- Dependencies: Phase 5.
- Acceptance criteria: `/flood/mumbai` returns flood depth per location with lead times and timestamps; handles errors gracefully.

**Phase 7 — End-to-End Integration & Testing**
- Status: **NOT STARTED**
- Objective: Validate the full chain from rainfall forecast to flood prediction.
- Main components/files: Test suite in `backend/tests/` for drainage and flood modules.
- Dependencies: All previous phases.
- Acceptance criteria: End-to-end test passes with synthetic data; predicts plausible flood depths for a test scenario.

## 7. 🧪 Testing Status

- **Existing test files**:
  - `backend/tests/test_open_meteo_adapter.py` (14 tests for rainfall adapter).
- **What they cover**:
  - Happy path (normal operation with fixture data).
  - All error conditions: timeout, HTTP error, parse error, missing field, unit mismatch, timezone mismatch, empty forecast, invalid timestamp.
  - Cache behavior: fresh cache returns data, expired cache returns None, empty cache returns None.
  - Negative lead time validation.
- **Latest known test results**: All 14 tests pass (last run just now).
- **Missing test coverage**:
  - No tests for the API layer (though integration tested via adapter).
  - No tests for drainage network (not yet implemented).
  - No tests for water quality monitoring system (separate, but its tests are absent).
- **What should be tested next**:
  - Once drainage network models are written, write unit tests for model validation and network connectivity.
  - After runoff generation, test with known rainfall and catchment parameters.
  - After network simulation, test surcharge detection on simple prototypes.
  - After surface routing, test flood depth propagation on a sloped plane.
  - Finally, write end-to-end tests that mock the Open-Meteo API and verify the flood nowcast output.

## 8. 📁 Important Files and Directories

| Path | Purpose | Status |
|------|---------|--------|
| `backend/app/infrastructure/rainfall/open_meteo.py` | Open-Meteo API adapter with caching, timezone conversion, TTL, negative lead time check | ✅ Implemented |
| `backend/app/domain/rainfall/models.py` | Pydantic models for rainfall records and series | ✅ Implemented |
| `backend/app/domain/rainfall/exceptions.py` | Custom exception hierarchy for rainfall adapter errors | ✅ Implemented |
| `backend/app/api/rainfall.py` | FastAPI endpoints for rainfall nowcast and cache status | ✅ Implemented |
| `backend/app/config.py` | Configuration for Open-Meteo timeout, cache TTL, Mumbai coordinates | ✅ Implemented |
| `backend/tests/test_open_meteo_adapter.py` | Test suite for the Open-Meteo adapter | ✅ Implemented (all pass) |
| `backend/app/infrastructure/drainage/__init__.py` | Placeholder for drainage network infrastructure | 🟡 Stub only |
| `backend/main.py` | AquaSense water quality monitoring API (separate system) | ✅ Implemented (but outside flood nowcasting scope) |
| `backend/models.py` | SQLAlchemy ORM models for water quality sensor readings, alerts, devices | ✅ Implemented (AquaSense) |
| `backend/schemas.py` | Pydantic schemas for water quality readings/alerts | ✅ Implemented (AquaSense) |
| `backend/routers/` | REST endpoints for sensors, alerts, devices, dashboard (AquaSense) | ✅ Implemented (AquaSense) |
| `backend/service.py` | Anomaly detection (Isolation Forest) and ingestion logic (AquaSense) | ✅ Implemented (AquaSense) |
| `backend/ml_anomaly.py` | ML model training/prediction for anomaly detection (AquaSense) | ✅ Implemented (AquaSense) |
| `backend/websocket_manager.py` | WebSocket connection manager for live dashboard updates (AquaSense) | ✅ Implemented (AquaSense) |
| `backend/database.py` | Database initialization and session helper (AquaSense) | ✅ Implemented (AquaSense) |
| `backend/seed_data.py` | Script to generate historical water quality readings with anomalies (AquaSense) | ✅ Implemented (AquaSense) |

## 9. 🚧 Known Limitations / Risks

- **Rainfall nowcasting limited to point forecast**: The Open-Meteo API provides a forecast for a single latitude/longitude (Mumbai city center). Spatial variability of rainfall across the city is not captured; this assumes uniform rainfall, which is a prototype assumption and should be labeled as such.
- **Drainage network data absent**: No real-world network topology, pipe capacities, or elevation data is included. Any simulation will require prototypical or assumed data, which must be explicitly labeled as a prototype.
- **Terrain data missing**: No DEM or elevation model is available for surface routing; flood depth predictions cannot be generated without terrain.
- **Antecedent moisture not modeled**: The runoff generation does not account for soil moisture or initial losses, which affects the rainfall excess.
- **Static network assumption**: The drainage network is assumed to be dendritic and pressurized flow not considered; surcharge modeling is simplified.
- **No uncertainty quantification**: Rainfall nowcasts are treated as deterministic; no skill degradation or confidence intervals are provided.
- **Separate water quality system**: The AquaSense system is present but not integrated; if water quality data is to be used for flood risk (e.g., contamination during floods), integration work is needed.
- **Scalability not tested**: The current implementation uses a simple in-memory cache and has not been tested under load or with large network sizes.

## 10. 👥 What Teammates Should Work On Next

| Task | Why it matters | Dependencies | Suggested owner type | Definition of done |
|------|----------------|--------------|----------------------|---------------------|
| Implement drainage network domain models (nodes, pipes, network) | Provides the foundational graph structure for hydraulic simulation | None | Backend | Can instantiate `DrainageNetwork` with validation; unit tests pass |
| Implement runoff generation service | Converts rainfall nowcast to network inflow, linking rainfall to drainage | Drainage network models, rainfall nowcast API | Backend | Given rainfall and catchment parameters, produces inflow time series; unit tests pass |
| Implement simple hydraulic simulator (e.g., steady-state Manning) | Detects surcharge and computes excess outflow from the network | Drainage network models, runoff generation | Backend | For a test network, computes correct flows and flags surcharge; unit tests pass |
| Obtain or prototype terrain data (DEM) for Mumbai | Required for 2D surface routing to predict flood depths | None (data task) | Data/GIS | Have a raster DEM (even if prototype) covering the area of interest with known coordinate system |
| Implement 2D surface routing algorithm | Routes excess water over terrain to predict flood depth at streets/intersections | Network simulator, terrain data | Backend | Given excess outflow locations, produces non-negative flood depths that obey gravity; unit tests pass |
| Implement flood nowcast API endpoint | Exposes predictions to users/dashboard | Surface routing | Backend | `/flood/mumbai` endpoint returns flood depth per location with timestamps and lead times; error handling |
| Write end-to-end integration tests | Validates the full chain from rainfall forecast to flood prediction | All components | Backend/QA | Test passes with synthetic data; predictions are sensible (non-negative, mass balance approx.) |

## 11. 📌 Quick Status Summary

| Component | Status | Notes |
|-----------|--------|-------|
| Rainfall ingestion | ✅ COMPLETE | Open-Meteo adapter with caching, error handling, timezone conversion |
| Rainfall normalization | ✅ COMPLETE | Asia/Kolkata → UTC, lead time calculation, negative lead time rejection |
| Caching | ✅ COMPLETE | 30-minute TTL enforced; returns STALE data on live failure when available |
| Drainage network | 🟡 STUB | Only placeholder `__init__.py`; no models or simulation |
| Hydrodynamic/flood modelling | ❌ NOT STARTED | No runoff generation, network simulation, or surface routing |
| Prediction/nowcasting | ❌ NOT STARTED | No flood depth predictions generated |
| API/backend | ✅ COMPLETE (rainfall only) | Rainfall endpoints functional; drainage/flood endpoints missing |
| Frontend/visualization | ❌ NOT STARTED | No frontend present; dashboard exists for AquaSense only |
| Testing | ✅ PARTIAL | Rainfall adapter tests pass; no tests for drainage/flood components |