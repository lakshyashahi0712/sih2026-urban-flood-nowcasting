# GCC Storm_Water_Drain Live GIS Forensic Audit — Chennai V3 Drainage Evidence Gate

**Scope:** live GCC ArcGIS REST service only (`Storm_Water_Drain`, layer 8). No flood model, no fused DTM, no invert-as-GCP use, no Delhi/Mumbai changes, no CAD replacement.
**Audit date:** 2026-09-19 (all retrievals UTC; timestamps and hashes below).
**Service:** `https://gisgcc.chennaicorporation.gov.in/server/rest/services/GCCDepts/GCC_COLLABORATION_LAYER/MapServer` (ArcGIS Server **currentVersion 11.5**).
**Layer:** id **8**, name **`Storm_Water_Drain`**, `esriGeometryPolyline`, capabilities `Query,Map,Data`, `maxRecordCount` **2000**, formats `JSON, geoJSON, PBF`, spatialReference **EPSG:32644** (UTM 44N; xyTolerance 0.001 m), declared **hasZ = true, hasM = true**, supports statistics/distinct/pagination/true-curve (advanced query capabilities dump: `data/chennai/drainage/raw/layer8_meta.json`).
**Citywide layer extent (EPSG:32644):** xmin 406037.4, ymin 1421973.4, xmax 427186.8, ymax 1462769.8 — consistent with the GCC area.

**Deliverables produced by this audit**
1. This report — `docs/CHENNAI_GCC_STORM_WATER_GIS_FORENSICS.md`
2. `data/chennai/drainage/gcc_storm_water_drain_adyar_inventory.csv` (620 features × 42 columns; raw API values + explicitly-labelled computed diagnostic columns)
3. `data/chennai/drainage/gcc_storm_water_drain_field_audit.csv` (28 fields: null fractions, distincts, parse rates, quantiles)
4. Optional snapshot — **produced**: `data/chennai/drainage/raw/gcc_storm_water_drain_adyar_snapshot.geojson` (2-D, provenance header embedded; see §Snapshot)
5. Raw evidence: `data/chennai/drainage/raw/` (service root, layer metadata, full-city attribute JSONL, Adyar raw JSON, manifests, SHA-256s)
6. Audit scripts (exact query parameters in code): `data/chennai/drainage/audit/gcc_swad_phase1_numeric_audit.py`, `gcc_swad_phase2_3_5_adyar_audit.py`

---

## 0. Quality gates (all met)

| Gate | Status |
|---|---|
| Exact query URL/parameters recorded | ✔ — endpoint + parameter sets quoted in §1/§2 and embedded in scripts/manifests |
| Retrieval timestamp | ✔ — attributes snapshot **2026-09-19T02:41:09Z**; Adyar snapshot **2026-09-19T02:46:13Z** (manifests) |
| Raw response hash | ✔ — city attributes JSONL **sha256 `fa399d86f9d533448b16a037040a7c662890be6ba251461c8aeaae4ad9854bed`**; Adyar bbox payload **sha256 `89d6402402b1ea2e18ec41a5cd5f2ccf7e9cd01c2401d8977dff02ea11d689fc`**; GeoJSON snapshot **sha256 `c06459e85ac92db3b737c1a7411de04eb7cdeade61a2a0b5ca41e30cc74a0df9`** |
| Original values preserved | ✔ — raw JSON/JSONL saved verbatim; inventory CSV carries API values verbatim; computed fields are separate, labelled columns |
| No silent unit conversion | ✔ — none performed; units assessed by distribution, never converted |
| No silent coordinate repair | ✔ — none; mismatches reported, nothing snapped/edited |
| No synthetic attributes | ✔ — inventory computed columns are pure diagnostics of source fields (offsets, parsed floats, delta/gradient flagged as diagnostics) |
| No DEM changes / no model changes | ✔ — untouched |

**Standing caveat:** GCC does not publish layer-level metadata (no survey date, no as-built flag, no vertical datum statement, no completeness statement). Everything below describes what the **API serves**; it does not certify survey vintage, field verification, or datum.

---

## 1. Service inventory (Phase 1)

