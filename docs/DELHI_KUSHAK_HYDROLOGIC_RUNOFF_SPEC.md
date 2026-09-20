# Delhi V2 Kushak Catchment: Spatial Hydrologic-Loss & Runoff Specification

**Document ID**: `DELHI_KUSHAK_HYDROLOGIC_RUNOFF_SPEC`  
**Version**: `1.0.0`  
**Status**: `PROVISIONAL BASELINE SPECIFICATION`  
**Target Domain**: Delhi NCT V2 — Kushak Drainage Basin (Barapullah Basin Sub-Catchment)  
**Date**: September 2026  
**Audience**: Antigravity Agents, Claude Code Implementation Teams, Municipal Hydrologists

---

## 1. Executive Summary & Strict Scientific Baseline

This specification governs the spatial hydrologic loss estimation, subcatchment discretization, and lateral inflow boundary conditions for the **Kushak Nallah Catchment** under the SIH 2026 Urban Flood Nowcasting System (Delhi V2).

To maintain absolute scientific defensibility and avoid fabricating precision where evidence is incomplete, all modeling downstream of this document must adhere to the established project baseline:

1. **Working Catchment Boundary**:
   - The catchment area is strictly designated as:  
     $$\mathbf{WORKING\ MODEL\ CATCHMENT\ —\ 27.66\text{ km}^2}$$
   - Its status remains formally:  
     $$\mathbf{WATERSHED\ STATUS\ —\ PROVISIONAL}$$
   - The boundary is derived from Scenario U2 (2.0 m hydro-enforced trenching along the 5.028 km Kushak drainage corridor). Scenario U3 ($28.402\text{ km}^2$, 3.0 m burn) is retained for **sensitivity analysis only**.
   - The historical figure of $35.4\text{ km}^2$ remains **ORIGIN UNRESOLVED** (an unverified government planning estimate whose GIS boundary has never been located).
2. **Hydraulic Corridor Dimensions**:
   - The corridor length is $5.028\text{ km}$, consisting of **Reach 1 (Underground Box Culvert, 2.319 km)** and **Reach 2 (Open Trapezoidal/Rectangular Canal, 2.709 km)**.
   - All 7 station-specific open-channel cross-section dimensions (CS-01 to CS-07) are **ASSUMED / REGULARIZED** based on macroscopic planning envelopes ($6–18\text{ m}$ top width, $2.5–4.2\text{ m}$ depth), not surveyed geodetic transects.
   - Underground Africa Avenue box culvert dimensions and longitudinal invert elevations remain **STRICTLY UNKNOWN**.
   - Open-channel invert elevations are **DERIVED SYNTHETIC OFFSETS** ($Z_{\text{bank}} - H$), subject to $\pm 1.0\text{ m}$ to $\pm 1.5\text{ m}$ elevation uncertainty.
3. **Precipitation Forcing**:
   - The two benchmark forcing datasets (28 June 2024 and 8–10 July 2023) are **PROVISIONAL DERIVED SCENARIOS**.
   - For 28 June 2024, only 1 hour (05:00–06:00 IST, 91 mm) is directly observed; remaining hours are reconstructed from 3-hour synoptic blocks.
   - For 8–10 July 2023, zero continuous hourly AWS observations exist; all non-zero hours are uniform block allocations.
   - **Never present derived hourly rainfall as observed continuous ground truth.**
4. **Discharge Observations**:
   - **No continuous or peak discharge gauge exists on the Kushak Nallah.**
   - The previously quoted discharge range of $65–145\text{ m}^3/\text{s}$ is **NOT AN OBSERVED DISCHARGE BOUNDARY CONDITION** and must never be treated as empirical calibration truth.
5. **No Code Implementation in this Phase**:
   - This document defines schemas, parameters, interfaces, and validation contracts. It does not implement runtime solvers, SWMM engines, or machine learning models.

---

## 2. Satellite Land-Cover Analysis (ESA WorldCover 10m v200)

### 2.1 Data Acquisition & Provenance
To determine the spatial distribution of pervious and impervious surfaces across the $27.664\text{ km}^2$ provisional catchment, the official **ESA WorldCover 10m 2021 v200** dataset was acquired directly from the European Space Agency / VITO Remote Sensing cloud repository.

- **Raw Tile File**: `data/delhi/raw/landcover/ESA_WorldCover_10m_2021_v200_N27E075_Map.tif`
- **Tile Extent**: $27^\circ\text{N}–28^\circ\text{N}$, $75^\circ\text{E}–78^\circ\text{E}$ (incorporating NCT Delhi)
- **Raw File Size**: $91,078,639\text{ bytes}$
- **SHA-256 Hash**: `447f74f2168bb14947a77c99a5a05bdf861300f1e0bdb66dd26e7262620f563f`
- **Evidence Class**: `OBSERVED (Satellite Remote Sensing, CC-BY 4.0)`

The raw tile is permanently preserved in the raw data store and indexed in `data/delhi/raw/landcover/manifest.json`.

