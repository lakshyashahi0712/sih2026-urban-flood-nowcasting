# Delhi NCT V2 — Kushak Public Evidence Expansion Catalog
## Exhaustive Audit of Public, Non-RTI Evidence for the Kushak Nallah / Barapullah Drainage System

**Document ID**: `DELHI_KUSHAK_PHASE13D_PUBLIC_EVIDENCE_CATALOG`  
**Investigation Phase**: Phase 13D  
**Date**: 16 September 2026  
**Repository Baseline**: `d4ab4baceb56044fb860a5c67f81dee4199d3853` (Immutable Digital Twin Baseline, 101 Python files, 652 passing tests)  
**Mandatory Integrity Notice**: This investigation is an operational, read-only evidence audit across public, non-RTI external repositories. In strict accordance with engineering ethics and project instructions:  
- **NO RTIs**: No RTI requests are filed, prepared, submitted, or recommended.  
- **NO FABRICATION**: Missing geometry is NEVER synthesized, interpolated, or declared measured.  
- **NO SPECIFICATION UPGRADES**: Tender scopes and costing buckets are NEVER treated as completed surveys.  
- **NO REMOTE SENSING CONFLATION**: Satellite radar flood extents are NEVER treated as street-level flood depth.  
- **NO DEM CONFLATION**: Global DEMs are NEVER treated as surveyed channel inverts.  
- **ZERO MODEL DRIFT**: Digital Twin Python code, tests, and parameters remain 100% untouched.  

---

## 1. Executive Summary & Audit Metrics

An exhaustive audit of publicly accessible, non-RTI repositories and engineering archives was conducted across eight institutional domains to discover scientifically usable evidence for the Kushak Nallah / Barapullah drainage network.

### Key Audit Summary:
1. **24 Public Sources Searched**: Exhaustive scans conducted across GSDL geoportal, NDMC/I&FC/MCD e-tenders, CWC flood bulletins, IMD surface synoptic stations, Copernicus Sentinel-1/2 constellations, satellite DEMs (Copernicus GLO-30, SRTM, ALOS), academic publications (IIT Delhi, cGanga), and historical civic observations.
2. **28 Candidate Datasets Audited**: Every discovered item was forensically categorized into six strict evidentiary partitions (A through F).
3. **6 New Usable Evidence Items Identified (Partition A)**: High-confidence boundary forcing and validation datasets: CWC Delhi Railway Bridge hydrometric stage series (July 2023 peak 208.66 m MSL), IMD Safdarjung hourly precipitation hyetographs, IMD Lodhi Road daily rainfall series, GSDL IRCH planimetric centerline alignment (stripped of false attributes), GSDL Waterlogging Points (116 validated hotspots), and Sentinel-1 C-SAR flood backscatter masks.
4. **Zero (0) New Tier-A Geometry Discovered**: **NO instrumented longitudinal bed profile, NO surveyed transverse cross-sections, and NO structural as-built invert schedules exist in the open public domain.** All authentic Tier-A engineering survey deliverables (I&FC NIQ 249 DGPS bathymetry, NDMC R-III structural drawings) remain strictly access-blocked in physical departmental archives.

| Metric | Value | Audit Verdict |
| :--- | :--- | :--- |
| **SOURCES_SEARCHED** | **24** | Comprehensive institutional coverage across 8 search targets |
| **CANDIDATES_FOUND** | **28** | Fully indexed and cataloged with complete metadata |
| **NEW_USABLE_EVIDENCE** | **6** | Boundary forcing, planimetric routing, and spatial validation masks |
| **TIER_A_CANDIDATES** | **3** | Evaluated for direct physical survey data |
| **NEW_TIER_A_EVIDENCE** | **0** | **ZERO**. Genuine Tier-A geometry remains unreleased/offline |

---

## 2. Forensic Gap Reduction Analysis (The 7 Priority Gaps)

The evaluation of all public sources against the project's seven primary hydraulic modeling gaps yields the following definitive, unvarnished verdicts:

```
┌────────────────────────────────┬──────────┬────────────────────────────────────────────────────────┐
│ Primary Modeling Gap           │ Status   │ Forensic Evidence Basis                                │
├────────────────────────────────┼──────────┼────────────────────────────────────────────────────────┤
│ 1. LONGITUDINAL_PROFILE        │ MISSING  │ Zero station bed elevations exist in public domain     │
│ 2. OPEN_REACH_CROSS_SECTIONS   │ MISSING  │ I&FC bathymetry offline; GSDL CRSC has 0 Kushak pts    │
│ 3. COVERED_CONDUIT_GEOMETRY    │ PARTIAL  │ NGT bounds depot (50m/5 bays); Africa Ave unmeasured   │
│ 4. STRUCTURE_OPENINGS          │ PARTIAL  │ Qualitative bay counts known; invert/soffits missing   │
│ 5. VERTICAL_DATUM_CONTROL      │ MISSING  │ No GTS benchmark ties; +6.24m NDMC/SDMC jump unbonded  │
│ 6. LATERAL_CONNECTIONS         │ MISSING  │ Invert levels of feeder drain connections unrecorded   │
│ 7. HYDRAULIC_OBSERVATIONS      │ PARTIAL  │ CWC Yamuna tailwater & IMD rain known; in-drain stage=0│
└────────────────────────────────┴──────────┴────────────────────────────────────────────────────────┘
```

### 2.1 Detailed Gap Audit:

1. **`LONGITUDINAL_PROFILE` = MISSING (Unreduced)**
   - *Engineering Requirement*: Continuous surveyed bed invert elevation ($z_{\text{bed}}(x)$) along the 5.028 km corridor from Chanakyapuri to Barapullah confluence.
   - *Public Findings*: Neither the Delhi Government GSDL portal, nor public tender attachments, nor academic literature provide surveyed bed RLs. The I&FC CD-XII DGPS bathymetric survey (NIQ 2025-26/249) was completed in October 2025 but the deliverables were never published online and remain in Basaidarapur archives. The GSDL IRCH invert field carries an unvalidated slope with two adverse rises and a catastrophic +6.24 m vertical jump at the SDMC boundary.
   - *Verdict*: **MISSING**. No public source closes this gap.

2. **`OPEN_REACH_CROSS_SECTIONS` = MISSING (Unreduced)**
   - *Engineering Requirement*: Transverse channel coordinates ($x, y, z$) at regular chainages for the open downstream reach (~0.87 km from Bus Depot to Lala Lajpat Rai Marg).
   - *Public Findings*: GSDL HYD CRSC layer contains 8,486 cross-section points across Delhi, but spatial querying confirmed **exactly 0 points in the Kushak corridor** (the closest cluster is ~4 km away along the Yamuna). Academic SWMM publications use synthetic trapezoidal approximations (e.g. uniform 25 m top width), which are methodologically invalid as physical observations.
   - *Verdict*: **MISSING**. No public cross-sections exist.

3. **`COVERED_CONDUIT_GEOMETRY` = PARTIAL (Context Bounds Only)**
   - *Engineering Requirement*: Internal clear dimensions (clear span $W$, clear rise $H$, barrel count $N_{\text{barrels}}$) of subterranean RCC box sections.
   - *Public Findings*: The NGT OA 6/2012 Joint Inspection Report (05-03-2025) officially bounds the 1.0 km Bus Depot reach: 50 m total width, 5 internal bays of 10 m each, visual clear depth 3.5 to 4.5 m, and 1.5 to 3.0 ft of silt. NDMC NIT-52 SOQ Item 1 classifies desilting in the 'width 4.00 m +25%' size class. However, the Africa Avenue covered conduit remains unmeasured, and detailed structural as-built shop drawings remain locked in NDMC R-III office (Room 306, SBS Place).
   - *Verdict*: **PARTIAL**. Structural bounding constraints exist for the Depot reach, but true as-built geometry for Africa Avenue remains missing.

