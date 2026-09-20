# Delhi V2 — Data Gap Closure Report (Kushak Nallah)

**Date:** 2026-09-11 · **Scope:** data acquisition research only — no code, no model changes, no synthetic data.
**Manifest:** `data/delhi/raw/MANIFEST_RECON_20260911.json` (31 items, SHA-256 per file). Prior raw acquisitions (GLO-30, WorldCover, GSDL extracts, IEM CSVs, IMD bulletins, hydraulic extracts) untouched.

---

## 1. Headline findings

1. **Aab Prahari (IIT Delhi) raw flood-report API is PUBLIC and UNAUTHENTICATED — acquired in full.** 106 dates (2022-07-01 → 2026-09-07), **731 citizen waterlogging reports**, 723 geolocated, each with timestamp, reverse-geocoded location, depth class (Ankle 532 / Knee 130 / Thigh 46 / Waist 9 / Above Head 12 / >Head 2) and photo link. **2023-07-09 = 24 reports / 22 unique locations concentrated in the Kushak corridor** (IIT campus, Jia Sarai, Hauz Khas, Aurobindo Market, South Ex-II, AIIMS/Ansari Nagar, Safdarjung, Kidwai Nagar). This **overturns the earlier RESTRICTED ruling** — the raw data is downloadable; it is crowdsourced and must stay labeled as such. Citizen photos were intentionally NOT downloaded (privacy).
2. **NOAA NCEI ISD global-hourly acquired for both benchmark events** — Safdarjung `42182099999` + IGI `42181099999`, 2023 & 2024. Verified: Safdarjung AA1 `24,1530` = **153.0 mm/24 h ending 08:30 IST 9-Jul-2023** (exact match with IMD's official figure); `24,2280` = **228.0 mm/24 h ending 28-Jun-2024** (matches IMD's 228.1 mm). This is the best machine-readable OBSERVED rainfall available. Limitation: 3-hourly SYNOP buckets (differencing cumulative AA1), not 1-hourly; Palam/Lodhi Road/Ayanagar/Ridge are NOT in ISD.
3. **The real Kushak survey is I&FC's, NGT-mandated, and its output is not public.** NGT order 06-08-2024 (OA 6/2012) records the Chief Secretary directing I&FC to run a bathymetric survey of Barapullah incl. Sunehripul + Kushak drains. Official NIQ `niq_cdxii0810.pdf` (DGPS + echo sounder, Civil Division XII) acquired; award (12-Nov-2024, Rs 2.45 lakh, Aar Pee Electrical Engineering Works) confirmed via aggregator. **The survey output (cross-sections, L-sections, AutoCAD) is held by I&FC CD-XII → RTI target.** The "NDMC SP Marg–Satya Sadan survey" premise is not corroborated as a public artifact; NDMC's verifiable Kushak activity is works-tendering (desilting NIT 52, robotic mapping 2025-26, cGanga rejuvenation Rs 169.57 Cr).
4. **NGT orders are the richest official connectivity/culvert source found** (both acquired as HTML): Kushak below Lala Lajpat Rai Marg culvert = **5 bays (3 flowing, 2 clogged)**; Sunehripul below LLR Marg = 5 bays (2 flowing, 3 clogged); old Barapullah bridge 12 arches (4 clogged); **Barapullah starts where Sunehripul meets Kushak**; Defence Colony drain 1,065 m, 9 vent shafts, joins Kushak; GK-I B-block 945 m (645 covered/300 open), 10 vent shafts; A1–A7 stretch mapping; 600 m inaccessible stretch opposite INA Market; desilting volumes (10,000 m³ A7–B etc.).
5. **Full IIT Delhi DMP 2018 PDF set acquired** (main report v5.1 + appendices IV–XIV from ifc.delhi.gov.in). Appendix IV = Pumps & Sumps; V = L-profiles Trans-Yamuna; **VI = L-profiles of drains in other basins (Kushak bed levels expected here)**; VII–XIV pending parsing. Main report verbatim: Barapullah basin **376.27 km²**; contains a **"model deduced flooding hot spots along with reported (as observed) extreme water logging events" inventory** — an official flood-observation validation asset. The string "Kushak" does NOT occur in main-text prose (figures/annexures only).
6. **No independent source corroborates a 35.4 km² Kushak catchment.** Official values found: **3.5 km²** (PIB Lok Sabha QA Feb 2023, CGWB recharge-works context; CGWB 2011 extract already local) and **2.03 km² = 502 acres for a 3,220 m stretch** (MCD storm-drain doc, Scribd rehost). The working **27.66 km² (2 m burn) stays DERIVED/PROVISIONAL** with an explicit reconciliation note: official figures likely count the nala's own micro-catchment; the model's D8 area counts the urban contributing surface. Neither validates the other.
7. **IEM METAR precipitation is empty for Indian stations** (p01m = 0.00 through the July-2023 window; verified) — the previously acquired IEM CSVs are occurrence-timing only. **Meteostat and Open-Meteo archive both underestimate the benchmark events by ~5–10×** (2023-07-08/09: ≈31.6/15.7 mm vs 153 observed) — NOT defensible for event forcing.
8. **Delhi eProcurement portal (browser-verified):** anonymous keyword search "Kushak" → *No Tenders found*; advanced search submit hangs; NIT 52/EE(R-III)/2025-26 BOQ requires free bidder registration. NIT extract confirms **L-sections, cross-sections and invert profiles are held in the EE(R-III) office, inspection restricted to pre-qualified bidders** → RTI/registration path.
9. **DTP live waterlogging page now 404s** (site rebuilt; browser-verified). The 2021 table survives in a Wayback snapshot — **acquired (792 KB HTML, ~200+ rows: road, specific location, dates, frequency)** incl. Africa Avenue, INA→AIIMS underpass (freq 3), Aurobindo Marg AIIMS→Barapulla flyover, IIT/Adhchini.
10. **I&FC daily flood-control-room reports follow a live pattern `ifc.delhi.gov.in/.../universal/DDMMYYYY.pdf`** ("Status of action at Vulnerable Points" tables) — 3 samples acquired; bulk enumeration feasible. FCO 2021/2023/2024/2026 are 404 at the known URL pattern (only fco_2025.pdf ever archived); FCO 2024 survives only as a Scribd copy.

