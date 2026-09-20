#!/usr/bin/env python3
"""
Zenodo dataset search module for dataset-hunter skill.
Searches Zenodo for datasets and research data.
"""

import requests
import json
import time
from typing import List, Dict, Any, Optional
from urllib.parse import quote_plus


def search_zenodo(query: str, max_results: int = 100) -> List[Dict[str, Any]]:
    """
    Search Zenodo for datasets.

    Args:
        query: Search query string
        max_results: Maximum number of results to return

    Returns:
        List of dataset candidate dictionaries
    """
    print(f"Searching Zenodo for: {query}")

    candidates = []

    try:
        # Zenodo REST API endpoint
        url = "https://zenodo.org/api/records"

        params = {
            'q': query,
            'size': min(max_results, 100),  # Zenodo API max is usually 100
            'sort': 'mostrecent',  # or 'bestmatch', 'views', 'downloads'
            'access_right': 'open'  # Focus on open access datasets
        }

        headers = {
            'User-Agent': 'dataset-hunter-skill/1.0'
        }

        response = requests.get(url, params=params, headers=headers, timeout=30)

        if response.status_code == 200:
            data = response.json()
            hits = data.get('hits', {}).get('hits', [])

            for hit in hits:
                candidate = extract_zenodo_candidate(hit)
                if candidate:
                    candidates.append(candidate)

        else:
            print(f"Zenodo search failed with status {response.status_code}")

    except Exception as e:
        print(f"Error searching Zenodo: {e}")

    return candidates


