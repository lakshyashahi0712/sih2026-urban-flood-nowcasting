# User Guide

This guide is for operators, researchers, and reviewers using the app at
<http://localhost:5173> (dev) or <http://localhost:8080> (Docker).

## Choosing a system

The switcher at the top-right selects the system:

- **DELHI V2 (CURRENT)** — the evidence-constrained Kushak nowcasting
  system. Default on launch.
- **MUMBAI V1 (LEGACY)** — the frozen Kurla pilot, preserved for
  reference.

## Delhi V2

The left panel has three tabs; the map shows the Kushak corridor in
South Delhi with toggleable layers (catchment, modeled corridor,
cross-sections, GSDL waterlogging occurrences, historical landmarks).

### NOWCAST — the live 0–3h outlook

1. **Status banner** — `NOWCAST COMPUTED` (green) or the explicit
   blocking state (amber, e.g. `NOWCAST BLOCKED_MISSING_FORCING` when
   the forecast provider is unreachable). The system never shows a
   fabricated outlook.
2. **Rainfall forecast input** — four hourly bins (t+0…t+3) from the
   Open-Meteo NWP forecast at the documented Safdarjung reference point.
   Each bin carries its provenance (`DERIVED` = model value; `UNKNOWN`
   = missing hour, never zero-filled).
3. **Ensemble inflow envelope** — the min–max band and median line
   across the 6 deterministic members. This is the model's defensible
   core signal: how much runoff the catchment scenario range produces
   under the forecast rainfall.
4. **Reach states** — per-reach storage (model-derived) and state. Stage
   is UNKNOWN *by design*: no storage–stage relation exists for Kushak,
   and the model contract refuses to invent one.
5. **Claim policy footer** — verbatim: behavioral envelopes under
   documented scenario assumptions; not a validated depth prediction.

Use **Refresh** to force a new forecast acquisition and re-run.

How to read it operationally: larger ensemble spread + rising median
inflow means the forecast rainfall drives the corridor toward its
effective conveyance limits under at least some scenario assumptions.
Because stage and depth are UNKNOWN, treat the envelope as a *stress
indicator*, not a water-level prediction.

### REPLAY — historical events

1. Pick an event card. Each card shows its replay status:
   - **REPLAY READY** (EVT-2024-06-27 / EV-01 with the observed 91 mm/h
     Safdarjung hour; EVT-2023-07-08 / EV-02 with 3-hour increments) —
     full documented forcing runs at native resolution.
   - **PARTIAL REPLAY** (EVT-2021-09-11 / EV-03) — only the documented
     verified 3-hour block (80 mm, 05:30–08:30 IST) is executed; the
     remainder of the daily total has no documented timing and stays
     UNKNOWN.
   - **CONTROL (NO FORCING)** / **NO FORCING** — not simulated, by
     design; the preserved evidence classification is shown instead.
2. For executable events you get:
   - the forcing bins exactly as documented (provenance per bin —
     `VERIFIED_ZERO`, `OBSERVED_DIRECT`, `UNKNOWN`),
   - the 6 member inflow hydrographs (gaps = UNKNOWN hours, preserved),
   - a timestep playback (Play/Prev/Next) with per-reach inflow,
     storage, transferred flow, model state, and the mass-balance
     residual (0 = closed) at each step,
   - the runtime integrity checks derived from the actual execution.
3. Events marked `NO FORCING` are not simulated — by design. Their
   preserved classifications (`NOT_COMPARABLE`, control, or UNKNOWN)
   are shown instead. The system never invents rainfall to make an
   event runnable.

The event panel separates **OBSERVED · DOCUMENTED EVIDENCE** (what
actually happened, per the official record) from **MODEL-RECONSTRUCTED
STATE** (what the runtime produced). These categories are never merged —
the same distinction is drawn on the map, where model states are
labeled MODEL FLOW and observations stay in their own layer.

The **Event timeline** bar shows each forcing interval: documented
forcing (blue), steps blocked downstream (amber border), and UNKNOWN
intervals (hatched). The **Why?** button on any reach row opens an
automated, rule-based explanation assembled from the actual model
outputs and evidence labels (it is explicitly labeled as not
AI-generated).

During playback the map follows the replay clock: the timestamp chip at
the top shows the current step, the corridor pulses while model flow is
computed, and a subtle rain animation appears ONLY when the current
step's documented rainfall is known — at UNKNOWN steps the animation
stops and an explicit "RAIN: UNKNOWN" chip explains why. All motion is
disabled under your system's reduced-motion preference.

The verdict banner (`HISTORICAL REPLAY VERDICT: PASS`) refers to runtime
execution integrity and qualitative consistency — **not** to accuracy.

### EVIDENCE — what the model is made of

- The reach chain with per-reach evidence status (UG-01's physical
  geometry is UNKNOWN and hydraulically blocked without a Tier-B
  effective-scenario declaration).
- The ensemble definition: hydraulic scenario multipliers with their
  documented ranges (INFERRED_EFFECTIVE, not surveyed/calibrated),
  catchment scenarios (PROVISIONAL), runoff C (ASSUMED).
- **What this system does not claim** — the explicit non-claims list.
  Read this before citing any number from the app.

## Mumbai V1 (legacy)

LIVE FORECAST (Open-Meteo NWP horizons), MODEL SCENARIO (20/40/50/70 mm
what-ifs), HISTORICAL REPLAY (29 Aug 2017), street intelligence, and
flood-safe routing. When the rainfall source is unreachable the header
shows `Open-Meteo NWP (UNAVAILABLE)` and the panels degrade honestly.

## Interpreting UNKNOWN / blocked states

| Display | Meaning |
| --- | --- |
| `UNKNOWN` (amber) | Evidence does not exist; the system will not guess. |
| `BLOCKED_*` | A required input is missing; execution stopped at that step and downstream propagation is blocked. |
| `NOT_EXECUTED` | The event has no documented executable forcing; simulation refused. |
| `NOT_COMPARABLE` | Evidence exists but cannot be defensibly compared (e.g. 3-hourly rainfall vs hourly model steps). |
| `UNAVAILABLE` | An external data source could not be reached; a cached value may be shown as `STALE`. |

These states are the product working correctly, not errors: a flood
system that silently guesses is more dangerous than one that says
UNKNOWN.
