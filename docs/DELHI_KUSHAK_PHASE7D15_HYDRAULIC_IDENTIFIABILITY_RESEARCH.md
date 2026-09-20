# Phase 7D-15 — Kushak Hydraulic Identifiability Research

**Document ID:** `DELHI_KUSHAK_PHASE7D15_HYDRAULIC_IDENTIFIABILITY_RESEARCH`
**Date:** 2026-09-12
**Type:** read-only research. No code, solver, models, tests, pipelines, or V1 modified. No synthetic geometry created. No uncertainty range invented. This report distinguishes **source facts** from **this report's inference** in every section.

**Question:** can the missing Kushak hydraulic geometry be *defensibly estimated* from historical observations and existing evidence — and if not geometry, can an **effective hydraulic relationship** be estimated instead?

---

## 1. EXECUTIVE CONCLUSION

**PARTIALLY CAN.**

- **CANNOT:** recover Kushak's physical geometry (cross-sections, inverts, conduit dimensions, structure openings) from the available evidence. The observation set is too sparse and too coarsely quantized (predominantly *binary flood occurrence at named points* plus a handful of official visual state statements) to constrain a distributed hydraulic geometry. Any claim of "reconstructed as-built geometry" from these data would be indefensible.
- **PARTIALLY CAN:** estimate a bounded **effective hydraulic relationship** — per-reach effective conveyance/capacity class, effective roughness/blockage ranges, an effective storage-stage envelope, and effective rainfall-to-inflow parameters — as **behavioral (non-unique) parameter sets** constrained by (i) hard dimensional bounds from official records, (ii) the observed flood/no-flood states of the two benchmark events under known forcing, (iii) the downstream boundary states, and (iv) physically-motivated antecedent-condition separation. The output would be *feasibility envelopes with stated non-uniqueness* (GLUE-style), **not** a single calibrated geometry.
- The honest framing for the project: **"effective hydraulic response consistent with observations and official dimensional bounds"** — never "as-built geometry".

## 2. EVIDENCE INVENTORY USED

All items below are on disk or previously verified in Phases 6B–6E/earlier audits. Provenance class per item.

### 2.1 Forcing (rainfall)
| # | Evidence | Class | Source artifact |
|---|---|---|---|
| F1 | Safdarjung SYNOP 3-h cumulative buckets, both events, complete chains; derived 3-h increments: EV-2024 = 149 mm (02:30–05:30 IST) + 74 mm (05:30–08:30); EV-2023 = 21/78/27/4 mm (8 Jul) and 94 mm burst (9 Jul 14:30–17:30) | **OBSERVED** (buckets) + DERIVED (differences, labeled) | `kushak_benchmark_3h_increments.csv`; `kushak_benchmark_rain_observations.csv` |
| F2 | Palam SYNOP buckets both events (75/14 mm EV-2024; ≈22 mm 8 Jul EV-2023) | OBSERVED + DERIVED | same |
| F3 | IMD daily totals & peak-hour narrative claims (Safdarjung 228.1 mm; 91 mm/h claim 05:00–06:00 IST 28-Jun; Lodhi 192.8 mm; 64+89 mm/h claims) | OBSERVED (daily) / OFFICIAL description (hourly claims) | `imd_bulletin_20240628_*.json`, `imd_press_release_20240628.pdf` |
| F4 | ERA5 hourly reanalysis both events (labeled; grossly under-observed: 51.3 mm vs 228 mm) | REANALYSIS (never forcing) | `era5_openmeteo_*.json` |

