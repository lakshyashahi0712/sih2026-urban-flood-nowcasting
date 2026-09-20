#!/usr/bin/env python3
"""
GitHub dataset search module for dataset-hunter skill.
Searches GitHub for repositories containing datasets.
"""

import requests
import json
import time
from typing import List, Dict, Any, Optional
from urllib.parse import quote_plus
import base64


def search_github(query: str, max_results: int = 100) -> List[Dict[str, Any]]:
    """
    Search GitHub for repositories containing datasets.

    Args:
        query: Search query string
        max_results: Maximum number of results to return

    Returns:
        List of dataset candidate dictionaries
    """
    print(f"Searching GitHub for: {query}")

    candidates = []

    try:
        # GitHub Search API endpoint
        url = "https://api.github.com/search/repositories"

        # Prepare search query - look for dataset-related terms
        search_query = f"{query} (dataset OR data OR csv OR json OR parquet) in:name,description,readme"

        params = {
            'q': search_query,
            'sort': 'stars',
            'order': 'desc',
            'per_page': min(max_results, 100)  # GitHub API max is 100 per page
        }

        headers = {
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'dataset-hunter-skill/1.0'
        }

        response = requests.get(url, params=params, headers=headers, timeout=30)

        if response.status_code == 200:
            data = response.json()
            items = data.get('items', [])

            for item in items:
                candidate = extract_github_candidate(item)
                if candidate:
                    candidates.append(candidate)

        elif response.status_code == 403:
            # Rate limited - try again after delay or use unauthenticated search
            print("GitHub API rate limit exceeded, trying unauthenticated search...")
            # Could implement retry with delay or use alternative approach
        else:
            print(f"GitHub search failed with status {response.status_code}")

    except Exception as e:
        print(f"Error searching GitHub: {e}")

    return candidates


