#!/usr/bin/env python3
"""
Validation module for dataset-hunter skill.
Assesses quality of datasets without downloading large files.
"""

from typing import List, Dict, Any


def validate_datasets(candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Assess quality of candidates without downloading large files.

    Args:
        candidates: List of normalized dataset dictionaries

    Returns:
        List of validated dataset dictionaries with quality scores
    """
    print(f"Validating {len(candidates)} dataset candidates")

    if not candidates:
        return []

    # Validate each candidate
    validated = []
    for candidate in candidates:
        quality_score = _assess_quality(candidate)
        candidate['quality_score'] = quality_score
        validated.append(candidate)

    print(f"Validation complete. Average quality score: {sum(c['quality_score'] for c in validated) / len(validated):.2f}")
    return validated


def _assess_quality(candidate: Dict[str, Any]) -> float:
    """
    Assess quality of a single dataset candidate.

    Args:
        candidate: Normalized dataset dictionary

    Returns:
        Quality score (0-100)
    """
    score = 0.0

    # Check for essential fields
    if candidate.get('dataset_name'):
        score += 15
    if candidate.get('description') and len(candidate['description']) > 10:
        score += 10
    if candidate.get('url') and _is_valid_url(candidate['url']):
        score += 15
    if candidate.get('organization'):
        score += 10

    # Check for data usefulness indicators
    if candidate.get('variables') and len(candidate['variables']) > 0:
        score += 15
    if candidate.get('file_formats') and candidate['file_formats'] != ['unknown']:
        score += 10
    if candidate.get('geographic_coverage', {}).get('mentions'):
        score += 10
    if candidate.get('temporal_coverage', {}).get('mentions'):
        score += 10

    # Check for metadata completeness
    if candidate.get('license'):
        score += 5
    if candidate.get('access_method'):
        score += 5
    if candidate.get('cost') != 'unknown':
        score += 5

    # Source reliability bonus
    reliability = candidate.get('source_reliability', 'tier_4')
    reliability_scores = {
        'tier_1': 20,  # Authoritative government/official
        'tier_2': 15,  # Academic/research institutions
        'tier_3': 10,  # Community/platform (GitHub, etc.)
        'tier_4': 5    # Unknown/questionable
    }
    score += reliability_scores.get(reliability, 0)

    # Ensure score is in 0-100 range
    return min(max(score, 0), 100)


def _is_valid_url(url: str) -> bool:
    """
    Basic URL validation.

    Args:
        url: URL string to validate

    Returns:
        True if URL appears valid
    """
    if not url or not isinstance(url, str):
        return False
    return url.startswith(('http://', 'https://')) and len(url) > 10


if __name__ == "__main__":
    # Test the function
    import sys
    import json
    if len(sys.argv) > 1:
        # For testing, we'd load a JSON file
        print("Usage: python validate.py < input.json > output.json")
        print("Or import and use validate_datasets() function")
    else:
        print("Validation module for dataset-hunter skill")
        print("Provides validate_datasets() function to assess dataset quality")