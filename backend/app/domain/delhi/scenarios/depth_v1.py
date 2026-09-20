"""V1-REFERENCE FLOOD DEPTH MODEL, ported to the Delhi window.

The Delhi/Kushak scenario depth product uses the Mumbai/Kurla V1
reference model semantics (`app.domain.flood.routing.route_flood_depth`):

- Runoff volume is distributed to drainage-network inlets; each inlet
  conveys up to its capacity volume; the SURCHARGE (excess) is placed at
  the inlet's cell and routed over the DEM.
- D8 equilibrium routing: ALL water moves fully downstream each pass
  until equilibrium; no infiltration during routing; water ponds where
  no lower valid downstream cell exists.
- Depth per cell = ponded volume / cell area (m).

Differences from the literal V1 code (documented):
- The V1 function is a Python double loop (height*width*2 iterations) —
  unusable on the 48k-cell Delhi window. This port uses an equivalent
  elevation-sorted single-pass solver with IDENTICAL equilibrium
  semantics (full downstream transfer converges in one sorted pass);
  `test_v1_equivalence_small_window` proves the two produce the same
  depth field on a small window.
- Window-edge cells drain OUT of the domain (open boundary) instead of
  ponding: the modeled corridor continues downstream (Barapullah), so a
  window edge is not a real sink. Outflow volume is tracked for mass
  balance.
- Provenance: this is the V1 reference model on Delhi data — SIMULATED
  scenario output, never observed depth, never real-event accuracy.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Dict, List, Optional, Tuple

import numpy as np

from backend.app.domain.delhi.surface import get_surface_structure
from backend.app.domain.delhi.scenarios.config import (
    ScenarioDefinition,
    classify_depth_cm,
    depth_config,
)

RUNOFF_C = 0.75  # ASSUMED (documented scenario convention)

# V1-prototype curb-and-gutter inlet parameters (documented ASSUMED values,
# mirroring the V1 pipeline's uniform_params): street gullies along roads
# capture surface runoff; capacity per inlet governs street ponding.
CURB_INLET_WIDTH_M = 0.45
CURB_INLET_DEPTH_M = 0.25
CURB_INLET_MANNING_N = 0.018
CURB_INLET_SLOPE = 0.0006
INLET_ROAD_MARGIN_M = 25.0  # cells within this distance of an OSM road host an inlet


@lru_cache(maxsize=1)
def inlet_cell_indices() -> np.ndarray:
    """Window cells within INLET_ROAD_MARGIN_M of an OSM road (V1 inlet
    convention with road-based inlets; roads are real OSM data)."""
    import rasterio
    import rasterio.features
    import json as _json
    from shapely.geometry import LineString, MultiLineString

    structure = get_surface_structure()
    roads_path = (
        structure.transform
        and None  # placeholder to keep import shape
    )
    from pathlib import Path as _Path

    _repo = _Path(__file__).resolve().parents[5]
    data = _json.loads(
        (_repo / "backend" / "app" / "data" / "roads" / "delhi_kushak_roads.geojson").read_text(encoding="utf-8")
    )
    # Roads are WGS84; the raster transform is UTM 43N - project first.
    import rasterio.warp as rw

    lines = []
    for feature in data.get("features", []):
        coords = feature["geometry"]["coordinates"]
        if len(coords) >= 2:
            lons = [c[0] for c in coords]
            lats = [c[1] for c in coords]
            xs, ys = rw.transform("EPSG:4326", "EPSG:32643", lons, lats)
            lines.append(LineString(zip(xs, ys)))
    # Rasterize the road lines directly (no topological union - that is
    # prohibitively slow on a 9k-line network), then dilate the mask by
    # one cell (~30 m, the documented inlet margin at 30 m cells).
    mask = rasterio.features.rasterize(
        lines,
        out_shape=(structure.height_full, structure.width_full),
        transform=structure.transform,
        fill=0,
        dtype="uint8",
    ).astype(bool)
    dilated = mask.copy()
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if dr == 0 and dc == 0:
                continue
            dilated |= np.roll(np.roll(mask, dr, axis=0), dc, axis=1)
    # Window cells only, valid elevation.
    win_flat = structure.cell_flat_idx
    in_win = dilated.ravel()[win_flat]
    valid = ~np.isnan(structure.elev)
    cells = win_flat[in_win & valid]
    # Gully spacing: V1 demo convention. The Mumbai V1 pipeline models 78
    # inlets over the ~555-cell (30 m) pilot ~= one inlet per ~7 street
    # cells; preserving that per-inlet contributing-area density keeps the
    # V1 dose-response (20 mm/h conveyed / 40-70 mm/h progressively
    # surcharging) faithful on the larger Delhi window. Cells are ordered
    # along the road raster, so ::N gives a near-uniform spatial spread.
    V1_INLET_CELL_STRIDE = 7
    return cells[::V1_INLET_CELL_STRIDE]


def _curb_inlet_capacity_m3(dt_h: float, efficiency: float = 1.0) -> float:
    import math as _m

    area = CURB_INLET_WIDTH_M * CURB_INLET_DEPTH_M
    perim = CURB_INLET_WIDTH_M + 2.0 * CURB_INLET_DEPTH_M
    radius = area / perim if perim > 0 else 0.0
    q = (1.0 / CURB_INLET_MANNING_N) * area * (radius ** (2.0 / 3.0)) * (CURB_INLET_SLOPE ** 0.5)
    return q * (dt_h * 3600.0) * efficiency


@dataclass
class V1DepthStep:
    """One timestep's V1-reference depth field + V1-style statistics."""

    timestep_index: int
    depth_m: np.ndarray            # per-window-cell ponded depth (m)
    flooded_cells: int
    max_depth_m: float
    total_flooded_area_m2: float
    total_runoff_volume_m3: float
    conveyed_volume_m3: float      # held by the drainage network (below capacity)
    surcharged_volume_m3: float    # placed on the surface (over capacity)
    drained_out_volume_m3: float   # left through the open window boundary
    overflow_volume_m3: float = 0.0  # beyond the terrain depression cap
    provenance: str = "MODELLED/DERIVED (V1 reference semantics, Delhi window)"


