"""Tests for drainage domain models."""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.domain.drainage.models import (
    DrainageChannel,
    DrainageNetwork,
    DrainageNode,
    NodeType,
    Provenance,
)


def test_valid_drainage_node():
    """Test creation of a valid DrainageNode."""
    node = DrainageNode(
        id="node_1",
        x=100.0,
        y=200.0,
        elevation_m=10.5,
        node_type=NodeType.INLET,
        provenance=Provenance.OSM,
    )
    assert node.id == "node_1"
    assert node.x == 100.0
    assert node.y == 200.0
    assert node.elevation_m == 10.5
    assert node.node_type == NodeType.INLET
    assert node.provenance == Provenance.OSM


def test_valid_drainage_channel():
    """Test creation of a valid DrainageChannel."""
    channel = DrainageChannel(
        id="channel_1",
        upstream_node_id="node_1",
        downstream_node_id="node_2",
        length_m=50.0,
        provenance=Provenance.DEM_DERIVED,
    )
    assert channel.id == "channel_1"
    assert channel.upstream_node_id == "node_1"
    assert channel.downstream_node_id == "node_2"
    assert channel.length_m == 50.0
    assert channel.provenance == Provenance.DEM_DERIVED


def test_invalid_channel_length():
    """Test that non-positive channel length raises ValidationError."""
    with pytest.raises(ValidationError) as exc_info:
        DrainageChannel(
            id="channel_1",
            upstream_node_id="node_1",
            downstream_node_id="node_2",
            length_m=0.0,
            provenance=Provenance.OSM,
        )
    assert "length_m" in str(exc_info.value)
    assert "greater than 0" in str(exc_info.value).lower()

    with pytest.raises(ValidationError) as exc_info:
        DrainageChannel(
            id="channel_1",
            upstream_node_id="node_1",
            downstream_node_id="node_2",
            length_m=-10.0,
            provenance=Provenance.OSM,
        )
    assert "length_m" in str(exc_info.value)
    assert "greater than 0" in str(exc_info.value).lower()


def test_valid_drainage_network():
    """Test creation of a valid DrainageNetwork."""
    nodes = {
        "node_1": DrainageNode(
            id="node_1",
            x=0.0,
            y=0.0,
            elevation_m=10.0,
            node_type=NodeType.INLET,
            provenance=Provenance.OSM,
        ),
        "node_2": DrainageNode(
            id="node_2",
            x=100.0,
            y=0.0,
            elevation_m=8.0,
            node_type=NodeType.OUTLET,
            provenance=Provenance.OSM,
        ),
    }
    channels = {
        "channel_1": DrainageChannel(
            id="channel_1",
            upstream_node_id="node_1",
            downstream_node_id="node_2",
            length_m=100.0,
            provenance=Provenance.OSM,
        )
    }
    network = DrainageNetwork(nodes=nodes, channels=channels, crs="EPSG:32643")
    assert len(network.nodes) == 2
    assert len(network.channels) == 1
    assert network.crs == "EPSG:32643"


def test_invalid_network_channel_reference():
    """Test that invalid channel references raise ValidationError."""
    nodes = {
        "node_1": DrainageNode(
            id="node_1",
            x=0.0,
            y=0.0,
            elevation_m=10.0,
            node_type=NodeType.INLET,
            provenance=Provenance.OSM,
        ),
    }
    channels = {
        "channel_1": DrainageChannel(
            id="channel_1",
            upstream_node_id="node_1",
            downstream_node_id="node_2",  # node_2 does not exist
            length_m=100.0,
            provenance=Provenance.OSM,
        )
    }
    with pytest.raises(ValidationError) as exc_info:
        DrainageNetwork(nodes=nodes, channels=channels, crs="EPSG:32643")
    assert "channel_1" in str(exc_info.value)
    assert "non-existent downstream node" in str(exc_info.value)