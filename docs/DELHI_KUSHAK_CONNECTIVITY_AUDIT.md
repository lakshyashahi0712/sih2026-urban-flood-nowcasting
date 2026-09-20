# DELHI KUSHAK — CONNECTIVITY EVIDENCE AUDIT (PHASE 14B)

**Date**: 2026-09-16 · Companion documents: `DELHI_KUSHAK_DRAINAGE_CONNECTIVITY_RESEARCH.md` (narrative), `DELHI_KUSHAK_CONNECTIVITY_MATRIX.md` (matrix), register `data/delhi/derived/research/kushak_connectivity_evidence.csv` (30 rows). Research-only phase; no model/twin/test/parameter changes.

---

## 1. SOURCES SEARCHED

**Official documents (on disk, previously acquired with provenance):**
1. DMP 2018 Appendix XII junction tables (IIT Delhi for I&FC; extraction doc + raw) — **primary model-topology evidence**
2. DMP 2018 main report fulltext (`_dmp_v50_fulltext.txt`) — basin partition, Barapullah description
3. NGT OA 6/2012 judgment 13-01-2015 (Para 10 route description)
4. NGT OA 6/2012 order 22-11-2023 (DJB network report quoted verbatim — the connectivity chain)
5. NGT OA 6/2012 order 06-08-2024 (bathymetry directive; "subsidiary drains viz. Sunehripul drain and Kushak drain")
6. NGT OA 6/2012 order 09-04-2025 JIR (depot-reach through-flow; confluence definition)
7. NGT OA 6/2012 order 20-08-2025 (43 sewage outfalls, MLD table; DC de-silting/wire-mesh)
8. MPD 1976 drain inventory (`201_drains_mpd.pdf` / `44_drains.pdf`) — named laterals incl. Sunehripulla, Naoroji Nagar, AIIMS, Lajpat Nagar
9. NDMC Subcity Development Plan 2007 (s.9.3.1 drainage systems; s.9.1 Kushak 11 km / 4.7 km covered)
10. CGWB 2011 groundwater report (Kushak Nala pilot — headwaters, 3.5 km² upper catchment)
11. Phase 14A GSDL hydrography audit (`DELHI_GSDL_HYDROGRAPHY_INVESTIGATION.md`) — 157 KushakNallah segments with node connectivity fields
12. Project gate docs (`DELHI_CATCHMENT_DRAINAGE_EVIDENCE_GATE.md`, `DELHI_V2_DATA_AUDIT.md`) — Qudesia separation
13. India Water Portal 2016 article (secondary, "Sunehri drain, a sub-drain of Barapullah")

**Live GIS services probed this session (2026-09-16):**
14. GSDL DIFC `storm_drain_08082024` MapServer (12 agency layers; counts verified: NDMC 7,676, PWD 23,163, SDMC 2,844, I&FC 377; attribute queries return 0 rows — server quirk documented, not circumvented)

**Searches run (no new usable sources):** ifc.delhi.gov.in drain inventory/outfall schedules (service layer exists; content unqueryable from this client), DJB sewer network maps (none public for this corridor), NDMC GIS (no drain layer public), MCD GIS (no public drain inventory), India-WRIS (no sub-district storm network), CPCB drain inventory (used for Qudesia numbering via prior phase), Bathymetry-survey output (directed 2024; **non-public**).

**Total sources reviewed: 14** (12 official / 1 secondary press-summary / 1 live GIS service; GIS=2 counting the GSDL audit + live probe).

**Documents NOT accessible (recorded blockers):**
- DMP 2018 Appendices I–XI and XIII (outfall schedules, as-built appendices) — never published online
- 2024 IFCD bathymetric survey output of Barapullah/Sunehripul/Kushak — directed 06-08-2024, no public release located
- DJB sewer-network GIS for the corridor — not public
- NDMC's identity of "two systems" draining to Kushak — no annexure public
- IFCD official reach-naming schedule (to resolve the "khushak nala"/"Barapulla" naming conflict)

---

## 2. CONNECTION-STATUS BREAKDOWN (from the 30-row register)

| Status | Count | Rows |
|---|---|---|
| CONFIRMED_INTO_KUSHAK | 17* | CX-003,004,005,006,007,008,009,010,011,012,013,014,015,016,017,018,030 |
| CONFIRMED_THROUGH | 9 | CX-001,002,020,022,023,024,025,028,029 |
| SEPARATE_SYSTEM | 2 | CX-021 (Qudesia), CX-027 (Kudesia Bagh ≠ Kushak) |
| UNKNOWN | 2 | CX-019 (GSDL feature content today), CX-026 (Sunehri model identity) |
| CONFIRMED_FROM_KUSHAK | 0 | none documented |
| PLANNED_ONLY | 0 | none found (absence of plan docs is not proof none exist) |
| AMBIGUOUS | 1 (within CX-015/016 group) | AIIMS/INA/Lajpat Nagar individual join points |

*Bank/junction specificity is deliberately weak inside several INTO rows (e.g., 1976 "into Barapulla basin/right bank" statements); the connection fact is official, the geometry is not.

**Model-only connections (MODEL_ONLY 2018):** 8 — CX-001, CX-010, CX-011, CX-012, CX-013, CX-014, CX-025, CX-028 (+ design-inventory CX-018 flagged separately as DESIGN_INVENTORY per GSDL disclaimer).

**Confirmed connections with two independent official sources:** Nauroji Nagar→Kushak (1976 + 2018 model); Sunehri→Kushak-to-form-Barapulla (1976 + 2023 DJB, + 2025 JIR phrasing); Defence Colony→Kushak (2023 DJB + 2015 NGT + 2024 CC); Kushak→Barapullah→Yamuna (2023 DJB + 2025 JIR + 2024 directive + DMP model).