---

## 2. Master source table

Status vocabulary: FOUND_RAW / FOUND_PARTIAL / FOUND_OFFICIAL_DOCUMENT / FOUND_API / FOUND_GIS / LEAD_ONLY / INACCESSIBLE / NOT_FOUND / NOT_RELEVANT. Confidence A–E (A = directly downloadable primary … E = unresolved lead).

### GAP A — Surveyed hydraulic geometry

| Source | Agency | Dataset | Variables | Downloadable | Primary | Provenance | Conf | Status | URL / Next action |
|---|---|---|---|---|---|---|---|---|---|
| I&FC NIQ CD-XII | I&FC GNCTD (Civil Div XII) | Hydrographical/topographical survey (DGPS+echo sounder) of Sunheripul, Kushak, Bijwasan drains | scope/deliverables clause | Yes (NIQ) — **output NOT public** | Yes | OFFICIAL | B | FOUND_OFFICIAL_DOCUMENT (tender) / LEAD_ONLY (output) | ifc.delhi.gov.in/sites/default/files/ifc/tender/niq_cdxii0810.pdf — acquired → RTI I&FC CD-XII for report |
| Award record | I&FC (via TendersInfo) | Award: Aar Pee Electrical Engineering Works, Rs 2.45 L, 12→27 Nov 2024, 5 corrigenda | award metadata | No (paywall) | No (mirror) | COMMUNITY | C | FOUND_PARTIAL | tendersinfo.net TRID 6541553 |
| NGT 06-08-2024 | NGT (Indian Kanoon) | OA 6/2012 order: bathymetric-survey direction + culvert bay counts + confluence topology + A1–A7 stretches + INA 600 m pain point | bays, flowing/clogged, lengths, volumes | Yes (HTML) — **acquired** | Yes | OFFICIAL | A | FOUND_OFFICIAL_DOCUMENT | indiankanoon.org/doc/21038964/ |
| NDMC NIT 52/EE(R-III)/2025-26 | NDMC | Desilting of RCC covered Kushak Nallah + Ring Road Nallah, Rs 12.29 Cr, closes 17-Sep-2026 | BOQ (reach-wise L×W×D expected); drawings held at EE(R-III) | Registration required | Yes | OFFICIAL | B | FOUND_OFFICIAL_DOCUMENT (extract local; BOQ INACCESSIBLE anonymously) | govtprocurement.delhi.gov.in → register → org NDMC → R-III |
| DMP 2018 Appendix VI | IIT Delhi / I&FC | Longitudinal profiles of drains in other basins (Najafgarh+Barapullah) | bed level vs chainage (expected) | Yes — **acquired** | Yes | OFFICIAL_MODEL_VALUE | B (title verified, content pending parse) | FOUND_OFFICIAL_DOCUMENT | ifc.delhi.gov.in/.../appendix_vi.pdf — parse for Kushak L-sections |
| NDMC robotic mapping tender | NDMC | CCTV/acoustic robotic survey of legacy sewers (profiling every 5 m, diameter+silt) | diameter, silt volume | No (HT report) | No | MEDIA citing OFFICIAL | C | LEAD_ONLY | hindustantimes.com (2025) — outputs post-tender |
| NDMC×IIT-K cGanga rejuvenation | NDMC | Kushak rejuvenation Rs 169.57 Cr, SP Marg→Kamal Ataturk Marg; 1×5 MLD + 2×2.5 MLD SCR; 10 MLD treated | reach definition, plant caps, flow assessment | No | No | MEDIA citing OFFICIAL | B | FOUND_PARTIAL | hindustantimes.com (2024); smartutilities.net.in |
| NDMC other works | NDMC (Delhi eProc) | Kidwai Nagar→Kushak Bus Depot silt removal; boundary wall INA metro→bus depot; Satya Sadan sump Rs 21.95 L; Teen Murti works | reach endpoints, costs | Registration | Yes | OFFICIAL | B | FOUND_PARTIAL | govtprocurement.delhi.gov.in (search) |
| NDMC budget 2021-22 | NDMC | "Kushak Nallah at Pillanji Village" + Satya Sadan line items | budget heads | Yes | Yes | OFFICIAL | B | FOUND_OFFICIAL_DOCUMENT | ndmc.gov.in Budget 2021-22 Vol-II PDF |

