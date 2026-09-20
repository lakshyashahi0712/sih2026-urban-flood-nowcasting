# Delhi / Kushak Urban Flood Nowcasting V2
# Consolidated Evidence & Findings Summary

**Project**: Delhi/Kushak Urban Flood Nowcasting — Operational-Quality Build  
**Status**: ACTIVE RESEARCH / INVESTIGATION PHASE  
**Prepared**: September 2026  
**Constraint Notice**: This is a forensic evidence-recovery document only. No hydraulic code, no canonical GIS geometry, no 27.66 km² catchment was modified in generating this document.

---

> [!IMPORTANT]
> **Scientific Integrity Mandate**: All values in this document are labelled with their evidence classification. Never use ASSUMED or INTERPOLATED values as if they were OFFICIAL / DIRECT SURVEY values. Where evidence is missing, that absence is explicitly recorded — not silently filled.

---

## PART A — EVIDENCE CLASSIFICATION SYSTEM

| Class | Meaning |
|---|---|
| `OFFICIAL / DIRECT SURVEY` | Independent field measurement with instrument certificate and benchmark tie |
| `OFFICIAL / DESIGN` | Published in official government report as a design parameter |
| `OFFICIAL / MODEL INPUT` | Used in an official hydraulic model (may have been processed, corrected, interpolated) |
| `OFFICIAL / MODEL INPUT (SHELVED)` | Above, but the model/report was rejected by a government TEC |
| `HISTORICAL` | From a historical plan; may describe demolished or encroached infrastructure |
| `DERIVED` | Calculated from other evidence (e.g., GIS measurement of a mapped feature) |
| `INTERPOLATED` | Gap-filled between known values |
| `ENGINEERING ASSUMPTION` | Standard engineering value used in the absence of survey data |
| `SECONDARY` | From a non-primary source (newspaper, court summary, secondary report) |
| `UNKNOWN` | Provenance cannot be established |
| `FABRICATED (RETRACTED)` | Previously reported value that has been confirmed as an error or invention |

---

## PART B — CANONICAL PROJECT GIS STATE

### B1. Kushak Corridor (Canonical — DO NOT MODIFY)

| Parameter | Value | Classification | Source |
|---|---|---|---|
| Mapped connected Kushak corridor length | **~5.028 km** | DERIVED | OSM-traced polyline, project baseline |
| Corridor start (upstream) | Chanakyapuri / Africa Avenue area | DERIVED | OSM + GSDL planimetric |
| Corridor end (downstream) | Barapullah confluence zone, ~28.5797°N 77.2364°E | DERIVED | OSM + project GIS |
| Canonical corridor CRS | WGS84 (EPSG:4326) | DERIVED | Project GIS standard |

### B2. Working Catchment (Provisional — DO NOT MODIFY)

| Parameter | Value | Classification | Source |
|---|---|---|---|
| Working Kushak catchment area | **~27.66 km²** | DERIVED | Copernicus GLO-30 DEM delineation, provisional |
| DEM source | Copernicus GLO-30 (30 m resolution) | OFFICIAL / DESIGN | ESA Copernicus |
| Historical CGWB Kushak catchment (Western Spine only) | **3.5 km²** | OFFICIAL / EMPIRICAL | CGWB 2011, p. 42-43 |
| Note | The 3.5 km² applies to the upper NDMC Kushak Nala only; the modern 27.66 km² is the full DEM-derived watershed | — | — |

---

## PART C — HISTORICAL NETWORK RECONCILIATION

### C1. The Dual-Spine Discovery (Critical Forensic Finding)

The historical "~11 km Kushak system" refers to **two entirely different drains**, each ~11 km long, both of which have been called "Kushak" in official documents:

