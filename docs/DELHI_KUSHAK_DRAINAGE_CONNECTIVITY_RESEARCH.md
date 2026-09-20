# DELHI KUSHAK — DRAINAGE CONNECTIVITY & LATERAL NETWORK EVIDENCE AUDIT (PHASE 14B)

**Phase**: 14B — connectivity research (research-only; no model, twin, test, or parameter changes)
**Date of research**: 2026-09-16 · **Register**: `data/delhi/derived/research/kushak_connectivity_evidence.csv` (30 rows × 20 columns) · **Audit**: `DELHI_KUSHAK_CONNECTIVITY_AUDIT.md` · **Matrix**: `DELHI_KUSHAK_CONNECTIVITY_MATRIX.md`

**Scope note.** This document reports what official sources *say* about connectivity. It does **not** redesign the hydraulic network, does not treat DMP-2018 model topology as as-built truth, does not use OSM or map proximity as hydraulic proof, and preserves every conflict found. "Kushak" is used in two senses in the literature — (a) the NDMC western spine from Birla Mandir headwaters to the INA reach, and (b) NGT Para-10 usage where "Kushak drainage system" denotes the whole southern collector ending at Barapullah. Where a source matters, the usage is quoted verbatim.

---

## 1. THE PRIMARY ANSWER

Three independent official sources, spanning 47 years, agree on the core topology:

| # | Source | Date | Statement (abridged; full text in register) |
|---|--------|------|---------------------------------------------|
| 1 | Delhi Administration, MPD 1976 drain inventory (`201_drains_mpd.pdf` p.8) | 1976 | "Sunehripulla Drain… joining Kushak to form Barapulla"; "Naoroji Nagar Drain… outfalling directly into Kushak Nallah at Kidwai Nagar West" |
| 2 | DJB network report, quoted verbatim in NGT OA 6/2012 order 22-11-2023 | 2023-11-22 | "The Kushak Nallah-Barapulla Nallah enters MCD area behind INA Market. After this a tributary, called Defence Colony Nallah joins the Kushak Nallah. There after Sunehri Nallah from New Delhi Areas joins it. From this point the Kushak Nallah is called Barapulla Nallah." … "outfalls into the river Yamuna across the ring road near Sarai Kale Khan Village" |
| 3 | NGT Court-Commissioner joint inspection record (order 09-04-2025) | 2025-04-09 | "Barapullah starts where Sunehripul meets Kushak" |

A fourth institutional confirmation: the GNCTD Chief-Secretary-level bathymetry directive (NGT OA 6/2012, order 06-08-2024) names "the Barapullah drain (including its subsidiary drains viz. Sunehripul drain and Kushak drain)" — official characterization of Kushak and Sunehripul as Barapullah subsidiaries.

**Confirmed mainstem chain (documented direction):** Kushak spine (NDMC, west) → INA/MCD reach → + Defence Colony Nallah (south, upper name Chirag Delhi Drain) → + Sunehri Nallah (north, NDMC side) → named Barapullah from this point → outfall to Yamuna across Ring Road near Sarai Kale Khan.

**What is NOT established by any of these:** junction coordinates, confluence invert elevations, as-built connection condition, or any post-1976 as-built survey of the named laterals.

---

## 2. DOCUMENTED MODEL TOPOLOGY (DMP 2018, Appendix XII) — MODEL ONLY, NOT AS-BUILT

The IIT-Delhi DMP 2018 Appendix XII junction tables (extracted on disk; extraction doc `DELHI_KUSHAK_DMP2018_APPENDIXXII_GEOMETRY_EXTRACTION.md`) provide the only named-junction, named-lateral record in existence:

