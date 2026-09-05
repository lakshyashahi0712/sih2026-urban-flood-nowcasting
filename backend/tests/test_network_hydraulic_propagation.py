"""Tests for Phase 2.2: Network Hydraulic Propagation.

Verifies:
1. Serial two-channel propagation (Node 1 -> Chan 1 -> Node 2 -> Chan 2 -> Node 3).
2. Branching junction:
   - Confluence (2 upstream channels merging into 1 downstream channel).
   - Divergence (1 upstream channel splitting into 2 downstream channels).
3. Capacity-limited downstream channel (downstream bottleneck constrains flow).
4. Upstream surcharge propagation (excess water backs up and surcharges at upstream nodes).
5. Node storage (manhole shaft stores water up to capacity, spills remaining excess).
6. Strict mass conservation across all nodes and entire network (error < 1e-10).
7. BMC US_NODE_ID -> DS_NODE_ID direction is authoritative and never reversed.
8. Multi-timestep state persistence (storage carries over, drains during dry periods).
9. Full BMC network integration with 1,240 real drains and 1,264 nodes.
"""
from __future__ import annotations

import pytest
from backend.app.domain.drainage.models import (
    DrainageNetwork,
    DrainageNode,
    DrainageChannel,
    NodeType,
    Provenance,
)
from backend.app.domain.drainage.capacity import (
    ChannelCapacity,
    compute_channel_capacity,
)
from backend.app.domain.drainage.propagation import (
    propagate_network_timestep,
    propagate_network_series,
    compute_manhole_storage_capacity,
    topological_sort_dag,
)
from backend.app.infrastructure.drainage.bmc_gis import BMCDrainageLoader


def make_test_node(nid: str, node_type: NodeType = NodeType.JUNCTION, elevation: float = 10.0, gl: float = 12.0) -> DrainageNode:
    return DrainageNode(
        id=nid,
        x=275000.0,
        y=2110000.0,
        elevation_m=elevation,
        node_type=node_type,
        provenance=Provenance.BMC,
        ground_level_m=gl,
    )


def make_test_channel(
    cid: str,
    us_id: str,
    ds_id: str,
    length: float = 100.0,
    us_inv: float = 10.0,
    ds_inv: float = 9.0,
    shape: str = "RECT",
    width_mm: float = 1000.0,
    height_mm: float = 1000.0,
) -> DrainageChannel:
    return DrainageChannel(
        id=cid,
        upstream_node_id=us_id,
        downstream_node_id=ds_id,
        length_m=length,
        provenance=Provenance.BMC,
        us_invert_m=us_inv,
        ds_invert_m=ds_inv,
        shape=shape,
        conduit_width_mm=width_mm,
        conduit_height_mm=height_mm,
    )


def test_serial_two_channel_propagation():
    """Verify water propagates smoothly through a serial 2-channel conduit to the outfall."""
    # N1 (Inlet) -> C1 -> N2 (Junction) -> C2 -> N3 (Outlet)
    nodes = {
        "N1": make_test_node("N1", NodeType.INLET, elevation=12.0),
        "N2": make_test_node("N2", NodeType.JUNCTION, elevation=11.0),
        "N3": make_test_node("N3", NodeType.OUTLET, elevation=10.0),
    }
    channels = {
        "C1": make_test_channel("C1", "N1", "N2", us_inv=12.0, ds_inv=11.0),
        "C2": make_test_channel("C2", "N2", "N3", us_inv=11.0, ds_inv=10.0),
    }
    net = DrainageNetwork(nodes=nodes, channels=channels, crs="EPSG:32643")

    caps = {
        "C1": ChannelCapacity(channel_id="C1", capacity_m3_per_s=0.1, capacity_volume_m3=100.0),
        "C2": ChannelCapacity(channel_id="C2", capacity_m3_per_s=0.1, capacity_volume_m3=100.0),
    }

    inflows = {"N1": 60.0, "N2": 0.0, "N3": 0.0}
    res = propagate_network_timestep(
        network=net,
        node_external_inflows_m3=inflows,
        channel_capacities=caps,
        node_storage_capacities_m3={"N1": 0.0, "N2": 0.0, "N3": 0.0},
    )

    # Conveyance check
    assert res.channels["C1"].conveyed_m3 == pytest.approx(60.0)
    assert res.channels["C2"].conveyed_m3 == pytest.approx(60.0)
    assert res.nodes["N2"].upstream_inflow_m3 == pytest.approx(60.0)
    assert res.total_outfall_outflow_m3 == pytest.approx(60.0)
    assert res.total_surcharge_volume_m3 == pytest.approx(0.0)
    assert res.mass_balance_error_m3 == pytest.approx(0.0, abs=1e-10)


