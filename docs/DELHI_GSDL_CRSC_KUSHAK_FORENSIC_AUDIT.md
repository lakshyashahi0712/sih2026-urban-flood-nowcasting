# GSDL HYD CRSC Layer — Kushak Nallah Forensic Audit
## Evidence-Recovery Investigation Report

**Project**: Delhi/Kushak Urban Flood Nowcasting V2  
**Report Type**: Forensic Evidence-Recovery Audit (NOT hydraulic engineering)  
**Date**: 10 September 2026  
**Status**: FINAL  
**Constraint Notice**: No canonical GIS geometry, hydraulic code, 27.66 km2 catchment, or any project model was modified during this investigation.

---

## 1. Executive Summary

The GSDL HYD CRSC (Cross Section) layer was successfully accessed via public REST API. The layer contains **8,486 cross-section point features** covering Delhi NCT. After exhaustive spatial querying with correct UTM coordinate derivation for the Kushak Nallah corridor:

**ZERO CRSC points exist within the Kushak Nallah corridor bounding box or within 500m of the Kushak main spine.**

The 8,486 CRSC points are distributed along open rivers and major drains in central-south Delhi, with the closest observed cluster located approximately 4 km northeast of the Kushak corridor, along the Barapullah confluence zone near the Yamuna.

The layer's CSCL field (elevation in m MSL) represents cross-section levels at those distant features and has no relevance to Kushak hydraulic geometry.

---

## 2. Service Access and Layer Metadata

### 2.1 Access Status

| Item | Result |
|---|---|
| REST access attempted | SUCCESS — no HTTP 403 in this environment |
| Service URL | https://gsdl.org.in/arcgis/rest/services/GSDL_LAYERS_UPDATED/HYD/MapServer |
| CRSC Layer ID | 0 |
| CRSC Layer Name | CRSC |
| ArcGIS Server version | 10.91 |
| Authentication required | None — public (allowOthersToQuery: true) |

### 2.2 Layer Characteristics

| Attribute | Value |
|---|---|
| Geometry Type | esriGeometryPoint (2D, no Z stored in geometry) |
| Total Feature Count | **8,486** (FIDs 0–8485, confirmed by returnIdsOnly query) |
| Spatial Reference | EPSG:32643 — WGS 84 / UTM Zone 43N |
| maxRecordCount | 1,000 (server-side pagination limit) |
| supportsStatistics | false |
| supportsPagination | false |
| Capabilities | Map, Query, Data |
| Display Field | SENM |
| Layer Extent (UTM 43N) | xmin=713171.7, ymin=3155411.2, xmax=730528.6, ymax=3194609.9 |
| Layer Extent (approx WGS84) | lon 77.12–77.28°E, lat 28.35–28.70°N |

### 2.3 Field Catalog (Complete — 4 Fields)

| Field Name | Alias | Type | Length | Description / Interpretation |
|---|---|---|---|---|
| FID | FID | esriFieldTypeOID | — | System object identifier (auto-assigned) |
| Shape | Shape | esriFieldTypeGeometry | — | 2D point geometry in EPSG:32643 |
| SENM | SENM | esriFieldTypeString | 50 | Cross Section Name/Number. All observed values are sequential integers (SENM = FID+1 in all records sampled). No drain-name references. No domains or coded values. |
| CSCL | CSCL | esriFieldTypeString | 50 | Cross Section Level — elevation in metres MSL as a numeric string. Range observed: ~197–215 m MSL across Delhi coverage. One record observed with CSCL='0' (FID 6593). |

**No other fields exist. There are NO fields for:**
- Drain name or ID
- Chainage or stationing
- Offset from centreline
- Bed/invert level vs bank level distinction
- Survey date or method
- Datum reference
- Section ID or transect group

### 2.4 Domains and Coded Values

**No domains exist** on any field. All fields are free-text strings. No controlled vocabulary, no coded value domain, no relationship class.

---

## 3. Coordinate System Validation and UTM Bbox Derivation

**Critical finding**: The previously reported bbox `xmin=714000, ymin=3171000, xmax=723000, ymax=3180000` used in earlier investigations was an error that targeted a location approximately 9 km northeast of the Kushak corridor. This audit corrected the coordinates.

