# Kushak Drainage Corridor: Hydraulic Geometry & Forensic Provenance Audit

---

## Executive Summary & Scientific Governance Principles

This document establishes the canonical hydraulic geometry dataset for the **$5.028\text{ km}$ ($5,027.56\text{ m}$)** Kushak drainage corridor in South Delhi and presents the complete findings of an independent **forensic provenance audit** conducted on cross-sections `CS-01` through `CS-07`.

### Strict Provenance & Scientific Guardrails
1. **Hydrological Basin Domain**:
   * Working Catchment: **`WORKING MODEL CATCHMENT — 27.66 km²`** (Scenario U2 Copernicus GLO-30 DEM).
   * Watershed Classification: **`WATERSHED STATUS — PROVISIONAL`** (retained as provisional pending municipal verification of subsurface routing across the Shanti Path / Chanakyapuri surface divide).
   * Sensitivity Domain: Scenario U3 ($28.402\text{ km}^2$) reserved strictly for hydrologic sensitivity runs.
   * Historical $35.4\text{ km}^2$ Value: Documented strictly as **`NUMERICAL CONSISTENCY WITH UNRESOLVED HISTORICAL VALUE`**; never claimed as ground truth.
2. **Provenance Downgrades Following Forensic Audit**:
   * OpenStreetMap waterway centerlines are classified as **`OBSERVED / SECONDARY PHYSICAL EVIDENCE`** (never "OFFICIAL").
   * Specific cross-section transects (`CS-01` through `CS-07`) have been **DOWNGRADED** from `OFFICIAL / OBSERVED` to **`ASSUMED / REGULARIZED`**. Earlier citations claiming reach-by-reach geometry tables in the IIT Delhi *Drainage Master Plan (2018)* (e.g., "Ch. 3.2.4 Reach A–E", "Appendix XII") were audited and found to be **UNVERIFIED / ERRONEOUS**.
   * The citation of `CPCB NWMP Drain #14` at Sewa Nagar railway bridge was discovered to be a **SPATIAL MISATTRIBUTION**: in official CPCB records, Drain #14 is the Barapullah outfall to the Yamuna River at Sarai Kale Khan (>6 km downstream), not Sewa Nagar.
   * Macroscopic corridor bounds ($6.0\text{ m} - 18.0\text{ m}$ bottom width, $2.5\text{ m} - 4.2\text{ m}$ wall depth) are verified as an **`OFFICIAL / OBSERVED — INDIRECT MATCH`** based on government court affidavits (Delhi High Court / NGT) and DMP general narrative.
   * The derivation of open-channel bed inverts via $Z_{\text{bank}} - H$ is audited as an **`UNVALIDATED SYNTHETIC OFFSET`** (vertical uncertainty $\pm 1.0\text{ m}$ to $\pm 1.5\text{ m}$), NOT a surveyed geodetic invert datum.
   * Underground conduit dimensions and invert levels for the Africa Avenue tunnel remain strictly **`UNKNOWN`**. Subsurface inverts are **NEVER** inferred from satellite DSM surface elevations.

---

## 1. Canonical Corridor Alignment & Reach Segmentation

The working hydraulic corridor spans **$5,027.56\text{ m}$ ($5.028\text{ km}$)** in UTM Zone 43N (EPSG:32643) and **$5,026.66\text{ m}$** geodetic from Nehru Park / Yashwant Place (Chanakyapuri) to the Barapullah confluence at Defence Colony West.

### 1.1 Reach Architecture
```
[Chainage 0.00 m]                                [Chainage 2,318.42 m]                          [Chainage 5,027.56 m]
Nehru Park / Yashwant Place                       Ring Road / Africa Ave Portal                   Defence Colony West Confluence
       ●───────────────────────────────────────────────────●───────────────────────────────────────────────────●
              REACH 1: UNDERGROUND BOX CULVERT                     REACH 2: OPEN TRAPEZOIDAL CANAL
                 Length: 2,318.42 m (2.318 km)                       Length: 2,709.14 m (2.709 km)
                 Invert: EXPLICITLY UNKNOWN                          Invert: UNVALIDATED SYNTHETIC OFFSET
                 Alignment: OBSERVED / SECONDARY                     Alignment: OBSERVED / SECONDARY
                 Dimensions: UNKNOWN (CAD unrecorded)                Dimensions: ASSUMED / REGULARIZED
```