**Western / Central Ridge Spine** (the TRUE historical Kushak):
- Origin: Birla Mandir / Mandir Marg (~245 m MSL), Central Ridge quartzite
- Named after: Kushak Mahal, 1354 AD hunting lodge of Sultan Firoz Shah Tughlaq (Teen Murti Complex)
- Route: West of Rashtrapati Bhawan → Chanakyapuri → Nehru Park → Africa Avenue (covered) → Safdarjung Hospital → AIIMS → INA Market → DTC Kushak Bus Depot → Barapullah confluence
- Length: ~11.0 to 11.4 km total; 4.7 km covered (NDMC 2007)
- CGWB (2011) effective catchment: 3.5 km²
- Evidence class: `OFFICIAL PLANNING INVENTORY` (NDMC 2007) + `OFFICIAL / EMPIRICAL` (CGWB 2011)

**Southern South Delhi Spine** (the NGT-designated "Kushak drainage system"):
- Origin: Southern Ridge beyond Mehrauli-Badarpur Road (~260 m MSL)
- Route: Saket → Pushp Vihar → Khidki Village → Sheikh Sarai → Chirag Delhi → Panchsheel Enclave → Siri Fort → Greater Kailash-I → Andrews Ganj → Defence Colony → JLN Stadium → Jangpura → Barapullah opposite Nizamuddin
- Length: "some 11 kms" (NGT 2015, Para 10)
- Municipal names: Chirag Delhi Drain / Andrews Ganj Drain / Defence Colony Drain
- Evidence class: `OFFICIAL` (NGT judgment 2015, OA No. 300/2013)

**Both spines converge at the same confluence near JLN Stadium / Defence Colony West, forming Barapullah Nallah.**

### C2. Source-by-Source Evidence Summary

| Document | Year | Class | Key Kushak Fact |
|---|---|---|---|
| NDMC Sub-city Development Plan | 2007 | OFFICIAL / DESIGN | Kushak = 11 km, 4.7 km covered; originates Central Ridge |
| CGWB Artificial Recharge Report | 2011 | OFFICIAL / EMPIRICAL | Kushak catchment = 3.5 km²; origin at Birla Mandir west of Rashtrapati Bhawan |
| NGT Judgment OA 6/2012 + 300/2013 | 2015 | OFFICIAL | Southern Kushak system ~11 km; Defence Colony / JLN Stadium alignment |
| IIT Delhi Drainage Master Plan | 2018 | OFFICIAL / MODEL INPUT (SHELVED) | Barapullah basin = 376.27 km²; Kushak as tributary; data quality severely compromised |
| 1976 MPD Drain Inventory | 1976 | HISTORICAL | 201 total Delhi drains; 44 untraceable; Barapullah basin = 44 drains |

### C3. 1976 MPD Inventory Reconciliation Findings

From the two PDFs (201 drains + 44 untraceable drains):
- Barapullah basin: 44 named drains (1976 classification)
- Kushak Nallah is among these 44 Barapullah tributaries
- Many 1976 drain alignments no longer exist due to urbanization, encroachment, and culverting
- The 44 "untraceable" drains represent infrastructure that was likely built over or absorbed into storm sewer networks
- Classification of 1976 data: `HISTORICAL` — not transferable to current GIS without independent field verification

---

## PART D — GSDL FORENSIC AUDIT FINDINGS

### D1. GSDL Architecture (Confirmed)

| Parameter | Value |
|---|---|
| ArcGIS Server | gsdl.org.in/arcgis/rest/services/ |
| Kushak storm drain layer | DIFC/storm_drain_08082024/MapServer, Layer 7 (NDMC) + Layer 6 (SDMC) |
| Spatial Reference | EPSG:32643 (WGS 84 UTM Zone 43N) |
| GSDL Feature List Version | Version 2.0, dated 7 February 2025 |
| Storm drain feature class | IRRIGATION CHANNEL (IRCH) — no standalone DRAIN feature class in GSDL V2 |

### D2. NDMC Kushak Records (Layer 7, 157 records)

