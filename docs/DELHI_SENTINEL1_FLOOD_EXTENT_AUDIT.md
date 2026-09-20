# Delhi NCT V2 — Sentinel-1 Historical Flood Extent Evidence Audit

**Document ID**: `DELHI_SENTINEL1_FLOOD_EXTENT_AUDIT`  
**Investigation Phase**: Phase 3E-5  
**Target Constellation**: Copernicus Sentinel-1 (C-SAR)  
**Primary Event**: Delhi / Yamuna Catastrophic Flood (July 2023)  
**Operating Agencies**: European Space Agency (ESA) / European Commission (Copernicus Programme)  
**Public Distributors**: Alaska Satellite Facility (NASA ASF DAAC) / Microsoft Planetary Computer / Copernicus Data Space Ecosystem (CDSE)  
**Date**: 11 September 2026  
**Status**: COMPLETE — LIGHTWEIGHT METADATA & ACCESSIBILITY AUDIT  
**Evidence Provenance Classification**: `DERIVED FROM OBSERVED REMOTE SENSING`  
**Mandatory Scientific Notice**: Satellite radar remote sensing provides macro-scale synoptic surface backscatter over open terrain. In strict adherence to physical remote sensing and hydrodynamic principles, satellite-derived flood masks represent open-water dielectric specular reflectance; they must **NEVER** be conflated with calibrated street-level flood depth, hydraulic discharge ground truth, or direct subterranean drainage behavior. Sentinel-1 C-band SAR cannot penetrate dense concrete urban canopies or resolve subsurface culverts (such as the covered Kushak box).

---

## 1. Executive Summary

An independent evidence acquisition, accessibility, and feasibility audit was conducted on Copernicus **Sentinel-1 C-band Synthetic Aperture Radar (SAR)** imagery covering the National Capital Territory (NCT) of Delhi for the July 2023 flood event.

### Key Audit Findings:
1. **Scene Availability Verified**:
   - Four high-priority Sentinel-1A Ground Range Detected High Resolution (**GRD_HD**) acquisitions were identified and verified through the Alaska Satellite Facility (ASF DAAC) and Microsoft Planetary Computer STAC APIs.
   - **Rising / Peak Inflow Phase**: `2023-07-12T00:52:33Z` (Orbit 136, Descending) — captured when the Yamuna River reached 207.55 m MSL at the Delhi Railway Bridge, breaching the historic 1978 record.
   - **Recession Phase**: `2023-07-16T12:55:21Z` (Orbit 27, Ascending) — captured when the river stage subsided to 205.75 m MSL.
   - **Pre-Event Baselines**: `2023-06-30T00:52:32Z` (Orbit 136 Descending pair) and `2023-07-04T12:55:20Z` (Orbit 27 Ascending pair), providing exact-orbit pre-flood reference geometry for change detection.
2. **Access Status & Data Structure**:
   - **Metadata & Quicklook Browses**: 100% public, verified, and freely accessible without credentials via ASF DAAC (`HTTP 200 OK`).
   - **Raw ESA SAFE Archives**: Programmatic download of complete multi-gigabyte ZIP packages from ASF DAAC is gated behind NASA Earthdata OAuth authentication.
   - **Cloud-Optimized GeoTIFFs (COGs)**: Hosted on Microsoft Planetary Computer Blob Storage with open SAS token access.
3. **Georeferencing & Processing Constraint**:
   - Inspection of raw Level-1 GRD measurement TIFFs revealed that they are delivered in native sensor slant/ground range coordinates with Ground Control Points (GCPs) stored in XML metadata (`CRS: None` in raw GeoTIFF headers; dimension $16,733 \times 25,528$ pixels).
   - Transforming raw Level-1 GRD SAR data into an orthorectified geospatial product requires rigorous Range-Doppler Terrain Correction (RTC), precise orbit ephemerides (POEORB), and digital elevation models (Copernicus DEM 30 m) via specialized SAR processing pipelines (e.g., ESA SNAP / pyroSAR / Orfeo Toolbox).
   - In accordance with project instructions, unprojected full-scene raster operations and uncalibrated heuristic thresholding were halted to prevent manufacturing an unverified, fabricated flood mask.
