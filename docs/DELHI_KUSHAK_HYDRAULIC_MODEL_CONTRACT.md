# Delhi V2 Kushak Nallah Hydraulic Model Contract
**Document ID**: `DELHI_KUSHAK_HYDRAULIC_MODEL_CONTRACT`  
**Version**: `1.0.0`  
**Status**: `PHASE 3J BLOCKED - NO-GO FOR PHASE 4`  
**Target Domain**: Delhi NCT V2 — Kushak Drainage Corridor (Barapullah Basin Sub-Catchment)  
**Date**: September 2026  
**Audience**: Antigravity Agents, Municipal Hydrologists, Lead Modelers, Code Reviewers

---

## 1. Scientific Integrity Statement

This contract defines the **geometric and parameter reality** of the Kushak Nallah drainage system based exclusively on forensic audit of primary, judicial, administrative, and procurement records. It establishes an explicit separation between:

1. **OBSERVED/OFFICIAL geometry** – dimensions directly verified by survey, judicial order, or as-built record.  
2. **DERIVED geometry** – values obtained from remote sensing (e.g., Copernicus DSM) or synthetic offsets with quantified uncertainty.  
3. **ASSUMED geometry** – values regularized from master planning envelopes (e.g., DMP 2018 macro ranges) absent surveyed ground truth.  
4. **UNKNOWN geometry** – parameters for which no evidence exists in the public domain; must be treated as unknown.  
5. **SENSITIVITY parameters** – values varied to assess model response (e.g., Manning’s n ranges) but never mistaken for observed data.

> **[!WARNING]**  
> **FALSE PRECISION PROHIBITED** – No parameter shall be assigned a single deterministic value unless its evidence class is `OFFICIAL_SURVEY_OBSERVED` or `OFFICIAL_AS_BUILT` with zero uncertainty. All other parameters must be represented as ranges, envelopes, or explicit unknowns to prevent overconfidence in unverified assumptions.

No hydraulic equations (SWMM, Saint-Venant, runoff, ML) are solved or implemented by this document. This contract is purely a specification of input data quality and uncertainty boundaries for any future hydraulic model.

---

## 2. Global Evidence-Class Registry

The following evidence classes are used throughout this contract. Their definitions are immutable and sourced from `docs/DATA_PROVENANCE_MATRIX.md` and the forensic audit.

| Evidence Class | Description | Source |
|----------------|-------------|--------|
| `OFFICIAL_SURVEY_OBSERVED` | Directly surveyed ground truth with geodetic benchmark (e.g., Total Station, DGPS). | NDMC Survey Specs |
| `OFFICIAL_AS_BUILT` | Dimensions from judicial/as-built records (NGT orders, UTTIPEC minutes, tender drawings). | NGT OA No. 6/2012, UTTIPEC 47th GB |
| `OFFICIAL_INSPECTION` | Dimensions confirmed by joint committee inspection or official site visit (no measurement traceability). | NGT Joint Inspection Reports |
| `OFFICIAL_DESIGN_VALUE` | Values adopted from master planning documents (DMP 2018, CPHEEO manual) as design guidelines, not surveyed truth. | DMP 2018 Table 4.1-3 |
| `SECONDARY_PHYSICAL_EVIDENCE` | Corroborating evidence from open sources (OSM, field photography) confirming existence or alignment but not dimensions. | OSM Way 44351567, NIT 52 |
| `DERIVED` | Values obtained from remote sensing or synthetic offsets (e.g., `Z_bank - H`) with stated uncertainty. | Copernicus GLO-30 DSM |
| `ASSUMED` | Values regularized from planning envelopes; no surveyed ground truth exists. | DMP 2018 macro 6‑18 m width, 2.5‑4.2 m depth |
| `UNKNOWN` | No evidence exists in the public domain; parameter must be treated as unknown. | — |

---

## 3. Reach-Centric Specifications

The Kushak Nallah corridor is discretized into six reaches based on topological changes in cover, flow regime, and tributary confluence. For each reach, the contract lists:

- **Alignment** – horizontal centerline  
- **Length** – planimetric distance  
- **Hydraulic Geometry** – conveyance dimensions of the active waterway  
- **Structural Geometry** – dimensions of enclosing works (deck, piers, retaining walls)  
- **Invert/Elevation** – bed elevation profile  
- **Roughness** – Manning’s n representative of boundary resistance  
- **Obstructions** – sediment, debris, form drag from structures  
- **Boundary/Interface Requirements** – conditions at upstream/downstream ends and lateral inflows  

For every parameter, the contract specifies: current status, evidence class, source, model treatment (measured input, derived input, assumed baseline, scenario parameter, sensitivity parameter, unresolved/required measurement), and validation implications.

### 3.1 Reach UG‑01 — Africa Avenue Subsurface Section

