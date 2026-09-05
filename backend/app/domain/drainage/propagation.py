"""Simplified network mass-balance / surcharge propagation model for BMC drainage networks.

IMPORTANT MODEL CLASSIFICATION & LIMITATION:
This is a simplified network mass-balance and hydraulic surcharge propagation model.
It is NOT a full dynamic 1D/2D Saint-Venant or SWMM hydrodynamic wave solver.
It models volume-based mass conservation, Manning gravity conveyance capacity,
manhole storage accumulation, downstream coastal boundary head (tailwater backpressure),
and upstream surcharge propagation over discrete timesteps.

Key Physical & Engineering Principles:
1. BMC US_NODE_ID -> DS_NODE_ID connectivity is authoritative and strictly directed.
   Channel direction is NEVER reversed under any circumstances (including adverse invert slopes).
2. Authoritative BMC conduit cross-sections (OREC, RECT, CIRC) and invert-derived slopes
   from Phase 2.1A govern physical conveyance capacities. Flat (S=0) and adverse (S<0)
   slopes have zero gravity conveyance capacity (0.0 m³/s).
3. Coastal / outfall boundary water levels H_boundary(t) can submerge outfalls, throttle
   discharge via head-loss reduction (phi <= 1.0), or completely lock outfalls (phi = 0.0),
   propagating backwater surcharge upstream.
4. Simplified Tide-Lock Condition: H_boundary >= ground is strictly the simplified
   model's tide-lock condition where gravity outflow is capped at zero. It does NOT
   claim that H_boundary >= ground physically means zero discharge in all real physical
   systems (which in reality may involve pressurized discharge or tidal flap-gate mechanics).
5. Real submerged-outfall hydraulics require a future dynamic hydraulic solver and
   measured downstream water levels.
6. Strictly distinguishes MODELLED / SYNTHETIC boundary levels from future OBSERVED tide data.
   No official Mumbai tide gauge data is claimed or invented.
7. No artificial pump, gate, or blockage effects are invented.
8. Strict mass conservation is mathematically guaranteed at every node and across the entire network.
"""
from __future__ import annotations

import math
from enum import Enum
from typing import Dict, List, Optional, Tuple
from pydantic import BaseModel, Field

try:
    from backend.app.domain.drainage.models import (
        DrainageNetwork,
        DrainageNode,
        DrainageChannel,
        NodeType,
        Provenance,
    )
    from backend.app.domain.drainage.capacity import (
        ChannelCapacity,
        ChannelHydraulicParameters,
        compute_channel_capacity,
    )
except ImportError:
    from app.domain.drainage.models import (
        DrainageNetwork,
        DrainageNode,
        DrainageChannel,
        NodeType,
        Provenance,
    )
    from app.domain.drainage.capacity import (
        ChannelCapacity,
        ChannelHydraulicParameters,
        compute_channel_capacity,
    )


class BoundarySourceType(str, Enum):
    """Source classification for downstream boundary water levels."""
    MODELLED = "MODELLED"
    SYNTHETIC = "SYNTHETIC"  # Used for testing/scenarios without claiming real tide data
    OBSERVED = "OBSERVED"    # Reserved for future real harbor gauge integration


class DownstreamBoundaryCondition(BaseModel):
    """Downstream coastal / outfall water-level boundary condition.

    Attributes:
        boundary_type: Source classification (MODELLED, SYNTHETIC, OBSERVED)
        fixed_level_m: Constant boundary head [m] applied across all timesteps (if uniform)
        time_series_levels_m: Sequence of boundary heads [m] per 1-hour timestep
        node_specific_levels_m: Optional mapping of specific outlet nodes to boundary levels {node_id: level_m}
        description: Explicit description of the boundary condition scenario
    """
    boundary_type: BoundarySourceType = BoundarySourceType.MODELLED
    fixed_level_m: Optional[float] = None
    time_series_levels_m: Optional[List[float]] = None
    node_specific_levels_m: Optional[Dict[str, float]] = None
    description: str = "Modelled downstream boundary water level"

    def get_boundary_level(self, timestep_index: int, node_id: Optional[str] = None) -> Optional[float]:
        """Get boundary water level for a given timestep index and optional node identifier."""
        if self.node_specific_levels_m and node_id and node_id in self.node_specific_levels_m:
            return self.node_specific_levels_m[node_id]
        if self.time_series_levels_m and 0 <= timestep_index < len(self.time_series_levels_m):
            return self.time_series_levels_m[timestep_index]
        return self.fixed_level_m


