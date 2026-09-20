# OpenStreetMap (OSM) Source

## Overview
Searches OpenStreetMap for geospatial datasets, including planet extracts, regional extracts, thematic extracts, and specialized OSM-based datasets.

## Search Approach
- Searches official OSM download sources (planet.osm.org, download.geofabrik.de, etc.)
- Looks for OSM data in various formats (.osm.pbf, .osm.bz2, .shp, .geojson, .csv)
- Searches for thematic extracts (roads, buildings, waterways, land use, POIs, etc.)
- Searches for regional/country/city extracts
- Looks for specialized OSM-derived datasets (traffic, elevation, routing, etc.)
- Uses Overpass API for custom extractions when needed
- Searches for OSM-based research datasets and academic extracts

## Known Sources
### Official OSM Distribution
- Planet OSM (https://planet.osm.org)
- Geofabrik extracts (https://download.geofabrik.de)
- BBBike extracts (https://extract.bbbike.org)
- OSM Chaos (https://www.osmchaos.com)

### Thematic Extracts
- OpenStreetMap wastewater networks
- OSM buildings heights
- OSM landuse extracts
- OSM roads and highways
- OSM waterways and hydrology
- OSM points of interest (POI) datasets
- OSM public transport networks
- OSM cycling and walking infrastructure

### Regional/Country Extracts
- Country-specific extracts (available from Geofabrik, BBBike, etc.)
- State/province extracts
- City/metro area extracts
- Watershed/basin extracts
- Custom boundary extracts

### Specialized OSM-Derived
- Elevation datasets derived from OSM (SRTM, ASTER merged with OSM)
- Routing graphs (OSRM, Valhalla, GraphHopper extracts)
- Navigation datasets
- Traffic simulation datasets
- Urban planning extracts from OSM
- Environmental analysis datasets

## API Endpoints
- Overpass API: https://overpass-api.de/api/interpreter
- Overpass Turbo (for querying): https://overpass-turbo.eu
- OSM Wiki API (for metadata): https://wiki.openstreetmap.org/w/api.php
- Nominatim (for geocoding/reverse geocoding): https://nominatim.openstreetmap.org
- OSM Changeset API: https://www.openstreetmap.org/api/0.6/changesets
- OSM Node/Way/Relation API: https://www.openstreetmap.org/api/0.6/

## Rate Limits
- Overpass API: Implement respectful usage (timeout, max size, frequency limits)
- Nominatim: Heavy usage requires appreciation email, rate limits apply
- OSM main API: Rate limited for editing, reading is more permissive but still respectful
- Implement caching and exponential backoff
- Respect robots.txt and terms of use

## Data Extracted
For each OSM dataset found, extracts:
- Dataset name and description
- Geographic coverage (bounding box, named region)
- Data format (.osm.pbf, .shp, .geojson, .csv, etc.)
- Date of extract/publication
- Source/organization providing the extract
- License (typically ODbL - Open Database License)
- File size and download URL
- Features included (roads, buildings, waterways, POIs, etc.)
- Coordinate reference system (usually EPSG:4326/WGS84)
- Update frequency (for regularly updated extracts)
- Method of extraction (if known)
- Quality/completeness indicators
- Related documentation or methodology

## Limitations
- ODbL license requires share-alike attribution (may not suit all use cases)
- Data quality varies by region and contributor activity
- Extracts may not be updated frequently
- Large datasets (planet file) are very large (~100+ GB compressed)
- Thematic extracts may have inconsistent definitions across regions
- Some specialized derivatives may have additional restrictions
- Overpass API queries limited by complexity and size
- Requires processing .osm.pbf format for full use (tools like osmosis, imposm, etc.)
- May not include derived attributes or processed fields
- Temporal aspects limited (mostly current state, limited historical access)

## Use Cases
- Geographic Information Systems (GIS) base layers
- Urban planning and transportation modeling
- Environmental analysis and hydrology
- Disaster response and humanitarian mapping
- Location-based services and geocoding
- Navigation and routing applications
- Spatial analysis and statistics
- Base map for web and mobile applications
- Research in geography, urban studies, environmental science