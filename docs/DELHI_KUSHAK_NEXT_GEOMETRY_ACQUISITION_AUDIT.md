# Kushak Nallah Hydraulic Geometry Acquisition Audit

**Document ID:** `DELHI_KUSHAK_NEXT_GEOMETRY_ACQUISITION_AUDIT`  
**Date:** 2026-09-12  
**Mission:** Forensic investigation to determine whether actual measured or as-built Kushak Nallah hydraulic geometry can be obtained through legitimate public or institutional routes.  
**Scope Boundaries:** Read-only forensic audit. No code, model, solver, or pipeline modification. No dimension fabrication or geometric interpolation. Provenance rules strictly maintained.

---

## 1. Executive Summary & Status

| Category | Finding | Scientific Status |
| :--- | :--- | :--- |
| **ACTUAL_MEASURED_DATA** | **NONE FOUND** on public channels. No instrumented survey (DGPS point clouds, echo-sounder bathymetric profiles, continuous station cross-sections, measured invert RLs) has been placed in the public domain. | **FAIL** (Cannot integrate into 1D solver) |
| **AS_BUILT_ENGINEERING_RECORD** | **PARTIAL (Structural dimensions only).** NGT Joint Inspection Report (05-03-2025) provides structural geometry for the ~1.0 km Bus Depot box section (50 m width, 5 equal bays of ~10 m each, 3.5–4.5 m depth, 1.5×1.5 m accesses, 2.50×1.15 m silt chambers). No continuous invert profile or bed level table. | **BOUNDS ONLY** |
| **PROCUREMENT_SPECIFICATION** | **VERIFIED.** I&FC NIQ No. `EE-CDXII/NIQ/2025-26/249` (08-10-2025) and NDMC NIT No. `52/EE(R-III)/2025-26` (Tender ID `2026_NDMC_297503_1`) mandate DGPS + echo sounding and 290 m robotic sonar profiling respectively. | **SCOPE ONLY** (Not measured data) |
| **Execution Status** | NDMC NIT-52 is **PRE-AWARD** (bids open 17-Sep-2026; no contractor exists). I&FC NIQ-249 award/deliverable was **NEVER PUBLISHED** online or annexed to court filings. | **NOT EXECUTED / UNPUBLISHED** |
| **Hydraulic Integration** | **BLOCKED.** Real Kushak geometry cannot be integrated into the numerical solver without committing severe scientific falsification. | **STOP — DO NOT IMPLEMENT CODE** |

---

## 2. Priority Evidence Investigations

### Priority 1: I&FC DGPS + Echo-Sounder Survey (NIQ No. EE-CDXII/NIQ/2025-26/249)