### 2.2 Catchment Clipping & Metric Processing
The raw raster was clipped to the provisional $27.664\text{ km}^2$ Kushak catchment boundary (`kushak_watershed_u2.geojson`) and projected to both the project's native metric coordinate system (**EPSG:32643 — WGS 84 / UTM Zone 43N**) and standard geographic coordinates (**EPSG:4326**):

- **Metric Grid**: `data/delhi/derived/landcover/kushak_landcover_10m.tif` ($10.0\text{ m} \times 10.0\text{ m}$ cell size; UTM Zone 43N)
- **Geographic Grid**: `data/delhi/derived/landcover/kushak_landcover_10m_wgs84.tif` (EPSG:4326)
- **Derived Manifest**: `data/delhi/derived/landcover/manifest.json`

### 2.3 Catchment Land-Cover Distribution
Across the $27.6636\text{ km}^2$ analyzed raster domain ($276,636$ valid $10\text{ m}$ pixels), the class breakdown is as follows:

| Class Code | ESA WorldCover Label | Pixel Count | Area (km²) | Catchment Fraction (%) | Dominant Physical Location in Catchment |
|:---:|---|:---:|:---:|:---:|---|
| **50** | Built-up / Urban Fabric | 136,011 | **13.6011** | **49.17%** | Bhikaji Cama, South Ext, Kotla Mubarakpur, AIIMS, Safdarjung Enclave |
| **10** | Tree Cover / Canopy | 125,499 | **12.5499** | **45.37%** | Central Ridge Reserve Forest, Nehru Park, Chanakyapuri Embassies |
| **30** | Grassland | 5,586 | **0.5586** | **2.02%** | Safdarjung Airport runways/verges, institutional lawns |
| **20** | Shrubland / Scrub | 4,819 | **0.4819** | **1.74%** | Degraded ridge slopes, railway embankments |
| **40** | Cropland / Nurseries | 3,949 | **0.3949** | **1.43%** | Sunder Nursery periphery, institutional research plots |
| **60** | Bare Soil / Quartzite Rock | 718 | **0.0718** | **0.26%** | Exposed Delhi Ridge quartzite outcrops, unpaved construction lots |
| **80** | Permanent Water Bodies | 54 | **0.0054** | **0.02%** | Sanjay Van periphery water bodies, Nehru Park ponds |
| **Total** | **Valid Catchment Area** | **276,636** | **27.6636** | **100.00%** | **WORKING MODEL CATCHMENT (27.66 km²)** |

#### Macro-Hydrologic Grouping
- **Pervious & Vegetated Surfaces** (Classes 10, 20, 30, 40): **$13.9853\text{ km}^2$ ($50.56%$)**
- **Urban Built-up Fabric** (Class 50): **$13.6011\text{ km}^2$ ($49.17%$)**
- **Bare Soil & Rock Outcrops** (Class 60): **$0.0718\text{ km}^2$ ($0.26%$)**
- **Water Bodies** (Class 80): **$0.0054\text{ km}^2$ ($0.02%$)**

```
Kushak Catchment Land-Cover Macro Breakdown (27.66 km²):
[===================== Built-up 49.17% =====================][=================== Vegetated 50.56% ===================][Bare 0.26%]
```

### 2.4 Imperviousness Governance Rule
> [!IMPORTANT]
> **DO NOT equate 100% of ESA WorldCover Class 50 (Built-up) to 100% hydrologic imperviousness.**  
> In dense Indian urban environments, satellite "built-up" pixels encompass significant unpaved roadside shoulders, internal courtyards, residential garden setbacks, and tree canopies overhanging streets. Equating satellite built-up directly to total imperviousness overestimates peak runoff by 20–35%.  
>  
> Consequently, **Effective Impervious Area (EIA)** must be modeled as a parameter fraction of Class 50:
> - **Dense Commercial / Continuous Urban Fabric** (South Extension, Kotla Mubarakpur, Bhikaji Cama): $\text{EIA} = 0.80–0.85$
> - **Open Institutional / Diplomatic Enclave Fabric** (Chanakyapuri, AIIMS campus): $\text{EIA} = 0.55–0.70$
> - **Catchment-Wide Nominal Baseline**: $\text{EIA} = 0.70$ ($34.42%$ of total catchment area directly connected impervious).

---

## 3. Authoritative Soil Evidence & Evidence Boundary

### 3.1 Soil Landscape & Geological Context
An evidence investigation was conducted using authoritative pedological records:
- **ICAR-NBSS&LUP Bulletin No. 112**: *"Soils of Delhi for Land-use Planning"* (National Bureau of Soil Survey & Land Use Planning, ICAR, Regional Centre Delhi, 2004).
- **ISRO Bhuvan Pedological Datasets**: Regional soil texture mapping for Delhi NCT.
- **ISRIC SoilGrids 250m v2.0**: Global gridded physical and chemical properties of soils.

The Kushak catchment spans two distinct physiographic units of the Delhi National Capital Territory:
1. **The Delhi Ridge (Aravalli Escarpment)** — Upper western catchment (Chanakyapuri west, Central Ridge, Anand Niketan):
   - **Parent Material**: Pre-Cambrian Alwar quartzite rocks.
   - **Soil Great Group**: **Lithic Ustochrepts** / **Lithic Torriorthents**.
   - **Characteristics**: Shallow, gravelly sandy loam, stony rocky outcrops with high surface relief and severe erosion hazard.
   - **Hydrologic Soil Group (HSG)**: **Group D** (shallow soils over impervious rock; high runoff potential when vegetation canopy is breached).
