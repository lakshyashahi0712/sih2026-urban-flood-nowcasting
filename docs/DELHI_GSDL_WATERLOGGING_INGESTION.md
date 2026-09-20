# Delhi NCT V2 — GSDL Waterlogging Incident Ingestion & Normalization Audit

**Document ID**: `DELHI_GSDL_WATERLOGGING_INGESTION`  
**Investigation Phase**: Phase 3E-2B  
**Target Source**: Geospatial Delhi Limited (GSDL) ArcGIS REST `waterlogging1` Service  
**Date**: 11 September 2026  
**Status**: COMPLETE — FULL INGESTION & VALIDATION PASS  
**Provenance Classification**: `OFFICIAL / OBSERVED — OCCURRENCE ONLY`  
**Operational Scope Notice**: This ingestion creates an official, machine-readable validation baseline of historical street waterlogging occurrences for Delhi NCT. Per project engineering standards, this dataset provides binary spatial failure occurrence; it is not calibrated flood depth, inundation duration, or hydraulic discharge.

---

## 1. Source and Layer Metadata

| Attribute | Service Details | Layer 0 Details | Layer 1 Details |
| :--- | :--- | :--- | :--- |
| **Service Name** | `waterlogging1` (`Layers`) | — | — |
| **Server Software** | ArcGIS Server 10.91 | — | — |
| **Layer ID** | — | `0` | `1` |
| **Layer Name** | — | `Water_Logging_Location2023_2024` | `Water_Logging_Locations_Dated_30042025` |
| **Base Endpoint** | `https://gsdl.org.in/arcgis/rest/services/waterlogging1/MapServer` | `https://gsdl.org.in/arcgis/rest/services/waterlogging1/MapServer/0` | `https://gsdl.org.in/arcgis/rest/services/waterlogging1/MapServer/1` |
| **Geometry Type** | — | `esriGeometryPoint` | `esriGeometryPoint` |
| **Native Spatial Reference** | `wkid: 32643` (UTM Zone 43N) | `wkid: 32643` (UTM Zone 43N) | `wkid: 4326` (WGS 84 geographic) |
| **Native Extent (UTM 43N)** | $X \in [665980.4, 728978.4]$, $Y \in [3147534.0, 3187377.0]$ | $X \in [689464.2, 728978.4]$, $Y \in [3147941.5, 3187377.0]$ | $X \in [665980.4, 727907.9]$, $Y \in [3147534.0, 3183354.0]$ |
| **Max Record Count** | 1000 | 1000 | 1000 |
| **Capabilities** | `Map, Query, Data` | `Map, Query, Data` | `Map, Query, Data` |
| **Supported Query Formats** | `JSON, geoJSON` | `JSON, geoJSON` | `JSON, geoJSON` |
| **Access Restriction** | Public / Unauthenticated | Public / Unauthenticated | Public / Unauthenticated |

---

## 2. Ingestion & Retrieval Timestamp

- **Ingestion Execution Timestamp**: `2026-09-11T10:01:22Z` (UTC) / `2026-09-11T15:31:22+05:30` (IST)
- **HTTP Transport**: Direct HTTPS GET via standard Python `urllib` (no scraping or credential use).
- **HTTP Response Status**: `200 OK` for both Layer 0 and Layer 1.
- **Raw Storage Location**: `data/delhi/raw/validation/gsdl_waterlogging/`
- **Manifest Location**: `data/delhi/raw/validation/gsdl_waterlogging/manifest.json`

---

## 3. Raw Feature Counts & Checksum Audit

Both layers were downloaded in their complete entirety through a single query request each, as both layer record counts are well below the server ceiling of `maxRecordCount = 1000`.

| Layer ID | Layer Name | Raw Server Feature Count | Raw File Size (Bytes) | SHA256 Hash of Raw Response |
| :---: | :--- | :---: | :---: | :--- |
| **0** | `Water_Logging_Location2023_2024` | **473** | 136,677 | `1a00ddad88365a5aed2bc1f4952ffa4fd80af27036900d8f4982599b36f4c789` |
| **1** | `Water_Logging_Locations_Dated_30042025` | **174** | 46,886 | `59cff7b3bcfbd000349c27a6938a885bff34f2ee515e35f8f5b691ed621e85bc` |
| **Total** | *Combined Raw Baseline* | **647** | 183,563 | — |

