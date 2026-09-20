# Delhi Rainfall Event Evidence Matrix

## Overview
This document provides a detailed evidence matrix for historical rainfall events in the Delhi/Kushak corridor, classifying each data point according to its provenance and suitability for hydrologic modeling purposes. The matrix follows the project's strict data provenance classification system and distinguishes between different types of observations for calibration vs. validation use.

## Classification System

### Observation Types
- **OBSERVED_DIRECT**: Direct measured values from instrumentation (e.g., hourly AWS telemetry)
- **OBSERVED_BLOCK_TOTAL**: Official accumulated totals over a time period (e.g., 3-hour, 24-hour blocks)
- **VERIFIED_ZERO**: Periods with confirmed zero rainfall through multiple sources
- **DERIVED_BLOCK_ALLOCATION**: Values derived by allocating official block totals across sub-periods
- **DERIVED_EXACT_DIFFERENCE**: Values derived by algebraic subtraction of known components from totals
- **MODELLED/NWP**: Values from numerical weather prediction models (not ground truth)

### Provenance Classes
- **OBSERVED/OFFICIAL**: Direct observations from official instruments (IMD AWS, etc.)
- **OFFICIAL/SECONDARY**: Official reports or compilations (DTP hotspots, etc.)
- **SECONDARY_REPORT**: Published tables or inventory documents (IIT DMP 2018)
- **NWP_FORECAST**: Numerical weather prediction model output
- **UNAVAILABLE_FOR_QPE**: Data that exists but cannot be converted to quantitative precipitation estimates

### Usability Flags
- **usable_as_observed_forcing**: Suitable for use as observed forcing in hydrodynamic models
- **usable_as_calibration_observation**: Suitable for model calibration (parameter optimization)
- **usable_as_validation_observation**: Suitable for independent model validation

## Evidence Matrix Summary

The matrix contains 12 rows representing distinct rainfall observations from two major events:

### Event EV-01: June 28, 2024 Cloudburst
- **Location**: Delhi/Kushak corridor (Safdarjung and Lodhi Road observatories)
- **Peak Intensity**: 91.0 mm/h (Safdarjung), 89.0 mm/h (Lodhi Road)
- **Total Accumulation**: 228.1 mm (Safdarjung), 192.8 mm (Lodhi Road)
- **Duration**: ~24 hours (08:30 IST June 27 to 08:30 IST June 28)

### Event EV-02: July 8-10, 2023 Monsoon Surge
- **Location**: Delhi/Kushak corridor (Safdarjung and Lodhi Road observatories)
- **Peak Intensity**: 77.3 mm/h (3-hour burst at Safdarjung)
- **Total Accumulation**: 153.0 mm (Safdarjung, July 8-9), 123.4 mm (Lodhi Road, July 8-9)
- **Duration**: Multi-day event with distinct daytime/nighttime components

## Key Findings

1. **Data Availability**: While official records exist for both events, sub-hourly observational time-series data are not publicly downloadable without RTI applications or institutional collaboration.

2. **Direct Observations**: Only specific peak hourly intervals have direct AWS telemetry confirmation:
   - Safdarjung: 05:00-06:00 IST June 28, 2024 (91.0 mm)
   - Lodhi Road: 05:00-06:00 IST and 06:00-07:00 IST June 28, 2024 (64.0 mm and 89.0 mm)

3. **Block Totals**: Official accumulated totals are available for:
   - 24-hour climate accumulations (both observatories, both events)
   - 3-hour AWS blocks (Safdarjung 02:30-05:30 IST June 28, 2024: 148.5 mm)
   - Daytime synoptic accumulations (Safdarjung 08:30-17:30 IST July 8, 2023: 126.1 mm)

4. **Derived Values**: Several intervals require derivation through:
   - Exact difference (algebraic subtraction of known components)
   - Block allocation (dividing official totals across sub-periods)

5. **Zero Rainfall Verification**: Multiple periods are verified as having zero rainfall through:
   - Pre-storm quiet periods (METAR and synoptic confirmation)
   - Post-storm cessations (official weather summaries)

## Usage Recommendations

### For Calibration
- **Best**: OBSERVED_DIRECT peak hourly intervals (where available)
- **Acceptable**: OBSERVED_BLOCK_TOTAL official accumulations (24h, 3h blocks)
- **Limited**: DERIVED_BLOCK_ALLOCATION and DERIVED_EXACT_DIFFERENCE values (require caution)

### For Validation
- **Best**: Independent sources not used in calibration (limited availability)
- **Acceptable**: OBSERVED_BLOCK_TOTAL from different observatories or events
- **Not Recommended**: Values derived from the same totals used in calibration

### For Forcing
- **Requires**: Complete hyetograph with sub-hourly resolution
- **Current Status**: Incomplete due to lack of publicly available sub-hourly observational records
- **Workaround**: Use NWP models (Open-Meteo) for 0-3h operational fallbacks only

## Limitations

1. **Temporal Resolution**: Lack of publicly accessible sub-hourly observational records prevents creation of complete, verified hyetographs for direct model forcing.

2. **Spatial Representation**: Point observations from observatories may not fully capture areal rainfall distribution over the Kushak catchment.

3. **Derivation Uncertainty**: Values derived through allocation or difference methods carry implicit assumptions about temporal distribution within blocks.

4. **Access Barriers**: Official instrumental records require RTI applications or institutional data sharing agreements for access.

## Next Steps

1. **RTI Applications**: File applications to IMD and NDMC for acquisition of sub-hourly AWS telemetry records for verified events.

2. **Institutional Collaboration**: Establish data sharing protocols with IIT Delhi for access to their DMP 2018 high-resolution datasets.

3. **Sensor Deployment**: Consider temporary rain gauge installation in Kushak corridor for direct observation of future events.

4. **Uncertainty Quantification**: Develop methods to quantify uncertainty in derived rainfall values for use in ensemble modeling approaches.

---
*Generated as part of the Delhi/Kushak hydroinformatics evidence acquisition task. All classifications based on publicly available authoritative sources without alteration of original numerical values.*