| Attribute | Finding | Classification |
|---|---|---|
| Total Kushak records | 157 (name = 'KushakNallah') | OFFICIAL |
| Network partition | 81 Box Drain segments + 76 Circular sewer segments — two physically distinct systems | OFFICIAL |
| Box drain main spine length | **4,926.989 m** (sum of Drn_Length) = **4.927 km** | OFFICIAL / DERIVED |
| Geodesic verification | 4,926.146 m (delta -0.84 m, 0.017% — UTM scale factor only) | DERIVED |
| Drn_Wd_m = 25.0 m | Administrative/ROW width; NOT hydraulic clear width | ENGINEERING ASSUMPTION |
| Drn_Dp_m = 7.354 m | Administrative/design template depth; repeated identically across 77 segments | ENGINEERING ASSUMPTION |
| Circular sewers | Dia = 0.45 m (450 mm); Chanakyapuri roadside sewer network | OFFICIAL |
| Invert head (upstream terminus) | ~216.906 m MSL, Node J_3178, Chanakyapuri | OFFICIAL / MODEL INPUT |
| Invert downstream terminus | ~203.770 m MSL, FID 6092 | OFFICIAL / MODEL INPUT |
| Total invert fall (NDMC) | 13.136 m over 4.927 km, avg slope S₀ = 0.00267 | DERIVED |
| Adverse rises in invert profile | 2 adverse rises identified; 1 abrupt 1.2 m drop | OFFICIAL / MODEL INPUT |
| Topology | 5 disconnected components; 6 source nodes; 8 terminal nodes | DERIVED |
| Blank node IDs | FIDs 6089, 6092, 6093, 6094 have no node ID | OFFICIAL |
| RDLvl_MSL field | 100% zero — road level NOT populated | OFFICIAL (null data) |

### D3. SDMC Kushak Records (Layer 6, 21 records)

| Attribute | Finding | Classification |
|---|---|---|
| SDMC Kushak records | 21 (name = 'Khushak Nallah', note H in spelling) | OFFICIAL |
| Bridging segment (NDMC/SDMC gap) | FID 461; L = 229.52 m; W = 25.0 m; D = 7.354 m; IL = 203.77 m | OFFICIAL |
| This segment resolves the apparent 233 m spatial gap | The gap is jurisdictional boundary, not a physical gap | DERIVED |
| CRITICAL: Vertical datum jump | SDMC FID 435 (immediately downstream of bridging segment) records IL = 210.010 m — a +6.24 m jump from NDMC terminus 203.770 m | OFFICIAL (anomaly) |

### D4. Vertical Datum Issue (BLOCKING for Hydraulic Modeling)

**The +6.24 m vertical discontinuity at the NDMC/SDMC boundary is the single most critical data quality issue discovered.**

- NDMC invert at downstream terminus: **203.770 m MSL**
- SDMC invert immediately downstream: **210.010 m MSL**
- This physically implies water flowing 6.24 m uphill — physically impossible
- Root cause: NDMC and SDMC used incompatible vertical datum baselines
- Resolution required: GTS benchmark survey at the junction point

**Status: UNRESOLVED. Cannot merge NDMC and SDMC invert data until datum reconciliation is performed.**

### D5. Planimetric Alignment Comparison (GSDL vs Project Corridor)

| Metric | Value |
|---|---|
| Sample points compared | 10 GSDL centroids vs project extended_alignment |
| Mean lateral distance | 16.87 m |
| Maximum lateral distance | 26.07 m |
| Assessment | Good planimetric agreement for a covered culvert corridor; within expected accuracy for remotely digitized infrastructure |
| Classification | SECONDARY reference; acceptable for corridor routing confirmation |

### D6. Files Produced by GSDL Audit