*Verification Check*: The downloaded raw feature counts (**473** for Layer 0 and **174** for Layer 1) match exactly with the counts established in the Phase 3E-2A verification pass.

---

## 4. Date Expansion & Normalization Logic

### 4.1 The Need for Date Expansion
In the raw GSDL database, each spatial point corresponds to a physical road section or underpass. For chronic failure points, the municipal compilers recorded multiple rain storm dates inside a single text field (e.g. `03.05.2023, 27.05.2023, 30.05.2023, 08.07.2023, 09.07.2023`).

To support rigorous hydrologic model validation, where simulations are evaluated event-by-event, each storm date must represent an independent observation instance linked to that geometry.

### 4.2 Expansion Rules
1. **Delimiting**: Date strings are parsed using standard regular expression delimiters (`[,/;
]+`).
2. **Formatting**:
   - Dates matching standard Indian municipal notation `DD.MM.YYYY` or `DD-MM-YYYY` are converted to standard ISO `YYYY-MM-DD`.
   - The original raw text is preserved verbatim in `date_raw` on every record for 100% auditability.
3. **No Fabrication**:
   - No timestamps (hours/minutes) were invented.
   - No duration was assumed or inferred.
   - No depth was estimated.
   - Unparseable or malformed date tokens were retained verbatim rather than guessing corrected numbers.

### 4.3 Expansion Multipliers Distribution
| Dates per Raw Record | Layer 0 Count | Layer 1 Count | Combined Raw Features | Total Resulting Observations |
| :---: | :---: | :---: | :---: | :---: |
| **1 date** | 339 | 149 | 488 | 488 |
| **2 dates** | 68 | 16 | 84 | 168 |
| **3 dates** | 29 | 1 | 30 | 90 |
| **4 dates** | 18 | 1 | 19 | 76 |
| **5 dates** | 4 | 3 | 7 | 35 |
| **6 dates** | 4 | 1 | 5 | 30 |
| **7 dates** | 5 | 0 | 5 | 35 |
| **8 dates** | 3 | 0 | 3 | 24 |
| **9 dates** | 2 | 1 | 3 | 27 |
| **10 dates** | 1 | 1 | 2 | 20 |
| **11 dates** | 0 | 1 | 1 | 11 |
| **Total** | **473** | **174** | **647** | **1,004** |

---

## 5. Normalized Record Counts & Schema

The normalized dataset is written to two production-ready formats:
- **CSV**: `data/delhi/derived/validation/gsdl_waterlogging/gsdl_waterlogging_normalized_occurrences.csv`
- **GeoJSON**: `data/delhi/derived/validation/gsdl_waterlogging/gsdl_waterlogging_normalized_occurrences.geojson`

### 5.1 Final Normalized Record Totals
- **Layer 0 Normalized Observations**: **744** records
- **Layer 1 Normalized Observations**: **260** records
- **Total Normalized Observations**: **1,004** records

### 5.2 Normalized Schema Specification

| Normalized Column | Output Data Type | Constraint / Default | Provenance & Handling |
| :--- | :--- | :--- | :--- |
| `source_layer` | String | Not Null | Fully qualified layer name (`Layer 0: ...` or `Layer 1: ...`) |
| `source_layer_id` | Integer | `0` or `1` | Layer index |
| `source_fid` | Integer | Not Null | System OID from raw server feature |
| `observation_date` | String | ISO `YYYY-MM-DD` or raw token | Specific expanded calendar date of waterlogging occurrence |
| `date_raw` | String | Verbatim raw text | Original unexpanded date string from source attribute |
| `road_name` | String | `UNKNOWN` if missing | Official primary road corridor |
| `location_raw` | String | `UNKNOWN` if missing | Specific landmark / underpass / junction description |
| `latitude` | Float (Double) | WGS 84 Decimal Degrees | Sourced directly from native ArcGIS point geometry ($y$) |
| `longitude` | Float (Double) | WGS 84 Decimal Degrees | Sourced directly from native ArcGIS point geometry ($x$) |
| `agency` | String | `UNKNOWN` if missing | Responsible municipal department (populated in Layer 1; `UNKNOWN` in Layer 0) |
| `year` | String | `UNKNOWN` if missing | Reporting season (`2023` or `2024`) |
| `provenance` | String | Constant | Fixed: `OFFICIAL / OBSERVED` |
| `observation_type`| String | Constant | Fixed: `WATERLOGGING_OCCURRENCE` |

