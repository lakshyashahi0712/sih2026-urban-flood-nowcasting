# Phase 6F — I&FC DGPS/Echo-Sounder Kushak Survey: **Deliverables Acquisition Audit** (channels exhausted)

**Document ID:** `DELHI_KUSHAK_PHASE6F_IFC_2024_SURVEY_DELIVERABLES_ACQUISITION_AUDIT`
**Date:** 2026-09-16 · **Predecessor:** `DELHI_KUSHAK_PHASE6E_IFC_2024_SURVEY_ACQUISITION_AUDIT.md` (2026-09-12)
**Mission:** locate the *actual* deliverables of the IFCD bathymetric/topographic (DGPS + echo-sounder) survey of **Kushak / Sunehripul / Barapullah** directed by NGT OA 6/2012 order 06-08-2024 — in NGT filings/annexures, IFCD/GNCTD repositories, tender/contractor submissions, court records, departmental uploads, procurement attachments, archived/cached copies, and GIS/document services. **No RTI, no email, no procurement-as-completion inference, no geometry fabricated from the directive, no model/code/test changes.**

---

## 1. STATUS

**NOT ACQUIRED — ALL MANDATED PUBLIC CHANNELS EXHAUSTED. ZERO DELIVERABLE SURFACED.**
The audit closes with a decisive negative plus one **new primary discovery**: a **third survey-procurement round (FY 2026-27)** published days before this audit, unknown to Phase 6E. No award, no completion record, and no survey output (report, L-section, cross-section, sounding file, datum note) exists on any reachable public channel as of 2026-09-16.

## 2. MANDATED-CHANNEL SEARCH LEDGER

| # | Channel | Probes executed | Outcome |
|---|---|---|---|
| 1 | **NGT filings & annexures** | indiankanoon docid 116093574 probed (turns out to be a **duplicate of the known 06-08-2024 directive order** — no hidden content); searches: `"bathymetric"+"Barapullah"`, `"Sunehripul"`, `"Kushak"+"survey"` → only the directive order; on-disk OA 6/2012 order set (09-04-2025 JIR, 23-04-2025, 14-10-2025) re-checked — no survey output annexed | **NO DELIVERABLE** |
| 2 | **IFCD/GNCTD repositories** | Live `ifc.delhi.gov.in/tender/niq-cd-xii` (16-09-2026): lists **only the new round-3 NIQ** — no award history, no comparative statement; delhi.gov.in centralized-order search (`title=survey`, domain=IFC) → **zero rows**; I&FC "All Documents" pattern (Phase 6E) yielded nothing new | **NO DELIVERABLE** |
| 3 | **Tender/contractor submissions** | Aggregator searches (bidassist/tenderdetail-class) for any survey award → none; NicGeP: NIQ-scale sealed-quotation works are not e-published (6E finding stands); **round 3 is still OPEN** (closes 17-09-2026 14:00) — no award can exist yet | **NO DELIVERABLE** |
| 4 | **Court records (Delhi HC)** | Court-on-its-own-motion order 28-02-2025 and 29-01-2026 status report give reach lengths/handover facts only — no bathymetry, no survey annexure | **NO DELIVERABLE** |
| 5 | **Departmental uploads** | Archived I&FC `circulars-orders/` and `inline-files/annex7–10.pdf` (via Wayback) → training circulars, debarment order, defacement policy — unrelated | **NO DELIVERABLE** |
| 6 | **Procurement attachments** | The NIQs themselves are the only public attachments; no DPR, billing, or measurement book extract is published for any round | **NO DELIVERABLE** |
| 7 | **Archived/cached copies** | Wayback CDX filtered query **finally succeeded** (earlier attempts 503'd): 201 total captures of `ifc.delhi.gov.in/sites/default/files/*` (2024-08 → 2026-09); **7 doc-format matches, none survey-related** (other divisions' NIQs 26-07-2024 / 06-08-2024 + generic annexures). Neither the 2025-26/249 NIQ nor `niqcdxii1509.pdf` was **ever archived** | **NO DELIVERABLE** |
| 8 | **GIS/document services** | GSDL/DIFC REST (Phase 14B audit): 12 agency layers, content-blocked to this client; **no bathymetry/survey layer exists** in the service | **NO DELIVERABLE** |

## 3. PROCUREMENT-ROUND LEDGER (updated — 3 rounds, one NEW)

| Round | NIQ / date | Status | Award / completion |
|---|---|---|---|
| 1 (claimed FY 2024-25) | "NIQ 08-10-2024", claimed award 12-11-2024 ("Aar Pee", ₹2.45 lakh) | **LEAD_ONLY** — Phase 6B→6E downgrade stands; nothing new found this audit | No primary ever located |
| 2 (FY 2025-26) | **No. EE-CDXII/NIQ/2025-26/249, dt 08-10-2025**; quotes opened 10-10-2025; "urgent… completed within 03 days" | **VERIFIED** — primary PDF on disk (sha256 `be817613…`) | Award **UNKNOWN**; no completion evidence |
| 3 (FY 2026-27) — **NEW, this audit** | NIQ published **12–16 Sep 2026** (absent from the 12-09-2026 page snapshot; present live 16-09-2026); **Open 15-09-2026 12:00, Close 17-09-2026 14:00** per live NIQ CD-XII page | **VERIFIED NOTICE** — scanned 2-page PDF captured (`ifc_niq_cdxii_20260915_survey.pdf`, 426,055 bytes, sha256 `00783798…`, **no text layer**) | Bidding **open**; award impossible before 17-09-2026 |

