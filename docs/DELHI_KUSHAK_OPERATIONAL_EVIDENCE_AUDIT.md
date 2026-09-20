# DELHI KUSHAK — OPERATIONAL EVIDENCE AUDIT

**Phase**: Operational-controls research (research-only) · **Date**: 2026-09-16
**Companion artifacts**: `DELHI_KUSHAK_OPERATIONAL_EVIDENCE_RESEARCH.md` · `DELHI_KUSHAK_OPERATIONAL_TIMELINE.md` · `data/delhi/derived/research/kushak_operational_evidence.csv` (38 rows) · raw captures in `data/delhi/raw/research/operational/`

---

## 1. Sources searched

**Official/primary (web, live-verified):**
1. NDMC Budget 2021-22 Vol-II (ndmc.gov.in PDF, downloaded; p.524 extracted verbatim)
2. NMCG Delhi Monthly Progress Report, Aug-2022 (nmcg.nic.in PDF, downloaded; pp. 6/14/30 extracted)
3. NGT OA 6/2012 order 20-08-2025 via Indian Kanoon (DJB affidavit; Andrews Ganj SPS; 43-outfall table)
4. NDMC civil engineering department pages (desilting scope listings)
5. PWD Monsoon Flood Control Order 2017 (Scribd mirror of official document)
6. GNCTD Flood Control Order 2024 (Scribd mirror of official document)
7. GNCTD district flood-control pages (dmcentralnorth.delhi.gov.in — FCO 2026 landing)

**Press/secondary (dated):**
8. Times of India 27-07-2024 (Africa Avenue underpass event; NDMC + Northern Railway statements)
9. ETInfra/TOI 19-03-2025 (NDMC monsoon action plan, chairman/VC statements)
10. The Hindu 26-08-2026 (ITO pump deployment during event)
11. Big News Network 23-09-2021 (Moolchand/Pul Prahladpur pump capacities)
12. TOI Delhi edition 14-06-2024 (I&FC silt quantities; digital-library scan)
13. OTV via Facebook (Barapullah 14,000 MT silt removal; CM statement, late-2025)
14. LG Delhi official X account, 28-06-2024; DD News X, Feb-2025 (Moolchand upgrade inspection)

**Already-on-disk official extracts (verified, not re-fetched):**
15. NDMC Sub-city Development Plan 2007 (verbatim in repo)
16. CGWB Artificial Recharge case studies 2011 (verbatim in repo)
17. NGT judgment 13-01-2015 OA 6/2012 & 300/2013 (PDF on disk)
18. IIT Delhi Drainage Master Plan 2018 (verbatim extracts in repo)
19. NIT 52/EE(R-III)/2025-26 package (work_396329.zip; NIT.txt + BOQ on disk)
20. NGT Joint Inspection Report 05-03-2025 / order 09-04-2025 (HTML on disk)
21. HC CONT.CAS(C) 434/2022 status 28-01-2026 (court record in Phase 7D-15)

**Negative probes (queries that returned nothing usable):** PWD/I&FC 2023–2025 monsoon-order PDFs on official domains (only Scribd mirrors found); Kushak pump activation logs; pump-failure reports; desilting completion certificates; Africa Avenue/Satya Marg pump-house documentation; Kushak culvert/regulator operating records; pre-2015 NDMC pump commissioning records; I&FC drain-wise desilting portal.

## 2. Documents found vs not accessible

**Found and used (public):** items 1–4, 8–19 above (21 sources reviewed in depth).
**Found but partially accessible:** PWD Monsoon Book 2017 + FCO 2024 (Scribd mirrors; page-level pump tables not machine-extracted here); FCO 2023 (Scribd Revenue Directory copy — snippet-level only); FCO 2026 (government page references, full PDF not pulled this phase).
**Not publicly accessible (documented blockers):** NDMC/DJB/PWD pump activation and failure logs; daily desilting progress reports (contractually required under NIT-52 clause 12 but not published); as-built drawings (already classified P0 access-restricted in `DELHI_KUSHAK_OFFICIAL_ENGINEERING_RECORD_AUDIT.md`); DJB Andrews Ganj SPS design/capacity sheets; cGanga NDMC study (10 MLD DWF source, agenda-level only).

## 3. Kushak-specific vs generic evidence

- **Kushak-specific (named reach/system in source):** OP-PUMP-001/002/003, OP-PUMP-008/009 (southern "Kushak drain" SPS), OP-DES-001/002/009, OP-STR-001/002/003/004/006/009/010 + OP-NEG-003 → **17 rows**.
- **Generic Delhi-wide / adjacent-system (BACKGROUND only):** OP-DES-003/004/005/006/007, OP-PUMP-004/005/006/007/010b, OP-STR-007/008/011/012/013, OP-NEG-001/004 → 18 rows; plus 3 method/null rows.
- **Guard applied:** Delhi-wide documents were admitted only with event_relevance = BACKGROUND, except where the source explicitly names a Kushak reach (e.g., NMCG "Kushak drain at Andrews Ganj"; NDMC budget "UNDER BRIDGE AFRICA AVENUE"; NGT JIR depot reach; NIT-52 "Kushak Nallah").

## 4. Event-linked evidence (9 rows)