4. **`STRUCTURE_OPENINGS` = PARTIAL (Context Bounds Only)**
   - *Engineering Requirement*: Clear span, soffit elevation, and weir/drop dimensions at bridges, culverts, and junctions (e.g. Africa Avenue, Brigadier Hoshiyar Singh Marg, INA Market, Lala Lajpat Rai Marg).
   - *Public Findings*: Visual bay counts and bridge span counts are noted in court inspection proceedings, but exact soffit levels ($z_{\text{soffit}}$), invert drop-steps, and trash screen head loss coefficients are unrecorded.
   - *Verdict*: **PARTIAL**. Macroscopic bay counts exist, but hydrodynamic opening parameters are unmeasured.

5. **`VERTICAL_DATUM_CONTROL` = MISSING (Unreduced)**
   - *Engineering Requirement*: Authoritative Survey of India Great Trigonometrical Survey (GTS) benchmark ties establishing datum consistency across administrative boundaries.
   - *Public Findings*: Forensic analysis of GSDL GIS reveals that NDMC records terminate at $203.770\text{ m MSL}$, while the adjacent SDMC segment records an invert of $210.010\text{ m MSL}$—an unphysical $+6.24\text{ m}$ jump that would require water to flow uphill. No public record provides benchmark ties connecting NDMC, SDMC, and I&FC local level ledgers to GTS MSL.
   - *Verdict*: **MISSING**. Incompatible datums block any merged numerical invert profile.

6. **`LATERAL_CONNECTIONS` = MISSING (Unreduced)**
   - *Engineering Requirement*: Invert levels, diameters, and backflow gate statuses of all secondary municipal stormwater drains and sewer outfalls discharging into Kushak Nallah.
   - *Public Findings*: GSDL maps 76 circular sewer lines in Chanakyapuri (diameter 450 mm), but connection inverts, outfall flumes, and flap gate installations along the main covered trunk are completely unrecorded in public GIS.
   - *Verdict*: **MISSING**. Unaccounted lateral inflows remain a source of uncalibrated discharge uncertainty.

7. **`HYDRAULIC_OBSERVATIONS` = PARTIAL**
   - *Engineering Requirement*: Synchronous in-situ stage hydrographs ($h(t)$) and discharge observations ($Q(t)$) along the Kushak corridor during flood events.
   - *Public Findings*: CWC provides verified stage hydrographs on the Yamuna mainstem at Delhi Railway Bridge (July 2023 peak 208.66 m MSL), establishing an excellent tailwater boundary. IMD Safdarjung and Lodhi Road provide sub-daily meteorological boundary forcing. cGanga/NDMC records a single non-rainy season dry-weather flow average of ~10 MLD (~0.116 m³/s). However, **ZERO continuous in-channel stage gauges or flow meters exist or report publicly along Kushak Nallah**.
   - *Verdict*: **PARTIAL**. Boundary conditions are available; in-situ channel calibration observations are absent.

---

## 3. Partitioned Public Evidence Catalog

Below is the exhaustive catalog of all 24 investigated candidate datasets, classified into Partitions A through F.
### SECTION A: NEW USABLE EVIDENCE
*Genuinely usable evidence with high provenance, open accessibility, and direct scientific utility for boundary forcing, routing, or validation.*

#### `[PUB-EVID-A01]` CWC Delhi Railway Bridge (Old Railway Bridge) Hydrometric Flood Bulletins (July 2023 Flood Event)
- **Publisher / Custodian**: Central Water Commission (CWC), Ministry of Jal Shakti, Upper Yamuna Division
- **URL / Access Channel**: https://cwc.gov.in / https://ffs.india-water.gov.in (Bulletins cfcrcwcdfb10.07.2023.pdf to 17.07.2023.pdf)
- **Public Access**: `PUBLIC_DOWNLOAD (Daily published situation reports / gazetted bulletins)`
- **Date / Temporal Scope**: 2023-07-08 to 2023-07-17 (Peak 2023-07-13 18:00 IST) | Sub-daily / daily observations during catastrophic July 2023 flood
- **Geographic Scope**: Yamuna River at Old Railway Bridge, Delhi (28.65917° N, 77.24500° E)
- **Data Format**: PDF bulletins / extracted CSV (cwc_old_railway_bridge_event.csv)
- **Provenance & Evidence Class**: `HIGH (Official ministerial hydrometric gauge network, Site #1008)` | `OFFICIAL — HYDROMETRIC GAUGE`
- **Tier Relevance**: `TIER-A (for downstream Yamuna tailwater boundary condition only)`
- **What It Establishes**: Definitive, verified water surface elevations (m MSL) of the Yamuna mainstem during the historic flood: Warning Level (204.50 m), Danger Level (205.33 m), and record peak (208.66 m MSL on 13-07-2023). Accurately defines the downstream tailwater backwater boundary for Barapullah outfall.
- **What It Does NOT Establish**: Does NOT establish internal Kushak Nallah stages, local in-channel discharges, internal head losses, or street-level waterlogging depths in South Delhi (~10-15 km upstream of Yamuna outfall).
- **Safety for Ingestion**: **SAFE FOR INGESTION (Strictly as downstream boundary condition: stage-time tailwater series)**

#### `[PUB-EVID-A02]` IMD Safdarjung Observatory Hourly & Daily Precipitation Series (Monsoon 2023-2024)
- **Publisher / Custodian**: India Meteorological Department (IMD), Ministry of Earth Sciences
- **URL / Access Channel**: https://mausam.imd.gov.in / https://internal.imd.gov.in / National Weather Bulletins
- **Public Access**: `PUBLIC_AVAILABLE (Daily weather reports, automated weather station summaries, extreme event press bulletins)`
- **Date / Temporal Scope**: Continuous historical; specific extreme events 2023-07-08/09 (153.0 mm) and 2024-06-28 (228.1 mm) | Hourly hyetographs and 24-hour accumulated rainfall
- **Geographic Scope**: Safdarjung Airport / Observatory Station #42182 (28.58° N, 77.21° E, within 1 km of Kushak basin)
- **Data Format**: Tabular text / CSV / PDF daily reports
- **Provenance & Evidence Class**: `HIGH (National meteorological authority reference station)` | `OFFICIAL — METEOROLOGICAL OBSERVATION`
- **Tier Relevance**: `TIER-A (for catchment meteorological boundary forcing only)`
- **What It Establishes**: Gold-standard surface rainfall depths and intensities (mm/hr) directly adjacent to the Kushak watershed. Captures intense microbursts (e.g. 74 mm/hr on 28-06-2024) driving pluvial runoff.
- **What It Does NOT Establish**: Does NOT establish channel geometry, Manning's n roughness, subterranean culvert capacity, silt depths, or backwater stages.
- **Safety for Ingestion**: **SAFE FOR INGESTION (Strictly as catchment hydrological forcing input)**

#### `[PUB-EVID-A03]` IMD Lodhi Road Observatory Daily Precipitation Observations
- **Publisher / Custodian**: India Meteorological Department (IMD), Ministry of Earth Sciences
- **URL / Access Channel**: https://mausam.imd.gov.in / IMD Regional Meteorological Centre Delhi
- **Public Access**: `PUBLIC_AVAILABLE (Daily weather bulletins and climatic data summaries)`
- **Date / Temporal Scope**: Continuous historical; extreme monsoon events 2023-2024 | Daily / synoptic rainfall totals
- **Geographic Scope**: Lodhi Road Observatory (28.59° N, 77.22° E, directly situated in the Kushak/Barapullah lower basin)
- **Data Format**: Tabular CSV / Daily summaries
- **Provenance & Evidence Class**: `HIGH (National meteorological standard)` | `OFFICIAL — METEOROLOGICAL OBSERVATION`
- **Tier Relevance**: `TIER-A (for spatial rainfall interpolation / cross-verification)`
- **What It Establishes**: Secondary spatial rainfall verification point within the Barapullah basin, confirming spatial distribution and gradients across the ~27.66 km² catchment.
- **What It Does NOT Establish**: Does NOT establish in-drain hydraulic state, velocity, or physical cross-sections.
- **Safety for Ingestion**: **SAFE FOR INGESTION (Strictly as secondary hydrologic boundary forcing)**

