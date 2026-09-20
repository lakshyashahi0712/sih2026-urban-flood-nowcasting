# DELHI KUSHAK — OPERATIONAL EVIDENCE RESEARCH (PUMPING / MAINTENANCE / STRUCTURAL CONTROLS)

**Phase**: Operational-controls research (research-only; no model, twin, or test changes)
**Date of research**: 2026-09-16 · **Companion register**: `data/delhi/derived/research/kushak_operational_evidence.csv` (38 rows) · **Timeline**: `DELHI_KUSHAK_OPERATIONAL_TIMELINE.md` · **Audit**: `DELHI_KUSHAK_OPERATIONAL_EVIDENCE_AUDIT.md`

**Scope note.** "Kushak" is used in two official senses, following `DELHI_KUSHAK_HISTORICAL_NETWORK_RECONCILIATION.md`:
1. **Western/NDMC spine** — Central Ridge → Chanakyapuri → Africa Avenue covered box (Reach 1, 2,318 m) → open canal past Safdarjung/AIIMS/INA → DTC Kushak Bus Depot covered deck (1,050 m) → Barapullah confluence head. This is the project's modelled corridor.
2. **Southern collector** (NGT OA 300/2013 nomenclature) — Chirag Delhi / Andrews Ganj / Defence Colony drain, which NMCG/DJB also call the "Kushak drain" (Andrews Ganj SPS). It converges with the western spine at the Barapullah confluence.

Every row below carries provenance_class ∈ {OBSERVED_OFFICIAL, DERIVED, ASSUMED, UNKNOWN}, confidence, event_relevance ∈ {DIRECT, INDIRECT, BACKGROUND}, and `hydraulic_interpretation_allowed` (YES only when the source directly documents the operational fact).

**Safeguards honoured.** No pump-horsepower→discharge conversion. Pump existence ≠ pump operation. Flooding ≠ proof of blockage. No-blockage-report ≠ unobstructed flow. Delhi-wide documents are not Kushak evidence unless they name a Kushak reach or agency jurisdiction over it. Procurement scope ≠ completed work. "Adequate pumping capacity" claims ≠ operation during events. No model parameters touched.

---

## 1. PUMPING EVIDENCE

### 1.1 The single strongest item: EV-2024-07-26, Africa Avenue underpass (DIRECT)
**OP-PUMP-001 / OP-PUMP-002 / OP-STR-005 / OP-EVT-001 — TOI, 27-07-2024, quoting NDMC and Northern Railway** (article captured to `data/delhi/raw/research/operational/`):
- Water "up to a depth of 6-7 feet around 8am" at the Africa Avenue underpass (near Leela Hotel); NDMC "had to call in extra resources to pump the water out by the afternoon." → **Pumps demonstrably operated during the event; they were insufficient.**
- NDMC official: "Though our equipment, including pumps, functioned efficiently, the inflow was so great that the pipes were unable to cope with the pressure. We also suspect clogging in the drainage system, probably due to construction material carried by the rainwater." → **Direct official statement that (a) pumps ran, (b) conveyance downstream of the pumps was overwhelmed, (c) clogging was suspected (not established).**
- NDMC attributed inflow to "rainwater diverted because of the construction being carried out by Northern Railway at the rear of Leela Hotel." Northern Railway countered that area drains/sewerage (Sanjay Camp, Nepali Camp, Inderpuri JJ Colony, etc.) are unattended and that NDMC/DJB pipelines leak over the Vande Mataram Marg flyover. → **Two competing official attributions; both are claims; neither verified.**
- Fleet context for monsoon-2024: six control rooms, **120 fixed + 62 temporary portable pumps**, 26 vulnerable locations **including Africa Avenue**; permanent pumps named at BKS Marg, Panchkuian Road, Purana Quila Road, Lodhi Estate, Nyaya Marg, Malcha Marg, Madhu Limaye Marg, Dara Shukoh Marg. Same-day resolution: "waterlogging… reported from 23 other places in Lutyens' Delhi… The council resolved 13 of them on priority."
- **Classification**: OBSERVED_OFFICIAL, HIGH confidence, DIRECT event relevance, hydraulic_interpretation_allowed = YES for the operational facts (pumps ran; overwhelmed; clogging suspected). The 6-7 ft depth is a reported figure, not a gauge measurement. No HP→discharge conversion performed.

