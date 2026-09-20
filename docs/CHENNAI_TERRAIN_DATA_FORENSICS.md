# Chennai Terrain Data Forensics — Surface Elevation Evidence for Adyar-Pilot Urban Flood Modelling

**Project:** SIH-2026 Urban Flood Nowcasting — Chennai extension (Adyar pilot)
**Status of this document:** forensic evidence register, September 2026
**Companion inventory:** [`data/chennai/terrain/terrain_inventory.csv`](../data/chennai/terrain/terrain_inventory.csv)
**Predecessor (Delhi method):** [`docs/DELHI_DEM_RECONNAISSANCE.md`](DELHI_DEM_RECONNAISSANCE.md)

Provenance classes used throughout (per task standard):
`OBSERVED/OFFICIAL` (dataset/product verified to exist from an authoritative source),
`DERIVED` (product verified, value computed by us from documented inputs),
`INFERRED` (existence supported by indirect but specific evidence),
`ASSUMED` (asserted without verification — flagged, never relied on),
`UNKNOWN`, `UNAVAILABLE`.

Access classes: `PUBLIC-DOWNLOAD`, `PUBLIC-API`, `PUBLIC-MAP-ONLY`, `REQUEST-BASED`, `RESTRICTED`, `PAID`, `ARCHIVED`, `BROKEN`, `UNAVAILABLE`, `UNKNOWN`.

Standing rules enforced in this report: a tender *requiring* LiDAR is not evidence that a LiDAR dataset exists or is public; "DEM" is never silently read as DTM; a 10 m posting is never upgraded to a 10 m accuracy; invert levels are never used as ground GCPs without explicit surface linkage; no datum is assumed without documentation.

---

## 1. Executive summary

**The single most important finding: a real airborne LiDAR dataset covering the lower Adyar basin exists.** A 2009 airborne laser scanning (ALS) flight over the urban lower reaches of the Adyar was used by the Anna University Institute of Remote Sensing (IRS) group to extract river cross-sections, manhole ground elevations, and 2-D model bathymetry, and is documented in three peer-reviewed/preprint works (Vidyapriya et al. 2012; Pradeep et al. 2023; Ajith Kumar et al. 2026 — the 2026 paper states verbatim that the cross-sections used were "obtained from the 2009 LIDAR images"). This is *not* a tender claim; it is a described input to published flood simulations validated against measured flood levels. However, the dataset has **no public download, no identified flight operator, no published density/datum metadata, and no tile index** — its provenance stops at the papers. It is the highest-value acquisition target in this file.

**What is actually obtainable today, verified:**
- **Copernicus GLO-30 (DSM, ~30 m, EGM2008)** — open download, zero friction; the repo already has a verified acquisition precedent for Delhi.
- **FABDEM V1-2 (bare-earth-class, ~30 m)** — open download from University of Bristol; a 2025 IEEE EarthSense study comparing DEMs for two Indian coastal cities (including Chennai) recommends it over raw Copernicus for flood inundation work. Not locally validated to survey points; the recommendation is the authors', not ours.
- **CartoDEM v3R1, 1 arc-sec (~32 m posting), DSM** — free after registration via Bhuvan/NRSC NOEDA. The free tier is **only** the ~32 m product; the **10 m posting is a priced commercial product** (Bhoonidhi/NSIL: ₹6,290 per 14×14 km tile; 2.5 m posting also exists commercially). An Anna University study demonstrably purchased 10 m CartoDEM tiles for Velachery (Adyar basin) in 2019 — purchase is realistic, not hypothetical.
- **Survey of India GT Bench Marks** — a real purchasable product (Helmert orthometric heights on Indian MSL; Rs 15,000 up to 3 points via the SoI online portal) — the only directly obtainable, datum-anchored vertical control for the pilot.
- **GCC storm-water drain (SWD) maps per zone** — official PDFs and AutoCAD files published per zone by Greater Chennai Corporation, mirrored by Arappor Iyakkam and OpenCity (this is the source of the Zone-1 DWG already extracted in this project, containing ~528 invert-level objects). Engineering-survey *geometry* (pipe sizes, invert heights, gradients), but the surveyed **road/ground levels embedded in the source CAD remain unexamined** — a defined local audit task (§10).

**What exists but is restricted:** the 2009 Adyar ALS; the GCC SWD engineering survey used in the 2026 model (119 km of network with invert heights and gradients; 30 outfalls with paired ground/invert levels); GCC's completed UAV-LiDAR + bathymetry of the Virugambakkam–Arumbakkam canal (6.3 km, Dec 2024); Anna University's 319-point DGPS survey of Velachery (invert levels only); any ADB/JICA/KfW/World Bank project survey deliverables (no public terrain files located).

**What is planned but does not exist:** GCC's Feb 2026 proposal for a LiDAR survey of ~1,000 km of bus-route roads (₹5 crore, Digital Twin programme; pilot on Khader Nawaz Khan Road) — no tender award or dataset release found as of 2026-09.

**Final situational classification: D — DATA ACQUISITION REQUIRED** (with a defensible PARTIAL for the §22 question: basin-to-corridor scale is supportable now; street-scale bare-earth is not, without acquisition).

---

## 2. Existing terrain gap (baseline being attacked)

The prior Chennai research conclusion, restated for the record: CartoDEM/Cartosat-class and Copernicus GLO-30 products are available and adequate for catchment/basin-scale work; no Chennai-specific high-resolution bare-earth DTM/LiDAR dataset was confirmed; road-elevation and drain-invert engineering survey data were not confirmed publicly available.

