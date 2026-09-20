# Phase 14A — Event Attribution & Acquisition Audit (Delhi / Kushak–Barapullah)

**Document ID:** `DELHI_KUSHAK_PHASE14A_EVENT_ATTRIBUTION_AUDIT`
**Date:** 2026-09-16 · **Companion:** `DELHI_KUSHAK_PHASE14A_HISTORICAL_EVENT_CATALOGUE.md`

---

## 1. Headline counts

```
TOTAL_CANDIDATE_EVENTS          = 22
INDEPENDENT_EVENTS              = 15
QUALIFIED_EVENTS                = 4
CONDITIONALLY_QUALIFIED_EVENTS  = 5
EXCLUDED_EVENTS                 = 13   (NOT_QUALIFIED: 5 uncertain spells + 2 continuations
                                        + 6 independent-but-unattributable/unforced events)
```

HIGH_ATTRIBUTION_EVENTS (≥1 HIGH observation): 9 · MEDIUM_ATTRIBUTION_EVENTS (≥1 MEDIUM, no HIGH): 1 · LOW/none: 12.
FLOOD_YES_EVENTS: 21 · CREDIBLE_FLOOD_NO_EVENTS: 0 qualified (1 non-event control row) · UNKNOWN-only events: 0 (all candidate events contain at least one FLOOD_YES record).
CWC_MATCHED_EVENTS: 13 (documented bounded or numeric boundary state) · CWC_UNAVAILABLE_EVENTS: 9.
HOURLY_RAINFALL_EVENTS: 1 · SUBDAILY_EVENTS: 2 (3-h buckets) · DAILY_ONLY_EVENTS: 4 (3 flood events + 1 documented non-event control) · NONE_DOCUMENTED forcing: 12.

## 2. Attrition funnel (explicit)

| Stage | Count | Mechanism |
|---|---:|---|
| Raw flood records acquired | **878** | 647 GSDL raw points (date-expanded to 1,004 normalized observations) + 211 DTP gazetted rows + 13 DTP alerts + 7 dated press/official records |
| → Dated observations | **1,325** | multi-date cells expanded (301 DTP gazetted dated rows); verbatim preservation; 1 FLOOD_NO control |
| → Matched to candidate event windows | 1,069 | 256 observations fall on dates outside the 22 defined storm windows (scattered singletons, retained in catalogue) |
| → Spatially attributable within windows (HIGH/MED) | 51 | RULE_A / RULE_C fire (63 HIGH/MED catalogue-wide; 12 fall outside event windows) |
| → Candidate events | 22 | storm-window aggregation (date-cluster + documented-event evidence) |
| → Independent events | 15 | −2 CONTINUATION (same-storm tails), −5 UNCERTAIN (unseparable recurring bursts) |
| → Final QUALIFIED events | **4** | require independent + credible obs + HIGH/MED attribution + documented forcing |
| → + CONDITIONALLY_QUALIFIED | **5** | one soft deficiency each (missing station forcing) |

No stage inflated the count: raw→dated expansion is a provenance-preserving row split (647→1,004 GSDL; 211→301 DTP gazetted), and event aggregation runs strictly downward: **878 raw → 1,325 dated → 1,069 matched → 51 attributable-in-window → 22 events → 15 independent → 4 qualified (+5 conditional)**.

## 3. Attribution hierarchy and exact rules

Order of evaluation; `ATTRIBUTION_BASIS` records the rule fired.

| Rule | Class | Evidence basis | Count |
|---|---|---|---:|
| **COMPETING** (named competing system in location text) | UNKNOWN | Yamuna mainstem/backwater (Bhairon, Sarai Kale Khan…), Chirag Delhi southern spine (Panchsheel, GK, Andrews Ganj…), northern Yamuna system (Minto, ITO, Firoz Shah, Nigam Bodh…), Najafgarh west | 190 |
| **RULE_A** named corridor connectivity, distance sanity ≤800 m | HIGH | Documented drainage: NGT-2015 southern-spine named drains, NDMC-2007 alignment, DMP-2018 basin assignment; corridor roads (AIIMS, Aurobindo, Moolchand, Sewa Nagar, Defence Colony, South Extension, Barapullah, LLRM, Africa Avenue, Bhikaji, INA, Sarojini, Satya Marg, Kidwai, JLN Stadium, Bhishma Pitamah, Lodhi) | 44 |
| RULE_A keyword but distance far | UNKNOWN | keyword present but point >800 m from corridor — prevents Minto-like false positives | 2 |
| **RULE_C** catchment topology (inside 27.66 km² U2 polygon) | MEDIUM | DEM-derived working catchment (provisional); supersedes pure distance | 19 |
| **RULE_E** distance ≤300 m only | LOW | weak support only; excluded from constraints | 2 |
| no match | UNKNOWN | outside catchment, >300 m, no keyword | 1,068 |