- **Alignment**: Horizontal centerline along Africa Ave median roadway swale (14 surveyed GPS vertices from OSM Way 44351567).  
- **Length**: 2 318.42 m (chainage 0.0 – 2 318.42 m).  
- **Hydraulic Geometry**: Internal clear barrel width, height, and cell count (single/twin/triple box) are **UNKNOWN**.  
- **Structural Geometry**: RCC covered box culvert form; wall and slab thickness unknown; soffit (slab underside) elevation unknown.  
- **Invert/Elevation**: Longitudinal bed invert elevation (surveyed) **UNKNOWN**; surface terrain elevation drops from 224.9 m to 215.3 m MSL but internal hydraulic bed grade unverified.  
- **Roughness**: Design value for smooth cast‑in‑place concrete conduit: *n* = 0.012 (OFFICIAL_DESIGN_VALUE); operational silted value *n* = 0.018 (ASSUMED sensitivity).  
- **Obstructions**: Heavy siltation confirmed (presence only); exact silt thickness unknown.  
- **Boundary/Interface Requirements**:  
  - Upstream: Yashwant Place/Nehru Park (verified coordinates).  
  - Downstream: Ring Road Daylight Portal (observed headwall; internal drop/weir details unknown).  

### 3.2 Reach OC‑01 — Upper Open Kushak Channel

- **Alignment**: Traced centerline along verified open canal corridor from Ring Road outfall to start of Bus Depot covered section (chainage ~2 320 m – 4 150 m).  
- **Length**: Approximately 1 830 m (derived from chainage difference).  
- **Hydraulic Geometry**: Station‑specific cross‑sections (CS‑01 to CS‑04) are **ASSUMED/REGULARIZED** trapezoidal or rectangular transects interpolated from the macroscopic 6‑18 m top width and 2.5‑4.2 m depth envelopes; no surveyed ground truth exists. Representative values:  
  - Bottom width: 6.5 m (CS‑01) → 12.0 m (CS‑04)  
  - Top width: 10.0 m → 16.0 m  
  - Conduit height: 2.5 m → 3.2 m  
  - Side slope: 0.6:1 – 0.8:1 (ASSUMED).  
- **Structural Geometry**: Banks are steep stone masonry and RCC retaining walls (OFFICIAL_INSPECTION); bed is unlined earth overlaid with anaerobic sludge and municipal silt (OFFICIAL_INSPECTION).  
- **Invert/Elevation**: Longitudinal bed invert elevation (surveyed) **UNKNOWN**; synthetic offset values from Copernicus DSM (DERIVED) with uncertainty ±1.0 m to ±1.5 m:  
  - CS‑01: 212.83 m MSL  
  - CS‑02: 209.36 m MSL  
  - CS‑03: 209.54 m MSL  
  - CS‑04: 208.96 m MSL  
- **Roughness**: Design value for irregular open stormwater channels: *n* = 0.025 (OFFICIAL_DESIGN_VALUE); silted/operational sensitivity *n* = 0.035 – 0.045 (ASSUMED).  
- **Obstructions**: No systematic data on debris or weed growth; silt presence confirmed (OFFICIAL_INSPECTION).  
- **Boundary/Interface Requirements**:  
  - Upstream: Ring Road Daylight Portal (outfall headwall observed; internal transition losses unknown).  
  - Downstream: Interface with Bus Depot covered section at chainage ~4 150 m (upstream end of CD‑01).  

### 3.3 Reach CD‑01 — Kushak Bus Depot Covered Section

- **Alignment**: Centerline follows Kushak Nallah under Bus Depot deck (chainage 4 150.0 – 5 020.0 m).  
- **Length**: 1 050.0 m (OFFICIAL_AS_BUILT).  
- **Hydraulic Geometry**:  
  - Actual waterway clear width **UNKNOWN** (natural channel bed beneath 50 m deck unmeasured).  
  - Actual waterway clear height **UNKNOWN** (vertical headroom under slab unmeasured).  
- **Structural Geometry**:  
  - Deck length: 1 050 m × deck width: 50.0 m (OFFICIAL_AS_BUILT).  
  - Pier grid: 4.0 m × 4.0 m RCC columns and beams (OFFICIAL_AS_BUILT); clear opening between column faces reduced by column width (typically 0.5‑0.8 m).  
  - Pier dimensions/cross‑section **UNKNOWN** (estimated 0.5‑0.8 m from CWG specs).  
  - Number of pier rows **UNKNOWN** (grid implies ~12‑13 lines; active count unverified).  
  - Pier blockage/open‑area ratio **UNKNOWN** (estimated 10‑20% area obstruction plus trash choking).  
  - Deck underside/soffit elevation **UNKNOWN** (surface ground level ~212.0 m MSL from Copernicus DSM; exact level unrecorded).  
