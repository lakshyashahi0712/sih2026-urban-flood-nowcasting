# Dynamic Discovery Source

## Overview
Implements dynamic discovery of domain-specific data sources that may not be in the predefined list. This allows the system to find new and emerging data repositories based on the research topic.

## Search Approach
- Analyzes the research topic to identify relevant domain keywords and concepts
- Uses search engines (Google, Bing, DuckDGoGo) to find data repositories mentioning those keywords
- Looks for patterns indicating data repositories: "data portal", "open data", "dataset repository", "data clearinghouse"
- Analyzes academic papers for cited data sources and repositories
- Checks GitHub for awesome lists and data repository collections
- Follows links from known repositories to discover related sources
- Uses Wikipedia and domain-specific portals to find data source recommendations

## Discovery Strategies
### 1. Keyword-Based Web Search
- Searches for "[topic] data portal", "[topic] open data", "[topic] dataset repository"
- Looks for "data.gov", "data.[domain].gov", "open.[domain].data" patterns
- Identifies domain-specific terms (e.g., for flooding: "hydrology", "hydrography", "rainfall", "streamflow")

### 2. Academic Paper Mining
- Searches Semantic Scholar, Google Scholar for recent papers on topic
- Extracts cited data sources and repositories from paper acknowledgments and data availability statements
- Looks for URLs to data repositories in paper supplementary materials

### 3. Awesome Lists and Curated Collections
- Searches GitHub for "awesome-[topic]-data", "[topic]-datasets", "data-[topic]"
- Checks GitHub topics for data-related repositories
- Looks for curated lists in domain-specific communities

### 4. Repository Network Analysis
- From known repositories, looks for "partners", "affiliates", "related projects" sections
- Follows links to discover new repositories in the same ecosystem
- Checks for mirror sites and regional instances of known repositories

### 5. Domain-Specific Portals and Wikis
- Checks Wikipedia portals for the topic (e.g., "Portal:Hydrology")
- Looks for domain-specific professional organization websites
- Checks for data archives maintained by scientific societies

## Implementation Approach
1. **Topic Analysis**: Extract key concepts, synonyms, and domain terms from research objective
2. **Seed Source Generation**: Create initial search queries based on topic analysis
3. **Web Search Phase**: Execute searches using multiple approaches
4. **Result Parsing**: Extract potential data repository URLs from search results
5. **Validation**: Verify that discovered URLs actually host data repositories
6. **Categorization**: Classify discovered sources by type (government, academic, community, etc.)
7. **Integration**: Add validated sources to the search queue for dataset extraction

## Data Extracted for Discovered Sources
For each dynamically discovered source, extracts:
- Source name and homepage URL
- Source type (government, academic, community, commercial, etc.)
- Description of what data they host
- Geographic and thematic focus
- Access methods (API, direct download, etc.)
- License information for their data
- Reliability indicators (citations, age, update frequency)
- Contact information and maintenance status

## Limitations
- Dynamic discovery depends on search engine availability and results quality
- May discover sources that are outdated or no longer maintained
- Requires careful validation to avoid false positives
- Some sources may have restrictive terms of service
- Language barriers may limit discovery of non-English sources
- Discovery process adds time to search; balanced against potential value

## Integration with Pipeline
Dynamic discovery occurs in Stage 2 (Source Discovery) of the 10-stage pipeline:
1. Problem decomposition identifies core concepts
2. Source discovery includes both predefined sources and dynamic discovery
3. Dynamic discovery generates additional source candidates based on topic analysis
4. All sources (predefined + dynamically discovered) proceed to candidate extraction

## Configuration Options
- Maximum number of dynamically discovered sources to add
- Minimum confidence score for accepting a discovered source
- Domains to prioritize or exclude from discovery
- Search engines to use for discovery
- Rate limiting for discovery searches