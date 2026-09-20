# DELHI KUSHAK — CATCHMENT REGIME AUDIT (PHASE 14C)

**Date**: 2026-09-16 · Companions: research narrative, timeline, crosswalk, and register `kushak_catchment_runoff_change_evidence.csv` (20 rows). Research-only; no model/twin/test/parameter/catchment changes.

---

## 1. SOURCES SEARCHED & DATASETS REVIEWED

**Official on-disk (previously acquired with provenance):** DMP 2018 main report + Appendix-XII extraction; NGT OA 6/2012 orders (13-01-2015, 06-08-2024, 09-04-2025 JIR, 20-08-2025); MPD 1976 inventory; NDMC 2007 Subcity Plan; CGWB 2011; PIB/CGWB 2023 (3.5 km²); MCD storm-drain doc (2.03 km²); NIT-52/2025-26 package; NMCG MPR Aug-2022; NDMC monsoon-plan 2025 coverage; Phase 14B connectivity register; project geometry/hydrology docs (WorldCover 2021 spec, delineation, reconciliation).

**External verification (this session):** PIB release 151440 (Kidwai Nagar schedule), NBCC/NCC/press for WTC Nauroji Nagar (HC restraint 2018, first office Jan-2024, construction complete May-2025), Barapullah Phase-1/2/3 timelines (TOI/The-Hindu/India-Today/NDTV-Profit/Construction-World/Hindustan-Times), Nature Communications 2024 (inter-dataset urban-land disagreement) + GAULCF (JAG).

**Datasets reviewed:** ESA WorldCover 10 m 2021 v200 (on disk, single epoch) · GAIA/GISA/WSE and GAULCF (literature context only — no download) · Copernicus GLO-30 DEM (catchment delineation, project-held) · Sentinel-1 (prior phase: zero street-level utility, urban radar shadow) · Bhuvan/NRSC/Bhuvan-LULC (no catchment-scale multi-epoch comparison located).

**Totals: TOTAL_SOURCES_REVIEWED=16 · OFFICIAL=10 · PEER_REVIEWED=2 · GIS_DATASETS=1** (WorldCover on disk; literature products counted as context, not datasets reviewed).

**Not accessible (recorded blockers):** PWD as-built drainage drawings for Barapullah Phase-2 · 2024 IFCD bathymetry output · DMP 2018 appendices beyond XII · official catchment polygon for any year · second WorldCover epoch validation.

---

## 2. HISTORICAL CATCHMENT DESCRIPTIONS (boundary evidence)

| Epoch | Source | Description | Polygon? |
|---|---|---|---|
| 1976 | MPD inventory | Named laterals only (Nauroji, Sunehripulla, AIIMS, Lajpat Nagar) | none |
| 2007 | NDMC plan | 11 km nallah, 4.7 km covered; 2 NDMC systems in | none |
| 2011 / 2023 | CGWB / PIB | 3.5 km² upper NDMC spine only | none |
| 2018 | DMP 2018 | Barapullah basin 376.27 km² (no Kushak-only figure) | none |
| 2023 | MCD doc | 2.03 km² = 502 acres for 3,220 m stretch | none |
| 2026 | Project D8 (U2/U3) | 27.66–28.40 km² urban corridor (provisional) | project-only |
| ~35.4 km² | historical (unreconciled) | plausibly 27.66 + Ridge headwaters + Lodhi feeders | none |

**Verdict: CONTESTED_METRICS_NOT_A_CHANGE.** No official polygon for any year; no in-window boundary reassignment/renaming documented → **CATCHMENT_BOUNDARY_STATUS_2015_2026 = STABLE (documentary)**; the provisional 27.66 km² working value is not modified.

---

## 3. DOCUMENTED URBANIZATION (LAND_USE_CHANGE_ITEMS=2)

- **East Kidwai Nagar GPRA (CR-004)** — 86 acres, Dec-2014 start, staged completion ~2019, AIIMS MoU 2017; INSIDE catchment; INCREASE_PLAUSIBLE; **delta unquantified** (EIA lists rainwater-harvesting pits; no net imperviousness number exists).
- **WTC Nauroji Nagar (CR-005)** — 2018 restraint → first office Jan-2024 → construction complete May-2025; INSIDE (on the J_5670 lateral); INCREASE_PLAUSIBLE; delta unquantified.

No other in-window redevelopment documents located for any named area (negative findings §7).

---

## 4. DOCUMENTED INFRASTRUCTURE CHANGES (INFRASTRUCTURE_CHANGE_ITEMS=4)

Phase-1 (2010, pre-window baseline) · Phase-2 (opened 28-07-2018, adjacent-to-mainstem, **drainage impact undocumented → UNKNOWN**) · Phase-3 (2015→2026, OUTSIDE catchment) · bus-depot deck (pre-existing envelope; no in-window change located).

## 5. DOCUMENTED DRAINAGE CHANGES (DRAINAGE_CHANGE_ITEMS=4)

