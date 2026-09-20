# Phase 6C — NIT-52 Public Tender Package Acquisition + Inspection Audit

**Document ID:** `DELHI_KUSHAK_PHASE6C_NIT52_PACKAGE_AUDIT`
**Date:** 2026-09-12
**Mission type:** acquisition + inspection of the publicly available NIT-52 tender package only. No code, solver, models, tests, V1, catchment/rainfall/historical pipelines, RTI, contractor contact, or broad web research. No geometry reconstructed; no specification upgraded to a measurement.

---

## 1. STATUS

**SUCCESS (acquisition + inspection complete).** The official tender package was downloaded through the portal's ordinary human flow (CAPTCHA read visually and typed — no bypass). Inspection is definitive: **the package contains zero measured Kushak geometry** — no drawings, no L-sections, no chainages, no inverts, no datum. It does contain one **new material specification fact** (covered-barrel size class "4.00 m +25%") and one **future-survey scope** (290 m robotic sonar silt-level survey with electronic report), plus a fully quantified BOQ.

## 2. ACQUISITION

| Field | Value |
|---|---|
| Acquired | **YES** |
| Exact package | **`work_396329.zip`** — 3,481,832 bytes. (Note: Phase 6B cited "work_384007.zip"; the actual portal package for Tender ID `2026_NDMC_297503_1` is `work_396329.zip`, matching `BOQ_396329.xls`. The 384007 reference was not the current package name.) |
| Source | govtprocurement.delhi.gov.in → Search → `2026_NDMC_297503_1` → Tender Details → "Download as zip" → DocDownCaptcha page |
| CAPTCHA handling | Image read visually in-browser and typed into "Enter Captcha" (`y3Db83`), then Submit — the ordinary human verification process; no automation/bypass of the CAPTCHA itself |
| Download timestamp | 2026-09-12, ~09:43 IST |
| SHA256 | `ba3067a1cae7a331f45f2f98e07d0ef1ed07f955be0d23871dda3028ca7054e0` |
| Access limitations | CAPTCHA only; **no login required** for the free packet download |
| Portal metadata at download | Org chain NDMC‖Civil-I‖R-III · published 24-Aug-2026 05:15 PM · document download window 24-Aug-2026 05:20 PM → 17-Sep-2026 03:30 PM · bid submission ends 17-Sep-2026 03:30 PM · bid opening 17-Sep-2026 04:00 PM · pre-bid meeting 03-Sep-2026 03:00 PM (Room 1021-22, Palika Kendra) · value ₹12,29,57,183 · EMD ₹22,29,572 · covers: (1) Fee/PreQual/Technical = NIT .pdf, (2) Finance = BoQ .xls · TIA: EE (R-III) Civil, Room 306, SBS Place, Gole Market |

## 3. PACKAGE INVENTORY

| File | Type | Size (B) | Relevant to geometry? | Notes |
|---|---|---:|---|---|
| `NIT.pdf` | PDF, 121 pages, digitally signed | 3,547,806 | Partially (specifications + quantities only) | NIT body; embedded e-tender notice (original release **27-05-2025**, receipt 13-06-2025); GCC/CPWD conditions; proforma Schedules A–F; **Schedule of Quantities pp. 120–121 (6 items)**; p.10 + p.119 images = signature stamp / CPWD cement-godown storage sketches (not drain drawings) |
| `BOQ_396329.xls` | XLS (BIFF, macro-enabled NicGeP `BoQ_Ver4.0` financial template) | 285,184 | Partially (mirrors SOQ items + bidder quote cells) | Items identical to SOQ; no additional data |
| *(no other files)* | — | — | — | **No DWG/DGN/CAD, no drawing PDFs, no survey files, no L-sections** |

SHA-256: zip `ba3067a1cae7a331f45f2f98e07d0ef1ed07f955be0d23871dda3028ca7054e0` · NIT.pdf `0e45504ab1a40f09…` · BOQ_396329.xls `2eda2b0c426c5b5d…` (full hashes in manifest).

## 4. GEOMETRY FOUND

