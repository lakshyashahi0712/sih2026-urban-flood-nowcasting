# Phase 7E — Kushak Continuous Hydraulic Observation Acquisition Research

**Document ID:** `DELHI_KUSHAK_PHASE7E_CONTINUOUS_HYDRAULIC_OBSERVATION_ACQUISITION`
**Date:** 2026-09-12
**Type:** read-only acquisition research. No RTI, no contact, no production code or model changes. Scope: direct hydraulic observations of **Kushak Nallah** (stage/discharge/velocity/logger/cross-section/bathymetry/survey) not already conclusively captured in Phases 6A–6E and 7D-15/16. Occurrence-only, DEM/OSM, CWC-ORB, and procurement-specification items are excluded per mission rules.

---

## 1. SEARCH SUMMARY

Trails executed (scoped): CPCB/DPCC/NMCG drain inventories and outfall tables · DPCC Monthly Progress Reports · IIT Kanpur (cGanga site, sponsored-projects portal, consultancy lists) · IIT Delhi (iRIC paper line, institutional repository, thesis trail) · NGT/court records already on disk plus Indian Kanoon recent-order searches · press coverage of the ₹169.57–170 Cr Kushak rejuvenation.

**Bottom line: no continuous or discrete in-drain hydraulic observation (stage, discharge, velocity, section) for Kushak Nallah itself was found in any public source.** One genuinely new **access-system fact** was discovered (I&FC holds/supplies daily drain-discharge records), and one Phase 6A lead was resolved as a **misattribution**.

## 2. CANDIDATE CLASSIFICATION

### FOUND_BUT_INACCESSIBLE

| # | Record | What proves it exists | Custodian | Route |
|---|---|---|---|---|
| 1 | **cGanga/IIT-K Kushak flow-assessment final report** (flow data + wastewater characteristics, S.P. Marg→Kamal Ataturk Marg) | NDMC Council Item 21, 28-02-2024 (verified verbatim, Phase 6D): ₹7.375 lakh study "completed timely"; "the report of the assessment exercise is being submitted separately" (cGanga letter 21-02-2024, annexure p. 470) | NDMC Sewerage Project Division, File V-16027/55/2024; cGanga/IIT-K (PI Prof. Purnendu Bose, pbose@iitk.ac.in per IIT system portal) | Non-RTI: institutional research request (voluntary); council-agenda monitoring. RTI otherwise. |
| 2 | **IIT-K Phase-II implementation records** ("Novel Solution For Improving Water Quality Of Kushak Nallah In New Delhi", NDMC-sponsored, ongoing ₹169.57–170 Cr rejuvenation with SCR/SABRE 1×5 MLD + 2×2.5 MLD units) | IIT system portal entry #17; HT 12-04-2024; smartutilities 24-04-2024; Council Item 21 annexures | cGanga/IIT-K + NDMC | Design/commissioning documents may later include flow/quality monitoring of the implemented system — monitor. |
| 3 | **I&FC drain-discharge archive** (daily discharge records of Delhi stormwater drains) | Kumar, Kaushal & Gosain (2018), *J. Applied Research and Technology* 16:67–78 — IIT Delhi study of the **Jahangirpuri drain** used "daily discharge data of the drains from the year 2005 to 2013" supplied by the **I&FC Department** (open-access: SciELO S1665-64232018000100067; local extract `data/delhi/raw/official_docs/iric_kumar_kaushal.txt`) | I&FC GNCTD (hydrology/observation wing) | Non-RTI research route: request via I&FC/IIT-D collaboration pattern already demonstrated; establishes I&FC *does* release drain-discharge series to researchers for gauged drains. Whether **Kushak was ever gauged** is UNKNOWN — must be asked (RTI if refused). |

### INDIRECT_ONLY

