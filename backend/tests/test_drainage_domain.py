"""Focused tests for the drainage domain models.

These exercise the real ``backend.app.domain.drainage.models`` contract:
strict channel node references, invert-derived slope status, and
shape-aware hydraulic geometry computation (RECT/OREC/CIRC only —
unsupported or incomplete geometry must report itself as unsupported,
never guessed).
"""

import math
import unittest

from backend.app.domain.drainage.models import (
    DrainageChannel,
    DrainageNetwork,
    DrainageNode,
    HydraulicAttributeSource,
    NodeType,
    Provenance,
    SlopeStatus,
)


def _make_node(node_id: str, elevation_m: float, node_type: NodeType) -> DrainageNode:
    return DrainageNode(
        id=node_id,
        x=0.0,
        y=0.0,
        elevation_m=elevation_m,
        node_type=node_type,
        provenance=Provenance.OSM,
    )


class TestNodeType(unittest.TestCase):
    """NodeType enum values."""

    def test_node_type_values(self):
        self.assertEqual(NodeType.INLET.value, "inlet")
        self.assertEqual(NodeType.JUNCTION.value, "junction")
        self.assertEqual(NodeType.OUTLET.value, "outlet")


class TestDrainageNode(unittest.TestCase):
    """DrainageNode requires full deterministic geometry."""

    def test_node_requires_geometry(self):
        """x, y, elevation_m, node_type and provenance are all required —
        a node without location evidence cannot be constructed."""
        with self.assertRaises(Exception):
            DrainageNode(id="NODE-001")  # type: ignore[call-arg]

    def test_node_creation_with_values(self):
        node = DrainageNode(
            id="NODE-002",
            x=100.5,
            y=200.3,
            elevation_m=10.5,
            node_type=NodeType.JUNCTION,
            provenance=Provenance.OSM,
            ground_level_m=12.0,
        )

        self.assertEqual(node.id, "NODE-002")
        self.assertEqual(node.x, 100.5)
        self.assertEqual(node.y, 200.3)
        self.assertEqual(node.elevation_m, 10.5)
        self.assertEqual(node.node_type, NodeType.JUNCTION)
        self.assertEqual(node.provenance, Provenance.OSM)
        self.assertEqual(node.ground_level_m, 12.0)


class TestDrainageChannel(unittest.TestCase):
    """DrainageChannel slope and hydraulic geometry contract."""

    def test_channel_requires_positive_length(self):
        """length_m is required and must be strictly positive."""
        with self.assertRaises(Exception):
            DrainageChannel(
                id="CHANNEL-001",
                upstream_node_id="NODE-001",
                downstream_node_id="NODE-002",
                provenance=Provenance.BMC,
            )
        with self.assertRaises(Exception):
            DrainageChannel(
                id="CHANNEL-001",
                upstream_node_id="NODE-001",
                downstream_node_id="NODE-002",
                length_m=-5.0,
                provenance=Provenance.BMC,
            )

    def test_slope_computation_positive(self):
        channel = DrainageChannel(
            id="CHANNEL-002",
            upstream_node_id="NODE-001",
            downstream_node_id="NODE-002",
            length_m=100.0,
            us_invert_m=10.0,
            ds_invert_m=8.0,
            provenance=Provenance.BMC,
        )
        self.assertAlmostEqual(channel.compute_longitudinal_slope(), 0.02)
        self.assertEqual(channel.get_slope_status(), SlopeStatus.POSITIVE)

    def test_slope_computation_flat(self):
        channel = DrainageChannel(
            id="CHANNEL-003",
            upstream_node_id="NODE-001",
            downstream_node_id="NODE-002",
            length_m=100.0,
            us_invert_m=10.0,
            ds_invert_m=10.0,
            provenance=Provenance.BMC,
        )
        self.assertEqual(channel.compute_longitudinal_slope(), 0.0)
        self.assertEqual(channel.get_slope_status(), SlopeStatus.FLAT)

    def test_slope_computation_adverse_preserves_direction(self):
        """Adverse slope is reported as-is; direction is never reversed."""
        channel = DrainageChannel(
            id="CHANNEL-004",
            upstream_node_id="NODE-001",
            downstream_node_id="NODE-002",
            length_m=100.0,
            us_invert_m=8.0,
            ds_invert_m=10.0,
            provenance=Provenance.BMC,
        )
        self.assertAlmostEqual(channel.compute_longitudinal_slope(), -0.02)
        self.assertEqual(channel.get_slope_status(), SlopeStatus.ADVERSE)

    def test_slope_missing_when_inverts_missing(self):
        """Missing inverts stay MISSING — never silently zero-filled."""
        channel = DrainageChannel(
            id="CHANNEL-005",
            upstream_node_id="NODE-001",
            downstream_node_id="NODE-002",
            length_m=100.0,
            provenance=Provenance.BMC,
        )
        self.assertIsNone(channel.compute_longitudinal_slope())
        self.assertEqual(channel.get_slope_status(), SlopeStatus.MISSING)

    def test_hydraulic_geometry_rect(self):
        channel = DrainageChannel(
            id="CHANNEL-006",
            upstream_node_id="NODE-001",
            downstream_node_id="NODE-002",
            length_m=100.0,
            shape="RECT",
            conduit_width_mm=2000.0,
            conduit_height_mm=1000.0,
            provenance=Provenance.BMC,
        )
        area, perimeter, radius, supported = channel.compute_hydraulic_geometry()
        self.assertTrue(supported)
        self.assertAlmostEqual(area, 2.0)
        self.assertAlmostEqual(perimeter, 4.0)
        self.assertAlmostEqual(radius, 0.5)

    def test_hydraulic_geometry_circ(self):
        channel = DrainageChannel(
            id="CHANNEL-007",
            upstream_node_id="NODE-001",
            downstream_node_id="NODE-002",
            length_m=100.0,
            shape="CIRC",
            conduit_width_mm=1000.0,
            provenance=Provenance.BMC,
        )
        area, perimeter, radius, supported = channel.compute_hydraulic_geometry()
        self.assertTrue(supported)
        self.assertAlmostEqual(area, math.pi * 0.25)
        self.assertAlmostEqual(perimeter, math.pi * 1.0)
        self.assertAlmostEqual(radius, 0.25)

    def test_hydraulic_geometry_unsupported_shape_reports_not_supported(self):
        """Unsupported shapes return not-supported, never a guessed area."""
        channel = DrainageChannel(
            id="CHANNEL-008",
            upstream_node_id="NODE-001",
            downstream_node_id="NODE-002",
            length_m=100.0,
            shape="U_SHAPE",
            provenance=Provenance.BMC,
        )
        area, perimeter, radius, supported = channel.compute_hydraulic_geometry()
        self.assertFalse(supported)
        self.assertIsNone(area)
        self.assertIsNone(perimeter)
        self.assertIsNone(radius)