### 1.2 Africa Avenue submersible pump — budgeted 2021-22 (INDIRECT)
**OP-PUMP-003 — NDMC Budget 2021-22 Vol-II, p.524** (PDF downloaded to raw): capital line *"IMPROVEMENT TO DRAINAGE SYSTEM AT UNDER BRIDGE AFRICA AVENUE, CHANAKYA PURI BY PROVIDING SUBMERSIBLE PUMP"*, Revised Estimate ₹150 lakh, Budget/Actual columns 0/0 in that volume.
→ **Provision, not commissioning.** Whether the pump was installed, and when it entered service, is UNKNOWN from public sources. Given the 26-07-2024 event above, any claim that a fixed submersible pump protected the underpass by 2024 is unsupported.

### 1.3 Moolchand underpass pumps (INDIRECT — corridor low point)
- **OP-PUMP-006** (Big News Network, 23-09-2021): "two water pumps of 500 horsepower installed… at Moolchand underpass." Press-reported capacity; operational status during events UNKNOWN.
- **OP-PUMP-007** (DD News via X, Feb 2025): Minister inspects "upgradation of Moolchand underpass pumps" pre-monsoon-2025 — an upgrade program existed; completion date UNKNOWN.
- Moolchand is a chronic low point in DMP-2018/IIT-Delhi hotspot material already on disk; it is on the Ring Road corridor adjacent to the Kushak southern system. hydraulic_interpretation_allowed = NO (capacity figures are press-reported; no operation record).

### 1.4 Andrews Ganj SPS — the "Kushak drain" sewage pumping (INDIRECT, southern spine)
- **OP-PUMP-008 — NMCG Delhi Monthly Progress Report, August 2022, p.14** (PDF downloaded): *"the work of trapping flow in Kushak drain at Andrews Ganj Pumping station have been completed."* The word **"Kushak drain" is explicit**; this is sewage-interception (dry-weather) pumping on the southern collector, **not** storm dewatering. OBSERVED_OFFICIAL, HIGH.
- **OP-PUMP-009 — NGT OA 6/2012 order 20-08-2025** quoting DJB affidavit: overflow at points AD9/AD10 "will be trapped at the **proposed augmented Andrews Ganj SPS**"; unsewered Shaheed Camp waste "can be trapped in Andrews Ganj SPS"; a surveyed table of **43 sewage outfalls** into Barapullah/Defence Colony drain with MLD values (AD9 0.35 MLD, AD10 0.45 MLD…). OBSERVED_OFFICIAL, HIGH.
- **Interpretation guard**: these items constrain the **dry-weather sewage regime** of the southern spine (baseflow composition), not storm hydraulics. No conversion of SPS capacity to storm discharge is permitted.

### 1.5 Fleet-level Delhi-wide context (BACKGROUND)
- **OP-PUMP-004**: NDMC acquired "eight new 32 horsepower trolley-mounted dewatering pumps" for monsoon-2025 (ETInfra 19-03-2025).
- **OP-PUMP-005 / OP-STR-012**: PWD Monsoon Flood Control Order 2017 — "Details of Drainage Pumps in Subways/Underpass" pp.58-73; "List of I & FC regulators" p.86; "List of pumping station of DJB" p.87 (Scribd mirror of official document; page-level extraction pending, non-blocking).
- **OP-PUMP-010b**: The Hindu 26-08-2026 — during the 2026-08-25/26 event at ITO: "six PTO pumps, 14 permanent pumps and 15 personnel have been deployed." Event-conditioned pump deployment at the Barapullah mainstem, adjacent to the Kushak confluence. OBSERVED_OFFICIAL, HIGH, INDIRECT.