* **Issuing Authority:** Executive Engineer, Civil Division No.-XII, Irrigation & Flood Control Department, GNCTD, Basaidarapur Office Complex, New Delhi – 110027 (`ifccdxii@gmail.com`, 011-25172699).
* **Document Acquired:** `ifc_niq_cdxii_20251008_dgps_echo_survey.pdf` (SHA-256: `be81761359eca84b134349241834d3a2918f81e58895503ac8d95cb614b6c62d`).
* **Origin Directive:** National Green Tribunal (NGT) Principal Bench, OA 6/2012, Order dated 06-08-2024, endorsing the Chief Secretary (GNCTD) affidavit: *"A bathymetric survey of the Barapullah drain (including its subsidiary drains viz. Sunehripul drain and Kushak drain) may be undertaken by the IFCD within a months' time."*
* **Date of Issue:** 08-10-2025. Sealed quotations invited from enlisted contractors to be submitted by 10-10-2025 at 14:00 and opened on 10-10-2025 at 15:00.
* **Tendered Scope:** Item 1: *"Bathymetry/Topographical Survey & Hydrographical Survey by the latest survey instruments i.e. DGPS machine and Eco sounder etc. of Sunheripul Drain, Kushak Drain and Bijwasan Drain under the jurisdiction of Civil Division No. XII."* Note 3: *"The work is of Urgent nature and to be completed within 03 days only."*
* **Execution Audit (Has it actually been executed?):**
  * Minor quotation works (< ₹5 lakh) in I&FC are processed through offline sealed envelopes at the division office and are not indexed on NicGeP award-of-contract (AOC) lists.
  * The parallel audit lead of *"Aar Pee Electrical Engineering Works, 12-11-2024, ₹2.45 lakh"* was forensically audited and **REJECTED / DOWNGRADED TO LEAD_ONLY**: Public commercial registers show Aar Pee is an electrical goods manufacturer (stabilizers/transformers) without hydrographic survey registration, and no primary government AOC exists.
  * Subsequent NGT filings (orders of 21-11-2024, 09-04-2025, 23-04-2025, 14-10-2025) and Delhi High Court contempt proceedings (`CONT.CAS(C) 434/2022`, order 29-01-2026) report desilting progress (e.g. 10,747 m³ silt, 4,000 m³ removed) and administrative walk-throughs, but **NEVER annex or cite a completed bathymetric survey report or cross-section drawing**.
  * **Finding:** The survey was commissioned via NIQ, but its physical execution remains unconfirmed in public records, and its deliverables (if completed) are retained exclusively within the internal departmental archives of Civil Division-XII.
* **Classification:** `PROCUREMENT_SPECIFICATION` (Notice); `NOT_FOUND` (Deliverables on public channels).

---

### Priority 2: NDMC Kushak Desilting & Survey Procurement (NIT-52 / 2026_NDMC_297503_1)

* **Issuing Authority:** Executive Engineer (R-III), Civil Engineering Department, New Delhi Municipal Council, Room 306, SBS Place, Gole Market, New Delhi – 110001.
* **Tender Package Acquired:** `work_396329.zip` (SHA-256: `ba3067a1cae7a331f45f2f98e07d0ef1ed07f955be0d23871dda3028ca7054e0`).
  * `ndmc_nit52_2026_tender_notice.pdf` (121 pages; SHA-256: `0e45504ab1a40f09988c90f83936aa692cdbb9c98f86a216472baf578a4bee4f`).
  * `ndmc_nit52_2026_boq.xls` (285,184 bytes; SHA-256: `2eda2b0c426c5b5d57f5cdf97f9f97e9c11e9d9fb9ee0242416658a53f4918e5`).
* **Timeline Audit:** Published on 24-Aug-2026; Pre-bid meeting held 03-Sep-2026; Document download / Bid submission closing date: **17-Sep-2026 at 15:30**; Bid opening: **17-Sep-2026 at 16:00**.
* **Current Operational Status (as of 12-Sep-2026):** **PRE-AWARD ACTIVE TENDER.** Bids have not closed or opened. No contractor has been selected or awarded.
* **Execution Audit:** The survey has **NOT been executed**. The acoustic sonar profiling is a contractual deliverable to be executed by the successful bidder *during* the 12-month contract period.
* **Survey Scope in Package:** Schedule of Quantities (SOQ) Item 2: Mandates 290.00 m of *"Robotic Silt-Level-Estimation using Acoustic Profiling (Sonar Method) for inspection, diameter measurement, and conditional assessment of the drains without stopping the flow"* with electronic reporting via Pipescape software.
* **Engineering Geometry Content:**
  * SOQ Item 1 specifies barrel size class: *"RCC covered Kushak Nallah and Ring Road Nallah... width 4.00 meter +25% wide in size"*.
  * Total silt quantity: 21,406.00 m³ (billing volume post-draining with 25% void deduction).
  * RCC slab cutting thickness: 8–12 inch (203–305 mm).
  * **Drawings:** 0 longitudinal profiles, 0 cross-sections, 0 invert levels in the public package. CPWD standard conditions specify that engineering drawings are available for physical inspection in the office of Executive Engineer (R-III).
