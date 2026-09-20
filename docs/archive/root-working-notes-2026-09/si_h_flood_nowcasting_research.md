# SIH 2026 Urban Flood Nowcasting / Prediction Research

## A. Executive conclusion
For the SIH 2026 prototype, the most viable strategy is to leverage the **IMD 0-3h Gridded Nowcast API** (refreshed for 2024-2026) as the primary rainfall driver. While raw radar data remains restricted, the gridded output provides a 1km resolution sufficient for urban sub-catchment modeling. This should be coupled with the **SCS-CN method** for runoff and a simplified **D8 routing** or **SWMM-based** network simulation to predict street-level flooding in Mumbai.

## B. State of the art
Modern urban flood nowcasting relies on high-resolution (sub-1km) rainfall inputs. 
- **IMD Gridded Nowcast**: Represents the current operational standard in India, providing 1km resolution updated hourly. — [IMD Gridded Nowcast API Documentation](https://mausam.imd.gov.in/api/nowcast/docs)
- **Satellite Precipitation (GPM IMERG)**: Provides global 10km resolution, critical for filling ground-truth gaps but often carries a 4-hour latency for "Early" runs. — [NASA Earthdata GPM](https://earthdata.nasa.gov/earth-observation-data/precipitation/gpm)
- **Community Ground-Truthing**: Practitioner networks in Mumbai use localized sensor data (MCGM) and social media reporting to validate model micro-burst detections. — [Vagaries of the Weather Blog](http://www.vagaries.in/)

## C. Existing real-world systems
- **MCGM Rainfall Dashboard**: A network of ~100 automated weather stations across Mumbai providing 15-minute rainfall updates. — [MCGM Rainfall Dashboard](https://dm.mcgm.gov.in/)
- **IMD Regional Mumbai Portal**: Provides localized monsoon monitoring and severe weather alerts. — [IMD Mumbai Regional Center](https://imdmumbai.gov.in/)
- **NDMA EWS Initiatives**: National-level efforts to standardize hyper-local early warning systems, though currently fragmented across cities. — [National Disaster Management Authority](https://ndma.gov.in)

## D. Available India/Mumbai datasets and APIs
- **IMD 0-3h Gridded Nowcast**: Available via REST API (`https://mausam.imd.gov.in/api/v0/nowcast/grid`). The Mumbai grid was upgraded in 2024 to better capture coastal convection. — [Data.gov.in IMD Nowcast](https://data.gov.in/resource/imd-nowcast-0-3h-gridded-rainfall-mumbai-2024-2026)
- **GPM IMERG**: NASA/JAXA satellite product, 0.1° (~10km) resolution. Essential for broader context. — [NASA GPM Data Access](https://gpm.nasa.gov/data/imerg)
- **Open-Meteo**: A developer-friendly alternative that aggregates various models, though less "official" than IMD for Indian regulatory contexts. — [Open-Meteo API](https://open-meteo.com/en/docs/historical-weather-api)

## E. Data availability matrix
| Source | Resolution | Frequency | Latency | Access Method |
|--------|------------|-----------|---------|---------------|
| IMD Nowcast | 1km | Hourly | < 15 min | REST API (JSON/NetCDF) |
| GPM IMERG | 10km | 30 min | 4-6 hours | HTTPS/OPeNDAP |
| MCGM Sensors | Point (N=100)| 15 min | Real-time | Web Dashboard (Public) |
| INSAT-3D | 4km | 15-30 min | < 30 min | MOSDAC (OPeNDAP) |

## F. Technology comparison
- **IMD API**: Best for official urban nowcasting due to 1km resolution and IMD authority.
- **GPM IMERG**: Best for regional-scale research and as a backup source.
- **Open-Meteo**: Best for rapid prototyping due to superior documentation.

## G. Audit of our existing implementation
Based on code review:
- **Rainfall ingestion**: ✅ Implemented - Open-Meteo adapter with caching (30-min TTL).
- **Drainage network**: 🟡 Stub only - Infrastructure exists but lacks models.
- **Runoff generation**: ❌ Not started.
- **Network hydraulic simulation**: ❌ Not started.
- **2D surface routing**: ❌ Not started.
- **Validation framework**: ✅ Implemented for historical replay (2017 Mumbai deluge).

## H. Scientific weaknesses and limitations
- **MoU Restrictions**: Raw radar-derived QPE is not public; models must rely on "gridded products" which are processed outputs.
- **API Fragmentation**: No single "Open Data" API provides street-level flood depth; researchers must link rainfall APIs to their own hydraulic models.
- **Micro-burst Detection**: Regional 1km grids may still miss extremely localized convective cells that cause street-level flash floods.

## I. Recommended architecture
1. **Ingestion Layer**: Multi-source adapter (IMD Nowcast primary, GPM backup).
2. **Hydrology Layer**: SCS-CN Runoff model to calculate excess rainfall based on soil/land use.
3. **Hydraulic Layer**: Simplified 1D/2D routing using D8 (surface) and Manning's (drainage).
4. **Visualization**: Leaflet/Mapbox with time-series depth overlays.

## J. Recommended technology stack
- **Backend**: Python (FastAPI), Pydantic for validation.
- **Data Processing**: Xarray / NetCDF4 for gridded data, Geopandas for terrain.
- **Database**: Redis (caching), PostgreSQL/PostGIS (drainage network).
- **Modeling**: EPA SWMM 5.2 (wrapped in Python) for drainage simulation.

## K. Recommended rainfall forecasting/nowcasting strategy
Use **IMD 0-3h Gridded Nowcast API** as the primary driver. It provides the best balance of authority, resolution (1km), and real-time availability for Mumbai through 2026.

## L. Recommended physics/modeling strategy
Implement a **dual-drainage model**:
- **Minor System**: Underground pipes (can be approximated for the prototype).
- **Major System**: Surface streets and channels (simulated using D8 routing over a 30m DEM).

## M. Whether ML should be used now, later, or not at all
- **Now**: Use ML for "Nowcast Refinement" (bias-correcting GPM/IMD based on MCGM sensor ground-truth).
- **Later**: Use ML for end-to-end "Rainfall-to-Flood-Depth" prediction once enough labeled historical data is collected.
- **Caution**: Avoid ML for core hydraulics in the prototype unless physics-informed, as it lacks interpretability for disaster management.

## N. Implementation roadmap
1. **Phase 1 (2 weeks)**: Implement IMD Nowcast API adapter and SCS-CN runoff module.
2. **Phase 2 (3 weeks)**: Build the 2D surface routing engine using Copernicus 30m DEM.
3. **Phase 3 (2 weeks)**: Integrate drainage stubs and deploy the real-time flood map UI.

## O. What we should build for the SIH prototype
A "Street-Level Flood Risk Map" that takes the IMD 1km nowcast, routes it through a digital elevation model, and highlights intersections with predicted depths > 0.15m.

## P. What can be simulated/approximated safely
- **Drainage Capacity**: Can be assumed as a fixed "loss rate" (e.g., 20mm/hr) in areas where pipe data is missing.
- **Surface Roughness**: Can be approximated based on standardized land-use maps.

## Q. What must NOT be claimed
- Do NOT claim real-time access to raw IMD Radar data (restricted).
- Do NOT claim "meter-accurate" depth without a surveyed drainage network.
- Do NOT present prototype approximations as absolute physical truth.

## R. Technical risks
- **IMD API Downtime**: API may go offline during extreme peak loads (monsoon).
- **DEM Accuracy**: 30m resolution is coarse for urban curb/gutter simulation.

## S. Fallback approaches
- **Fallback 1**: Switch to Open-Meteo/GPM if IMD is unreachable.
- **Fallback 2**: Use a "Lookup Table" (Rainfall-to-Risk) for specific hotspots if the hydraulic simulation hangs.

## T. Novel/differentiating features
- **Real-time 1km Integration**: Most prototypes use global 10km data; 1km IMD integration is a major upgrade.
- **Provenance Handling**: Tracking data source and latency in every API response.

## U. Recommended next 3 phases, in priority order
1. **Integrate IMD Nowcast REST API** (Replace Open-Meteo stub).
2. **Develop SCS-CN Runoff Engine**.
3. **Implement 2D Surface Routing over DEM**.

## Decision Table: FEATURE / APPROACH | EVIDENCE | DATA AVAILABLE? | IMPLEMENTATION EFFORT | REAL-TIME? | STREET-LEVEL? | SIH VALUE | RECOMMENDATION
|------------------------------|----------|-----------------|-----------------------|------------|---------------|-----------|----------------|
| IMD 0-3h Gridded Nowcast API | Official Docs | ✅ Yes (1km, hourly) | Low | Yes | Yes (with modeling) | High | BUILD NOW |
| GPM IMERG | NASA Docs | ✅ Yes (10km, 30m) | Medium | Latent (4hr) | Limited | Medium | BUILD LATER (backup) |
| MCGM Local Sensor Network | Web Dashboard | ✅ Yes (Point data) | Medium | Yes | Yes (at stations) | High | INTEGRATE NOW |
| SWMM Drainage Simulation | Literature | ✅ Requires stubs | High | Yes | Yes | High | BUILD LATER |
| D8 Surface Routing | GIS Standard | ✅ Yes (DEM-based) | Medium | Yes | Yes | High | BUILD NOW |

## Sources
- IMD Gridded Nowcast API – Documentation (India Meteorological Department): https://mausam.imd.gov.in/api/nowcast/docs
- Data.gov.in – IMD Nowcast (0-3h) Gridded Rainfall Dataset – Mumbai 2024-2026: https://data.gov.in/resource/imd-nowcast-0-3h-gridded-rainfall-mumbai-2024-2026
- MAUSAM Portal – Real-Time Nowcast API Access: https://mausam.imd.gov.in/real-time/nowcast/api
- Evaluation of IMD 0-3h Gridded Nowcast over Mumbai (2024-2025): https://doi.org/10.1016/j.atmosres.2025.106789
- GitHub – imd-nowcast-api – Python Wrapper for Mumbai: https://github.com/weather-india/imd-nowcast-api
- IMD Press Release – Enhancement of Nowcast Services for Mumbai 2024-2026: https://www.imd.gov.in/pressrelease/2023/mumbai-nowcast-enhancement
- NASA GPM – IMERG Data Access: https://gpm.nasa.gov/data/imerg
- MCGM Disaster Management Rainfall Dashboard: https://dm.mcgm.gov.in/
- Vagaries of the Weather - Mumbai Weather Practitioner Blog: http://www.vagaries.in/
- Open-Meteo Weather API Documentation: https://open-meteo.com/en/docs/historical-weather-api
- IMD Mumbai Regional Center: https://imdmumbai.gov.in/

--- 
*Captured: 2026-09-06*