class TestDrainageNetwork(unittest.TestCase):
    """DrainageNetwork reference integrity."""

    def setUp(self):
        self.node1 = _make_node("NODE-001", 10.0, NodeType.INLET)
        self.node2 = _make_node("NODE-002", 8.0, NodeType.OUTLET)
        self.channel = DrainageChannel(
            id="CHANNEL-001",
            upstream_node_id="NODE-001",
            downstream_node_id="NODE-002",
            length_m=100.0,
            us_invert_m=10.0,
            ds_invert_m=8.0,
            provenance=Provenance.BMC,
        )

    def test_network_creation(self):
        network = DrainageNetwork(
            nodes={"NODE-001": self.node1, "NODE-002": self.node2},
            channels={"CHANNEL-001": self.channel},
            crs="EPSG:32643",
        )
        self.assertEqual(len(network.nodes), 2)
        self.assertEqual(len(network.channels), 1)
        self.assertEqual(network.crs, "EPSG:32643")
        self.assertEqual(network.provenance, Provenance.BMC)

    def test_network_invalid_upstream_reference(self):
        with self.assertRaises(ValueError) as ctx:
            DrainageNetwork(
                nodes={"NODE-001": self.node1},
                channels={"CHANNEL-002": DrainageChannel(
                    id="CHANNEL-002",
                    upstream_node_id="NODE-003",
                    downstream_node_id="NODE-001",
                    length_m=50.0,
                    provenance=Provenance.OSM,
                )},
                crs="EPSG:32643",
            )
        self.assertIn("references non-existent upstream node", str(ctx.exception))

    def test_network_invalid_downstream_reference(self):
        with self.assertRaises(ValueError) as ctx:
            DrainageNetwork(
                nodes={"NODE-001": self.node1},
                channels={"CHANNEL-002": DrainageChannel(
                    id="CHANNEL-002",
                    upstream_node_id="NODE-001",
                    downstream_node_id="NODE-003",
                    length_m=50.0,
                    provenance=Provenance.OSM,
                )},
                crs="EPSG:32643",
            )
        self.assertIn("references non-existent downstream node", str(ctx.exception))

    def test_hydraulic_attribute_source_enum(self):
        self.assertEqual(HydraulicAttributeSource.BMC_AUTHORITATIVE.value, "BMC_AUTHORITATIVE")
        self.assertEqual(HydraulicAttributeSource.ASSUMED.value, "ASSUMED")
        self.assertEqual(HydraulicAttributeSource.UNAVAILABLE.value, "UNAVAILABLE")


if __name__ == "__main__":
    unittest.main()
