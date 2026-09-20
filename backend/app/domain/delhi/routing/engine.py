"""Deterministic flood-aware route engine (ONE core, all modes).

Cost model (documented; weights are ASSUMED engineering constants, not
observed/calibrated values):

    edge_cost = travel_time_s
              + RISK_PENALTY_S_PER_M[risk_state] * length_m

    RISK_PENALTY_S_PER_M:
      LOW_RISK      0.00   (no modeled loading)
      UNKNOWN       0.09   (~1.5 min/km: uncertainty is penalized, never
                              treated as free, and never treated as SAFE)
      ELEVATED_RISK 0.18   (~3 min/km: modeled conveyance loading)
      BLOCKED       hard-excluded from candidate routes

The optimizer therefore prefers lower modeled flood exposure, not merely
short distance; routes through UNKNOWN segments are only returned when
no better-supported alternative exists, and are explicitly labeled.

Determinism: identical inputs (graph version, risk states, snapping,
constants) produce identical routes and route_run_id.
"""

from __future__ import annotations

import hashlib
import heapq
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

from .network import DelhiRoadGraph, SegmentEdge, get_road_graph, road_network_provenance
from .risk import (
    CORRIDOR_MAP_DISTANCE_M,
    RiskState,
    aggregate_reach_states,
    build_edge_reach_map,
    freshness_state,
    route_evidence_state,
    segment_evidence,
    translate_reach_to_road_risk,
)
from .state_source import ModeReachStates, now_utc

RISK_PENALTY_S_PER_M: Dict[RiskState, float] = {
    "LOW_RISK": 0.0,
    "UNKNOWN": 0.09,       # ASSUMED: ~1.5 min/km uncertainty penalty
    "ELEVATED_RISK": 0.18, # ASSUMED: ~3 min/km modeled-loading penalty
    "BLOCKED": float("inf"),  # hard-excluded
}

# Assumed divergence factor for the alternative-route search: edges of the
# recommended route are re-costed with this multiplier so the alternative
# is genuinely distinct rather than a trivial variation.
ALTERNATIVE_DIVERGENCE_FACTOR = 4.0
# Two routes sharing more than this edge fraction are considered the same.
MIN_DISTINCT_EDGE_FRACTION = 0.7


@dataclass
class RouteCandidate:
    edges: List[SegmentEdge]
    risk_by_edge: Dict[str, Tuple[RiskState, str]] = field(default_factory=dict)
    total_distance_m: float = 0.0
    travel_time_s: float = 0.0
    risk_penalty_s: float = 0.0
    counts: Dict[str, int] = field(default_factory=dict)

    @property
    def total_cost_s(self) -> float:
        return self.travel_time_s + self.risk_penalty_s

    def counts_summary(self) -> Dict[str, int]:
        return {
            "blocked": self.counts.get("BLOCKED", 0),
            "elevated_risk": self.counts.get("ELEVATED_RISK", 0),
            "unknown": self.counts.get("UNKNOWN", 0),
            "low_risk": self.counts.get("LOW_RISK", 0),
        }


def _edge_risk_states(
    mode_states: ModeReachStates,
) -> Dict[str, Tuple[RiskState, str]]:
    """Translate aggregated reach states into per-edge road risk."""
    observations = aggregate_reach_states(mode_states.member_states)
    reach_risk = {
        reach_id: translate_reach_to_road_risk(obs)
        for reach_id, obs in observations.items()
    }
    edge_map = build_edge_reach_map()
    out: Dict[str, Tuple[RiskState, str]] = {}
    for edge_key, mapped_reach in edge_map.items():
        if mapped_reach is None:
            out[edge_key] = (
                "UNKNOWN",
                "outside the modeled Kushak corridor; no defensible road-model relationship",
            )
        else:
            out[edge_key] = reach_risk[mapped_reach]
    return out


