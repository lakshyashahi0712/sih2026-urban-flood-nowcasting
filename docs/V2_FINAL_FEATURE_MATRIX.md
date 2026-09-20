# V2 FINAL FEATURE MATRIX

Delhi V2 after the V1-parity recovery (branch `v2-recovery-parity`).
Every row names the backend API, the frontend surface, the data source, the
fallback, and the provenance label the user actually sees.

Legend — **Working?**: ✅ verified in browser / tests · ⚠️ partial · ❌ absent.
**Test** column: B = backend pytest, E = browser E2E (this session), — = manual.

---

## 1. LIVE FORECAST CHAIN (RAIN → RUNOFF → DRAINAGE → SURFACE → DEPTH → RISK → ROUTING)

| Feature | Backend API | Frontend UI | Data source | Fallback | Provenance shown | Working? | Test |
|---|---|---|---|---|---|---|---|
| Live rainfall provider | `GET /api/delhi/live-state` (Open-Meteo NWP ingest) | Horizon stepper `NOW / +1h / +2h / +3h` with per-hour mm tags | Open-Meteo hourly NWP (model value) | `SYNTHETIC_FALLBACK` deterministic field when NWP unreachable — never labeled observed | "Rainfall: Open-Meteo NWP (COMPUTED)" / `NWP_FALLBACK` / `SYNTHETIC_FALLBACK` | ✅ | B, E |
| Rainfall–runoff | `live_state.py` → V1 reference pipeline (C=0.75, 60-min step) | Water-balance card: runoff / conveyed / surcharged / overflow / drained | DEM-derived catchment | n/a (physical model) | "Runoff C = 0.75 • SIMULATED MODEL OUTPUT" | ✅ | B |
| Inlet conveyance + surcharge | curb-inlet capacity vs. total runoff ÷ n_inlets (V1 rule) | Water-balance "Surcharged to surface" row | Derived drainage attributes | `ASSUMED` capacity documented in config | "Drainage: DERIVED / INFERRED_EFFECTIVE (not as-built)" | ✅ | B |
| Surface routing / ponding | depression-filling on enforced 30 m DSM | Depth polygons on map (1,296 cells) | Copernicus GLO-30 DSM (30 m, enforced) | Verified available DEM only — never claimed high-res | "Elevation: Copernicus GLO-30 DSM (30m, enforced)" | ✅ | B |
| Per-horizon depth states NOW/+1/+2/+3 | `GET /api/delhi/live-state?horizon=NOW|+1h|+2h|+3h` — each simulated independently with only its own hour's rain | Clickable horizon stepper; hero card + map + streets all switch | Same pipeline per hour | UNKNOWN hours stay UNKNOWN (never zero-filled) | "HORIZON +1h COMPUTED · Hour beginning … · rainfall provenance DERIVED" | ✅ | B, E |
| Peak depth + inundated area | computed in live-state | Hero card: risk class, peak depth (m/cm), inundated m² | Model output | n/a | "PREDICTED RISK … Peak Inundation" | ✅ | B, E |
| Dose–response sanity | 20 mm/h → 0 m · 40 → 0.64 m · 70 → 1.35 m (V1-identical) | Risk class follows depth thresholds | — | — | — | ✅ | B |

## 2. STREET + INTERSECTION INTELLIGENCE

| Feature | Backend API | Frontend UI | Data source | Fallback | Provenance shown | Working? | Test |
|---|---|---|---|---|---|---|---|
| Street flood risk | `live-state` → OSM segments matched to depth grid (KD-tree, 3-sample max per segment) | "STREET FLOOD RISK" card: passable/impassable counts, risk pills, named corridors | OpenStreetMap roads | Segments beyond match distance = `UNKNOWN`, never 0 m | "OSM roads/junctions matched to the modelled depth grid • Not municipal road sensors" | ✅ | B, E |
| Intersection risk | junctions from road topology, max depth over ~30 m neighborhood | Junction count in intel card + markers on map | OSM junctions | Same UNKNOWN rule | Same as above | ✅ | B, E |
| Map street overlay | `street-risk-roads` / `street-risk-junctions` GeoJSON sources | Color-coded segments + clickable popups | Model output | — | depth + risk class per feature | ✅ | E |
| Affected counts | per-horizon | Hero: "7,382 street segments · 5 junctions affected" (scenario 70) | — | — | — | ✅ | B, E |

## 3. FLOOD-AWARE ROUTING

| Feature | Backend API | Frontend UI | Data source | Fallback | Provenance shown | Working? | Test |
|---|---|---|---|---|---|---|---|
| Safe route (live) | `POST /api/delhi/safe-route` — Dijkstra with hazard costs from active horizon state | Route panel: geometry on map, distance, max depth on route, roads avoided, risk summary | Road graph + live depth | Coherent synthetic route graph if OSM graph unavailable | "lowest supported MODELED flood exposure — never a guarantee" | ✅ | B, E |
| Safe route (scenario) | same endpoint, `mode=scenario&intensity=` → what-if edge depths | Route recomputes around flooded segments at 40/70 mm/h | what-if depth cache | — | "MODELLED" | ✅ | B, E |
| Route follows mode switch | live ↔ scenario ↔ replay state source | Map + summary update without page reload | — | — | — | ✅ | E |

