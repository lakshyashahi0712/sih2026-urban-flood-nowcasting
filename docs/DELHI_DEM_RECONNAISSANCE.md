# Delhi V2 Terrain & Digital Elevation Model (DEM) Reconnaissance

## 1. Overview & Evaluation Mandate

Accurate urban hydrodynamic modeling requires a high-fidelity digital representation of terrain gradients. Street gutters, road crowns, railway embankments, and depressed underpasses dictate overland flow pathways. In flat alluvial plains like Delhi ($200\text{ m} - 260\text{ m}$ MSL), a vertical error of $1\text{ to }2\text{ meters}$ can falsely redirect entire sub-catchment runoff volumes.

**Scientific Integrity Principles**:
- Never resample a 30 m DEM to 10 m or 5 m and present it as high-resolution terrain.
- Never claim a high-resolution dataset is available unless public, unencumbered download has been verified.
- Explicitly distinguish Digital Surface Models (DSM, including canopy/buildings) from bare-earth Digital Terrain Models (DTM).

---

## 2. Comprehensive Candidate Terrain Records

### Candidate 1: Government Airborne / Drone LiDAR DTM
- **Source Organization**: Survey of India (SoI) / National High-Speed Rail Corporation (NHSRCL) / National Hydrology Project (NHP).
- **Exact Dataset / Product**: Project-specific Airborne LiDAR Ground DTM (Delhi-Varanasi HSR corridor & Yamuna Floodplain NHP pilot).
- **Spatial Resolution / Posting**: Sub-meter ($0.5\text{ m} - 1.0\text{ m}$).
- **Surface Representation**: DTM (bare-earth ground points filtered with classification algorithms).
- **Vertical Accuracy**: $\le 15\text{ cm}$ RMSE.
- **Horizontal Accuracy**: $\le 25\text{ cm}$ RMSE.
- **CRS / Geodetic Reference**: WGS 84 / UTM Zone 43N (EPSG:32643) or Everest 1956 / Polyconic.
- **Vertical Datum**: Mean Sea Level (MSL), Great Trigonometrical Survey (GTS) of India.
- **Spatial Coverage**: Linear infrastructure corridors (rail alignment, Yamuna active flood zone); NOT contiguous city-wide or catchment-wide.
- **File Format**: LAS / LAZ point clouds or GeoTIFF bare-earth DEM.
- **Access Method**: Restricted departmental repository. Access requires institutional clearance under the National Geospatial Policy (2022) / Ministry of Jal Shakti.
- **License / Use Restrictions**: Government internal / project-restricted. Not licensed for open public software redistribution.
- **Can our project legitimately obtain/use it?**: **NO**. We do not possess an active institutional MoU or classified clearance for this data.
- **Can data actually be downloaded?**: **NO**. Not publicly downloadable.
- **Suitability for Urban Flood Modeling**: Ideal hydro-accuracy, but disqualified due to lack of open availability and fragmented spatial coverage.

---

### Candidate 2: ISRO / NRSC CartoDEM 10 m
- **Source Organization**: National Remote Sensing Centre (NRSC), Indian Space Research Organisation (ISRO).
- **Exact Dataset / Product**: CartoDEM Version-3 (10 m posting) derived from Cartosat-1 (IRS-P5) along-track stereoscopic fore-aft ($+26^\circ, -5^\circ$) high-resolution optical cameras ($2.5\text{ m}$ panchromatic).
- **Spatial Resolution / Posting**: 10 meters ($0.33\text{ arc-second}$).
- **Surface Representation**: DSM (Digital Surface Model; includes top of buildings and tree canopy).
- **Vertical Accuracy**: Documented RMSE $\sim 3\text{ to }4\text{ meters}$ across urban terrain.
- **Horizontal Accuracy**: $\le 8\text{ meters}$ with ground control points (GCPs).
- **CRS / Geodetic Reference**: Geographic WGS 84 (EPSG:4326) or UTM Zone 43N.
- **Vertical Datum**: WGS 84 ellipsoidal height or EGM96 geoid.
- **Spatial Coverage**: India-wide coverage in $1^\circ \times 1^\circ$ or $7.5' \times 7.5'$ tiles.
- **File Format**: GeoTIFF (16-bit signed integer or 32-bit floating point).
- **Access Method**: Bhuvan Geoportal (`bhuvan.nrsc.gov.in`).
- **License / Use Restrictions**: Restricted by Remote Sensing Data Policy (RSDP) and Geospatial Data Guidelines. While Bhuvan Open Data Archive (NOEDA) provides **CartoDEM 30 m (1 arc-second) Version 3 R1** for free registered public download, **the 10 m posting is classified as restricted high-resolution data** requiring formal institutional justification, government vetting, and payment/MOU.
- **Can our project legitimately obtain/use it?**: **NO** for immediate unencumbered open-source development.
- **Can data actually be downloaded?**: **NO**. Verified that Bhuvan public NOEDA download provides 30 m tiles only; 10 m tiles are blocked from public direct download.
- **Suitability for Urban Flood Modeling**: High potential resolution, but being an optical stereo DSM, it suffers from severe building roof elevation artifacts in dense Delhi urban clusters (Old Delhi, Paharganj, Lajpat Nagar), and is legally unobtainable for open deployment.