This forensics pass **breaks that conclusion in exactly one place**: the 2009 lower-Adyar ALS dataset demonstrably exists (as a research input, not a public product). It does not break the access conclusion: nothing at ≤10 m posting covering Adyar is publicly downloadable as of this audit. The gap now has a name, an approximate vintage, and a holding institution pattern (academic group + municipal survey source), which converts "does it exist?" into "who releases it?" — a fundamentally more actionable position.

---

## 3. LiDAR audit (high priority)

Search families executed (web, primary + combination forms): "Chennai LiDAR", "Greater Chennai Corporation LiDAR survey", "Chennai LIDAR survey tender", "Chennai airborne LiDAR", "Adyar LiDAR", "Chennai DTM LiDAR bare earth", "Chennai mobile/corridor LiDAR", "Chennai elevation LiDAR", plus combinations with GCC, CMDA, WRD, CMWSSB, TNUIFSL, World Bank, ADB, JICA, KfW, Smart City, AMRUT, DPR, topographic.

### 3.1 Candidate L1 — 2009 Adyar airborne LiDAR (the confirmed dataset)

| Attribute | Finding | Class |
|---|---|---|
| Did the survey happen? | **Yes** — used as model input in published work | OBSERVED/OFFICIAL (existence) |
| Survey date | 2009 (stated explicitly in Ajith Kumar et al. 2026: "cross-sections used for modelling obtained from the 2009 LIDAR images") | OBSERVED |
| Survey area | Lower/urban reaches of the Adyar basin; a 16.5 km urban stretch of the Adyar simulated; ALS DEM used for the 2-D domain of the MIKE FLOOD model | OBSERVED (extent approximate) |
| Resolution class | ALS-derived, "0.5–2 m" spatial class and "10–20 cm" vertical-error class stated generically for ALS DEMs in the 2026 paper's methods (paper's own wording, not a dataset spec sheet) | INFERRED (no product spec) |
| Point density / accuracy / classification / format | Not published anywhere found | UNKNOWN |
| Vertical datum | Not stated; the model works in "MSL" per Chennai practice | UNKNOWN |
| Tile index / download URL / license | None found | UNAVAILABLE (public), UNKNOWN (holding) |
| Covering Adyar? | **Yes** — that is its study area | OBSERVED |

Evidence chain (originals, not search pages):
1. Vidyapriya V., Ramalingam M., Raju K.S., Iyyappan M. (2012). "Airborne laser scanner data for floodplain mapping for Adyar watershed." *European Journal of Scientific Research* 82(2): 213–226. (Journal is defunct/paywalled-erratic; full text not retrieved this pass — flagged.)
2. Pradeep C., Sankar C.P. et al. (2023). "3-Way coupled urban flood modelling for a part of Chennai City using high-resolution topographic data." Anna University IRS preprint (ResearchGate 373607274).
3. Ajith Kumar K., Sankar C.P., Venkatramanan S., Pradeep C., Arun Bharathi V., Prabha K., Vidyasakar A. (2026). "Monitoring and simulation of Chennai floods through a high-resolution topographic datasets." *Discover Cities* 3:62. DOI: 10.1007/s44327-026-00238-8 (open access, CC BY-NC-ND 4.0). Full text read this pass; §2.2 (ALS DEM for the lower Adyar 2-D domain), §2.6 (GCC-surveyed SWD network, 119 km selected for the study area), §2.12 (invert heights/gradients), Table 3 (30 outfalls with ground level, invert level, 2015 MFL), and the limitations note attributing model error partly to cross-sections "obtained from the 2009 LIDAR images".

**Tender-trace rule applied:** no GCC/CMDA/CMWSSB tender found that *awarded* a Chennai-wide airborne LiDAR contract; the tenders encountered (e.g., a WAPCOS GeM bid for drone-LiDAR topographical survey, Mar 2025; NIHCL/NHIDCL corridor RFPs) are corridor or unrelated programmes. None establishes a public Chennai LiDAR product.

### 3.2 Candidate L2 — GCC UAV-LiDAR + bathymetry, Virugambakkam–Arumbakkam canal

The Hindu (29 Dec 2024): GCC "completed work on UAV LiDAR mapping and bathymetry survey of 6.3 km of the Virugambakkam–Arumbakkam Canal". Class: OBSERVED (existence, via official statement in press), access UNAVAILABLE (no release located). North-west Chennai; **does not cover Adyar**; relevant as precedent that GCC commissions UAV-LiDAR and holds the data in-house.

### 3.3 Candidate L3 — GCC road LiDAR / Digital Twin (planned)

DT Next (19 Feb 2026): GCC GIS Cell to undertake LiDAR survey of ~1,000 km of bus-route and key interior roads (₹5 cr) generating high-resolution road data and digital maps; pilot on Khader Nawaz Khan Road; part of a ~5 km² Digital Twin pilot (Nungambakkam/Greams Road/Anna Salai area). Class: ASSUMED (planned only). No GeM/CPPP tender award, no dataset, not Adyar, not yet real. Tracked as a future access opportunity.

### 3.4 Candidate L4 — "Carbon accounting of urban forest in Chennai using LiDAR"

Ramalingam/Iyyappan-circle publication (EJSR 81(3), 2012) documents an actual Chennai LiDAR flight (point density ~2 pts/m², 25 h 45 m flying hours quoted in snippets). Full text not retrieved; flight date, contractor, and area not confirmed this pass. Class: INFERRED (existence of *a* Chennai ALS campaign), plausibly the same 2009 acquisition as L1. Open follow-up.

