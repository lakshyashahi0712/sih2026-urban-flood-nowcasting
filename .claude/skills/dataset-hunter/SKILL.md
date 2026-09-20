# Dataset Hunter Skill

A comprehensive dataset discovery and reconnaissance system for finding publicly accessible datasets across the web.

## Overview

This skill performs systematic dataset discovery across multiple sources including Hugging Face, Kaggle, GitHub, Zenodo, government portals, scientific repositories, academic sources, and web discovery. It implements a multi-stage pipeline for problem decomposition, source discovery, candidate extraction, relevance scoring, quality assessment, duplicate detection, license checking, and domain-aware discovery.

## Usage

Invoke this skill with natural language requests like:

- "Find datasets for urban flood nowcasting in Mumbai."
- "Find all publicly available rainfall datasets for Delhi from 2010 onward."
- "Find high-resolution drainage datasets for Indian cities."
- "Find datasets suitable for training a flood prediction model."
- "Search the web for datasets containing rainfall, water level and flood extent."
- "Find alternatives to this dataset."
- "Perform a complete dataset reconnaissance for my project."

## Modes

The skill supports different search modes:
- **QUICK**: Fast discovery of likely datasets
- **STANDARD**: Multiple source categories + ranking (default)
- **DEEP**: Broad multi-pass reconnaissance with source expansion, query expansion, repository discovery, academic discovery, duplicate detection, license inspection, and quality inspection
- **TARGETED**: Focus on a specified variable/source/geography

## Output

The skill produces:
- Human-readable reconnaissance report (Markdown)
- Machine-readable dataset catalog (JSON and CSV)
- Source reliability assessment
- Duplicate detection results
- License and accessibility classification
- Quality assessment for high-ranking datasets

## Implementation

The skill consists of:
- Source-specific search scripts (Python)
- Normalization and deduplication utilities
- Ranking and validation scripts
- Export functionality
- JSON schemas for dataset records and search reports
- Templates for reconnaissance reports

## Dependencies

- Python 3.7+
- Standard library modules (requests may be added if network access is available)
- No external dependencies required for basic operation

## Examples

See README.md for detailed usage examples.