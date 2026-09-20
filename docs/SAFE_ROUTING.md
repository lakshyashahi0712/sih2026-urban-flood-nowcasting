# Safe Routing (Flood-Aware Routing)

*One routing core, three integrations: LIVE nowcast, HISTORICAL replay,
EVIDENCE exploration.*

## What "safe" means here (read first)

The recommended route is the route with the **lowest supported MODELED
flood exposure under the currently available evidence**. It is **never**
a guarantee of safety:

- The Kushak hydraulic runtime has no stage and no depth (no
  storage–stage relation exists), so the system can never establish
  road passability or water depth.
- The risk translation therefore never emits `BLOCKED` or `SAFE` from
  model data. The best a segment can get from positive evidence is
  `LOW_RISK` ("no modeled runoff loading under the documented
  scenario") — and even that carries an explicit "not a guarantee of
  dry conditions" caveat in its reason.
- `UNKNOWN` is never `SAFE`: unknown segments carry a routing penalty,
  are listed explicitly, and force the route's evidence state down to
  LOW (weakest link).

## Architecture

```
            ┌─────────────────────────────┐
            │     SAFE ROUTING CORE       │
            │  backend/app/domain/delhi/  │
            │           routing/          │
            │  network.py  road graph     │
            │  risk.py     risk mapping   │
            │  engine.py   cost + search  │
            │  state_source.py adapters   │
            └──────────────┬──────────────┘
                           │ same engine, two state sources
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
     LIVE NOWCAST    HISTORICAL       EVIDENCE
     (nowcast        REPLAY (Phase    (route/segment
      ensemble)       15.5 harness)    provenance API)
```

- `network.py` — graph over the committed OSM-derived pilot GeoJSON
  (`backend/app/data/roads/delhi_kushak_roads.geojson`, 9,048 ways,
  acquired build-time via Overpass with a provenance sidecar; never
  scraped at runtime). Directed edges honoring one-ways; UTM 43N metric
  math; node snapping with an 800 m threshold; `lru_cache` singleton.
- `risk.py` — the ONLY place hydraulic state becomes road risk:
  - Spatial mapping: each road edge maps to its nearest reach centerline
    (UG-01 from the documented subsurface segment; OC-01/CD-01/OC-02 by
    chainage-fraction split of the open trunk) within a **150 m ASSUMED
    threshold**; otherwise `UNKNOWN` ("outside modeled corridor").
  - Translation (loading-based, stage-less):
    `blocked/missing member state → UNKNOWN`;
    `positive loading (inflow > 0 or storage above initial) → ELEVATED_RISK`;
    `zero loading across computed members → LOW_RISK`.
  - Member aggregation is **weakest-link**: any blocked member of the
    six makes the segment UNKNOWN. Ensemble disagreement is reported.
  - Route evidence state (documented derivation): UNKNOWN if no route
    segment has coverage; LOW if any segment is UNKNOWN (a single
    unknown portion caps the route — coverage is never averaged away);
    MEDIUM if fully covered with member disagreement; HIGH only when
    fully covered with full agreement.
  - Freshness: FRESH ≤ 15 min, RECENT ≤ 60 min, STALE beyond, UNKNOWN
    when no timestamp. Historical mode reports EVENT evidence timestamps
    and never presents them as live data age.
- `engine.py` — deterministic cost model and search:
  `edge_cost = travel_time_s + RISK_PENALTY_S_PER_M[state] × length_m`
  with documented ASSUMED weights: LOW 0.0, UNKNOWN 0.09 s/m
  (~1.5 min/km), ELEVATED 0.18 s/m (~3 min/km), BLOCKED hard-excluded.
  Travel speeds by OSM highway class are ASSUMED engineering defaults.
  Dijkstra with deterministic tie-breaking; the alternative route is a
  re-run with recommended roads re-costed (×4 divergence factor) and is
  returned only if it is genuinely distinct (edge-set difference ≥ 30%),
  otherwise `no_alternative_reason` explains why not.
- `state_source.py` — mode adapters producing the SAME per-member
  per-reach structure: LIVE from the cached deterministic nowcast
  ensemble at the departure hour; HISTORICAL from the genuine Phase 15.5
  replay runtime at event + timestep (cached per event). Historical
  adapters never read live state and vice versa.

## API

### `GET /api/delhi/safe-route`

| Param | Meaning |
| --- | --- |
| `origin_lon/lat`, `dest_lon/lat` | WGS84 coordinates (validated; snapped ≤ 800 m) |
| `mode` | `live` (default) or `historical` |
| `departure_hour` | LIVE: forecast hour 0–3 |
| `event_id`, `timestep_index` | HISTORICAL: catalogue event + replay timestep |

Response: `recommended_route` (geometry, distance, ASSUMED-speed travel
time, flood-risk summary, `route_state` = `LOWER_MODELED_RISK` or
`CONDITIONAL_UNKNOWN_RISK_PORTION`), `alternative_route` (or
`no_alternative_reason`), `route_comparison`, `evidence_state` (with the
derivation text), `explanation` (structured facts), `data_freshness`
(per-source timestamps), `provenance` (mode, event, model timestamp,
forcing source, road-network source + acquisition date, mapping method +
threshold, cost weights, member count), `route_run_id` (deterministic
hash of all route inputs — reproducible), `generated_at`, and a
`claim_policy` that states the modeled-exposure boundary.

Errors: 400 invalid coordinates / bad timestep; 404 unknown event or
segment; 409 historical routing requested for a non-executable event
(`NOT_COMPUTABLE` — absent forcing is never simulated).

### `GET /api/delhi/safe-route/segments/{segment_id}`

Segment-level evidence for ANY segment (route-agnostic): geometry
source, spatial mapping (method/threshold/mapped reach/status), risk
state + reason, underlying model state (per-reach ensemble aggregation),
model/forcing timestamps, mode/event/timestep, and the segment evidence
state. Missing information is `UNKNOWN`, never inferred. This is the
traceability chain: **route → segment → risk → model state → forcing →
source**.

## Historical replay behavior

- The historical route uses ONLY the replayed state of the selected
  event + timestep. No live state leaks in (test-enforced), and a
  historical run never mutates live state.
- Timestep risk is per-timestep: UNKNOWN timesteps produce UNKNOWN risk
  on the mapped corridor — the previous timestep's state is never
  carried forward, and nothing is interpolated between timesteps.
- Historical routes are labeled **MODEL RECONSTRUCTIONS** in the claim
  policy; they do not assert that a route was actually passable during
  the real event.
- Non-executable events (control, missing forcing) return HTTP 409 with
  `NOT_COMPUTABLE` — the system does not fabricate a historical route.

## Frontend

The ROUTE tab (Delhi V2) follows the flow: pick origin/destination on
the map → choose LIVE departure hour or HISTORICAL event + timestep
slider → Find route. The map draws the recommended route (thick, white
cased), the alternative (dashed), ELEVATED segments (amber), UNKNOWN
segments (dotted grey) — color plus line-style plus legend, never color
alone — with origin/destination pins. The panel shows the risk summary
chips, comparison table, the structured WHY panel, the evidence state
with its derivation, freshness timestamps, the run id, and a
click-through segment evidence inspector for any risk segment.

## Limitations

- Risk is loading-based: the runtime has no stage/depth, so ELEVATED
  means "modeled conveyance loading", not observed flooding, and BLOCKED
  is never produced by the model.
- Only corridor-adjacent roads (150 m threshold) receive model-informed
  risk; everything else is UNKNOWN. Most urban routes will therefore be
  LOW evidence with many UNKNOWN segments — that is the honest state of
  coverage, not a defect.
- Travel speeds and cost weights are ASSUMED engineering constants,
  documented and exposed in the API payload, not calibrated values.
- The road network is a bounded OSM pilot extract; route directness
  depends on OSM completeness (a 1.5–1.7× straight-line ratio is typical
  here; some origin pockets route longer).
- `route_run_id` reproducibility holds for identical inputs; a new
  forecast acquisition (live) legitimately changes the risk state and
  the run.
