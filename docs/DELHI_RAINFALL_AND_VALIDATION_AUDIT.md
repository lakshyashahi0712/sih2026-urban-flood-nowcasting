# Delhi V2 Rainfall & Flood Observation Audit

## 1. Rainfall Data Sources Reconnaissance

Urban flood nowcasting requires precipitation data across two distinct operational time horizons:
1. **Real-time & Nowcasting (0–3h)**: High-temporal-resolution observations and short-term forecasts to force the forward simulation.
2. **Historical Event Replay (Calibration & Validation)**: Authoritative hourly storm hyetographs from historic severe monsoon storms.

---

### 1.1 Detailed Audit of Delhi Rainfall Providers

| Source / Provider | Operator | Live vs. Historical | Temporal Resolution | Spatial Resolution | Modality (Numeric vs. Visual) | Access Method / API | Access Restrictions | Suitability for Hydrodynamic Model Forcing | Provenance Classification |
|---|---|---|---|---|---|---|---|---|---|
| **IMD Safdarjung Base Observatory** | India Meteorological Dept. (IMD) | Both (Live + Historical since 1901) | Hourly (Live AWS), Daily (Climate records) | Point ($28.585^\circ\text{N}, 77.206^\circ\text{E}$) | Numeric (mm) | MAUSAM API / Daily Weather Reports | Public Open Access | **Ideal Base Forcing** for South/Central Delhi (Barapullah / Kushak) | `OBSERVED` |
| **IMD Lodhi Road Observatory** | IMD | Both | Hourly AWS | Point ($28.590^\circ\text{N}, 77.220^\circ\text{E}$) | Numeric (mm) | MAUSAM Portal | Public Open Access | **Ideal Secondary Forcing** for Barapullah basin | `OBSERVED` |
| **IMD Palam Airport AWS** | IMD | Both | Half-hourly (METAR) / Hourly | Point ($28.563^\circ\text{N}, 77.116^\circ\text{E}$) | Numeric (mm) | Aviation Weather Portal / MAUSAM | Public Open Access | Excellent for Southwest Delhi | `OBSERVED` |
| **IMD Delhi Ridge AWS** | IMD | Both | Hourly | Point ($28.670^\circ\text{N}, 77.210^\circ\text{E}$) | Numeric (mm) | MAUSAM Portal | Public Open Access | **Ideal Forcing** for North Delhi / Qudesia Nallah | `OBSERVED` |
| **IMD Delhi Doppler Weather Radar (Palam)** | IMD | Live | 10–15 min sweep | $500\text{ m} - 1\text{ km}$ polar radial grid | **Visual (PPI/MAX dBZ PNG/GIF)**; Raw volume is binary UF/NetCDF | MAUSAM website display; Raw radar data restricted | **Restricted** (MoES data policy blocks raw QPE API) | **Prohibited from direct intensity decoding** (no official numeric QPE API). Visual images must NOT be color-decoded. | `UNAVAILABLE_FOR_QPE` |
| **Open-Meteo Hourly NWP API** | Open-Meteo GmbH (ECMWF / GFS blends) | Live + Recent Forecast (0–3h lead) | 1 hour | $0.1^\circ \times 0.1^\circ$ (~$11\text{ km}$) | Numeric (JSON) | `https://api.open-meteo.com/v1/forecast` | Free open public REST API | **Operational Fallback / Forecast Forcing** for 0–3h forward prediction | `NWP_FORECAST` |
| **National Water Data Portal (India-WRIS)** | NWIC / Ministry of Jal Shakti | Historical | Daily / Monthly | Basin / District | Numeric (CSV/XLS) | `indiawris.gov.in` | Free public registration | Good for multi-decadal water balance; inadequate for sub-hourly nowcasting | `OBSERVED` |
| **Delhi DMP 2018 Historical Storm Data** | IIT Delhi / I&FC | Historical | Hourly / 15-min | Point rain gauges | Numeric (Report tables) | DMP Volume II Appendices | Published report tables | **Authoritative Historical Forcing** for model calibration | `SECONDARY_REPORT` |

---

### 1.2 Strict Radar Rule Enforcement
- **IMD Radar Constraints**: While IMD operates a C-band Doppler Weather Radar (DWR) at Palam and a polarimetric radar at Mausam Bhawan (Lodhi Road), only rendered PNG/GIF reflectivity graphics are accessible to the public.
- **Rule Compliance**: In strict adherence to project guidelines, **IMD radar visual products MUST NOT be color-decoded into rainfall intensity**. Color-decoding uncalibrated radar imagery introduces gross quantitative precipitation estimation (QPE) errors ($\pm 300\%$) due to ground clutter, beam blockage by urban high-rises, and uncalibrated $Z\text{--}R$ relationships ($Z = a R^b$).
- **V2 Operational Policy**:
  - Live nowcasting forward runs will use **Open-Meteo NWP forecasts** as the operational quantitative forecast driver, calibrated against **IMD Safdarjung / Lodhi Road AWS hourly observations**.

---

### 1.3 Notable Historical Deluge Events for Delhi V2 Replay

1. **8–10 July 2023 Deluge (The Benchmark Historical Event)**:
   - *Precipitation*: **153.0 mm in 24 hours** recorded at Safdarjung on 9 July 2023 (highest single-day July rainfall in 41 years since 1982).
   - *Peak Hourly Intensity*: Exceeded $45\text{ mm/h}$ during afternoon storm burst.
   - *Fluvial Coincidence*: Concurrently, the Yamuna River reached an all-time record water level of **208.66 m** at the Old Railway Bridge on July 13, 2023, submerging outfall drains and creating a catastrophic compound flood across North, Central, and East Delhi.
   - *Suitability*: **Primary candidate for V2 retrospective event replay**.