Network-topology stability synthesis (CR-014; zero lateral-change documents) · NGT 2015 covering restraint (CR-010) · annual pre-monsoon desilting programmes (2024 season officially disputed; 2025 programme documented; **NIT-52 2025-26 is PRE-AWARD, not executed** — procurement ≠ completion) · bathymetry directed 2024, output non-public (gap, not change). **DOCUMENTED_DRAINAGE_REROUTES=0.**

## 6. SEWER/STORMWATER CHANGES (SEWER_STORMWATER_CHANGE_ITEMS=1)

Andrews Ganj SPS sewage trapping completed Aug-2022 (CR-008) — sewage component only; `runoff_generation_relevance=NO_CLEAR_EFFECT` (mission rule); storm-time SPS hydraulics undocumented (`connectivity=UNKNOWN`). **DOCUMENTED_CONTRIBUTING_AREA_CHANGES=0.**

## 7. EVENT LINKAGE

4 of 22 events placed into a known catchment/operational regime (2021 pre-intervention ×2; 2023 post-urbanization; 2024-06 pre-desilting contested) — full crosswalk: `DELHI_KUSHAK_EVENT_REGIME_CROSSWALK.md`. **EVENTS_WITH_KNOWN_REGIME_CHANGE=4 · EVENTS_WITH_UNKNOWN_REGIME=18.** No causal inference anywhere.

---

## 8. CONFLICTS (CONFLICTS_FOUND=2 — preserved, not averaged)

- **K1 area-metrics**: 3.5 vs 2.03 vs 27.66–28.40 vs ~35.4 km² — different metrics/epochs; safe interpretation: preserve all, keep 27.66 km² provisional working value; resolving evidence: official polygon (none public) or bathymetry output (non-public).
- **K2 construction-vs-impact**: Phase-2 documented completion vs zero documented drainage effect — safe interpretation: impact UNKNOWN, never treated as zero; resolving evidence: PWD as-built drainage drawings (access-restricted).

## 9. NEGATIVE FINDINGS (absence ≠ proof of absence)

1. No official catchment polygon/area for any specific year; 2. no 2015/2026 imperviousness figure (only 2021 epoch); 3. no as-built rerouting/new-drain/culvert-reconstruction record 2015–2026; 4. no bathymetry completion documentation; 5. no in-window depot redevelopment record; 6. no Phase-2 construction-diversion record for Kushak reaches; 7. no sewer-separation/outfall-closure orders for Kushak inputs; 8. no second remote-sensing epoch acquired/validated.

## 10. UNRESOLVED QUESTIONS

(a) magnitude of Kidwai/WTC imperviousness deltas; (b) Phase-2 drainage effect; (c) SPS storm-time hydraulics post-2022; (d) bathymetry result (conveyance/storage state); (e) unrecorded micro-connectivity changes; (f) validated multi-epoch imperviousness change.

## 11. FINAL COUNTERS

```
TOTAL_SOURCES_REVIEWED=16
OFFICIAL_SOURCES=10
PEER_REVIEWED_SOURCES=2
GIS_DATASETS=1
DIRECT_CATCHMENT_CHANGE_ITEMS=1
REGIONAL_CONTEXT_ITEMS=2
DRAINAGE_CHANGE_ITEMS=4
LAND_USE_CHANGE_ITEMS=2
SEWER_STORMWATER_CHANGE_ITEMS=1
INFRASTRUCTURE_CHANGE_ITEMS=4
CATCHMENT_BOUNDARY_CHANGE_ITEMS=2
DOCUMENTED_RUNOFF_REGIME_CHANGES=0        (direction-only: 2 rows INCREASE_PLAUSIBLE, unquantified)
DOCUMENTED_CONTRIBUTING_AREA_CHANGES=0
DOCUMENTED_DRAINAGE_REROUTES=0
EVENTS_WITH_KNOWN_REGIME_CHANGE=4
EVENTS_WITH_UNKNOWN_REGIME=18
CONFLICTS_FOUND=2
HIGH_CONFIDENCE_ITEMS=12
MEDIUM_CONFIDENCE_ITEMS=8
LOW_CONFIDENCE_ITEMS=0
CATCHMENT_STATUS_2015_2026=STABLE (documentary; contested area metrics preserved)
RUNOFF_REGIME_STATUS_2015_2026=UNKNOWN (direction-qualified; no quantified change)
TIER_A_GAPS_REDUCED=1                     (imperviousness-baseline context + dataset-uncertainty rationale documented)
TIER_A_GAPS_REMAINING=6                   (polygons, bathymetry output, Phase-2 as-builts, SPS storm hydraulics, second epoch, micro-connectivity)
MODEL_CHANGED=NO
DIGITAL_TWIN_CHANGED=NO
TESTS_CHANGED=NO
GIT_HEAD=d4ab4baceb56044fb860a5c67f81dee4199d3853
WORKTREE_STATUS=4 untracked research docs + gitignored CSV; nothing staged or committed
```
