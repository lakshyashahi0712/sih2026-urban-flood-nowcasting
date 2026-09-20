# Kushak Nallah — Official Longitudinal Geometry Extracted from DMP 2018 Appendix XII

**Date:** 2026-09-11 · **Type:** evidence extraction (no code modified, no model built)
**Source PDF:** `data/delhi/raw/drainage/appendixxii.pdf` — IIT Delhi, *Drainage Master Plan for NCT of Delhi*, Final Report v5.1 (July 2018), **APPENDIX XII: Longitudinal Profiles of drains in Barapullah basin** (42 MB), downloaded from `https://ifc.delhi.gov.in/sites/default/files/inline-files/appendixxii.pdf`.
**Data artifacts:** `kushak_longitudinal_profile_curated.json` · `kushak_longitudinal_profile.csv` (84 unique nodes) · `kushak_corridor_dmp2018_appendixxii_rawparse.json` · `dmp2018_appendixxii_sections_index.json` (all in `data/delhi/raw/drainage/`).

---

## 0. Provenance ruling (read first)

| Class | What this data is |
|---|---|
| **IS it** | The **official departmental-record longitudinal geometry** of Kushak Nallah as digitized and model-corrected by IIT Delhi for the DMP 2018 (commissioned by I&FC GNCTD). Per-drain tables: junction Top/Invert levels (MSL) + conduit type, inlet→outlet connectivity, width/depth/diameter. |
| **IS NOT** | A **field survey certificate**. No GTS benchmark tie, no survey date, no contractor certificate accompanies these tables. `Old_Invert` = departmental record (provenance of record itself undocumented); `New_Invert` = IITD-corrected (interpolation/smoothing per DMP §2.4–2.5). Datum inconsistencies between agencies were previously proven (+6.24 m NDMC/SDMC jump in GSDL). |
| **Classification** | `OFFICIAL / MODEL_INPUT` (a superset of the GSDL `OFFICIAL/MODEL_INPUT (processed)` class). It is the **best publicly obtainable** longitudinal geometry for Kushak — but it does **not** upgrade any finding to "surveyed". Actual survey outputs (Nov-2024 bathymetric survey; NIT-52 drawings) remain with I&FC CD-XII / NDMC EE(R-III) — RTI targets. |

## 1. Answers to the seven asked items

| Asked | Found? | What |
|---|---|---|
| **Surveyed longitudinal invert** | **YES — departmental-record inverts, chain-complete** | 84-junction invert profile from Ridge head J_3055 (216.841 m) to modeled outfall J_7549 (203.752 m), with IITD corrections flagged (20 nodes where old≠new). |
| **Actual cross-sections** | **PARTIAL — per-conduit type/W/D from departmental records** | Kushak trunk + Part II: `RECT_CLOSED` 25.0 m top / 7.354–7.554 m depth / 10.0 m bottom. Defence Colony→Barapullah reach: varying RECT_CLOSE 22–33 m × 2.26–4.05 m, open-drain start 33.0 × 3.428, trunk link 60.0 × 4.812. Kudesia Bagh: 3.7 × 2.0. Street sewers: CIRCULAR Ø0.45–0.9. **Whether 25/7.354 is as-built clear dimension or departmental template remains UNVERIFIED** (constant repetition + prior GSDL template analysis). |
| **Underground box clear width** | **RECORDED, semantics annotated, survey status UNVERIFIED** | Appendix XII annotates the Part II conduits: *"DrainWidth Is Top Width"* (25.0 m) and *"Drain Dia Is Bottom Width"* (10.0 m) — so 25.0 = top width, 10.0 = bottom width. These are the same values previously flagged as GSDL template attributes; the annotation tells us what the department meant, not that it was surveyed. |
| **Underground box clear height (depth)** | **RECORDED: 7.554 m (upper 4 conduits) → 7.354 m (thereafter)** | Two distinct depth values — upper Part II reach (J_5105→J_5505) 7.554 m; from C_8968 (J_5505→) 7.354 m. |
| **Structure invert elevations** | **YES — per-junction, incl. IITD corrections** | Every junction carries Top_Level_MSL + Old/New invert. Notable corrections: J_4785 207.030→206.930, J_4897 207.030→206.245, J_4914 207.030→206.230, **J_7549 210.010→203.752 (adverse old record)**; Nauroji Nagar adverse 215.33 → 208.137–211.541. Pump/sump structures: Appendix VII lists PWD sumps with coordinates/dimensions but **contains no NDMC/Kushak pump entries** — Africa Avenue (241 HP) and Satya Sadan pumps remain news/tender-sourced only. |
| **Verified hydraulic connectivity** | **YES — DMP model connectivity via shared junction IDs** | Chains walk by conduit inlet→outlet across sections; tributaries verified by shared node IDs: Nauroji Nagar Nallah → Kushak Part II at **J_5670** (204.900 m); Berral–Shanti Path barrel → trunk at **J_4771** (208.114 m); Africa Avenue roadside sewers (A–E, W 0.4–0.7 m) terminate at **J_3141** (217.133 m) which sits on the Nauroji/Kushak head system; MAHARAJAAGARSEN MARG LHS/RHS street sewers (Ø0.45–0.6) discharge into Part II at J_6182/J_6043. **J_7549 is terminal** (Kushak outfall in the DMP Barapullah model). |
| **Actual current hydraulic geometry** | **PARTIAL** | "Current" = 2018 departmental state, not post-2018 desilting/reconstruction. Post-2018 change evidence: I&FC silt-removal targets (NGT, 14.02.2025): **Kushak 21,252 MT, Sunehri Pul 21,692 MT, Barapulla 113,120 MT** — volumes, not geometry. The Nov-2024 I&FC bathymetric survey output (DGPS + echo sounder, Sunheripul+Kushak+Bijwasan) is **not public** (NIQ acquired; award Nov-2024; RTI path documented). |