| Lateral / system | Model connection | Junction | Documented invert (m) | Provenance flag |
|---|---|---|---|---|
| Nauroji Nagar Nallah | joins Kushak Part II | J_5670 | 204.900 | departmental record, IITD-corrected |
| Nauroji Nagar profile (own reach) | — | — | old 215.33 (adverse) → corrected 208.137–211.541 | IITD correction of adverse record |
| Berral-Shanti Path barrel | joins Kushak trunk | J_4771 | 208.114 (top 215.468) | departmental record |
| Africa Avenue roadside sewers A–E (W 0.4–0.7 m) | terminate on head system | J_3141 | 217.133 | departmental record, semantics unverified |
| Maharaja Agrasen Marg LHS/RHS sewers (dia 0.45–0.6 m) | discharge into Part II | J_6182 / J_6043 | 203.769 both | IITD-corrected |
| Defence Colony→Barapullah trunk link C_937 (60.0 × 4.812 m) | labelled "khushak nala" | J_1264 outfall | J_12646 corrected 206.289 → 203.532 | departmental record |
| Kushak Part II terminal (model outfall) | outfall node | J_7549 | top 208.336; new invert 203.752 (old 210.010 was adverse) | IITD-corrected |
| Spine chain | 84-junction chain | J_3055 → J_7549 | 216.841 → 203.752 (20 nodes IITD-corrected) | departmental records |

**Mandatory caveats (per mission rules):**
- This is **DOCUMENTED MODEL TOPOLOGY (2018)** — a modelling input assembled by IIT Delhi from departmental records. It is **not** an as-built certificate. The mission explicitly forbids treating Appendix-XII topology as current topology; every model row in the register carries `current_as_built_status = MODEL_ONLY (2018)`.
- The IITD "corrections" are model-side fixes of internally adverse (uphill) old records — evidence that the underlying departmental records have datum/quality problems, not that field conditions match the corrected values.
- No GTS-tied surveyed elevation exists anywhere in the public record (Tier-A). DEM-derived values are deliberately **excluded** from the register's elevation column; any future DEM use must carry `DERIVED — DEM ONLY — NOT SURVEYED`.

**Sewer-classification caution.** Appendix XII lists Africa Avenue and Maharaja Agrasen street *sewers* discharging into stormwater junctions. Whether these are storm inlets mislabelled, combined sewers, or a sewer-stormwater interface is **not established** by the source. A sewer connection is not asserted to be a stormwater hydraulic lateral (mission §3).

---

## 3. NDMC STORMWATER CONNECTIONS

- **NDMC 2007 Subcity Development Plan (s.9.3.1)**: "There are 14 drainage system networks in the NDMC area out of which 13 are covered drains and one open Nallah (Khushak). Two systems drain off to Khushak Nallah at Lodhi Road near Dayal Singh College in MCD area…" — count-level official confirmation that **two** NDMC systems connect into Kushak near Dayal Singh College. **Which two systems, and their junction elevations: UNKNOWN.**
- **GSDL DIFC storm-drain service, NDMC layer** (audited 2026-09-10 from the live public REST service; live re-probe 2026-09-16): 157 surveyed KushakNallah segments — 81 spine segments (W 25 m, D 7.354 m, total 4,926.99 m, inverts 216.91 → 203.77 m) + **76 tributary feeder segments** (W 1.0 m, D 0.83–2.51 m, total 3,964.09 m) carrying `INLETNODE`/`OUTLETNODE` connectivity fields. This is a **design inventory**: GSDL's own disclaimer states department submissions are *not ground-truthed or verified*. Feeder identities (which streets feed which nodes) were not itemized in the audit extract.
- Named NDMC-area systems (Africa Avenue, Chanakyapuri, Lodhi Road, Nehru Park, Yashwant Place, S.P. Marg, Satya Marg): **no official document located that individually names their outfall relationships to Kushak.** The Africa Avenue roadside sewers appear only inside Appendix-XII model tables (§2). Everything else for these named systems is UNKNOWN — recorded, not inferred from map proximity.

---

## 4. MCD / DRAINAGE NETWORK (SOUTHERN COLLECTOR)