### 2.2 Catchment / rainfall-to-inflow
| # | Evidence | Class | Source artifact |
|---|---|---|---|
| C1 | 5 lateral-inflow zones SC-01…SC-05, total 27.66 km² working catchment (provisional), zone areas 10.42/14.15/1.12/1.80/0.18 km², built-up %, corridor chainage bands | DERIVED (Voronoi on hydro-enforced corridor; boundary provisional) | `kushak_subcatchment_inventory.csv`, `kushak_lateral_inflow_zones.csv` |
| C2 | Loss/runoff parameter set with tested ranges (Ks 3.5–15.2 mm/h; CN 61–98 by cover; EIA 29.5–41.8 %; depression storage; overland and channel Manning ranges) — **declared ASSUMED BASELINE RANGES**; ICAR-NBSS&LUP soil mapping; no in-situ infiltration gauge | ASSUMED (ranges) | `kushak_hydrologic_parameter_provenance.csv` |
| C3 | Three antecedent scenarios mapped to events: SCEN-02 (saturated, AMC III) → 2023 multi-day; SCEN-03 (dry, AMC I) → 2024 first-burst; SCEN-01 baseline | ASSUMED (physically reasoned, not fitted) | `kushak_runoff_scenarios.csv` |
| C4 | Pre-computed subcatchment hydrographs for EV-2024 (both loss models; peaks e.g. SC-01 ≈123.5–124.3 m³/s, SC-02 ≈167.8–168.8 m³/s, at ~11 h; mass-balance ok) | DERIVED (model output under ASSUMED params) | `runoff/SCEN-01/EV-01/*/summary.csv` |
| C5 | Dry-weather flow ≈**10 MLD** (0.116 m³/s), non-rainy season, S.P. Marg→Kamal Ataturk Marg reach | OFFICIAL_DESCRIPTION_OF_REPORT (agenda-level; cGanga study non-public) | NDMC Council Item 21, 28-02-2024 |

### 2.3 Geometry / structural
| # | Evidence | Class | Source |
|---|---|---|---|
| G1 | DMP-2018 84-node invert backbone + 281-edge connectivity; dims 25 m top / 10 m bottom / 7.354–7.554 m | OFFICIAL_MODEL_VALUE | Appendix XII (template-suspect; established) |
| G2 | Digitized model chainages; 170/281 edges with digitized model lengths; section extents (trunk 3,539 m; II-u 1,094; II-l 542; Berral 1,699) | MODEL_REACH_LENGTH (digitized) | `kushak_conduit_lengths_digitized.csv` |
| G3 | OSM corridor 5,027.56 m (Reach 1 covered 2,318.42; Reach 2 open 2,709.14) | GIS_DERIVED | `kushak_corridor_centerline.geojson` |
| G4 | JIR 05-03-2025 (NGT 09-04-2025): covered depot reach **50 m wide, 5 equal bays**, box depth **3.5–4.5 m (visual)**, access openings **1.5×1.5 m @ ~50 m**, silt chambers 2.50×1.15 m @ ~100 m, **silt 1.5–3 ft in all 5 bays**, **flow ≈1 ft through 2 of 5 bays** (a 2025 flow-state observation) | OFFICIAL_AS_BUILT (visual) | NGT order (on disk) |
| G5 | HC CONT.CAS(C) 434/2022 status 28-01-2026: INA→LLRM ≈2.62 km = 1.75 km + 1.0 km depot + 0.87 km; MCD→I&FC as-is-where-is handovers | COURT_NGT_RECORD | indiankanoon 125400451 |
| G6 | NIT-52 BOQ: covered-barrel size class **"4.00 m +25%"**; desilting quantity 21,406 m³ (−25 % voids); 216 m² slab cutting | PROCUREMENT_SPECIFICATION / BOQ_QUANTITY | `work_396329.zip` |
| G7 | Sunehri Pul (confluence reach): five RCC boxes × 10 m width, depth 3.5–5.5 m (press quoting tender) | SECONDARY_REFERENCE | TOI 29-05-2025 |
| G8 | Copernicus DSM bank elevations along corridor | DERIVED (DSM, not channel) | derived/terrain |
| G9 | 1976/2015/2007 length statements (11 km; 4.7 km covered; 2.8/6.5/3.85/3.225/2.62 km reach variants) | OFFICIAL_RECORD (reach-definition-dependent) | various |

### 2.3b Africa Avenue covered conduit specifics
Covered conduit internal geometry **UNKNOWN** (Phase 6C: NIT-52 package contains none). Only bounds: CPWD box class in BOQ, the 3.5–4.5 m visual depth (depot reach), and the existence of ~1.5×1.5 m access openings.

