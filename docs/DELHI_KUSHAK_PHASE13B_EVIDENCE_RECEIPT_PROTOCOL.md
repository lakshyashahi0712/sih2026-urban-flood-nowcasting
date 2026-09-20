# Phase 13B — Scientific Evidence Receipt Protocol & Tier-A Acceptance Rules

**Document ID:** `DELHI_KUSHAK_PHASE13B_EVIDENCE_RECEIPT_PROTOCOL`  
**Date:** 2026-09-16  
**Status:** ACTIVE PROTOCOL (Standard Operating Procedure for Physical Survey Ingestion)  
**Scope:** Custodial intake, cryptographic verification, metadata extraction, structural parsing, provenance evaluation, and numerical readiness gating for Kushak Nallah hydraulic geometry.

---

## 1. PURPOSE & APPLICABILITY

This protocol governs the intake and validation of any incoming engineering survey deliverables, court filings, RTI disclosures, or institutional records relating to Kushak Nallah and the Barapullah basin.

**Core Principle:** No incoming record shall be integrated into the numerical hydraulic solver or used to upgrade Tier-A readiness without passing every verification gate defined herein.

---

## 2. EVIDENCE INTAKE MANIFEST SCHEMA

Every received artifact must be registered in the project manifest (`data/delhi/evidence_manifest.json`) with the following immutable metadata fields:

| Field Name | Type | Description | Mandatory? |
| :--- | :--- | :--- | :--- |
| `evidence_id` | String | Unique slug (e.g., `EVID_IFC_CDXII_2025_SURVEY_REPORT`) | YES |
| `source_organization` | String | Issuing department (e.g., `I&FCD_CDXII`, `NDMC_R3`, `NGT_PB`) | YES |
| `custodian_office` | String | Specific office/division providing the record | YES |
| `procurement_ref` | String | NIQ / NIT / Tender ID / Court Case number | YES |
| `document_title` | String | Exact title appearing on the face of the document | YES |
| `document_date` | String | Date of issuance (ISO 8601: `YYYY-MM-DD`) | YES |
| `document_number` | String | Official memo, dispatch, or drawing number | YES |
| `received_date` | String | Date of physical/electronic intake | YES |
| `intake_channel` | String | `RTI_DISCLOSURE`, `COURT_FILING`, `OFFICIAL_PORTAL`, `INSTITUTIONAL_TRANSFER` | YES |
| `original_filename` | String | Filename as received from source | YES |
| `file_format` | String | `PDF`, `DWG`, `DXF`, `CSV`, `XYZ`, `LAS`, `SHP`, `TIFF` | YES |
| `byte_size` | Integer | Exact file size in bytes | YES |
| `sha256_hash` | String | 64-character lowercase SHA-256 cryptographic checksum | YES |
| `geographic_scope` | String | Reach boundaries (e.g., `SP_MARG_TO_LODHI_COLONY`, `INA_TO_LLRM`) | YES |
| `survey_date` | String | Date of field measurement / instrument deployment | YES |
| `survey_method` | String | `DGPS`, `ECHO_SOUNDER`, `TOTAL_STATION`, `ROBOTIC_SONAR`, `TAPE_MEASURE` | YES |
| `horizontal_crs` | String | Coordinate system (e.g., `EPSG:32643`, `EPSG:4326`, `LOCAL_GRID`) | YES |
| `vertical_datum` | String | Vertical reference (e.g., `MSL_SURVEY_OF_INDIA`, `LOCAL_BM`, `UNKNOWN`) | YES |
| `benchmark_ref` | String | Description, location, and RL of tie-in benchmark | YES |
| `provenance_status` | String | `OBSERVED/OFFICIAL`, `DERIVED`, `ASSUMED`, `UNKNOWN` | YES |
| `lifecycle_state` | String | Active lifecycle state (see Section 3) | YES |

---

## 3. STRICT LIFECYCLE PROGRESSION

Every incoming artifact transitions through a linear, non-skippable lifecycle:

```
[ NOT_ACQUIRED ]
       │
       ▼
[ RECEIVED ] ─────────────────────────► [ REJECTED ] (Tampered / Unreadable)
       │
       ▼
[ CHECKSUM_VERIFIED ]
       │
       ▼
[ PROVENANCE_VERIFIED ] ──────────────► [ BLOCKED ] (Unverifiable Origin / Seal)
       │
       ▼
[ STRUCTURALLY_PARSED ]
       │
       ▼
[ READY_FOR_RECONCILIATION ]
       │
       ▼
[ READY_FOR_TIER_A_EVALUATION ]
```