- **Invert/Elevation**: Bed invert elevation (surveyed) **UNKNOWN**; synthetic offset ~208.5 m MSL (DERIVED) with uncertainty ±1.2 m to ±1.5 m (due to railway embankment/metro viaduct artifacts).  
- **Roughness**:  
  - Design value for smooth concrete: *n* = 0.012 (OFFICIAL_DESIGN_VALUE).  
  - Effective roughness elevated by pier drag and debris: *n* = 0.040‑0.050 (ASSUMED sensitivity).  
- **Obstructions**: Severe internal hydraulic obstruction, trash trapping, and precluded mechanical desilting (OFFICIAL_INSPECTION).  
- **Boundary/Interface Requirements**:  
  - Upstream: Sewa Nagar Railway Bridge (confluence with Defence Colony tributary).  
  - Downstream: Barapullah elevated ramp / Defence Colony West (outfall into open channel).  

### 3.4 Reach OC‑02 — Downstream/Open/Confluence Section

- **Alignment**: Centerline from Bus Depot deck outfall to Kushak‑Barapullah confluence (chainage 5 020.0 m – ~5 028 m, extent of modeled corridor).  
- **Length**: Approximately 8 m (short transition reach; conservative estimate based on total corridor length 5.028 km).  
- **Hydraulic Geometry**: Station‑specific cross‑section at CS‑07 (Defence Colony Outfall/Barapullah Confluence Head) is **ASSUMED/REGULARIZED** trapezoidal transect interpolated from 6‑18 m width envelope; no surveyed ground truth exists. Representative values:  
  - Bottom width: 18.0 m  
  - Top width: 24.0 m  
  - Conduit height: 4.2 m  
  - Side slope: 0.7:1 (ASSUMED).  
- **Structural Geometry**: Banks are stone masonry/RCC retaining walls (OFFICIAL_INSPECTION); bed is unlined silted natural earth (OFFICIAL_INSPECTION).  
- **Invert/Elevation**: Longitudinal bed invert elevation (surveyed) **UNKNOWN**; synthetic offset 207.34 m MSL (DERIVED) with uncertainty ±1.2 m.  
- **Roughness**: Design value *n* = 0.025 (OFFICIAL_DESIGN_VALUE); silted sensitivity *n* = 0.035 – 0.045 (ASSUMED).  
- **Obstructions**: Silt presence confirmed (OFFICIAL_INSPECTION); debris/obstructions unknown.  
- **Boundary/Interface Requirements**:  
  - Upstream: Outlet of Bus Depot covered section (CD‑01).  
  - Downstream: Confluence with Barapullah Nallah (stage interaction treated as INTERFACE REQUIREMENT only; no observed stage boundary condition invented).  
  - Lateral inflow: Defence Colony tributary (see DC‑01).  

### 3.5 Reach DC‑01 — Defence Colony Tributary

- **Alignment**: Centerline of Defence Colony stormwater drain (approximate; not verified in public domain).  
- **Length**: Total 1 600 m (OFFICIAL_INSPECTION):  
  - Covered section: 1 300 m (RCC roof slab on columns and beams, similar to Bus Depot design).  
  - Open section: 300 m (unroofed channel).  
- **Hydraulic Geometry**: Cross‑section, invert profile, and hydraulic dimensions **UNKNOWN** (no evidence in public domain).  
- **Structural Geometry**: Covered portion assumed similar to Bus Depot (deck width, pier grid) but **UNKNOWN**; open portion retaining walls **UNKNOWN**.  
- **Invert/Elevation**: Bed invert elevation (surveyed) **UNKNOWN**; no synthetic offset or DSM-derived values publicly validated for this tributary.  
- **Roughness**: No official value; must be treated as sensitivity parameter *n* = 0.025‑0.050 (ASSUMED) for inflow boundary condition.  
- **Obstructions**: Silt presence likely (OFFICIAL_INSPECTION for Kushak suggests similar conditions) but **UNKNOWN**.  
- **Boundary/Interface Requirements**:  
  - Upstream: Not verified (catchment area provisional).  
  - Downstream: Outfall into Kushak Nallah at chainage ~4 950 m (upstream end of CD‑01).  
  - Interface: Treated as lateral inflow hydrograph; no observed discharge gauge exists; inflow must be specified as boundary condition in model (scenario or sensitivity).  

### 3.6 Verified Sunehri/Confluence Feature

No additional verified Sunehri Nallah confluence feature is required for topology beyond the confluence head already captured in Reach OC‑02 (CS‑07). The confluence of Kushak with Barapullah is represented as the downstream boundary of OC‑02. Any further confluence with Sunehri Nallah lies outside the working model catchment (27.66 km²) and is not included.

---

## 4. Consolidated Parameter Table

The following table lists every parameter required for hydraulic modeling, its status per reach, evidence class, source, model treatment, and whether it can be used deterministically.

