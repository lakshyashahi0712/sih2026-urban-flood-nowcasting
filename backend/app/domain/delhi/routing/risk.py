"""Road-risk mapping: corridor geometry, hydraulic→road translation,
evidence state, and freshness.

SCIENTIFIC CONTRACT (documented translation layer — see docs/SAFE_ROUTING.md):

- Only roads spatially mapped to the modeled Kushak corridor receive
  model-informed risk; everything else is explicitly UNKNOWN ("outside
  modeled corridor"). Never guessed.
- The hydraulic runtime produces states WITHOUT stage (no storage-stage
  relation exists) and without depth. Therefore the translation NEVER
  claims road passability or water depth, and NEVER emits BLOCKED or
  SAFE from model data alone:
    - member step blocked / no computed state  -> UNKNOWN
    - computed, positive loading (inflow > 0 or storage accumulation) -> ELEVATED_RISK
    - computed, zero loading across agreeing members -> LOW_RISK
  ELEVATED_RISK means "modeled conveyance loading under the active
  scenario", NOT observed flooding and NOT a depth claim.
- Member aggregation is weakest-link: any blocked/unknown member makes
  the segment UNKNOWN. Scenario disagreement is reported, never hidden.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from shapely.geometry import LineString, Point
from shapely.ops import substring

from .network import DelhiRoadGraph, SegmentEdge, get_road_graph

_REPO_ROOT = Path(__file__).resolve().parents[5]
CENTERLINE_PATH = (
    _REPO_ROOT / "data" / "delhi" / "derived" / "hydraulic" / "kushak_corridor_centerline.geojson"
)

# ASSUMED engineering threshold: a road within this distance of a reach
# centerline is mapped to that reach for risk translation. Exposed here
# so it is a documented assumption, not a hidden constant.
CORRIDOR_MAP_DISTANCE_M = 150.0

# Reach chainages (locked Phase 8B model reaches).
REACH_CHAINAGES: Tuple[Tuple[str, float, float], ...] = (
    ("UG-01", 0.0, 2318.5),
    ("OC-01", 2318.5, 3700.0),
    ("CD-01", 3700.0, 4700.0),
    ("OC-02", 4700.0, 5027.56),
)

RiskState = str  # LOW_RISK | ELEVATED_RISK | BLOCKED | UNKNOWN


@dataclass(frozen=True)
class ReachCorridor:
    """Model-reach corridor linework in UTM 43N with an STRtree index."""

    reach_ids: Tuple[str, ...]
    lines: Tuple[LineString, ...]
    tree: "STRtreeWrapper"


class STRtreeWrapper:
    """Small index wrapper pairing STRtree results with reach ids."""

    def __init__(self, lines: List[LineString]) -> None:
        from shapely.strtree import STRtree

        self._tree = STRtree(lines)
        self._lines = lines

    def nearest(self, geom) -> int:
        return int(self._tree.nearest(geom))

    def line(self, idx: int) -> LineString:
        return self._lines[idx]


@lru_cache(maxsize=1)
def get_reach_corridor() -> ReachCorridor:
    """Build reach-resolved corridor linework from the derived centerline.

    The centerline's underground segment (Africa Avenue Subsurface
    Stormwater Conduit) is UG-01. The open trunk (Kushak Nallah Open
    Trunk Drain) is split by cumulative-length fraction into OC-01 /
    CD-01 / OC-02 using the locked reach chainages (DERIVED
    approximation: uniform chainage rate along the digitized centerline).
    """
    data = json.loads(CENTERLINE_PATH.read_text(encoding="utf-8"))
    underground: Optional[LineString] = None
    open_trunk: Optional[LineString] = None
    for feature in data.get("features", []):
        props = feature.get("properties", {})
        geom = feature.get("geometry", {})
        if geom.get("type") != "LineString":
            continue
        name = props.get("name", "")
        if "Subsurface" in name:
            underground = LineString(geom["coordinates"])
        elif "Open Trunk" in name:
            open_trunk = LineString(geom["coordinates"])
    if underground is None or open_trunk is None:
        raise RuntimeError("corridor centerline is missing its documented segments")

    def utm_line(line_wgs84: LineString) -> LineString:
        from rasterio.warp import transform as rio_transform

        lons = [c[0] for c in line_wgs84.coords]
        lats = [c[1] for c in line_wgs84.coords]
        xs, ys = rio_transform("EPSG:4326", "EPSG:32643", lons, lats)
        return LineString(zip(xs, ys))

    underground_utm = utm_line(underground)
    open_utm = utm_line(open_trunk)

    open_total = REACH_CHAINAGES[3][2] - REACH_CHAINAGES[1][1]
    lines: List[LineString] = [underground_utm]
    reach_ids: List[str] = ["UG-01"]
    for reach_id, start, end in REACH_CHAINAGES[1:]:
        f0 = (start - REACH_CHAINAGES[1][1]) / open_total
        f1 = (end - REACH_CHAINAGES[1][1]) / open_total
        segment = substring(open_utm, f0 * open_utm.length, f1 * open_utm.length)
        lines.append(segment)
        reach_ids.append(reach_id)

    return ReachCorridor(
        reach_ids=tuple(reach_ids),
        lines=tuple(lines),
        tree=STRtreeWrapper(lines),
    )


# ---------------------------------------------------------------------------
# Edge -> reach mapping
# ---------------------------------------------------------------------------


@lru_cache(maxsize=1)
def build_edge_reach_map() -> Dict[str, Optional[str]]:
    """Map every graph edge to its nearest reach within the documented
    threshold, else None (outside modeled corridor -> UNKNOWN)."""
    graph = get_road_graph()
    corridor = get_reach_corridor()
    mapping: Dict[str, Optional[str]] = {}
    for edge_key, edge in graph.edge_index.items():
        mx = (graph.node_xy[edge.u][0] + graph.node_xy[edge.v][0]) / 2.0
        my = (graph.node_xy[edge.u][1] + graph.node_xy[edge.v][1]) / 2.0
        pt = Point(mx, my)
        nearest = corridor.tree.nearest(pt)
        dist = pt.distance(corridor.tree.line(nearest))
        mapping[edge_key] = corridor.reach_ids[nearest] if dist <= CORRIDOR_MAP_DISTANCE_M else None
    return mapping


# ---------------------------------------------------------------------------
# Hydraulic state -> road risk translation (the documented layer)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ReachStateObservation:
    """Aggregated ensemble state of ONE model reach at ONE timestep."""

    reach_id: str
    any_member_blocked: bool
    blocked_members: int
    computed_members: int
    any_positive_loading: bool
    all_zero_loading: bool
    loading_basis: str  # documented basis of the loading determination


def translate_reach_to_road_risk(obs: Optional[ReachStateObservation]) -> Tuple[RiskState, str]:
    """The ONLY place hydraulic state becomes road risk.

    Returns (risk_state, reason). The mapping is DERIVED from model state
    with ASSUMED interpretation (loading-based, stage-less). It never
    emits BLOCKED or SAFE from model data: the Kushak runtime has no
    defensible depth, so "blocked road" cannot be established.
    """
    if obs is None or obs.any_member_blocked or obs.computed_members == 0:
        return "UNKNOWN", (
            "no defensible model state for the mapped reach"
            + (f" ({obs.blocked_members}/6 members blocked)" if obs else "")
            if obs is not None and obs.any_member_blocked
            else "no computed model state for the mapped reach"
        )
    if obs.any_positive_loading:
        return "ELEVATED_RISK", (
            "modeled conveyance loading present in the mapped reach "
            f"({obs.loading_basis}); stage is UNKNOWN — no depth or "
            "passability claim is made"
        )
    if obs.all_zero_loading:
        return "LOW_RISK", (
            "no modeled runoff loading in the mapped reach under the "
            f"documented scenario ({obs.loading_basis}); stage remains "
            "UNKNOWN — this is not a guarantee of dry conditions"
        )
    return "UNKNOWN", "insufficient model state"


def aggregate_reach_states(
    member_states: List[Dict[str, Dict[str, Optional[float]]]],
    reach_ids: Tuple[str, ...] = tuple(r[0] for r in REACH_CHAINAGES),
) -> Dict[str, ReachStateObservation]:
    """Aggregate per-member reach states at ONE timestep.

    member_states: one dict per member of reach_id -> {
        status: str (continuity status value),
        incoming_flow_m3_s: float | None,
        storage_m3: float | None,
    }
    Initial storage (10000 m³, ASSUMED scenario convention) is used as the
    accumulation baseline.
    """
    observations: Dict[str, ReachStateObservation] = {}
    n_members = len(member_states)
    for reach_id in reach_ids:
        blocked = 0
        computed = 0
        positive = 0
        zero = 0
        bases: List[str] = []
        for states in member_states:
            st = states.get(reach_id)
            if st is None:
                blocked += 1
                continue
            status = str(st.get("status", ""))
            inflow = st.get("incoming_flow_m3_s")
            storage = st.get("storage_m3")
            if status.startswith("BLOCKED") or inflow is None or storage is None:
                blocked += 1
                continue
            computed += 1
            if inflow > 0.0 or storage > 10000.0 + 1e-6:
                positive += 1
                basis = []
                if inflow > 0.0:
                    basis.append(f"inflow {inflow:.1f} m³/s")
                if storage > 10000.0 + 1e-6:
                    basis.append(f"storage {storage:.0f} m³ (> initial)")
                bases.append("+".join(basis))
            elif inflow == 0.0 and abs(storage - 10000.0) <= 1e-6:
                zero += 1
            else:
                # storage <= initial with zero inflow: no loading either
                zero += 1
        observations[reach_id] = ReachStateObservation(
            reach_id=reach_id,
            any_member_blocked=blocked > 0,
            blocked_members=blocked,
            computed_members=computed,
            any_positive_loading=positive > 0,
            all_zero_loading=computed > 0 and positive == 0 and zero == computed,
            loading_basis="; ".join(bases[:2]) if bases else "zero inflow, storage at initial",
        )
    return observations


# ---------------------------------------------------------------------------
# Evidence state + freshness (documented derivations)
# ---------------------------------------------------------------------------


def route_evidence_state(
    total_edges: int, covered_edges: int, has_unknown_on_route: bool, member_disagreement: bool
) -> Tuple[str, str]:
    """Route-level evidence state (documented rule, weakest-link).

    - UNKNOWN: no route segment has model coverage at all.
    - LOW: any route segment is UNKNOWN (a single unknown portion caps the
      whole route — coverage is never averaged away).
    - MEDIUM: every segment covered, but ensemble members disagree.
    - HIGH: every segment covered with full member agreement.
    """
    if total_edges == 0 or covered_edges == 0:
        return "UNKNOWN", "no route segment has model-state coverage"
    if has_unknown_on_route:
        return "LOW", (
            f"{total_edges - covered_edges} of {total_edges} route segments "
            "have no model-state coverage; a single unknown portion caps "
            "the route evidence state (weakest link)"
        )
    if member_disagreement:
        return "MEDIUM", "all segments covered, but ensemble members disagree on the modeled loading"
    return "HIGH", "all segments covered with full ensemble agreement"


FRESH_S, RECENT_S = 15 * 60, 60 * 60


def freshness_state(timestamp: Optional[datetime], now: datetime) -> str:
    """FRESH / RECENT / STALE / UNKNOWN freshness classification.

    Documented thresholds: FRESH <= 15 min, RECENT <= 60 min, STALE beyond.
    """
    if timestamp is None:
        return "UNKNOWN"
    age_s = abs((now - timestamp).total_seconds())
    if age_s <= FRESH_S:
        return "FRESH"
    if age_s <= RECENT_S:
        return "RECENT"
    return "STALE"


def segment_evidence(
    edge_key: str,
    risk_state: RiskState,
    reason: str,
    mapped_reach: Optional[str],
    model_state: Optional[Dict[str, object]],
    mode: str,
    event_id: Optional[str],
    timestep_index: Optional[int],
    model_timestamp: Optional[str],
    forcing_source: Optional[str],
) -> dict:
    """Segment-level evidence record (28-style traceability)."""
    graph = get_road_graph()
    edge = graph.edge_index.get(edge_key)
    if edge is None:
        return {"edge_key": edge_key, "error": "unknown segment"}
    corridor_mapped = mapped_reach is not None
    return {
        "segment_id": edge_key,
        "geometry_source": (
            "OpenStreetMap (committed pilot GeoJSON; ODbL) — see "
            "delhi_kushak_roads.provenance.json"
        ),
        "name": edge.name,
        "highway": edge.highway,
        "length_m": round(edge.length_m, 1),
        "risk_state": risk_state,
        "risk_reason": reason,
        "spatial_mapping": {
            "method": "distance-to-reach-centerline (midpoint), documented threshold",
            "threshold_m": CORRIDOR_MAP_DISTANCE_M,
            "threshold_provenance": "ASSUMED engineering constant",
            "mapped_reach": mapped_reach,
            "status": "MAPPED" if corridor_mapped else "OUTSIDE_MODELED_CORRIDOR",
        },
        "hydraulic_state": model_state,
        "mode": mode,
        "event_id": event_id,
        "timestep_index": timestep_index,
        "model_timestamp": model_timestamp,
        "forcing_source": forcing_source,
        "evidence_state": (
            "MAPPED_MODEL_DERIVED" if corridor_mapped else "UNKNOWN"
        ),
    }