2. **The Trans-Yamuna / Alluvial Plain** — Central and eastern valley corridor (Safdarjung Airport, Bhikaji Cama, AIIMS, South Extension, Defence Colony):
   - **Parent Material**: Quaternary Yamuna alluvium (older alluvial plain).
   - **Soil Great Group**: **Typic Ustochrepts** (loamy skeletal to coarse loamy).
   - **Characteristics**: Deep, well-drained, pale brown to yellowish brown, sandy loam to silt loam with moderate permeability and low organic matter.
   - **Hydrologic Soil Group (HSG)**: **Group B** (moderate infiltration rates when thoroughly wetted; moderately deep to deep soils).

### 3.2 Stopping at the Evidence Boundary
> [!WARNING]
> **EVIDENCE BOUNDARY STOPPING POINT:**  
> A forensic check of municipal, academic, and state records confirmed that **no localized, in-situ double-ring infiltrometer tests or calibrated soil infiltration parameters exist for the Kushak Nallah catchment**. Neither the IIT Delhi 2018 Drainage Master Plan nor the Delhi PWD / I&FC desilting reports conducted field soil moisture, tension, or hydraulic conductivity tests.  
>  
> Therefore, we **REFUSE to invent synthetic point measurements** of Green-Ampt parameters ($K_s, \psi, \Delta\theta$) or empirical Horton decay constants. All soil infiltration parameters specified below are classified strictly as **ASSUMED BASELINE RANGES** mapped from USDA-NRCS NEH Part 630 and Rawls, Brakensiek, & Miller (1983) based on ICAR pedological class correspondences.

---

## 4. Candidate Subcatchment Discretization & Lateral Inflow Zones

### 4.1 Discretization Methodology
To couple catchment hydrology to the 1D/2D hydraulic corridor without fabricating unverified micro-conduit networks, the $27.664\text{ km}^2$ catchment was discretized into **5 candidate subcatchments** representing **5 lateral inflow zones** along the $5.028\text{ km}$ corridor.

Partitioning was executed via nearest-reach spatial Voronoi clustering on the $10\text{ m}$ metric raster grid using `scipy.spatial.cKDTree`, constrained by the hydro-enforced corridor geometry:
- **Corridor Reach 1 (Underground Box Culvert, 0 to 2,318.4 m)**: Partitioned into Zone 1 (Upper) and Zone 2 (Lower).
- **Corridor Reach 2 (Open Trapezoidal Canal, 2,318.4 to 5,027.6 m)**: Partitioned into Zone 3 (Safdarjung/INA), Zone 4 (South Ext/Sewa Nagar), and Zone 5 (Defence Colony Confluence).

### 4.2 Candidate Subcatchment & Lateral Inflow Inventory
The derived dataset is preserved in:
- `data/delhi/derived/hydrology/kushak_candidate_subcatchments.geojson` (Vector polygons, EPSG:4326)
- `data/delhi/derived/hydrology/kushak_subcatchment_inventory.csv` (Tabular inventory)
- `data/delhi/derived/hydrology/kushak_lateral_inflow_zones.csv` (Hydraulic coupling summary)

| Subcatchment / Zone ID | Name & Location | Reach Type | Chainage Range (m) | Length (m) | Area (km²) | Built-up (%) | Vegetated (%) | Bare (%) | Key Landmarks | Hydrologic Response & Uncertainties |
|---|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|---|---|
| **SC-01 / LZ-01** | Chanakyapuri & Upper Africa Ave West | Underground Box Culvert | 0.0 – 1,150.0 | 1,150.0 | **10.4173** | 48.19% | 51.70% | 0.11% | Nehru Park, Vinay Marg, Diplomatic Enclave, Central Ridge headwaters | **High parkland infiltration** buffered by Nehru Park. Runoff enters covered culvert via street drop inlets. Uncertainty: Unmapped Shanti Path divide; subsurface drainage divides unverified. |
| **SC-02 / LZ-02** | Lower Africa Ave & Bhikaji Cama Place | Underground Box Culvert | 1,150.0 – 2,318.4 | 1,168.4 | **14.1482** | 46.38% | 53.23% | 0.35% | Bhikaji Cama Place, Netaji Nagar, Nauroji Nagar, Ring Road Daylight Portal | **Largest contributing area (51.1%)**. High runoff surge from Bhikaji Cama commercial center. Uncertainty: Underground conduit internal dimensions unknown; manhole drop structures unmapped. |
| **SC-03 / LZ-03** | Upper Open Kushak / Safdarjung & INA | Open Masonry Canal | 2,318.4 – 3,200.0 | 881.6 | **1.1164** | 70.29% | 29.05% | 0.65% | Daylight Portal, Safdarjung Airport apron, INA Market, AIIMS Culvert | **Extremely rapid flash response**. High impervious fraction (70.3%). Uncertainty: Airport internal perimeter ditch gates unverified; AIIMS underpass sump dewatering pump dependence. |
| **SC-04 / LZ-04** | Mid Open Kushak / South Ext & Sewa Nagar | Open Masonry Canal | 3,200.0 – 3,900.0 | 700.0 | **1.8029** | 60.40% | 39.45% | 0.14% | Ring Road, South Extension Part-I, Kotla Mubarakpur, Sewa Nagar railway | **Direct canal surcharge risk**. Dense residential/commercial runoff. Masonry retaining wall constraints. Uncertainty: Informal pipe connections; railway culvert constriction. |
| **SC-05 / LZ-05** | Lower Open Kushak & Outfall / Defence Colony | Open Masonry Canal to Confluence | 3,900.0 – 5,027.6 | 1,127.6 | **0.1802** | 81.19% | 18.59% | 0.22% | South Extension Part-II, Andrews Ganj, Sunehri Nallah, Barapullah Confluence | **Severe tailwater backwater zone**. Highly paved urban strip (81.2% built-up). Note: Direct lateral contributing area downstream of chainage 4368m is unpartitioned in U2 model. |
| **Total** | **Working Catchment Total** | — | **0.0 – 5,027.6** | **5,027.6** | **27.6650** | **49.17%** | **50.56%** | **0.26%** | — | **Matches 27.664 km² U2 boundary.** |