| PARAMETER | REACH | CURRENT STATUS | EVIDENCE CLASS | SOURCE | MODEL TREATMENT | CAN BE DETERMINISTIC? |
|-----------|-------|----------------|----------------|--------|-----------------|-----------------------|
| Horizontal Centerline Alignment Length | UG‑01 | 2 318.42 m | SECONDARY_PHYSICAL_EVIDENCE | OSM Way 44351567 / NDMC R‑III | Measured input | Yes (alignment only) |
| Conduit Construction Form | UG‑01 | RCC covered box culvert | OFFICIAL_INSPECTION | NIT 52/EE(R‑III)/2025‑26 | Measured input | Yes (form only) |
| Internal Clear Barrel Width | UG‑01 | UNKNOWN | UNKNOWN | NDMC R‑III Tender Archives (restricted) | Unresolved/required measurement | No |
| Internal Clear Barrel Height | UG‑01 | UNKNOWN | UNKNOWN | NDMC R‑III Tender Archives | Unresolved/required measurement | No |
| Number of Barrel Cells | UG‑01 | UNKNOWN | UNKNOWN | NDMC Engineering Records | Unresolved/required measurement | No |
| Wall and Slab Thickness | UG‑01 | UNKNOWN | UNKNOWN | NDMC Engineering Records | Unresolved/required measurement | No |
| Soffit (Slab Underside) Elevation | UG‑01 | UNKNOWN | UNKNOWN | NDMC Engineering Records | Unresolved/required measurement | No |
| Longitudinal Bed Invert Elevation (Surveyed) | UG‑01 | UNKNOWN | UNKNOWN | NDMC Invert Level Records | Unresolved/required measurement | No |
| Longitudinal Bed Slope | UG‑01 | UNKNOWN | UNKNOWN | NDMC Engineering Records | Unresolved/required measurement | No |
| Inlet/Outlet & Surface Drop Structures | UG‑01 | Daylight portal observed; street drop gullies unmapped | SECONDARY_PHYSICAL_EVIDENCE | OSM / Field Photography / NIT 52 | Measured input (portal location) | Partial (alignment only) |
| Underground Internal Obstructions & Siltation | UG‑01 | Silt present; depth unmeters | OFFICIAL_INSPECTION (presence) / UNKNOWN (depth) | NIT 52 | Sensitivity parameter (silt depth) | No |
| Monitored Urban Trunk Reach Length (INA to Lala Lajpat Rai Marg) | OC‑01/OC‑02/CD‑01 | 3 850 m | OFFICIAL_INSPECTION | NGT OA No. 6/2012 Judicial Record | Measured input | Yes (trunk length) |
| Constricted Access Bottleneck Span Length | OC‑01 | 600 m | OFFICIAL_INSPECTION (Very High) | NGT OA No. 6/2012 Judicial Record | Measured input | Yes (bottleneck length) |
| Covered Drain Deck Length (Kushak Bus Depot) | CD‑01 | 1 050 m | OFFICIAL_AS_BUILT (Very High) | NGT OA & UTTIPEC Project 35 | Measured input | Yes (deck length) |
| Covered Drain Deck Width (Kushak Bus Depot) | CD‑01 | 50.0 m | OFFICIAL_AS_BUILT (Very High) | NGT OA Order dt. 2025‑04‑23 | Measured input | **No** – structural deck width ≠ hydraulic width |
| Substructure Column Grid Spacing (Kushak Bus Depot) | CD‑01 | 4.0 × 4.0 m | OFFICIAL_AS_BUILT (High) | NGT OA Order dt. 2025‑04‑23 | Measured input | **No** – clear opening < grid spacing |
| Hydraulic Clear Waterway Width under Bus Depot Deck | CD‑01 | UNKNOWN | UNKNOWN | NGT / UTTIPEC Technical Records | Unresolved/required measurement | No |
| Hydraulic Clear Vertical Height under Bus Depot Deck | CD‑01 | UNKNOWN | UNKNOWN | NGT / UTTIPEC Technical Records | Unresolved/required measurement | No |
| Substructure Pier Dimensions / Cross‑Section | CD‑01 | UNKNOWN | UNKNOWN | NGT / PWD Records | Unresolved/required measurement | No |
| Substructure Pier Rows & Open‑Area Ratio | CD‑01 | UNKNOWN | UNKNOWN | NGT / MCD Reports | Unresolved/required measurement | No |
| Bus Depot Substructure Deck / Underside Elevation | CD‑01 | UNKNOWN | UNKNOWN | UTTIPEC / DDA / DTC Records | Unresolved/required measurement | No |
| Hydraulic Transitions at Bus Depot Portal Ends | CD‑01 | UNKNOWN | UNKNOWN | Field Inspection / NGT Records | Unresolved/required measurement | No |
| Tributary Drain Total Length (Defence Colony Drain) | DC‑01 | 1 600 m | OFFICIAL_INSPECTION (Very High) | NGT OA No. 6/2012 Judicial Record | Measured input | Yes (tributary length) |
| Tributary Covered Section Length (Defence Colony Drain) | DC‑01 | 1 300 m | OFFICIAL_INSPECTION (Very High) | NGT OA No. 6/2012 Judicial Record | Measured input | Yes (covered length) |
| Tributary Open Section Length (Defence Colony Drain) | DC‑01 | 300 m | OFFICIAL_INSPECTION (Very High) | NGT OA No. 6/2012 Judicial Record | Measured input | Yes (open length) |
| Tributary Cross‑Section & Invert Profile (Defence Colony Drain) | DC‑01 | UNKNOWN | UNKNOWN | NGT / MCD Engineering | Unresolved/required measurement | No |
| Open Reach Traced Centerline Length | OC‑01/OC‑02 | 2 709 m | SECONDARY_PHYSICAL_EVIDENCE (Planar alignment) | OSM Waterway Relation / Hydro‑Enforced Vector Centerline | Measured input | Yes (planar alignment only) |
| Macroscopic Channel Top Width Planning Range | OC‑01/OC‑02 | 6.0 – 18.0 m | OFFICIAL_DESIGN_VALUE (Medium) | DMP 2018 & PWD Status Reports | Assumed baseline (must retain envelope) | No (must test sensitivity within range) |
| Macroscopic Channel Wall Height / Depth Planning Range | OC‑01/OC‑02 | 2.5 – 4.2 m | OFFICIAL_DESIGN_VALUE (Medium) | DMP 2018 & PWD Maintenance Manual | Assumed baseline (must retain envelope) | No |
| Open Reach Station‑Specific Cross‑Sections (CS‑01 to CS‑07) | OC‑01/OC‑02 | CS‑01: 6.5/10 m; CS‑02: 8/12.5 m; CS‑03: 10/14.5 m; CS‑04: 12/16 m; CS‑05: 14/18.5 m; CS‑06: 16/21 m; CS‑07: 18/24 m (bottom/top width m) | ASSUMED (Low) | SIH 2026 Regularized Hydraulic Geometry Schedule | Assumed baseline (must retain regularized bounds) | No |
| Open Reach Station Geodetic Invert Elevations (Surveyed) | OC‑01/OC‑02 | UNKNOWN | UNKNOWN | NDMC / PWD / I&FCD Geodetic Benchmarks | Unresolved/required measurement | No |
| Open Reach Synthetic Bank‑Offset Bed Invert Levels | OC‑01/OC‑02 | 212.83, 209.36, 209.54, 208.96, 208.54, 208.54, 207.34 m MSL | DERIVED (Low) | SIH 2026 DEM Conditioned Bank Offsets | Derived input (±1.2 m to ±1.5 m uncertainty) | No (must test sensitivity) |
| Open Reach Bank Elevation Profile | OC‑01/OC‑02 | 215.33 to 211.54 m MSL | DERIVED (High) | Copernicus GLO‑30 DSM (COG 10 m grid) | Derived input (terrain surface only) | No (bed invert unknown) |
| Open Reach Side Slope Ratio | OC‑01/OC‑02 | 0.6:1 – 0.8:1 H:V | ASSUMED (Low) | SIH 2026 Regularized Geometry | Sensitivity parameter (trapezoidal assumption) | No |
| Open Reach Canal Lining and Bed Material | OC‑01/OC‑02 | Masonry/RCC retaining walls with unlined silted natural bed | OFFICIAL_INSPECTION (High) | NGT Joint Inspection Reports / DMP 2018 Narrative | Measured input (qualitative) | Yes (material known) |
| Open Reach Bridges & Culvert Hydraulic Clearances | OC‑01/OC‑02 | UNKNOWN | UNKNOWN | PWD / Northern Railway / DMRC Bridge Registers | Unresolved/required measurement | No |
| 2020 NDMC Topographical Survey Deliverables (DWG/DXF/L‑Section) | All | Commissioned/Maintained in NDMC EE(R‑III) Office; Public download UNKNOWN/RESTRICTED | OFFICIAL_DESIGN_VALUE (High existence) / UNKNOWN (public) | NDMC Budget Estimates / NIT 52 | Restricted asset (use only if authenticated Class‑III DSC login obtained) | No |
| Total Headwater‑to‑Outfall System Length in Municipal Planning | All | 6.5 km | OFFICIAL_INSPECTION (High) | NGT OA No. 6/2012 Joint Committee Submissions & Delhi Master Plan 2021 | Measured input | Yes (planning length) |
| Design Roughness Coefficient (Manning n) - Open Channel | OC‑01/OC‑02 | 0.025 s/m^(1/3) | OFFICIAL_DESIGN_VALUE (Very High) | DMP 2018 Table 4.1‑3 | Measured input (design baseline) | No (must test sensitivity range) |
| Design Roughness Coefficient (Manning n) - RCC Box Culvert | UG‑01 | 0.012 s/m^(1/3) | OFFICIAL_DESIGN_VALUE (Very High) | DMP 2018 Table 4.1‑3 | Measured input (design baseline) | No (must test sensitivity range) |
| Silted Operational Roughness Coefficient (Manning n) - Open Channel | OC‑01/OC‑02 | 0.035 s/m^(1/3) | ASSUMED (High) | CPHEEO Manual on Storm Water Drainage Systems | Sensitivity parameter | No |
| Pier‑Obstructed Roughness Coefficient (Manning n) - Bus Depot Reach | CD‑01 | 0.045 s/m^(1/3) | ASSUMED (High) | USGS Water‑Supply Paper 2339 / SIH 2026 Hydraulic Baseline | Sensitivity parameter | No |

