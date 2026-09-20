# IIT Delhi 2018 Drainage Master Plan — Kushak Nallah Cross-Section Investigation
## Forensic Evidence Report

**Project**: Delhi/Kushak Urban Flood Nowcasting V2  
**Report Type**: Evidence-Recovery Investigation (NOT hydraulic engineering)  
**Prepared**: September 2026  
**Status**: FINAL — NO-GO for hydraulic cross-section data; CONDITIONAL GO for planimetric reference  
**Constraint**: No GIS geometry, hydraulic code, or canonical network was modified during this investigation.

---

## 1. Objective

Determine whether the IIT Delhi 2018 Drainage Master Plan for NCT of Delhi contains usable, independently surveyed cross-section data for Kushak Nallah — specifically:

- Field-surveyed hydraulic clear dimensions (width, depth, invert levels)
- Chainage-referenced cross-section profiles (any "KP-xx" or equivalent designation)
- GTS-benchmarked absolute invert levels for Kushak
- Any downloadable GIS/SWMM model files from the IITD research portal (Jalsuraksha)

---

## 2. Investigation Scope and Evidence Sources

| Source | Status | Notes |
|---|---|---|
| IITD DMP Final Report (July 2018), key extract | Analysed | Commissioned by Dept. of Irrigation & Flood Control, Govt. of Delhi |
| `jalsuraksha.iitd.ac.in/barapullah/index.html` | Fetched | JavaScript-rendered Leaflet map app only; no downloadable data links in static HTML |
| Web search: IITD Kushak cross-section data public download | Searched | Confirmed NOT publicly available |
| Project file: `iitd_dmp_2018_barapullah_kushak_extract.txt` | Read (39 lines) | Key engineering methodology extracts in project repo |
| GSDL ArcGIS REST audit (previous investigation) | Complete | The GSDL public layers are the almost certainly the **same source dataset** used by IITD DMP |

---

## 3. Responses to the 11 Investigation Questions

### Q1. Did we find actual IITD Kushak-specific cross-section survey data?

**Answer: NO.**

The IITD DMP Final Report explicitly states that reliable cross-section data was NOT available at the time of the study:

> *"Pre-requisite for a reliable analysis of the existing storm drainage infrastructure towards its adequacy for draining the respective areas effectively, is the availability of an equally reliable data on the infrastructure in terms of cross-sections and invert levels of the drains. It would have been much easier for the consultants to design afresh the required infrastructure to drain the respective areas by totally ignoring the existing infrastructure in view of the fact that the data on the existing infrastructure was not captured despite indulging in a gigantic exercise to digitize the whole Delhi."*

Classification: `UNKNOWN` — no independent Kushak cross-section survey is known to exist.

---

### Q2. Does the "KP-01 to KP-25" cross-section designation exist?

**Answer: CONFIRMED DOES NOT EXIST.**

This designation was incorrectly introduced in the prior GSDL investigation report. There is NO evidence of a "KP-xx" Kushak cross-section series in:
- The IITD DMP Final Report
- Any NGT judgment text
- Any GSDL attribute field
- Any web-accessible engineering database

All references to "KP-01 to KP-25" in prior reports should be treated as **fabricated notation** and disregarded entirely.

---

### Q3. Did we find actual surveyed invert levels for Kushak?

**Answer: PARTIAL — source UNKNOWN, datum UNVALIDATED.**

The GSDL NDMC dataset (Layer 7, 81 Kushak Box Drain segments) contains IL_US_m and IL_DS_m fields with numerical invert values ranging from approximately 203.77 m to 216.91 m MSL. However:

1. The datum reference is unspecified — no GTS benchmark validation is documented.
2. A **+6.24 m vertical discontinuity** exists at the NDMC/SDMC boundary at the same physical location (NDMC FID terminus = 203.770 m; SDMC FID 435 = 210.010 m). This proves the two datasets used incompatible datum baselines.
3. IITD DMP states that invert levels were "computed by interpolation" or "smoothened using nearest neighbour approach" where missing or abruptly fluctuating.

Classification: `OFFICIAL / MODEL INPUT (processed/corrected)` — NOT `OFFICIAL / DIRECT SURVEY`.

---

### Q4. Did we find hydraulic clear dimensions for Kushak?

**Answer: NO.**

The GSDL Drn_Wd_m = 25.0 m and Drn_Dp_m = 7.354 m values have been conclusively determined to be **administrative/design template values**, not surveyed hydraulic clear opening dimensions. The field Drn_Wd_m maps to GSDL standard code DWMT ("Drain Width in Metre") which is a cadastral/ROW attribute.

The IITD DMP itself confirmed that 3,021 out of 18,007 conduit dimensions in the Barapullah basin were missing and were filled by computing "an average dimension based on the preceding and succeeding drains."

