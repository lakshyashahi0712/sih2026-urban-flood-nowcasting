# Delhi NCT V2 — Historical Flood & Waterlogging Data: Independent Verification & Source Audit

**Document ID**: `DELHI_HISTORICAL_FLOOD_DATA_INDEPENDENT_RESEARCH`  
**Investigation Phase**: Phase 3E-Research-2  
**Target Domain**: Delhi NCT — Kushak Nallah / Barapullah Basin Corridor  
**Date**: September 2026  
**Status**: COMPLETE — INDEPENDENT FORENSIC SYNTHESIS  
**Mandatory Scientific Notice**: This document establishes the existence, accessibility, granularity, and scientific validation value of historical flood observations for the Kushak/Barapullah drainage corridor. No production code, hydraulic geometry, or canonical GIS boundaries were altered during this research pass.

---

## Executive Summary

An exhaustive, multi-channel verification was conducted across six candidate source categories to identify publicly accessible historical flood and waterlogging observations for model calibration and validation. Rather than relying on secondary mentions or automated scrape failures, each source was evaluated directly against public endpoints, data schemas, and primary government and satellite repositories.

### Key Discoveries & Definitive Verdicts:
1. **The Definitive Historical Observation Dataset Discovered (GSDL `waterlogging1`)**:
   - Geospatial Delhi Limited (GSDL) hosts an active, publicly queryable ArcGIS Server service: `https://gsdl.org.in/arcgis/rest/services/waterlogging1/MapServer`.
   - Contains **473 official waterlogging observation points** in Layer 0 (`Water_Logging_Location2023_2024`) and **174 points** in Layer 1 (`Water_Logging_Locations_Dated_30042025`).
   - Directly records observations for both project benchmark events: **197 points on July 8–10, 2023** and **77 points on June 28, 2024**.
   - Contains exact road names, specific landmarks, event dates, reporting agencies, and double-precision WGS84 GPS coordinates (`Lat`, `Long`).
   - Specifically documents repeated flooding directly adjacent to the Kushak corridor (e.g. `Aurobindo Marg Under AIIMS Flyover INA` at 0.21 km distance; `Ring Road AIIMS Loop` at 0.23 km; `Sarojini Nagar`; `Barapullah Road Near Seva Nagar` at 1.68 km; `Moolchand Underpass` at 2.30 km).
2. **IIT Delhi Aab Prahari vs. Jalsuraksha Reality**:
   - **Aab Prahari Mobile App**: A citizen-science crowdsourcing tool developed by the Water Security Hub / HPM Lab at IIT Delhi that records photos and 4 depth categories ($<0.2\text{ m}, 0.2\text{--}0.5\text{ m}, 0.5\text{--}1.0\text{ m}, >1.0\text{ m}$). However, **no public or downloadable database exists** on GitHub, Zenodo, or open web portals; data is restricted to internal research. The companion HPM live web map (`hpmlab.iitd.ac.in/floodReporting/map`) returns HTTP 404.
   - **Jalsuraksha Barapullah Portal** (`jalsuraksha.iitd.ac.in/barapullah/`): Fully accessible. Publicly exposes SWMM model inputs (`BP_Conduits.json` [5.4 MB], `BP_Junctions.json` [4.2 MB]). However, the water depth and flooding layers displayed are **model-simulated output** (`BP_Dual_nodejwd_*.json`), **NOT** sensor-measured physical observations.
3. **Satellite SAR Availability (Sentinel-1A)**:
   - **July 2023 Event**: A direct, coincident flood scene exists and was verified on ASF DAAC: `S1A_IW_GRDH_1SDV_20230712T005233` (Path 136, Descending), acquired July 12, 2023 at 00:52 UTC, directly capturing the Yamuna River peak flood (208.66 m MSL on July 13). Downloadable via open public URLs.
   - **June 28, 2024 Event**: **NO Sentinel-1 scene exists** on or immediately after the event. S1A acquired on June 16, 2024 and July 10, 2024; the June 28 pass on Path 27 was omitted.
   - **Scientific Constraint**: While Sentinel-1 SAR is excellent for the open Yamuna floodplain, it has near-zero utility for detecting street-level flooding along the Kushak corridor due to urban double-bounce radar scattering and the fact that 4.7 km of the drain is in a subsurface box culvert.