---

## 4. High-resolution DTM/DSM audit (by resolution band)

| Band | Product class | Chennai finding |
|---|---|---|
| ≤1 m | ALS/TSLS point clouds, UAV-LiDAR | Only the 2009 Adyar ALS (restricted) and the 6.3 km canal UAV-LiDAR (restricted, non-Adyar). No public product. |
| 1–2 m | Engineering DTMs from project DPRs | DPR deliverables (Aarvee 2008 core-city SWD DPR; Tetratech 2011 extended-area ISWD DPR; ADB IUFM DDR 2022) necessarily contain surveyed geometry, but no terrain deliverable is public. |
| 2–5 m | CartoDEM 2.5 m posting | Exists as a priced NRSC/NSIL commercial product (Bhoonidhi FAQ table). No evidence it is DTM (it is a Cartosat-1 stereo DSM family). Adyar coverage would need purchased tiles. |
| 5–10 m | CartoDEM 10 m posting | Priced (₹6,290 per 14×14 km tile; ₹4,070 educational/other tier per FAQ). Purchased by Anna University for Velachery (Andimuthu et al. 2019, "CartoDEM data of 10 m resolution was procured from NRSC" — 4 tiles). DSM from stereo; urban accuracy in Chennai not published. |
| 10–30 m | CartoDEM v3R1 1-arc-sec (~32 m) free tier; Copernicus GLO-30 (~26–30 m effective); FABDEM (~30 m) | All obtainable (FABDEM/GLO-30 openly; CartoDEM free after registration). See §5–§6. |

Bare-earth vs surface discipline: **none** of the obtainable products except FABDEM makes a bare-earth claim; CartoDEM and GLO-30 are DSMs. "DEM" from these sources is not usable as DTM for street-scale depths.

---

## 5. CartoDEM deep audit (do not assume one resolution)

Currently documented NRSC/Bhoonidhi/Bhuvan product set (Bhuvan wiki "List of free satellite data products", retrieved this pass; Bhoonidhi NSIL commercial FAQ, 2024):

| Product | Posting | Access | Price | Format/coverage |
|---|---|---|---|---|
| CartoDEM v1 | 1″ (~32 m) | Bhuvan (free, registration) | free | 1°×1° tiles, GeoTIFF |
| CartoDEM v1.1R1 | 1″ (~32 m) | Bhuvan (free) | free | same |
| CartoDEM v2R1 | 1″ (~32 m) | Bhuvan (free) | free | same |
| **CartoDEM v3R1** | 1″ (~32 m) | **Bhuvan NOEDA (free)** | free | same; the standard "CartoDEM 30 m" |
| CartoDEM 10 m posting | 10 m, DSM, 14×14 km tiles | Bhoonidhi via NSIL | **₹6,290** (₹4,070 concessional tier) | commercial order |
| CartoDEM 2.5 m posting | 2.5 m | Bhoonidhi via NSIL | priced (rate in FAQ table) | commercial order |

Sensor lineage: Cartosat-1 (IRS-P5) along-track stereo, fore-aft ±26°/−5°, 2.5 m pan — all DEM products are **stereo-DSM** derivatives; buildings/vegetation included; no bare-earth filtering claimed by NRSC.
Vertical accuracy: NRSC's v3 specification quote (~3 m LE90 with GCPs) is a product-level global figure; **no Chennai-specific validation exists in anything we found**. The Anna University Velachery study (2019) *used* 10 m CartoDEM for sub-catchment delineation and simultaneously stated it was desirable to have "fine resolution DEM preferably with sub meter accuracy" they did not have — i.e., the local academic consensus treats 10 m CartoDEM as catchment-grade, not street-grade. We adopt that classification and do **not** upgrade a 10 m posting into a 10 m accuracy.
Chennai tile availability: 1°×1° free tiles covering Chennai (13°N, 80°E) exist (v3R1); free-download quota ~20 tiles/day per Bhuvan FAQ. 10 m tile purchase path: Bhoonidhi ordering interface.

---

## 6. Copernicus / FABDEM / alternative open DEM audit

| Product | Type | Native res. | Vertical datum | Accuracy (documented) | Access | Chennai-specific validation |
|---|---|---|---|---|---|---|
| Copernicus GLO-30 (DGED/COG) | DSM (TanDEM-X InSAR, hydro-edited) | 1″ (~26–30 m at 13°N) | EGM2008 | LE90 ≈ 1.7 m (tile XML carries per-tile values) | PUBLIC-DOWNLOAD (AWS S3 `copernicus-dem-30m`, Copernicus Data Space, Planetary Computer) | None found |
| **FABDEM V1-2** | bare-earth-class DSM (ML removal of buildings/forest bias from GLO-30) | 1″ (~30 m) | EGM2008 (inherits) | product-level (Bristol docs); no Chennai figure | PUBLIC-DOWNLOAD (Bristol data portal; GEE community catalog mirror) | Ganesh, Goswami, Nagendra (IEEE EarthSense 2025, Hyderabad) compared SRTM/CartoDEM/CoastalDEM/FABDEM/NASADEM/PALSAR for flood inundation in **two Indian coastal cities including Chennai** and report FABDEM performing best for their use; peer-reviewed venue, but **not** a survey-anchored local accuracy assessment — we do not call FABDEM locally validated terrain |
| ALOS AW3D30 v3.2 | DSM (optical stereo) | 1″ | EGM96 | RMSE ~4.4 m product-level | PUBLIC-DOWNLOAD (JAXA, registration) | None found |
| NASADEM / SRTM GL1 | DSM (C-band InSAR, Feb 2000) | 1″ / 3″ | EGM96 | LE90 ~6 m class | PUBLIC-DOWNLOAD (USGS) | Obsolete baseline; pre-dates most Chennai infrastructure |

