# Delhi V2 API Reference

Base URL: `http://localhost:8000`. Interactive docs: `/docs`.
All Delhi V2 routes are under the `/api/delhi` prefix
(`backend/routers/delhi.py`). Every response carries provenance labels
and explicit operational states; no endpoint fabricates data.

System-wide endpoints (outside the prefix):

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/health` | Liveness |
| GET | `/ready` | Readiness with **named** component checks (delhi router, event catalogue, geo layers, Mumbai DEM, database) |

## Delhi V2 endpoints

### `GET /api/delhi/status`

System status: components (reach chain, ensemble, events, nowcast
reference point), capabilities, and `explicit_non_claims` — the list of
things this system deliberately does not claim.

### `GET /api/delhi/ensemble`

The deterministic 6-member ensemble: 3 hydraulic scenarios
(CONSERVATIVE / CENTRAL / DEGRADED_CAPACITY, each with its Phase 7D16
parameter ranges) × 2 catchment scenarios (WORKING_27_66 /
SENSITIVITY_28_40, PROVISIONAL). Runoff coefficient C = 0.75 (ASSUMED).

### `GET /api/delhi/network`

The locked reach chain UG-01 → OC-01 → CD-01 → OC-02 with chainage,
tier, provenance, and `hydraulic_status` (UG-01 is
`HYDRAULICALLY_BLOCKED_PHYSICAL_GEOMETRY_UNKNOWN`). Includes the
Qudesia-separation and Barapullah-downstream continuity note.

### `GET /api/delhi/events`

The Phase 14A event catalogue with forcing availability, preserved
classifications, and the **28B replay status** derived from the
validated declarative event manifest
(`backend/app/domain/delhi/digital_twin/kushak_replay_manifest.py`):

| replay_status | Meaning | Events |
| --- | --- | --- |
| `EXECUTABLE` | Full documented forcing runs at native resolution | `EVT-2024-06-27` (EV-01), `EVT-2023-07-08` (EV-02) |
| `PARTIAL` | Only the documented defensible portion runs; remainder stays UNKNOWN | `EVT-2021-09-11` (EV-03: verified 80 mm 05:30-08:30 IST 3-hour block; the rest of the daily total has no documented timing) |
| `CONTROL` | Documented non-flood control; absent forcing never simulated | `EVT-2026-01-23` |
| `UNKNOWN` | No documented executable forcing | `EVT-2021-07-19`, `EVT-2023-05-27` |

Each event also declares `observation_status`,
`spatial_attribution_status`, `replay_claim`, and `executable_status`.
The manifest is machine-validated at import time (28E): a declaration
that contradicts the actual runtime forcing catalog fails loudly, and
registering a NEW event requires only data entries — never hydraulic
code changes.

### `GET /api/delhi/events/{event_id}/replay?refresh=false`

Genuine event-specific runtime replay.

- **Executable events** — run all 6 members through the canonical
  runtime (`run_integrated_simulation` → `advance_chain_series` →
  `classify_chain_timestep` → `validate_observation`). Response:
  forcing bins with provenance (resolution preserved, no
  disaggregation), per-member inflow steps (`null` = UNKNOWN preserved),
  per-reach per-step chain states with mass-balance residuals,
  validation records (`result_provenance` always `DERIVED`), runtime
  counters, and derived integrity checks (mass balance, terminal
  outfall, unknown propagation, runtime consistency).
- **Non-executable events** — `runtime_status: "NOT_EXECUTED"` with the
  preserved classification (`NOT_COMPARABLE`, control, or
  `BLOCKED_MISSING_FORCING`). Absent forcing is never converted into a
  simulation.
- Results are deterministic; cached in-process. `refresh=true` forces
  re-execution. Unknown event ids → 404.

### `GET /api/delhi/events/{event_id}/artifact`

The reproducible **28C replay artifact**: `event_id`,
`resolved_event_id`, `event_window`, `forcing_source`,
`forcing_resolution`, `forcing_provenance`, `forcing_timesteps`,
`ensemble_members`, `runtime_status` (`EXECUTED` / `PARTIAL_EXECUTED` /
`NOT_EXECUTED`), `hydraulic_states`, `routing_states`,
`uncertainty_states`, `validation_status`, `observation_matches`,
`unknown_intervals`, `blocked_intervals`, `generation_timestamp`, and
`repository_revision`. Deterministic; generated on demand and cached.
Non-executable events produce an artifact that documents exactly WHY the
runtime refused. Artifacts live ONLY under
`data/delhi/derived/replay_artifacts/` — never mixed with operational
forecast outputs. Generate the full set with:

```bash
python backend/app/domain/delhi/replay_artifacts.py
```

### `GET /api/delhi/replay/summary?refresh=false`

The full Phase 15.5 replay: per-event records, all 9 system flags, and
the overall verdict (`PASS` expected). This is the scientific release
gate.

### `GET /api/delhi/nowcast?refresh=false`

Live 0–3h ensemble nowcast:

1. `forecast` — Open-Meteo NWP hourly precipitation for the documented
   Safdarjung reference point. Status `COMPUTED` (fresh) / `STALE`
   (cached fallback after a failed refresh) / `UNAVAILABLE`. Bins carry
   `DERIVED` (model value) or `UNKNOWN` provenance. The backend caches
   the last successful fetch for 15 minutes.
2. `envelope_inflow` — per timestep: forecast depth plus the min/median/
   max modeled inflow across members (`null`s preserved with
   `computed_members` / `unknown_members` counts).
3. `members` — per-member inflow hydrograph, per-reach chain states,
   classifications (UNKNOWN — no stage may be invented), volumes,
   diagnostics.
4. `status` — `COMPUTED` or `BLOCKED_MISSING_FORCING` (no fabricated
   nowcasts, ever).
5. `claim_policy` / `horizon_note` — verbatim honesty statements the UI
   displays.

### `GET /api/delhi/layers` · `GET /api/delhi/geo/{layer_id}`

Derived GeoJSON evidence layers served from an **allowlist** with
provenance labels: `corridor_centerline`, `watershed` (PROVISIONAL
27.66 km²), `cross_sections`, `gsdl_occurrences` (OFFICIAL),
`historical_landmarks`. Unknown layer ids → 404.

## Example

```bash
curl -s http://localhost:8000/api/delhi/nowcast | jq '.status, .envelope_inflow'
curl -s "http://localhost:8000/api/delhi/events/EVT-2024-06-27/replay" | jq '.counters, .integrity_checks'
curl -s http://localhost:8000/ready | jq '.status, .checks'
```

## Legacy (Mumbai V1, frozen)

`/flood/*` (model, forecast, streets, historical/2017), `/routing/safe-route`,
`/rainfall/*` (Mumbai NWP/radar composite), `/api/readings|alerts|devices|
dashboard` (water-quality monitoring shell). Documented here for
completeness; not under active development.
