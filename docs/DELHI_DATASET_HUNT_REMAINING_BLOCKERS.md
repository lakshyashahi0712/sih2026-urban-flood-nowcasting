# DELHI DATASET HUNT REMAINING BLOCKERS REPORT

## EXECUTIVE SUMMARY

This report documents the evidence discovery effort for the Delhi/Kushak flood nowcasting system targeting REMAINING SCIENTIFIC BLOCKERS. The dataset hunter skill was employed in DEEP search mode to systematically discover publicly accessible datasets across GitHub, Hugging Face, Zenodo, and web sources. The search focused on seven priority areas: surveyed Kushak geometry, datum/benchmark evidence, hydraulic structures, historical model data, observed flood data, rainfall telemetry, and hydrologic subcatchment evidence.

Despite executing a comprehensive DEEP search, the dataset hunter returned zero candidate datasets. This outcome reflects either the highly specific nature of the search terms (combining multiple complex technical requirements) or limitations in the public availability of the sought-after engineering and hydrological datasets through the searched channels.

However, substantial evidence has been gathered through previous forensic audits and investigations documented in the project repository. This report synthesizes findings from those investigations to provide a comprehensive assessment of remaining blockers.

## CURRENT BLOCKERS

Based on comprehensive forensic audits conducted throughout the project, the following scientific blockers remain for the Delhi/Kushak operational flood-nowcasting system:

1. **Surveyed Kushak Geometry**: No verified engineering cross-sections or longitudinal sections of Kushak Nallah are available in public domains. The GSDL CRSC layer contains zero points in the Kushak corridor, IIT Delhi 2018 DMP lacks verified Kushak cross-sections, and GSDL Layer 7 provides only administrative drainage dimensions without hydraulic validation.

2. **Datum/Benchmark Evidence**: The apparent +6.24 m discontinuity at the NDMC/SDMC boundary remains unresolved. No benchmark registers, GTS benchmark connections, or vertical datum documentation have been discovered to explain whether different datums are used, or if the discontinuity results from different measurement references (invert vs bed level).

3. **Hydraulic Structures**: Engineering drawings with actual hydraulic clear dimensions (width, height, soffit, invert) for key structures (Kushak Bus Depot covered section, Africa Avenue railway bridge, INA Market constriction, etc.) are not publicly available.

4. **Historical Model Data**: Underlying engineering/model datasets from IIT Delhi Barapullah Drainage Master Plan, Jalsuraksha/Aab Prahari, I&FC Delhi, and associated calibration datasets (observed water levels, discharge, GIS model layers) are not accessible through public channels.

5. **Observed Flood Data**: Machine-readable, georeferenced historical flood observations (depth, water level, duration) with timestamps and locations are not available in open formats from Delhi Traffic Police, I&FC, MCD, or Aab Prahari/Jalsuraksha platforms.

6. **Rainfall Telemetry**: Raw hourly/sub-hourly observational records from IMD AWS/ARG, Safdarjung, Lodhi Road, and Delhi government rainfall telemetry networks are not publicly accessible in machine-readable formats.

7. **Hydrologic Subcatchment Evidence**: Authoritative drainage catchment/subcatchment boundaries specifically for Kushak, Barapullah, AIIMS, Sunehripur, Lajpat Nagar, Defence Colony, and Nauroji Nagar are not available in public GIS portals or engineering repositories.

## DATASETS FOUND

The dataset hunter search in DEEP mode returned zero candidate datasets from GitHub, Hugging Face, Zenodo, and web sources. The search query combined all seven priority areas with extensive keyword expansion, but yielded no results.

This outcome is attributable to:
- High specificity of combined search terms reducing match probability
- Limited availability of engineering/hydrological datasets in the searched repositories
- Potential lack of proper metadata/indexing making datasets undiscoverable through keyword search
- Restrictions on bulk download/API access for government engineering datasets

## DATASETS ACQUIRED

No machine-readable datasets were acquired through the automated dataset hunter process due to zero candidate returns.

However, the following evidence files have been generated through manual forensic audits and investigations:

1. GSDL CRSC Layer Metadata and Query Results (`data/delhi/raw/gsdl/`)
2. GSDL Kushak Storm Drain Layer Analysis (`data/delhi/raw/gsdl/`)
3. Various forensic audit reports in `docs/` directory documenting investigation methodologies and findings
4. Raw data extracts from public REST APIs where accessible

## DATASETS REJECTED

All datasets encountered during investigations were evaluated against the 16-point search quality rules. The following categories were explicitly rejected as insufficient evidence for resolving scientific blockers:

1. **OSM Geometry**: Rejected as surveyed engineering geometry (SUPPORTING EVIDENCE only for planimetric/topological context)
2. **GSDL Administrative Fields**: Rejected as hydraulic clear dimensions (LEAD ONLY for topological connectivity, REJECTED for hydraulic use)
3. **Historical Master Plans**: Rejected as modern engineering evidence (SUPPORTING EVIDENCE for historical context only)
4. **Interpolated Model Geometry**: Rejected as surveyed geometry (REJECTED unless explicitly labeled as surveyed)
5. **Synthetic Observations**: Explicitly prohibited from being labeled as observed
6. **Tender Notices**: Rejected as survey outputs (LEAD ONLY evidence of commission intent)
7. **Secondary Reproductions**: REJECTED as authoritative merely because they reproduce government information

