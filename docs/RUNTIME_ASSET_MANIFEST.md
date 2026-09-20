# RUNTIME ASSET MANIFEST

**Document ID:** `DOC-CHN-DEP-002`  
**Target Environment:** Vercel Hobby (Frontend) + Render Free 512 MB (Backend)  
**Date:** September 2026  
**Status:** ACTIVE RUNTIME INVENTORY  

---

## 1. Executive Summary

A full audit of the repository identified that out of **609.96 MB** residing in `data/`, only **15 files totaling 2.25 MB** are genuinely read during runtime across the entire Delhi V2 digital twin. Together with the Mumbai V1 assets under `backend/app/data/` (8 files totaling 7.43 MB), the complete runtime footprint required for full functionality of both cities is **9.68 MB**.

By committing only these verified runtime assets and keeping the remaining ~600 MB of raw research PDFs, satellite imagery, and intermediate analysis files safely ignored, the cloned repository remains lean and builds instantaneously within Render's free tier quotas.

---

## 2. Verified Runtime Assets

### 2.1 Delhi V2 Digital Twin Assets (`data/delhi/`)
| Path | File Size | Feature Requiring It | City / Catchment | Lifecycle | Provenance | Bundling Strategy |
|---|:---:|---|---|:---:|---|:---:|
| `data/delhi/derived/dem/kushak_enforced_dem_burn1m.tif` | 1,171.8 KB | 2D D8 surface routing, depression storage, elevation queries | Delhi / Kushak | On-demand | DERIVED (Copernicus 30m DSM + 1m stream burn) | Git Tracked |
| `data/delhi/derived/hydraulic/kushak_corridor_centerline.geojson` | 12.2 KB | Reach backbone display, `/ready` health probe, drainage graph | Delhi / Kushak | **Startup + On-demand** | DERIVED (Appendix XII longitudinal backbone) | Git Tracked |
| `data/delhi/derived/hydraulic/kushak_cross_sections.geojson` | 15.5 KB | Cross-section layer `/api/delhi/geo/cross_sections` | Delhi / Kushak | On-demand | DERIVED (Appendix XII geometry) | Git Tracked |
| `data/delhi/derived/hydraulic/historical_reconciliation/kushak_historical_landmarks.geojson` | 21.7 KB | Historical landmarks `/api/delhi/geo/historical_landmarks` | Delhi / Kushak | On-demand | OFFICIAL (Documented historical evidence) | Git Tracked |
| `data/delhi/derived/watershed/kushak_watershed.geojson` | 78.8 KB | Catchment boundary layer `/api/delhi/geo/watershed` | Delhi / Kushak (~27.66 km²) | On-demand | DERIVED / PROVISIONAL (D8 project watershed) | Git Tracked |
| `data/delhi/derived/validation/kushak_historical_events.csv` | 10.7 KB | Historical event catalogue `/api/delhi/events`, `/ready` probe | Delhi / Safdarjung | **Startup + On-demand** | OFFICIAL (Curated historical event catalogue) | Git Tracked |
| `data/delhi/derived/validation/gsdl_waterlogging/gsdl_waterlogging_normalized_occurrences.geojson` | 698.3 KB | GSDL waterlogging map layer `/api/delhi/geo/gsdl_occurrences` | Delhi / NCT Delhi | On-demand | OBSERVED / OFFICIAL (GSDL records) | Git Tracked |
| `data/delhi/derived/validation/gsdl_waterlogging/gsdl_waterlogging_normalized_occurrences.csv` | 212.9 KB | Hotspot validation & reach spatial attribution | Delhi / Kushak | On-demand | OBSERVED / OFFICIAL (GSDL records) | Git Tracked |
| `data/delhi/derived/rainfall/kushak_event_inventory.csv` | 4.5 KB | Event forcing catalogue used by replay harness | Delhi / Safdarjung | On-demand | OFFICIAL (IMD station event inventory) | Git Tracked |
| `data/delhi/derived/rainfall/kushak_forcing_hyetograph_20230708_10_safdarjung.csv` | 20.1 KB | Replay execution for July 2023 deluge (`EVT-2023-07-08`) | Delhi / Safdarjung | On-demand | OBSERVED / OFFICIAL (IMD Safdarjung hyetograph) | Git Tracked |
| `data/delhi/derived/rainfall/kushak_forcing_hyetograph_20240628_safdarjung.csv` | 5.9 KB | Replay execution for June 2024 deluge (`EVT-2024-06-28`) | Delhi / Safdarjung | On-demand | OBSERVED / OFFICIAL (IMD Safdarjung hyetograph) | Git Tracked |
| `data/delhi/derived/research/kushak_junction_chainages_digitized.csv` | 21.5 KB | Longitudinal chainage calibration and junction modeling | Delhi / Kushak | On-demand | DERIVED (Digitized drain chainages) | Git Tracked |
| `data/delhi/derived/validation/cwc_downstream/cwc_old_railway_bridge_event.csv` | 3.8 KB | Yamuna downstream boundary level validation | Delhi / Yamuna ORB | On-demand | OBSERVED / OFFICIAL (CWC gauge records) | Git Tracked |
| `data/delhi/derived/validation/dtp_waterlogging/dtp_waterlogging_severity_normalized.csv` | 4.7 KB | Delhi Traffic Police waterlogging severity validation | Delhi / NCT Delhi | On-demand | OBSERVED / OFFICIAL (DTP traffic logs) | Git Tracked |
| `data/delhi/raw/drainage/kushak_longitudinal_profile_curated.json` | 20.6 KB | Kushak longitudinal profile evidence model | Delhi / Kushak | On-demand | OFFICIAL / CURATED (Appendix XII profile) | Git Tracked |
| **Subtotal (Delhi V2)** | **2,302.9 KB (~2.25 MB)** | | | | | |