def _v1_route(excess_input, structure) -> Tuple[np.ndarray, float]:
    """V1 equilibrium routing on the Delhi window (fast sorted pass).

    Full downstream transfer each step; water ponds at interior sinks and
    LEAVES at window-edge cells (open boundary, documented deviation).
    Returns (ponded volume per local cell, drained_out_m3).
    """
    n = structure.cell_flat_idx.size
    if isinstance(excess_input, dict):
        water = np.zeros(n)
        for local_i, vol in excess_input.items():
            water[local_i] += vol
    else:
        water = np.array(excess_input, dtype=np.float64)

    # Elevation-sorted descending pass: each cell transfers ALL its water
    # downstream once; interior sinks pond, window-edge cells drain out
    # (open boundary). One sorted pass converges exactly (V1 semantics).
    flow = structure.flow_to_local
    exits = getattr(structure, "edge_exit", None)
    # V1 transfer threshold: cells holding at or below this depth do not
    # move (V1 route_flood_depth threshold_m, default 0.001 m).
    threshold_vol = 0.001 * structure.cell_area_m2
    drained_out = 0.0
    for local_i in structure.order:
        v = water[local_i]
        if v <= threshold_vol:
            continue  # sub-threshold residue ponds (V1 semantics)
        target = flow[local_i]
        if target >= 0:
            water[target] += v
            water[local_i] = 0.0
        elif exits is not None and exits[local_i]:
            # True window-edge exit: the corridor continues downstream.
            drained_out += v
            water[local_i] = 0.0
        else:
            # Interior sink: water ponds here (V1 semantics) - retained.
            pass
    return water, drained_out