### 3.1 Kushak Corridor UTM 43N Coordinates (Derived)

| Location | Easting (m) | Northing (m) |
|---|---|---|
| Upstream anchor (Chanakyapuri, J_3178) | 713,789 | 3,165,036 |
| Africa Avenue midpoint | 714,714 | 3,164,255 |
| NDMC downstream terminus | 716,103 | 3,162,684 |
| Canonical corridor start | 716,338 | 3,162,688 |
| Barapullah confluence | 718,731 | 3,163,464 |

### 3.2 Kushak Corridor CRSC Query Bounding Box (500m buffer)

```
xmin = 713,289 E   ymin = 3,162,184 N
xmax = 719,231 E   ymax = 3,165,536 N
(EPSG:32643, WGS 84 / UTM Zone 43N)
```

---

## 4. Spatial Query Results

### 4.1 Query Sequence

| Query | Bbox (UTM 43N) | Count | Assessment |
|---|---|---|---|
| Exact Kushak corridor (500m buffer) | 713289–719231 E, 3162184–3165536 N | **0** | No CRSC in Kushak corridor |
| Wider Kushak catchment (2km buffer) | 711000–721000 E, 3159000–3168000 N | **187** | Points NOT on Kushak — see Section 4.2 |
| Incorrect earlier bbox (Barapullah river area) | 714000–723000 E, 3171000–3180000 N | 1,000 (capped) | Wrong area — Barapullah river mainstem |

### 4.2 The 187 Points in the Wider Search Area

The 187 CRSC features returned in the wider bbox cluster at:
- **Centroid latitude**: ~28.587–28.622°N
- **Centroid longitude**: ~77.252–77.261°E

This is the **Barapullah drain confluence zone near Sarai Kale Khan / Yamuna**, approximately 4 km northeast of the Kushak NDMC corridor. They are NOT on the Kushak Nallah alignment.

Sample CSCL values from these 187 features:
- Min observed: 197.337 m MSL (FID 6642)
- Max observed: 215.0 m MSL (approx, FID 6274 = 214.416)
- Typical values: 198–208 m MSL (Barapullah confluence area terrain)

### 4.3 Proximity Analysis — Kushak Main Spine

| Distance Threshold | CRSC Points Found |
|---|---|
| Within 0 m (on spine) | **0** |
| Within 10 m | **0** |
| Within 25 m | **0** |
| Within 50 m | **0** |
| Within 100 m | **0** |
| Within 200 m | **0** |
| Within 500 m | **0** |
| Closest known CRSC point | >3,500 m (Barapullah zone) |

**Result: ZERO CRSC points are associated with the Kushak Nallah corridor in any way.**

---

## 5. What the CRSC Layer Represents

### 5.1 Interpretation of CRSC Data (Delhi-wide)

Based on the spatial pattern, SENM/CSCL field structure, and the associated HYD service layers (FLBD_2011, FLBD_206, FLBD_207, FLBD_208, FLBD_209 — multiple flood boundary level polygons), the CRSC points most likely represent:

**Bed/bank elevation sample points along major open rivers and drains used for 1D hydraulic flood modelling (e.g., HEC-RAS) to define cross-section geometry.**

Evidence for this interpretation:
1. CSCL = "Cross Section Level" per GSDL V2 schema — an elevation value, not a transect ID
2. Points cluster in dense linear arrays (10–30 consecutive SENM values spaced ~100m apart) along drainage corridors
3. Co-located with FLBD (Flood Boundary Level) polygon layers — indicative of a completed 1D flood inundation study
4. The Barapullah confluence zone is a known area for CWPRS/IIT Delhi HEC-RAS flood studies
5. 8,486 points for all major drains across ~576 km2 Delhi coverage = plausible density for a systematic cross-section survey

### 5.2 What CRSC Points Are NOT

- They are NOT Kushak Nallah cross-sections (none found on Kushak)
- They are NOT named with drain names in the SENM field (SENM is a numeric sequence only)
- They do NOT represent transect profiles (each CRSC is a single point, not a multi-point transect)
- They do NOT have offset or chainage references
- They do NOT have bed vs bank vs top-of-bank attribute differentiation

