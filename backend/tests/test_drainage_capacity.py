"""Tests for the drainage capacity model (Phase 0.9)."""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.domain.drainage.capacity import (
    ChannelHydraulicParameters,
    ChannelCapacity,
    compute_channel_capacity,
    compute_channel_excess
)
from app.domain.drainage.models import DrainageChannel, DrainageNode, Provenance, NodeType


def make_test_channel(upstream_id: str, downstream_id: str, length_m: float = 100.0) -> DrainageChannel:
    """Create a minimal DrainageChannel for testing."""
    return DrainageChannel(
        id=f"ch_{upstream_id}_{downstream_id}",
        upstream_node_id=upstream_id,
        downstream_node_id=downstream_id,
        length_m=length_m,
        provenance=Provenance.DEM_DERIVED
    )


def test_known_manning_capacity_calculation():
    """Test a known Manning's equation calculation."""
    # Create a test channel
    channel = make_test_channel("n_0_0", "n_0_1", 50.0)

    # Hydraulic parameters: rectangular channel 2m wide, 1m deep, n=0.015, slope 0.001
    params = ChannelHydraulicParameters(
        width_m=2.0,
        depth_m=1.0,
        manning_n=0.015,
        slope_m_per_m=0.001
    )

    # Manual calculation:
    # A = width * depth = 2.0 * 1.0 = 2.0 m²
    # P = width + 2*depth = 2.0 + 2*1.0 = 4.0 m
    # R = A/P = 2.0/4.0 = 0.5 m
    # Q = (1/n) * A * R^(2/3) * S^(1/2)
    #   = (1/0.015) * 2.0 * (0.5)^(2/3) * (0.001)^(1/2)
    #   = 66.6667 * 2.0 * 0.62996 * 0.03162
    #   ≈ 2.656 m³/s

    capacity = compute_channel_capacity(channel, params, timestep_hours=1.0)

    # Check that capacity is positive and reasonable
    assert capacity.capacity_m3_per_s > 0
    assert abs(capacity.capacity_m3_per_s - 2.656) < 0.01  # Within 0.01 m³/s
    assert capacity.capacity_volume_m3 == capacity.capacity_m3_per_s * 3600.0
    assert capacity.channel_id == channel.id
    assert capacity.hydraulic_params == params
    assert capacity.provenance == Provenance.DEM_DERIVED


def test_zero_inflow_zero_surcharge():
    """Zero inflow should produce zero excess."""
    channel = make_test_channel("n_0_0", "n_0_1")
    params = ChannelHydraulicParameters(width_m=1.0, depth_m=0.5, manning_n=0.013, slope_m_per_m=0.0005)
    capacity = compute_channel_capacity(channel, params, timestep_hours=1.0)

    excess = compute_channel_excess(0.0, capacity)
    assert excess == 0.0


def test_inflow_below_capacity_zero_excess():
    """Inflow below capacity should produce zero excess."""
    channel = make_test_channel("n_0_0", "n_0_1")
    params = ChannelHydraulicParameters(width_m=3.0, depth_m=1.0, manning_n=0.02, slope_m_per_m=0.001)
    capacity = compute_channel_capacity(channel, params, timestep_hours=1.0)

    # Inflow at 90% of capacity
    inflow = capacity.capacity_volume_m3 * 0.9
    excess = compute_channel_excess(inflow, capacity)
    assert excess == 0.0


def test_inflow_above_capacity_positive_excess():
    """Inflow above capacity should produce positive excess."""
    channel = make_test_channel("n_0_0", "n_0_1")
    params = ChannelHydraulicParameters(width_m=2.0, depth_m=0.8, manning_n=0.014, slope_m_per_m=0.0008)
    capacity = compute_channel_capacity(channel, params, timestep_hours=1.0)

    # Inflow at 110% of capacity
    inflow = capacity.capacity_volume_m3 * 1.1
    excess = compute_channel_excess(inflow, capacity)
    expected = inflow - capacity.capacity_volume_m3
    assert excess == expected
    assert excess > 0.0


def test_exact_capacity_boundary_zero_excess():
    """Inflow exactly at capacity should produce zero excess."""
    channel = make_test_channel("n_0_0", "n_0_1")
    params = ChannelHydraulicParameters(width_m=1.5, depth_m=0.6, manning_n=0.012, slope_m_per_m=0.0007)
    capacity = compute_channel_capacity(channel, params, timestep_hours=1.0)

    excess = compute_channel_excess(capacity.capacity_volume_m3, capacity)
    assert excess == 0.0