**Method (exact requests):**
- Metadata: `GET .../MapServer/8?f=json` → `data/chennai/drainage/raw/layer8_meta.json`
- Count: `GET .../MapServer/8/query?where=1%3D1&returnCountOnly=true&f=json` → `{"count": 11531}`
- Full snapshot: `GET .../MapServer/8/query?where=1=1&outFields=*&returnGeometry=false&orderByFields=objectid&resultOffset=<0,2000,4000,...>&resultRecordCount=2000&f=json` (6 pages, all 11,531 records)

**Result: 11,531 polyline features, 28 fields.**

### 1.1 Field list and types (verbatim from metadata)

| Field | Type | Field | Type |
|---|---|---|---|
| objectid | esriFieldTypeOID | swd_mat | String |
| zone | String | drain_detl | String |
| ward | String | invert_sp | **String** |
| location | String | invert_ep | **String** |
| drain_type | String | inlet_shp | String |
| cover | String | strt_east | **String** |
| drain_len | **String** | strt_north | **String** |
| drain_wid | **String** | end_east | **String** |
| drain_dep | **String** | end_north | **String** |
| drain_size | String | obstacles | String |
| mh_shape | String | dlen_km | **Double** |
| mh_size | String | shape | Geometry |
| typ_mat | String | st_length(shape) | Double (system) |

⚠ **Every engineering attribute is a String** (only `objectid`, `dlen_km`, `shape` are numeric-typed). All numeric statements below are empirical parse results on string contents, not schema guarantees.

### 1.2 Completeness (null/empty fraction) and distinct counts — city-wide

Full table: `gcc_storm_water_drain_field_audit.csv`. Highlights:

| Field | Null/empty % | Distinct | Numeric parse rate (of non-null) |
|---|---|---|---|
| zone | 0 | 15 | — |
| ward | 0 | 198 | — |
| location | ~0 | high | — |
| drain_type | 0 | 7 | — |
| cover | 0.01 | 5 | — |
| drain_len | 0 | 11,519 | **1.000** |
| drain_wid | 0 | 869 | **0.9999** |
| drain_dep | 0 | 797 | **0.9999** |
| drain_size | 0 | 669 | n/a (composite text) |
| mh_shape | 0.03 | 16 | — |
| mh_size | 0.01 | 52 | — |
| typ_mat | 0.01 | 8 | — |
| water_flow | 0 | 5 | — |
| puca_kacha | 2.0 | 4 | — |
| status | 0 | 3 | — |
| swd_mat | 0.4 | 12 | — |
| drain_detl | (mostly empty) | — | — |
| invert_sp | 0 | 7,178 | **0.9994** |
| invert_ep | 0 | 7,037 | **0.9995** |
| inlet_shp | 0.03 | 4 | — |
| strt_east / strt_north | 0.01 | 11,111 / 11,061 | **1.000** |
| end_east / end_north | 0.01 | 11,040 / 10,995 | **1.000** |
| obstacles | 20.5 | 143 | — |
| dlen_km | 0 | 11,322 | **1.000** |

**Completeness is exceptional city-wide** (obstacles 79.5% filled is the worst; drain_detl essentially unused). The layer is a filled-in attribute table, not a skeleton.

### 1.3 Categorical distributions (city-wide, top values)