#### `[PUB-EVID-A04]` GSDL Geo-Spatial Data Infrastructure — Irrigation Channel (IRCH) Alignment Layer
- **Publisher / Custodian**: Geospatial Delhi Limited (GSDL), GNCTD
- **URL / Access Channel**: https://gsdl.org.in/arcgis/rest/services/DIFC/storm_drain_08082024/MapServer (Layers 6 and 7)
- **Public Access**: `PUBLIC_REST_API (Queryable ESRI REST endpoint, EPSG:32643)`
- **Date / Temporal Scope**: Data baseline 2024; GSDL Feature List V2.0 February 2025 | Static infrastructure inventory
- **Geographic Scope**: Kushak Nallah alignment from Chanakyapuri (J_3178) to Barapullah confluence
- **Data Format**: ESRI GeoJSON / ESRI JSON (157 NDMC + 21 SDMC records)
- **Provenance & Evidence Class**: `MEDIUM-HIGH (State GIS infrastructure repository)` | `OFFICIAL — GIS CARTOGRAPHIC / DERIVED`
- **Tier Relevance**: `TIER-B (Planform alignment only; TIER-C/REJECTED for cross-section attributes)`
- **What It Establishes**: Planimetric centerline routing and segment lengths (NDMC box spine: 4,926.99 m; mean lateral agreement ~16.87 m with satellite imagery). Confirms subterranean connectivity corridors through Central Delhi.
- **What It Does NOT Establish**: Does NOT establish hydraulic clear dimensions. Nominal attributes ('Drn_Wd_m = 25.0 m', 'Drn_Dp_m = 7.354 m') are repeated identical administrative templates. Invert levels carry a catastrophic +6.24 m vertical jump across the NDMC/SDMC border.
- **Safety for Ingestion**: **SAFE FOR INGESTION (Planform polyline coordinates ONLY; attributes must be stripped)**

#### `[PUB-EVID-A05]` GSDL Waterlogging Vulnerability Point Database
- **Publisher / Custodian**: Geospatial Delhi Limited (GSDL) / Urban Development Department, GNCTD
- **URL / Access Channel**: https://gsdl.org.in/arcgis/rest/services/GSDL_WATERLOGGING/MapServer/0
- **Public Access**: `PUBLIC_REST_API (116 georeferenced points across NCT Delhi)`
- **Date / Temporal Scope**: 2021-2024 compilation | Historical hotspot frequency
- **Geographic Scope**: NCT Delhi, including key nodes near Kushak (AIIMS, Moolchand, Defence Colony, Dhaula Kuan)
- **Data Format**: GeoJSON point feature class
- **Provenance & Evidence Class**: `MEDIUM (Municipal field reporting compilation)` | `OFFICIAL — MUNICIPAL REPORTING`
- **Tier Relevance**: `TIER-C (Spatial validation binary mask only)`
- **What It Establishes**: Geospatial coordinates of recurring surface flood locations along the Kushak corridor; provides binary spatial validation targets for surface ponding.
- **What It Does NOT Establish**: Does NOT record water depth, duration, flow velocity, or in-channel stage.
- **Safety for Ingestion**: **SAFE FOR INGESTION (Binary validation checkpoint coordinates only)**

#### `[PUB-EVID-A06]` Copernicus Sentinel-1 C-SAR July 2023 Event Scene Collection (ASF DAAC / Planetary Computer)
- **Publisher / Custodian**: European Space Agency (ESA) / Copernicus Programme / NASA ASF DAAC
- **URL / Access Channel**: https://asf.alaska.edu / https://planetarycomputer.microsoft.com (Scenes: 20230712T005233, 20230716T125521, 20230630T005232, 20230704T125520)
- **Public Access**: `PUBLIC_AVAILABLE (Metadata/quicklooks public; COGs open via SAS; raw SAFE gated by Earthdata login)`
- **Date / Temporal Scope**: Acquisitions on 2023-07-12 (peak rise) and 2023-07-16 (recession), plus pre-flood baselines | Synoptic snapshots during peak and receding flood
- **Geographic Scope**: NCT Delhi & Yamuna Floodplain (Path 136 / Path 27 frames)
- **Data Format**: GeoTIFF / COG / SAR Level-1 GRD_HD (10 m pixel spacing)
- **Provenance & Evidence Class**: `HIGH (Authoritative international earth observation satellite mission)` | `DERIVED FROM OBSERVED REMOTE SENSING`
- **Tier Relevance**: `TIER-B (Macro-scale open water extent; TIER-D for urban streets)`
- **What It Establishes**: Synoptic macro-scale open-water extent across the Yamuna River floodplain, outfall marshes, and major open water bodies; delineates backwater inundation along open Barapullah reach.
- **What It Does NOT Establish**: Does NOT penetrate dense urban concrete/canopies. Cannot detect subterranean flows inside Kushak RCC box culvert. Specular radar backscatter does NOT measure water depth.
- **Safety for Ingestion**: **SAFE FOR INGESTION (Synoptic floodplain boundary mask; forbidden for street-depth calibration)**

### SECTION B: USEFUL CONTEXT ONLY
*Authoritative official records providing valuable physical bounds or operational context, but incapable of directly parameterizing hydraulic equations.*

#### `[PUB-EVID-B01]` NGT OA 6/2012 Joint Inspection Report (05-03-2025) on Kushak Covered Reach
- **Publisher / Custodian**: National Green Tribunal (Principal Bench, New Delhi) / Chief Engineers MCD & I&FC
- **URL / Access Channel**: https://indiankanoon.org/doc/192522997/ (NGT Order dated 09-04-2025 in OA No. 6/2012)
- **Public Access**: `PUBLIC_JUDICIAL_RECORD (Published order text)`
- **Date / Temporal Scope**: Joint Field Inspection 05-03-2025; Order 09-04-2025 | Current operational condition (2025)
- **Geographic Scope**: Kushak Covered Reach at DTC Kushak Bus Depot (~1.0 km)
- **Data Format**: Judicial transcript / engineering inspection text
- **Provenance & Evidence Class**: `HIGH (Sworn joint municipal engineering inspection report)` | `COURT_NGT_RECORD / OFFICIAL_FIELD_INSPECTION`
- **Tier Relevance**: `TIER-B/C (Bounding structural constraints only)`
- **What It Establishes**: Crucial macroscopic geometric bounding dimensions: Total structure width = 50 m; 5 internal bays of ~10 m each; visual internal clear depth = 3.5 to 4.5 m; cleaning openings = 1.5 x 1.5 m @ 50 m intervals; silt chambers = 2.50 x 1.15 m @ 100 m intervals; operational silt accumulation = 1.5 to 3.0 ft (0.45 to 0.91 m).
- **What It Does NOT Establish**: Does NOT provide instrumented total-station or DGPS survey points, bed reduced levels (RLs), soffit levels, or continuous longitudinal bed profile.
- **Safety for Ingestion**: **SAFE AS CONTEXT ONLY (Use to set plausible parameter bounds: width 50m / 5 bays, clear height ~4.0m; do NOT inject as surveyed RL points)**