def _dijkstra(
    graph: DelhiRoadGraph,
    source: int,
    target: int,
    risk_by_edge: Dict[str, Tuple[RiskState, str]],
    cost_multiplier_by_road: Optional[Dict[str, float]] = None,
) -> Optional[List[SegmentEdge]]:
    """Deterministic Dijkstra over the flood-aware cost. BLOCKED edges are
    hard-excluded. Tie-breaking is by (cost, node) for determinism."""
    multiplier = cost_multiplier_by_road or {}
    dist: Dict[int, float] = {source: 0.0}
    prev: Dict[int, Tuple[int, str]] = {}
    visited = set()
    heap: List[Tuple[float, int]] = [(0.0, source)]
    while heap:
        d, u = heapq.heappop(heap)
        if u in visited:
            continue
        visited.add(u)
        if u == target:
            break
        for edge in graph.adj.get(u, ()):  # directed
            if edge.v in visited:
                continue
            risk, _ = risk_by_edge.get(edge.edge_key, ("UNKNOWN", ""))
            if RISK_PENALTY_S_PER_M.get(risk, float("inf")) == float("inf"):
                continue  # BLOCKED: hard-excluded from candidates
            cost = graph.travel_time_s(edge) + RISK_PENALTY_S_PER_M[risk] * edge.length_m
            cost *= multiplier.get(edge.road_id, 1.0)
            nd = d + cost
            if nd < dist.get(edge.v, float("inf")) - 1e-12:
                dist[edge.v] = nd
                prev[edge.v] = (u, edge.edge_key)
                heapq.heappush(heap, (nd, edge.v))
    if target not in dist:
        return None
    edges: List[SegmentEdge] = []
    cur = target
    while cur != source:
        u, key = prev[cur]
        edges.append(graph.edge_index[key])
        cur = u
    edges.reverse()
    return edges


def _build_candidate(
    edges: List[SegmentEdge], risk_by_edge: Dict[str, Tuple[RiskState, str]]
) -> RouteCandidate:
    candidate = RouteCandidate(edges=edges)
    for edge in edges:
        risk, reason = risk_by_edge[edge.edge_key]
        candidate.risk_by_edge[edge.edge_key] = (risk, reason)
        candidate.total_distance_m += edge.length_m
        candidate.risk_penalty_s += RISK_PENALTY_S_PER_M.get(risk, 0.0) * edge.length_m
        candidate.counts[risk] = candidate.counts.get(risk, 0) + 1
    candidate.travel_time_s = sum(
        get_road_graph().travel_time_s(e) for e in edges
    )
    return candidate


def _route_geojson(edges: List[SegmentEdge]) -> dict:
    coords: List[List[float]] = []
    for edge in edges:
        if not coords:
            coords.append(list(edge.coords_4326[0]))
        coords.append(list(edge.coords_4326[1]))
    return {
        "type": "Feature",
        "properties": {},
        "geometry": {"type": "LineString", "coordinates": coords},
    }


def _route_risk_geojson(edges: List[SegmentEdge], risk_by_edge: Dict[str, Tuple[RiskState, str]]) -> dict:
    features = []
    for edge in edges:
        risk, _ = risk_by_edge[edge.edge_key]
        if risk in ("UNKNOWN", "ELEVATED_RISK", "BLOCKED"):
            features.append({
                "type": "Feature",
                "properties": {"segment_id": edge.edge_key, "risk_state": risk, "name": edge.name},
                "geometry": {
                    "type": "LineString",
                    "coordinates": [list(edge.coords_4326[0]), list(edge.coords_4326[1])],
                },
            })
    return {"type": "FeatureCollection", "features": features}


def _explain(
    recommended: RouteCandidate,
    alternative: Optional[RouteCandidate],
    evidence_state: str,
    evidence_reason: str,
    no_alternative_reason: Optional[str],
) -> List[str]:
    """Structured facts -> factual sentences (rule-based, no invention)."""
    lines: List[str] = []
    counts = recommended.counts_summary()
    if counts["elevated_risk"] == 0 and counts["unknown"] == 0:
        lines.append(
            "Recommended route follows road segments with no modeled flood "
            "loading on the mapped corridor."
        )
    else:
        parts = []
        if counts["elevated_risk"]:
            parts.append(
                f"{counts['elevated_risk']} elevated-risk segment(s) adjacent "
                "to the modeled corridor"
            )
        if counts["unknown"]:
            parts.append(
                f"{counts['unknown']} UNKNOWN segment(s) with no model-state "
                "coverage"
            )
        lines.append(
            "Recommended route contains " + " and ".join(parts) + "."
        )
    if alternative is not None:
        d_dist = (alternative.total_distance_m - recommended.total_distance_m) / 1000.0
        d_time = (alternative.travel_time_s - recommended.travel_time_s) / 60.0
        a_counts = alternative.counts_summary()
        delta_elev = a_counts["elevated_risk"] - counts["elevated_risk"]
        delta_unknown = a_counts["unknown"] - counts["unknown"]
        trade = []
        if delta_elev != 0:
            trade.append(
                f"{abs(delta_elev)} {'more' if delta_elev > 0 else 'fewer'} elevated-risk segment(s)"
            )
        if delta_unknown != 0:
            trade.append(
                f"{abs(delta_unknown)} {'more' if delta_unknown > 0 else 'fewer'} UNKNOWN segment(s)"
            )
        lines.append(
            f"Alternative route is {abs(d_dist):.2f} km "
            f"{'longer' if d_dist >= 0 else 'shorter'} and "
            f"{abs(d_time):.1f} min {'slower' if d_time >= 0 else 'faster'} "
            + (", with " + " and ".join(trade) if trade else "with the same risk profile")
            + "."
        )
    elif no_alternative_reason:
        lines.append(f"No supported alternative: {no_alternative_reason}")
    lines.append(f"Route evidence state: {evidence_state} — {evidence_reason}")
    return lines


