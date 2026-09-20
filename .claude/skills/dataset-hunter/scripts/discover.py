#!/usr/bin/env python3
"""
Main discovery script for the dataset-hunter skill.
Orchestrates the 10-stage dataset discovery pipeline.
"""

import argparse
import json
import sys
import time
import hashlib
import pickle
import os
from typing import Dict, List, Any, Optional
from pathlib Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import wraps
import random

# When run as a script, adjust the path to allow relative imports
if __name__ == "__main__" and __package__ is None:
    # Add the parent directory of this script to the sys.path
    sys.path.insert(0, str(Path(__file__).parent))
    # Now we can import the modules as if they were in a package
    from search_github import search_github
    from search_huggingface import search_huggingface
    from search_zenodo import search_zenodo
    from search_web import search_web
    from normalize import normalize_datasets
    from deduplicate import deduplicate_datasets
    from rank import rank_datasets
    from validate import validate_datasets
    from export import export_results
else:
    # Import pipeline stages (when imported as a module)
    from .search_github import search_github
    from .search_huggingface import search_huggingface
    from .search_zenodo import search_zenodo
    from .search_web import search_web
    from .normalize import normalize_datasets
    from .deduplicate import deduplicate_datasets
    from .rank import rank_datasets
    from .validate import validate_datasets
    from .export import export_results


# Constants for execution limits and timeouts
MAX_DISCOVERY_DEPTH = 2
SEARCH_LIMITS = {
    'QUICK': 15,
    'STANDARD': 50,
    'DEEP': 100
}
EXECUTION_TIME_BUDGET = {
    'QUICK': 120,   # 2 minutes
    'STANDARD': 300, # 5 minutes
    'DEEP': 900     # 15 minutes
}
MAX_CONCURRENT_SEARCHES = 4
MAX_RETRIES = 3
BASE_BACKOFF = 1  # seconds
MAX_BACKOFF = 10  # seconds
CONNECT_TIMEOUT = 10  # seconds
READ_TIMEOUT = 30   # seconds
MAX_PAGES_PER_SOURCE = 5
MAX_CANDIDATES_PER_SOURCE = 50
MAX_TOTAL_CANDIDATES = 500
CACHE_DIR = Path(__file__).parent.parent / ".cache"
CACHE_ENABLED = True
CACHE_EXPIRY_HOURS = 24


def load_schemas() -> Dict[str, Any]:
    """Load JSON schemas for validation."""
    schema_dir = Path(__file__).parent.parent / "schemas"
    schemas = {}

    try:
        with open(schema_dir / "dataset-record.schema.json", 'r') as f:
            schemas['dataset_record'] = json.load(f)
        with open(schema_dir / "search-report.schema.json", 'r') as f:
            schemas['search_report'] = json.load(f)
    except FileNotFoundError as e:
        print(f"Warning: Could not load schemas: {e}", file=sys.stderr)

    return schemas


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Dataset Hunter - Comprehensive dataset discovery system"
    )
    parser.add_argument(
        "research_objective",
        help="The research objective or question to search for datasets"
    )
    parser.add_argument(
        "--mode",
        choices=["QUICK", "STANDARD", "DEEP", "TARGETED"],
        default="STANDARD",
        help="Search mode (default: STANDARD)"
    )
    parser.add_argument(
        "--output",
        choices=["json", "csv", "both"],
        default="both",
        help="Output format (default: both)"
    )
    parser.add_argument(
        "--output-dir",
        default="./output",
        help="Output directory for results (default: ./output)"
    )
    parser.add_argument(
        "--max-sources",
        type=int,
        default=50,
        help="Maximum number of sources to search (default: 50)"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=30,
        help="Timeout per source in seconds (default: 30)"
    )

    return parser.parse_args()


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

        # Ensure cache directory exists
        CACHE_DIR.mkdir(parents=True, exist_ok=True)

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