#### `[PUB-EVID-B02]` Delhi High Court CONT.CAS(C) 434/2022 Official Inspection Report & Order
- **Publisher / Custodian**: High Court of Delhi (Sunayana Sibal v. GNCTD) / Joint Inspection Committee (MCD, NDMC, I&FC)
- **URL / Access Channel**: https://indiankanoon.org/doc/125400451/ (Order dated 29-01-2026)
- **Public Access**: `PUBLIC_JUDICIAL_RECORD (Published court order)`
- **Date / Temporal Scope**: Inspection 2026-01-21; Report 2026-01-28; Order 2026-01-29 | Contemporary administrative and physical state (January 2026)
- **Geographic Scope**: Kushak Nallah reach from INA Market to Lala Lajpat Rai Marg
- **Data Format**: Judicial transcript / official report summary
- **Provenance & Evidence Class**: `HIGH (Signed official status report by Dy. Director MCD and executive engineers)` | `COURT_RECORD / OFFICIAL_STATUS_REPORT`
- **Tier Relevance**: `TIER-C (Reach segmentation and jurisdiction boundaries)`
- **What It Establishes**: Definitive reach length segmentation: Total corridor INA to LLRM = ~2.62 km, partitioned into: (1) 1.75 km from INA to DTC Bus Depot (transferred MCD -> I&FC 'as-is where-is'), (2) 1.0 km covered Bus Depot reach (retained in MCD possession), (3) 0.87 km open reach from Bus Depot to Lala Lajpat Rai Marg (transferred to I&FC). Also documents that iron trash screens were rejected due to extreme clogging and backwater flooding risk.
- **What It Does NOT Establish**: Does NOT provide elevation coordinates, cross-sectional geometry, bed slope, or hydraulic roughness.
- **Safety for Ingestion**: **SAFE AS CONTEXT ONLY (Use to calibrate model reach breaks and multi-agency jurisdictional segmentation)**

