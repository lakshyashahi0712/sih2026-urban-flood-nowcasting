# Phase 6E — I&FC 2024/2025 DGPS + Echo-Sounder Kushak Survey: Acquisition Audit

**Document ID:** `DELHI_KUSHAK_PHASE6E_IFC_2024_SURVEY_ACQUISITION_AUDIT`
**Date:** 2026-09-12
**Mission type:** procurement/award/deliverable trace of the I&FC CD-XII hydrographic/topographical survey of Kushak Nallah, and identification of a legitimate non-RTI route to its deliverables. No RTI filed/drafted; no contact; no geometry reconstructed; no code/models/tests/pipelines/V1 touched.

**Inputs inspected (scoped):** `data/delhi/raw/drainage/ifc_niq_cdxii0810_survey.pdf` (primary NIQ, on disk), `data/delhi/raw/official_docs/ngt_order_20240806_oa6_2012_bathymetry.html` (survey-origin directive), `data/delhi/raw/drainage/ifc_niq_cdxii_20260819_survey.pdf` (CD-XII jurisdiction record), the on-disk NGT order set (OA 6/2012), `docs/DELHI_KUSHAK_PHASE6B/6C` audits.

---

## 1. STATUS

**PARTIAL.** The survey's *origin directive* and one *primary NIQ* are verified from documents on disk; the NIQ listing page and Delhi-govt order repositories were probed live. **The award/AOC/work order is not published on any reachable official channel, the survey agency is UNKNOWN (the "Aar Pee" claim fails identity scrutiny), and no survey deliverable has surfaced anywhere.** The "~870 m survey / 03-12-2024 takeover" affidavit referenced by the Phase 6E brief could not be located in any primary record during this audit and is classified LEAD_ONLY.

## 2. PRIMARY PROCUREMENT RECORD

| Field | Value | Evidence source | Confidence |
|---|---|---|---|
| **Verified NIQ** | **No. EE-CDXII/NIQ/2025-26/249, dated 08-10-2025** (FY 2025-26) | `data/delhi/raw/drainage/ifc_niq_cdxii0810_survey.pdf` (SHA-256 `be817613…`, read in full this audit) | HIGH (primary document on disk) |
| Authority | Executive Engineer, Civil Division No.-XII, I&FC Dept, GNCTD, Basaidarapur Office Complex, New Delhi-110027 (ifccdxii@gmail.com; 011-25172699) | same | HIGH |
| Scope (3 packages, same NIQ) | (1) Bathymetry/Topographical + Hydrographical Survey (DGPS + echo sounder) of **Sunheripul Drain, Kushak Drain, Bijwasan Drain** (CD-XII jurisdiction); (2) same for **Barapullah Drain**; (3) same for **drains 12, 12A, 14, 15, Civil Military drain, Delhi Gate drain** | same | HIGH |
| Process | Sealed quotations collected from the office; submission **10-10-2025 14:00**; opening **10-10-2025 15:00**; eligibility = I&FC-enlisted agencies with GST + PAN + enlistment certificate | same | HIGH |
| Completion constraint | "**The work is of Urgent nature and to be completed within 03 days only.**" | same | HIGH |
| **Award / AOC / work order** | **NOT publicly published. Not located.** | NIQ listing page `ifc.delhi.gov.in/tender/niq-cd-xii` (checked live — lists only the 19-08-2026 NIQ, no award history); Delhi centralized-order search has no IFC domain; NIQ-scale works are not e-published on NicGeP | HIGH (absence, within probed channels) |
| **Awardee** | **UNKNOWN.** The parallel audit's "Aar Pee Electrical Engineering Works, 12-11-2024, ₹2.45 lakh" is **not primary-verified**; the only public footprint of that name is an electrical-goods manufacturer (IndiaMART) | Phase 6B verification | HIGH (that it is unverified) |
| Amount | UNKNOWN (₹2.45 lakh figure = unverified parallel-audit claim) | — | — |
| Completion date | UNKNOWN | — | — |

**Date-discrepancy resolution:** the Phase 6B citation "NIQ EE/CD-XII/NIQ/08-10-2024" does **not** match the on-disk primary (which is **2025-26/249 dt. 08-10-2025**). Either a separate FY 2024-25 NIQ existed (first survey round, consistent with an NGT Aug-2024 directive → late-2024 execution) or the 2024 NIQ/award claim is a misdating of this 2025 document. **Both possibilities are recorded; neither is merged or assumed.**