class NodeHydraulicState(BaseModel):
    """Hydraulic state of a drainage node (manhole / inlet / junction / outfall) over a timestep.

    Attributes:
        node_id: Identifier of the DrainageNode
        external_inflow_m3: Direct surface inflow into node during timestep [m³]
        upstream_inflow_m3: Water delivered to node by upstream channels [m³]
        total_inflow_m3: Sum of external and upstream inflows [m³]
        initial_storage_m3: Storage volume carried over from previous timestep [m³]
        total_available_m3: Total water available at node (initial storage + total inflow) [m³]
        downstream_outflow_m3: Water conveyed to downstream channels or outfall [m³]
        final_storage_m3: Water retained in node storage at end of timestep [m³]
        storage_capacity_m3: Maximum storage capacity of the node [m³]
        water_depth_m: Depth of stored water in node shaft [m]
        water_level_m: Water surface elevation in node [m] (invert + depth, if available)
        surcharge_volume_m3: Volume exceeding node storage that overflows to surface [m³]
        is_outfall: Whether this node acts as a network terminal outfall
        boundary_level_m: Downstream boundary water level applied [m] (if outfall)
        tailwater_submergence_factor: Capacity reduction factor phi in [0, 1] due to tailwater
        is_tailwater_limited: Whether outfall discharge was constrained by downstream water level
    """
    node_id: str
    external_inflow_m3: float = Field(default=0.0, ge=0.0)
    upstream_inflow_m3: float = Field(default=0.0, ge=0.0)
    total_inflow_m3: float = Field(default=0.0, ge=0.0)
    initial_storage_m3: float = Field(default=0.0, ge=0.0)
    total_available_m3: float = Field(default=0.0, ge=0.0)
    downstream_outflow_m3: float = Field(default=0.0, ge=0.0)
    final_storage_m3: float = Field(default=0.0, ge=0.0)
    storage_capacity_m3: float = Field(default=0.0, ge=0.0)
    water_depth_m: float = Field(default=0.0, ge=0.0)
    water_level_m: Optional[float] = None
    surcharge_volume_m3: float = Field(default=0.0, ge=0.0)
    is_outfall: bool = False
    boundary_level_m: Optional[float] = None
    tailwater_submergence_factor: Optional[float] = None
    is_tailwater_limited: bool = False


class ChannelHydraulicState(BaseModel):
    """Hydraulic state of a drainage channel conduit over a timestep.

    Attributes:
        channel_id: Identifier of the DrainageChannel
        upstream_node_id: Upstream node ID (US_NODE_ID, authoritative)
        downstream_node_id: Downstream node ID (DS_NODE_ID, authoritative)
        full_capacity_m3: Full gravity capacity via Manning's equation over timestep [m³]
        effective_capacity_m3: Usable capacity after downstream bottleneck/tailwater constraint [m³]
        inflow_m3: Water allocated to enter channel from upstream node [m³]
        conveyed_m3: Water successfully conveyed through channel to downstream node [m³]
        excess_m3: Water that could not be conveyed due to capacity limits [m³]
        is_capacity_limited: Whether channel was constrained by its own physical capacity
        is_downstream_throttled: Whether channel was constrained by downstream backpressure/tailwater
    """
    channel_id: str
    upstream_node_id: str
    downstream_node_id: str
    full_capacity_m3: float = Field(default=0.0, ge=0.0)
    effective_capacity_m3: float = Field(default=0.0, ge=0.0)
    inflow_m3: float = Field(default=0.0, ge=0.0)
    conveyed_m3: float = Field(default=0.0, ge=0.0)
    excess_m3: float = Field(default=0.0, ge=0.0)
    is_capacity_limited: bool = False
    is_downstream_throttled: bool = False


class NetworkPropagationTimestepResult(BaseModel):
    """Result of network hydraulic propagation for a single timestep."""
    timestep_index: int = 0
    timestep_hours: float = 1.0
    nodes: Dict[str, NodeHydraulicState]
    channels: Dict[str, ChannelHydraulicState]
    total_external_inflow_m3: float
    total_outfall_outflow_m3: float
    total_initial_storage_m3: float
    total_final_storage_m3: float
    total_surcharge_volume_m3: float
    mass_balance_error_m3: float
    boundary_type: Optional[str] = None
    boundary_level_m: Optional[float] = None
    disclaimer: str = (
        "Simplified network mass-balance / tailwater backpressure model. "
        "Not a dynamic 1D/2D Saint-Venant solver; does not claim real tide observations."
    )


