# Phase 14A — Multi-Year Historical Flood Event Catalogue (Delhi / Kushak–Barapullah)

**Document ID:** `DELHI_KUSHAK_PHASE14A_HISTORICAL_EVENT_CATALOGUE`
**Date:** 2026-09-16 · **Mode:** RESEARCH + DATA ACQUISITION ONLY. No model code, no hydraulic parameters, no calibration, no GLUE, no RTI, no email-dependent acquisition. No file under `backend/` was modified.

**Companion document:** `docs/DELHI_KUSHAK_PHASE14A_EVENT_ATTRIBUTION_AUDIT.md` (attrition funnel, rule tables, blocker log).

---

## 1. Coverage

| Field | Value |
|---|---|
| Target period | 2015–2026 (not forced) |
| **Actual observation-backed coverage** | **2021-05-19 → 2026-08-25** |
| Years with zero dated observations located | 2015, 2016, 2017, 2018, 2019, 2020 |
| Primary occurrence layers | GSDL `waterlogging1` (2023–2024 seasons), DTP gazetted monsoon-2021 table, DTP advisories (2023–2024), dated press (2025–2026) |

2015–2020 coverage was probed and documented as absent, not assumed: the DTP gazetted table's earliest corridor-relevant row is 19.05.2021; the Wayback CWC index begins 2020; no GSDL layer predates 2023.

## 2. Sources and acquisition verdicts (2026-09-16)

| Source | Route | Verdict |
|---|---|---|
| GSDL `waterlogging1` (Layers 0, 1) | Live ArcGIS REST re-query | **NO_DRIFT** — 473 + 174 features, attribute-identical to 2026-09-11 archive |
| Delhi Traffic Police gazetted waterlogging table (Monsoon 2021) | Wayback capture 2024-03-18 of the HTTP-403 page | **ACQUIRED — 211 official rows → 301 dated observations** (incl. Aurobindo Marg ×INA–AIIMS underpass 29.07 / 21.08 / 11.09.2021; Moolchand underpass 31.08 / 11.09.2021; Africa Avenue 01.09.2021) |
| CWC daily flood bulletins | Live URLs (47 dates: all 404; controls 200) + **Wayback CDX (511 archived URLs)** | **ACQUIRED for 2021-07/08/09 + 2024-08 windows** — 29 bulletins parsed; bounded ORB states (see §7). No numeric stage for these windows (bulletins tabulate only above-warning sites) |
| IMD station archive (Safdarjung / Palam / Lodhi / Ridge) | IMD Pune data-supply portal | **BLOCKED** — registration pages HTTP 404; no instant product; no email follow-up per constraint |
| IMD daily rainfall (district/state) | India-WRIS NWDP CKAN datastore (open API) | **PARTIAL** — rolling 28-day window only (2026-08-19→09-15); 280 Delhi rows saved; gives 2026-08-25 event forcing |
| Sentinel-1 SAR | Prior on-disk audit | NO-GO for Kushak street-level (prior verdict unchanged; never used as occurrence) |
| IITD Aab Prahari | Prior on-disk audit | RESTRICTED (no public DB) — documented gap |

Raw evidence + retrieval manifest: `data/delhi/raw/validation/phase14a/manifest.json`.

## 3. Deliverable files

| File | Rows | Content |
|---|---|---|
| `data/delhi/derived/validation/kushak_historical_observations.csv` | **1,325** | Event-level observations with full provenance, FLOOD_STATUS, attribution |
| `data/delhi/derived/validation/kushak_historical_events.csv` | **22** | Storm-window events with matching, independence, quality, CWC, antecedent, diversity |
| `data/delhi/derived/validation/kushak_phase14a/gsdl_attribution_intermediate.csv` | 1,004 | Per-point attribution + corridor distance (deterministic, reproducible) |
| `data/delhi/derived/validation/kushak_phase14a/dtp_gazetted_waterlogging_hotspots_2024wayback.csv` | 211 | DTP gazetted table verbatim extraction |

Observation composition: GSDL 1,004 (FLOOD_YES, native GPS) · DTP gazetted 2021: 301 (FLOOD_YES, landmark text) · DTP advisories 13 (FLOOD_YES) · dated press/official 6 (FLOOD_YES) · documented non-event control 1 (**FLOOD_NO**, see §6). Attribution: HIGH 44 · MEDIUM 19 · LOW 2 · UNKNOWN 1,260.

## 4. Rainfall events (resolution preserved exactly as documented)