**Interpretation flag (not asserted as fact):** three procurement rounds for the same scope class within ~23 months, with zero completion evidence for the first two, is *consistent with* repeated non-execution or urgent re-tendering — but non-execution is **not** established either; it is equally consistent with execution without publication. **Documented status of survey execution: NOT_ESTABLISHED for all three rounds.**

**Honest caveat on round-3 scope:** the "same DGPS/echo-sounder scope" attribution rests on the listing context, file naming, and the page title read in the live session — the PDF is a scanned image and **no text was extracted** (no OCR performed; nothing inferred from the images). Classified ASSUMED-pending-read; only its existence, dates, and URL are OBSERVED_OFFICIAL.

## 4. DELIVERABLE DISPOSITION (final)

Every candidate custodial channel was probed (EE CD-XII published record; NGT registry annexures; GNCTD centralized orders; Wayback; tender aggregators; GSDL). If the deliverable exists, it exists **only in physical/departmental custody** (EE, Civil Division-XII, I&FC, Basaidarapur — per the NIQ custody pattern) or in an NGT filing not yet made. Per the standing rule — *procurement ≠ completion* — the 06-08-2024 directive remains **directed, never evidenced as executed or delivered** in any public record.

## 5. GEOMETRY CONTENT AUDIT

**Unchanged from Phase 6E, and deliberately not extended:** no bed level, invert, chainage, RL, cross-section, coordinate, or datum value exists publicly. The round-3 PDF adds **zero measurable content** (scanned; no text layer; no values inferred from images). No geometry has been fabricated from the directive text, the NIQ scope lines, or jurisdiction records.

## 6. WHAT THIS AUDIT ADDED (vs Phase 6E)

1. **Round-3 discovery + captured artifact** — the first new primary document since 08-10-2025.
2. **Publication-window proof** (snapshot-delta method: absent 12-09-2026 → live 16-09-2026) — the first precisely bounded procurement-timeline fact for the chain since 08-10-2025.
3. **CDX negative secured** with a successful filtered query (all prior attempts 503'd).
4. **indiankanoon 116093574 resolved** as a duplicate of the 06-08-2024 directive — no unlocated compliance filing hides behind it.
5. **Centralized-order negative** (`title=survey`, domain=IFC → zero rows) — channel now formally closed.

## 7. REMAINING NON-RTI ROUTES (ranked, honest)

1. **Watch the round-3 outcome** — quotes open 15-09 and close 17-09-2026; an award/comparative-statement upload on the NIQ CD-XII page within days–weeks is the single highest-yield passive observation available.
2. **Post-17-09-2026 re-probe** of the NIQ CD-XII page and the I&FC tender tree for award uploads.
3. **NGT OA 6/2012 compliance affidavits** remain the official annexation route (monitor for new orders).
4. **Voluntary office-level request** to EE CD-XII — identified only, per prior audits; not exercised (mission prohibits email reliance).
5. **RTI remains the decisive route** — Phase 6E §9 conclusion stands unchanged: one targeted filing to EE CD-XII (award + deliverable, both rounds) closes both unknowns.

## 8. FINAL VERDICT

```
SURVEY_DELIVERABLES_FOUND            = 0
PROCUREMENT_ROUNDS_DOCUMENTED        = 3   (1 LEAD_ONLY · 1 VERIFIED primary · 1 VERIFIED notice, scanned)
ROUNDS_WITH_COMPLETION_EVIDENCE      = 0
NGT_COMPLIANCE_FILINGS_WITH_RESULTS  = 0
NEW_PRIMARY_ARTIFACTS_CAPTURED       = 1   (ifc_niq_cdxii_20260915_survey.pdf + manifest entry)
```

Any future reference to "the 2024 IFCD bathymetric survey" must carry the caveat: **directed 06-08-2024; procurement attempted in at least three rounds; executed-and-delivered status NOT ESTABLISHED; no deliverable public as of 2026-09-16.**

## 9. CHANGED / CREATED FILES

**Created:** this document; `data/delhi/raw/hydraulic/ifc_niq_cdxii_20260915_survey.pdf` (+ manifest entry in `data/delhi/raw/hydraulic/acquisition_candidates/manifest.json`).
**Modified:** nothing else — no code, no model, no tests, no parameters; nothing staged or committed.

---

*Anti-fabrication note: no awardee, amount, date, or measurement was inferred; the round-3 scope attribution is flagged ASSUMED pending a text read of a scanned document; the two older NIQ vintages remain unmerged; no tender wording was treated as measured geometry; no MSL/GTS datum assumed; procurement≠completion enforced on every row.*