---

### 2.2 Mumbai V1 Pilot Assets (`backend/app/data/`)
| Path | File Size | Feature Requiring It | City / Catchment | Lifecycle | Provenance | Bundling Strategy |
|---|:---:|---|---|:---:|---|:---:|
| `backend/app/data/dem/mumbai_pilot_dem_30m.tif` | 76.7 KB | Mumbai flood modeling pipeline, `/ready` health probe | Mumbai / Kurla | **Startup + On-demand** | DERIVED (Copernicus 30m GLO-30 DSM) | Git Tracked |
| `backend/app/data/drainage/bmc/storm_water_drains_pilot.geojson` | 856.8 KB | BMC storm water drain polylines and capacity analysis | Mumbai / Kurla | On-demand | OFFICIAL (BMC GIS Layer-8) | Git Tracked |
| `backend/app/data/drainage/bmc/storm_water_manholes_pilot.geojson` | 382.8 KB | BMC storm water manhole points | Mumbai / Kurla | On-demand | OFFICIAL (BMC GIS Layer-8) | Git Tracked |
| `backend/app/data/roads/mumbai_pilot_intersections.geojson` | 318.8 KB | Mumbai road intersection flood intelligence | Mumbai / Kurla | On-demand | DERIVED (OSM intersections) | Git Tracked |
| `backend/app/data/roads/mumbai_pilot_roads.geojson` | 502.0 KB | Mumbai road segment flood risk & safe routing | Mumbai / Kurla | On-demand | DERIVED (OSM road network) | Git Tracked |
| `backend/app/data/roads/delhi_kushak_roads.geojson` | 4,402.2 KB | Delhi OSM road segments for street flood risk & routing | Delhi / Kushak | On-demand | DERIVED (OSM road network) | Git Tracked |
| `backend/app/data/roads/delhi_kushak_roads.provenance.json` | 2.0 KB | Evidence lineage contract for Delhi OSM road network | Delhi / Kushak | On-demand | OFFICIAL METADATA | Git Tracked |
| `backend/app/data/mumbai_pilot_osm_raw.json` | 1,230.1 KB | Raw OSM data reference for Mumbai pilot | Mumbai / Kurla | On-demand | DERIVED (OSM Overpass API) | Git Tracked |
| **Subtotal (Mumbai V1 + Roads)** | **7,771.4 KB (~7.59 MB)** | | | | | |

---

### 2.3 Precomputed Fixtures (Deterministic Accelerators)
| Path | Est. Size | Feature Requiring It | City / Catchment | Lifecycle | Provenance | Bundling Strategy |
|---|:---:|---|---|:---:|---|:---:|
| `backend/app/data/historical/mumbai_2017_replay.json` | ~250 KB | `/flood/historical/2017` instant replay | Mumbai / Kurla | On-demand | SIMULATED_RECONSTRUCTION / OBSERVED | Git Tracked |
| `backend/app/data/scenarios/sim-SCN-01-*.json` | ~120 KB | `/api/scenarios/SCN-01/run` instant response | Delhi / Kushak | On-demand | SIMULATED_MODEL_OUTPUT | Git Tracked |
| `backend/app/data/scenarios/sim-SCN-02-*.json` | ~120 KB | `/api/scenarios/SCN-02/run` instant response | Delhi / Kushak | On-demand | SIMULATED_MODEL_OUTPUT | Git Tracked |
| `backend/app/data/scenarios/sim-SCN-03-*.json` | ~120 KB | `/api/scenarios/SCN-03/run` instant response | Delhi / Kushak | On-demand | SIMULATED_MODEL_OUTPUT | Git Tracked |
| `backend/app/data/scenarios/sim-SCN-04-*.json` | ~120 KB | `/api/scenarios/SCN-04/run` instant response | Delhi / Kushak | On-demand | SIMULATED_MODEL_OUTPUT | Git Tracked |
| `backend/app/data/scenarios/sim-SCN-05-*.json` | ~120 KB | `/api/scenarios/SCN-05/run` instant response | Delhi / Kushak | On-demand | SIMULATED_MODEL_OUTPUT | Git Tracked |
| `backend/app/data/scenarios/sim-SCN-06-*.json` | ~240 KB | `/api/scenarios/SCN-06/run` instant response | Delhi / Kushak | On-demand | SIMULATED_MODEL_OUTPUT | Git Tracked |
| **Subtotal (Snapshots)** | **~1,090 KB (~1.06 MB)** | | | | | |

---

## 3. Grand Total Runtime Package Size
- **Total Tracked Data Footprint:** **~10.9 MB**
- **Ignored Research / Raw Footprint:** **~600.0 MB** (98.2% reduction from raw repository disk usage).

---

## 4. Maintenance & Exclusion Rules

1. **Never commit raw PDF reports:** E.g., `ndmc_council_meeting_*.pdf`, `appendixxii.pdf`, `chennai.pdf`.
2. **Never commit raw multi-band satellite rasters:** E.g., `ESA_WorldCover_*.tif`, `Copernicus_DSM_*.tif`, `kushak_dsm_utm44n.tif`.
3. **Never commit profiling or scratch data:** Files in `.superpowers/`, `.system_generated/`, or scratch directories.
4. **Preserve provenance:** Precomputed fixtures retain strict metadata (`SIMULATED_RECONSTRUCTION`, `SIMULATED_MODEL_OUTPUT`) and must never be labeled as real observed measurements.
