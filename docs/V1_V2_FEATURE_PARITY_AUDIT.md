# V1 ↔ V2 FEATURE PARITY AUDIT

**Baseline identification (git history):**
- **V1 (proven product baseline):** commit `ec1ccb8` (2026-09-07) *"feat: complete flood nowcasting prototype and historical replay"* — the Mumbai/Kurla platform: map-first emergency UI, LIVE/NOW/+1h/+2h/+3h, MODEL SCENARIO (20/40/50/70 mm/h), HISTORICAL REPLAY (29 Aug 2017), street/intersection intelligence, flood-safe routing, provenance cards.
- **V2 (technical/data upgrade):** commit `d4ab4ba` (2026-09-16) *"feat(delhi): establish evidence-constrained Kushak digital twin baseline"* + extensive uncommitted Delhi work — Delhi/Kushak digital twin: 4-reach hydraulic chain (UG-01→OC-01→CD-01→OC-02), 6-member deterministic ensemble, historical replay harness, drainage graph, surface D8 pass, safe routing, radar probe, ML gating.
- **Checkpoint:** work performed on branch `v2-recovery-parity`; V1 code paths are **not** deleted — the Mumbai app remains functional at `FloodMap.tsx` + `/flood`, `/routing`, `/rainfall` routers.

**Legend:** PRESERVED · DEGRADED · MISSING · BETTER · BROKEN

---

## 1. FRONTEND