### GAP B — Network / connectivity

| Source | Agency | Key facts | Primary | Provenance | Conf | Status | Next action |
|---|---|---|---|---|---|---|---|
| NGT 22-11-2023 order | NGT/DJB (Indian Kanoon) | Kushak(+Mehrauli) originates Central Ridge; enters MCD area behind INA Market; Defence Colony Nallah joins; then Sunehri; "from this point called Barapulla"; GK-I 945 m (645 covered), 10 vents, 4 channels; 11 sewage entry points | Yes — **acquired** | OFFICIAL | A | FOUND_OFFICIAL_DOCUMENT | parse into network schema |
| DMP 2018 main + appendices | IIT Delhi/I&FC | Basin 376.27 km²; Chirag Delhi = longest; 4,401 conduits with adverse slopes; data-limitation statements | Yes — **acquired** | OFFICIAL | A | FOUND_OFFICIAL_DOCUMENT | PDF extraction |
| GSDL drainage portal | GSDL/GNCTD | NDMC spine ~4.927 km (prior acquisition); **no public self-registration** (verified) | No | OFFICIAL | A | INACCESSIBLE | official request/RTI |
| IITD GIS server | IIT Delhi | gisserver.civil.iitd.ac.in/delhidrainagemasterplan/ — connection timeout ×2 | No | OFFICIAL (academic) | D | INACCESSIBLE | email authors |
| Pavitra Ganga | EU-India project | Deliverables page lists D1.2, D2.x, D3.x — **D1.1 not listed**; demo stats only (drain ~100 m wide, ~16 km, 3.4 M people) | Partial | RESEARCH | C | FOUND_PARTIAL | contact consortium |
| Public SWMM models | — | No Barapullah/Delhi .inp on GitHub/Zenodo/Figshare (multi-query negative) | — | RESEARCH | D | NOT_FOUND | stop searching |
| CRSC cross-sections | GSDL | Prior negative confirmed — not revisited | — | OFFICIAL | — | NOT_RELEVANT | closed |