def test_branching_junction_confluence():
    """Verify confluences: two upstream tributaries converge into a single downstream conduit."""
    # N1 -> C1 -> N3, N2 -> C2 -> N3, N3 -> C3 -> N4 (Outlet)
    nodes = {
        "N1": make_test_node("N1", NodeType.INLET),
        "N2": make_test_node("N2", NodeType.INLET),
        "N3": make_test_node("N3", NodeType.JUNCTION),
        "N4": make_test_node("N4", NodeType.OUTLET),
    }
    channels = {
        "C1": make_test_channel("C1", "N1", "N3"),
        "C2": make_test_channel("C2", "N2", "N3"),
        "C3": make_test_channel("C3", "N3", "N4"),
    }
    net = DrainageNetwork(nodes=nodes, channels=channels, crs="EPSG:32643")

    caps = {
        "C1": ChannelCapacity(channel_id="C1", capacity_m3_per_s=0.1, capacity_volume_m3=50.0),
        "C2": ChannelCapacity(channel_id="C2", capacity_m3_per_s=0.1, capacity_volume_m3=50.0),
        "C3": ChannelCapacity(channel_id="C3", capacity_m3_per_s=0.2, capacity_volume_m3=100.0),
    }

    inflows = {"N1": 30.0, "N2": 40.0, "N3": 0.0, "N4": 0.0}
    res = propagate_network_timestep(
        network=net,
        node_external_inflows_m3=inflows,
        channel_capacities=caps,
        node_storage_capacities_m3={"N1": 0.0, "N2": 0.0, "N3": 0.0, "N4": 0.0},
    )

    assert res.channels["C1"].conveyed_m3 == pytest.approx(30.0)
    assert res.channels["C2"].conveyed_m3 == pytest.approx(40.0)
    assert res.nodes["N3"].upstream_inflow_m3 == pytest.approx(70.0)
    assert res.channels["C3"].conveyed_m3 == pytest.approx(70.0)
    assert res.total_outfall_outflow_m3 == pytest.approx(70.0)
    assert res.mass_balance_error_m3 == pytest.approx(0.0, abs=1e-10)


def test_branching_junction_divergence():
    """Verify divergences: a single node splits flow proportionally into two outgoing channels."""
    # N1 -> C1 -> N2 (Outlet), N1 -> C2 -> N3 (Outlet)
    nodes = {
        "N1": make_test_node("N1", NodeType.INLET),
        "N2": make_test_node("N2", NodeType.OUTLET),
        "N3": make_test_node("N3", NodeType.OUTLET),
    }
    channels = {
        "C1": make_test_channel("C1", "N1", "N2"),
        "C2": make_test_channel("C2", "N1", "N3"),
    }
    net = DrainageNetwork(nodes=nodes, channels=channels, crs="EPSG:32643")

    caps = {
        "C1": ChannelCapacity(channel_id="C1", capacity_m3_per_s=0.06, capacity_volume_m3=60.0),
        "C2": ChannelCapacity(channel_id="C2", capacity_m3_per_s=0.04, capacity_volume_m3=40.0),
    }

    inflows = {"N1": 50.0, "N2": 0.0, "N3": 0.0}
    res = propagate_network_timestep(
        network=net,
        node_external_inflows_m3=inflows,
        channel_capacities=caps,
        node_storage_capacities_m3={"N1": 0.0, "N2": 0.0, "N3": 0.0},
    )

    # 50 split by 60:40 capacity ratio -> 30 to C1, 20 to C2
    assert res.channels["C1"].conveyed_m3 == pytest.approx(30.0)
    assert res.channels["C2"].conveyed_m3 == pytest.approx(20.0)
    assert res.total_outfall_outflow_m3 == pytest.approx(50.0)
    assert res.mass_balance_error_m3 == pytest.approx(0.0, abs=1e-10)


