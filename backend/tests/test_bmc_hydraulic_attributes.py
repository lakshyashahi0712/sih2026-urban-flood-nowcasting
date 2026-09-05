"""Unit tests for Phase 2.1A — Complete ALL BMC Cross-Section Handling.

Verifies:
1. Every BMC drain (1,240) and manhole (1,241 surveyed / 1,264 total nodes) remains present in the network.
2. BMC RECT channel hydraulic geometry calculation (Area = W * H, P = W + 2H, R = A / P).
3. BMC OREC channel hydraulic geometry calculation using actual BMC dimensions (Area = W * H, P = W + 2H, R = A / P).
4. BMC CIRC channel hydraulic geometry calculation (Area = pi * D^2 / 4, P = pi * D, R = D / 4).
5. Unsupported shapes or missing dimensions on BMC channels are marked UNAVAILABLE with zero capacity
   rather than fabricating arbitrary 0.45 x 0.25 m dimensions.
6. Longitudinal slope calculation from (US_INVERT - DS_INVERT) / length_m.
7. Flat slope (S = 0) explicit zero capacity handling without slope fabrication.
8. Adverse slope (S < 0) explicit zero capacity handling with strict US_NODE_ID -> DS_NODE_ID preservation (never reversed).
9. Missing attributes handling (safe fallback for DEM-derived, UNAVAILABLE for BMC).
10. Manning's n roughness is explicitly recorded as ASSUMED.
11. Full pilot dataset verification: exact counts for RECT, CIRC, OREC, other, supported, and unsupported.
"""
from __future__ import annotations

import math
import pytest

from backend.app.domain.drainage.models import (
    DrainageChannel,
    DrainageNode,
    Provenance,
    NodeType,
    SlopeStatus,
    HydraulicAttributeSource,
)
from backend.app.domain.drainage.capacity import (
    ChannelHydraulicParameters,
    ChannelCapacity,
    compute_channel_capacity,
    compute_channel_excess,
)
from backend.app.infrastructure.drainage.bmc_gis import BMCDrainageLoader


def test_all_bmc_drains_and_manholes_preserved():
    """Verify that all 1,240 BMC drains and 1,241 manholes remain present in the network without any removal."""
    net = BMCDrainageLoader.load_default_bmc_network()
    assert net is not None
    assert len(net.channels) == 1240, f"Expected 1,240 drains, got {len(net.channels)}"
    # 1,241 surveyed manholes + 23 virtual junction nodes = 1,264 nodes
    assert len(net.nodes) >= 1241, f"Expected at least 1,241 nodes, got {len(net.nodes)}"
    assert len(net.nodes) == 1264

    # Verify channels maintain original BMC IDs and node references
    for cid, channel in net.channels.items():
        assert cid.startswith("bmc_drain_")
        assert channel.upstream_node_id in net.nodes
        assert channel.downstream_node_id in net.nodes
        assert channel.provenance == Provenance.BMC


def test_rect_hydraulic_geometry_calculation():
    """Verify rectangular box channel geometry: Area = W * H, P = W + 2H, R = A / P."""
    channel = DrainageChannel(
        id="chan_rect_test",
        upstream_node_id="node_us",
        downstream_node_id="node_ds",
        length_m=100.0,
        provenance=Provenance.BMC,
        shape="RECT",
        conduit_width_mm=3000.0,   # 3.0 m
        conduit_height_mm=2000.0,  # 2.0 m
        us_invert_m=15.0,
        ds_invert_m=14.0,          # S = (15 - 14)/100 = 0.01
    )

    area, perim, radius, is_supported = channel.compute_hydraulic_geometry()
    assert is_supported is True
    assert area == pytest.approx(6.0)
    assert perim == pytest.approx(7.0)
    assert radius == pytest.approx(6.0 / 7.0)

    cap = compute_channel_capacity(channel)
    assert cap.shape == "RECT"
    assert cap.area_m2 == pytest.approx(6.0)
    assert cap.wetted_perimeter_m == pytest.approx(7.0)
    assert cap.hydraulic_radius_m == pytest.approx(6.0 / 7.0)
    assert cap.geometry_source == HydraulicAttributeSource.BMC_AUTHORITATIVE.value
    assert cap.slope == pytest.approx(0.01)
    assert cap.slope_source == HydraulicAttributeSource.BMC_AUTHORITATIVE.value
    assert cap.slope_status == SlopeStatus.POSITIVE.value
    assert cap.roughness_source == HydraulicAttributeSource.ASSUMED.value

    expected_q = (1.0 / 0.018) * 6.0 * ((6.0 / 7.0) ** (2.0 / 3.0)) * (0.01 ** 0.5)
    assert cap.capacity_m3_per_s == pytest.approx(expected_q, rel=1e-3)
    assert cap.capacity_volume_m3 == pytest.approx(expected_q * 3600.0, rel=1e-3)


