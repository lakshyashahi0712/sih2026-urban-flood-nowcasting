---
name: key-technical-concepts-green-ampt-infiltration-model-scs-cn-method-mass-balance-conservation
description: Key technical concepts including Green-Ampt, SCS-CN, mass balance
metadata:
  type: project
---

# Key Technical Concepts

## Hydrology/Hydraulics:
- Green-Ampt infiltration model
- SCS-CN (Curve Number) method
- Effective Impervious Area (EIA)
- Antecedent Moisture Conditions (AMC)
- Mass balance conservation (P = L + E + ΔS)
- Simplified Kinematic Wave approximation for overland flow
- Depression storage tracking
- Initial Abstraction (Ia)

## Units and Dimensions:
- Rainfall depth in mm
- Area in m²
- Volume in m³
- Discharge in m³/s
- Time step handling (conversion between minutes/hours)

## Modeling Constraints:
- No SWMM
- No hydraulic routing
- No machine learning
- No new modeling capability beyond specified loss models and runoff transformation

## Data Quality:
- Unit consistency
- Mass balance error tolerance (≤0.10%)
- Monotonicity of cumulative infiltration/runoff

## Testing:
- Automated test suite for loss models and runoff transformation covering zero rainfall, constant low/high rainfall, intermittent rainfall, mass balance verification

## Repository Management:
- Git status inspection
- Commit history
- File existence checks

## IIT Delhi 2018 Report:
- Drainage Master Plan for NCT of Delhi
- Data limitations (interpolation, engineering judgment, missing infrastructure data)
- Barapullah basin characteristics
- Design parameters (Manning's n values, Horton infiltration parameters, Safdarjung IDF)

## GSDL CRSC Audit:
- Cross-section spatial querying
- Attribute analysis
- Provenance determination (surveyed vs digitized/model/DEM-derived/interpolated)
- Comparison with existing corridors (Kushak 5.028 km, GSDL Layer 7 NDMC spine)
- Right-angle transect verification
- Field meaning investigation