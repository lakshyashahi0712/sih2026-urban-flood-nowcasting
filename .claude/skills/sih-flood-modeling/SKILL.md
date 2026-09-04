---
name: sih-flood-modeling
description: Domain guidance for SIH 2026 Problem Statement 26085 — Urban Flood Nowcasting System (Drainage and Rainfall Coupling). Use whenever the work involves rainfall nowcasting, DEM/terrain processing, runoff and imperviousness, drainage networks, hydraulic capacity/surcharge/blockages, 2D surface routing, street/intersection flood depth prediction, 0–3 hour lead time, GIS layers, flood-safe routing, validation, uncertainty, or deciding between physically meaningful modelling and prototype approximations. Do NOT use for generic dashboard or web-app work unrelated to flood/hydrology.
---

# Urban Flood Nowcasting (PS 26085)

Goal: predict **where streets and intersections flood**, and **how deep**, 0–3 hours ahead, by coupling **rainfall** with **drainage**. The lead time matters: this is *nowcasting* (very short term), not seasonal forecasting. Decisions are about alerting people, closing routes, and deploying response — so outputs must be *interpretable and honest about uncertainty*, not just "it might flood."

## Grounding principles

* **Never claim data, sensors, models, or APIs exist that are not actually available to this project.** If a needed input (radar, rain gauge, DEM, drainage asset inventory, calibrated hydraulic model) is missing, say so explicitly and model the gap as an assumption — do not fabricate it.
* **Physically meaningful modelling ≠ prototype approximation.** Keep them visibly separate and label every result with which one it is.
  * *Physically meaningful:* conservation-respecting flow (mass balance, continuity), real topographic gradient from a real DEM, real pipe capacities from a real asset table, units checked.
  * *Prototype approximation:* a heuristic that stands in for a missing input (e.g. "assume uniform rainfall" when no radar exists). Prototypes are fine for a hackathon — but they must be *declared*, never dressed up as science.
* **Flow direction matters.** Water obeys gravity: from high to low, along the steepest descent, then into the network, then through pipes until capacity is exceeded and water surfaces onto the street. Every step must respect this ordering.
* **Coupling is the point.** Rainfall → runoff → network inflow → surcharge → surface flooding is one chain. A model that only does rainfall or only does drainage has not answered the problem.

## The modelling chain (in order)

### 1. Rainfall nowcasting (0–3 h)
* Inputs that *may* exist here: rain-gauge point readings, IMD or other forecast products, radar reflectivity, satellite estimates. Discover which are actually available before choosing a method.
* Methods, from physically grounded to prototype:
  * Radar/nowcast extrapolation (advection of reflectivity fields) — most defensible if radar data exists.
  * NWP short-range QPF if a forecast product exists.
  * Persistence / "last hour repeats" — the honest baseline when nothing better exists.
  * Spatially-uniform assumed intensity — prototype only; label it.
* Always express rainfall as an **intensity (mm/h)** over a **duration** and a **spatial footprint**. A single number without duration/footprint is meaningless for runoff.
* Report lead-time degradation: skill drops as lead time grows. State this.

### 2. DEM / terrain processing
* Work in a **projected, metric CRS** for all distance/area/slope math (e.g. UTM zone for the city, or the national grid). Never compute slopes/areas in EPSG:4326 degrees.
* Fill sinks *only* where justified; over-filling hides real depressions that genuinely flood.
* Derive: flow direction (D8 or similar), flow accumulation, watersheds, slope, and the **street/intersection surface**, which is what people experience. Buildings act as barriers — account for them in routing where data allows.
* Terrain is the single biggest driver of *where* water goes. Getting CRS and flow direction wrong invalidates everything downstream.

### 3. Imperviousness and runoff
* Runoff coefficient (C) or Curve Number (CN) per land-cover class: impervious (roads, roofs) sheds fast; pervious (parks, soil) absorbs.
* Generate a **time series of rainfall excess** (rainfall minus losses) — this is what actually enters the network.
* Convert rainfall excess to a **network inflow** (catchment area × excess intensity), with unit checks (mm/h × m² → volume rate).
* If land-cover data is absent, use a coarse, clearly-labeled default classification — prototype.

### 4. Drainage network as a directed graph
* Model pipes/culverts as **directed edges** (downhill, from inlet to outlet), junctions as **nodes**. This is a graph problem: topological sort, upstream/downstream traversal, sink detection.
* Track **capacity** (diameter/slope → conveyance, e.g. Manning's equation) per edge, and **surcharge**: when inflow > capacity, the pipe is full and excess water must go *somewhere* — onto the surface.
* **Blockages** reduce capacity: model a blocked pipe as reduced effective area. If blockage data doesn't exist, make it an explicit scenario parameter, not a hidden constant.
* A network with unknown asset data is a *structural prototype* — say so and note what real data would replace it.

### 5. 2D surface routing (the flood map)
* Once the network surcharges, water moves over the street grid. Route excess volume along the topographic gradient computed in step 2.
* Produce **flood depth per street segment / intersection** — this is the user-facing prediction, not just a flooded-area polygon.
* Keep this as a coupled estimate: network capacity → how much surfaces; terrain → where it pools. Both halves must agree on units and time step.

### 6. Outputs and lead time
* Deliverables: predicted flood depth at streets/intersections, at **now + 0/1/2/3 h**.
* **Flood-safe routing**: given predicted flooded segments, produce alternative routes that avoid them — a shortest-path variant with flooded edges removed or penalized.
* Every output should carry a timestamped **validity window** and an uncertainty/confidence qualifier.

## GIS layers (make these explicit)
Suggested working layers (create only those you have data for):
* Rainfall nowcast (raster/field)
* Terrain/DEM (raster)
* Imperviousness / land cover (raster)
* Catchments (polygon)
* Drainage network — nodes & edges (line/point)
* Flood depth predictions (per-street/intersection attribute, plus a surface raster)
* Flood-safe routes (line)
* Basemap + city context (vector)

Preserve **provenance** for every layer: source, acquisition time, CRS, license, and any processing applied. Store these as sidecar metadata, not just in chat.

## Validation and uncertainty
* **Validate against real/project data where it exists**: observed rainfall vs nowcast, observed flood extents vs predicted. If no observed flood data exists, state it and validate what you can (mass balance, unit checks, sanity of flow directions, capacity sums).
* **Mass-balance check**: rainfall volume in ≈ runoff + storage + routed volume out (within tolerance). If water is created or destroyed, the chain is wrong.
* **Uncertainty**: give each prediction a range or confidence. Nowcasting is uncertain; a single crisp "0.5 m" without a range overstates certainty. Flag the largest uncertainty source (rainfall intensity? missing asset data? terrain?).
* **Distinguish in every result** whether it is a *validated estimate* or a *prototype approximation*.

## Anti-patterns to flag
* Computing slope/area/buffer in EPSG:4326 (degrees treated as meters).
* Letting water flow uphill or into a closed sink without justification.
* Declaring "the model predicts flooding" with no stated rainfall input or lead time.
* Treating a prototype heuristic as calibrated science, or vice-versa.
* Omitting capacity/surcharge so the network never actually floods on the surface.
* Fabricating radar/gauge/DEM/asset data to make a demo look real.
* Reporting a single crisp depth with no uncertainty or validity window.