## 4. MODEL SCENARIO (WHAT-IF)

| Feature | Backend API | Frontend UI | Data source | Fallback | Provenance shown | Working? | Test |
|---|---|---|---|---|---|---|---|
| Scenario execution | `GET /api/scenarios/delhi/what-if?intensity=` — real backend computation | MODEL SCENARIO mode, intensity buttons 20/40/50/70 mm/h | Hypothetical uniform rainfall | — | "WHAT-IF: hypothetical uniform rainfall … not live weather" · `MODEL_SCENARIO` | ✅ | B, E |
| Scenario → map/streets/routing | what-if edge-depth cache (deterministic) | Map overlays, hero (40→HIGH 0.64 m · 70→SEVERE 1.34 m), street intel all update | — | — | — | ✅ | B, E |
| LIVE vs SCENARIO separation | distinct endpoints + labeled UI | Mode toggle always visible; scenario badge in top bar | — | — | — | ✅ | E |

## 5. HISTORICAL REPLAY

| Feature | Backend API | Frontend UI | Data source | Fallback | Provenance shown | Working? | Test |
|---|---|---|---|---|---|---|---|
| Event selection | replay events API — 6 events (3 replayable) | Event list with status chips (REPLAY READY / PARTIAL / CONTROL / NO FORCING) | GSDL documented events (OBSERVED) | Synthetic events would be labeled `SYNTHETIC / DEMO VALIDATION` (none currently presented as observed) | "OBSERVED · DOCUMENTED EVIDENCE" | ✅ | E |
| Timeline + playback | per-timestep state | Prev/Play/Next, REPLAY T clock chip, map follows replay clock | Documented forcing at preserved resolution | UNKNOWN hours preserved, never zero-filled | "documented forcing (computed) / step blocked downstream / UNKNOWN" | ✅ | B, E |
| Observed vs modelled separation | integrity panel | Forcing provenance chips per bin (VERIFIED_ZERO / OBSERVED_DIRECT / UNKNOWN) | — | — | "MODEL-RECONSTRUCTED STATE: MODEL-DERIVED" | ✅ | B, E |
| Runtime integrity checks | mass balance, terminal outfall, unknown propagation | RUNTIME INTEGRITY CHECKS panel | Runtime-derived | — | "NOT an accuracy/calibration claim" | ✅ | B |

## 6. PROVENANCE & STATUS

| Feature | Backend API | Frontend UI | Data source | Fallback | Provenance shown | Working? | Test |
|---|---|---|---|---|---|---|---|
| Per-domain provenance card | every response carries provenance enums | "DATA PROVENANCE & STATUS" card: Rainfall / Elevation / Flood depth / Roads / Drainage / Observations | all | all fallbacks labeled | OFFICIAL / OBSERVED / DERIVED / ASSUMED / MODELLED / SYNTHETIC_FALLBACK vocabulary | ✅ | B, E |
| Radar status | radar provider abstraction (Visual/quantitative distinction) | Diagnostics surface | IMD radar when quantitative grid available | `NWP_FALLBACK` field — no color-decoded fake rainfall | RADAR STATUS honest label | ✅ | B |
| No-fabrication rule | — | UI copy enforced ("never observed", "not observed rainfall") | — | — | — | ✅ | E |

## 7. PERFORMANCE / CACHING

| Feature | Implementation | Working? | Test |
|---|---|---|---|
| Deterministic live-state cache | horizon results cached; scenario what-if edge depths cached per intensity | ✅ | B |
| Precomputed geometry | road/junction match index (55k segments + KD-tree) built once | ✅ | B |
| Responsive scenario calls | cached intensity results; no page reload needed anywhere | ✅ | E |
| Frontend | map-first render, panels load async, loading states, stale-overlay-free (sources keyed to active mode) | ✅ | E |

## 8. CITY ARCHITECTURE

| Feature | Status | Working? |
|---|---|---|
| Mumbai V1 retained | `MUMBAI V1 LEGACY` tab intact — all V1 tests (17) pass | ✅ |
| Delhi independent | `DELHI V2 CURRENT` tab runs standalone on its own catchment config | ✅ |
| Shared engine concept | V1 reference depth model reused via `depth_v1.py`; city-specific configs | ✅ |

## 9. TESTS / BUILD / E2E

| Check | Result |
|---|---|
| Backend pytest (full suite incl. 17 new parity tests) | **481 passed** (0 failed) |
| Frontend TypeScript + production build | **clean** |
| Browser E2E | LIVE → NOW → +1h/+2h/+3h → MODEL SCENARIO (40/70) → street intel → scenario safe route → HISTORICAL REPLAY (event + timeline + playback) → LIVE — **all pass**, console clean (only third-party basemap tile warnings) |