| Reach Parameter | Reach 1: Underground Corridor | Reach 2: Open Trunk Canal | Total Corridor |
|---|:---:|:---:|:---:|
| **Official Feature Name** | Africa Avenue Subsurface Conduit | Kushak Nallah (Open Trunk) | Kushak Drainage Trunk Corridor |
| **Physical Typology** | Subsurface Reinforced Concrete Box Culvert | Open Trapezoidal / Rectangular Masonry Canal | Dual Subsurface / Surface Trunk |
| **Chainage (m)** | **`0.00 m` to `2,318.42 m`** | **`2,318.42 m` to `5,027.56 m`** | **`0.00 m` to `5,027.56 m`** |
| **Length (m)** | **$2,318.42\text{ m}$ ($2.318\text{ km}$)** | **$2,709.14\text{ m}$ ($2.709\text{ km}$)** | **$5,027.56\text{ m}$ ($5.028\text{ km}$)** |
| **Primary Spatial Source**| OpenStreetMap `Way 44351567` (`tunnel=yes`) | 9 contiguous OSM ways (`name="Kushak Nallah"`) | Verified Contiguous Alignment |
| **Alignment Provenance** | `OBSERVED / SECONDARY PHYSICAL EVIDENCE` | `OBSERVED / SECONDARY PHYSICAL EVIDENCE` | `OBSERVED / SECONDARY PHYSICAL EVIDENCE` |
| **Upstream Endpoint** | $28.5869652^\circ\text{ N}, 77.1992434^\circ\text{ E}$ | $28.5731338^\circ\text{ N}, 77.2117996^\circ\text{ E}$ | $28.5869652^\circ\text{ N}, 77.1992434^\circ\text{ E}$ |
| **Downstream Endpoint**| $28.5731338^\circ\text{ N}, 77.2117996^\circ\text{ E}$ | $28.5797164^\circ\text{ N}, 77.2363871^\circ\text{ E}$ | $28.5797164^\circ\text{ N}, 77.2363871^\circ\text{ E}$ |
| **Daylight Junction Gap**| **$0.000\text{ m}$ (Exact coordinate equality)** | **$0.000\text{ m}$ (Exact coordinate equality)** | Seamless topological junction |
| **Hydraulic Invert Status**| **`UNKNOWN`** | **`DERIVED (UNVALIDATED SYNTHETIC OFFSET)`** | Explicit separation |

Centerline Vector: `data/delhi/derived/hydraulic/kushak_corridor_centerline.geojson`

---

## 2. Forensic Provenance Audit of Cross-Sections CS-01 through CS-07

A forensic provenance investigation was conducted to independently evaluate the documentation, citations, and spatial attribution of the seven open-channel cross-sections.

### 2.1 Audit Findings by Individual Cross-Section

#### 1. CS-01: Daylight Outfall Portal (Chainage 2,320.0 m)
* **Reported Location**: Ring Road / Africa Avenue portal emergence ($28.57313^\circ	ext{ N}, 77.21182^\circ	ext{ E}$).
* **Claimed Dimensions**: $B = 6.5	ext{ m}$, $W_{	ext{top}} = 10.0	ext{ m}$, $H = 2.5	ext{ m}$, $z = 0.70$.
* **Cited Source**: "PWD Desilting Tender Schedule Reach A / IITD DMP Ch 3.2.4 (Reach A)".
* **Forensic Finding**:
  * In the IIT Delhi DMP (2018), Chapter 3.2 models the SWMM network; Table 3.2-4 tabulates "Flooding Volume ($m^3$)" at node junctions (J_19, J_17, etc.), NOT channel dimensions. No "Reach A" schedule exists in DMP Chapter 3.2.
  * PWD desilting tenders list volumetric dredging targets ($m^3$) and divisional jurisdictions, not surveyed structural as-built cross-sections.
  * *Spatial Match*: The physical portal exists at this exact coordinate on Kushak Nallah (`OBSERVED / SECONDARY PHYSICAL EVIDENCE`).
  * *Dimension Status*: The $6.5	ext{ m}$ bottom width is consistent with macroscopic corridor bounds ($6 - 18	ext{ m}$), but the specific value is an engineered regularized assumption.