---

## 6. Provenance Assessment

### 6.1 Survey Origin

| Attribute | Status |
|---|---|
| Survey method documented | UNKNOWN — no metadata in REST service |
| Survey date documented | UNKNOWN |
| Surveying agency documented | UNKNOWN |
| GTS benchmark reference | UNKNOWN |
| Vertical datum certification | UNKNOWN |
| Independent verification | Not possible from available data |

### 6.2 Classification

All CRSC values are classified: **UNKNOWN provenance**.

The CSCL values cannot be assigned even a `SECONDARY` classification without independent confirmation of survey methodology. They are plausible numerically but have no certified provenance.

### 6.3 A CSCL Elevation Value Does NOT Prove Surveyed Origin

Per the project evidence rule: *"a CRSC point having an elevation does NOT by itself prove it is a surveyed hydraulic cross-section. Provenance must be established independently."*

The CSCL values in the Barapullah confluence zone (~197–215 m MSL) are consistent with DEM-derived elevations from SRTM or GLO-30 for that area. They could equally be:
- Field-surveyed total-station measurements
- GPS RTK survey elevations
- DEM-derived samples at regular intervals
- Interpolated from existing surveys

Without survey records, there is no basis to assign a higher provenance class.

---

## 7. Transect and Perpendicularity Analysis

### 7.1 Transect Structure Assessment

Since ZERO CRSC points exist within the Kushak corridor, no perpendicularity analysis of Kushak cross-sections was possible.

For the 187 Barapullah zone points (which are NOT Kushak), a structural observation:
- Dense linear clusters of consecutive SENM values are observed running roughly E-W or perpendicular to the Barapullah channel alignment
- Points in a given run are spaced approximately 100–200 m apart
- This spatial pattern is consistent with systematic cross-section survey transects perpendicular to the drain alignment

However, these observations apply only to the **Barapullah confluence zone** and have no bearing on Kushak.

### 7.2 Kushak Transect Status

| Check | Result |
|---|---|
| CRSC points crossing Kushak centreline | 0 |
| Perpendicular transects detected | 0 |
| Candidate cross-sections grouped | 0 |
| Hydraulic geometry recoverable | NOT APPLICABLE — no points |

---

## 8. Comparison with GSDL Layer 7 (Kushak Box Drain Spine)

| Metric | GSDL Layer 7 (Kushak Storm Drain) | GSDL HYD CRSC |
|---|---|---|
| Geometry type | Polyline (conduit segments) | Point |
| Kushak coverage | YES — 81 box drain segments, 4.927 km | NO — zero Kushak points |
| Attribute content | Drain width, depth, inverts, agency, topology | Elevation level only (SENM=ID, CSCL=elevation) |
| Provenance | OFFICIAL / MODEL INPUT (NDMC administrative records) | UNKNOWN |
| Useful for hydraulic modelling | Planimetric only; dimensions unreliable; datum unvalidated | Not applicable to Kushak |

---

## 9. Data Files Produced

### Raw Data
| File | Description |
|---|---|
| data/delhi/raw/gsdl/crsc_layer_metadata.json | Full CRSC layer metadata (service, fields, extent) |
| data/delhi/raw/gsdl/crsc_all_objectids.json | All 8,486 object IDs (from returnIdsOnly query) |
| data/delhi/raw/gsdl/crsc_kushak_bbox_raw.geojson | 1,000 features from incorrect earlier bbox (Barapullah river — NOT Kushak) |
| data/delhi/raw/gsdl/crsc_kushak_corridor_raw.geojson | 0 features from correct Kushak corridor bbox (confirmed empty) |

### Derived Analysis
| File | Description |
|---|---|
| data/delhi/derived/hydraulic/gsdl_crsc_audit/crsc_kushak_spatial_analysis.json | Spatial query log with all bbox attempts and results |
| data/delhi/derived/hydraulic/gsdl_crsc_audit/crsc_senm_cscl_analysis.json | SENM/CSCL field analysis and interpretation |
| data/delhi/derived/hydraulic/gsdl_crsc_audit/crsc_provenance_analysis.json | Provenance classification and evidence basis |