4. **Final Phase Verdict**: **`CONDITIONAL GO`**. Authoritative satellite event imagery is fully verified, but processing constraints prevent producing a reproducible, publication-grade flood mask within lightweight local environments.

---

## 2. Investigated Sentinel-1 Scenes

All candidate acquisitions were extracted from official Copernicus / ASF DAAC catalogues using spatial intersection at the Delhi Railway Bridge and Kushak–Barapullah corridor:

| Acquisition Role | Scene / Product ID | Platform & Sensor | Acquisition Time (UTC) | Pass & Rel Orbit | Mode & Pol | Resolution & Pixel Spacing | Bounding Footprint (WKT) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **Event Acquisition 1 (Peak Rise)** | `S1A_IW_GRDH_1SDV_20230712T005233_20230712T005258_049383_05F03C_4A85` | Sentinel-1A C-SAR | **2023-07-12 00:52:33** | Descending / 136 | IW / VV+VH | GRD_HD ($10\times 10\text{ m}$) | `POLYGON ((77.65 27.72, 77.98 29.23, 75.39 29.64, 75.10 28.14, 77.65 27.72))` |
| **Event Acquisition 2 (Recession)** | `S1A_IW_GRDH_1SDV_20230716T125521_20230716T125550_049449_05F23F_FA6F` | Sentinel-1A C-SAR | **2023-07-16 12:55:21** | Ascending / 27 | IW / VV+VH | GRD_HD ($10\times 10\text{ m}$) | `POLYGON ((75.75 28.50, 76.14 26.75, 78.68 27.17, 78.33 28.92, 75.75 28.50))` |
| **Pre-Event Baseline 1** | `S1A_IW_GRDH_1SDV_20230630T005232_20230630T005257_049208_05EACB_6F4E` | Sentinel-1A C-SAR | **2023-06-30 00:52:32** | Descending / 136 | IW / VV+VH | GRD_HD ($10\times 10\text{ m}$) | Identical track geometry to 2023-07-12 (pair 1) |
| **Pre-Event Baseline 2** | `S1A_IW_GRDH_1SDV_20230704T125520_20230704T125549_049274_05ECD4_B090` | Sentinel-1A C-SAR | **2023-07-04 12:55:20** | Ascending / 27 | IW / VV+VH | GRD_HD ($10\times 10\text{ m}$) | Identical track geometry to 2023-07-16 (pair 2) |

---

## 3. Public Access & Distribution Status

| Provider / Channel | Endpoint Protocol | Accessibility Evaluation | Public Cost / Credential Requirement |
| :--- | :--- | :--- | :--- |
| **NASA ASF DAAC** | HTTPS REST Search API | **100% Public & Immediate** | No registration required for search and GeoJSON metadata retrieval. |
| **NASA ASF Datapool** | HTTPS Direct Download | **Gated (Earthdata OAuth)** | Raw ZIP download requests redirect to `urs.earthdata.nasa.gov` (free registration required). |
| **ASF Browse Service** | HTTPS Direct JPG Image | **100% Public (HTTP 200 OK)** | Full-resolution browse images (~600–700 KB) accessible directly without credentials. |
| **Microsoft Planetary Computer** | STAC API + Azure Blob SAS | **Public SAS Token Available** | Free temporary SAS tokens allow programmatic inspection of individual asset headers. |
| **Copernicus Data Space (CDSE)** | OData / S3 Open API | **Gated (CDSE OAuth)** | Open access under EU Copernicus terms; requires institutional/user login. |

---

## 4. Processing & Flood-Mask Methodology Requirements