| # | Record | Measured quantity | Why only indirect |
|---|---|---|---|
| 4 | **DPCC MPR Oct-2022, p. 31** — "Status of 18 Major Drains Directly Out Falling into River Yamuna": **Barapullah Drain 145.15 MLD (31.97 MGD)** (DJB); "trapping flow in Kushak drain at Andrews Ganj Pumping station have been completed… expected to reduce about **45.46 MLD (10 MGD)** flow in the Barapulla Drain. The remaining flow is expected to be around **68.91 to 90.92 MLD**" (on disk: `data/delhi/raw/pollution/dpcc_mpr_2022-10.pdf`) | Drain outfall discharge accounting (sewage-component estimates) | Barapullah-system level, not a Kushak measurement; values are DJB flow accounting/expectations, not gauge observations. Kushak is not separately listed (subidiary of Barapullah). |
| 5 | **DJB KD1–KD22 point-flow table** (NGT, DJB affidavit 19-08-2025; already held) | 22 Kushak-catchment sewage points, 0.006–11.5 MLD | Official estimates of sewage inflow points, not in-drain measurements. |
| 6 | **DPCC MPR Oct-2022, p. 15** — "waste water in Kushak Nala running through NDMC areas is under bio-remediation" | status only | Qualitative. |
| 7 | **CPCB 18/22-drain monitoring & outfall inventories** (PIB 19-01-2021; CPCB Apr-2020 inventory) | outfall WQ/discharge for major drains | Kushak not separately identified (subservient to Barapullah outfall). |
| 8 | **NMCG monthly progress reports** (18–22 outfall drains; tapping status) | tapping/treatment status | No Kushak in-drain measurement. |

### NOT_FOUND

| Target | Result |
|---|---|
| Kushak stage/staff-gauge/logger records (any agency) | NOT_FOUND |
| Kushak discharge/velocity measurements (any) | NOT_FOUND |
| "Amrita Mandal 2015 IIT-D thesis" on Kushak (Phase 6A lead) | **NOT_FOUND — misattribution.** The only indexed "Amrita Mandal" is a combinatorial-matrix-theory academic (NIT Agartala). The related IIT-D work is **Satish Kumar's study of the Jahangirpuri drain** (supervisors D.R. Kaushal & A.K. Gosain — the DMP-2018 faculty), published as the iRIC paper above. |
| Kushak bathymetry/sonar/DGPS outputs | NOT_FOUND (consistent with Phase 6E: commissioned, outputs not published) |
| Kushak hydraulic survey report / L-sections | NOT_FOUND (Phase 6E) |
| cGanga/IIT-K public copy of the flow report (incl. IIT-K repository, IWIS proceedings) | NOT_FOUND |
| Purnendu Bose / Vinod Tare publications describing Kushak measurements | NOT_FOUND (project ongoing; no public output located) |

## 3. THE NEW ACCESS-SYSTEM FACT (material)

**Kumar, S., Kaushal, D.R., Gosain, A.K. (2018), "Hydrodynamic simulation of urban stormwater drain (Delhi city, India) using iRIC Model", J. Applied Research and Technology 16(1):67–78** (open access: SciELO/jart.icat.unam.mx; authors are the DMP-2018 core faculty). Key verified content: 2D hydrodynamic (Nays2DFlood/iRIC) model of the **Jahangirpuri drain** (5,470 m, 18 m bed width, Najafgarh basin) built on a **GSDL 5×5 m DEM** and **I&FC-supplied daily discharge data 2005–2013**; Manning 0.025 from literature; **no formal calibration** (qualitative validation only). 

Relevance to Kushak: (a) it proves **I&FC maintains and releases daily drain-discharge series** for drains it gauges — the strongest available evidence that a data-request route to I&FC for drain hydraulic records is realistic; (b) it demonstrates the methodology class (2D effective hydraulic modelling on GSDL DEM with literature n) that IIT-D itself used for a Delhi drain under identical data constraints — directly parallel to the Phase 7D-16 effective approach.

## 4. DOES ANYTHING CHANGE THE PHASE 7D-16 RESULT?

**No.** No new Kushak-specific hydraulic observation was found; the identifiability conclusions and the Phase 7D-16 behavioral-envelope result stand unchanged. The one strengthening is prospective: the demonstrated I&FC data-release practice (item 3) raises the prior that an **I&FC drain-gauging archive request** (research/collaboration route, non-RTI-first) could surface Kushak discharge records *if any gauging ever existed* — currently UNKNOWN.

## 5. RECOMMENDED NEXT ACTION (one)

**Verify with I&FC (research/collaboration request, non-RTI-first) whether Kushak Nallah was ever gauged — citing the Kumar–Kaushal–Gosain (2018) precedent of I&FC releasing daily drain-discharge data (2005–2013) for the Jahangirpuri drain — and if gauging exists, request the series; escalate to RTI only on refusal.** (Single action; not executed.)

---

## Candidate inventory (machine-readable): `data/delhi/derived/research/phase7e/candidate_inventory.json`

*Anti-fabrication note: every claim above quotes or cites a located document; the iRIC paper's drain identity (Jahangirpuri, not Kushak) was verified against the paper's own text; no estimate was upgraded to a measurement; DPCC/Barapullah figures are recorded with their system-level caveat.*