- **Defence Colony Nallah**: officially confirmed tributary (2023 DJB/NGT: "joins the Kushak Nallah"; 2024 CC record: 1,065 m, 9 vent shafts, covered sections; 2025 NGT order: de-silting directed, wire-mesh at upstream from 15-09-2025). Upper name: Chirag Delhi Drain, originating "from three hilly Nallahs above Devli Bandh in Mehrauli" (DJB, 2023). The junction is documented but **not georeferenced** in any order text.
- **NGT judgment 13-01-2015 (Para 10)**: the drain "flows further into G.K.-I, Andrews Ganj, Defence Colony along the Jawahar Lal Nehru Stadium and Jangpura before meeting the Barapula Drain opposite Nizamuddin area" — note this 2015 route description has the join *east* of the Jangpura reach, while the 2023 DJB sequence has Defence Colony joining *Kushak* before Sunehri. Both are preserved; the disagreement is about the named point of confluence, not about the fact of confluence (see §9 Conflicts).
- **Andrews Ganj, Aurobindo Marg, INA, Moolchand, Ring Road**: named in flood/operational records (Phase: operational evidence, separate register) but **no connectivity document** locates their specific drain junctions. UNKNOWN — not inferred.
- **1976 MPD inventory (p.8, South Zone)**: A.I.I.M.S. Drain (2.65 km, "draining AIIMS/Safdarjung area into Barapulla basin") and Lajpat Nagar Drain (3.29 km, "outfalling to Barapulla right bank") — both "traceable" in 1976. **Which bank/junction for the AIIMS drain — i.e., whether it joins Kushak (west of confluence) or Barapullah proper (east) — is not resolved** by the 1976 text, and the 2023 DJB source lists AIIMS/INA/Lajpat Nagar only as an unnamed group. Recorded at group level with an AMBIGUOUS flag.

---

## 5. DJB / SEWER SYSTEM

- **Official sewage-inflow evidence (quantified)**: DJB's 43-outfall survey into Barapullah/Defence Colony drain (NGT 20-08-2025) with per-outfall MLD values (e.g., AD9 0.35 MLD, AD10 0.45 MLD). This documents **sewer inflow to the drain system**, not stormwater laterals.
- **Andrews Ganj SPS**: NMCG Aug-2022 monthly report (p.14) records works "trapping flow in Kushak drain at Andrews Ganj Pumping station … have been completed" — a **sewage-trapping (interception)** intervention on Kushak flow at the SPS. This is operational/interception evidence; it does **not** establish any additional stormwater lateral (operational register, OPV rows).
- **Sewer vs stormwater classification** is nowhere officially reconciled for the Kushak corridor: the same named reaches appear as "storm water drain" (DJB 2023), "Nallah" (1976), and as sewage carriers (43 outfalls). The conflict between "once a drain, now a sewer" usage (India Water Portal 2016) and storm-drain classification is **preserved, not resolved**.

---

## 6. I&FC DRAINAGE MASTER PLAN — WHAT THE MODEL SAYS vs WHAT EXISTS

- DMP 2018 main report: Barapullah basin 376.27 km² (vs Najafgarh 977.26, Trans-Yamuna 196.93); "Barapullah Nallah/drain is the biggest drain which carries almost 80% of the storm water from this region and outfalls into River Yamuna." **Basin membership is not connection proof** for any particular drain (mission guard) — the register records the basin statement as CONFIRMED_THROUGH at basin level only.
- **Appendix XII is the model's junction-level connectivity evidence** (§2 above). It was **not** located as a signed/sealed as-built appendix beyond the IIT extraction; Appendices I–XI and XIII (including any as-built/outfall schedules) were **not accessible** (audit §2).
- **A named-system gap inside the official model itself**: "The Sunehri Nallah trunk does not appear by name in Appendix XII — candidate sections are JangpuraNallah (4 junctions) and PanthNagar Nallah (29 junctions)" (extraction doc s.3.6). Sunehri's model identity is **UNKNOWN** — preserved, not assumed.
- **Naming-collision traps documented**: "Kudesia Bagh Nallah" is a separate Appendix-XII section chain (J_9783→J_12081, inverts 212.99→204.97) on the Lodhi/Golf-Links side — **not** Kushak Part II; and **Qudesia/Qudsia Bagh Drain is CPCB Drain #6 outfalling at Qudsia Ghat, North Delhi (28.670N 77.230E)** — zero connection to Kushak/Barapullah (SEPARATE_SYSTEM, register CX-021). Generic "Barapullah Basin" statements are never used to merge these.

---

## 7. PUBLISHED GIS / MAP SERVICES