---

## 10. Investigation Methodology

### 10.1 Queries Executed (all via public REST API, no authentication bypass)

1. `GET .../GSDL_LAYERS_UPDATED/HYD/MapServer?f=json` — service metadata
2. `GET .../HYD/MapServer/layers?f=json` — all layer definitions  
3. `GET .../MapServer/0/query?where=1=1&returnIdsOnly=true` — feature count (confirmed 8,486)
4. `GET .../MapServer/0/query?geometry=[kushak_bbox]&returnCountOnly=true` — correct Kushak bbox count (result: 0)
5. `GET .../MapServer/0/query?geometry=[kushak_bbox]&outFields=*&returnGeometry=true` — correct Kushak bbox features (result: empty FeatureCollection)
6. `GET .../MapServer/0/query?geometry=[wider_bbox]&returnCountOnly=true` — wider area count (result: 187)
7. `GET .../MapServer/0/query?geometry=[wider_bbox]&outFields=*&returnGeometry=true` — wider area features (returned, analyzed)
8. `GET .../MapServer/0/query?geometry=[incorrect_earlier_bbox]&outFields=*` — earlier bbox (1,000 features — confirmed as Barapullah zone, not Kushak)

### 10.2 Important Error Documented

The previous GSDL investigation had recommended querying CRSC with a bbox that was approximately **9 km northeast** of the actual Kushak corridor. This audit identified and corrected this error. The correct Kushak corridor UTM 43N coordinates were computed from known WGS84 reference points (NDMC node J_3178, NDMC downstream terminus, Barapullah confluence) using a validated WGS84→UTM43N projection formula.

---

## 11. Final Verdict

| Assessment Item | Result |
|---|---|
| **CRSC Kushak coverage** | **NO** — zero CRSC points in Kushak Nallah corridor |
| **Actual cross-sections recovered** | **0** |
| **Survey provenance** | **UNKNOWN** |
| **Hydraulic geometry recoverable** | **NO** |
| **Vertical datum** | **UNKNOWN** (no datum metadata in GSDL REST service) |
| **Safe for hydraulic modelling** | **NO** — zero coverage of Kushak, unknown provenance for other features |
| **FINAL VERDICT** | **NO-GO** |

---

## 12. Implications for Project

1. **The GSDL CRSC layer is definitively exhausted as a Kushak cross-section source.** It contains zero coverage of the Kushak corridor. No further CRSC queries for Kushak are warranted.

2. **The project remains without validated hydraulic cross-section data for Kushak Nallah.** All four major candidate sources (IITD DMP 2018, GSDL Layer 7, GSDL HYD CRSC, Jalsuraksha portal) have now been investigated and found to provide NO usable Kushak cross-section geometry.

3. **The GSDL CRSC layer does cover Barapullah confluence zone.** If the project scope were to expand to the full Barapullah system (not Kushak specifically), the CRSC layer would be worth further investigation for those reaches — but provenance must still be established before hydraulic use.

4. **Kushak cross-section data can only be obtained through:**
   - RTI application to NDMC Engineering Dept (engineering drawings)
   - RTI application to I&FC Delhi (IITD DMP model files)
   - Independent field survey (total station / GPS levelling)
   - NGT OA compliance submissions (may contain court-directed measurements)

---

## 13. Recommended Next Steps

### Immediate
No further GSDL REST queries for Kushak CRSC are warranted. The CRSC evidence track for Kushak is **closed** with verdict: NO-GO.

### Future Evidence Recovery
The priority actions listed in `DELHI_PROJECT_EVIDENCE_SUMMARY.md` remain valid:

1. RTI to NDMC Engineering Department for Kushak box culvert engineering drawings
2. RTI to I&FC Delhi for IITD DMP Barapullah sub-model input files
3. Direct contact with IIT Delhi Jalsuraksha team
4. Check NGT OA 300/2013 compliance reports for court-directed survey data

---

*End of Forensic Audit Report.*  
*No canonical GIS geometry, hydraulic code, or project model was modified during this investigation.*  
*All queries were performed via publicly accessible REST endpoints without authentication bypass.*
