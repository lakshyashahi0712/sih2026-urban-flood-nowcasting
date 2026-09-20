# Phase 6B — Non-RTI Physical Data Acquisition Audit: Kushak Nallah

**Document ID:** `DELHI_KUSHAK_PHASE6B_NON_RTI_ACQUISITION_AUDIT`
**Date:** 2026-09-12
**Mission type:** forensic acquisition-path identification only. No RTI filed or drafted; no contact made; no hydraulic/model/solver/catchment/rainfall/historical-flood code or artifacts touched; Mumbai/Kurla V1 untouched.

**Inputs inspected (scoped):** `data/delhi/derived/research/kushak_current_geometry_audit.md` (the parallel Phase-6A acquisition audit), `data/delhi/raw/MANIFEST_CURRENT_GEOMETRY_20260912.json`, `data/delhi/derived/research/kushak_hydraulic_structure_inventory.md`, `data/delhi/raw/hydraulic/ndmc_nit_52_ee_r3_2025_26_kushak_desilting.txt`, `data/delhi/raw/drainage/ifc_niq_cdxii0810_survey.pdf`.

---

## 1. STATUS

**PARTIAL.** Acquisition paths for several records were identified and some *new official records were acquired outright* (Delhi HC January-2026 inspection order contents; NDMC budget line items; I&FC portal states). **No file containing instrumented survey data (bed levels, L-sections, cross-section sheets, sonar points) was found publicly downloadable anywhere.** Two claimed award/contractor facts could not be verified from primary sources and are downgraded to LEAD_ONLY.

## 2. ACTUAL DATA FOUND

| Dataset / record | Exact source | Date | Custodian | Spatial coverage | Data type | Actual measurements present? | Public download? | Provenance class |
|---|---|---|---|---|---|---|---|---|
| Joint Inspection Report of Kushak covered reach (5 bays, 50 m width, depth 3.5–4.5 m visual, openings 1.5×1.5 m @50 m, silt chambers 2.50×1.15 m @100 m, silt 1.5–3 ft) | NGT order 09-04-2025 (indiankanoon.org/doc/192522997), JIR of 05-03-2025, CEs MCD + I&FC | 05-03-2025 | NGT OA 6/2012 record | Kushak covered reach (~1 km, Bus Depot) | Field inspection record | Lengths/dimensions/bay counts/qualitative depths only — **no instrumented sections** | Yes (order text) | COURT_NGT_RECORD |
| **Delhi HC status report of 28-01-2026 + order 29-01-2026** (inspection of 21-01-2026 by NDMC/I&FC/MCD officers; signed Dr. Sanjeev Gupta, Dy Dir (VS), MCD) | indiankanoon.org/doc/125400451 — *Sunayana Sibal & Anr*, **CONT.CAS(C) 434/2022** (& connected 868/2022) | inspection 21-01-2026; report 28-01-2026; order 29-01-2026 | Delhi High Court | Kushak Nallah INA Market → Lala Lajpat Rai Marg | Official inspection report (cattle/dairy contempt matter) | **Lengths only: total ≈2.62 km; 1.75 km (INA→depot, MCD→I&FC "as-is where-is"); 1.0 km depot (MCD possession); 0.87 km (depot→LLRM, handed to I&FC)**; 7 illegal dairies INA→Gurjar Chowk; AIIMS-side covered NDMC drain is the cattle entry; iron-grill rejected over clogging/backwater risk | Yes (order text) | COURT_NGT_RECORD / OFFICIAL_RECORD |
| NIT-52 tender documents: NIT + BOQ (`work_384007.zip`) + drawings annexure | govtprocurement.delhi.gov.in, Tender ID `2026_NDMC_297503_1`, NIT **52/EE(R-III)/2025-26** | published 24-08-2026; bids close 17-09-2026 (BidEasy; repo text said 15-09 — portal is authoritative) | NDMC EE(R-III), Civil-I | RCC covered Kushak Nallah + Ring Road Nallah (R-III) | Procurement: BOQ (silt quantities per L-section), tender drawings **for bidder inspection only** | BOQ = quantities (not geometry); drawings = pre-bid inspection only | **Listed publicly; download CAPTCHA-gated** (verified 2026-09-12; not circumvented) | PROCUREMENT_RECORD |
| I&FC CD-XII hydrographic/topographic survey NIQ `EE/CD-XII/NIQ/2024-25` (Sunheripul + Kushak + Bijwasan, DGPS + echo sounder) | `ifc.delhi.gov.in` NIQ PDF (on disk: `ifc_niq_cdxii0810_survey.pdf`); NIQ listing page `ifc.delhi.gov.in/tender/niq-cd-xii` (checked 2026-09-12 — lists only the 19-08-2026 NIQ; no award history) | NIQ dated 08-10-2024; parallel audit states award 12-11-2024, ₹2.45 lakh, "Aar Pee Electrical Engineering Works" — **primary award document NOT located; NOT verified** | I&FC Civil Division-XII (EE Gagan Gaur; ifccdxii@gmail.com) | Sunheripul + Kushak + Bijwasan drains | Survey procurement | none public | NIQ yes; **survey report no** | PROCUREMENT_RECORD (NIQ) / **UNKNOWN** (award & output) |
| NDMC Budget 2021-22 Vol-II Kushak line items | ndmc.gov.in Budget 2021-22 Vol-II PDF (downloaded, hashed) | FY 2021-22 | NDMC Finance | 1905 mm barrel Khushak Nalah→Aurobindo Marg (₹13.86 Cr A/A&E/S; tender 08-02-2023); Arjun Dass Camp berms; Pillanji item = **horticulture gazebo, not the survey** | Budget record | amounts only | Yes | OFFICIAL_RECORD |
| NDMC Sewerage Project Division status table | ndmc.gov.in/departments/civil_i.aspx | 2023-24 targets | NDMC Sewerage Project Division | Sadar Bazar–Sant Path–Satya Sadan via Kushak Nallah (Phase-III, ₹9.27 Cr CIPP rehabilitation); 1905 mm barrel ₹13.86 Cr | Project status | "Technical bid of Pre & Post **Consultancy** work opened, under scrutiny" — consultant unnamed | Yes | OFFICIAL_RECORD |
| cGanga/IIT-K Kushak flow-assessment final report (₹7.375 lakh) | NDMC Council agenda 28-02-2024, Item 21 (report "received", submitted separately) | 2023-24 | NDMC Sewerage Project Division (File No. V-16027/55/2024/Sewerage-Project) | Kushak Nallah NDMC reaches | Flow survey report (dry-weather flow ≈10 MLD quoted in agenda) | report itself **not public** | No | LEAD_ONLY (report) / OFFICIAL_RECORD (agenda quote) |
| Financial-evaluation result, Tender ID `2026_NDMC_289211_1` (same NIT number 52/EE(R-III)/2025-26; relationship to `297503_1` **unresolved — not merged here**) | Tenderkart result page (value ₹12.79 Cr, updated 24-08-2026); contractor name not indexed anywhere | 24-08-2026 | NDMC / portal | R-III Kushak + Ring Road Nallah | Procurement result | none public | Aggregator-only; official "Results of Tenders" needs interactive portal session | LEAD_ONLY |