def test_invalid_hydraulic_parameters_rejected():
    """Invalid hydraulic parameters should be rejected."""
    # Non-positive width
    with pytest.raises(ValidationError):
        ChannelHydraulicParameters(width_m=0.0, depth_m=1.0, manning_n=0.013, slope_m_per_m=0.0005)

    # Non-positive depth
    with pytest.raises(ValidationError):
        ChannelHydraulicParameters(width_m=2.0, depth_m=0.0, manning_n=0.013, slope_m_per_m=0.0005)

    # Non-positive Manning's n
    with pytest.raises(ValidationError):
        ChannelHydraulicParameters(width_m=2.0, depth_m=1.0, manning_n=0.0, slope_m_per_m=0.0005)

    # Non-positive slope
    with pytest.raises(ValidationError):
        ChannelHydraulicParameters(width_m=2.0, depth_m=1.0, manning_n=0.013, slope_m_per_m=0.0)

    # Negative values
    with pytest.raises(ValidationError):
        ChannelHydraulicParameters(width_m=-1.0, depth_m=1.0, manning_n=0.013, slope_m_per_m=0.0005)


def test_deterministic_results():
    """Same inputs should produce same outputs."""
    channel = make_test_channel("n_0_0", "n_0_1")
    params = ChannelHydraulicParameters(width_m=2.5, depth_m=1.2, manning_n=0.016, slope_m_per_m=0.0009)

    cap1 = compute_channel_capacity(channel, params, timestep_hours=2.0)
    cap2 = compute_channel_capacity(channel, params, timestep_hours=2.0)

    assert cap1.capacity_m3_per_s == cap2.capacity_m3_per_s
    assert cap1.capacity_volume_m3 == cap2.capacity_volume_m3
    assert cap1.hydraulic_params == cap2.hydraulic_params


def test_multiple_channels_handled_independently():
    """Each channel's capacity should be computed independently."""
    channel1 = make_test_channel("n_0_0", "n_0_1", 30.0)
    channel2 = make_test_channel("n_0_1", "n_0_2", 45.0)

    # Different parameters for each channel
    params1 = ChannelHydraulicParameters(width_m=2.0, depth_m=0.8, manning_n=0.014, slope_m_per_m=0.0005)
    params2 = ChannelHydraulicParameters(width_m=1.5, depth_m=0.6, manning_n=0.012, slope_m_per_m=0.0008)

    cap1 = compute_channel_capacity(channel1, params1, timestep_hours=1.0)
    cap2 = compute_channel_capacity(channel2, params2, timestep_hours=1.0)

    # Capacities should differ based on parameters and lengths
    assert cap1.channel_id == channel1.id
    assert cap2.channel_id == channel2.id
    assert cap1.capacity_m3_per_s != cap2.capacity_m3_per_s  # Very likely different


def test_conservation_of_flow_at_node():
    """Test that excess flows correctly represent unconveyed volume."""
    # Simple scenario: one channel receiving inflow
    channel = make_test_channel("n_0_0", "n_0_1")
    params = ChannelHydraulicParameters(width_m=1.0, depth_m=0.5, manning_n=0.015, slope_m_per_m=0.001)
    capacity = compute_channel_capacity(channel, params, timestep_hours=1.0)

    # Test various inflow scenarios
    test_cases = [
        (0.0, 0.0),           # No inflow
        (capacity.capacity_volume_m3 * 0.5, 0.0),  # Below capacity
        (capacity.capacity_volume_m3, 0.0),        # At capacity
        (capacity.capacity_volume_m3 * 1.5, capacity.capacity_volume_m3 * 0.5),  # Above capacity
    ]

    for inflow, expected_excess in test_cases:
        excess = compute_channel_excess(inflow, capacity)
        assert abs(excess - expected_excess) < 1e-9, f"Failed for inflow {inflow}: got {excess}, expected {expected_excess}"


def test_capacity_volume_scaling_with_timestep():
    """Capacity volume should scale linearly with timestep."""
    channel = make_test_channel("n_0_0", "n_0_1")
    params = ChannelHydraulicParameters(width_m=2.0, depth_m=1.0, manning_n=0.013, slope_m_per_m=0.0005)

    cap_1hr = compute_channel_capacity(channel, params, timestep_hours=1.0)
    cap_2hr = compute_channel_capacity(channel, params, timestep_hours=2.0)
    cap_0_5hr = compute_channel_capacity(channel, params, timestep_hours=0.5)

    # Same flow rate (m³/s)
    assert abs(cap_1hr.capacity_m3_per_s - cap_2hr.capacity_m3_per_s) < 1e-9
    assert abs(cap_1hr.capacity_m3_per_s - cap_0_5hr.capacity_m3_per_s) < 1e-9

    # Volume should scale with time
    assert abs(cap_2hr.capacity_volume_m3 - 2 * cap_1hr.capacity_volume_m3) < 1e-9
    assert abs(cap_0_5hr.capacity_volume_m3 - 0.5 * cap_1hr.capacity_volume_m3) < 1e-9


if __name__ == "__main__":
    pytest.main([__file__, "-v"])