def compute_node_invert_elevation(node_id: str, network: DrainageNetwork) -> Optional[float]:
    """Determine representative invert elevation for a node from connected channels.

    Returns the minimum invert among incoming (ds_invert_m) and outgoing (us_invert_m) channels.
    """
    inverts: List[float] = []
    for c in network.channels.values():
        if c.downstream_node_id == node_id and c.ds_invert_m is not None:
            inverts.append(c.ds_invert_m)
        elif c.upstream_node_id == node_id and c.us_invert_m is not None:
            inverts.append(c.us_invert_m)
    return min(inverts) if inverts else None


def compute_tailwater_submergence_factor(
    node_id: str,
    network: DrainageNetwork,
    boundary_level_m: Optional[float] = None,
) -> float:
    """Compute tailwater submergence reduction factor phi in [0.0, 1.0] for an outfall node.

    Physics / Engineering Formulation:
      - If boundary_level_m is None or <= invert: phi = 1.0 (Free gravity discharge)
      - If boundary_level_m >= head_max (ground level or crown): phi = 0.0 (Tide locked)
      - If invert < boundary_level_m < head_max:
          Submerged orifice head-loss:
          phi = sqrt((head_max - boundary_level_m) / (head_max - invert))
    """
    if boundary_level_m is None:
        return 1.0

    node = network.nodes.get(node_id)
    if node is None:
        return 1.0

    invert = compute_node_invert_elevation(node_id, network)
    if invert is None:
        invert = node.elevation_m

    # Estimate conduit height from incoming channels
    in_channels = [c for c in network.channels.values() if c.downstream_node_id == node_id]
    heights = [
        (c.conduit_height_mm / 1000.0) if c.conduit_height_mm
        else ((c.conduit_width_mm / 1000.0) if c.conduit_width_mm else 1.0)
        for c in in_channels
    ]
    conduit_h = max(heights) if heights else 1.0

    # Ground level or conduit crown as upper head limit
    gl = node.ground_level_m
    if gl is not None and gl > invert:
        head_max = gl
    else:
        head_max = invert + conduit_h

    if head_max <= invert:
        head_max = invert + 1.0

    if boundary_level_m <= invert:
        return 1.0
    elif boundary_level_m >= head_max:
        return 0.0
    else:
        phi = math.sqrt((head_max - boundary_level_m) / (head_max - invert))
        return max(0.0, min(1.0, phi))


def compute_manhole_storage_capacity(
    node: DrainageNode,
    network: DrainageNetwork,
    default_diameter_m: float = 1.0,
    default_storage_m3: float = 0.0,
) -> float:
    """Compute physical storage volume of a manhole shaft [m³].

    Storage = cross_sectional_area * max(0, ground_level - invert).
    If ground level or inverts are not available, returns default_storage_m3.
    """
    if node.ground_level_m is not None:
        invert = compute_node_invert_elevation(node.id, network)
        if invert is not None and node.ground_level_m > invert:
            depth = node.ground_level_m - invert
            radius = default_diameter_m / 2.0
            area = math.pi * (radius ** 2)
            return area * depth
    return default_storage_m3


def topological_sort_dag(network: DrainageNetwork) -> List[str]:
    """Compute topological ordering of network nodes (upstream to downstream).

    Because the BMC network is a directed acyclic graph (DAG), Kahn's algorithm
    produces a complete ordering from source inlets down to outfalls.
    """
    in_degree: Dict[str, int] = {nid: 0 for nid in network.nodes.keys()}
    out_adj: Dict[str, List[str]] = {nid: [] for nid in network.nodes.keys()}

    for c in network.channels.values():
        u = c.upstream_node_id
        v = c.downstream_node_id
        if u in network.nodes and v in network.nodes:
            out_adj[u].append(v)
            in_degree[v] = in_degree.get(v, 0) + 1

    queue = [nid for nid, deg in in_degree.items() if deg == 0]
    topo_order: List[str] = []

    while queue:
        curr = queue.pop(0)
        topo_order.append(curr)
        for nxt in out_adj.get(curr, []):
            in_degree[nxt] -= 1
            if in_degree[nxt] == 0:
                queue.append(nxt)

    if len(topo_order) < len(network.nodes):
        visited = set(topo_order)
        for nid in network.nodes.keys():
            if nid not in visited:
                topo_order.append(nid)

    return topo_order