def test_capacity_limited_downstream_channel():
    """Verify that when a downstream channel has limited capacity, flow is constrained and excess surcharges."""
    # N1 -> C1 (cap=100) -> N2 -> C2 (cap=35) -> N3 (Outlet)
    nodes = {
        "N1": make_test_node("N1", NodeType.INLET),
        "N2": make_test_node("N2", NodeType.JUNCTION),
        "N3": make_test_node("N3", NodeType.OUTLET),
    }
    channels = {
        "C1": make_test_channel("C1", "N1", "N2"),
        "C2": make_test_channel("C2", "N2", "N3"),
    }
    net = DrainageNetwork(nodes=nodes, channels=channels, crs="EPSG:32643")

    caps = {
        "C1": ChannelCapacity(channel_id="C1", capacity_m3_per_s=0.1, capacity_volume_m3=100.0),
        "C2": ChannelCapacity(channel_id="C2", capacity_m3_per_s=0.035, capacity_volume_m3=35.0),
    }

    inflows = {"N1": 70.0, "N2": 0.0, "N3": 0.0}
    res = propagate_network_timestep(
        network=net,
        node_external_inflows_m3=inflows,
        channel_capacities=caps,
        node_storage_capacities_m3={"N1": 0.0, "N2": 0.0, "N3": 0.0},
    )

    # Downstream C2 capacity of 35 throttles C1 effective capacity to 35
    assert res.channels["C1"].effective_capacity_m3 == pytest.approx(35.0)
    assert res.channels["C1"].conveyed_m3 == pytest.approx(35.0)
    assert res.channels["C2"].conveyed_m3 == pytest.approx(35.0)
    assert res.channels["C1"].is_downstream_throttled is True

    # Remaining 35 surcharges upstream at N1
    assert res.nodes["N1"].surcharge_volume_m3 == pytest.approx(35.0)
    assert res.total_outfall_outflow_m3 == pytest.approx(35.0)
    assert res.total_surcharge_volume_m3 == pytest.approx(35.0)
    assert res.mass_balance_error_m3 == pytest.approx(0.0, abs=1e-10)


def test_upstream_surcharge_propagation():
    """Verify multi-segment backwater surcharge propagation: bottleneck at tail propagates all the way upstream."""
    # N1 -> C1 (100) -> N2 -> C2 (100) -> N3 -> C3 (20) -> N4 (Outlet)
    nodes = {
        "N1": make_test_node("N1", NodeType.INLET),
        "N2": make_test_node("N2", NodeType.JUNCTION),
        "N3": make_test_node("N3", NodeType.JUNCTION),
        "N4": make_test_node("N4", NodeType.OUTLET),
    }
    channels = {
        "C1": make_test_channel("C1", "N1", "N2"),
        "C2": make_test_channel("C2", "N2", "N3"),
        "C3": make_test_channel("C3", "N3", "N4"),
    }
    net = DrainageNetwork(nodes=nodes, channels=channels, crs="EPSG:32643")

    caps = {
        "C1": ChannelCapacity(channel_id="C1", capacity_m3_per_s=0.1, capacity_volume_m3=100.0),
        "C2": ChannelCapacity(channel_id="C2", capacity_m3_per_s=0.1, capacity_volume_m3=100.0),
        "C3": ChannelCapacity(channel_id="C3", capacity_m3_per_s=0.02, capacity_volume_m3=20.0),
    }

    inflows = {"N1": 80.0, "N2": 0.0, "N3": 0.0, "N4": 0.0}
    res = propagate_network_timestep(
        network=net,
        node_external_inflows_m3=inflows,
        channel_capacities=caps,
        node_storage_capacities_m3={"N1": 0.0, "N2": 0.0, "N3": 0.0, "N4": 0.0},
    )

    # C3 limit (20) throttles C2 (20), which in turn throttles C1 (20)
    assert res.channels["C1"].effective_capacity_m3 == pytest.approx(20.0)
    assert res.channels["C2"].effective_capacity_m3 == pytest.approx(20.0)
    assert res.channels["C3"].effective_capacity_m3 == pytest.approx(20.0)

    assert res.channels["C1"].conveyed_m3 == pytest.approx(20.0)
    assert res.channels["C2"].conveyed_m3 == pytest.approx(20.0)
    assert res.channels["C3"].conveyed_m3 == pytest.approx(20.0)

    # 60 surcharges at N1 (the upstream origin)
    assert res.nodes["N1"].surcharge_volume_m3 == pytest.approx(60.0)
    assert res.total_outfall_outflow_m3 == pytest.approx(20.0)
    assert res.total_surcharge_volume_m3 == pytest.approx(60.0)
    assert res.mass_balance_error_m3 == pytest.approx(0.0, abs=1e-10)