### GAP C — Flood ground truth

| Source | Agency | Variables | Machine-readable | Provenance | Conf | Status | Next action |
|---|---|---|---|---|---|---|---|
| **Aab Prahari API** | IIT Delhi HPM Lab | cmpldate, location, depth class, photo link, lat, lon — **731 records/106 dates acquired** | Yes (JSON, no auth) | OBSERVED (crowdsourced) | B | **FOUND_API/FOUND_RAW** | bbox-clean; enumerate images metadata; contact anrohith@iitd.ac.in |
| DTP 2021 table | Delhi Traffic Police | road, specific location, dates, frequency (~200+ rows) | Yes (archived HTML) — **acquired** | OFFICIAL (archived) | A | FOUND_OFFICIAL_DOCUMENT | parse rows; geocode |
| IFC daily reports | I&FC GNCTD | per-day vulnerable-points status, Yamuna levels, rainfall | PDF (bulk pattern) — 3 samples acquired | OFFICIAL | B | FOUND_OFFICIAL_DOCUMENT | bulk enumerate monsoon dates |
| DMP 2018 main report | IIT Delhi/I&FC | "reported (as observed) extreme water logging events" inventory + model-deduced hotspots | PDF — **acquired** | OFFICIAL | A | FOUND_OFFICIAL_DOCUMENT | extract appendix tables/maps |
| FCO 2025 | I&FC GNCTD | 169 waterlogging-prone locations, 9 underpasses | PDF — **acquired** | OFFICIAL | A | FOUND_OFFICIAL_DOCUMENT | extract + geocode |
| IFI v4 (Zenodo 16994648) | IITD HydroSense | event-scale flood inventory 1967–2023 | CSV — checked: **zero Delhi rows** | DERIVED (media-digitized) | A | NOT_RELEVANT | closed for Delhi |
| FCO 2024 | I&FC (Scribd rehost) | prior-year hotspot list | Scribd only | OFFICIAL-origin | D | LEAD_ONLY | transcribe if needed |
| Hotspot counts | PWD/DTP via press | 448 hotspots+169 underpasses (2026); 445 (2023-25); 194 (2024) | No | MEDIA citing OFFICIAL | B | LEAD_ONLY | RTI for the lists |
| NRSC 13/20-Jul-2023 map | NRSC/ISRO | riverine inundation extent (Yamuna floodplain) | image product | OFFICIAL | A | FOUND_PARTIAL (extent-only) | use as riverine check |
| Sentinel-1 GRD | ESA/Copernicus | 10 m SAR; 12/16-Jul-2023 scenes (per Esri paper); odata catalog anonymous works | Yes | OFFICIAL | B | FOUND_PARTIAL (scene IDs need bbox confirm) | Copernicus Browser bbox search |
| MCD-311 / NDMC-311 | MCD/NDMC | waterlogging complaints | No bulk export found | OFFICIAL | C | LEAD_ONLY | Open311 probe / RTI |
| DDMA | DDMA Delhi | descriptive hazard page; no monsoon archive | No | OFFICIAL | B | NOT_FOUND | RTI / Delhi Dastavez |
| Google Flood Hub | Google | riverine gauges only | Yes | DERIVED | B | NOT_RELEVANT (pluvial) | skip |

### GAP D — Historical hourly rainfall