## 2. The longitudinal profile (New_Invert, m; IITD-corrected nodes marked †)

**Trunk "KushakNallah"** (Ridge → Sunehri Pul area; RECT_CLOSED 25.0 × 7.354 × 10.0):

| Node | Top | Invert | | Node | Top | Invert | | Node | Top | Invert |
|---|---|---|---|---|---|---|---|---|---|---|
| J_3055 | 224.195 | **216.841** | | J_4387 | 218.154 | 210.800 | | J_4771 | 215.468 | **208.114** (Berral join) |
| J_3115 | 223.946 | 216.592 | | J_4454 | 218.139 | 210.785 | | J_4775 | 215.316 | 207.962 |
| J_3168 | 222.746 | 215.392 | | J_4520 | 217.964 | 210.610 | | J_4767 | 215.302 | 207.948 |
| J_3258 | 221.846 | 214.492 | | J_4555 | 217.329 | 209.975 | | J_4772 | 215.215 | 207.861 |
| J_3303 | 221.646 | 214.292 | | J_4567 | 217.294 | 209.940 | | J_4774 | 215.211 | 207.857 |
| J_3369 | 221.042 | 213.688 | | J_4572 | 217.259 | 209.905 | | J_4758 | 215.108 | 207.754 |
| J_3406 | 220.075 | 212.721 | | J_4611 | 217.224 | 209.870 | | J_4757 | 215.100 | 207.746 |
| J_3455 | 220.005 | 212.651 | | J_4653 | 217.188 | 209.834 | | J_4745 | 214.904 | 207.550 |
| J_3525 | 219.951 | 212.597 | | J_4674 | 217.153 | 209.799 | | J_4736 | 214.852 | 207.498 |
| J_3565 | 219.745 | 212.391 | | J_4688 | 216.746 | 209.392 | | J_4723 | 214.800 | 207.446 |
| J_3614 | 219.643 | 212.289 | | J_4695 | 216.733 | 209.379 † | | J_4713 | 214.755 | 207.401 |
| J_3781 | 219.575 | 212.221 | | J_4711 | 216.707 | 209.353 † | | J_4702 | 214.746 | 207.392 |
| J_3849 | 219.508 | 212.154 | | J_4797 | 216.653 | 209.299 † | | J_4693 | 214.644 | 207.290 |
| J_3918 | 219.416 | 212.062 | | J_4790 | 216.632 | 209.278 | | J_4681 | 214.592 | 207.238 |
| J_4006 | 218.680 | 211.326 | | J_4779 | 216.480 | 209.126 | | J_4671 | 214.440 | 207.086 |
| J_4088 | 218.645 | 211.291 | | J_4782 | 216.231 | 208.877 † | | J_4665 | 214.418 | 207.064 |
| J_4124 | 218.410 | 211.056 | | J_4798 | 216.085 | 208.731 † | | J_4704 | 214.394 | 207.040 |
| J_4152 | 218.375 | 211.021 | | J_4811 | 215.924 | 208.570 | | J_4755 | 214.384 | 207.030 |
| J_4196 | 218.240 | 210.886 | | J_4819 | 215.872 | 208.518 | | J_4785 | 214.284 | 206.930 † |
| J_4261 | 218.205 | 210.851 | | J_4806 | 215.642 | 208.288 | | J_4897 | 213.599 | 206.245 † |
| J_4313 | 218.170 | 210.816 | | | | | | J_4914 | 213.584 | 206.230 † |