* **Predecessor Tender (NIT-51/EE(R-III)/2020-21):** *"Conducting Of Detailed Topographical Survey Of Kushak Nallah From S.P Marg To Satya Sadan / Lodhi Colony"*. Deliverables (L-sections, CAD drawings, bench marks) were retained internally and never published on open portals.
* **Classification:** `PROCUREMENT_SPECIFICATION` (Tender Package); `INACCESSIBLE_BUT_VERIFIED_RECORD` (Office drawings).

---

### Priority 3: Actual Survey Contractor Identity

| Procurement | Contractor Identity Status | Evidence / Verification Trail |
| :--- | :--- | :--- |
| **I&FC NIQ-249 (Oct 2025)** | **UNKNOWN** | Offline sealed quotation opening. "Aar Pee Electrical Engineering Works" lead rejected due to business mismatch (electrical goods) and lack of official AOC document. |
| **NDMC NIT-52 (Aug/Sep 2026)** | **NO CONTRACTOR EXISTS YET** | Tender is currently in bidding stage (closes 17-Sep-2026). Contractor identity will only emerge post-evaluation. |
| **NDMC NIT-51 (2020-21 Survey)** | **UNKNOWN** | Award records absent from public portals; consultancy deliverables held in physical divisional archives. |

*Finding:* No survey contractor identity can be legitimately established on public channels without guessing or violating anti-fabrication rules.

---

### Priority 4: NGT & High Court Filings

#### A. NGT OA 6/2012 — Order dated 09-04-2025 (Joint Inspection Report of 05-03-2025)
* **Issuing Authority:** National Green Tribunal, Principal Bench, New Delhi (quoting Joint Inspection Committee of Chief Engineers, MCD and I&FC).
* **Acquired Document:** `ngt_oa6_2012_order_20250409_joint_inspection_report.html` (SHA-256: `11032b0feffca0b05b5327299a9cf5c635d8e7cffc82a5f560e7e1a3bc330691`).
* **Reach / Location:** Covered portion of Kushak Nallah at Kushak Bus Depot (near JLN Stadium).
* **Measured / Observed Dimensions:**
  * Covered reach length: ~1.0 km.
  * Structure Type: Multi-cell RCC box structure, total width **50 m**, consisting of **5 equal bays** (~10 m clear span per bay).
  * Approximate Box Depth: **3.5 m to 4.5 m** (visual assessment).
  * Intermediate Access Openings: 1.5 m × 1.5 m openings at 50 m center-to-center intervals along RHS box (covered by Bus Depot parking, vent pipes remaining).
  * Silt Chambers: 2.50 m × 1.15 m constructed @ 100 m intervals.
  * Hydraulic & Sediment Condition: Minimal dry-weather flow (~1 ft / 0.3 m) flowing through only 2 out of 5 bays. At downstream exit, thick silt deposit across all 5 bays visually assessed between **1.5 ft and 3 ft (0.45 m to 0.9 m)** depth.
* **Classification:** `INDIRECT_EVIDENCE` / `COURT_NGT_RECORD` (Field inspection physical observation; provides structural bounds, but not instrumented cross-section coordinates or invert levels).

#### B. Delhi High Court — CONT.CAS(C) 434/2022 (Order dated 29-01-2026, Status Report dated 28-01-2026)
* **Authority:** High Court of Delhi (*Sunayana Sibal & Anr.*). Inspection conducted 21-01-2026 by joint team of NDMC, I&FC, and MCD.
* **Reach / Location:** Kushak Nallah from INA Market to Lala Lajpat Rai Marg.
* **Measured Segment Lengths:**
  * Total corridor length: **≈ 2.62 km**.
  * Reach 1 (INA to Kushak Bus Depot): **1.75 km** (MCD transferred to I&FC on "as-is where-is" basis).
  * Reach 2 (Kushak Bus Depot): **1.0 km** (in possession of MCD/DTC).
  * Reach 3 (Kushak Bus Depot to Lala Lajpat Rai Marg): **0.87 km** (open reach handed over to I&FC).