### 1.6 Pumping items explicitly NOT found
No public record of: Kushak Bus Depot pumping operations; pump activation timestamps for any Kushak reach; pump outages/failures on the corridor; Africa Avenue/Satya Marg dedicated pump-house operating logs. `hydraulic_interpretation_allowed` is NO for anything requiring these.

---

## 2. MAINTENANCE / DESILTING EVIDENCE

### 2.1 Kushak-reach desilting — tenders with named reaches (DIRECT)
- **OP-DES-001 — NDMC monsoon plan (ETInfra, 19-03-2025)**: tender floated "for desilting at **Dayal Singh College, Lodhi Road, and DTC Depot**, with the project expected to be awarded in April 2025 and completed by June 2025"; the same locations "experienced severe flooding" and were cleaned after LG/CS intervention "last year" (i.e., during/after monsoon-2024); methods: robotic machines, super suckers, non-manual. **DTC Depot is the Kushak covered depot reach (CD-01).** OBSERVED_OFFICIAL, HIGH, DIRECT; completion not independently verified (procurement ≠ completion).
- **OP-DES-002 — NIT 52/EE(R-III)/2025-26** (package on disk, `work_396329.zip`): "Desilting of RCC covered **Kushak Nallah** and Ring Road Nallah under jurisdiction of R-III Division"; BOQ item 1 covers "RCC covered Nallah… having width **4.00 meter +25%**" desilted "by mechanical means /Robotic Machine/super sucker machines… **pumps for dewatering pumping**… **blocking the flow on upstream and downstream of required length**"; quantity **21,406 m³**. OBSERVED_OFFICIAL, HIGH, DIRECT.
  - **Operational by-products documented in the spec**: (a) desilting the covered barrel class requires **flow blocking** upstream/downstream — i.e., during works the conduit is operated under artificial flow control; (b) dewatering pumps are integral to the method (confined-space dewatering, IS 11972-1987 safety regime); (c) daily progress reporting of "Quantity desilted" is contractually required — such reports would be the authoritative maintenance record, but they are not public.

### 2.2 In-drain state observation — JIR 2025 (DIRECT, post-dates events)
**OP-DES-009 / OP-STR-003 / OP-NEG-003 — NGT Joint Inspection Report 05-03-2025 (order 09-04-2025)**: covered depot reach ≈50 m wide, 5 equal bays; box depth 3.5-4.5 m (visual); **silt 1.5-3 ft in all 5 bays**; **flow ≈1 ft through only 2 of 5 bays** at dry-weather; access openings ≈1.5×1.5 m @ ~50 m; silt chambers 2.50×1.15 m @ ~100 m.
→ A **direct, official, in-drain state observation** (2025 pre-monsoon): heavy silt load and 3/5 bays effectively not conveying at DWF. It **post-dates all catalogue events** and is therefore timeline/state context — it must not be used to calibrate the 2021/2023/2024 event models (Phase 7D-15 usage rule, preserved).

### 2.3 Desilting quantities and disputed completion, 2024 season (INDIRECT)
- **OP-DES-005 — TOI 14-06-2024**: I&FC to "collect 15 lakh tonnes of silt by June 15 and had already collected 10 lakh tonnes."
- **OP-PUMP-010 — LG Delhi, 28-06-2024 (X)**: "It is shocking that the Flood Control Order & de-silting of drains that should have been issued and completed by 15.06.24, are yet pending."
→ **Two official statements 14 days apart disagree about completion** — and the LG's statement is same-day with EVT-2024-06-28. The register therefore refuses to resolve "desilted before EV-2024" as true or false; both items are carried with their dates. OBSERVED_OFFICIAL; HIGH (existence of statements) with event-state resolution UNKNOWN.