| File | Description |
|---|---|
| data/delhi/raw/gsdl/kushak_ndmc_gsdl_extracted.geojson | 157 Kushak NDMC features, WGS84 |
| data/delhi/raw/gsdl/kushak_ndmc_raw_esri_32643.json | Native ESRI JSON, EPSG:32643 |
| data/delhi/raw/gsdl/manifest.json | Provenance manifest with extraction timestamp |
| data/delhi/derived/hydraulic/gsdl_audit/kushak_gsdl_attribute_statistics.csv | Field-level statistics |
| data/delhi/derived/hydraulic/gsdl_audit/kushak_gsdl_invert_profile.csv | 81 segments ordered with slope classification |
| data/delhi/derived/hydraulic/gsdl_audit/kushak_gsdl_topology.csv | Node/conduit connectivity |
| data/delhi/derived/hydraulic/gsdl_audit/kushak_gsdl_gap_analysis.geojson | Gap and jurisdiction boundary analysis |
| data/delhi/derived/hydraulic/gsdl_audit/kushak_gsdl_alignment_comparison.geojson | GSDL vs project alignment overlay |

---

## PART E — IIT DELHI 2018 DRAINAGE MASTER PLAN FINDINGS

### E1. Report Status

| Item | Detail |
|---|---|
| Full title | "Drainage Master Plan for NCT of Delhi", Final Report, July 2018 |
| Prepared by | Department of Civil Engineering, IIT Delhi |
| Prepared for | Department of Irrigation & Flood Control, Govt. of Delhi |
| Model used | SWMM (Storm Water Management Model / PCSWMM) |
| **Current official status** | **SHELVED — August 2021** by Delhi Govt. Technical Expert Committee (TEC) |
| TEC findings | "Discrepancies in data"; mathematical model "too complicated to use" operationally |
| Replacement | Delhi Govt. designated PWD as nodal agency for new master plan; IITD report used as base reference only |

### E2. Data Quality Admissions (from the DMP itself)

> *"Pre-requisite for a reliable analysis... is the availability of an equally reliable data on the infrastructure in terms of cross-sections and invert levels of the drains... the data on the existing infrastructure was not captured despite indulging in a gigantic exercise to digitize the whole Delhi."*

| Data Issue | Scale | Classification |
|---|---|---|
| Conduit dimensions missing | 3,021 / 18,007 conduits in Barapullah (16.8%) — filled by average of adjacent conduits | INTERPOLATED |
| Adverse slopes | 4,401 / 16,977 conduits (25.9%) — corrected to natural gradient | OFFICIAL / DERIVED |
| Invert levels partially missing | Computed by linear interpolation | INTERPOLATED |
| Invert levels abruptly fluctuating | Smoothed using nearest-neighbour approach | OFFICIAL / DERIVED |
| Diversions/gates/weirs/culverts | Excluded from model due to no data | UNKNOWN (excluded) |
| Sewers crossing storm drains | Excluded from model due to no data | UNKNOWN (excluded) |

### E3. KP-01 to KP-25 Cross-Section Designation — RETRACTED

**This designation DOES NOT EXIST.**

It was introduced erroneously in a prior investigation report (GSDL Hydrography Investigation). There is no "KP-xx" Kushak cross-section numbering series in:
- The IITD DMP Final Report
- Any NGT judgment text
- Any GSDL attribute field or domain
- Any publicly accessible engineering database

**All references to "KP-01 to KP-25" in prior project documents are FABRICATED (RETRACTED) and must be treated as null.**

### E4. Jalsuraksha Portal (jalsuraksha.iitd.ac.in)

| Item | Finding |
|---|---|
| Portal purpose | Real-time urban flood warning system for Barapullah basin |
| Technology | jQuery + D3.v4 + Leaflet 1.4.0 — JavaScript-rendered display dashboard |
| Downloadable GIS data | NONE found in static HTML |
| Cross-section / model files | NOT publicly accessible |
| Status | Display dashboard only; underlying SWMM model files are internal to IIT Delhi research |

### E5. IITD DMP Engineering Parameters (Usable as OFFICIAL / DESIGN)