## 3. PROCUREMENT CHAIN

**Verified origin (primary):** NGT OA 6/2012, order **06-08-2024** — Chief Secretary (GNCTD) affidavit recommendation: *"A bathymetric survey of the Barapullah drain (including its subsidiary drains viz. Sunehripul drain and Kushak drain) may be undertaken by the IFCD within a months' time"* (`ngt_order_20240806_oa6_2012_bathymetry.html`).
→ **(unverified 2024 first round:** NIQ Oct-2024 → claimed award 12-11-2024 → claimed execution after the 03-12-2024 takeover — LEAD_ONLY, no primary located**)**
→ **Verified 2025 NIQ (2025-26/249, 08-10-2025, 3-day urgent completion, quotes opened 10-10-2025)** — consistent with a repeat/urgent sounding round, plausibly post-desilting verification (interpretation flagged, not asserted)
→ **Award: UNKNOWN** (no public AOC/comparative statement/work order)
→ **Agency: UNKNOWN** (no primary identification; "Aar Pee" claim rejected per contractor-class rule)
→ **Deliverable: UNKNOWN / not published** (survey report + L-sections/sections + DGPS/sounder data presumed held by EE CD-XII per NIQ custody pattern)
→ **Custodian: EE, Civil Division-XII, I&FC (ifccdxii@gmail.com, 011-25172699, Basaidarapur)**

## 4. ACTUAL SURVEY DATA

**"No ACTUAL_SURVEY_DATA acquired."**

No survey report, L-section, cross-section sheet, sounding/XYZ file, CAD file, or field book exists on any public channel located during this audit. The only primary survey-procurement document is the 1-page NIQ itself.

## 5. GEOMETRY CONTENT AUDIT

| Feature | Value | Source | Classification | Measured? |
|---|---|---|---|---|
| Survey instrumentation | "DGPS machine and Eco sounder etc." | NIQ 2025-26/249 | D. PROCUREMENT_SPECIFICATION | No |
| Survey scope (drains) | Sunheripul + Kushak + Bijwasan; Barapullah; drains 12/12A/14/15/Civil Military/Delhi Gate | NIQ 2025-26/249 | D. PROCUREMENT_SPECIFICATION | No |
| Urgency/completion | 3 days | NIQ 2025-26/249 | D. PROCUREMENT_SPECIFICATION | No |
| Kushak survey reach (per later jurisdiction record) | "INA metro station to D/S of Lala Lajpat Rai bridge" (CD-XII maintenance reach, FY 2026-27) | I&FC NIQ 19-08-2026 (`ifc_niq_cdxii_20260819_survey.pdf`, acquired earlier) | OFFICIAL_RECORD (jurisdiction only) | No |
| "~870 m bathymetric survey of the open Kushak stretch (Bus Depot → LLRM), after takeover on 03-12-2024" | — | Phase-6E brief citing an NGT affidavit; **primary document not located** (searched: on-disk NGT orders incl. 06-08-2024 / 09-04-2025 / 23-04-2025 / 14-10-2025; indiankanoon recent-order searches) | **LEAD_ONLY** | Not established |
| Any bed level, invert, chainage, RL, cross-section, coordinate, datum from the survey | — | — | — | No such value exists publicly |

## 6. COVERAGE AUDIT

- **Only defensible statement:** the survey (if executed per the NIQ scope) covers the **CD-XII jurisdiction reach of Kushak** — per the I&FC's own later record, the reach **"from INA metro station to downstream (D/S) of Lala Lajpat Rai bridge"** (the open, accessible stretch; the Delhi HC 29-01-2026 status report independently records this 0.87 km segment as handed to I&FC).
- **NOT covered by this survey:** the Africa Avenue covered conduit (NDMC R-III), the Bus Depot covered reach (MCD/DTC possession), the upstream NDMC open reaches, and the tributaries' covered portions.
- Chainage start/end values: **UNKNOWN** (no chainage appears in any located document).
- **If the deliverable is obtained, expected coverage ≈ 0.87 km open reach — not the 5 km corridor.** (Rated as an expectation from jurisdiction records; exact surveyed extent remains UNKNOWN until the report is seen.)

## 7. DATUM / CONTROL AUDIT