def propagate_network_timestep(
    network: DrainageNetwork,
    node_external_inflows_m3: Dict[str, float],
    initial_node_storage_m3: Optional[Dict[str, float]] = None,
    channel_capacities: Optional[Dict[str, ChannelCapacity]] = None,
    node_storage_capacities_m3: Optional[Dict[str, float]] = None,
    boundary_condition: Optional[DownstreamBoundaryCondition] = None,
    boundary_level_m: Optional[float] = None,
    timestep_hours: float = 1.0,
    timestep_index: int = 0,
    default_manhole_diameter_m: float = 1.0,
    default_node_storage_m3: float = 0.0,
    assumed_manning_n: float = 0.018,
) -> NetworkPropagationTimestepResult:
    """Execute simplified network mass-balance and hydraulic surcharge propagation for one timestep.

    Downstream Boundary Condition & Backwater Integration:
      - Outfall nodes (out-degree 0 or NodeType.OUTLET) interact with downstream boundary water level H_boundary(t).
      - Free discharge occurs when H_boundary <= outfall invert (phi = 1.0).
      - Submerged tailwater reduces outfall conveyance (0 < phi < 1.0).
      - Tide lock occurs when H_boundary >= outfall ground level (phi = 0.0).
      - Tailwater capacity limitations propagate backwater surcharge upstream in Pass 1.
      - Strict mass conservation is mathematically guaranteed at every node.
    """
    if timestep_hours <= 0:
        raise ValueError("Timestep hours must be positive")

    # Topological order: upstream -> downstream
    topo_order = topological_sort_dag(network)
    reverse_topo_order = topo_order[::-1]

    # Precompute channel connection lookups
    in_channels: Dict[str, List[str]] = {nid: [] for nid in network.nodes.keys()}
    out_channels: Dict[str, List[str]] = {nid: [] for nid in network.nodes.keys()}
    for cid, c in network.channels.items():
        if c.upstream_node_id in out_channels:
            out_channels[c.upstream_node_id].append(cid)
        if c.downstream_node_id in in_channels:
            in_channels[c.downstream_node_id].append(cid)

    # 1. Precompute channel capacities
    if channel_capacities is None:
        channel_caps: Dict[str, ChannelCapacity] = {}
        for cid, channel in network.channels.items():
            channel_caps[cid] = compute_channel_capacity(
                channel=channel,
                timestep_hours=timestep_hours,
                assumed_manning_n=assumed_manning_n,
            )
    else:
        channel_caps = channel_capacities

    # 2. Node initial storage and storage capacities
    init_storage: Dict[str, float] = {}
    storage_caps: Dict[str, float] = {}
    ext_inflows: Dict[str, float] = {}

    for nid, node in network.nodes.items():
        init_storage[nid] = max(0.0, initial_node_storage_m3.get(nid, 0.0) if initial_node_storage_m3 else 0.0)
        ext_inflows[nid] = max(0.0, node_external_inflows_m3.get(nid, 0.0))
        if node_storage_capacities_m3 is not None and nid in node_storage_capacities_m3:
            storage_caps[nid] = max(0.0, node_storage_capacities_m3[nid])
        else:
            storage_caps[nid] = compute_manhole_storage_capacity(
                node=node,
                network=network,
                default_diameter_m=default_manhole_diameter_m,
                default_storage_m3=default_node_storage_m3,
            )

    # 3. Resolve boundary condition inputs
    resolved_boundary_type = "FREE_DISCHARGE"
    primary_boundary_level = None
    if boundary_condition is not None:
        resolved_boundary_type = boundary_condition.boundary_type.value
        primary_boundary_level = boundary_condition.get_boundary_level(timestep_index)
    elif boundary_level_m is not None:
        resolved_boundary_type = BoundarySourceType.SYNTHETIC.value
        primary_boundary_level = boundary_level_m

    # =========================================================================
    # PASS 1: BACKWARD PASS (Downstream Bottleneck & Tailwater Backpressure)
    # =========================================================================
    eff_capacities: Dict[str, float] = {}
    is_downstream_throttled: Dict[str, bool] = {cid: False for cid in network.channels.keys()}
    outfall_submergence_factors: Dict[str, float] = {}
    outfall_limits: Dict[str, float] = {}

    for nid in reverse_topo_order:
        node = network.nodes[nid]
        out_cids = out_channels[nid]
        in_cids = in_channels[nid]

        is_outfall = (len(out_cids) == 0) or (node.node_type == NodeType.OUTLET)

        if is_outfall:
            # Resolve boundary level for this outfall node
            b_level = None
            if boundary_condition is not None:
                b_level = boundary_condition.get_boundary_level(timestep_index, nid)
            elif boundary_level_m is not None:
                b_level = boundary_level_m

            phi = compute_tailwater_submergence_factor(nid, network, b_level)
            outfall_submergence_factors[nid] = phi

            total_physical_in_cap = sum(channel_caps[cid].capacity_volume_m3 for cid in in_cids)
            avail_storage = max(0.0, storage_caps[nid] - init_storage[nid])

            if phi >= 1.0:
                # Free outfall discharge
                v_allow = float("inf")
                outfall_limits[nid] = float("inf")
            else:
                # Tailwater-submerged outfall discharge capacity
                c_outfall_limit = phi * total_physical_in_cap
                outfall_limits[nid] = c_outfall_limit
                v_allow = max(0.0, c_outfall_limit + avail_storage - ext_inflows[nid])
        else:
            # Internal node: sum of outgoing effective capacities
            c_out_total = sum(eff_capacities[cid] for cid in out_cids)
            avail_storage = max(0.0, storage_caps[nid] - init_storage[nid])
            v_allow = max(0.0, c_out_total + avail_storage - ext_inflows[nid])

        # Constrain incoming channels entering this node
        if in_cids:
            total_physical_in_cap = sum(channel_caps[cid].capacity_volume_m3 for cid in in_cids)
            if total_physical_in_cap == 0.0:
                for cid in in_cids:
                    eff_capacities[cid] = 0.0
            elif total_physical_in_cap <= v_allow:
                for cid in in_cids:
                    eff_capacities[cid] = channel_caps[cid].capacity_volume_m3
            else:
                # Downstream bottleneck / tailwater backpressure throttles incoming channels
                throttle_ratio = v_allow / total_physical_in_cap
                for cid in in_cids:
                    phys_cap = channel_caps[cid].capacity_volume_m3
                    eff_capacities[cid] = phys_cap * throttle_ratio
                    if eff_capacities[cid] < phys_cap:
                        is_downstream_throttled[cid] = True

    # =========================================================================
    # PASS 2: FORWARD PASS (Mass Conservation & Conveyance Propagation)
    # =========================================================================
    channel_conveyed: Dict[str, float] = {}
    channel_inflows: Dict[str, float] = {}
    channel_excesses: Dict[str, float] = {}

    node_upstream_inflows: Dict[str, float] = {nid: 0.0 for nid in network.nodes.keys()}
    node_outflows: Dict[str, float] = {nid: 0.0 for nid in network.nodes.keys()}
    node_final_storage: Dict[str, float] = {}
    node_surcharges: Dict[str, float] = {}
    outfall_outflows: Dict[str, float] = {}

    for nid in topo_order:
        node = network.nodes[nid]
        out_cids = out_channels[nid]

        w_avail = init_storage[nid] + ext_inflows[nid] + node_upstream_inflows[nid]
        is_outfall = (len(out_cids) == 0) or (node.node_type == NodeType.OUTLET)

        if is_outfall:
            phi = outfall_submergence_factors.get(nid, 1.0)
            limit = outfall_limits.get(nid, float("inf"))

            if phi >= 1.0:
                q_outfall = w_avail
                r_rem = 0.0
            else:
                q_outfall = min(w_avail, limit)
                r_rem = max(0.0, w_avail - q_outfall)

            outfall_outflows[nid] = q_outfall
            node_outflows[nid] = q_outfall

            # Water remaining at outfall node accumulates in storage or surcharges
            s_cap = storage_caps[nid]
            s_final = min(r_rem, s_cap)
            surcharge = max(0.0, r_rem - s_final)

            node_final_storage[nid] = s_final
            node_surcharges[nid] = surcharge

            for cid in out_cids:
                channel_inflows[cid] = 0.0
                channel_conveyed[cid] = 0.0
                channel_excesses[cid] = 0.0
        else:
            c_eff_out_tot = sum(eff_capacities[cid] for cid in out_cids)
            phys_out_tot = sum(channel_caps[cid].capacity_volume_m3 for cid in out_cids)
            conveyed_from_node = 0.0

            if c_eff_out_tot > 0.0:
                if w_avail <= c_eff_out_tot:
                    for cid in out_cids:
                        share = eff_capacities[cid] / c_eff_out_tot
                        q_conv = w_avail * share
                        channel_inflows[cid] = q_conv
                        channel_conveyed[cid] = q_conv
                        channel_excesses[cid] = 0.0
                        conveyed_from_node += q_conv
                        ds_nid = network.channels[cid].downstream_node_id
                        node_upstream_inflows[ds_nid] = node_upstream_inflows.get(ds_nid, 0.0) + q_conv
                else:
                    for cid in out_cids:
                        q_conv = eff_capacities[cid]
                        phys_share = channel_caps[cid].capacity_volume_m3 / phys_out_tot if phys_out_tot > 0 else (1.0 / len(out_cids))
                        q_in = w_avail * phys_share
                        channel_inflows[cid] = q_in
                        channel_conveyed[cid] = q_conv
                        channel_excesses[cid] = max(0.0, q_in - q_conv)
                        conveyed_from_node += q_conv
                        ds_nid = network.channels[cid].downstream_node_id
                        node_upstream_inflows[ds_nid] = node_upstream_inflows.get(ds_nid, 0.0) + q_conv
            else:
                for cid in out_cids:
                    channel_inflows[cid] = 0.0
                    channel_conveyed[cid] = 0.0
                    channel_excesses[cid] = 0.0

            node_outflows[nid] = conveyed_from_node
            r_rem = max(0.0, w_avail - conveyed_from_node)

            s_cap = storage_caps[nid]
            s_final = min(r_rem, s_cap)
            surcharge = max(0.0, r_rem - s_final)

            node_final_storage[nid] = s_final
            node_surcharges[nid] = surcharge

    # 4. Assemble channel hydraulic states
    channel_states: Dict[str, ChannelHydraulicState] = {}
    for cid, c in network.channels.items():
        phys_cap = channel_caps[cid].capacity_volume_m3
        eff_cap = eff_capacities.get(cid, 0.0)
        q_in = channel_inflows.get(cid, 0.0)
        q_conv = channel_conveyed.get(cid, 0.0)
        q_exc = channel_excesses.get(cid, 0.0)
        is_cap_lim = (q_in > phys_cap) or (phys_cap == 0.0 and q_in > 0)
        is_ds_thr = is_downstream_throttled.get(cid, False)

        channel_states[cid] = ChannelHydraulicState(
            channel_id=cid,
            upstream_node_id=c.upstream_node_id,
            downstream_node_id=c.downstream_node_id,
            full_capacity_m3=phys_cap,
            effective_capacity_m3=eff_cap,
            inflow_m3=q_in,
            conveyed_m3=q_conv,
            excess_m3=q_exc,
            is_capacity_limited=is_cap_lim,
            is_downstream_throttled=is_ds_thr,
        )

    # 5. Assemble node hydraulic states
    node_states: Dict[str, NodeHydraulicState] = {}
    for nid, node in network.nodes.items():
        ext_in = ext_inflows[nid]
        up_in = node_upstream_inflows.get(nid, 0.0)
        tot_in = ext_in + up_in
        s_init = init_storage[nid]
        tot_avail = s_init + tot_in
        outflow = node_outflows.get(nid, 0.0)
        s_fin = node_final_storage.get(nid, 0.0)
        surch = node_surcharges.get(nid, 0.0)
        s_cap = storage_caps[nid]

        is_outfall = (len(out_channels[nid]) == 0) or (node.node_type == NodeType.OUTLET)
        phi = outfall_submergence_factors.get(nid) if is_outfall else None

        b_level = None
        if is_outfall:
            if boundary_condition is not None:
                b_level = boundary_condition.get_boundary_level(timestep_index, nid)
            elif boundary_level_m is not None:
                b_level = boundary_level_m

        mh_radius = default_manhole_diameter_m / 2.0
        mh_area = math.pi * (mh_radius ** 2)
        depth = s_fin / mh_area if mh_area > 0 else 0.0

        invert = compute_node_invert_elevation(nid, network)
        w_elev = (invert + depth) if invert is not None else (node.elevation_m + depth)

        node_states[nid] = NodeHydraulicState(
            node_id=nid,
            external_inflow_m3=ext_in,
            upstream_inflow_m3=up_in,
            total_inflow_m3=tot_in,
            initial_storage_m3=s_init,
            total_available_m3=tot_avail,
            downstream_outflow_m3=outflow,
            final_storage_m3=s_fin,
            storage_capacity_m3=s_cap,
            water_depth_m=depth,
            water_level_m=w_elev,
            surcharge_volume_m3=surch,
            is_outfall=is_outfall,
            boundary_level_m=b_level,
            tailwater_submergence_factor=phi,
            is_tailwater_limited=(phi is not None and phi < 1.0),
        )

    # 6. Mass conservation check
    total_ext_inflow = sum(ext_inflows.values())
    total_init_storage = sum(init_storage.values())
    total_final_storage = sum(node_final_storage.values())
    total_outfall_outflow = sum(outfall_outflows.values())
    total_surcharge = sum(node_surcharges.values())

    total_mass_in = total_ext_inflow + total_init_storage
    total_mass_out = total_outfall_outflow + total_final_storage + total_surcharge
    mass_balance_error = abs(total_mass_in - total_mass_out)

    return NetworkPropagationTimestepResult(
        timestep_index=timestep_index,
        timestep_hours=timestep_hours,
        nodes=node_states,
        channels=channel_states,
        total_external_inflow_m3=total_ext_inflow,
        total_outfall_outflow_m3=total_outfall_outflow,
        total_initial_storage_m3=total_init_storage,
        total_final_storage_m3=total_final_storage,
        total_surcharge_volume_m3=total_surcharge,
        mass_balance_error_m3=mass_balance_error,
        boundary_type=resolved_boundary_type,
        boundary_level_m=primary_boundary_level,
    )


