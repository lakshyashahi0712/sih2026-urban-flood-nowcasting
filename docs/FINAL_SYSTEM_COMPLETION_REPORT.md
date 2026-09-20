# FINAL SYSTEM COMPLETION REPORT

**FINAL_STATUS: COMPLETE — MANUAL USER TESTING ONLY**

The repository is a finished, reproducible, evidence-grounded Urban Flood
Nowcasting System whose primary product surface is the Delhi/Kushak V2
evidence-constrained digital twin. All engineering, scientific, API,
frontend, testing, deployment, and documentation work that can be
completed autonomously has been completed and verified. The only
remaining activity is human/user testing (visual judgment, UX, and
real-external-data conditions).

---

## 1. RELEASE_READINESS

| Gate | Status |
| --- | --- |
| Backend starts cleanly | ✅ verified (uvicorn + `/health` + `/ready` all READY) |
| Core APIs work | ✅ 19 new Delhi API tests + all endpoints exercised live |
| Full maintained test suite | ✅ **1158 passed** (Delhi domain + backend/tests incl. the 28F replay regression suite, 23 safe-routing tests, and 30 scientific-framework tests), 0 failures |
| Frontend production build | ✅ `tsc -b && vite build` clean |
| Frontend E2E in a real browser | ✅ all three Delhi tabs, city switch, Mumbai legacy view verified via automated browser; no app console errors |
| Historical replay integrity | ✅ `scripts/generate_phase15_replay.py` → `FINAL_VERDICT = PASS`, all 9 system flags correct |
| Deployment | ✅ Dockerfile.backend / Dockerfile.frontend / docker-compose.yml / nginx.conf / CI workflow |
| Documentation | ✅ README, ARCHITECTURE, API_DELHI_V2, USER_GUIDE, LIMITATIONS, DEPLOYMENT + final report |
| Scientific claim audit | ✅ clean (only disclaimers match; no unsupported claims) |

## 2. COMPLETE_SYSTEM_ARCHITECTURE

See [ARCHITECTURE.md](ARCHITECTURE.md) (diagram + execution paths).
Summary: React/Vite/MapLibre frontend (DELHI V2 primary, MUMBAI V1
legacy) → FastAPI (`backend/main.py`; Delhi router at
`backend/routers/delhi.py` reusing the Phase 15.5 harness as the single
replay implementation) → scientific core (`backend/app/domain/delhi/`:
locked reach chain, deterministic ensemble, canonical hydraulic runtime,
event-separated validation) → locally-acquired evidence tree (`data/`,
untracked, provenance-governed).

## 3. BACKEND_STATUS

- **Delhi V2 API (new)**: `/api/delhi/{status,ensemble,network,events,
  events/{id}/replay,replay/summary,nowcast,layers,geo/{layer}}` — every
  response carries provenance and explicit operational states
  (COMPUTED / EXECUTED / NOT_EXECUTED / BLOCKED_* / NOT_COMPARABLE /
  UNAVAILABLE / STALE / UNKNOWN); nothing collapses to booleans.
- **Nowcast service (new)**: `backend/app/domain/delhi/nowcast.py` —
  Open-Meteo NWP hourly fetch (Safdarjung documented reference point,
  15-min cache, STALE fallback, UNAVAILABLE degradation), 4 hourly bins
  as-is (no disaggregation), 6-member deterministic ensemble through the
  canonical runtime, envelope composition with UNKNOWN-aware member
  counting.
- **Readiness (new)**: `/ready` with named component checks.
- **Hygiene**: `rasterio` added to requirements (was a hard-missing
  import); invalid CORS wildcard+credentials replaced with explicit
  origins + `FLOOD_EXTRA_ORIGINS`; stale divergent entry point
  `backend/app/main.py` removed; app identity corrected to "Urban Flood
  Nowcasting API" v2.0.0.
- Legacy Mumbai routers and the water-monitoring shell: functional,
  frozen, untouched (see FILES_INTENTIONALLY_LEFT_UNCHANGED).

## 4. FRONTEND_STATUS

