# Delhi Rainfall & Flood Observation Audit

## Executive Summary
This audit consolidates publicly available, authoritative evidence for historical rainfall and flood/waterlogging observations in Delhi, specifically targeting the Kushak/Barapullah corridor. 

Despite comprehensive forensic audits, machine-readable, open-access datasets suitable for hydrodynamic calibration/validation are not currently available through public portals. Evidence relies heavily on official institution reports, secondary inventory tables, and traffic management records rather than direct, downloadable observational time-series data.

## 1. Rainfall Observations
### Strongest Rainfall Dataset
- **Source**: IMD Safdarjung / Lodhi Road Base Observatories
- **Provenance**: `OBSERVED / OFFICIAL`
- **Status**: Official records exist (not machine-readable via public APIs)
- **Suitability**: Requires RTI or official institutional request to acquire sub-hourly observational hyetographs for historic events.

### Other Sources
- **Open-Meteo API**: `MODELLED / NWP_FORECAST`. Usable for 0-3h operational nowcasting fallbacks only. Not ground truth.
- **IIT Delhi DMP 2018 Appendices**: `SECONDARY_REPORT`. Authoritative tables published in reports, usable for historic calibration, but not machine-readable.

## 2. Flood Observations
### Strongest Flood Dataset
- **Source**: IIT Delhi Aab Prahari / Jalsuraksha Platform
- **Provenance**: `OBSERVED / OFFICIAL`
- **Status**: Crowdsourced mobile reports, academic database.
- **Suitability**: High relevance for Barapullah basin. Requires institutional collaboration to access.

### Other Sources
- **Delhi Traffic Police (DTP) Waterlogging Hotspots**: `OFFICIAL / SECONDARY`. 147 gazetted hotspots. Qualitative but authoritative for identifying chronic failure points.
- **IIT Delhi DMP 2018 Inventory**: `SECONDARY_REPORT`. Detailed table of failure points for historic storms (2003-2013).

## 3. Summary of Usability
- **Calibration**: Secondary reports (DMP 2018) can provide baseline parameters for historic events.
- **Validation**: DTP hotspots and photographic/crowdsourced evidence provide qualitative validation of failure points (locations) but not quantitative depth/duration time-series.

## 4. Remaining Blockers
As documented in `DELHI_DATASET_HUNT_REMAINING_BLOCKERS.md`, all 7 scientific blockers remain open (Surveyed geometry, Datum/Benchmarks, Hydraulic structures, Historical models, Observed flood data, Rainfall telemetry, Subcatchment delineation).

## 5. Recommended Next Single Action
File RTI application to NDMC Engineering Department for the 2020 Detailed Topographical Survey of Kushak Nallah deliverables (survey drawings, level books, field books).
