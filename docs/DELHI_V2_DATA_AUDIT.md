# Delhi V2 Data Audit & Existing Architecture Assessment

## Executive Summary

This document establishes the technical baseline for **Version 2 (V2)** of the **SIH 2026 Urban Flood Nowcasting System**. The project objective is to evolve from the working Mumbai/Kurla V1 prototype to a high-accuracy, genuinely useful urban flood nowcasting system for the National Capital Territory (NCT) of Delhi, starting with a carefully selected, authoritative testbed catchment.

**Fundamental Mandate**: Mumbai V1 is the operational baseline and **must remain unbroken, unmodified, and regression-free**. All 232 existing backend tests and frontend builds must continue passing without interference. V2 research and design strictly decouples city-specific data from the underlying hydro-computational engine.

---

## 1. Existing Project Audit (Mumbai V1 Prototype)

A thorough architectural and codebase inspection of `C:\Users\laksh\OneDrive\Desktop\sih2026` was executed on September 8, 2026. The system consists of a FastAPI backend and a React/TypeScript MapLibre GL frontend.

### 1.1 Backend Architecture
- **Framework**: FastAPI with asynchronous lifecycle management (`lifespan`).
- **Entry Points**:
  - `backend/app/main.py`: Standalone rainfall nowcast API service.
  - `backend/main.py`: Root API server combining IoT monitoring with flood nowcasting, historical event replay, street intelligence, and flood-safe routing routers (`backend/routers/flood.py`, `backend/routers/routing.py`, `backend/app/api/rainfall.py`).
- **Layering**: Clean separation across `domain/` (pure business logic, mathematical equations, Pydantic models), `infrastructure/` (GIS loaders, raster engines, third-party API adapters), and `api/` or `routers/` (HTTP serialization, parameter validation).

### 1.2 Frontend Architecture
- **Framework**: React 18 + Vite + TypeScript.
- **Mapping Engine**: MapLibre GL (`maplibre-gl` 5.x) utilizing OpenFreeMap vector tile basemaps (`https://tiles.openfreemap.org/styles/liberty`).
- **State Management**: React hooks (`useRef`, `useState`, `useCallback`) coordinating four operational modes:
  1. `LIVE`: 0–3h nowcasting driven by weather forecast (NOW, +1h, +2h, +3h).
  2. `SCENARIO`: Stress-testing design storms (20, 40, 50, 70 mm/h).
  3. `HISTORICAL`: 24-hour retrospective replay of the 29 August 2017 Mumbai deluge.
  4. `ROUTING`: Flood-safe emergency routing avoiding waterlogged streets.
- **Component**: Single comprehensive UI component `frontend/src/components/FloodMap.tsx` (104 KB).

### 1.3 Domain Models
- **Rainfall Domain** (`backend/app/domain/rainfall/`):
  - `RainfallRecord`, `RainfallSeries`: Normalized ISO UTC records with interval bounds, lead time, mm depth, and intensity.
  - `radar_models.py`: `SpatialRainfallGrid`, `RainfallProvenance` (`RADAR`, `MESONET`, `NWP_FALLBACK`, `UNAVAILABLE`).
- **Drainage Domain** (`backend/app/domain/drainage/`):
  - `DrainageNode`, `DrainageChannel`, `DrainageNetwork`: Topological directed graph.
  - `NodeType` (`inlet`, `junction`, `outfall`), `Provenance` (`BMC`, `DEM_DERIVED`, `OSM`).
  - `capacity.py`: Closed-form Manning's open-channel hydraulic capacity ($Q = \frac{1}{n} A R^{2/3} S^{1/2}$) and volumetric surcharge calculation.
- **Flood Routing Domain** (`backend/app/domain/flood/routing.py`):
  - 2D D8 cellular flood routing over digital elevation models, calculating flood depths, inundated mask, and mass conservation audits.
- **Road & Intersection Domain** (`backend/app/domain/roads/`):
  - `AffectedRoad`, `AffectedIntersection`, `StreetFloodIntelligence`.
  - Risk classification thresholds: `CRITICAL` ($d \ge 0.50\text{ m}$), `HIGH` ($0.30 \le d < 0.50\text{ m}$), `MEDIUM` ($0.15 \le d < 0.30\text{ m}$), `LOW` ($0.05 \le d < 0.15\text{ m}$).
