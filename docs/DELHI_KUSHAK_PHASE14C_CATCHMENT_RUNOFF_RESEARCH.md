# DELHI KUSHAK — PHASE 14C: CATCHMENT / RUNOFF-REGIME CHANGE RESEARCH

**Phase**: 14C — catchment & runoff-regime change (research-only; no model, twin, test, parameter, or catchment-boundary changes)
**Date of research**: 2026-09-16 · **Register**: `data/delhi/derived/research/kushak_catchment_runoff_change_evidence.csv` (20 rows × 21 columns) · **Timeline**: `DELHI_KUSHAK_CATCHMENT_CHANGE_TIMELINE.md` · **Audit**: `DELHI_KUSHAK_CATCHMENT_REGIME_AUDIT.md` · **Crosswalk**: `DELHI_KUSHAK_EVENT_REGIME_CROSSWALK.md`

**Scope note.** The working catchment remains frozen at **27.66 km² (U2 provisional)** — untouched by this phase. Every documented change below is classified by provenance (OBSERVED_OFFICIAL / DERIVED / ASSUMED / UNKNOWN), hydrologic relevance direction only (no coefficients, no runoff estimates), and completion status. Procurement ≠ completion; planned ≠ observed; conflicts preserved.

---

## 1. PRIMARY ANSWER

**Did the Kushak drainage catchment or its runoff-generating characteristics change materially between 2015 and 2026?**

- **Catchment boundary: STABLE (per documentary record).** No official document evidences boundary reassignment, basin renaming, or area transfer during the window. The multi-agency area *figures* conflict (3.5 / 2.03 / 27.66–28.40 / ~35.4 km²) — but those are **different metrics at different epochs, not evidence of change** (CONTESTED_METRICS_NOT_A_CHANGE, CR-015).
- **Drainage network: STABLE per documentary record.** Phase 14B found zero documents of construction/removal/rerouting/disconnection for any named lateral 2015–2026 (CR-014). The NGT 2015 covering restraint froze further covering (CR-010). Caveat: this is *documentary* stability — no as-built survey exists to instrument it.
- **Runoff-generating characteristics: TWO DOCUMENTED IN-CATCHMENT REDEVELOPMENTS**, direction INCREASE_PLAUSIBLE, **magnitude unquantified** — East Kidwai Nagar GPRA (86 acres, Dec-2014 start, staged completion to 2019) and WTC Nauroji Nagar (2018–2025, on the Nauroji Nagar lateral). No before/after imperviousness measurement exists; none is fabricated here.
- **Quantified regime change: NONE DOCUMENTED.** No source provides a catchment-scale imperviousness delta, a contributing-area change, or a drainage reroute for the window. RUNOFF_REGIME_STATUS_2015_2026 = **UNKNOWN (direction-qualified)**.

---

## 2. LAND-USE / URBANIZATION (documented)

| Change | Location | Period | Completion | Catchment position | Register |
|---|---|---|---|---|---|
| NBCC East Kidwai Nagar GPRA redevelopment — 2,444 houses → 4,608 apartments, 78 residential + 4 office towers, 86 acres; AIIMS residential expansion MoU Jan-2017 (built-up 72,766 → 5,99,810 sq m) | East Kidwai Nagar (28.5748N, 77.2173E — adjacent to Kushak channel at the CS-03 geometry location) | Dec 2014 → staged completion ~2019 | COMPLETED_STAGED (per PIB/press schedule revisions; ministerial direction to Dec-2018) | **INSIDE** | CR-004 |
| WTC Nauroji Nagar commercial redevelopment (NBCC/NCC) | Nauroji Nagar — directly on the lateral that outfalls to Kushak at J_5670 | 2018 (HC restraint) → first offices Jan-2024 → construction complete May-2025 | COMPLETED_2025 (construction); phased occupancy from 2024 | **INSIDE** | CR-005 |

**Hydrologic classification (direction only):** both rows carry `runoff_generation_relevance = INCREASE_PLAUSIBLE`, `contributing_area_relevance = NO_CHANGE_DOCUMENTED`, `drainage_connectivity_relevance = NO_CHANGE_DOCUMENTED`. The NBCC EIA records on-site modular rainwater-harvesting pits and internal colony drainage discharging to the adjacent MCD/PWD nallah — a documented *mitigation feature*, but no source quantifies the **net** imperviousness delta. That delta remains UNKNOWN; no percentage is invented.

Other named areas (Africa Avenue, INA, AIIMS, Chanakyapuri, Lodhi Road, Defence Colony, Andrews Ganj, Maharaja Agrasen, Jangpura, Sewa Nagar, Kushak Bus Depot): **no additional completed-redevelopment documents located for the window** (negative findings §7). The depot deck (1,050 m × 50 m, 4×4 m pier grid) is a pre-existing structural envelope with **no in-window construction/redevelopment record found** (CR-013) — and deck dimensions are not convertible to catchment imperviousness (mission rule).

---

## 3. IMPERVIOUSNESS / REMOTE-SENSING EVIDENCE

