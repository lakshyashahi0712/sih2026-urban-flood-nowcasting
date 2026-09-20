# Chennai Historical Observation Forensics — Adyar Basin Validation Evidence Gate

**Scope:** Forensic extraction and audit of historical flood observations, hydraulic calibration evidence, and stormwater drainage outfall data from the 27-page Research Square study:
> Pradeep C., Sankar C.P., Thirumalaivasan D., Ajith Kumar K., Kathiravan K., Vidyasakar A., Arunbharathi V. (2023). *"3- Way coupled urban flood modelling for a part of Chennai City using high-resolution topographic data."* Research Square preprint, DOI: [10.21203/rs.3.rs-3308842/v1](https://doi.org/10.21203/rs.3.rs-3308842/v1), posted 01 September 2023.

**Audit Date:** 2026-09-19  
**Status:** FORENSIC EVIDENCE REGISTER — CHENNAI V3  
**Model & Production State:** Production model UNTOUCHED; no calibration performed; no synthetic coordinates generated; no point depths inferred from aggregates.

---

## 0. Quality Gates & Verification Audit

| Quality Gate | Requirement | Forensic Status | Evidence / Reference |
|---|---|---|---|
| **Gate 1: Exact Citations** | Every extracted number must cite page/table/figure | **PASSED** | Fully cited throughout report and CSV files. |
| **Gate 2: Unit Preservation** | Preserve exact printed units (m, sq.km, cms, hrs, %) | **PASSED** | Metres, sq.km, cms ($m^3/s$), hours, and % maintained verbatim. |
| **Gate 3: Coordinate Integrity** | No invented coordinates; unknown coordinates remain UNKNOWN | **PASSED** | All 30 outlets set to `UNKNOWN` in crosswalk; no coordinates hallucinated. |
| **Gate 4: Numeric Fidelity** | No silent rounding; verbatim string capture | **PASSED** | Captured verbatim (e.g. Outlet 5 invert = `4.325`, Outlet 14 duration = `48.25`). |
| **Gate 5: Calibration Discipline** | No calibration performed; author calibration results not claimed as ours | **PASSED** | 2008 HEC-HMS $E_{NS}=0.79$, $d=0.90$ recorded strictly as authors' published calibration. |
| **Gate 6: Model Invariance** | Zero production model modifications | **PASSED** | No backend/domain code modified. |
| **Gate 7: CSV Parse Validation** | Machine-readable, zero syntax/type errors | **PASSED** | Automated parse validation suite passed (`validate_observation_csvs.py`). |
| **Gate 8: Record Accounting** | Exact counts (30 outlets, 744/72 for 2005, 200/45 for 2015) | **PASSED** | Verified and catalogued without inflation or truncation. |
| **Gate 9: Visual Inspection** | Visual inspection of pages 8–11, 23–26 | **PASSED** | All tables, scatter plots, maps, and hydrographs visually checked. |

---

## 1. Deliverables Catalog

The forensic extraction produced the following files in [`data/chennai/observations/`](file:///c:/Users/laksh/OneDrive/Desktop/sih2026/data/chennai/observations):

1. **[`adyar_swd_outlets_published.csv`](file:///c:/Users/laksh/OneDrive/Desktop/sih2026/data/chennai/observations/adyar_swd_outlets_published.csv)**: Complete verbatim extraction of Table 2 (30 stormwater outlets discharging into the Adyar River), pages 8–9.
2. **[`adyar_2005_published_summary.csv`](file:///c:/Users/laksh/OneDrive/Desktop/sih2026/data/chennai/observations/adyar_2005_published_summary.csv)**: Documented aggregate observations and validation statistics for the 02 December 2005 flood event (Table 3, Table 1, pp. 5, 7, 10).
3. **[`adyar_2015_published_summary.csv`](file:///c:/Users/laksh/OneDrive/Desktop/sih2026/data/chennai/observations/adyar_2015_published_summary.csv)**: Documented aggregate observations and validation statistics for the 01 December 2015 flood event (Table 4, Table 1, pp. 5, 7, 10, 11).
4. **[`adyar_swd_outlets_crosswalk.csv`](file:///c:/Users/laksh/OneDrive/Desktop/sih2026/data/chennai/observations/adyar_swd_outlets_crosswalk.csv)**: Spatial crosswalk register mapping Outlets 1–30 from Figure 12 (p. 23) to candidate localities with `coordinates_status = UNKNOWN`.
5. **[`validate_observation_csvs.py`](file:///c:/Users/laksh/OneDrive/Desktop/sih2026/data/chennai/observations/validate_observation_csvs.py)**: Automated verification script validating CSV schemas, row counts, and data types.

---

## 2. Phase 1: 30 Stormwater Outlets (Table 2 Forensics)

### 2.1 Table Structure & Verbatim Contents
Table 2 spans **Page 8** (Outlets 1–16) and **Page 9** (Outlets 17–30), titled *"Comparison of SWD Outlet levels with MFL in River"*.

The table records:
- `Outlet Id`: 1 to 30.
- `Ground Level`: Ground elevation in metres.
- `Invert Level`: Outfall invert level in metres.
- `MFL`: Maximum Flood Level in metres during the 2015 event.
- `Time Period`:
  - `Complete submergence of SWD`: Timestamp when river stage overtops ground level.
  - `Complete free fall of SWD`: Timestamp when river stage recedes below invert level.
- `Duration of SWD Ineffective (Hrs)`: Time duration during which the outlet cannot discharge freely by gravity.

### 2.2 Forensic Discrepancies & Observations
1. **Missing Time Fields**:
   - Outlets 28 and 30 have `-` printed for *Complete submergence of SWD* and *Duration of SWD Ineffective (Hrs)*.
   - **Reason**: Outlet 28 has Ground Level = 3.88 m, Invert Level = 3.13 m, but MFL = 3.56 m. Outlet 30 has Ground Level = 4.35 m, Invert Level = 3.45 m, but MFL = 3.52 m. Because the river MFL never reached their ground elevation (though it exceeded their invert level), the pipe outlet crown/ground was never completely submerged under river backwater. The paper states on page 7: *"It can be easily visualized in Table 2 that only two outlets are effective during the peak discharge in the river."*
   - **Protocol Enforcement**: Stored strictly as `NULL`, not `-`. Complete free fall timestamps are printed and preserved (`2/12/2015 11:30` and `2/12/2015 07:00` respectively).
2. **Missing Column `mfl_start`**:
   - The paper's Table 2 does not contain an `mfl_start` column. Stored strictly as `NULL` across all 30 rows.
3. **Duration Inconsistency in Outlet 14**:
   - For Outlet 14, submergence is `1/12/2015 14:00` and free fall is `3/12/2015 15:30`.
   - Elapsed physical time is $24 + 24 + 1.5 = 49.5\text{ hours}$.
   - However, Table 2 prints `48.25` in the duration column.
   - **Protocol Enforcement**: Verbatim value `48.25` preserved in the CSV; documented in notes.
4. **Precision Variations**:
   - Outlet 5 has Invert Level `4.325` (3 decimal places); all other levels are given to 2 decimal places (e.g. `10.03`, `5.68`, `6.28`, `0.67`).
   - Durations are a mix of integers (`57`, `36`, `41`, `54`, `44`) and decimals (`35.25`, `20.5`, `22.5`, `41.25`, `45.75`, `66.25`, `67.75`).
   - Verbatim values preserved without silent rounding.

### 2.3 Provenance Classification: Why Calling Table 2 "LiDAR-Derived" is Unproven
- Page 2 states: *"High-resolution LiDAR DEM acquired through Airborne Laser Scanning technology is used for extraction of cross section of rivers, ground level of manholes for stormwater drains and for preparing accurate bathymetry for use in MIKE 21."*
- Page 4 (§3.4) states: *"The network of the stormwater drain for the study area was collected from Stormwater drainage department, Greater Chennai Corporation (GCC)... 119km length of the stormwater drainage network within the study area (B) is taken for hydrodynamic simulation."*
- Page 6 states: *"The stormwater drainage network and its attribute parameters such as dimensions of drains, invert levels and slope etc., were used to setup the storm sewer network model in MU MOUSE."*
- Page 7 states: *"Duration of ineffectiveness of the storm water drain have been estimated as the time difference between the complete submergence to complete free fall of the storm water drains... MU MOUSE model was neither calibrated nor validated due to non-availability of observed data."*

**Verdict:**
1. Invert levels originate from **GCC Stormwater Drainage Department engineering records / GIS**.
2. Ground levels are stated to be extracted from the 2009 ALS LiDAR DEM (or GCC manhole records).
3. MFL, Complete Submergence, Complete Free Fall, and Duration of Ineffectiveness are **NOT field observations**; they are **model-simulated hydraulic outputs** from the coupled MIKE FLOOD (MIKE 11 HD / MU MOUSE / MIKE 21) simulation of the December 2015 event!
4. Therefore, labeling Table 2 as purely "LiDAR-derived" or "field observed" is scientifically false. The table is classified as **`SOURCE-PUBLISHED`** (a hybrid publication artifact of GCC engineering invert levels, DEM ground elevations, and 2015 1D/2D hydraulic simulation results).

---

## 3. Phase 2: 2005 Flood Event Forensics

### 3.1 Documented Event Parameters
- **Event Date:** 02 December 2005 (Page 4, Page 6). Preceded by saturated antecedent conditions (AMC III) from above-normal October–November rainfall.
- **Precipitation:** Meenambakkam rainfall station recorded **235 mm** total rainfall with a peak intensity of **60 mm/hr** (Page 9).

### 3.2 Published Observation Evidence
- **Citywide Survey:** Page 5 (§3.5) documents that flood depth data was collected via a **questionnaire survey in the field at 744 locations** across Chennai city to reconstruct a flood risk map.
- **Adyar Validation Sample:** Page 10 documents that **72 locations** fell within the Adyar study area (B) and were used to validate the MIKE FLOOD simulated flood depths (shown as scatter points in Figure 14).
- **Error Distribution:** **56 out of 72 locations** had a difference of **0.0 m to 0.5 m** (77.8% within 0.5 m) (Page 10).
- **Published Correlation:** $R^2 = 0.772$ (Page 2, Page 25 Figure 14).
- **River MFL Validation (Table 1, Page 7):**
  - *Nandambakkam Bridge (chainage 12,600 m):* Simulated MFL = **9.23 m**, Observed MFL = **9.40 m** (error = -0.17 m).
  - *Maraimalai Adigal Bridge (chainage 7,400 m):* Simulated MFL = **5.52 m**, Observed MFL = **5.60 m** (error = -0.08 m).
- **Aggregate Inundation Extent (Table 3, Page 10):**
  - Considering minimum flood depth $\ge 0.25\text{ m}$, total inundation extent was **9.02 sq.km**, representing **14% of the study area**.

| Depth Range (m) | Published Inundation Extent ($\text{km}^2$) | Source Reference |
|---|---|---|
| 0.25m – 0.5m | 4.34 | Table 3, Page 10 |
| 0.5m – 1m | 2.40 | Table 3, Page 10 |
| 1.0 m – 2.5m | 2.23 | Table 3, Page 10 |
| **Total** | **9.02** | **Table 3, Page 10** |

> [!NOTE]
> **Table 3 Arithmetic Check:** $4.34 + 2.40 + 2.23 = 8.97\text{ km}^2$. The printed total is $9.02\text{ km}^2$ (a discrepancy of $+0.05\text{ km}^2$). Both the verbatim depth bins and the verbatim total are recorded without alteration.

**Classification:** These values are **published aggregate summaries and model outputs**, NOT original point observation records.

---

## 4. Phase 3: 2015 Flood Event Forensics

### 4.1 Documented Event Parameters
- **Event Date:** 01 December 2015 (Page 4, Page 6). Extreme Northeast Monsoon storm.
- **Precipitation:** Chennai witnessed **346 mm of rainfall in 24 hours** (Page 2, Page 4). Soil in AMC III condition.
- **Return Period:** Estimated return period of 165 years (Page 7).

### 4.2 Published Observation Evidence
- **Citywide Survey:** Page 5 (§3.5) documents that a field survey immediately after December 2015 measured flood depths at **200 locations** using physical **flood marks** (e.g., water stain lines on buildings, photographed in Figure 3, p. 17).
- **Adyar Validation Sample:** Page 10 documents that **45 locations** fell within the Adyar study area (B) and were used to validate simulated flood depths (shown as scatter points in Figure 16).
- **Error Distribution:** **68% of validation points** had a difference $\le 0.5\text{ m}$ (Page 10, Page 11).
- **Published Correlation:** $R^2 = 0.883$ (Page 2, Page 27 Figure 16).
- **River MFL Validation (Table 1, Page 7):**
  - *Nandambakkam Bridge (chainage 12,600 m):* Simulated MFL = **9.94 m**, Observed MFL = **10.11 m** (error = -0.17 m).
  - *Maraimalai Adigal Bridge (chainage 7,400 m):* Simulated MFL = **7.30 m**, Observed MFL = **7.50 m** (error = -0.20 m).
- **Extreme Depths Reported in Text (Page 11):**
  - Worst affected areas: Manapakkam, Nandambakkam, Jafferkhanpet, Saidapet, Mambalam, and Kotturpuram.
  - Flood depths in these areas ranged from **2 m to 7 m**.
  - **Maximum observed flood depth:** **7.0 m observed in Saidapet**.
- **Upstream Breaches:** Page 11 notes that discrepancies were influenced by unmodeled tank breaches upstream in Nandhivaram, Urappakkam, Mannivakkam, and Adanur tanks (citing Press Statement of Chief Secretary, GoTN).
- **Aggregate Inundation Extent (Table 4, Page 10):**
  - Total inundation extent: **14.88 sq.km**.

| Depth Range (m) | Published Inundation Extent ($\text{km}^2$) | Source Reference |
|---|---|---|
| 0.25m – 0.5m | 4.97 | Table 4, Page 10 |
| 0.5m – 1m | 4.07 | Table 4, Page 10 |
| 1.0 m – 2.0 m | 3.31 | Table 4, Page 10 |
| 2.0 m – 3.0 m | 1.91 | Table 4, Page 10 |
| 3 m – 7.0 m | 0.62 | Table 4, Page 10 |
| **Total** | **14.88** | **Table 4, Page 10** |

> [!NOTE]
> **Table 4 Arithmetic Check:** $4.97 + 4.07 + 3.31 + 1.91 + 0.62 = 14.88\text{ km}^2$. The bin sum matches the published total exactly ($14.88\text{ km}^2$).

---

## 5. Phase 4: Search for Raw / Supplementary Data

An exhaustive lexical search across the entire 27-page document was conducted for target terms:

| Target Query | Occurrences | Matched Pages | Context & Forensic Evaluation |
|---|---|---|---|
| `latitude` | 0 | None | Not mentioned in document text. Graticule ticks appear only on overview map frames (Fig 1, Fig 6). |
| `longitude` | 0 | None | Not mentioned in document text. |
| `coordinates` | 0 | None | Zero coordinates (WGS84 or UTM) published for any observation point, outfall, or survey station. |
| `GPS` | 0 | None | Never mentioned in document text. |
| `GIS` | 2 | p. 14 | Appears solely in formal bibliography citations (Ref 19: Prodanovic et al. 1998; Ref 24: Werner 2001). (Also preprocessor name `HEC-GeoHMS` on p. 5). |
| `supplement` / `supplementary` | 0 | None | No supplementary materials, no appendices, no external repository links. |
| `dataset` | 2 | p. 3 | Refers generically to low-resolution satellite DEMs (*"satellite-based observations are used for generating topographic datasets..."*). |
| `data availability` | 0 | None | Zero Data Availability statement in this Research Square preprint. Declarations (p. 12) only state: *"All of the material in the manuscript is owned by the authors no permissions are required to publish."* |
| `744` | 1 | p. 5 | Number of questionnaire survey locations for 2005 event across Chennai. |
| `200` | 2 | p. 5, p. 10 | Number of post-event flood mark survey locations for 2015 event across Chennai. |
| `72` | 4 | p. 2, p. 10, p. 25 | Validation points within Adyar study area B for 2005 event. |
| `45` | 2 | p. 10, p. 27 | Validation points within Adyar study area B for 2015 event. |
| `observed depth` | 3 | p. 7, p. 25, p. 27 | Discussion on p. 7; Y-axis title of Fig 14 (p. 25); X-axis title of Fig 16 (p. 27). |
| `flood depth` | 30 | pp. 2, 5, 9, 10, 11, 25, 27 | Used throughout text and table/figure headers. |

### Explicit Forensic Determination
1. **Supplementary Tables / Appendices:** NONE exist in the document.
2. **Embedded Coordinates:** NONE exist in the document for the 744, 200, 72, 45, or 30 locations.
3. **Hidden Textual Tables:** NONE exist. All tables are Table 1 (p. 7), Table 2 (pp. 8–9), Table 3 (p. 10), and Table 4 (p. 10).
4. **Downloadable Data References:** NONE exist.
5. **Raw Observation Status:** The raw point-level observation tables for the 744/72 (2005) and 200/45 (2015) survey points are **UNAVAILABLE** in the paper.

---

## 6. Phase 5: Validation Figures Forensics (Figures 14 and 16)

### 6.1 Figure 14 Forensics (2005 Validation Scatter Plot, Page 25)
- **Caption:** *"Figure 14. Scatter plot of simulated and observed flood depth for 2005 flood"*
- **Geometry & Axes:**
  - Horizontal axis ($X$): **Simulated flood depth (m)**, scale 0.0 to 2.5 m (tick interval 0.5 m).
  - Vertical axis ($Y$): **Observed flood depth (m)**, scale 0.0 to 1.8 m (tick interval 0.2 m).
- **Data Points:** 72 individual diamond glyphs plotted.
- **Published Metric:** Linear regression trendline with $R^2 = 0.772$.
- **Recoverability:** Exact numeric coordinates, survey IDs, street names, and exact numeric depths for the 72 points **CANNOT be recovered** from this raster plot. Automated or manual pixel digitization can only produce approximate paired scalar values $(x_i, y_i)$, with zero spatial attribution.
- **Classification Rule:** Any values extracted from Figure 14 must be classified strictly as **`DERIVED_FROM_PUBLISHED_FIGURE`** and must NEVER be represented as original field observations.

### 6.2 Figure 16 Forensics (2015 Validation Scatter Plot, Page 27)
- **Caption:** *"Figure 16. Scatter plot of simulated and observed flood depth for 2015 flood event"*
- **Geometry & Axes (Note Axis Inversion!):**
  - Horizontal axis ($X$): **Observed flood depth (m)**, scale 0.0 to 6.0 m (tick interval 1.0 m).
  - Vertical axis ($Y$): **Simulated flood depth (m)**, scale 0.0 to 5.0 m (tick interval 0.5 m).
  - *Axis inversion caveat:* The authors plotted Simulated on X and Observed on Y in Fig 14, but reversed them to Observed on X and Simulated on Y in Fig 16.
- **Data Points:** 45 individual diamond glyphs plotted.
- **Published Metric:** Linear regression trendline with $R^2 = 0.883$.
- **Spatial Tracing in Figure 15 (Page 26):**
  - Figure 15 shows the 2015 inundation map with small black triangles representing "Field Points".
  - However, Figure 15 contains no coordinate grid, no point labels, no point IDs, and low raster resolution. Point locations cannot be reliably reverse-geocoded without arbitrary guesswork.
- **Classification Rule:** Any values extracted from Figure 16 or Figure 15 must be classified strictly as **`DERIVED_FROM_PUBLISHED_FIGURE`**.

---

## 7. Phase 6: 2008 Hydrologic Calibration Forensics (Figure 8 & Figure 9)

### 7.1 Calibration Event Details
- **Event Period:** 25 November 2008 to 01 December 2008 (Northeast Monsoon flood event).
- **Model:** HEC-HMS hydrologic basin model for Upper Catchment A (upstream of GCC urban reach B).
- **Element / Location:** `Element: OUTLET` at the outlet of Adyar sub-basin (where upper river enters urban reach B).
- **Source Agency:** Water Resources Department (WRD), Government of Tamil Nadu (acknowledged in §4 and p. 13).
- **Reason for 2008 Selection:** Page 6 states: *"The model was calibrated at outlet of Adyar sub-basin for the flood event in 2008 since observed flow data was available only for that particular event (Fig. 8)."*

### 7.2 Graphical Characteristics (Figure 8, Page 21)
- **Vertical Axis ($Y$):** `Flow (cms)` ($m^3/s$), scale 0 to 1,200 cms (major ticks at intervals of 200 cms: 0, 200, 400, 600, 800, 1000, 1200).
- **Horizontal Axis ($X$):** Date axis with labels `25 Nov 2008`, `26`, `27`, `28`, `29`, `30`, `1 Dec 2008`.
- **Legend & Series:**
  - `(Compute Time: 20Apr2018, 13:54:09)`
  - `Run:2008 Element: OUTLET Result: Observed Flow`: Solid black line connecting black circular marker symbols.
  - `Run:2008 Element: OUTLET Result: Outflow`: Solid blue line (simulated hydrograph).
  - Dashed grey line: Baseflow / recession component.
- **Approximate Timestep & Peak:**
  - Counting the circular observation markers shows approximately 4 points per 24-hour day ($\approx 6\text{-hour timestep}$).
  - Observed peak flow reaches approximately **$980\text{–}1,000\text{ cms}$** on 28 November 2008.
  - Simulated peak flow reaches approximately **$1,100\text{ cms}$** on 28 November 2008.

### 7.3 Published Calibration Metrics (Figure 9, Page 22)
- **Nash-Sutcliffe Efficiency ($E_{NS}$):** **0.79** (Page 6).
- **Index of Agreement ($d$):** **0.90** (Page 6).
- **Coefficient of Determination ($R^2$):** **0.810** (Figure 9 scatter plot, Page 22).

> [!IMPORTANT]
> **Authors' Result Discipline:** These goodness-of-fit indices ($E_{NS} = 0.79$, $d = 0.90$, $R^2 = 0.810$) are the **authors' published calibration results**, NOT our own model results. The numeric time-series values of the 2008 observed flow hydrograph are not published in tabular form and are classified as **`DERIVED_FROM_PUBLISHED_FIGURE`** if digitized.

---

## 8. Phase 7: Stormwater Outlets Spatial Crosswalk Forensics (Figure 12)

### 8.1 Inspection of Figure 12 (Pages 23–24)
- **Title / Caption:** *"Figure 12. Location of Stormwater drains outlets"* (caption header spans bottom of p. 23 and top of p. 24).
- **Errata in Published Text:** On page 7, the text states: *"Figure 9depicts locations of the stormwater outlets into the Adyar River..."*. Figure 9 is actually the 2008 flow scatter plot. The actual outlet location map is Figure 12.
- **Cartographic Elements:**
  - Contains a scale bar (`Scale 1:50,000`) and a North arrow.
  - Shows Reach B of the Adyar River with 30 numbered black dots (1 through 30).
  - Shows major locality text labels: `Porur`, `Manapakkam`, `Nandambakkam`, `Jafferkhanpet`, `Ashok Nagar`, `Saidapet`, `Kotturpuram`, `Mylapore`, `Adyar`.
  - **CRITICAL DEFECT:** Figure 12 contains **NO coordinate graticule**, NO latitude/longitude border ticks, and NO projected grid ticks.

### 8.2 Spatial Attribution & Crosswalk Summary
Per protocol, **coordinates cannot be assigned by visual guessing** and are strictly marked **`UNKNOWN`**. The complete crosswalk file is stored in `data/chennai/observations/adyar_swd_outlets_crosswalk.csv`.

| Outlet Range | Published Locality Label (Fig 12) | Candidate Locality / Channel Reach | Coordinates Status | Source Page |
|---|---|---|---|---|
| **1 – 2** | Manapakkam | Manapakkam (south bank, western limit of Reach B) | `UNKNOWN` | 23 |
| **3 – 4** | Porur / Nandambakkam | Nandambakkam (south bank river bend) | `UNKNOWN` | 23 |
| **5 – 7** | Porur / Nandambakkam / Jafferkhanpet | Porur / Nandambakkam reach (north bank) | `UNKNOWN` | 23 |
| **8 – 11** | Jafferkhanpet | Jafferkhanpet (north bank 4-outlet cluster) | `UNKNOWN` | 23 |
| **12 – 13** | Nandambakkam / Jafferkhanpet | Nandambakkam / Jafferkhanpet (south bank opposite cluster) | `UNKNOWN` | 23 |
| **14 – 16** | Saidapet | Saidapet (west approach reach, south bank) | `UNKNOWN` | 23 |
| **17 – 19** | Saidapet | Saidapet / Guindy reach (south bank meander) | `UNKNOWN` | 23 |
| **20 – 22** | Kotturpuram | Kotturpuram approach (north bank) | `UNKNOWN` | 23 |
| **23 – 25** | Kotturpuram | Kotturpuram bend (central/south bank meander) | `UNKNOWN` | 23 |
| **26** | Kotturpuram / Adyar | Kotturpuram / Adyar reach (south bank) | `UNKNOWN` | 23 |
| **27** | Mylapore / Adyar | Mylapore / Adyar reach (north bank) | `UNKNOWN` | 23 |
| **28** | Adyar | Adyar (south bank) | `UNKNOWN` | 23 |
| **29** | Mylapore / Adyar | Mylapore / Adyar reach (north bank near estuary) | `UNKNOWN` | 23 |
| **30** | Adyar | Adyar (south bank near river mouth / estuary) | `UNKNOWN` | 23 |

---

## 9. Phase 8: Model-Limitation Register

The model calibration, validation, and uncalibrated boundary constraints from the study are formally registered below:

```
========================================================================================
                          CHENNAI V3 MODEL-LIMITATION REGISTER
========================================================================================

1. 2008 EVENT:
   - Hydrologic model: HEC-HMS (Upper Catchment A, 824.4 sq.km).
   - Status: CALIBRATED against observed discharge flow series at sub-basin outlet.
   - Goodness-of-Fit: Nash-Sutcliffe ENS = 0.79, Index of Agreement d = 0.90, R2 = 0.810.
   - Limitation: Raw time-series discharge data not published in machine-readable table.

2. 2005 EVENT:
   - Observation Type: Post-flood field questionnaire survey (744 citywide points).
   - Adyar Validation: 72 validation locations in Study Area B.
   - Model Performance: 56 of 72 points (77.8%) within 0.0 to 0.5 m difference; R2 = 0.772.
   - Published Extent: 9.02 sq.km inundated (14% of study area).
   - Limitation: Raw point-level coordinates and measured depths NOT RECOVERED.

3. 2015 EVENT:
   - Observation Type: Post-event physical flood marks survey (200 citywide points).
   - Adyar Validation: 45 validation locations in Study Area B.
   - Model Performance: 68% of points within 0.5 m difference; R2 = 0.883.
   - Published Extent: 14.88 sq.km inundated.
   - Limitation: Raw point-level coordinates and measured depths NOT RECOVERED.

4. MIKE 11 HD (RIVER 1D HYDRAULICS):
   - Manning's Roughness: n = 0.025.
   - Status: NOT CALIBRATED.
   - Reason: River water-level gauging station data is unavailable along Adyar reach.
   - Partial Validation: Spot validation against observed MFL at only 2 bridges
     (Nandambakkam Bridge at 12,600m; Maraimalai Adigal Bridge at 7,400m).

5. MIKE URBAN / MOUSE (STORM SEWER NETWORK):
   - Extent: 119 km stormwater drains in Study Area B.
   - Status: NEITHER CALIBRATED NOR VALIDATED.
   - Reason: Complete non-availability of observed flow/stage monitoring in SWD network.
========================================================================================
```

---

## 10. Phase 9: Project Data Gap Update

The Chennai Urban Flood Nowcasting data gap is formally updated with the following evidence statements:

1. **FLOOD OBSERVATIONS: DOCUMENTED + PUBLISHED**
   - High-quality historical flood observations for Chennai are documented and scientifically established in peer-reviewed literature.
   - **However, publication in an academic paper is NOT equivalent to possession of raw, machine-readable records.**
   - Point coordinates, survey forms, and raw tabular depths remain external to this paper.
2. **INDEPENDENT HISTORICAL EVENTS: TWO CONFIRMED (2005 + 2015)**
   - The 2005 event (questionnaire-based, 72 Adyar points) and 2015 event (flood-mark-based, 45 Adyar points) represent two independent historical extreme events suitable for benchmark validation once point records are acquired.
3. **RAW OBSERVATION ACCESS: UNKNOWN**
   - The primary field data remains with the originating institutions:
     - Institute of Remote Sensing (IRS), Anna University, Chennai.
     - Public Works Department (PWD) / Water Resources Department (WRD), Government of Tamil Nadu.
     - Greater Chennai Corporation (GCC) Stormwater Drainage Department.
   - Access status is `UNKNOWN` until formal academic sharing or institutional data release is negotiated.

---

## 11. Final Summary Report (Sections A through I)

### A. Exact Raw Values Recovered
1. **Table 2 SWD Outlets (Verbatim):**
   - 30 distinct outlet records with exact Ground Level, Invert Level, MFL, Submergence Timestamp, Free Fall Timestamp, and Ineffective Duration.
   - Complete capture in [`data/chennai/observations/adyar_swd_outlets_published.csv`](file:///c:/Users/laksh/OneDrive/Desktop/sih2026/data/chennai/observations/adyar_swd_outlets_published.csv).
2. **Table 1 Bridge MFLs (Verbatim):**
   - Nandambakkam Bridge (12,600 m): 2005 Obs 9.40 m, Sim 9.23 m; 2015 Obs 10.11 m, Sim 9.94 m.
   - Maraimalai Adigal Bridge (7,400 m): 2005 Obs 5.60 m, Sim 5.52 m; 2015 Obs 7.50 m, Sim 7.30 m.

### B. Exact Published Aggregate Values Recovered
1. **2005 Event Aggregates:**
   - Citywide questionnaire points = 744.
   - Adyar validation points = 72.
   - Points within 0 to 0.5 m error = 56 (77.8%).
   - Published inundation extent = 9.02 sq.km (depth bins: 0.25–0.5m: 4.34; 0.5–1m: 2.40; 1.0–2.5m: 2.23 sq.km).
   - Affected study area fraction = 14%.
2. **2015 Event Aggregates:**
   - Citywide flood mark points = 200.
   - Adyar validation points = 45.
   - Fraction within 0.5 m error = 68%.
   - Published inundation extent = 14.88 sq.km (depth bins: 0.25–0.5m: 4.97; 0.5–1m: 4.07; 1.0–2.0m: 3.31; 2.0–3.0m: 1.91; 3.0–7.0m: 0.62 sq.km).
   - Maximum localized flood depth = 7.0 m in Saidapet.

### C. Values Only Available Through Figures
1. **Figure 8 (2008 Calibration Hydrograph):** Observed discharge hydrograph series (cms vs time) is purely graphical.
2. **Figure 9 (2008 Discharge Scatter Plot):** Simulated vs observed discharge points are purely graphical.
3. **Figure 10 (2005 & 2015 HEC-HMS Outflow Hydrographs):** Simulated hydrographs entering Reach B are purely graphical.
4. **Figure 11 (2015 River Longitudinal Section):** Water surface profile along 17.5 km channel is purely graphical.
5. **Figure 12 (30 Outfall Locations):** Ungeoreferenced schematic dot distribution on river centerline.
6. **Figure 14 (2005 Depth Scatter Plot):** 72 paired depth points are purely graphical.
7. **Figure 15 (2015 Inundation & Survey Map):** 45 survey point locations are unlabelled glyphs on a map.
8. **Figure 16 (2015 Depth Scatter Plot):** 45 paired depth points are purely graphical.

### D. Missing Point-Level Fields
For the 744 (2005) and 200 (2015) field survey locations:
- `point_id` (Missing)
- `latitude` / `longitude` / `easting` / `northing` (Missing)
- `locality_name` / `street_address` (Missing)
- `observed_depth_m` (Missing from tables; embedded in scatter plots without IDs)
- `simulated_depth_m` (Missing from tables; embedded in scatter plots without IDs)
- `measurement_method` (Documented in text only: questionnaire for 2005, flood mark measurement for 2015)
- `timestamp_of_peak` (Missing)

### E. 30-Outlet Provenance
- Invert levels: GCC Stormwater Drainage Department engineering records / GIS.
- Ground levels: GCC records / 2009 Airborne Laser Scanning (ALS) LiDAR DEM.
- MFL & Ineffective Duration: Coupled MIKE FLOOD hydraulic model simulation of the December 2015 event.
- Spatial Position: Plotted along Reach B without coordinates. Classified as **`SOURCE-PUBLISHED`**. Calling them purely "LiDAR-derived" is scientifically unproven.

### F. 2005 / 2015 Validation Evidence
- Two distinct validation campaigns conducted by Anna University IRS.
- 2005 relied on retrospective post-disaster household surveys (subject to recall bias, typical $\pm 0.2\text{–}0.5\text{ m}$ uncertainty).
- 2015 relied on physical high-water mark measurements immediately post-flood ($\pm 0.1\text{–}0.2\text{ m}$ structural measurement precision).
- Both confirm substantial severe inundation along the Adyar corridor (Manapakkam to Saidapet and Kotturpuram).

### G. 2008 Discharge Evidence
- Provides the only hydrologic calibration anchor for upper Adyar catchment runoff.
- Calibrated at the outlet of Adyar sub-basin against observed WRD flow data ($E_{NS} = 0.79$, $d = 0.90$).
- Numerical flow values are restricted/unpublished.

### H. Remaining Data Acquisition Blockers
1. **Primary Point Observation GIS Layer:** The original Anna University IRS shapefiles / geodatabases containing the 72 (2005) and 45 (2015) Adyar point depths and coordinates.
2. **2008 WRD Gauged Flow Series:** The official hourly/daily runoff time series for the Adyar outlet gauging station from Water Resources Department, Government of Tamil Nadu.
3. **2009 ALS LiDAR Point Cloud / DTM:** Raw or processed bare-earth tiles covering the 16.5 km Adyar corridor.
4. **Official SWD Outfall Registry:** GCC GIS asset database linking the 30 outfall IDs to specific GCC drain polyline endpoints in layer 8.

### I. Recommended Next Steps
1. **Maintain Strict Evidence Gate:** Do NOT attempt model calibration against digitized scatter plot points. Keep validation records strictly categorized as `DERIVED_FROM_PUBLISHED_FIGURE` or `SOURCE-PUBLISHED-AGGREGATE`.
2. **Spatial Outfall Cross-Matching:** Attempt an automated topological proximity join between the live GCC GIS Layer 8 polyline terminal vertices terminating along the Adyar river polygon and the 30 outfalls in Table 2 based on invert level matching and candidate localities.
3. **Academic / Institutional Outreach:** Formulate an academic data-sharing inquiry directed to Anna University IRS (corresponding author Dr. A. Vidyasakar / Dr. D. Thirumalaivasan) requesting the validation point shapefiles under research attribution.