- **Routing Domain** (`backend/app/domain/routing/`):
  - `SafeRouteRequest`, `SafeRouteResponse`, NetworkX directed graph router penalizing ponded segments ($Cost = Length \times (1 + 10 \cdot d^2)$) and hard-severing segments with depth $\ge 0.30\text{ m}$.
- **Historical Domain** (`backend/app/domain/historical/`):
  - `HistoricalEvent`, `HistoricalReplayEngine`, `ObservedFloodBenchmark`, `ValidationComparison`.

### 1.4 Flood Modeling Pipeline (`backend/app/domain/pipeline/flood_pipeline.py`)
- Executes the core coupling sequence:
  $$\text{Rainfall (mm)} \xrightarrow{\text{Rational Method}} \text{Runoff Volume } V_{\text{runoff}} \xrightarrow{\text{Intake / Conveyance}} \text{Channel Surcharge } V_{\text{excess}} \xrightarrow{\text{D8 Routing}} \text{Surface Inundation Depth } d(x,y)$$
- Supports authoritative municipal drainage topology with automatic fallback to DEM-derived synthetic topology.
- Performs hydraulic volume conservation checking:
  $$V_{\text{runoff}} = V_{\text{conveyed}} + V_{\text{surface\_flood}}$$

### 1.5 DEM & Raster Handling
- `RasterEngine` (`backend/app/infrastructure/drainage/raster_engine.py`) wraps `rasterio`, `scipy.ndimage`, and `pysheds`.
- Algorithms: Priority-flood sink depression filling, D8 single-flow direction calculation (codes 1 to 128), upstream flow accumulation area calculation, threshold-based channel initiation.
- Coordinate projection: Handles UTM projection transformations (EPSG:32643) with affine transform matrices.

### 1.6 Drainage Abstraction & Municipal GIS Integration
- `BMCDrainageLoader` (`backend/app/infrastructure/drainage/bmc_gis.py`) ingests official municipal storm water drain shapefiles/GeoJSONs.
- Extracts node IDs, ground levels, upstream/downstream invert levels, conduit dimensions (width, height), and cross-section shapes.
- Enforces strict topological rules: CRS EPSG:32643, valid geometries, zero self-loops, upstream-to-downstream flow direction preservation, fallback to DEM surface elevation when invert levels are missing.

### 1.7 Rainfall Provider Abstraction
- Multi-tier `CompositeRainfallProvider` (`backend/app/infrastructure/rainfall/composite_provider.py`):
  1. *Primary*: IMD Doppler Weather Radar (probes real-time radar grid).
  2. *Secondary*: Municipal Rain Mesonet (probes automated ground weather stations).
  3. *Fallback*: Open-Meteo NWP Forecast (hourly Numerical Weather Prediction).
- Bounded additive correction ($\le 20\text{ mm/h}$) calibrates NWP when ground observations exist.
- Rigorous exception hierarchy ensures system never claims forecast is radar.

### 1.8 Street Risk, Routing & Historical Replay
- `OSMRoadNetworkCache` spatially matches 2D flood rasters to road polygons using a 7.0-meter corridor buffer.
- Real-world validation engine reproduces the 29 August 2017 Mumbai Deluge (331.4 mm / 24h at Santacruz) and cross-validates modeled depths against surveyed ground benchmarks at Kurla West, Kalina, Premier Road, and Milan Subway.

---

## 2. Component Categorization Matrix

