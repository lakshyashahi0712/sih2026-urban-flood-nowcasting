"""Drainage graph loading + honest depth-estimate layer.

LOADING (scenario-derived, never observed): given aggregated model reach
states (LIVE nowcast or HISTORICAL replay), each graph edge is mapped to
its model reach, and the peak modeled inflow for that reach is compared
against the edge's inferred-effective capacity RANGE:

    inflow == 0                        -> NO_LOADING
    0 < inflow <= capacity_min          -> WITHIN_CAPACITY_RANGE
    inflow > capacity_min               -> POTENTIAL_OVERLOAD (lower bound
                                           of the documented capacity class
                                           already breached — the
                                           scenario-consistent 'backflow
                                           potential' condition)
    reach blocked / unknown             -> UNKNOWN

POTENTIAL_OVERLOAD is a scenario-consistent capacity-exceedance flag for
the lower capacity bound — NOT an observed flood and NOT a depth claim.

DEPTH ESTIMATE (ESTIMATED_UNDER_ASSUMED_GEOMETRY): a single-store prism
proxy, channel depth = storage / (length x effective width), using the
documented geometry class ranges -> a depth RANGE in cm, plus the
surface-ponding proxy from the 2D pass. Labeled everywhere as an
estimate under assumed geometry, never observed depth.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

from ..routing.state_source import ModeReachStates
from .graph import (
    JIR_DEPTH,
    NIT52_WIDTH,
    DrainageEdge,
    DrainageGraph,
    build_drainage_graph,
    get_drainage_graph,
)

INITIAL_STORAGE_M3 = 10000.0


@dataclass(frozen=True)
class EdgeLoading:
    edge_id: str
    node_id: str  # downstream node (where surcharge materializes)
    reach_id: str
    inflow_m3_s: Optional[float]
    capacity_min_m3_s: float
    capacity_max_m3_s: float
    status: str  # NO_LOADING | WITHIN_CAPACITY_RANGE | POTENTIAL_OVERLOAD | UNKNOWN
    reason: str


def edge_loading_for_reach_states(
    mode_states: ModeReachStates,
    graph: Optional[DrainageGraph] = None,
) -> List[EdgeLoading]:
    """Per-edge loading from the aggregated mode states (real runs)."""
    graph = graph or get_drainage_graph()
    from ..routing.risk import aggregate_reach_states, translate_reach_to_road_risk

    observations = aggregate_reach_states(mode_states.member_states)
    # Peak modeled inflow per reach across computed members.
    inflow_by_reach: Dict[str, Optional[float]] = {}
    for reach_id, obs in observations.items():
        if obs.any_member_blocked or obs.computed_members == 0:
            inflow_by_reach[reach_id] = None
            continue
        # Aggregate state carries a boolean loading flag, not the peak; use
        # per-member peaks for the magnitude.
        inflow_by_reach[reach_id] = _peak_member_inflow(mode_states, reach_id)

    result: List[EdgeLoading] = []
    for edge in graph.edges:
        inflow = inflow_by_reach.get(edge.reach_id)
        if inflow is None:
            result.append(EdgeLoading(
                edge_id=edge.edge_id,
                node_id=edge.downstream_node_id,
                reach_id=edge.reach_id,
                inflow_m3_s=None,
                capacity_min_m3_s=edge.capacity_min_m3_s,
                capacity_max_m3_s=edge.capacity_max_m3_s,
                status="UNKNOWN",
                reason="model state for the mapped reach is blocked/UNKNOWN; "
                "no loading determination (never zero-interpreted)",
            ))
        elif inflow <= 0.0:
            result.append(EdgeLoading(
                edge_id=edge.edge_id,
                node_id=edge.downstream_node_id,
                reach_id=edge.reach_id,
                inflow_m3_s=0.0,
                capacity_min_m3_s=edge.capacity_min_m3_s,
                capacity_max_m3_s=edge.capacity_max_m3_s,
                status="NO_LOADING",
                reason="no modeled inflow into the mapped reach under the "
                "documented scenario",
            ))
        elif inflow <= edge.capacity_min_m3_s:
            result.append(EdgeLoading(
                edge_id=edge.edge_id,
                node_id=edge.downstream_node_id,
                reach_id=edge.reach_id,
                inflow_m3_s=round(inflow, 2),
                capacity_min_m3_s=edge.capacity_min_m3_s,
                capacity_max_m3_s=edge.capacity_max_m3_s,
                status="WITHIN_CAPACITY_RANGE",
                reason=f"modeled inflow {inflow:.1f} m3/s within the inferred "
                f"capacity range [{edge.capacity_min_m3_s:.0f}, "
                f"{edge.capacity_max_m3_s:.0f}] m3/s (scenario-derived)",
            ))
        else:
            result.append(EdgeLoading(
                edge_id=edge.edge_id,
                node_id=edge.downstream_node_id,
                reach_id=edge.reach_id,
                inflow_m3_s=round(inflow, 2),
                capacity_min_m3_s=edge.capacity_min_m3_s,
                capacity_max_m3_s=edge.capacity_max_m3_s,
                status="POTENTIAL_OVERLOAD",
                reason=(
                    f"modeled inflow {inflow:.1f} m3/s EXCEEDS the lower "
                    "bound of the documented capacity class "
                    f"[{edge.capacity_min_m3_s:.0f}, {edge.capacity_max_m3_s:.0f}] "
                    "m3/s — scenario-consistent backflow/surcharge POTENTIAL "
                    "(not observed, not a depth claim)"
                ),
            ))
    return result


def _peak_member_inflow(mode_states: ModeReachStates, reach_id: str) -> Optional[float]:
    """Peak incoming flow for a reach across computed members."""
    peaks: List[float] = []
    for member in mode_states.member_states:
        st = member.get(reach_id)
        if st is None:
            continue
        q = st.get("incoming_flow_m3_s")
        if q is not None and q > 0:
            peaks.append(q)
    return max(peaks) if peaks else (0.0 if any(
        (m.get(reach_id) or {}).get("incoming_flow_m3_s") == 0.0
        for m in mode_states.member_states
        if m.get(reach_id)
    ) else None)


# ---------------------------------------------------------------------------
# Honest depth-estimate layer (ESTIMATED_UNDER_ASSUMED_GEOMETRY)
# ---------------------------------------------------------------------------


def channel_depth_estimate_cm(
    edge: DrainageEdge,
    storage_m3: Optional[float],
    initial_storage_m3: float = INITIAL_STORAGE_M3,
) -> Dict[str, Optional[float]]:
    """Single-store prism proxy: depth = storage / (length x effective
    width), using the DOCUMENTED geometry class ranges -> a cm RANGE.

    Returns None when storage is UNKNOWN. The estimate is labeled
    ESTIMATED_UNDER_ASSUMED_GEOMETRY everywhere it is surfaced — it is
    not a hydraulic stage and not an observed depth.
    """
    if storage_m3 is None:
        return {
            "depth_min_cm": None,
            "depth_max_cm": None,
            "status": "UNKNOWN",
            "reason": "storage UNKNOWN for the mapped reach; no estimate",
        }
    length = edge.length_m
    if length <= 0:
        return {"depth_min_cm": None, "depth_max_cm": None, "status": "UNKNOWN",
                "reason": "edge length invalid"}
    if edge.reach_id == "UG-01":
        w_lo, w_hi = NIT52_WIDTH
        cap_h = JIR_DEPTH[1]
    else:
        # Open edges: use the documented cross-section width class derived
        # from the bounding sections (bottom width), approximated from the
        # edge's dimension basis text via the bounding CS values.
        w_lo, w_hi = _open_width_range(edge)
        cap_h = None  # open reaches: no documented height cap used
    vol = max(storage_m3 - initial_storage_m3, 0.0)  # above-initial only
    if vol <= 0:
        return {"depth_min_cm": 0.0, "depth_max_cm": 0.0, "status": "ESTIMATED",
                "reason": "storage at/below the documented initial condition"}
    d_min = (vol / (length * w_hi)) * 100.0
    d_max = (vol / (length * w_lo)) * 100.0
    if cap_h is not None:
        d_max = min(d_max, cap_h * 100.0)  # cannot exceed the box class height
    return {
        "depth_min_cm": round(d_min, 1),
        "depth_max_cm": round(d_max, 1),
        "status": "ESTIMATED",
        "reason": (
            "single-store prism proxy under ESTIMATED_UNDER_ASSUMED_GEOMETRY "
            f"(length {length:.0f} m; width class {w_lo:.1f}-{w_hi:.1f} m; "
            "storage above the documented initial condition). Not hydraulic "
            "stage, not observed depth."
        ),
    }


def _open_width_range(edge: DrainageEdge) -> Tuple[float, float]:
    """Bounds of the open-reach width from the edge dimension basis text
    (the documented cross-section bottom widths)."""
    import re

    m = re.search(r"bottom ([\d.]+)-([\d.]+) m", edge.dimension_basis)
    if m:
        return float(m.group(1)), float(m.group(2))
    return 6.5, 18.0  # documented corridor range (CS-01 .. CS-07)


def depth_estimates_for_reach_states(
    mode_states: ModeReachStates,
    graph: Optional[DrainageGraph] = None,
) -> Dict[str, Dict[str, object]]:
    """Per-edge depth estimate range + loading, from real mode states."""
    graph = graph or get_drainage_graph()
    from ..routing.risk import aggregate_reach_states

    observations = aggregate_reach_states(mode_states.member_states)
    storage_by_reach: Dict[str, Optional[float]] = {
        rid: (obs.any_member_blocked and None or _peak_member_storage(mode_states, rid))
        for rid, obs in observations.items()
    }
    out: Dict[str, Dict[str, object]] = {}
    for edge in graph.edges:
        storage = storage_by_reach.get(edge.reach_id)
        est = channel_depth_estimate_cm(edge, storage)
        out[edge.edge_id] = {
            "reach_id": edge.reach_id,
            "node_id": edge.downstream_node_id,
            "storage_m3": storage,
            **est,
            "provenance": "ESTIMATED_UNDER_ASSUMED_GEOMETRY",
            "caveat": (
                "depth estimate under assumed prism geometry and the "
                "documented initial-storage convention; NOT observation, "
                "NOT hydraulic stage, NOT street depth"
            ),
        }
    return out


def _peak_member_storage(mode_states: ModeReachStates, reach_id: str) -> Optional[float]:
    vals = [
        (m.get(reach_id) or {}).get("storage_m3")
        for m in mode_states.member_states
        if m.get(reach_id)
    ]
    known = [v for v in vals if v is not None]
    return max(known) if known else None