**"KushakNalla Part II" upper** (J_5105→J_6182; RECT_CLOSED 25.0 × 7.554→7.354 × 10.0):
J_5105 **206.033** → J_5330 206.007† → J_5336 206.006† → J_5408 205.998† → J_5505 205.987 → J_5532 205.944 → J_5561 205.785 → J_5587 205.600 → J_5626 205.183 → J_5670 204.900 (← Nauroji Nagar inflow) → J_5710 204.630 → J_5753 204.160 → J_5818 204.058 → J_5902 203.968 → J_5997 203.769† → J_6043 203.769† → J_6182 203.769†

**"Kushak Nalla Part II" lower → outfall** (J_6182→J_7549; RECT_CLOSED 25.0 × 7.354 × 10.0):
J_6182 203.769† → J_6863 203.767† → J_6891 203.767† → J_6920 203.766† → J_6976 203.765† → **J_7549 203.752†** (top 208.336; old record 210.010 was adverse — corrected; terminal in DMP model)

**Kudesia Bagh Nallah** (RECT_CLOSED 3.7 × 2.0): J_9783 212.99 (old 0.0, derived) → J_10548 211.1 → J_10822 208.37 → J_10900 207.909 → J_11490 **204.97** (old=204.97, genuine record) → J_12081 204.97.

**Barapullah trunk below Defence Colony reach** ("Chirag Delhi To Defense Colony Nallah" section; DMP labels the last conduit "khushak nala"): C_923 33.0×4.048 → … C_931–C_935 22–24 m × 2.26–3.80 → C_9029/C_936 33.0×3.428 *"start of open drain"* → **C_937 60.0×4.812 "khushak nala" → outfall J_1264**. Example junction J_12646: top 208.344, old 206.289 → new 203.532 — consistent with Kushak's 203.752 outfall ~0.2 m upstream.

## 3. Remaining UNKNOWN (unchanged by this extraction)

1. Whether the 25.0/10.0/7.354–7.554 dimensions are **as-built clear openings** vs departmental template values (prior GSDL forensics say template for the same numbers; the Appendix XII annotation defines semantics only).
2. **Vertical datum** of the MSL values (no GTS tie; known inter-agency datum conflict).
3. **Actual Nov-2024 bathymetric survey output** (I&FC CD-XII) — the true current bed profile post-desilting.
4. **NIT 52/EE(R-III) BOQ drawings** (L-sections/X-sections held for bidder inspection).
5. Post-2018 structural changes (culvert reconstruction, encroachment effects on clear openings).
6. The Sunehri Nallah trunk does **not** appear by name in Appendix XII — candidate sections are "JangpuraNallah From Hospital Road To Barapulla" (only 4 junctions parsed) and "PanthNagar Nallah – L.S.R College To Barapulla Nallah" (29 junctions); identification needs map cross-referencing.

## 4. Recommended use

- The 84-node profile + junction connectivity is now sufficient to build the **hydraulic network layout with OFFICIAL/MODEL_INPUT inverts** (still requiring monotonic-downhill checks against the † corrections and datum sensitivity runs).
- Cross-sections remain `OFFICIAL/MODEL_VALUE` with template suspicion → keep sensitivity ranges (e.g., clear width 10–25 m, depth 2.5–7.554 m bounds) until the bathymetric survey output or NIT-52 drawings are obtained via RTI.
- The CSV/JSON are ready for ingestion — **no hydraulic solver has been run or modified as part of this extraction**.

*Anti-fabrication note: every number above was read from `appendixxii.pdf` text; nothing was interpolated, invented, or "filled". Parser caveats: page-wrap artifacts affected a few conduit rows in Africa Avenue/KAUTILYA sections (counts flagged in the raw-parse JSON); the junction tables — the core deliverable — verified verbatim against raw text for all spot-checked IDs.*