def scenario_v1_depth_steps(
    scenario: ScenarioDefinition,
    member_scale: float,
    capacity_by_edge: Dict[str, float],
    fields: Optional[List[np.ndarray]] = None,
) -> List[V1DepthStep]:
    """Full V1 reference coupling per scenario timestep:

    runoff -> distribute to drainage edges (inlet share) -> convey up to
    the capacity volume -> surcharge placed at the edge's downstream node
    cell -> V1 equilibrium routing -> per-cell depth.
    """
    structure = get_surface_structure()
    cell_area = structure.cell_area_m2
    n_steps = scenario.n_steps
    dt_h = scenario.timestep_min / 60.0

    inlets = inlet_cell_indices()
    n_inlets = int(inlets.size)
    if n_inlets == 0:
        raise RuntimeError("no inlet cells in the corridor window")
    inlet_local = {int(f): i for i, f in enumerate(inlets)}

    # Drainage condition (SCN-05): the experimental modifier reduces the
    # effective curb-inlet intake AND the trunk capacity class.
    modifier = scenario.drainage_modifier
    inlet_efficiency = modifier if modifier is not None else 1.0
    curb_cap = _curb_inlet_capacity_m3(dt_h, inlet_efficiency)

    steps: List[V1DepthStep] = []
    # Map full-grid flat indices of inlets to WINDOW-local positions (the
    # depth fields are window-local arrays).
    flat_to_win_local = {int(f): i for i, f in enumerate(structure.cell_flat_idx)}
    inlet_win_local = np.array(
        [flat_to_win_local[int(f)] for f in inlets if int(f) in flat_to_win_local],
        dtype=np.int64,
    )
    for t in range(n_steps):
        areal_depth = _areal_depth_mm(scenario, t, member_scale)
        total_runoff = areal_depth / 1000.0 * RUNOFF_C * cell_area * n_window_cells(structure)

        # V1 inlet convention (spatially faithful): each street inlet
        # receives ITS OWN cell's runoff (the scenario's normalized field
        # concentrates rainfall), conveys up to its curb capacity, and the
        # surplus ponds at the inlet cell. Routing then accumulates the
        # surplus downstream - localized cores flood locally, broad storms
        # flood widely.
        runoff_at_inlets = (
            np.asarray(fields[t], dtype=np.float64)[inlet_win_local]
            / 1000.0
            * RUNOFF_C
            * cell_area
        ) if fields is not None else np.full(len(inlet_win_local), areal_depth / 1000.0 * RUNOFF_C * cell_area)
        conveyed_total = float(np.minimum(runoff_at_inlets, curb_cap).sum())
        surcharge_vec = np.zeros(structure.cell_flat_idx.size)
        excess = np.maximum(runoff_at_inlets - curb_cap, 0.0)
        surcharged_vec_total = float(excess.sum())
        if excess.any():
            surcharge_vec[inlet_win_local] = excess

        water, drained_out = _v1_route(surcharge_vec, structure)
        # Terrain bound: a cell cannot pond deeper than its local
        # depression (flat cells: documented 10 cm bound). Water beyond the
        # cap is OVERFLOW - tracked honestly in the mass balance, never
        # allowed to produce absurd sink depths.
        cap_m = np.where(structure.depression_cap_m > 0.15,
                         structure.depression_cap_m, 0.10)
        overflow_m3 = float(np.maximum(water - cap_m * cell_area, 0.0).sum())
        water = np.minimum(water, cap_m * cell_area)
        depth_m = water / cell_area
        flooded = depth_m > 0.001
        steps.append(V1DepthStep(
            timestep_index=t,
            depth_m=depth_m,
            flooded_cells=int(np.count_nonzero(flooded)),
            max_depth_m=float(depth_m.max()) if depth_m.size else 0.0,
            total_flooded_area_m2=float(np.count_nonzero(flooded)) * cell_area,
            total_runoff_volume_m3=total_runoff,
            conveyed_volume_m3=conveyed_total,
            surcharged_volume_m3=float(surcharged_vec_total),
            overflow_volume_m3=overflow_m3,
            drained_out_volume_m3=drained_out,
        ))
    return steps


def n_window_cells(structure) -> int:
    return int(structure.cell_flat_idx.size)