- `zone` (15): N11=1503, N12=1372, N14=1261, N07=1256, N13=949, N10=883, N09=820, N08=729, N06=571, N04=502, N05=399, N01=380, N15=308, N03=303, N02=295 — **zone codes N01–N15; no "Zone 1" naming** (GCC's published SWD-map "Zone 1" numbering is a different, map-series convention — crosswalk note in §6).
- `drain_type` (7): SWD=9383, Side Drain=2065, Open Drain=60, Side drain=19, Closed=3, Pipe Line=1 — **case variants exist** (Side Drain/Side drain; also `Closed` collides with the `cover` vocabulary).
- `cover` (5): Yes=9754, No=1719, Open=54, Closed=2, SWD=1 — mixed semantics (Yes/No vs Open/Closed vs junk value).
- `status` (3): Good=10657, Bad=871, Yes=3 — "Yes" is a corrupt value.
- `typ_mat` (8): Concrete=9594, NA=1675, concrete=124, Brick=59, Conctrete=47, Brick Wall=21, Brickwall=6, Bricks=4 — case/spelling variants.
- `swd_mat` (12): Concrete=10801, Concrete Wall=383, Concrete wall=197, Brick wall=59, Brick Wall=18, Soil=8, Brickwall=7, Paving Stones=5, Steel=4, NA=3, Open=1.
- `water_flow` (5): Yes=11320, Concrete=129, YES=42, No=37, yes=3 — "Concrete" is a corrupt value; case variants.
- `inlet_shp` (4): Rectangular=10633, Rectangle=850, Rounded=43, NA=1.
- `puca_kacha` (4): Pucca=10171, Kacha=1127, kacha=2, Puca=1 (puca/kacha = paved/unpaved locality flag).
- `obstacles` (143 distinct; 20.5% empty): NA=6664, Electrical Junction Box=753, EJB=285, Water Tank=255, Electric Pole=123, Electric Post=104, EP=103, Lamp Post=87, … — free-text, abbreviated, inconsistent.
- `ward`: 198 distinct values (city-wide, e.g. 156=209, 173=209, 182=193 …).

### 1.4 Numeric parse success and quantiles (city-wide)

| Field | Parse rate | min | median | max | Read |
|---|---|---|---|---|---|
| drain_len | 1.000 | 0.115 | 140.5 | 3,035.015 | metres (see §1.5) |
| drain_wid | 0.9999 | 0.0 | 0.88 | 1,181.1 | metres (see §4; 1,181 = corrupt) |
| drain_dep | 0.9999 | 0.0 | 0.88 | 10.6 | metres (see §4) |
| invert_sp | 0.9994 | −0.927 | 6.863 | **104,860** | metres MSL-class (see §4/§5) |
| invert_ep | 0.9995 | −0.927 | 6.281 | **80,202** | metres MSL-class |
| dlen_km | 1.000 | 0.000115 | 0.1405 | 3.035 | km (see §1.5) |
| strt_east | 1.000 | 406,148 | 414,327 | 427,146 | EPSG:32644 Easting |
| strt_north | 1.000 | 1,422,006 | 1,442,597 | 1,462,670 | EPSG:32644 Northing |
| end_east | 1.000 | 406,106 | 414,365 | 427,185 | EPSG:32644 Easting |
| end_north | 1.000 | 1,422,030 | 1,442,633 | 1,462,706 | EPSG:32644 Northing |

Unparseable residues are small and diagnostic: drain_wid/dep `"0.81."` (trailing period); invert_sp `"7..849"`, `"6.6.4520"`, `"17. 493"`, `"NA"`; i.e., **decimal-typo corruption**, not a different unit convention.

### 1.5 Units determination (evidence-based)

- **drain_len = metres, and equals the GIS geometry length.** Max 3,035.01526682 m; per-feature comparison: `drain_len` within 0.5 m of the polyline length for **616/620** Adyar features (all 620 within 20 m). `dlen_km` = `drain_len`/1000 for **11,527/11,531** city records (4 tiny mismatches at rounding level). ⇒ both are server-derived from geometry (derivative fields), not independent surveyed lengths. A handful of records (e.g., 62 where `drain_wid`==`drain_len`) show column-shift contamination.
- **strt/end east/north = EPSG:32644 coordinates in metres** — ranges match the layer extent exactly (Eastings 406–427 km ≈ Chennai; Northings 1,422–1,463 km).
- **invert_sp/invert_ep = elevation-class metres** (median ≈ 6.3–6.9; 94.95% of all values inside −1…15 m) — magnitude consistent with Chennai "MSL" practice (city land ≈ 2 m MSL average; drains deeper than grade). **Vertical datum: NOT documented anywhere in the service ⇒ UNKNOWN** (see §7).
- **drain_wid/drain_dep/drain_size = metres** (§4): 0.30–1.32 m dominates; size strings are "w x d".

---

## 2. Adyar pilot extraction (Phase 2)

**Pilot bbox (DERIVED, not official):** no Adyar pilot bbox existed in this repo (checked docs/, backend/, data/ — `data/chennai/` contained only the terrain inventory). The bbox is therefore **derived and documented** from this project's own forensics report (§11/§15 of `CHENNAI_TERRAIN_DATA_FORENSICS.md`: the lower-Adyar hotspot corridor Saidapet–Kotturpuram–Nandambakkam–Manapakkam–Jafferkhanpet):

- WGS84: **lon 80.2000–80.2750 E, lat 12.9950–13.0250 N**
- EPSG:32644 (pyproj 4326→32644, always_xy): **xmin 413242.62, ymin 1436718.99, xmax 421385.99, ymax 1440012.48**
- Query: `where=1=1&geometry={envelope}&geometryType=esriGeometryEnvelope&inSR=32644&spatialRel=esriSpatialRelIntersects&outFields=*&returnGeometry=true&outSR=32644&orderByFields=objectid&resultOffset=...&resultRecordCount=1000&f=json`

| Metric | Value |
|---|---|
| Features intersecting bbox | **620** |
| Total mapped length (geometry) | **135.611 km** |
| Total mapped length (Σ dlen_km) | 136.099 km |
| Median segment length | 160.0 m (min 0.22 m, max 3,035 m) |
| drain_type | SWD=580, Side Drain=40 |
| status | Good=594, Bad=26 |
| cover | Yes=563, Open=51, No=4, Closed=2 |
| typ_mat | Concrete=467, concrete=103, NA=37, Brick Wall=9, Brickwall=4 |
| zones | **N13=454, N12=124, N10=25, N09=17** |
| wards (top) | 173=151, 160=74, 170=58, 174=55, 168=53, 171=52, 161=49, 169=46, 172=22, 142=19, 179=10 … |
| width available / >0 | 100% / 99.84% |
| depth available / >0 | 100% / 99.84% |
| size available | 100% |
| start invert available | 100% |
| end invert available | 100% |
| inlet shape available | 100% |
| obstacles filled | 82.9% |
| water_flow / status | 100% / 100% |

Raw payload + manifest: `data/chennai/drainage/raw/layer8_adyar_bbox_features.json` (sha256 `89d6402…`), `layer8_adyar_snapshot_manifest.json` (timestamp, bbox, provenance note). Per-feature inventory: `gcc_storm_water_drain_adyar_inventory.csv`.

---

## 3. Geometric consistency (Phase 3)

Compared, in EPSG:32644, for all 620 features: geometry first vertex vs (`strt_east`,`strt_north`); geometry last vertex vs (`end_east`,`end_north`). 1,240 endpoint comparisons; **0 missing** (all 620 have geometry paths AND all four coordinate attributes).

| Statistic | Value |
|---|---|
| offset ≤ 1 m | **86.53%** |
| offset ≤ 5 m | 93.31% |
| offset ≤ 20 m | 94.35% |
| median offset | **0.00 m** |
| max offset | 692.6 m |

Interpretation: the coordinate attributes are the **delineator-digitized endpoints of the same geometry** (majority identical to centimetres), not independently surveyed end points. The ~5.7% of endpoints >20 m are digitization drift, not survey discrepancy.

Worst cases (max offset, objectid, zone, ward, location, drain_len): 692.6 m / 5273 / N13 / 169 / "Saidapet, Chennai" / 694.0 m; 680.8 m / 5229 / N13 / 168 / "Guindy" / 815.2 m; 606.3 m / 5658 / N13 / 173 / "Adayar OT" / 103.6 m; 495.0 m / 5670 / 17.3 m; 465.1 m / 5674 / 9.1 m; 416.3 m / 5567 / 628.0 m. Note the pattern: several short segments (9–17 m attribute length) with ~400–600 m offsets ⇒ **attribute endpoint sets that do not correspond to the drawn segment at all**.

- Zero-length segments: geometry min 0.22 m (near-zero slivers exist); attribute start==end coordinate pairs with plausible UTM values: **1**.
- Duplicate segments (identical rounded start/end keys): **0**.
- Overlap detection: not computed (would require topology build) — flagged NOT_DONE; nothing snapped or merged.
- **HasZ/HasM:** declared true in metadata; **the served JSON geometry contains 2-tuples only** (checked all 620 features: every path point has exactly 2 coordinates). ⇒ **No elevations are exposed via geometry JSON.** If Z exists in the enterprise geodatabase, it is not reachable through this endpoint in JSON/GeoJSON form. (PBF untested — listed as a follow-up.)

---

## 4. Hydraulic attribute forensics (Phase 4)

### drain_wid
- Semantics: **cross-sectional width of the drain (m)**. Evidence: dominated by 0.30–1.32 m values; `drain_size` strings are "w x d" with w == wid (e.g., "0.75 x 0.75", "1.25 x 1.25"); wid == dep for **98.0%** of records (11,301/11,530) — Chennai SWD drains are typically square-box sections (GCC SWD page: standard drain 600×750 mm and upward).
- Unit confidence: **HIGH (metres)**. Parse rate 0.9999.
- Range: min 0.0 (7 records), median 0.88 m, p99 ≈ 3 m class, max **1,181.1 m = corrupt** (column-shift or keying error; city-wide, a handful >9 m: Koyambedu "7.00 x 7.00", Vadapalani "9.00 x 9.00" — large trunk channels exist but 1,181 m is impossible).
- Usable for hydraulics: **CONDITIONAL — after size-consistency filter (wid/dep/size mutual agreement, wid<10 m) and case-normalisation**. Zero-width records (7 city-wide) excluded.

### drain_dep
- Semantics: **depth of the drain section (m)** (same square-box convention).
- Evidence: distribution ≈ wid; equality with wid 98%; plausible 0.3–10.6 m.
- Unit confidence: **HIGH**. Parse 0.9999. Max 10.6 m plausible for trunk/deep sections.
- Usable: **CONDITIONAL (same filter)**.

### drain_size
- Semantics: **text "w x d" box size in metres** (669 distinct). Formats: predominantly "0.75 x 0.75"-style; 461 values don't match the pure `a x b` pattern (variants, NA, single numbers); 208 matched strict numeric pattern in the strict-regex count (the remainder are valid but spaced/annotated differently — see field-audit top values).
- Unit confidence: **HIGH** (metres, two axes).
- Usable: **CONDITIONAL — parse "w x d" with tolerant regex; reconcile against wid/dep**.

### invert_sp / invert_ep
- Semantics: **invert elevation at start/end of segment, elevation-class metres.** Evidence: 94.95% of all values in −1…15 m; medians 6.86/6.28 m; downstream-reach values approach sea level (−0.927 min); deltas over segment lengths produce realistic gradients (median 0.31%, §5).
- Unit confidence: **HIGH (metres)**. Parse rate 0.9994/0.9995.
- **Vertical datum: UNKNOWN.** Values are consistent with GCC/WRD "MSL" practice, but no service metadata states the datum, epoch, or benchmark connection. Treated as "MSL-class metres, datum undocumented" — **not usable as terrain GCPs regardless** (these are inverts).
- Corruption: **5 features with values >1,000 m** (objectids 5793, 10214, 10226, 10390, 10755 — max 104,860 m: decimal-shifted), **3 slightly negative** (5242, 7216, 7217 — −0.927 m is plausible near the outfall; flagged not condemned), 1 literal "NA", ~12 decimal-typo strings ("7..849", "6.6.4520", "17. 493").
- Usable: **YES for drainage-network hydraulics (bed datum) after exclusion list (|value|>15 m, literal NA, unparseable) — and ONLY as network inverts, never terrain.**

### location
- Free-text locality ("Adayar OT,Chennai", "Guindy, Chennai", "Koyambedu, Chennai") — useful for crosswalks, no semantics for hydraulics.

---

## 5. Invert logic (Phase 5) — diagnostic only

`delta_invert = invert_sp − invert_ep`; `gradient = delta_invert / geometry_length` (geometry length; fallback not needed — all features have paths). **No flow direction was reversed; no source data modified; these are diagnostics.**

| Class (Adyar 620) | Count |
|---|---|
| downhill (sp > ep) | **599 (96.6%)** |
| uphill (sp < ep) | 17 (2.7%) |
| zero-slope | 0 |
| extreme \|gradient\| > 0.5 | 3 |
| missing/unparseable both-present | 1 |

Gradient stats: **median 0.00313 (0.31%)**, p95 |grad| 0.0466 (4.7%).

Extreme-slope features (all plausibly short-segment digitization artifacts): objectid 4458 (Alandur; sp 10.382 → ep 7.088 over 0.3 m), 5254 (Guindy; 2.185 → 1.135 over 1.1 m), 5617 (Adayar OT; 4.825 → 4.625 over 0.2 m).

Interpretation: the invert pair is **internally coherent for 96.6% of the pilot network** (downhill toward the river/sea, realistic gradients). 17 uphill segments are either genuine siphon/flat-storage behaviour, endpoint order slips, or digitization direction errors — unresolved, flagged, untouched.

---

## 6. CAD crosswalk (Phase 6) — NOT EXECUTABLE IN THIS WORKSPACE

The referenced Zone-1 CAD extraction **does not exist in this repository** (searched: no DWG/DXF/SWD files anywhere under data/ or docs/; `data/chennai/` contained only `terrain/terrain_inventory.csv` before this audit). Additionally, GCC's live `zone` vocabulary is **N01–N15**, which does not correspond numerically to the map-series "Zone 1..15" naming of the published GCC SWD PDF/DWG sets (different numbering conventions; e.g., live zone **N13** dominates the Adyar corridor, whereas map-series Zone 13 is Thiru-Vi-Ka Nagar in north Chennai).

**Documented, not performed:** matched %, unmatched GIS/CAD lists, attribute agreement, temporal versioning. Forcing a crosswalk without the CAD would be fabrication.

**Pre-registered crosswalk method (for when the CAD is available):** convert DWG→DXF (ODAFileConverter); extract polyline + text layers; match by (a) 32644 proximity of segment endpoints (≤5 m both ends), (b) length agreement (±5%), (c) drain-type/size agreement, (d) invert value agreement where CAD pairs exist. Report matched GIS%, matched CAD%, attribute deltas, and version hypotheses (e.g., GIS post-2021 digitization vs older DPR-era CAD). **Do not force matches.**

---

## 7. Provenance classification (Phase 7)

| Attribute | Content class | Access class |
|---|---|---|
| objectid, shape, st_length(shape), dlen_km, drain_len | OBSERVED/OFFICIAL (server-served; dlen/len are DERIVED by GCC from geometry — derivative noted) | PUBLIC-API |
| zone, ward, location, drain_type, cover, typ_mat, swd_mat, puca_kacha, water_flow, status, mh_shape, mh_size, inlet_shp, obstacles | OBSERVED/OFFICIAL **as served** (unverified as-built; free-text; case-corrupt variants present) | PUBLIC-API |
| drain_wid, drain_dep, drain_size | OBSERVED/OFFICIAL as served; **engineering semantics CONFIRMED by internal consistency; survey provenance UNKNOWN** | PUBLIC-API |
| invert_sp, invert_ep | OBSERVED/OFFICIAL as served; **vertical datum UNKNOWN**; corruption tail documented | PUBLIC-API |
| geometry Z/M | Declared (HasZ/HasM true) but **NOT SERVED** in JSON → content UNKNOWN | PUBLIC-API (2-D only) |
| Survey date / as-built status / field-verification / completeness / datum | **UNKNOWN — not published by GCC** | UNKNOWN |

The service is an **official GCC endpoint** (chennaicorporation.gov.in subdomain) with no stated license; treat as government-work-inferred, request-based clarification for reuse beyond research.

**GeoJSON snapshot legality/propriety:** it is a verbatim extract of a publicly served government layer for research documentation, with provenance embedded and no modifications — retained in `raw/` (do not redistribute as an official product).

---

## 8. Adyar hydraulic value (Phase 8)

Coverage matrix (Adyar bbox, 620 features):

| Attribute | Coverage % | Classification |
|---|---|---|
| drain geometry | 100% (0 missing paths) | **READY_FOR_RECONCILIATION** |
| length (drain_len/dlen_km) | 100% (parse 1.000; == geometry length) | **READY_FOR_RECONCILIATION** (as geometry-derived length) |
| width | 100% (99.84% >0) | **CONDITIONAL** (corruption filter; wid/dep/size reconciliation) |
| depth | 100% (99.84% >0) | **CONDITIONAL** (same) |
| size | 100% | **CONDITIONAL** (text parse; reconcile) |
| start invert | 100% (99.84% parse-class) | **CONDITIONAL** (datum UNKNOWN; corruption filter; network-only use) |
| end invert | 100% | **CONDITIONAL** (same) |
| inlet shape | 100% | **READY_FOR_RECONCILIATION** (after Rect/Rectangle merge) |
| material | 99.99% (case variants) | **READY_FOR_RECONCILIATION** (after normalisation) |
| water flow | 100% (129 "Concrete" corrupt) | **CONDITIONAL** |
| status | 100% ("Yes"×3 corrupt) | **READY_FOR_RECONCILIATION** (Good/Bad after cleaning) |
| obstacles | 82.9% filled, free-text | **CONDITIONAL** (annotation only; not hydraulic) |
| cover (open/closed) | 100% (mixed vocab) | **CONDITIONAL** (Yes/No ≡ Closed/Open mapping must be confirmed) |
| Z elevations from geometry | **0% (not served)** | **NOT_USABLE** (via this API) |

**What can enter Chennai V3 (no ingestion performed yet):** drain alignment geometry (EPSG:32644), lengths, and — after the documented filters — a cleaned attributes table (type, material, cover, status, size/width/depth, inverts as **network bed datum only**). This is a drainage-network layer, **not terrain**; inverts remain excluded from any DTM/GCP role (per standing rules).

**What remains conditional:** width/depth/size semantic uniformity (98% square-box hypothesis must be verified against a GCC drawing or spec before hydraulic use); invert datum (needs one benchmark tie or GCC confirmation); corrupt-value exclusion list; cover-vocabulary mapping.

**What remains unknown:** survey vintage (any date between digitization era and now), as-built vs design status, field-verification, completeness vs the real network, Z availability (PBF test), and the vertical datum name/epoch.

---

## Final report (A–J)

**A. Current GCC API status:** LIVE and robust — ArcGIS Server 11.5, anonymous query access, pagination/statistics supported, 11,531 features served city-wide; attributes ~100% populated; engineering values carried as **strings** (with a small corrupt tail); **served geometry is 2-D despite declared HasZ/HasM**.

**B. Adyar feature count and mapped length:** **620 features, 135.6 km** (geometry sum; 136.1 km by attribute sum) inside the derived pilot bbox; zones N13/N12/N10/N09; wards led by 173/160/170/174/168/171.

**C. Attribute completeness:** effectively full for geometry/length/size/inverts/material/status (≈100%); obstacles 82.9%; the only structurally empty field is `drain_detl`.

**D. Hydraulic-field semantic confidence:** width/depth/size — **high** (square-box metres, mutually consistent 98%); invert pair — **high as network bed elevations in metres**, datum **unknown**; none of these should be treated as verified as-built dimensions without GCC confirmation.

**E. Invert consistency:** 599 downhill / 17 uphill / 3 extreme-gradient (short segments) / 0 zero-slope / 1 unparseable; median gradient 0.31% — physically coherent network behaviour.

**F. CAD crosswalk:** **not executed** — the Zone-1 CAD is absent from this workspace, and GCC's live `zone` codes (N01–N15) are a different namespace from the CAD map-series zone numbering. Method pre-registered (§6); do not merge datasets on assumed equivalence.

**G. What can enter Chennai V3:** this layer as the **stormwater network backbone** (geometry + cleaned attributes + network inverts), clearly separated from terrain work.

**H. What remains conditional:** width/depth/size reconciliation; invert datum; corrupt-value filters; open/covered vocabulary; obstacles semantics.

**I. What remains unknown:** survey date/vintage, as-built vs design, field verification, completeness, Z-in-geometry (PBF), vertical datum name/epoch.

**J. Recommended next acquisition step:** (1) test PBF query for Z exposure (single request, no auth); (2) email GCC (SWD dept / GIS cell, via the evidence chain in `CHENNAI_TERRAIN_DATA_FORENSICS.md` §17) asking for: layer survey date & update cadence, vertical datum statement for invert fields, and whether Z is populated in the source SDE; (3) obtain the GCC CAD/SWD map legend to fix the zone-namespace crosswalk; (4) only then run the pre-registered CAD crosswalk and (separately, later) a cleaned V3 ingestion — no ingestion before the datum question is answered.