| Parameter | Value | Classification |
|---|---|---|
| Barapullah basin total catchment area | 376.27 km² | OFFICIAL / DESIGN |
| Manning's n, RCC Box Drain | 0.012 | OFFICIAL / DESIGN |
| Manning's n, Circular Drain | 0.013 | OFFICIAL / DESIGN |
| Manning's n, Irregular Open Drain | 0.025 | OFFICIAL / DESIGN |
| Horton infiltration, Loam (HSG D) f_inf | 0.635 mm/hr | OFFICIAL / DESIGN |
| Horton infiltration, Loam (HSG D) f_0 | 76.2 mm/hr | OFFICIAL / DESIGN |
| Horton infiltration decay constant kd | 4.0 /hr | OFFICIAL / DESIGN |
| Safdarjung IDF (2-yr, 15-min intensity) | 87.205 mm/hr | OFFICIAL / DESIGN |
| Safdarjung IDF (5-yr, 15-min intensity) | 112.22 mm/hr | OFFICIAL / DESIGN |
| NDMC storm runoff system total length | 335.29 km | OFFICIAL / DESIGN |
| SDMC storm runoff system total length | 258.78 km | OFFICIAL / DESIGN |

---

## PART F — GSDL FEATURE LIST V2 HYDROGRAPHY SCHEMA

The official GSDL Hydrography layer catalogue (Version 2.0, 7 February 2025) contains:

| Feature Code | Feature Name | Relevance |
|---|---|---|
| WABD | Water Body | Rivers, water bodies |
| GHAT | Ghat | River ghats |
| EMBK | Embankment | Flood embankments |
| IRCH | Irrigation Channel | **Storm drains catalogued here** — includes all storm drain attributes |
| RIBK | River Bank | River bank delineation |
| CRSC | Cross Section | 8,486 cross-section points in GSDL_LAYERS_UPDATED/HYD |
| FLBD | Flood Boundary Level | Flood extent markers |

**Key finding**: There is NO standalone "DRAIN" or "STORM_DRAIN" feature class in GSDL V2. Storm drains are registered under the IRCH (Irrigation Channel) feature with storm-drain-specific attributes.

**CRSC Layer**: 8,486 cross-section points exist in GSDL_LAYERS_UPDATED/HYD/MapServer. These have not yet been audited for Kushak coverage. This is a HIGH-VALUE next investigation target.

---

## PART G — WHAT WE KNOW vs WHAT WE DO NOT KNOW

### G1. What IS known with evidence

| Fact | Evidence Class | Source |
|---|---|---|
| Kushak Nallah is the primary NDMC tributary to Barapullah | OFFICIAL | NDMC 2007, NGT 2015, IITD 2018 |
| The NDMC Kushak box drain is approximately 4.927 km long | OFFICIAL / DERIVED | GSDL audit |
| The drain type is a covered RCC/brick box drain in the NDMC section | OFFICIAL | GSDL Drn_type field |
| Upstream invert approx. 216.9 m MSL (Chanakyapuri) | OFFICIAL / MODEL INPUT | GSDL; datum UNVALIDATED |
| Downstream invert approx. 203.77 m MSL (NDMC terminus) | OFFICIAL / MODEL INPUT | GSDL; datum UNVALIDATED |
| Average invert slope approx. 0.00267 (2.67 m per km) | DERIVED | GSDL audit computation |
| Barapullah basin total catchment = 376.27 km² | OFFICIAL / DESIGN | IITD DMP 2018 |
| Manning's n for RCC Box Drain = 0.012 | OFFICIAL / DESIGN | IITD DMP Table 4.1-3 |
| NDMC and SDMC used incompatible vertical datums | DERIVED (anomaly confirmed) | GSDL audit |
| The ~11 km "Kushak system" refers to two different drains | DERIVED (forensic reconciliation) | Multi-source synthesis |
| Kushak upper catchment (CGWB) = 3.5 km² | OFFICIAL / EMPIRICAL | CGWB 2011, p. 42-43 |

