"""V1-PARITY LIVE STATE ENGINE (Delhi/Kushak window).

Reconstructs the Mumbai V1 product surface on the Delhi V2 data stack:

- Independent NOW / +1h / +2h / +3h flood states: each forecast hour is
  simulated SEPARATELY through the shared V1-reference depth model
  (``depth_v1.v1_depth_step_for_intensity``) — exactly V1's "each horizon
  uses ONLY its own single hour's rainfall" rule.
- Street & intersection flood intelligence: the depth grid is sampled at
  OSM road-segment midpoints / graph junctions (the V1 spatial-matching
  approach, ported to the Delhi road graph). Roads outside the modeled
  surface window, or beyond the sample distance, are UNKNOWN — never 0 m.
- WHAT-IF scenario state: one intensity (mm/h) through the same depth
  model, labeled MODEL_SCENARIO / WHAT-IF. Never presented as live
  weather.
- SYNTHETIC_FALLBACK rainfall: when the live NWP forecast cannot be
  acquired, a deterministic, spatially-uniform, physically-bounded
  synthetic series keeps the system usable. It is labeled SYNTHETIC_FALLBACK
  everywhere it appears and is NEVER presented as observed or forecast
  weather.

DATA PROVENANCE RULES (unchanged from the V2 evidence contracts):
- Depth fields are SIMULATED_MODEL_OUTPUT (V1 reference model on a 30 m
  DSM) — never observed depth.
- Street/intersection depths inherit that provenance; UNKNOWN stays
  UNKNOWN (no zero-fill, no invention).
- Rainfall provenance is one of LIVE (NWP acquired) / SYNTHETIC_FALLBACK
  (demo series) and travels with every payload.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np
from shapely.geometry import LineString, Point
from shapely.strtree import STRtree

from backend.app.domain.delhi.digital_twin.models import ProvenanceStatus  # noqa: F401
from backend.app.domain.delhi.nowcast import (
    DelhiForecastFetch,
    ForecastBin,
    fetch_delhi_rainfall_forecast,
)
from backend.app.domain.delhi.routing.network import get_road_graph
from backend.app.domain.delhi.scenarios.config import classify_depth_cm, depth_config
from backend.app.domain.delhi.scenarios.depth_v1 import (
    V1DepthStep,
    depth_cells_from_v1,
    depth_polygons_from_v1,
    v1_depth_step_for_intensity,
)
from backend.app.domain.delhi.single_flight import single_flight_cached
from backend.app.domain.delhi.surface import get_surface_structure

# IST = UTC+05:30 (matches the nowcast module's forecast window convention).
IST = timezone(timedelta(hours=5, minutes=30))

HORIZON_LABELS: Tuple[str, ...] = ("NOW", "+1h", "+2h", "+3h")
LEAD_TIMES: Dict[str, str] = {"NOW": "0h", "+1h": "+1h", "+2h": "+2h", "+3h": "+3h"}

# V1 road-risk classification (backend/app/domain/roads/models.py semantics,
# identical thresholds so both cities classify identically).
ROAD_RISK_THRESHOLDS_M = {"CRITICAL": 0.60, "HIGH": 0.30, "MEDIUM": 0.15}


def classify_road_risk(depth_m: Optional[float]) -> str:
    """V1 road-risk tiers from modelled depth. UNKNOWN never maps to NONE."""
    if depth_m is None:
        return "UNKNOWN"
    if depth_m >= ROAD_RISK_THRESHOLDS_M["CRITICAL"]:
        return "CRITICAL"
    if depth_m >= ROAD_RISK_THRESHOLDS_M["HIGH"]:
        return "HIGH"
    if depth_m >= ROAD_RISK_THRESHOLDS_M["MEDIUM"]:
        return "MEDIUM"
    if depth_m > 0.001:
        return "LOW"
    return "NONE"


# Sample radius for road/junction depth matching: one DEM cell (~30 m) —
# V1 matches the road/crossing AREA, not a single point. Documented ASSUMED
# matching distance; beyond it segments are UNKNOWN (never 0 m).
MATCH_DISTANCE_M = 45.0
SAMPLE_RADIUS_M = 32.0

# V1-style curb-inlet conveyance share used for the peak summary claim.
CONVEYANCE_NOTE = (
    "Runoff C = 0.75 (ASSUMED, documented) • curb-and-gutter inlets every "
    "~60 m along OSM roads (DEMO spacing) • V1-reference equilibrium "
    "surface routing on the enforced 30 m DEM"
)


# ---------------------------------------------------------------------------
# Synthetic fallback rainfall (labeled, deterministic, bounded)
# ---------------------------------------------------------------------------

# Deterministic demo hyetograph (mm per hour) used ONLY when the NWP
# forecast is unavailable. Bounded to a physically plausible monsoon burst;
# shape is fixed (no randomness) so every fallback run is reproducible.
SYNTHETIC_FALLBACK_PROFILE_MM = (2.5, 12.0, 18.0, 8.0)
SYNTHETIC_FALLBACK_PROVENANCE = "SYNTHETIC_FALLBACK"


def synthetic_fallback_forecast() -> DelhiForecastFetch:
    """A clearly-labeled SYNTHETIC_FALLBACK forecast for the 0-3h window.

    Deterministic: the same four intensities every time, anchored to the
    current hour. Diagnostics make the fallback visible at the API level;
    provenance per bin is SYNTHETIC_FALLBACK (never DERIVED, never
    observed, never presented as live weather).
    """
    now_utc = datetime.now(timezone.utc)
    now_ist = now_utc.astimezone(IST)
    hour_start = now_ist.replace(minute=0, second=0, microsecond=0)
    bins = []
    for i, mm in enumerate(SYNTHETIC_FALLBACK_PROFILE_MM):
        t0 = hour_start + timedelta(hours=i)
        bins.append(ForecastBin(
            time_start=t0,
            time_end=t0 + timedelta(hours=1),
            depth_mm=float(mm),
            provenance=SYNTHETIC_FALLBACK_PROVENANCE,
        ))
    return DelhiForecastFetch(
        status="SYNTHETIC_FALLBACK",
        reference_point="Kushak catchment window (synthetic demo forcing)",
        latitude=28.5595,
        longitude=77.2265,
        acquired_at=now_utc,
        bins=tuple(bins),
        diagnostics=[
            "Live NWP forecast unavailable — serving a labeled SYNTHETIC_"
            "FALLBACK rainfall series so the system remains usable. These "
            "are NOT observed measurements and NOT a weather forecast.",
        ],
        source="SYNTHETIC_FALLBACK demo rainfall series (deterministic, bounded)",
    )


def fetch_forecast_with_fallback(use_cache: bool = True) -> DelhiForecastFetch:
    """NWP forecast when obtainable; labeled synthetic demo series otherwise."""
    fetch = fetch_delhi_rainfall_forecast(use_cache=use_cache)
    if fetch.status == "UNAVAILABLE" or not fetch.bins:
        fb = synthetic_fallback_forecast()
        fb.diagnostics = list(fetch.diagnostics) + fb.diagnostics
        return fb
    return fetch


def client_forecast_fetch(mm_values: Sequence[float]) -> DelhiForecastFetch:
    """A client-assisted Open-Meteo forecast fetch when cloud egress is rate-limited (HTTP 429)."""
    now_utc = datetime.now(timezone.utc)
    now_ist = now_utc.astimezone(IST)
    hour_start = now_ist.replace(minute=0, second=0, microsecond=0)
    bins = []
    for i, mm in enumerate(mm_values[:4]):
        t0 = hour_start + timedelta(hours=i)
        bins.append(ForecastBin(
            time_start=t0,
            time_end=t0 + timedelta(hours=1),
            depth_mm=float(mm),
            provenance="DERIVED",
        ))
    return DelhiForecastFetch(
        status="COMPUTED",
        reference_point="Safdarjung (Open-Meteo NWP client-assisted ingest)",
        latitude=28.5862,
        longitude=77.2090,
        acquired_at=now_utc,
        bins=tuple(bins),
        diagnostics=[],
        source="Open-Meteo NWP hourly forecast (client-assisted ingest)",
    )


# ---------------------------------------------------------------------------
# Street/intersection geometry indexes (built once, cached process-wide)
# ---------------------------------------------------------------------------


class RoadSegmentIndex:
    """Columnar (CSR-style) index of road segments over surface cells.

    One entry per deduplicated directed edge, in graph insertion order. The
    previous representation stored a dict, a cell list and a nested
    coordinate list PER SEGMENT: ~380k permanently reachable Python objects
    (~100 MB) describing data that is actually five pointer lists plus three
    flat arrays. Nothing about the CONTENT changed - same segment order, same
    edge keys, same matched cell indices in the same order, same coordinates,
    same lengths (pinned by backend/tests/test_delhi_memory_refactor.py).

    ``edge_keys``/``road_ids``/``names``/``highways``/``osm_ids`` reference
    the string/int objects already owned by the road graph, so the lists cost
    8 bytes per entry and never re-box a JSON scalar (avoids numpy-scalar
    leaking into API payloads too).
    """

    __slots__ = (
        "edge_keys", "road_ids", "names", "highways", "osm_ids",
        "lengths_m", "coords", "cell_offsets", "cells_flat",
    )

    def __init__(
        self,
        edge_keys: List[str],
        road_ids: List[str],
        names: List[str],
        highways: List[str],
        osm_ids: List[int],
        lengths_m: np.ndarray,
        coords: np.ndarray,
        cell_offsets: np.ndarray,
        cells_flat: np.ndarray,
    ) -> None:
        self.edge_keys = edge_keys
        self.road_ids = road_ids
        self.names = names
        self.highways = highways
        self.osm_ids = osm_ids
        self.lengths_m = lengths_m
        self.coords = coords
        self.cell_offsets = cell_offsets
        self.cells_flat = cells_flat

    def __len__(self) -> int:
        return len(self.edge_keys)

    def row(self, i: int) -> dict:
        """Row-wise view of segment ``i`` (test/reference helper)."""
        start, stop = int(self.cell_offsets[i]), int(self.cell_offsets[i + 1])
        cells = [int(c) for c in self.cells_flat[start:stop]]
        return {
            "edge_key": self.edge_keys[i],
            "road_id": self.road_ids[i],
            "name": self.names[i],
            "highway": self.highways[i],
            "length_m": float(self.lengths_m[i]),
            "osm_id": self.osm_ids[i],
            "cells": cells or None,
            "coords": [[float(c) for c in self.coords[i][0]],
                       [float(c) for c in self.coords[i][1]]],
        }

    def max_depth(self, depth_m: np.ndarray) -> np.ndarray:
        """Per-segment maximum modelled depth (m); NaN where no cell matched.

        Equivalent to ``max(depth_m[c] for c in cells)`` per segment, done as
        one vectorised segmented reduction instead of ~76k Python generators.
        """
        starts = self.cell_offsets[:-1]
        nonempty = np.flatnonzero(self.cell_offsets[1:] > starts)
        out = np.full(starts.size, np.nan)
        if nonempty.size:
            # Cells are stored in segment order, so the span between two
            # consecutive NON-EMPTY starts covers exactly the earlier
            # segment's cells (any segments in between are empty).
            out[nonempty] = np.maximum.reduceat(
                depth_m[self.cells_flat], starts[nonempty]
            )
        return out


@single_flight_cached
def _road_match_index():
    """Road segments + graph junctions with surface-window cell mapping.

    Returns (RoadSegmentIndex, junctions) where the index covers EVERY
    directed edge (deduplicated by geometry) of the Delhi road graph and
    junctions is a list of dicts (node_idx, lonlat, connecting road names)
    for graph nodes with >= 3 connections (topological intersections).
    """
    graph = get_road_graph()
    structure = get_surface_structure()

    # KD-tree over window-cell centers: O(log n) nearest-cell queries for
    # every road midpoint/junction (the matching runs once, then caches).
    try:
        import rasterio
        from scipy.spatial import cKDTree
        win_x, win_y = rasterio.transform.xy(
            structure.transform, structure.window_rows, structure.window_cols,
            offset="center",
        )
        win_x = np.asarray(win_x)
        win_y = np.asarray(win_y)
        cell_tree = cKDTree(np.column_stack([win_x, win_y]))
    except Exception:  # pragma: no cover - rasterio/scipy always present
        cell_tree = None

    from rasterio.warp import transform as rio_transform  # noqa: F401

    # Queries are issued in bounded batches: the KD-tree returns one Python
    # list per query point, and asking for all ~227k at once materialised a
    # transient object storm (the single biggest spike of a cold build).
    BATCH_SEGMENTS = 4096

    edge_keys: List[str] = []
    road_ids: List[str] = []
    names: List[str] = []
    highways: List[str] = []
    osm_ids: List[int] = []
    lengths: List[float] = []
    coord_flat: List[float] = []
    cell_offsets: List[int] = [0]
    cell_chunks: List[np.ndarray] = []

    seen_geo = set()
    batch: List[Tuple] = []  # (edge_key, ux0, uy0, ux1, uy1) - bounded

    def flush_batch() -> None:
        if not batch:
            return
        pts = np.empty((len(batch) * 3, 2), dtype=np.float64)
        for k, (_key, ux0, uy0, ux1, uy1) in enumerate(batch):
            pts[3 * k] = (ux0, uy0)
            pts[3 * k + 1] = ((ux0 + ux1) / 2.0, (uy0 + uy1) / 2.0)
            pts[3 * k + 2] = (ux1, uy1)
        near = (
            cell_tree.query_ball_point(pts, r=SAMPLE_RADIUS_M)
            if cell_tree is not None
            else [[] for _ in range(len(pts))]
        )
        flat = np.fromiter(
            (int(c) for group in near for c in group),
            dtype=np.int32,
            count=sum(len(group) for group in near),
        )
        cell_chunks.append(flat)
        pos = 0
        for key, ux0, uy0, ux1, uy1 in batch:
            edge = graph.edge_index[key]
            geo = edge.coords_4326
            edge_keys.append(key)
            road_ids.append(edge.road_id)
            names.append(edge.name)
            highways.append(edge.highway)
            osm_ids.append(edge.osm_id)
            lengths.append(edge.length_m)
            coord_flat.extend((geo[0][0], geo[0][1], geo[1][0], geo[1][1]))
            # Documented sample area: V1 matches the road/crossing AREA
            # (endpoint + midpoint + endpoint cells, in that order).
            cell_offsets.append(
                cell_offsets[-1] + len(near[pos]) + len(near[pos + 1]) + len(near[pos + 2])
            )
            pos += 3
        batch.clear()

    for edge_key, edge in graph.edge_index.items():
        geo = edge.coords_4326
        gsig = (
            round(geo[0][0], 7), round(geo[0][1], 7),
            round(geo[1][0], 7), round(geo[1][1], 7),
        )
        if gsig in seen_geo:
            continue
        seen_geo.add(gsig)
        ux0, uy0 = graph.node_xy[edge.u]
        ux1, uy1 = graph.node_xy[edge.v]
        batch.append((edge_key, ux0, uy0, ux1, uy1))
        if len(batch) >= BATCH_SEGMENTS:
            flush_batch()
    flush_batch()

    segments = RoadSegmentIndex(
        edge_keys=edge_keys,
        road_ids=road_ids,
        names=names,
        highways=highways,
        osm_ids=osm_ids,
        lengths_m=np.asarray(lengths, dtype=np.float64),
        coords=np.asarray(coord_flat, dtype=np.float64).reshape(-1, 2, 2),
        cell_offsets=np.asarray(cell_offsets, dtype=np.int64),
        cells_flat=(
            np.concatenate(cell_chunks) if cell_chunks else np.empty(0, dtype=np.int32)
        ),
    )

    # Junctions: nodes with >= 3 distinct connections (topological
    # intersections), sampled from the same graph the router uses.
    connection_names: Dict[int, set] = {}
    for node, edges in graph.adj.items():
        for e in edges:
            connection_names.setdefault(node, set()).add(e.name)

    valid_junction_nodes = [
        node for node, jnames in sorted(connection_names.items()) if len(jnames) >= 3
    ]
    j_pts = [
        [float(graph.node_xy[n][0]), float(graph.node_xy[n][1])]
        for n in valid_junction_nodes
    ]
    j_near = (
        cell_tree.query_ball_point(j_pts, r=SAMPLE_RADIUS_M)
        if cell_tree is not None and j_pts
        else [[]] * len(j_pts)
    )

    junctions: List[dict] = []
    for idx, node in enumerate(valid_junction_nodes):
        lon, lat = graph.node_lonlat[node]
        jnames = connection_names[node]
        cells = [int(c) for c in j_near[idx]]
        junctions.append({
            "node_idx": node,
            "lonlat": [lon, lat],
            "roads": sorted(jnames)[:4],
            "cells": cells or None,
        })

    return segments, junctions


# ---------------------------------------------------------------------------
# Per-horizon live state
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class HorizonLiveState:
    horizon: str
    lead_time: str
    rainfall_mm: Optional[float]
    rainfall_provenance: str
    time_start: Optional[datetime]
    time_end: Optional[datetime]
    step: Optional[V1DepthStep]
    provenance: str


def _intensity_for_horizon(fetch: DelhiForecastFetch, horizon_idx: int) -> Tuple[
    Optional[float], str, Optional[datetime], Optional[datetime]
]:
    """Rainfall for one horizon: the NWP/synthetic bin's hourly depth.

    Each horizon uses ONLY its own hour's value (V1 rule). A missing bin is
    UNKNOWN — that horizon reports UNKNOWN state, never zero-fill.
    """
    bins = fetch.bins
    if horizon_idx < len(bins):
        b = bins[horizon_idx]
        return b.depth_mm, b.provenance, b.time_start, b.time_end
    return None, "UNKNOWN", None, None


def _street_intelligence(step: V1DepthStep, structure, horizon: str) -> dict:
    """V1-style street + intersection intelligence from the depth grid."""
    index, junctions = _road_match_index()
    depth_m = step.depth_m

    roads_features = []
    affected_roads = []
    risk_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
    flooded_length = 0.0
    max_street_depth = 0.0

    # Segmented max over the CSR cell array replaces ~76k per-segment Python
    # generators; NaN marks a segment with no matched cell (UNKNOWN).
    seg_depth = index.max_depth(depth_m)
    lengths = index.lengths_m
    for i in np.flatnonzero(np.isfinite(seg_depth) & (seg_depth > 0.001)):
        depth = float(seg_depth[i])
        length_m = float(lengths[i])
        risk = classify_road_risk(depth)
        flooded_length += length_m
        max_street_depth = max(max_street_depth, depth)
        if risk in risk_counts:
            risk_counts[risk] += 1
        if depth > 0.015:
            props = {
                "road_id": index.road_ids[i],
                "osm_id": index.osm_ids[i],
                "name": index.names[i],
                "highway": index.highways[i],
                "max_depth_m": round(depth, 3),
                "flooded_length_m": round(length_m, 1),
                "risk_level": risk,
                "provenance": "SIMULATED_MODEL_OUTPUT (V1 reference depth grid)",
            }
            roads_features.append({
                "type": "Feature",
                "properties": props,
                "geometry": {"type": "LineString", "coordinates": [
                    [float(index.coords[i][0][0]), float(index.coords[i][0][1])],
                    [float(index.coords[i][1][0]), float(index.coords[i][1][1])],
                ]},
            })
            affected_roads.append(props)

    intersections_features = []
    affected_intersections = []
    for j in junctions:
        cells = j["cells"]
        depth = float(max(depth_m[c] for c in cells)) if cells else None
        risk = classify_road_risk(depth)
        if depth is not None and depth > 0.015:
            props = {
                "intersection_id": f"node-{j['node_idx']}",
                "name": " & ".join(j["roads"][:2]),
                "roads_display": " / ".join(j["roads"]),
                "max_depth_m": round(depth, 3),
                "risk_level": risk,
                "connection_count": len(j["roads"]),
                "provenance": "SIMULATED_MODEL_OUTPUT (V1 reference depth grid)",
            }
            intersections_features.append({
                "type": "Feature",
                "properties": props,
                "geometry": {"type": "Point", "coordinates": j["lonlat"]},
            })
            affected_intersections.append(props)

    affected_roads.sort(key=lambda r: r["max_depth_m"], reverse=True)
    affected_intersections.sort(key=lambda r: r["max_depth_m"], reverse=True)

    # Map payload cap: the deepest segments only (the full road set stays in
    # the routing/segment-evidence APIs; the map needs the impactful ones).
    MAX_ROAD_FEATURES = 500
    roads_features = roads_features[:MAX_ROAD_FEATURES]

    return {
        "horizon": horizon,
        "summary": {
            "total_affected_roads": len(affected_roads),
            "total_affected_intersections": len(affected_intersections),
            "max_street_depth_m": round(max_street_depth, 3),
            "total_flooded_road_length_m": round(flooded_length, 1),
            "risk_counts": risk_counts,
        },
        "affected_roads": affected_roads[:12],
        "affected_intersections": affected_intersections[:12],
        "roads_geojson": {"type": "FeatureCollection", "features": roads_features},
        "intersections_geojson": {
            "type": "FeatureCollection", "features": intersections_features,
        },
        "provenance": {
            "roads": "OpenStreetMap (ODbL) — committed pilot extract",
            "intersections": "OSM graph topology (nodes with >=3 connections)",
            "depth": "MODELLED — V1 reference depth model on the enforced "
                     "30 m Copernicus GLO-30 DSM; never observed",
            "matching": f"nearest surface cell within {MATCH_DISTANCE_M:.0f} m; "
                        "beyond that UNKNOWN (never 0 m)",
            "risk_thresholds": "V1 road-risk tiers 0.15/0.30/0.60 m (DEMO thresholds)",
        },
    }


def _state_payload(
    fetch: DelhiForecastFetch,
    horizon_idx: int,
    include_geo: bool = True,
    max_cells: int = 320,
) -> dict:
    """Full V1-style state for ONE horizon (depth + streets + provenance)."""
    horizon = HORIZON_LABELS[horizon_idx]
    rain_mm, rain_prov, t_start, t_end = _intensity_for_horizon(fetch, horizon_idx)

    if rain_mm is None:
        return {
            "horizon": horizon,
            "lead_time": LEAD_TIMES[horizon],
            "rainfall_mm": None,
            "rainfall_provenance": "UNKNOWN",
            "status": "UNKNOWN_FORCING",
            "max_depth_m": None,
            "flooded_area_m2": None,
            "flood_volume_m3": None,
            "depth_cells": [],
            "depth_polygons": {"type": "FeatureCollection", "features": []},
            "streets": None,
            "provenance": {
                "rainfall": "UNKNOWN (missing forecast hour — no zero-fill)",
                "flood": "NOT_COMPUTED",
            },
        }

    step = v1_depth_step_for_intensity(
        depth_mm=rain_mm, dt_h=1.0, timestep_index=horizon_idx
    )
    structure = get_surface_structure()
    streets = _street_intelligence(step, structure, horizon)

    max_depth_m = round(step.max_depth_m, 3)
    if max_depth_m >= ROAD_RISK_THRESHOLDS_M["CRITICAL"]:
        risk_text, risk_desc = "SEVERE", "Major inundation • significant roadway disruption"
    elif max_depth_m >= ROAD_RISK_THRESHOLDS_M["HIGH"]:
        risk_text, risk_desc = "HIGH", "Curb overflow • street flooding in low-lying areas"
    elif step.flooded_cells > 0:
        risk_text, risk_desc = "MODERATE", "Localized waterlogging in terrain depressions"
    else:
        risk_text, risk_desc = "NO INUNDATION", "Runoff conveyed by inlets • no surface ponding"

    payload = {
        "horizon": horizon,
        "lead_time": LEAD_TIMES[horizon],
        "rainfall_mm": round(rain_mm, 2),
        "rainfall_provenance": rain_prov,
        "time_start": t_start.isoformat() if t_start else None,
        "time_end": t_end.isoformat() if t_end else None,
        "status": "COMPUTED",
        "max_depth_m": max_depth_m,
        "flooded_area_m2": round(step.total_flooded_area_m2, 1),
        "flood_volume_m3": round(step.total_flooded_area_m2 * (step.max_depth_m / 2.0), 1)
        if step.flooded_cells else 0.0,
        "v1_mass_balance": {
            "total_runoff_m3": round(step.total_runoff_volume_m3, 1),
            "conveyed_m3": round(step.conveyed_volume_m3, 1),
            "surcharged_m3": round(step.surcharged_volume_m3, 1),
            "overflow_m3": round(step.overflow_volume_m3, 1),
            "drained_out_m3": round(step.drained_out_volume_m3, 1),
        },
        "risk": {"text": risk_text, "description": risk_desc},
        "depth_cells": depth_cells_from_v1(step, structure) if include_geo else [],
        "depth_polygons": (
            depth_polygons_from_v1(step, structure) if include_geo
            else {"type": "FeatureCollection", "features": []}
        ),
        "streets": streets,
        "source_type": "SIMULATED_MODEL_OUTPUT",
    }
    return payload


def build_live_states(
    fetch: DelhiForecastFetch, include_geo: bool = True
) -> dict:
    """All four horizon states from ONE forecast fetch (cached upstream)."""
    horizons = [_state_payload(fetch, i, include_geo=include_geo) for i in range(4)]
    computed = [h for h in horizons if h["status"] == "COMPUTED"]
    peak = max(
        (h["max_depth_m"] for h in computed if h["max_depth_m"] is not None),
        default=None,
    )
    peak_street = max(
        (
            h["streets"]["summary"]["max_street_depth_m"]
            for h in computed if h["streets"]
        ),
        default=0.0,
    )
    return {
        "rainfall_status": fetch.status,  # COMPUTED | STALE | SYNTHETIC_FALLBACK
        "rainfall_source": fetch.source,
        "rainfall_acquired_at": fetch.acquired_at.isoformat() if fetch.acquired_at else None,
        "diagnostics": list(fetch.diagnostics),
        "horizons": horizons,
        "peak": {
            "max_depth_m": peak,
            "peak_horizon": (
                next(
                    (h["horizon"] for h in computed if h["max_depth_m"] == peak),
                    None,
                )
                if peak is not None else None
            ),
            "max_street_depth_m": round(peak_street, 3),
            "total_flooded_area_m2": round(
                max(
                    (h["flooded_area_m2"] or 0.0 for h in computed),
                    default=0.0,
                ), 1
            ),
        },
        "claim_policy": (
            "MODELLED flood states: the V1 reference depth model per forecast "
            "hour on the enforced 30 m DSM. Never observed depth, never a "
            "guarantee. UNKNOWN hours stay UNKNOWN."
        ),
        "provenance": {
            "rainfall": fetch.source,
            "rainfall_status": fetch.status,
            "depth": "MODELLED (V1 reference model, 30 m enforced DSM)",
            "streets": "OSM roads/junctions matched to modelled depth grid",
            "model_convention": CONVEYANCE_NOTE,
        },
    }


# ---------------------------------------------------------------------------
# WHAT-IF scenario state (free intensity; labeled MODEL_SCENARIO)
# ---------------------------------------------------------------------------

WHAT_IF_PRESETS_MM = (20.0, 40.0, 50.0, 70.0)


def build_what_if_state(rainfall_mm_h: float) -> dict:
    """V1-style what-if state for ONE uniform intensity (mm/h).

    The same shared depth model as the live states — a scenario input
    triggers REAL backend computation. Labeled MODEL_SCENARIO / WHAT-IF
    everywhere; never presented as live weather or a forecast.
    """
    if not 0 <= rainfall_mm_h <= 250:
        raise ValueError("rainfall_mm_h must be within [0, 250] mm/h")
    step = v1_depth_step_for_intensity(
        depth_mm=rainfall_mm_h, dt_h=1.0, timestep_index=0
    )
    structure = get_surface_structure()
    streets = _street_intelligence(step, structure, "SCENARIO")
    max_depth_m = round(step.max_depth_m, 3)
    return {
        "scenario": {
            "kind": "MODEL_SCENARIO",
            "label": "WHAT-IF",
            "rainfall_mm_h": round(rainfall_mm_h, 1),
            "note": (
                "Hypothetical uniform rainfall input — evaluated through the "
                "same modelled pipeline as LIVE. NOT live weather, NOT a "
                "forecast, NOT an observed event."
            ),
        },
        "status": "COMPUTED",
        "max_depth_m": max_depth_m,
        "flooded_area_m2": round(step.total_flooded_area_m2, 1),
        "v1_mass_balance": {
            "total_runoff_m3": round(step.total_runoff_volume_m3, 1),
            "conveyed_m3": round(step.conveyed_volume_m3, 1),
            "surcharged_m3": round(step.surcharged_volume_m3, 1),
            "overflow_m3": round(step.overflow_volume_m3, 1),
            "drained_out_m3": round(step.drained_out_volume_m3, 1),
        },
        "depth_cells": depth_cells_from_v1(step, structure),
        "depth_polygons": depth_polygons_from_v1(step, structure),
        "streets": streets,
        "source_type": "SIMULATED_MODEL_OUTPUT",
        "provenance": {
            "rainfall": f"MODEL_SCENARIO input ({rainfall_mm_h} mm/h uniform)",
            "depth": "MODELLED (V1 reference model, 30 m enforced DSM)",
            "streets": "OSM roads/junctions matched to modelled depth grid",
        },
    }


# ---------------------------------------------------------------------------
# Depth-derived road risk override (scenario routing; canonical thresholds)
# ---------------------------------------------------------------------------


def road_risk_override_from_depths(
    edge_depths: Dict[str, Optional[float]],
) -> Dict[str, Tuple[str, str]]:
    """V1-style depth-based routing risk from the modelled street depths.

    Uses the canonical scenario config thresholds (single source: 
    ``scenarios.config.depth_config``): segments at/above the hazard
    threshold are ELEVATED_RISK, at/above the exclusion threshold are
    BLOCKED (hard-excluded from candidate routes) — the V1 routing
    behavior, with the Delhi-window's documented demo thresholds.
    """
    from backend.app.domain.delhi.scenarios.config import (
        ROUTING_EXCLUDE_CM,
        ROUTING_HAZARD_CM,
    )

    out: Dict[str, Tuple[str, str]] = {}
    for edge_key, depth_m in edge_depths.items():
        if depth_m is None:
            out[edge_key] = ("UNKNOWN", "no modelled depth sample for this segment")
            continue
        cm = depth_m * 100.0
        if cm >= ROUTING_EXCLUDE_CM:
            out[edge_key] = (
                "BLOCKED",
                f"modelled depth {cm:.0f} cm >= {ROUTING_EXCLUDE_CM:.0f} cm "
                "exclusion threshold (MODEL_SCENARIO what-if)",
            )
        elif cm >= ROUTING_HAZARD_CM:
            out[edge_key] = (
                "ELEVATED_RISK",
                f"modelled depth {cm:.0f} cm >= {ROUTING_HAZARD_CM:.0f} cm "
                "hazard threshold (MODEL_SCENARIO what-if)",
            )
        else:
            out[edge_key] = (
                "LOW_RISK",
                f"modelled depth {cm:.1f} cm below the {ROUTING_HAZARD_CM:.0f} cm "
                "hazard threshold (MODEL_SCENARIO what-if)",
            )
    return out


def what_if_edge_depths(rainfall_mm_h: float) -> Dict[str, Optional[float]]:
    """Return {edge_key: modelled depth (m) | None} for ONE what-if intensity.
    Cached (deterministic); used by the scenario safe-route mode."""
    step = v1_depth_step_for_intensity(
        depth_mm=rainfall_mm_h, dt_h=1.0, timestep_index=0
    )
    index, _ = _road_match_index()
    depth_m = step.depth_m
    seg_depth = index.max_depth(depth_m)
    return {
        edge_key: (None if not np.isfinite(d) else float(d))
        for edge_key, d in zip(index.edge_keys, seg_depth)
    }


# ---------------------------------------------------------------------------
# Cached builders (deterministic per forecast acquisition; Stage-7 perf)
# ---------------------------------------------------------------------------

_LIVE_STATES_CACHE: Dict[str, dict] = {}
_LIVE_STATES_CACHE_KEY: Optional[str] = None
_WHAT_IF_CACHE: Dict[str, dict] = {}
_WHAT_IF_EDGE_DEPTHS_CACHE: Dict[str, Dict[str, Optional[float]]] = {}


def get_cached_live_states(
    use_cache: bool = True,
    include_geo: bool = True,
    client_rainfall_mm: Optional[Sequence[float]] = None,
) -> dict:
    """Live states keyed by forecast acquisition (deterministic; cached).

    The expensive part (surface structure + routing) is lru_cached in the
    depth model; the per-horizon step runs are cached per forecast fetch so
    repeated horizon clicks are instant.
    """
    global _LIVE_STATES_CACHE_KEY
    if client_rainfall_mm is not None and len(client_rainfall_mm) >= 4:
        fetch = client_forecast_fetch(client_rainfall_mm)
        key = f"client:{','.join(str(round(v, 2)) for v in client_rainfall_mm[:4])}"
    else:
        fetch = fetch_forecast_with_fallback(use_cache=use_cache)
        key = f"{fetch.acquired_at.isoformat() if fetch.acquired_at else 'none'}:{fetch.status}"
    if use_cache and _LIVE_STATES_CACHE_KEY == key and "states" in _LIVE_STATES_CACHE:
        cached = _LIVE_STATES_CACHE["states"]
        if include_geo:
            return cached
        # Geo-less variant for cheap polling (strip heavy arrays).
        stripped = json.loads(json.dumps(cached))  # deep copy
        for h in stripped.get("horizons", []):
            h["depth_cells"] = []
            h["depth_polygons"] = {"type": "FeatureCollection", "features": []}
            if h.get("streets"):
                h["streets"]["roads_geojson"] = {"type": "FeatureCollection", "features": []}
                h["streets"]["intersections_geojson"] = {"type": "FeatureCollection", "features": []}
        return stripped
    states = build_live_states(fetch, include_geo=include_geo)
    _LIVE_STATES_CACHE_KEY = key
    _LIVE_STATES_CACHE["states"] = states
    return states


def get_cached_what_if(rainfall_mm_h: float) -> dict:
    """Deterministic what-if cache keyed by rounded intensity."""
    key = str(round(rainfall_mm_h, 1))
    if key not in _WHAT_IF_CACHE:
        _WHAT_IF_CACHE[key] = build_what_if_state(rainfall_mm_h)
    return _WHAT_IF_CACHE[key]


def get_cached_what_if_edge_depths(rainfall_mm_h: float) -> Dict[str, Optional[float]]:
    """Cached per-edge modelled depths for one what-if intensity."""
    key = str(round(rainfall_mm_h, 1))
    if key not in _WHAT_IF_EDGE_DEPTHS_CACHE:
        _WHAT_IF_EDGE_DEPTHS_CACHE[key] = what_if_edge_depths(rainfall_mm_h)
    return _WHAT_IF_EDGE_DEPTHS_CACHE[key]
