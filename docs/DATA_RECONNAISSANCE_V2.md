# DATA RECONNAISSANCE — SIH 2026 Urban Flood Nowcasting V2 (Delhi)

**Role:** data reconnaissance lead. **Scope:** full-repository audit mapped
against the SIH problem statement (0–3 h street-level nowcasting via
radar + DEM + drainage-graph coupling), with gaps and improvement paths.

---

## 1. Requirement → repository status map

| Problem statement requirement | In repo? | Where / status |
| --- | --- | --- |
| Real-time 0–3 h rainfall nowcasting | ✅ operational | Open-Meteo NWP forced live nowcast for Delhi (`nowcast.py`), 6-member ensemble, freshness/STALE semantics |
| **Doppler Weather Radar rainfall** | ⚠️ partial | IMD radar adapter + composite exists **for Mumbai only** (`infrastructure/rainfall/imd_radar.py`, `/rainfall/radar/diagnostics`, `/rainfall/composite`). **No radar input in the Delhi/Kushak live path.** |
| High-resolution DEM | ⚠️ limited | Copernicus GLO-30 **DSM 30 m** derivatives for Delhi (667×667, UTM 43N). Correctly never claims <2 m accuracy; 30 m DSM is coarse for street-level. |
| **Graph-based underground drainage network** | ⚠️ partial | Mumbai V1 has a real node/edge drainage graph (manholes, drains, capacities: `infrastructure/drainage/network_builder.py`). **Delhi has NO manhole/inlet/pipe graph** — only the evidence-constrained 4-reach serial corridor (UG-01 … OC-02) with underground geometry UNKNOWN. |
| Route rainfall volume across **2D surface terrain** | ⚠️ partial | Mumbai V1 has a 2D raster surface engine producing flood-depth rasters; **Delhi live path has no 2D routing** (runoff transform is a lag; corridor hydraulics are 1D). |
| Hydraulic capacity / overcapacity / backflow prediction | ⚠️ partial | Capacity machinery exists but is **blocked without stage** (stage UNKNOWN by contract) → no defensible overcapacity/backflow/surcharge output on the live path. |
| **Street-by-street water depth (cm)** | ❌ not supportable | The physics runtime explicitly has no storage–stage relation and never emits depth. Mumbai V1 produces depth rasters (legacy, frozen); Delhi does not. |
| Web GIS dashboard, real-time street projections | ✅ | Delhi V2 dashboard + map + replay + routing; honest UNKNOWN states. |
| Flood-safe routing API | ✅ | Delhi `safe-routing` (live + historical + evidence), OSM network, provenance-gated risk states. |

## 2. The critical gap (honest framing)

The problem statement's headline deliverable — **street-by-street depth
in centimetres** — is the one thing the current physics cannot
defensibly produce for Delhi: there is no storage–stage relation, no
surveyed cross-section evidence, and no depth observations to validate
against. The repo's choice to say UNKNOWN rather than invent a depth is
scientifically correct, but relative to the SIH deliverable it is the
single largest distance-to-goal. Everything else is either present or
recoverable with modest effort.

## 3. Ranked gaps

1. **Street-level depth pathway (Delhi).** No depth estimation of any
   kind; risk is binary-class/loading-based. *Unlocks with:* surveyed
   cross-sections/as-built geometry, depth observations, or an explicit
   "estimated depth under stated model assumptions" layer with
   strong uncertainty labeling.
2. **Delhi drainage graph.** No manhole/inlet/pipe topology, no node
   capacities, no inlet-to-corridor connectivity — so no per-node
   overcapacity/backflow prediction for Delhi. *Assets on disk:*
   Aab Prahari data, GSDL points, 1976 drain inventory, DMP Appendix XII,
   NIT52 procurement geometry — enough for a **documented DERIVED graph**
   (with provenance) that the engine could drive.
3. **Radar into the Delhi live path.** IMD Delhi Doppler (Aya Nagar) is
   not probed and the Delhi nowcast uses NWP only. The Mumbai adapter
   pattern (probe → composite → provenance `RADAR`/`NWP_FALLBACK`) is
   directly reusable; keep the "never call Open-Meteo radar" rule.
4. **2D surface routing for Delhi.** The terrain-conditioned rasters
   (enforced DEMs, flow accumulation for burn variants) exist and are
   unused by the live pipeline; the runoff transformer is a lag, not a
   2D model. A light 2D routing step (cell-to-cell volumetric pass over
   the DEM) would satisfy the "route volume across 2D surface" clause.
5. **High-resolution terrain.** 30 m DSM is the bound. Access-blocked
   items (RTI as-built survey, lidar) are documented; ALOS/COP-DEM or
   commissioned survey would raise ceiling; until then everything stays
   sub-street-scale honest.

## 4. Ranked improvements (cheap → costly)

1. **Delhi radar probe + composite** (reuse Mumbai machinery, add Delhi
   grids; provenance-separated) — highest demonstration value per effort.
2. **Derived Delhi drainage graph** from on-disk evidence with explicit
   DERIVED provenance and capacity metadata from the documented
   geometry classes — unlocks node-level surcharge/backflow logic
   (even as conservative scenario outputs).
3. **Honest depth-estimate layer**: stage from storage only where a
   documented storage–stage proxy exists (e.g., closed corridors with
   known box geometry classes), labeled "ESTIMATED UNDER ASSUMED
   GEOMETRY" — converts the cm-depth requirement into a defensible
   product rather than refusing.
4. **2D surface routing over the enforced DEMs** in the live path
   (volumetric split: infiltrate → overland → inlet), feeding the
   corridor and the routing graph.
5. **Dashboard "model mode" honesty** (already underway) + a
   "monitoring stations / validation" overlay for future sensor data —
   the ingestion interface exists conceptually in the registry.
6. **City-pair parity**: port the depth/raster path from Mumbai V1 only
   where it can be made defensible for Delhi; avoid copying frozen code
   that violates Delhi's evidence discipline.

## 5. Unavailable measurements (as of this date)

Local Kushak stage, discharge, depth, surveyed extent; sub-hour radar
grids for Delhi; surveyed as-built underground geometry; lidar/high-res
DTM. All are documented as UNKNOWN/BLOCKED in the framework rather than
invented.

## 6. Bottom line

Architecture and honesty: strong (coupled rainfall→runoff→hydraulic
chain, ensemble, provenance, routing, GIS). Deliverable gap: the
**street-depth centimetre prediction cannot be claimed honestly yet** —
the fastest defensible path is (a) Delhi radar, (b) a DERIVED drainage
graph, (c) a clearly-labeled estimated-depth layer, (d) 2D surface
routing — in that order. Radar and the surface pass are the two
"problem-statement-native" pieces most visibly absent from the
operational Delhi system.
