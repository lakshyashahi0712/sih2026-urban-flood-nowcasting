# Phase 6D — cGanga / IIT-K Kushak Flow-Assessment Report: Acquisition Audit

**Document ID:** `DELHI_KUSHAK_PHASE6D_CGANGA_FLOW_ASSESSMENT_ACQUISITION_AUDIT`
**Date:** 2026-09-12
**Mission type:** forensic identification of an existing engineering/research report and its legitimate non-RTI acquisition route. No RTI filed; no person or organization contacted; no report content invented; no production code or prior research artifacts modified.

**Inputs inspected (scoped):** `docs/DELHI_KUSHAK_PHASE6B_NON_RTI_ACQUISITION_AUDIT.md`, `docs/DELHI_KUSHAK_PHASE6C_NIT52_PACKAGE_AUDIT.md`, `data/delhi/raw/official_docs/ndmc_council_meeting_28-02-2024.pdf` (already-acquired primary record), `data/delhi/raw/MANIFEST_CURRENT_GEOMETRY_20260912.json`.

---

## 1. STATUS

**PARTIAL.** The primary Council record and the cGanga covering letter were located and read from the already-acquired 980-page scanned Council file, and the IIT Kanpur institutional project registration was verified on the official IIT system portal. **The actual flow-assessment report itself is NOT publicly available** — the cGanga letter states it "is being submitted separately" to NDMC, and no public copy exists on any searched institutional or government source. Report identity (exact title/number): **UNKNOWN**. The non-RTI route is identified but voluntary (academic request).

## 2. REPORT IDENTITY