- **GSDL DIFC `storm_drain_08082024` MapServer** (https://gsdl.org.in/arcgis/rest/services/DIFC/storm_drain_08082024/MapServer) — live-verified 2026-09-16: 12 agency layers (NHAI, JAMIA, I&FC, FOREST, EDMC, North_DMC, SDMC, NDMC, PWD, DDA, DUSIB, DSIIDC). Counts via `returnCountOnly`: I&FC 377, SDMC 2,844, **NDMC 7,676**, **PWD 23,163**. Attribute/feature queries returned **0 rows for every where-clause tested** (f=json, f=geojson, with/without geometry) — the same server quirk documented in Phase 14A; the Sep-2026 on-disk extraction of the same service remains the evidence basis. Count-level liveness is recorded as evidence; feature-level re-verification is a documented blocker, **not circumvented**.
- **GSDL disclaimer governs all use**: department-submitted layers are explicitly *not ground-truthed*. GSDL geometry is therefore classified as DESIGN_INVENTORY — usable as documented inventory, never as hydraulic proof. Map proximity is never used as connection evidence anywhere in this phase.
- India-WRIS / NDMC GIS / MCD GIS drain centerline services: none located that cover the Kushak corridor with authoritative metadata (searched; see audit).

---

## 8. STRUCTURE-SPECIFIC CONNECTIVITY (summary; full matrix in deliverable D)

- **S-01 Kushak Bus Depot reach**: through-flow **documented by inspection** — 2025 JIR: 50 m wide, 5 bays, silt 1.5–3 ft, flow ~1 ft through **2/5 bays at DWF**; below-LLR-Marg culvert 5 bays (3 flowing, 2 clogged).
- **S-03 Defence Colony tributary**: CONFIRMED_INTO_KUSHAK (three official sources); 1,065 m, 9 vent shafts (2024); de-silting + wire-mesh directed 2025.
- **C-02 Berral-Shanti Path**: model junction J_4771 only (MODEL_ONLY).
- **C-03 Nauroji Nagar**: 1976 official outfall statement (Kidwai Nagar West) + 2018 model junction J_5670 — the best-attested lateral; both sources agree on the connection.
- **C-01/C-04 street sewers (Africa Avenue, Maharaja Agrasen)**: model-table connections only; storm/sewer classification unestablished.
- **C-07 Sunehri**: join sequence triple-confirmed; model-section identity UNKNOWN; 2024 CC record documents receiving-mainstem constrictions (Sunehripul 2/5 bays flowing, old Barapullah bridge 4/12 arches clogged).
- **C-09 AIIMS Nalla**: group-level only (1976 + 2023); individual junction AMBIGUOUS.
- **C-10 NDMC systems**: count-level (2 systems into Kushak) + GSDL feeder network; identities UNKNOWN.
- **B-01…B-07 structures**: connectivity along the spine is implicit in the through-flow records; **no document states individual culvert/bridge connectivity conditions beyond the inspected reaches.** The 1976–2026 chronology of structures is in `DELHI_KUSHAK_OPERATIONAL_TIMELINE.md` (companion phase).

---

## 9. CONNECTION CONFLICTS (all preserved, none silently resolved)

| # | Source A | Source B | Conflict | Possible explanations | Safe current interpretation | What would resolve it |
|---|---|---|---|---|---|---|
| C1 | NGT 2015 Para 10 ("Kushak drainage system" = whole southern collector) | DJB/NGT 2023 + project spine naming (Kushak = western spine to confluence) | What "Kushak" names | Para-10 narrative shorthand vs hydrographic naming | Use NGT-2023 DJB sequence as canonical; treat Para-10 as system-level prose | GNCTD notified drain nomenclature list (none public) |
| C2 | NGT 2015 Para 10 (DC drain meets Barapula "opposite Nizamuddin") | DJB/NGT 2023 (DC drain joins Kushak before Sunehri) | Join point east vs west of confluence | Narrative route description vs drainage-department sequence; both may be true at different specificity | Both preserved; junction location officially unreferenced | NGT court-commissioner junction map / bathymetry output (directed 2024, output non-public) |
| C3 | DMP Appendix XII downstream trunk labelled "khushak nala" (C_937) | NGT/DJB 2023 ("from this point called Barapulla") | Name of the downstream trunk reach | DMP labelling inherited from departmental template; naming non-standardized | Treat as naming inconsistency; connectivity itself (continuity to Barapullah) agreed by both | I&FC official reach-naming schedule |
| C4 | Appendix XII Sunehri absence | 1976 + 2023 official statements that Sunehri joins | Named system missing from named model | Sunehri carried under different model section name (JangpuraNallah / PanthNagarNallah candidates) | UNKNOWN model identity; official join fact retained | Appendix map cross-reference or GSDL node-name match |

**Additional conflict class (not counted as connection conflicts)**: elevation provenance — departmental old records contain adverse slopes (Nauroji 215.33; J_7549 old 210.010), IITD-corrected in the model. Corrections are model-side; as-built inverts remain unverified.

---

## 10. HISTORICAL CHANGES TO CONNECTIVITY (documented)

1. **1976** — MPD inventory records Sunehripulla, Naoroji Nagar, AIIMS, Lajpat Nagar drains as *Existing/Remodeling* and traceable; Kushak-Barapullah junction sequence as today.
2. **2007** — NDMC plan: 13/14 systems covered; Kushak 11 km total, 4.7 km covered — the covering of the western spine is documented state by 2007.
3. **2015** — NGT (13-01-2015) restrains further covering of Nallahs (operational timeline; connectivity-relevant as a change-freeze marker).
4. **2018** — DMP model assembled from departmental records with 20 adverse-slope corrections; represents the departmental record state, not a physical change.
5. **2022** — NMCG: sewage trapping of Kushak flow at Andrews Ganj SPS **completed** (Aug-2022) — interception of sewage component; stormwater connectivity unchanged.
6. **2024–2025** — bathymetry of Barapullah + Sunehripul + Kushak directed (2024, output non-public); Defence Colony de-silting + upstream wire-mesh directed (2025, in progress as of order date). No connectivity change evidenced; maintenance state changes documented in the operational phase.

No document evidences removal, rerouting, disconnection, or planned-but-uncompleted connections for any named Kushak lateral. PLANNED_ONLY count: **0** (nothing found; absence of a plan document is not proof none exists).

---

## 11. CATCHMENT RELEVANCE (no redrawing)

- Provisional working catchment: **27.66 km²** (project value; unchanged by this phase).
- Best-attested laterals inside any plausible catchment: Nauroji Nagar (5.4 km, 1976) and Defence Colony/Chirag Delhi (origin Mehrauli, 2023) — the Defence Colony upper catchment extends to Mehrauli, which is **far outside** the 27.66 km² provisional boundary; whether the provisional boundary ever included it is a project question this phase does **not** answer.
- Whether the two NDMC systems (CX-017) fall inside the provisional boundary **cannot be established from evidence** — their identities are UNKNOWN. Recorded as unresolved; catchment not redrawn.

---

## 12. WHAT THIS PHASE REDUCED vs WHAT REMAINS UNKNOWN

**Reduced by documentary evidence:** (1) Kushak→Barapullah→Yamuna continuity and confluence definition — triple-confirmed official; (2) Defence Colony and Sunehri join order and their official descriptions; (3) Nauroji Nagar's connection (two independent official sources, 1976 + 2018); (4) existence of two (unnamed) NDMC systems into Kushak near Dayal Singh College; (5) model-level junction identification for Berral, Africa Avenue sewers, Maharaja Agrasen sewers; (6) Qudesia ≠ Kushak/Barapullah (separate system, CPCB-numbered).

**Remain UNKNOWN (Tier-A):** (1) junction coordinates/georeferencing for every lateral join; (2) as-built condition and surveyed inverts of every connection (no GTS survey public); (3) identities of the two NDMC systems; (4) Sunehri's model-section identity; (5) AIIMS/INA/Lajpat Nagar individual join points; (6) storm-vs-sewer classification of the Africa Avenue / Maharaja Agrasen street networks; (7) the 2024 bathymetry output (directed but non-public) — the single document most likely to resolve (1), (2) and (5) at once.

**No model changes proposed or made.** The hydraulic network, parameters, and catchment are untouched; every value in this document is either quoted, cited to an on-disk official extraction, or explicitly labelled UNKNOWN.
