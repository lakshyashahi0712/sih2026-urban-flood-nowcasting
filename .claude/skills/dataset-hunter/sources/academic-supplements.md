# Academic Supplements Source

## Overview
Searches for datasets that are supplementary material to academic papers, including those in institutional repositories and university datasets.

## Search Approach
- Searches academic paper databases for supplementary material links
- Looks for datasets mentioned in papers with links to repositories
- Searches institutional repositories (Harvard Dataverse, Figshare, Dryad, etc.)
- Searches university-specific data repositories
- Uses Google Scholar and other academic search approaches when APIs unavailable

## Known Sources
### Supplementary Material Repositories
- Figshare (https://figshare.com)
- Dryad (https://datadryad.org)
- Harvard Dataverse (https://dataverse.harvard.edu)
- OSF (Open Science Framework) (https://osf.io)
- Zenodo (also covered separately)
- Pan Stanford (https://pangaea.de)

### Institutional Repositories
- University-specific data repositories (when discoverable)
- Domain-specific repositories (PANGAEA for earth sciences, GenBank for genetics, etc.)
- Government research institution repositories (NASA, NOAA, USGS, etc. - also in scientific-repositories)

### Academic Search
- Google Scholar dataset search
- Semantic Scholar
- Microsoft Academic
- CORE (COnnecting Repositories)

## API Endpoints
Varies by source:
- Figshare: https://api.figshare.com/v2/articles/search
- Dryad: https://datadryad.org/api/v2/resources
- Harvard Dataverse: https://dataverse.harvard.edu/api/datasets/:persistentId
- OSF: https://api.osf.io/v2/search/
- PANGAEA: https://doi.pangaea.de/api

## Rate Limits
- Varies by source
- Implements exponential backoff and respectful rate limiting
- Some require registration for API access
- Caches responses where appropriate

## Data Extracted
For each supplementary dataset, extracts:
- Associated paper title, authors, DOI, and URL
- Dataset title and description
- Repository/platform where hosted
- Authors and contributors of dataset
- Publication date of paper and dataset
- License information
- File list with formats and sizes
- Variables and measurements
- Geographic and temporal coverage (when available in paper)
- Access method and download URLs
- Citation information for both paper and dataset

## Limitations
- Requires linking datasets to their academic papers
- Supplementary material may not always be clearly identified as a dataset
- Access may be restricted even when paper is open access
- Metadata quality varies significantly between repositories
- Some repositories focus on specific domains (genomics, crystallography, etc.)
- May miss datasets not linked to published papers