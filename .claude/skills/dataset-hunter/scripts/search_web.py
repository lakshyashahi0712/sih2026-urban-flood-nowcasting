#!/usr/bin/env python3
"""
Web search module for dataset-hunter skill.
Searches the web for datasets using search engines and web scraping.
"""

import requests
import json
import time
import re
import hashlib
import pickle
from typing import List, Dict, Any, Optional
from urllib.parse import quote_plus, urljoin, urlparse
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
import random

# Constants for execution limits and timeouts
CONNECT_TIMEOUT = 10  # seconds
READ_TIMEOUT = 30     # seconds
MAX_RETRIES = 3
BASE_BACKOFF = 1      # seconds
MAX_BACKOFF = 10      # seconds
MAX_PAGES_PER_SOURCE = 5
MAX_RESULTS_PER_PAGE = 20
CACHE_ENABLED = True
CACHE_DIR = None  # Will be initialized later
CACHE_EXPIRY_HOURS = 24

# Initialize cache directory
def _init_cache_dir():
    global CACHE_DIR
    if CACHE_DIR is None:
        CACHE_DIR = Path(__file__).parent.parent / ".cache"
        CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Import Path after defining _init_cache_dir to avoid circular issues
from pathlib import Path


def retry_with_backoff(max_retries: int = MAX_RETRIES, base_backoff: float = BASE_BACKOFF, max_backoff: float = MAX_BACKOFF):
    """Decorator for retrying functions with exponential backoff."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries:
                        # Calculate backoff with jitter
                        backoff = min(base_backoff * (2 ** attempt) + random.uniform(0, 1), max_backoff)
                        time.sleep(backoff)
                    else:
                        raise last_exception
            return None  # Should not reach here
        return wrapper
    return decorator


def cache_result(func):
    """Decorator to cache function results."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not CACHE_ENABLED:
            return func(*args, **kwargs)

        # Initialize cache directory if needed
        _init_cache_dir()

        # Create cache key from function name and arguments
        cache_key = hashlib.md5(
            f"{func.__name__}_{str(args)}_{str(kwargs)}".encode()
        ).hexdigest()

        cache_file = CACHE_DIR / f"{cache_key}.pkl"

        # Check if cached result exists and is not expired
        if cache_file.exists():
            try:
                with open(cache_file, 'rb') as f:
                    cached_data = pickle.load(f)
                if time.time() - cached_data['timestamp'] < CACHE_EXPIRY_HOURS * 3600:
                    return cached_data['result']
            except Exception:
                pass  # If cache read fails, proceed to compute

        # Compute result and cache it
        result = func(*args, **kwargs)

        # Cache the result
        cache_data = {
            'result': result,
            'timestamp': time.time()
        }
        try:
            with open(cache_file, 'wb') as f:
                pickle.dump(cache_data, f)
        except Exception:
            pass  # If cache write fails, continue without caching

        return result
    return wrapper


def log_progress(message: str):
    """Log progress with timestamp."""
    timestamp = time.strftime('%H:%M:%S')
    print(f"[{timestamp}] {message}")


def safe_request(method: str, url: str, **kwargs) -> Optional[requests.Response]:
    """
    Make a safe HTTP request with timeouts and retry logic.

    Args:
        method: HTTP method ('get', 'post', etc.)
        url: URL to request
        **kwargs: Additional arguments to pass to requests

    Returns:
        Response object or None if failed
    """
    # Set default timeouts if not provided
    if 'timeout' not in kwargs:
        kwargs['timeout'] = (CONNECT_TIMEOUT, READ_TIMEOUT)

    # Set default headers if not provided
    if 'headers' not in kwargs:
        kwargs['headers'] = {
            'User-Agent': 'dataset-hunter-skill/1.0'
        }

    # Attempt request with retries
    for attempt in range(MAX_RETRIES + 1):
        try:
            response = requests.request(method, url, **kwargs)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            if attempt < MAX_RETRIES:
                # Calculate backoff with jitter
                backoff = min(BASE_BACKOFF * (2 ** attempt) + random.uniform(0, 1), MAX_BACKOFF)
                time.sleep(backoff)
            else:
                # Log final failure
                print(f"Failed to request {url} after {MAX_RETRIES} attempts: {e}")
                return None
    return None


