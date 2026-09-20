# Delhi V2 Machine Learning Strategy & Model Evaluation

## 1. Executive Position & Core ML Tenets

The primary role of Machine Learning in the SIH 2026 Urban Flood Nowcasting System is strictly defined:
1. **Physics-First Architecture**: Machine learning will **NEVER replace the physics-based hydrodynamic simulation engine** in the initial deployment. The physical laws of mass conservation, shallow water gravity flow, and open-channel hydraulics provide foundational physical guarantees (water does not flow uphill, flood volume cannot exceed rainfall excess, and dry cells cannot spontaneously pond).
2. **Ground-Truth Calibration**: ML is introduced solely as an empirical calibration and residual correction layer, bridging the unavoidable gap between idealized numerical equations and real-world micro-topographic friction, curb-inlet blockages, and unmodeled siltation.
3. **Event-Separated Validation**: Training and validation splits **MUST strictly be separated by discrete storm events** (Leave-One-Event-Out or Event-Grouped Cross-Validation). Randomly splitting spatial pixels or timesteps from within the same storm event creates severe spatial auto-correlation leakage and produces grossly exaggerated, fraudulent validation metrics.

---

## 2. Evaluation of Candidate ML Roles

### Role A: Physics-Model Residual Error Correction (RECOMMENDED FIRST ML ROLE)
- **Concept**:
  The physical flood engine computes predicted water depth $\hat{d}_{\text{phys}}(x, y, t)$ across the domain. The ML model is trained to predict the residual error:
  $$\epsilon(x, y, t) = d_{\text{observed}}(x, y, t) - \hat{d}_{\text{phys}}(x, y, t)$$
  The final nowcast depth is the physics prediction adjusted by the bounded learned correction:
  $$d_{\text{final}}(x, y, t) = \max\left(0.0,\; \hat{d}_{\text{phys}}(x, y, t) + \hat{\epsilon}(x, y, t)\right)$$
- **Recommended Algorithm**:
  **Tabular Gradient-Boosted Decision Trees (GBDT)** — specifically **LightGBM** or **XGBoost**.
- **Why GBDT is Best Suited**:
  - Ground-truth flood observations in Delhi (as in Mumbai) are **sparse, structured tabular records** (observed water depth ranges or binary flood/no-flood logs at 50–200 specific traffic intersections and underpasses).
  - GBDT natively excels on small to medium-sized tabular datasets ($10^2 - 10^4$ records) with non-linear feature interactions and missing values.
  - GBDT is fully interpretable via TreeSHAP (SHapley Additive exPlanations), allowing flood emergency operators to audit exactly why an error adjustment was applied (e.g., "AIIMS underpass depth increased by $12\text{ cm}$ due to $45\text{ mm/h}$ rainfall intensity exceeding Kushak culvert capacity threshold").
  - Graceful degradation: If features are out-of-distribution or ML inference fails, the system safely falls back to pure physics $\hat{d}_{\text{phys}}$ with explicit provenance logging.

---

