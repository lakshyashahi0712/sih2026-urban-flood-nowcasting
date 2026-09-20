# IMD Rainfall Archive Acquisition — Practitioner Playbook

How to actually get India Meteorological Department rainfall data for Delhi (Safdarjung, Palam, Lodhi Road) for 2015–2026: the free routes that work today, the routes that look open but aren't, and the sanctioned paid route. Every route below was probed live on 2026-09-16 with real downloads, not just search results.

---

## The lay of the land

- IMD's station archive is not on any open portal. The historical station series (daily/hourly, per-station, quality-controlled) is supplied only through the IMD Data Supply Portal (DSP) at NDC Pune under an account-enrolment workflow launched 16 Aug 2021 (v4.0). The portal is alive and fast: September 2026 saw 173 requests received, 118 completed, average delivery 2 minutes. — [IMD-DSP portal + delivery stats](https://dsp.imdpune.gov.in/home_sampledata_costestimate.php)
- Enrolment is a portal login process, not an email request; the procedure document specifies the v4.0 account-login flow and revised data charges. — [Procedure for Data Procurement (IMD)](https://mausam.imd.gov.in/shimla/docs/data-procedure.pdf)
- Escalation if a request stalls: NDC Data Service (data.service@imd.gov.in, +91 20 25572 255), then In-Charge NDC, then Head CRS Pune — published with timeframes. — [IMD-DSP escalation matrix](https://dsp.imdpune.gov.in/home_sampledata_costestimate.php)
- Three genuinely free routes exist and each fills a different hole: NOAA GHCNd per-station daily CSVs (official 0830-0830 gauge-derived values, partial recent coverage), IMD Pune's 0.25° gridded daily product 1901–2024 (complete, official, area-averaged), and rolling ~28-day windows (NWDP CKAN, api.imd.gov.in) for current seasons only. — [NCEI GHCNd access](https://www.ncei.noaa.gov/products/land-based-station/global-historical-climatology-network-daily), [IMD Pune gridded rainfall](https://www.imdpune.gov.in/cmpg/Griddata/Rainfall_25_NetCDF.html), [NWDP IMD rainfall dataset](https://www.data.gov.in/resource/rainfall-daily-imd)
- Reanalysis products (Open-Meteo/ERA5 family) are not rainfall observations for Delhi: on 2021-09-11 they returned 15.3 mm where Safdarjung's official value is 95.0 mm. Use for temporal shape only, never as forcing truth. — [GHCNd Safdarjung CSV](https://www.ncei.noaa.gov/data/global-historical-climatology-network-daily/access/IN022021900.csv), [Open-Meteo archive API](https://archive-api.open-meteo.com/v1/archive)

---

## Route A — GHCNd per-station CSVs: the free workhorse

This is the highest-value free route for event work and was verified end-to-end.

- Delhi's canonical GHCNd station IDs are `IN022021900` (NEW DELHI/SAFDARJUN, 28.583 N 77.200 E), `IN022023000` (NEW DELHI/PALAM, 28.567 N 77.117 E), and `IN022021600` (DELHI SADAR). Match them from the fixed-column station list; do not trust city-name searches (they return dozens of Delhis in North America). — [ghcnd-stations.txt](https://www.ncei.noaa.gov/pub/data/ghcn/daily/ghcnd-stations.txt)
- Safdarjung's PRCP series spans 1901–2025; Palam's 1959–2025. DELHI SADAR ends in 1965 — climatology only. — [IN022021900.csv](https://www.ncei.noaa.gov/data/global-historical-climatology-network-daily/access/IN022021900.csv), [IN022023000.csv](https://www.ncei.noaa.gov/data/global-historical-climatology-network-daily/access/IN022023000.csv), [IN022021600.csv](https://www.ncei.noaa.gov/data/global-historical-climatology-network-daily/access/IN022021600.csv)
- The per-station access CSV is wide-format (`"STATION","DATE",...,"PRCP","PRCP_ATTRIBUTES"`), PRCP in tenths of mm, −99.9 = missing. Download URL pattern: `https://www.ncei.noaa.gov/data/global-historical-climatology-network-daily/access/<ID>.csv`. — [GHCNd Safdarjung CSV head](https://www.ncei.noaa.gov/data/global-historical-climatology-network-daily/access/IN022021900.csv)
- Values are official-gauge compatible: 2023-07-09 Safdarjung 152.9 mm and 2024-06-28 228.1 mm reproduce the canonical press figures for those storms; Palam 103.1 mm on 2021-09-11 sits beside Safdarjung's 95.0 mm. — [IN022021900.csv](https://www.ncei.noaa.gov/data/global-historical-climatology-network-daily/access/IN022021900.csv), [IN022023000.csv](https://www.ncei.noaa.gov/data/global-historical-climatology-network-daily/access/IN022023000.csv)
- Gotcha: recent-year rows carry source flag `S` = Global Summary of the Day (DSI-9618), a METAR-derived 24-h accumulation, not the archived synoptic day. Consequences: (a) the daily "day" approximates the synoptic 0830–0830 IST gauge day — India measures daily rainfall 0830–0830 IST; (b) day coverage is partial — ~78–104 days/year 2015–2024, ending 2025-08-24; (c) values can differ slightly from IMD's own daily publication. Treat every day as *present* or *absent*; absence is not zero. — [ghcnd readme (source flags)](https://www.ncei.noaa.gov/pub/data/ghcn/daily/readme.txt), [ECMWF forum: Indian daily = 0830–0830 IST](https://forum.ecmwf.int/t/questions-about-indian-station-data-and-daily-observation-time-in-copernicus-in-situ-surface-land-dataset/14559)
- Sampled coverage is not random: monsoon months are mostly present (July 2023 has 20 of 31 days), so key storm days are frequently hit — but always check the exact date before concluding anything.
- Element availability per station varies; expect PRCP + TMAX/TMIN for these IDs, with the attributes column identifying the source of each row.

---

## Route B — IMD Pune 0.25° gridded daily (official, free, complete)

- IMD publishes the Pai et al. 0.25°×0.25° daily gridded rainfall for 1901–2024 as free NetCDF/binary downloads from CMPG Pune — the longest, most complete official rainfall product for any Delhi location. — [IMD Pune gridded rainfall (NetCDF)](https://www.imdpune.gov.in/cmpg/Griddata/Rainfall_25_NetCDF.html)
- Built from 6,955 rain gauges after quality control; the download automation (IMDLIB) wraps it. — [IMDLIB: open-source library for IMD gridded data](https://www.sciencedirect.com/science/article/abs/pii/S1364815223002554)
- IMDLIB downloads and handles the binary/NetCDF grids with xarray; usable commands are `imdlib.get_data("rain", ...)` then `imdlib.open_to_xarray`. — [IMDLIB docs](https://imdlib.readthedocs.io/en/latest/), [imdlib on PyPI](https://pypi.org/project/imdlib/), [iamsaswata/imdlib on GitHub](https://github.com/iamsaswata/imdlib)
- Delhi sits in grid cells (77.25 E, 28.50 N) and (77.25 E, 28.75 N) — exactly the cells the open "Delhi Rainfall Data" CKAN dataset republishes as monthly CSVs 1901–2021. Use those CSVs for quick sanity checks, the NetCDF for event work. — [Delhi Rainfall Data (opencity CKAN)](https://data.opencity.in/dataset/delhi-rainfall-data)
- Real-time gridded rainfall is also published on IMD Pune's LRF/Climate Application pages for recent periods. — [IMD Pune LRF index](https://www.imdpune.gov.in/lrfindex.php), [Climate Application UI](https://www.imdpune.gov.in/caui.php)
- Gotcha: a grid-cell average is not a station observation — for Kushak-scale event forcing treat gridded as corroboration/antecedent context, and cite it as DERIVED, never as station totals. The CDSP portal launch (free gridded download) is the PIB-documented origin of this product line. — [PIB: Climate Data Service Portal](https://www.pib.gov.in/PressReleaseIframePage.aspx?PRID=1707201)

---

## Route C — Rolling windows and APIs (current data only)

- The National Water Data Portal (NWDP) exposes IMD "Rainfall Daily" as an open CKAN datastore API by State/District/Date — but only a rolling ~28-day window (verified 2026-08-19 → 2026-09-15 for `'NCT of DELHI'`). Poll it on a schedule to accumulate your own archive. — [NWDP dataset page](https://nwdp.nwic.gov.in/dataset/), [data.gov.in resource](https://www.data.gov.in/resource/rainfall-daily-imd)
- IMD's official API suite includes `districtrainfall` (daily/weekly/cumulative/monthly actual + normal per district) and station nowcast/current-weather endpoints with `Past_24_hrs_Rainfall` — current-facing, IP-whitelisted for production use. — [IMD API reference](https://api.imd.gov.in/public/api_reference.html), [IMD APIs page](https://mausam.imd.gov.in/responsive/apis.php)
- The API's AWS/ARG sample payload carries temperature/wind/pressure but **no rainfall field** — don't build an AWS-rainfall pipeline on `api.imd.gov.in/api/v1/aws_data` without checking live payloads first. — [IMD API reference, AWS/ARG section](https://api.imd.gov.in/public/api_reference.html)
- District "Daily Actual" values (e.g. Central Delhi 102.2 mm on 2026-08-25) are station-max-based district aggregates — usable as event forcing corroboration at district level, distinct from station gauge totals. — [IMD district rainfall API](https://api.imd.gov.in/api/v1/districtrainfall)

---

## Route D — Sub-daily: 3-hourly, hourly, and the paid archive

- IMD New Delhi (amssdelhi.gov.in) publishes an "Observational Data of Delhi → 3 Hourly Rainfall Delhi/NCR" page — live today, current periods only. Its menu also carries per-station 7-day forecast pages (Safdarjung, Palam, Ayanagar, Ridge, Narela, Delhi University). — [IMD New Delhi menu](https://amssdelhi.gov.in/07072017/left.html)
- The 2018-era hourly route: `aws.imd.gov.in` exposed state-wise hourly ARG/AWS tables one week at a time (1,351 ARG + 573 AWS stations); community scripts archived 2018 JJA hourly data one month at a time. — [India Water Portal: station-wise hourly rainfall from IMD](https://www.indiawaterportal.org/climate-change/climate/station-wise-hourly-rainfall-data-imd-now-available)
- The scraper (`getpastRainfallData`) hits the IMD AWS site per month with station/date parameters; Wayback retains the underlying endpoints (`AWS/rainfalldown.php`, dated `AGRIMET/YYYY-MM-DD.csv` files from 2018). Availability of historical years through this route today is unverified — probe before relying on it. — [craigdsouza/getRainfallData](https://github.com/craigdsouza/getRainfallData), [Wayback CDX: aws.imd.gov.in](http://web.archive.org/cdx/search/cdx?url=aws.imd.gov.in*&output=json&collapse=urlkey&fl=timestamp,original,statuscode&limit=300)
- For guaranteed sub-daily history (autographic/ARG series), the sanctioned route is the DSP paid request: register on dsp.imdpune.gov.in, check availability + charge estimate before submitting (v2.0 feature), track via the portal dashboard. Sample formats list "Surface Rainfall Autographic" explicitly. — [IMD-DSP formats & cost](https://dsp.imdpune.gov.in/home_sampledata_costestimate.php)
- NOAA's GHCNh (launched May 2024, replaces ISD, aligned with GHCNd IDs) is the free hourly hope for 42182-series stations — check the official station list and bulk-download (PSV/parquet) for Delhi holdings before assuming. — [GHCNh product page](https://www.ncei.noaa.gov/products/global-historical-climatology-network-hourly), [GHCNh bulk download](https://www.ncei.noaa.gov/oa/global-hourly/), [GHCNh Explorer guide](https://climateexplorer.app/guides/ghcnh/)

---

## Gotchas that cost hours

- gov.in TLS often fails Python defaults with `DH_KEY_TOO_SMALL`; rebuild the context with `set_ciphers('DEFAULT:@SECLEVEL=1')` (verified needed for amssdelhi.gov.in).
- ESRI ArcGIS REST servers serving GSDL-style layers: `f=json` + `outSR=4326` can silently return empty features while `f=geojson` works, and `resultOffset` pagination can be ignored — count-only queries are the reliable liveness test.
- Wayback CDX returns 503s under load; sleep between calls, and treat capture-index hits of PDF bulletins as a discovery index, not a guarantee (some captures are truncated server-side).
- `python` + heredoc scripts with CRLF endings corrupt on Windows Git Bash — write builder scripts to files instead of piping heredocs.
- IMD daily = 0830–0830 IST; GHCNd `S`-flagged rows approximate this but are synoptic-derived. Never mix a GHCNd `S` row with an IMD-published same-date value in one series without labeling provenance.
- Daily ≠ hourly: never manufacture hourly from daily (or 3-hourly from daily); preserve native resolution and label derived products DERIVED.

---

## Recommended strategy for the Kushak event catalogue

1. Backfill all catalogue event windows from Route A (Safdarjung + Palam CSVs) — verified to hit 2021-05-20, 2021-07-30, 2021-09-11, 2023-05-27, 2023-07-09, 2024-06-28 with official-compatible values; explicitly mark days absent from the `S`-flag coverage as NOT_AVAILABLE (not zero).
2. Route B (0.25° grid via IMDLIB) for complete daily context 2015–2024: antecedent indicators (24h/72h/7d) and cross-checks of unobserved event days — labeled DERIVED.
3. Keep Route C polling as a standing acquisition habit for 2025–2026 onward (NWDP 28-day + district API), archiving weekly.
4. If sub-daily forcing becomes a hard requirement for identification, submit one DSP request specifying stations (Safdarjung, Palam, Lodhi Road), period (2015–2026), element (autographic/ARG rainfall), and format — availability check + cost estimate are free before commitment.
5. Never cite Open-Meteo/ERA5 as station forcing (verified 6× underestimate on a key event day); use only for temporal shape with a caution flag.

---

## Sources

- https://dsp.imdpune.gov.in/home_sampledata_costestimate.php
- https://mausam.imd.gov.in/shimla/docs/data-procedure.pdf
- https://www.ncei.noaa.gov/pub/data/ghcn/daily/ghcnd-stations.txt
- https://www.ncei.noaa.gov/pub/data/ghcn/daily/readme.txt
- https://www.ncei.noaa.gov/data/global-historical-climatology-network-daily/access/IN022021900.csv
- https://www.ncei.noaa.gov/data/global-historical-climatology-network-daily/access/IN022023000.csv
- https://www.ncei.noaa.gov/data/global-historical-climatology-network-daily/access/IN022021600.csv
- https://www.ncei.noaa.gov/products/land-based-station/global-historical-climatology-network-daily
- https://www.ncei.noaa.gov/products/global-historical-climatology-network-hourly
- https://www.ncei.noaa.gov/oa/global-hourly/
- https://climateexplorer.app/guides/ghcnh/
- https://www.imdpune.gov.in/cmpg/Griddata/Rainfall_25_NetCDF.html
- https://www.imdpune.gov.in/lrfindex.php
- https://www.imdpune.gov.in/caui.php
- https://www.pib.gov.in/PressReleaseIframePage.aspx?PRID=1707201
- https://imdlib.readthedocs.io/en/latest/
- https://pypi.org/project/imdlib/
- https://github.com/iamsaswata/imdlib
- https://www.sciencedirect.com/science/article/abs/pii/S1364815223002554
- https://data.opencity.in/dataset/delhi-rainfall-data
- https://nwdp.nwic.gov.in/dataset/
- https://www.data.gov.in/resource/rainfall-daily-imd
- https://api.imd.gov.in/public/api_reference.html
- https://mausam.imd.gov.in/responsive/apis.php
- https://amssdelhi.gov.in/07072017/left.html
- https://www.indiawaterportal.org/climate-change/climate/station-wise-hourly-rainfall-data-imd-now-available
- https://github.com/craigdsouza/getRainfallData
- http://web.archive.org/cdx/search/cdx?url=aws.imd.gov.in*&output=json&collapse=urlkey&fl=timestamp,original,statuscode&limit=300
- https://archive-api.open-meteo.com/v1/archive
- https://forum.ecmwf.int/t/questions-about-indian-station-data-and-daily-observation-time-in-copernicus-in-situ-surface-land-dataset/14559

---
*Captured: 2026-09-16*