* **Hydraulic Risk Finding:** Proposed iron trash screen / grill across the drain was formally rejected by engineers due to extreme clogging risk and catastrophic backwater flooding into NDMC upstream drains.
* **Classification:** `INDIRECT_EVIDENCE` / `COURT_RECORD` (Definitive administrative chainage segmentation; no cross-sections).

#### C. NGT OA 6/2012 — Order dated 06-08-2024
* **Acquired Document:** `ngt_oa6_2012_order_20240806_bathymetry_directive.html` (SHA-256: `db57a314ac57d140b070498bfe1b9d4ba0156dcbeea728f32c1cff5ce7fce95a`).
* **Bottleneck Geometry:** Kushak Drain culvert below Lala Lajpat Rai Road: Consists of 5 structural bays; 2 bays completely blocked by C&D waste and silt; flow restricted to only 3 bays.
* **Classification:** `INDIRECT_EVIDENCE`.

---

### Priority 5: NDMC & I&FC Technical Documents

* **MPD 1976 Drainage Register (`ifc_drains_register_mpd1976.pdf`):** Documents 1976 historical drain parameters (lengths, catchment area, nominal capacity in cusecs). Outdated by 50 years of urban modification; contains no modern as-built invert levels. Classification: `HISTORICAL_RECORD`.
* **NDMC Sub-City Plan 2007:** Mentions INTACH bio-drainage proposals. No hydraulic cross-sections. Classification: `PLANNING_DOCUMENT`.
* **NDMC Council Minutes (28-02-2024):** Approves administrative sanctions for sewerage works; mentions 1905 mm brick barrel CCTV survey by TTI Environment & Services. Kushak main drain invert profiles absent. Classification: `OFFICIAL_RECORD`.

---

### Priority 6: Academic & Institutional Material (IIT Delhi / IIT Kanpur / cGanga)

#### A. IIT Delhi — Drainage Master Plan for Delhi (DMP 2018)
* **Documents:** DMP 2018 Main Report & Appendix XII (`appendixxii.pdf` / `appendixxii.txt`).
* **Content:** Contains 84 nodes and 281 conduit edges covering the Kushak basin. Formulates 1D SWMM/HEC-RAS model inputs with assigned invert levels, nominal bed slopes, design discharges ($Q_{10}$, $Q_{50}$), and idealized rectangular/trapezoidal channels (e.g. 25 m top width, 10 m base width).
* **Provenance Audit:** These geometry parameters were derived from historical 1976 registers and coarse topographic contours to establish baseline drainage capacity. They are **NOT** modern as-built field survey cross-sections.
* **Classification:** `MODEL_VALUE` (Must NOT be treated as actual measured geometry).

#### B. cGanga / IIT Kanpur — Kushak Flow Assessment Study (2023–2024)
* **Authority:** Centre for Ganga River Basin Management & Studies (cGanga), IIT Kanpur (Prof. Vinod Tare / Prof. Purnendu Bose). Commissioned by NDMC Sewerage Project Division (File No. `V-16027/55/2024`, Council Item 21, 28-02-2024).
* **Scope:** Study and prepare flow data and wastewater characteristics for open reach from Sardar Patel Marg to Kamal Ataturk Marg.
* **Reported Value:** Average dry-weather flow observed at **≈ 10 MLD** during non-rainy season.
* **Hydraulic Geometry Content:** The investigation focused on water quality and discharge characterization; no cross-sectional bathymetry or invert leveling was conducted. The final report was submitted separately to NDMC and has not been published online.
* **Classification:** `INDIRECT_EVIDENCE` (10 MLD baseflow anchor); `LEAD_ONLY` (Unpublished study report).