### 2.4 Response / state observations (the identifiability currency)
| # | Evidence | Class | Source |
|---|---|---|---|
| R1 | **EV-2024 (28-Jun-2024):** DTP alerts 07:30–08:15 IST — waterlogging **under AIIMS flyover on Aurobindo Marg (both carriageways)**, Sewa Nagar, Defence Colony underpass; (+Moolchand, Dhaula Kuan, Pragati tunnel — adjacent systems) | OBSERVED (binary occurrence + coarse timing) | `dtp_waterlogging_severity_normalized.csv` |
| R2 | **EV-2023 (8–9-Jul-2023):** DTP alerts — Aurobindo Marg (8 Jul), Panchsheel×Shanti Path, Ring Road Nehru Nagar, Minto Bridge (9 Jul). **Note: 13-Jul-2023 alerts (Sarai Kale Khan–IP, Bhairon) are Yamuna/Barapullah-mainstem floodplain points, NOT Kushak corridor — excluded from Kushak constraints.** | OBSERVED (binary) | same |
| R3 | **GSDL waterlogging layer: 1,004 occurrences 2023–24** city-wide (dates + points; corridor-adjacent subset usable) | OBSERVED (binary, secondary compilation) | `gsdl_waterlogging_normalized_occurrences.csv` |
| R4 | **Downstream boundary states:** CWC ORB daily Jul-2023 (204.63 → **208.66 m peak 13-Jul** → 205.45); **EV-2024: no Delhi station above warning 27–30 Jun** (CWC bulletins, verified) | OBSERVED (DOWNSTREAM RIVER STAGE only) | `cwc_old_railway_bridge_event.csv`; Phase 6E-adjacent CWC bulletin set |
| R5 | JIR flow state (flow ≈1 ft through 2/5 bays; silt 1.5–3 ft) — **2025 pre-monsoon snapshot; post-dates both benchmark events** | OFFICIAL (current-state, non-historical) | G4 |
| R6 | Desilting progress (66 % of covered sections by 22-05-2025; 21,252 MT I&FC target) | OFFICIAL (context; state-changing interventions) | press/NGT |

### 2.5 Explicitly EXCLUDED as Kushak hydraulic evidence
CWC ORB as Kushak stage (downstream context only) · DTP/GSDL points as depth measurements (occurrence only) · historical obstruction descriptions as current geometry · DMP dims as as-built · 13-Jul-2023 mainstem-adjacent flooding as Kushak response · NIT-52/BOQ specs as measurements.

## 3. PARAMETER-BY-PARAMETER IDENTIFIABILITY TABLE

Classes: **A** directly observed/measured · **B** official model value · **C** inferable from historical data (bounded, non-unique) · **D** only weakly identifiable / highly non-unique · **E** fundamentally blocked without new geometry.

| Parameter | Best available anchor | Identifiability | Reasoning |
|---|---|---|---|
| **Effective storage-stage V(h)** (per reach, current) | Reaches' dimensional bounds (G4/G6/G7 + G1); DSM banks (G8) | **D** (envelope only) | V(h) is geometry-determined; geometry unknown. Observations never report storage. Only a *feasibility envelope* between "small local storage + rapid routing" and "large storage + attenuation" is testable against event timing. |
| **Effective conveyance / capacity** (per reach/bottleneck) | Flood/no-flood states (R1/R2/R3) under known 3-h forcing (F1) + JIR flow state (R5) + DWF (C5) | **C (bounded, non-unique)** | Each observed surcharge point gives one inequality: local WL ≥ ground for a known inflow. Multiple (section, n, blockage, silt) combinations satisfy it. Capacity *order-of-magnitude class* is identifiable (e.g., whether the 149 mm/3 h burst overloads the corridor — it did); exact capacity is not. |
| **Cross-sectional dimensions** (width/depth, current) | Class bounds: 4.0–5.0 m spec class (G6); 10 m bays/50 m (G4); 25/10 model (G1); Sunehri 10 m boxes (G7) | **E → at best D (bounded classes)** | No observation reports a dimension. Only consistency with class bounds is testable. |
| **Manning roughness n** (open masonry; silted; box; pier-laden) | Design values (CPWD/CPHEEO via DMP: 0.012 box, 0.025 open); literature silted/pier 0.035–0.045; JIR silt state | **D** | n trades off against section and blockage for the same WL. Only jointly bounded; single-event binary data cannot separate n from geometry (classic equifinality). |
| **Bottleneck / constriction parameters** (depot 5-bay effective blockage; INA 600 m choke; opening capacity 1.5×1.5 m @50 m) | JIR state (R5: 2/5 bays flowing at DWF, silt state); binary flood occurrence near bottlenecks (R1/R2); spec opening dims | **C (partially)** | The *existence and rough severity ranking* of bottlenecks is documented (INA 600 m official; depot bays/silt official). The *effective blockage fraction during storm peaks* is weakly identifiable: only inequalities (surcharge upstream of choke during known bursts) constrain it. |
| **Downstream boundary effects** (Barapullah/Yamuna backwater) | ORB daily stages Jul-2023 (R4); EV-2024 no-exceedance (R4); confluence geometry (C-08) | **C** | The two benchmark events cleanly *bracket* the boundary: 2023 = compound event (ORB record peak 208.66 m) vs 2024 = free outfall. Boundary state per event is **OBSERVED**, so it enters as forcing, not a calibrated parameter. Flap-gate/outfall regulation behavior remains UNKNOWN (SC-05 note). |
| **Rainfall-to-inflow parameters** (loss model params, EIA, routing widths/times) | 3-h buckets (F1) + antecedent scenarios (C3) + binary flood response (R1–R3) | **C/D** | Volumes are bounded by observed rainfall and plausible loss ranges (C2); but with only binary flood observations (no in-drain stage/discharge), loss-parameter identification is weak; only *antecedent-class assignment* (already encoded in C3) is defensible without circularity. |
| **Dry-weather baseflow** | 10 MLD (C5) | **B/A-hybrid** | Official description of a measured study result; single reach + season qualifier; not a series. |
| **In-drain stage/discharge time series** | none | **E** | No instrument has ever published Kushak stage/discharge. |

