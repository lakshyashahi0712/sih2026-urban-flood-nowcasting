# Data.gov Source

## Overview
Searches the U.S. government's open data portal (data.gov) for datasets.

## Search Approach
- Uses data.gov's CKAN-based API to search for datasets
- Searches by keywords in dataset titles, notes, and tags
- Filters by organization, format, and other facets
- Focuses on U.S. federal government datasets

## API Endpoint
- Search API: https://catalog.data.gov/api/3/action/package_search
- Query format: https://catalog.data.gov/api/3/action/package_search?q={query}&rows={rows}

## Rate Limits
- Generally generous for public access
- Implements exponential backoff for rate limiting
- Uses pagination to handle large result sets

## Data Extracted
For each dataset, extracts:
- Title, notes, and URL
- Organization and maintainer information
- Date created and last modified
- License information
- Tags and groups
- Resources (files) with format, size, and download URLs
- Spatial and temporal coverage (if available)
- Frequency of update
- Language

## Limitations
- Only searches U.S. federal government data (data.gov)
- Does not include state, local, or tribal government data (covered in government-portals.md)
- Some datasets may be restricted or require special access
- Metadata quality varies across different agencies