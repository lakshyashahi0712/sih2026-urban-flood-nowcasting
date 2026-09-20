#!/usr/bin/env python3
"""
Normalization module for dataset-hunter skill.
Normalizes dataset candidates to a common schema.
"""

import json
import re
from typing import List, Dict, Any, Optional
from datetime import datetime


def normalize_datasets(candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Normalize dataset candidates to a common schema.

    Args:
        candidates: List of dataset candidate dictionaries from various sources

    Returns:
        List of normalized dataset dictionaries
    """
    print(f"Normalizing {len(candidates)} dataset candidates")

    normalized = []

    for candidate in candidates:
        try:
            normalized_candidate = normalize_single_dataset(candidate)
            if normalized_candidate:
                normalized.append(normalized_candidate)
        except Exception as e:
            print(f"Error normalizing dataset {candidate.get('title', 'unknown')}: {e}")

    return normalized


def normalize_single_dataset(candidate: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Normalize a single dataset candidate to the common schema.

    Args:
        candidate: Raw dataset candidate dictionary

    Returns:
        Normalized dataset dictionary or None if invalid
    """
    try:
        # Extract basic fields with fallbacks
        title = candidate.get('title', '') or candidate.get('name', '')
        description = candidate.get('description', '')
        url = candidate.get('url', '')

        # Skip if missing essential fields
        if not title or not url:
            return None

        # Build normalized dataset according to schema
        normalized = {
            'dataset_name': clean_dataset_name(title),
            'source': candidate.get('source', 'unknown'),
            'description': clean_description(description),
            'url': url,
            'api_url': candidate.get('api_url', ''),
            'organization': candidate.get('organization', ''),
            'version': candidate.get('version', ''),
            'access_method': candidate.get('access_method', ''),
            'access_restrictions': candidate.get('access_restrictions', 'unknown'),
            'cost': candidate.get('cost', 'unknown'),
            'file_formats': normalize_file_formats(candidate.get('file_formats', [])),
            'variables': candidate.get('variables', []),
            'geographic_coverage': normalize_geographic_coverage(
                candidate.get('geographic_coverage', {})
            ),
            'temporal_coverage': normalize_temporal_coverage(
                candidate.get('temporal_coverage', {})
            ),
            'license': candidate.get('license', ''),
            'doi': candidate.get('doi', ''),
            'record_id': candidate.get('record_id', ''),
            'dataset_id': candidate.get('dataset_id', ''),
            'keywords': candidate.get('keywords', []),
            'subjects': candidate.get('subjects', []),
            'creators': candidate.get('creators', []),
            'communities': candidate.get('communities', []),
            'file_count': candidate.get('file_count', 0),
            'total_size': candidate.get('total_size', 0),
            'download_url': candidate.get('download_url', ''),
            'relevance_score': candidate.get('relevance_score', 0),
            'source_reliability': candidate.get('source_reliability', 'tier_4'),
            'documentation_url': candidate.get('documentation_url', url),
            'citation': candidate.get('citation', ''),
            'paper_url': candidate.get('paper_url', ''),
            'discovery_timestamp': datetime.now().isoformat(),
            'raw_metadata': candidate  # Keep original for reference
        }

        # Ensure required fields are present
        if not normalized['dataset_name']:
            normalized['dataset_name'] = generate_dataset_name_from_url(url)

        return normalized

    except Exception as e:
        print(f"Error normalizing single dataset: {e}")
        return None


def clean_dataset_name(title: str) -> str:
    """
    Clean and standardize dataset name.

    Args:
        title: Raw title/name

    Returns:
        Cleaned dataset name
    """
    if not title:
        return ""

    # Remove extra whitespace and special characters
    name = re.sub(r'\s+', ' ', title.strip())
    # Remove common prefixes/suffixes that don't add value
    name = re.sub(r'^(dataset|data|collection|database)[\s\-_:]*', '', name, flags=re.IGNORECASE)
    name = re.sub(r'[\s\-_:]*(dataset|data|collection|database)$', '', name, flags=re.IGNORECASE)

    # Limit length
    if len(name) > 200:
        name = name[:200].strip()

    return name or title  # Fallback to original if cleaning removed everything


def clean_description(description: str) -> str:
    """
    Clean and standardize dataset description.

    Args:
        description: Raw description

    Returns:
        Cleaned description
    """
    if not description:
        return ""

    # Remove extra whitespace
    desc = re.sub(r'\s+', ' ', description.strip())

    # Limit length
    if len(desc) > 2000:
        desc = desc[:2000] + "..."

    return desc


def normalize_file_formats(formats: List[str]) -> List[str]:
    """
    Normalize file formats list.

    Args:
        formats: List of file format strings

    Returns:
        Normalized list of file formats
    """
    if not formats:
        return ['unknown']

    # Standardize format names
    format_mapping = {
        'csv': 'csv',
        'tsv': 'tsv',
        'json': 'json',
        'jsonl': 'jsonl',
        'parquet': 'parquet',
        'xls': 'excel',
        'xlsx': 'excel',
        'xml': 'xml',
        'html': 'html',
        'htm': 'html',
        'pdf': 'pdf',
        'zip': 'zip',
        'gz': 'gzip',
        'tar': 'tar',
        'netcdf': 'netcdf',
        'nc': 'netcdf',
        'hdf5': 'hdf5',
        'h5': 'hdf5',
        'geojson': 'geojson',
        'shapefile': 'shapefile',
        'shp': 'shapefile',
        'sqlite': 'sqlite',
        'db': 'sqlite',
        'mat': 'mat',
        'rdata': 'rdata',
        'r': 'r',
        'txt': 'text',
        'text': 'text'
    }

    normalized = []
    for fmt in formats:
        if isinstance(fmt, str):
            fmt_lower = fmt.lower().strip()
            # Remove leading dots
            fmt_lower = re.sub(r'^\.+', '', fmt_lower)
            # Map to standard format
            std_format = format_mapping.get(fmt_lower, fmt_lower)
            if std_format not in normalized:
                normalized.append(std_format)

    return normalized if normalized else ['unknown']


def normalize_geographic_coverage(geo_coverage: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize geographic coverage information.

    Args:
        geo_coverage: Raw geographic coverage dictionary

    Returns:
        Normalized geographic coverage dictionary
    """
    if not isinstance(geo_coverage, dict):
        return {
            'mentions': [],
            'type': 'unknown',
            'detail': 'Invalid geographic coverage format'
        }

    # Ensure required structure
    normalized = {
        'mentions': geo_coverage.get('mentions', []),
        'type': geo_coverage.get('type', 'textual_description'),
        'detail': geo_coverage.get('detail', 'Geographic coverage information')
    }

    # Ensure mentions is a list
    if not isinstance(normalized['mentions'], list):
        if isinstance(normalized['mentions'], str):
            normalized['mentions'] = [normalized['mentions']]
        else:
            normalized['mentions'] = []

    return normalized


def normalize_temporal_coverage(temp_coverage: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize temporal coverage information.

    Args:
        temp_coverage: Raw temporal coverage dictionary

    Returns:
        Normalized temporal coverage dictionary
    """
    if not isinstance(temp_coverage, dict):
        return {
            'mentions': [],
            'dates': [],
            'type': 'unknown',
            'detail': 'Invalid temporal coverage format'
        }

    # Ensure required structure
    normalized = {
        'mentions': temp_coverage.get('mentions', []),
        'dates': temp_coverage.get('dates', []),
        'type': temp_coverage.get('type', 'textual_description'),
        'detail': temp_coverage.get('detail', 'Temporal coverage information')
    }

    # Ensure mentions and dates are lists
    for field in ['mentions', 'dates']:
        if not isinstance(normalized[field], list):
            if isinstance(normalized[field], str):
                normalized[field] = [normalized[field]]
            else:
                normalized[field] = []

    return normalized


def generate_dataset_name_from_url(url: str) -> str:
    """
    Generate a dataset name from URL when title is missing.

    Args:
        url: Dataset URL

    Returns:
        Generated dataset name
    """
    if not url:
        return "unknown_dataset"

    try:
        # Extract meaningful parts from URL
        from urllib.parse import urlparse
        parsed = urlparse(url)
        path = parsed.path.strip('/')

        # Get the last meaningful segment
        if path:
            segments = [seg for seg in path.split('/') if seg]
            if segments:
                # Take the last segment, clean it
                name = segments[-1]
                # Remove file extensions
                name = re.sub(r'\.(csv|json|xml|zip|tar|gz|txt)$', '', name, flags=re.IGNORECASE)
                # Replace underscores/hyphens with spaces
                name = re.sub(r'[_-]+', ' ', name)
                # Title case
                name = name.title()
                return name if len(name) > 2 else "unknown_dataset"

        # Fallback to domain name
        domain = parsed.netloc
        if domain:
            # Remove www. and common prefixes
            domain = re.sub(r'^www\.', '', domain)
            # Take first part of domain
            domain_parts = domain.split('.')
            if domain_parts:
                name = domain_parts[0].replace('-', ' ').title()
                return name if len(name) > 2 else "unknown_dataset"
    except Exception:
        pass

    return "unknown_dataset"


if __name__ == "__main__":
    # Test the function
    import sys
    if len(sys.argv) > 1:
        # For testing, we'd need to load a JSON file
        print("Usage: python normalize.py < input.json > output.json")
        print("Or import and use normalize_datasets() function")
    else:
        print("Normalization module for dataset-hunter skill")
        print("Provides normalize_datasets() function to standardize dataset candidates")