**Nothing in this table is ACTUAL_SURVEY_DATA.** No sonar/bathymetric point data, no instrumented cross-section, and no surveyed invert has surfaced in any public channel as of 2026-09-12.

## 3. PROCUREMENT CHAIN

| Chain | Status |
|---|---|
| **NIT-52** `52/EE(R-III)/2025-26` / `2026_NDMC_297503_1` (₹12.30 Cr desilting, robotic methods, 12-month) → NDMC EE(R-III) | **No corrigendum, no award, no L1 as of 2026-09-12** (bids close 17-09-2026). Pre-award: no contractor exists; BOQ/drawings gated by CAPTCHA (legitimate human step). Post-award route: official "Results of Tenders" on govtprocurement.delhi.gov.in (interactive session required; deep links are session-bound). |
| `2026_NDMC_289211_1` (same NIT number; aggregator financial result ₹12.79 Cr) | **Not merged with `297503_1`.** Either an earlier listing superseded by relisting, or aggregator artifact. Official portal required to disambiguate. |
| **NIT 51/EE(R-III)/2020-21** | **Not found.** No aggregator or official hit for a 2020-21 NIT with this number; NDMC 2020-21/2021-22 budget Vol-II Kushak items are horticulture/sewer works, not the survey. The "Detailed Topographical Survey, Geo-technical Investigation and DPR for Kushak Nallah (Pillanji Village/Chanakyapuri Reach)" budget line cited in earlier audits was **not located in Vol-II** — its consultancy award remains UNKNOWN. |
| **I&FC CD-XII survey NIQ (08-10-2024)** → (claimed) award 12-11-2024 ₹2.45 lakh → "Aar Pee Electrical Engineering Works" | Award claim **downgraded**: public identity of "Aar Pee Electrical Engineering Works" is an **electrical-goods manufacturer** (IndiaMART: stabilizers/voltmeters/transformers) — a name-only match to a survey contract fails the mission's contractor-class rule. No primary award document (AOC/work order) is on any fetched page. Chain status: NIQ = PROCUREMENT_RECORD; award = **UNKNOWN**; survey output = UNKNOWN (no report published). |
| NDMC Sewerage consultancies | (a) TTI Environment & Services — DPR consultant for the 1905 mm barrel incl. CCTV survey (Council Item 19; scanned minutes) — LEAD_ONLY; (b) Phase-III CIPP "Pre & Post Consultancy" — bid under scrutiny, consultant unnamed; (c) cGanga/IIT-K flow assessment — report received, not public. |