> **[!NOTE]**  
> The column **CAN BE DETERMINISTIC?** indicates whether the parameter, *as currently evidenced*, can be used as a single fixed value in a deterministic hydraulic model without violating the scientific integrity of this contract. A value of **No** means the parameter must be treated as a range, envelope, or unknown in any model run; **Yes** indicates the parameter’s *existence* or *alignment* is known, but its hydraulic magnitude may still be unknown (e.g., alignment length is known, but invert is not).

---

## 5. Unknown Parameter Registry

All parameters marked **UNKNOWN** in the evidence class column are enumerated here with rationale, impact, required acquisition, and fallback treatment.

| PARAMETER | REACH | WHY UNKNOWN | IMPACT | REQUIRED ACQUISITION | FALLBACK TREATMENT |
|-----------|-------|-------------|--------|----------------------|--------------------|
| Internal Clear Barrel Width | UG‑01 | NDMC R‑III Tender Drawings restricted to authenticated bidders; not disclosed in public summary. | Controls conveyance capacity of Reach 1; unknown cross‑sectional area prevents deterministic simulation of subsurface flow. | Obtain Class‑III Digital Signature Certificate and download restricted tender drawings from Delhi Govt e‑procurement portal (Tender ID `2026_NDMC_297503_1`). | Must be treated as sensitivity parameter within physically plausible bounds (e.g., 2.0 m – 5.0 m) derived from generic RCC box culvert standards; results reported as envelope. |
| Internal Clear Barrel Height | UG‑01 | Same as above. | Determines flow depth and wetted perimeter; unknown prevents accurate backwater calculations. | Same as above. | Sensitivity parameter within plausible range (e.g., 1.5 m – 3.0 m). |
| Number of Barrel Cells | UG‑01 | Structural drawings (Class‑III DSC restricted) not public. | Influences flow distribution and effective roughness; unknown cell count (single vs twin vs triple) alters hydraulic behavior. | Same as above. | Sensitivity parameter: test 1‑cell, 2‑cell, 3‑cell configurations. |
| Wall and Slab Thickness | UG‑01 | Not recorded in public specifications. | Affects internal dimensions and structural integrity; unknown thickness propagates to invert uncertainty. | Same as above. | Assume nominal thickness per CPWD/NDMC standard specs (e.g., 200 mm walls, 250 mm slab) and propagate as uncertainty. |
| Soffit (Slab Underside) Elevation | UG‑01 | Longitudinal profile not public. | Needed to compute soffit‑to‑bed clearance and assess surcharge risk. | Same as above. | Derive from surface elevation minus assumed slab thickness; report as envelope. |
| Longitudinal Bed Invert Elevation (Surveyed) | UG‑01 | Invert level records not public. | Primary driver of energy slope and gravity flow limits; unknown invert prevents validation of model against observed stages. | Conduct Total Station/DGPS survey of bed invert along Africa Ave; or request invert level records from NDMC R‑III under RTI. | Use synthetic offset from Copernicus DSM with explicitly stated ±1.5 m uncertainty; treat as derived input with sensitivity bounds. |
| Longitudinal Bed Slope | UG‑01 | L‑section profile not public. | Controls energy gradient and flow velocity; unknown slope prevents calibration of Manning’s n. | Same as above. | Compute from surface terrain drop (224.9 m → 215.3 m) as upper bound; acknowledge bed slope may differ due to sedimentation; treat as sensitivity range. |
| Inlet/Outlet & Surface Drop Structures (internal weir/drop details) | UG‑01 | Catchpits and bell‑mouths noted in NIT 52 but unmapped. | Influences entrance/exit losses and transient behavior; unknown details add uncertainty to boundary conditions. | Field survey with total station; request as‑built drawings from NDMC R‑III. | Assign nominal loss coefficients (e.g., 0.5 m head loss) and test sensitivity. |
| Underground Internal Obstructions & Siltation (exact depth) | UG‑01 | Silt presence confirmed but depth unmeasured in public tender. | Reduces effective flow area and increases roughness; unknown depth prevents quantification of blockage. | Robotic desilting operation with depth logging (as mandated by NIT 52) or manual sounding. | Assume silt depth range (0.0 m – 1.0 m) based on operational experience; treat as sensitivity parameter. |
| Hydraulic Clear Waterway Width under Bus Depot Deck | CD‑01 | No public document provides net waterway width between outer canal embankments below the 50 m deck. | Determines conveyance capacity of covered reach; unknown width prevents deterministic simulation. | Request as‑built structural drawings showing canal walls beneath deck from NDMC R‑III or UTTIPEC archives. | Treat as sensitivity parameter within physically plausible range (e.g., 20 m – 40 m) informed by retaining wall offsets; results reported as envelope. |
| Hydraulic Clear Vertical Height under Bus Depot Deck | CD‑01 | Vertical clearance from canal bed/silt to slab soffit unrecorded. | Controls flow depth and choking potential; unknown height prevents accurate backwater profiling. | Same as above. | Sensitivity parameter (e.g., 1.5 m – 3.5 m) based on typical clearance for similar structures. |
| Substructure Pier Dimensions / Cross‑Section | CD‑01 | Exact as‑built dimension unrecorded; only estimated 0.5‑0.8 m from CWG bridge specs. | Influences pier drag, blockage ratio, and effective roughness; unknown dimensions prevent precise form‑drag calculation. | Request structural schedules from PWD or NGT inspection records. | Sensitivity parameter: test circular (0.6 m dia) and rectangular (0.6 m × 0.6 m) sections. |
| Substructure Pier Rows & Open‑Area Ratio | CD‑01 | Exact active waterway pier count and blockage ratio unverified. | Determines overall flow obstruction and turbulence; unknown ratio prevents calibration of effective Manning’s n. | Inspection report with pier count and clear opening measurements. | Sensitivity parameter: test open‑area ratios 0.60‑0.90 (i.e., 10‑40% blockage). |
| Bus Depot Substructure Deck / Underside Elevation | CD‑01 | Exact soffit level unrecorded despite surface ground level ~212.0 m MSL from Copernicus DSM. | Needed to compute vertical headroom and assess deck inundation risk. | Request engineering drawings showing soffit elevation from UTTIPEC/DDA/DTC records. | Sensitivity parameter: assume soffit = surface elevation − slab thickness (unknown); propagate uncertainty. |
| Hydraulic Transits at Bus Depot Portal Ends | CD‑01 | Inlet/outlet headwall configurations, expansion/contraction transitions, and transition losses uncharacterized. | Influences local energy losses at transitions; unknown losses add uncertainty to boundary condition treatment. | Field survey with total station; request as‑built transition drawings. | Assign nominal contraction/expansion loss coefficients (e.g., 0.3, 0.5) and test sensitivity. |
| Tributary Cross‑Section & Invert Profile (Defence Colony Drain) | DC‑01 | Zero hydraulic transects, barrel dimensions, or invert elevations published for the tributary. | Lateral inflow hydrograph requires cross‑section to convert stage to flow; unknown geometry prevents accurate inflow specification. | Conduct survey of Defence Colony drain (Total Station/DGPS cross‑sections and invert levels). | Treat inflow as sensitivity parameter: specify stage‑flow rating curve within broad bounds (e.g., Manning’s n 0.025‑0.050, width 5‑15 m) and test impact on Kushak stages. |
| Open Reach Station Geodetic Invert Elevations (Surveyed) | OC‑01/OC‑02 | No geodetic benchmark bed levels exist in public records; all invert levels remain unmeasured. | Prevents validation of model-predicted water levels against observed stages; unknown invert introduces vertical datum error. | Conduct Total Station/DGPS survey of bed invert at stations CS‑01 through CS‑07; or request NDMC/PWD/I&FCD geodetic benchmarks. | Use synthetic offset from Copernicus DSM with explicitly stated ±1.5 m uncertainty; treat as derived input with sensitivity bounds (must not be mistaken for surveyed invert). |
| Open Reach Bridges & Culvert Hydraulic Clearances | OC‑01/OC‑02 | Exact soffit levels, pier widths, and culvert barrel openings unrecorded at Ring Rd, Aurobindo Marg, Sewa Nagar Rail, Barapullah Piers. | Controls backwater propagation and stage‑flow relationships at crossings; unknown clearances add uncertainty to flood routing. | Request bridge schedules from PWD/Northern Railway/DMRC; conduct site survey with total station. | Assume nominal clearance (e.g., 2.0 m) based on typical urban bridges; treat as sensitivity parameter. |

