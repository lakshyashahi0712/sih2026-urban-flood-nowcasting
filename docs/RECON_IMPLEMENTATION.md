# Data-Reconnaissance Fixes — Implementation Report

Implements all five ranked gaps from `docs/DATA_RECONNAISSANCE_V2.md`.

## 1. Street-depth pathway (honest estimated-depth layer)

`backend/app/domain/delhi/drainage/loading.py` — a single-store prism
proxy: `depth = (storage above the documented initial condition) /
(length x effective width)` using the documented geometry class ranges
(NIT52 box width 4-5 m x JIR depth 3.5-4.5 m for UG-01; bounding
cross-section bottom widths for open edges) → a **depth RANGE in cm**,
labeled **ESTIMATED_UNDER_ASSUMED_GEOMETRY** with an explicit caveat:
not hydraulic stage, not observed depth, not street depth. UNKNOWN
storage → UNKNOWN (never invented). Surfaced in the nowcast payload
(`depth_estimates`) and the NOWCAST UI.

## 2. DERIVED Delhi drainage graph + overcapacity logic

`backend/app/domain/delhi/drainage/graph.py` — 9 nodes (corridor origin,
the 7 documented Appendix XII cross-sections with their documented
coordinates+chainage, the Barapullah confluence) and 8 chainage-ordered
edges whose geometry follows the documented corridor centerline. Each
edge carries an **INFERRED_EFFECTIVE full-bore capacity RANGE** from the
documented geometry classes (box class for UG-01; trapezoidal
bottom/bank/side-slope from the bounding cross-sections) × DMP Manning n
× the corrected backbone slope. Loading logic (`loading.py`): modeled
inflow vs capacity-range lower bound →

- NO_LOADING / WITHIN_CAPACITY_RANGE / **POTENTIAL_OVERLOAD** / UNKNOWN

At the EV-01 peak hour the UG-01 box conduit correctly shows
POTENTIAL_OVERLOAD (538 m3/s vs the ~76-142 m3/s class) — the
scenario-consistent backflow/surcharge potential, with reasons that
never claim observed flooding or depth. API: `/api/delhi/drainage-graph`
and `/drainage-graph/loading` (live or historical/replay states); map
layer shows nodes+edges.

## 3. Delhi radar probe + composite

`backend/app/domain/delhi/radar.py` — probes the IMD Delhi Doppler (Aya
Nagar) endpoints; a visual GIF/JPG is reported accessible but **never
decoded** (no official color calibration). Composite decision with strict
provenance: RADAR only when a quantitative gridded product is actually
available, otherwise NWP_FALLBACK (Open-Meteo is never called radar).
Endpoints: `/api/delhi/rainfall/radar` and `/rainfall/composite`.

## 4. 2D surface routing over the enforced DEM

`backend/app/domain/delhi/surface.py` — static cached D8 flow structure
over the corridor window (vectorized rasterization, ~1.6 s build), then
a cell-to-cell volumetric pass: excess = rainfall x ASSUMED C (0.75);
columns bounded by the local terrain depression depth (a cell with no
outlet is a pit, not an infinite reservoir); UNKNOWN forcing timesteps
produce NO loading. Outputs: peak surface column proxy (cm), candidate
ponding **hotspots** (WGS84), and per-reach corridor-margin inflow proxy
(m3/s, reported, never injected into the replay). Endpoints:
`/api/delhi/surface` (live or historical) + nowcast payload + map
hotspot layer with size ∝ column.

## 5. Terrain resolution

Documented as a hard evidence bound (GLO-30 DSM 30 m; lidar/DTM and
as-built surveys access-blocked). The surface products carry the DSM
caveat verbatim; nothing implies <2 m vertical accuracy or street-scale
ponding truth.

## Bonus fix

Found and fixed a latent evidence-layer bug: `backbone_slope_m_per_m()`
picked the first digitized chainage row per junction; J_5105's first row
is a 10.6 m "Part II" section fragment, so the documented slope computed
as 1.02 m/m. The selector now prefers the maximal chainage (the main
trunk's single-label digitization) → slope 0.00304. Full suite confirms
no regressions (slope feeds only the capacity echo).

## Verification

- Full suite: **1138 passed** (23 new reconstruction tests: graph
  structure/provenance, plausible capacities, UNKNOWN-never-NO_LOADING,
  peak-hour overload, depth labels, surface honesty, radar provenance,
  API contracts).
- Frontend `npm run build` clean; NOWCAST UI gains drainage-loading
  and estimated-depth tables plus the surface-pass summary; the map
  gains the drainage graph and hotspot layers.
- Production mode remains PHYSICS_ONLY; all new products are reported
  alongside the physics with provenance, never replacing it.