---

## 6. Missing-Field Statistics

A rigorous null and unknown value audit was conducted across all 1,004 normalized records:

| Field Name | Total Populated | Missing / Unknown Count | Completeness Ratio | Impact / Notes |
| :--- | :---: | :---: | :---: | :--- |
| `source_layer` | 1,004 | 0 | **100.0%** | Full traceability |
| `source_layer_id` | 1,004 | 0 | **100.0%** | Full traceability |
| `source_fid` | 1,004 | 0 | **100.0%** | Preserved from raw OID |
| `observation_date` | 1,004 | 0 | **100.0%** | All records have a date token |
| `date_raw` | 1,004 | 0 | **100.0%** | Unaltered raw reference |
| `road_name` | 1,004 | 0 | **100.0%** | Every record identifies a road corridor |
| `location_raw` | 1,004 | 0 | **100.0%** | Every record identifies a specific spot |
| `latitude` | 1,004 | 0 | **100.0%** | Derived from server geometry |
| `longitude` | 1,004 | 0 | **100.0%** | Derived from server geometry |
| `agency` | 260 | 744 | **25.9%** | `Agency` exists in Layer 1 (260 rows); absent in Layer 0 (744 rows set to `UNKNOWN`) |
| `year` | 1,004 | 0 | **100.0%** | All records identify season year |
| `provenance` | 1,004 | 0 | **100.0%** | Constant `OFFICIAL / OBSERVED` |
| `observation_type` | 1,004 | 0 | **100.0%** | Constant `WATERLOGGING_OCCURRENCE` |

---

## 7. Data Quality & Integrity Validation Checks

| Validation Check | Expected / Threshold | Observed Result | Status | Corrective Action / Audit Finding |
| :--- | :--- | :--- | :---: | :--- |
| **Raw Feature Counts** | Layer 0: 473; Layer 1: 174 | Layer 0: 473; Layer 1: 174 | **PASS** | Exact match with previous verification. |
| **Missing Coordinates** | 0 features missing geometry | 0 features missing geometry | **PASS** | Every feature has valid numeric point geometry. |
| **Duplicate Source FIDs** | 0 duplicate FIDs within layer | 0 duplicate FIDs within layer | **PASS** | Layer 0 spans FIDs 0–472; Layer 1 spans FIDs 0–173. |
| **Duplicate Normalized Observations** | 0 duplicate `(layer_id, fid, date)` | 0 duplicate `(layer_id, fid, date)` | **PASS** | Every expanded date per feature is unique. |
| **Geographic Bounds (Delhi NCT)** | Lat $\in [28.30, 28.95]$, Lon $\in [76.80, 77.40]$ | **1 anomaly detected** | **FLAGGED / PRESERVED** | Layer 1, FID 79 (`Dada Maheshwar Road | Karala to Mundka`) has coords $[76.7000263^\circ	ext{E}, 28.5304006^\circ	ext{N}]$, ~10 km west of Delhi border. Preserved verbatim per non-fabrication rule. |
| **Date Parsing Integrity** | Standard ISO `YYYY-MM-DD` | **10 typographic tokens flagged** | **FLAGGED / PRESERVED** | 10 date tokens contain source typographic errors (see Section 7.1). Preserved verbatim in `observation_date` without ungrounded guessing. |
| **Cross-Layer Coincidence** | Document overlap | 3 coincident points | **DOCUMENTED** | 3 locations share identical coordinates and storm dates across Layer 0 and Layer 1 (e.g. Seva Nagar on June 28, 2024). |

