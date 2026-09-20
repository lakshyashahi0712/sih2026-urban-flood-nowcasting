# Common Crawl Source

## Overview
Searches Common Crawl for web archive data that can be used as datasets, particularly for web-scale analysis, language models, and longitudinal studies.

## Search Approach
- Uses Common Crawl's public index (CC-MAIN-* and CC-ARCHIVE-*) to identify relevant web archives
- Searches for specific patterns indicating dataset-like content (CSV, JSON, XML files, API endpoints, data directories)
- Filters by crawl date, language, and content type
- Extracts metadata about archived web resources that resemble datasets
- Provides access to the raw web archive data through Common Crawl's AWS public datasets

## Known Collections
- CC-MAIN-* : Main crawls (monthly/bi-monthly)
- CC-ARCHIVE-* : Archive crawls (specialized/targeted)
- Specific indexes for language models, news, etc.

## API Endpoints
- Common Crawl Index API: https://index.commoncrawl.org/
- CDX API for querying crawled resources
- AWS Public Dataset access via s3://commoncrawl/
- Example: https://index.commoncrawl.org/CC-MAIN-2023-06-index

## Rate Limits
- Index API is generally generous but implements respectful rate limiting
- AWS access follows standard S3 public dataset policies
- Implements exponential backoff and caching
- Respects robots.txt from original crawl when accessing live versions (though we work with archived data)

## Data Extracted
For each Common Crawl record that appears dataset-like, extracts:
- URL of the archived resource
- Timestamp of crawl (when it was archived)
- MIME type/content type
- Language detection (when available)
- File size in archive
- Compression format
- Access path in Common Crawl's WARC/ARCD files
- S3 location for direct access (when using AWS mirror)
- Context from surrounding HTML/text (when available)
- Indicators that it might be a dataset (file extension, URL patterns, surrounding text)

## Dataset Identification Heuristics
Looks for resources that appear to be datasets based on:
- File extensions: .csv, .tsv, .json, .xml, .parquet, .feather, .h5, .nc, .gz (when containing data)
- URL patterns: containing "data", "dataset", "download", "api", "feed"
- Surrounding context: mentions of "dataset", "data", "download", "CSV", etc.
- Structured data indicators: JSON-LD, microdata, schema.org markers
- Known data repositories: links to Kaggle, Hugging Face, Zenodo, etc. found in crawl

## Limitations
- Common Crawl contains raw web content; not all resources are datasets
- Requires post-processing to extract actual dataset files from WARC/ARCD archives
- Data may be outdated (depends on crawl date)
- Large scale - requires careful filtering to avoid noise
- Some content may be behind paywalls or restricted (though crawled)
- Duplicate content across crawls requires deduplication
- Extracting files from WARC format requires special tools
- May contain personal data or sensitive information requiring ethical consideration

## Access Methods
1. **Direct Index Search**: Use Common Crawl's index API to find promising URLs
2. **AWS Public Dataset**: Access via s3://commoncrawl/ (requires AWS account but data is free)
3. **Third-party Services**: Some services provide easier access to CC data
4. **Custom Processing**: Download and process WARC/ARCD files to extract candidate resources

## Use Cases
- Training language models on web text
- Longitudinal studies of web content
- Web-scale data mining and analysis
- Finding publicly shared datasets embedded in web pages
- Tracking changes in data publication over time
- Academic research on web data ecosystems