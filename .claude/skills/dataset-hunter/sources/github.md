# GitHub Source

## Overview
Searches GitHub for repositories containing datasets using the GitHub Search API.

## Search Approach
- Uses GitHub's Search API to find repositories with dataset-related content
- Searches for keywords in repository names, descriptions, and READMEs
- Filters by language, stars, and other metadata to find quality dataset repositories
- Looks for common dataset file extensions and data directory structures

## API Endpoint
- Search API: https://api.github.com/search/repositories
- Query parameters: q={query}+in:name,description,readme&sort=stars&order=desc

## Rate Limits
- Unauthenticated: 10 requests per minute
- Authenticated: 30 requests per minute
- Implements exponential backoff for rate limiting
- Uses pagination to handle large result sets

## Data Extracted
For each repository, extracts:
- Repository name, URL, and description
- Owner/organization information
- Stars, forks, and watchers count
- Primary language and topics
- Last updated date
- License information
- README content (first 500 chars for description)
- Identifies potential dataset files (CSV, JSON, GeoTIFF, etc.)

## Limitations
- Only searches public repositories (unless authenticated)
- May miss datasets in private repositories
- Repository may contain code alongside data, requiring manual inspection
- Some large datasets may be stored in Git LFS or external links
- Search relevance depends on repository naming and description quality