def compute_safe_route(
    origin_lon: float,
    origin_lat: float,
    dest_lon: float,
    dest_lat: float,
    mode_states: ModeReachStates,
    model_timestamp: Optional[str],
    forcing_source: Optional[str],
    mode_freshness_note: str,
) -> dict:
    """Compute the full flood-aware routing result for ONE mode.

    The same function serves LIVE and HISTORICAL modes; the mode only
    determines the reach-state source (never the engine, never the cost
    model). Raises ValueError on invalid/unroutable inputs with explicit
    messages.
    """
    graph = get_road_graph()
    o_idx, o_dist, o_name = graph.snap(origin_lon, origin_lat)
    d_idx, d_dist, d_name = graph.snap(dest_lon, dest_lat)

    if mode_states.status not in ("COMPUTED", "EXECUTED") or not mode_states.member_states:
        risk_by_edge = {
            k: ("UNKNOWN", "model state unavailable for this mode/timestep: " +
                "; ".join(mode_states.diagnostics[:1]))
            for k in build_edge_reach_map()
        }
        status = "UNKNOWN_RISK_STATE"
    else:
        risk_by_edge = _edge_risk_states(mode_states)
        status = "COMPUTED"

    edges = _dijkstra(graph, o_idx, d_idx, risk_by_edge)
    if edges is None:
        raise ValueError("NO_ROUTE: origin and destination are not connected")

    recommended = _build_candidate(edges, risk_by_edge)

    # Alternative: re-run with the recommended roads penalized.
    multiplier = {e.road_id: ALTERNATIVE_DIVERGENCE_FACTOR for e in recommended.edges}
    alt_edges = _dijkstra(graph, o_idx, d_idx, risk_by_edge, multiplier)
    alternative: Optional[RouteCandidate] = None
    no_alt_reason: Optional[str] = None
    if alt_edges is None:
        no_alt_reason = "no connected alternative avoiding the recommended corridor"
    else:
        alt_candidate = _build_candidate(alt_edges, risk_by_edge)
        rec_roads = {e.road_id for e in recommended.edges}
        alt_roads = {e.road_id for e in alt_candidate.edges}
        shared = len(rec_roads & alt_roads)
        denom = max(len(rec_roads | alt_roads), 1)
        if 1.0 - (shared / denom) < (1.0 - MIN_DISTINCT_EDGE_FRACTION):
            no_alt_reason = (
                "the best alternative is not sufficiently distinct from the "
                "recommended route"
            )
            alternative = None
        else:
            alternative = alt_candidate

    # Evidence state (documented weakest-link derivation).
    covered = sum(
        1 for e in recommended.edges
        if recommended.risk_by_edge[e.edge_key][0] != "UNKNOWN"
    )

    def _member_positive(states: Dict[str, Dict[str, Optional[float]]]) -> bool:
        return any(
            ((states.get(rid) or {}).get("incoming_flow_m3_s") or 0.0) > 0.0
            for rid in ("UG-01", "OC-01", "CD-01", "OC-02")
        )

    computed_members = [m for m in mode_states.member_states if m]
    positive_members = sum(1 for m in computed_members if _member_positive(m))
    member_disagreement = (
        len(computed_members) > 0 and 0 < positive_members < len(computed_members)
    )
    evidence_state, evidence_reason = route_evidence_state(
        total_edges=len(recommended.edges),
        covered_edges=covered,
        has_unknown_on_route=any(
            recommended.risk_by_edge[e.edge_key][0] == "UNKNOWN"
            for e in recommended.edges
        ),
        member_disagreement=member_disagreement,
    )

    explanation = _explain(
        recommended, alternative, evidence_state, evidence_reason, no_alt_reason
    )

    now = now_utc()
    network_prov = road_network_provenance()
    route_run_id = hashlib.sha256(
        "|".join(
            str(x)
            for x in (
                mode_states.mode, mode_states.event_id, mode_states.timestep_index,
                round(origin_lon, 6), round(origin_lat, 6),
                round(dest_lon, 6), round(dest_lat, 6),
                o_idx, d_idx, status,
                [e.edge_key for e in recommended.edges],
                recommended.total_cost_s,
            )
        ).encode("utf-8")
    ).hexdigest()[:16]

    def route_payload(c: RouteCandidate) -> dict:
        cs = c.counts_summary()
        route_unknown = cs["unknown"]
        return {
            "edges": [e.edge_key for e in c.edges],
            "geometry": _route_geojson(c.edges),
            "risk_segments": _route_risk_geojson(c.edges, c.risk_by_edge),
            "total_distance_km": round(c.total_distance_m / 1000.0, 2),
            "estimated_travel_time_min": round(c.travel_time_s / 60.0, 1),
            "flood_risk_summary": {
                "blocked_segments": cs["blocked"],
                "elevated_risk_segments": cs["elevated_risk"],
                "unknown_segments": route_unknown,
                "low_risk_segments": cs["low_risk"],
            },
            "route_state": (
                "CONDITIONAL_UNKNOWN_RISK_PORTION" if route_unknown > 0
                else "LOWER_MODELED_RISK"
            ),
            "risk_penalty_s": round(c.risk_penalty_s, 1),
        }

    result: dict = {
        "status": status,
        "mode": mode_states.mode,
        "event_id": mode_states.event_id,
        "timestep_index": mode_states.timestep_index,
        "route_run_id": route_run_id,
        "generated_at": now.isoformat(),
        "origin": {
            "coords": [origin_lon, origin_lat],
            "snapped_road": o_name,
            "snap_distance_m": round(o_dist, 1),
        },
        "destination": {
            "coords": [dest_lon, dest_lat],
            "snapped_road": d_name,
            "snap_distance_m": round(d_dist, 1),
        },
        "recommended_route": route_payload(recommended),
        "alternative_route": route_payload(alternative) if alternative else None,
        "no_alternative_reason": no_alt_reason,
        "route_comparison": {
            "recommended": {
                **recommended.counts_summary(),
                "distance_km": round(recommended.total_distance_m / 1000.0, 2),
                "travel_time_min": round(recommended.travel_time_s / 60.0, 1),
                "risk_penalty_s": round(recommended.risk_penalty_s, 1),
            },
            "alternative": (
                {
                    **alternative.counts_summary(),
                    "distance_km": round(alternative.total_distance_m / 1000.0, 2),
                    "travel_time_min": round(alternative.travel_time_s / 60.0, 1),
                    "risk_penalty_s": round(alternative.risk_penalty_s, 1),
                }
                if alternative else None
            ),
        },
        "evidence_state": {
            "route_state": evidence_state,
            "reason": evidence_reason,
            "derivation": (
                "weakest link: any UNKNOWN segment on the route caps the "
                "route at LOW; MEDIUM requires full coverage with member "
                "disagreement; HIGH requires full coverage with full "
                "ensemble agreement"
            ),
        },
        "explanation": explanation,
        "claim_policy": (
            "Recommended route with lowest supported MODELED flood exposure "
            "under the available evidence — NOT a guarantee of safety. "
            "UNKNOWN segments are not safe segments; stage and depth are "
            "UNKNOWN throughout."
            + (
                " Historical routes are MODEL RECONSTRUCTIONS of a replayed "
                "event, not observations of the real event."
                if mode_states.mode == "HISTORICAL" else ""
            )
        ),
        "provenance": {
            "mode": mode_states.mode,
            "event_id": mode_states.event_id,
            "timestep_index": mode_states.timestep_index,
            "model_timestamp": model_timestamp,
            "forcing_source": forcing_source,
            "road_network_source": network_prov.get("source"),
            "road_network_acquired_at": network_prov.get("acquired_at_utc"),
            "risk_mapping_method": (
                "distance-to-reach-centerline (documented threshold), "
                "loading-based translation (stage-less)"
            ),
            "risk_mapping_threshold_m": CORRIDOR_MAP_DISTANCE_M,
            "cost_model": {
                "type": "travel_time + risk_penalty (documented ASSUMED weights)",
                "weights_s_per_m": {
                    k: (None if v == float("inf") else v)
                    for k, v in RISK_PENALTY_S_PER_M.items()
                },
            },
            "ensemble_members": len(mode_states.member_states),
            "data_freshness": mode_freshness_note,
        },
    }
    return result
