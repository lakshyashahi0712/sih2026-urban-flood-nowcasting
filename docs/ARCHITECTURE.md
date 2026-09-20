# Architecture

## Overview

```
┌────────────────────────────  frontend (React + Vite + MapLibre)  ───────────────────────────┐
│  DELHI V2 (primary)                              MUMBAI V1 (legacy, frozen)                 │
│  DelhiApp: NOWCAST | REPLAY | EVIDENCE           FloodMap: LIVE | SCENARIO | HISTORICAL     │
│  DelhiMap: corridor/watershed/GSDL layers        street intelligence, safe routing          │
└──────────────┬──────────────────────────────────────────────────────┬──────────────────────┘
               │  /api/delhi/*                                        │  /flood /rainfall /routing
┌──────────────▼───────────────────────────────┐   ┌──────────────────▼───────────────────┐
│ backend/routers/delhi.py (V2 API surface)    │   │ backend/routers/{flood,routing,...}  │
│  reuses scripts/generate_phase15_replay.py   │   │ + app/api/rainfall.py                │
│  as the single replay implementation         │   │ (Mumbai pipeline, frozen)            │
└──────────────┬───────────────────────────────┘   └──────────────────────────────────────┘
               │
┌──────────────▼─────────────────────────────────────────────────────────────────────────────┐
│ backend/app/domain/delhi — the scientific core                                             │
│                                                                                            │
│  nowcast.py                NWP forecast fetch → ensemble → canonical runtime               │
│  digital_twin/                                                                             │
│    kushak_reaches_tiered       locked reach chain UG-01→OC-01→CD-01→OC-02 (Tier-B)         │
│    kushak_scenario_ensemble    deterministic 6-member ensemble (3 hydraulic × 2 catchment) │
│    hydraulic_integrated_orchestrator   rainfall_to_inflow → run_hydrograph_simulation      │
│    kushak_continuity_routing   multi-timestep chain (V_next = V + dt·(Qin+Qlat−Qout))      │
│    kushak_flow_accounting      independent mass-balance audit (residual per reach-step)    │
│    kushak_hydraulic_state_classification  MODEL-STATE only (never "observed flood")        │
│    kushak_event_validation     event-separated validation (EVT-* → EV-01/EV-02 bridge)     │
│    kushak_evidence_model       scenario ranges, provenance, backbone slope                 │
│    kushak_historical_rainfall_catalog  EV-01 / EV-02 forcing profiles (bins+provenance)    │
│  hydrology/                 SCS-CN & Green-Ampt losses, runoff transformation              │
└────────────────────────────────────────────────────────────────────────────────────────────┘
               │
┌──────────────▼─────────────────────────────────────────────────────────────────────────────┐
│ data/delhi/{raw,derived} — locally-acquired evidence (not committed; see .gitignore)       │
│  catalogues, forcing hyetographs, DEM derivatives, corridor/catchment GeoJSON, GSDL/DTP    │
│  observations, Phase 14A event catalogue, Phase 15.5 replay CSVs                           │
└────────────────────────────────────────────────────────────────────────────────────────────┘
```

## Execution paths

### Live 0–3h nowcast (`GET /api/delhi/nowcast`)

1. `nowcast.fetch_delhi_rainfall_forecast()` acquires the Open-Meteo
   hourly precipitation forecast for the documented Safdarjung reference
   point (2-day window, current IST hour located by timestamp). States:
   `COMPUTED` / `STALE` (cached fallback) / `UNAVAILABLE` (explicit
   diagnostics; no synthetic weather).
2. Each forecast hour becomes exactly one runtime timestep (resolution
   preserved). A missing hour stays `UNKNOWN` (`None` depth) and
   propagates as a blocked timestep — never zero-filled.
3. All 6 ensemble members (`build_kushak_ensemble()`) execute through the
   canonical path — `run_integrated_simulation` (rainfall → runoff →
   hydrograph-driven hydraulic run) then `advance_chain_series` over the
   locked reach chain with the Phase 8A/15.5 boundary conventions
   (explicit zero outflow ASSUMED on UG-01/OC-01/CD-01, Tier-B declaration
   on UG-01; OC-02 terminal, no outflow decision).
4. The API returns per-member hydrographs/states plus the min/median/max
   envelope. Reach stage is UNKNOWN by contract (no storage–stage
   relation exists); capacity comparisons without stage are blocked, not
   invented.

### Historical replay (`GET /api/delhi/events/{event_id}/replay`, `.../artifact`, `/api/delhi/replay/summary`)

The router imports the Phase 15.5 harness (`scripts/generate_phase15_replay.py`)
as a module and reuses `build_event_forcing_series`,
`execute_member_for_event`, and `run_historical_replay` directly — the
script is the single source of truth, so the API can never drift from the
audited replay, and the replay shares the operational runtime exactly
(no separate "historical simulator" exists).

Event classes (28A):

- **EXECUTABLE** — EVT-2024-06-27 (EV-01) and EVT-2023-07-08 (EV-02) run
  all 6 members with event-specific forcing; unknown bins propagate as
  blocked steps.
- **PARTIALLY EXECUTABLE** — EVT-2021-09-11 (EV-03) executes ONLY the
  documented verified 3-hour block (80 mm, 05:30-08:30 IST) at its
  native interval; the remainder of the daily total has no documented
  timing and stays UNKNOWN (no interpolation, no disaggregation).
- **NON-EXECUTABLE** — control and missing-forcing events return their
  preserved evidence classifications without runtime execution.

Results are deterministic; responses are cached in-process and can be
forced to recompute with `?refresh=true`. Per-event 28C artifacts are
built by `backend/app/domain/delhi/replay_artifacts.py` into
`data/delhi/derived/replay_artifacts/` (separated from operational
outputs) and served at `/api/delhi/events/{id}/artifact`. The 28F
regression suite (`backend/tests/test_historical_replay_regression.py`)
guards runtime lineage, event separation, no-zero-fill,
no-disaggregation, reproducibility, and provenance separation.

## Honest-state model

- Provenance enum: `OBSERVED, OFFICIAL, OFFICIAL_MODEL_VALUE, DERIVED,
  ASSUMED, PROVISIONAL, UNKNOWN` (`digital_twin/models.py`).
- Forcing provenance: `OBSERVED_DIRECT, VERIFIED_ZERO, DERIVED, UNKNOWN`
  (`kushak_rainfall_forcing.py`). NWP forecast values are `DERIVED`
  model values, explicitly not observations.
- Operational statuses surfaced by the API: `COMPUTED / EXECUTED /
  NOT_EXECUTED / BLOCKED_* / NOT_COMPARABLE / UNAVAILABLE / STALE /
  UNKNOWN`. Meaningful states are never collapsed into booleans.

## Known deliberate limitations

See [LIMITATIONS.md](LIMITATIONS.md). The headline items: UG-01 conduit
geometry is UNKNOWN (Tier-B effective-scenario abstraction), there is no
storage–stage relation (stage/depth outputs are UNKNOWN by construction),
and historical replay establishes runtime integrity and qualitative
consistency only — no accuracy, calibration, or depth-skill claims.