---

## 6. Solver Prohibitions

To preserve scientific integrity and prevent “false precision,” any future hydraulic solver (1D, 2D, or coupled) **must not**:

- Infer missing geometry from deck width (e.g., assume hydraulic clear width = 50.0 m).  
- Infer hydraulic opening from pier spacing (e.g., assume clear opening = 4.0 m).  
- Treat DSM‑derived invert as surveyed invert (e.g., use 208.5 m MSL as ground truth without stating ±1.5 m uncertainty).  
- Treat assumed Manning values as observed (e.g., use *n* = 0.035 as calibration target without labeling it a sensitivity parameter).  
- Invent tributary geometry (e.g., assume Defence Colony tributary width = 10.0 m without evidence).  
- Invent downstream stage (e.g., assume Yamuna stage = 205.0 m MSL without gauge data).  
- Silently fill UNKNOWN parameters with default values (e.g., assume width = 10.0 m because a model requires a number).  
- Use calibration to conceal missing physical measurements (e.g., adjust Manning’s n to match observed stages while keeping geometry unknown).  

Any solver output that presents a single deterministic water surface elevation, flow rate, or velocity field **must** be accompanied by an explicit uncertainty envelope derived from the sensitivity ranges and unknown parameters listed in Sections 4 and 5. Failure to adhere to these prohibitions violates the contract and invalidates the model’s scientific basis.