| Event | Forcing (documented) | Resolution | IMD intensity bin |
|---|---|---|---|
| EVT-2024-06-27/28 | 228.1 mm/24 h Safdarjung; 149+74 mm/3-h buckets; **91 mm/h peak hour OBSERVED_DIRECT**; Lodhi 192.8 mm | HOURLY (2 direct hourly observations + 3-h buckets) | EXTREME |
| EVT-2023-07-08/09/10 | 153.0 + 126.1 mm days; 77.3 mm/3-h burst; 2-day 279.1 mm | SUBDAILY_3H (hourly rows on disk are DERIVED_BLOCK_ALLOCATION) | EXTREME |
| EVT-2021-09-11 | 117.9 mm/24 h; 80 mm/3-h 05:30–08:30 IST | SUBDAILY_3H | HIGH |
| EVT-2021-07-13 | 133.8 mm/24 h Safdarjung (then-record July day) | DAILY | HIGH |
| EVT-2025-07-30 | 129.8 mm/24 h | DAILY | HIGH |
| EVT-2026-08-25/26 | 102.2 mm district max (Central Delhi, IMD/NWDP); NDMC apology | DAILY | HIGH |
| EVT-2026-01-23 | 28.4 mm/24 h (winter WD; documented NON-flood) | DAILY | LOW |
| 12 further events | DTP-gazetted/GSDL-cluster event days; **no station total located** | NONE_DOCUMENTED | UNKNOWN |

No hourly rainfall was manufactured from daily totals. No 3-h bucket was disaggregated. Missing periods were not interpolated.

## 5. Event matching and independence

Observations sharing a storm window belong to one `EVENT_ID`; 326 observations on 8–9 Jul 2023 = **one event** (plus 18 on 10 Jul inside the same window), not 344 events. 22 candidate storm windows were defined from the GSDL date histogram (≥5-point clusters), DTP gazetted date clusters, the on-disk 6-event inventory, and dated press.

**Independence classes:** INDEPENDENT **15** · CONTINUATION **2** (EVT-2021-09-13 tail of the 11-Sep storm; EVT-2023-07-15 recession-phase rain of the same July-2023 synoptic system) · UNCERTAIN **5** (the late-monsoon 2024 recurring-burst spells — distinct bursts within one week that no available station series can separate; deliberately not counted as independent sample mass).

## 6. FLOOD_STATUS discipline

- `FLOOD_YES` (1,324) — documented occurrence in an official/secondary dated source.
- `FLOOD_NO` (1) — **EVT-2026-01-23 only**: the on-disk inventory asserts no waterlogging and normal traffic for the 23-Jan-2026 winter event. Flagged `verification pending` in the observation row; it is a non-flood control, not a hydraulic constraint.
- `UNKNOWN` — every date without a located record. **No record was ever converted to FLOOD_NO** (years 2015–2020 and all unlisted 2023–2024 dates remain UNKNOWN).
- Depth/duration: preserved verbatim only where a source reports it (DTP categorical bands, press narrative). No qualitative-to-numeric conversion anywhere.

## 7. CWC downstream boundary (indicator only — never equated to Kushak stage)

| Boundary state | Events |
|---|---|
| BELOW_WARNING (documented, bounded) | EVT-2021-07-13, -07-19, -08-21, -08-31, -09-11, -09-13, EVT-2023-07-08 (pre-compound phase), EVT-2024-06-27, EVT-2024-08-07, -08-20, -08-29 |
| ABOVE_WARNING / COMPOUND | EVT-2021-07-28 (31.07–02.08), EVT-2023-07-15 (207.27 m, receding), EVT-2023-07-08→13 (crossed WL 10 Jul → record 208.66 m 13 Jul) |
| UNKNOWN (not probed / unavailable) | EVT-2023-05-27, -07-26, -09-10, EVT-2024-07-24, -07-31, -09-10, EVT-2025-07-30, EVT-2026-01-23, EVT-2026-08-25 |

Method note: for 2021/2024-08 windows the numeric stage is NOT recoverable (bulletins list only above-warning stations), but each bulletin's *national above-warning table* is populated, so absence of the Delhi Railway Bridge row is an **official bounded observation**: stage < Warning Level 204.50 m. Discriminative validity demonstrated: ORB rows ARE present in the 2021-07-31→08-02 bulletins.

## 8. Antecedent conditions

Only where on-disk documentation permits: EVT-2024-06-27 (dry antecedent, SCEN-03 reasoning), EVT-2023-07-08 (saturated multi-day, SCEN-02), EVT-2021-09-11 (monsoon-active; magnitude unknown). All labeled DERIVED. Numeric 24 h/72 h/7 d antecedent totals are NOT derivable for any event because no multi-year daily station series could be acquired — recorded as `NOT_DERIVABLE` per event. No soil-moisture inference.

## 9. Event diversity

Intensity bins use IMD's official daily classifications (64.5 / 115.6 / 204.5 mm thresholds — documented, not invented); duration bins are ordinal (SHORT ≤1 d, MEDIUM 2–3 d, LONG ≥4 d). No CWC data was required for qualification; CWC-unavailable events are flagged, not disqualified.

## 10. Scientific safeguards (verbatim preservation)

