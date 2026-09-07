"""Historical event replay engine for retrospective flood simulations.

IMPORTANT ENGINEERING & MODELING CLASSIFICATION:
This is a RETROSPECTIVE SIMULATION of an historical extreme flood event.
It is NOT a historical forecast and does NOT claim the model predicted the 2017 event.
It feeds verified historical rainfall forcing (SECONDARY-REPORT) and derived tidal boundary
levels (DERIVED) into the EXISTING production flood pipeline:
Rational Method Runoff -> BMC Hydraulic Propagation -> Coastal Outfall Backwater -> D8 Surface Routing.

Observed flood benchmarks are used strictly for post-simulation validation and are
never injected into the hydraulic pipeline.
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from zoneinfo import ZoneInfo
import numpy as np
import pyproj
from shapely.geometry import box, Polygon, MultiPolygon
from shapely.ops import unary_union
from pydantic import BaseModel, Field

try:
    from backend.app.config import settings
    from backend.app.domain.drainage.models import DrainageNetwork, NodeType, Provenance
    from backend.app.domain.drainage.capacity import (
        ChannelCapacity,
        compute_channel_capacity,
    )
    from backend.app.domain.drainage.propagation import (
        BoundarySourceType,
        DownstreamBoundaryCondition,
        NetworkPropagationTimestepResult,
        propagate_network_timestep,
    )
    from backend.app.domain.rainfall.runoff import RunoffVolume
    from backend.app.domain.flood.routing import route_flood_depth, FloodResult
    from backend.app.infrastructure.drainage.bmc_gis import BMCDrainageLoader
    from backend.app.infrastructure.drainage.raster_engine import RasterEngine
    from backend.app.domain.historical.models import (
        HistoricalBoundaryCondition,
        HistoricalEvent,
        HistoricalProvenance,
        HistoricalRainfallForcing,
        ObservedFloodBenchmark,
        assert_no_benchmark_leakage,
    )
    from backend.app.domain.roads.models import StreetFloodIntelligence
    from backend.app.domain.roads.spatial_matcher import match_flood_to_streets
except ImportError:
    from app.config import settings
    from app.domain.drainage.models import DrainageNetwork, NodeType, Provenance
    from app.domain.drainage.capacity import (
        ChannelCapacity,
        compute_channel_capacity,
    )
    from app.domain.drainage.propagation import (
        BoundarySourceType,
        DownstreamBoundaryCondition,
        NetworkPropagationTimestepResult,
        propagate_network_timestep,
    )
    from app.domain.rainfall.runoff import RunoffVolume
    from app.domain.flood.routing import route_flood_depth, FloodResult
    from app.infrastructure.drainage.bmc_gis import BMCDrainageLoader
    from app.infrastructure.drainage.raster_engine import RasterEngine
    from app.domain.historical.models import (
        HistoricalBoundaryCondition,
        HistoricalEvent,
        HistoricalProvenance,
        HistoricalRainfallForcing,
        ObservedFloodBenchmark,
        assert_no_benchmark_leakage,
    )
    from app.domain.roads.models import StreetFloodIntelligence
    from app.domain.roads.spatial_matcher import match_flood_to_streets

logger = logging.getLogger(__name__)
TZ_IST = ZoneInfo("Asia/Kolkata")


class HistoricalReplayTimestepState(BaseModel):
    """Result of an historical retrospective replay simulation for a single timestep."""
    event_id: str
    timestep_index: int
    replay_timestamp: datetime = Field(..., description="Timezone-aware timestamp (Asia/Kolkata)")
    rainfall_mm: float = Field(..., ge=0.0)
    rainfall_intensity_mm_per_hr: float = Field(..., ge=0.0)
    rainfall_provenance: HistoricalProvenance = Field(..., description="SECONDARY-REPORT for literature profile")
    boundary_level_m: float = Field(..., description="Tidal water level [m above Chart Datum]")
    boundary_provenance: HistoricalProvenance = Field(..., description="DERIVED for astronomical tide")
    peak_flood_depth_m: float = Field(..., ge=0.0)
    flooded_area_m2: float = Field(..., ge=0.0)
    flood_volume_m3: float = Field(..., ge=0.0)
    flooded_cell_count: int = Field(..., ge=0)
    drainage_surcharge_volume_m3: float = Field(..., ge=0.0)
    model_provenance: str = Field(default="RETROSPECTIVE_SIMULATION")
    geojson: Optional[Dict[str, Any]] = Field(default=None, description="Optional GeoJSON FeatureCollection for mapping")
    # Street flood risk intelligence for this timestep
    street_risk: Optional[StreetFloodIntelligence] = Field(default=None, description="Street and intersection flood risk assessment")


HistoricalReplayTimestepState.model_rebuild()


class BenchmarkValidationComparison(BaseModel):
    """Comparison of retrospective simulation output against an observed flood benchmark.

    Evaluated strictly AFTER replay execution. Benchmark data is NEVER used as model input.
    """
    location_id: str
    location_name: str
    observed_min_depth_m: float
    observed_max_depth_m: Optional[float] = None
    exact_cell_depth_m: Optional[float] = None
    matched_depth_m: Optional[float] = None
    match_method: str = Field(..., description="EXACT_CELL, NEIGHBORHOOD_BUFFER, or NONE")
    search_radius_m: float = Field(default=200.0, ge=0.0)
    matched_cell_distance_m: Optional[float] = None
    within_observed_range: bool
    absolute_difference_m: Optional[float] = None
    observed_provenance: HistoricalProvenance = HistoricalProvenance.OBSERVED
    modeled_provenance: str = "RETROSPECTIVE_SIMULATION"
    spatial_status: str = Field(..., description="MATCHED or OUTSIDE_PILOT_EXTENT")
    observed_depth_range: str = Field(default="", description="Canonical descriptor of observed depth range")
    minimum: float = Field(default=0.0, description="Minimum observed depth [m]")
    maximum: Optional[float] = Field(default=None, description="Maximum observed depth [m]")
    is_model_input: bool = Field(default=False, description="STRICT SAFEGUARD: Always False for validation benchmarks")
    notes: str = ""


class HistoricalReplaySummary(BaseModel):
    """Summary of the complete retrospective event replay simulation."""
    event_id: str
    event_name: str
    disclaimer: str = (
        "RETROSPECTIVE SIMULATION. Not an operational forecast or historical prediction. "
        "Driven by literature-calibrated rainfall (SECONDARY-REPORT) and astronomical tide (DERIVED)."
    )
    first_timestamp: datetime
    last_timestamp: datetime
    timestep_count: int
    peak_modeled_depth_m: float
    peak_flooded_area_m2: float
    peak_flood_volume_m3: float
    peak_surcharge_volume_m3: float
    timesteps: List[HistoricalReplayTimestepState]
    validation_comparisons: List[BenchmarkValidationComparison]


def compare_benchmarks_against_grid(
    benchmarks: List[ObservedFloodBenchmark],
    depth_grid: np.ndarray,
    engine: RasterEngine,
    search_radius_m: float = 200.0,
) -> List[BenchmarkValidationComparison]:
    """Compare observed flood benchmarks against modeled surface depth grid using defensible spatial matching.

    Evaluates:
    1. Exact containing grid cell depth.
    2. Nearest flooded cell across the domain.
    3. Road-relevant buffer neighborhood (search_radius_m, default 200m).
    4. Distance to selected modeled cell.
    5. Milan Subway correctly tagged as OUTSIDE_PILOT_EXTENT.
    """
    import math
    transformer = pyproj.Transformer.from_crs("EPSG:4326", "EPSG:32643", always_xy=True)
    inv_transform = ~engine.transform
    t = engine.transform
    cell_size = 30.0

    flooded_r, flooded_c = np.where(depth_grid > 0.001)
    if len(flooded_r) > 0:
        flooded_xs = t.c + (flooded_c + 0.5) * t.a
        flooded_ys = t.f + (flooded_r + 0.5) * t.e
        flooded_depths = depth_grid[flooded_r, flooded_c]
    else:
        flooded_xs = np.array([])
        flooded_ys = np.array([])
        flooded_depths = np.array([])

    comparisons: List[BenchmarkValidationComparison] = []

    for b in benchmarks:
        bx, by = transformer.transform(b.longitude, b.latitude)
        col_f, row_f = inv_transform @ (bx, by)
        c, r = int(col_f + 0.5), int(row_f + 0.5)

        if 0 <= r < engine.height and 0 <= c < engine.width:
            exact_depth = float(depth_grid[r, c])
            obs_min = b.depth_range.min_depth_m
            obs_max = b.depth_range.max_depth_m

            # Distance to nearest flooded cell in whole domain
            if len(flooded_r) > 0:
                dists_all = np.sqrt((flooded_xs - bx)**2 + (flooded_ys - by)**2)
                min_idx = int(np.argmin(dists_all))
                nearest_flooded_dist = float(dists_all[min_idx])
            else:
                nearest_flooded_dist = float("inf")

            # Local neighborhood window within search_radius_m
            r_radius_cells = max(1, int(math.ceil(search_radius_m / cell_size)))
            r_min = max(0, r - r_radius_cells)
            r_max = min(engine.height - 1, r + r_radius_cells)
            c_min = max(0, c - r_radius_cells)
            c_max = min(engine.width - 1, c + r_radius_cells)

            sub_rows, sub_cols = np.meshgrid(
                np.arange(r_min, r_max + 1),
                np.arange(c_min, c_max + 1),
                indexing="ij"
            )
            sub_xs = t.c + (sub_cols + 0.5) * t.a
            sub_ys = t.f + (sub_rows + 0.5) * t.e
            sub_dists = np.sqrt((sub_xs - bx)**2 + (sub_ys - by)**2)
            sub_depths = depth_grid[sub_rows, sub_cols]

            mask_in_radius = sub_dists <= search_radius_m
            in_rad_depths = sub_depths[mask_in_radius]
            in_rad_dists = sub_dists[mask_in_radius]

            max_depth_in_buf = float(np.max(in_rad_depths)) if len(in_rad_depths) > 0 else 0.0

            if exact_depth > 0.0 and exact_depth >= max_depth_in_buf:
                matched_depth = exact_depth
                match_method = "EXACT_CELL"
                matched_dist = 0.0
            elif max_depth_in_buf > 0.0:
                matched_depth = max_depth_in_buf
                match_method = "NEIGHBORHOOD_BUFFER"
                max_indices = np.where(in_rad_depths == max_depth_in_buf)[0]
                matched_dist = float(in_rad_dists[max_indices[0]])
            else:
                matched_depth = 0.0
                match_method = "NEIGHBORHOOD_BUFFER"
                matched_dist = nearest_flooded_dist if nearest_flooded_dist < float("inf") else None

            if obs_max is None:
                within = matched_depth >= obs_min
                diff = max(0.0, obs_min - matched_depth)
            elif obs_min <= matched_depth <= obs_max:
                within = True
                diff = 0.0
            elif matched_depth < obs_min:
                within = False
                diff = obs_min - matched_depth
            else:
                within = False
                diff = matched_depth - obs_max

            dist_note = f"dist={matched_dist:.1f}m" if matched_dist is not None else "no flooded cells"
            notes = (
                f"Evaluated with {search_radius_m:.0f}m road-relevant buffer. "
                f"Exact cell ({r}, {c}) depth: {exact_depth:.3f}m. "
                f"Matched ({match_method}) depth: {matched_depth:.3f}m ({dist_note}). "
                f"Nearest flooded cell across domain: {nearest_flooded_dist:.1f}m. "
                f"Observed descriptor: {b.depth_range.descriptor}."
            )

            comparisons.append(
                BenchmarkValidationComparison(
                    location_id=b.location_id,
                    location_name=b.location_name,
                    observed_depth_range=b.depth_range.descriptor,
                    minimum=obs_min,
                    maximum=obs_max,
                    observed_min_depth_m=obs_min,
                    observed_max_depth_m=obs_max,
                    exact_cell_depth_m=round(exact_depth, 3),
                    matched_depth_m=round(matched_depth, 3),
                    match_method=match_method,
                    search_radius_m=search_radius_m,
                    matched_cell_distance_m=round(matched_dist, 1) if matched_dist is not None else None,
                    within_observed_range=within,
                    absolute_difference_m=round(diff, 3),
                    observed_provenance=b.provenance,
                    modeled_provenance="RETROSPECTIVE_SIMULATION",
                    spatial_status="MATCHED",
                    is_model_input=b.is_model_input,
                    notes=notes,
                )
            )
        else:
            comparisons.append(
                BenchmarkValidationComparison(
                    location_id=b.location_id,
                    location_name=b.location_name,
                    observed_depth_range=b.depth_range.descriptor,
                    minimum=b.depth_range.min_depth_m,
                    maximum=b.depth_range.max_depth_m,
                    observed_min_depth_m=b.depth_range.min_depth_m,
                    observed_max_depth_m=b.depth_range.max_depth_m,
                    exact_cell_depth_m=None,
                    matched_depth_m=None,
                    match_method="NONE",
                    search_radius_m=search_radius_m,
                    matched_cell_distance_m=None,
                    within_observed_range=False,
                    absolute_difference_m=None,
                    observed_provenance=b.provenance,
                    modeled_provenance="RETROSPECTIVE_SIMULATION",
                    spatial_status="OUTSIDE_PILOT_EXTENT",
                    is_model_input=b.is_model_input,
                    notes=f"Coordinates ({b.latitude}, {b.longitude}) fall outside pilot DEM extent (~1.3 km west). Benchmark retained for regional validation.",
                )
            )

    return comparisons


DEPTH_CLASS_LABELS: Dict[int, str] = {
    0: "0.0–0.5 m",
    1: "0.5–1.0 m",
    2: "1.0–2.0 m",
    3: "2.0+ m",
}


def _get_depth_class_id(d: float) -> int:
    if d < 0.5:
        return 0
    elif d < 1.0:
        return 1
    elif d < 2.0:
        return 2
    else:
        return 3


def flood_result_to_geojson(
    flood_result: Any,
    cell_size: float = 30.0,
    origin_x: float = 0.0,
    origin_y: float = 0.0,
) -> Dict[str, Any]:
    """Convert FloodResult to GeoJSON FeatureCollection (EPSG:4326) for frontend mapping.

    Adjacent flooded cells that share an edge within the same depth class are dissolved
    into contiguous surface polygons, eliminating internal 30m checkerboard tile boundaries
    while strictly preserving underlying raster depths, depth classification, and
    disconnected component topology.
    """
    flood_depth = flood_result.flood_depth_m
    flooded_mask = flood_result.flooded_mask

    if flood_depth is None or flooded_mask is None or not np.any(flooded_mask):
        return {
            "type": "FeatureCollection",
            "features": [],
            "summary": {
                "max_depth_m": 0.0,
                "total_flooded_area_m2": 0.0,
                "total_flood_volume_m3": 0.0,
            },
        }

    transformer = pyproj.Transformer.from_crs("EPSG:32643", "EPSG:4326", always_xy=True)
    rows, cols = flood_depth.shape

    class_cells: Dict[int, List[Dict[str, Any]]] = {0: [], 1: [], 2: [], 3: []}

    for r in range(rows):
        for c in range(cols):
            if flooded_mask[r, c]:
                depth = float(flood_depth[r, c])
                if depth < 0.001:
                    continue
                cid = _get_depth_class_id(depth)
                x_min = origin_x + c * cell_size
                y_max = origin_y - r * cell_size
                x_max = x_min + cell_size
                y_min = y_max - cell_size
                cell_box = box(x_min, y_min, x_max, y_max)
                class_cells[cid].append({
                    "box": cell_box,
                    "row": r,
                    "col": c,
                    "depth": depth,
                })

    features: List[Dict[str, Any]] = []

    for cid, cells in class_cells.items():
        if not cells:
            continue

        boxes = [item["box"] for item in cells]
        merged_geom = unary_union(boxes)

        polys: List[Polygon] = []
        if isinstance(merged_geom, Polygon):
            polys = [merged_geom]
        elif isinstance(merged_geom, MultiPolygon):
            polys = list(merged_geom.geoms)

        for poly in polys:
            constituent = [
                item for item in cells
                if poly.contains(item["box"].centroid) or poly.intersects(item["box"].centroid)
            ]
            if not constituent:
                continue

            poly_depths = [item["depth"] for item in constituent]
            peak_d = max(poly_depths)
            min_d = min(poly_depths)
            mean_d = sum(poly_depths) / len(poly_depths)

            ext_xs, ext_ys = poly.exterior.coords.xy
            lons, lats = transformer.transform(list(ext_xs), list(ext_ys))
            exterior_coords = [[round(lo, 6), round(la, 6)] for lo, la in zip(lons, lats)]

            interior_coords = []
            for interior in poly.interiors:
                in_xs, in_ys = interior.coords.xy
                i_lons, i_lats = transformer.transform(list(in_xs), list(in_ys))
                interior_coords.append([[round(lo, 6), round(la, 6)] for lo, la in zip(i_lons, i_lats)])

            geom_coords = [exterior_coords] + interior_coords
            primary_cell = constituent[0]

            features.append({
                "type": "Feature",
                "properties": {
                    "depth": round(peak_d, 3),
                    "min_depth": round(min_d, 3),
                    "max_depth": round(peak_d, 3),
                    "mean_depth": round(mean_d, 3),
                    "depth_class": DEPTH_CLASS_LABELS[cid],
                    "depth_class_id": cid,
                    "cell_count": len(constituent),
                    "cell_row": primary_cell["row"],
                    "cell_col": primary_cell["col"],
                    "cells": [
                        {"row": it["row"], "col": it["col"], "depth": round(it["depth"], 3)}
                        for it in constituent
                    ],
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": geom_coords,
                },
            })

    return {
        "type": "FeatureCollection",
        "features": features,
        "summary": {
            "max_depth_m": round(float(flood_result.max_depth_m), 3),
            "total_flooded_area_m2": round(float(flood_result.total_flooded_area_m2), 1),
            "total_flood_volume_m3": round(float(flood_result.total_flood_volume_m3), 1),
        },
    }


class HistoricalReplayEngine:
    """Orchestrates retrospective historical flood simulations using existing production models."""

    def __init__(
        self,
        dem_raster_path: Optional[str] = None,
        drainage_network: Optional[DrainageNetwork] = None,
        raster_engine: Optional[RasterEngine] = None,
        contributing_area_m2: float = 500000.0,
        runoff_coefficient: float = 0.7,
        cell_size_m: float = 30.0,
    ):
        self.dem_raster_path = dem_raster_path or settings.dem_path
        self.contributing_area_m2 = contributing_area_m2
        self.runoff_coefficient = runoff_coefficient
        self.cell_size_m = cell_size_m

        # 1. Initialize Raster Engine
        if raster_engine is not None:
            self.engine = raster_engine
        else:
            self.engine = RasterEngine(self.dem_raster_path, threshold_area_m2=15000.0)
            self.engine.load_and_preprocess()
            self.engine.condition_dem()
            self.engine.compute_flow_direction()

        # 2. Initialize Drainage Network (BMC authoritative)
        if drainage_network is not None:
            self.network = drainage_network
        else:
            loaded_net = BMCDrainageLoader.load_default_bmc_network()
            if loaded_net is None:
                raise RuntimeError("Failed to load default BMC drainage network for historical replay")
            self.network = loaded_net

        # Precompute channel capacities once for 1-hour timesteps
        self.channel_capacities: Dict[str, ChannelCapacity] = {
            cid: compute_channel_capacity(c, timestep_hours=1.0)
            for cid, c in self.network.channels.items()
        }

        # Identify inlet nodes for surface runoff distribution
        self.inlet_node_ids = [
            nid for nid, n in self.network.nodes.items()
            if n.node_type == NodeType.INLET
        ]
        if not self.inlet_node_ids:
            # Fallback to all nodes if no explicit inlet type
            self.inlet_node_ids = list(self.network.nodes.keys())

    def run_replay(self, event: HistoricalEvent, include_geojson: bool = False) -> HistoricalReplaySummary:
        """Execute chronological retrospective replay across all forcing timesteps.

        Guarantees:
        - Rainfall forcing provenance is strictly preserved (SECONDARY-REPORT).
        - Tide boundary condition provenance is strictly preserved (DERIVED).
        - No Open-Meteo or external APIs are invoked.
        - Benchmarks are never supplied as simulation inputs.
        - Timesteps are executed sequentially with storage carryover.
        """
        # Strict Safeguards: ensure simulation inputs are not benchmarks
        assert_no_benchmark_leakage(event.rainfall_forcing)
        assert_no_benchmark_leakage(event.boundary_condition)

        if event.rainfall_forcing.provenance == HistoricalProvenance.OBSERVED:
            raise ValueError("Replay rejected: rainfall forcing cannot claim OBSERVED provenance.")
        if event.boundary_condition.provenance == HistoricalProvenance.OBSERVED:
            raise ValueError("Replay rejected: tidal boundary condition cannot claim OBSERVED provenance.")

        rf_series = event.rainfall_forcing.series
        bc_series = event.boundary_condition.series

        if len(rf_series) == 0:
            raise ValueError("Historical event contains zero rainfall forcing steps")

        # Map boundary levels by step index
        boundary_levels: List[float] = [
            bc_series[i].water_level_m if i < len(bc_series) else event.boundary_condition.peak_level_m
            for i in range(len(rf_series))
        ]

        flow_direction = self.engine.get_flow_direction()
        inv_transform = ~self.engine.transform
        origin_x = self.engine.transform[2]
        origin_y = self.engine.transform[5]

        timestep_states: List[HistoricalReplayTimestepState] = []
        current_storage: Optional[Dict[str, float]] = None
        accumulated_flood_grid = np.zeros((self.engine.height, self.engine.width), dtype=float)

        peak_depth_overall = 0.0
        peak_area_overall = 0.0
        peak_vol_overall = 0.0
        peak_surcharge_overall = 0.0

        for idx, rf_step in enumerate(rf_series):
            # 1. Existing Runoff Model (Rational Method)
            runoff = RunoffVolume(
                rainfall_mm=rf_step.rainfall_mm,
                contributing_area_m2=self.contributing_area_m2,
                runoff_coefficient=self.runoff_coefficient,
                timestep_hours=1.0,
            )
            total_runoff_vol = runoff.volume_m3

            # Distribute runoff to inlet nodes
            if total_runoff_vol > 0:
                inflow_per_inlet = total_runoff_vol / len(self.inlet_node_ids)
                inflows = {nid: inflow_per_inlet for nid in self.inlet_node_ids}
            else:
                inflows = {}

            # 2. Existing Hydraulic Propagation Model (Mass Balance + Tailwater)
            tide_level = boundary_levels[idx]
            prop_res: NetworkPropagationTimestepResult = propagate_network_timestep(
                network=self.network,
                node_external_inflows_m3=inflows,
                initial_node_storage_m3=current_storage,
                channel_capacities=self.channel_capacities,
                boundary_level_m=tide_level,
                timestep_hours=1.0,
                timestep_index=idx,
            )
            # Carry over final manhole storage to next timestep
            current_storage = {nid: ns.final_storage_m3 for nid, ns in prop_res.nodes.items()}

            # 3. Project Drainage Surcharges onto Raster Grid
            excess_runoff_m3: Dict[Tuple[int, int], float] = {}

            for nid, ns in prop_res.nodes.items():
                if ns.surcharge_volume_m3 > 0:
                    node = self.network.nodes[nid]
                    col_f, row_f = inv_transform @ (node.x, node.y)
                    c, r = int(col_f + 0.5), int(row_f + 0.5)
                    if 0 <= r < self.engine.height and 0 <= c < self.engine.width:
                        excess_runoff_m3[(r, c)] = excess_runoff_m3.get((r, c), 0.0) + ns.surcharge_volume_m3

            for cid, cs in prop_res.channels.items():
                if cs.excess_m3 > 0:
                    node = self.network.nodes[cs.downstream_node_id]
                    col_f, row_f = inv_transform @ (node.x, node.y)
                    c, r = int(col_f + 0.5), int(row_f + 0.5)
                    if 0 <= r < self.engine.height and 0 <= c < self.engine.width:
                        excess_runoff_m3[(r, c)] = excess_runoff_m3.get((r, c), 0.0) + cs.excess_m3

            # 4. Existing Surface Routing Model (D8 routing)
            flood_res: FloodResult = route_flood_depth(
                excess_runoff_m3=excess_runoff_m3,
                flow_direction=flow_direction,
                cell_size_m=self.cell_size_m,
                total_runoff_volume_m3=total_runoff_vol,
                conveyed_drainage_volume_m3=prop_res.total_outfall_outflow_m3,
                drainage_provenance="BMC",
            )

            # Update accumulated flood grid
            accumulated_flood_grid = np.maximum(accumulated_flood_grid, flood_res.flood_depth_m)

            # Record stats
            peak_depth_overall = max(peak_depth_overall, flood_res.max_depth_m)
            peak_area_overall = max(peak_area_overall, flood_res.total_flooded_area_m2)
            peak_vol_overall = max(peak_vol_overall, flood_res.total_flood_volume_m3)
            peak_surcharge_overall = max(peak_surcharge_overall, prop_res.total_surcharge_volume_m3)

            flooded_cells = int(np.sum(flood_res.flooded_mask))

            step_geojson = None
            street_intel = None
            if include_geojson:
                step_geojson = flood_result_to_geojson(
                    flood_result=flood_res,
                    cell_size=self.cell_size_m,
                    origin_x=origin_x,
                    origin_y=origin_y,
                )
                time_str = rf_step.step_start.strftime("%H:%M IST") if hasattr(rf_step.step_start, "strftime") else f"Step {idx + 1}"
                street_intel = match_flood_to_streets(
                    flood_depth_m=flood_res.flood_depth_m,
                    flooded_mask=flood_res.flooded_mask,
                    cell_w=self.cell_size_m,
                    cell_h=self.cell_size_m,
                    origin_x=origin_x,
                    origin_y=origin_y,
                    horizon=time_str,
                    lead_time=f"Step {idx + 1}",
                    rainfall_mm=rf_step.rainfall_mm,
                )
                if street_intel and street_intel.provenance:
                    street_intel.provenance["classification"] = "Modelled Retrospective Impact (OSM + 2D D8 routing)"
                    street_intel.provenance["disclaimer"] = "Modelled retrospective road impact (OSM + 2D D8 routing). Not historical road observations."

            state = HistoricalReplayTimestepState(
                event_id=event.metadata.event_id,
                timestep_index=idx,
                replay_timestamp=rf_step.step_start,
                rainfall_mm=rf_step.rainfall_mm,
                rainfall_intensity_mm_per_hr=rf_step.intensity_mm_per_hr,
                rainfall_provenance=rf_step.provenance,
                boundary_level_m=tide_level,
                boundary_provenance=event.boundary_condition.provenance,
                peak_flood_depth_m=round(flood_res.max_depth_m, 3),
                flooded_area_m2=round(flood_res.total_flooded_area_m2, 1),
                flood_volume_m3=round(flood_res.total_flood_volume_m3, 1),
                flooded_cell_count=flooded_cells,
                drainage_surcharge_volume_m3=round(prop_res.total_surcharge_volume_m3, 1),
                model_provenance="RETROSPECTIVE_SIMULATION",
                geojson=step_geojson,
                street_risk=street_intel,
            )
            timestep_states.append(state)

        # 5. Independent Post-Replay Validation Comparison
        # Benchmarks are evaluated strictly against accumulated peak depth grid
        validation_comps = compare_benchmarks_against_grid(
            benchmarks=event.observed_flood_benchmarks,
            depth_grid=accumulated_flood_grid,
            engine=self.engine,
            search_radius_m=200.0,
        )

        return HistoricalReplaySummary(
            event_id=event.metadata.event_id,
            event_name=event.metadata.event_name,
            first_timestamp=timestep_states[0].replay_timestamp,
            last_timestamp=timestep_states[-1].replay_timestamp,
            timestep_count=len(timestep_states),
            peak_modeled_depth_m=round(peak_depth_overall, 3),
            peak_flooded_area_m2=round(peak_area_overall, 1),
            peak_flood_volume_m3=round(peak_vol_overall, 1),
            peak_surcharge_volume_m3=round(peak_surcharge_overall, 1),
            timesteps=timestep_states,
            validation_comparisons=validation_comps,
        )