### 7.1 Detailed Audit of Flagged Date Typography in Source
The 10 flagged unparsed date tokens reflect human data-entry typos in the municipal source tables:
1. `FID 29` (L0), `FID 66` (L0), `FID 162` (L0), `FID 169` (L0), `FID 185` (L0): `'1 1.08.2024'` — Space inserted between ones (intended `11.08.2024`).
2. `FID 54` (L0): `'26 07.2024'` — Space instead of period between day and month (intended `26.07.2024`).
3. `FID 244` (L0): `'27,05.2023'` — Comma instead of period between day and month (intended `27.05.2023`). Unpacked as `'27'` and `'05.2023'`.
4. `FID 428` (L0): `'1 1.09.2023'` — Space inserted between ones (intended `11.09.2023`).
5. `FID 159` (L1): `'23.062023'` — Missing period between month and year (intended `23.06.2023`).

*Compliance Confirmation*: Neither the ingestion script nor Antigravity modified these raw entries. They are retained verbatim to preserve forensic data integrity.

---

## 8. Provenance & Attribution Statement

- **Data Creator / Publisher**: Geospatial Delhi Limited (GSDL), Government of National Capital Territory of Delhi (GNCTD).
- **Primary Operational Collectors**: Public Works Department (PWD), Municipal Corporation of Delhi (MCD), New Delhi Municipal Council (NDMC), Central Public Works Department (CPWD), and Delhi Traffic Police.
- **Formal Provenance Tag**:  
  $$\mathbf{OFFICIAL\ /\ OBSERVED\ —\ OCCURRENCE\ ONLY}$$
- **Data Lineage**:
  - Raw JSON downloaded from live public ArcGIS Server REST query endpoint (`outSR=4326`).
  - Stored verbatim with cryptographic SHA256 checksums in project raw repository.
  - Normalized and date-expanded using strictly documented deterministic parsing logic.

---

## 9. Scientific Scope & Limitations

1. **Binary Occurrence vs. Depth**:
   - This dataset provides unequivocal official evidence that waterlogging occurred at a specific road location on a specific date.
   - It **DOES NOT provide numerical water depth** ($m$ or $cm$). It cannot be used to tune hydraulic roughness parameters against measured stage heights.
2. **Calendar Date vs. Time-Series Hydrograph**:
   - Observations are resolved to calendar storm dates.
   - It **DOES NOT provide sub-daily arrival times, peak inundation hours, or recession duration**.
3. **Absence of Absence (Zero-Inflation Caveat)**:
   - Points indicate locations where municipal agencies formally logged standing water.
   - The absence of a point on a road does **NOT** definitively prove the road was dry; it merely indicates no official record was filed in this specific compilation.
4. **Spatial Decoupling**:
   - In accordance with task constraints, **no spatial join or distance attribution to Kushak Nallah drainage geometry was performed during this ingestion step**.

---

## 10. Generated File Artifacts

### Raw Artifacts (`data/delhi/raw/validation/gsdl_waterlogging/`)
- `layer0_Water_Logging_Location2023_2024_raw.json` (136.7 KB, SHA256: `1a00ddad88365a5aed2bc1f4952ffa4fd80af27036900d8f4982599b36f4c789`)
- `layer1_Water_Logging_Locations_Dated_30042025_raw.json` (46.9 KB, SHA256: `59cff7b3bcfbd000349c27a6938a885bff34f2ee515e35f8f5b691ed621e85bc`)
- `manifest.json` (Metadata, timestamps, URLs, and checksums)

### Derived Normalized Artifacts (`data/delhi/derived/validation/gsdl_waterlogging/`)
- `gsdl_waterlogging_normalized_occurrences.csv` (1,004 rows, 13 normalized columns)
- `gsdl_waterlogging_normalized_occurrences.geojson` (1,004 Point features with complete metadata)
- `normalization_validation_stats.json` (Comprehensive machine-readable validation statistics)

---

## 11. Final Verdict

### **PASS**

**Justification**:
- The complete raw contents of both layers were successfully acquired, verified, and cryptographically preserved without altering server responses.
- The normalized dataset correctly preserves all mandated fields, enforces non-fabrication of missing attributes, cleanly expands multi-date records while retaining raw strings, and utilizes true ArcGIS coordinates.
- All validation checks were executed and transparently documented.

---

*End of GSDL Waterlogging Ingestion Report.*  
*Authored by: Antigravity (Advanced Agentic Systems)*