---

## 3. Comprehensive Source Classification Matrix

| Source / Document | Authority | Date | Classification | Public Access | Hydraulic Value |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **I&FC NIQ EE-CDXII/NIQ/2025-26/249** | I&FC CD-XII | 2025-10-08 | `PROCUREMENT_SPECIFICATION` | YES (PDF acquired) | Survey scope & instrumentation (DGPS + Echo sounder) |
| **I&FC CD-XII Survey Deliverables** | I&FC CD-XII | 2025/2026 | `NOT_FOUND` / `INACCESSIBLE_BUT_VERIFIED_RECORD` | NO | Unreleased bathymetric points and cross-sections |
| **NDMC NIT 52/EE(R-III)/2025-26** | NDMC R-III | 2026-08-24 | `PROCUREMENT_SPECIFICATION` | YES (Zip acquired) | Silt volume (21,406 m³), size class (4.0m +25%), sonar scope (290m) |
| **NDMC R-III As-Built CAD Drawings** | NDMC R-III | Ongoing | `INACCESSIBLE_BUT_VERIFIED_RECORD` | NO (Office only) | As-built L-sections, invert RLs, cross-sections |
| **NGT JIR Order (09-04-2025)** | NGT / MCD / I&FC | 2025-04-09 | `INDIRECT_EVIDENCE` | YES (HTML acquired) | Bus Depot box: 50m wide, 5 bays, 3.5–4.5m depth, 1.5–3ft silt |
| **Delhi HC CONT.CAS(C) 434/2022** | Delhi HC | 2026-01-29 | `INDIRECT_EVIDENCE` | YES (Public order) | INA→LLRM reach lengths: 1.75km, 1.0km, 0.87km (total 2.62km) |
| **NGT Order (06-08-2024)** | NGT | 2024-08-06 | `INDIRECT_EVIDENCE` | YES (HTML acquired) | LLRM culvert 5 bays (2 blocked); survey directive |
| **IITD DMP 2018 Appendix XII** | IIT Delhi | 2018 | `MODEL_VALUE` | YES (PDF on disk) | Theoretical 1D model parameters (25m/10m idealized channels) |
| **cGanga / IIT-K Flow Study** | cGanga / IITK | 2024-02-28 | `LEAD_ONLY` / `INDIRECT_EVIDENCE` | NO (Council quote only) | Dry-weather baseflow ≈ 10 MLD (SP Marg to Kamal Ataturk) |
| **MPD 1976 Drain Register** | Delhi DDA/IFC | 1976 | `HISTORICAL_RECORD` | YES (PDF on disk) | 50-year-old nominal lengths & discharge capacities |

---

## 4. Inaccessible but Verified Records & Strongest Acquisition Routes

| Record Title | Legal Custodian | Tender / File Reference | Strongest Legitimate Access Route |
| :--- | :--- | :--- | :--- |
| **Kushak As-Built L-Sections, Invert Registers & Cross-Section Drawings** | Executive Engineer (R-III), Civil Engineering Dept., NDMC, Room 306, SBS Place, Gole Market, New Delhi – 110001 | NIT No. `52/EE(R-III)/2025-26` / NIT No. `51/EE(R-III)/2020-21` | **Statutory RTI Application** to PIO / EE (R-III), NDMC. (Alternative: Prospective bidder physical inspection under CPWD clause). |
| **Hydrographic & Bathymetric Survey Deliverables (DGPS + Echo Sounder)** | Executive Engineer, Civil Division No.-XII, I&FC Dept., Basaidarapur Office Complex, New Delhi – 110027 | NIQ No. `EE-CDXII/NIQ/2025-26/249` dated 08-10-2025 | **Statutory RTI Application** to PIO / EE, CD-XII, I&FC. (Alternative: Institutional data-sharing request via Delhi Disaster Management Authority). |
| **cGanga Kushak Flow-Assessment Final Report** | Executive Engineer, Sewerage Project Division, NDMC / Prof. Purnendu Bose, Civil Eng., IIT Kanpur | NDMC File No. `V-16027/55/2024/Sewerage-Project` (Council Item 21) | **Academic Research Request** to cGanga / IIT Kanpur PI (`pbose@iitk.ac.in`). (Alternative: RTI to NDMC Sewerage Project Division). |
| **Robotic Pipescape Sonar Silt-Level Survey (290 m)** | Future awarded contractor / NDMC R-III | SOQ Item 2 of Tender ID `2026_NDMC_297503_1` | **Post-Award Monitoring:** Monitor tender opening on/after 17-Sep-2026, identify L1 contractor, and submit voluntary research request. |