| Component / Subsystem | Location | Current Role | Category | Reuse / Refactoring Guidance for Delhi V2 |
|---|---|---|:---:|---|
| **Rational Runoff Engine** | `app/domain/rainfall/runoff.py` | Converts $P \to Q$ via Rational Method | **A** | **Reuse without modification.** City-independent physics. |
| **Manning Capacity Solver** | `app/domain/drainage/capacity.py` | Hydraulic conduit conveyance calculation | **A** | **Reuse without modification.** Physics-based. |
| **D8 Surface Routing Engine** | `app/domain/flood/routing.py` | Routes excess water over terrain | **A** | **Reuse without modification.** Operates on any DEM grid. |
| **Flood-Safe Dijkstra Router** | `app/domain/routing/router.py` | Depth-weighted path optimization | **A** | **Reuse without modification.** Operates on any NetworkX graph. |
| **Raster Processing Engine** | `app/infrastructure/drainage/raster_engine.py` | Sink-filling, flow direction, accumulation | **A** | **Reuse without modification.** General raster algorithms. |
| **Open-Meteo Adapter** | `app/infrastructure/rainfall/open_meteo.py` | Ingests NWP hourly precipitation | **A** | **Reuse without modification.** Accepts arbitrary coordinates. |
| **Composite Provider Logic** | `app/infrastructure/rainfall/composite_provider.py` | Fallback hierarchy & correction bounds | **A** | **Reuse logic.** City-independent orchestration. |
| **Road Risk Classification** | `app/domain/roads/models.py` | Classified risk thresholds (0.15m, 0.3m, etc.) | **A** | **Reuse without modification.** Universal vehicle safety standards. |
| **Application Configuration** | `app/config.py` | Hardcodes Mumbai lat/lon and DEM path | **B** | **Refactor.** Introduce multi-city configuration or parameterization. |
| **Mumbai DEM Dataset** | `app/data/dem/mumbai_pilot_dem_30m.tif` | Kurla Copernicus GLO-30 30m raster | **B** | **Retain for Mumbai.** Add separate `delhi/` data tree for V2. |
| **BMC Drainage Data** | `app/data/drainage/bmc/*.geojson` | 1,240 conduits, 1,264 manholes in Kurla | **B** | **Retain for Mumbai.** Create Delhi drainage loader. |
| **Mumbai Road Geometries** | `app/data/roads/mumbai_pilot_*.geojson` | Kurla/BKC OSM roads & junctions | **B** | **Retain for Mumbai.** Add Delhi OSM road network cache. |
| **Mumbai 2017 Event Profile** | `app/domain/historical/events/mumbai_2017.py` | 2017 deluge forcing & benchmarks | **B** | **Retain for Mumbai.** Add Delhi historical event (e.g. July 2023). |
| **Mumbai Radar Adapter** | `app/infrastructure/rainfall/imd_radar.py` | Veravali DWR probing | **B** | **Retain for Mumbai.** Delhi needs Palam/Mausam Bhawan adapter. |
| **Mumbai Rain Mesonet** | `app/infrastructure/rainfall/mesonet.py` | Mumbai station scraping | **B** | **Retain for Mumbai.** Delhi needs IMD AWS network adapter. |
| **Flood Modeling Pipeline** | `app/domain/pipeline/flood_pipeline.py` | Orchestrator checking Mumbai pilot bbox | **C** | **Tightly coupled.** Must generalize to accept city/basin bounds without hardcoded coordinates. |
| **Spatial Road Matcher** | `app/domain/roads/spatial_matcher.py` | Singleton hardcoding Mumbai file paths | **C** | **Tightly coupled.** Must support catchment-specific road loading. |
| **API Endpoints (`flood.py`)** | `backend/routers/flood.py` | `/flood/forecast`, `/historical/2017` | **C** | **Tightly coupled.** Hardcodes Mumbai center and historical event. Needs city selector. |
| **Frontend Map Container** | `frontend/src/components/FloodMap.tsx` | Hardcoded center `[72.8777, 19.0760]` | **C** | **Tightly coupled.** Center and zoom must be configurable by city mode. |

### Summary of Categories:
- **Category A (Already City-Independent)**: Core mathematical equations, hydrological models, raster algorithms, network routing, and API schemas.
- **Category B (Mumbai-Specific)**: Checked-in geospatial files, historical event definitions, municipal GIS loader, and city-specific station endpoints.
- **Category C (Tightly Coupled / Future Refactoring Needed)**: Pipelines and loaders with hardcoded bounding boxes or singleton file paths.
- **Category D (Safe to Reuse for Delhi Without Modification)**: The entire physics engine (`runoff.py`, `capacity.py`, `routing.py`), routing graph algorithms, and base Pydantic models.

---

## 3. Delhi V2 Objective & Spatial Framework

### 3.1 The Intended Architecture
```
                     National Capital Territory of Delhi
                                     ↓
                 Major Drainage Basin (e.g. Barapullah Basin)
                                     ↓
                  Selected Sub-Catchment (e.g. Kushak Nallah)
                                     ↓
      Highest-Quality Terrain (Copernicus GLO-30 DSM, EPSG:32643)
                                     +
      Real Drainage Network (I&FC / PWD Trunk Alignments + Outfall)
                                     +
         Rainfall Forcing (IMD Safdarjung / Lodhi Road AWS + NWP)
                                     +
        Observed Flood Benchmarks (Delhi Traffic Police / Hotspots)
                                     ↓
           Validated Physics-Based Hydrodynamic Model (1D/2D)
                                     ↓
       ML Residual Calibration Layer (LightGBM Error Correction)
                                     ↓
               Street & Intersection Risk Classification
                                     ↓
                  Public Warning & Flood-Safe Routing
```

