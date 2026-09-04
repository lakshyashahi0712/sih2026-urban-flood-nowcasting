"""Tests for the flood routing model (Phase 1.0)."""
from __future__ import annotations

import numpy as np
import pytest

from app.domain.flood.routing import (
    FloodResult,
    route_flood_depth,
    compute_flood_statistics
)


def test_zero_excess_zero_flood_depth():
    """Zero excess runoff should produce zero flood depth everywhere."""
    flow_dir = np.array([[0, 0], [0, 0]], dtype=np.uint8)  # all sinks
    excess_runoff = {}  # no excess
    cell_size = 10.0  # 10m cells

    result = route_flood_depth(excess_runoff, flow_dir, cell_size)

    assert np.all(result.flood_depth_m == 0.0)
    assert not np.any(result.flooded_mask)
    assert result.max_depth_m == 0.0
    assert result.total_flooded_area_m2 == 0.0
    assert result.total_flood_volume_m3 == 0.0
    assert result.provenance == "MODELLED/DERIVED"


def test_known_volume_known_area_expected_depth():
    """Known volume over known cell area should produce expected depth."""
    # 1x1 grid, single cell receiving excess
    flow_dir = np.array([[0]], dtype=np.uint8)  # sink
    excess_runoff = {(0, 0): 10.0}  # 10 m³ excess
    cell_size = 5.0  # 5m cells -> 25 m² area

    result = route_flood_depth(excess_runoff, flow_dir, cell_size)

    expected_depth = 10.0 / (5.0 * 5.0)  # volume / area = 10/25 = 0.4 m
    assert result.flood_depth_m[0, 0] == expected_depth
    assert result.flooded_mask[0, 0] == True
    assert result.max_depth_m == expected_depth
    assert result.total_flooded_area_m2 == 25.0  # 1 cell * 25 m²
    assert result.total_flood_volume_m3 == 10.0  # volume conserved


def test_excess_routed_downstream():
    """Excess should flow downstream following D8 directions."""
    # 2x1 grid: top cell flows to bottom cell
    flow_dir = np.array([[4], [0]], dtype=np.uint8)  # top flows S (4), bottom is sink (0)
    excess_runoff = {(0, 0): 20.0}  # 20 m³ excess at top
    cell_size = 10.0  # 10m cells -> 100 m² area

    result = route_flood_depth(excess_runoff, flow_dir, cell_size)

    # All water should flow to bottom cell
    assert result.flood_depth_m[0, 0] == 0.0  # top cell dry
    assert result.flood_depth_m[1, 0] == 20.0 / 100.0  # bottom cell gets all water
    assert result.flooded_mask[0, 0] == False
    assert result.flooded_mask[1, 0] == True
    assert result.total_flood_volume_m3 == 20.0  # volume conserved


def test_ponding_when_no_downstream():
    """Water should pond when no lower valid downstream cell exists."""
    # Single sink cell - water should pond where it falls
    flow_dir = np.array([[0]], dtype=np.uint8)  # sink
    excess_runoff = {(0, 0): 15.0}  # 15 m³ excess
    cell_size = 3.0  # 3m cells -> 9 m² area

    result = route_flood_depth(excess_runoff, flow_dir, cell_size)

    # Water should pond in place
    expected_depth = 15.0 / 9.0
    assert result.flood_depth_m[0, 0] == expected_depth
    assert result.flooded_mask[0, 0] == True
    assert result.total_flood_volume_m3 == 15.0  # volume conserved


def test_nodata_cells_excluded():
    """Nodata cells should be excluded from flow and flooding."""
    # 2x2 grid with nodata in bottom right
    flow_dir = np.array([
        [4, 1],   # top row: left flows S, right flows E
        [0, 0]    # bottom row: both sinks
    ], dtype=np.uint8)
    nodata_mask = np.array([
        [False, False],
        [False, True]   # bottom right is nodata
    ])
    excess_runoff = {(0, 0): 12.0}  # excess at top left
    cell_size = 2.0  # 2m cells -> 4 m² area

    result = route_flood_depth(excess_runoff, flow_dir, cell_size, nodata_mask)

    # Water from top left should flow down to bottom left (not right, as that path hits nodata)
    assert result.flood_depth_m[0, 0] == 0.0  # source cell empty after routing
    assert result.flood_depth_m[1, 0] == 12.0 / 4.0  # bottom left gets water
    assert result.flood_depth_m[0, 1] == 0.0  # top right dry (no inflow)
    assert result.flood_depth_m[1, 1] == 0.0  # nodata cell remains dry
    assert not result.flooded_mask[1, 1]  # nodata not counted as flooded
    assert result.total_flood_volume_m3 == 12.0  # volume conserved


def test_multiple_sources_conserve_volume():
    """Multiple source cells should conserve total water volume."""
    # 2x2 grid, all flowing to bottom right sink
    flow_dir = np.array([
        [4, 8],   # top row: left flows S (4), right flows SW (8)
        [1, 0]    # bottom row: left flows E (1), right is sink (0)
    ], dtype=np.uint8)
    excess_runoff = {
        (0, 0): 5.0,   # top left flows to [1,0]
        (0, 1): 3.0,   # top right flows to [1,0] (SW from [0,1] -> [1,0])
        (1, 0): 2.0    # bottom left flows to [1,1]
    }  # total excess = 10.0 m³
    cell_size = 1.0  # 1m cells -> 1 m² area

    result = route_flood_depth(excess_runoff, flow_dir, cell_size)

    # All water should end up in bottom right sink
    assert result.flood_depth_m[1, 1] == 10.0  # 10 m³ / 1 m² per cell = 10 m depth
    assert result.total_flood_volume_m3 == 10.0  # volume conserved
    assert result.total_flooded_area_m2 == 1.0  # only one cell flooded