* **Classification**: **`UNVERIFIED (CITATIONS ERRONEOUS); GEOMETRY IS ASSUMED / REGULARIZED`**.

#### 2. CS-02: Safdarjung Airport South Perimeter (Chainage 2,850.0 m)
* **Reported Location**: South of Safdarjung Airport runway boundary ($28.57322^\circ	ext{ N}, 77.21485^\circ	ext{ E}$).
* **Claimed Dimensions**: $B = 8.0	ext{ m}$, $W_{	ext{top}} = 12.5	ext{ m}$, $H = 2.8	ext{ m}$, $z = 0.80$.
* **Cited Source**: "IIT Delhi DMP 2018 SWMM Network Schedule (Reach B) & PWD records".
* **Forensic Finding**:
  * No "Reach B" table exists in DMP 2018.
  * The dimensions are an idealized regularization representing the upper open canal.
* **Classification**: **`UNVERIFIED (CITATIONS ERRONEOUS); GEOMETRY IS ASSUMED / REGULARIZED`**.

#### 3. CS-03: Kidwai Nagar West / AIIMS Residential Transit (Chainage 3,350.0 m)
* **Reported Location**: Adjacent to NBCC East Kidwai Nagar redevelopment ($28.57480^\circ	ext{ N}, 77.21730^\circ	ext{ E}$).
* **Claimed Dimensions**: $B = 10.0	ext{ m}$, $W_{	ext{top}} = 14.5	ext{ m}$, $H = 3.0	ext{ m}$, $z = 0.75$.
* **Cited Source**: "NBCC Kidwai Nagar Redevelopment EIA Drainage Study / IITD DMP Reach C".
* **Forensic Finding**:
  * The NBCC East Kidwai Nagar EIA and SEIAA environmental clearance documents focus on on-site modular rainwater harvesting pits and internal colony drainage discharging to the adjacent MCD/PWD nallah. They do NOT publish an as-built cross-section of Kushak Nallah with $B = 10.0	ext{ m}, H = 3.0	ext{ m}$.
  * DMP 2018 contains no "Reach C".
* **Classification**: **`UNVERIFIED (CITATIONS ERRONEOUS); GEOMETRY IS ASSUMED / REGULARIZED`**.

#### 4. CS-04: INA Market / Aurobindo Marg Culvert Transition (Chainage 3,700.0 m)
* **Reported Location**: Upstream of Aurobindo Marg arterial road ($28.57650^\circ	ext{ N}, 77.21980^\circ	ext{ E}$).
* **Claimed Dimensions**: $B = 12.0	ext{ m}$, $W_{	ext{top}} = 16.0	ext{ m}$, $H = 3.2	ext{ m}$, $z = 0.60$.
* **Cited Source**: "PWD Delhi Aurobindo Marg Underpass Drainage Audit / IITD DMP Reach D".
* **Forensic Finding**:
  * PWD underpass drainage audit reports document waterlogging caused by backwater surcharging from Kushak Nallah, but do not provide a published engineering drawing tabulating $B = 12.0	ext{ m}, H = 3.2	ext{ m}$.
  * DMP 2018 contains no "Reach D".
* **Classification**: **`UNVERIFIED (CITATIONS ERRONEOUS); GEOMETRY IS ASSUMED / REGULARIZED`**.