- **EVT-2024-06-28** (3 rows): LG desilting-pending statement (same day); I&FC silt quantities (14-06); CWC free-outfall boundary. → DIRECT ×1, INDIRECT ×2.
- **EVT-2024-07-26** (4 rows): pump operation during event (OVERWHELMED); 120+62 fleet; 23-reported/13-resolved same-day; construction-diversion/clogging claims. → **the only DIRECT pump-operation evidence in 2015–2026.**
- **EVT-2026-08-25** (2 rows): ITO pump deployment; "temporary accumulation" clearance framing (adjacent mainstem).

## 5. Negative controls

- **Zero** credible Kushak-specific FLOOD_NO-under-substantial-rainfall records found (OP-NEG-002, explicit null — silence NOT converted to FLOOD_NO).
- One **partial** negative control: ITO 26-08-2026 pump-assisted rapid clearance (OP-NEG-001) — not a FLOOD_NO.
- One **low-flow** state control (JIR 2025 DWF, OP-NEG-003) and one **boundary** control (free outfall EV-2024-06-28, OP-NEG-004).

## 6. Unsupported claims explicitly rejected

1. "Moolchand has 2×500 HP pumps" → **not** evidence they operated during any event (existence ≠ operation).
2. "NDMC budgeted a submersible pump for Africa Avenue (2021-22)" → **not** evidence of installation/commissioning (0/0 budget/actual columns in the volume).
3. "Pumps functioned efficiently" (NDMC, 26-07-2024) → accepted **only** as evidence pumps ran; the same statement documents they were overwhelmed — capacity claims rejected as hydraulic truth.
4. "I&FC collected 10/15 lakh tonnes (14-06-2024)" → **not** resolved into "Kushak was desilted before EV-2024-06-28" (contradicted in real time by LG statement of 28-06; city-wide ≠ reach-level).
5. "Desilting tender floated; completion expected June 2025" → **not** evidence work was completed (procurement ≠ completion).
6. "NDMC drain capacity 25 mm/h" → network-class admission only; **not** converted to Kushak discharge.
7. Northern Railway's "absent drains" attribution and NDMC's "construction diversion" attribution → recorded as **competing claims**; neither accepted as established mechanism.
8. Any inference of blockage from flooding, or of unobstructed flow from absent blockage reports → rejected (both directions).

## 7. Unresolved gaps (blocking improved constraint)

1. **Pump operation records** for any Kushak node, any event (activation times, run hours, failures).
2. **Post-desilting state observation** for the depot/Africa Avenue reaches (no public after-state exists; NIT-52 execution status unknown).
3. **Kushak rows** of PWD/FCO pump and regulator tables (2017/2023/2024 mirrors exist but page-level extraction pending).
4. **Commissioning status** of the 2021-22 Africa Avenue submersible pump.
5. **Regulator/outfall gate states** during compound events (FCO doctrine exists; no per-event logs).
6. **Moolchand upgrade completion** (2025 program) and its event performance.
7. **Andrews Ganj SPS capacity** and augmented-SPS timeline (proposed 2025 → commissioning unknown).
8. **Elevated-corridor/pier obstruction** documentation on Barapullah mainstem (hypothesis only; no public record found).

## 8. Model-safety verification

- `git rev-parse HEAD` = `d4ab4baceb56044fb860a5c67f81dee4199d3853` (unchanged baseline)
- `git diff HEAD -- backend/app/domain/delhi/digital_twin/` = empty
- `git diff --cached` = empty; nothing staged, nothing committed
- Digital twin tests: 652/652 passing (baseline re-verified this session); no test files touched
- Files created this phase: 3 tracked docs (`OPERATIONAL_EVIDENCE_RESEARCH.md`, `OPERATIONAL_TIMELINE.md`, this audit) + 1 pending tracked doc from prior approved plan (`PLAYBOOK_IMD_RAINFALL_ACQUISITION.md`); all data outputs under gitignored `/data/`
- MODEL_CHANGED=NO · DIGITAL_TWIN_CHANGED=NO · TESTS_CHANGED=NO

## 9. Final report

```
TOTAL_SOURCES_REVIEWED=21
KUSHAK_SPECIFIC_SOURCES=11
EVENT_LINKED_SOURCES=6
PUMPING_EVIDENCE_ITEMS=11
MAINTENANCE_EVIDENCE_ITEMS=9
STRUCTURAL_OPERATIONAL_ITEMS=13
NEGATIVE_CONTROL_ITEMS=4
HIGH_CONFIDENCE_ITEMS=29
MEDIUM_CONFIDENCE_ITEMS=9
LOW_CONFIDENCE_ITEMS=0
DIRECT_EVENT_OPERATIONAL_EVIDENCE=10
INDIRECT_EVENT_OPERATIONAL_EVIDENCE=14
KEY_TIMELINE_CHANGES=7   (2007 pumped-node designation; 2015 covering restraint; Aug-2022 Andrews Ganj SPS trapping completed; 2024 season disputed desilting + 26-07 pump-chain overwhelm; Mar-Jun-2025 depot desilting program + NIT-52; Sep-2025 wire-mesh screen + proposed SPS augmentation; Jan-2026 MCD→I&FC handovers)
CRITICAL_GAPS=8          (see §7)
MODEL_CHANGED=NO
DIGITAL_TWIN_CHANGED=NO
TESTS_CHANGED=NO
```