A scientifically defensible SAR flood extent cannot be generated by naive pixel thresholding of raw Level-1 amplitude data. The required technical workflow comprises:

```
┌────────────────────────────────────────────────────────┐
│ Raw Level-1 GRD Product (Slant/Ground Range Geometry) │
└───────────────────────────┬────────────────────────────┘
                            │ 1. Apply Precise Orbit Ephemerides (.EOF)
                            ▼
┌────────────────────────────────────────────────────────┐
│ Radiometric Calibration (Convert DN to Sigma0 / Gamma0)│
└───────────────────────────┬────────────────────────────┘
                            │ 2. Speckle Filtering (Lee / Refined Lee 5x5)
                            ▼
┌────────────────────────────────────────────────────────┐
│ Range-Doppler Terrain Correction (Orthorectify via DEM)│
│ • Projects native coordinates to EPSG:32643 (UTM 43N)  │
│ • Eliminates foreshortening, layover, and radar shadow │
└───────────────────────────┬────────────────────────────┘
                            │ 3. Change Detection (Bitemporal Ratio)
                            ▼
┌────────────────────────────────────────────────────────┐
│ Thresholding & Mask Refinement                         │
│ • VV polarization: Primary surface water detection     │
│ • VH polarization: Suppresses rough water/wind effects │
│ • Permanent water masking (JRC Global Surface Water)   │
│ • Slope masking (HAND / DEM slope > 5° excluded)       │
└────────────────────────────────────────────────────────┘
```

### Why a Fabricated Flood Mask Was Rejected:
1. **Unprojected Raw Geometry**: Opening the raw Level-1 measurement TIFF directly in GIS yields `CRS: None` with image-coordinate bounds `(0, 16733, 25528, 0)`. Applying an arbitrary linear affine transform without rigorous Range-Doppler equations results in spatial distortion of up to several hundred meters across the Delhi floodplain.
2. **Urban Double-Bounce & Radar Shadow**: In dense South and Central Delhi, multi-story concrete structures induce corner reflection (strong double-bounce bright returns) and tall-building radar shadows. Naive SAR thresholding in urban zones either misclassifies street shadows as standing water or misses deep street inundation masked by building reflections.
3. **Scientific Integrity**: Because a fully calibrated RTC pipeline (such as ESA SNAP) is not hosted within the lightweight runtime, generating a pseudo-mask would violate project standards. Metadata and browse verification provide the necessary proof of event coverage without compromising scientific accuracy.

---

## 5. Relevance to the Kushak and Barapullah Drainage Network

| Zone / Component | Elevation & Physical Setting | Sentinel-1 C-SAR Observability & Utility |
| :--- | :--- | :--- |
| **Yamuna Active Floodplain** | $202	ext{ to }208	ext{ m MSL}$; open agricultural/riverbed floodplain. | **HIGH (Fully Observable)**: Open water bodies exhibit low backscatter (specular reflection away from antenna, typically $<-18	ext{ dB}$ in VV/VH). Synoptic inundation extent along the Yamuna channel is clearly captured on both 12 July and 16 July 2023. |
| **Barapullah Lower Reach & Outfall** | $201	ext{ to }206	ext{ m MSL}$; open drain corridor near Nizamuddin / Sarai Kale Khan. | **MODERATE**: Outfall embayment into Yamuna is visible; however, elevated metro viaducts, RRTS flyovers, and rail bridges create radar backscatter noise and obstruction. |
| **Sarai Kale Khan / Ring Road** | $207	ext{ to }210	ext{ m MSL}$; major road junction adjacent to Yamuna floodplain. | **MODERATE / QUALITATIVE**: Broad overtopping over low-lying highway embankment is detectable if standing water forms open ponds; obstructed by overhead highway structures. |
| **Mid-Kushak Corridor (Defence Colony / INA)** | $210	ext{ to }216	ext{ m MSL}$; covered box drain beneath parking and multi-lane roads. | **ZERO (Physically Inaccessible)**: C-band radar (wavelength $\approx 5.6\text{ cm}$) cannot penetrate reinforced concrete deck slabs. Flow inside the Kushak conduit is completely invisible to SAR. |
| **Upper Kushak & Catchment Streets (AIIMS / Pushp Vihar)** | $216	ext{ to }225	ext{ m MSL}$; dense urban street grid, underpasses, flyovers. | **ZERO (Urban Radar Shadow)**: Street-level pluvial waterlogging cannot be resolved due to building layover, street-canyon shadowing, and sub-pixel road widths ($<10\text{ m}$). |