---

## 5. Acquired Files & Cryptographic Hashes

All newly acquired and organized candidate artifacts are archived under:  
`data/delhi/raw/hydraulic/acquisition_candidates/`

Manifest file: `data/delhi/raw/hydraulic/acquisition_candidates/manifest.json`

| File Name | Authority | Date | Classification | SHA-256 Hash |
| :--- | :--- | :--- | :--- | :--- |
| `ifc_niq_cdxii_20251008_dgps_echo_survey.pdf` | I&FC Civil Division-XII | 2025-10-08 | `PROCUREMENT_SPECIFICATION` | `be81761359eca84b134349241834d3a2918f81e58895503ac8d95cb614b6c62d` |
| `ndmc_nit52_2026_tender_notice.pdf` | NDMC Roads-III | 2026-08-24 | `PROCUREMENT_SPECIFICATION` | `0e45504ab1a40f09988c90f83936aa692cdbb9c98f86a216472baf578a4bee4f` |
| `ndmc_nit52_2026_boq.xls` | NDMC Roads-III | 2026-08-24 | `PROCUREMENT_SPECIFICATION` | `2eda2b0c426c5b5d57f5cdf97f9f97e9c11e9d9fb9ee0242416658a53f4918e5` |
| `ngt_oa6_2012_order_20240806_bathymetry_directive.html` | National Green Tribunal | 2024-08-06 | `INDIRECT_EVIDENCE` | `db57a314ac57d140b070498bfe1b9d4ba0156dcbeea728f32c1cff5ce7fce95a` |
| `ngt_oa6_2012_order_20250409_joint_inspection_report.html` | National Green Tribunal | 2025-04-09 | `INDIRECT_EVIDENCE` | `11032b0feffca0b05b5327299a9cf5c635d8e7cffc82a5f560e7e1a3bc330691` |

---

## 6. Exact Remaining Hydraulic Geometry Gaps

| Gap ID | Engineering Hydraulic Parameter | Public Status | Can Public Data Close It? |
| :--- | :--- | :--- | :--- |
| **P0-1** | **Longitudinal Invert Profile** (Bed RLs at continuous chainages) | Inaccessible (Held in NDMC R-III / I&FC CD-XII archives) | **NO** |
| **P0-2** | **Modern Measured Cross-Sections** (Open reaches: INA to LLRM) | Inaccessible (Unpublished survey deliverables) | **NO** |
| **P0-3** | **Africa Avenue Subterranean Conduit Geometry** (Clear width, height, invert) | Inaccessible (NDMC covered trunk records) | **NO** |
| **P0-4** | **Culvert & Bridge Apertures** (Kamal Ataturk, Africa Ave, Brig Hoshiyar Singh, LLRM) | Inaccessible (Structural bridge registers) | **NO** |
| **P0-5** | **Certified Vertical Datum** (GTS / MSL Benchmark references) | Inaccessible (Survey control registers) | **NO** |

---

## 7. Operational Verdict: Can Real Geometry Be Integrated Now?

### **NO.**