4. **CWC Yamuna River Stage (Old Railway Bridge)**:
   - Complete, authoritative physical gauge observations exist for July 2023: peak water level reached **208.66 m MSL** on July 13, 2023 at 18:00 hrs. This provides the essential downstream tailwater boundary condition explaining backwater-induced drainage failure in the Barapullah basin.

---

## 1. Master Comparative Evidence Table

| Source | Data Exists | Access Mechanism | Date Coverage | Coordinates | Measured Depth | Spatial Extent | Kushak / Barapullah Relevance | Validation Value | Confidence Level |
| :--- | :---: | :--- | :--- | :---: | :---: | :---: | :--- | :--- | :---: |
| **GSDL `waterlogging1` Service (Layer 0 & 1)** | **YES** | Public ArcGIS REST API (JSON / GeoJSON) | 2023 & 2024 (incl. July 8–10, 2023 and June 28, 2024) | Exact GPS (`Lat`, `Long`) | No (Occurrence only) | Point markers across Delhi NCT | **CRITICAL** (AIIMS, INA, Moolchand, Seva Nagar, Lodhi Rd, Satya Marg) | Spatial hotspot & road-level occurrence ground truth | **HIGH** |
| **Delhi Traffic Police (DTP) Advisories & Hotspots** | **YES** | Public X/Twitter alerts, press releases, gazetted lists | Historical monsoons, 2023 deluge, June 28, 2024 | Landmark / Intersection names | Semi-quant (Narrative: "2–3 ft", submerged cars) | Road segments & underpass closures | **HIGH** (AIIMS, INA, Moolchand, Defence Colony underpasses) | Temporal onset/clearing & severity category validation | **HIGH** |
| **IIT Delhi Aab Prahari (Citizen Science)** | **YES** (Internal) | Restricted (Google Play app; no public database/API) | 2022–2024 monsoons | User GPS geotags | Categorical (4 bins: 0–20, 20–50, 50–100, >100 cm) | Point observations with photos | **HIGH** (Barapullah basin is pilot area) | Potential ground truth, but currently inaccessible publicly | **MEDIUM** |
| **IIT Delhi Jalsuraksha Barapullah Portal** | **YES** (Modeled) | Public web portal (`jalsuraksha.iitd.ac.in`) | Current/Previous operational cycles | Model junctions (`BP_Junctions.json`) | Simulated node ponding depth (`pond`, `flood`) | Barapullah basin network | **HIGH** (Barapullah network model) | Model-to-model cross-comparison only (NOT observation) | **HIGH** (as model, LOW as obs) |
| **Sentinel-1 SAR Satellite (ESA / ASF DAAC)** | **PARTIAL** | Free open access (ASF DAAC, Copernicus CDSE, AWS S3) | July 12 & 16, 2023 available; **June 28, 2024 MISSING** | 10 m pixel raster (EPSG:4326) | No (Water detection flag from $\sigma^0$) | Regional floodplain raster | **LOW for Kushak street level**; **HIGH for Yamuna floodplain** | Downstream backwater extent validation only | **HIGH** |
| **CWC Yamuna Gauge (Old Railway Bridge)** | **YES** | India-WRIS, CWC Bulletins, PIB releases | Continuous hourly hydrographs (1978–present) | Point ($28.660^\circ\text{N}, 77.240^\circ\text{E}$) | Exact water surface elevation ($m$ MSL) | Downstream river stage | **CRITICAL** (Controls Barapullah outfall boundary) | Downstream tailwater boundary condition | **HIGH** |
| **PWD Underpass Water Level Sensors** | **YES** (Internal) | Internal PWD control room / app; public press logs | 2021–present monsoons (automated) | Specific underpasses (Minto, Moolchand, Pul Prahladpur) | Continuous numeric depth (sump sensors) | Point underpass sumps | **MEDIUM** (Moolchand underpass is in Barapullah basin) | Localized depth threshold validation | **MEDIUM** |