| Feature | V1 behavior (Mumbai) | Current V2 behavior (Delhi) | Status | Required action | Priority |
|---|---|---|---|---|---|
| Map-first layout | Full-viewport MapLibre map, all controls overlaid | Map present but small; panels stacked in a scrolling left column; visual hierarchy lost | **DEGRADED** | Rebuild Delhi layout on V1 geometry: map-dominant workspace, compact top bar, overlay panels | P0 |
| Compact top bar | `URBAN FLOOD NOWCAST | MUMBAI | subtitle | status pill | telemetry` | Similar but busier (chain labels, ensemble jargon in top bar) | **DEGRADED** | Slim to V1 pattern; move jargon to detail panels | P1 |
| Forecast timeline NOW/+1h/+2h/+3h | 4-step stepper with per-step rainfall tag; instant switching | NO horizon stepper at all; only a single forecast strip in NowcastPanel | **MISSING** | Implement horizon stepper driving independent per-horizon states | P0 |
| LIVE FORECAST / MODEL SCENARIO / HISTORICAL REPLAY modes | 3 explicit mode buttons with distinct styling + status pill | LIVE/SCENARIO/REPLAY tabs exist but tiny; SCENARIO = pre-baked synthetic scenarios, not V1-style what-if intensity | **DEGRADED** | Restore mode toggle group; add V1-style MODEL SCENARIO (intensity what-if) | P0 |
| Peak depth hero summary | Big risk card: depth in m, risk class, description, colored banner | Depth widget exists only inside ScenarioPanel; no live-mode hero | **MISSING** | Add hero status card for every mode | P0 |
| Flood-depth legend | Persistent legend card (4-band V1 ramp #ffeda0→#bd0026) | Legend only when depthCells present; different bands (2/10/30/60 cm) | **DEGRADED** | Persistent V1-style legend using V1 ramp | P1 |
| Full Extent / Target Zone | Two extent buttons + fly-to | None | **MISSING** | Add FULL EXTENT · DELHI / TARGET ZONE · KUSHAK | P1 |
| Flood-cell popup | Click cell → depth, risk, rainfall source, modelled-vs-observed | depthCells are circles without popups | **MISSING** | Add popups on depth cells/roads/intersections | P1 |
| Provenance card | Dedicated card: rainfall/boundary/elevation/flood/benchmarks/routing each labeled + disclaimer | Provenance scattered through panels; no single card | **MISSING** | Add provenance card | P0 |
| Street intelligence panel | Roads+junctions counts, risk pills, top corridors, overlay toggle, provenance footer | Only inside ScenarioPanel (road depths table); no live street panel | **MISSING** | Build street intel panel (live) | P0 |
| Intersection intelligence | Junction risk markers + popups | None (only GSDL occurrence circles) | **MISSING** | Intersections from OSM graph with mapped risk | P0 |
| Safe-route interaction | Click origin→dest, HUD panel with metrics/presets/avoided roads, route on map | RoutePanel exists (pick origin/dest) but no HUD, no presets, buried in panel | **DEGRADED** | Restore HUD-style routing UX | P1 |
| Historical replay | 24-step transport (play/pause/prev/next/peak), slider, forcing summary, benchmarks, validation table | ReplayPanel has playback + integrity checks; no benchmark/validation comparisons, no road overlay | **DEGRADED** | Add observed-benchmark comparison block (labeled OBSERVED vs MODELLED) | P1 |
| Loading/error states | Banner spinners + error banners | Per-panel status text | **PRESERVED** | Keep | P2 |
| Modelled-vs-observed distinction | Explicit labels everywhere (MODELLED, OBSERVED, SECONDARY-REPORT) | Even stricter than V1 (UNKNOWN preservation) | **BETTER** | Keep V2 honesty vocabulary; surface it in V1-style provenance card | P1 |

## 2. BACKEND

| Feature | V1 (Mumbai) | V2 (Delhi) | Status | Required action | Priority |
|---|---|---|---|---|---|
| Rainfall provider abstraction | `app.api.rainfall` composite adapter (Open-Meteo/IMD/mesonet) with cache TTL | `delhi.nowcast.fetch_delhi_rainfall_forecast` (Open-Meteo only, cache TTL 15 min) | **BETTER** (simpler, honest) | Keep; add explicit fallback state for UI smoothness | P1 |
| Independent +1h/+2h/+3h forecast states | `/flood/forecast` runs the pipeline once per horizon | Single nowcast payload; horizons derivable from bins but no per-horizon flood states | **MISSING** | Add per-horizon depth/street states endpoint | P0 |
| Runoff calculation | rainfall→runoff (C=0.7) in `flood_pipeline` | `rainfall_to_inflow` hydrograph conversion (C per member) | **BETTER** | Keep | — |
| Drainage capacity/surcharge | `domain/drainage.capacity` + curb inlets in pipeline | `drainage/loading.py` capacity classes + V1-port curb inlets in `scenarios/depth_v1` | **BETTER** | Keep; expose in live mode | P1 |
| Downstream propagation/backpressure | `drainage.propagation` (Mumbai network) | `kushak_continuity_routing` chain transfer | **BETTER** | Keep | — |
| Tailwater/boundary | Mumbai tidal boundary in replay | Explicit closed-boundary declarations (honest UNKNOWN) | **BETTER** | Keep | — |
| Surface routing | D8 in pipeline | `surface.py` D8 pass + `depth_v1` V1-equivalent routing | **BETTER** | Keep | — |
| Flood depth/extent output | GeoJSON polygons per horizon | depth cells + polygons exist but only for scenarios/replay | **MISSING in LIVE** | Expose in live mode per horizon | P0 |
| Street/intersection risk | `match_flood_to_streets` on OSM roads | Only scenario road depths; live mode has loading-based corridor risk only | **MISSING** | Add live street/intersection intelligence | P0 |
| Safe routing | `/routing/safe-route` (depth-based exclusion) | `/api/delhi/safe-route` (Dijkstra + risk penalties + evidence) | **BETTER** | Keep; add scenario mode | P1 |
| Historical replay | `/flood/historical/2017` with observed benchmarks + validation | 4-event catalogue, genuine runtime replay, integrity checks | **BETTER** | Keep; add benchmark comparison surface | P1 |
| Radar diagnostics | `infrastructure/rainfall/imd_radar` probe | `delhi/radar.py` probe + composite (RADAR vs NWP_FALLBACK) | **BETTER** | Keep | — |
| Scenario execution | `rainfall_mm_list` override in `/flood/forecast` + `/flood/streets?rainfall_mm=` | `/api/scenarios/*` (6 pre-baked) — no free-intensity what-if | **DEGRADED** | Add intensity-parameterised scenario endpoint | P0 |
| Health/status | `/health`, `/ready` | + `/api/delhi/status` | **BETTER** | Keep | — |
| Caching | Rainfall cache; historical replay cache | Replay/nowcast/science caches + lru_cached static products | **BETTER** | Keep + cache new endpoints deterministically | P1 |

## 3. DATA

| Item | V1 | V2 | Status | Action | Priority |
|---|---|---|---|---|---|
| DEM | Copernicus GLO-30 30 m (Mumbai) with synthetic-DEM fallback | Enforced GLO-30 30 m (Kushak) + conditioning products; no runtime fallback needed | **BETTER** | Keep | — |
| Roads | Mumbai OSM pilot roads/intersections | Delhi OSM extract (`delhi_kushak_roads.geojson`, 9k lines) + provenance JSON | **BETTER** | Build intersections from it | P0 |
| Drainage | BMC GIS 1,240 conduits (official) | DERIVED corridor graph (no official GIS available) with INFERRED_EFFECTIVE capacity classes | **DIFFERENT** (honest) | Keep labeling; document in matrix | — |
| Rainfall | Open-Meteo NWP | Open-Meteo NWP at Safdarjung reference | **PRESERVED** | Keep | — |
| Observations | 4 observed 2017 benchmarks (real) | GSDL official occurrences + documented event evidence | **BETTER** | Keep | — |

## 4. SIH PROBLEM-STATEMENT COVERAGE

| Requirement | Current support | Data source | Backend | Frontend | Fallback | Status |
|---|---|---|---|---|---|---|
| Rainfall nowcast (0–3h) | NWP hourly bins, provenance DERIVED | Open-Meteo @ Safdarjung | `/api/delhi/nowcast` | forecast strip | STALE cache; **no synthetic fallback → UI dead-ends when offline** | PARTIAL |
| Terrain/DEM | Enforced 30 m DEM, D8 products | GLO-30 + stream burn | `surface.py` structure | corridor layers | n/a | ✅ |
| Catchment | 27.66 km² working watershed (PROVISIONAL) | D8 delineation | `/geo/watershed` | map layer | n/a | ✅ |
| Runoff | Rainfall→inflow hydrograph, C per member | — | `rainfall_to_inflow` | envelope chart | UNKNOWN bins blocked, never zero-filled | ✅ |
| Drainage network | 4-reach chain + derived graph | Appendix XII geometry | `/drainage-graph` | dashed overlay | INFERRED_EFFECTIVE capacities labeled | ✅ |
| Capacity/storage | Capacity classes + storage states | — | `drainage/loading.py` | loading table | ASSUMED initial storage documented | ✅ |
| Surcharge/backpressure | Loading breach = POTENTIAL_OVERLOAD; curb-inlet surcharge in depth model | — | loading + depth_v1 | tables + map | labeled scenario-derived | ✅ |
| Surface flow/depth | D8 equilibrium + depression caps | enforced DEM | `surface.py`, `depth_v1` | depth polygons (scenario/replay only) | DSM caveat labeled | ✅ backend / ⚠️ live frontend |
| Flood extent | depth polygons | — | depth_v1 | map (scenario/replay only) | — | ⚠️ live missing |
| Street risk | corridor-mapped ELEVATED/LOW/UNKNOWN | OSM roads | routing/risk | route panel only | UNKNOWN labeled | ⚠️ live street panel missing |
| Intersection risk | none | OSM graph | — | — | — | ❌ MISSING |
| Safe routing | flood-aware Dijkstra + evidence states | OSM graph + model states | `/safe-route` | RoutePanel | UNKNOWN penalty | ✅ (needs scenario mode) |
| Historical replay | 4 events, 2 executable | catalog forcing | `/events/{id}/replay` | ReplayPanel | NOT_EXECUTED states preserved | ✅ (needs validation surface) |
| Scenario what-if | 6 pre-baked synthetic runs | seeded synthetic | `/api/scenarios/*` | ScenarioPanel | SYNTHETIC labeled | ⚠️ free-intensity missing |
| Provenance | Every payload labeled | — | everywhere | scattered | — | ⚠️ needs V1-style card |

## 5. REQUIRED ACTIONS (ordered)

1. **P0 — Live flood depth per horizon (backend + frontend):** new endpoint `/api/delhi/live-state?horizon=NOW|+1h|+2h|+3h` returning V1-style depth polygons + stats per forecast hour, cached per forecast acquisition.
2. **P0 — Live street/intersection intelligence (backend + frontend):** extend live-state with OSM road/intersection matching (depth-sampled from the same model state; UNKNOWN preserved).
3. **P0 — V1-style Delhi frontend layout:** top bar, mode toggle (LIVE FORECAST / MODEL SCENARIO / HISTORICAL REPLAY), horizon stepper, hero risk card, street intel panel, provenance card, legend, extent buttons, popups.
4. **P0 — Free-intensity MODEL SCENARIO (what-if):** `/api/delhi/scenario/what-if?rainfall_mm=X` running the same V1 depth model, labeled MODEL_SCENARIO/WHAT-IF.
5. **P1 — Synthetic rainfall fallback (labeled):** when Open-Meteo is unreachable, a clearly marked `SYNTHETIC_FALLBACK` rainfall series keeps the demo alive (never presented as observed/live).
6. **P1 — Safe-route scenario mode** + route HUD presets.
7. **P1 — Replay validation block:** observed vs modelled benchmark comparison where documented evidence exists.
8. **P2 — Perf pass:** cache all new deterministic endpoints; precompute street geometry.