---

### Candidate 3: Copernicus DEM GLO-30 (RECOMMENDED BASELINE)
- **Source Organization**: European Space Agency (ESA) & European Union Copernicus Programme (in partnership with Airbus Defence and Space and DLR).
- **Exact Dataset / Product**: Copernicus DEM Global 30m (COP-DEM_GLO-30-DGED / COP-DEM_GLO-30-COG).
- **Spatial Resolution / Posting**: 1.0 arc-second ($\approx 30\text{ m}$ at equator, $\approx 26.3\text{ m}$ east-west posting at Delhi's latitude $28.6^\circ\text{N}$).
- **Surface Representation**: DSM (Digital Surface Model) derived from WorldDEM / TanDEM-X radar interferometry (X-band SAR, 2010–2015), with extensive water-body flattening, coastline editing, and morphological void-filling.
- **Vertical Accuracy**: Absolute vertical accuracy $< 4.0\text{ m}$ (documented LE90 of $1.68\text{ m}$ globally, vastly outperforming SRTM and ASTER).
- **Horizontal Accuracy**: Absolute horizontal circular error $< 6.0\text{ m}$ (CE90).
- **CRS / Geodetic Reference**: WGS 84 Geographic (EPSG:4326), reprojected internally to WGS 84 / UTM Zone 43N (EPSG:32643).
- **Vertical Datum**: EGM2008 Geoid (Earth Gravitational Model 2008).
- **Spatial Coverage**: Contiguous 100% coverage of Delhi NCT and surrounding NCR basins.
  - Primary tile: `Copernicus_DSM_COG_10_N28_00_E077_00_DEM.tif` (covering $28^\circ\text{N} - 29^\circ\text{N}$, $77^\circ\text{E} - 78^\circ\text{E}$).
  - Western tile (if buffer extends west of $77^\circ\text{E}$): `Copernicus_DSM_COG_10_N28_00_E076_00_DEM.tif`.
- **File Format**: Cloud-Optimized GeoTIFF (COG), 32-bit floating point.
- **Access Method**: Free and open download via public AWS S3 bucket (`s3://copernicus-dem-30m/`), Microsoft Planetary Computer, or Copernicus Data Space Ecosystem (CDSE).
- **License / Use Restrictions**: Free, full, and open access under the Copernicus Open Access Policy. Worldwide commercial and scientific use permitted with attribution.
- **Can our project legitimately obtain/use it?**: **YES**. Fully open and legally compliant.
- **Can data actually be downloaded?**: **YES**. Verified active open download without authentication gates.
- **Suitability for Urban Flood Modeling**: **Highest among all legitimately obtainable open datasets**. Provides smooth, hydro-enforced regional slopes. While micro-scale curbs ($\sim 15\text{ cm}$) are not resolved at 30 m, trunk drainage gradients, macro-depressions, and ridge-to-river slope lines are reliably represented.

---

### Candidate 4: JAXA ALOS World 3D - 30m (AW3D30)
- **Source Organization**: Japan Aerospace Exploration Agency (JAXA).
- **Exact Dataset / Product**: ALOS World 3D - 30m (AW3D30) Version 3.2.
- **Spatial Resolution / Posting**: 1.0 arc-second ($\approx 30\text{ m}$).
- **Surface Representation**: DSM generated from PRISM optical stereo pairs on the ALOS satellite (2006–2011).
- **Vertical Accuracy**: Documented RMSE $\sim 4.4\text{ m}$ (PRISM height error target $5\text{ m}$).
- **Horizontal Accuracy**: $\le 5\text{ m}$.
- **CRS / Geodetic Reference**: WGS 84 (EPSG:4326).
- **Vertical Datum**: EGM96 Geoid.
- **Spatial Coverage**: Global coverage, tile `N028E077`.
- **File Format**: GeoTIFF.
- **Access Method**: JAXA Earth Observation Research Center (EORC) portal.
- **License / Use Restrictions**: Free for non-commercial and research use upon registration.
- **Can our project legitimately obtain/use it?**: **YES**.
- **Can data actually be downloaded?**: **YES**.
- **Suitability for Urban Flood Modeling**: Fair, but inferior to Copernicus GLO-30. Optical stereo matching in dense urban cores creates notable cloud, shadow, and building-height noise (steep spurious spikes) compared to radar interferometry.

---

### Candidate 5: NASA / USGS SRTM 30 m (1 Arc-Second Global)
- **Source Organization**: NASA / USGS / NGA.
- **Exact Dataset / Product**: Shuttle Radar Topography Mission (SRTM) GL1 Version 3.0 (Void Filled).
- **Spatial Resolution / Posting**: 1.0 arc-second ($\approx 30\text{ m}$).
- **Surface Representation**: C-band InSAR DSM (acquired February 2000).
- **Vertical Accuracy**: Documented LE90 $\sim 6.2\text{ m}$ across Eurasia.
- **Horizontal Accuracy**: $\le 20\text{ m}$ CE90.
- **CRS / Geodetic Reference**: WGS 84 (EPSG:4326).
- **Vertical Datum**: EGM96 Geoid.
- **Spatial Coverage**: Contiguous coverage of Delhi.
- **File Format**: GeoTIFF or HGT.
- **Access Method**: USGS EarthExplorer / LP DAAC.
- **License / Use Restrictions**: Public domain.
- **Can our project legitimately obtain/use it?**: **YES**.
- **Can data actually be downloaded?**: **YES**.
- **Suitability for Urban Flood Modeling**: Poor compared to Copernicus GLO-30. Acquired in 2000, it predates major Delhi infrastructure (Delhi Metro viaducts, Barapullah Elevated Corridor, new embankments, modern expressways) and has higher radar speckle noise.

---

## 3. Systematic Dataset Comparison

| Evaluation Criterion | Candidate 1: Airborne LiDAR | Candidate 2: CartoDEM 10 m | Candidate 3: Copernicus GLO-30 | Candidate 4: ALOS AW3D30 | Candidate 5: SRTM 30 m |
|---|---|---|---|---|---|
| **True Spatial Posting** | $0.5\text{ m} - 1.0\text{ m}$ | 10.0 m | 30.0 m (~26.3 m) | 30.0 m | 30.0 m |
| **Model Type** | Bare-Earth DTM | Optical Stereo DSM | Radar InSAR DSM | Optical Stereo DSM | Radar InSAR DSM |
| **Acquisition Era** | 2018–2022 (fragmented) | 2005–2014 | 2011–2015 | 2006–2011 | February 2000 |
| **Vertical RMSE** | **$< 0.15\text{ m}$** | $\sim 3.5\text{ m}$ | **$\sim 1.7\text{ m}$** | $\sim 4.4\text{ m}$ | $\sim 6.2\text{ m}$ |
| **Vertical Datum** | GTS MSL | WGS84 / EGM96 | EGM2008 | EGM96 | EGM96 |
| **City-wide Contiguity** | No (strips only) | Yes | Yes | Yes | Yes |
| **Public Downloadability** | **Blocked / Restricted** | **Blocked / Restricted** | **Verified Open / Free** | Verified Open | Verified Open |
| **Licensing Barrier** | High (Govt Classified) | High (Institutional MOU) | **None (Open Policy)** | Low (User Registration) | None (Public Domain) |
| **Hydro-Enforced Water?** | Project-dependent | No | **Yes (Standard)** | Partial | Void-filled only |
| **Overall Recommendation** | Disqualified (Inaccessible) | Disqualified (Inaccessible) | **PRIMARY BASELINE** | Secondary Backup | Obsolete Baseline |

---

## 4. Technical Conclusion & Implementation Directive

1. **Definitive Decision**: **Copernicus GLO-30 DSM** (`Copernicus_DSM_COG_10_N28_00_E077_00_DEM.tif`) is the **sole authoritative, verified, and legitimate terrain dataset** available for the Delhi V2 hydrodynamic model.
2. **Strict Resolution Protocol**: The grid resolution must be handled at its genuine native resolution ($\approx 30\text{ m}$ or reprojected to $30.0\text{ m}$ UTM grid). Under no circumstances will the raster be bilinearly resampled to $10\text{ m}$ or $5\text{ m}$ and presented as high-resolution terrain.
3. **Hydro-Conditioning Requirement**: Because Copernicus GLO-30 is a DSM, elevated roads, railway bridges, and flyovers (e.g., Barapullah elevated road piers, Ring Road embankments) create artificial digital dams across natural nallahs. The `RasterEngine` must apply priority-flood depression breach-routing to carve culverts through artificial embankments where known drain centerlines cross transportation corridors.


---

## 5. Acquired Dataset Verification & Audit Record (Delhi V2 Production DEM)

### 5.1 Dataset Acquisition Summary
The official **Copernicus DEM Global 30m (GLO-30)** product covering the National Capital Territory of Delhi and the candidate Kushak Nallah study area has been acquired, hashed, verified, and archived in the Delhi V2 data repository.

| Attribute | Verified Value / Specification | Provenance Authority |
|---|---|---|
| **Product Name** | Copernicus DEM Global 30m (COP-DEM_GLO-30-COG) | European Space Agency (ESA) & Airbus Defence and Space |
| **Tile Identifier** | `Copernicus_DSM_COG_10_N28_00_E077_00` | Official Copernicus Tile Grid System |
| **Originating Authority** | ESA Copernicus Programme / Airbus Defence and Space GmbH / DLR | ISO 19115 XML Metadata (`Copernicus_DSM_10_N28_00_E077_00.xml`) |
| **Official Source URL** | `https://copernicus-dem-30m.s3.amazonaws.com/Copernicus_DSM_COG_10_N28_00_E077_00_DEM/Copernicus_DSM_COG_10_N28_00_E077_00_DEM.tif` | Registry of Open Data on AWS (`s3://copernicus-dem-30m/`) |
| **Metadata Source URL** | `https://copernicus-dem-30m.s3.amazonaws.com/Copernicus_DSM_COG_10_N28_00_E077_00_DEM/Copernicus_DSM_10_N28_00_E077_00.xml` | Registry of Open Data on AWS |
| **Release / Edition Date** | Analysis: 2018-03-26; Product Edition: 2019-10-18; AWS Distribution: 2022-05-09 | Official XML Metadata Timestamp |
| **Download Timestamp** | September 8, 2026 | Local Acquisition System |
| **Local Storage Path** | `data/delhi/raw/dem/Copernicus_DSM_COG_10_N28_00_E077_00_DEM.tif` | Delhi V2 Raw Data Repository |
| **Local XML Path** | `data/delhi/raw/dem/Copernicus_DSM_10_N28_00_E077_00.xml` | Delhi V2 Raw Data Repository |
| **Local Manifest Path** | `data/delhi/raw/dem/manifest.json` | Delhi V2 Raw Data Repository |
| **File Format** | Cloud-Optimized GeoTIFF (COG), 32-bit floating point (`float32`), single-band | Deflate compression, tiled $1024 \times 1024$ |
| **File Size (Raster)** | **$41,680,243\text{ bytes}$** ($39.75\text{ MiB}$) | Bit-level filesystem audit |
| **File Size (XML)** | **$44,698\text{ bytes}$** ($43.65\text{ KiB}$) | Bit-level filesystem audit |
| **SHA-256 (Raster)** | `a8e69d432869bf85a63b7cfcaa61b5a770c7705125b3cfde9b892d65dfed98b4` | Cryptographic SHA-256 Verification |
| **SHA-256 (XML)** | `2beab12cde235f08c08c3cb5acf5238c3ff99ae2963de95d3379df4f45daafa2` | Cryptographic SHA-256 Verification |
| **License / Terms** | Copernicus Open Access Policy / Free Worldwide Open Data | Airbus EULA (`INFO/eula_F.pdf`) |
| **Git Tracking Policy** | Excluded from version control via `.gitignore` (`/data/`) | Project Data Governance Standard |

---

### 5.2 Technical Metadata & Geodetic Parameters

* **Horizontal Coordinate Reference System (CRS)**:
  * Projection: Geographic 2D (Latitude / Longitude)
  * EPSG Code: `EPSG:4326`
  * Geodetic Datum: `WGS84-G1150` (World Geodetic System 1984, realization G1150)
  * Ellipsoid: WGS 84 ($a = 6378137.0\text{ m}, 1/f = 298.257223563$)
  * Horizontal Units: Decimal degrees ($^\circ$)
* **Vertical Coordinate Reference System**:
  * Vertical Datum: **EGM2008 Geoid** (Earth Gravitational Model 2008)
  * Vertical Units: Meters ($\text{m}$)
  * Vertical Spacing / Quantization: $0.1\text{ m}$
* **Spatial Resolution & Dimensions**:
  * Grid Dimensions: **$3600\text{ columns} \times 3600\text{ rows}$** ($12,960,000\text{ total pixels}$)
  * Native Angular Pixel Spacing: $0.0002777777777777778^\circ = 1.0\text{ arc-second}$
  * Native Metric Posting at Delhi Latitude ($28.6^\circ\text{N}$):
    * North-South: $1'' \approx 30.87\text{ m}$
    * East-West: $1'' \times \cos(28.6^\circ) \approx 27.10\text{ m}$
  * NoData Identifier: `None` (Tile is an inland continental land area; $100\%$ valid pixels, $0$ NoData pixels)
* **Geographic Extent (Tile Bounds)**:
  * West Longitude: $76.99986111111112^\circ\text{E}$ (Nominal $77.0^\circ\text{E}$)
  * East Longitude: $77.99986111111112^\circ\text{E}$ (Nominal $78.0^\circ\text{E}$)
  * South Latitude: $28.000138888888888^\circ\text{N}$ (Nominal $28.0^\circ\text{N}$)
  * North Latitude: $29.000138888888888^\circ\text{N}$ (Nominal $29.0^\circ\text{N}$)

---

### 5.3 DSM vs. DTM Classification & Hydrological Implications

* **Classification**: **Digital Surface Model (DSM)**
* **Sensor Origin**: Derived from synthetic aperture radar (SAR) X-band interferometry acquired during the TanDEM-X mission (DLR / Airbus, 2010–2015), supplemented by WorldDEM hydro-enforcement editing.
* **Surface Phenomenon Represented**:
  * The elevation values represent the **first-surface reflective canopy**, which includes:
    1. Tops of buildings, institutional campuses, and residential housing clusters.
    2. Tree canopies in the Delhi Central Ridge reserve forest and city parks.
    3. Elevated transportation viaducts (Delhi Metro elevated lines, Barapullah elevated corridor, Ring Road flyovers).
    4. Railway embankments and canal bunds.
  * It is **NOT a bare-earth Digital Terrain Model (DTM)**.
* **Critical Implications for Urban Hydrological Analysis**:
  * *Digital Dam Artifacts*: Elevated flyovers and road bridges spanning open nallahs (e.g., Ring Road flyover crossing Kushak Nallah at AIIMS, railway bridges at Defence Colony) appear as elevated topographical barriers in a DSM. If raw D8 flow accumulation is run without hydro-conditioning, these features act as artificial "digital dams," erroneously severing stream connectivity and inducing artificial upstream ponding.
  * *Building Envelope Effects*: Dense residential neighborhoods (e.g., South Extension Part 1 & 2, Kidwai Nagar) exhibit elevated pixel clusters reflecting roof heights ($+5\text{ m}$ to $+15\text{ m}$). While these buildings naturally obstruct overland flow, narrow street corridors ($\le 15\text{ m}$ width) cannot be fully resolved at $30\text{ m}$ posting.
  * *Methodological Directive*: When hydrological modeling commences in subsequent steps, the raw DSM must be hydro-conditioned via culvert burning / depression breaching along verified open-drain centerlines. The raw DEM raster, however, must remain **100% native and unmodified in storage**.

---

### 5.4 Documented Vertical Accuracy & Sensor Qualification

Per the ISO 19115 quality evaluation statement embedded in `Copernicus_DSM_10_N28_00_E077_00.xml`:
* **Tile-Specific Absolute Vertical Accuracy**:
  * **$\text{LE90} = 1.763\text{ m}$** (Linear Error at 90% confidence level)
  * **$\text{LE68} = 1.442\text{ m}$** (Linear Error at 68% confidence level / $\approx 1\sigma$ RMSE)
  * Evaluation Date: 2018-03-26 (Airbus Defence and Space Product Quality Unit)
* **Horizontal Accuracy**:
  * Circular Error $\text{CE90} < 6.0\text{ m}$
* **Relative Vertical Accuracy & Slope Dependence**:
  * For flat to gently sloping terrain ($< 20\%$ slope), relative point-to-point vertical precision is $< 1.5\text{ m}$.
  * In steep micro-relief (e.g., quarry scarps and rocky slopes of the Southern Ridge), radar layover and shadow effects increase local uncertainty.
* **Urban Flood Modeling Disclaimer**:
  * Product-level vertical accuracy ($\sim 1.76\text{ m}$) is a macro-scale geodetic metric evaluated against GPS ground control networks.
  * **This accuracy does NOT mean street-level flood depths are known to $1.76\text{ m}$ precision.** Sub-grid vertical features that govern urban waterlogging—such as road curb reveals ($15 - 20\text{ cm}$), road camber crowns ($5 - 10\text{ cm}$), and underpass sump dips ($1.0 - 2.5\text{ m}$)—fall below the $30\text{ m}$ horizontal resolution of the dataset.

---

### 5.5 Spatial Coverage & Candidate Area Verification

* **Candidate Study Area**: Kushak Nallah sub-catchment / western branch of Barapullah basin.
* **Candidate Bounding Box**:
  * Latitude: $28.52^\circ\text{N}$ to $28.63^\circ\text{N}$
  * Longitude: $77.15^\circ\text{E}$ to $77.25^\circ\text{E}$
* **Coverage Evaluation**:
  * The candidate study area lies **entirely within the acquired tile `N28_00_E077_00`**.
  * Distance from the westernmost catchment divide (Central Ridge / Dhaula Kuan, $\approx 77.16^\circ\text{E}$) to the western tile boundary ($77.00^\circ\text{E}$) is **$> 16.5\text{ km}$**.
  * Distance from the southern catchment divide (Hauz Khas / Andrews Ganj, $\approx 28.53^\circ\text{N}$) to the southern tile boundary ($28.00^\circ\text{N}$) is **$> 58\text{ km}$**.
  * **Single-Tile Sufficiency**: Exactly **one tile** (`N28_00_E077_00`) provides $100\%$ contiguous spatial coverage. No edge-mosaicking or adjacent tile downloads are required.

---

### 5.6 Non-Destructive Statistical Inspection

Statistical summary computed across the entire tile and across the candidate Kushak window using `rasterio`:

```
================================================================================
                       DEM NUMERICAL INTEGRITY AUDIT
================================================================================
Full 1° x 1° Tile (12,960,000 pixels):
  • Min Elevation:      178.00 m MSL (Yamuna floodplain south of Delhi)
  • Max Elevation:      336.72 m MSL (Aravalli Ridge outcrops in southern NCR)
  • Mean Elevation:     209.30 m MSL
  • Median Elevation:   207.43 m MSL
  • Standard Deviation:  17.61 m
  • 1st Percentile:     185.10 m MSL
  • 99th Percentile:    287.05 m MSL
  • NoData Pixels:      0 (100% valid inland coverage)

Candidate Kushak Window (Lat 28.52°–28.63°N, Lon 77.15°–77.25°E; 396 x 360 pixels):
  • Min Elevation:      196.84 m MSL (Barapullah confluence low ground)
  • Max Elevation:      286.81 m MSL (Central Ridge horst divide / Dhaula Kuan)
  • Mean Elevation:     232.05 m MSL
  • Median Elevation:   230.32 m MSL
================================================================================
```

*All elevation values are physically and numerically plausible, showing an expected downward topographic gradient of $\approx 90\text{ meters}$ from the rocky Central Ridge crest ($286.8\text{ m}$) down to the Barapullah confluence corridor ($196.8\text{ m}$).*

---

### 5.7 Scientific Suitability for Delhi V2 Hydrological Modeling

1. **Topographic Continuity**: The tile provides unbroken, seamless elevation coverage across the entire Kushak corridor, from its headwaters at Rashtrapati Bhavan / Central Ridge to its outfall at Defence Colony / Sunehri Pul.
2. **Hydraulic Slope Fidelity**: Macro-scale bed slopes along the Kushak corridor ($S_0 \approx 0.001 - 0.002$) are clearly preserved without artificial step artifacts present in coarser or legacy DEMs.
3. **Data Integrity & Compliance**: The native dataset has been archived without reprojection, resampling, or interpolation, maintaining complete traceability and reproducibility under the project's strict provenance mandate.