2. **11 September 2021 Severe Cloudburst**:
   - *Precipitation*: **117.9 mm in 24 hours** at Safdarjung, with $80\text{ mm}$ falling within 3 hours.
   - *Impact*: Widespread street inundation; Minto Bridge, Pul Prahladpur, AIIMS, and Ring Road completely submerged.

---

## 2. Flood Observation & Ground-Truth Validation Data

Validation data must be strictly segregated from model outputs:
- **OBSERVED GROUND TRUTH**: Direct physical measurements, high-water marks, traffic police closure logs, or crowdsourced geotagged photos.
- **MODELLED / DERIVED OUTPUT**: Flood depths, velocity vectors, and inundation masks generated by the physics engine or ML layers.

---

### 2.1 Authoritative Delhi Flood Observation Sources

| Observation Source | Lead Organization | Modality | Coordinates | Water Depth Information | Timestamp & Event Linkage | Access & Licensing | Validation Usability |
|---|---|---|---|---|---|---|---|
| **IIT Delhi Aab Prahari Platform** | Water Security and Sustainable Development Hub, IIT Delhi | Crowdsourced citizen science mobile reports | Precise GPS lat/lon | Reported depth ranges ($< 0.15\text{ m}, 0.15 - 0.30\text{ m}, > 0.50\text{ m}$) | Timestamped with geotagged photo attachments | Academic research database; published in project reports and journal articles | **High for Barapullah Basin**. Specifically targeted to the Barapullah pilot catchment. |
| **Delhi Traffic Police (DTP) Waterlogging Hotspots** | Delhi Traffic Police / Govt. of NCT of Delhi | Official public advisories & traffic disruption logs | Verified landmark intersections and road underpasses | Categorized by severity (Severe $\ge 0.5\text{ m}$, Moderate $0.2 - 0.5\text{ m}$, Mild $< 0.2\text{ m}$) | Linked to specific monsoon rain days and storm advisories | Publicly released annual advisories and court compliance filings | **Authoritative Ground Truth**. 147 officially gazetted chronic hotspots. |
| **Delhi DMP 2018 Waterlogged Vulnerability Inventory** | IIT Delhi / Dept. of I&FC | Engineered survey tables and hotspot maps | Geo-referenced road intersections | Observed peak waterlogging depth and duration | Documented across historic storms (2003, 2010, 2013) | Published report appendices | **Ideal for Baseline Verification**. Tabulates exact failure points. |
| **CWC Yamuna River Gauge Records** | Central Water Commission (CWC) | Physical staff gauge & automated telemetry | Old Railway Bridge ($28.660^\circ\text{N}, 77.240^\circ\text{E}$) | Water surface elevation ($m$ above MSL) | Hourly stage records | CWC Hydrological Data / India-WRIS | **Critical Boundary Condition** for drain outfall submergence. |

---

### 2.2 Chronic Waterlogging Hotspots in Candidate Catchments

#### A. Barapullah / Kushak Nallah Corridor Hotspots
1. **AIIMS Flyover & Underpass (Aurobindo Marg / Ring Road)**:
   - *Coordinates*: $28.5685^\circ\text{N}, 77.2105^\circ\text{E}$
   - *Severity*: DTP Category A (Chronic severe waterlogging, depths frequently exceed $0.60\text{ m}$).
   - *Cause*: Depression at junction of Kushak Nallah culvert crossing; stormwater backs up when Kushak is bankfull.
2. **South Extension Part I & II (Ring Road)**:
   - *Coordinates*: $28.5720^\circ\text{N}, 77.2215^\circ\text{E}$
   - *Severity*: DTP Category B ($0.30 - 0.50\text{ m}$).
   - *Cause*: Local terrain depression adjacent to Kushak Nallah open channel.
3. **Moolchand Underpass (Lala Lajpat Rai Marg / Ring Road)**:
   - *Coordinates*: $28.5670^\circ\text{N}, 77.2340^\circ\text{E}$
   - *Severity*: DTP Category A (Depths exceed $0.80\text{ m}$ during heavy bursts; requires dedicated PWD dewatering pumps).
4. **Defence Colony Underpass**:
   - *Coordinates*: $28.5790^\circ\text{N}, 77.2365^\circ\text{E}$
   - *Severity*: DTP Category A (Depths $> 0.50\text{ m}$; severe traffic halting).

#### B. Qudesia Nallah Corridor Hotspots
1. **Kashmere Gate ISBT / Ring Road Bypass**:
   - *Coordinates*: $28.6685^\circ\text{N}, 77.2310^\circ\text{E}$
   - *Severity*: DTP Category A ($0.50 - 1.20\text{ m}$ during Yamuna high stage).
   - *Cause*: Compound flood—local street runoff trapped behind elevated river embankment + Yamuna backflow through Qudesia regulator.
2. **Mori Gate Underpass**:
   - *Coordinates*: $28.6650^\circ\text{N}, 77.2220^\circ\text{E}$
   - *Severity*: DTP Category A (Chronic underpass submergence).
3. **Monastery Market / Ladakh Buddhist Market (Ring Road)**:
   - *Coordinates*: $28.6720^\circ\text{N}, 77.2325^\circ\text{E}$
   - *Severity*: DTP Category A (Severely inundated during July 2023 Yamuna event).