---

## 3. CONFLICTS FOUND (4 — all preserved; full table in research doc §9)

1. **"Kushak" naming**: NGT-2015 Para-10 system-level usage vs NGT-2023 DJB hydrographic usage (spine ends at confluence).
2. **Defence Colony join point**: "opposite Nizamuddin" (2015) vs "joins Kushak before Sunehri" (2023) — narrative vs departmental sequence; junction georeferenced in neither.
3. **Downstream trunk name**: Appendix XII labels trunk link C_937 "khushak nala"; DJB 2023 says "from this point called Barapulla" — template/labelling suspicion; connectivity continuity agreed by both.
4. **Sunehri model identity**: officially named system absent by name from Appendix XII; candidate sections JangpuraNallah / PanthNagarNallah unresolved.

Plus a cross-cutting provenance conflict: **departmental old records contain adverse slopes** (Nauroji 215.33; J_7549 old 210.010) "corrected" model-side by IITD — corrected model values are not as-built verification.

---

## 4. ELEVATION EVIDENCE

- **CONFIRMED_ELEVATIONS = 10 rows carry values** — all `DEPARTMENTAL_RECORD` or `DESIGN_INVENTORY` provenance (Appendix-XII model tables: J_5670 204.900; J_4771 208.114; J_3141 217.133; J_6182/J_6043 203.769; J_7549 203.752 top 208.336; J_12646 203.532; spine chain 216.841→203.752; GSDL 216.91→203.77; Kudesia Bagh 204.97; Nauroji corrected 208.137–211.541).
- **DEM_DERIVED_ELEVATIONS = 0 in the register** — DEM values deliberately excluded; any future use must carry `DERIVED — DEM ONLY — NOT SURVEYED`.
- **NO GTS-tied surveyed elevation exists publicly** for any Kushak structure or junction. Elevation "confirmation" is departmental/model-record confirmation, not survey.

## 5. HYDRAULIC-DIRECTION EVIDENCE

- **DOCUMENTED_OFFICIAL** direction exists only as narrative sequences (DJB 2023 join order; JIR 2025 confluence; 1976 outfall statements) — no gauge-, dye-, or survey-based direction measurement exists.
- **DOCUMENTED_MODEL_TOPOLOGY** direction exists in Appendix-XII node chains (upstream→downstream inverts, IITD-corrected).
- **No direction claim is converted to current hydraulic truth** without its MODEL_ONLY/DESIGN_INVENTORY qualifier. Through-flow direction at the depot reach is the only inspection-observed case (2025 JIR: flow ~1 ft through 2/5 bays at DWF).

## 6. TIER-A GAPS

**TIER_A_GAPS_REDUCED = 3**: (1) confluence definition/location-at-narrative-level now triple-sourced; (2) Nauroji Nagar connection now two-source-attested (was single-source); (3) the two NDMC systems' existence (count-level) now documented (was folklore).

**TIER_A_GAPS_REMAINING = 5**: (1) junction coordinates for all laterals; (2) as-built connectivity condition & surveyed inverts; (3) two NDMC systems' identities; (4) Sunehri model-section identity; (5) AIIMS/INA/Lajpat Nagar individual join points + storm-vs-sewer classification of Africa Avenue / Maharaja Agrasen street networks. The **single highest-value unresolved document** remains the 2024 bathymetric survey output (would address 1, 2, 5 simultaneously) — directed by NGT, not publicly released.

## 7. SCIENTIFIC SAFEGUARDS HONOURED

No connection inferred from proximity (every INTO/THROUGH row carries a named-source statement). OSM never used as proof (only as unverifiable coordinate hint, flagged non-authoritative). No dimension/invert/opening invented — every number is quoted from a named source. Conflicts preserved (4). Procurement ≠ completion respected (no PLANNED_ONLY claimed as existing). Sewer ≠ stormwater lateral (§5 caution). Model topology ≠ as-built (all 2018 rows flagged). DEM excluded from register. Catchment not redrawn. No RTI, no email reliance.

## 8. FINAL COUNTERS

```
TOTAL_SOURCES_REVIEWED=14
OFFICIAL_SOURCES=12
GIS_SOURCES=2
CONFIRMED_CONNECTIONS=26          (17 INTO + 9 THROUGH; *see register for per-row specificity)
CONFIRMED_INTO_KUSHAK=17
CONFIRMED_FROM_KUSHAK=0
CONFIRMED_THROUGH=9
SEPARATE_SYSTEMS=2
MODEL_ONLY_CONNECTIONS=8
PLANNED_ONLY_CONNECTIONS=0
AMBIGUOUS_CONNECTIONS=1
UNKNOWN_CONNECTIONS=2
CONFIRMED_ELEVATIONS=10           (all departmental/model/design-inventory provenance)
DEM_DERIVED_ELEVATIONS=0
HISTORICAL_CONNECTION_CHANGES=3   (2007 covering state; 2022 Andrews-Ganj sewage trapping; 2024-25 inspection/directive era)
CONFLICTS_FOUND=4
HIGH_CONFIDENCE_ITEMS=20
MEDIUM_CONFIDENCE_ITEMS=10
LOW_CONFIDENCE_ITEMS=0
TIER_A_GAPS_REDUCED=3
TIER_A_GAPS_REMAINING=5
MODEL_CHANGED=NO
DIGITAL_TWIN_CHANGED=NO
TESTS_CHANGED=NO
```
