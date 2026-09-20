# Safe Routing Implementation Report

**Final verdict: SAFE_ROUTING_COMPLETE_WITH_DOCUMENTED_LIMITATIONS**

The safe-routing feature is complete end-to-end (backend engine, API,
frontend, map, tests, documentation) and fully integrated with all three
system modes. The "WITH_DOCUMENTED_LIMITATIONS" qualifier reflects
structural scientific limits that are explicitly surfaced rather than
hidden: the hydraulic runtime has no stage/depth, so road risk is a
loading-based translation (never passability), and only corridor-adjacent
roads receive model-informed risk (everything else is honestly UNKNOWN).

## 1. Architecture

ONE routing core (`backend/app/domain/delhi/routing/`) serves all modes:

| Module | Role |
| --- | --- |
| `network.py` | Directed graph over the committed OSM pilot GeoJSON (9,048 ways, 38,736 nodes, 75,619 edges, 98.3% in the main component); UTM 43N; snapping ≤ 800 m; cached singleton |
| `risk.py` | Edge→reach spatial mapping (150 m ASSUMED threshold; outside → UNKNOWN); documented hydraulic→road-risk translation; weakest-link member aggregation; route evidence state; freshness classification |
| `engine.py` | Deterministic Dijkstra with flood-aware cost; genuinely-distinct alternative search; route comparison; structured explanation; `route_run_id` |
| `state_source.py` | Mode adapters: LIVE (cached deterministic nowcast ensemble at departure hour) and HISTORICAL (genuine Phase 15.5 replay runtime at event + timestep), both emitting the same per-member per-reach structure |

Data acquisition: `scripts/fetch_delhi_roads.py` fetched the bounded
Kushak-area network once (build time) via Overpass into
`backend/app/data/roads/delhi_kushak_roads.geojson` + a provenance
sidecar (bbox, query, timestamp) — the same committed-artifact pattern
as the Mumbai pilot, and never a runtime scrape.

## 2. Changed / created files

Created:

- `scripts/fetch_delhi_roads.py`
- `backend/app/data/roads/delhi_kushak_roads.geojson` (+ `.provenance.json`)
- `backend/app/domain/delhi/routing/{__init__,network,risk,engine,state_source}.py`
- `backend/tests/test_delhi_safe_routing.py` (23 tests)
- `frontend/src/components/delhi/RoutePanel.tsx`
- `docs/SAFE_ROUTING.md`, this report

Modified:

- `backend/routers/delhi.py` — `/api/delhi/safe-route` + segment evidence endpoint
- `frontend/src/api/delhi.ts` — SafeRoute types + client methods
- `frontend/src/components/delhi/DelhiMap.tsx` — route layers, pins, click picking, risk-segment click-through, route legend
- `frontend/src/components/delhi/DelhiApp.tsx` — ROUTE tab + shared routing state
- `frontend/src/styles/delhi.css` — routing UI styles
- `docs/FINAL_SYSTEM_COMPLETION_REPORT.md` — routing section

## 3. API

- `GET /api/delhi/safe-route` — params: `origin_lon/lat, dest_lon/lat,
  mode=live|historical, departure_hour=0..3, event_id, timestep_index`.
  Returns recommended + alternative routes (geometry, distance,
  ASSUMED-speed time, risk summary, route_state), route_comparison,
  evidence_state (+derivation), explanation (structured facts),
  data_freshness (per-source timestamps), provenance (model timestamp,
  forcing source, road-network source + acquisition, mapping method +
  threshold, cost weights), deterministic `route_run_id`, generated_at,
  claim policy. Errors: 400 (invalid input/unroutable), 404 (unknown
  event/segment), 409 (historical routing on a non-executable event —
  `NOT_COMPUTABLE`).
- `GET /api/delhi/safe-route/segments/{segment_id}` — segment evidence
  with the full traceability chain (segment → mapping → reach → model
  state → forcing → timestamps), route-agnostic.

## 4. Routing algorithm