**Scientific Rationale:**
1. **Zero Measured Bed Levels:** Public web archives contain notices, scope items, and court observations, but **zero tabular invert elevations or station coordinates**.
2. **Model Values vs As-Built:** The DMP 2018 Appendix XII numbers are idealized model design inputs ($25\text{ m} \times 10\text{ m}$ trapezoidal), not as-built measurements. Treating them as measured ground truth would violate hydraulic engineering integrity.
3. **Severe Conflict:** Field inspection observations in NGT records document a 50 m wide 5-bay box with 3.5–4.5 m depth, whereas DMP-2018 assumes idealized trapezoidal/rectangular sections with depths over 7 m. Inverting a numerical hydraulic solver on unresolved geometry creates meaningless water level predictions.

---

## 8. Blockers & Final Directive

* **Blocker 1:** Municipal engineering records (AutoCAD `.dwg` files, L-sections, leveling books) are retained exclusively within physical government divisional offices in Delhi and are not hosted on open web portals.
* **Blocker 2:** Active procurement state of NDMC NIT-52 means that actual robotic acoustic sonar profiling deliverables will only come into existence during future contract execution.
* **Blocker 3:** Legitimate access requires statutory RTI filing or formal institutional data-sharing requests to NDMC and I&FC.

### **STOP — DO NOT IMPLEMENT HYDRAULIC CODE.**
No solver, mathematical interpolation, or production code modification may proceed until certified as-built geometry is formally acquired through institutional or RTI channels.

---

## 9. Addendum — Independent verification probes (2026-09-12, later session)

The following additional probes were executed in a separate verification pass and are consistent with the audit above:

1. **I&FC "Work Under Execution" (CD-XII entry)** — `ifc.delhi.gov.in/ifc/work-under-execution`: the CD-XII entry links only to Flood Control Order PDFs (`fco_6.pdf`/`fco_7.pdf`, byte-identical captures, **no text layer**, zero Kushak/bathymetry content). No survey-execution record.
2. **I&FC documents repository** — `ifc.delhi.gov.in/ifc/documents` and variants: 404 / no document listing exposed. The "INTACH Reports" section remains an empty shell.
3. **Indian Kanoon post-Aug-2025 searches** ("Kushak" + "survey", most-recent, pages 1–2 of 28): **no NGT/court document after 20-08-2025 carries Kushak survey findings**, the 870-m affidavit, or DGPS/echo-sounder results. The only post-Aug-2025 hit (Khushnuma Khan, Delhi HC 11-05-2026) is unrelated. Additional find: Delhi HC *Court On Its Own Motion* order 28-02-2025 in **W.P.(C) 7594/2018** records the Defence Colony drain (1600 m, 1300 m covered, DDA→MCD 2020) joint survey and a DMRC "113 m long drain under Aurobindo Marg" — adjacent-system context only, no Kushak sections.
4. **NIT-52 state re-confirmed on the official portal** (in-browser session 12-09-2026): published 24-Aug-2026 05:15 PM; document download window to 17-Sep-2026 03:30 PM; bid opening 17-Sep-2026 04:00 PM; pre-bid 03-Sep-2026. Package files: `Tendernotice_1.pdf`, `NIT.pdf`, `BOQ_396329.xls` (zip `work_396329.zip`).
5. **Cross-reference to the Phase 7D-16 effective-conveyance feasibility study** (`data/delhi/derived/research/phase7d16/`): the bounded effective-parameter approach remains the only defensible hydraulic representation until a surveyed deliverable is obtained; its depot-reach diagnostic (main-conduit capacity cannot explain depot-area street flooding within official bounds) adds a mechanism finding that any future survey should be checked against.
6. **Cross-reference to Phase 7E** (`docs/DELHI_KUSHAK_PHASE7E_...`): the I&FC drain-discharge archive precedent (Kumar–Kaushal–Gosain 2018, daily discharge 2005–2013 for the Jahangirpuri drain) supports a non-RTI research route to I&FC records, to be combined with the RTI fallbacks in §4.
