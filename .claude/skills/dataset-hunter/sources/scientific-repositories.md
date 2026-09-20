# Scientific Repositories Source

## Overview
Searches major scientific data repositories including NASA, NOAA, ESA, Copernicus, USGS, and other scientific organizations.

## Search Approach
- Maintains a list of known scientific data repositories
- For each repository, uses their specific API when available
- Falls back to website search when API is not available
- Focuses on earth observation, climate, hydrology, and geospatial datasets

## Known Repositories
### Space/Agencies
- NASA Earthdata (https://earthdata.nasa.gov)
- NOAA NCEI (https://www.ncei.noaa.gov)
- ESA Earth Online (https://earth.esa.int)
- Copernicus Open Access Hub (https://scihub.copernicus.eu)
- JAXA (https://www.eorc.jaxa.jp)
- ISRO Bhuvan (https://bhuvan.nrsc.gov.in)

### Earth Science
- USGS ScienceBase (https://www.sciencebase.gov)
- IRIS Data Management Center (https://www.iris.edu)
- UNAVCO (https://www.unavco.org)
- GEOSS Portal (https://www.geoportal.org)
- PANGAEA (https://doi.pangaea.de)

### Climate & Weather
- NOAA Climate Data Online (https://www.ncdc.noaa.gov/cdo-web)
- ECMWF Public Datasets (https://www.ecmwf.int/en/forecasts/datasets)
- NOAA Storm Events Database (https://www.ncdc.noaa.gov/stormevents)
- Global Precipitation Measurement (https://pmm.nasa.gov)

### Hydrology & Water
- GRDC (Global Runoff Data Centre) (https://www.bafg.de/GRDC)
- HYDROS (https://hydros.tamu.edu)
- CUAHSI HIS Central (https://hiscentral.cuahsi.org)
- WaterML2 services

## API Endpoints
Varies by repository:
- NASA CMR: https://cmr.earthdata.nasa.gov/search
- NOAA NCEI: https://www.ncei.noaa.gov/cdo-web/api/v2
- USGS ScienceBase: https://www.sciencebase.gov/catalog/items
- ESA Copernicus: API varies by service
- PANGAEA: https://doi.pangaea.de/api

## Rate Limits
- Varies significantly by repository
- Implements exponential backoff and respectful rate limiting
- Caches responses where appropriate
- Some require registration for heavy usage

## Data Extracted
For each dataset/granule, extracts:
- Title, description, and URL
- Collecting organization/instrument
- Temporal coverage (start/end dates)
- Spatial coverage (bounding box, geometry)
- Spatial and temporal resolution
- Variables/measurements
- Data format (NetCDF, HDF, GeoTIFF, etc.)
- File size and access method
- License information (often open for scientific use)
- DOI or persistent identifier
- Processing level and version
- Quality flags and metadata URLs

## Limitations
- Coverage depends on maintaining an updated list of repositories
- API availability and quality varies widely
- Some repositories specialize in specific data types (satellite, ground-based, etc.)
- Data volumes can be very large (TB/PB scale)
- Authentication may be required for certain datasets
- Near real-time data may have different access procedures