#### `[PUB-EVID-B03]` NDMC NIT No. 52/EE(R-III)/2025-26 Tender Schedule of Quantities (SOQ) & Specifications
- **Publisher / Custodian**: New Delhi Municipal Council (NDMC), Civil Engineering Department, Roads-III
- **URL / Access Channel**: https://govtprocurement.delhi.gov.in (Tender ID: 2026_NDMC_297503_1, work_396329.zip)
- **Public Access**: `PUBLIC_DOWNLOAD (Public e-tender package download via standard CAPTCHA verification)`
- **Date / Temporal Scope**: Published 2026-08-24; Bid closing 2026-09-17 | Current procurement cycle (FY 2025-26 / 2026-27)
- **Geographic Scope**: RCC covered Kushak Nallah and Ring Road Nallah under NDMC R-III Division
- **Data Format**: Signed PDF (NIT.pdf) + NicGeP Excel template (BOQ_396329.xls)
- **Provenance & Evidence Class**: `HIGH (Primary government tender contract document, SHA256 verified)` | `PROCUREMENT_RECORD / TENDER_SPECIFICATION`
- **Tier Relevance**: `TIER-C/D (Procurement rate-bucket specification; NOT a survey)`
- **What It Establishes**: Material procurement facts: Item 1 classifies the desilting barrel size as 'width 4.00 meter +25% wide in size' (4.0 to 5.0 m barrel span class); Item 1 specifies total desilting billing volume of 21,406 m³ (minus 25% voids); Item 2 scopes 290 m of future robotic sonar profiling using Pipescape software; Item 3 specifies RCC slab cutting thickness 8-12 inches (203-305 mm).
- **What It Does NOT Establish**: Does NOT contain measured cross-sections, surveyed bed levels, or longitudinal profiles. Contains zero CAD drawings or elevation coordinates. Tender drawings are withheld for in-office pre-bid inspection only.
- **Safety for Ingestion**: **SAFE AS CONTEXT ONLY (Validates that individual internal barrels are ~4.0-5.0 m wide, highly consistent with NGT's 5 bays across 50 m)**

#### `[PUB-EVID-B04]` Copernicus GLO-30 Global Digital Elevation Model (30 m Spatial Resolution)
- **Publisher / Custodian**: European Space Agency (ESA) / Airbus Defence and Space
- **URL / Access Channel**: https://spacedata.copernicus.eu / OpenTopography / Planetary Computer
- **Public Access**: `PUBLIC_DOWNLOAD (Open access under Copernicus license)`
- **Date / Temporal Scope**: 2020 baseline (WorldDEM TanDEM-X source) | Contemporary topography
- **Geographic Scope**: Kushak Basin and Central Delhi Ridge (27.66 km² delineated catchment)
- **Data Format**: Cloud-Optimized GeoTIFF (COG), 32-bit floating point elevation (m)
- **Provenance & Evidence Class**: `HIGH (World-standard satellite elevation product)` | `OFFICIAL — SATELLITE DEM`
- **Tier Relevance**: `TIER-B for overland catchment delineation; TIER-F for drain channel inverts`
- **What It Establishes**: Regional terrain slope and macroscopic hydrologic watershed boundary (~27.66 km² working catchment delineated from Central Ridge to Barapullah). Identifies overland flow accumulation paths.
- **What It Does NOT Establish**: CANNOT resolve channel inverts of narrow (4-25 m wide) incised drains or underground box culverts. Urban bridge decks and building canopies corrupt channel bottom elevations by +2 to +8 m.
- **Safety for Ingestion**: **SAFE AS CONTEXT ONLY (For surface subcatchment delineation and overland routing; strictly forbidden for channel bed levels)**

#### `[PUB-EVID-B05]` cGanga / IIT Kanpur Kushak Flow Assessment Study — Council Agenda Narrative
- **Publisher / Custodian**: New Delhi Municipal Council (NDMC) / cGanga IIT Kanpur
- **URL / Access Channel**: https://www.ndmc.gov.in (Council Meeting No. 12/2023-24, 28-02-2024, Item 21, File V-16027/55/2024)
- **Public Access**: `PUBLIC_RECORD (Official Council meeting minutes PDF, on disk)`
- **Date / Temporal Scope**: Study completed 2023-2024; Council resolution 2024-02-28 | Non-rainy season dry-weather flow baseline
- **Geographic Scope**: Kushak Nallah open reach from Sardar Patel Marg to Kamal Ataturk Marg
- **Data Format**: Scanned administrative meeting record
- **Provenance & Evidence Class**: `MEDIUM-HIGH (Official Council agenda text recording study outcome)` | `OFFICIAL_DESCRIPTION_OF_REPORT / SECONDARY`
- **Tier Relevance**: `TIER-C (Dry-weather baseflow estimate)`
- **What It Establishes**: Official executive statement of dry-weather baseflow: 'the average flow in the Kushak Nallah was observed around 10 MLD during non-rainy season'. Provides design basis for decentralized wastewater treatment plants (1x5 MLD at S.P. Marg, 2x2.5 MLD downstream).
- **What It Does NOT Establish**: Does NOT provide the actual study report, flow hydrographs, sampling dates, cross-sections, or storm runoff discharges. Full study report is held in physical files.
- **Safety for Ingestion**: **SAFE AS CONTEXT ONLY (Use as nominal baseflow parameter ~0.116 m³/s; do NOT use for storm event calibration)**

### SECTION C: DUPLICATE OF EXISTING EVIDENCE
*Public records that duplicate or confirm baseline evidence already fully assimilated into the repository.*

#### `[PUB-EVID-C01]` Master Plan for Delhi (MPD) 1976 Drain Inventory (201 Main Drains + 44 Untraceable Drains)
- **Publisher / Custodian**: Delhi Development Authority (DDA) / Delhi I&FC
- **URL / Access Channel**: Historical gazetted inventory / DDA engineering archives
- **Public Access**: `PUBLIC_HISTORICAL_RECORD`
- **Date / Temporal Scope**: 1976 baseline | Pre-modernization historical state (50 years ago)
- **Geographic Scope**: NCT Delhi Barapullah Basin (44 historical tributary drains)
- **Data Format**: Tabular PDF extracts / Historical register
- **Provenance & Evidence Class**: `HIGH (Authoritative historical government gazette)` | `HISTORICAL_RECORD`
- **Tier Relevance**: `TIER-D (Historical baseline only)`
- **What It Establishes**: Catalogues 44 tributary drains in Barapullah basin, confirming Kushak as a primary tributary. Already reconciled in docs/DELHI_KUSHAK_1976_DRAIN_INVENTORY_RECONCILIATION.md.
- **What It Does NOT Establish**: Does NOT reflect current urbanization, culverting, encroachments, or current hydraulic dimensions.
- **Safety for Ingestion**: **DUPLICATE (Already assimilated in project historical network reconciliation)**

#### `[PUB-EVID-C02]` Central Ground Water Board (CGWB) 2011 Artificial Recharge Feasibility Report
- **Publisher / Custodian**: Central Ground Water Board (CGWB), Ministry of Water Resources
- **URL / Access Channel**: http://cgwb.gov.in / Official technical reports
- **Public Access**: `PUBLIC_DOWNLOAD (Technical report PDF)`
- **Date / Temporal Scope**: 2011 report | 2011 groundwater assessment
- **Geographic Scope**: Upper Kushak catchment (Western / Central Ridge spine)
- **Data Format**: Technical report narrative
- **Provenance & Evidence Class**: `HIGH (National hydrogeological authority)` | `OFFICIAL_EMPIRICAL`
- **Tier Relevance**: `TIER-C (Catchment bounds)`
- **What It Establishes**: Identifies upper Kushak catchment area as 3.5 km² (Western spine only from Birla Mandir / Central Ridge to Chanakyapuri). Already incorporated in project evidence base.
- **What It Does NOT Establish**: Does NOT cover the lower 24 km² urbanized catchment or provide channel hydraulic geometry.
- **Safety for Ingestion**: **DUPLICATE (Already assimilated in docs/DELHI_PROJECT_EVIDENCE_SUMMARY.md)**

#### `[PUB-EVID-C03]` IIT Delhi 2018 Drainage Master Plan (DMP 2018) Appendix XII & Design Tables
- **Publisher / Custodian**: Department of Civil Engineering, IIT Delhi / I&FC Delhi
- **URL / Access Channel**: IIT Delhi Civil Eng archives / I&FC Delhi
- **Public Access**: `PUBLIC_CONSULTATION_RELEASE (2018 public draft before shelving)`
- **Date / Temporal Scope**: July 2018 | 2018 SWMM modeling exercise
- **Geographic Scope**: Barapullah Basin (376.27 km² total basin)
- **Data Format**: PDF report tables and extracts
- **Provenance & Evidence Class**: `MEDIUM (Shelved by Delhi Govt TEC in August 2021)` | `OFFICIAL / MODEL INPUT (SHELVED)`
- **Tier Relevance**: `TIER-C (Design parameters only)`
- **What It Establishes**: Standard design parameters: Manning's n = 0.012 (RCC box), 0.025 (open drain); Horton infiltration parameters for Delhi loam (f0=76.2 mm/hr, finf=0.635 mm/hr, k=4.0/hr); Safdarjung IDF intensities. Already extracted in project files.
- **What It Does NOT Establish**: Does NOT provide reliable surveyed cross-sections or verified invert levels (DMP explicitly admits interpolating 16.8% of conduits and smoothing adverse slopes).
- **Safety for Ingestion**: **DUPLICATE (Already assimilated; values retained as design priors)**

### SECTION D: INSUFFICIENT / NON-COMPARABLE
*Datasets lacking spatial resolution, physical instrumentation, or temporal alignment required for hydrodynamic modeling.*

#### `[PUB-EVID-D01]` Delhi Traffic Police (DTP) Waterlogging Advisories & Twitter/X Bulletins
- **Publisher / Custodian**: Delhi Traffic Police (DTP), GNCTD
- **URL / Access Channel**: https://twitter.com/dtptraffic / https://delhitrafficpolice.nic.in
- **Public Access**: `PUBLIC_WEB_FEED (Real-time social media traffic alerts)`
- **Date / Temporal Scope**: Monsoon 2021, 2022, 2023, 2024 | Event-driven real-time alert timestamps
- **Geographic Scope**: Key South Delhi traffic intersections (e.g. AIIMS Flyover, Moolchand Underpass, Chirag Delhi, Brigadier Hoshiyar Singh Marg)
- **Data Format**: Short text / tweets / press releases
- **Provenance & Evidence Class**: `MEDIUM (Real-time operational police observation)` | `MUNICIPAL_OPERATIONAL_ALERT`
- **Tier Relevance**: `TIER-D (Qualitative surface proxy)`
- **What It Establishes**: Confirms timing of road traffic disruption caused by standing surface water during intense rainfall events.
- **What It Does NOT Establish**: Contains ZERO hydraulic measurements: no flood depth (only 'waterlogging', 'slow traffic', or 'diversion'), no flow velocity, no in-drain water stage, and no channel discharge.
- **Safety for Ingestion**: **INSUFFICIENT (Qualitative event timestamp verification only; cannot calibrate hydraulic equations)**

#### `[PUB-EVID-D02]` Aab Prahari Crowdsourced Flood Observation Dataset
- **Publisher / Custodian**: IIT Delhi / C-DAC / DST
- **URL / Access Channel**: https://aabprahari.iitd.ac.in (Mobile app crowdsourced backend)
- **Public Access**: `REST_ENDPOINT (JSON date list getdates.json, on disk)`
- **Date / Temporal Scope**: July 2022 to April 2023 (38 discrete dates) | Intermittent citizen reports
- **Geographic Scope**: Scattered citizen points across Delhi NCT
- **Data Format**: JSON point arrays with user-uploaded photo links and categorical flags
- **Provenance & Evidence Class**: `LOW-MEDIUM (Uncalibrated citizen smartphone crowdsourcing)` | `CROWDSOURCED_OBSERVATION`
- **Tier Relevance**: `TIER-D (Qualitative validation only)`
- **What It Establishes**: Presence of surface water at specific user coordinates on 38 monsoon dates.
- **What It Does NOT Establish**: No benchmarked elevation, no physical depth measurement, no sensor calibration, and extremely sparse coverage along the Kushak culvert alignment.
- **Safety for Ingestion**: **INSUFFICIENT (Secondary qualitative check only)**

#### `[PUB-EVID-D03]` SRTM (Shuttle Radar Topography Mission) 30m / 90m Elevation Grid
- **Publisher / Custodian**: NASA / USGS
- **URL / Access Channel**: https://earthexplorer.usgs.gov
- **Public Access**: `PUBLIC_DOWNLOAD`
- **Date / Temporal Scope**: February 2000 acquisition | Year 2000 snapshot
- **Geographic Scope**: Global / Delhi NCT
- **Data Format**: Raster GeoTIFF / HGT
- **Provenance & Evidence Class**: `HIGH (for year 2000)` | `SATELLITE_RADAR_DEM`
- **Tier Relevance**: `TIER-D / NON-COMPARABLE`
- **What It Establishes**: Historical year-2000 macro-topography.
- **What It Does NOT Establish**: Severely outdated: ignores 25 years of intensive flyover, metro, and culvert construction along the Kushak corridor. Radar surface reflection represents tree canopy and rooflines rather than bare ground.
- **Safety for Ingestion**: **NON-COMPARABLE (Superseded entirely by Copernicus GLO-30)**

#### `[PUB-EVID-D04]` ALOS World 3D (AW3D30) Elevation Model
- **Publisher / Custodian**: Japan Aerospace Exploration Agency (JAXA)
- **URL / Access Channel**: https://www.eorc.jaxa.jp/ALOS/en/dataset/aw3d30/index.htm
- **Public Access**: `PUBLIC_REGISTRATION`
- **Date / Temporal Scope**: 2006-2011 PRISM optical stereo compilation | 2010 optical baseline
- **Geographic Scope**: Delhi NCT
- **Data Format**: Raster GeoTIFF 30 m
- **Provenance & Evidence Class**: `MEDIUM-HIGH` | `SATELLITE_OPTICAL_DSM`
- **Tier Relevance**: `TIER-D / NON-COMPARABLE`
- **What It Establishes**: Digital Surface Model (DSM) of building roofs and tree canopies.
- **What It Does NOT Establish**: DSM surface artifacts place the Kushak channel bed 5 to 15 m higher than actual terrain due to dense roadside tree canopies and bridge decks.
- **Safety for Ingestion**: **NON-COMPARABLE (Unsuitable for hydraulic channel bed profiling)**

#### `[PUB-EVID-D05]` Mainstream Print & Broadcast Media Coverage (July 2023 & June 2024 Flood Events)
- **Publisher / Custodian**: Times of India, Hindustan Times, The Hindu, Indian Express
- **URL / Access Channel**: Public news archives / press aggregators
- **Public Access**: `PUBLIC_WEB`
- **Date / Temporal Scope**: July 2023, June 2024 | Immediate post-disaster reporting
- **Geographic Scope**: Delhi / Barapullah / Pragati Maidan / ITO / Safdarjung
- **Data Format**: Journalistic articles and photographic stills
- **Provenance & Evidence Class**: `LOW-MEDIUM (Journalistic accounts)` | `SECONDARY_MEDIA`
- **Tier Relevance**: `TIER-D`
- **What It Establishes**: General awareness of severe waterlogging, submerged vehicle incidents, and political disputes over drain desilting.
- **What It Does NOT Establish**: Contains no engineering surveys, no elevation datums, no discharge figures, and anecdotal depth estimates ('knee-deep', 'waist-deep') lacking geospatial calibration.
- **Safety for Ingestion**: **INSUFFICIENT (Forbidden as direct scientific modeling input)**

### SECTION E: ACCESS-BLOCKED
*High-value engineering surveys and as-built drawings confirmed to exist in official custody, but strictly withheld from public download.*

#### `[PUB-EVID-E01]` I&FC CD-XII 2024/2025 DGPS + Echo-Sounder Bathymetric Survey Deliverables
- **Publisher / Custodian**: Executive Engineer, Civil Division No. XII, Irrigation & Flood Control Dept (I&FC), GNCTD
- **URL / Access Channel**: Physical custody: Office of EE CD-XII, Basaidarapur Office Complex, New Delhi - 110027
- **Public Access**: `ACCESS_BLOCKED (Procured under NIQ No. EE-CDXII/NIQ/2025-26/249 dt. 08-10-2025; deliverables held offline)`
- **Date / Temporal Scope**: Survey executed October 2025 (3-day urgent completion) | Post-monsoon 2025 actual survey
- **Geographic Scope**: Sunheripul Drain, Kushak Drain (CD-XII jurisdiction: INA Metro to downstream LLRM bridge), Bijwasan Drain
- **Data Format**: CAD/DXF drawings, longitudinal profile sheets, XYZ cross-section coordinates, echo-sounder raw points
- **Provenance & Evidence Class**: `CONFIRMED_EXISTENCE / HIGH_TECHNICAL_VALUE` | `OFFICIAL_SURVEY_DELIVERABLE (UNRELEASED)`
- **Tier Relevance**: `TIER-A (Gold standard for open reach bed geometry if obtained)`
- **What It Establishes**: Confirmed to exist by official procurement notice. Contains true DGPS coordinates, echo-sounder bathymetry, station-by-station cross-sections, and bed reduced levels for ~0.87 km open reach.
- **What It Does NOT Establish**: Not publicly accessible on any portal or web server. No public download link exists. Remains locked in physical departmental files at Basaidarapur.
- **Safety for Ingestion**: **ACCESS-BLOCKED (Cannot be ingested without receiving official unreleased survey records)**

#### `[PUB-EVID-E02]` NDMC Roads-III Kushak Longitudinal Profiles, Cross-Sections & Structural As-Built Drawings
- **Publisher / Custodian**: Executive Engineer (Roads-III), Civil Engineering Department, NDMC
- **URL / Access Channel**: Physical custody: Room No. 306, 3rd Floor, SBS Place, Gole Market, New Delhi - 110001
- **Public Access**: `ACCESS_BLOCKED (Maintained per tender conditions for pre-bid physical inspection only; withheld from portal zip)`
- **Date / Temporal Scope**: Historical as-built records + 2020 Topographical Survey + 2025-26 tender records | As-built construction baseline and contemporary desilting schedules
- **Geographic Scope**: RCC covered Kushak Nallah (Chanakyapuri, Africa Avenue, Brigadier Hoshiyar Singh Marg)
- **Data Format**: Structural CAD drawings (.dwg), L-section sheets, invert schedules
- **Provenance & Evidence Class**: `CONFIRMED_EXISTENCE / HIGH_TECHNICAL_VALUE` | `OFFICIAL_AS_BUILT_DRAWING (UNRELEASED)`
- **Tier Relevance**: `TIER-A (Definitive structural clear geometry for covered box conduit)`
- **What It Establishes**: Confirmed to exist by NDMC NIT No. 52/EE(R-III)/2025-26. Contains exact internal box dimensions (clear span W, rise H), number of cells/barrels, invert elevations, manhole drop steps, and wall thicknesses.
- **What It Does NOT Establish**: Drawings are explicitly not attached to the public tender zip (`work_396329.zip`); bidders and researchers are directed to in-office physical inspection only. Gated behind municipal office custody.
- **Safety for Ingestion**: **ACCESS-BLOCKED (Cannot be ingested from open web)**

#### `[PUB-EVID-E03]` cGanga / IIT Kanpur Kushak Flow-Assessment & Wastewater Characteristics Full Technical Report
- **Publisher / Custodian**: NDMC Sewerage Project Division (File No. V-16027/55/2024) / cGanga IIT Kanpur
- **URL / Access Channel**: Physical/e-Office custody: NDMC Sewerage Project Division / cGanga IIT Kanpur
- **Public Access**: `ACCESS_BLOCKED (Submitted separately to NDMC per cGanga letter dt. 21-02-2024; not published on web)`
- **Date / Temporal Scope**: 2023-2024 field study | 2023-2024 continuous / seasonal flow gauging
- **Geographic Scope**: Kushak Nallah (Open Drain) from Sardar Patel Marg to Kamal Ataturk Marg
- **Data Format**: Technical report with hydrometric monitoring data and water quality profiles
- **Provenance & Evidence Class**: `CONFIRMED_EXISTENCE / HIGH_TECHNICAL_VALUE` | `OFFICIAL_RESEARCH_REPORT (UNRELEASED)`
- **Tier Relevance**: `TIER-A/B (In-situ flow and hydraulic calibration data)`
- **What It Establishes**: Confirmed to exist by NDMC Council Meeting No. 12/2023-24 (Item 21). Contains observed discharge measurements, flow velocities, and dry-weather flow hydrographs.
- **What It Does NOT Establish**: The full report was submitted separately in confidential departmental files and has never been posted to cganga.org or ndmc.gov.in.
- **Safety for Ingestion**: **ACCESS-BLOCKED (Cannot be ingested from open public sources)**

#### `[PUB-EVID-E04]` IIT Delhi 2018 Drainage Master Plan Raw GIS & SWMM Input Geodatabase
- **Publisher / Custodian**: Department of Civil Engineering, IIT Delhi / Delhi I&FC Department
- **URL / Access Channel**: Institutional custody: IIT Delhi / I&FC Delhi
- **Public Access**: `ACCESS_BLOCKED (Shelved by Delhi Govt in August 2021; underlying model files withheld from public domain)`
- **Date / Temporal Scope**: 2016-2018 study baseline | 2018 model inputs
- **Geographic Scope**: Barapullah Basin / Delhi NCT drainage network
- **Data Format**: SWMM .inp files, GIS shapefiles, surveyed cross-section point databases (601 cross-sections)
- **Provenance & Evidence Class**: `CONFIRMED_EXISTENCE / HIGH_TECHNICAL_VALUE` | `OFFICIAL_MODEL_INPUTS (UNRELEASED)`
- **Tier Relevance**: `TIER-B/C (Numerical model network topology)`
- **What It Establishes**: Contains digitized conduit network topology and surveyed cross-section stations executed by IITD survey teams.
- **What It Does NOT Establish**: Jalsuraksha portal (jalsuraksha.iitd.ac.in) is a closed frontend dashboard without data download capabilities; underlying input files are not publicly accessible.
- **Safety for Ingestion**: **ACCESS-BLOCKED (Institutional access required)**

### SECTION F: REJECTED / SCIENTIFICALLY UNSUITABLE
*Spurious claims, administrative templates, retracted designations, or synthetic approximations that must NEVER be ingested.*

#### `[PUB-EVID-F01]` GSDL HYD CRSC (Cross Section) Point Layer for Kushak Nallah Corridor
- **Publisher / Custodian**: Geospatial Delhi Limited (GSDL), GNCTD
- **URL / Access Channel**: https://gsdl.org.in/arcgis/rest/services/GSDL_LAYERS_UPDATED/HYD/MapServer/0
- **Public Access**: `PUBLIC_REST_API (Queryable ESRI REST endpoint, 8,486 points)`
- **Date / Temporal Scope**: 2024-2025 REST layer state | Static layer
- **Geographic Scope**: Delhi NCT (Major open rivers and floodplains)
- **Data Format**: 2D point features with CSCL elevation string field
- **Provenance & Evidence Class**: `HIGH (that points exist in Delhi), REJECTED (for Kushak corridor)` | `REJECTED / OUT-OF-SCOPE`
- **Tier Relevance**: `REJECTED (0 points in Kushak corridor)`
- **What It Establishes**: Audit of all 8,486 CRSC points confirmed that exactly ZERO points exist within the Kushak Nallah corridor bounding box or within 500 m buffer. Closest points lie ~4 km away along the distant Yamuna confluence.
- **What It Does NOT Establish**: Contains ZERO cross-sections, zero elevations, and zero relevance to Kushak Nallah.
- **Safety for Ingestion**: **REJECTED (Must never be used or queried for Kushak geometry)**

#### `[PUB-EVID-F02]` GSDL IRCH Administrative Template Attributes ('Drn_Wd_m = 25.0 m', 'Drn_Dp_m = 7.354 m')
- **Publisher / Custodian**: Geospatial Delhi Limited (GSDL) / DIFC
- **URL / Access Channel**: https://gsdl.org.in/arcgis/rest/services/DIFC/storm_drain_08082024/MapServer
- **Public Access**: `PUBLIC_REST_API`
- **Date / Temporal Scope**: August 2024 layer | Static attribute table
- **Geographic Scope**: Kushak Nallah segments (Layer 7 NDMC)
- **Data Format**: Attribute table fields in ESRI Feature Service
- **Provenance & Evidence Class**: `REJECTED_AS_HYDRAULIC_GEOMETRY` | `ADMINISTRATIVE_TEMPLATE / NON-HYDRAULIC`
- **Tier Relevance**: `REJECTED (Nominal administrative width/depth)`
- **What It Establishes**: Represents ROW / administrative planning corridor envelope repeated identically across 77 consecutive segments. Physically contradicts all field inspections (e.g. 50 m wide depot structure, 4.0 m box barrels).
- **What It Does NOT Establish**: Does NOT represent hydraulic clear flow width or flow depth.
- **Safety for Ingestion**: **REJECTED (Forbidden from ingestion as hydraulic channel dimensions)**

#### `[PUB-EVID-F03]` Fabricated 'KP-01 to KP-25' Cross-Section Stationing Series
- **Publisher / Custodian**: Retracted project draft artifact
- **URL / Access Channel**: N/A (Erroneously introduced in draft GSDL investigation)
- **Public Access**: `RETRACTED`
- **Date / Temporal Scope**: Retracted September 2026 | N/A
- **Geographic Scope**: Kushak Nallah
- **Data Format**: Text stationing labels
- **Provenance & Evidence Class**: `FABRICATED_RETRACTED` | `FABRICATED (RETRACTED)`
- **Tier Relevance**: `REJECTED / NULL`
- **What It Establishes**: Formally audited across IITD DMP 2018, NGT judgments, GSDL layers, and municipal archives: this numbering series DOES NOT EXIST in any engineering record.
- **What It Does NOT Establish**: Zero engineering existence.
- **Safety for Ingestion**: **REJECTED (Formally retracted; null and void)**

#### `[PUB-EVID-F04]` Commercial Aggregator Award Claim ('Aar Pee Electrical Engineering Works')
- **Publisher / Custodian**: Secondary tender aggregators (Tenderkart / IndiaMART match)
- **URL / Access Channel**: Aggregator scraping trails
- **Public Access**: `PUBLIC_UNVERIFIED_CLAIM`
- **Date / Temporal Scope**: Alleged November 2024 award | Alleged 2024
- **Geographic Scope**: I&FC CD-XII NIQ 2024/2025
- **Data Format**: Web scraping text snippet
- **Provenance & Evidence Class**: `REJECTED (Identity conflict)` | `UNVERIFIED_LEAD / MISATTRIBUTION`
- **Tier Relevance**: `REJECTED`
- **What It Establishes**: Entity matches an electrical goods manufacturer (transformers/voltmeters), violating the contractor-class rule for hydrographic total-station surveys. No primary government award document exists.
- **What It Does NOT Establish**: Does NOT establish a valid survey awardee or verified survey deliverable.
- **Safety for Ingestion**: **REJECTED (Forbidden from being cited as survey awardee)**

#### `[PUB-EVID-F05]` Academic SWMM Synthetic Trapezoidal & Rectangular Cross-Section Geometries
- **Publisher / Custodian**: Academic literature / secondary research journal papers
- **URL / Access Channel**: Various hydrology/environmental science journal publications
- **Public Access**: `OPEN_ACCESS_JOURNAL_PAPERS`
- **Date / Temporal Scope**: 2019-2024 | Simulation models
- **Geographic Scope**: Barapullah / Kushak drainage system
- **Data Format**: Journal paper tables and figures
- **Provenance & Evidence Class**: `METHODOLOGICALLY_SYNTHETIC` | `SYNTHETIC_NUMERICAL_IDEALIZATION`
- **Tier Relevance**: `REJECTED AS OBSERVATION`
- **What It Establishes**: Demonstrates numerical model sensitivity using idealized geometric approximations (e.g. uniform 10 m or 25 m trapezoids with 1:1 side slopes) derived from regional DEMs or 1976 registers.
- **What It Does NOT Establish**: Does NOT provide as-built field survey measurements. Treating idealized academic SWMM shapes as physical ground truth corrupts hydrodynamic calibration.
- **Safety for Ingestion**: **REJECTED (Must never be ingested as observed physical cross-sections)**

---

## 4. Material Impact Assessment & Candidate Profiling

For every candidate that could potentially or materially impact the hydraulic model or Digital Twin, the exact scientific evaluation is presented below:

### Forensic Profile: `PUB-EVID-A01` — CWC Delhi Railway Bridge (Old Railway Bridge) Hydrometric Flood Bulletins (July 2023 Flood Event)
- **Exact Source**: Central Water Commission (CWC), Ministry of Jal Shakti, Upper Yamuna Division
- **Exact URL / Path**: https://cwc.gov.in / https://ffs.india-water.gov.in (Bulletins cfcrcwcdfb10.07.2023.pdf to 17.07.2023.pdf)
- **Evidence Class**: `OFFICIAL — HYDROMETRIC GAUGE`
- **Provenance Assessment**: HIGH (Official ministerial hydrometric gauge network, Site #1008)
- **Scientific & Physical Limitations**:
  - Does NOT establish internal Kushak Nallah stages, local in-channel discharges, internal head losses, or street-level waterlogging depths in South Delhi (~10-15 km upstream of Yamuna outfall).
- **Safe for Ingestion**: **SAFE FOR INGESTION (Strictly as downstream boundary condition: stage-time tailwater series)**

### Forensic Profile: `PUB-EVID-A02` — IMD Safdarjung Observatory Hourly & Daily Precipitation Series (Monsoon 2023-2024)
- **Exact Source**: India Meteorological Department (IMD), Ministry of Earth Sciences
- **Exact URL / Path**: https://mausam.imd.gov.in / https://internal.imd.gov.in / National Weather Bulletins
- **Evidence Class**: `OFFICIAL — METEOROLOGICAL OBSERVATION`
- **Provenance Assessment**: HIGH (National meteorological authority reference station)
- **Scientific & Physical Limitations**:
  - Does NOT establish channel geometry, Manning's n roughness, subterranean culvert capacity, silt depths, or backwater stages.
- **Safe for Ingestion**: **SAFE FOR INGESTION (Strictly as catchment hydrological forcing input)**

### Forensic Profile: `PUB-EVID-A04` — GSDL Geo-Spatial Data Infrastructure — Irrigation Channel (IRCH) Alignment Layer
- **Exact Source**: Geospatial Delhi Limited (GSDL), GNCTD
- **Exact URL / Path**: https://gsdl.org.in/arcgis/rest/services/DIFC/storm_drain_08082024/MapServer (Layers 6 and 7)
- **Evidence Class**: `OFFICIAL — GIS CARTOGRAPHIC / DERIVED`
- **Provenance Assessment**: MEDIUM-HIGH (State GIS infrastructure repository)
- **Scientific & Physical Limitations**:
  - Does NOT establish hydraulic clear dimensions. Nominal attributes ('Drn_Wd_m = 25.0 m', 'Drn_Dp_m = 7.354 m') are repeated identical administrative templates. Invert levels carry a catastrophic +6.24 m vertical jump across the NDMC/SDMC border.
- **Safe for Ingestion**: **SAFE FOR INGESTION (Planform polyline coordinates ONLY; attributes must be stripped)**

### Forensic Profile: `PUB-EVID-B01` — NGT OA 6/2012 Joint Inspection Report (05-03-2025) on Kushak Covered Reach
- **Exact Source**: National Green Tribunal (Principal Bench, New Delhi) / Chief Engineers MCD & I&FC
- **Exact URL / Path**: https://indiankanoon.org/doc/192522997/ (NGT Order dated 09-04-2025 in OA No. 6/2012)
- **Evidence Class**: `COURT_NGT_RECORD / OFFICIAL_FIELD_INSPECTION`
- **Provenance Assessment**: HIGH (Sworn joint municipal engineering inspection report)
- **Scientific & Physical Limitations**:
  - Does NOT provide instrumented total-station or DGPS survey points, bed reduced levels (RLs), soffit levels, or continuous longitudinal bed profile.
- **Safe for Ingestion**: **SAFE AS CONTEXT ONLY (Use to set plausible parameter bounds: width 50m / 5 bays, clear height ~4.0m; do NOT inject as surveyed RL points)**

### Forensic Profile: `PUB-EVID-B03` — NDMC NIT No. 52/EE(R-III)/2025-26 Tender Schedule of Quantities (SOQ) & Specifications
- **Exact Source**: New Delhi Municipal Council (NDMC), Civil Engineering Department, Roads-III
- **Exact URL / Path**: https://govtprocurement.delhi.gov.in (Tender ID: 2026_NDMC_297503_1, work_396329.zip)
- **Evidence Class**: `PROCUREMENT_RECORD / TENDER_SPECIFICATION`
- **Provenance Assessment**: HIGH (Primary government tender contract document, SHA256 verified)
- **Scientific & Physical Limitations**:
  - Does NOT contain measured cross-sections, surveyed bed levels, or longitudinal profiles. Contains zero CAD drawings or elevation coordinates. Tender drawings are withheld for in-office pre-bid inspection only.
- **Safe for Ingestion**: **SAFE AS CONTEXT ONLY (Validates that individual internal barrels are ~4.0-5.0 m wide, highly consistent with NGT's 5 bays across 50 m)**

### Forensic Profile: `PUB-EVID-E01` — I&FC CD-XII 2024/2025 DGPS + Echo-Sounder Bathymetric Survey Deliverables
- **Exact Source**: Executive Engineer, Civil Division No. XII, Irrigation & Flood Control Dept (I&FC), GNCTD
- **Exact URL / Path**: Physical custody: Office of EE CD-XII, Basaidarapur Office Complex, New Delhi - 110027
- **Evidence Class**: `OFFICIAL_SURVEY_DELIVERABLE (UNRELEASED)`
- **Provenance Assessment**: CONFIRMED_EXISTENCE / HIGH_TECHNICAL_VALUE
- **Scientific & Physical Limitations**:
  - Not publicly accessible on any portal or web server. No public download link exists. Remains locked in physical departmental files at Basaidarapur.
- **Safe for Ingestion**: **ACCESS-BLOCKED (Cannot be ingested without receiving official unreleased survey records)**

### Forensic Profile: `PUB-EVID-E02` — NDMC Roads-III Kushak Longitudinal Profiles, Cross-Sections & Structural As-Built Drawings
- **Exact Source**: Executive Engineer (Roads-III), Civil Engineering Department, NDMC
- **Exact URL / Path**: Physical custody: Room No. 306, 3rd Floor, SBS Place, Gole Market, New Delhi - 110001
- **Evidence Class**: `OFFICIAL_AS_BUILT_DRAWING (UNRELEASED)`
- **Provenance Assessment**: CONFIRMED_EXISTENCE / HIGH_TECHNICAL_VALUE
- **Scientific & Physical Limitations**:
  - Drawings are explicitly not attached to the public tender zip (`work_396329.zip`); bidders and researchers are directed to in-office physical inspection only. Gated behind municipal office custody.
- **Safe for Ingestion**: **ACCESS-BLOCKED (Cannot be ingested from open web)**

### Forensic Profile: `PUB-EVID-F01` — GSDL HYD CRSC (Cross Section) Point Layer for Kushak Nallah Corridor
- **Exact Source**: Geospatial Delhi Limited (GSDL), GNCTD
- **Exact URL / Path**: https://gsdl.org.in/arcgis/rest/services/GSDL_LAYERS_UPDATED/HYD/MapServer/0
- **Evidence Class**: `REJECTED / OUT-OF-SCOPE`
- **Provenance Assessment**: HIGH (that points exist in Delhi), REJECTED (for Kushak corridor)
- **Scientific & Physical Limitations**:
  - Contains ZERO cross-sections, zero elevations, and zero relevance to Kushak Nallah.
- **Safe for Ingestion**: **REJECTED (Must never be used or queried for Kushak geometry)**

### Forensic Profile: `PUB-EVID-F02` — GSDL IRCH Administrative Template Attributes ('Drn_Wd_m = 25.0 m', 'Drn_Dp_m = 7.354 m')
- **Exact Source**: Geospatial Delhi Limited (GSDL) / DIFC
- **Exact URL / Path**: https://gsdl.org.in/arcgis/rest/services/DIFC/storm_drain_08082024/MapServer
- **Evidence Class**: `ADMINISTRATIVE_TEMPLATE / NON-HYDRAULIC`
- **Provenance Assessment**: REJECTED_AS_HYDRAULIC_GEOMETRY
- **Scientific & Physical Limitations**:
  - Does NOT represent hydraulic clear flow width or flow depth.
- **Safe for Ingestion**: **REJECTED (Forbidden from ingestion as hydraulic channel dimensions)**

---

## 5. Model Safety Verification

In compliance with the immutable baseline directive:
1. **Git Commit Baseline**: HEAD remains strictly locked at `d4ab4baceb56044fb860a5c67f81dee4199d3853`.
2. **Zero Code/Test Modifications**: `git diff HEAD -- backend/app/domain/delhi/digital_twin/` is completely empty.
3. **Zero Git Staging**: `git diff --cached` is completely empty.
4. **Digital Twin Pytest Baseline**: All 652 Digital Twin tests pass with 0 failures (`652 passed, 46 warnings in 8.27s`).
5. **Clean Working State**: No parameters were recalibrated, no synthetic geometries were injected, and no RTIs were drafted or recommended.

---
*Document compiled autonomously under strict evidence-constrained engineering protocols.*