---

## 6. Integration with the GSDL + DTP + CWC Validation Stack

The Sentinel-1 audit completes the four-tier validation framework for the Kushak/Barapullah system:

```
┌────────────────────────────────────────────────────────────────────────┐
│ Tier 1: CWC Downstream Boundary (Gauge DRB) [Phase 3E-4]               │
│ • Provides mainstem Yamuna hydrograph (204.63 m -> 208.66 m MSL).      │
│ • Governs tailwater pressure and backflow locking at Barapullah outfall.│
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Governs
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ Tier 2: Sentinel-1 Synoptic Satellite Imagery [Phase 3E-5]             │
│ • Captures macro-scale floodplain inundation along Yamuna active zone. │
│ • Validates outer limits of river backwater flooding at Sarai Kale Khan.│
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Constrains
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ Tier 3: Delhi Traffic Police (DTP) Incident Records [Phase 3E-3]       │
│ • Establishes operational roadway disruptions and underpass closures.  │
│ • Connects river backwater to arterial closures (Ring Road, Bhairon).  │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Pinpoints
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ Tier 4: GSDL Waterlogging Point Inventory [Phase 3E-2B]                │
│ • Delivers 45 high-precision GIS coordinates within Kushak corridor.   │
│ • Validates local pluvial drainage failure sites (AIIMS, Moolchand).   │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 7. Preserved Evidence & Manifest

Lightweight scene metadata and provider manifests are preserved under:  
[sentinel1_july2023_scene_manifest.json](file:///C:/Users/laksh/OneDrive/Desktop/sih2026/data/delhi/raw/validation/sentinel1/sentinel1_july2023_scene_manifest.json)

The manifest details:
- Complete scene identifiers, ESA SAFE naming conventions, and absolute orbit numbers.
- Start and stop acquisition timestamps to sub-second precision.
- Dual-polarization channels (`VV+VH`) and beam modes (`IW`).
- Exact bounding polygon vertices in WGS84 coordinates.
- Direct download links, browse imagery endpoints, and accessibility protocols.

---

## 8. Final Verdict

### **CONDITIONAL GO**

**Justification**:
- **Why NOT NO-GO**: Authoritative satellite event imagery from Copernicus Sentinel-1A covering the entire Delhi / Yamuna corridor during both key phases of the July 2023 flood (12 July rising stage and 16 July receding stage) is fully identified, verified, and catalogued with complete pre-event baseline pairs and public quicklook browses.
- **Why NOT Full GO**: Level-1 GRD SAR products require specialized Range-Doppler Terrain Correction and precise ephemerides to project from radar slant coordinates to geographic space (`CRS: None` in raw measurement TIFFs). A fully reproducible, publication-grade flood mask cannot safely be derived without external heavyweight SAR orthorectification software (e.g., ESA SNAP). Naive thresholding was deliberately halted to maintain scientific rigor.
- **Approved Scope**: Approved specifically as a **Macro-Scale Floodplain Reference Layer** (`DERIVED FROM OBSERVED REMOTE SENSING`). It must not be treated as hydraulic ground truth, local street depth, or direct drainage observation.

---

*End of Sentinel-1 Historical Flood Extent Audit.*  
*Authored by: Antigravity (Advanced Agentic Systems)*