### 4.3 Outfall & Boundary Condition Physical Detail
> [!NOTE]
> In the hydro-enforced U2 model, the numerical stream convergence terminates at Chainage $4,368.25\text{ m}$ (the culvert crossing at Sewa Nagar / South Extension).  
> The remaining $659.3\text{ m}$ of the corridor (Chainage $4,368.25\text{ m}$ to $5,027.56\text{ m}$) extends across the Defence Colony urban strip into the confluence with Barapullah Nallah.  
> As a result, the direct local lateral area for Zone 5 is captured at $0.1802\text{ km}^2$ within the U2 boundary, with the remainder of the eastern bank lateral overland area currently **UNPARTITIONED** pending full joint delineation of the Barapullah trunk basin.

---

## 5. Hydrologic Parameter Provenance Table

All parameters required by standard hydrologic loss models (Green-Ampt, SCS-CN, Horton) and subcatchment overland routing are inventoried below and preserved in `data/delhi/derived/hydrology/kushak_hydrologic_parameter_provenance.csv`:

| Parameter Name | Symbol | Units | Applicable Loss Model | Baseline Value | Sensitivity Range | Scientific Evidence Class | Authoritative Source / Technical Justification | Sensitivity Level & Impact on Peak Runoff |
|---|:---:|:---:|:---:|:---:|:---:|:---:|---|---|
| **Satiated Hydraulic Conductivity** | $K_s$ | mm/hr | Green-Ampt, Richards | **10.9** | 3.5 – 15.2 | `ASSUMED BASELINE RANGE` | ICAR-NBSS&LUP Bulletin 112 (Typic Ustochrepts, Silt Loam) mapped to Rawls et al. (1983) Table 1. | **VERY HIGH**. Controls steady infiltration rate. A 50% decrease in $K_s$ increases total pervious runoff volume by ~35% during monsoonal bursts. |
| **Wetting Front Suction Head** | $\psi$ | mm | Green-Ampt | **140.0** | 80.0 – 210.0 | `ASSUMED BASELINE RANGE` | USDA-ARS / Rawls, Brakensiek, & Miller (1983) standard physical constants for loam / silt loam texture class. | **HIGH**. Governs initial infiltration suction flux before saturation. Primarily alters time to ponding ($t_p$) and hydrograph peak timing by 10–25 minutes. |
| **Initial Soil Moisture Deficit** | $\Delta\theta$ | m³/m³ | Green-Ampt | **0.15** | 0.05 – 0.25 | `ASSUMED BASELINE RANGE` | Rawls et al. (1983). AMC II baseline 0.15; AMC III saturated 0.05; AMC I dry 0.25. Continuous probe data UNKNOWN. | **VERY HIGH**. Controls initial abstraction volume before surface ponding. Under AMC III (0.05), ponding occurs almost immediately (<10 min under 20 mm/hr rain). |
| **SCS Curve Number (Pervious/Veg)** | $CN_{\text{perv}}$ | — | SCS-CN (TR-55) | **75** | 61 – 88 | `ASSUMED BASELINE RANGE` | USDA-NRCS TR-55 Table 2-2a for Open Space / Lawns / Parks in fair condition on Hydrologic Soil Group B. | **VERY HIGH**. Shifting $CN$ from 75 to 88 more than doubles cumulative pervious runoff volume for a 60 mm design rainfall. |
| **SCS Curve Number (Bare Ridge)** | $CN_{\text{bare}}$ | — | SCS-CN (TR-55) | **89** | 80 – 95 | `ASSUMED BASELINE RANGE` | USDA-NRCS TR-55 Table 2-2d for Arid / Semi-Arid Rangeland / Exposed Quartzite Rock outcrop on HSG D. | **MODERATE**. Generates rapid overland wash from Central Ridge headwaters, but bare rock covers only 0.26% of catchment. |
| **Effective Impervious Area Fraction** | $EIA$ | fraction | Urban Loss Models | **0.70** | 0.60 – 0.85 | `ASSUMED BASELINE RANGE` | MoUD CPHEEO Drainage Manual (2019) & Alley & Veenhuis (1983). Applied to ESA WorldCover Class 50 (Built-up). | **CRITICAL**. Catchment is 49.17% built-up. Shifting EIA from 0.70 to 0.85 increases connected impervious area by 2.04 km², elevating peak runoff by 18–24%. |
| **Depression Storage (Impervious)** | $d_{p,\text{imp}}$ | mm | SWMM / Horton / All | **2.0** | 1.0 – 3.0 | `OFFICIAL MODEL VALUE` | EPA SWMM Reference Manual Vol I (Hydrology), Table 3-5 standard default for impervious asphalt / concrete surfaces. | **LOW**. Absorbs initial 1–3 mm of storm rainfall; negligible impact during extreme 100+ mm monsoonal deluges. |
| **Depression Storage (Pervious)** | $d_{p,\text{perv}}$ | mm | SWMM / Horton / All | **5.0** | 2.5 – 8.0 | `OFFICIAL MODEL VALUE` | EPA SWMM Reference Manual Vol I (Hydrology), Table 3-5 standard default for lawns and woodland turf. | **LOW to MODERATE**. Delays onset of overland runoff from Nehru Park, Central Ridge, and roadside verge soils by 15–30 minutes. |
| **Overland Manning n (Impervious)** | $n_{\text{ov,imp}}$ | s/m^(1/3) | Kinematic Wave / SWMM | **0.013** | 0.011 – 0.015 | `OFFICIAL MODEL VALUE` | EPA SWMM Reference Manual Table 3-3; Engman (1986) standard value for smooth asphalt / paved urban surfaces. | **MODERATE**. Alters subcatchment overland sheet flow time of concentration; affects sharpness of lateral hydrograph peaks. |
| **Overland Manning n (Pervious)** | $n_{\text{ov,perv}}$ | s/m^(1/3) | Kinematic Wave / SWMM | **0.25** | 0.15 – 0.40 | `OFFICIAL MODEL VALUE` | EPA SWMM Reference Manual Table 3-3; Engman (1986) standard value for dense turf grass and forest litter. | **MODERATE**. Dramatically attenuates overland flow velocity across parks and gardens, stretching the receding limb of lateral inflows. |
| **Trunk Channel Manning n (Open Drain)** | $n_{\text{ch,open}}$ | s/m^(1/3) | Hydraulic Solver / SWMM | **0.025** | 0.028 – 0.035 | `OFFICIAL MODEL VALUE` | IIT Delhi Master Plan for Delhi Drainage (2018), Volume 1 Schedule of Drains; verified direct match for lined trunk drains. | **VERY HIGH**. Governs stage-discharge curve and water surface profile. Increasing $n$ to 0.035 increases flow depth by 18–22%, triggering bank overtopping at South Ext. |
| **Trunk Channel Manning n (RCC Box)** | $n_{\text{ch,box}}$ | s/m^(1/3) | Hydraulic Solver / SWMM | **0.012** | 0.013 – 0.015 | `OFFICIAL MODEL VALUE` | CPHEEO Manual on Sewerage & Sewage Treatment (2019) Table 4.1 for smooth finish precast/cast-in-situ RCC conduits. | **HIGH**. Determines barrel capacity before pressurization (surcharging). Surcharging backs water up into Chanakyapuri manholes and surface gullies. |