#### 5. CS-05: Sewa Nagar Railway Bridge (Chainage 4,150.0 m)
* **Reported Location**: Northern Railway Ring Railway crossing ($28.57880^\circ	ext{ N}, 77.22210^\circ	ext{ E}$).
* **Claimed Dimensions**: $B = 14.0	ext{ m}$, $W_{	ext{top}} = 18.5	ext{ m}$, $H = 3.5	ext{ m}$, $z = 0.65$.
* **Cited Source**: "CPCB NWMP Drain #14 Station / Railway Bridge Clearance".
* **Forensic Finding**:
  * **CRITICAL SPATIAL MISATTRIBUTION**: In official CPCB/DPCC monitoring gazettes, **Drain #14 is the Barapullah outfall to the Yamuna River at Sarai Kale Khan / Nizamuddin**, situated $> 6	ext{ km}$ to the east ($28.585^\circ	ext{N}, 77.260^\circ	ext{E}$)!
  * CPCB has no water quality station at Sewa Nagar railway bridge on Kushak Nallah.
  * Attributing CPCB Drain #14 data to Sewa Nagar is a major spatial misattribution.
* **Classification**: **`UNVERIFIED (SPATIALLY MISATTRIBUTED CITATION); GEOMETRY IS ASSUMED / REGULARIZED`**.

#### 6. CS-06: South Extension Part-I (Chainage 4,550.0 m)
* **Reported Location**: North of South Extension-I running parallel to Barapullah elevated piers ($28.57960^\circ	ext{ N}, 77.22550^\circ	ext{ E}$).
* **Claimed Dimensions**: $B = 16.0	ext{ m}$, $W_{	ext{top}} = 21.0	ext{ m}$, $H = 3.8	ext{ m}$, $z = 0.65$.
* **Cited Source**: "PWD Barapullah Phase-I Drawings / IITD DMP Reach E".
* **Forensic Finding**:
  * Barapullah Phase-I elevated corridor runs from Sarai Kale Khan to JLN Stadium; Phase-II extends along the nallah towards INA. While construction drawings depict piers along the nallah reserve, specific transect $B = 16.0	ext{ m}, H = 3.8	ext{ m}$ is not from a published table.
  * DMP 2018 contains no "Reach E".
* **Classification**: **`UNVERIFIED (CITATIONS ERRONEOUS); GEOMETRY IS ASSUMED / REGULARIZED`**.

#### 7. CS-07: Defence Colony Outfall / Barapullah Confluence Head (Chainage 5,020.0 m)
* **Reported Location**: Mouth of Kushak Nallah at confluence with Sunehri Nallah ($28.57970^\circ	ext{ N}, 77.23630^\circ	ext{ E}$).
* **Claimed Dimensions**: $B = 18.0	ext{ m}$, $W_{	ext{top}} = 24.0	ext{ m}$, $H = 4.2	ext{ m}$, $z = 0.70$.
* **Cited Source**: "Delhi I&FC Barapullah Basin Outfall Schedule (Drain #14) & IIT Delhi DMP App. XII".
* **Forensic Finding**:
  * This is the confluence forming the main Barapullah Nala. Downstream, the main Barapullah channel expands to $30 - 40	ext{ m}$ and up to $100	ext{ m}$ near the Yamuna.
  * No specific "Appendix XII Outfall Schedule" tabulating $B = 18.0	ext{ m}, H = 4.2	ext{ m}$ for the Kushak mouth exists in DMP 2018.
* **Classification**: **`UNVERIFIED (CITATIONS ERRONEOUS); GEOMETRY IS ASSUMED / REGULARIZED`**.

---

### 2.2 Master Evidence Table (CS-01 through CS-07)