def test_orec_hydraulic_geometry_calculation():
    """Verify open rectangular (OREC) channel geometry using actual BMC dimensions: Area = W * H, P = W + 2H, R = A / P."""
    channel = DrainageChannel(
        id="chan_orec_test",
        upstream_node_id="node_us",
        downstream_node_id="node_ds",
        length_m=80.0,
        provenance=Provenance.BMC,
        shape="OREC",
        conduit_width_mm=4000.0,   # 4.0 m
        conduit_height_mm=2500.0,  # 2.5 m
        us_invert_m=20.0,
        ds_invert_m=19.2,          # S = (20.0 - 19.2)/80 = 0.01
    )

    area, perim, radius, is_supported = channel.compute_hydraulic_geometry()
    assert is_supported is True
    assert area == pytest.approx(10.0)
    assert perim == pytest.approx(4.0 + 2 * 2.5)  # 9.0 m
    assert radius == pytest.approx(10.0 / 9.0)

    cap = compute_channel_capacity(channel)
    assert cap.shape == "OREC"
    assert cap.area_m2 == pytest.approx(10.0)
    assert cap.wetted_perimeter_m == pytest.approx(9.0)
    assert cap.hydraulic_radius_m == pytest.approx(10.0 / 9.0)
    assert cap.geometry_source == HydraulicAttributeSource.BMC_AUTHORITATIVE.value
    assert cap.slope == pytest.approx(0.01)
    assert cap.slope_source == HydraulicAttributeSource.BMC_AUTHORITATIVE.value
    assert cap.slope_status == SlopeStatus.POSITIVE.value
    assert cap.capacity_m3_per_s > 0

    expected_q = (1.0 / 0.018) * 10.0 * ((10.0 / 9.0) ** (2.0 / 3.0)) * (0.01 ** 0.5)
    assert cap.capacity_m3_per_s == pytest.approx(expected_q, rel=1e-3)


def test_circ_hydraulic_geometry_calculation():
    """Verify circular pipe geometry: Area = pi*D^2/4, P = pi*D, R = D / 4."""
    diameter_mm = 1200.0  # 1.2 m diameter
    channel = DrainageChannel(
        id="chan_circ_test",
        upstream_node_id="node_us",
        downstream_node_id="node_ds",
        length_m=50.0,
        provenance=Provenance.BMC,
        shape="CIRC",
        conduit_width_mm=diameter_mm,
        conduit_height_mm=None,
        us_invert_m=10.5,
        ds_invert_m=10.0,        # S = (10.5 - 10.0)/50 = 0.01
    )

    area, perim, radius, is_supported = channel.compute_hydraulic_geometry()
    assert is_supported is True
    d = 1.2
    assert area == pytest.approx(math.pi * (d ** 2) / 4.0)
    assert perim == pytest.approx(math.pi * d)
    assert radius == pytest.approx(d / 4.0)

    cap = compute_channel_capacity(channel)
    assert cap.shape == "CIRC"
    assert cap.area_m2 == pytest.approx(math.pi * (d ** 2) / 4.0)
    assert cap.wetted_perimeter_m == pytest.approx(math.pi * d)
    assert cap.hydraulic_radius_m == pytest.approx(d / 4.0)
    assert cap.geometry_source == HydraulicAttributeSource.BMC_AUTHORITATIVE.value
    assert cap.slope == pytest.approx(0.01)
    assert cap.slope_source == HydraulicAttributeSource.BMC_AUTHORITATIVE.value
    assert cap.slope_status == SlopeStatus.POSITIVE.value
    assert cap.capacity_m3_per_s > 0


