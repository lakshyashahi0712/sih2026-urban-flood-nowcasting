"""Deterministic 1D hydraulic network solver for Phases 7B/7C.

Phase 7B: per-reach Manning capacity, topology validation, provenance.
Phase 7C: steady-state flow conservation and propagation:

    Q_node_in = sum(propagated upstream reach flows) + sum(explicit external inflows)
    Q_out = Q_in   (no storage, losses, or attenuation)

Manning capacity is a property of the reach geometry and is reported
separately from the propagated discharge; it never overwrites a supplied
flow. Unknown inflows block propagation (zero is never inferred from a
missing record). Branching without a supplied flow-split rule leaves the
branch discharge unresolved rather than duplicating or splitting flow.
"""

from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from .hydraulic_contract import (
    HydraulicDataset,
    HydraulicNode,
    OpenChannelReach,
    CoveredConduit,
    ProvenancedValue,
    InflowAttachment,
    DownstreamBoundary,
)
from .hydraulic_calculations import (
    HydraulicCalculationResult,
    calculate_hydraulic_radius,
)
from .hydraulic_continuity import combine_provenance_weakest
from .hydraulic_geometry_input import HydraulicGeometryBundle
from .hydraulic_manning_adapter import calculate_capacity_from_bundle
from .models import ProvenanceStatus


@dataclass
class SolverHydraulicGeometry:
    """Hydraulic geometry for a reach, with provenance tracking."""
    area: ProvenancedValue
    wetted_perimeter: ProvenancedValue


@dataclass
class ReachFlowResult:
    """Result of steady-state conservation for a single reach.

    propagated_flow_m3_s: conserved flow assigned to the reach
        (Q_node_in, preserved unchanged — Phase 7C).
    capacity_m3_s: Manning-derived conveyance for the supplied geometry
        (never the propagated discharge).
    capacity_exceeded: propagated flow above Manning capacity; no
        overflow/depth is invented here.
    flow_m3_s: legacy Phase 7B field, still the Manning capacity value
        when status is COMPUTED (kept for backward compatibility).
    """
    reach_id: str
    flow_m3_s: Optional[float] = None
    propagated_flow_m3_s: Optional[float] = None
    capacity_m3_s: Optional[float] = None
    capacity_exceeded: Optional[bool] = None
    status: str = "BLOCKED_MISSING_GEOMETRY"
    # COMPUTED, BLOCKED_MISSING_GEOMETRY, BLOCKED_INVALID_INPUT,
    # BLOCKED_TOPOLOGY, BLOCKED_UNKNOWN_INFLOW, UNRESOLVED_FLOW_SPLIT
    diagnostic: Optional[str] = None
    inflow_sources: Tuple[str, ...] = ()  # e.g. ("upstream:R1", "external:I1")
    inflow_components_m3_s: Dict[str, float] = field(default_factory=dict)
    geometry_provenance: Tuple[ProvenanceStatus, ProvenanceStatus] = (ProvenanceStatus.UNKNOWN, ProvenanceStatus.UNKNOWN)
    manning_provenance: ProvenanceStatus = ProvenanceStatus.UNKNOWN
    inflow_provenance: ProvenanceStatus = ProvenanceStatus.UNKNOWN
    propagated_flow_provenance: ProvenanceStatus = ProvenanceStatus.UNKNOWN  # DERIVED when propagated