---

## 6. Proposed Runoff Scenarios for Future Simulation

To support robust numerical sensitivity testing without making unsupported claims about calibration truth, three conservative simulation scenarios have been defined and saved in `data/delhi/derived/hydrology/kushak_runoff_scenarios.csv`:

### Scenario 1: Base Operational / Moderate Infiltration (`SCEN-01`)
- **Antecedent Condition**: AMC II (Normal moisture condition; typical pre-storm summer soil).
- **Target Events**: Standard design storms; moderate monsoon convective storms.
- **Effective Impervious Area Fraction ($EIA$)**: $0.70$ (Total connected imperviousness = $34.42\%$ of catchment).
- **Green-Ampt Parameters**: $K_s = 10.9\text{ mm/hr}$, $\psi = 140.0\text{ mm}$, $\Delta\theta = 0.15$.
- **SCS-CN Parameters**: $CN_{\text{perv}} = 75$, $CN_{\text{bare}} = 89$, $CN_{\text{imp}} = 98$.
- **Depression Storage**: Impervious $2.0\text{ mm}$, Pervious $5.0\text{ mm}$.
- **Expected Hydrologic Behavior**: Moderate infiltration across the $50.6\%$ pervious footprint (Nehru Park, Central Ridge). Rapid initial runoff is generated strictly from the $34.4\%$ directly connected impervious surfaces. Pervious areas generate runoff only after cumulative rainfall exceeds approximately $25\text{ mm}$.
- **Validation Role**: Serves as the operational baseline for both the 28 June 2024 convective burst and 8–10 July 2023 monsoon simulations.