| Value / feature | Source file | Chainage/location | Value | Classification | Actual survey evidence? |
|---|---|---|---|---|---|
| Covered barrel **size class** for desilting | NIT.pdf SOQ item 1; BOQ | "RCC covered Kushak Nallah and Ring Road Nallah" (no chainage stated) | "**width 4.00 meter +25%** wide in size" | **D. PROCUREMENT_SPECIFICATION** (CPWD size-bucket for costing) | **NO** |
| **Robotic silt-level estimation scope** (Pipeline Acoustic Profiling — **sonar method**; diameter measurement, conditional assessment, silt-level estimation in running flow; electronic report via Pipescape software, hard+soft) | NIT.pdf SOQ item 2; BOQ | not chainage-tagged; **290.00 m** total | 290 m @ ₹1,702.57/m = ₹4,93,745.30 | **D. PROCUREMENT_SPECIFICATION** (scope). The future deliverable will be **A. ACTUAL_SURVEY_DATA** when produced | Not yet (pre-award) |
| Desilting **quantity** (debris/silt/sludge, measured post-draining, **deduct 25% voids**) | NIT.pdf SOQ item 1; BOQ | whole covered scope (Kushak + Ring Road Nallah, R-III) | **21,406.00 m³** | **E. BOQ_QUANTITY** | NO (costing volume; indirect current-condition proxy only) |
| **RCC slab cutting** 8–12 inch thickness | SOQ item 3 | not located | 216.00 m² | E. BOQ_QUANTITY (+spec thickness 203–305 mm) | NO |
| Centering/shuttering | SOQ item 4 | — | 126.00 m² | E. BOQ_QUANTITY | NO |
| Steel reinforcement Fe-500D | SOQ item 5 | — | 30,300.00 kg | E. BOQ_QUANTITY | NO |
| RCC design-mix concrete works | SOQ item 6 | — | (rate item) | E. BOQ_QUANTITY | NO |
| **100% videography / CCTV, 360° of cleaned pipe surface**, submitted with bills (hard+soft) | SOQ item 1 Note 2 | whole desilted scope | deliverable | **D. PROCUREMENT_SPECIFICATION** → future visual record (post-desilting condition evidence) | Not yet |
| Sanction/estimate chain | NIT.pdf p.1 | — | Admin approval ₹30,84,68,000 (Council Item 22(Civil), Note 121/C); detailed estimate ₹12,66,45,900 tech-sanctioned by CE(C-I) vide 288 & 296 dt. **24-11-2025**, TS Register Sr. 68 dt. 05-12-2025; preliminary estimate ₹13,10,43,000 | OFFICIAL_RECORD (procurement chain) | n/a |
| **Original invitation dates** (embedded e-tender notice, p.3–4) | NIT.pdf | — | release **27-05-2025**; receipt closed 13-06-2025 15:00; pre-bid 04-06-2025 | OFFICIAL_RECORD (procurement chain) | n/a |

**Whole-document keyword result (121 pages):** `longitudinal` 0 · `L-section` 0 · `cross-section` 0 · `invert` 0 · `bed level` 0 · `chainage` 0 · `reduced level` 0 · `soffit` 0 · `culvert` 0 · `DGPS` 0 · `echo` 0 · `bathymetry` 0 · `topographic` 0 · `as-built` 0 · `benchmark` 0 · `GTS` 0 · `MSL` 0 · `UTM` 0 · `coordinates` 0 · `datum` 0. Only survey-adjacent hits: `sonar` 1 (item 2), `Pipescape` 1, `videography` 2, `CCTV` 1, `4.00 meter` 2 (items 1–2).

**Integrity flag:** the "Clause 6" text quoted in earlier project artifacts ("All longitudinal sections, cross-sections, and invert profile levels are maintained in the Office of the Executive Engineer (R-III)…") **does not appear anywhere in this actual downloaded package**. The pre-existing extract `data/delhi/raw/hydraulic/ndmc_nit_52_ee_r3_2025_26_kushak_desilting.txt` must therefore be treated as provenance-uncertain (portal listing text or paraphrase) until re-verified against a primary capture.

## 5. DRAWING AUDIT

- **Longitudinal profiles: NONE in package.**
- **Cross-sections: NONE.**
- **Structure drawings: NONE** (p.119 images are CPWD cement-godown storage sketches; p.10 image is a signature block).
- **Invert levels: NONE.** **Conduit dimensions: only the item-1/item-2 size-class string "4.00 meter +25%"** (specification bucket, not a dimensioned drawing).
- **Survey control/datum: NONE stated** anywhere in the package.
- All 22 textual mentions of "drawings" are generic CPWD contract clauses (document-preference order, confidentiality, contractor obligations) — several explicitly say "drawings, **if any**".