def v1_depth_step_for_intensity(
    depth_mm: float,
    dt_h: float = 1.0,
    timestep_index: int = 0,
) -> V1DepthStep:
    """One V1-reference depth step for a UNIFORM areal rainfall intensity.

    V1's exact inlet convention (``flood_pipeline.run_flood_modeling_``
    ``pipeline``): TOTAL catchment runoff volume divided EVENLY across all
    street inlets; each inlet conveys up to its curb capacity; the
    SURCHARGE (excess) is placed at the inlet cell and routed over the DEM
    (V1 equilibrium semantics). This is the same rule the historical
    replay depth grid uses. Exposed as a reusable function so the LIVE
    forecast horizons, the WHAT-IF scenario, and the historical replay all
    share ONE depth model (single source of truth — no parallel
    implementations).
    """
    structure = get_surface_structure()
    cell_area = structure.cell_area_m2
    inlets = inlet_cell_indices()
    if inlets.size == 0:
        raise RuntimeError("no inlet cells in the corridor window")

    flat_to_win = {int(f): i for i, f in enumerate(structure.cell_flat_idx)}
    inlet_win = np.array(
        [flat_to_win[int(f)] for f in inlets if int(f) in flat_to_win], dtype=np.int64
    )
    total_runoff = depth_mm / 1000.0 * RUNOFF_C * cell_area * n_window_cells(structure)
    curb_cap = _curb_inlet_capacity_m3(dt_h, 1.0)
    # V1 rule: uniform per-inlet dose of the total catchment runoff.
    runoff_at_inlets = np.full(len(inlet_win), total_runoff / max(len(inlet_win), 1))
    conveyed_total = float(np.minimum(runoff_at_inlets, curb_cap).sum())
    excess = np.maximum(runoff_at_inlets - curb_cap, 0.0)
    surcharge = np.zeros(structure.cell_flat_idx.size)
    if excess.any():
        surcharge[inlet_win] = excess
    water, drained_out = _v1_route(surcharge, structure)
    cap_m = np.where(structure.depression_cap_m > 0.15, structure.depression_cap_m, 0.10)
    overflow_m3 = float(np.maximum(water - cap_m * cell_area, 0.0).sum())
    water = np.minimum(water, cap_m * cell_area)
    depth_m = water / cell_area
    flooded = int(np.count_nonzero(depth_m > 0.001))
    return V1DepthStep(
        timestep_index=timestep_index,
        depth_m=depth_m,
        flooded_cells=flooded,
        max_depth_m=float(depth_m.max()) if depth_m.size else 0.0,
        total_flooded_area_m2=flooded * cell_area,
        total_runoff_volume_m3=total_runoff,
        conveyed_volume_m3=conveyed_total,
        surcharged_volume_m3=float(excess.sum()),
        overflow_volume_m3=overflow_m3,
        drained_out_volume_m3=drained_out,
    )


def _areal_depth_mm(scenario: ScenarioDefinition, timestep_index: int, member_scale: float = 1.0) -> float:
    from backend.app.domain.delhi.scenarios.rainfall import _areal_depth_mm as areal

    return areal(scenario, timestep_index, member_scale)


def depth_cells_from_v1(
    step: V1DepthStep, structure, max_cells: int = 320
) -> List[dict]:
    """Top depth cells for the map layer (V1-reference grid samples)."""
    import rasterio
    import rasterio.warp as rw

    shallow = depth_config()["thresholds_cm"]["SHALLOW"]
    cand = np.flatnonzero(step.depth_m * 100.0 >= shallow)
    if cand.size == 0:
        return []
    cand = cand[np.argsort(step.depth_m[cand])[::-1]][:max_cells]
    rows = structure.window_rows[cand]
    cols = structure.window_cols[cand]
    xs, ys = rasterio.transform.xy(structure.transform, rows, cols, offset="center")
    lons, lats = rw.transform(
        structure.crs, "EPSG:4326", [float(x) for x in xs], [float(y) for y in ys]
    )
    out = []
    for j in range(len(cand)):
        cm = float(step.depth_m[cand[j]] * 100.0)
        out.append({
            "lon": round(lons[j], 5),
            "lat": round(lats[j], 5),
            "depth_cm": round(cm, 1),
            "flood_state": classify_depth_cm(cm),
            "provenance": "SIMULATED_MODEL_OUTPUT (V1 reference depth grid)",
        })
    return out


