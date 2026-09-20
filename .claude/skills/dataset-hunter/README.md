# Dataset Hunter Skill

A reusable research/data-acquisition skill for discovering publicly accessible datasets across the web.

## Features

- Searches across 18+ source categories including Hugging Face, Kaggle, GitHub, Zenodo, government portals, scientific repositories, and more
- 10-stage discovery pipeline for thorough dataset reconnaissance
- Automatic query expansion based on domain understanding
- Relevance scoring (0-100) with explainable weights
- Duplicate detection across platforms
- License and accessibility verification
- Quality assessment without downloading large datasets
- Machine-readable output (JSON/CSV) and human-readable reports
- Configurable search modes (QUICK, STANDARD, DEEP, TARGETED)

## Installation

The skill is automatically available in Claude Code when placed in `.claude/skills/dataset-hunter/`.

## Usage

Invoke the skill with natural language requests:

```
Find datasets for urban flood nowcasting in Mumbai.
```

```
Find all publicly available rainfall datasets for Delhi from 2010 onward.
```

```
Find high-resolution drainage datasets for Indian cities.
```

```
Search the web for datasets containing rainfall, water level and flood extent.
```

## Output

The skill generates:
- Human-readable reconnaissance report
- Machine-readable dataset catalog (JSON and CSV formats)
- Source reliability assessment
- Failure reports for sources that couldn't be searched

## Modes

- **QUICK**: Fast discovery of likely datasets
- **STANDARD**: Multiple source categories + ranking (default)
- **DEEP**: Broad multi-pass reconnaissance with expansion
- **TARGETED**: Focus on specified variable/source/geography

## Source Categories

1. Primary repositories (Hugging Face, Kaggle, Zenodo, UCI, data.gov.in)
2. Scientific repositories (NASA, NOAA, ESA, Copernicus, USGS)
3. Code/repository sources (GitHub, GitLab, Bitbucket)
4. Academic sources (papers, supplementary material, institutional repositories)
5. Web discovery (CSV, XLSX, JSON, GeoJSON, Shapefile, GeoTIFF, NetCDF, Parquet, HDF5, APIs)

## Example

For urban flood nowcasting in Mumbai, Delhi, and Chennai:
```
Find datasets for an operational urban flood nowcasting system for Mumbai, Delhi and Chennai.
```

The skill automatically expands to search for rainfall, precipitation, water level, flood depth, drainage networks, DEM, LiDAR, and other relevant variables.