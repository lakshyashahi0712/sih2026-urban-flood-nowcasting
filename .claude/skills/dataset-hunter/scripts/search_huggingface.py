#!/usr/bin/env python3
"""
Hugging Face dataset search module for dataset-hunter skill.
Searches Hugging Face Hub for datasets.
"""

import requests
import json
import time
from typing import List, Dict, Any, Optional
from urllib.parse import quote_plus


def search_huggingface(query: str, max_results: int = 100) -> List[Dict[str, Any]]:
    """
    Search Hugging Face Hub for datasets.

    Args:
        query: Search query string
        max_results: Maximum number of results to return

    Returns:
        List of dataset candidate dictionaries
    """
    print(f"Searching Hugging Face for: {query}")

    candidates = []

    try:
        # Hugging Face Hub API endpoint for dataset search
        url = "https://huggingface.co/api/datasets"

        params = {
            'search': query,
            'limit': min(max_results, 100),
            'sort': 'downloads',  # or 'likes', 'lastModified'
            'direction': -1
        }

        headers = {
            'User-Agent': 'dataset-hunter-skill/1.0'
        }

        response = requests.get(url, params=params, headers=headers, timeout=30)

        if response.status_code == 200:
            data = response.json()
            # HF API returns a list of dataset objects

            for item in data:
                candidate = extract_hf_candidate(item)
                if candidate:
                    candidates.append(candidate)

        else:
            print(f"Hugging Face search failed with status {response.status_code}")
            # Try alternative approach if needed

    except Exception as e:
        print(f"Error searching Hugging Face: {e}")

    return candidates