def test_flooded_mask_threshold():
    """Flooded mask should respect the threshold parameter."""
    flow_dir = np.array([[0]], dtype=np.uint8)  # sink
    excess_runoff = {(0, 0): 0.1}  # small excess
    cell_size = 1.0  # 1m cells -> 1 m² area

    # With default threshold (0.001m), 0.1m depth should be flooded
    result_default = route_flood_depth(excess_runoff, flow_dir, cell_size)
    assert result_default.flooded_mask[0, 0] == True

    # With high threshold (0.2m), 0.1m depth should NOT be flooded
    result_high_thresh = route_flood_depth(excess_runoff, flow_dir, cell_size, threshold_m=0.2)
    assert result_high_thresh.flooded_mask[0, 0] == False
    assert result_high_thresh.flood_depth_m[0, 0] == 0.1  # depth still computed
    assert result_high_thresh.total_flooded_area_m2 == 0.0
    assert result_high_thresh.total_flood_volume_m3 == 0.1  # volume still present but not "flooded"


def test_deterministic_output():
    """Same inputs should produce same outputs."""
    flow_dir = np.array([[4, 0], [0, 0]], dtype=np.uint8)
    excess_runoff = {(0, 0): 7.5, (0, 1): 2.5}
    cell_size = 5.0

    result1 = route_flood_depth(excess_runoff, flow_dir, cell_size)
    result2 = route_flood_depth(excess_runoff, flow_dir, cell_size)

    assert np.array_equal(result1.flood_depth_m, result2.flood_depth_m)
    assert np.array_equal(result1.flooded_mask, result2.flooded_mask)
    assert result1.max_depth_m == result2.max_depth_m
    assert result1.total_flooded_area_m2 == result2.total_flooded_area_m2
    assert result1.total_flood_volume_m3 == result2.total_flood_volume_m3


def test_total_flooded_area_calculation():
    """Total flooded area should be computed correctly."""
    # 3x3 grid, various depths
    flow_dir = np.array([[0, 0, 0], [0, 0, 0], [0, 0, 0]], dtype=np.uint8)  # all sinks
    excess_runoff = {
        (0, 0): 2.0,  # 2 m³
        (1, 1): 3.0,  # 3 m³
        (2, 2): 0.0   # 0 m³ (not flooded)
    }
    cell_size = 2.0  # 2m cells -> 4 m² area

    result = route_flood_depth(excess_runoff, flow_dir, cell_size, threshold_m=0.001)

    # Cells (0,0) and (1,1) should be flooded, (2,2) not
    expected_depth_00 = 2.0 / 4.0  # 0.5 m
    expected_depth_11 = 3.0 / 4.0  # 0.75 m
    expected_depth_22 = 0.0 / 4.0  # 0.0 m

    assert result.flood_depth_m[0, 0] == expected_depth_00
    assert result.flood_depth_m[1, 1] == expected_depth_11
    assert result.flood_depth_m[2, 2] == expected_depth_22

    assert result.flooded_mask[0, 0] == True
    assert result.flooded_mask[1, 1] == True
    assert result.flooded_mask[2, 2] == False

    # Total flooded area = 2 cells * 4 m²/cell = 8 m²
    assert result.total_flooded_area_m2 == 8.0
    # Total volume = 2.0 + 3.0 + 0.0 = 5.0 m³
    assert result.total_flood_volume_m3 == 5.0


def test_total_flood_volume_calculation():
    """Total flood volume should be computed correctly."""
    flow_dir = np.array([[0]], dtype=np.uint8)  # sink
    excess_runoff = {(0, 0): 7.25}  # 7.25 m³ excess
    cell_size = 1.5  # 1.5m cells -> 2.25 m² area

    result = route_flood_depth(excess_runoff, flow_dir, cell_size)

    # Volume should be conserved exactly
    assert result.total_flood_volume_m3 == 7.25
    # Depth = volume / area = 7.25 / 2.25
    expected_depth = 7.25 / (1.5 * 1.5)
    assert result.flood_depth_m[0, 0] == expected_depth


def test_compute_flood_statistics():
    """Additional statistics computation should work."""
    flow_dir = np.array([[0, 0], [0, 0]], dtype=np.uint8)  # all sinks
    excess_runoff = {(0, 0): 4.0, (0, 1): 8.0, (1, 0): 0.0, (1, 1): 12.0}
    cell_size = 2.0  # 2m cells -> 4 m² area

    result = route_flood_depth(excess_runoff, flow_dir, cell_size)
    stats = compute_flood_statistics(result)

    # Depths: [1.0, 2.0, 0.0, 3.0] m (4.0/4, 8.0/4, 0.0/4, 12.0/4)
    flooded_depths = [1.0, 2.0, 3.0]  # exclude the 0.0 depth cell
    assert stats["mean_depth_m"] == np.mean(flooded_depths)
    assert stats["std_depth_m"] == np.std(flooded_depths)
    assert stats["depth_90th_percentile_m"] == np.percentile(flooded_depths, 90)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])