### G2. What is UNKNOWN or MISSING (Critical Gaps)

| Missing Data Item | Impact on Project | Required Action |
|---|---|---|
| Hydraulic clear width and depth (surveyed) | Cannot compute Manning's capacity without true cross-section | RTI to NDMC Engineering / field survey |
| GTS-benchmarked invert levels | Cannot compute HGL or water surface profiles | GTS benchmark survey at junction |
| NDMC/SDMC vertical datum reconciliation | +6.24 m error blocks any merged hydraulic model | Benchmark survey |
| Kushak roughness by condition (Manning's n measured) | Design value 0.012 assumed; actual may differ | Field inspection |
| Kushak box drain structural details (cell count, wall thickness) | Affects hydraulic capacity calculation | NDMC engineering drawings |
| IITD DMP raw SWMM input files (Kushak sub-model) | Could provide processed network topology | RTI to I&FC Delhi |
| GSDL CRSC cross-section layer coverage for Kushak | 8,486 points exist; Kushak coverage unknown | Query GSDL CRSC layer |
| Current encroachment / blockage inventory | Affects effective cross-section | Field survey |
| Kushak confluence geometry with Barapullah | Affects backwater and confluence head loss | Survey / engineering drawings |

---

## PART H — INVESTIGATION AUDIT TRAIL

### H1. Investigations Completed

| # | Investigation | Report File | Status |
|---|---|---|---|
| 1 | Historical Network Reconciliation (5-source) | DELHI_KUSHAK_HISTORICAL_NETWORK_RECONCILIATION.md | COMPLETE |
| 2 | 1976 MPD Drain Inventory (201 + 44 drains) | DELHI_KUSHAK_1976_DRAIN_INVENTORY_RECONCILIATION.md | COMPLETE |
| 3 | GSDL Hydrography Layer Survey (Level 1) | DELHI_GSDL_HYDROGRAPHY_INVESTIGATION.md | COMPLETE |
| 4 | GSDL Kushak Forensic Audit (Level 2) | DELHI_GSDL_KUSHAK_FORENSIC_AUDIT.md | COMPLETE |
| 5 | IITD DMP 2018 Cross-Section Investigation | DELHI_IITD_2018_KUSHAK_CROSS_SECTION_INVESTIGATION.md | COMPLETE |
| 6 | Data Provenance Matrix | DATA_PROVENANCE_MATRIX.md | COMPLETE |
| 7 | Hydraulic Geometry Evidence Gate | DELHI_KUSHAK_HYDRAULIC_GEOMETRY.md | COMPLETE |
| 8 | Catchment/Drainage Evidence Gate | DELHI_CATCHMENT_DRAINAGE_EVIDENCE_GATE.md | COMPLETE |
| 9 | Hydrologic Delineation | DELHI_KUSHAK_HYDROLOGIC_DELINEATION.md | COMPLETE |
| 10 | Rainfall/Runoff Investigation | DELHI_KUSHAK_RAINFALL_RUNOFF.md + DELHI_KUSHAK_RAINFALL_EVENT_EVIDENCE.md | COMPLETE |
| 11 | GSDL CRSC cross-section layer audit | Not started | **PENDING** |
| 12 | Datum reconciliation (NDMC/SDMC boundary) | Not started | **PENDING** |

### H2. Investigation Verdicts Summary

| Investigation | Verdict | Key Output |
|---|---|---|
| GSDL as hydraulic cross-section source | **NO-GO** | 25m × 7.354m = administrative template; not hydraulic clear dimensions |
| GSDL as planimetric alignment reference | **CONDITIONAL GO** | ±26 m accuracy; use as SECONDARY reference only |
| GSDL invert profile for hydraulic slope | **CONDITIONAL GO** | Slope direction and order-of-magnitude valid; absolute datum UNVALIDATED |
| IITD DMP as Kushak cross-section source | **NO-GO** | No public data; DMP shelved; underlying data confirmed unreliable |
| IITD Manning's n values | **CONDITIONAL GO** | Standard engineering values; use as OFFICIAL / DESIGN assumption |
| KP-01 to KP-25 designation | **NO-GO (RETRACTED)** | Does not exist; was an error in prior report |

---

## PART I — RECOMMENDED NEXT ACTIONS (PRIORITIZED)

### Priority 1 — Highest Value, Actionable Now

1. **Query GSDL CRSC layer** (8,486 cross-section points): Filter for Kushak corridor bounding box. These are the only known official cross-section point dataset in GSDL and have not yet been analysed for Kushak coverage.
   - Endpoint: gsdl.org.in/arcgis/rest/services/GSDL_LAYERS_UPDATED/HYD/MapServer (Layer 8, CRSC = 8,486 pts)
   - Spatial query: bbox ~[28.565°N, 77.185°E] to [28.595°N, 77.240°E]

2. **RTI Application to NDMC Engineering Department**: Request engineering drawings for Kushak Nallah box culvert, particularly the Chanakyapuri to INA Market section.

3. **RTI Application to I&FC Delhi**: Request the Barapullah sub-model input files from the IITD DMP project.

### Priority 2 — High Value, Requires Access

4. **GTS Benchmark Survey** at the NDMC/SDMC administrative boundary (~77.21176°E, 28.57312°N) to resolve the +6.24 m vertical datum discontinuity.

5. **Contact IIT Delhi Jalsuraksha team** (Prof. Subhankar Karmakar group, Dept. Civil Engineering) about research data-sharing for Kushak network.

6. **Check NGT OA compliance reports**: Court-directed compliance submissions by NDMC/SDMC may contain measured cross-sections and invert data not in public domain.

### Priority 3 — Future Evidence Recovery

7. **Access NDMC Drainage Master Plan (post-2021)**: Delhi Govt. directed PWD to develop a new plan after shelving IITD DMP; check for any published outputs.

8. **Delhi Jal Board (DJB) sewer records**: The Kushak corridor has documented sewer/storm sewer confluence issues — DJB records may have cross-section data at confluence points.

---

## PART J — DATA FILES INVENTORY

| Path | Description | Format |
|---|---|---|
| data/delhi/raw/gsdl/kushak_ndmc_gsdl_extracted.geojson | 157 NDMC Kushak features, WGS84 | GeoJSON |
| data/delhi/raw/gsdl/kushak_ndmc_raw_esri_32643.json | Native ESRI JSON, UTM Zone 43N | JSON |
| data/delhi/raw/gsdl/manifest.json | GSDL extraction provenance | JSON |
| data/delhi/raw/hydraulic/iitd_dmp_2018_barapullah_kushak_extract.txt | Key IITD DMP extracts (39 lines) | TXT |
| data/delhi/derived/hydraulic/gsdl_audit/kushak_gsdl_attribute_statistics.csv | Field statistics for 157 records | CSV |
| data/delhi/derived/hydraulic/gsdl_audit/kushak_gsdl_invert_profile.csv | 81 box drain segments, ordered, slope class | CSV |
| data/delhi/derived/hydraulic/gsdl_audit/kushak_gsdl_topology.csv | Node/conduit connectivity table | CSV |
| data/delhi/derived/hydraulic/gsdl_audit/kushak_gsdl_gap_analysis.geojson | Gap and jurisdiction boundary analysis | GeoJSON |
| data/delhi/derived/hydraulic/gsdl_audit/kushak_gsdl_alignment_comparison.geojson | GSDL vs project corridor overlay | GeoJSON |
| data/delhi/derived/hydraulic/gsdl_audit/audit_manifest.json | Audit provenance | JSON |

---

*End of Consolidated Evidence & Findings Summary.*  
*No canonical GIS geometry, hydraulic code, or project catchment was modified in preparing this document.*  
*All fabricated values previously introduced (KP-01 to KP-25) have been formally retracted.*
