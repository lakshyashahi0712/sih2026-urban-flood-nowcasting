"""Tests for Phase 2.3: Coastal Outfall Boundary & Backwater.

Verifies:
1. Identification of BMC outlet / terminal nodes (all 43 outlet nodes).
2. Free discharge when downstream boundary is below or at outfall invert (phi = 1.0).
3. Elevated downstream boundary causing partial submergence and throttled discharge (0 < phi < 1.0).
4. Complete tide lock when boundary water level reaches or exceeds outfall crown/ground level (phi = 0.0).
5. Upstream backwater propagation: tailwater at outfall throttles upstream conduits and causes upstream surcharge.
6. Multi-timestep dry-to-wet and wet-to-dry behavior with varying boundary levels (e.g. high tide storm -> low tide drain).
7. Strict mass conservation across all boundary conditions (error < 1e-10).
8. Explicit provenance distinction: MODELLED vs SYNTHETIC vs OBSERVED (no claim of real tide data).
9. Real BMC network execution with synthetic coastal boundary condition.
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
    BoundarySourceType,
    DownstreamBoundaryCondition,
    compute_tailwater_submergence_factor,
    propagate_network_timestep,
    propagate_network_series,
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


def test_bmc_outlet_nodes_identified():
    """Verify exact identification of all 43 BMC terminal outlet nodes with surveyed inverts."""
    net = BMCDrainageLoader.load_default_bmc_network()
    assert net is not None

    outlets = [n for n in net.nodes.values() if n.node_type == NodeType.OUTLET]
    assert len(outlets) == 43

    # All 43 have incoming conduits with surveyed downstream invert
    for out in outlets:
        in_chans = [c for c in net.channels.values() if c.downstream_node_id == out.id]
        assert len(in_chans) >= 1
        has_invert = any(c.ds_invert_m is not None for c in in_chans)
        assert has_invert is True
        # Inverts must be within reasonable Mumbai coastal elevation bounds (20m - 32m)
        inv = min(c.ds_invert_m for c in in_chans if c.ds_invert_m is not None)
        assert 20.0 <= inv <= 32.0


def test_free_discharge_low_boundary():
    """Verify free discharge when downstream boundary water level is below outfall invert."""
    # N1 (Inlet) -> C1 -> N2 (Outlet, invert=9.0, ground=12.0)
    nodes = {
        "N1": make_test_node("N1", NodeType.INLET, elevation=11.0, gl=13.0),
        "N2": make_test_node("N2", NodeType.OUTLET, elevation=9.0, gl=12.0),
    }
    channels = {
        "C1": make_test_channel("C1", "N1", "N2", us_inv=10.0, ds_inv=9.0),
    }
    net = DrainageNetwork(nodes=nodes, channels=channels, crs="EPSG:32643")
    caps = {"C1": ChannelCapacity(channel_id="C1", capacity_m3_per_s=0.1, capacity_volume_m3=100.0)}

    # Tailwater submergence factor for H <= 9.0 is 1.0 (free discharge)
    phi = compute_tailwater_submergence_factor("N2", net, boundary_level_m=8.5)
    assert phi == pytest.approx(1.0)

    # Execute propagation
    res = propagate_network_timestep(
        network=net,
        node_external_inflows_m3={"N1": 60.0, "N2": 0.0},
        channel_capacities=caps,
        boundary_level_m=8.5,
    )

    assert res.nodes["N2"].is_outfall is True
    assert res.nodes["N2"].tailwater_submergence_factor == pytest.approx(1.0)
    assert res.nodes["N2"].is_tailwater_limited is False
    assert res.channels["C1"].conveyed_m3 == pytest.approx(60.0)
    assert res.total_outfall_outflow_m3 == pytest.approx(60.0)
    assert res.total_surcharge_volume_m3 == pytest.approx(0.0)
    assert res.mass_balance_error_m3 == pytest.approx(0.0, abs=1e-10)


def test_elevated_downstream_boundary_partial_submergence():
    """Verify that elevated downstream tailwater reduces outfall discharge capacity."""
    # N1 -> C1 (cap=100) -> N2 (Outlet, invert=9.0, ground=12.0, head_max=12.0)
    nodes = {
        "N1": make_test_node("N1", NodeType.INLET, elevation=11.0, gl=13.0),
        "N2": make_test_node("N2", NodeType.OUTLET, elevation=9.0, gl=12.0),
    }
    channels = {
        "C1": make_test_channel("C1", "N1", "N2", us_inv=10.0, ds_inv=9.0),
    }
    net = DrainageNetwork(nodes=nodes, channels=channels, crs="EPSG:32643")
    caps = {"C1": ChannelCapacity(channel_id="C1", capacity_m3_per_s=0.1, capacity_volume_m3=100.0)}

    # Boundary at 11.25m: remaining head = 12.0 - 11.25 = 0.75m. Total head = 12.0 - 9.0 = 3.0m.
    # phi = sqrt(0.75 / 3.0) = sqrt(0.25) = 0.50!
    phi = compute_tailwater_submergence_factor("N2", net, boundary_level_m=11.25)
    assert phi == pytest.approx(0.50)

    # Inflow at N1 is 80.0 m³. With phi=0.5, outfall discharge capacity is 0.5 * 100 = 50.0 m³!
    res = propagate_network_timestep(
        network=net,
        node_external_inflows_m3={"N1": 80.0, "N2": 0.0},
        channel_capacities=caps,
        node_storage_capacities_m3={"N1": 0.0, "N2": 0.0},
        boundary_level_m=11.25,
    )

    assert res.nodes["N2"].is_tailwater_limited is True
    assert res.nodes["N2"].tailwater_submergence_factor == pytest.approx(0.5)

    # Outfall discharge is capped at 50.0 m³
    assert res.total_outfall_outflow_m3 == pytest.approx(50.0)
    # C1 conveyance was throttled by downstream outfall limit to 50.0 m³
    assert res.channels["C1"].conveyed_m3 == pytest.approx(50.0)
    assert res.channels["C1"].is_downstream_throttled is True

    # Remaining 30.0 m³ surcharges upstream at N1!
    assert res.nodes["N1"].surcharge_volume_m3 == pytest.approx(30.0)
    assert res.total_surcharge_volume_m3 == pytest.approx(30.0)
    # Mass conservation: Inflow (80) == Outflow (50) + Surcharge (30)
    assert res.mass_balance_error_m3 == pytest.approx(0.0, abs=1e-10)


def test_complete_tide_lock_zero_outfall_discharge():
    """Verify complete tide lock when boundary head is at or above outfall ground level."""
    # N1 -> C1 (cap=100) -> N2 (Outlet, invert=9.0, ground=12.0)
    nodes = {
        "N1": make_test_node("N1", NodeType.INLET, elevation=11.0, gl=13.0),
        "N2": make_test_node("N2", NodeType.OUTLET, elevation=9.0, gl=12.0),
    }
    channels = {
        "C1": make_test_channel("C1", "N1", "N2", us_inv=10.0, ds_inv=9.0),
    }
    net = DrainageNetwork(nodes=nodes, channels=channels, crs="EPSG:32643")
    caps = {"C1": ChannelCapacity(channel_id="C1", capacity_m3_per_s=0.1, capacity_volume_m3=100.0)}

    # Boundary at 12.5m >= 12.0m ground level -> phi = 0.0 (tide locked!)
    phi = compute_tailwater_submergence_factor("N2", net, boundary_level_m=12.5)
    assert phi == pytest.approx(0.0)

    res = propagate_network_timestep(
        network=net,
        node_external_inflows_m3={"N1": 60.0, "N2": 0.0},
        channel_capacities=caps,
        node_storage_capacities_m3={"N1": 0.0, "N2": 0.0},
        boundary_level_m=12.5,
    )

    # Zero discharge out to sea
    assert res.total_outfall_outflow_m3 == pytest.approx(0.0)
    assert res.channels["C1"].conveyed_m3 == pytest.approx(0.0)
    assert res.channels["C1"].is_downstream_throttled is True

    # Entire 60.0 m³ surcharges upstream at N1
    assert res.nodes["N1"].surcharge_volume_m3 == pytest.approx(60.0)
    assert res.total_surcharge_volume_m3 == pytest.approx(60.0)
    assert res.mass_balance_error_m3 == pytest.approx(0.0, abs=1e-10)


def test_backwater_propagation_through_multi_segment_network():
    """Verify tailwater backpressure propagates upstream across a multi-segment drainage network."""
    # N1 -> C1 (100) -> N2 -> C2 (100) -> N3 (Outlet, invert=9.0, ground=12.0)
    nodes = {
        "N1": make_test_node("N1", NodeType.INLET, elevation=12.0, gl=14.0),
        "N2": make_test_node("N2", NodeType.JUNCTION, elevation=10.5, gl=13.0),
        "N3": make_test_node("N3", NodeType.OUTLET, elevation=9.0, gl=12.0),
    }
    channels = {
        "C1": make_test_channel("C1", "N1", "N2", us_inv=11.5, ds_inv=10.5),
        "C2": make_test_channel("C2", "N2", "N3", us_inv=10.5, ds_inv=9.0),
    }
    net = DrainageNetwork(nodes=nodes, channels=channels, crs="EPSG:32643")
    caps = {
        "C1": ChannelCapacity(channel_id="C1", capacity_m3_per_s=0.1, capacity_volume_m3=100.0),
        "C2": ChannelCapacity(channel_id="C2", capacity_m3_per_s=0.1, capacity_volume_m3=100.0),
    }

    # Boundary head causes 75% throttling (phi = 0.25) at N3
    # With head_max=12.0, invert=9.0: phi = 0.25 -> phi^2 = 0.0625 -> head = 12.0 - 0.0625*3 = 11.8125
    b_level = 12.0 - (0.25 ** 2) * 3.0
    phi = compute_tailwater_submergence_factor("N3", net, boundary_level_m=b_level)
    assert phi == pytest.approx(0.25)

    res = propagate_network_timestep(
        network=net,
        node_external_inflows_m3={"N1": 80.0, "N2": 0.0, "N3": 0.0},
        channel_capacities=caps,
        node_storage_capacities_m3={"N1": 0.0, "N2": 0.0, "N3": 0.0},
        boundary_level_m=b_level,
    )

    # N3 outfall capacity = 0.25 * 100 = 25.0 m³
    assert res.total_outfall_outflow_m3 == pytest.approx(25.0)

    # Both C2 and C1 effective capacities throttled to 25.0 m³
    assert res.channels["C2"].effective_capacity_m3 == pytest.approx(25.0)
    assert res.channels["C1"].effective_capacity_m3 == pytest.approx(25.0)
    assert res.channels["C2"].is_downstream_throttled is True
    assert res.channels["C1"].is_downstream_throttled is True

    # 55.0 m³ (80 - 25) surcharges upstream at N1
    assert res.nodes["N1"].surcharge_volume_m3 == pytest.approx(55.0)
    assert res.total_surcharge_volume_m3 == pytest.approx(55.0)
    assert res.mass_balance_error_m3 == pytest.approx(0.0, abs=1e-10)


def test_dry_to_wet_and_wet_to_dry_with_time_varying_boundary():
    """Verify multi-timestep simulation: high tide storm (tide lock) followed by low tide ebb (storage drainage)."""
    # N1 -> C1 (cap=100) -> N2 (storage=20) -> C2 (cap=40) -> N3 (Outlet, invert=9.0, ground=12.0)
    nodes = {
        "N1": make_test_node("N1", NodeType.INLET, elevation=12.0),
        "N2": make_test_node("N2", NodeType.JUNCTION, elevation=10.5),
        "N3": make_test_node("N3", NodeType.OUTLET, elevation=9.0, gl=12.0),
    }
    channels = {
        "C1": make_test_channel("C1", "N1", "N2", us_inv=11.5, ds_inv=10.5),
        "C2": make_test_channel("C2", "N2", "N3", us_inv=10.5, ds_inv=9.0),
    }
    net = DrainageNetwork(nodes=nodes, channels=channels, crs="EPSG:32643")
    caps = {
        "C1": ChannelCapacity(channel_id="C1", capacity_m3_per_s=0.1, capacity_volume_m3=100.0),
        "C2": ChannelCapacity(channel_id="C2", capacity_m3_per_s=0.04, capacity_volume_m3=40.0),
    }

    # 4-hour cycle:
    # Hour 0: Dry, Low Tide (H=8.0m) -> zero flow
    # Hour 1: Storm Inflow (50m³), High Tide Lock (H=12.5m) -> outfall locked (0 discharge), N2 stores 20m³, N1 surcharges 30m³
    # Hour 2: Rain Stops (0m³), Low Tide Ebb (H=8.0m) -> N2 drains 20m³ stored water out to outfall!
    # Hour 3: Dry, Low Tide (H=8.0m) -> 0 flow, system empty
    series_inflows = [
        {"N1": 0.0, "N2": 0.0, "N3": 0.0},
        {"N1": 50.0, "N2": 0.0, "N3": 0.0},
        {"N1": 0.0, "N2": 0.0, "N3": 0.0},
        {"N1": 0.0, "N2": 0.0, "N3": 0.0},
    ]
    tide_series = [8.0, 12.5, 8.0, 8.0]

    b_cond = DownstreamBoundaryCondition(
        boundary_type=BoundarySourceType.SYNTHETIC,
        time_series_levels_m=tide_series,
        description="Synthetic diurnal high-tide surge and ebb test series"
    )

    results = propagate_network_series(
        network=net,
        series_external_inflows_m3=series_inflows,
        channel_capacities=caps,
        node_storage_capacities_m3={"N1": 0.0, "N2": 20.0, "N3": 0.0},
        boundary_condition=b_cond,
    )

    assert len(results) == 4

    # Step 0: Dry, nothing happening
    assert results[0].total_outfall_outflow_m3 == 0.0
    assert results[0].total_final_storage_m3 == 0.0

    # Step 1: High tide lock -> 0 outfall discharge!
    assert results[1].total_outfall_outflow_m3 == 0.0
    assert results[1].total_final_storage_m3 == pytest.approx(20.0)  # stored in N2
    assert results[1].total_surcharge_volume_m3 == pytest.approx(30.0)  # surcharged at N1
    assert results[1].mass_balance_error_m3 == pytest.approx(0.0, abs=1e-10)

    # Step 2: Ebb tide (low water) -> stored 20.0 m³ drains out through N3!
    assert results[2].total_initial_storage_m3 == pytest.approx(20.0)
    assert results[2].total_outfall_outflow_m3 == pytest.approx(20.0)
    assert results[2].total_final_storage_m3 == pytest.approx(0.0)
    assert results[2].total_surcharge_volume_m3 == pytest.approx(0.0)
    assert results[2].mass_balance_error_m3 == pytest.approx(0.0, abs=1e-10)

    # Step 3: Completely drained
    assert results[3].total_outfall_outflow_m3 == 0.0
    assert results[3].total_final_storage_m3 == 0.0

    # Cumulative Mass Conservation:
    total_in = sum(r.total_external_inflow_m3 for r in results)
    total_out = sum(r.total_outfall_outflow_m3 for r in results)
    total_sur = sum(r.total_surcharge_volume_m3 for r in results)
    assert total_in == pytest.approx(50.0)
    assert total_out + total_sur == pytest.approx(50.0)


def test_boundary_source_provenance_labels():
    """Verify clear distinction of boundary types: MODELLED, SYNTHETIC, OBSERVED."""
    # Ensure BoundarySourceType enum values
    assert BoundarySourceType.MODELLED.value == "MODELLED"
    assert BoundarySourceType.SYNTHETIC.value == "SYNTHETIC"
    assert BoundarySourceType.OBSERVED.value == "OBSERVED"

    cond_synth = DownstreamBoundaryCondition(
        boundary_type=BoundarySourceType.SYNTHETIC,
        fixed_level_m=11.5,
        description="Synthetic tidal test"
    )
    assert cond_synth.boundary_type == BoundarySourceType.SYNTHETIC

    # Verify disclaimer mentions absence of real tide claims
    net = BMCDrainageLoader.load_default_bmc_network()
    res = propagate_network_timestep(
        network=net,
        node_external_inflows_m3={},
        boundary_condition=cond_synth,
    )
    assert "does not claim real tide observations" in res.disclaimer
    assert res.boundary_type == "SYNTHETIC"
    assert res.boundary_level_m == 11.5


def test_real_bmc_network_with_synthetic_boundary():
    """Verify propagation on the full BMC network with 43 outlets under synthetic elevated coastal boundary."""
    net = BMCDrainageLoader.load_default_bmc_network()
    assert net is not None
    assert len(net.channels) == 1240
    assert len(net.nodes) == 1264

    # 43 outlets have inverts between 23.0m and 29.2m. Set a synthetic boundary of 26.5m.
    # Outlets with invert > 26.5m discharge freely; outlets with invert < 26.5m experience tailwater throttling.
    inlet_nodes = [nid for nid, n in net.nodes.items() if n.node_type == NodeType.INLET]
    inflows = {nid: 40.0 for nid in inlet_nodes}
    total_inflow = 78 * 40.0

    b_cond = DownstreamBoundaryCondition(
        boundary_type=BoundarySourceType.SYNTHETIC,
        fixed_level_m=26.5,
        description="Synthetic coastal tailwater elevation across Mumbai pilot outlets"
    )

    res = propagate_network_timestep(
        network=net,
        node_external_inflows_m3=inflows,
        boundary_condition=b_cond,
    )

    # Verify all 43 outlets are flagged
    outlet_states = [ns for ns in res.nodes.values() if ns.is_outfall]
    assert len(outlet_states) == 43

    # Some outlets with invert < 26.5m are tailwater limited
    limited_outlets = [ns for ns in outlet_states if ns.is_tailwater_limited]
    assert len(limited_outlets) > 0

    # Total mass conservation verified across the full real BMC pilot network
    total_out = res.total_outfall_outflow_m3 + res.total_final_storage_m3 + res.total_surcharge_volume_m3
    assert total_out == pytest.approx(total_inflow, rel=1e-6)
    assert res.mass_balance_error_m3 == pytest.approx(0.0, abs=1e-5)


def test_strict_mass_conservation_under_all_boundary_conditions():
    """Verify mass conservation error is mathematically zero (<= 1e-10) across diverse boundary heads."""
    nodes = {
        "N1": make_test_node("N1", NodeType.INLET, elevation=12.0),
        "N2": make_test_node("N2", NodeType.JUNCTION, elevation=10.5),
        "N3": make_test_node("N3", NodeType.OUTLET, elevation=9.0, gl=12.0),
    }
    channels = {
        "C1": make_test_channel("C1", "N1", "N2", us_inv=11.5, ds_inv=10.5),
        "C2": make_test_channel("C2", "N2", "N3", us_inv=10.5, ds_inv=9.0),
    }
    net = DrainageNetwork(nodes=nodes, channels=channels, crs="EPSG:32643")
    caps = {
        "C1": ChannelCapacity(channel_id="C1", capacity_m3_per_s=0.1, capacity_volume_m3=100.0),
        "C2": ChannelCapacity(channel_id="C2", capacity_m3_per_s=0.04, capacity_volume_m3=40.0),
    }

    # Test across a sweep of boundary levels: below invert, halfway, at crown, above ground
    for test_head in [7.0, 9.0, 10.0, 11.5, 12.0, 15.0]:
        res = propagate_network_timestep(
            network=net,
            node_external_inflows_m3={"N1": 65.0, "N2": 15.0},
            channel_capacities=caps,
            node_storage_capacities_m3={"N1": 10.0, "N2": 15.0, "N3": 5.0},
            boundary_level_m=test_head,
        )
        assert res.mass_balance_error_m3 == pytest.approx(0.0, abs=1e-10)
        tot_in = res.total_external_inflow_m3 + res.total_initial_storage_m3
        tot_out = res.total_outfall_outflow_m3 + res.total_final_storage_m3 + res.total_surcharge_volume_m3
        assert tot_in == pytest.approx(tot_out, abs=1e-10)