### 2.4 Judicially-directed maintenance on the southern system (INDIRECT)
**OP-DES-008 / OP-STR-004 — NGT 20-08-2025** (reproducing 07-07-2025 directions): "In the meanwhile, MCD is directed to **expedite the de-silting work**"; MCD to disclose installation of **wire mesh at the upstream of the Defence Colony drain** after completing de-silting (start 15-09-2025, 2-3 weeks duration) "and also arrangement for regular cleaning of mesh wire to avoid clogging."
→ As of Jul-Aug 2025 the Defence Colony de-silting was **incomplete and under judicial direction**; a screen control with an O&M (anti-clogging) obligation was being added post-2025.

### 2.5 City-wide context (BACKGROUND only)
- **OP-DES-003**: "66% of covered sections by 22-05-2025; 21,252 MT I&FC target" (as recorded in Phase 7D-15 R6). DERIVED (from press/NGT synthesis), MEDIUM.
- **OP-DES-004**: NDMC monsoon-2025 scope — 11,867 manholes, 8,704 bellmouths, 7,177 chambers/gully traps cleaned; RWH pit maintenance by 30-05-2025. Scope statements, not verified completion.
- **OP-DES-006** (Najafgarh, 17,000 MT by 18-11-2022) and **OP-DES-007** (Barapullah mainstem, 14,000 MT, late-2025, CM statement via social post): different systems; mainstem item retained solely as tailwater-context. **Explicitly not Kushak evidence.**

### 2.6 Maintenance items NOT found
No dated, Kushak-specific: pre/post-monsoon cleaning completion certificates; silt-quantity-withheld figures for a Kushak reach; robotic-desilting completion reports for the depot or Africa Avenue box; before/after condition surveys.

---

## 3. STRUCTURAL / HYDRAULIC CONTROLS

| ID | Control | Documented fact | Class / hyd_allowed |
|---|---|---|---|
| OP-STR-001 | **Africa Avenue railway underpass** | NDMC Plan 2007 §9.3.1: waterlogging occurs "such as the Railway bridge underpass at Africa Avenue (Chanakyapuri), from where accumulated water **has to be pumped out**" → the node is **pumped, not gravity-drained** | OBSERVED_OFFICIAL / **YES** |
| OP-STR-002 | **Outfall inverse gradient + capacity class** | NDMC (19-03-2025): "limited drain capacity (**25 mm per hour**), **inverse gradient issues at key outfalls such as Sunheri Pulla Nallah and Purana Qila Road**, and ongoing construction projects of other agencies" | OBSERVED_OFFICIAL / YES (as stated constraint; 25 mm/h is a network claim, not a Kushak discharge) |
| OP-STR-003 | **Access openings + silt chambers (depot reach)** | JIR 2025: openings ≈1.5×1.5 m @ ~50 m; chambers 2.50×1.15 m @ ~100 m | OBSERVED_OFFICIAL / YES |
| OP-STR-004 | **Wire-mesh screen (Defence Colony upstream)** | Planned from NGT record; installation from 15-09-2025; anti-clogging O&M required | OBSERVED_OFFICIAL / YES (existence+plan; performance UNKNOWN) |
| OP-STR-005 | **Third-party construction interference (2024 event)** | NDMC attributes underpass flooding to NR construction at rear of Leela Hotel diverting rainwater; suspected construction-material clogging; NR disputes and alleges absent drains + leaking NDMC/DJB pipelines over Vande Mataram Marg flyover | OBSERVED_OFFICIAL (claims) / YES that the claims were made; NO that the mechanism is established |
| OP-STR-006 | **Covering / encroachment (upper NDMC reach)** | NGT OA 300/2013: "conversion of Kushak Drain into parking and road-cum-parking space"; JNNURM parking conversion; tribunal restraints (2015) | OBSERVED_OFFICIAL / YES (historical covering timeline) |
| OP-STR-007 | **Headwater gabion/nala bunds** | CGWB 2011: two gabion + two nala bunds to recharge 110,000 m³ runoff (3.5 km² catchment) | OBSERVED_OFFICIAL / NO (infiltration structure; no storm-routing effect documented) |
| OP-STR-008 | **Confluence box geometry (Sunehri Pul)** | Five RCC boxes × 10 m; depth 3.5-5.5 m (press quoting tender, 29-05-2025) | OBSERVED_OFFICIAL (medium) / NO |
| OP-STR-009 | **Lagoon retention project (S.P. Marg→Satya Marg)** | NDMC 2007 §9.3.2: 8 lagoons, 2 h retention, 7 septic tanks, INTACH consultant — completion status UNKNOWN | OBSERVED_OFFICIAL (plan) / NO |
| OP-STR-010 | **In-channel bio-remediation (NDMC stretch)** | NMCG MPR Aug-2022: "waste water in Kushak Nala… is under bio-remediation" | OBSERVED_OFFICIAL / NO |
| OP-STR-011 | **Controls excluded from official modelling** | DMP-2018: "Regulators, gates, weirs, culverts, embankments, and portable pumps were completely excluded from simulation due to lack of operational rules"; 4,401/16,977 Barapullah conduits with adverse slopes; 2,458 missing inverts; 3,021 missing dimensions | OBSERVED_OFFICIAL / YES (as evidence of operational-data absence) |
| OP-STR-012 | **Regulator/barrage lists exist** | PWD Monsoon Book 2017 pp.86-89 (I&FC regulators; barrage operations; DJB SPS) | OBSERVED_OFFICIAL / NO (Kushak rows not yet extracted) |
| OP-STR-013 | **Regulator pump-out doctrine (compound events)** | FCO-2024: regulators at mouths of MCD drains into the Yamuna "will have to be operated from time to time to suitably pump out the city drainage in case the river is in high flood and heavy local rainfall occurs to prevent back flow" | OBSERVED_OFFICIAL / YES (doctrine; city-wide) |