| Source | Station(s) | Resolution | Event coverage | Provenance | Conf | Status | Next action |
|---|---|---|---|---|---|---|---|
| **NOAA NCEI ISD global-hourly** | Safdarjung 421820, IGI 421810 | 3-hourly (SYNOP AA1 cumulative) | **Both events verified** (153.0 & 228.0 mm/24 h exact) | OBSERVED | A | **FOUND_RAW — acquired** | differencing pipeline (DERIVED product) |
| ISD-Lite | Safdarjung | 3-hourly lossy subset | sparse precip only | OBSERVED | B | FOUND_PARTIAL | skip (use global-hourly) |
| IEM ASOS | VIDP/VIDD | 30-min | precip fields empty for IN | OBSERVED | B | FOUND_API (precip NOT_RELEVANT) | occurrence timing only |
| Meteostat bulk | 42182 | hourly | underestimates 5–10× | COMMUNITY/DERIVED | C | FOUND_PARTIAL (unfit) | do not use for benchmarks |
| Open-Meteo archive (ERA5) | gridded | hourly | day sums 27/48/31 mm vs 153 | DERIVED | B | FOUND_API (fallback only) | label DERIVED |
| ERA5 CDS | gridded | hourly | 5-day latency | DERIVED | B | FOUND_API | context only |
| IMD Pune DSP | Safdarjung/Lodhi/Ayanagar/Ridge | 1-min/15-min ARG (true hourly) | paid request | OFFICIAL | B | REQUIRES REQUEST (paid) | budget request for 2 events |
| IMD api.imd.gov.in | all AWS | 24-h rainfall only; hourly not guaranteed | n/a | OFFICIAL | B | REQUIRES REQUEST | register; ask field list in writing |

### GAP E — Catchment boundary evidence

| Source | Value | Context | Provenance | Conf | Status | Next action |
|---|---|---|---|---|---|---|
| PIB Lok Sabha QA PRID 1885759 (Feb 2023) | **3.5 km²** | Kushak Nala recharge works (CGWB) | OFFICIAL | A (fetched verbatim) — **acquired** | FOUND_OFFICIAL_DOCUMENT | reconcile as micro-catchment |
| CGWB 2011 report (already local extract) | 3.5 km² effective | recharge pilot | OFFICIAL | B | FOUND_OFFICIAL_DOCUMENT | consistent with PIB |
| MCD storm-drain doc (Scribd rehost) | **2.03 km² (502 acres)** for 3,220 m drain | Kushak–Barapulla system | OFFICIAL-origin, COMMUNITY host | D | LEAD_ONLY | locate primary MCD doc |
| DMP 2018 main report + DDA Appendix II | Barapullah basin **376.27 km²** | whole basin (GIS, within Delhi) | OFFICIAL_MODEL_VALUE | A — main report **acquired** | FOUND_OFFICIAL_DOCUMENT | Appendix II not acquirable (dda.gov.in refused) — verified existing |
| "35.4 km²" historical claim | **uncorroborated** | — | UNKNOWN | — | NOT_FOUND | keep model area DERIVED/PROVISIONAL |

### GAP F — Hydraulic parameters (sourced values only)

| Parameter | Value | Source | Provenance | Conf |
|---|---|---|---|---|
| Kushak culvert @ LLR Marg | 5 bays, 3 flowing, 2 clogged (2024) | NGT 06-08-2024 | OFFICIAL | A |
| Sunehripul culvert @ LLR Marg | 5 bays, 2 flowing, 3 clogged | NGT 06-08-2024 | OFFICIAL | A |
| Old Barapullah bridge | 12 arches (4 clogged) + 4 more bridges | NGT 06-08-2024 | OFFICIAL | A |
| Defence Colony drain | 1,065 m (Chetna Marg→Divya Marg), 9 vent shafts | NGT 06-08-2024 | OFFICIAL | A |
| GK-I B-block | 945 m (645 covered/300 open), 10 vents @~30 m | NGT 22-11-2023 | OFFICIAL | A |
| NDMC drain design capacity | 25 mm/hr | NDMC via ET Infra (2025) | MEDIA citing OFFICIAL | C |
| Africa Avenue pump | 241 HP pump set, monsoon round-the-clock, at sump of covered drain meeting Kushak | NDMC via TOI (2023) | MEDIA citing OFFICIAL | C |
| Satya Sadan pump house | on Kushak; sump works tender Mar 2025 Rs 21.95 L; 500 KLD STP | NDMC tenders/dept page | OFFICIAL | B |
| Desilting volumes | 10,000 m³ (I&FCD A7–B); 54,000 m³ (NGT ref); 3,150 m³ robotic pilot | NGT/press | OFFICIAL/MEDIA | B/C |
| Kushak bed slope / inverts / design Q | **UNKNOWN publicly** — expected in DMP App VI + bathymetric survey output | — | UNKNOWN | — |
| Manning n (DMP Table 4.1-3) | RCC box 0.012; circular concrete 0.013; smooth impervious 0.014; irregular open 0.025 | DMP (prior verified) | OFFICIAL_MODEL_VALUE | B |