def test_unsupported_shapes_and_missing_dims_marked_unavailable():
    """Do NOT replace unsupported shapes or missing dimensions with arbitrary 0.45 x 0.25 m geometry;
    mark their capacity as explicitly UNAVAILABLE."""
    # Case 1: Unsupported shape (e.g. TRAP) on BMC channel
    chan_trap = DrainageChannel(
        id="chan_trap_test",
        upstream_node_id="u",
        downstream_node_id="d",
        length_m=50.0,
        provenance=Provenance.BMC,
        shape="TRAP",
        conduit_width_mm=2000.0,
        conduit_height_mm=1500.0,
        us_invert_m=12.0,
        ds_invert_m=11.5,
    )
    area, perim, rad, is_supp = chan_trap.compute_hydraulic_geometry()
    assert is_supp is False
    assert area is None

    cap_trap = compute_channel_capacity(chan_trap)
    assert cap_trap.geometry_source == HydraulicAttributeSource.UNAVAILABLE.value
    assert cap_trap.area_m2 == 0.0
    assert cap_trap.capacity_m3_per_s == 0.0
    assert cap_trap.capacity_volume_m3 == 0.0

    # Case 2: OREC with missing height
    chan_orec_missing = DrainageChannel(
        id="chan_orec_missing",
        upstream_node_id="u",
        downstream_node_id="d",
        length_m=50.0,
        provenance=Provenance.BMC,
        shape="OREC",
        conduit_width_mm=2000.0,
        conduit_height_mm=None,  # Missing height
        us_invert_m=12.0,
        ds_invert_m=11.5,
    )
    area2, perim2, rad2, is_supp2 = chan_orec_missing.compute_hydraulic_geometry()
    assert is_supp2 is False

    cap_orec_missing = compute_channel_capacity(chan_orec_missing)
    assert cap_orec_missing.geometry_source == HydraulicAttributeSource.UNAVAILABLE.value
    assert cap_orec_missing.capacity_m3_per_s == 0.0

    # Case 3: OREC with non-positive dimension (e.g. 0 mm)
    chan_orec_zero = DrainageChannel(
        id="chan_orec_zero",
        upstream_node_id="u",
        downstream_node_id="d",
        length_m=50.0,
        provenance=Provenance.BMC,
        shape="OREC",
        conduit_width_mm=0.0,
        conduit_height_mm=1000.0,
        us_invert_m=12.0,
        ds_invert_m=11.5,
    )
    area3, perim3, rad3, is_supp3 = chan_orec_zero.compute_hydraulic_geometry()
    assert is_supp3 is False

    cap_orec_zero = compute_channel_capacity(chan_orec_zero)
    assert cap_orec_zero.geometry_source == HydraulicAttributeSource.UNAVAILABLE.value
    assert cap_orec_zero.capacity_m3_per_s == 0.0


def test_invert_derived_slope_calculation():
    """Verify longitudinal slope computed from (US_INVERT - DS_INVERT) / conduit_length."""
    channel = DrainageChannel(
        id="chan_slope_test",
        upstream_node_id="node_us",
        downstream_node_id="node_ds",
        length_m=80.0,
        provenance=Provenance.BMC,
        shape="RECT",
        conduit_width_mm=2000.0,
        conduit_height_mm=1500.0,
        us_invert_m=28.45,
        ds_invert_m=28.05,
    )

    expected_slope = (28.45 - 28.05) / 80.0  # 0.40 / 80 = 0.005
    assert channel.compute_longitudinal_slope() == pytest.approx(expected_slope)
    assert channel.get_slope_status() == SlopeStatus.POSITIVE

    cap = compute_channel_capacity(channel)
    assert cap.slope == pytest.approx(expected_slope)
    assert cap.slope_source == HydraulicAttributeSource.BMC_AUTHORITATIVE.value
    assert cap.slope_status == SlopeStatus.POSITIVE.value
    assert cap.capacity_m3_per_s > 0


def test_flat_slope_explicit_zero_capacity():
    """Flat slope (S = 0) must produce 0 capacity explicitly without fabricating physical slope."""
    channel = DrainageChannel(
        id="chan_flat_test",
        upstream_node_id="node_us",
        downstream_node_id="node_ds",
        length_m=60.0,
        provenance=Provenance.BMC,
        shape="OREC",
        conduit_width_mm=2000.0,
        conduit_height_mm=1500.0,
        us_invert_m=25.0,
        ds_invert_m=25.0,  # S = 0.0
    )

    assert channel.compute_longitudinal_slope() == pytest.approx(0.0)
    assert channel.get_slope_status() == SlopeStatus.FLAT

    cap = compute_channel_capacity(channel)
    assert cap.slope == pytest.approx(0.0)
    assert cap.slope_status == SlopeStatus.FLAT.value
    assert cap.slope_source == HydraulicAttributeSource.BMC_AUTHORITATIVE.value
    assert cap.capacity_m3_per_s == 0.0
    assert cap.capacity_volume_m3 == 0.0