| Cross-Section ID | Station Chainage (m) | Claimed $B$ (m) | Claimed $H$ (m) | Forensic Provenance Classification | True Basis / Physical Evidence Status | Spatial Consistency Audit |
|:---:|:---:|:---:|:---:|:---:|---|---|
| **CS-01** | `2320.0` | $6.5$ | $2.5$ | **`ASSUMED`** (Specific) / **`OFFICIAL INDIRECT MATCH`** (Macro) | Synthesized regularized estimate. Follows macro $6 - 18	ext{ m}$ corridor range from PWD/I&FC affidavits. Cited table unlocated. | **MATCH**: Located on physical Kushak portal south of Ring Road. |
| **CS-02** | `2850.0` | $8.0$ | $2.8$ | **`ASSUMED`** (Specific) / **`OFFICIAL INDIRECT MATCH`** (Macro) | Synthesized regularized estimate. Cited DMP "Reach B" table unlocated. | **MATCH**: Located on Kushak channel at Safdarjung Airport south perimeter. |
| **CS-03** | `3350.0` | $10.0$ | $3.0$ | **`ASSUMED`** (Specific) / **`OFFICIAL INDIRECT MATCH`** (Macro) | Synthesized regularized estimate. NBCC EIA does not publish drain cross-sections; DMP lacks "Reach C". | **MATCH**: Located on Kushak channel at Kidwai Nagar West. |
| **CS-04** | `3700.0` | $12.0$ | $3.2$ | **`ASSUMED`** (Specific) / **`OFFICIAL INDIRECT MATCH`** (Macro) | Synthesized regularized estimate. PWD underpass audit has no cross-section table; DMP lacks "Reach D". | **MATCH**: Located on Kushak channel upstream of Aurobindo Marg culvert. |
| **CS-05** | `4150.0` | $14.0$ | $3.5$ | **`ASSUMED`** (Specific) / **`UNVERIFIED CITATION`** | Synthesized regularized estimate. Cited "CPCB NWMP Drain #14" is a **SPATIAL MISATTRIBUTION** to Barapullah Yamuna outfall. | **SPATIAL MISATTRIBUTION FLAGGED**: CPCB Drain #14 is $>6	ext{ km}$ downstream. Physical point is on Kushak. |
| **CS-06** | `4550.0` | $16.0$ | $3.8$ | **`ASSUMED`** (Specific) / **`OFFICIAL INDIRECT MATCH`** (Macro) | Synthesized regularized estimate. Cited DMP "Reach E" table unlocated. | **MATCH**: Located on Kushak channel north of South Extension-I. |
| **CS-07** | `5020.0` | $18.0$ | $4.2$ | **`ASSUMED`** (Specific) / **`OFFICIAL INDIRECT MATCH`** (Macro) | Synthesized regularized estimate. Cited DMP "App. XII Outfall Schedule" unlocated. Downstream channel widens to $30 - 40	ext{ m}$. | **MATCH**: Located on Kushak mouth immediately upstream of Sunehri confluence. |

*Summary*: Exactly **0 out of 7 cross-sections** represent a verified direct match to an official tabular survey. All 7 are **`ASSUMED / REGULARIZED`** geometric interpolations anchored to an **`OFFICIAL / OBSERVED — INDIRECT MATCH`** macroscopic width range ($6.0	ext{ m} - 18.0	ext{ m}$).

---

## 3. Scientific Audit of the Invert Derivation Methodology ($Z_{	ext{bed}} = Z_{	ext{bank}} - H$)

The previous methodology derived channel bed elevations by subtracting the nominal wall depth $H$ from the conditioned Copernicus GLO-30 DSM bank elevation:
$$Z_{	ext{bed}} = Z_{	ext{bank}} - H$$
with a monotonic downward gradient constraint ($S_0 \ge 0.0003$).

### Forensic Scientific Critique
1. **Nature of Copernicus GLO-30 DSM**:
   * Copernicus GLO-30 is a **Digital Surface Model (DSM)** with a nominal $30	ext{ m}$ pixel posting.
   * In dense urban corridors like South Delhi, a $30	ext{ m} 	imes 30	ext{ m}$ pixel covers $900	ext{ m}^2$, averaging canal retaining walls, water surfaces, roadway asphalt, footpaths, tree canopies, and adjacent building parapets.
   * As proven in our longitudinal profile audit, raw DSM elevations spike by $+3	ext{ m}$ to $+6.5	ext{ m}$ at bridge crossings and elevated road decks.
2. **Nature of Wall Depth $H$**:
   * $H$ ($2.5	ext{ m}$ to $4.2	ext{ m}$) is a nominal structural dimension from regional engineering descriptions, NOT a geodetic elevation referenced to Mean Sea Level (MSL).
