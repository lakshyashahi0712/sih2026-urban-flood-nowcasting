# Known Limitations & Explicit Non-Claims

This document is part of the product. The system's defining behavior is
that it **represents missing evidence as UNKNOWN instead of guessing**.
The limitations below are structural and honest, not temporary gaps to
be silently closed.

## Scientific non-claims

The system does **NOT** claim:

1. **No calibrated or validated flood-depth accuracy.** There are no
   defensible depth observations paired with a valid comparison
   workflow. Historical replay establishes runtime execution integrity
   and qualitative/directional consistency only.
2. **No street-level flood truth from coarse terrain.** The DEM is
   Copernicus GLO-30 **DSM** (not a DTM); blanket vertical accuracy
   better than ~2 m is not claimed.
3. **No observed stage or discharge.** No storage–stage relation exists
   for Kushak; stage is UNKNOWN everywhere. CWC stage is downstream
   boundary *context*, never a local Kushak observation.
4. **No invented rainfall.** Missing forcing bins stay UNKNOWN and
   propagate as blocked timesteps. Coarse records (3-hourly blocks +
   daily totals) are never disaggregated into hourly values. Absent
   forcing is never converted into a simulation.
5. **No official/as-built drainage geometry.** UG-01's internal barrel
   geometry is UNKNOWN (tender drawings bidder-restricted). Tier-B
   reach profiles are *effective-scenario* abstractions, not surveyed
   sections. The Appendix XII-derived backbone is a monotonic
   model-input backbone with documented caveats.
6. **No synthetic drainage network labeled official.** No arbitrary
   Manning values presented as surveyed; scenario multipliers are
   INFERRED_EFFECTIVE within documented ranges (Phase 7D16).
7. **No accuracy from internal checks.** Mass-balance closure and
   conservation are correctness properties of the implementation, not
   validation against reality.
8. **No equifinality violation.** Historical events constrain effective
   hydraulic behavior/conveyance only; parameters are never uniquely
   inferred from flood outcomes, and events are never pooled or
   leaked between calibration and validation.

## Structural limitations

| Area | Limitation |
| --- | --- |
| Catchment | Working model 27.66 km² (PROVISIONAL, D8-derived); 28.40 km² is sensitivity only; historical ≈35.4 km² unresolved — never silently expanded. Disconnected headwaters are not reconnected. |
| Network | Kushak is modeled as a 4-reach serial corridor; lateral inflows, Qudesia Nallah (hydraulically separate), and the underground box structure inventory are out of scope for the runtime. |
| Nowcast forcing | Open-Meteo NWP hourly precipitation is a model forecast at a reference point, not a gauge observation of the catchment; no radar ingestion (Open-Meteo is never called radar; IMD GIF colors are never quantitatively decoded). |
| Nowcast outputs | Inflow/storage envelopes only; stage, capacity exceedance, and street-level depth are UNKNOWN by construction. |
| Replay | Full replay for EV-01/EV-02; PARTIAL replay for EV-03 (only the documented 80 mm 05:30-08:30 IST 3-hour block executes at native resolution — the remainder of the daily total is UNKNOWN). Control and missing-forcing events are never simulated. Validation for date-only observations stays temporally incomparable. |
| Data | The `data/` evidence tree is locally acquired and not committed; without it the Delhi features report NOT_READY components instead of fake data. |
| Validation | GSDL/DTP occurrence evidence is date/time-anchored occurrence data; without coordinates the spatial match stays UNKNOWN and no occurrence/state comparison is attempted. No RMSE or skill scores exist or are invented. |
| Deployment | External dependencies: Open-Meteo API, OpenFreeMap/OSM tiles. Behind firewalls blocking these, the app degrades to explicit UNAVAILABLE/STALE states. |

## Visual motion policy

Map animations (rain streaks, corridor pulse) are strictly data-driven:
rain animation runs only when the active step's rainfall is a known
model/forcing value, stops at UNKNOWN steps (with an explicit chip), and
never implies intensity beyond the data. Everything is disabled under
`prefers-reduced-motion: reduce`. No animation implies flood depth —
depth remains UNKNOWN everywhere.

## AI feature status

Intentionally omitted. The system's core value is a defensible,
provenance-tracked physics pipeline; a language-model layer would add
narrative risk (fabricated confidence, unfaithful summaries of evidence)
without adding hydrological skill. The API already explains every output
through structured provenance, integrity checks, and claim policies, and
the UI surfaces them directly. If an explanation layer is added later it
must consume only these structured outputs, cite them, expose
uncertainty, and degrade gracefully — per the repository's scientific
non-negotiables.