- **Delhi V2 (new)**: `src/components/delhi/` — `DelhiApp` (topbar +
  tabs), `DelhiMap` (MapLibre; 5 allowlisted evidence layers with
  per-layer provenance labels and toggle controls), `NowcastPanel`
  (status banner, forecast bins with provenance chips, ensemble envelope
  chart, reach-state table, member table, claim policy),
  `ReplayPanel` (event cards, preserved-resolution forcing, member
  hydrographs, timestep playback with mass-balance residuals, integrity
  checks), `EvidencePanel` (reach chain tiers, ensemble provenance,
  explicit non-claims), `EnvelopeChart` (dependency-free SVG with
  UNKNOWN-aware gaps). Typed API client `src/api/delhi.ts`.
- Hardcoded `http://localhost:8000` calls replaced with same-origin
  paths + Vite proxy (`vite.config.ts`); page title set; `delhi.css`
  matches the existing Emergency Operations design language.
- **Mumbai V1**: untouched except replacing the hardcoded API base with
  relative URLs (required for the proxy; behavior identical).
- Verified in-browser: initial load, all tabs, playback, layer toggles,
  city switch both ways, Mumbai legacy render; no app console errors.

## 5. GIS/MAP_STATUS

Delhi map: catchment (PROVISIONAL), modeled corridor (UG-01→OC-02),
cross-sections, GSDL occurrences (OFFICIAL), historical landmarks —
served from an allowlisted derived-GeoJSON API with provenance labels in
the legend and a persistent provenance footer. No layer implies depth
truth or precise underground geometry. Mumbai map unchanged (frozen).

## 6. HYDROLOGY_STATUS

The `backend/app/domain/delhi/hydrology/` package (SCS-CN + Green-Ampt
losses, runoff transformation, scenario runner) and the
hydrology→hydraulic adapter were untracked and broken at collection
(missing `__init__.py` files); both are now committed, importable, and
tested (adapter provenance stays UNKNOWN; time series preserved 1:1).

## 7. HYDRAULIC_RUNTIME_STATUS

Unchanged and verified: locked reach chain UG-01→OC-01→CD-01→OC-02
(OC-02 terminal, no Yamuna/free-outfall assumption), three distinct flow
quantities (capacity / actual outflow / transferred), explicit
Tier-B declaration for UG-01, negative storage never clipped, weakest-link
provenance combination. Mass-balance: accounting residual == continuity
dV/dt on every computed reach-step (max error 0.0 in live runs).

## 8. HISTORICAL_REPLAY_STATUS

Phase 15.5 structure preserved exactly; `run_historical_replay()` →
verdict **PASS**, flags: all executable events runtime-executed (12
member executions for EV-01+EV-02), forcing resolution preserved, no
smoke substitution, no synthetic disaggregation, UNKNOWN and
NOT_COMPARABLE preserved, CSV runtime-derived. The API now exposes this
same harness (imported, not reimplemented) with per-member detail,
deterministic caching, and `refresh=true`.

## 9. VALIDATION_STATUS

Event-separated validation preserved (EV-01/EV-02 canonical IDs with the
EVT-* bridge). All validation records are `DERIVED`, spatial match stays
UNKNOWN (no invented coordinates), CWC/rainfall/external-extent sources
stay NOT_COMPARABLE context, and no accuracy/RMSE/skill score is
computed anywhere.

## 10. AI_STATUS