3. **Scientific Invalidation of Direct Invert Equivalence**:
   * Subtracting a nominal wall depth $H$ from a noisy $30	ext{ m}$ satellite DSM surface does **NOT** produce the true hydraulic invert level.
   * Civil drainage engineering requires total station / level surveys referencing official Survey of India Great Trigonometrical Survey (GTS) benchmarks.
   * Treating $Z_{	ext{bank}} - H$ as a surveyed invert is scientifically invalid and creates false precision.
4. **Mandatory Methodological Classification**:
   * All open-channel bed elevations derived via this approach are re-classified as:
     **`DERIVED (UNVALIDATED SYNTHETIC OFFSET, ±1.0m to ±1.5m VERTICAL UNCERTAINTY)`**.
   * They must **NEVER** be treated as surveyed geodetic invert benchmarks.

---

## 4. Independent Verification of Manning's Roughness Parameters

An independent verification of the IIT Delhi *Drainage Master Plan for NCT of Delhi (2018)* was conducted:

* **Document**: *Drainage Master Plan for NCT of Delhi* (July 2018)
* **Author / Issuing Body**: Prepared by IIT Delhi (Prof. A.K. Gosain et al.) for Department of Irrigation & Flood Control, Govt. of NCT of Delhi.
* **Exact Location**: **Chapter 4, Section 4.1, Table 4.1-3, Page 109** (entitled *"Manning’s Roughness Coefficient considered in the study"*).

### Table 4.1-3 Verified Values
| Drain Typology | Prescribed Manning's $n$ | Verified Source | Formal Provenance |
|---|:---:|---|:---:|
| **Impervious smooth surface** | **`0.014`** | DMP 2018, Ch. 4.1, Table 4.1-3, Page 109 | `OFFICIAL / MODEL VALUE (DIRECT MATCH)` |
| **RCC Box Drain** | **`0.012`** | DMP 2018, Ch. 4.1, Table 4.1-3, Page 109 | `OFFICIAL / MODEL VALUE (DIRECT MATCH)` |
| **Circular drain** | **`0.013`** | DMP 2018, Ch. 4.1, Table 4.1-3, Page 109 | `OFFICIAL / MODEL VALUE (DIRECT MATCH)` |
| **Irregular, open drain** | **`0.025`** | DMP 2018, Ch. 4.1, Table 4.1-3, Page 109 | `OFFICIAL / MODEL VALUE (DIRECT MATCH)` |

### Status of Operational Silted Roughness ($n = 0.028 - 0.035$)
* **Independent Verification**: Does **NOT** appear in Table 4.1-3 of DMP 2018.
* **Actual Origin**: Table 4.1-1 of DMP 2018 (overland flow on bare soil/gravel), CPHEEO Manual (2019), and NGT/High Court desilting affidavits describing heavy silt deposits.
* **Formal Classification**: **`ASSUMED (OPERATIONAL SENSITIVITY ONLY)`**. It must never be cited as an official Table 4.1-3 value.

---

## 5. Underground Corridor Inventory (Africa Avenue)

The $2,318.42	ext{ m}$ covered conduit beneath Africa Avenue remains strictly classified as:
* **Horizontal Alignment**: `OBSERVED / SECONDARY PHYSICAL EVIDENCE` (14 GPS vertices from OSM `Way 44351567`).
* **Daylight Junction**: `OBSERVED / SECONDARY PHYSICAL EVIDENCE` ($0.000	ext{ m}$ gap connection to open canal).
* **Internal Conduit Width**: **`UNKNOWN`** (candidate twin-box geometry is NOT a model input).
* **Internal Conduit Height**: **`UNKNOWN`** (unrecorded in public CAD).
* **Hydraulic Invert Profile**: **`UNKNOWN`** (cannot be inferred from street DSM).

---

## 6. Quality Assurance (QA) Checklist After Forensic Audit