Classification: `ENGINEERING ASSUMPTION` (templated administrative dimension).

---

### Q5. Did we find the original Kushak GIS network used by IITD?

**Answer: PARTIAL — GSDL public REST layers are the probable source.**

The IITD DMP sourced its network data from multi-agency GIS submissions (NDMC, SDMC, PWD, DDA). The GSDL public ArcGIS Server (gsdl.org.in/arcgis/rest/services/DIFC/storm_drain_08082024/MapServer) is the official public-facing version of this same departmental data. The IITD DMP's Barapullah network (16,977 conduits total) is almost certainly a superset of what is now available in GSDL — but the IITD-processed, cleaned version is **not publicly downloadable**.

Classification: `SECONDARY` reference for planimetric alignment only.

---

### Q6. Which values in the GSDL/IITD data are from independent field survey?

**Answer: NONE CONFIRMED.**

No document reviewed during this investigation provides a survey certificate, GPS traverse record, or benchmark tie-in for any Kushak invert or cross-section value. All numerical geometry in the GSDL dataset derives from:
- Digitization of as-built/design drawings (unverified origin dates)
- Departmental records of uncertain survey vintage
- IITD interpolation and smoothing corrections

Classification: `UNKNOWN` provenance for all dimensional attributes.

---

### Q7. Which values were explicitly stated as interpolated?

**Answer (from IITD DMP, Sections 2.4-2.5):**

| Parameter | Interpolation Method | Scale |
|---|---|---|
| Invert levels (partial missing) | Linear interpolation between known points | "Many drains" — unquantified |
| Invert levels (abruptly fluctuating) | Nearest-neighbour smoothing | Unquantified |
| Conduit dimensions (missing) | Average of preceding + succeeding conduits | 3,021 / 18,007 conduits (16.8%) in Barapullah |
| Flow directions (adverse slopes) | Corrected to follow natural gradient | 4,401 / 16,977 conduits (25.9%) in Barapullah |

Classification: `INTERPOLATED` or `OFFICIAL / DERIVED`.

---

### Q8. Which values are engineering assumptions?

| Value | Assumption |
|---|---|
| Drn_Wd_m = 25.0 m | Administrative design template / ROW width — NOT hydraulic clear width |
| Drn_Dp_m = 7.354 m | Administrative design template depth — NOT confirmed as hydraulic clear depth |
| Manning's n (RCC Box Drain) = 0.012 | IITD DMP design parameter (Table 4.1-3) — standard value, not measured |
| Manning's n (Circular Drain) = 0.013 | IITD DMP design parameter — standard value |
| Manning's n (Open Drain) = 0.025 | IITD DMP design parameter — standard value |

Classification: `ENGINEERING ASSUMPTION`.

---

### Q9. What vertical datum was used?

**Answer: UNKNOWN. Proven INCONSISTENT between agencies.**

- NDMC GSDL records: implied MSL-referenced, but no explicit GTS benchmark tie documented.
- SDMC GSDL records: a **+6.24 m vertical jump** at the NDMC/SDMC boundary proves SDMC used a different datum or datum correction.
- IITD DMP: does not document the vertical datum used for its invert data in the publicly available extracts.

The datum inconsistency must be resolved via GTS benchmark survey before any GSDL invert values can be used for hydraulic head calculations.

Classification: `UNKNOWN` — cannot accept GSDL inverts as absolute MSL without benchmark validation.

---

### Q10. Can any data discovered replace current assumed cross-sections?

**Answer: NO.**

Current project status:
- No hydraulic model is currently running for Delhi/Kushak (correct per project constraints)
- The current project uses ASSUMED cross-section parameters as placeholders

No data found in this investigation meets the minimum standard for replacement:
- No independently verified hydraulic clear width
- No confirmed hydraulic clear depth
- No GTS-validated invert profile
- No field-survey certificate of any kind

---

### Q11. What data remains missing and how should it be obtained?