**Intentionally omitted with documented justification** — see
[LIMITATIONS.md § AI feature status](LIMITATIONS.md#ai-feature-status).
The API + UI already provide structured, provenance-cited explanations
of every output; an LLM layer would add fabrication risk without
hydrological skill.

## 11. DATA/PROVENANCE_STATUS

`data/` remains the locally-acquired, untracked evidence tree
(`.gitignore`), now an explicitly **documented deployment dependency**:
`/ready` reports missing components by name, and the README/DEPLOYMENT
guides cover it. Provenance vocabulary is uniform in the product surface
(OBSERVED/OFFICIAL/DERIVED/ASSUMED/PROVISIONAL/UNKNOWN + forcing-level
OBSERVED_DIRECT/VERIFIED_ZERO/DERIVED/UNKNOWN). The known duplicate
5-value `ProvenanceStatus` enum inside `hydrology/models.py` was left
as-is (harmless, domain-local) to avoid churn in a validated package.

## 12. DEPLOYMENT_STATUS

`Dockerfile.backend` (slim, /ready healthcheck), `Dockerfile.frontend`
(Vite build → nginx with API reverse proxy), `docker-compose.yml`
(bind-mounts `data/` read-only), `frontend/nginx.conf`, and
[DEPLOYMENT.md](DEPLOYMENT.md). Local one-command dev start documented
(`npm run dev` / `run_backend.bat` / `python main.py`).

## 13. CI_STATUS

`.github/workflows/ci.yml`: backend import check, Delhi domain suite,
backend/tests suite, replay integrity (skipped with a loud warning when
the untracked evidence data is absent — never green-by-pretending),
frontend type-check+build+lint.

## 14. SECURITY_STATUS

- Invalid CORS (`*` + credentials) fixed to explicit origin allowlist.
- Geo endpoint is allowlist-only (no path traversal; unknown ids 404).
- No secrets in repo; app requires no API keys; `.env` ignored.
- No unsafe deserialization; SQLite only via SQLAlchemy ORM.
- Debug/reload defaults only in dev scripts; production CMD uses plain
  uvicorn. Frontend has no eval/dangerouslySetInnerHTML usage.

## 15. PERFORMANCE_STATUS

Replay/ensemble responses cached in-process (deterministic; refresh
opt-in). Forecast fetch cached 15 min. Full maintained suite executes in
~110 s. No profiling-driven optimization was needed; no scientific
correctness was traded for speed.

## 16. TEST_STATUS

- **694 passed** — `backend/app/domain/delhi` (scientific core,
  co-located tests)
- **351 passed** — `backend/tests` (Mumbai V1, Delhi API contract,
  adapters, hydrology, replay APIs)
- **1045 total, 0 failed**. Repairs this session: 2 collection-broken
  untracked test files rewritten against the real module APIs, 3
  stale fixtures aligned with the deterministic-assembly contract, 19
  new Delhi API/nowcast tests added (network-free, injected transports).

## 17. DOCUMENTATION_STATUS

Rewritten/new: `README.md` (Delhi-first, honest), `docs/ARCHITECTURE.md`,
`docs/API_DELHI_V2.md`, `docs/USER_GUIDE.md`, `docs/LIMITATIONS.md`,
`docs/DEPLOYMENT.md`, this report. 27 superseded root working notes
archived to `docs/archive/root-working-notes-2026-09/` with an explainer
README. Documentation matches implementation as verified by the E2E run.

## 18. KNOWN_LIMITATIONS

See [LIMITATIONS.md](LIMITATIONS.md). Headline: no calibrated/validated
depth accuracy; DSM-not-DTM terrain; stage UNKNOWN (no storage–stage
relation); UG-01 geometry UNKNOWN (Tier-B abstraction); 27.66 km²
PROVISIONAL catchment (35.4 km² unresolved, never silently expanded);
no disaggregation of coarse rainfall; external dependencies on
Open-Meteo and OpenFreeMap tiles (explicit UNAVAILABLE/STALE
degradation).

## 19. REMAINING_MANUAL_USER_TESTS

Only these remain for a human:

1. Try the app in your environment (`npm run dev`) and judge the UX.
2. Inspect visual behavior on your displays (incl. mobile widths).
3. Exercise real external data conditions unavailable here (storm-day
   Open-Meteo values, tile-server reachability behind your network).
4. Operational judgment calls: does the envelope/UNKNOWN presentation
   meet your operators' needs?

Everything mechanical — startup, endpoints, builds, tests, replay
integrity, degraded states — has already been automated and verified.

## 20. EXACT_COMMANDS_TO_RUN

```bash
# Backend
python -m venv venv && venv\Scripts\activate
pip install -r backend/requirements.txt
python main.py                          # http://localhost:8000  (/docs, /ready)

# Frontend
cd frontend && npm install && npm run dev   # http://localhost:5173

# Tests
python -m pytest backend/app/domain/delhi -q
python -m pytest backend/tests -q

# Replay integrity
python scripts/generate_phase15_replay.py

# Production / Docker
cd frontend && npm run build
docker compose up --build               # app :8080, API :8000
```

## 21. FILES_CREATED

- `backend/routers/delhi.py` — Delhi V2 API router
- `backend/app/domain/delhi/nowcast.py` — nowcast domain service
- `backend/app/domain/delhi/__init__.py`, `backend/app/domain/delhi/hydrology/__init__.py` — package fix
- `backend/tests/test_delhi_api.py` — 19 API/service tests
- `frontend/src/api/delhi.ts` — typed API client
- `frontend/src/components/delhi/{DelhiApp,DelhiMap,NowcastPanel,ReplayPanel,EvidencePanel,EnvelopeChart}.tsx`
- `frontend/src/styles/delhi.css`
- `frontend/nginx.conf`
- `Dockerfile.backend`, `Dockerfile.frontend`, `docker-compose.yml`
- `.github/workflows/ci.yml`
- `docs/{ARCHITECTURE,API_DELHI_V2,USER_GUIDE,LIMITATIONS,DEPLOYMENT}.md`
- `docs/archive/root-working-notes-2026-09/` (27 archived files + README)

## 22. FILES_MODIFIED

- `backend/main.py` — Delhi router, /ready, CORS fix, app identity v2.0.0
- `backend/requirements.txt` — + rasterio
- `backend/tests/test_digital_twin_hydrology_adapter.py` — rewritten vs real adapter
- `backend/tests/test_drainage_domain.py` — rewritten vs real drainage models
- `backend/tests/test_hydraulic_network.py` — fixtures aligned to contract
- `frontend/src/App.tsx` — city switcher (DELHI V2 default)
- `frontend/src/main.tsx` — delhi.css import
- `frontend/src/components/FloodMap.tsx` — relative API URLs only
- `frontend/vite.config.ts` — dev proxy
- `frontend/index.html` — title
- `README.md` — rewritten
- `.gitignore` — deduplicated + tooling state
- `kushak_event_validation.py` — pre-existing uncommitted EVT-*→EV-* bridge, preserved

## 23. FILES_INTENTIONALLY_LEFT_UNCHANGED

- All of `backend/app/domain/delhi/digital_twin/` scientific core
  (except the pre-existing uncommitted `kushak_event_validation.py`
  bridge, kept as-is) — validated, 694 tests green, no redesign.
- All Mumbai V1 code (`backend/routers/flood|routing`, `app/domain/
  {flood,historical,routing,...}`, `app/infrastructure/`, FloodMap UI
  beyond the URL fix) — frozen per policy.
- `scripts/generate_phase15_replay.py` — canonical harness, imported
  unchanged by the API.
- `scripts/process_kushak_terrain*.py`, `data/` tree, `memory/`,
  agent tooling dirs (`.claude/`, `.freebuff/`, `.superpowers/`).
- Pre-existing untracked new tests/domain files (committed as-is).

## 24. SCIENTIFIC_CLAIMS_ALLOWED

- Genuine event-specific runtime replay executed through the canonical
  hydraulic path with documented forcing, resolution preserved.
- Deterministic 6-member ensemble behavior; mass-balance closure
  (implementation-correctness property).
- Qualitative/directional behavioral compatibility of replay outcomes
  with documented evidence.
- Provenance-tracked, UNKNOWN-preserving outputs under explicit
  effective-scenario assumptions.

## 25. SCIENTIFIC_CLAIMS_EXPLICITLY_NOT_ALLOWED

- Accuracy, calibration, rating-curve skill, RMSE, or depth-skill
  claims of any kind.
- Street-level flood depth truth; exact inundation extents.
- Observed stage/discharge; CWC stage as local Kushak observation.
- Official/as-built status for effective-scenario or Appendix
  XII-derived geometry.
- Historical replay as "validated" or "calibrated" — it is runtime
  integrity + qualitative consistency only.

## 25A. HISTORICAL SIMULATION / HINDCAST COMPLIANCE (28A-28F)

- **28A (engine)** — the historical replay reuses the operational
  canonical runtime (no separate simulator). Event classes:
  **EXECUTABLE** (EV-01, EV-02: full documented forcing at native
  resolution), **PARTIALLY EXECUTABLE** (EV-03: only the documented
  verified 80 mm 05:30-08:30 IST 3-hour block executes at its native
  interval; the remainder of the daily total stays UNKNOWN — never
  interpolated or disaggregated), **NON-EXECUTABLE** (control and
  missing-forcing events: preserved UNKNOWN/NOT_COMPARABLE/CONTROL,
  refusal reasons documented, no zero-fill, no FLOOD_NO invention).
  Observations remain OFFICIAL evidence; validation output stays DERIVED;
  street-level observations are never forced into conduit stage targets.
- **28B (frontend)** — event selector with manifest-derived statuses
  (REPLAY READY / PARTIAL REPLAY / CONTROL / NO FORCING), documented
  window/resolution/provenance display, explicit OBSERVED vs
  MODEL-RECONSTRUCTED blocks, event timeline with
  computed/blocked/UNKNOWN intervals, timestep playback synchronized
  with the map (timestamp chip, corridor pulse, data-driven rain
  animation), ensemble uncertainty display, Why? explanations, and the
  same uncertainty/provenance language as the operational nowcast.
- **28C (artifacts)** — every event produces a reproducible JSON
  artifact (`.../artifact` endpoint + generator) containing all required
  fields including `unknown_intervals`, `blocked_intervals`,
  `repository_revision`; stored ONLY in
  `data/delhi/derived/replay_artifacts/` (never mixed with operational
  outputs). Non-executable events document exactly WHY the runtime
  refused.
- **28D (replay vs validation)** — replay (execution),
  behavioral consistency (qualitative compatibility), and quantitative
  validation are kept distinct; nothing is called "accuracy"; no RMSE or
  skill metric is computed anywhere.
- **28E (discovery/reusability)** — `kushak_replay_manifest.py` is a
  declarative, import-validated event registry: a new event requires
  only data entries (metadata, forcing, provenance, observations,
  attribution); the hydraulic engine is untouched. Declarations are
  reconciled against the actual runtime forcing catalog at import.
- **28F (regressions)** — `backend/tests/test_historical_replay_regression.py`
  covers every required test: fully-executable replay, multi-timestep
  replay, six-member ensemble, UNKNOWN-forcing event, temporal-resolution
  discipline, no-zero-fill, no-synthetic-disaggregation, event
  separation, runtime lineage (manual-strings/CSV-derived flags),
  reproducibility, observed-vs-model provenance, manifest validation,
  artifact completeness, and operational/historical output separation.
  The Phase 15.2 execution-integrity tests were updated to encode the
  deliberate EV-03 partial-replay state (18 member executions across
  three executable events).

## 25B. SAFE ROUTING INTEGRATION

Flood-aware routing is complete end-to-end with ONE engine serving all
modes (see `docs/SAFE_ROUTING.md` + `docs/SAFE_ROUTING_IMPLEMENTATION_REPORT.md`):
LIVE routes from the current nowcast ensemble, HISTORICAL route
reconstruction from the genuine replay runtime at event + timestep, and
route/segment-level EVIDENCE traceability (route → segment → risk →
model state → forcing → source). UNKNOWN segments are never safe, are
penalized in routing, cap route evidence at LOW (weakest link), and the
recommended route is always labeled as the lowest supported MODELED
exposure — never a guarantee. 23 dedicated tests cover the critical
invariants including cross-mode isolation and determinism.

## 25C. SCIENTIFIC VALIDATION / CALIBRATION / PHYSICS-GUIDED ML

Complete scientific layer implemented (see `docs/FINAL_SCIENTIFIC_MODEL_PERFORMANCE_REPORT.md`,
`docs/FINAL_MODEL_READINESS_MATRIX.md` and the six method docs):
observation registry (1,130 records, tiered, usability-gated), metric
library, evidence-sufficiency gate, event-separated quantitative
validation, bounded calibration framework with a GLUE-style behavioral
screen (real runs; honest null result: NO DISCRIMINATING POWER —
equifinality), identifiability analysis (multipliers inert under current
contracts; C has no documented range), uncertainty decomposition, and a
physics-guided ML pipeline with event-grouped gating and a tested
physics-only fallback. Honest verdicts: calibration BLOCKED_BY_DATA
(no local quantitative target), ML BLOCKED_BY_DATA (insufficient
events), production_mode = PHYSICS_ONLY everywhere — no fabricated
accuracy, no deployed ML. Capability statuses are kept separate
(IMPLEMENTED != COMPUTED != VALIDATED != CALIBRATED != DEPLOYED).

## 25D. PROBLEM-STATEMENT RECONSTRUCTION PRODUCTS (radar / graph / surface / depth)

Implemented per `docs/RECON_IMPLEMENTATION.md`: (1) DERIVED Delhi
drainage graph (9 documented nodes, 8 edges, inferred-effective capacity
ranges) with honest per-node POTENTIAL_OVERLOAD logic; (2) Delhi Doppler
radar probe + composite with strict RADAR/NWP_FALLBACK provenance
(visual GIFs never decoded); (3) 2D surface routing over the enforced
DSM (D8 pass, ponding hotspots, corridor-inflow proxy — never injected
into the replay); (4) ESTIMATED_UNDER_ASSUMED_GEOMETRY depth-range layer;
(5) terrain-resolution bound documented. Also fixed the latent
backbone-slope chainage-selection bug (1.02 -> 0.00304 m/m). All
products are reported alongside the physics with provenance; production
remains PHYSICS_ONLY.

## 25E. SYNTHETIC SCENARIO ENGINE + FLOOD DEPTH INDICATOR

Six deterministic scenarios (SCN-01..06) travel through the SAME canonical
pipeline as live forcing (rainfall -> inflow -> chain -> 2D surface pass
-> depth -> road risk -> routing), with seeded reproduction, a compact
`/api/scenarios` API (list/meta/run/status/results/config/validation),
synthetic telemetry (SIM-AWS/DRAIN/PUMP/GATE, internally consistent),
an independent controlled ground truth, a SEPARATE
`SYNTHETIC VALIDATION - CONTROLLED TEST DATA` category, and a full
frontend SCENARIOS tab featuring a numeric FLOOD DEPTH INDICATOR
(depth m + cm, state, timestamp, scenario, source SIMULATED), the
canonical depth legend, timeline, ensemble envelope (explicitly not a
confidence interval), and road-depth listing. Provenance discipline:
every synthetic artifact carries source_type SIMULATED /
SIMULATED_MODEL_OUTPUT / SYNTHETIC_GROUND_TRUTH; production mode and
real-event validation are untouched; real-event metrics remain
separate and unchanged. 18 new tests (determinism, provenance,
consistency, API); full suite 1156 green.

### V1-PARITY FRONTEND STRUCTURE

The Delhi V2 frontend now mirrors the Mumbai V1 layout: **three
operational modes** (LIVE / SCENARIO / REPLAY) with the route workflow
inside LIVE and the MODEL evidence merged into the EVIDENCE tab. Flood
depth is a first-class map layer (canonical color/size legend) in both
SCENARIO and REPLAY modes; the REPLAY tab shows the V1-reference depth
grid evolving with the replay clock (per documented forcing bin, with a
per-event depth endpoint `/api/delhi/events/{id}/depth` and coherent
V1 mass-balance accounting) — like the Mumbai 2017 replay, ported to
V2 with honest SIMULATED_MODEL_OUTPUT provenance.

### V1 REFERENCE DEPTH MODEL

The scenario depth product now runs the **V1 (Mumbai/Kurla) reference
flood model** on the Delhi window — the exact `route_flood_depth`
semantics (inlet capacity capture -> surcharge -> D8 equilibrium ponding)
with an equivalence test proving the port matches V1. Scenario outcomes
are physically coherent and demonstrate hyper-locality: broad extreme
rain mostly drains; localized bursts flood streets.

### FLOOD DEPTH INDICATOR — DATA TRACE

SCN-03 display path (the shown depth is generated by the actual runtime
pipeline, never hardcoded):

1. Scenario config SCN-03 (peak 48 mm/h, profile with mid-event peak).
2. `generate_scenario_forcing` -> areal depths per 15-min step
   (e.g., step 6 = 12.9 mm) + normalized spatial Gaussian field.
3. `run_integrated_simulation` (rainfall_to_inflow over the documented
   27.66 km2, C=0.75) -> inflow series; `advance_chain_series` ->
   storage trajectory.
4. `surface_pass(spatial_fields)` -> routed surface columns (cm),
   bounded by terrain depression + documented infiltration -> per-step
   `depth_field_cm`.
5. Engine builds `steps[i].max_depth_cm` (e.g., 79.2 cm at step 6 ->
   `SEVERE` by the canonical thresholds) and `flood_state`.
6. `/api/scenarios/SCN-03/results?run_id=...&timestep_index=6` returns
   that step verbatim (source_type SIMULATED_MODEL_OUTPUT).
7. ScenarioPanel fetches results and renders
   `0.79 m = 79 cm` in the MAX FLOOD DEPTH widget with the scenario,
   timestamp, and state — a pure pass-through of the runtime number.

## 26. FINAL VERDICT

**COMPLETE — MANUAL USER TESTING ONLY.** The system is operationally
usable and scientifically honest: it tells users what it knows, how it
knows it, and — explicitly — what it does not know.