### 3.2 Critical Spatial Clarification: Barapullah vs. Qudesia Nallah
The project brief identified **Qudesia Nallah** as a potential candidate, alongside the **Barapullah basin**. 

A strict geographical, hydrological, and institutional audit reveals:
1. **Qudesia Nallah is NOT inside the Barapullah basin**:
   - **Qudesia Nallah** (Qudsia drain) is located in **North/Central Delhi** (Lat $28.66^\circ\text{N} - 28.68^\circ\text{N}$, Lon $77.21^\circ\text{E} - 77.24^\circ\text{E}$). It drains Tis Hazari, Civil Lines, and Qudsia Bagh directly into the Yamuna River near Vasudev Ghat / ISBT Kashmere Gate, upstream of the Old Railway Bridge.
   - **Barapullah Basin** is located in **South/Central-South Delhi** (Lat $28.53^\circ\text{N} - 28.60^\circ\text{N}$, Lon $77.16^\circ\text{E} - 77.26^\circ\text{E}$). It drains Chanakyapuri, AIIMS, South Extension, Defence Colony, Lodhi Estate, and Nizamuddin into the Yamuna near Sarai Kale Khan, downstream of the ITO barrage.
2. **Institutional Alignment**:
   - IIT Delhi’s **Water Security and Sustainable Development Hub** (the creators of the *IITD Aab Prahari* citizen flood monitoring platform) explicitly selected the **Barapullah basin** as their dedicated urban flood early warning testbed.
   - The primary IMD reference station for Delhi—**Safdarjung Observatory**—is situated directly on the western boundary of the Barapullah/Kushak catchment.
3. **Conclusion**:
   - If the architecture is `Delhi -> Barapullah basin -> sub-catchment`, the sub-catchment **must be a Barapullah tributary**, such as **Kushak Nallah** or **Sunhari Nallah**.
   - If **Qudesia Nallah** were selected, the hierarchy would be `Delhi -> Yamuna Right Bank North Direct Catchments -> Qudesia Nallah`.
   - As established in Section 9 of this report, **Kushak Nallah (Barapullah Basin)** is the recommended candidate.

---

## 4. Multi-Domain Data Summary

| Domain | Recommended Authoritative Source | Spatial / Temporal Resolution | Access Method | Current Availability |
|---|---|---|---|:---:|
| **Terrain (DEM)** | Copernicus GLO-30 DSM | 30 m (~26 m at Delhi lat) | AWS S3 / OpenTopography GeoTIFF | **Fully Downloadable** |
| **Drainage Network** | Delhi I&FC / PWD / DMP 2018 + OSM | Trunk conduits & outfall junctions | Hybrid (Open GIS + Digitized DMP tables) | **Partially Available / Semi-Restricted** |
| **Rainfall Observations** | IMD Safdarjung & Lodhi Road AWS | Hourly precipitation / 15-min | IMD Mausam Portal / Open Data | **Available** |
| **Rainfall Nowcast** | Open-Meteo Hourly NWP / IMD 0-3h | Hourly forecast (0-3h lead) | REST JSON API | **Fully Downloadable** |
| **Flood Validation** | Delhi Traffic Police Hotspots + Aab Prahari | Point coordinates + depth bands | Official DTP advisory & IITD papers | **Available (Tabular)** |
| **Land Use / Imperviousness** | ESA WorldCover 10m (v200) | 10 m raster | AWS S3 Cloud-Optimized GeoTIFF | **Fully Downloadable** |
| **Road Network** | OpenStreetMap / Geofabrik India | Vector LineStrings & Nodes | Overpass API / Geofabrik extract | **Fully Downloadable** |

---

## 5. Non-Interference Verification

To guarantee zero impact on existing functionality during this research task:
1. **Zero Source Code Edits**: No files in `backend/app/`, `backend/routers/`, or `frontend/src/` were modified.
2. **Zero File Deletions / Moves**: All existing Mumbai datasets in `backend/app/data/` remain untouched.
3. **Automated Test Run**: Running `pytest backend/tests/` completed with **232 passed tests** (exit code 0).
4. **Frontend Build Verification**: Running `npm run build` in `frontend/` completed successfully (exit code 0).