- **On disk (single epoch)**: ESA WorldCover 10 m **2021 v200** clipped to the 27.66 km² catchment — 276,636 valid pixels; built-up 49.17% (+0.26% other impervious); nominal directly-connected impervious baseline EIA = 0.70 (34.42% of catchment) (CR-006). This is a **2021 snapshot, not a change measurement**.
- **No second epoch acquired.** A 2015-vs-2026 comparison would require acquiring/validating another product epoch (WorldCover 2017 v100, Dynamic World NRT, GHSL built-up series). Not performed this phase; no DELTA claimed.
- **Peer-reviewed context (why no number is claimed)**: the multi-product urban-land literature shows inter-dataset disagreements as large as the signals themselves — Nature Communications 2024 documents a **+297.4%** spread across global urban estimates among the longest-series products (GAIA/GISA/WSE); GAULCF (2001–2020) shows near-doubling of global impervious with strong product dependence (CR-007). Any Kushak-scale delta from dataset A vs B could differ by more than the true change. This is recorded as REGIONAL_CONTEXT, explicitly not a catchment measure.
- **DIRECT_CATCHMENT_MEASURE vs CITY/REGION_CONTEXT is enforced in the register** (`inside_working_catchment` column: INSIDE vs REGIONAL_CONTEXT).

---

## 4. DRAINAGE NETWORK CHANGES

- **Topology: no change documented.** The full Phase-14B lateral set (Nauroji Nagar → J_5670; Berral → J_4771; Africa Avenue sewers → J_3141; Maharaja Agrasen → J_6182/J_6043; Defence Colony drain; Sunehri join; Kushak→Barapullah→Yamuna outfall chain) carries **zero** construction/removal/reroute/disconnection documents for 2015–2026, and PLANNED_ONLY = 0 (CR-014).
- **Covering: restrained.** NGT 13-01-2015 restrained further nallah covering; the start-of-window covering state (11 km nallah, 4.7 km covered, NDMC 2007) is not altered by any located post-2015 record (CR-010).
- **Maintenance-state changes are temporary, not structural — and the flagship desilting procurement is NOT executed**: NIT-52/EE(R-III)/2025-26 (21,406 m³, robotic/super-sucker, flow-blocking method, published 24-08-2026, bids close 17-09-2026) is **PRE-AWARD — procurement intent only, no contractor exists**; the NGT JIR 09-04-2025 records the April-2025 pre-NIT-52 silt state (1.5–3 ft; 2/5 bays conveying at DWF). The separate annual pre-monsoon desilting seasons (2024 officially disputed; 2025 season) are maintenance-state records, not structural changes (CR-011). Procurement ≠ completion is enforced by this phase's own correction record.
- **Bathymetry**: NGT-directed 06-08-2024 for Barapullah incl. Sunehripul and Kushak (CR-009) — the *output* (the one document that would quantify in-window conveyance/storage change) was **never publicly released**. Recorded as a gap, not a change.
- **Effects on contributing area / path length / storage / bypass / new inflow**: **none documented** for any of the above (`drainage_connectivity_relevance = NO_CHANGE_DOCUMENTED` throughout; `UNKNOWN` only where SPS-storm hydraulics are concerned, CR-008).

---

## 5. SEWAGE / STORMWATER SEPARATION

- **Andrews Ganj SPS sewage trapping of Kushak drain flow: completed Aug-2022** (NMCG MPR, verbatim "have been completed") (CR-008). This intercepts the **sewage component**; per mission rule, it is **not assumed to change stormwater runoff** — `runoff_generation_relevance = NO_CLEAR_EFFECT`. Its storm-time hydraulic effect (trapped-flow behaviour at the SPS during storms) is undocumented → `drainage_connectivity_relevance = UNKNOWN`.
- **Other separations**: no dated outfall closures, sewer-stormwater separation works, or illegal-connection removal campaigns specific to Kushak inputs (Africa Avenue, Maharaja Agrasen, Defence Colony) were located for the window (negative finding §7). The sewer-vs-stormwater classification caution from Phase 14B (§5) carries over unchanged.

---

## 6. MAJOR ROAD / INFRASTRUCTURE CHANGES

| Project | Period | Status | Catchment position | Documented drainage impact | Register |
|---|---|---|---|---|---|
| Barapullah Phase-1 (SKK ↔ JLN Stadium) | opened 2010 | COMPLETED_2010 (pre-window baseline) | ADJACENT | Piers along nallah reserve already embedded in pre-2015 regime; NGT 2015 barred NEW piers in the active waterway | CR-003 |
| **Barapullah Phase-2 (JLN ↔ INA)** | opened **28-07-2018** after 5 missed deadlines | COMPLETED_2018-07 | ADJACENT (the reach along the mainstem, east of the modelled corridor) | **NONE DOCUMENTED** → UNKNOWN | CR-002 |
| Barapullah Phase-3 (SKK ↔ Mayur Vihar) | construction 2015 → completed, opening expected Aug-2026 | COMPLETED_2026 | **OUTSIDE** (crosses the Yamuna) | none expected; construction-era diversions documented only on the east side | CR-001 |