No other legitimate open DEM at ≤10 m covering Chennai was found.

---

## 7. Survey of India / benchmarks / vertical control

- **GT Bench Marks dataset** — SoI's own portal text (AboutPortal): "Helmert orthometric heights (in meters) above the Geoid (Indian Mean Sea Level) along with the detailed description and Co[ordinates]". Priced product (PricingPolicy page: Rs 15,000 up to 3 BMs; PDF product). Class: OBSERVED/OFFICIAL, access PAID/REQUEST-BASED. This is the only directly purchasable, datum-documented vertical control relevant to the pilot. Practical value: anchor point(s) inside the Adyar corridor to tie any DEM/bias-correction to Indian MSL.
- SoI also advertises DGPS/RTK network activity and NHP-related work, but no Chennai large-scale topographic product or public benchmark database was found. Chennai sheets of 1:50k toposheets (66 D1/D5 era) exist as paper-lineage products, not modern terrain.
- Geodetic background (documented): Indian vertical datum = MSL of tidal observatories (Chennai/Madras is the founding GTS baseline city, 1802); national levelling epochs differ; heights in local engineering practice are "MSL" without epoch — see §12.

---

## 8. GCC / CMDA / CMWSSB engineering survey audit

**Greater Chennai Corporation (verified from chennaicorporation.gov.in, read this pass):**
- SWD department page states the city's flat terrain (average land ~2.0 m above MSL), drain-top 6 in above road level, manhole tops flush with footpath — i.e., GCC's own design standard ties drain geometry to road levels.
- DPR lineage: M/s Aarvee Associates engaged 19.06.2008 for the core-city SWD DPR (topographical survey basis; city divided into 4 basins/12 watersheds); M/s Tetratech engaged 2011 for extended-areas ISWD DPR (Adyar+Cooum, Kovalam, Kosasthalaiyar basins) — DPRs produced 2009/2012; works executed (345 km JnNURM; 406 km TNSUDP Adyar/Cooum at ₹1,387 cr; Kosasthalaiyar 508+ km ADB; Kovalam KfW). **No DPR, level book, or survey drawing is published on the site.** The engineering survey data exist (GCC's SWD dept. survey was used directly as model input in the 2026 paper) but are RESTRICTED.
- **SWD Network Maps page** (`/gcc/swd_net_maps/`): per-zone SWD maps with zone dropdown (JS-driven). Arappor Iyakkam's mirror (`arappor.org/gcc-swd-map/`) provides "PDF and AutoCAD files by Zone and Region"; OpenCity CKAN mirrors ward-level PDFs + a 2023 KML (`data.opencity.in/dataset/chennai-stormwater-drain-swd-maps`). Class: OBSERVED/OFFICIAL, PUBLIC-DOWNLOAD. Content class: engineering-survey geometry (alignment, sizes, invert annotations) — see §10.
- Feb 2026 Digital Twin/road-LiDAR plan (§3.3) — ASSUMED/PLANNED.
- Mar 2025: GCC AI/drone road-condition survey of 419 km BRR + 100 km footpaths (The Hindu) — condition data, not a released terrain product.

**CMDA:** Second Master Plan and the 2010 "Seminar on Waterways" proceedings (cmdachennai.gov.in PDFs; cited by the 2026 paper for carrying capacity and tidal levels) — reports with river capacity figures (Adyar ~1,104 m³/s), not released survey geometry.

**CMWSSB:** ADB TNUFIP/CCRWSSP project IEEs/ESIAs hosted on cmwssb.tn.gov.in (e.g., Nessapakkam CCRWSSP doc; TNUFIP UGSS IEEs) — these document utility corridors and construction but publish no elevation points. Class: OBSERVED (programmes), UNAVAILABLE (terrain deliverables).

**TNUIFSL:** fund manager for the SWD programmes (ESMF/EARF public); no survey deliverables published.

---

## 9. Flood-project survey audit

| Programme | Funder/Agency | Terrain evidence | Access |
|---|---|---|---|
| Integrated Urban Flood Management, Chennai–Kosasthalaiyar (49107-012/013) | ADB | Loan docs/IEED name a "Digital Elevation Model" among inputs; ₹561.29 cr approved 2021 | RESTRICTED/UNKNOWN — no public terrain file |
| Missing-Links SWD EIA (Jan 2021), core city Zones IV–XIII | World Bank (TNSUDP via TNUIFSL) | EIA text read this pass: 45 km drains, design rainfall 68 mm/h, silt pits every 10–30 m — **no levels published**; zones are core-city, not Adyar | PUBLIC-DOWNLOAD (EIA only), UNAVAILABLE (terrain) |
| ISWDP Kovalam M1/M2 ESIA (GCC-hosted PDF) | KfW | Environmental/social only; not Adyar | PUBLIC-DOWNLOAD (ESIA), UNAVAILABLE (terrain) |
| CCRWSSP / TNUFIP sub-projects | ADB via CMWSSB | IEEs list baseline surveys; no elevation points | UNAVAILABLE (terrain) |
| CRRT Adyar/Cooum ecological restoration | GoTN/JICA-linked | Restoration plans public; survey geometry not | UNAVAILABLE (terrain) |
| C-FLOWS Chennai (NCCR + PSA office + IITs, 2018) | GoTN/PSA | Ward-level DSS with elevation/surface layers internal to the system | RESTRICTED (not a public dataset) |
| NRSC 2015 Chennai flood assessment (DMS division) | NRSC/ISRO | Satellite+field flood-depth atlas (public PDF via NIDM) — flood depths, not terrain | PUBLIC-DOWNLOAD (atlas) — explicitly **not** a terrain source |

---

## 10. CAD surface-elevation audit (GCC SWD CAD source)

Established source chain: GCC per-zone SWD maps → Arappor mirror (PDF+DWG by zone) → our Zone-1 DWG extraction (~528 INVERT LEVEL text objects). This CAD is **engineering-survey geometry of the drainage network**, not a terrain product.

**Task 16 answers (pre-registered, to be confirmed by the local CAD audit below):**
- **A. Constrain drainage bed elevation? YES** — that is what invert levels are.
- **B. Constrain road surface elevation? NO/conditional** — only if a label explicitly pairs road/ground level with the invert (GCC standard: drain top ≈ road level + 150 mm; footpath-flush manhole tops). Any such pair must be quoted verbatim from the CAD text.
- **C. Constrain ground terrain? NO** — inverts sit below grade by design depth (typically 0.6–2 m+); treating them as ground biases the terrain down by exactly the burial depth, systematically worse in low-lying areas.
- **D. Use as GCPs? NO** — unless the source explicitly establishes surface linkage (a documented manhole-cover RL or "GL" label at the same node).
- **E. Conditions:** paired labels (GL + IL), datum note in the title block, and survey-date evidence. Absent all three: invert data stay in the hydraulic network model only.

**Local audit specification (executable next, on the extracted Zone-1 DWG):** convert with ODAFileConverter (DWG→DXF); scan with `ezdxf`: all TEXT/MTEXT/DIMENSION string values; token classes: `GL`, `G.L`, `GROUND LEVEL`, `ROAD LEVEL`, `RL`, `R.L`, `EXISTING LEVEL`, `FORMATION LEVEL`, `SPOT LEVEL`, `BM`, `BENCHMARK`, `MANHOLE TOP`, `TOP LEVEL`, `CHAMBER TOP`, `CROSS SECTION`, `L.S`, `CONTOUR` vs the invert family `INVERT`, `I.L`, `IL`, `BED`, `BED LEVEL`, `SOFFIT`, `PIPE INVERT`. Output: counts per class, layer names, coordinate scatter, and a CSV of any surface-class candidates with their XY. Numeric sanity gate: surface-class values should cluster ≈ 1.5–10 m (GCC's stated 2.0 m average MSL context); values ≤ 0 m or > 15 m get flagged for review rather than silently used.

---

## 11. Adyar-specific terrain availability (smallest area with strongest data)

| Terrain source | Covers Adyar? | Notes |
|---|---|---|
| 2009 ALS | **Yes** (lower basin) — the exact pilot area | Restricted; the single most valuable target |
| GCC SWD engineering survey (via 2026 paper) | Yes — 119 km network in the study stretch + 30 outfalls | Restricted; ground+invert pairs for 30 outlets are already published in the paper's Table 3 |
| Anna U Velachery DGPS (319 pts) | Yes (Velachery = upper Adyar basin) | Invert levels only |
| GCC SWD CAD (Zone-wise) | Yes — zones in the Adyar basin | Public; invert-dominant; surface-label audit pending |
| CartoDEM v3R1 (~32 m) | Yes | Free; DSM |
| CartoDEM 10 m | Yes (per-tile purchase) | Paid; DSM; realistic purchase precedent |
| Copernicus GLO-30 / FABDEM | Yes | Open; DSM / bare-earth-class |
| SoI GT Bench Marks | Yes (select BMs purchasable) | Paid; vertical anchor |
| Canal UAV-LiDAR (Virugambakkam–Arumbakkam) | No | North-west city |

A high-quality 5×5 km pilot tile (e.g., Saidapet–Kotturpuram–Nandambakkam corridor around the river) is the right target: the 2026 paper independently flags Manapakkam, Nandambakkam, Jafferkhanpet, Saidapet and Kotturpuram as the 2–7 m depth hotspots — i.e., the highest-value streets for terrain fidelity sit inside one small box.

---

## 12. Vertical datum analysis (hard requirement)

- **Chennai practice:** municipal/WRD elevations are quoted "MSL" following the Indian datum lineage (Madras is the GTS origin city; Indian MSL defined from tidal observatories incl. Madras). GCC states average city land ≈ 2.0 m above MSL; Adyar basin terrain spans ~1.5–10 m MSL in the low corridors.
- **Open DEMs:** GLO-30/FABDEM are EGM2008 orthometric; AW3D30/SRTM/CartoDEM-v3 free tier are EGM96-era. The Indian local MSL datum and EGM2008 differ by a region-scale offset (decimetre-to-metre class at Chennai's latitude; the precise local value is not established in any document we found).
- **Consequence:** a 1–2 m geoid/datum mismatch is **material** for a city whose average land elevation is ~2 m. Therefore: (1) never subtract datasets with different vertical references; (2) any fused product must be tied to Indian MSL via SoI GT Bench Marks (or GCC/WRD benchmark values quoted in official documents); (3) record every source's vertical datum in the inventory (done, `vertical_datum` column); (4) the EGM2008→Indian-MSL offset for Chennai is a **known unknown** — resolve it once, at the SoI-BM step, before any fusion.
- **Horizontal CRS:** everything open is EPSG:4326; GCC CAD/works drawings are typically local-grid or UTM 44N (EPSG:32644) — the Zone-1 DWG CRS must be confirmed from the CAD before any overlay.

---

## 13. Multi-source fusion feasibility (analysis only — no fused DTM is created)

Prerequisites before choosing a method (all must pass):
1. ≥ 30 verified surface-elevation points inside the pilot tile (sources: SoI BMs; GCC "GL"/road-level labels if the CAD audit finds them; the 30 published outfall ground levels from the 2026 paper's Table 3 — *their surface status must be treated as conditional because "Ground Level" there is an engineering attribute, not a surveyed spot level, until corroborated*).
2. Datum homogenisation (all points → Indian MSL).
3. Geometry check: spatial distribution (clustered vs corridor-spread), density (points per km²), and vertical spread (if the point population's residual spread vs FABDEM exceeds ~2 m, the points, not the DEM, are suspect first).

Then, defensible methods in order of preference for our data regime (sparse, unevenly distributed 1-D control on a 30 m DSM):
- **Local bias correction (mean/IDW of DEM-minus-point residuals, corridor-weighted)** — most defensible with < 100 points; produces an honest, auditable correction.
- **Thin-plate spline / local residual interpolation** if points exceed ~100 and are spatially spread.
- **Kriging/co-kriging** only if residual variography is stable (needs ≥ 150 points realistically).
- **Trend-surface correction** as a sanity cross-check, not the primary product.
Inverts are admitted **only** as hydraulic-network constraints (bed datum), never as terrain control (§10). Building/road masking: FABDEM already removes building bias at 30 m; do not double-correct.

---

## 14. Terrain suitability matrix

| Dataset | Real/local | Resolution | Vert. accuracy | Datum known | Surface validity | Adyar | Access | Flood-model usefulness |
|---|---|---|---|---|---|---|---|---|
| 2009 Adyar ALS | Yes (real, local) | ~0.5–2 m class | 10–20 cm class (paper's generic ALS statement) | Unknown | Bare-earth-class DTM (published use) | **Yes** | Restricted | **Highest** — but only via acquisition |
| GCC SWD eng. survey | Yes | point/network | unspecified | MSL (practice) | inverts (network), ground levels at 30 outfalls (conditional surface) | Yes | Restricted | Hydraulic geometry: high; terrain: conditional |
| GCC SWD CAD (public) | Yes | vector+labels | n/a | unlabelled in CAD | network geometry; surface labels TBD (§10 audit) | Yes | PUBLIC-DOWNLOAD | Drainage network; conditional surface labels |
| Anna U Velachery DGPS | Yes | 319 pts | DGPS-class (unstated) | unstated | **Inverts only** | Yes (upper basin) | RESTRICTED (in paper) | Drainage network only |
| SoI GT Bench Marks | Yes | points | survey-grade | **Indian MSL (explicit)** | Spot BMs (surface) | Yes (select points) | PAID | Vertical anchor — essential |
| CartoDEM v3R1 (~32 m) | Yes (India-wide) | ~32 m | not locally validated | EGM96-era | DSM | Yes | PUBLIC-DOWNLOAD (reg.) | Catchment delineation only |
| CartoDEM 10 m | Yes | 10 m | not locally validated; priced | NRSC spec (global) | DSM | Yes (per tile) | PAID | Catchment/sub-basin; not street-scale |
| Copernicus GLO-30 | Yes (global) | ~26–30 m | LE90 ≈1.7 m (tile XML) | EGM2008 | DSM | Yes | PUBLIC-DOWNLOAD | Basin/corridor backbone |
| FABDEM V1-2 | Yes (global) | ~30 m | product-level | EGM2008 | **Bare-earth-class** | Yes | PUBLIC-DOWNLOAD | Best open terrain base for the pilot; preferred by the 2025 coastal-city comparison |
| AW3D30 / NASADEM / SRTM | Yes (global) | ~30 m | 4–6 m class | EGM96 | DSM | Yes | PUBLIC-DOWNLOAD | Baseline comparison only |
| C-FLOWS elevation layers | Yes | unknown | unknown | unknown | unknown | Yes | RESTRICTED | None (not obtainable) |

Explicitly **excluded from terrain** (task §20): OSM/Google terrain, hillshades, screenshots, elevation APIs without provenance, terrain inferred from flood maps, invert levels as terrain, building heights as terrain, media graphics, reanalysis elevation, uncontrolled interpolation.

---

## 15. Recommended terrain stack (Chennai hierarchy)

- **LEVEL 1 — Survey-grade local DTM/LiDAR/RTK:** 2009 Adyar ALS (if acquired); GCC UAV-LiDAR (if released); future GCC road-LiDAR (if delivered open). *Supports:* street-scale depths, inlet submergence, kerb/underpass relief. *Cannot support:* anything until obtained.
- **LEVEL 2 — Engineering topographic survey:** GCC SWD surveyed network (inverts, gradients) + any CAD surface labels found in §10 + SoI GT Bench Marks. *Supports:* hydraulic network datum, vertical anchoring, conditional surface checks. *Cannot support:* 2-D street depths alone.
- **LEVEL 3 — High-resolution photogrammetric terrain:** none identified for Chennai (no public UAV-photogrammetry DTM found). Empty level — documented gap.
- **LEVEL 4 — High-resolution national DEM:** CartoDEM 10 m (paid) / 2.5 m (paid). *Supports:* sub-basin delineation, corridor slopes. *Cannot support:* street-scale depths (DSM; unvalidated locally).
- **LEVEL 5 — 10 m class (CartoDEM v3R1 ~32 m free):** catchment-scale work. *Cannot support:* street-scale claims.
- **LEVEL 6 — 30 m open (FABDEM primary, GLO-30 secondary):** the operative terrain base today. *Supports:* basin-to-corridor flood extent/depth at honest resolution; FABDEM preferred (bare-earth-class, coastal-city comparison). *Cannot support:* street-gutter/kerb-scale claims.

**Operative stack for the Adyar pilot today:** FABDEM V1-2 (terrain base) → GLO-30 (cross-check) → SoI GT Bench Marks (datum anchor, once purchased) → GCC CAD network (hydraulic geometry; surface labels pending audit) → published outfall ground/invert pairs (conditional control, corroborated before use).

---

## 16. Remaining terrain uncertainties

1. **2009 ALS full metadata** (operator, area, density, datum, format, holding institution) — UNKNOWN until a GCC/IRS/author response.
2. **EGM2008 ↔ Indian-MSL offset at Chennai** — unresolved (decimetre-to-metre scale); blocks honest datum tie-in until a BM is used.
3. **Chennai-specific vertical accuracy of every obtainable raster** — none locally validated; the 2025 EarthSense FABDEM preference is model-behaviour evidence, not accuracy measurement.
4. **Surface-elevation content of GCC SWD CAD** — pending the §10 audit on Zone 1 (and then other Adyar-basin zones).
5. **Datum of the SWD CAD numbers** — likely MSL by practice; must be confirmed from title block/notes.
6. **2015→2026 terrain change** (regrading, road raising — GCC itself documents manhole chambers raised ~6 in; Feb 2026 FB post) — no dataset quantifies it.
7. **Vidyapriya 2012 full text** — needed to close the 2009-ALS provenance chain (journal defunct; retrieval flagged).
8. **Carbon-accounting LiDAR flight details** — possibly the same 2009 campaign; unresolved.

---

## 17. Exact acquisition actions (in order, with the blocker each removes)

1. **Email the corresponding author** (Vidyasakar A., a.vidyasakar@gmail.com, per the 2026 paper; CC IRS Anna University) requesting: the 2009 ALS DEM provenance (provider, extent, density, datum) and whether the dataset can be shared for research. *Removes:* the biggest single uncertainty (U1).
2. **RTI application to GCC** (SPIO, Greater Chennai Corporation): (a) survey reports/DPR annexes for SWD zones in the Adyar basin including any road-level/GL records; (b) the Virugambakkam–Arumbakkam UAV-LiDAR + bathymetry survey (2024) — existence, extent, and public-release status; (c) the 2009 Adyar LiDAR — whether GCC holds or commissioned it. *Removes:* U1, U4, and the "restricted" wall on GCC survey data.
3. **Bhoonidhi/NSIL order (or quote request): CartoDEM 10 m posting** tiles covering the Adyar pilot (14×14 km tiles; ₹6,290 standard tier). *Removes:* the 5–10 m band absence; precedented by the 2019 academic purchase.
4. **SoI GT Bench Marks order** (onlinemaps.surveyofindia.gov.in, Rs 15,000 up to 3 BMs): select BMs inside the pilot corridor. *Removes:* the datum anchor gap (U2) — this is the prerequisite for any fusion.
5. **Download now (zero cost):** FABDEM V1-2 tiles (Bristol portal), Copernicus GLO-30 tile(s) `N13_00_E080_00` (S3/Copernicus Data Space), CartoDEM v3R1 1° tile (Bhuvan, registration), AW3D30 (JAXA, registration) — for the §18 quality screen. *Removes:* nothing about resolution, but establishes the honest 30 m base immediately.
6. **Monitor:** GeM/CPPP for the GCC 1,000 km road-LiDAR tender award; GCC SWD map page updates for new zones/DWG; *Discover Cities* group publications for ALS metadata.
7. **If (1)–(4) all stall:** commission the 5×5 km RTK/UAV-photogrammetry pilot over the Saidapet–Kotturpuram–Nandambakkam hotspot box (spec separable; ~2–4 weeks field work), tied to purchased SoI BMs. This is the only path that *guarantees* street-scale terrain regardless of institutional response.

---

## 18. Source register

**Papers (originals):**
- Ajith Kumar K. et al. 2026, *Discover Cities* 3:62 — landing: https://doi.org/10.1007/s44327-026-00238-8 (OA, CC BY-NC-ND)
- Andimuthu R. et al. 2019, *Sci Rep* 9:7783 — https://pmc.ncbi.nlm.nih.gov/articles/PMC6533249/ (OA)
- Vidyapriya V. et al. 2012, *EJSR* 82(2):213–226 — record: https://www.researchgate.net/publication/275957154 (full text NOT retrieved)
- Pradeep C. et al. 2023 preprint — https://www.researchgate.net/publication/373607274
- Ganesh V., Goswami S., Nagendra H. 2025, IEEE EarthSense — https://doi.org/10.1109/earthsense66084.2025.11297222
- Carbon-accounting LiDAR record — https://www.researchgate.net/publication/287932487

**Official portals / downloads:**
- GCC SWD department: https://chennaicorporation.gov.in/gcc/department/storm-water/
- GCC SWD network maps: https://chennaicorporation.gov.in/gcc/swd_net_maps/
- Arappor GCC SWD mirror: https://arappor.org/gcc-swd-map/
- OpenCity CKAN mirror: https://data.opencity.in/dataset/chennai-stormwater-drain-swd-maps
- Bhuvan free products list (CartoDEM v3R1 ~32 m): https://bhuvan.nrsc.gov.in/wiki/index.php/List_of_free_satellite_data_products — order via https://bhuvan.nrsc.gov.in (NOEDA)
- Bhoonidhi (10 m/2.5 m priced CartoDEM, NSIL FAQ PDF): https://bhoonidhi.nrsc.gov.in/bhoonidhi
- Survey of India portal (GT Bench Marks): https://onlinemaps.surveyofindia.gov.in/AboutPortal.aspx ; pricing: https://onlinemaps.surveyofindia.gov.in/PricingPolicy.aspx
- Copernicus GLO-30: https://dataspace.copernicus.eu/explore-data/data-collections/copernicus-contributing-missions/collections-description/COP-DEM ; S3: `s3://copernicus-dem-30m/` (tile for Chennai: `Copernicus_DSM_COG_10_N13_00_E080_00`)
- FABDEM V1-2: https://research-information.bris.ac.uk/en/datasets/fabdem-v1-2/ ; community mirror: https://gee-community-catalog.org/projects/fabdem/
- AW3D30: https://www.eorc.jaxa.jp/ALOS/en/aw3d30/
- ADB IUFM project docs: https://www.adb.org/projects/documents/ind-59311-001-rrp (and 49107 series)
- World Bank TNSUDP Missing-Links SWD EIA (mirror): https://studylib.net/doc/28948249/gcc-missing-links-swd---eia-report-
- KfW ISWDP Kovalam ESIA (GCC-hosted): https://chennaicorporation.gov.in/gcc/pdf/ISWDP_Kovalam_M1M2_ESIA_Ph1s.pdf
- NRSC 2015 Chennai flood atlas (via NIDM): https://nidm.gov.in/PDF/pubs/ChennailFlood_NIDM2021.pdf
- CMDA waterways seminar: https://www.cmdachennai.gov.in/pdfs/SeminarOnWaterways/7.pdf

**Press (existence evidence, secondary):**
- The Hindu, GCC UAV-LiDAR canal survey (29 Dec 2024): https://www.thehindu.com/news/cities/chennai/greater-chennai-corporation-takes-steps-to-improve-water-carrying-capacity-of-canals-in-the-city/article69040333.ece
- DT Next, GCC LiDAR road survey plan (19 Feb 2026): https://www.dtnext.in/news/chennai/chennai-corporation-to-create-digital-model-of-city-map-1000-km-of-roads-for-planning
- The Hindu, GCC AI road survey (24 Mar 2025): https://www.thehindu.com/news/cities/chennai/fewer-jolting-rides-and-safer-walks-soon-chennai-corporation-to-map-roads-footpaths-with-ai-technology/article69365083.ece
- The Wire Science, C-FLOWS (22 Oct 2018): https://science.thewire.in/society/urban/nccr-develops-warning-system-for-flooding-in-chennai-with-ward-level-detail/

---

## 19. Final decision matrix and verdict

**Category: D — DATA ACQUISITION REQUIRED** (with the PARTIAL nuance below).

- **What we can use now (verified):** FABDEM V1-2 + GLO-30 (open), CartoDEM v3R1 ~32 m (free/registration), GCC SWD CAD network geometry (public), NRSC 2015 flood atlas (for independent comparison, not terrain).
- **What can be improved:** CAD surface-label audit (§10) may add true surface points for free; the 30 published outfall ground levels may become corroborated surface control; SoI BMs anchor the datum once purchased.
- **What exists but is restricted:** 2009 Adyar ALS; GCC SWD engineering survey; canal UAV-LiDAR; C-FLOWS layers; ADB/JICA/KfW project terrain.
- **What must be acquired:** author/GCC responses (actions 1–2), CartoDEM 10 m tiles (action 3), SoI BMs (action 4), or the fallback RTK/UAV pilot (action 7).

**§22 answer: PARTIAL.**
- **YES (now, defensibly):** a bare-earth-class ~30 m surface (FABDEM) for the **whole Adyar basin and river corridor**, on a documented vertical reference (EGM2008), with basin-scale flood-extent/depth claims supportable at 30 m honesty; corridor-scale hydraulic geometry from GCC CAD inverts for the drainage network.
- **NO (not from public data):** street-scale bare-earth at 1–5 m with a measured vertical accuracy — no obtainable dataset supports kerb/camber/underpass-scale depth claims, and none of the obtainable products has a Chennai-validated vertical accuracy.
- **PARTIAL portions:** the parts of the pilot that can be high-resolution *today* are exactly those covered by public engineering geometry (drain alignments, 30 outfall pairs) — corridors, not surfaces. The street-scale surface becomes obtainable only via: 2009-ALS release, GCC road-LiDAR delivery, CartoDEM 10 m purchase (improves to DSM 10 m, still not bare-earth), or the 5×5 km survey campaign.
- **Street-scale flood-depth claims still unsupported by evidence:** ponding depth on specific streets; kerb-to-kerb flow spread; underpass/sump depths; inlet-submergence timing at individual drains; any claim requiring < 1 m vertical certainty. These remain **unsupported** until one of the acquisition actions lands — and we will not fake them by resampling 30 m terrain or reusing invert levels as ground.
