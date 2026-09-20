#!/usr/bin/env python3
"""
Deduplication module for dataset-hunter skill.
Detects and removes duplicate datasets.
"""

import hashlib
from typing import List, Dict, Any
from urllib.parse import urlparse


def deduplicate_datasets(candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Detect and remove duplicate datasets based on URL and content similarity.

    Args:
        candidates: List of normalized dataset dictionaries

    Returns:
        List of deduplicated dataset dictionaries
    """
    print(f"Deduplicating {len(candidates)} dataset candidates")

    if not candidates:
        return []

    # Track seen URLs and titles to detect duplicates
    seen_urls = set()
    seen_titles = set()
    deduplicated = []

    for candidate in candidates:
        # Create a signature for deduplication
        url = candidate.get('url', '').lower().strip()
        title = candidate.get('dataset_name', '').lower().strip()

        # Skip if we've seen this exact URL before
        if url in seen_urls and url:
            print(f"Skipping duplicate URL: {url}")
            continue

        # Skip if we've seen this exact title before (and it's not empty)
        if title in seen_titles and title and len(title) > 3:
            print(f"Skipping duplicate title: {title}")
            continue

        # Add to seen sets
        if url:
            seen_urls.add(url)
        if title:
            seen_titles.add(title)

        deduplicated.append(candidate)

    print(f"Removed {len(candidates) - len(deduplicated)} duplicates")
    return deduplicated


def _calculate_content_hash(candidate: Dict[str, Any]) -> str:
    """
    Calculate a hash based on dataset content for advanced deduplication.

    Args:
        candidate: Normalized dataset dictionary

    Returns:
        SHA-256 hash string
    """
    # Create a string representation of key fields
    key_fields = [
        candidate.get('dataset_name', ''),
        candidate.get('description', ''),
        candidate.get('organization', ''),
        str(sorted(candidate.get('variables', []))),
        str(sorted(candidate.get('file_formats', [])))
    ]

    content_string = '|'.join(key_fields)
    return hashlib.sha256(content_string.encode('utf-8')).hexdigest()


if __name__ == "__main__":
    # Test the function
    import sys
    import json
    if len(sys.argv) > 1:
        # For testing, we'd load a JSON file
        print("Usage: python deduplicate.py < input.json > output.json")
        print("Or import and use deduplicate_datasets() function")
    else:
        print("Deduplication module for dataset-hunter skill")
        print("Provides deduplicate_datasets() function to remove duplicates")