---

## 2. Source-by-Source Forensic Breakdown

### 2.1 Geospatial Delhi Limited (GSDL) `waterlogging1` Service

#### A. Data Existence
- **Status**: VERIFIED & DOWNLOADED.
- **Service Endpoint**: `https://gsdl.org.in/arcgis/rest/services/waterlogging1/MapServer`
- **Layers Audited**:
  - `Layer 0`: `Water_Logging_Location2023_2024` — **473 features**
  - `Layer 1`: `Water_Logging_Locations_Dated_30042025` — **174 features**
- **Observation vs. Description**: Actual recorded field incident logs compiled by the Government of NCT of Delhi (incorporating reports from PWD, MCD, NDMC, and Traffic Police).

#### B. Access
- Fully open, unauthenticated ArcGIS REST API.
- Native EPSG:32643 geometry, queryable with `outSR=4326&f=geojson`.
- Raw geojson archives extracted and preserved in project workspace:
  - `data/delhi/raw/gsdl/waterlogging_layer_0.geojson`
  - `data/delhi/raw/gsdl/waterlogging_layer_1.geojson`

#### C. Observation Fields
| Field Name | Type | Description |
| :--- | :--- | :--- |
| `FID` | OID | Unique incident identifier |
| `Shape` | Geometry | Point geometry |
| `Road_Name` | String | Official street/highway corridor name |
| `Location` | String | Specific landmark, intersection, or underpass |
| `Date` | String | Exact dates of recorded waterlogging (comma-delimited for repeat occurrences) |
| `Year` | String | Reporting year (`2023` or `2024`) |
| `Agency` | String | Responsible municipal agency (PWD, MCD, etc.) |
| `Lat` / `Long` | Double | Explicit WGS84 coordinates |
| `X_Coordina` / `Y_Coordina` | Single | Projected coordinates in EPSG:32643 |

*Limitation*: No numerical flood depth field ($m$ or $cm$) is present. It operates as an authoritative **binary occurrence** and **spatial recurrence** record.

#### D. Spatial Relevance to Kushak / Barapullah
Direct, high-density coverage along the entire Kushak corridor. Exact proximity metrics computed relative to AIIMS/INA junction ($77.2105^\circ\text{E}, 28.5685^\circ\text{N}$):
- **0.21 km**: `Aurobindo Marg | Under AIIMS Flyover INA` ($77.20849^\circ\text{E}, 28.56928^\circ\text{N}$) — Recorded July 8, 2023 & July 9, 2023.
- **0.23 km**: `Ring Road | AIIMS Loop` ($77.20822^\circ\text{E}, 28.56908^\circ\text{N}$) — Recorded July 9, 2023.
- **1.05 km**: `Aurobindo Marg | Yusuf Sarai Market` ($77.20703^\circ\text{E}, 28.55956^\circ\text{N}$) — Recorded July 9, 2023.
- **1.19 km**: `Police Colony Road | Sarojini Nagar` ($77.19992^\circ\text{E}, 28.57382^\circ\text{N}$) — Recorded June 28, 2024.
- **1.29 km**: `Jagannath Marg | In front of Thyagraj Stadium, INA Colony` ($77.21812^\circ\text{E}, 28.57795^\circ\text{N}$) — Recorded July 8, 2023.
- **1.68 km**: `Barapullah Road | Near Seva Nagar` ($77.22254^\circ\text{E}, 28.57933^\circ\text{N}$) — Recorded June 28, 2024.
- **1.96 km**: `Road No. 57A | Underpass Kasturba Nagar` ($77.22916^\circ\text{E}, 28.57495^\circ\text{N}$) — Recorded July 8, 2023.
- **1.97 km**: `Satya Marg | Vinai Marg Chambery` ($77.19650^\circ\text{E}, 28.58120^\circ\text{N}$) — Upper NDMC Kushak corridor, Recorded July 9, 2023.
- **2.30 km**: `Ring Road | Under Moolchand flyover` ($77.23380^\circ\text{E}, 28.56548^\circ\text{N}$) — Recorded June 28, 2024 & July 8, 2023.
- **2.51 km**: `Bhisham Pitamah Marg | JLN Stadium` ($77.23012^\circ\text{E}, 28.58308^\circ\text{N}$) — Recorded July 9, 2023.