### Role B: Direct Street Flood-Risk Classification (Secondary / Downstream Role)
- **Concept**:
  Predict an ordinal risk label (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`) directly for each road corridor or intersection node:
  $$Y \in \{\text{LOW, MEDIUM, HIGH, CRITICAL}\}$$
- **Evaluation**:
  - Feasible using GBDT (multi-class or ordinal classification), but **redundant as a primary ML role**.
  - In our architecture, street risk is already deterministically classified from predicted flood depth via `classify_road_risk()` based on vehicle passage safety standards (e.g., $d \ge 0.30\text{ m} \implies \text{HIGH}$, causing small car engine stalls; $d \ge 0.50\text{ m} \implies \text{CRITICAL}$, impassable to emergency vehicles).
  - Predicting depth with residual correction (Role A) is more informative because it directly feeds both street risk categorization and depth-weighted shortest-path routing algorithms.

---

### Role C: Physics-Model Neural Surrogate / Emulator (EXPLICITLY REJECTED)
- **Concept**:
  Completely replace the hydraulic differential equation solver with a 2D deep learning emulator (e.g., U-Net, Fourier Neural Operator [FNO], or Spatio-Temporal Graph Neural Network [GNN]) mapping rainfall grids directly to 2D flood depth rasters:
  $$P(x, y, 0:t) \xrightarrow{\text{Deep Neural Network}} D(x, y, t)$$
- **Explicit Rejection Justification**:
  1. **Severe Training Data Deficit**: Training a deep 2D spatial emulator requires tens of thousands of diverse, paired spatiotemporal hydrodynamic simulation rasters across hundreds of storm hydrographs. Real ground-truth observations in Delhi consist of sparse point benchmarks, not continuous 2D depth grids.
  2. **Physical Hallucinations & Violations**: Neural surrogates are notorious for violating basic conservation of mass (creating phantom water or vanishing flood volumes) and predicting negative water depths or reverse uphill drainage.
  3. **Catastrophic Generalization Failure**: Deep models trained on moderate historical events hallucinate unpredictably when presented with out-of-distribution cloudbursts (such as the $153\text{ mm}$ July 2023 deluge).
  4. **Computational & Certification Overhead**: Complex neural networks require heavy GPU infrastructure and cannot be verified or certified for municipal disaster management advisories.
  - **Verdict**: **REJECTED FOR V2**.

---

## 3. Recommended ML Architecture: Tabular GBDT Residual Calibrator

```
   [Rainfall Forcing P_t]
             │
             ▼
┌───────────────────────────┐
│ Physics Hydrodynamic Engine│
│  - Rational Method Runoff │
│  - Manning Pipe Conveyance│
│  - D8 Surface Flow Routing│
└─────────────┬─────────────┘
              │
              ├──────────────────────────────────┐
              │ Physics Modeled Depth d_phys     │
              ▼                                  ▼
      ┌───────────────┐                  ┌───────────────┐
      │ Primary Depth │                  │ Feature Vector│
      │  Prediction   │                  │  Construction │
      └───────┬───────┘                  └───────┬───────┘
              │                                  │
              │                                  ▼
              │                     ┌─────────────────────────┐
              │                     │ LightGBM GBDT Calibrator │
              │                     │ (Event-Grouped Trained) │
              │                     └────────────┬────────────┘
              │                                  │
              │  + Predicted Residual Error ε    │
              └───────────────┬──────────────────┘
                              │
                              ▼
                 Final Calibrated Depth:
                 d_final = max(0, d_phys + ε)
                              │
                              ▼
                 Street Risk & Safe Routing
```

### 3.1 Feature Vector Specification

For each monitored validation junction / street segment $i$ at time $t$:

| Feature Name | Type | Description | Source |
|---|---|---|---|
| `d_phys` | Float ($m$) | Uncalibrated depth modeled by physics engine | 2D D8 surface routing output |
| `elevation_m` | Float ($m$) | Ground elevation from Copernicus GLO-30 | DEM raster |
| `slope_deg` | Float ($^\circ$) | Local terrain slope angle | Derived from DEM gradient |
| `twi` | Float | Topographic Wetness Index ($\ln(a / \tan \beta)$) | Computed from DEM accumulation |
| `dist_to_drain_m` | Float ($m$) | Planar Euclidean distance to nearest trunk drain | Derived from OSM/I&FC drain vectors |
| `drain_capacity_deficit`| Float ($m^3$) | Modeled conduit surcharge volume at nearest node | Manning capacity solver output |
| `rain_current_hour_mm` | Float ($mm$) | Rainfall depth in current 1-hour interval | IMD AWS / NWP forecast |
| `rain_cum_3h_mm` | Float ($mm$) | 3-hour cumulative antecedent rainfall | Sum of preceding 3 hours |
| `rain_cum_6h_mm` | Float ($mm$) | 6-hour cumulative antecedent rainfall | Soil saturation proxy |
| `road_class` | Categorical | Highway type (`primary`, `secondary`, `tertiary`) | OpenStreetMap attributes |
| `impervious_ratio` | Float ($0-1$) | Fraction of impervious built-up area in cell | ESA WorldCover 10m raster |
| `is_underpass` | Boolean | True if location is a depressed road underpass | DTP hotspot catalog |

---

## 4. Training, Validation & Protocol Integrity

### 4.1 Strict Event-Separation Protocol
To prevent data leakage, the training dataset must be partitioned using **GroupKFold** or **Leave-One-Event-Out (LOEO)** based strictly on the storm event identifier:
- **Fold 1**: Train on July 2021 Storm + August 2020 Deluge; Test on **July 2023 Benchmark Deluge**.
- **Fold 2**: Train on July 2023 Deluge + August 2020 Deluge; Test on **July 2021 Storm**.
- **Fold 3**: Train on July 2023 Deluge + July 2021 Storm; Test on **August 2020 Deluge**.

Under no circumstances may individual time-steps or spatial points from the July 2023 event be leaked into the training set when validating against July 2023 observations.

### 4.2 Error Metrics
- Mean Absolute Error (MAE) on observed depth ($m$).
- Critical Underpass Hit Rate: Sensitivity to depths $> 0.30\text{ m}$.
- False Alarm Ratio (FAR) for emergency vehicle warnings.
- Physical Boundedness: Count of negative depth anomalies (must be strictly zero).

---

## 5. Summary Recommendation
- **ML Role**: Physics-Model Error Correction / Residual Calibration.
- **Model Family**: LightGBM (Gradient-Boosted Decision Trees).
- **Implementation Sequence**:
  1. *First*: Build and validate pure physics hydrodynamic engine on Delhi testbed.
  2. *Second*: Collect tabular error residuals ($d_{obs} - \hat{d}_{phys}$) across historical monsoon events.
  3. *Third*: Train and cross-validate LightGBM residual model using Leave-One-Event-Out.
  4. *Fourth*: Expose ML-calibrated nowcasts alongside uncalibrated physics nowcasts with transparent provenance metadata.