### GAP G — Forecast/nowcast inputs (new items only)

| Source | Finding | Provenance | Conf | Status |
|---|---|---|---|---|
| ECMWF open data | free, **no registration**, CC-BY-4.0; but 0.25°/3-hourly, IFS 0–144 h, ~6 h publish lag → limited 0–3 h street-scale utility | OFFICIAL_MODEL_VALUE | A | FOUND_API (limited) |
| NOAA GFS NOMADS | anonymous grib filter verified (0.25° APCP) | OFFICIAL_MODEL_VALUE | A | FOUND_API |
| IMD api.imd.gov.in signup | self-service registration UI exists; approval flow + fees not published | OFFICIAL | B | FOUND_PARTIAL |

### GAP H — Terrain

No new source found that materially beats the already-local GLO-30 + FABDEM option; public LiDAR for Delhi remains nonexistent (verified negative, prior recon). Status unchanged.

### GAP I — Road/intersection impact

PWD 448 hotspots + 169 underpasses (2026, via The Hindu/TOI) and DTP 445 (2023-25) lists are not published as data — RTI/press-office route. Minto Bridge now has PWD water-level sensors (news; no archive). DTP live page 404 — use Wayback 2021 table (acquired). Structured closure-duration records: NOT_FOUND.

### GAP J — Validation/benchmark

DMP 2018 observed-waterlogging inventory (in acquired main report) + Aab Prahari corpus (acquired) + DTP 2021 (acquired) + IFC daily reports (pattern verified) are the validation stack. No Aab Prahari paper/GitHub/Zenodo release exists for the app data. NIDM proceedings PDF (33.7 MB) exceeds fetch tooling — contents UNKNOWN pending local parse.

---

## 3. Acquired files (this run)

All under `data/delhi/raw/` — checksums in `MANIFEST_RECON_20260911.json`:

| Category | Files |
|---|---|
| `rainfall/` | `isd_globalhourly_42182099999_{2023,2024}.csv` (Safdarjung), `isd_globalhourly_42181099999_{2023,2024}.csv` (IGI), `isd_history_full.csv`, `isd_history_delhi_stations.csv` (extract) |
| `drainage/` | `iitd_dmp_2018_main_report_v51.pdf` (4.1 MB), `appendix_{iv,v_1_1,vi,vii,viii,ix,x,xi,xii,xi_0,xiv}.pdf` (11 files, incl. 21–42 MB map volumes), `ifc_niq_cdxii0810_survey.pdf` |
| `flood_observations/` | `fco_2025_ifc_delhi.pdf` (2.7 MB), `ifc_daily_flood_report_{23092025,09072025,0107.2024}.pdf`, `dtp_waterlogging_2021_wayback_20240318.html` |
| `official_docs/` | `pib_loksabha_qa_1885759_kushak_catchment.html`, `ngt_order_20240806_oa6_2012_bathymetry.html`, `ngt_order_20231122_oa6_2012_topology.html` |
| `aab_prahari/` | `getdates.json` + 106 × `wl_YYYY-MM-DD.json` (731 records; photos not downloaded) |

Not acquired (verified existing): DDA Appendix II (`dda.gov.in` refused connection ×3). Housekeeping: stray `C:\Users\laksh\s1.json` (agent curl artifact, 147 B) inspected and removed.

---

## 4. MUST HAVE BEFORE HYDRAULIC MODEL