def test_adverse_slope_explicit_zero_capacity_never_reverses_direction():
    """Adverse slope (S < 0) must produce 0 capacity and NEVER reverse authoritative US -> DS direction."""
    channel = DrainageChannel(
        id="chan_adverse_test",
        upstream_node_id="node_us_high_ground",
        downstream_node_id="node_ds_low_ground",
        length_m=50.0,
        provenance=Provenance.BMC,
        shape="OREC",
        conduit_width_mm=15000.0,
        conduit_height_mm=3778.0,
        us_invert_m=24.0,
        ds_invert_m=25.5,  # Invert slopes uphill: (24.0 - 25.5) / 50 = -0.03
    )

    assert channel.upstream_node_id == "node_us_high_ground"
    assert channel.downstream_node_id == "node_ds_low_ground"

    slope = channel.compute_longitudinal_slope()
    assert slope == pytest.approx(-0.03)
    assert channel.get_slope_status() == SlopeStatus.ADVERSE

    cap = compute_channel_capacity(channel)
    assert cap.channel_id == "chan_adverse_test"
    assert cap.slope == pytest.approx(-0.03)
    assert cap.slope_status == SlopeStatus.ADVERSE.value
    assert cap.slope_source == HydraulicAttributeSource.BMC_AUTHORITATIVE.value
    assert cap.capacity_m3_per_s == 0.0
    assert cap.capacity_volume_m3 == 0.0


def test_missing_inverts_on_bmc_channel_marked_unavailable():
    """BMC channels with missing inverts must have slope marked UNAVAILABLE with 0 capacity."""
    chan_no_inverts = DrainageChannel(
        id="chan_no_inverts",
        upstream_node_id="u",
        downstream_node_id="d",
        length_m=40.0,
        provenance=Provenance.BMC,
        shape="OREC",
        conduit_width_mm=2000.0,
        conduit_height_mm=1500.0,
        us_invert_m=None,
        ds_invert_m=None,
    )
    assert chan_no_inverts.compute_longitudinal_slope() is None
    assert chan_no_inverts.get_slope_status() == SlopeStatus.MISSING

    cap = compute_channel_capacity(chan_no_inverts)
    assert cap.geometry_source == HydraulicAttributeSource.BMC_AUTHORITATIVE.value
    assert cap.slope_source == HydraulicAttributeSource.UNAVAILABLE.value
    assert cap.capacity_m3_per_s == 0.0


def test_manning_roughness_provenance_is_always_assumed():
    """Manning's n must always be recorded as ASSUMED prototype roughness."""
    channel = DrainageChannel(
        id="ch_manning",
        upstream_node_id="u",
        downstream_node_id="d",
        length_m=50.0,
        provenance=Provenance.BMC,
        shape="OREC",
        conduit_width_mm=3000.0,
        conduit_height_mm=2000.0,
        us_invert_m=12.0,
        ds_invert_m=11.5,
    )

    cap = compute_channel_capacity(channel)
    assert cap.roughness_source == HydraulicAttributeSource.ASSUMED.value


def test_bmc_cross_section_counts_and_hydraulic_support():
    """Verify exact counts of RECT, CIRC, OREC, other shapes, and hydraulic support status on real BMC pilot dataset."""
    net = BMCDrainageLoader.load_default_bmc_network()
    assert net is not None
    assert len(net.channels) == 1240

    rect_count = sum(1 for c in net.channels.values() if c.shape == "RECT")
    circ_count = sum(1 for c in net.channels.values() if c.shape == "CIRC")
    orec_count = sum(1 for c in net.channels.values() if c.shape == "OREC")
    other_count = sum(1 for c in net.channels.values() if c.shape not in ("RECT", "CIRC", "OREC"))

    assert rect_count == 424
    assert circ_count == 12
    assert orec_count == 804
    assert other_count == 0

    supported_count = 0
    unsupported_count = 0
    positive_slopes = 0
    flat_slopes = 0
    adverse_slopes = 0

    for cid, chan in net.channels.items():
        area, perim, rad, is_supp = chan.compute_hydraulic_geometry()
        if is_supp:
            supported_count += 1
        else:
            unsupported_count += 1

        status = chan.get_slope_status()
        if status == SlopeStatus.POSITIVE:
            positive_slopes += 1
        elif status == SlopeStatus.FLAT:
            flat_slopes += 1
        elif status == SlopeStatus.ADVERSE:
            adverse_slopes += 1

    # In Phase 2.1A: ALL 1,240 channels have valid RECT, CIRC, or OREC geometry
    assert supported_count == 1240
    assert unsupported_count == 0
    assert positive_slopes == 1223
    assert flat_slopes == 15
    assert adverse_slopes == 2

    # Verify both known adverse channels
    assert net.channels["bmc_drain_28238"].get_slope_status() == SlopeStatus.ADVERSE
    assert net.channels["bmc_drain_28239"].get_slope_status() == SlopeStatus.ADVERSE