- **FLOOD_YES ≠ FLOOD_NO** — occurrence and non-occurrence are different evidence classes; one FLOOD_NO control exists, verified against its source text.
- **NO_RECORD ≠ FLOOD_NO** — absence of a record (2015–2020; unlisted dates) is UNKNOWN.
- **PROXIMITY ≠ CAUSAL_ATTRIBUTION** — distance was used only as weak support (RULE_E, 2 observations); no observation is HIGH/MEDIUM on distance alone.
- **MULTIPLE_REPORTS_IN_ONE_STORM ≠ MULTIPLE_INDEPENDENT_EVENTS** — 348 observations on 8–10 Jul 2023 = one event.
- **DAILY_RAINFALL ≠ HOURLY_RAINFALL** — per-event resolution declared explicitly; derived hourly rows flagged, never treated as observed.
- **CWC_STAGE ≠ KUSHAK_STAGE** — CWC rows are downstream boundary indicators only.
- **DEM_FLOW_DIRECTION ≠ SURVEYED_DRAINAGE_CONNECTIVITY** — DEM/catchment topology supports only MEDIUM (RULE_C); named-connectivity (RULE_A) rests on documented drainage, not terrain inference.

## 11. Critical deliverable — how many independent events can actually constrain Kushak?

**4 QUALIFIED events** (independent, credible observations, HIGH/MEDIUM attribution, documented forcing with resolution):

| Event | Attribution | Boundary (CWC) | Forcing resolution | Why it constrains |
|---|---|---|---|---|
| **EVT-2024-06-27/28** | 7 HIGH + 3 MED | Free outfall (below WL, HIGH conf) | HOURLY (91 mm/h direct) | Cleanest single event: extreme burst + dry antecedent + bounded free outfall + corridor surcharge points |
| **EVT-2023-07-08/09/10** | 8 HIGH + 8 MED | Below WL → **compound** (record 208.66 m 13 Jul) | SUBDAILY_3H | The compound-mode counterpart; saturated antecedent; multi-burst |
| **EVT-2021-09-11** | 5 HIGH | Free outfall (HIGH conf, same-day bulletin) | SUBDAILY_3H | Independent replication of the pluvial-surcharge mode |
| **EVT-2021-07-13** | 4 HIGH | Free outfall (HIGH conf) | DAILY | Record-July-day deluge; daily-resolution forcing |

**Plus 5 CONDITIONALLY_QUALIFIED** independent events (EVT-2021-07-19, -07-28, -08-21, -08-31, EVT-2023-05-27): corridor-attributed observations + bounded CWC states, but no located station rainfall total (forcing `NONE_DOCUMENTED`) — usable for spatial-pattern validation, not for forcing-constrained inference without further source verification.

**Breakdown of the 4 constraint-capable events:** attribution — 3 high-dominant (2024-06-27: 7H/3M; 2021-09-11: 5H; 2021-07-13: 4H), 1 balanced (2023-07-08: 8H/8M) · flood polarity — 4 flood_yes, 0 credible flood_no (the single FLOOD_NO control is not qualified as an event) · resolution — 1 HOURLY, 2 SUBDAILY_3H, 1 DAILY · CWC — 4/4 with a documented bounded boundary state (3 free-outfall, 1 below-warning→compound).

**MOST_INFORMATIVE_EVENTS:** EVT-2024-06-27 (identification-grade), EVT-2023-07-08 (validation-grade compound counterpart), EVT-2021-09-11 (independent replication).
**DATA_POOR_EVENTS:** the 5 CONDITIONALLY_QUALIFIED 2021/2023 events (forcing missing) + all UNCERTAIN 2024 spells.
**EVENTS_REQUIRING_FURTHER_SOURCE_VERIFICATION:** EVT-2026-01-23 (FLOOD_NO control), EVT-2026-08-25 (corridor point not yet named), EVT-2025-07-30 (corridor landmarks rest on on-disk inventory row), EVT-2024-08-20 (Minto/Firoz Shah = northern system; corridor relevance unproven).

## 12. Major gaps

1. **IMD station archive 2015–2026 (daily, a fortiori sub-daily) — the single biggest blocker.** Registration pages 404; NWDP exposes only a rolling 28-day window. A station daily series would (a) force the 5 conditional events, (b) enable numeric antecedent indicators, (c) let the 2024 UNCERTAIN spells be separated or merged definitively.
2. **CWC numeric stage for 2021/2024-08 windows** — only bounded states; ffs.india-water.gov.in historical archives remain unauthenticated-inaccessible.
3. **2025 season occurrence layer** — GSDL Layer 1 is 2024-season; no 2025 points; only press narrative for EVT-2025-07-30.
4. **2015–2020 occurrence records** — no public dated point source located at all.
5. **Depth** — no source reports instrumented depth; categorical bands only (unchanged from prior phases).

**NEXT_RESEARCH_GAP (Phase 14B input):** acquire the IMD Safdarjung daily series (data.gov.in RTI-exempt datasets, IMD Pune supply portal via human applicant, or published daily-weather-report compilations) and re-probe CWC/IMD archives via additional archive services (archive.today, national web archives). This converts up to 5 conditional events and 5 uncertain spells into testable events and would roughly triple the usable catalogue.

---

*No digital-twin file, test, or hydraulic parameter was read-modified or written. All computations were ephemeral commands whose methods are documented here and in the companion audit; builder scripts live under gitignored `data/delhi/derived/validation/kushak_phase14a/` and are not repository code.*