## 4. HISTORICAL-EVENT CONSTRAINT ANALYSIS

**EV-2024 (28-Jun-2024) — clean pluvial event:**
- Forcing (F1): 149 mm + 74 mm in consecutive 3-h buckets, 02:30–08:30 IST; antecedent = first major burst after heatwave (C3 → SCEN-03).
- Boundary: free outfall (R4) — no mainstem interference.
- Responses: surcharge/waterlogging at Aurobindo-AIIMS, Sewa Nagar, Defence Colony underpass during/just after the burst (R1).
- **Constraints produced:** the corridor must surcharge at those three named points under ~223 mm/6 h with a dry-antecedent catchment and free outfall; upstream reaches must convey to those points (occurrence at downstream points implies conveyance upstream). This is the **most geometry-informative single event**.
- **Non-uniqueness warning (this report's inference):** binary surcharge at 3 points under one event constrains at most 3 inequalities; the parameters listed in §3 number ≥8. Many parameter vectors satisfy all three inequalities. Fitting more than inequality-consistency is impossible.

**EV-2023 (8–10-Jul-2023) — multi-day monsoon event:**
- Forcing (F1): 153 mm (24 h to 08:30 9 Jul, with an 78 mm/3 h midday burst) + 107 mm (9 Jul, 94 mm/3 h burst) + tail; antecedent multi-day (C3 → SCEN-02).
- Boundary: outfall state on 8–9 Jul is NOT directly documented (ORB was below warning until 10 Jul, i.e., mainstem low — R4 supports near-free outfall for the pluvial phase); by 13 Jul the Yamuna hit 208.66 m (compound mainstem event, R4) — but the 13-Jul DTP points are mainstem-adjacent, so **13 Jul contributes boundary context, not Kushak response constraints**.
- Responses: corridor-area waterlogging 8–9 Jul (R2).
- **Constraints produced:** repeatability under multi-burst saturated conditions; distinguishes sustained-capacity limits from single-burst behavior.

**Leakage-safe split (this report's inference):**
- **Identification set:** EV-2024 (clean boundary, highest-quality forcing resolution, dry antecedent). Fit/retain only inequality-consistent behavioral sets.
- **Validation set:** EV-2023 (different forcing structure: multi-day, saturated antecedent, repeated bursts; different loss scenario class). A behavioral set identified on 2024 must reproduce 2023's observed occurrence pattern **without re-tuning**; antecedent scenario assignment (C3) is a-priori physical reasoning, not fitted — this prevents leakage.
- Additional independent check: the JIR 2025 DWF flow state (R5) can sanity-check the *low-flow* end of the effective-conveyance envelope (10 MLD producing ~1 ft depth through 2/5 bays is a low-flow inequality), and the cGanga 10 MLD anchors the baseflow. The 2025 state post-dates the events and **must not** be used to calibrate the event models.
- **Residual leakage risk:** GSDL occurrence layer spans the whole season and includes 2024 points — it may only be used for *spatial pattern* validation after date-filtering to the benchmark windows, never for parameter selection on the same windows.

## 5. PUBLISHED INVERSE / CALIBRATION METHODS RELEVANT TO KUSHAK

(Methodology-only references — applicability judged for sparse/binary observations; all classification below is this report's inference.)

| Method family | Relevance to Kushak | Applicability verdict |
|---|---|---|
| **GLUE — Generalized Likelihood Uncertainty Estimation** (Beven & Binley 1992; Beven 2006 "equifinality… GLUE", Lancaster ePrints 2083) | Explicitly embraces equifinality: returns behavioral *sets* + prediction ranges instead of one optimum. Matches our constraint type (inequalities/occurrence, sparse). | **Primary recommendation** (informal likelihoods, binary/occurrence scoring) |
| Formal Bayesian / DREAM for SWMM (comparative literature incl. "Equifinality of formal (DREAM) and informal (GLUE) Bayesian approaches", UC Irvine PDF) | Formal likelihoods need residuals statistics we do not have (no stage series). | Not applicable now; revisit if stage sensors ever exist |
| Morris screening + optimization for SWMM (MDPI Water 2023, 15(1):149); stepwise SWMM calibration practice (CHI Journal R176-24: calibrate impervious runoff volume → timing/peak → routing) | Dimension reduction before any sampling: the screening order (volume → timing → conveyance) matches our evidence hierarchy. | Applicable as a *design* step (reduce to a handful of effective parameters) |
| Multi-variable calibration to reduce equifinality (IAHR identifiability note); outlet-only calibration produces right flows/wrong internal states (Rajib et al. 2018, PMC6687302) | Directly warns the exact trap: matching "waterlogging happened" (occurrence) can hide wrong internal levels. | Governing caveat for the whole inference |
| Input-uncertainty-aware SWMM calibration (Gao et al., HESS 2020-367 framework); rainfall-type-dependent uncertainty (MDPI Water 2025, 17(23):3435) | Our forcing itself is 3-h-bucket-derived, not hourly — forcing uncertainty must enter the ensemble (e.g., within-bucket temporal placement). | Applicable; ties to the known 3-h forcing limitation |
| Parameter transferability warnings (AGU WRR 2022, 10.1029/2021WR031603) | Calibrated effective parameters must not be sold as transferable/physical. | Governing caveat |
| Synthetic-network generation under sparse data (SWMManywhere, Dobson 2025, Env. Mod. & Software) | Evidence that synthetic/effective networks are an accepted fallback class when real networks are unknown. | Supports the effective-model framing |

**Key literature caution replicated in every source:** with sparse/binary observations, calibration ≠ geometry recovery; parameter sets are event- and structure-specific, non-transferable, and multiple (equifinality). Kushak is a textbook instance: ≥8 effective parameters vs <10 binary/inequality observations.

## 6. WHAT CAN REALISTICALLY BE INFERRED FOR KUSHAK

(All inference, bounded by §2 evidence; nothing below is observed geometry.)

1. **Effective per-reach conveyance classes** for Reach 1 (covered box), the depot covered reach, and Reach 2 (open canal): a bounded range of (effective width × effective depth, effective n, effective blockage) consistent with surcharge inequalities under the known 3-h forcings and free/backwater boundary states. Report form: ranges + behavioral-set statistics, not point values.
2. **Effective bottleneck characterization:** minimum effective waterway at the depot reach (given 5 bays and observed silt/flow state) and the INA-600 m choke severity class — as inequality-consistent ranges.
3. **Effective storage-stage envelope:** per-reach stage-storage feasibility band between the dimensioned bounds; only its *order* (attenuating vs near-kinematic) is likely discriminable.
4. **Effective rainfall-to-inflow parameters:** restricted to the already-defined scenario ranges (C2/C3) with the antecedent assignment fixed a-priori; optionally EIA as the single best-identifiable loss parameter under the two events (its effect on volume/peak is first-order).
5. **Baseflow:** 10 MLD class DWF + season scaling — carried as official description.
6. **Boundary rule:** event-conditional boundary (free vs ORB-imposed backwater) driven by CWC ORB state — observed, not inferred.

## 7. WHAT CANNOT BE INFERRED WITHOUT SURVEYED GEOMETRY

1. True cross-sections (width/depth/side details) of any reach — only class bounds exist.
2. Bed/invert levels (current or historical) and longitudinal bed slope — no observation exists; DMP inverts are model values; DSM is surface.
3. Africa Avenue conduit internals (cell count, clear dimensions, soffit, actual slope).
4. Structure inverts/opening clear dimensions (only nominal 1.5×1.5 m opening class and bay counts exist).
5. A unique Manning n (fundamentally entangled with section and blockage).
6. Post-2018 / post-desilting geometry state (desilting has materially changed the system since both benchmark events).
7. Any claim that "reproduced waterlogging = correct geometry" — ruled out by equifinality (§4–5).

## 8. RECOMMENDED INFERENCE / CALIBRATION METHODOLOGY (if justified; NOT implemented here)

1. **Model class:** simple 1D storage/conveyance effective model per reach (or SWMM with effective cross-sections at bound mid-classes); 2D not justified by data.
2. **Parameters (small set):** per-reach effective conveyance multiplier + blockage factor at depot/INA + one loss-model parameter (EIA) + boundary switch by CWC state. Everything else fixed at official bounds/classes.
3. **Forcing:** 3-h bucket increments (labeled derived) with a within-burst temporal-placement ensemble (e.g., burst fraction scenarios) to honor forcing uncertainty rather than pretending hourly knowledge.
4. **Inference:** GLUE-style behavioral sampling against **inequality/occurrence likelihoods** (surcharge yes/no at Aurobindo-AIIMS, Sewa Nagar, Defence Colony for 2024; occurrence pattern for 2023), with hard prior bounds from G4/G6/G7/G1 classes. Report behavioral ranges (5–95 %) and the count of distinct behavioral mechanism families — explicitly not a unique optimum.
5. **Validation (leakage-safe):** identify on 2024; validate on 2023 (different antecedent class per C3); spatial-pattern check on date-filtered GSDL occurrences; low-flow check against JIR/cGanga DWF facts as external plausibility only.
6. **Documentation:** every effective parameter labeled `INFERRED/CALIBRATED (effective)` with its provenance chain; every geometry claim from this exercise is prohibited.
7. **Kill-criteria:** if behavioral sets prove non-existent under the official bounds (i.e., no parameter vector reproduces the 2024 surcharge within dimensional limits), that is itself a decisive finding (implying unrecorded conveyance elements such as additional inlets/pump assistance or boundary effects) — report as such, do not widen bounds silently.

## 9. REQUIRED OBSERVATIONS / DATA TO STRENGTHEN THE INFERENCE

1. **Any in-drain stage record** (even one pressure logger for one monsoon) — converts binary constraints into continuous ones.
2. The **NIT-52 post-award 290 m sonar report + CCTV** (Phase 6C route) — first true current sections for the covered reach.
3. The **I&FC CD-XII survey deliverables** (Phase 6E, RTI route) — open-reach L-sections.
4. The **cGanga flow-assessment report** (Phase 6D) — measured flows/quality beyond the single 10 MLD figure.
5. **NIT-52 pre/post-desilting CCTV** comparisons — direct state-change data.
6. Cross-sections of Sunehri Pul / confluence (controls the outfall stage interaction).
7. Hourly rainfall (IMD AWS telemetry, Phase 6D-adjacent route) to sharpen burst placement.
8. Manhole/ground-level survey along the corridor (ground elevations for surcharge thresholds — currently DTP "waterlogging" implies street level but no ground profile exists).

## 10. RECOMMENDED NEXT IMPLEMENTATION PHASE (only when approved)

**Phase 7D-16 (proposal):** "Effective-conveyance feasibility study" — implement §8 as a research script under `data/delhi/derived/research/` (not production code): build the effective 3-reach model, run the GLUE-style inequality sampling over the official bounds, and emit behavioral envelopes for the two events with the 2024→2023 split. Deliverable: behavioral parameter ranges + per-event surcharge-consistency verdicts + explicit non-uniqueness documentation. No geometry claims; no production integration.

## 11. SOURCES

**Project artifacts (facts):** `kushak_benchmark_3h_increments.csv` / `kushak_benchmark_rain_observations.csv` (Phase 7D-15 predecessor audits) · `kushak_runoff_scenarios.csv`, `kushak_hydrologic_parameter_provenance.csv`, `kushak_subcatchment_inventory.csv`, `kushak_lateral_inflow_zones.csv`, `runoff/SCEN-01/EV-01/*/summary.csv` · `kushak_corridor_centerline.geojson`, `kushak_conduit_lengths_digitized.csv` · `dtp_waterlogging_severity_normalized.csv`, `gsdl_waterlogging_normalized_occurrences.csv` · `cwc_old_railway_bridge_event.csv` · `ndmc_council_meeting_28-02-2024.pdf` (Item 21) · `work_396329.zip` (NIT-52) · `ifc_niq_cdxii0810_survey.pdf` · NGT orders 09-04-2025 / 23-04-2025 / 14-10-2025 / 06-08-2024 · Indian Kanoon 125400451 (HC 29-01-2026) · docs Phases 6B/6C/6E + prior Kushak audits.

**Methodology (web, consulted 2026-09-12):**
- Beven (2006), "Equifinality, Data Assimilation, and Uncertainty Estimation Using the GLUE Methodology" — https://eprints.lancs.ac.uk/id/eprint/2083/
- "Equifinality of Formal (DREAM) and Informal (GLUE) Bayesian Approaches" — https://bpb-us-e2.wpmucdn.com/faculty.sites.uci.edu/dist/f/94/files/2016/04/49.pdf
- Morris+optimization SWMM workflow, MDPI Water 2023, 15(1):149 — https://www.mdpi.com/2073-4441/15/1/149
- Stepwise SWMM calibration methodology, CHI Journal R176-24 — https://www.chijournal.org/Journals/PDF/R176-24
- GLUE-based SWMM uncertainty (Frontiers 2025) — https://www.frontiersin.org/journals/environmental-science/articles/10.3389/fenvs.2025.1582306/full
- Bayesian SWMM calibration & rainfall-type uncertainty, MDPI Water 2025, 17(23):3435 — https://www.mdpi.com/2073-4441/17/23/3435
- Input-uncertainty-aware SWMM calibration framework (HESS) — https://d-nb.info/1216246467/34
- Parameter transferability in SWMM, AGU WRR 2022 — https://agupubs.onlinelibrary.wiley.com/doi/full/10.1029/2021WR031603
- SWMM review, Niazi et al. 2017 — https://pmc.ncbi.nlm.nih.gov/articles/PMC7326159/
- Outlet-only calibration caveat, Rajib et al. 2018 — https://pmc.ncbi.nlm.nih.gov/articles/PMC6687302/
- SWMM (EPA) — https://www.epa.gov/water-research/storm-water-management-model-swmm
- Multi-variable identifiability note (IAHR) — https://www.iahr.org/library/infor?pid=21174

## 12. SOURCE FACTS vs INFERENCE — EXPLICIT SEPARATION

**Facts (from records, verbatim-verifiable):** all §2 entries with their classes; the event timestamps/stages/quantities; the JIR dimensional/visual statements; the 10 MLD agenda statement; ORB stages; BOQ quantities and spec classes.
**Inference (this report):** every identifiability grade in §3; the inequality-constraint framing of §4; the leakage-safe split design; the applicability verdicts in §5; the entirety of §6–§10. Wherever this report ranks, bounds, or proposes, it is reasoning — and it is labeled as such.

---

## FINAL SUMMARY (as required)

- **Files created/modified:** created `docs/DELHI_KUSHAK_PHASE7D15_HYDRAULIC_IDENTIFIABILITY_RESEARCH.md` (this file). Modified: **NONE**.
- **Research sources consulted:** project artifacts listed in §11 (all on disk, read-only) + the twelve methodology sources above (web, 2026-09-12).
- **Key conclusion:** **PARTIALLY CAN** — an effective, bounded hydraulic relationship (conveyance/capacity classes, blockage ranges, boundary rule, antecedent-classed inflow parameters) is defensibly inferable as GLUE-style behavioral envelopes; **physical geometry is not inferable** and must not be claimed.
- **Strongest defensible opportunity:** inequality-based behavioral inference identified on the **28-Jun-2024 clean pluvial event** (free outfall, 149+74 mm/3 h buckets, three named surcharge points) and validated on the **8–9 Jul 2023 multi-day event**, with the boundary rule set by CWC ORB observations and the DWF anchored by the official 10 MLD statement.
- **Strongest scientific blocker:** **equifinality under binary observations** — surcharge occurrence at a few points cannot uniquely determine cross-sections, roughness and blockage simultaneously; and the true current cross-sections/inverts are simply absent from every record (P0 gaps stand).
- **Recommended next step:** Phase 7D-16 effective-conveyance feasibility study (§10) — research-script only, producing behavioral envelopes and consistency verdicts for both benchmark events, with geometry claims explicitly prohibited.
