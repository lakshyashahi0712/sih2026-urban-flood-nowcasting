# Phase 13C — Operational Evidence Acquisition & Submission Package

**Document ID:** `DELHI_KUSHAK_PHASE13C_OPERATIONAL_SUBMISSION_PACKAGE`  
**Date:** 2026-09-16  
**Status:** DRAFT_READY (Submission-Ready Packages Formulated; Awaiting Citizen Filing)  
**Baseline Git Commit:** `d4ab4baceb56044fb860a5c67f81dee4199d3853`  
**Mission:** Operationalize the acquisition of existing official engineering survey records for Kushak Nallah from I&FCD (CD-XII) and NDMC (Road-III), track active procurement milestones (NDMC NIT-52), and enforce evidence receipt gating.

---

## 1. OPERATIONAL SUBMISSION CHECKLIST

### Request 1: I&FC Civil Division-XII (Hydrographic & Bathymetric Survey Deliverables)
* **Authority:** Irrigation & Flood Control Department (I&FCD), Government of NCT of Delhi
* **Office / Custodian:** Office of the Executive Engineer, Civil Division No.-XII, Basaidarapur Office Complex, New Delhi – 110027 (`ifccdxii@gmail.com`, 011-25172699)
* **Reference Number:** NIQ No. `EE-CDXII/NIQ/2025-26/249` dated 08-10-2025
* **Subject:** Request under Section 6(1) of RTI Act, 2005 for existing procurement records, comparative statement, award particulars, and completed hydrographic/bathymetric survey deliverables (L-sections, cross-sections, DGPS/echo-sounder point clouds, CAD files, datum) for Kushak Drain, Sunheripul Drain, and Barapullah Drain
* **Final Request Text:** Formulated and validated in full in `docs/DELHI_KUSHAK_PHASE13B_RTI_IFC_ACQUISITION.md`
* **Submission Channel:** Delhi Government Online RTI Portal (`rtionline.delhi.gov.in`) or Physical Speed Post with ₹10/- Indian Postal Order (IPO)
* **Date Submitted:** `NOT SUBMITTED` (Pending physical/authorized human citizen filing; autonomous AI cannot execute statutory citizen affidavits or financial portal payments)
* **Acknowledgement / Reference Number:** `NONE` (Never fabricated)
* **Operational Status:** `DRAFT_READY`

---

### Request 2: NDMC Civil Engineering Department (Road-III) (As-Built Conduit Geometry)
* **Authority:** New Delhi Municipal Council (NDMC)
* **Office / Custodian:** Office of the Executive Engineer (Road-III), Civil Engineering Department, Room No. 306, SBS Place, Gole Market, New Delhi – 110001
* **Reference Number:** NIT No. `52/EE(R-III)/2025-26` (Tender ID `2026_NDMC_297503_1`) and Predecessor Survey NIT No. `51/EE(R-III)/2020-21`
* **Subject:** Request under Section 6(1) of RTI Act, 2005 for existing as-built structural drawings, longitudinal sections, cross-sections, invert profiles, and survey records for the covered Kushak Nallah corridor (Sardar Patel Marg to Lodhi Colony / Africa Avenue), with formal invocation of Section 2(j)(i) physical inspection rights
* **Final Request Text:** Formulated and validated in full in `docs/DELHI_KUSHAK_PHASE13B_RTI_NDMC_ACQUISITION.md`
* **Submission Channel:** NDMC RTI Portal / Physical Speed Post to SBS Place / In-Person Physical Inspection under Section 2(j)(i)
* **Date Submitted:** `NOT SUBMITTED` (Pending physical/authorized human citizen filing)
* **Acknowledgement / Reference Number:** `NONE` (Never fabricated)
* **Operational Status:** `DRAFT_READY`

---

## 2. NDMC NIT-52 PUBLIC PROCUREMENT LIVE TRACKING

* **Tender ID:** `2026_NDMC_297503_1`
* **NIT Reference:** `52/EE(R-III)/2025-26`
* **Work Description:** Comprehensive Cleaning of Covered Kushak Nallah and Ring Road Nallah by Mechanical/Robotic Means
* **Estimated Cost:** ₹12,29,57,183 (approx. ₹12.30 Crore)
* **Published Date:** 24-Aug-2026
* **Pre-Bid Meeting:** Held on 03-Sep-2026 at Palika Kendra
* **Bid Submission Closing:** 17-Sep-2026 at 15:30 IST
* **Bid Opening:** 17-Sep-2026 at 16:00 IST (Room 306, SBS Place)
* **Current Operational Status (as of 16-Sep-2026):** `PRE_AWARD` (Active tender approaching bid close; no bids opened, no L1 contractor evaluated, no work order issued).
* **Future Deliverable Milestone:** Item 2 of Schedule of Quantities mandates 290 m of robotic pipeline acoustic profiling (sonar method via Pipescape). This deliverable is prospective and will only be executed by the successful contractor during the 12-month contract period following financial award.

---

## 3. EVIDENCE INTAKE AUDIT & LIFECYCLE EVALUATION

Pursuant to the `DELHI_KUSHAK_PHASE13B_EVIDENCE_RECEIPT_PROTOCOL`:

| Tier-A Hydraulic Geometry Target | Evidence Status | Provenance Category | Current Public Availability |
| :--- | :--- | :--- | :--- |
| **Longitudinal Profile ($Z_{\text{bed}}(x)$)** | `MISSING` | `UNAVAILABLE` | No station-by-station invert levels exist on public channels. |
| **Open-Reach Cross-Sections ($B(x, z), A(z)$)** | `MISSING` | `UNAVAILABLE` | Survey deliverables from I&FC NIQ 249 remain in offline divisional archives. |
| **Covered Conduit Geometry (Box & Invert)** | `PARTIAL` | `OBSERVED/OFFICIAL` (Bounds only) | 1.0 km Bus Depot box structure bounds verified from NGT Joint Inspection (50 m wide, 5 bays of 10 m, depth 3.5–4.5 m); continuous invert & Africa Avenue geometry `UNAVAILABLE`. |
| **Structure Openings (Bridges / Culverts)** | `PARTIAL` | `OBSERVED/OFFICIAL` (Qualitative) | Lala Lajpat Rai Marg culvert 5 bays noted in NGT order (2 choked); exact invert/soffit elevations `UNAVAILABLE`. |
| **Vertical Datum & Control Ties** | `MISSING` | `UNKNOWN` | No GTS benchmark or MSL tie specified in public procurement notices. |
| **Lateral Inflow Connections** | `MISSING` | `UNAVAILABLE` | Municipal feeder drain connection invert levels remain unrecorded. |
| **Hydraulic Observations** | `PARTIAL` | `OBSERVED/OFFICIAL` | cGanga/IIT Kanpur 2024 empirical dry-weather flow (≈10 MLD / 0.116 m³/s) between SP Marg and Kamal Ataturk Marg; continuous time-series hydrographs `UNAVAILABLE`. |

---

## 4. SCIENTIFIC RESTRAINTS & MODEL SAFETY VERIFICATION

1. **Zero Model Modifications:** No Python files under `backend/app/domain/delhi/digital_twin/` were modified, created, or deleted.
2. **Zero Parameter Changes:** Hydraulic roughness, bed slopes, and conduit dimensions were not altered.
3. **Zero Synthetic Inventions:** No unmeasured survey points or interpolated cross-sections were injected into any domain data structure.
4. **Git Baseline Integrity:** Commit `d4ab4baceb56044fb860a5c67f81dee4199d3853` remains the clean, unaltered HEAD.\n