def road_depths_from_v1(
    step: V1DepthStep,
    structure,
    edge_midpoints_wgs84: Dict[str, Tuple[float, float]],
) -> Dict[str, dict]:
    """V1-style road matching: sample the depth grid at each road
    segment's midpoint (spatial matching of road network with flooded
    cells). UNKNOWN stays UNKNOWN — never 0 m."""
    import rasterio
    import rasterio.warp as rw

    out: Dict[str, dict] = {}
    if not edge_midpoints_wgs84:
        return out
    ids = list(edge_midpoints_wgs84.keys())
    lons = np.array([edge_midpoints_wgs84[k][0] for k in ids])
    lats = np.array([edge_midpoints_wgs84[k][1] for k in ids])
    # Project to the window CRS and find nearest window cell.
    utm_x, utm_y = rw.transform("EPSG:4326", structure.crs, lons.tolist(), lats.tolist())
    win_x, win_y = rasterio.transform.xy(
        structure.transform, structure.window_rows, structure.window_cols, offset="center"
    )
    win_x = np.asarray(win_x)
    win_y = np.asarray(win_y)
    for i, edge_id in enumerate(ids):
        d = (win_x - utm_x[i]) ** 2 + (win_y - utm_y[i]) ** 2
        local_i = int(np.argmin(d))
        # Confirm the nearest cell is within ~1 cell of the road point.
        dist_m = float(np.sqrt(d[local_i]))
        cm = float(step.depth_m[local_i] * 100.0) if dist_m <= 45.0 else None
        out[edge_id] = {
            "road_segment_id": edge_id,
            "depth_cm": round(cm, 1) if cm is not None else None,
            "depth_m": round(cm / 100.0, 3) if cm is not None else None,
            "water_depth_state": classify_depth_cm(cm),
            "source_type": "SIMULATED_MODEL_OUTPUT",
            "match_method": "nearest surface cell at segment midpoint (<=45 m)",
            "uncertainty": "V1 reference grid (30 m DSM); UNKNOWN if beyond match distance",
        }
    return out

# V1 color ramp (the Mumbai FloodMap legend colors, App.css
# --color-depth-low/mod/high/severe) - exact V1 parity for the map layer.
V1_DEPTH_COLORS = {
    "SHALLOW": "#ffeda0",
    "MODERATE": "#feb24c",
    "DEEP": "#f03b20",
    "SEVERE": "#bd0026",
}


def depth_polygons_from_v1(
    step, structure, min_depth_cm: float = 0.1
) -> dict:
    """Flooded cells as filled 30 m square polygons, colored by the V1
    depth ramp - the raster-like flood-depth map layer (V1 parity)."""
    import rasterio
    import rasterio.warp as rw

    cand = np.flatnonzero(step.depth_m * 100.0 >= min_depth_cm)
    if cand.size == 0:
        return {"type": "FeatureCollection", "features": []}
    rows = structure.window_rows[cand]
    cols = structure.window_cols[cand]
    xs, ys = rasterio.transform.xy(structure.transform, rows, cols, offset="center")
    lons, lats = rw.transform(
        structure.crs, "EPSG:4326", [float(x) for x in xs], [float(y) for y in ys]
    )
    half = 0.000135  # ~15 m in degrees at this latitude (30 m cell)
    features = []
    for j in range(len(cand)):
        cm = float(step.depth_m[cand[j]] * 100.0)
        state = classify_depth_cm(cm)
        color = V1_DEPTH_COLORS.get(state, "#38bdf8")
        lon, lat = lons[j], lats[j]
        features.append({
            "type": "Feature",
            "properties": {"depth_cm": round(cm, 1), "flood_state": state, "color": color},
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [lon - half, lat - half], [lon + half, lat - half],
                    [lon + half, lat + half], [lon - half, lat + half],
                    [lon - half, lat - half],
                ]],
            },
        })
    return {"type": "FeatureCollection", "features": features}
