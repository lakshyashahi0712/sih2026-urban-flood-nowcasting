# Delhi Satellite Historical Flood-Extent Access Audit

## 1. Attempt to Access Copernicus Data Space OData API
- **Target URL**: https://catalogue.dataspace.copernicus.eu/odata/v1
- **Agency**: European Space Agency (ESA) / Copernicus Programme
- **What the resource represents**: OData API for searching and accessing satellite imagery products (Sentinel-1, Sentinel-2, etc.) from the Copernicus Data Space.
- **Date coverage**: Not determined due to inaccessibility.
- **Whether records are historical**: Not determined.
- **Available fields**: Not determined.
- **Machine-readable access**: Not determined (API inaccessible).
- **Whether individual records can be retrieved**: Not determined.
- **Whether bulk extraction is possible**: Not determined.
- **Whether Kushak/Barapullah area can be identified explicitly**: Not determined.
- **Whether the data supports**:
  - occurrence validation: Not determined
  - spatial validation: Not determined
  - temporal validation: Not determined
  - depth validation: Not determined
- **Provenance and limitations**: Multiple attempts to access the Copernicus Data Space OData API returned HTTP 404 Not Found errors. Attempts included:
  - Base URL: https://catalogue.dataspace.copernicus.eu/odata/v1
  - Metadata endpoint: https://catalogue.dataspace.copernicus.eu/odata/v1/$metadata
  - Alternative versionless endpoint: https://catalogue.dataspace.copernicus.eu/odata
  - Root domain: https://catalogue.dataspace.copernicus.eu
  All attempts resulted in 404 responses, indicating the API endpoint is inaccessible or unavailable.

## 2. Event-Specific Analysis (Inaccessible API Prevents Evaluation)
Due to the inability to access the Copernicus Data Space OData API, no evaluation could be performed for the following events:

### Event 1: 2023-07-08 to 2023-07-10 (Search Window: 2023-07-06 to 2023-07-12)
- **Sentinel-1 SAR (Primary)**: No assessment possible.
- **Sentinel-2 (Secondary)**: No assessment possible.
- **Geographic bounds**: Kushak/Barapullah area (approx. 77.18-77.28°E, 28.55-28.62°N) could not be queried.
- **Temporal overlap**: Could not verify acquisition timestamps relative to event window.
- **Product details**: Could not inspect product IDs, sensor (Sentinel-1A/1B), polarization, orbit direction, or product type (GRD/SLC).
- **Footprint/coverage**: Could not determine overlap with Kushak area.
- **Download/access mechanism**: Could not verify.
- **Metadata machine-readability**: Could not assess via API.

### Event 2: 2024-06-28 (Search Window: 2024-06-26 to 2024-06-30)
- **Sentinel-1 SAR (Primary)**: No assessment possible.
- **Sentinel-2 (Secondary)**: No assessment possible.
- Same limitations as above apply.

## 3. Limitations
- The Copernicus Data Space OData API endpoint (https://catalogue.dataspace.copernicus.eu/odata/v1) is inaccessible via automated HTTP requests, returning consistent 404 errors.
- Without API access, no satellite imagery metadata can be retrieved, searched, or inspected.
- Consequently, no determination can be made regarding the availability, suitability, or machine-readability of Sentinel-1 or Sentinel-2 data for flood extent validation over the Kushak/Barapullah area for the specified events.
- The inaccessibility prevents evaluation of scientific limitations (e.g., SAR layover, shadows, urban effects) that would require actual product inspection.
- No distinction can be made between imagery availability and flood extent derivation capability.

## 4. Recommended Downstream Use
None. The primary data source (Copernicus Data Space OData API) is inaccessible, preventing any assessment of satellite imagery for historical flood extent validation.

## 5. Verdict
NO-GO