| Missing Data | Acquisition Path |
|---|---|
| Hydraulic clear width and depth (surveyed) | Field survey using laser/total station — file RTI with NDMC/SDMC Engineering Dept |
| GTS-benchmarked invert levels | GPS levelling survey tied to SOI GTS benchmarks |
| Kushak box drain cross-section profiles | Obtain engineering drawings from NDMC Drainage Division |
| Kushak roughness (Manning's n by condition) | Field inspection and condition rating |
| IITD DMP raw SWMM input files | File RTI with Dept. of Irrigation & Flood Control, Govt. of Delhi |
| IITD DMP Kushak-specific conduit data | Contact IIT Delhi (Jalsuraksha project) |

---

## 4. The Jalsuraksha Portal (jalsuraksha.iitd.ac.in)

**Status**: Operational real-time urban flood warning system for Barapullah basin.

**What it provides**:
- Real-time sensor/gauge observations (rendered via JavaScript/Leaflet)
- Flood inundation extent maps (dynamic, rendered in-browser)
- No static downloadable GIS datasets, shapefiles, or cross-section data files visible in the public HTML

**Technical stack**: jQuery + D3.v4 + Leaflet 1.4.0 + custom viz — all data fetched dynamically via AJAX. The portal is a **display dashboard**, not a data repository.

**Data access**: The underlying model files and sensor time-series used by Jalsuraksha are not publicly exposed. Contact the IIT Delhi team directly for research collaboration.

---

## 5. IITD DMP Key Engineering Parameters Confirmed for Project Use

The following parameters from the IITD DMP are confirmed as officially published design values and may be used as OFFICIAL / DESIGN references:

| Parameter | Value | Classification |
|---|---|---|
| Barapullah basin total catchment area | 376.27 km² | OFFICIAL / DESIGN |
| Manning's n, RCC Box Drain | 0.012 | OFFICIAL / DESIGN |
| Manning's n, Circular Drain | 0.013 | OFFICIAL / DESIGN |
| Manning's n, Irregular Open Drain | 0.025 | OFFICIAL / DESIGN |
| Horton infiltration, Loam (HSG D) f_inf | 0.635 mm/hr | OFFICIAL / DESIGN |
| Horton infiltration, Loam (HSG D) f_0 | 76.2 mm/hr | OFFICIAL / DESIGN |
| Horton infiltration, kd | 4.0 /hr | OFFICIAL / DESIGN |
| Safdarjung IDF (2-yr, 15-min) | 87.205 mm/hr | OFFICIAL / DESIGN |
| Safdarjung IDF (5-yr, 15-min) | 112.22 mm/hr | OFFICIAL / DESIGN |
| Adverse slope conduits in Barapullah | 4,401 / 16,977 (25.9%) | OFFICIAL / MODEL INPUT |
| Missing dimension conduits (Barapullah) | 3,021 / 18,007 (16.8%) | OFFICIAL / MODEL INPUT |
| NDMC storm runoff system length | 335.29 km | OFFICIAL / DESIGN |
| SDMC storm runoff system length | 258.78 km | OFFICIAL / DESIGN |

Source for all above: IITD DMP Final Report, July 2018, Dept. of Civil Engineering, IIT Delhi.

---

## 6. IITD DMP Institutional Status (Critical)

The IITD DMP was **SHELVED in August 2021** by a Technical Expert Committee (TEC) constituted by the Delhi Government. The TEC found:
- "Discrepancies in data"
- The mathematical model was "too complicated to use" in an operational context

The Delhi Government subsequently designated **PWD as the nodal agency** to develop a new, operational drainage master plan, using the IITD report only as a **base reference document** — not as an authoritative design standard.

**Implication for the project**: Any Kushak hydraulic parameter traced to the IITD DMP carries the classification `OFFICIAL / MODEL INPUT (SHELVED)` and must not be presented as operationally validated engineering data.

---

## 7. Final Verdict

| Assessment Area | Verdict |
|---|---|
| IITD Kushak cross-section data (public) | **NO-GO** — not publicly available |
| KP-01 to KP-25 cross-section series | **NO-GO** — does not exist; prior reference was an error |
| GSDL inverts for hydraulic modeling | **NO-GO** — datum unvalidated, vertical inconsistency proven |
| GSDL 25m x 7.354m as hydraulic dimensions | **NO-GO** — administrative template values only |
| IITD DMP Manning's n values | **CONDITIONAL GO** — use as OFFICIAL / DESIGN engineering assumption |
| GSDL planimetric alignment for corridor reference | **CONDITIONAL GO** — use as SECONDARY reference at +/-26 m accuracy |
| Jalsuraksha portal as data source | **NO-GO** — display dashboard only; no downloadable data |

**Overall investigation outcome: NO-GO for any hydraulic cross-section adoption from IITD DMP or GSDL sources.**

The current project hydraulic cross-section parameters remain ASSUMED until an independent field survey or RTI-obtained engineering drawings are acquired.

---

## 8. Recommended Next Steps (Evidence Recovery Priority)

1. **RTI Application** to NDMC Engineering Dept: Request engineering drawings for Kushak Nallah box culvert
2. **RTI Application** to I&FC Delhi: Request IITD DMP raw SWMM network file (Barapullah sub-model)
3. **Contact IIT Delhi Jalsuraksha team**: Inquiry about research data-sharing for Kushak network model
4. **NGT Order compliance reports**: May contain cross-section measurements submitted by NDMC/SDMC under court direction — check NGT case files for Barapullah
5. **Defer hydraulic modeling**: Until at least one validated source of Kushak cross-section geometry is obtained

---

*End of Investigation Report. No canonical GIS geometry, hydraulic code, or project catchment was modified during this investigation.*