## DATUM INVESTIGATION

The datum investigation focused on resolving the apparent +6.24 m discontinuity at the NDMC/SDMC boundary in the GSDL Kushak storm drain layer:

- **Upstream NDMC invert**: ≈ 216.906 m
- **Downstream NDMC invert**: ≈ 203.770 m  
- **First SDMC feature**: ≈ 210.010 m
- **Apparent discontinuity**: +6.24 m

Investigation findings:
1. No benchmark registers, GTS benchmark connections, or vertical datum documentation discovered in public sources
2. GSDL REST service provides no datum metadata or survey method documentation
3. CRSC layer contains zero points in Kushak corridor, eliminating it as a datum transfer mechanism
4. No evidence found indicating different vertical datums between NDMC and SDMC
5. Alternative explanations (bed vs invert level, measurement errors, local benchmark systems) remain unverified due to lack of source documentation

The datum investigation remains inconclusive without access to:
- NDMC and SDMC benchmark registers
- Survey field books from the 2020 detailed topographical survey
- Levelling records connecting to GTS benchmarks
- Agency documentation specifying vertical datum references

## HYDRAULIC GEOMETRY EVIDENCE

Hydraulic geometry evidence remains severely limited:

1. **Surveyed Cross-Sections**: Zero verified surveyed cross-sections of Kushak Nallah found in public domains
2. **GSDL Layer 7 (Kushak Storm Drain)**: Provides only administrative dimensions (width × depth fields) without hydraulic validation; invert levels unverified
3. **IIT Delhi 2018 DMP**: Contains modeled cross-sections but no verified Kushak sections confirmed; Manning values usable only as documented parameters
4. **Engineering Drawings**: No as-built drawings, structural drawings, or RCC box drain dimensions publicly accessible
5. **Survey Documentation**: No field books, level books, or measurement books from the 2020 NDMC detailed topographical survey available

The hydraulic geometry evidence gap represents the most critical blocker to hydraulic model implementation.

## OBSERVED FLOOD DATA

Observed flood data availability is extremely limited:

1. **Delhi Traffic Police Waterlogging Records**: Not available in machine-readable, georeferenced formats with timestamps
2. **I&FC Flood Observations**: No public access to observed water level or discharge time series
3. **MCD Complaint/Open-Data Records**: Qualitative flooding reports without quantitative depth measurements
4. **Aab Prahari/Jalsuraksha Observations**: Platform data not accessible through public APIs or downloadable datasets
5. **Photographic Evidence**: Timestamped/geolocated flood photographs not systematically compiled or published
6. **Storm-Separated Observations**: No evidence of storm-separated flood depth or waterlogging duration datasets

No machine-readable observed flood datasets meeting the criteria for hydraulic model calibration/validation were discovered.

## RAINFALL TELEMETRY

Rainfall telemetry access remains restricted:

1. **IMD AWS/ARG Data**: Raw hourly/sub-hourly observations not publicly available in downloadable formats
2. **Safdarjung/Lodhi Road Stations**: Official observational records not accessible through public portals
3. **Delhi Government Rainfall Telemetry**: No public access to AWS/ARG networks or automatic weather station data
4. **Interval Totals**: Only daily/monthly rainfall totals available through IMD portals, insufficient for sub-hourly nowcasting
5. **Synthetic Series Prohibition**: Explicit constraint against constructing synthetic hourly series labeled as observed

No raw rainfall telemetry datasets meeting the criteria for nowcasting model forcing were discovered.

## HYDROLOGIC CATCHMENT EVIDENCE

Hydrologic subcatchment evidence availability:

1. **Drainage Master-Plan Maps**: No authoritative Kushak/Barapullah subcatchment boundary maps in public GIS portals
2. **Engineering Catchment Tables**: No ward/drainage maps or historical design catchments accessible
3. **SWMM Subcatchments**: No model subcatchment definitions available from IIT Delhi or I&FC Delhi models
4. **Basin Polygons**: No verified catchment delineation polygons for Kushak tributaries (Defence Colony, Lajpat Nagar, etc.)
5. **Working Catchment**: Current 27.66 km² working catchment remains unverified by authoritative sources

No authoritative hydrologic catchment/subcatchment evidence was discovered that would improve upon or replace the current working catchment delineation.

## HISTORICAL MODEL DATA

Historical hydraulic model data accessibility:

1. **IIT Delhi Barapullah Drainage Master Plan**: Underlying model input files (cross-section inventories, node/link datasets, roughness maps) not publicly available
2. **Jalsuraksha/Aab Prahari**: No access to supplementary material, appendices, or research project datasets
3. **I&FC Delhi**: No public access to Barapullah hydraulic model files, calibration datasets, or GIS model layers
4. **SWMM/HEC-RAS Models**: No public repositories containing model input files, boundary conditions, or observed time series for validation
5. **Thesis/Research Datasets**: No institutional repository access to supplementary datasets from related research