class HydraulicNetworkSolver:
    """Solves for steady-state flow conservation and Manning capacity in a hydraulic network."""

    def __init__(self, dataset: HydraulicDataset, zero_inflow_node_ids: Optional[set] = None):
        self.dataset = dataset
        # Only nodes the contract explicitly marks as zero-flow boundaries
        # may be treated as zero when no inflow record exists.
        self.zero_inflow_node_ids = zero_inflow_node_ids or set()
        self._validate_inputs()

        # Build topology maps
        self.node_ids = {node.node_id for node in dataset.nodes}
        self.reach_map: Dict[str, OpenChannelReach] = {
            reach.reach_id: reach for reach in dataset.open_channel_reaches
        }
        # Note: We could add covered_conduits similarly, but for Phase 7B we focus on open channels.
        # The same principles apply to conduits.

        # Maps for topology validation and traversal
        self.node_to_incoming_reaches: Dict[str, List[str]] = defaultdict(list)
        self.node_to_outgoing_reaches: Dict[str, List[str]] = defaultdict(list)
        self._build_topology_maps()

        # Lateral inflows attached to nodes (we ignore reach attachments for simplicity in Phase 7B)
        self.node_lateral_inflows: Dict[str, List[InflowAttachment]] = defaultdict(list)
        self._collect_lateral_inflows()

        # Explicit external inflows supplied by the caller, keyed by node_id.
        # Distinct from lateral_inflow_attachments (which have no discharge here).
        self.node_external_inflows: Dict[str, List[Tuple[str, float, ProvenanceStatus]]] = defaultdict(list)
        self.downstream_boundaries: List[DownstreamBoundary] = list(dataset.downstream_boundaries)

    def _validate_inputs(self) -> None:
        """Validate that the dataset has been checked for basic readiness."""
        # We assume the caller has run validate_hydraulic_dataset and checked for readiness.
        # We do not repeat the full validation here to avoid duplication.
        pass

    def _build_topology_maps(self) -> None:
        """Build maps of incoming and outgoing reaches for each node."""
        for reach in self.dataset.open_channel_reaches:
            # Upstream node -> outgoing reach
            self.node_to_outgoing_reaches[reach.upstream_node_id].append(reach.reach_id)
            # Downstream node -> incoming reach
            self.node_to_incoming_reaches[reach.downstream_node_id].append(reach.reach_id)

    def _collect_lateral_inflows(self) -> None:
        """Collect lateral inflows attached to nodes (ignore reach attachments for Phase 7B)."""
        for attachment in self.dataset.inflow_attachments:
            if attachment.attachment_node_id:
                self.node_lateral_inflows[attachment.attachment_node_id].append(attachment)
            # Note: We ignore attachment_reach_id for Phase 7B as per simplification.

    def _is_deterministic_pv_for_slope(self, pv: ProvenancedValue) -> bool:
        """Check if a ProvenancedValue is a valid non-negative float for slope."""
        if pv.value is None:
            return False
        try:
            val = float(pv.value)
            return val >= 0
        except (ValueError, TypeError):
            return False

    def _is_deterministic_pv_for_manning(self, pv: ProvenancedValue) -> bool:
        """Check if a ProvenancedValue is a valid positive float for Manning's n."""
        if pv.value is None:
            return False
        try:
            val = float(pv.value)
            return val > 0
        except (ValueError, TypeError):
            return False

    def _is_deterministic_pv_for_geometry(self, pv: ProvenancedValue) -> bool:
        """Check if a ProvenancedValue is a valid positive float for area/perimeter."""
        if pv.value is None:
            return False
        try:
            val = float(pv.value)
            return val > 0
        except (ValueError, TypeError):
            return False

    def _calculate_reach_flow(
        self,
        reach: OpenChannelReach,
        area_pv: ProvenancedValue,
        perimeter_pv: ProvenancedValue,
    ) -> ReachFlowResult:
        """Calculate flow for a single reach given its hydraulic geometry."""
        # Check slope
        if not self._is_deterministic_pv_for_slope(reach.slope_m_per_m):
            return ReachFlowResult(
                reach_id=reach.reach_id,
                status="BLOCKED_INVALID_INPUT",
                diagnostic=f"Slope must be non-negative (got {reach.slope_m_per_m.value})",
                manning_provenance=reach.manning_n.provenance,
            )

        # Check Manning's n
        if not self._is_deterministic_pv_for_manning(reach.manning_n):
            return ReachFlowResult(
                reach_id=reach.reach_id,
                status="BLOCKED_INVALID_INPUT",
                diagnostic=f"Manning's n must be positive (got {reach.manning_n.value})",
                geometry_provenance=(area_pv.provenance, perimeter_pv.provenance),
            )

        # Check area and perimeter
        if not self._is_deterministic_pv_for_geometry(area_pv):
            return ReachFlowResult(
                reach_id=reach.reach_id,
                status="BLOCKED_MISSING_GEOMETRY",
                diagnostic="Missing or invalid cross-sectional area",
                manning_provenance=reach.manning_n.provenance,
                geometry_provenance=(ProvenanceStatus.UNKNOWN, perimeter_pv.provenance),
            )

        if not self._is_deterministic_pv_for_geometry(perimeter_pv):
            return ReachFlowResult(
                reach_id=reach.reach_id,
                status="BLOCKED_MISSING_GEOMETRY",
                diagnostic="Missing or invalid wetted perimeter",
                manning_provenance=reach.manning_n.provenance,
                geometry_provenance=(area_pv.provenance, ProvenanceStatus.UNKNOWN),
            )

        # All inputs are valid: compute capacity via the canonical Phase 7D-8
        # Manning adapter (geometry bundle -> calculate_capacity_from_bundle).
        # No Manning equation duplication here.
        try:
            # Calculate hydraulic radius first (for the bundle).
            hydraulic_radius = area_pv.value / perimeter_pv.value
            bundle = HydraulicGeometryBundle(
                status="COMPUTED",
                area_m2=float(area_pv.value),
                perimeter_m=float(perimeter_pv.value),
                radius_m=float(hydraulic_radius),
                geometry_provenance=combine_provenance_weakest(
                    [area_pv.provenance, perimeter_pv.provenance]
                ),
            )
            capacity = calculate_capacity_from_bundle(
                bundle,
                n=float(reach.manning_n.value),
                slope=float(reach.slope_m_per_m.value),
                n_provenance=reach.manning_n.provenance,
                slope_provenance=reach.slope_m_per_m.provenance,
            )

            if capacity.status == "COMPUTED":
                return ReachFlowResult(
                    reach_id=reach.reach_id,
                    flow_m3_s=capacity.capacity_m3_s,
                    status="COMPUTED",
                    geometry_provenance=(area_pv.provenance, perimeter_pv.provenance),
                    manning_provenance=reach.manning_n.provenance,
                    inflow_provenance=ProvenanceStatus.UNKNOWN,  # To be set by caller during propagation
                )
            else:
                return ReachFlowResult(
                    reach_id=reach.reach_id,
                    status=capacity.status,
                    diagnostic=capacity.diagnostic,
                    geometry_provenance=(area_pv.provenance, perimeter_pv.provenance),
                    manning_provenance=reach.manning_n.provenance,
                )
        except Exception as e:
            return ReachFlowResult(
                reach_id=reach.reach_id,
                status="BLOCKED_INVALID_INPUT",
                diagnostic=f"Calculation error: {str(e)}",
                geometry_provenance=(area_pv.provenance, perimeter_pv.provenance),
                manning_provenance=reach.manning_n.provenance,
            )

    def _topological_sort(self) -> Tuple[List[str], bool, Optional[str]]:
        """Perform topological sort on the network graph.

        Returns:
            (sorted_node_ids, has_cycle, error_message)
        """
        # We'll work on the graph of nodes connected by reaches.
        # Build adjacency list and in-degree count for nodes.
        adj = defaultdict(list)
        in_degree = {node_id: 0 for node_id in self.node_ids}

        errors: List[str] = []
        for reach_id, reach in self.reach_map.items():
            u = reach.upstream_node_id
            v = reach.downstream_node_id
            if u not in self.node_ids or v not in self.node_ids:
                missing = u if u not in self.node_ids else v
                errors.append(
                    f"Reach '{reach_id}' references node '{missing}' which was not found in the network"
                )
                continue
            adj[u].append(v)
            in_degree[v] += 1

        # Kahn's algorithm
        queue = deque([node_id for node_id in self.node_ids if in_degree[node_id] == 0])
        topo_order = []

        while queue:
            node = queue.popleft()
            topo_order.append(node)
            for neighbor in adj[node]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if len(topo_order) != len(self.node_ids):
            # There is a cycle
            return [], True, "Network contains a directed cycle"

        return topo_order, False, errors

    def set_external_inflow(
        self, node_id: str, inflow_id: str, discharge_m3_s: float,
        provenance: ProvenanceStatus = ProvenanceStatus.OBSERVED,
    ) -> None:
        """Supply an explicit external inflow at a node (Phase 7C)."""
        if not isinstance(discharge_m3_s, (int, float)) or discharge_m3_s < 0:
            raise ValueError(
                f"External inflow '{inflow_id}' at node '{node_id}' must be a non-negative number"
            )
        self.node_external_inflows[node_id].append(
            (inflow_id, float(discharge_m3_s), provenance)
        )

    def solve(
        self,
        reach_geometry: Dict[str, Tuple[ProvenancedValue, ProvenancedValue]],
    ) -> Tuple[List[ReachFlowResult], List[str]]:
        """Solve steady-state flow conservation across the network.

        Phase 7C semantics:
          - Q_node_in = sum(upstream propagated reach flows) + sum(external inflows)
          - Propagated flow is passed to the single downstream reach unchanged
            (no storage, losses, or attenuation).
          - Manning capacity is computed separately per reach and never
            replaces the propagated flow.
          - A required upstream inflow that is unknown blocks the downstream
            reach as BLOCKED_UNKNOWN_INFLOW (zero is never inferred).
          - A node with multiple downstream reaches and no supplied flow
            split leaves each branch UNRESOLVED_FLOW_SPLIT.

        Args:
            reach_geometry: Mapping from reach_id to (area_pv, perimeter_pv).

        Returns:
            (list of ReachFlowResult for each reach, list of topology errors)
        """
        topo_order, has_cycle, topo_node_errors = self._topological_sort()
        topology_errors = list(topo_node_errors)
        if has_cycle:
            topology_errors.append("Network contains a directed cycle")
            return [], topology_errors

        isolated_nodes = []
        for node_id in self.node_ids:
            if (not self.node_to_incoming_reaches[node_id] and
                not self.node_to_outgoing_reaches[node_id] and
                not self.node_lateral_inflows[node_id]):
                isolated_nodes.append(node_id)
        if isolated_nodes:
            topology_errors.append(
                f"Isolated nodes (no reaches or lateral inflows): {', '.join(isolated_nodes)}"
            )

        results: List[ReachFlowResult] = []
        results_by_reach: Dict[str, ReachFlowResult] = {}

        # Node inflow state: None means "required but unknown" (blocks propagation).
        node_inflow: Dict[str, Optional[float]] = {}
        node_inflow_components: Dict[str, Dict[str, float]] = {}
        node_inflow_sources: Dict[str, Tuple[str, ...]] = {}
        node_unknown_reasons: Dict[str, List[str]] = {}

        for node_id in self.node_ids:
            node_inflow[node_id] = 0.0
            node_inflow_components[node_id] = {}
            node_inflow_sources[node_id] = ()
            node_unknown_reasons[node_id] = []

        def combine_provenance(provs: List[ProvenanceStatus]) -> ProvenanceStatus:
            """Conservative provenance combination for summed flows."""
            if not provs:
                return ProvenanceStatus.UNKNOWN
            if len(set(provs)) == 1:
                return provs[0]
            # Mixed provenance: keep the weakest deterministic state present.
            order = [
                ProvenanceStatus.UNKNOWN, ProvenanceStatus.PROVISIONAL,
                ProvenanceStatus.ASSUMED, ProvenanceStatus.DERIVED,
                ProvenanceStatus.OFFICIAL_MODEL_VALUE,
                ProvenanceStatus.OFFICIAL, ProvenanceStatus.OBSERVED,
            ]
            ranks = {p: i for i, p in enumerate(order)}
            return min(provs, key=lambda p: ranks.get(p, len(order)))

        def mark_unknown(node_id: str, reason: str) -> None:
            node_inflow[node_id] = None
            node_unknown_reasons[node_id].append(reason)

        # Process nodes in topological order.
        for node_id in topo_order:
            components = dict(node_inflow_components[node_id])
            sources = list(node_inflow_sources[node_id])
            provenances: List[ProvenanceStatus] = []
            is_unknown = False

            # 1. Inflow from upstream reaches (already propagated).
            for rid in self.node_to_incoming_reaches[node_id]:
                up = results_by_reach.get(rid)
                if up is None:
                    # Upstream reach was not solved (e.g. blocked for topology
                    # before results were recorded) — its contribution is unknown.
                    is_unknown = True
                    mark_unknown(node_id, f"upstream reach '{rid}' has no computed flow")
                    continue
                if up.status == "BLOCKED_UNKNOWN_INFLOW":
                    is_unknown = True
                    mark_unknown(node_id, f"upstream reach '{rid}' has unknown inflow")
                    continue
                if up.propagated_flow_m3_s is None:
                    is_unknown = True
                    mark_unknown(
                        node_id,
                        f"upstream reach '{rid}' status {up.status}: no propagated flow",
                    )
                    continue
                key = f"upstream:{rid}"
                components[key] = up.propagated_flow_m3_s
                sources.append(key)
                # Upstream propagated flow is DERIVED; a reach whose inflow was
                # explicitly supplied may carry stronger provenance.
                provenances.append(
                    up.propagated_flow_provenance
                    if up.propagated_flow_provenance != ProvenanceStatus.UNKNOWN
                    else up.inflow_provenance
                )

            # 2. Explicit external inflows at this node.
            for inflow_id, discharge, prov in self.node_external_inflows[node_id]:
                key = f"external:{inflow_id}"
                components[key] = components.get(key, 0.0) + discharge
                sources.append(key)
                provenances.append(prov)

            # 3. Lateral inflow attachments: they carry no discharge value in
            # the contract. An attachment without a caller-supplied external
            # inflow is an unknown required inflow, never a silent zero.
            for attachment in self.node_lateral_inflows[node_id]:
                supplied = any(
                    key == f"external:{attachment.inflow_id}" for key in components
                )
                if not supplied:
                    is_unknown = True
                    mark_unknown(
                        node_id,
                        f"lateral inflow attachment '{attachment.inflow_id}' "
                        "has no discharge value",
                    )

            # 4. Upstream boundary with no inflow record at all.
            if (not sources and not is_unknown
                    and node_id not in self.zero_inflow_node_ids):
                is_unknown = True
                mark_unknown(
                    node_id,
                    "upstream boundary node has no inflow record "
                    "(zero not inferred; mark as zero_inflow_node_ids to allow)",
                )

            if is_unknown:
                node_inflow[node_id] = None
                node_inflow_sources[node_id] = tuple(sources)
                node_inflow_components[node_id] = components
                # Do not propagate a partial sum: downstream is blocked too
                # (handled when the downstream node sees a blocked upstream).
            else:
                node_inflow[node_id] = sum(components.values())
                node_inflow_sources[node_id] = tuple(sources)
                node_inflow_components[node_id] = components

            node_prov = (
                combine_provenance(provenances)
                if (not is_unknown and provenances)
                else ProvenanceStatus.UNKNOWN
            )
            node_flow = node_inflow[node_id]

            # Outgoing reaches.
            outgoing_reach_ids = self.node_to_outgoing_reaches[node_id]
            if len(outgoing_reach_ids) > 1:
                # Branching: no defensible flow-split rule exists in the
                # contract; leave each branch unresolved rather than
                # duplicating or splitting the flow.
                for rid in outgoing_reach_ids:
                    result = ReachFlowResult(
                        reach_id=rid,
                        status="UNRESOLVED_FLOW_SPLIT",
                        diagnostic=(
                            f"Node '{node_id}' has multiple downstream reaches and "
                            "no flow-split rule; branch discharge unresolved"
                        ),
                        propagated_flow_m3_s=node_flow,
                        inflow_sources=tuple(sources),
                        inflow_components_m3_s=components,
                        inflow_provenance=node_prov,
                    )
                    results.append(result)
                    results_by_reach[rid] = result
                continue

            for rid in outgoing_reach_ids:
                reach = self.reach_map[rid]
                if rid not in reach_geometry:
                    result = ReachFlowResult(
                        reach_id=rid,
                        status="BLOCKED_MISSING_GEOMETRY",
                        diagnostic="Hydraulic geometry (area/perimeter) not provided for reach",
                        propagated_flow_m3_s=node_flow,
                        inflow_sources=tuple(sources),
                        inflow_components_m3_s=components,
                        inflow_provenance=node_prov,
                    )
                    results.append(result)
                    results_by_reach[rid] = result
                    continue

                if node_flow is None:
                    result = ReachFlowResult(
                        reach_id=rid,
                        status="BLOCKED_UNKNOWN_INFLOW",
                        diagnostic=(
                            f"Node '{node_id}' inflow unknown: "
                            + "; ".join(node_unknown_reasons[node_id])
                        ),
                        inflow_sources=tuple(sources),
                        inflow_components_m3_s=components,
                    )
                    results.append(result)
                    results_by_reach[rid] = result
                    continue

                area_pv, perimeter_pv = reach_geometry[rid]
                capacity_result = self._calculate_reach_flow(reach, area_pv, perimeter_pv)

                # Propagated flow is conserved unchanged; capacity is separate.
                capacity_value = (
                    capacity_result.flow_m3_s
                    if capacity_result.status == "COMPUTED" else None
                )
                result = ReachFlowResult(
                    reach_id=rid,
                    flow_m3_s=capacity_result.flow_m3_s,
                    propagated_flow_m3_s=node_flow,
                    capacity_m3_s=capacity_value,
                    capacity_exceeded=(
                        node_flow > capacity_value
                        if capacity_value is not None else None
                    ),
                    status=capacity_result.status,
                    diagnostic=capacity_result.diagnostic,
                    inflow_sources=tuple(sources),
                    inflow_components_m3_s=components,
                    geometry_provenance=capacity_result.geometry_provenance,
                    manning_provenance=capacity_result.manning_provenance,
                    inflow_provenance=node_prov,
                    propagated_flow_provenance=ProvenanceStatus.DERIVED,
                )
                results.append(result)
                results_by_reach[rid] = result

        return results, topology_errors