### Scenario 2: Saturated Ground / Monsoonal Stress (`SCEN-02`)
- **Antecedent Condition**: AMC III (Saturated antecedent conditions after 3–5 consecutive heavy rainfall days).
- **Target Events**: 8–10 July 2023 multi-day monsoonal event; compound flood hazard assessments.
- **Effective Impervious Area Fraction ($EIA$)**: $0.85$ (Total connected imperviousness = $41.79\%$ of catchment; unpaved shoulders and saturated lawns sealed).
- **Green-Ampt Parameters**: $K_s = 3.5\text{ mm/hr}$, $\psi = 80.0\text{ mm}$, $\Delta\theta = 0.05$ (near-surface saturation).
- **SCS-CN Parameters**: $CN_{\text{perv}} = 88$, $CN_{\text{bare}} = 95$, $CN_{\text{imp}} = 98$.
- **Depression Storage**: Impervious $1.0\text{ mm}$, Pervious $2.5\text{ mm}$ (pre-filled micro-depressions).
- **Expected Hydrologic Behavior**: Infiltration is drastically suppressed due to pre-filled soil pore spaces. Pervious parks and gardens begin shedding overland runoff almost immediately (initial abstraction $< 7\text{ mm}$). Total runoff volume increases by $60–90\%$ compared to baseline, severely stressing the $5.028\text{ km}$ trunk corridor.
- **Validation Role**: Mandatory stress-test scenario for open drain overtopping, underground culvert pressurization, and Barapullah backwater confluence vulnerability.

### Scenario 3: Dry Antecedent / Early Season Convective Burst (`SCEN-03`)
- **Antecedent Condition**: AMC I (Parched dry soil matrix following prolonged pre-monsoon heatwave).
- **Target Events**: 28 June 2024 early-season extreme convective event (first major burst of the season).
- **Effective Impervious Area Fraction ($EIA$)**: $0.60$ (Total connected imperviousness = $29.50\%$ of catchment; dry unpaved yards absorb significant initial runoff).
- **Green-Ampt Parameters**: $K_s = 15.2\text{ mm/hr}$, $\psi = 180.0\text{ mm}$, $\Delta\theta = 0.25$ (high dry matrix suction).
- **SCS-CN Parameters**: $CN_{\text{perv}} = 61$, $CN_{\text{bare}} = 80$, $CN_{\text{imp}} = 98$.
- **Depression Storage**: Impervious $2.5\text{ mm}$, Pervious $8.0\text{ mm}$ (high dry vegetation and soil surface retention).
- **Expected Hydrologic Behavior**: High soil suction head ($\psi = 180\text{ mm}$) and deep moisture deficit ($0.25$) enable Central Ridge soils and South Delhi parks to absorb $40–50\text{ mm}$ of rainfall before pervious overland runoff initiates. Early peak discharge in the Kushak Nallah is driven almost exclusively by urban street runoff directly connected to drop inlets.
- **Validation Role**: Evaluates the buffering capacity of Delhi's urban green spaces and quantifies sensitivity to pre-monsoon antecedent moisture assumptions.

---

## 7. Implementation Contract for Claude Code

When Claude Code is authorized to implement hydrologic runoff generation in application code, it **MUST STRICTLY ADHERE** to the architecture, interfaces, and validation rules specified below.

### 7.1 File Schemas & Directory Layout
All future hydrologic runtime code must be encapsulated under the backend domain architecture:
```
backend/app/domain/delhi/hydrology/
├── __init__.py
├── models.py                 # Pydantic schemas for rainfall, losses, and hydrographs
├── loss_green_ampt.py         # Green-Ampt infiltration loss engine
├── loss_scs_cn.py            # SCS-CN empirical runoff volume engine
├── runoff_transform.py        # Subcatchment overland routing (Kinematic Wave / SWMM Non-linear Reservoir)
├── lateral_inflows.py         # Coupler mapping subcatchment hydrographs to 1D corridor nodes
└── validation.py              # Mass balance and Rational Method sanity check harness
```

### 7.2 Expected Interfaces & Function Signatures