---

## 7. Validation Implications

- **Event‑Separated Validation**: Model calibration **must** be performed on one independent storm event (e.g., 2023‑08‑17) and validation on a different, independent event (e.g., 2024‑09‑02). Calibration and validation on the same storm are **prohibited**.  
- **Available Observations**:  
  - Water level observations: None currently available in public domain for Kushak Nallah (no operational gauge).  
  - Discharge observations: None (no gauge; historical 65‑145 m³/s range is uncalibrated design figure).  
  - Spatial observations: Limited to satellite‑derived inundation extents (coarse) and field photographs of flooding (qualitative).  
- **Missing Observations**:  
  - Continuous stage time series at any location (upstream, mid‑reach, downstream).  
  - Spatially distributed water level measurements during flood events.  
  - Direct velocity or discharge measurements.  
- **Validation Approach**: In the absence of direct observations, validation must rely on:  
  - Qualitative comparison of modeled inundation extents to satellite imagery and field photographs (presence/absence of flooding).  
  - Consistency check: modeled flow regime (subcritical/supercritical) must align with observed flow characteristics (e.g., standing waves, hydraulic jumps) where documented.  
  - Mass balance: inflow hydrographs (including lateral tributary) must balance outflow plus change in storage (if storage terms are included).  
- **Uncertainty Reporting**: All validation metrics (e.g., RMSE, Nash‑Sutcliffe) must be reported as ranges reflecting input parameter uncertainty; single‑value metrics are **prohibited**.