def search_web(query: str, max_results: int = 100) -> List[Dict[str, Any]]:
    """
    Search the web for datasets using search engines and web scraping.

    Args:
        query: Search query string
        max_results: Maximum number of results to return

    Returns:
        List of dataset candidate dictionaries
    """
    log_progress(f"Searching web for: {query}")

    candidates = []

    # Use multiple search approaches
    try:
        # Try DuckDuckGo instant answer API (no key required)
        ddg_results = search_duckduckgo(query, max_results // 2)
        candidates.extend(ddg_results)

        # Try Google Custom Search (if available) or alternative approach
        # For now, we'll use a simplified approach with known data portals
        portal_results = search_known_portals(query, max_results // 2)
        candidates.extend(portal_results)

    except Exception as e:
        print(f"Error searching web: {e}")

    # Limit results to max_results
    return candidates[:max_results]


@retry_with_backoff()
@cache_result
def search_duckduckgo(query: str, max_results: int) -> List[Dict[str, Any]]:
    """
    Search using DuckDuckGo instant answer API with pagination support.

    Args:
        query: Search query string
        max_results: Maximum number of results

    Returns:
        List of dataset candidate dictionaries
    """
    log_progress(f"  Searching DuckDuckGo for: {query}")
    candidates = []

    try:
        # DuckDuckGo instant answer API
        url = "https://api.duckduckgo.com/"

        # Calculate how many pages we need (DuckDuckGo doesn't have traditional pagination,
        # but we can use different query variations or related searches)
        pages_to_search = min(MAX_PAGES_PER_SOURCE, (max_results // MAX_RESULTS_PER_PAGE) + 1)

        for page in range(pages_to_search):
            # Modify query for different pages to get varied results
            if page == 0:
                page_query = f"{query} dataset data csv json"
            else:
                page_query = f"{query} dataset data csv json page {page + 1}"

            params = {
                'q': page_query,
                'format': 'json',
                'no_html': '1',
                'skip_disambig': '1'
            }

            response = safe_request('GET', url, params=params)

            if response is None:
                log_progress(f"    Failed to get response from DuckDuckGo for page {page + 1}")
                continue

            if response.status_code == 200:
                data = response.json()

                # Extract results from related topics and abstract
                results = []

                # Check abstract
                if data.get('Abstract'):
                    results.append({
                        'title': data.get('Heading', ''),
                        'description': data.get('Abstract', ''),
                        'url': data.get('AbstractURL', '')
                    })

                # Check related topics
                for topic in data.get('RelatedTopics', []):
                    if isinstance(topic, dict) and topic.get('Text'):
                        results.append({
                            'title': topic.get('Text', '')[:100],
                            'description': topic.get('Text', ''),
                            'url': topic.get('FirstURL', '')
                        })

                # Process results into dataset candidates
                for result in results:
                    candidate = extract_web_candidate(result, 'DuckDuckGo')
                    if candidate:
                        candidates.append(candidate)

                # Break if we have enough results
                if len(candidates) >= max_results:
                    break
            else:
                log_progress(f"    DuckDuckGo returned status {response.status_code} for page {page + 1}")

    except Exception as e:
        print(f"Error searching DuckDuckGo: {e}")

    log_progress(f"  Found {len(candidates)} candidates from DuckDuckGo")
    return candidates


@retry_with_backoff()
@cache_result
def search_known_portals(query: str, max_results: int) -> List[Dict[str, Any]]:
    """
    Search known data portals for datasets.

    Args:
        query: Search query string
        max_results: Maximum number of results

    Returns:
        List of dataset candidate dictionaries
    """
    log_progress(f"  Searching known portals for: {query}")
    candidates = []

    # List of known data portals to search
    portals = [
        {
            'name': 'Data.gov',
            'base_url': 'https://catalog.data.gov',
            'search_path': '/dataset/',
            'type': 'government'
        },
        {
            'name': 'European Data Portal',
            'base_url': 'https://www.europeandataportal.eu',
            'search_path': '/dataset/',
            'type': 'government'
        },
        {
            'name': 'Knoema',
            'base_url': 'https://knoema.com',
            'search_path': '/',
            'type': 'community'
        }
    ]

    # Search each portal with controlled parallelism
    with ThreadPoolExecutor(max_workers=min(3, len(portals))) as executor:
        # Submit all portal search tasks
        future_to_portal = {
            executor.submit(search_portal, portal, query, max_results // len(portals)): portal
            for portal in portals
        }

        # Collect results as they complete
        for future in as_completed(future_to_portal):
            portal = future_to_portal[future]
            try:
                portal_candidates = future.result(timeout=30)  # 30 second timeout per portal
                candidates.extend(portal_candidates)
                log_progress(f"    Found {len(portal_candidates)} candidates from {portal['name']}")
            except Exception as e:
                print(f"Error searching {portal['name']}: {e}")

    return candidates


def search_portal(portal: Dict[str, str], query: str, max_results: int) -> List[Dict[str, Any]]:
    """
    Search a specific data portal.

    Args:
        portal: Portal configuration dictionary
        query: Search query string
        max_results: Maximum number of results

    Returns:
        List of dataset candidate dictionaries
    """
    candidates = []

    try:
        log_progress(f"    Searching {portal['name']} for: {query}")

        # Try to search the portal's API if available
        if portal['name'] == 'Data.gov':
            # Data.gov has a CKAN API
            api_url = urljoin(portal['base_url'], '/api/3/action/package_search')
            params = {
                'q': query,
                'rows': min(max_results, 100)  # CKAN limit
            }

            response = safe_request('GET', api_url, params=params)
            if response and response.status_code == 200:
                data = response.json()
                if data.get('success') and 'result' in data:
                    for item in data['result'].get('results', []):
                        candidate = extract_ckan_candidate(item, portal['name'])
                        if candidate:
                            candidates.append(candidate)

        elif portal['name'] == 'European Data Portal':
            # European Data Portal also uses CKAN
            api_url = urljoin(portal['base_url'], '/api/3/action/package_search')
            params = {
                'q': query,
                'rows': min(max_results, 100)
            }

            response = safe_request('GET', api_url, params=params)
            if response and response.status_code == 200:
                data = response.json()
                if data.get('success') and 'result' in data:
                    for item in data['result'].get('results', []):
                        candidate = extract_ckan_candidate(item, portal['name'])
                        if candidate:
                            candidates.append(candidate)

        elif portal['name'] == 'Knoema':
            # Knoema search - simplified approach
            search_url = urljoin(portal['base_url'], '/search')
            params = {
                'text': query,
                'type': 'dataset'
            }

            response = safe_request('GET', search_url, params=params)
            if response and response.status_code == 200:
                # Parse HTML response for dataset listings
                soup = BeautifulSoup(response.content, 'html.parser')
                # Look for dataset cards or listings
                dataset_elements = soup.find_all(['div', 'article'], class_=re.compile(r'dataset|result|item', re.I))

                for element in dataset_elements[:max_results]:
                    candidate = extract_html_candidate(element, portal['name'])
                    if candidate:
                        candidates.append(candidate)

        # If API search failed or not implemented, fall back to web search approach
        if not candidates:
            log_progress(f"    API search failed for {portal['name']}, falling back to web search")
            # Use DuckDuckGo to search within the specific domain
            domain_query = f"site:{urlparse(portal['base_url']).netloc} {query} dataset"
            ddg_results = search_duckduckgo(domain_query, max_results)
            candidates.extend(ddg_results)

    except Exception as e:
        print(f"Error searching portal {portal['name']}: {e}")

    return candidates


def extract_ckan_candidate(item: Dict[str, Any], source: str) -> Optional[Dict[str, Any]]:
    """
    Extract dataset candidate from CKAN API response.

    Args:
        item: CKAN dataset item
        source: Source name

    Returns:
        Dataset candidate dictionary or None if not suitable
    """
    try:
        title = item.get('title', '')
        notes = item.get('notes', '')  # Description in CKAN
        url = item.get('url', '')

        # If no explicit URL, try to construct from name
        if not url and item.get('name'):
            url = urljoin(item.get('url', ''), f"/dataset/{item['name']}")

        # Skip if no meaningful data
        if not title or not url:
            return None

        # Assess if this looks like a dataset
        is_likely_dataset = assess_if_web_dataset(title, notes, url)

        # Extract additional information
        organization = item.get('organization', {}).get('title', '') if item.get('organization') else ''

        # Build candidate
        candidate = {
            'name': title.replace('-', ' ').replace('_', ' ').title()[:100],
            'title': title,
            'source': source,
            'organization': organization,
            'description': notes[:1000] if notes else '',
            'url': url,
            'api_url': '',  # Would need to be discovered from resources
            'relevance_score': calculate_web_relevance(title, notes),
            'source_reliability': assess_source_reliability(urlparse(url).netloc),
            'access_method': 'web_download_or_api',
            'file_formats': infer_ckan_formats(item.get('resources', [])),
            'variables': extract_web_variables(title + " " + notes),
            'geographic_coverage': extract_web_geographic(title + " " + notes),
            'temporal_coverage': extract_web_temporal(title + " " + notes),
            'access_restrictions': 'unknown',  # Would need to check license
            'cost': 'free',  # Assume free unless known otherwise
            'documentation_url': url,
            'citation': '',
        }

        return candidate

    except Exception as e:
        print(f"Error extracting CKAN candidate: {e}")
        return None


def extract_html_candidate(element, source: str) -> Optional[Dict[str, Any]]:
    """
    Extract dataset candidate from HTML element.

    Args:
        element: BeautifulSoup element
        source: Source name

    Returns:
        Dataset candidate dictionary or None if not suitable
    """
    try:
        # Try to find title and description
        title_elem = element.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'a'],
                                 class_=re.compile(r'title|name|heading', re.I))
        title = title_elem.get_text(strip=True) if title_elem else ''

        desc_elem = element.find(['p', 'div'],
                                class_=re.compile(r'desc|summary|description', re.I))
        description = desc_elem.get_text(strip=True) if desc_elem else ''

        # Try to find URL/link
        link_elem = element.find('a', href=True)
        url = link_elem['href'] if link_elem else ''

        # Make URL absolute if it's relative
        if url and not url.startswith(('http://', 'https://')):
            # This is a simplified approach - in practice we'd need the base URL
            pass

        # Skip if no meaningful data
        if not title or not url:
            return None

        # Assess if this looks like a dataset
        is_likely_dataset = assess_if_web_dataset(title, description, url)

        # Build candidate
        candidate = {
            'name': title.replace('-', ' ').replace('_', ' ').title()[:100],
            'title': title,
            'source': source,
            'organization': extract_organization_from_url(urlparse(url).netloc),
            'description': description[:1000] if description else '',
            'url': url,
            'api_url': '',
            'relevance_score': calculate_web_relevance(title, description),
            'source_reliability': assess_source_reliability(urlparse(url).netloc),
            'access_method': 'web_download_or_api',
            'file_formats': infer_web_formats(title + " " + description),
            'variables': extract_web_variables(title + " " + description),
            'geographic_coverage': extract_web_geographic(title + " " + description),
            'temporal_coverage': extract_web_temporal(title + " " + description),
            'access_restrictions': 'unknown',
            'cost': 'free',
            'documentation_url': url,
            'citation': '',
        }

        return candidate

    except Exception as e:
        print(f"Error extracting HTML candidate: {e}")
        return None


def extract_web_candidate(result: Dict[str, Any], source: str) -> Optional[Dict[str, Any]]:
    """
    Extract dataset candidate information from web search result.

    Args:
        result: Web search result dictionary
        source: Source of the result (e.g., 'DuckDuckGo', 'Google')

    Returns:
        Dataset candidate dictionary or None if not suitable
    """
    try:
        title = result.get('title', '')
        description = result.get('description', '')
        url = result.get('url', '')

        # Skip if no meaningful data
        if not title or not url:
            return None

        # Assess if this looks like a dataset
        is_likely_dataset = assess_if_web_dataset(title, description, url)

        # Extract additional information
        domain = urlparse(url).netloc if url else ''

        # Build candidate
        candidate = {
            'name': title.replace('-', ' ').replace('_', ' ').title()[:100],
            'title': title,
            'source': source,
            'organization': extract_organization_from_url(domain),
            'description': description[:1000] if description else '',
            'url': url,
            'api_url': '',  # Would need to be discovered
            'relevance_score': calculate_web_relevance(title, description),
            'source_reliability': assess_source_reliability(domain),
            'access_method': 'web_download_or_api',
            'file_formats': infer_web_formats(title, description),
            'variables': extract_web_variables(title + " " + description),
            'geographic_coverage': extract_web_geographic(title + " " + description),
            'temporal_coverage': extract_web_temporal(title + " " + description),
            'access_restrictions': 'unknown',  # Would need to check
            'cost': 'free',  # Assume free unless known otherwise
            'documentation_url': url,
            'citation': '',
        }

        return candidate

    except Exception as e:
        print(f"Error extracting web candidate: {e}")
        return None


def assess_if_web_dataset(title: str, description: str, url: str) -> bool:
    """
    Assess if a web result is likely a dataset.

    Args:
        title: Title of the result
        description: Description of the result
        url: URL of the result

    Returns:
        Boolean indicating if likely a dataset
    """
    text_to_search = f"{title} {description}".lower()

    # Strong dataset indicators
    dataset_indicators = [
        'dataset', 'data', 'csv', 'json', 'xml', 'parquet', 'excel',
        'database', 'spreadsheet', 'timeseries', 'geospatial',
        'download', 'api', 'repository'
    ]

    # Check for dataset indicators
    for indicator in dataset_indicators:
        if indicator in text_to_search:
            return True

    # Check URL for data-like patterns
    url_lower = url.lower()
    data_url_patterns = [
        '.csv', '.json', '.xml', '.parquet', '.xls', '.xlsx',
        '/data/', '/dataset/', '/download/', '/api/'
    ]

    for pattern in data_url_patterns:
        if pattern in url_lower:
            return True

    return False


def extract_organization_from_url(domain: str) -> str:
    """
    Extract organization from URL domain.

    Args:
        domain: Domain name from URL

    Returns:
        Organization string
    """
    # Remove www. and common prefixes
    domain = domain.lower()
    if domain.startswith('www.'):
        domain = domain[4:]

    # Extract organization name (simplified)
    # In practice, this would use a more sophisticated approach
    parts = domain.split('.')
    if len(parts) >= 2:
        org = parts[-2]  # Second-to-last part
        # Capitalize and format
        return org.replace('-', ' ').title()

    return domain


def calculate_web_relevance(title: str, description: str) -> int:
    """
    Calculate relevance score for web result.

    Args:
        title: Title of the result
        description: Description of the result

    Returns:
        Relevance score (0-10)
    """
    score = 0
    text_to_search = f"{title} {description}".lower()

    # Check for data-related keywords
    data_keywords = [
        'dataset', 'data', 'csv', 'json', 'xml', 'parquet', 'excel',
        'database', 'spreadsheet', 'timeseries', 'geospatial',
        'download', 'api', 'repository', 'observation', 'measurement'
    ]

    for keyword in data_keywords:
        if keyword in text_to_search:
            score += 1

    # Boost for multiple indicators
    if sum(1 for k in data_keywords if k in text_to_search) >= 3:
        score += 2

    return min(score, 10)


def assess_source_reliability(domain: str) -> str:
    """
    Assess reliability of source based on domain.

    Args:
        domain: Domain name

    Returns:
        Reliability tier ('tier_1', 'tier_2', 'tier_3', 'tier_4')
    """
    domain = domain.lower()

    # Tier 1: Official government and scientific institutions
    tier_1_domains = [
        '.gov', '.mil',  # US government
        '.gc.ca',  # Canadian government
        '.gov.uk', '.gov.au', '.gov.in',  # Other national governments
        'nasa.gov', 'noaa.gov', 'usgs.gov', 'nih.gov',  # US science agencies
        'esa.int', 'eo.ca',  # Space agencies
        'who.int', 'un.org',  # International organizations
    ]

    # Tier 2: Major research repositories and educational institutions
    tier_2_domains = [
        'edu', 'ac.uk', 'ac.jp', 'ac.kr',  # Educational
        'github.com', 'gitlab.com',  # Major code hosts (though these are tier_3 in our system)
        'zenodo.org', 'figshare.com', 'datadryad.org',  # Major repositories
        'kaggle.com',  # Though we have specific handling for this
        'huggingface.co',  # Though we have specific handling
    ]

    # Check tiers
    for tld in tier_1_domains:
        if domain.endswith(tld) or tld in domain:
            return 'tier_1'

    for tld in tier_2_domains:
        if domain.endswith(tld) or tld in domain:
            return 'tier_2'

    # Default to tier 3 for unknown domains
    return 'tier_3'


def infer_ckan_formats(resources: List[Dict[str, Any]]) -> List[str]:
    """
    Infer likely file formats from CKAN resources.

    Args:
        resources: List of CKAN resource dictionaries

    Returns:
        List of inferred file formats
    """
    formats = set()

    for resource in resources:
        format_str = resource.get('format', '').lower().strip()
        url = resource.get('url', '').lower()

        # Check explicit format
        if format_str:
            if format_str in ['csv', 'json', 'xml', 'parquet', 'xls', 'xlsx']:
                formats.add(format_str)
            elif 'excel' in format_str:
                formats.add('excel')

        # Check URL extension
        if url:
            if url.endswith('.csv'):
                formats.add('csv')
            elif url.endswith('.json'):
                formats.add('json')
            elif url.endswith('.xml'):
                formats.add('xml')
            elif url.endswith('.parquet'):
                formats.add('parquet')
            elif url.endswith(('.xls', '.xlsx')):
                formats.add('excel')

    # If no specific formats but seems data-related
    if not formats and resources:
        formats.add('unknown')

    return list(formats)


def infer_web_formats(title: str, description: str) -> List[str]:
    """
    Infer likely file formats from web result.

    Args:
        title: Title of the result
        description: Description of the result

    Returns:
        List of inferred file formats
    """
    formats = []
    text_to_search = f"{title} {description}".lower()

    format_indicators = {
        'csv': ['csv', 'comma-separated'],
        'json': ['json', 'jsonl'],
        'parquet': ['parquet'],
        'excel': ['xls', 'xlsx', 'excel'],
        'xml': ['xml'],
        'sql': ['sql', 'database'],
        'netcdf': ['netcdf', 'nc'],
        'hdf5': ['hdf5', 'h5'],
        'geojson': ['geojson', 'json'],
        'shapefile': ['shapefile', 'shp', 'gis']
    }

    for fmt, indicators in format_indicators.items():
        if any(indicator in text_to_search for indicator in indicators):
            formats.append(fmt)

    # If no specific formats but seems data-related
    if not formats and any(indicator in text_to_search for indicator in ['data', 'dataset']):
        formats = ['unknown']

    return list(set(formats))


def extract_web_variables(text: str) -> List[str]:
    """
    Extract potential variables from web result text.

    Args:
        text: Text to search for variables

    Returns:
        List of potential variables
    """
    # Common variables across domains
    common_variables = [
        'temperature', 'precipitation', 'rainfall', 'humidity', 'pressure',
        'wind_speed', 'wind_direction', 'solar_radiation', 'evapotranspiration',
        'soil_moisture', 'water_level', 'discharge', 'ph', 'dissolved_oxygen',
        'conductivity', 'turbidity', 'chlorophyll', 'nitrate', 'phosphate',
        'pm2_5', 'pm10', 'co2', 'methane', 'latitude', 'longitude', 'elevation',
        'depth', 'age', 'gender', 'income', 'education', 'employment',
        'price', 'volume', 'weight', 'height', 'width', 'area', 'volume'
    ]

    found_variables = []
    text_lower = text.lower()

    for var in common_variables:
        if var in text_lower:
            found_variables.append(var.replace('_', ' '))

    return found_variables[:10]


def extract_web_geographic(text: str) -> Dict[str, Any]:
    """
    Extract geographic coverage from web result text.

    Args:
        text: Text to search for geographic hints

    Returns:
        Dictionary with geographic coverage information
    """
    geographic_terms = [
        'global', 'world', 'international', 'continental', 'national',
        'country', 'state', 'province', 'city', 'urban', 'rural',
        'watershed', 'basin', 'river', 'lake', 'ocean', 'coastal',
        'floodplain', 'wetland', 'forest', 'mountain', 'valley',
        'africa', 'asia', 'europe', 'north america', 'south america',
        'antarctica', 'arctic'
    ]

    found_terms = []
    text_lower = text.lower()

    for term in geographic_terms:
        if term in text_lower:
            found_terms.append(term)

    return {
        'mentions': found_terms,
        'type': 'textual_description',
        'detail': 'Geographic coverage extracted from text mentions'
    }


def extract_web_temporal(text: str) -> Dict[str, Any]:
    """
    Extract temporal coverage from web result text.

    Args:
        text: Text to search for temporal hints

    Returns:
        Dictionary with temporal coverage information
    """
    temporal_terms = [
        'realtime', 'real-time', 'hourly', 'daily', 'weekly', 'monthly',
        'annual', 'yearly', 'seasonal', 'historical', 'past', 'present',
        'future', 'forecast', 'trend', 'climatology', 'normals',
        'micosecond', 'millisecond', 'second', 'minute', 'hour', 'day',
        'week', 'month', 'year', 'decade', 'century'
    ]

    found_terms = []
    text_lower = text.lower()

    for term in temporal_terms:
        if term in text_lower:
            found_terms.append(term)

    return {
        'mentions': found_terms,
        'type': 'textual_description',
        'detail': 'Temporal coverage extracted from text mentions'
    }


if __name__ == "__main__":
    # Test the function
    import sys
    if len(sys.argv) > 1:
        test_query = sys.argv[1]
        results = search_web(test_query, max_results=5)
        print(f"Found {len(results)} candidates:")
        for i, candidate in enumerate(results[:3]):
            print(f"{i+1}. {candidate['title']} - {candidate['description'][:100]}...")
    else:
        print("Usage: python search_web.py <query>")