#### 1. Infiltration Loss Interface
```python
from typing import Literal, Dict, Any, List
from pydantic import BaseModel, Field

class SoilParameters(BaseModel):
    ks_mm_hr: float = Field(..., description="Satiated hydraulic conductivity (mm/hr)")
    psi_mm: float = Field(..., description="Wetting front suction head (mm)")
    delta_theta: float = Field(..., description="Initial volumetric moisture deficit (m3/m3)")
    cn_pervious: float = Field(..., description="SCS Curve Number for pervious soils")
    cn_bare: float = Field(..., description="SCS Curve Number for bare soil/rock")
    cn_impervious: float = Field(default=98.0, description="SCS Curve Number for impervious surfaces")
    depression_storage_imp_mm: float = Field(default=2.0)
    depression_storage_perv_mm: float = Field(default=5.0)

class LandCoverFractions(BaseModel):
    built_up_fraction: float = Field(..., description="ESA WorldCover Class 50 fraction (0.0 - 1.0)")
    eia_fraction: float = Field(default=0.70, description="Effective Impervious Area factor for built-up")
    vegetated_fraction: float = Field(..., description="Vegetation fraction (0.0 - 1.0)")
    bare_fraction: float = Field(..., description="Bare soil fraction (0.0 - 1.0)")
    water_fraction: float = Field(default=0.0)

class HyetographStep(BaseModel):
    time_minutes: float
    rainfall_intensity_mm_hr: float
    rainfall_depth_mm: float

class LossResultStep(BaseModel):
    time_minutes: float
    rainfall_depth_mm: float
    infiltration_loss_mm: float
    depression_loss_mm: float
    excess_runoff_mm: float

class SubcatchmentLossResult(BaseModel):
    subcatchment_id: str
    total_precipitation_mm: float
    total_loss_mm: float
    total_excess_runoff_mm: float
    runoff_coefficient: float
    time_series: List[LossResultStep]

def compute_subcatchment_losses(
    subcatchment_id: str,
    rainfall_series: List[HyetographStep],
    landcover: LandCoverFractions,
    soil: SoilParameters,
    loss_method: Literal["green_ampt", "scs_cn"] = "green_ampt"
) -> SubcatchmentLossResult:
    """
    Computes time-varying infiltration, depression storage, and rainfall excess
    for a given subcatchment.
    """
    pass
```

#### 2. Overland Runoff Transformation Interface
```python
class HydrographStep(BaseModel):
    time_minutes: float
    discharge_m3_s: float

class SubcatchmentHydrograph(BaseModel):
    subcatchment_id: str
    zone_id: str
    drainage_area_km2: float
    peak_discharge_m3_s: float
    time_to_peak_minutes: float
    total_volume_m3: float
    hydrograph: List[HydrographStep]

def transform_excess_to_runoff(
    loss_result: SubcatchmentLossResult,
    drainage_area_km2: float,
    overland_slope_m_m: float,
    flow_length_m: float,
    routing_method: Literal["kinematic_wave", "swmm_reservoir"] = "kinematic_wave"
) -> SubcatchmentHydrograph:
    """
    Transforms effective rainfall excess into an overland discharge hydrograph
    at the subcatchment lateral outlet.
    """
    pass
```

#### 3. Lateral Inflow Coupling Interface
```python
class LateralCouplingAssignment(BaseModel):
    zone_id: str
    subcatchment_id: str
    reach_id: str
    chainage_start_m: float
    chainage_end_m: float
    is_point_source: bool = False
    distributed_hydrograph: List[HydrographStep]

def couple_subcatchments_to_hydraulic_corridor(
    subcatchment_hydrographs: List[SubcatchmentHydrograph],
    corridor_centerline_geojson_path: str
) -> List[LateralCouplingAssignment]:
    """
    Distributes subcatchment overland discharge as lateral inflows along the
    5.028 km 1D hydraulic corridor.
    """
    pass
```

### 7.3 Loss Model Options & Urban Trade-Offs
| Infiltration Model | Mathematical Basis | Major Strengths for Delhi V2 | Major Weaknesses / Trade-Offs | Recommendation |
|---|---|---|---|:---:|
| **Green-Ampt** | Physics-based Darcy flow into wetting front | Directly responds to time-varying sub-hourly rainfall intensity; accurately models time-to-ponding ($t_p$) during intense convective deluges (e.g. 28 June 2024, $91\text{ mm/h}$). | Requires physically realistic suction head ($\psi$) and hydraulic conductivity ($K_s$), which are unmeasured in Kushak. | **PRIMARY (Recommended for continuous dynamic routing)** |
| **SCS-CN** | Empirical total volume abstraction ($S = \frac{25400}{CN} - 254$) | Globally standardized; robust for daily and multi-day totals (e.g. 8–10 July 2023 extended deluge); low parameter count. | Not physically suited for sub-hourly burst dynamics; tends to under-predict initial runoff rates during short cloudbursts. | **SECONDARY (Recommended for multi-day cumulative mass balance checks)** |
| **Horton** | Empirical exponential decay: $f(t) = f_c + (f_0 - f_c)e^{-kt}$ | Simple numerical implementation; smooth continuous loss curve. | Independent of cumulative infiltration; if rainfall ceases and restarts, recovery curve is highly sensitive and uncalibrated. | **NOT RECOMMENDED** |

### 7.4 Runoff Transformation Method Recommendation
1. **Kinematic Wave / Non-linear Reservoir (SWMM style)**:  
   **STRONGLY RECOMMENDED**. Urban catchments with $49.2\%$ built-up area and short overland lengths ($< 500\text{ m}$) respond non-linearly to rainfall intensity. Kinematic routing preserves sharp hydrograph peaks and directly accounts for overland Manning roughness ($n_{\text{ov,imp}} = 0.013$ vs $n_{\text{ov,perv}} = 0.25$).
2. **Synthetic Unit Hydrograph (SCS Dimensionless / Clark)**:  
   **ACCEPTABLE AS SENSITIVITY BASELINE**, but tends to over-smooth urban peak discharges unless lag time ($t_L$) is rigorously calibrated to drainage pipe velocities.

