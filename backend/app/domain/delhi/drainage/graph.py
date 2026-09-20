"""DELHI DERIVED DRAINAGE GRAPH (documented DERIVED network).

Built entirely from on-disk evidence — never surveyed/as-built:

Nodes:
- KUSHAK-0000  corridor upstream origin (chainage 0, Nehru Park area),
              from the documented corridor centerline
- CS-01..CS-07  documented Appendix XII cross-sections (coordinates +
              chainage + geometry in ``kushak_cross_sections.geojson``)
- KUSHAK-5027  Barapullah confluence (chainage ~5027.56)

Edges: chainage-ordered segments between consecutive nodes, with
geometry taken along the documented corridor centerline (chainage
fraction), and per-edge inferred-effective capacity RANGES derived from:
- open reaches: the bounding cross-section geometry classes
  (trapezoidal: bottom 6.5-18 m, bank height 2.5-4.2 m, side slope
  0.6-0.8) with DMP Manning n and the documented backbone slope
- the underground (UG-01) portion: NIT52 procurement class (4.0-5.0 m)
  x NGT JIR visual depth (3.5-4.5 m) box geometry with DMP RCC-box n

EVERY quantity carries DERIVED/ASSUMED provenance and is never
presented as as-built, surveyed, or calibrated. The graph gives the
model something concrete to attach per-node surcharge/backflow POTENTIAL
(scenario-derived) to — never a depth claim.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from shapely.geometry import LineString, Point
from shapely.ops import substring

from backend.app.domain.delhi.digital_twin.kushak_evidence_model import (
    DMP_MANNING_N,
    backbone_slope_m_per_m,
)

_REPO_ROOT = Path(__file__).resolve().parents[5]
_DATA = _REPO_ROOT / "data" / "delhi" / "derived"

CENTERLINE_PATH = _DATA / "hydraulic" / "kushak_corridor_centerline.geojson"
CROSS_SECTIONS_PATH = _DATA / "hydraulic" / "kushak_cross_sections.geojson"

CHAIN_UG_END = 2318.5
CHAIN_TOTAL = 5027.56
CHAIN_OPEN_START = CHAIN_UG_END

# NIT52 procurement class and NGT JIR visual depth (documented classes).
NIT52_WIDTH = (4.0, 5.0)
JIR_DEPTH = (3.5, 4.5)


@dataclass(frozen=True)
class DrainageNode:
    node_id: str
    chainage_m: float
    lon: float
    lat: float
    evidence: str
    provenance: str


@dataclass(frozen=True)
class DrainageEdge:
    edge_id: str
    upstream_node_id: str
    downstream_node_id: str
    chainage_start_m: float
    chainage_end_m: float
    length_m: float
    reach_id: str  # model reach containing the edge midpoint
    geometry_wgs84: List[Tuple[float, float]]
    geometry_provenance: str
    capacity_min_m3_s: float
    capacity_max_m3_s: float
    capacity_provenance: str
    dimension_basis: str


@dataclass
class DrainageGraph:
    nodes: Tuple[DrainageNode, ...]
    edges: Tuple[DrainageEdge, ...]

    def node(self, node_id: str) -> DrainageNode:
        for n in self.nodes:
            if n.node_id == node_id:
                return n
        raise KeyError(node_id)

    def edge_for_node(self, node_id: str) -> Optional[DrainageEdge]:
        """The edge that discharges INTO a node (its downstream end)."""
        for e in self.edges:
            if e.downstream_node_id == node_id:
                return e
        return None


def _load_centerline_lines_wgs84() -> Tuple[LineString, LineString]:
    """(underground segment 0..2318.5, open trunk 2318.5..5027.56)."""
    data = json.loads(CENTERLINE_PATH.read_text(encoding="utf-8"))
    underground: Optional[LineString] = None
    open_trunk: Optional[LineString] = None
    for feature in data.get("features", []):
        geom = feature.get("geometry", {})
        props = feature.get("properties", {})
        if geom.get("type") != "LineString":
            continue
        if "Subsurface" in props.get("name", ""):
            underground = LineString(geom["coordinates"])
        elif "Open Trunk" in props.get("name", ""):
            open_trunk = LineString(geom["coordinates"])
    if underground is None or open_trunk is None:
        raise RuntimeError("centerline segments missing")
    return underground, open_trunk


def _chainage_point(chainage: float) -> Tuple[float, float]:
    """Point on the centerline at a chainage (documented corridor
    geometry). Undefined portions refuse rather than invent."""
    underground, open_trunk = _load_centerline_lines_wgs84()
    if chainage <= CHAIN_UG_END:
        frac = max(0.0, chainage / CHAIN_UG_END)
        p = underground.interpolate(frac, normalized=True)
    else:
        frac = min(
            1.0, (chainage - CHAIN_OPEN_START) / (CHAIN_TOTAL - CHAIN_OPEN_START)
        )
        p = open_trunk.interpolate(frac, normalized=True)
    return (p.x, p.y)


def _edge_geometry(start_chainage: float, end_chainage: float) -> List[Tuple[float, float]]:
    underground, open_trunk = _load_centerline_lines_wgs84()
    parts: List[Tuple[float, float]] = []

    def line_for(c: float) -> LineString:
        return underground if c <= CHAIN_UG_END else open_trunk

    def frac_on(line: LineString, c: float) -> float:
        if line is underground:
            return max(0.0, min(1.0, c / CHAIN_UG_END))
        return max(0.0, min(1.0, (c - CHAIN_OPEN_START) / (CHAIN_TOTAL - CHAIN_OPEN_START)))

    if start_chainage <= CHAIN_UG_END < end_chainage:
        seg = substring(underground, frac_on(underground, start_chainage), 1.0, normalized=True)
        parts.extend(seg.coords)
        seg2 = substring(open_trunk, 0.0, frac_on(open_trunk, end_chainage), normalized=True)
        parts.extend(seg2.coords)
    else:
        line = line_for(start_chainage)
        seg = substring(line, frac_on(line, start_chainage), frac_on(line, end_chainage), normalized=True)
        parts.extend(seg.coords)
    # De-duplicate the joint coordinate.
    clean: List[Tuple[float, float]] = []
    for c in parts:
        if not clean or (c[0] - clean[-1][0]) ** 2 + (c[1] - clean[-1][1]) ** 2 > 1e-12:
            clean.append((round(c[0], 6), round(c[1], 6)))
    return clean


def _reach_for_chainage(c: float) -> str:
    for reach_id, lo, hi in (("UG-01", 0.0, 2318.5), ("OC-01", 2318.5, 3700.0),
                             ("CD-01", 3700.0, 4700.0), ("OC-02", 4700.0, 5027.56)):
        if lo <= c < hi:
            return reach_id
    return "OC-02"


def _trapezoid_area_perimeter(h: float, b: float, z: float) -> Tuple[float, float]:
    """Trapezoid full-section area and wetted perimeter (full-bore
    convention for capacity — an INFERRED_EFFECTIVE estimate, not a
    surveyed hydraulic section)."""
    area = h * (b + z * h)
    perimeter = b + 2.0 * h * math.sqrt(1.0 + z * z)
    return area, perimeter


def _manning_capacity(area: float, perimeter: float, n: float, slope: float) -> float:
    if perimeter <= 0 or area <= 0:
        return 0.0
    radius = area / perimeter
    return (1.0 / n) * area * radius ** (2.0 / 3.0) * math.sqrt(max(slope, 1e-6))


def build_drainage_graph() -> DrainageGraph:
    """Assemble the DERIVED graph from on-disk evidence (deterministic)."""
    cs_data = json.loads(CROSS_SECTIONS_PATH.read_text(encoding="utf-8"))
    cross_sections: List[dict] = []
    for feature in cs_data.get("features", []):
        props = feature["properties"]
        cross_sections.append({
            "id": props["cross_section_id"],
            "chainage": float(props["chainage_m"]),
            "lon": float(props["longitude"]),
            "lat": float(props["latitude"]),
            "bottom": float(props.get("bottom_width_m") or 0),
            "top": float(props.get("top_width_m") or 0),
            "bank_h": float(props.get("bank_height_m") or 0),
            "z": float(props.get("side_slope_h_v") or 0),
        })
    cross_sections.sort(key=lambda c: c["chainage"])

    slope = backbone_slope_m_per_m()
    if slope is None:
        raise RuntimeError("documented backbone slope unavailable")

    # Nodes.
    upstream_lon, upstream_lat = _chainage_point(0.0)
    confluence_lon, confluence_lat = _chainage_point(CHAIN_TOTAL)
    nodes: List[DrainageNode] = [
        DrainageNode(
            node_id="KUSHAK-0000",
            chainage_m=0.0,
            lon=round(upstream_lon, 6),
            lat=round(upstream_lat, 6),
            evidence="corridor centerline upstream origin (Nehru Park / Yashwant Place)",
            provenance="DERIVED (documented corridor centerline)",
        ),
    ]
    for c in cross_sections:
        nodes.append(DrainageNode(
            node_id=c["id"],
            chainage_m=c["chainage"],
            lon=c["lon"],
            lat=c["lat"],
            evidence=f"Appendix XII cross-section {c['id']} (documented coordinates + chainage)",
            provenance="DERIVED (Appendix XII geometry; NOT surveyed/as-built)",
        ))
    nodes.append(DrainageNode(
        node_id="KUSHAK-5027",
        chainage_m=CHAIN_TOTAL,
        lon=round(confluence_lon, 6),
        lat=round(confluence_lat, 6),
        evidence="corridor confluence origin (Defence Colony / Barapullah confluence)",
        provenance="DERIVED (documented corridor centerline)",
    ))

    ordered = sorted(nodes, key=lambda n: n.chainage_m)

    # Edges.
    edges: List[DrainageEdge] = []
    for i in range(len(ordered) - 1):
        up, dn = ordered[i], ordered[i + 1]
        mid = (up.chainage_m + dn.chainage_m) / 2.0
        reach = _reach_for_chainage(mid)
        length = dn.chainage_m - up.chainage_m

        if reach == "UG-01":
            # Underground box class: NIT52 width x JIR visual depth.
            dims = (
                ("width", NIT52_WIDTH[0], NIT52_WIDTH[1]),
                ("height", JIR_DEPTH[0], JIR_DEPTH[1]),
            )
            n = DMP_MANNING_N["rcc_box"]
            basis = (
                "underground box geometry class: NIT52 procurement width "
                "4.0-5.0 m x NGT JIR visual depth 3.5-4.5 m (OFFICIAL class "
                "ranges; not measured clear dimensions)"
            )
            caps = []
            for w_lo, w_hi, h_lo, h_hi in (
                (NIT52_WIDTH[0], NIT52_WIDTH[1], JIR_DEPTH[0], JIR_DEPTH[1]),
            ):
                a_lo, p_lo = w_lo * h_lo, w_lo + 2 * h_lo
                a_hi, p_hi = w_hi * h_hi, w_hi + 2 * h_hi
                caps = [
                    _manning_capacity(a_lo, p_lo, n, slope),
                    _manning_capacity(a_hi, p_hi, n, slope),
                ]
        else:
            # Open trapezoid from the BOUNDING documented cross-sections.
            cs_up = cross_sections[i - 1] if i - 1 < len(cross_sections) else None
            cs_dn = cross_sections[i] if i < len(cross_sections) else cross_sections[-1]
            # first edge (CS-01) bounds: use CS-01 itself on both sides.
            cs_a = cs_up if cs_up is not None else cs_dn
            cs_b = cs_dn
            b_lo = min(cs_a["bottom"], cs_b["bottom"])
            b_hi = max(cs_a["bottom"], cs_b["bottom"])
            h_lo = min(cs_a["bank_h"], cs_b["bank_h"])
            h_hi = max(cs_a["bank_h"], cs_b["bank_h"])
            z_lo = min(cs_a["z"], cs_b["z"])
            z_hi = max(cs_a["z"], cs_b["z"])
            n = DMP_MANNING_N["irregular_open_drain"]
            basis = (
                f"open trapezoid bounded by {cs_a['id']} and {cs_b['id']}: "
                f"bottom {b_lo}-{b_hi} m, bank height {h_lo}-{h_hi} m, side "
                f"slope {z_lo}-{z_hi}" + "; capacity class INFERRED_EFFECTIVE"
            )
            lo = _manning_capacity(*_trapezoid_area_perimeter(h_lo, b_lo, z_lo), n, slope)
            hi = _manning_capacity(*_trapezoid_area_perimeter(h_hi, b_hi, z_hi), n, slope)
            caps = [lo, hi]

        edges.append(DrainageEdge(
            edge_id=f"E{i:02d}",
            upstream_node_id=up.node_id,
            downstream_node_id=dn.node_id,
            chainage_start_m=up.chainage_m,
            chainage_end_m=dn.chainage_m,
            length_m=round(length, 2),
            reach_id=reach,
            geometry_wgs84=_edge_geometry(up.chainage_m, dn.chainage_m),
            geometry_provenance="DERIVED (documented corridor centerline, chainage fraction)",
            capacity_min_m3_s=round(min(caps), 2),
            capacity_max_m3_s=round(max(caps), 2),
            capacity_provenance=(
                "INFERRED_EFFECTIVE (full-bore Manning estimate over "
                "documented geometry class ranges; never surveyed or calibrated)"
            ),
            dimension_basis=basis,
        ))

    return DrainageGraph(nodes=tuple(ordered), edges=tuple(edges))


@lru_cache(maxsize=1)
def get_drainage_graph() -> DrainageGraph:
    return build_drainage_graph()


def graph_to_geojson(graph: Optional[DrainageGraph] = None) -> dict:
    graph = graph or get_drainage_graph()
    nodes = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "node_id": n.node_id,
                    "chainage_m": n.chainage_m,
                    "provenance": n.provenance,
                },
                "geometry": {"type": "Point", "coordinates": [n.lon, n.lat]},
            }
            for n in graph.nodes
        ],
    }
    edges = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "edge_id": e.edge_id,
                    "reach_id": e.reach_id,
                    "length_m": e.length_m,
                    "capacity_min_m3_s": e.capacity_min_m3_s,
                    "capacity_max_m3_s": e.capacity_max_m3_s,
                    "capacity_provenance": e.capacity_provenance,
                    "dimension_basis": e.dimension_basis,
                },
                "geometry": {
                    "type": "LineString",
                    "coordinates": [list(c) for c in e.geometry_wgs84],
                },
            }
            for e in graph.edges
        ],
    }
    return {"nodes": nodes, "edges": edges}