### Lifecycle State Definitions
1. **`NOT_ACQUIRED`:** Evidence identified in procurement/court records but not physically present in repository.
2. **`RECEIVED`:** File placed in intake quarantine (`data/delhi/intake/`); checksum unverified.
3. **`CHECKSUM_VERIFIED`:** SHA-256 hash computed and frozen; file moved to immutable raw storage (`data/delhi/raw/`).
4. **`PROVENANCE_VERIFIED`:** Official seals, signatures, issuing memo, and institutional chain authenticated.
5. **`STRUCTURALLY_PARSED`:** Dimensions, chainages, and elevations extracted into standardized tabular/vector schemas.
6. **`READY_FOR_RECONCILIATION`:** Cross-checked against adjacent reach geometry and historical flood marks.
7. **`READY_FOR_TIER_A_EVALUATION`:** Integrated into Tier-A readiness gate for numerical hydraulic modeling.
8. **`REJECTED`:** Corrupted file, forged attribution, or illegible scan.
9. **`BLOCKED`:** Genuine document, but missing vital technical metadata (e.g., unlocated benchmark, undefined datum).
10. **`UNAVAILABLE`:** Formally confirmed by public authority as lost, destroyed, or non-existent.

---

## 4. SCIENTIFIC EVIDENCE ACCEPTANCE & ANTI-FABRICATION RULES

The following nine rules are mandatory and inviolable across all project pipelines:

### Rule 1: Tender / Procurement Notices Do Not Satisfy Survey Requirements
* A Notice Inviting Tender (NIT), Notice Inviting Quotation (NIQ), Request for Proposal (RFP), or Bill of Quantities (BOQ) represents an administrative statement of intent, not an empirical observation.
* Possession of NIQ 2025-26/249 or NIT 52/2025-26 classifies strictly as `PROCUREMENT_SPECIFICATION`. It does **not** upgrade `SURVEY_FOUND` to `YES`.

### Rule 2: Administrative Statements Require Primary Underlying Records
* A statement in a government report, council minute, or judicial affidavit asserting that *"a survey was performed"* or *"the drain was desilted to bed level"* does **not** satisfy Tier-A requirements without the primary, authenticated survey deliverable (drawing sheet, sounding log, or point cloud).

### Rule 3: Procurement Size Classes Are Not Measured Cross-Sections
* Contractual costing buckets (e.g., *"width 4.00 meter +25%"* in NIT-52 SOQ Item 1) or estimated billing quantities (e.g., 21,406 m³ silt) shall **never** be converted into numerical solver cross-sections or bed elevations.

### Rule 4: Drawings Without Provenance Must Be Rejected
* Any CAD file (.dwg/.dxf) or drawing sheet missing an issuing departmental stamp, signed title block, drawing number, and date shall be rejected and must not upgrade Tier-A status.

### Rule 5: Open Reach Cross-Sections Require Georeferenced Chainage
* Measured cross-sections qualify for `OPEN_REACH_CROSS_SECTIONS` only if each cross-section is tied to a verified longitudinal chainage ($x$), transverse offsets ($y$), and elevation ($z$) relative to a known survey alignment.

### Rule 6: Covered Conduit Drawings Apply Strictly to Documented Segments
* An as-built drawing of a specific covered section (e.g., the 1.0 km Bus Depot multi-cell box) satisfies `COVERED_CONDUIT_GEOMETRY` **strictly and exclusively** for that documented reach. It must never be extrapolated or assumed to represent the Africa Avenue conduit or upstream NDMC reaches.

### Rule 7: Vertical Datum Remains UNKNOWN Until Explicitly Established
* Unless a survey sheet or report explicitly documents tie-in to a Survey of India GTS Benchmark or defined Mean Sea Level (MSL) reference with verified Reduced Level, vertical datum must be classified as `UNKNOWN`.
* **Zero Elevation Assumption Prohibited:** An engineer must never assume that an arbitrary local datum equals MSL or that inter-agency invert levels share a common baseline.

### Rule 8: Zero Interpolation During Ingestion
* If survey cross-sections are available at Chainage 1+000 and Chainage 1+500, no intermediate synthetic cross-sections shall be created or marked as surveyed. Missing reaches must remain explicitly labeled `UNSURVEYED / UNKNOWN`.

### Rule 9: Immutability of Raw Evidence
* Raw files deposited in `data/delhi/raw/` shall be set read-only. No script or agent shall edit, re-save, or overwrite raw evidence files. All parsing, coordinate transforms, and unit conversions must occur in isolated derivation scripts writing to `data/delhi/derived/`.\n