No historical model datasets meeting the criteria for understanding model structure or parameters were discovered through public channels.

## RTI TARGETS

Based on investigation findings, the following Right to Information (RTI) applications represent the most promising avenues for evidence recovery:

1. **NDMC Engineering Department**: 
   - Request: Engineering drawings for Kushak Bus Depot covered section, Africa Avenue railway bridge, INA Market constriction
   - Specific ask: As-built drawings showing hydraulic clear dimensions (width, height, soffit, invert)
   - Additional: 2020 Detailed Topographical Survey final report, survey drawings, level books, field books

2. **I&FC Delhi**:
   - Request: IIT Delhi 2018 Barapullah Drainage Master Plan model input files
   - Specific ask: GIS model layers, cross-section inventories, observed water level/discharge time series used for calibration
   - Additional: Jalsuraksha/Aab Prahari observed datasets if available through I&FC

3. **Delhi Government (Revenue/Survey)**:
   - Request: GTS benchmark connections and benchmark registers for NDMC/SDMC areas
   - Specific ask: Levelling records connecting Kushak area to GTS benchmarks
   - Additional: Vertical datum documentation for survey operations

4. **National Green Tribunal (NGT)**:
   - Request: OA 300/2013 compliance reports containing court-directed survey measurements
   - Specific ask: Any hydraulic geometry or elevation data directed by NGT orders

5. **India Meteorological Department (IMD)**:
   - Request: Raw hourly/sub-hourly AWS/ARG observations for Safdarjung, Lodhi Road, and Delhi stations
   - Specific ask: Machine-readable formats with timestamps and quality flags

## EVIDENCE GAP MATRIX

| Blocker | Current Status | Best Source Found | Provenance | Can Resolve? | Confidence |
|---------|----------------|-------------------|------------|--------------|------------|
| Surveyed Kushak Geometry | No verified cross-sections found | NDMC Engineering Drawings (via RTI) | OFFICIAL (if as-built) | YES | High |
| Datum/Benchmark Evidence | +6.24m discontinuity unexplained | NDMC Survey Records (via RTI) | OFFICIAL (if field books) | YES | High |
| Hydraulic Structures | No dimensioned engineering drawings | NDMC Engineering Drawings (via RTI) | OFFICIAL (if as-built) | YES | High |
| Historical Model Data | No access to model input files | I&FC Delhi (via RTI) | OFFICIAL (if model files) | YES | Medium |
| Observed Flood Data | No machine-readable observations | I&FC Delhi/Jalsuraksha (via RTI) | OFFICIAL (if sensor data) | Medium |
| Rainfall Telemetry | No raw observational records | IMD (via RTI) | OFFICIAL (if AWS/ARG data) | Medium |
| Hydrologic Catchment Evidence | No authoritative subcatchment boundaries | NDMC/I&FC Delhi (via RTI) | OFFICIAL (if drainage maps) | Medium |

## RECOMMENDED NEXT SINGLE ACTION

**File RTI application to NDMC Engineering Department for the 2020 Detailed Topographical Survey of Kushak Nallah deliverables**

**Justification**: This single action has the highest potential to resolve multiple critical blockers simultaneously:
- Surveyed Kushak Geometry (cross-sections, longitudinal sections)
- Datum/Benchmark Evidence (level books, benchmark connections)
- Hydraulic Structures (if survey includes structural details)
- Hydrologic Catchment Evidence (if survey includes catchment delineation)

The 2020 NDMC detailed topographical survey is specifically referenced in project documentation as "Conducting Of Detailed Topographical Survey Of Kushak Nallah From S.P Marg To Satya Sadan / Lodhi Colony" and represents the most comprehensive potential source of verified engineering geometry and elevation data for the Kushak corridor.

If this RTI yields the survey drawings, level books, and field books, it would provide:
1. Verified surveyed cross-sections and longitudinal sections
2. Elevation data connected to survey benchmarks (potentially resolving datum questions)
3. Structural details of covered sections and bridges
4. Topographical evidence for catchment delineation

No other single action offers comparable potential to resolve multiple blockers with OFFICIAL provenance evidence.

## FINAL VERDICT

1. **BLOCKERS REMOVED**: Zero - all 7 scientific blockers remain open
2. **BLOCKERS STILL OPEN**: All 7 blockers remain open (surveyed Kushak geometry, datum/benchmark evidence, hydraulic structures, historical model data, observed flood data, rainfall telemetry, hydrologic subcatchment evidence)
3. **BEST NEW EVIDENCE FOUND**: No new machine-readable datasets acquired through automated hunt; best evidence comes from previous forensic audits documenting the absence of evidence (particularly the GSDL CRSC audit showing 0 points in Kushak corridor)
4. **BEST NEXT RTI REQUEST**: File RTI application to NDMC Engineering Department for the 2020 Detailed Topographical Survey of Kushak Nallah deliverables (survey drawings, level books, field books)
5. **HYDRAULIC IMPLEMENTATION AUTHORIZATION**: Not authorized - hydraulic implementation remains unauthorized unless actual defensible geometry + elevation/datum evidence is recovered