Distance was computed only AFTER rule A/C tests against the projected (EPSG:32643) 5,027.6 m corridor centerline; it never promoted an observation by itself. DEM flow direction was used only through the catchment polygon (RULE_C) and is documented as DEM_FLOW_DIRECTION ≠ SURVEYED_DRAINAGE_CONNECTIVITY.

Worked example of the anti-proximity discipline: `Outer Ring Road | Munirka Village` sits inside the polygon but is keyword-negative → MEDIUM via RULE_C with distance recorded (3,528 m, polygon margin) — never HIGH.

## 4. Event matching rules

1. A storm window is defined by convergent evidence: ≥5-point GSDL date clusters, DTP gazetted date clusters, the on-disk 6-event inventory (EV-01…EV-06), dated press records, or IMD district exceedances.
2. All observations within [DATE_START, DATE_END] belong to one EVENT_ID; counts aggregate (e.g., EVT-2023-07-08: 348 observations, 8 HIGH + 8 MEDIUM).
3. Windows never overlap; multi-day spells remain single events with a span, never one event per day.
4. Mainstem/competing-system observations (e.g., 13-Jul-2023 Sarai Kale Khan class) either map to COMPETING=UNKNOWN or form separate non-corridor context; they never become Kushak response constraints.

## 5. Independence decisions (per event, documented)

| Event | Independence | Basis |
|---|---|---|
| EVT-2021-09-13 | CONTINUATION | tail day of the 11-Sep storm system |
| EVT-2023-07-15 | CONTINUATION | recession-phase rain of the same July-2023 synoptic system |
| EVT-2024-07-24, -08-07, -08-20, -08-29, -09-10 | UNCERTAIN | recurring bursts within weeks; no station series to separate or merge |
| all others | INDEPENDENT | distinct documented storm systems |

## 6. Quality classification rules (no numeric scores)

QUALIFIED = INDEPENDENT ∧ ≥1 credible observation (FLOOD_YES/FLOOD_NO) ∧ ≥1 HIGH/MEDIUM attribution ∧ documented forcing (resolution ∈ {HOURLY, SUBDAILY_3H, DAILY}).
CONDITIONALLY_QUALIFIED = as above but forcing NONE_DOCUMENTED (or single soft deficiency; continuations with attribution would fall here, none do).
NOT_QUALIFIED = fails attribution or credibility, or is a documented non-event control (EVT-2026-01-23).
CWC availability is never a disqualifier; every event carries `CWC_STAGE_AVAILABLE` and source/confidence.

## 7. Acquisition blocker log (nothing silently dropped)

| Route | Attempt | Result | Consequence |
|---|---|---|---|
| CWC live bulletins (47 probed dates, 2021/2025/2026) | direct GET, controls on known-live URLs | all 404; controls 200 → files never existed at path for those dates | 2025/2026 events lack CWC state |
| CWC 2021-07-13 wayback capture | 3 downloads | server-side truncation (100,225/114,400 B) | event day bounded via 07-12/07-14 bulletins instead |
| IMD Pune data-supply portal | direct probes | pages 404 | no station archive; no email follow-up per constraint |
| India-WRIS NWDP | open CKAN API succeeded | rolling 28-day window only | 2026-08-25 forcing obtained; no history |
| data.gov.in | resource probe | timeout (WAF) | no data |
| Sentinel-1 | prior on-disk audit | NO-GO for Kushak street-level | not used |
| Aab Prahari | prior on-disk audit | restricted, no public DB | documented gap |
| ffs.india-water.gov.in historical API | prior on-disk audit | IAM-gated | no numeric stage for 2021/2024-08 |

## 8. Method reproducibility statement

All attribution/aggregation was executed by ephemeral commands; deterministic builders are preserved (gitignored) at `data/delhi/derived/validation/kushak_phase14a/_build_observations.py` and `_build_events.py`, with the geometry inputs (`kushak_corridor_centerline.geojson`, `kushak_watershed_u2.geojson`), keyword rule tables, window definitions, and CWC state map verbatim in code. Re-running the two builders reproduces both CSVs byte-identically from the archived raw evidence. Raw retrieval manifest with hashes: `data/delhi/raw/validation/phase14a/manifest.json`.

**Events requiring further source verification:** EVT-2026-01-23 (FLOOD_NO control), EVT-2026-08-25 (corridor point unnamed), EVT-2025-07-30 (landmarks via on-disk inventory row), EVT-2024-08-20 (Minto/Firoz Shah = northern system; corridor relevance unproven).
