# Synthetic Scenario Engine (V2)

Controlled, reproducible, fully traceable demonstration scenarios that run
through the SAME canonical pipeline as real/live forcing. Synthetic data
demonstrate system behaviour; they do NOT demonstrate real-world accuracy.

## Architecture

Scenario -> seeded rainfall generator (elliptical Gaussian core,
hyetograph profile, translation) -> areal forcing depths into the
CANONICAL interface (run_integrated_simulation / rainfall_to_inflow)
-> corridor chain (advance_chain_series) -> 2D surface pass with the
SPATIAL field -> flood-depth field (cm) -> state classification ->
road-segment depth -> drainage-graph loading -> synthetic telemetry
(SIM-AWS/DRAIN/PUMP/GATE) -> controlled synthetic ground truth
(independent LOCAL reference) -> SYNTHETIC VALIDATION metrics.

Modules: `backend/app/domain/delhi/scenarios/{config,rainfall,engine,validation}.py`,
API `backend/routers/scenarios.py` (prefix `/api/scenarios`).

## Scenario definitions

| ID | Name | Purpose |
| --- | --- | --- |
| SCN-01 | MODERATE MONSOON | normal response, distributed rain, little inundation |
| SCN-02 | LOCALIZED CLOUD BURST | intense rain over a small headwater core |
| SCN-03 | EXTREME STORM | sustained high intensity, mid-event peak (DEFAULT DEMO) |
| SCN-04 | HIGH-TIDE COMPOUND | heavy rain + SYNTHETIC downstream boundary (backwater factor 0.55) |
| SCN-05 | DRAINAGE CAPACITY CONSTRAINT | SCN-02 rain + experimental conveyance multiplier 0.65 |
| SCN-06 | ENSEMBLE | 6 seeded rainfall realizations, min/mean/max envelope (NOT a confidence interval) |

All definitions live in `scenarios/config.py` (duration, timestep 15 min,
seed 20260917, storm profile/spatial/translation, modifiers, boundary,
ensemble perturbations).

## V1 REFERENCE DEPTH MODEL (taken from Mumbai/Kurla V1)

The scenario flood-depth product uses the **V1 reference model semantics**
(`app.domain.flood.routing.route_flood_depth`) on the Delhi window:
runoff distributed to street inlets (curb-gutter capacity, documented
V1-prototype parameters; gullies every ~60 m along real OSM roads), each
conveying up to its capacity, the surplus ponding at the inlet cell, and
D8 equilibrium routing to per-cell depth. Terrain bounds cap ponded depth
at the local depression (flat cells 10 cm) with honest overflow accounting.
`test_v1_equivalence_small_window` proves the Delhi port reproduces the
V1 `route_flood_depth` field within the V1 model's own transfer threshold.

The scenario progression demonstrates the problem statement's core
insight (hyper-locality): the broad 91 mm/h extreme storm (SCN-03) mostly
drains (MODERATE, 13.5 cm) while the LOCALIZED burst (SCN-02/05) floods
streets (SEVERE, ~226-231 cm pits); SCN-01 (moderate monsoon) does not
flood; SCN-04 (compound) shows prolonged recession; SCN-06 shows a real
ensemble spread. All V1-reference outputs are SIMULATED_MODEL_OUTPUT —
never observed depth, never real-event accuracy.

## Core equations / logic

- Hyetograph: piecewise-linear amplitude over [0,1] of duration.
- Spatial core: `rain(x,y,t) = base + peak*amp(t) * exp(-0.5*((dx/sx)^2+(dy/sy)^2))` with the core translated by the storm-movement vector; the field is NORMALIZED so its window mean equals the areal hyetograph depth.
- Surface pass: D8 cell-to-cell volumetric routing over the enforced
  30 m DSM window; columns bounded by local terrain depression depth
  (flat cells capped at a documented 10 cm); documented ASSUMED
  infiltration (4 mm/h) gives a physical recession.
- Depth states: NO_FLOOD/SHALLOW/MODERATE/DEEP/SEVERE/UNKNOWN via the
  ONE canonical config (`/api/scenarios/config`); UNKNOWN is separate,
  never NO_FLOOD.
- Road depth: nearest surface cell at each road-segment midpoint
  (depth_m + state; UNKNOWN stays UNKNOWN, never 0 m).
- Channel depth: single-store prism proxy (ESTIMATED_UNDER_ASSUMED_GEOMETRY).

## Synthetic truth generation

Controlled reference with a DIFFERENT mechanism than the displayed
forecast: each cell accumulates its own excess (0.90 x C) into its local
depression, capped by terrain — no D8 routing. Validation therefore
compares two distinct responses, never a copy.

## Validation (SEPARATE category)

`SYNTHETIC VALIDATION - CONTROLLED TEST DATA`: per-step + aggregated
depth MAE/RMSE/bias, extent IoU/precision/recall, cell-level occurrence
F1. Real-event validation is untouched and separate.

## Routing integration

Scenario mode is opt-in; production/live never consumes synthetic data.
Depth thresholds (routing hazard 15 cm / exclude 45 cm) are configured in
the same canonical config the routing engine reads.

## Limitations

SIMULATED only; no real observation claims; 30 m DSM surface proxies;
conveyance modifiers/boundary profiles are experimental forcing, not
claims about real blockage or tides; ensemble envelope is a spread, not
a confidence interval.

## Judge-demo depth map (V1-EXACT PARITY)

The depth map layer renders flooded cells as **filled 30 m square
polygons** colored by the **exact V1 color ramp** (the Mumbai FloodMap
legend: #ffeda0 / #feb24c / #f03b20 / #bd0026) — a contiguous
raster-like flood-depth map like V1's, generated by the real pipeline.
Each scenario/event step returns `depth_polygons` (full flooded-cell set)
alongside the depth samples; roads color by modeled depth; REPLAY shows
the depth grid evolving with the replay clock.

## Judge-demo depth map

Each scenario run returns per-step `depth_cells` (up to 320 routed-field
samples, WGS84, classified by the canonical thresholds) and per-edge
`drainage_loading` (modeled peak inflow vs the documented capacity class,
with any scenario modifier applied). The frontend SCENARIOS tab renders:

- the depth map layer (color/size by SHALLOW/MODERATE/DEEP/SEVERE),
- flooded-road coloring on the drainage graph edges,
- the numeric MAX FLOOD DEPTH widget (m + cm),
- the drainage network response table (POTENTIAL_OVERLOAD = capacity-class
  breach under the synthetic forcing — never observed flooding),

with the FLOOD DEPTH legend sourced from `/api/scenarios/config` and a
persistent SIMULATED badge. SCN-03 (default demo) shows the full chain:
rain -> rising load -> POTENTIAL_OVERLOAD at the UG-01 box conduit ->
surface depth growth -> road hazards -> recession.

## Acceptable demos

Run SCN-03: select SCENARIOS -> SCN-03 -> Start -> timeline shows rainfall
depth, flood depth indicator (0-3h steps), drainage state, telemetry,
synthetic validation. Re-run = identical (deterministic).