def propagate_network_series(
    network: DrainageNetwork,
    series_external_inflows_m3: List[Dict[str, float]],
    initial_node_storage_m3: Optional[Dict[str, float]] = None,
    channel_capacities: Optional[Dict[str, ChannelCapacity]] = None,
    node_storage_capacities_m3: Optional[Dict[str, float]] = None,
    boundary_condition: Optional[DownstreamBoundaryCondition] = None,
    series_boundary_levels_m: Optional[List[float]] = None,
    timestep_hours: float = 1.0,
    default_manhole_diameter_m: float = 1.0,
    default_node_storage_m3: float = 0.0,
    assumed_manning_n: float = 0.018,
) -> List[NetworkPropagationTimestepResult]:
    """Execute network hydraulic propagation across a sequence of timesteps with boundary conditions."""
    results: List[NetworkPropagationTimestepResult] = []
    current_storage = initial_node_storage_m3

    # Precompute channel capacities once for speed if not provided
    if channel_capacities is None:
        channel_caps: Dict[str, ChannelCapacity] = {}
        for cid, channel in network.channels.items():
            channel_caps[cid] = compute_channel_capacity(
                channel=channel,
                timestep_hours=timestep_hours,
                assumed_manning_n=assumed_manning_n,
            )
    else:
        channel_caps = channel_capacities

    # Setup boundary condition if series passed directly
    active_boundary = boundary_condition
    if active_boundary is None and series_boundary_levels_m is not None:
        active_boundary = DownstreamBoundaryCondition(
            boundary_type=BoundarySourceType.SYNTHETIC,
            time_series_levels_m=series_boundary_levels_m,
            description="Synthetic time-varying downstream boundary level series"
        )

    for idx, step_inflows in enumerate(series_external_inflows_m3):
        res = propagate_network_timestep(
            network=network,
            node_external_inflows_m3=step_inflows,
            initial_node_storage_m3=current_storage,
            channel_capacities=channel_caps,
            node_storage_capacities_m3=node_storage_capacities_m3,
            boundary_condition=active_boundary,
            timestep_hours=timestep_hours,
            timestep_index=idx,
            default_manhole_diameter_m=default_manhole_diameter_m,
            default_node_storage_m3=default_node_storage_m3,
            assumed_manning_n=assumed_manning_n,
        )
        results.append(res)
        current_storage = {nid: ns.final_storage_m3 for nid, ns in res.nodes.items()}

    return results


__all__ = [
    "BoundarySourceType",
    "DownstreamBoundaryCondition",
    "NodeHydraulicState",
    "ChannelHydraulicState",
    "NetworkPropagationTimestepResult",
    "compute_manhole_storage_capacity",
    "compute_node_invert_elevation",
    "compute_tailwater_submergence_factor",
    "topological_sort_dag",
    "propagate_network_timestep",
    "propagate_network_series",
]