## 4. COURT / NGT CHAIN

| Chain | Engineering material actually obtainable? |
|---|---|
| NGT OA 6/2012: MCD status 17-11-2023 → JIR 05-03-2025 → MCD affidavit 22-04-2025 → DJB status 14-10-2025 | Yes (already acquired by parallel audit): structure bays/width/visual depth/openings/silt state + reach lengths. **No instrumented survey annexed in any fetched order.** |
| **Delhi HC `CONT.CAS(C) 434/2022` (Sibal) — orders 22-12-2025 / 16-01-2026 / 29-01-2026 / 18-02-2026** | Order of 29-01-2026 reproduces the 28-01-2026 status report **inline**: the 21-01-2026 inspection's content is the lengths/handover/dairy facts above. No annexure list, no photographs, no dimensions beyond lengths in the order text; full paper file (with the signed report) retrievable via Delhi HC record room / e-Inspection portal (dhcmisc.nic.in/inspection) — non-RTI judicial-record route. |
| Delhi HC W.P.(C) 7594/2018 (Barapullah) | Barapullah main drain only — digital survey plan + silt-volume report exist as exhibits but are **not Kushak**; not pursued further per scope. |
| Delhi HC W.P.(C) 4221/2024 (20-03-2024, Arora J.) — 1905 mm brick barrel rehabilitation | adjacent sewer line; no Kushak survey annexure located. |

## 5. CONTRACTOR / CONSULTANT LEADS (verified identities only; uncertainty marked)

| Identity | Role (evidence) | Confidence | Public contact/research route |
|---|---|---|---|
| **cGanga (Centre for Ganga River Basin Management & Studies), IIT Kanpur** | Consultant for Kushak Nallah flow assessment (NDMC Council Item 21, 28-02-2024; report received by NDMC) | HIGH (official agenda) | cganga.org public research channel; report-holder route (institutional research request, not RTI) |
| **TTI Environment & Services** | DPR consultant, 1905 mm brick barrel incl. CCTV survey (NDMC Council Item 19, 28-02-2024) | MEDIUM (council minutes, scanned) | corporate site; DPR deliverable held by NDMC Sewerage PD |
| **"Aar Pee Electrical Engineering Works"** | claimed survey awardee (parallel audit, unverified) | **LOW / identity conflict** (public footprint = electrical goods manufacturer) | none — do not contact on this basis |
| **DMRC** | executor, Sunehri Pul desilting/rehabilitation (₹35 Cr, NDMC-funded, 2025-26) — **works contractor, not survey** | MEDIUM (press quoting tender) | n/a (not a survey route) |
| **INTACH** | 2007 Kushak bio-drainage consultant (NDMC Sub-city Plan) | HIGH (official plan) | I&FC publishes an "INTACH Reports" section — **page exists, zero content posted** (verified) |
| **IIT Delhi, Dept. of Civil Engineering** | DMP-2018 consultant (with I&FC) | HIGH | departmental research contact; DMP working files (incl. any survey inputs) route |

## 6. NON-RTI ACQUISITION ROUTES (ranked by expected yield)