def test_node_storage_accumulation_and_spill():
    """Verify node storage accumulates water up to S_max and spills excess when full."""
    # N1 -> C1 (cap=100) -> N2 (storage=15) -> C2 (cap=20) -> N3 (Outlet)
    nodes = {
        "N1": make_test_node("N1", NodeType.INLET),
        "N2": make_test_node("N2", NodeType.JUNCTION),
        "N3": make_test_node("N3", NodeType.OUTLET),
    }
    channels = {
        "C1": make_test_channel("C1", "N1", "N2"),
        "C2": make_test_channel("C2", "N2", "N3"),
    }
    net = DrainageNetwork(nodes=nodes, channels=channels, crs="EPSG:32643")

    caps = {
        "C1": ChannelCapacity(channel_id="C1", capacity_m3_per_s=0.1, capacity_volume_m3=100.0),
        "C2": ChannelCapacity(channel_id="C2", capacity_m3_per_s=0.02, capacity_volume_m3=20.0),
    }

    inflows = {"N1": 50.0, "N2": 0.0, "N3": 0.0}
    res = propagate_network_timestep(
        network=net,
        node_external_inflows_m3=inflows,
        channel_capacities=caps,
        node_storage_capacities_m3={"N1": 0.0, "N2": 15.0, "N3": 0.0},
    )

    # N2 can convey 20 downstream and store 15 in manhole -> accepts 35 from C1
    assert res.channels["C1"].effective_capacity_m3 == pytest.approx(35.0)
    assert res.channels["C1"].conveyed_m3 == pytest.approx(35.0)
    assert res.channels["C2"].conveyed_m3 == pytest.approx(20.0)

    # N2 retains 15.0 in final storage
    assert res.nodes["N2"].final_storage_m3 == pytest.approx(15.0)
    assert res.nodes["N2"].surcharge_volume_m3 == pytest.approx(0.0)

    # Upstream N1 surcharges 15.0 (50 - 35 = 15)
    assert res.nodes["N1"].surcharge_volume_m3 == pytest.approx(15.0)
    assert res.total_outfall_outflow_m3 == pytest.approx(20.0)
    assert res.total_final_storage_m3 == pytest.approx(15.0)
    assert res.total_surcharge_volume_m3 == pytest.approx(15.0)

    # Mass balance: Inflow (50) == Outflow (20) + Storage (15) + Surcharge (15)
    assert res.mass_balance_error_m3 == pytest.approx(0.0, abs=1e-10)


def test_mass_conservation_multi_timesteps():
    """Verify strict cumulative mass conservation across multiple timesteps (wet -> dry -> dry)."""
    # N1 -> C1 (cap=100) -> N2 (storage=15) -> C2 (cap=20) -> N3 (Outlet)
    nodes = {
        "N1": make_test_node("N1", NodeType.INLET),
        "N2": make_test_node("N2", NodeType.JUNCTION),
        "N3": make_test_node("N3", NodeType.OUTLET),
    }
    channels = {
        "C1": make_test_channel("C1", "N1", "N2"),
        "C2": make_test_channel("C2", "N2", "N3"),
    }
    net = DrainageNetwork(nodes=nodes, channels=channels, crs="EPSG:32643")

    caps = {
        "C1": ChannelCapacity(channel_id="C1", capacity_m3_per_s=0.1, capacity_volume_m3=100.0),
        "C2": ChannelCapacity(channel_id="C2", capacity_m3_per_s=0.02, capacity_volume_m3=20.0),
    }

    series_inflows = [
        {"N1": 50.0, "N2": 0.0, "N3": 0.0},  # Timestep 1: Storm event
        {"N1": 0.0, "N2": 0.0, "N3": 0.0},   # Timestep 2: Rain stops; stored water drains
        {"N1": 0.0, "N2": 0.0, "N3": 0.0},   # Timestep 3: Completely dry
    ]

    results = propagate_network_series(
        network=net,
        series_external_inflows_m3=series_inflows,
        channel_capacities=caps,
        node_storage_capacities_m3={"N1": 0.0, "N2": 15.0, "N3": 0.0},
    )

    assert len(results) == 3

    # Step 1: 50 in -> 20 out, 15 stored at N2, 15 surcharged at N1
    assert results[0].total_outfall_outflow_m3 == pytest.approx(20.0)
    assert results[0].total_final_storage_m3 == pytest.approx(15.0)
    assert results[0].total_surcharge_volume_m3 == pytest.approx(15.0)
    assert results[0].mass_balance_error_m3 == pytest.approx(0.0, abs=1e-10)

    # Step 2: 0 in, 15 initial storage at N2 -> C2 drains 15.0 to N3!
    assert results[1].total_initial_storage_m3 == pytest.approx(15.0)
    assert results[1].total_outfall_outflow_m3 == pytest.approx(15.0)
    assert results[1].total_final_storage_m3 == pytest.approx(0.0)
    assert results[1].total_surcharge_volume_m3 == pytest.approx(0.0)
    assert results[1].mass_balance_error_m3 == pytest.approx(0.0, abs=1e-10)

    # Step 3: 0 in, 0 initial storage -> 0 out
    assert results[2].total_initial_storage_m3 == pytest.approx(0.0)
    assert results[2].total_outfall_outflow_m3 == pytest.approx(0.0)
    assert results[2].total_final_storage_m3 == pytest.approx(0.0)
    assert results[2].mass_balance_error_m3 == pytest.approx(0.0, abs=1e-10)

    # Cumulative check: Total Inflow (50) == Total Outflow (20+15=35) + Total Surcharge (15)
    total_in = sum(r.total_external_inflow_m3 for r in results)
    total_out = sum(r.total_outfall_outflow_m3 for r in results)
    total_sur = sum(r.total_surcharge_volume_m3 for r in results)
    assert total_in == pytest.approx(50.0)
    assert total_out + total_sur == pytest.approx(50.0)