`edge_cost = travel_time_s (ASSUMED speeds by OSM class) + risk_penalty_s_per_m × length_m`
with LOW 0.0 / UNKNOWN 0.09 / ELEVATED 0.18 / BLOCKED hard-excluded
(ASSUMED engineering constants, exposed in every API response).
Deterministic Dijkstra; alternative = re-run with recommended roads ×4
re-costed, accepted only if ≥ 30% edge-set distinct, else an explicit
`no_alternative_reason`.

## 5. Risk mapping & UNKNOWN handling

- Translation (the only hydraulic→road mapping): blocked/missing member
  → UNKNOWN; positive loading → ELEVATED_RISK; zero loading → LOW_RISK.
  SAFE and BLOCKED are never emitted (no stage/depth exists).
- Weakest-link aggregation over the 6-member ensemble; disagreement
  reported, never hidden.
- Segments outside the 150 m corridor threshold are UNKNOWN ("outside
  modeled corridor").
- UNKNOWN is penalized in routing (never free, never safe), listed
  explicitly, forces `CONDITIONAL_UNKNOWN_RISK_PORTION` labeling when on
  a route, and caps route evidence at LOW.

## 6. Freshness & evidence state

FRESH/RECENT/STALE/UNKNOWN with documented thresholds (15/60 min). LIVE
routes carry the forecast acquisition timestamp and model timestep;
HISTORICAL routes carry the event's forcing anchor and timestep —
event-date, model-execution-date, and live-data timestamps are kept
distinct fields. Route evidence state derivation is documented in the
API response itself (weakest link).

## 7. Recommended / alternative behavior

The optimizer prefers lower modeled exposure over distance; when the
shortest path is also lowest-exposure the explanation states the risk
profile, and when an alternative trades distance against exposure the
explanation quantifies it from actual metrics (e.g. "0.55 km longer …
with 15 fewer UNKNOWN segments"). If no genuinely distinct alternative
exists the response says so instead of fabricating one.

## 8. Historical replay support

Event + timestep select the replay runtime state; the same engine maps
it to road risk. Verified: timestep 0 (verified-zero hour) → LOW corridor
risk; timestep 1 (the 91 mm/h hour) → ELEVATED on UG-01-adjacent
segments; timestep 2 (UNKNOWN hour) → UNKNOWN, no carry-forward, no
interpolation. Cross-mode isolation is test-enforced (no live leakage
into historical, no historical mutation of live, engine never mutates
model state).

## 9. Frontend

ROUTE tab: mode toggle (LIVE NOWCAST / HISTORICAL REPLAY), departure-hour
buttons or event select + timestep slider, map-click origin/destination
picking with pins, Find route, then recommended/alternative rendering
(thick white-cased blue vs dashed grey), ELEVATED (amber) and UNKNOWN
(dotted) segment overlays with legend (style + color + label),
stat/risk chips, WHY panel (structured facts), comparison table, evidence
panel with freshness + run id, and click-through segment evidence.
Invalid picks surface the exact API error (e.g. snapping distance).

## 10. Test counts

- 23 safe-routing tests (unit + integration + API + cross-mode
  isolation), all green.
- Full repository suite: **1085 passed, 0 failed**
  (`backend/app/domain/delhi` + `backend/tests`).

## 11. Known limitations

See `docs/SAFE_ROUTING.md` § Limitations: loading-based risk (no
stage/depth exists), corridor-only coverage (else UNKNOWN), ASSUMED
speeds/weights, bounded OSM pilot network, and live-mode reproducibility
scoped to identical inputs.

## 12. Exact commands used

```bash
backend/venv/Scripts/python.exe scripts/fetch_delhi_roads.py      # one-time network acquisition
backend/venv/Scripts/python.exe -m pytest backend/tests/test_delhi_safe_routing.py -q
backend/venv/Scripts/python.exe -m pytest backend/app/domain/delhi backend/tests -q
cd frontend && npm run build
```

## 13. Final git status summary

Untracked additions: the routing package, tests, frontend RoutePanel,
docs, and the committed road-network artifact. Modified: `delhi.py`
router, `delhi.ts`, `DelhiMap.tsx`, `DelhiApp.tsx`, `delhi.css`, the
final completion report. No Mumbai V1 files touched; no hydraulic model
changes; historical replay behavior unchanged except the routing
integration reading its runtime outputs.