**UNKNOWN.** The NIQ names "DGPS machine and Eco sounder" but states **no vertical datum, no benchmark, no GTS tie**. DGPS implies WGS84 horizontal referencing; the vertical datum of the echo-sounder reductions is unspecified. No assumption of MSL/GTS is carried. Any obtained survey must be datum-audited before ingestion (known inter-agency datum conflicts exist in Delhi drainage records).

## 8. NON-RTI ACQUISITION ROUTES (ranked)

1. **Government attachment (monitoring route):** I&FC occasionally annexes survey outcomes in NGT filings — monitor post-2025 NGT OA 6/2012 orders and I&FC's site (`ifc.delhi.gov.in` NIQ/tender pages and the "All Documents" section) for any annexed Kushak survey summary/L-sections. (Current yield: zero — but the 06-08-2024 order shows this survey class does enter NGT records.)
2. **Institutional route:** the CD-XII jurisdiction/maintenance records (e.g., the FY 2026-27 A/R & M/O quotation file) show recurring office engagement — a non-RTI **office-level information request** to EE CD-XII (ifccdxii@gmail.com) for the survey report is the direct route; voluntary, outcome not presumable. *(Identified only; not exercised.)*
3. **Survey-agency research request:** blocked at STEP 2 — the agency is UNKNOWN; if a future record names it, a research request to the agency becomes possible.
4. **Direct public download:** none exists today (award and deliverable are not published).

## 9. RTI NECESSITY

**Yes — RTI is currently necessary** for the two decisive records, neither of which is published:
1. **Award/AOC/work order** for the bathymetric/topographical survey of Kushak (and Sunheripul/Bijwasan/Barapullah) under CD-XII — to identify the actual survey agency (FY 2024-25 and/or the 2025-26/249 quotation).
2. **The survey deliverable itself** — hydrographic/topographic survey report with L-sections/cross-sections, DGPS/echo-sounder data and datum statement, held by EE, Civil Division-XII, I&FC.

The only non-RTI route (monitoring NGT filings / voluntary office request) has so far produced nothing and cannot be relied upon.

## 10. SCIENTIFIC IMPACT

- **No P0 blocker is resolved.** A commissioned survey is not acquired data: no bed profile, cross-section, invert, structure geometry, datum control, or Africa Avenue geometry value exists publicly from this procurement.
- **Reduced (context only):** the survey's *expected coverage* is now bounded — CD-XII's own jurisdiction record (INA metro → D/S LLRM, ≈0.87 km open reach) means even full delivery would address only the open outfall reach, **not** the Africa Avenue conduit, the depot reach, or the upstream covered system. This sharpens the acquisition strategy: the Africa Avenue P0 gap requires the NDMC R-III/NIT-52 chain (Phase 6C route), not this I&FC survey.
- **Corrections banked:** Phase 6B's "NIQ 08-10-2024 / award 12-11-2024 / ₹2.45 lakh / Aar Pee" chain is downgraded to LEAD_ONLY with the identity conflict documented; the primary-verified NIQ is **2025-26/249 dt. 08-10-2025 (3-day urgent completion, quotes opened 10-10-2025)**.

## 11. EXACT NEXT ACTION (one)

**File a targeted RTI application to the EE, Civil Division-XII, I&FC (Basaidarapur) requesting, for NIQ No. EE-CDXII/NIQ/2025-26/249 dt. 08-10-2025 (and any FY 2024-25 predecessor for the same survey): the quotation-opening result, name of the accepted agency, work order/AOC, and the completed hydrographic/topographic survey report of Kushak Drain with all L-sections, cross-sections and datum notes.** *(This is the single action that closes both unknowns — agency and deliverable — in one filing; flagged here as the mission's route conclusion, not drafted or sent.)*

## 12. CHANGED / CREATED FILES

Created:
- `docs/DELHI_KUSHAK_PHASE6E_IFC_2024_SURVEY_ACQUISITION_AUDIT.md` (this report)

Modified / downloaded: **NONE** (no new raw acquisitions — the decisive primary NIQ, the origin directive, and the jurisdiction records were already on disk; live portal probes produced no new files).

*Anti-fabrication note: no awardee, amount, date, or measurement was inferred; the "~870 m / 03-12-2024" statement is carried as LEAD_ONLY with its primary source declared unlocated; the two NIQ vintages (2024 claim vs 2025 primary) are kept separate; no tender wording was treated as measured geometry; no MSL/GTS datum assumed.*