def extract_hf_candidate(item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Extract dataset candidate information from Hugging Face dataset item.

    Args:
        item: Hugging Face API dataset object

    Returns:
        Dataset candidate dictionary or None if not suitable
    """
    try:
        # Basic dataset info
        dataset_id = item.get('id', '')  # format: "username/dataset-name"
        name = item.get('id', '').split('/')[-1] if '/' in item.get('id', '') else item.get('id', '')
        description = item.get('description', '') or ''
        likes = item.get('likes', 0)
        downloads = item.get('downloads', 0)
        created_at = item.get('createdAt', '')
        last_modified = item.get('lastModified', '')

        # Skip if no meaningful identifier
        if not dataset_id or dataset_id == '':
            return None

        # Construct URLs
        base_url = "https://huggingface.co/datasets"
        url = f"{base_url}/{dataset_id}"

        # Extract additional metadata from HF response
        tags = item.get('tags', [])
        pipeline_tag = item.get('pipeline_tag', '')
        library_name = item.get('library_name', '')

        # Determine if this looks like a genuine dataset (not just a model demo)
        is_likely_dataset = assess_if_dataset(item)

        if not is_likely_dataset:
            # Still include but with lower confidence
            pass

        # Extract file information if available
        # Note: HF API doesn't always return file details in search results
        # Might need additional API calls for detailed file info

        # Build candidate
        candidate = {
            'name': name,
            'title': name.replace('-', ' ').replace('_', ' ').title(),
            'source': 'Hugging Face',
            'organization': dataset_id.split('/')[0] if '/' in dataset_id else 'unknown',
            'description': description[:1000] if description else '',  # Limit length
            'url': url,
            'api_url': f"https://huggingface.co/api/datasets/{dataset_id}",
            'dataset_id': dataset_id,
            'likes': likes,
            'downloads': downloads,
            'created_at': created_at,
            'last_modified': last_modified,
            'tags': tags,
            'pipeline_tag': pipeline_tag,
            'library_name': library_name,
            'license': item.get('license', ''),  # Often not in search results
            'task_categories': item.get('task_categories', []),
            'size': item.get('size', 'unknown'),  # Size in bytes if available
            'relevance_score': calculate_relevance_score(item),
            'source_reliability': 'tier_2',  # HF is tier 2 (major research repository)
            'access_method': 'huggingface_hub',
            'file_formats': infer_hf_formats(item),
            'variables': extract_hf_variables(item),
            'geographic_coverage': extract_hf_geographic(item),
            'temporal_coverage': extract_hf_temporal(item),
            'access_restrictions': 'none',  # HF datasets are generally open
            'cost': 'free',
            'documentation_url': url,
            'citation': item.get('citation', ''),
            'paper_url': item.get('paper_url', ''),
        }

        return candidate

    except Exception as e:
        print(f"Error extracting HF candidate: {e}")
        return None


def assess_if_dataset(item: Dict[str, Any]) -> bool:
    """
    Assess if an HF item is likely a genuine dataset vs. model demo, etc.

    Args:
        item: Hugging Face API dataset object

    Returns:
        Boolean indicating if likely a dataset
    """
    # Check for dataset-like characteristics
    description = item.get('description', '').lower()
    tags = [tag.lower() for tag in item.get('tags', [])]
    pipeline_tag = item.get('pipeline_tag', '').lower()

    # Strong indicators it's a dataset
    dataset_indicators = [
        'dataset', 'data', 'csv', 'json', 'parquet', 'image', 'audio',
        'text', 'video', 'multimodal', 'tabular', 'timeseries'
    ]

    # Model/demo indicators (might not be pure datasets)
    model_indicators = [
        'model', 'demo', 'example', 'pretrained', 'finetuned',
        'classification', 'detection', 'segmentation', 'generation'
    ]

    text_to_check = " ".join([description] + tags + [pipeline_tag])

    dataset_score = sum(1 for indicator in dataset_indicators if indicator in text_to_check)
    model_score = sum(1 for indicator in model_indicators if indicator in text_to_check)

    # If it has strong dataset indicators and weak model indicators, likely a dataset
    return dataset_score >= 2 and dataset_score > model_score


def calculate_relevance_score(item: Dict[str, Any]) -> int:
    """
    Calculate relevance score based on HF metadata.

    Args:
        item: Hugging Face API dataset object

    Returns:
        Relevance score (0-10)
    """
    score = 0
    description = item.get('description', '').lower()
    tags = [tag.lower() for tag in item.get('tags', [])]

    # Check for data-related keywords in description/tags
    data_keywords = [
        'dataset', 'data', 'csv', 'json', 'xml', 'parquet', 'hdf5', 'netcdf',
        'geojson', 'shapefile', 'csv', 'tsv', 'excel', 'sql', 'database'
    ]

    text_to_search = " ".join([description] + tags)

    for keyword in data_keywords:
        if keyword in text_to_search:
            score += 1

    # Boost for high downloads/likes (indicates quality/use)
    downloads = item.get('downloads', 0)
    likes = item.get('likes', 0)

    if downloads > 1000:
        score += 2
    elif downloads > 100:
        score += 1

    if likes > 50:
        score += 2
    elif likes > 10:
        score += 1

    return min(score, 10)  # Cap at 10


def infer_hf_formats(item: Dict[str, Any]) -> List[str]:
    """
    Infer likely file formats from Hugging Face dataset metadata.

    Args:
        item: Hugging Face API dataset object

    Returns:
        List of inferred file formats
    """
    formats = []
    description = item.get('description', '').lower()
    tags = [tag.lower() for tag in item.get('tags', [])]

    text_to_search = " ".join([description] + tags)

    format_mapping = {
        'csv': ['csv', 'comma-separated'],
        'json': ['json', 'jsonl'],
        'parquet': ['parquet'],
        'excel': ['xls', 'xlsx', 'excel'],
        'image': ['jpg', 'jpeg', 'png', 'tiff', 'bmp'],
        'audio': ['wav', 'mp3', 'flac', 'ogg'],
        'text': ['txt', 'text'],
        'video': ['mp4', 'avi', 'mov'],
        'geospatial': ['geojson', 'shapefile', 'shp', 'netcdf', 'hdf5'],
        'timeseries': ['csv', 'json', 'parquet']
    }

    for fmt, indicators in format_mapping.items():
        if any(indicator in text_to_search for indicator in indicators):
            formats.append(fmt)

    # If no specific formats but seems data-related
    if not formats and any(indicator in text_to_search for indicator in ['data', 'dataset']):
        formats = ['unknown']

    return list(set(formats))


def extract_hf_variables(item: Dict[str, Any]) -> List[str]:
    """
    Extract potential variables from Hugging Face dataset metadata.

    Args:
        item: Hugging Face API dataset object

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
    description = item.get('description', '').lower()
    tags = [tag.lower() for tag in item.get('tags', [])]
    text_to_search = " ".join([description] + tags)

    for var in common_variables:
        if var in text_to_search:
            found_variables.append(var.replace('_', ' '))

    return found_variables[:10]


def extract_hf_geographic(item: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract geographic coverage from Hugging Face dataset metadata.

    Args:
        item: Hugging Face API dataset object

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
    description = item.get('description', '').lower()
    tags = [tag.lower() for tag in item.get('tags', [])]
    text_to_search = " ".join([description] + tags)

    for term in geographic_terms:
        if term in text_to_search:
            found_terms.append(term)

    return {
        'mentions': found_terms,
        'type': 'textual_description',
        'detail': 'Geographic coverage extracted from text mentions'
    }


def extract_hf_temporal(item: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract temporal coverage from Hugging Face dataset metadata.

    Args:
        item: Hugging Face API dataset object

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
    description = item.get('description', '').lower()
    tags = [tag.lower() for tag in item.get('tags', [])]
    text_to_search = " ".join([description] + tags)

    for term in temporal_terms:
        if term in text_to_search:
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
        results = search_huggingface(test_query, max_results=5)
        print(f"Found {len(results)} candidates:")
        for i, candidate in enumerate(results[:3]):
            print(f"{i+1}. {candidate['name']} - {candidate['description'][:100]}...")
    else:
        print("Usage: python search_huggingface.py <query>")