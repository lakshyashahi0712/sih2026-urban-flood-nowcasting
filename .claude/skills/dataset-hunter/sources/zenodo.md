# Zenodo Source

## Overview
Searches Zenodo for datasets using their REST API.

## Search Approach
- Uses Zenodo's REST API to search for datasets and publications with attached data
- Searches by keywords in title, description, and metadata
- Filters by resource type, access right, and other facets
- Focuses on uploads that contain downloadable datasets

## API Endpoint
- Search API: https://zenodo.org/api/records
- Query format: https://zenodo.org/api/records?q={query}&size={size}&sort={sort}

## Rate Limits
- Generally generous for public access
- Implements exponential backoff for rate limiting
- Uses pagination (default size 10, max 100 per request)

## Data Extracted
For each record, extracts:
- Title, description, and URL
- Authors and affiliations
- Publication date and version
- Resource type (dataset, publication, etc.)
- Access rights (open, embargoed, restricted)
- License information
- File list with descriptions and URLs
- Size of downloadable files
- DOI and citation information
- Communities and keywords
- Related identifiers (isSupplementTo, etc.)

## Limitations
- Zenodo hosts both datasets and publications; need to filter for actual datasets
- Some records may be embargoed or have restricted access
- File metadata may not always indicate if it's a dataset vs. supplementary material
- Search relevance depends on how well records are tagged and described