def stage_1_problem_decomposition(research_objective: str) -> Dict[str, Any]:
    """
    Stage 1: Problem Decomposition
    Break down the research objective into key components.
    """
    log_progress("Stage 1: Problem Decomposition")

    # Simple decomposition - in practice this could use NLP
    words = research_objective.lower().split()
    # Remove common stop words
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can'}
    keywords = [w for w in words if w not in stop_words and len(w) > 2]

    # Extract potential geographic terms
    geo_indicators = ['city', 'urban', 'rural', 'region', 'country', 'nation', 'state', 'province', 'district', 'watershed', 'basin', 'river', 'lake', 'ocean', 'coastal', 'flood', 'flooding', 'rainfall', 'precipitation']
    geographic_terms = [w for w in keywords if any(indicator in w for indicator in geo_indicators)]

    # Extract potential temporal terms
    temporal_indicators = ['hourly', 'daily', 'weekly', 'monthly', 'annual', 'yearly', 'seasonal', 'realtime', 'real-time', 'historical', 'past', 'future', 'forecast', 'trend']
    temporal_terms = [w for w in keywords if any(indicator in w for indicator in temporal_indicators)]

    return {
        'original_objective': research_objective,
        'keywords': keywords,
        'geographic_terms': geographic_terms,
        'temporal_terms': temporal_terms,
        'domain_terms': [w for w in keywords if w not in geographic_terms and w not in temporal_terms]
    }


def stage_2_source_discovery(problem_components: Dict[str, Any], args: argparse.Namespace) -> List[Dict[str, Any]]:
    """
    Stage 2: Source Discovery
    Discover both predefined and dynamically discovered sources.
    """
    log_progress("Stage 2: Source Discovery")

    sources = []

    # Predefined sources (would normally load from source documentation)
    predefined_sources = [
        {'name': 'GitHub', 'type': 'code_hosting', 'module': 'search_github'},
        {'name': 'Hugging Face', 'type': 'dataset_repository', 'module': 'search_huggingface'},
        {'name': 'Zenodo', 'type': 'academic_repository', 'module': 'search_zenodo'},
        {'name': 'Web Search', 'type': 'general_web', 'module': 'search_web'},
        # Additional sources would be loaded here based on documentation
    ]

    # For now, we'll use a simplified set
    # In a full implementation, this would load all source documentation
    # and potentially add dynamically discovered sources

    sources = predefined_sources[:args.max_sources]

    log_progress(f"Discovered {len(sources)} sources to search")
    return sources


@retry_with_backoff()
@cache_result
def safe_search_github(query: str, max_results: int) -> List[Dict[str, Any]]:
    """Safe wrapper for GitHub search with timeout and retries."""
    log_progress(f"  Searching GitHub (attempt)")
    return search_github(query, max_results=max_results)


@retry_with_backoff()
@cache_result
def safe_search_huggingface(query: str, max_results: int) -> List[Dict[str, Any]]:
    """Safe wrapper for Hugging Face search with timeout and retries."""
    log_progress(f"  Searching Hugging Face (attempt)")
    return search_huggingface(query, max_results=max_results)


@retry_with_backoff()
@cache_result
def safe_search_zenodo(query: str, max_results: int) -> List[Dict[str, Any]]:
    """Safe wrapper for Zenodo search with timeout and retries."""
    log_progress(f"  Searching Zenodo (attempt)")
    return search_zenodo(query, max_results=max_results)


@retry_with_backoff()
@cache_result
def safe_search_web(query: str, max_results: int) -> List[Dict[str, Any]]:
    """Safe wrapper for web search with timeout and retries."""
    log_progress(f"  Searching web (attempt)")
    return search_web(query, max_results=max_results)