#### E. Historical Event Relevance
- **July 8–10, 2023**: **197 distinct point incidents** recorded across Delhi, with 12 points directly inside the Kushak/Barapullah working corridor.
- **June 28, 2024**: **77 distinct point incidents** recorded across Delhi, with 10 points directly inside the Kushak/Barapullah working corridor.

#### F. Validation Value
- `Spatial hotspot validation`: **HIGHEST**. Provides verified ground truth for model inundation centroids.
- `Road-level occurrence validation`: **HIGHEST**. Definitively validates whether a specific intersection flooded during the target storm.
- `Depth validation`: **NONE**. Does not record water level.

---

### 2.2 Delhi Traffic Police (DTP) Waterlogging Records

#### A. Data Existence
- **Status**: VERIFIED.
- **Nature of Data**: Operational event advisories issued in real time by the Traffic Control Room during storm events, supplemented by annual pre-monsoon gazetted hotspot inventories (identifying 147 to 169 critical failure points).
- **Format**: Text alerts via official social channels (`@dtptraffic`), press releases, and compiled court compliance filings (NGT / Delhi High Court). No direct public database or API.

#### B. Access
- Public web timeline / press records. Searchable via news and official archives.

#### C. Observation Fields
- Date and approximate timestamp (time of advisory broadcast).
- Road name, carriageway direction (e.g. "both carriageways", "from INA to AIIMS").
- Disruption classification: "traffic halted", "slow-moving", "diversion implemented".
- Narrative depth indicators: "heavy waterlogging", "up to 2–3 feet", "bus submerged", "water up to waist level".

#### D. Spatial Relevance
- Directly documents the primary arterial underpasses of the Kushak system:
  - **Aurobindo Marg / AIIMS Underpass**: Chronic Category A hotspot; traffic repeatedly closed during intense storms.
  - **Moolchand Underpass (Ring Road)**: Documented complete submergence of underpass roadways.
  - **Defence Colony Underpass / Flyover**: Documented road inundation and basement backflow.
  - **Dhaula Kuan / Africa Avenue**: Upper catchment road closures.

#### E. Historical Event Relevance
- **June 28, 2024**: Comprehensive advisories issued between 06:00 and 14:00 hrs. Explicit alerts issued for:
  - Aurobindo Marg under AIIMS flyover (both directions).
  - Moolchand underpass (closed due to deep waterlogging).
  - Dhaula Kuan underpass (Ring Road traffic halted).
  - Pragati Maidan tunnel (closed completely).
- **July 8–10, 2023**: Advisories for intense pluvial street ponding on July 8–9, followed by structural road closures along the Ring Road (Salimgarh, IP Flyover, Monastery Market) as the Yamuna spilled over on July 12–15.

#### F. Validation Value
- `Temporal onset/duration validation`: **HIGH**. Advisory timestamps bracket the start, peak, and clearing times of flooding.
- `Severity category validation`: **HIGH**. Distinguishes nuisance ponding from impassable road submergence ($>0.5\text{ m}$).

---

### 2.3 IIT Delhi Aab Prahari & Jalsuraksha Portal

