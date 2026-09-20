#!/usr/bin/env python3
"""
Ranking module for dataset-hunter skill.
Ranks datasets based on relevance to research objective.
"""

from typing import List, Dict, Any
import math


def rank_datasets(candidates: List[Dict[str, Any]], problem_components: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Rank datasets based on relevance to the research objective.

    Args:
        candidates: List of normalized dataset dictionaries
        problem_components: Output from stage 1 problem decomposition

    Returns:
        List of ranked dataset dictionaries (highest relevance first)
    """
    print(f"Ranking {len(candidates)} dataset candidates")

    if not candidates:
        return []

    # Score each candidate
    scored_candidates = []
    for candidate in candidates:
        score = _calculate_relevance_score(candidate, problem_components)
        candidate['final_relevance_score'] = score
        scored_candidates.append(candidate)

    # Sort by score descending
    ranked = sorted(scored_candidates, key=lambda x: x['final_relevance_score'], reverse=True)

    print(f"Ranking complete. Top score: {ranked[0]['final_relevance_score']:.2f}" if ranked else "No candidates to rank")
    return ranked


def _calculate_relevance_score(candidate: Dict[str, Any], problem_components: Dict[str, Any]) -> float:
    """
    Calculate relevance score for a dataset candidate.

    Args:
        candidate: Normalized dataset dictionary
        problem_components: Problem decomposition results

    Returns:
        Relevance score (0-100)
    """
    score = 0.0

    # Get text fields to search
    title = candidate.get('dataset_name', '').lower()
    description = candidate.get('description', '').lower()
    variables = [v.lower() for v in candidate.get('variables', [])]
    keywords = [k.lower() for k in candidate.get('keywords', [])]

    # Combine all searchable text
    searchable_text = f"{title} {description} {' '.join(variables)} {' '.join(keywords)}"

    # Check for keyword matches
    keywords_list = problem_components.get('keywords', [])
    geo_terms = problem_components.get('geographic_terms', [])
    temporal_terms = problem_components.get('temporal_terms', [])
    domain_terms = problem_components.get('domain_terms', [])

    # Score keyword matches
    keyword_matches = 0
    for keyword in keywords_list:
        if keyword.lower() in searchable_text:
            keyword_matches += 1

    if keywords_list:
        keyword_score = (keyword_matches / len(keywords_list)) * 30
        score += keyword_score

    # Score geographic term matches
    geo_matches = 0
    for term in geo_terms:
        if term.lower() in searchable_text:
            geo_matches += 1

    if geo_terms:
        geo_score = (geo_matches / len(geo_terms)) * 25
        score += geo_score

    # Score temporal term matches
    temporal_matches = 0
    for term in temporal_terms:
        if term.lower() in searchable_text:
            temporal_matches += 1

    if temporal_terms:
        temporal_score = (temporal_matches / len(temporal_terms)) * 20
        score += temporal_score

    # Score domain term matches
    domain_matches = 0
    for term in domain_terms:
        if term.lower() in searchable_text:
            domain_matches += 1

    if domain_terms:
        domain_score = (domain_matches / len(domain_terms)) * 25
        score += domain_score

    # Boost score based on existing relevance score from source
    existing_score = candidate.get('relevance_score', 0)
    if existing_score > 0:
        # Normalize existing score (assuming 0-100 scale) and add weighted bonus
        score += min(existing_score * 0.2, 10)  # Max 10 point boost

    # Ensure score is in 0-100 range
    return min(max(score, 0), 100)


if __name__ == "__main__":
    # Test the function
    import sys
    import json
    if len(sys.argv) > 1:
        # For testing, we'd load a JSON file
        print("Usage: python rank.py < input.json > output.json")
        print("Or import and use rank_datasets() function")
    else:
        print("Ranking module for dataset-hunter skill")
        print("Provides rank_datasets() function to rank dataset candidates")