**Culvert/choke-point evidence status**: no official document explicitly naming a Kushak culvert restriction, regulator setting, or outfall gate state was found public. The documented control-relevant facts are: the **pumped node** (OP-STR-001), the **inverse-gradient outfalls** (OP-STR-002), the **partial bay conveyance + silt** (OP-DES-009), and the **construction-interference claims** (OP-STR-005). The elevated-corridor/pier-obstruction hypothesis for Barapullah remains undocumented publicly (carried in the audit as an unresolved gap).

---

## 4. EVENT-CONDITIONED OPERATIONS (per catalogue event)

| Event | Pumps operating? | Maintenance state | Blockage/obstruction evidence | Downstream state | Operational verdict |
|---|---|---|---|---|---|
| **EVT-2024-06-28** | No Kushak-specific operation record (NGT/DTP material documents surcharge at Aurobindo-AIIMS, Sewa Nagar, Defence Colony underpass) | LG: Flood Control Order + de-silting **pending past 15-06** (same-day official statement, OP-PUMP-010); I&FC claimed 10/15 lakh tonnes by 14-06 (OP-DES-005) | None documented | CWC: **no Delhi station above warning 27-30 Jun** → free outfall (OP-NEG-004) | **Maintenance readiness officially disputed on event day**; pumps not documented for corridor; boundary clean |
| **EVT-2024-07-26** | **YES — NDMC pumped, overwhelmed** (OP-PUMP-001/002); 120 fixed + 62 portable in fleet; Africa Avenue on the 26-point vulnerable list | Construction debris clogging **suspected** by NDMC (not established); NR construction diversion alleged | Suspected clogging (claim, OP-STR-005) | n/a (pluvial) | **Strongest event-conditioned operational evidence in the catalogue** |
| **EVT-2023-07-08/09 (multi-day)** | No operation record found | None documented for corridor | None documented | ORB below warning until 10 Jul → near-free outfall during pluvial phase; compound mainstem flood from 13 Jul (context) | Operational silence; only response-side (DTP/GSDL) evidence exists |
| **EVT-2021-09-11 (and 2021 season)** | No operation record; Moolchand 2×500 HP existed (press, 23-09-2021, OP-PUMP-006) | None documented | None documented | CWC bulletins: ORB below warning on all corridor event days (Phase 14A) | Pump existence ≠ operation; nothing event-conditioned |
| **EVT-2026-08-25** | Deployment documented at ITO (6 PTO + 14 permanent, OP-PUMP-010b); "temporary accumulation" framing | NDMC bell-mouth cleaning campaigns active (NDMC social, Sep-2026) | None documented | Mainstem context, not resolved here | Adjacent-system pump deployment documented; corridor-specific silence |