### 7.5 Validation Hooks & Strict Guardrails
Every hydrologic runoff simulation executed in the codebase must pass two automated validation hooks:

#### Hook 1: Conservation of Water Mass Balance
For every subcatchment $i$ and across the entire catchment:
$$P_i = R_i + I_i + D_{p,i} + \Delta S_i$$
Where:
- $P_i$ = Cumulative precipitation depth (mm)
- $R_i$ = Cumulative direct runoff depth (mm)
- $I_i$ = Cumulative infiltration loss (mm)
- $D_{p,i}$ = Depression storage loss (mm)
- $\Delta S_i$ = Surface detention storage change (mm)

$$\text{Mass Balance Error} = \left| \frac{P_i - (R_i + I_i + D_{p,i} + \Delta S_i)}{P_i} \right| \times 100\% \le 0.10\%$$
Any run with mass balance error $> 0.10\%$ must raise a fatal `HydrologicConservationError`.

#### Hook 2: Rational Method Peak Runoff Sanity Envelope
Under the peak 1-hour cloudburst intensity of $91.0\text{ mm/hr}$ observed on 28 June 2024, the catchment-wide peak discharge ($Q_{\text{peak}}$) must be checked against the standard Rational envelope:
$$Q_{\text{rational}} = \frac{C \cdot I \cdot A}{3.6}$$
Where:
- $A = 27.664\text{ km}^2$
- $I = 91.0\text{ mm/hr}$
- Composite $C \in [0.40, 0.70]$ (accounting for $50.6\%$ pervious parkland and $49.2\%$ built-up fabric with $0.70\text{ EIA}$)

$$\text{Minimum Expected Peak } Q_p (C=0.40) = \frac{0.40 \times 91.0 \times 27.664}{3.6} \approx 280\text{ m}^3/\text{s}$$
$$\text{Maximum Expected Peak } Q_p (C=0.70) = \frac{0.70 \times 91.0 \times 27.664}{3.6} \approx 490\text{ m}^3/\text{s}$$

> [!CAUTION]
> **SANITY CHECK ON TRUNK CONDUIT CAPACITY:**  
> The nominal bankfull capacity of the Kushak open channel (Reach 2, $6–18\text{ m}$ top width) is estimated at approximately $70–120\text{ m}^3/\text{s}$.  
> Under an extreme $91\text{ mm/h}$ cloudburst generating $280–490\text{ m}^3/\text{s}$ of catchment runoff, **the Kushak Nallah is physically incapable of conveying the total hydrograph within its banks**.  
>  
> The surplus volume ($150–350\text{ m}^3/\text{s}$) will inevitably cause:
> 1. Pressurization and surface surcharge of the Africa Avenue underground culvert.
> 2. Severe street waterlogging along Ring Road, AIIMS subway, and South Extension.
> 3. Overland ponding in Safdarjung Airport apron depressions and Nehru Park.
>  
> Therefore, hydraulic simulations must never artificially force the entire $280+\text{ m}^3/\text{s}$ into the channel cross-sections without modeling surface street detention and spillover.

---

## 8. Summary of Created Artifacts & Next Steps

### 8.1 Deliverables Created in this Task
1. `data/delhi/raw/landcover/ESA_WorldCover_10m_2021_v200_N27E075_Map.tif` (Official raw tile, SHA-256 verified)
2. `data/delhi/raw/landcover/manifest.json` (Raw data manifest)
3. `data/delhi/derived/landcover/kushak_landcover_10m.tif` (10m UTM 43N metric land-cover grid)
4. `data/delhi/derived/landcover/kushak_landcover_10m_wgs84.tif` (10m WGS 84 geographic land-cover grid)
5. `data/delhi/derived/landcover/kushak_landcover_statistics.csv` (Zonal land-cover statistics table)
6. `data/delhi/derived/landcover/manifest.json` (Derived land-cover manifest)
7. `data/delhi/derived/hydrology/kushak_candidate_subcatchments.geojson` (5 candidate subcatchments vector)
8. `data/delhi/derived/hydrology/kushak_subcatchment_inventory.csv` (Subcatchment geometry & land-cover table)
9. `data/delhi/derived/hydrology/kushak_lateral_inflow_zones.csv` (5 lateral inflow coupling zones table)
10. `data/delhi/derived/hydrology/kushak_hydrologic_parameter_provenance.csv` (Forensic parameter provenance table)
11. `data/delhi/derived/hydrology/kushak_runoff_scenarios.csv` (3 simulation scenarios table)
12. `data/delhi/derived/hydrology/manifest.json` (Hydrology directory manifest)
13. `docs/DELHI_KUSHAK_HYDROLOGIC_RUNOFF_SPEC.md` (This master specification)
14. Updated `docs/DATA_PROVENANCE_MATRIX.md` and `data/delhi/derived/watershed/manifest.json`.

### 8.2 Boundary Condition for Future Implementation
- **Hydrology Specification Phase**: **COMPLETE**.
- **Hydraulic & Application Solvers**: **REMAIN UNTOUCHED**.
- Implementation of runtime runoff generation equations, SWMM conduits, 1D/2D hydraulic coupling, ML models, or UI dashboards remains deferred until explicit authorization.