def extract_zenodo_candidate(hit: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Extract dataset candidate information from Zenodo hit.

    Args:
        hit: Zenodo API hit record

    Returns:
        Dataset candidate dictionary or None if not suitable
    """
    try:
        metadata = hit.get('metadata', {})
        files = hit.get('files', [])

        # Basic record info
        title = metadata.get('title', '')
        description = metadata.get('description', '') or ''
        creators = metadata.get('creators', [])
        publication_date = metadata.get('publication_date', '')
        version = metadata.get('version', '')
        resource_type = metadata.get('resource_type', {}).get('type', '')
        access_right = metadata.get('access_right', '')
        license = metadata.get('license', {}).get('id', '') if metadata.get('license') else ''
        doi = metadata.get('doi', '')

        # Skip if no title or description
        if not title or not description:
            return None

        # Check if this looks like a dataset (not just a publication)
        is_likely_dataset = assess_if_zenodo_dataset(metadata, files)

        # Construct URLs
        record_id = hit.get('id', '')
        url = f"https://zenodo.org/record/{record_id}"
        if doi:
            url = f"https://doi.org/{doi}"

        # Extract file information
        file_info = extract_zenodo_file_info(files)

        # Build candidate
        candidate = {
            'name': title.replace('-', ' ').replace('_', ' ').title()[:100],  # Limit length
            'title': title,
            'source': 'Zenodo',
            'organization': extract_organization(creators),
            'description': description[:1000],  # Limit length
            'url': url,
            'api_url': hit.get('links', {}).get('self', ''),
            'doi': doi,
            'record_id': record_id,
            'version': version,
            'resource_type': resource_type,
            'access_right': access_right,
            'license': license,
            'publication_date': publication_date,
            'creators': creators,
            'file_count': len(files),
            'total_size': sum(f.get('size', 0) for f in files),
            'file_formats': file_info['formats'],
            'file_list': file_info['file_list'],
            'download_url': file_info['download_url'],
            'keywords': metadata.get('keywords', []),
            'subjects': metadata.get('subjects', []),
            'communities': metadata.get('communities', []),
            'relevance_score': calculate_zenodo_relevance(metadata, files),
            'source_reliability': 'tier_2',  # Zenodo is tier 2 (major research repository)
            'access_method': 'direct_download_or_api',
            'variables': extract_zenodo_variables(metadata, files),
            'geographic_coverage': extract_zenodo_geographic(metadata),
            'temporal_coverage': extract_zenodo_temporal(metadata),
            'access_restrictions': 'none' if access_right == 'open' else 'restricted',
            'cost': 'free',
            'documentation_url': url,
            'citation': metadata.get('citation', ''),
        }

        return candidate

    except Exception as e:
        print(f"Error extracting Zenodo candidate: {e}")
        return None


def assess_if_zenodo_dataset(metadata: Dict[str, Any], files: List[Dict[str, Any]]) -> bool:
    """
    Assess if a Zenodo record is likely a dataset vs. just a publication.

    Args:
        metadata: Zenodo record metadata
        files: List of files in the record

    Returns:
        Boolean indicating if likely a dataset
    """
    # Check resource type
    resource_type = metadata.get('resource_type', {}).get('type', '').lower()
    resource_subtype = metadata.get('resource_type', {}).get('subtype', '').lower()

    # Strong dataset indicators
    dataset_types = ['dataset', 'data', 'datapaper', 'collection']
    if any(dt in resource_type for dt in dataset_types) or any(dt in resource_subtype for dt in dataset_types):
        return True

    # Check file types - if it has data files, likely a dataset
    data_extensions = ['.csv', '.tsv', '.json', '.xml', '.parquet', '.hdf5', '.netcdf', '.geojson', '.shp', '.mat', '.rdata']
    has_data_files = False
    for file in files:
        filename = file.get('key', '').lower()
        if any(ext in filename for ext in data_extensions):
            has_data_files = True
            break

    if has_data_files:
        return True

# Check description for dataset indicators
    description = metadata.get('description', '').lower()
    dataset_indicators = [
        'dataset', 'data', 'csv', 'json', 'table', 'database', 'spreadsheet',
        'measurement', 'observation', 'survey', 'experiment', 'simulation'
    ]

    if any(indicator in description for indicator in dataset_indicators):
        return True

    # If it's primarily a publication with no data files, less likely to be a dataset
    publication_types = ['publication', 'article', 'book', 'chapter', 'conferencepaper']
    if any(pub in resource_type for pub in publication_types) and not has_data_files:
        return False

    # Default to true for unclear cases (better to include and filter later)
    return True


def extract_organization(creators: List[Dict[str, Any]]) -> str:
    """
    Extract organization from Zenodo creators.

    Args:
        creators: List of creator dictionaries

    Returns:
        Organization string or empty
    """
    organizations = []
    for creator in creators:
        # Check for affiliation in creator
        affiliation = creator.get('affiliation', '')
        if affiliation:
            organizations.append(affiliation)

    return '; '.join(organizations) if organizations else ''


def extract_zenodo_file_info(files: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Extract file information from Zenodo files.

    Args:
        files: List of file dictionaries from Zenodo

    Returns:
        Dictionary with file information
    """
    formats = []
    file_list = []
    download_url = ''

    for file in files:
        filename = file.get('key', '')
        file_type = file.get('type', '')
        size = file.get('size', 0)
        download_link = file.get('links', {}).get('self', '')

        file_list.append({
            'filename': filename,
            'type': file_type,
            'size': size,
            'download_url': download_link
        })

        # Extract format from filename
        if '.' in filename:
            ext = filename.split('.')[-1].lower()
            formats.append(ext)

        # Use first file as primary download URL (or look for specific data files)
        if not download_url and size > 0:
            download_url = download_link

    # Also look for files that seem like datasets
    data_file_keywords = ['data', 'dataset', 'csv', 'json', 'table']
    for file in files:
        filename = file.get('key', '').lower()
        if any(keyword in filename for keyword in data_file_keywords):
            if not download_url or file.get('size', 0) > 0:  # Prefer larger data files
                download_url = file.get('links', {}).get('self', '')

    return {
        'formats': list(set(formats)),
        'file_list': file_list,
        'download_url': download_url
    }


def calculate_zenodo_relevance(metadata: Dict[str, Any], files: List[Dict[str, Any]]) -> int:
    """
    Calculate relevance score for Zenodo record.

    Args:
        metadata: Zenodo record metadata
        files: List of files in the record

    Returns:
        Relevance score (0-10)
    """
    score = 0
    description = metadata.get('description', '').lower()
    title = metadata.get('title', '').lower()
    keywords = [kw.lower() for kw in metadata.get('keywords', [])]
    subjects = [subj.lower() for subj in metadata.get('subjects', [])]

    text_to_search = " ".join([description, title] + keywords + subjects)

    # Check for data-related keywords
    data_keywords = [
        'dataset', 'data', 'csv', 'json', 'xml', 'parquet', 'hdf5', 'netcdf',
        'geojson', 'shapefile', 'tabular', 'spreadsheet', 'database',
        'measurement', 'observation', 'survey', 'experiment', 'timeseries'
    ]

    for keyword in data_keywords:
        if keyword in text_to_search:
            score += 1

    # Boost for having files
    if len(files) > 0:
        score += 2
    if len(files) > 5:
        score += 1

    # Boost for file sizes (indicates substantial data)
    total_size = sum(f.get('size', 0) for f in files)
    if total_size > 1000000:  # > 1MB
        score += 2
    elif total_size > 100000:  # > 100KB
        score += 1

    # Check for open access
    access_right = metadata.get('access_right', '')
    if access_right == 'open':
        score += 1

    return min(score, 10)


def extract_zenodo_variables(metadata: Dict[str, Any], files: List[Dict[str, Any]]) -> List[str]:
    """
    Extract potential variables from Zenodo record.

    Args:
        metadata: Zenodo record metadata
        files: List of files in the record

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
    description = metadata.get('description', '').lower()
    title = metadata.get('title', '').lower()
    keywords = [kw.lower() for kw in metadata.get('keywords', [])]
    subjects = [subj.lower() for subj in metadata.get('subjects', [])]

    text_to_search = " ".join([description, title] + keywords + subjects)

    for var in common_variables:
        if var in text_to_search:
            found_variables.append(var.replace('_', ' '))

    return found_variables[:10]


def extract_zenodo_geographic(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract geographic coverage from Zenodo record.

    Args:
        metadata: Zenodo record metadata

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
    description = metadata.get('description', '').lower()
    title = metadata.get('title', '').lower()
    keywords = [kw.lower() for kw in metadata.get('keywords', [])]
    subjects = [subj.lower() for subj in metadata.get('subjects', [])]

    text_to_search = " ".join([description, title] + keywords + subjects)

    for term in geographic_terms:
        if term in text_to_search:
            found_terms.append(term)

    # Also check for spatial coverage in metadata
    spatial = metadata.get('spatial', {})
    if spatial:
        # Could extract coordinates, bounding box, etc.
        pass

    return {
        'mentions': found_terms,
        'type': 'textual_description',
        'detail': 'Geographic coverage extracted from text mentions'
    }


def extract_zenodo_temporal(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract temporal coverage from Zenodo record.

    Args:
        metadata: Zenodo record metadata

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
    description = metadata.get('description', '').lower()
    title = metadata.get('title', '').lower()
    keywords = [kw.lower() for kw in metadata.get('keywords', [])]
    subjects = [subj.lower() for subj in metadata.get('subjects', [])]

    text_to_search = " ".join([description, title] + keywords + subjects)

    for term in temporal_terms:
        if term in text_to_search:
            found_terms.append(term)

    # Also check for dates in metadata
    dates = []
    pub_date = metadata.get('publication_date', '')
    if pub_date:
        dates.append(pub_date)

    return {
        'mentions': found_terms,
        'dates': dates,
        'type': 'textual_description',
        'detail': 'Temporal coverage extracted from text mentions'
    }


if __name__ == "__main__":
    # Test the function
    import sys
    if len(sys.argv) > 1:
        test_query = sys.argv[1]
        results = search_zenodo(test_query, max_results=5)
        print(f"Found {len(results)} candidates:")
        for i, candidate in enumerate(results[:3]):
            print(f"{i+1}. {candidate['title']} - {candidate['description'][:100]}...")
    else:
        print("Usage: python search_zenodo.py <query>")