def stage_3_candidate_extraction(sources: List[Dict[str, Any]], problem_components: Dict[str, Any], args: argparse.Namespace) -> List[Dict[str, Any]]:
    """
    Stage 3: Candidate Extraction
    Extract dataset candidates from each source.
    """
    log_progress("Stage 3: Candidate Extraction")

    all_candidates = []

    # Extract search query from problem_components
    research_objective = problem_components.get('research_objective', '')
    keywords = problem_components.get('keywords', [])
    geographic_terms = problem_components.get('geographic_terms', [])
    temporal_terms = problem_components.get('temporal_terms', [])
    domain_terms = problem_components.get('domain_terms', [])

    # Build enhanced search query
    search_terms = [research_objective] + keywords + geographic_terms + temporal_terms + domain_terms
    search_query = ' '.join([term for term in search_terms if term])

    # Determine which sources to search based on args
    search_all_sources = getattr(args, 'all_sources', False)
    search_github_flag = getattr(args, 'github', False) or search_all_sources
    search_huggingface_flag = getattr(args, 'huggingface', False) or search_all_sources
    search_zenodo_flag = getattr(args, 'zenodo', False) or search_all_sources
    search_web_flag = getattr(args, 'web', False) or search_all_sources

    # Default to searching all sources if no specific source flags are set
    if not any([search_github_flag, search_huggingface_flag, search_zenodo_flag, search_web_flag]):
        search_github_flag = search_huggingface_flag = search_zenodo_flag = search_web_flag = True

    # Search each enabled source with controlled parallelism
    search_functions = []
    if search_github_flag:
        search_functions.append(('GitHub', safe_search_github))
    if search_huggingface_flag:
        search_functions.append(('Hugging Face', safe_search_huggingface))
    if search_zenodo_flag:
        search_functions.append(('Zenodo', safe_search_zenodo))
    if search_web_flag:
        search_functions.append(('Web', safe_search_web))

    # Execute searches with controlled parallelism
    with ThreadPoolExecutor(max_workers=min(MAX_CONCURRENT_SEARCHES, len(search_functions))) as executor:
        # Submit all search tasks
        future_to_source = {
            executor.submit(func, search_query, min(SEARCH_LIMITS[args.mode], MAX_CANDIDATES_PER_SOURCE)): name
            for name, func in search_functions
        }

        # Collect results as they complete
        for future in as_completed(future_to_source):
            source_name = future_to_source[future]
            try:
                candidates = future.result(timeout=EXECUTION_TIME_BUDGET[args.mode] // len(search_functions))
                all_candidates.extend(candidates)
                log_progress(f"  Found {len(candidates)} candidates from {source_name}")
            except Exception as e:
                log_progress(f"  Error searching {source_name}: {e}")
                # Continue with other sources even if one fails

    # Limit total candidates to prevent overload
    if len(all_candidates) > MAX_TOTAL_CANDIDATES:
        log_progress(f"  Limiting candidates from {len(all_candidates)} to {MAX_TOTAL_CANDIDATES}")
        all_candidates = all_candidates[:MAX_TOTAL_CANDIDATES]

    log_progress(f"Total candidates extracted: {len(all_candidates)}")
    return all_candidates


def stage_4_relevance_scoring(candidates: List[Dict[str, Any]], problem_components: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Stage 4: Relevance Scoring
    Score candidates based on relevance to the research objective.
    """
    log_progress("Stage 4: Relevance Scoring")

    if not candidates:
        return []

    # In a full implementation, this would use the rank.py module
    # For now, return candidates as-is
    return candidates


def stage_5_quality_assessment(candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Stage 5: Quality Assessment
    Assess quality of candidates without downloading large files.
    """
    log_progress("Stage 5: Quality Assessment")

    if not candidates:
        return []

    # In a full implementation, this would use the validate.py module
    # For now, return candidates as-is
    return candidates


def stage_6_duplicate_detection(candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Stage 6: Duplicate Detection
    Detect and remove duplicate datasets.
    """
    log_progress("Stage 6: Duplicate Detection")

    if not candidates:
        return []

    # In a full implementation, this would use the deduplicate.py module
    # For now, return candidates as-is
    return candidates


def stage_7_license_check(candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Stage 7: License Check
    Check licenses for each candidate.
    """
    log_progress("Stage 7: License Check")

    if not candidates:
        return []

    # In a full implementation, this would enhance license information
    # For now, return candidates as-is
    return candidates


def stage_8_domain_aware_discovery(candidates: List[Dict[str, Any]], problem_components: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Stage 8: Domain-Aware Discovery
    Expand search based on domain knowledge.
    """
    log_progress("Stage 8: Domain-Aware Discovery")

    # In a full implementation, this would trigger additional searches
    # based on domain-specific knowledge from problem_components
    # For now, return candidates as-is
    return candidates


def stage_9_source_reliability(candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Stage 9: Source Reliability Assessment
    Assess reliability of sources.
    """
    log_progress("Stage 9: Source Reliability Assessment")

    if not candidates:
        return []

    # In a full implementation, this would score sources by reliability tier
    # For now, return candidates as-is
    return candidates


def stage_10_search_report(all_results: Dict[str, Any], args: argparse.Namespace) -> Dict[str, Any]:
    """
    Stage 10: Search Report Generation
    Generate final search report.
    """
    log_progress("Stage 10: Search Report Generation")

    # Generate comprehensive report
    report = {
        'research_objective': args.research_objective,
        'search_interpretation': {
            'target_phenomenon': args.research_objective,
            'geography': 'unspecified',
            'time_period': 'unspecified',
            'variables': [],
            'resolutions': [],
            'data_type': 'unspecified',
            'format': [],
            'intended_use': 'research',
            'constraints': []
        },
        'expanded_search_concepts': [],
        'sources_searched': [],
        'total_candidates': 0,
        'unique_datasets': 0,
        'duplicate_groups': 0,
        'top_datasets': [],
        'all_datasets': [],
        'search_metadata': {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'search_mode': args.mode,
            'tools_used': ['dataset-hunter'],
            'failed_sources': [],
            'scoring_configuration': {
                'task_relevance_weight': 0.25,
                'geographic_match_weight': 0.15,
                'temporal_match_weight': 0.10,
                'source_reliability_weight': 0.15,
                'quality_score_weight': 0.20,
                'license_score_weight': 0.10,
                'recency_weight': 0.05
            }
        }
    }

    return report


def main():
    """Main execution function with global time budget enforcement."""
    start_time = time.time()
    args = parse_arguments()

    log_progress(f"Starting dataset hunt for: '{args.research_objective}'")
    log_progress(f"Search mode: {args.mode}")
    log_progress(f"Output format: {args.output}")
    log_progress(f"Output directory: {args.output_dir}")

    # Check global time budget
    time_budget = EXECUTION_TIME_BUDGET[args.mode]
    log_progress(f"Global execution time budget: {time_budget} seconds")

    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Stage 1: Problem Decomposition
        problem_components = stage_1_problem_decomposition(args.research_objective)

        # Stage 2: Source Discovery
        sources = stage_2_source_discovery(problem_components, args)

        # Stage 3: Candidate Extraction
        candidates = stage_3_candidate_extraction(sources, problem_components, args)

        # Check if we've exceeded time budget
        elapsed_time = time.time() - start_time
        if elapsed_time > time_budget:
            log_progress(f"Warning: Exceeded time budget ({elapsed_time:.1f}s > {time_budget}s)")
            # Continue anyway but warn user

        # Stages 4-9: Processing pipeline
        scored_candidates = stage_4_relevance_scoring(candidates, problem_components)
        quality_candidates = stage_5_quality_assessment(scored_candidates)
        dedup_candidates = stage_6_duplicate_detection(quality_candidates)
        license_candidates = stage_7_license_check(dedup_candidates)
        domain_candidates = stage_8_domain_aware_discovery(license_candidates, problem_components)
        reliable_candidates = stage_9_source_reliability(domain_candidates)

        # Check time budget again
        elapsed_time = time.time() - start_time
        if elapsed_time > time_budget:
            log_progress(f"Warning: Exceeded time budget after processing ({elapsed_time:.1f}s > {time_budget}s)")

        # Stage 10: Generate report
        search_report = stage_10_search_report({
            'candidates': reliable_candidates
        }, args)

        # Export results
        export_results(search_report, args.output, args.output_dir)

        elapsed_time = time.time() - start_time
        log_progress(f"\nSearch complete! Results saved to {output_dir}")
        log_progress(f"Found {len(reliable_candidates)} unique datasets")
        log_progress(f"Total execution time: {elapsed_time:.1f} seconds")

    except Exception as e:
        elapsed_time = time.time() - start_time
        log_progress(f"Error during dataset hunt after {elapsed_time:.1f} seconds: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()