**Before/after-intervention contrasts** (the most valuable future constraints): JIR 2025 state (silt 1.5-3 ft; 2/5 bays flowing) **pre-dates** the NIT-52 desilting execution and the DTC-depot tender completion (Apr→Jun 2025 target) but **post-dates** every catalogue event; the LG-28-06-2024 statement sits **on** EV-2024-06-28. Each is a documented before/after marker — but no post-work state observation exists yet in public sources.

---

## 5. NEGATIVE CONTROLS

- **OP-NEG-002 (explicit null)**: a systematic search for credible **Kushak-specific FLOOD_NO during substantial rainfall** — e.g., "drain desilted + pumps operational + heavy rain + no waterlogging" — returned **zero qualifying public records**. Per the mission rules, silence is not converted into FLOOD_NO; this is recorded as a research finding and an audit gap, not as data.
- **OP-NEG-001 (partial)**: ITO on 26-08-2026 — flooding described by the PWD minister as "temporary accumulation" with pumps deployed and clearance steps announced: a **pump-assisted rapid-clearance** observation at an adjacent mainstem point, explicitly **not** a FLOOD_NO.
- **OP-NEG-003 (low-flow control)**: JIR 2025 DWF state (~1 ft through 2/5 bays with heavy silt) is the only low-flow operational observation; usable only as a weak low-end sanity check, never for event calibration.
- **OP-NEG-004 (boundary control)**: free-outfall bounding of EV-2024-06-28 (CWC), carried so operational interpretation never attributes 2024 surcharge to Yamuna backwater.

---

## 6. WHAT THIS EVIDENCE CAN AND CANNOT CONSTRAIN

**Can (with hydraulic_interpretation_allowed = YES):**
1. The Africa Avenue underpass is a **pumped node** whose pump-plus-conveyance chain **failed to hold** EV-2024-07-26 despite operating (inequality: inflow > pumped+gravity capacity that afternoon).
2. The covered depot reach carried only **2/5 bays at DWF** in 2025 with 1.5-3 ft silt — a *state* bound for the post-2024 period.
3. NDMC's network operates with **inverse-gradient outfalls** and a stated **25 mm/h** capacity class; DMP-2018 found 25.9% adverse slopes basin-wide — corroborating chronically adverse gradients.
4. Desilting methodology **requires flow blocking** — works periods are artificial-flow-control periods (relevant to any event that occurred during works).
5. The southern spine's DWF regime changed with **Andrews Ganj SPS completion (by Aug-2022)** and will change again with the **augmented SPS** (proposed 2025).

**Cannot (would require inference — NO rows):**
- Any pump capacity→discharge conversion; any pump operation inference for 2021/2023 events; any "desilted before event X" resolution beyond the documented statements; any blockage/unblocked inference from flooding or its absence; any Kushak stage reconstruction from operational facts.

---

## 7. PROVENANCE LEDGER (this document)

All 38 register rows: `OBSERVED_OFFICIAL` 36 · `DERIVED` 2 (OP-DES-003 synthesis; OP-NEG-002 null-result) · `ASSUMED` 0 · `UNKNOWN` 0. Confidence: HIGH 29 · MEDIUM 9 · LOW 0. Relevance: DIRECT 10 · INDIRECT 14 · BACKGROUND 14. Event-linked rows: 9 (EV-2024-06-28 ×3; EV-2024-07-26 ×4; EV-2026-08-25 ×2).

Raw captures: `data/delhi/raw/research/operational/` (NMCG PDF + extract; NDMC budget PDF + p.524 extract; 11 source snapshots + manifest `MANIFEST_OPERATIONAL_RESEARCH_20260916.json`).