def test_bmc_us_ds_direction_authoritative():
    """Verify BMC US_NODE_ID -> DS_NODE_ID is strictly respected and never reversed, even on adverse slopes."""
    net = BMCDrainageLoader.load_default_bmc_network()
    assert net is not None

    # Check adverse slope conduit bmc_drain_28238 (US invert 27.24 < DS invert 27.35)
    chan_adverse = net.channels["bmc_drain_28238"]
    assert chan_adverse.compute_longitudinal_slope() < 0.0

    # Execute propagation with inflow at US node
    us_node = chan_adverse.upstream_node_id
    ds_node = chan_adverse.downstream_node_id
    inflows = {us_node: 50.0}

    res = propagate_network_timestep(
        network=net,
        node_external_inflows_m3=inflows,
    )

    # Because slope is adverse, capacity is 0.0 m³; channel carries 0.0 flow forward
    # and NEVER reverses to carry flow backward from ds_node to us_node!
    adv_state = res.channels["bmc_drain_28238"]
    assert adv_state.full_capacity_m3 == 0.0
    assert adv_state.conveyed_m3 == 0.0
    assert adv_state.upstream_node_id == us_node
    assert adv_state.downstream_node_id == ds_node
    assert res.mass_balance_error_m3 == pytest.approx(0.0, abs=1e-6)


def test_real_bmc_network_full_propagation():
    """Verify propagation executes across all 1,240 BMC conduits and 1,264 nodes with strict mass conservation."""
    net = BMCDrainageLoader.load_default_bmc_network()
    assert net is not None
    assert len(net.channels) == 1240
    assert len(net.nodes) == 1264

    # Inject realistic monsoon inflow (50 m³ each) across all 78 inlet nodes (3,900 m³ total)
    inlet_nodes = [nid for nid, n in net.nodes.items() if n.node_type == NodeType.INLET]
    assert len(inlet_nodes) == 78
    inflows = {nid: 50.0 for nid in inlet_nodes}
    total_inflow = 78 * 50.0

    res = propagate_network_timestep(
        network=net,
        node_external_inflows_m3=inflows,
        timestep_hours=1.0,
    )

    # All 1,264 nodes and 1,240 channels have state records
    assert len(res.nodes) == 1264
    assert len(res.channels) == 1240

    # Flow is conveyed and/or surcharged
    assert res.total_external_inflow_m3 == pytest.approx(total_inflow)
    assert res.total_outfall_outflow_m3 > 0.0
    assert res.total_final_storage_m3 >= 0.0

    # Strict Mass Conservation across the entire Mumbai BMC network
    total_out = res.total_outfall_outflow_m3 + res.total_final_storage_m3 + res.total_surcharge_volume_m3
    assert total_out == pytest.approx(total_inflow, rel=1e-7)
    assert res.mass_balance_error_m3 == pytest.approx(0.0, abs=1e-6)

    # Disclaimer is present
    assert "Simplified network mass-balance" in res.disclaimer