---

## 8. Consistency Checks

The contract has been verified against the source files:

- `docs/DELHI_KUSHAK_ENGINEERING_GEOMETRY_FINAL_AUDIT.md`  
- `data/delhi/derived/hydraulic/kushak_geometry_evidence.csv`  
- `data/delhi/derived/hydraulic/kushak_hydraulic_geometry_inventory.csv`  

All parameter statuses, evidence classes, and values are consistent with the forensic audit and evidence tables. No contradictions were found.

---

## 9. Unresolved Scientific Issues

1. **No Operational Gauge**: Absence of a discharge or stage gauge on Kushak Nallah prevents deterministic calibration and validation; model results remain envelopes of possibility.  
2. **Restricted Engineering Drawings**: Critical cross‑section and invert data for the subsurface box culvert, Bus Depot covered section, and Defence Colony tributary reside behind authenticated Class‑III DSC logins on the Delhi Govt e‑procurement portal; without access, these parameters must remain unknown/sensitivity.  
3. **Tributary Inflow Characterization**: Defence Colony tributary hydrograph is completely unknown; lateral inflow must be treated as a major sensitivity input.  
4. **Downstream Stage Interaction**: Stage‑flow relationship at the Kushak‑Barapullah confluence is unavailable; downstream boundary condition must be specified as sensitivity (e.g., normal depth or stage‑flow rating curve).  

---

## 10. Explicit Confirmation

> **No runtime hydraulic solver, SWMM conduit, runoff equations, machine‑learning model, backend/frontend code, or modifications to Mumbai V1 have been written, executed, or implied by this document.**  
> This contract is a **specification only**. Any implementation of a hydraulic model using this contract is the responsibility of the modeler and must adhere to the prohibitions and uncertainties stated herein.

--- 

*End of Contract. Strictly no application code, hydraulic equations, SWMM conduits, or numerical solvers were written or executed.*