Phase-2 is the only in-window construction physically adjacent to the Kushak/Barapullah mainstem. Its **piers along the nallah reserve** are documented by project records, but no source documents a drainage impact (conveyance change, backwater effect, or diversion) — recorded `UNKNOWN`, not inferred. Construction-period (2015–2018) temporary diversions for Phase-2 in the Kushak reaches: **no document located**.

---

## 7. NEGATIVE FINDINGS (searched, not found — absence is not proof of absence)

1. No official catchment **polygon or area figure** for Kushak for any specific year (1976/2007/2011/2015/2018/2023/2024/2025/2026) — only the conflicting agency figures of §9/CR-015.
2. No official or peer-reviewed **Kushak imperviousness percentage for 2015 or 2026** — only the 2021 WorldCover epoch on disk.
3. No **as-built drainage rerouting**, new-storm-drain, drain-extension, or culvert-reconstruction record for any Kushak reach 2015–2026.
4. No **completion documentation** for the 2024 bathymetric survey (directed, not published).
5. No **in-window Kushak Bus Depot** construction/redevelopment record.
6. No **temporary construction diversion** record for Kushak reaches during Phase-2 construction (2015–2018).
7. No **sewer-stormwater separation works** or outfall-closure orders specific to Kushak inputs in the window.
8. No second **WorldCover/product epoch** acquired (would be a new acquisition task; documented cross-dataset uncertainty makes naive differencing unsafe).

---

## 8. EVENT-REGIME LINKAGE (summary; full 22-event crosswalk in deliverable E)

- **2021 events (EVT-2021-07-13, EVT-2021-09-11; both QUALIFIED)**: pre-intervention regime — pre-dating Andrews Ganj trapping completion (2022) and all desilting programmes. DTP gazetted corridor points active.
- **2023 events (EVT-2023-07-08/09 QUALIFIED; others NOT_QUALIFIED)**: urbanized post-trapping regime (Phase-2 open 2018; Kidwai Nagar staged-complete 2019; Andrews Ganj trapping completed 2022-08; WTC under construction).
- **EVT-2024-06-27 (QUALIFIED, identification-grade)**: pre-desilting-season-2024; **operational regime officially CONTESTED on the adjacent day** (LG-vs-I&FC desilting dispute, 28-06-2024); WTC construction ongoing; trapping complete.
- **2024-07/08 & 2024-09 events (all NOT_QUALIFIED/UNCERTAIN)**: regime UNKNOWN beyond the above; the 26-07-2024 Africa Avenue pump-overwhelm episode (CR-012) sits in this cluster as event-conditioned operational evidence.
- **2025–2026 events**: **pre-NIT-52-execution regime** — the NIT-52 desilting works had not begun (bids close 17-09-2026); EVT-2025-07-30 falls after the documented April-2025 silt state (1.5–3 ft); EVT-2026-08-25 occurs weeks after Barapullah Phase-3 completion (out-of-catchment) and under the documented 25 mm/h NDMC-capacity-deficit context.
- No causal effect is inferred anywhere; the crosswalk records placement and confidence only.

---

## 9. CONFLICTS (dedicated table; full version in audit)

| # | SOURCE A | SOURCE B | CONFLICT | DATE | POSSIBLE EXPLANATION | SAFE INTERPRETATION | RESOLVING EVIDENCE |
|---|---|---|---|---|---|---|---|
| K1 | PIB/CGWB (3.5 km²); MCD doc (2.03 km²/3,220 m) | Project D8 (27.66–28.40 km²); historical ~35.4 km² | Kushak catchment area figures differ by >10× | 2011–2026 | Different metrics: nalla's own micro-catchment vs urban contributing surface vs summed historic basins | All preserved; no figure adopted as the other's replacement; 27.66 km² remains the provisional working value; conflicting metrics are NOT a boundary change | Official polygon (none public); 2024 bathymetry output (non-public) |
| K2 | Press/PIWD (Phase-2 "opened 2018") | Drainage-impact silence in all sources | Major adjacent construction vs zero documented drainage effect | 2018 | Drainage works under road agencies not covered by press; DMP 2018 model predates assimilation | Completion is fact; drainage effect is UNKNOWN — never treated as zero | PWD as-built drainage drawings for Phase-2 (access-restricted) |

---

## 10. WHAT REMAINS UNKNOWN

(a) the magnitude of the Kidwai/WTC imperviousness deltas; (b) any Phase-2 drainage effect; (c) SPS storm-time hydraulics post-2022; (d) the 2024 bathymetry result (conveyance/storage state); (e) whether any unrecorded local works altered micro-connectivity (documentary silence ≠ absence); (f) a validated second remote-sensing epoch for change detection.

**Sufficiency verdict (stated, no parameters touched):** the documented evidence is **NOT sufficient to justify modifying rainfall-runoff parameters** — two direction-qualified land-use changes exist, but no quantified imperviousness/area/conveyance delta exists for the window; parameter changes would require the missing quantification (second epoch + bathymetry + as-builts). No coefficient proposed; no GLUE started; catchment untouched.