| Attribute | Value | Confidence |
|---|---|---|
| Exact title | **UNKNOWN** (never printed publicly; the Council text describes only the *scope*: "To study and prepare flow data, wastewater characteristics etc. for the wastewater of Kushak Nallah (Open Drain) from S.P Marg to Kamal Attaturk Marg") | HIGH (absence verified across Council pages 462–480 and web sources) |
| Report number | UNKNOWN | — |
| Date of report | UNKNOWN (letter transmitting the *proposal* is 21-02-2024; Phase-I study "completed timely" per agenda) | — |
| Authors | UNKNOWN (individual authors not published). Institutional authorship: **cGanga — Centre for Ganga River Basin Management and Studies, IIT Kanpur**; covering letter signed **Dr. Vinod Tare, Professor & Founding Head, cGanga**; e-Office transmission by **Dr. Asish Sengupta, Consultant, cGanga** | HIGH (from primary documents) |
| Commissioning department | **NDMC Civil Engineering Department, Public Health Circle, Sewerage Project Division** | HIGH |
| File / work-order reference | NDMC File No. **V-16027/55/2024** (letterhead: "V-16027/55/2024 U/o JE(SP)", e-Office computer no. 135133; file series 132689//2024/Sewerage Project). Phase-I amount **₹7.375 lakh**, "completed timely" | HIGH |
| Related registered project (institutional) | **"Novel Solution For Improving Water Quality Of Kushak Nallah In New Delhi"** — sponsor **NEW DELHI MUNICIPAL COUNCIL**, PI **Prof. Purnendu Bose, Civil Engineering, IIT Kanpur (pbose@iitk.ac.in)** — IIT Kanpur sponsored-projects portal entry #17 | HIGH (official portal) |

**Do-not-merge note:** this flow assessment (cGanga/IIT-K, NDMC Sewerage PD, 2023-24) is distinct from (1) the I&FC 2024 DGPS+echo-sounder survey, (2) the NIT-52 future sonar survey, (3) the 1905 mm barrel CCTV/DPR work, and (4) the DMP-2018 model. Nothing was merged.

## 3. PUBLIC RECORD FOUND

| Source | Document | Exact URL / location | Public? | Actual report? | Provenance |
|---|---|---|---|---|---|
| NDMC Council Meeting No. 12/2023-24, 28-02-2024 (980-page scanned PDF, already on disk) | **Item 21 (Civil Engg.-I)**, internal pp. 462–469 + annexures 470–480 | `data/delhi/raw/official_docs/ndmc_council_meeting_28-02-2024.pdf` (pp. 462–485 rendered to `_council_png/`) | Yes (file on disk; NDMC posts council agendas) | **No** — contains agenda narrative + cGanga covering letter + Phase-II (treatment) proposal annexures; the assessment report is explicitly "being submitted separately" | OFFICIAL_RECORD (verbatim read from scan) |
| cGanga covering letter (Annexure p. 470) | Letter, Dr. Vinod Tare → Chairman NDMC, **21-02-2024** | same PDF, annexure page 470 | Yes (in council file) | No — transmits the Phase-II *proposal*; states the assessment **report** goes separately | OFFICIAL_RECORD |
| IIT system sponsored-projects portal | IIT Kanpur project list entry #17 | https://www.iitsystem.ac.in/mhrdprojects (`?search=kushak`; capture: `data/delhi/raw/official_docs/iitsystem_kushak_search.html`) | Yes | No — project registration only (title/sponsor/PI) | OFFICIAL_RECORD |
| cganga.org | Site-wide check | https://cganga.org/ | Yes | No — zero Kushak/NDMC mentions anywhere on the landing content | SECONDARY_REFERENCE (negative) |
| Web (smartutilities, TOI, HT Apr-2024) | Press on the ₹169.57–170 Cr Kushak rejuvenation approval (5 MLD DWWTP under Namami Gange) | smartutilities.net.in 24-04-2024; TOI 01-03-2024; HT 08-03-2024 | Yes | No | SECONDARY_REFERENCE |

## 4. ACTUAL REPORT ACQUISITION

- **Found: NO. Downloaded: NO.** No PDF/DOC/repo copy of the flow-assessment report exists on cganga.org, the IIT system portal, NDMC's public site, DPCC/NMCG uploads, or any indexed archive (searched within the scoped trails only).
- What WAS newly extracted from the already-held Council file (verbatim, now citable): Item 21 full narrative (pp. 462–469) and the cGanga letter + proposal annexures (pp. 470–480). Page renders preserved at `data/delhi/raw/official_docs/_council_png/pg0462–0485.png`.
- Access limitations: the report is held inside NDMC Sewerage Project Division's physical/e-Office file **V-16027/55/2024**; no publication channel exists for consultancy reports on NDMC's site.

## 5. CONTENT AUDIT

The report itself is unavailable, so **no DIRECT_REPORT_CONTENT claims are made**. What is officially on record about it:

| Claim | Value | Class |
|---|---|---|
| Study objective (agenda + letter) | "To study and prepare **flow data, wastewater characteristics** etc. for the wastewater of Kushak Nallah (Open Drain) from S.P Marg to Kamal Attaturk Marg" | OFFICIAL_DESCRIPTION_OF_REPORT |
| Headline result quoted by NDMC | "the **average flow in the Kushak Nallah was observed around 10 MLD during non-rainy season**" | OFFICIAL_DESCRIPTION_OF_REPORT (agenda-level; not a dataset) |
| Downstream design assumption | Phase-II system "designed for a total flow of **10 MLD**": Part 1 = 1 × 5 MLD near Sardar Patel Marg (first outfall); Part 2 = 2 × 2.5 MLD at the last stretch (last outfall) | OFFICIAL_DESCRIPTION_OF_REPORT (design basis, cGanga letter/annexure 2) |
| Coverage of geometry | Nothing on record indicates the report contains cross-sections, invert/bed levels, bathymetry, structure geometry, GPS/survey points, or monitoring coordinates | UNKNOWN (unverifiable without the report) |
| Methodology / QA / uncertainty | UNKNOWN | UNKNOWN |
| Dates/times of field observations | UNKNOWN | UNKNOWN |

Related-but-separate context kept distinct: the earlier "Innovative Project… Stream Restoration / Eco Fert / Bio mats / Gabions / microbial consortia" work order (completed; "slight improvement" per agenda) is **not** the cGanga study.

## 6. WHAT IT CAN LEGITIMATELY SUPPORT (if and when obtained)

- **Hydraulic calibration evidence:** potentially strong — an institutional dry-weather flow measurement series (flow data + wastewater characteristics) for the S.P. Marg→Kamal Ataturk Marg open reach. Currently only the single ≈10 MLD non-rainy average is citable (OFFICIAL_DESCRIPTION_OF_REPORT).
- **Geometry evidence:** UNKNOWN until inspected — the stated scope is flow/quality, not surveying; **do not assume cross-sections exist**.
- **Boundary-condition evidence:** NO (upstream open-reach flows, not outfall boundary).
- **Descriptive/contextual evidence:** confirmed — pollution history, treatment-project basis, 10 MLD design basis.

## 7. NON-RTI ACQUISITION ROUTES (ranked)

1. **Council-record attachment route (already 60 % exercised):** the Item 21 file annexures (470–480) hold the *proposal*; later NDMC Council agendas (post-28-02-2024) may attach or summarize the assessment report when tabling the Phase-II award/progress — monitor subsequent NDMC Council agendas (ndmc.gov.in) for File V-16027/55/2024 continuations.
2. **Institutional research request (voluntary, non-RTI):** the report's authors are publicly identifiable — cGanga/IIT-K (Dr. Vinod Tare; project PI **Prof. Purnendu Bose, pbose@iitk.ac.in**, listed publicly on the IIT system portal). A research-collaboration/courtesy request to the group is the only identified route that does not involve NDMC. (Not exercised per mission rules.)
3. **NDMC public-document request (non-statutory):** a written request to Sewerage Project Division citing the Council Item number may yield a voluntary copy; falls short of RTI but is at NDMC's discretion.
4. **Academic collaboration route:** the Phase-II implementation (₹169.57–170 Cr rejuvenation, IIT-K "roped in" per HT) gives a standing institutional relationship through which study data may be shared with research partners.

## 8. RTI NECESSITY

**Yes — currently necessary for the report itself.** No public copy exists; custody is NDMC Sewerage Project Division (File No. V-16027/55/2024/Sewerage-Project) and the cGanga/IIT-K group. The only non-RTI alternatives are *voluntary* (routes 2–4 above), which cannot be presumed. Exact record that would require RTI: *"Final flow-assessment/wastewater-characteristics study report of Kushak Nallah (Open Drain) S.P. Marg to Kamal Attaturk Marg, by cGanga IIT-Kanpur, held with NDMC Sewerage Project Division, File No. V-16027/55/2024/Sewerage-Project (Council Item 21, 28-02-2024)."*

## 9. SCIENTIFIC IMPACT

- **P1 (calibration) partially reduced, at description level:** the officially-recorded **≈10 MLD non-rainy-season average flow** for the S.P. Marg→Kamal Ataturk Marg open reach is now anchored to its primary source (Item 21, verified verbatim from the council scan) — usable as a single-point dry-weather-flow anchor with its stated caveat (agenda-level figure, non-rainy season, single reach).
- **P0 geometry blockers: untouched.** Nothing suggests the report contains cross-sections/inverts; no geometry value was claimed, and none was upgraded.
- Positive side-effect: the Item 21 record also documents the *failed* first treatment attempt (Stream Restoration work order) and the Phase-II design basis (10 MLD = 1×5 + 2×2.5 MLD at first/last outfalls) — contextual evidence for in-drain flow-control scenarios.

## 10. EXACT NEXT ACTION (one)

**Monitor subsequent NDMC Council meeting agendas (post 28-02-2024, ndmc.gov.in) for any item under File No. V-16027/55/2024 (Sewerage Project Division) and, if the flow-assessment report or its findings appear as an agenda annexure, acquire that council PDF and preserve it under `data/delhi/raw/official_docs/` with a manifest.**

## 11. CHANGED / CREATED FILES

Created:
- `docs/DELHI_KUSHAK_PHASE6D_CGANGA_FLOW_ASSESSMENT_ACQUISITION_AUDIT.md` (this report)
- `data/delhi/raw/official_docs/_council_png/p0001–p0006.png` and `pg0462–pg0485.png` (page renders of the already-manifested council PDF used for the verbatim Item 21 read; extraction aids)
- `data/delhi/raw/official_docs/iitsystem_kushak_search.html` (capture of the IIT system portal search showing project entry #17, "Novel Solution For Improving Water Quality Of Kushak Nallah In New Delhi", NDMC-sponsored, PI Purnendu Bose)

Modified: **NONE** (no code, models, tests, pipelines, V1, or pre-existing research artifacts changed; the source council PDF untouched — renders only).

*Anti-fabrication note: no report content was invented; the ≈10 MLD figure is quoted strictly as an official agenda-level statement with its reach and season qualifiers; "submitted separately" is quoted verbatim from the cGanga letter; the exact report title is declared UNKNOWN rather than guessed.*