1. **Kushak longitudinal profile (bed level vs chainage)** — first parse DMP Appendix VI (already in hand); if absent, RTI the Nov-2024 bathymetric survey output.
2. **Reach cross-sections / box dimensions** — DMP Basin-II tables (in acquired PDFs) + NIT 52 BOQ/drawings (RTI/registration). Until then, GSDL/OSM planimetric + NGT bay counts are the only sourced geometry; B/H remain OFFICIAL_MODEL_VALUE from DMP tables, inverts DERIVED.
3. **Sub-catchment structure** — DMP Barapullah subcatchment inventory (parse acquired main report) as independent structure against the PROVISIONAL 27.66 km² D8 delineation.
4. **Yamuna boundary condition** — available (India-WRIS hourly; CWC WL 204.50 m / DL 205.33 m).

## 5. MUST HAVE BEFORE VALIDATION

1. **Observed event forcing** — ISD 3-hourly (acquired) is sufficient for 3-h event replay; true hourly for Safdarjung-class stations needs the paid IMD DSP route.
2. **Geolocated ground truth with depth** — Aab Prahari (acquired; depth CLASSES, not cm) + DTP 2021 recurrence (acquired) + DMP observed-waterlogging inventory (in acquired PDF) + FCO 2025 (acquired). Measured-cm street depths exist nowhere public — treat as permanently unavailable and validate ordinally.
3. **Event-day official status** — IFC daily reports for 2023-07-09/10 and 2024-06-28 (bulk enumeration + PDF extraction).

## 6. NICE TO HAVE

MOSDAC satellite QPE feed (signup); Sentinel-1 DIY flood extent for Jul-2023 riverine check; NDMC robotic-survey outputs (diameters, post-tender); cGanga flow assessment; NDMC 311/MCD-311 archives via RTI; PWD/DTP hotspot lists via RTI; ECMWF/GFS ensemble context; FCO-2024 Scribd transcription for multi-year recurrence.

## 7. CURRENTLY UNRESOLVED (must remain UNKNOWN — do not fabricate)

Surveyed invert levels; hydraulic clear width/depth of the underground twin-box reaches; culvert clear openings beyond NGT bay counts; colony-feeder subterranean connectivity; real-time siltation state; pump operational telemetry; an official Kushak catchment-area figure (3.5 vs 27.66 vs 35.4 km² unreconciled); any measured-cm street depth dataset; Aab Prahari moderation/QA methodology; NIDM proceedings contents; IMD API approval/fee terms.

## 8. BEST NEXT DATA ACQUISITION (top 5, ranked by importance × likelihood × impact)

1. **Parse the acquired DMP 2018 Appendix VI (+ IV, VII–XIV)** for Kushak L-sections, pump schedules and the observed-waterlogging inventory — zero external dependency, likely unlocks bed levels and official validation locations.
2. **RTI to I&FC Civil Division XII** for the Nov-2024 bathymetric/topographic survey report (Sunheripul+Kushak+Bijwasan) — the single most valuable geometry artifact that exists.
3. **Register on govtprocurement.delhi.gov.in → NDMC R-III** and pull NIT 52/EE(R-III)/2025-26 BOQ + drawing schedule (reach-wise L×W×D; .dwg inspection clause).
4. **IMD Pune DSP paid request** for hourly/15-min ARG rainfall (Safdarjung, Lodhi Road, Ayanagar, Ridge) covering 2023-07-08/09 and 2024-06-27/28.
5. **Bulk-enumerate IFC daily flood-control-room reports** (`DDMMYYYY.pdf`) for monsoons 2023–2026 and extract per-day vulnerable-point status aligned to benchmark events.

*(Operational, not validation: register on MOSDAC for INSAT-3D IMR/HEM half-hourly QPE as the real-time quantitative rainfall proxy.)*

---

*Anti-fabrication note: no missing hydraulic value was filled. Every derived/assumed item remains tagged as before; ISD 3-h buckets produced by differencing are DERIVED products of OBSERVED data; Aab Prahari records are OBSERVED/crowdsourced and must never be presented as official survey data.*
