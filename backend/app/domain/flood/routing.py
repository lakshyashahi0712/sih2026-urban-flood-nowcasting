"""Surface flood routing model for converting excess runoff to flood depth.

This MVP model routes excess water along D8 flow directions and computes
flood depth using simple volume-to-depth conversion.
"""
from __future__ import annotations

import numpy as np
from typing import Dict, Tuple, Optional
from dataclasses import dataclass

from backend.app.domain.drainage.models import Provenance


@dataclass
class FloodResult:
    """Results from flood routing computation."""
    flood_depth_m: np.ndarray  # Flood depth in meters for each cell
    flooded_mask: np.ndarray   # Boolean mask where flood depth > 0
    max_depth_m: float         # Maximum flood depth in meters
    total_flooded_area_m2: float  # Total area of flooded cells (m²)
    total_flood_volume_m3: float  # Total volume of flood water (m³)
    provenance: str            # Source of the flood depth calculation


def route_flood_depth(
    excess_runoff_m3: Dict[Tuple[int, int], float],
    flow_direction: np.ndarray,
    cell_size_m: float,
    nodata_mask: Optional[np.ndarray] = None,
    threshold_m: float = 0.001
) -> FloodResult:
    """Route excess runoff over the DEM surface using D8 flow directions.

    Args:
        excess_runoff_m3: Dictionary mapping (row, col) to excess volume (m³) from drainage surcharge
        flow_direction: D8 flow direction array (0 for sink/no flow, powers of 2 for directions)
        cell_size_m: Size of grid cell in meters (assuming square cells)
        nodata_mask: Boolean mask where True indicates nodata/invalid cells (default: None)
        threshold_m: Minimum depth to consider as flooded (meters) (default: 0.001m = 1mm)

    Returns:
        FloodResult containing flood depth map and summary statistics

    Assumptions:
        - Water flows only to the single steepest downstream neighbor (D8)
        - No infiltration, evaporation, or transmission losses during routing
        - Instantaneous equilibrium state (no temporal dynamics)
        - Rectangular grid cells with uniform size
        - Water ponds where no lower valid downstream neighbor exists
        - Nodata cells are excluded from flow and flooding
        - Conservation of mass: total input volume = total output volume (within numerical precision)
    """
    if flow_direction.size == 0:
        raise ValueError("Flow direction array cannot be empty")

    height, width = flow_direction.shape

    # Initialize flood depth array (meters)
    flood_depth = np.zeros((height, width), dtype=np.float64)

    # Set up nodata mask
    if nodata_mask is None:
        nodata_mask = np.zeros((height, width), dtype=bool)
    elif nodata_mask.shape != (height, width):
        raise ValueError("nodata_mask must have same shape as flow_direction")

    # Cell area for depth conversion
    cell_area_m2 = cell_size_m * cell_size_m

    # D8 direction mappings (matching RasterEngine)
    D8_DIRS = {
        'E': 1,   # (0, 1)
        'SE': 2,  # (1, 1)
        'S': 4,   # (1, 0)
        'SW': 8,  # (1, -1)
        'W': 16,  # (0, -1)
        'NW': 32, # (-1, -1)
        'N': 64,  # (-1, 0)
        'NE': 128,# (-1, 1)
    }
    D8_DIRS_REV = {v: k for k, v in D8_DIRS.items()}
    D8_OFFSETS = {
        'E': (0, 1),
        'SE': (1, 1),
        'S': (1, 0),
        'SW': (1, -1),
        'W': (0, -1),
        'NW': (-1, -1),
        'N': (-1, 0),
        'NE': (-1, 1),
    }

    # Distances for each D8 direction (for slope calculation, though not used in this MVP)
    D8_DISTANCE = {
        'E': 1.0, 'SE': np.sqrt(2), 'S': 1.0, 'SW': np.sqrt(2),
        'W': 1.0, 'NW': np.sqrt(2), 'N': 1.0, 'NE': np.sqrt(2)
    }

    # Helper to check if a cell is valid (in bounds and not nodata)
    def is_valid_cell(r: int, c: int) -> bool:
        return (0 <= r < height and 0 <= c < width and not nodata_mask[r, c])

    # Helper to get downstream neighbor coordinates
    def get_downstream(r: int, c: int) -> Optional[Tuple[int, int]]:
        dir_val = flow_direction[r, c]
        if dir_val == 0:  # sink/no flow
            return None
        dir_name = D8_DIRS_REV.get(dir_val)
        if dir_name is None:
            return None
        dr, dc = D8_OFFSETS[dir_name]
        nr, nc = r + dr, c + dc
        if is_valid_cell(nr, nc):
            return (nr, nc)
        return None

    # Step 1: Initialize depth from direct excess input (volume -> depth)
    for (r, c), volume_m3 in excess_runoff_m3.items():
        if is_valid_cell(r, c):
            # Convert volume to depth: depth = volume / area
            flood_depth[r, c] += volume_m3 / cell_area_m2

    # Step 2: Route water downstream until equilibrium
    # We'll use a simple iterative approach: repeatedly move water downstream
    # until no more movement occurs (or max iterations reached)
    max_iterations = height * width * 2  # conservative upper bound
    for iteration in range(max_iterations):
        # Create array to track water movement this iteration
        depth_change = np.zeros((height, width), dtype=np.float64)
        moved_any = False

        # Process each cell
        for r in range(height):
            for c in range(width):
                if not is_valid_cell(r, c):
                    continue

                current_depth = flood_depth[r, c]
                if current_depth <= threshold_m:
                    continue  # insignificant depth, skip

                # Get downstream neighbor
                downstream = get_downstream(r, c)
                if downstream is None:
                    # No valid downstream - water ponds here
                    continue

                nr, nc = downstream
                # Move all water downstream (simple instantaneous routing)
                depth_change[r, c] -= current_depth
                depth_change[nr, nc] += current_depth
                moved_any = True

        # Apply depth changes
        flood_depth += depth_change

        # Ensure no negative depths (shouldn't happen with our logic, but safety)
        flood_depth = np.maximum(flood_depth, 0.0)

        # If no water moved this iteration, we've reached equilibrium
        if not moved_any:
            break
    else:
        # If we exhausted iterations without convergence, warn but continue
        pass  # In MVP, we accept this limitation

    # Step 3: Compute results
    flooded_mask = flood_depth > threshold_m
    max_depth_m = np.max(flood_depth) if np.any(flooded_mask) else 0.0
    total_flooded_area_m2 = np.sum(flooded_mask) * cell_area_m2
    total_flood_volume_m3 = np.sum(flood_depth) * cell_area_m2

    return FloodResult(
        flood_depth_m=flood_depth,
        flooded_mask=flooded_mask,
        max_depth_m=float(max_depth_m),
        total_flooded_area_m2=float(total_flooded_area_m2),
        total_flood_volume_m3=float(total_flood_volume_m3),
        provenance="MODELLED/DERIVED"
    )


def compute_flood_statistics(flood_result: FloodResult) -> Dict[str, float]:
    """Compute additional statistics from flood result.

    Args:
        flood_result: FloodResult from route_flood_depth

    Returns:
        Dictionary with additional computed statistics
    """
    return {
        "mean_depth_m": float(np.mean(flood_result.flood_depth_m[flood_result.flooded_mask]))
                       if np.any(flood_result.flooded_mask) else 0.0,
        "std_depth_m": float(np.std(flood_result.flood_depth_m[flood_result.flooded_mask]))
                      if np.any(flood_result.flooded_mask) else 0.0,
        "depth_90th_percentile_m": float(np.percentile(flood_result.flood_depth_m[flood_result.flooded_mask], 90))
                                  if np.any(flood_result.flooded_mask) else 0.0,
    }


__all__ = [
    "FloodResult",
    "route_flood_depth",
    "compute_flood_statistics"
]