def extract_github_candidate(item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Extract dataset candidate information from GitHub repository item.

    Args:
        item: GitHub API repository item

    Returns:
        Dataset candidate dictionary or None if not suitable
    """
    try:
        # Basic repository info
        name = item.get('name', '')
        full_name = item.get('full_name', '')
        description = item.get('description', '') or ''
        html_url = item.get('html_url', '')
        owner = item.get('owner', {}).get('login', '')

        # Skip if no description or name
        if not name or not description:
            return None

        # Check if this looks like a dataset repository
        dataset_indicators = [
            'dataset', 'data', 'csv', 'json', 'parquet', 'hdf5', 'netcdf',
            'geojson', 'shapefile', 'gis', 'remote sensing', 'satellite',
            'climate', 'weather', 'oceanography', 'hydrology', 'meteorology'
        ]

        text_to_search = (name + " " + description + " " +
                         str(item.get('topics', []))).lower()

        # Calculate relevance score based on dataset indicators
        relevance_score = 0
        for indicator in dataset_indicators:
            if indicator in text_to_search:
                relevance_score += 1

        # If no dataset indicators found, might still be useful but lower priority
        if relevance_score == 0:
            # Check for common data file extensions in description
            if any(ext in description.lower() for ext in ['.csv', '.json', '.xml', '.parquet']):
                relevance_score = 1

        # Extract additional metadata
        stars = item.get('stargazers_count', 0)
        forks = item.get('forks_count', 0)
        language = item.get('language', '')
        created_at = item.get('created_at', '')
        updated_at = item.get('updated_at', '')
        size = item.get('size', 0)  # in KB
        topics = item.get('topics', [])

        # Try to get README for more information
        readme_content = get_github_readme(full_name)

        # Build candidate
        candidate = {
            'name': name,
            'title': name.replace('-', ' ').replace('_', ' ').title(),
            'source': 'GitHub',
            'organization': owner,
            'description': description[:500] if description else '',  # Limit length
            'url': html_url,
            'api_url': item.get('url', ''),
            'clone_url': item.get('clone_url', ''),
            'stars': stars,
            'forks': forks,
            'language': language,
            'created_at': created_at,
            'updated_at': updated_at,
            'size_kb': size,
            'topics': topics,
            'readme_preview': readme_content[:200] if readme_content else '',
            'repo_full_name': full_name,
            'license': item.get('license', {}).get('name', '') if item.get('license') else '',
            'relevance_score': relevance_score,
            'source_reliability': 'tier_3',  # GitHub is tier 3 (community)
            'access_method': 'git_clone_or_download',
            'file_formats': infer_file_formats(description, readme_content, topics),
            'variables': extract_variables_from_text(description + " " + (readme_content or '')),
            'geographic_coverage': extract_geographic_coverage(description + " " + (readme_content or '')),
            'temporal_coverage': extract_temporal_coverage(description + " " + (readme_content or '')),
            'access_restrictions': 'none' if not item.get('private') else 'private',
            'cost': 'free',
            'documentation_url': html_url,  # README serves as documentation
        }

        return candidate

    except Exception as e:
        print(f"Error extracting GitHub candidate: {e}")
        return None


def get_github_readme(full_name: str) -> str:
    """
    Fetch README content from GitHub repository.

    Args:
        full_name: Repository full name (owner/repo)

    Returns:
        README content or empty string if not available
    """
    try:
        url = f"https://api.github.com/repos/{full_name}/readme"
        headers = {
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'dataset-hunter-skill/1.0'
        }

        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            data = response.json()
            # README content is base64 encoded
            content = base64.b64decode(data.get('content', '')).decode('utf-8', errors='ignore')
            return content[:1000]  # Limit length
    except Exception:
        pass

    return ""


def infer_file_formats(description: str, readme: str, topics: List[str]) -> List[str]:
    """
    Infer likely file formats from repository description and metadata.

    Args:
        description: Repository description
        readme: README content
        topics: Repository topics

    Returns:
        List of inferred file formats
    """
    formats = []
    text_to_search = (description + " " + readme + " " + " ".join(topics)).lower()

    format_indicators = {
        'csv': ['csv', 'comma-separated'],
        'json': ['json', 'jsonl'],
        'parquet': ['parquet'],
        'excel': ['xls', 'xlsx', 'excel'],
        'shapefile': ['shapefile', 'shp', 'gis'],
        'geojson': ['geojson'],
        'netcdf': ['netcdf', 'nc'],
        'hdf5': ['hdf5', 'h5'],
        'xml': ['xml'],
        'txt': ['txt', 'text'],
        'sqlite': ['sqlite', 'db'],
    }

    for fmt, indicators in format_indicators.items():
        if any(indicator in text_to_search for indicator in indicators):
            formats.append(fmt)

    # If no specific formats found but seems data-related, add generic
    if not formats and any(indicator in text_to_search for indicator in ['data', 'dataset']):
        formats = ['unknown']

    return list(set(formats))  # Remove duplicates


def extract_variables_from_text(text: str) -> List[str]:
    """
    Extract potential variables/measurements from text.

    Args:
        text: Text to search for variables

    Returns:
        List of potential variables
    """
    # Common variable names in geoscience/environmental datasets
    common_variables = [
        'temperature', 'precipitation', 'rainfall', 'humidity', 'pressure',
        'wind_speed', 'wind_direction', 'solar_radiation', 'evapotranspiration',
        'soil_moisture', 'water_level', 'discharge', 'flow_rate', 'ph',
        'dissolved_oxygen', 'conductivity', 'turbidity', 'chlorophyll',
        'nitrate', 'phosphate', 'pm2_5', 'pm10', 'co2', 'methane',
        'latitude', 'longitude', 'elevation', 'depth'
    ]

    found_variables = []
    text_lower = text.lower()

    for var in common_variables:
        if var in text_lower:
            found_variables.append(var.replace('_', ' '))

    return found_variables[:10]  # Limit to top 10


def extract_geographic_coverage(text: str) -> Dict[str, Any]:
    """
    Extract geographic coverage hints from text.

    Args:
        text: Text to search for geographic hints

    Returns:
        Dictionary with geographic coverage information
    """
    # This is a simplified implementation
    # In practice, would use NLP gazetteer or geoparsing

    geographic_terms = [
        'global', 'world', 'international', 'continental', 'national',
        'country', 'state', 'province', 'city', 'urban', 'rural',
        'watershed', 'basin', 'river', 'lake', 'ocean', 'coastal',
        'floodplain', 'wetland', 'forest', 'mountain', 'valley'
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


def extract_temporal_coverage(text: str) -> Dict[str, Any]:
    """
    Extract temporal coverage hints from text.

    Args:
        text: Text to search for temporal hints

    Returns:
        Dictionary with temporal coverage information
    """
    temporal_terms = [
        'realtime', 'real-time', 'hourly', 'daily', 'weekly', 'monthly',
        'annual', 'yearly', 'seasonal', 'historical', 'past', 'present',
        'future', 'forecast', 'trend', 'climatology', 'normals'
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
        results = search_github(test_query, max_results=5)
        print(f"Found {len(results)} candidates:")
        for i, candidate in enumerate(results[:3]):
            print(f"{i+1}. {candidate['name']} - {candidate['description'][:100]}...")
    else:
        print("Usage: python search_github.py <query>")