1. **Procurement attachment (highest yield, fully legal, non-RTI):** free registration on govtprocurement.delhi.gov.in → open Tender `2026_NDMC_297503_1` → download `work_384007.zip` (NIT + BOQ; CAPTCHA is the ordinary human-verification step). BOQ carries per-L-section silt quantities; if any L-section/drawing annexure is uploaded pre-award it appears in the same zip. Watch the post-award "Results of Tenders" entry for the L1 (who then holds/produces pre-desilting joint survey records).
2. **Court record (non-RTI):** Delhi HC e-Inspection (dhcmisc.nic.in/inspection) for CONT.CAS(C) 434/2022 — the signed 28-01-2026 status report and any photo annexures beyond the order text; subsequent orders (18-02-2026 onward) may attach the boundary-wall/grill drawings.
3. **Institutional research request (non-RTI):** cGanga/IIT-K public research channel for the Kushak flow-assessment report (they authored it; NDMC already has it — a courtesy copy to a research collaborator is the consultant's prerogative).
4. **Contractor/consultant direct request (non-RTI, after award):** once NIT-52 is awarded (post 17-09-2026), the L1's own pre-desilting survey (robotic/sonar per tender scope) becomes a company deliverable — a research-request route to the contractor exists without RTI.
5. **Direct public download:** currently nil for survey data (I&FC INTACH page empty; NIQ listing carries no award history; WRIS down).

## 7. EXACT NEXT ACTION (one)

**Register a free bidder account on govtprocurement.delhi.gov.in and download `work_384007.zip` for Tender ID `2026_NDMC_297503_1` (NIT-52), solving the portal CAPTCHA in-browser as the normal human-verification step.** This is the only channel that can put official quantitative current-condition data (per-L-section silt quantities) and, if uploaded, the tender's L-section/BOQ annexures into our hands without RTI — and it must be done before the portal's post-award cycle reshuffles attachments.

## 8. RTI NECESSITY

- **Can we avoid RTI?** **Partially yes.** Non-RTI routes exist for: NIT-52 BOQ/drawings-as-uploaded (§7), the Delhi HC 434/2022 file (e-Inspection), the NDMC Council scanned minutes (download + OCR), and post-award contractor deliverables (research request).
- **What still requires RTI (specific records):**
  1. **The Nov-2024 I&FC bathymetric survey output** (L-sections/cross-sections/DGPS-echo-sounder data of Sunheripul + Kushak + Bijwasan; NIQ `EE/CD-XII/08-10-2024`; award unverified) — custodian EE, Civil Division-XII, I&FC (ifccdxii@gmail.com). No publication duty exists for a ~₹2.45 lakh NIQ work; this record will not surface voluntarily.
  2. **NDMC R-III's longitudinal sections, cross-sections and invert profiles** of the covered Kushak Nallah (held per NIT-52 Clause 6; drawings for bidder inspection only — non-bidders are steered to RTI).
  3. **cGanga Kushak flow-assessment final report** (NDMC Sewerage PD, File V-16027/55/2024/Sewerage-Project) — institutional request first; RTI only if refused.
  4. **The 2020-21 topographical-survey/DPR consultancy award and deliverables** (custodian NDMC; procurement trail not publicly indexed — RTI likely required to even identify the consultant).

## 9. SCIENTIFIC IMPACT

- **Not resolved:** none of the four core geometry blockers (instrumented current bed profile; true box clear depth vs the 3.5–4.5 m visual / 7.354–7.554 m model conflict; open-reach cross-sections; structure inverts/survey datum) moved this phase — no ACTUAL_SURVEY_DATA was located in any public channel.
- **Resolved/strengthened this phase:** (i) an **official, current (Jan-2026) reach segmentation** — INA→LLRM ≈2.62 km split 1.75 km / 1.0 km / 0.87 km with the MCD→I&FC as-is-where-is handover — COURT_NGT_RECORD, usable to reconcile the conflicting published lengths (3.85 km vs 2.62 km are different reach definitions); (ii) a documented **official obstruction-risk statement** (grill/mesh clogging → NDMC-drain backwater) usable qualitatively in blockage scenarios; (iii) **definitive NIT-52 status** (no corrigendum, no award; two portal IDs disambiguation required) — which fixes the timing of any future contractor-deliverable route; (iv) verification that the "Aar Pee" award identity fails scrutiny (prevents a false contractor lead from entering the evidence base).

## 10. CHANGED FILES

Created:
- `docs/DELHI_KUSHAK_PHASE6B_NON_RTI_ACQUISITION_AUDIT.md` (this report)
- `data/delhi/raw/MANIFEST_PHASE6B_20260912.json` (manifest of new downloads)
- `data/delhi/raw/official_docs/ndmc_budget/ndmc_budget_2021-22_vol2.pdf` + `.txt` (NDMC Budget Vol-II, downloaded + text layer)
- `data/delhi/raw/drainage/niq_cdxii_page_20260912.html`, `data/delhi/raw/drainage/intach_reports_page.html` (portal-state evidence)

Modified: **NONE** (no code, solver, models, tests, V1, catchment/rainfall/historical pipelines, or pre-existing research artifacts touched).

---

*Anti-fabrication note: no contractor, survey value, dimension, chainage or date was invented; tender numbers are quoted verbatim (`52/EE(R-III)/2025-26`, `2026_NDMC_297503_1`, `2026_NDMC_289211_1`, `EE/CD-XII/08-10-2024`, `CONT.CAS(C) 434/2022`); the "Aar Pee" award claim was deliberately downgraded rather than repeated; tender specifications were nowhere treated as survey results.*