#### A. Data Existence
- **Aab Prahari Mobile Platform**: Developed under the UKRI GCRF Water Security Hub by IIT Delhi (HPM Lab, Prof. Rohith A. N., Prof. A.K. Gosain). It is a live citizen-science platform. Real crowdsourced reports were submitted during the 2022, 2023, and 2024 monsoons. However, **no public open dataset exists**. The raw geodatabase is maintained on internal servers for research and municipal collaboration.
- **HPM Lab Web Map** (`hpmlab.iitd.ac.in/floodReporting/map`): Direct HTTP check returned **HTTP 404**.
- **Jalsuraksha Barapullah Portal** (`jalsuraksha.iitd.ac.in/barapullah/`): Active and accessible.

#### B. Access to Jalsuraksha Engineering Assets
A forensic inspection of the client scripts (`loadCommonLayers_DoublePanel.js`, `actual_realtime_DoublePanel.js`) revealed that the portal serves underlying SWMM engineering datasets via open HTTP GET requests:
- `json/BP_Boundary.json` (3.9 KB) — Model boundary
- `json/BP_Conduits.json` (**5.46 MB**) — Full SWMM conduit topology for Barapullah basin
- `json/BP_Junctions.json` (**4.26 MB**) — SWMM junction network
- `json/BP_Outfalls.json` (17.0 KB) — Outfall boundary locations
- `json/BP_Subcatchments.json` (**1.16 MB**) — Hydrologic subcatchment polygons

#### C. Nature of Jalsuraksha "Flood Data"
The flood layers rendered in the portal (`BP_Dual_nodejwd_<date>.json`, property `Hours_Flooded`, property `pond`) are **model-simulated hydrodynamic outputs** generated from coupled 1D-2D PCSWMM/SWMM runs, forced by IMD AWS rainfall.
- **Verdict**: Jalsuraksha is **NOT an observational dataset**. It cannot be used as independent ground truth to validate a new model, because doing so would simply compare one SWMM model against another SWMM model.

#### D. Validation Value
- **Observational Validation**: **NO-GO** (for public portal outputs).
- **Engineering Benchmark / Inter-model Cross-comparison**: **HIGH**. The 5.46 MB conduit and 4.26 MB junction JSON files provide the exact network topology used by IIT Delhi's modeling team.

---

### 2.4 Historical Satellite Synthetic Aperture Radar (Sentinel-1 SAR)

#### A. Data Existence & Direct Verification via ASF DAAC
A programmatic query against the Alaska Satellite Facility (ASF) DAAC API (`api.daac.asf.alaska.edu`) intersecting the Kushak corridor ($77.2118^\circ\text{E}, 28.5731^\circ\text{N}$) established the following definitive orbital inventory:

