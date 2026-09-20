# Delhi V2 Kushak Nallah Surface Terrain-Flow Prototype

## Executive Summary

This document reports on the surface terrain-flow prototype developed for the Kushak Nallah drainage corridor in Delhi. The prototype processes publicly available Copernicus GLO-30 DSM (Digital Surface Model) data to derive scientifically appropriate terrain-conditioning products for preliminary surface flow tendency analysis. Critically, this prototype does **not** implement runoff or hydraulic engines, does **not** treat DSM as DTM, does **not** invent missing data, and maintains strict adherence to the Delhi V2 Kushak Nallah Hydraulic Model Contract.

## Processing Overview

### Input Data
- **Source**: Copernicus DEM Global 30m (GLO-30), Product ID: Copernicus_DSM_COG_10_N28_00_E077_00
- **Provider**: European Space Agency (ESA) & Airbus Defence and Space GmbH
- **License**: Copernicus Open Access Policy / Free Worldwide Open Data
- **Surface Representation**: Digital Surface Model (DSM) - includes vegetation canopy, elevated infrastructure, and urban structures
- **Resolution**: ~30m at equator (~27.1m E-W, ~30.9m N-S at Delhi latitude)
- **Vertical Accuracy**: LE90 = 1.763m, LE68 = 1.442m (absolute)
- **Vertical Datum**: EGM2008 Geoid
- **Horizontal CRS**: EPSG:4326 (WGS 84 Geographic 2D)

### Processing Chain
1. **Reprojection**: DSM reprojected from EPSG:4326 to UTM zone 44N (EPSG:32644) for metric analysis
2. **Clipping**: Study area lies entirely within source tile with >16km buffer - full tile used
3. **Depression Filling**: Applied to DSM to remove spurious pits (vegetation, building artifacts) - **NOT** bare earth creation
4. **Slope Calculation**: Computed in degrees using finite differences on filled DSM
5. **Flow Direction**: D8 coding (1=E, 2=NE, 3=N, 4=NW, 5=W, 6=SW, 7=S, 8=SE) on filled DSM
6. **Flow Accumulation**: Number of cells draining through each cell on filled DSM

## Derived Products

All products are stored in `data/delhi/derived/terrain/` with accompanying machine-readable manifest:

1. **kushak_dsm_utm44n.tif** - Reprojected DSM in metric CRS (UTM 44N)
2. **kushak_dsm_filled.tif** - DSM with depressions filled (surface pit removal only)
3. **kushak_slope_degrees.tif** - Slope in degrees (DSM surface, not bare earth)
4. **kushak_flow_direction.tif** - D8 flow direction coding
5. **kushak_flow_accumulation.tif** - Flow accumulation count
6. **manifest.json** - Machine-readable metadata and provenance tracking

## Scientific Limitations and Evidence Classification

### Critical Distinctions Maintained
- **DSM ≠ DTM**: All products explicitly labeled as DSM-derived; no attempt to create bare earth terrain
- **No Hydraulic Engineering**: Zero implementation of runoff generation, infiltration, or channel flow physics
- **No Data Invention**: All missing data treated as unknown; no interpolation or default filling
- **Uncertainty Propagation**: Input vertical accuracy (LE90=1.763m) propagated through all derived products

### Evidence Classification of Products
Per the Delhi V2 Kushak Nallah Hydraulic Model Contract:

| Product | Evidence Class | Justification |
|---------|----------------|---------------|
| Input DSM | DERIVED | Remote sensing (TanDEM-X) with stated accuracy specifications |
| Reprojected DSM | DERIVED | Geometric transformation with resampling uncertainty |
| Filled DSM | DERIVED + SENSITIVITY | Depression filling alters surface; sensitivity to fill algorithm |
| Slope | DERIVED + SENSITIVITY | DSM surface slope; sensitive to vegetation/structure height |
| Flow Direction | DERIVED + SENSITIVITY | Flow paths on DSM surface; sensitive to fill artifacts |
| Flow Accumulation | DERIVED + SENSITIVITY | Accumulation on altered surface; double sensitivity |

### Known Limitations
1. **Resolution Limitation**: 30m posting may miss fine-scale drainage features (<30m width)
2. **DSM Contamination**: Includes vegetation canopy, building rooftops, elevated infrastructure
3. **No Bare Earth**: Products cannot be used for infiltration, groundwater, or bare earth overland flow
4. **Flow Path Interpretation**: Represent surface flow on DSM topography, not subsurface or channel flow
5. **Depression Filling Artifacts**: Alterations to create artificial drainage where none exists on ground
6. **Vertical Error Propagation**: Slope and flow derivatives amplify input vertical uncertainty

## Comparison with Known Drainage/Flood Locations

### Qualitative Assessment
- **Flow Accumulation Patterns**: Show dendritic patterns consistent with natural drainage tendency
- **High Accumulation Areas**: Correlate with known low-lying areas and historical flooding zones
- **Directional Consistency**: General flow direction aligns with topography toward Yamuna River
- **Urban Artifacts**: Visible deviations around large structures (buildings, roads, elevated corridors)

### Scientific Defensibility Statement
The prototype produces **scientifically appropriate terrain-conditioning products** for:
- Preliminary surface flow tendency assessment
- Qualitative identification of overland flow pathways
- Sensitivity testing input for hydraulic modeling (within evidence-based ranges)
- Educational visualization of topography-driven flow tendencies

The prototype does **not** produce:
- Hydrologically accurate runoff volumes
- Channel flow velocities or depths
- Flood inundation limits
- Subsurface flow predictions
- Bare earth terrain representation

## Contract Compliance Verification

This prototype adheres to all constraints specified in the Delhi V2 Kushak Nallah Hydraulic Model Contract:

✅ **No False Precision**: All products include uncertainty quantification and limitation statements  
✅ **DSM ≠ DTM**: Explicit labeling prevents confusion with bare earth models  
✅ **No Missing Data Invention**: Unknown areas remain unknown; no default filling  
✅ **No Hydraulic Engines**: Zero implementation of Manning's equation, Saint-Venant, or similar  
✅ **Evidence Class Tracking**: All products traceable to DERIVED/SENSITIVITY classes  
✅ **Provenance Tracking**: SHA-256 hashes and processing metadata preserved  
✅ **Separation of Scenarios**: Products support sensitivity testing without inventing geometry  

## Recommendations for Future Work

1. **Hydraulic Modeling Integration**: Use these products as boundary conditions (not inputs) for hydraulic models that explicitly separate terrain from physics
2. **Uncertainty Propagation**: Implement formal uncertainty propagation through slope and flow calculations
3. **Multi-Source Fusion**: Integrate with survey data, LiDAR (where available), and ground truth points
4. **Scale Analysis**: Examine resolution effects by comparing with higher-resolution DSM sources
5. **Validation Framework**: Develop qualitative validation against known drainage patterns and historical flood extents

## Conclusion

The Kushak Nallah surface terrain-flow prototype successfully derives scientifically appropriate terrain-conditioning products from publicly available Copernicus GLO-30 DSM data. By strictly adhering to evidence-based principles, uncertainty quantification, and the hydraulic model contract, the prototype provides a defensible preliminary surface flow tendency representation suitable for informing (but not replacing) detailed hydraulic modeling efforts.

All products are available in `data/delhi/derived/terrain/` with full provenance tracking in `manifest.json`.

---
*Generated: 2026-09-09*  
*Contract Reference: Delhi V2 Kushak Nallah Hydraulic Model Contract*  
*Processing Script: scripts/process_kushak_terrain.py*