## 6. BOQ AUDIT

The BOQ is a **costing document**, not a geometry record:

- **21,406.00 m³** desilting quantity is a billing volume (loose, post-draining, **−25 % voids** on payment). It is a legitimate *current-condition volumetric proxy* — consistent in scale with I&FC's separately-reported Kushak silt target (21,252 MT, 14-02-2025) though that target is a different department, scope and unit — but it yields **no width, depth, bed level or profile**.
- **290.00 m** sonar-survey quantity establishes only the contracted survey *length*, not the drain's geometry, and covers a small fraction of the ~2.6 km covered system.
- The SOQ references no drawings by number, includes no L-section sheets, and carries no chainages; nothing in the BOQ points to a surveyed bed level or cross-section dimension.
- The specification thickness "RCC slab 8–12 inch" applies to slabs the contractor may cut (item 3) — a works spec, not an as-built record of Kushak's slab.

## 7. SCIENTIFIC IMPACT

**No P0 geometry blocker is resolved** — as anticipated, the package is a procurement document, not a survey. What it *does* add to the evidence base:

1. **NEW constraint (D. PROCUREMENT_SPECIFICATION):** NDMC R-III prices the covered Kushak desilting in the **"width 4.00 m +25%" barrel class** (i.e., 4.0–5.0 m). This sits in tension with the DMP-2018 model values (25 m top / 10 m bottom) and with the depot-structure description (50 m wide, 5 bays), and is a material cross-check: either the R-III barrel is a genuinely narrower element than the depot structure, or the specification uses a nominal size bucket. It must stay a specification — but it now bounds what the department itself expects to find in the barrel.
2. **Confirmed future ACTUAL_SURVEY_DATA:** the contract *mandates* (i) a 290 m robotic sonar silt-level survey with a digital (Pipescape) report and (ii) 100 % CCTV/360° videography of the cleaned barrel. Post-award, these deliverables will be the first instrumented current-condition observations of the covered Kushak — a non-RTI research-request target once the L1 is known.
3. **Procurement chain clarified:** original invitation 27-05-2025 → receipt 13-06-2025 (this explains the separate Tender ID `2026_NDMC_289211_1` "result" trail) → re-invitation published 24-Aug-2026, closing 17-Sep-2026. The two IDs are stages of one NIT number and must not be merged.
4. **Provenance correction:** the previously-cited NIT "Clause 6" (L-sections held in EE(R-III) office) is not present in the authentic package; the earlier extract artifact is provenance-uncertain.

## 8. NON-RTI ACQUISITION STATUS

- **Actual survey data provided by the package:** **NO.**
- **Useful engineering constraints provided:** **YES** — barrel size-class specification (4.0–5.0 m), silt volume 21,406 m³, RCC slab thickness class 8–12″ (203–305 mm), sanctioned cost chain, and the defined future survey deliverables.
- **Otherwise:** only procurement information.

## 9. EXACT NEXT ACTION (one)

**On/after 17-Sep-2026, open the portal's "Results of Tenders" for `2026_NDMC_297503_1` to identify the L1 bidder — the future holder of the Item-2 sonar silt-survey electronic report and Item-1 CCTV record — and thereafter route a non-RTI research request for those deliverables.**

## 10. CHANGED / CREATED FILES

Created:
- `docs/DELHI_KUSHAK_PHASE6C_NIT52_PACKAGE_AUDIT.md` (this report)
- `data/delhi/raw/procurement/nit52/MANIFEST_NIT52_PACKAGE_20260912.json` (acquisition manifest with SHA-256 + portal metadata)
- `data/delhi/raw/procurement/nit52/work_396329.zip` (original archive, preserved byte-exact)
- `data/delhi/raw/procurement/nit52/extracted/NIT.pdf`, `extracted/BOQ_396329.xls` (verbatim extraction)
- `data/delhi/raw/procurement/nit52/extracted/NIT.txt` (pdftotext text layer, audit aid)
- `data/delhi/raw/procurement/nit52/extracted/_imgs/` (p119/p10 image renders used for the drawing audit)

Modified: **NONE.**

*Anti-fabrication note: every quoted value was read directly from the acquired files (SHA-256 pinned in the manifest); the CAPTCHA was solved by the ordinary human visual step; no specification was upgraded to a measurement; no missing geometry was reconstructed.*