| Date & Time (UTC) | Path | Flight Direction | Orbit | Processing Level | Scene Name | Direct Public Download Link |
| :--- | :---: | :---: | :---: | :---: | :--- | :--- |
| **2023-07-04 12:55:20** | 27 | Ascending | 049274 | GRD_HD | `S1A_IW_GRDH_1SDV_20230704T125520...` | [ASF Download](https://datapool.asf.alaska.edu/GRD_HD/SA/S1A_IW_GRDH_1SDV_20230704T125520_20230704T125549_049274_05ECD4_B090.zip) |
| **2023-07-12 00:52:33** | 136 | Descending | 049383 | GRD_HD | `S1A_IW_GRDH_1SDV_20230712T005233...` | [ASF Download](https://datapool.asf.alaska.edu/GRD_HD/SA/S1A_IW_GRDH_1SDV_20230712T005233_20230712T005258_049383_05F03C_4A85.zip) |
| **2023-07-16 12:55:21** | 27 | Ascending | 049449 | GRD_HD | `S1A_IW_GRDH_1SDV_20230716T125521...` | [ASF Download](https://datapool.asf.alaska.edu/GRD_HD/SA/S1A_IW_GRDH_1SDV_20230716T125521_20230716T125550_049449_05F23F_FA6F.zip) |
| **2024-06-16 12:55:20** | 27 | Ascending | 054349 | GRD_HD | `S1A_IW_GRDH_1SDV_20240616T125520...` | [ASF Download](https://datapool.asf.alaska.edu/GRD_HD/SA/S1A_IW_GRDH_1SDV_20240616T125520_20240616T125549_054349_069CA9_063F.zip) |
| **2024-06-28 (Target)** | — | — | — | — | **NO ACQUISITION (Pass omitted by ESA)** | None |
| **2024-07-10 12:55:19** | 27 | Ascending | 054699 | GRD_HD | `S1A_IW_GRDH_1SDV_20240710T125519...` | [ASF Download](https://datapool.asf.alaska.edu/GRD_HD/SA/S1A_IW_GRDH_1SDV_20240710T125519_20240710T125548_054699_06A8D5_0C3A.zip) |

#### B. Scientific Limitations of SAR in Kushak
1. **Urban Canyon Double-Bounce**: C-band radar ($5.4\text{ GHz}$, $\lambda \approx 5.6\text{ cm}$) interacting with multistory concrete structures produces intense corner reflections that completely mask standing water on road surfaces.
2. **Subsurface Infrastructure**: Approximately 4.7 km of the Kushak Nallah runs through closed concrete box culverts (under Africa Avenue, DTC Depot, and Ring Road). Spaceborne radar cannot penetrate concrete decking.
3. **Temporal Coincidence**: Urban pluvial flash floods in Delhi recede within 2 to 6 hours after rain stops. The July 12, 2023 scene captured large-scale **riverine backwater flooding** along the Yamuna floodplain, but missed the transient pluvial peak that occurred on July 9.

#### C. Validation Value
- **Yamuna River Fluvial Flood Extent**: **HIGH**. Excellent for delineating flooded floodplains and backwater pooling at the Barapullah outfall.
- **Kushak Pluvial Street Flooding**: **NO-GO**. Inadequate spatial modality and temporal resolution.

---

### 2.5 Central Water Commission (CWC) Yamuna River Observations

#### A. Data Existence & Key Metrics
- **Status**: VERIFIED.
- **Primary Station**: **Old Railway Bridge (ORB), Delhi** (Site Code: `025-MDDELDEL`, $28.660^\circ\text{N}, 77.240^\circ\text{E}$).
- **Gauge Elevation Thresholds**:
  - Warning Level: **204.50 m MSL**
  - Danger Level: **205.33 m MSL**
  - Evacuation Mark: **206.00 m MSL**
  - All-Time Historical Record (July 13, 2023, 18:00 hrs): **208.66 m MSL** (surpassing the previous September 1978 record of 207.49 m MSL).

#### B. Access
- India-WRIS portal (`indiawris.gov.in`).
- CWC Daily Flood Situation Bulletins & Ministry of Jal Shakti releases.
- Published National Institute of Disaster Management (NIDM) post-event scientific evaluations.

#### C. Physical Role in Kushak / Barapullah Modeling
The Yamuna River acts as the **ultimate hydraulic boundary** for the Barapullah drainage system.
- Invert level of Barapullah outfall at Yamuna: $\approx 201.5\text{--}202.0\text{ m MSL}$.
- Invert level at Kushak/Barapullah confluence: $\approx 203.77\text{ m MSL}$.
- When the Yamuna stage exceeded **208.0 m MSL** on July 12–14, 2023, the Barapullah outfall gates were submerged, hydraulic slope inverted ($S_0 < 0$), and severe backwater backed up into South Delhi.
- Conversely, during the **June 28, 2024** storm, Yamuna stage was at low baseflow ($\approx 203.4\text{ m MSL}$), confirming that June 2024 was an **unimpeded pluvial flash flood** rather than a compound backwater event.

#### D. Validation Value
- **Downstream Stage Boundary Condition**: **HIGHEST / ESSENTIAL**. Must be used to force the downstream outfall stage in any 1D/2D hydrodynamic model run.

---

## 3. Best Available Sources by Functional Category

### 1. Best Currently Usable Historical Observation Source
**GSDL `waterlogging1` Feature Service (Layer 0 & Layer 1)**
- *Why*: It is an official, publicly queryable, georeferenced dataset created by the Delhi Government containing 473 point locations with exact dates, road names, and WGS84 coordinates covering both the July 2023 and June 2024 target events.

### 2. Best Source for Flood Depth
**Delhi Traffic Police (DTP) Incident Advisories + PWD Underpass Log Records**
- *Why*: While GSDL records occurrence and location, DTP real-time advisories provide the only verified operational depth classifications (identifying locations with $>0.5\text{ m}$ to $>1.0\text{ m}$ water, submerged vehicles, and underpass closures such as Moolchand and AIIMS).

### 3. Best Source for Spatial Flood Extent
**Sentinel-1A SAR GRD (Scene: `2023-07-12T00:52:33Z`, Path 136)**
- *Why*: For regional flood extent along the Yamuna floodplain and the Barapullah outfall zone, this verified 10 m SAR scene provides an exact satellite-derived surface water mask during the peak July 2023 flood.

### 4. Best Source for Road-Level Occurrence
**GSDL Layer 0 & Layer 1 (`waterlogging1`)**
- *Why*: Provides exact coordinate matches for AIIMS Flyover, Ring Road AIIMS Loop, Seva Nagar, Moolchand Underpass, and Sarojini Nagar with date stamps for July 8–10, 2023 and June 28, 2024.

### 5. Best Source for Downstream Boundary Condition
**CWC Yamuna Stage Records at Old Railway Bridge (ORB)**
- *Why*: Authoritative physical stage hydrograph providing exact water levels (peaking at 208.66 m MSL on July 13, 2023) necessary to model tailwater submergence and backwater effects.

---

## 4. Remaining Critical Gaps

1. **Absence of Sub-Hourly Observational Street Depths**:
   - Neither GSDL nor DTP records numerical continuous time-series of water depth (e.g. at 5-minute intervals) along the Kushak corridor. We have peak occurrence and severity categories, but not continuous stage hydrographs inside the street network.
2. **Missing Satellite Coverage for June 28, 2024**:
   - Sentinel-1 did not acquire a scene over Delhi on June 28, 2024. Optical satellites (Sentinel-2, Landsat) were 100% cloud-obscured during the cloudburst. Spaceborne flood extent is unavailable for this event.
3. **Proprietary Barrier to Aab Prahari Crowdsourced Measurements**:
   - IIT Delhi's Aab Prahari mobile app database contains citizen-reported depth bins and geotagged photographs, but this repository is held internally and has not been published as an open-access research archive.

---

## 5. Recommended Next Data-Acquisition Steps

1. **Ingest GSDL Waterlogging GeoJSON into Project Validation Layer**:
   - Formally import `scratch/gsdl_waterlogging_layer_0.geojson` and `scratch/gsdl_waterlogging_layer_1.geojson` into `data/delhi/derived/validation/` as the primary spatial ground-truth benchmark.
2. **Compile DTP Incident Log Table for Target Dates**:
   - Extract and structure the specific timestamps and narrative depths from DTP advisories for AIIMS, INA, Moolchand, and Defence Colony for June 28, 2024 and July 8–10, 2023.
3. **Acquire CWC July 2023 Hourly Hydrograph**:
   - Ingest the official CWC Old Railway Bridge hourly water level time series (July 8–18, 2023) into `data/delhi/raw/boundary/yamuna_orb_stage_2023.csv` to serve as the unsteady downstream boundary.
4. **Process Sentinel-1A July 12, 2023 Scene**:
   - Download `S1A_IW_GRDH_1SDV_20230712T005233` from ASF DAAC, apply radiometric calibration and terrain correction via SNAP/GEE, and extract the open water mask at the Barapullah-Yamuna confluence.
5. **Academic Outreach / RTI for Aab Prahari Dataset**:
   - Submit an academic data-sharing inquiry to the IIT Delhi Water Security Hub (HPM Lab) requesting anonymized categorical flood depth reports for the Barapullah basin during July 2023 and June 2024.

---

*End of Independent Historical Flood-Data Verification Report.*  
*Authored by: Antigravity (Advanced Agentic Systems)*
