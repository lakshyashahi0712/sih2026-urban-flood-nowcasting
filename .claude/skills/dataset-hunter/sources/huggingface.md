# Hugging Face Datasets Source

## Overview
Searches the Hugging Face Hub for datasets using their public API.

## Search Approach
- Uses the Hugging Face Hub API to search for datasets
- Searches by keywords derived from problem decomposition
- Filters by dataset type, language, and other metadata
- Extracts relevant metadata for each dataset found

## API Endpoint
- Main API: https://huggingface.co/api/datasets
- Search endpoint: https://huggingface.co/api/datasets?search={query}&limit={limit}

## Rate Limits
- Generally generous for public access
- Implements exponential backoff for rate limiting
- Caches responses to reduce API calls

## Data Extracted
For each dataset, extracts:
- Dataset name, ID, and URL
- Description and tags
- Last modified date
- Download size (if available)
- License information
- Number of likes/downloaded
- Papers with Code link (if available)
- Dataset preview information

## Limitations
- Only searches Hugging Face Hub
- May miss datasets not uploaded to HF
- Some metadata fields may be incomplete
- Private datasets are not accessible without authentication