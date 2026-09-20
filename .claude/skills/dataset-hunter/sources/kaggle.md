# Kaggle Source

## Overview
Searches Kaggle for datasets using their public API and web scraping where needed.

## Search Approach
- Uses Kaggle's public API for dataset search when available
- Falls back to web scraping of search results when API is not accessible
- Searches by keywords derived from problem decomposition
- Filters by file size, usability score, and other metadata

## API Endpoint
- Main API: https://www.kaggle.com/api/v1/datasets.list
- Search via: https://www.kaggle.com/datasets?search={query}

## Rate Limits
- Kaggle API has rate limits (typically 100 calls per day for unauthenticated)
- Implements exponential backoff and caching
- Respects robots.txt where applicable

## Data Extracted
For each dataset, extracts:
- Dataset title, URL, and slug
- Description and subtitle
- File size and number of files
- Last updated date
- License information
- Usability score and vote count
- Topic tags
- Author/team information
- Download count

## Limitations
- Requires handling of Kaggle's authentication for some endpoints
- Some datasets may require Kaggle account to access
- API may be limited for unauthenticated users
- Web scraping approach may break with site changes