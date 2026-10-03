"""2D SURFACE ROUTING over the enforced DEM (DSM-derived, documented).

Fulfils the problem statement's "route rainfall volume across a 2D
surface terrain model" clause using the on-disk terrain-conditioned DEM
(Copernicus GLO-30 DSM 30 m, enforced with the 1 m stream burn):

- STATIC (cached): corridor-window cells (within ~2.5 km of the modeled
  corridor) and a deterministic D8 flow-direction pass over the window.
- PER-REQUEST: each live cell receives rainfall-excess volume
  (rainfall_depth x ASSUMED runoff C = 0.75, documented) and routes
  downhill along D8 from highest to lowest elevation -> per-cell surface
  water column proxy (cm), ponding hotspots, and corridor-margin inflow
  per model reach.

SCIENTIFIC LABELING:
- Surface columns are MODEL-DERIVED SURFACE PROXIES, not ponded depths:
  the DEM is a 30 m DSM (not a DTM), blanket vertical accuracy < 2 m is
  never claimed, and micro-connectivity (curbs, inlets, walls) is not
  modeled. Hotspots are candidate ponding cells, not observed flooding.
- The per-reach corridor-margin inflow is a LATERAL PROXY reported
  alongside the corridor model; it is never injected into the historical
  replay (whose laterals stay documented-zero) and never replaces the
  physics.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

from rasterio.transform import xy as rio_xy

from backend.app.domain.delhi.digital_twin.kushak_reaches_tiered import (
    KUSHAK_MODEL_REACHES,
)
from backend.app.domain.delhi.digital_twin.kushak_scenario_ensemble import (
    SCENARIO_RUNOFF_C,
)
from backend.app.domain.delhi.routing.risk import get_reach_corridor
from backend.app.domain.delhi.single_flight import single_flight_cached
from backend.app.domain.delhi.structure_cache import disk_artifact

_REPO_ROOT = Path(__file__).resolve().parents[4]
DEM_PATH = _REPO_ROOT / "data" / "delhi" / "derived" / "dem" / "kushak_enforced_dem_burn1m.tif"

NODATA = -9999.0
RUNOFF_C = SCENARIO_RUNOFF_C  # ASSUMED (documented)
HOTSPOT_THRESHOLD_CM = 2.0
CORRIDOR_WINDOW_M = 2500.0    # ASSUMED window radius for the surface pass
CORRIDOR_LATERAL_MARGIN_M = 120.0  # ASSUMED margin for corridor inflow proxy
# ASSUMED infiltration loss for the surface pass (mm/h) - documented
# engineering assumption giving a physical recession mechanism; it is
# not a calibrated parameter.
INFILTRATION_MM_H = 4.0

D8 = ((-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1))


@dataclass(frozen=True)
class SurfaceRoutingStructure:
    # 1-D arrays over the cropped window cells only.
    cell_flat_idx: np.ndarray     # index into the full DEM flat array
    elev: np.ndarray              # elevation (m)
    flow_to_local: np.ndarray     # local index of steepest downslope (-1 sink)
    order: np.ndarray             # local indices sorted by elevation desc
    cell_area_m2: float
    window_rows: np.ndarray       # row of each cell in the full grid
    window_cols: np.ndarray
    width_full: int
    height_full: int
    transform: object
    crs: str
    depression_cap_m: np.ndarray
    edge_exit: np.ndarray


@single_flight_cached
@disk_artifact("surface_structure")
def get_surface_structure() -> SurfaceRoutingStructure:
    """Deterministic D8 structure over the corridor window (cached)."""
    import rasterio
    from shapely.geometry import Point

    with rasterio.open(DEM_PATH) as ds:
        dem = ds.read(1).astype(np.float64)
        transform = ds.transform
        crs = ds.crs.to_string()
    height, width = dem.shape
    elev = np.where(dem == NODATA, np.nan, dem)

    from shapely.geometry import MultiLineString
    import rasterio.features

    corridor = get_reach_corridor()
    # Vectorized window: rasterize the buffered corridor onto the grid.
    buffered = MultiLineString(corridor.lines).buffer(CORRIDOR_WINDOW_M)
    mask = rasterio.features.rasterize(
        [(buffered, 1)],
        out_shape=(height, width),
        transform=transform,
        fill=0,
        dtype="uint8",
    )
    in_window = mask.ravel().astype(bool)
    cell_flat = np.flatnonzero(in_window)
    elev_win = elev.ravel()[cell_flat]
    valid = ~np.isnan(elev_win)
    cell_flat = cell_flat[valid]
    elev_win = elev_win[valid]

    n = cell_flat.size
    flat = np.full(width * height, np.inf)
    flat[cell_flat] = elev_win
    win_rows = (cell_flat // width).astype(np.int64)
    win_cols = (cell_flat % width).astype(np.int64)

    # Both D8 passes run as numpy ops over one (n, 8) neighbour block instead
    # of 2 x 8 x n Python iterations. Off-grid and out-of-window neighbours
    # read as +inf, which is what `flat` already holds for non-window cells,
    # so every comparison below behaves exactly as the guarded loop did.
    nbr = np.asarray(D8, dtype=np.int64)
    nbr_r = win_rows[:, None] + nbr[None, :, 0]
    nbr_c = win_cols[:, None] + nbr[None, :, 1]
    in_grid = (nbr_r >= 0) & (nbr_r < height) & (nbr_c >= 0) & (nbr_c < width)
    nbr_flat_idx = np.where(in_grid, nbr_r * width + nbr_c, 0)
    nbr_elev = np.where(in_grid, flat[nbr_flat_idx], np.inf)

    # Local depression depth per window cell: elevator minus the lowest
    # neighbor elevation (clamped >= 0). Used to BOUND standing water so a
    # cell with no outlet cannot report an unbounded column.
    lowest = np.minimum(elev_win, nbr_elev.min(axis=1))
    depression_cap_m = np.maximum(elev_win - lowest, 0.0)

    local_of = np.full(width * height, -1, dtype=np.int64)
    local_of[cell_flat] = np.arange(n)
    nbr_local = np.where(in_grid, local_of[nbr_flat_idx], -1)

    # Flow target is the lowest IN-WINDOW neighbour, ties broken by D8 order;
    # np.argmin returns the first minimum, which is what `if zj < best_z` did.
    cand_elev = np.where(nbr_local >= 0, nbr_elev, np.inf)
    best_dir = np.argmin(cand_elev, axis=1)
    rows = np.arange(n)
    flow_to_local = np.where(
        np.isfinite(cand_elev[rows, best_dir]),
        nbr_local[rows, best_dir], -1,
    ).astype(np.int64)

    order = np.argsort(elev_win, kind="stable")[::-1]
    # True window-edge exits: a strictly lower neighbor exists but lies
    # OUTSIDE the window (the corridor continues downstream there).
    # Interior sinks (no lower neighbor at all) keep flow_to_local = -1
    # and edge_exit = False - they POND.
    edge_exit = ((nbr_elev < elev_win[:, None]) & (nbr_local < 0)).any(axis=1)

    return SurfaceRoutingStructure(
        cell_flat_idx=cell_flat,
        elev=elev_win,
        flow_to_local=flow_to_local,
        order=order,
        cell_area_m2=float(ds.res[0] * ds.res[1]),
        window_rows=win_rows,
        window_cols=win_cols,
        width_full=width,
        height_full=height,
        transform=transform,
        crs=crs,
        depression_cap_m=depression_cap_m,
        edge_exit=edge_exit,
    )


def surface_pass(
    rainfall_depth_mm: List[Optional[float]],
    timestep_hours: List[float],
    spatial_fields: Optional[List[Optional[np.ndarray]]] = None,
) -> dict:
    """Run the 2D surface pass for one forcing sequence (UNKNOWN depths
    produce no surface loading for that timestep — never zero-filled)."""
    structure = get_surface_structure()
    n = structure.cell_flat_idx.size
    cell_area = structure.cell_area_m2

    timesteps: List[dict] = []
    for t_idx, (depth_mm, dt_h) in enumerate(zip(rainfall_depth_mm, timestep_hours)):
        if depth_mm is None:
            timesteps.append({
                "timestep_index": t_idx,
                "status": "UNKNOWN_FORCING_SKIPPED",
                "peak_surface_cm": None,
                "hotspots": [],
                "per_reach_surface_inflow_m3_s": {},
            })
            continue

        # Spatial fields (synthetic scenarios) override the uniform depth:
        # each cell receives its own excess; otherwise the uniform depth.
        field = spatial_fields[t_idx] if spatial_fields is not None else None
        if field is not None:
            excess_m = np.asarray(field, dtype=np.float64) / 1000.0 * RUNOFF_C
            water_local = np.maximum(np.asarray(excess_m, dtype=np.float64) * cell_area, 0.0)
        else:
            excess_m = depth_mm / 1000.0 * RUNOFF_C
            water_local = np.full(n, excess_m * cell_area)
        for local_i in structure.order:
            if water_local[local_i] <= 0:
                continue
            target = structure.flow_to_local[local_i]
            if target >= 0:
                water_local[target] += water_local[local_i]
                water_local[local_i] = 0.0
        # Bound: standing water cannot exceed the local depression depth
        # (a cell with no outlet is a pit, not an infinite reservoir).
        # Flat cells (no measurable depression) get a documented 10 cm
        # standing-water bound - a 30 m flat cell holding more is a
        # modeling artifact (curbs/walls are not modeled).
        cap_m = np.where(structure.depression_cap_m > 0.15,
                         structure.depression_cap_m, 0.10)
        water_local = np.minimum(water_local, cap_m * cell_area)
        # Infiltration: subtract the documented ASSUMED loss from each
        # cell (capped at available water) - a physical recession mechanism.
        infiltration_m = INFILTRATION_MM_H / 1000.0 * (dt_h if dt_h else 1.0)
        if infiltration_m > 0:
            available = np.maximum(water_local - infiltration_m * cell_area, 0.0)
            water_local = available
        columns_cm = water_local / cell_area * 100.0

        timesteps.append({
            "timestep_index": t_idx,
            "status": "COMPUTED",
            "peak_surface_cm": round(float(columns_cm.max()), 1),
            "hotspots": _extract_hotspots(structure, columns_cm),
            "per_reach_surface_inflow_m3_s": _corridor_margin_inflow(
                structure, water_local, dt_h
            ),
            "depth_field_cm": columns_cm,  # routed surface column (proxy)
        })

    return {
        "method": (
            "D8 cell-to-cell volumetric pass over the enforced 30 m GLO-30 "
            "DSM (corridor window); excess = rainfall x ASSUMED C (0.75); "
            "surface columns are MODEL-DERIVED PROXIES, not ponded depths"
        ),
        "caveat": (
            "DSM (not DTM), 30 m cells; vertical accuracy < 2 m never "
            "claimed; curbs/inlets/backwater not modeled; hotspots are "
            "candidate ponding cells, not observed flooding; corridor "
            "inflow is a lateral proxy, never injected into replay"
        ),
        "runoff_coefficient": RUNOFF_C,
        "runoff_coefficient_provenance": "ASSUMED (documented)",
        "window_m": CORRIDOR_WINDOW_M,
        "timesteps": timesteps,
    }


def _extract_hotspots(
    structure: SurfaceRoutingStructure,
    columns_cm: np.ndarray,
    top_n: int = 8,
) -> List[dict]:
    candidates = np.flatnonzero(columns_cm >= HOTSPOT_THRESHOLD_CM)
    if candidates.size == 0:
        return []
    candidates = candidates[np.argsort(columns_cm[candidates])[::-1]][:top_n]
    out = []
    for local_i in candidates:
        r = int(structure.window_rows[local_i])
        c = int(structure.window_cols[local_i])
        utm_x, utm_y = rio_xy(structure.transform, r, c)
        lon_arr, lat_arr = __import__("rasterio.warp", fromlist=["transform"]).transform(
            structure.crs, "EPSG:4326", [float(utm_x)], [float(utm_y)]
        )
        lon, lat = lon_arr[0], lat_arr[0]
        out.append({
            "lon": round(float(lon), 5),
            "lat": round(float(lat), 5),
            "surface_water_cm_estimated": round(float(columns_cm[local_i]), 1),
            "provenance": "MODEL-DERIVED_SURFACE_PROXY (DSM pass)",
        })
    return out


def _corridor_margin_inflow(
    structure: SurfaceRoutingStructure,
    water_local: np.ndarray,
    dt_h: float,
) -> Dict[str, float]:
    """Routed volume arriving on corridor-margin cells, per model reach,
    as an inflow proxy (m3/s over the timestep)."""
    from shapely.geometry import Point

    corridor = get_reach_corridor()
    reach_inflow = {r.reach_id: 0.0 for r in KUSHAK_MODEL_REACHES}
    for local_i in np.flatnonzero(water_local > 0):
        r = int(structure.window_rows[local_i])
        c = int(structure.window_cols[local_i])
        utm_x, utm_y = rio_xy(structure.transform, r, c)
        # Both the corridor lines and these coords are UTM 43N: point
        # comparisons stay in the metric CRS.
        pt = Point(float(utm_x), float(utm_y))
        nearest = corridor.tree.nearest(pt)
        if pt.distance(corridor.tree.line(nearest)) <= CORRIDOR_LATERAL_MARGIN_M:
            reach_inflow[corridor.reach_ids[nearest]] += float(water_local[local_i])
    if dt_h > 0:
        for k in reach_inflow:
            q = reach_inflow[k] / (dt_h * 3600.0)
            reach_inflow[k] = round(q, 3) if q > 0 else 0.0
    return reach_inflow