- [x] **1. Complete Provenance Downgrade**: All 7 cross-sections updated from `OFFICIAL / OBSERVED` to `ASSUMED / REGULARIZED`.
- [x] **2. Retraction of Erroneous Citations**: Erroneous citations to "DMP Ch. 3.2.4 Reach A–E" and "Appendix XII" explicitly retracted and documented.
- [x] **3. Correction of Spatial Misattribution**: CPCB Drain #14 misattribution to Sewa Nagar formally retracted; documented as Barapullah Yamuna outfall.
- [x] **4. Invert Elevation Re-Classification**: Derived inverts re-classified as unvalidated synthetic offsets with $\pm 1.0	ext{ m}$ to $\pm 1.5	ext{ m}$ uncertainty.
- [x] **5. Independent Confirmation of Manning $n$**: Table 4.1-3 values ($0.012, 0.013, 0.014, 0.025$) verified with exact chapter, table, and page number.
- [x] **6. Underground Geometry Restraint**: Africa Avenue conduit dimensions and inverts preserved strictly as `UNKNOWN`.
- [x] **7. Basin Area Integrity**: Working model catchment preserved at **$27.664	ext{ km}^2$** (provisional); sensitivity preserved at **$28.402	ext{ km}^2$**.
- [x] **8. Zero Code Modification**: Raw DEM, Mumbai V1, and application source code untouched.

---

## 7. Deliverable Artifact Manifest

| File Path | Modality | Records / Features | Forensic Status |
|---|:---:|:---:|---|
| `data/delhi/derived/hydraulic/kushak_corridor_centerline.geojson` | Vector GeoJSON | 6 features | Verified alignment; segmented reaches. |
| `data/delhi/derived/hydraulic/kushak_longitudinal_profile.csv` | Tabular CSV | 206 rows | Open inverts tagged as UNVALIDATED SYNTHETIC OFFSET; underground inverts UNKNOWN. |
| `data/delhi/derived/hydraulic/kushak_cross_sections.geojson` | Vector GeoJSON | 7 features | All 7 transects downgraded to ASSUMED; erroneous citations retracted. |
| `data/delhi/derived/hydraulic/kushak_hydraulic_geometry_inventory.csv` | Tabular CSV | 8 rows | Master inventory with explicit forensic classifications and uncertainty notes. |
| `docs/DELHI_KUSHAK_HYDRAULIC_GEOMETRY.md` | Markdown Doc | Full Document | Forensic provenance audit report and specification. |
| `docs/DATA_PROVENANCE_MATRIX.md` | Markdown Doc | Full Matrix | Updated with ASSUMED regularized transect tags. |
| `data/delhi/derived/watershed/manifest.json` | JSON Manifest | v2.4.0 | Manifest updated with forensic audit findings. |

---

## 8. Unresolved Blockers & Next Single Step

### 8.1 Remaining Blockers
1. **True Surveyed Channel Cross-Sections**: Detailed total station cross-sections showing exact bottom widths, side wall slopes, and bank heights along the Kushak corridor exist only inside internal departmental CAD drawings of PWD/I&FC, not in public reports.
2. **True Geodetic Invert Benchmarks**: Millimeter-level invert levels relative to GTS datum are unavailable, requiring all 1D/2D hydraulic models to acknowledge $\pm 1.0	ext{ m}$ to $\pm 1.5	ext{ m}$ vertical uncertainty in bed slope.
3. **Africa Avenue Tunnel As-Built Geometry**: Internal barrel dimensions and invert slopes remain unrecorded.

### 8.2 Recommended Next Single Step
**Formally declare the regularized open-channel geometry (CS-01 to CS-07) and candidate Africa Avenue twin-box conduit ($2 	imes [3.0	ext{m} 	imes 2.5	ext{m}]$) as `ASSUMED / SENSITIVITY PARAMETERS`, and perform an analytical hydraulic sensitivity analysis (evaluating $\pm 20\%$ channel width, $\pm 0.5	ext{m}$ invert offset, and $n = 0.025 	ext{ vs } 0.035$) to establish how sensitive backwater flood depths are to geometric uncertainty.**
