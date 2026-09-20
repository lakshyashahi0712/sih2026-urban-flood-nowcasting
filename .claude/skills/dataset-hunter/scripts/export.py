#!/usr/bin/env python3
"""
Export module for dataset-hunter skill.
Exports search results to JSON/CSV formats.
"""

import json
import csv
import os
from typing import Dict, Any
from pathlib import Path


def export_results(search_report: Dict[str, Any], output_format: str, output_dir: str) -> None:
    """
    Export search results to JSON and/or CSV formats.

    Args:
        search_report: The search report dictionary from stage 10
        output_format: 'json', 'csv', or 'both'
        output_dir: Directory to save output files
    """
    print(f"Exporting results in {output_format} format to {output_dir}")

    # Create output directory if it doesn't exist
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Export JSON
    if output_format in ['json', 'both']:
        json_file = output_path / "search_report.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(search_report, f, indent=2, ensure_ascii=False)
        print(f"JSON report saved to {json_file}")

    # Export CSV
    if output_format in ['csv', 'both']:
        csv_file = output_path / "datasets.csv"
        # Extract datasets from the report
        datasets = search_report.get('all_datasets', [])
        if not datasets:
            # Fallback to top datasets if all_datasets not available
            datasets = search_report.get('top_datasets', [])

        if datasets:
            # Flatten the dataset data for CSV
            flattened_data = []
            for dataset in datasets:
                flat_dataset = {
                    'dataset_name': dataset.get('dataset_name', ''),
                    'source': dataset.get('source', ''),
                    'organization': dataset.get('organization', ''),
                    'description': dataset.get('description', ''),
                    'url': dataset.get('url', ''),
                    'variables': '; '.join(dataset.get('variables', [])),
                    'geographic_mentions': '; '.join(dataset.get('geographic_coverage', {}).get('mentions', [])),
                    'temporal_mentions': '; '.join(dataset.get('temporal_coverage', {}).get('mentions', [])),
                    'file_formats': '; '.join(dataset.get('file_formats', [])),
                    'license': dataset.get('license', ''),
                    'access_method': dataset.get('access_method', ''),
                    'cost': dataset.get('cost', ''),
                    'relevance_score': dataset.get('final_relevance_score', dataset.get('relevance_score', 0)),
                    'quality_score': dataset.get('quality_score', 0),
                    'source_reliability': dataset.get('source_reliability', ''),
                    'discovery_timestamp': dataset.get('discovery_timestamp', '')
                }
                flattened_data.append(flat_dataset)

            # Write CSV
            if flattened_data:
                fieldnames = flattened_data[0].keys()
                with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(flattened_data)
                print(f"CSV report saved to {csv_file}")
            else:
                print("No dataset data to export to CSV")
        else:
            print("No datasets found to export to CSV")


if __name__ == "__main__":
    # Test the function
    import sys
    import json
    if len(sys.argv) > 1:
        # For testing, we'd load a JSON file
        print("Usage: python export.py < input.json > output.csv")
        print("Or import and use export_results() function")
    else:
        print("Export module for dataset-hunter skill")
        print("Provides export_results() function to export search results")