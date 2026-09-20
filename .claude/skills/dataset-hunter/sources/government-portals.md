# Government Portals Source

## Overview
Searches various government open data portals at municipal, state, national, and international levels.

## Search Approach
- Maintains a list of known government open data portals
- For each portal, attempts to use their API (CKAN, Socrata, ArcGIS, etc.) when available
- Falls back to website search when API is not available or documented
- Special focus on Indian government sources including data.gov.in and state portals

## Known Portals
### International
- data.gov (USA)
- data.gov.in (India)
- data.gov.uk (UK)
- data.gov.au (Australia)
- data.gc.ca (Canada)
- govdata.de (Germany)
- data.govt.nz (New Zealand)

### National (India)
- data.gov.in (National Open Data Portal)
- Various state portals (data.maharashtra.gov.in, data.karnataka.gov.in, etc.)
- Ministry-specific portals (IMD, ISRO, NRSC, etc.)

### Municipal/City
- City-specific open data portals (when discoverable)
- Smart City mission portals in India

## API Endpoints
Varies by portal:
- CKAN-based: {portal}/api/3/action/package_search
- Socrata-based: {portal}/resource/{id}.json
- ArcGIS Open Data: {portal}/opendata/api
- Custom APIs: portal-specific endpoints

## Rate Limits
- Varies significantly by portal
- Implements exponential backoff and respectful rate limiting
- Caches responses where appropriate
- Respects robots.txt and terms of service

## Data Extracted
For each dataset, extracts:
- Title, description, and URL
- Publishing organization/agency
- Date published and last updated
- License information
- File formats and sizes
- Geographic and temporal coverage (when available)
- Update frequency
- Language
- Tags and categories

## Limitations
- Coverage depends on maintaining an updated list of portals
- API availability and quality varies widely between portals
- Some portals may require registration for certain datasets
- Language barriers for non-English portals
- Inconsistent metadata quality across different government entities