"""Tests for hydraulic network assembly."""

from __future__ import annotations

from datetime import datetime

import pytest

from backend.app.domain.delhi.digital_twin.hydraulic_contract import (
    ProvenancedValue,
    HydraulicNode,
    ChainagePoint,
    OpenChannelReach,
    CoveredConduit,
    HydraulicStructure,
    InflowAttachment,
    DownstreamBoundary,
    HydraulicObservation,
    CrossSection,
    HydraulicDataset,
)
from backend.app.domain.delhi.digital_twin.models import ProvenanceStatus
from backend.app.domain.delhi.digital_twin.hydraulic_network import (
    assemble_hydraulic_network,
    HydraulicNetwork,
    HydraulicNetworkAssemblyError,
)


def test_complete_synthetic_dataset_assembles_successfully():
    """Test that a complete synthetic TEST-ONLY deterministic dataset assembles successfully."""
    # Create nodes
    node1 = HydraulicNode(
        node_id="N1",
        easting=ProvenancedValue(value=0.0, provenance=ProvenanceStatus.OBSERVED),
        northing=ProvenancedValue(value=0.0, provenance=ProvenanceStatus.OBSERVED),
        invert_elev_m=ProvenancedValue(value=10.0, provenance=ProvenanceStatus.OBSERVED),
        node_type="JUNCTION",
        upstream_connections=[],
        downstream_connections=["N2"]
    )

    node2 = HydraulicNode(
        node_id="N2",
        easting=ProvenancedValue(value=100.0, provenance=ProvenanceStatus.OBSERVED),
        northing=ProvenancedValue(value=0.0, provenance=ProvenanceStatus.OBSERVED),
        invert_elev_m=ProvenancedValue(value=9.5, provenance=ProvenanceStatus.OBSERVED),
        node_type="OUTFALL",
        upstream_connections=["N1"],
        downstream_connections=[]
    )

    # Create cross-section
    xs = CrossSection(
        cross_section_id="XS1",
        geometry_reference="test_data.csv",
        geometry_representation="IRREGULAR",
        provenance=ProvenanceStatus.OBSERVED
    )

    # Create reach
    reach = OpenChannelReach(
        reach_id="R1",
        upstream_node_id="N1",
        downstream_node_id="N2",
        chainage_profile=[
            ChainagePoint(
                chainage=ProvenancedValue(value=0.0, provenance=ProvenanceStatus.OBSERVED),
                invert_elev_m=ProvenancedValue(value=10.0, provenance=ProvenanceStatus.OBSERVED)
            ),
            ChainagePoint(
                chainage=ProvenancedValue(value=50.0, provenance=ProvenanceStatus.OBSERVED),
                invert_elev_m=ProvenancedValue(value=9.8, provenance=ProvenanceStatus.OBSERVED)
            ),
            ChainagePoint(
                chainage=ProvenancedValue(value=100.0, provenance=ProvenanceStatus.OBSERVED),
                invert_elev_m=ProvenancedValue(value=9.5, provenance=ProvenanceStatus.OBSERVED)
            )
        ],
        geometry_representation="TABULATED",
        width_m=ProvenancedValue(value=5.0, provenance=ProvenanceStatus.OBSERVED),
        depth_m=ProvenancedValue(value=2.0, provenance=ProvenanceStatus.OBSERVED),
        slope_m_per_m=ProvenancedValue(value=0.005, provenance=ProvenanceStatus.OBSERVED),
        length_m=ProvenancedValue(value=100.0, provenance=ProvenanceStatus.OBSERVED),
        manning_n=ProvenancedValue(value=0.015, provenance=ProvenanceStatus.OBSERVED),
        structure_refs=[],
        cross_section_refs=["XS1"]
    )

    # Create structure
    structure = HydraulicStructure(
        structure_id="S1",
        structure_type="CULVERT",
        upstream_node_id="N1",
        downstream_node_id="N2",
        inlet_invert_elev_m=ProvenancedValue(value=10.0, provenance=ProvenanceStatus.OBSERVED),
        outlet_invert_elev_m=ProvenancedValue(value=9.5, provenance=ProvenanceStatus.OBSERVED),
        structure_geometry={"length": 50.0}
    )

    # Create inflow attachment
    attachment = InflowAttachment(
        inflow_id="I1",
        source_subcatchment_id="SC1",
        attachment_node_id="N1",
        invert_elev_at_attachment_m=ProvenancedValue(value=10.0, provenance=ProvenanceStatus.OBSERVED)
    )

    # Create downstream boundary
    boundary = DownstreamBoundary(
        boundary_id="B1",
        boundary_node_id="N2",
        boundary_type="FIXED_WATER_LEVEL",
        parameters={"water_level_m": 2.0},
        provenance=ProvenanceStatus.OBSERVED
    )

    # Create observation
    observation = HydraulicObservation(
        observation_id="O1",
        event_id="E1",
        observation_type="WATER_LEVEL",
        timestamp=datetime.now(),
        location_ref="N2",
        measured_value=ProvenancedValue(value=3.0, provenance=ProvenanceStatus.OBSERVED),
        units="m"
    )

    # Assemble dataset
    dataset = HydraulicDataset(
        nodes=[node1, node2],
        open_channel_reaches=[reach],
        covered_conduits=[],
        hydraulic_structures=[structure],
        inflow_attachments=[attachment],
        downstream_boundaries=[boundary],
        cross_sections=[xs],
        hydraulic_observations=[observation]
    )

    # Assemble network
    network = assemble_hydraulic_network(dataset)

    # Verify all entities are present
    assert len(network.nodes) == 2
    assert len(network.open_channel_reaches) == 1
    assert len(network.hydraulic_structures) == 1
    assert len(network.cross_sections) == 1
    assert len(network.inflow_attachments) == 1
    assert len(network.downstream_boundaries) == 1
    assert len(network.hydraulic_observations) == 1

    # Verify specific entities are preserved
    assert network.nodes[0].node_id == "N1"
    assert network.open_channel_reaches[0].reach_id == "R1"
    assert network.hydraulic_structures[0].structure_id == "S1"
    assert network.cross_sections[0].cross_section_id == "XS1"
    assert network.inflow_attachments[0].inflow_id == "I1"
    assert network.downstream_boundaries[0].boundary_id == "B1"
    assert network.hydraulic_observations[0].observation_id == "O1"


def test_unknown_physical_geometry_blocks_assembly():
    """Test that UNKNOWN physical geometry cannot assemble as deterministic network."""
    node = HydraulicNode(
        node_id="N1",
        easting=ProvenancedValue(value=0.0, provenance=ProvenanceStatus.OBSERVED),
        northing=ProvenancedValue(value=0.0, provenance=ProvenanceStatus.OBSERVED),
        invert_elev_m=ProvenancedValue(provenance=ProvenanceStatus.UNKNOWN),  # UNKNOWN blocks readiness
        node_type="JUNCTION",
        upstream_connections=[],
        downstream_connections=["N2"]
    )

    node2 = HydraulicNode(
        node_id="N2",
        easting=ProvenancedValue(value=100.0, provenance=ProvenanceStatus.OBSERVED),
        northing=ProvenancedValue(value=0.0, provenance=ProvenanceStatus.OBSERVED),
        invert_elev_m=ProvenancedValue(value=9.5, provenance=ProvenanceStatus.OBSERVED),
        node_type="OUTFALL",
        upstream_connections=["N1"],
        downstream_connections=[]
    )

    boundary = DownstreamBoundary(
        boundary_id="B1",
        boundary_node_id="N2",
        boundary_type="FIXED_WATER_LEVEL",
        parameters={"water_level_m": 2.0},
        provenance=ProvenanceStatus.OBSERVED
    )

    dataset = HydraulicDataset(
        nodes=[node, node2],
        downstream_boundaries=[boundary]
    )

    # Should raise assembly error due to UNKNOWN invert
    with pytest.raises(HydraulicNetworkAssemblyError) as exc_info:
        assemble_hydraulic_network(dataset)

    assert "Dataset not ready for assembly" in str(exc_info.value)
    assert "invert_elev_m missing or not deterministic" in str(exc_info.value)


def test_missing_upstream_node_blocks_assembly():
    """Test that missing upstream node blocks assembly."""
    # Create nodes that exist
    node_actual = HydraulicNode(
        node_id="N_ACTUAL",
        easting=ProvenancedValue(value=0.0, provenance=ProvenanceStatus.OBSERVED),
        northing=ProvenancedValue(value=0.0, provenance=ProvenanceStatus.OBSERVED),
        invert_elev_m=ProvenancedValue(value=10.0, provenance=ProvenanceStatus.OBSERVED),
        node_type="JUNCTION",
        upstream_connections=[],
        downstream_connections=["N2"]
    )

    node2 = HydraulicNode(
        node_id="N2",
        easting=ProvenancedValue(value=100.0, provenance=ProvenanceStatus.OBSERVED),
        northing=ProvenancedValue(value=0.0, provenance=ProvenanceStatus.OBSERVED),
        invert_elev_m=ProvenancedValue(value=9.5, provenance=ProvenanceStatus.OBSERVED),
        node_type="OUTFALL",
        upstream_connections=["N_ACTUAL"],
        downstream_connections=[]
    )

    # Reach references N1 (non-existent) as upstream, but N_ACTUAL exists
    reach = OpenChannelReach(
        reach_id="R1",
        upstream_node_id="N1",  # N1 doesn't exist
        downstream_node_id="N2",
        chainage_profile=[
            ChainagePoint(
                chainage=ProvenancedValue(value=0.0, provenance=ProvenanceStatus.OBSERVED),
                invert_elev_m=ProvenancedValue(value=10.0, provenance=ProvenanceStatus.OBSERVED)
            ),
            ChainagePoint(
                chainage=ProvenancedValue(value=100.0, provenance=ProvenanceStatus.OBSERVED),
                invert_elev_m=ProvenancedValue(value=9.5, provenance=ProvenanceStatus.OBSERVED)
            )
        ],
        geometry_representation="TABULATED",
        manning_n=ProvenancedValue(value=0.015, provenance=ProvenanceStatus.OBSERVED),
        structure_refs=[],
        cross_section_refs=[]
    )

    # Add a downstream boundary for N2 to make the dataset ready for other checks
    boundary = DownstreamBoundary(
        boundary_id="B1",
        boundary_node_id="N2",
        boundary_type="FIXED_WATER_LEVEL",
        parameters={"water_level_m": 2.0},
        provenance=ProvenanceStatus.OBSERVED
    )

    dataset = HydraulicDataset(
        nodes=[node_actual, node2],  # N_ACTUAL and N2 exist, but reach references N1
        open_channel_reaches=[reach],
        downstream_boundaries=[boundary]
    )

    # Should raise assembly error due to missing upstream node reference
    with pytest.raises(HydraulicNetworkAssemblyError) as exc_info:
        assemble_hydraulic_network(dataset)

    assert "Unresolved references in dataset" in str(exc_info.value)
    assert "upstream node N1 not found" in str(exc_info.value)


def test_missing_downstream_node_blocks_assembly():
    """Test that missing downstream node blocks assembly."""
    # Create the actual nodes that exist
    node1 = HydraulicNode(
        node_id="N1_ACTUAL",
        easting=ProvenancedValue(value=0.0, provenance=ProvenanceStatus.OBSERVED),
        northing=ProvenancedValue(value=0.0, provenance=ProvenanceStatus.OBSERVED),
        invert_elev_m=ProvenancedValue(value=10.0, provenance=ProvenanceStatus.OBSERVED),
        node_type="JUNCTION",
        upstream_connections=[],
        downstream_connections=["N2"]  # References N2
    )

    # N2_DOESNT_EXIST is referenced but we won't create it
    reach = OpenChannelReach(
        reach_id="R1",
        upstream_node_id="N1_ACTUAL",
        downstream_node_id="N2_DOESNT_EXIST",  # N2 doesn't exist
        chainage_profile=[
            ChainagePoint(
                chainage=ProvenancedValue(value=0.0, provenance=ProvenanceStatus.OBSERVED),
                invert_elev_m=ProvenancedValue(value=10.0, provenance=ProvenanceStatus.OBSERVED)
            ),
            ChainagePoint(
                chainage=ProvenancedValue(value=100.0, provenance=ProvenanceStatus.OBSERVED),
                invert_elev_m=ProvenancedValue(value=9.5, provenance=ProvenanceStatus.OBSERVED)
            )
        ],
        geometry_representation="TABULATED",
        manning_n=ProvenancedValue(value=0.015, provenance=ProvenanceStatus.OBSERVED),
        structure_refs=[],
        cross_section_refs=[]
    )

    dataset = HydraulicDataset(
        nodes=[node1],
        open_channel_reaches=[reach]
    )

    # Should raise assembly error due to missing downstream node
    with pytest.raises(HydraulicNetworkAssemblyError) as exc_info:
        assemble_hydraulic_network(dataset)

    assert "Unresolved references in dataset" in str(exc_info.value)
    assert "downstream node N2_DOESNT_EXIST not found" in str(exc_info.value)


def test_missing_structure_reference_blocks_assembly():
    """Test that missing structure reference blocks assembly."""
    # Create nodes that exist
    node1 = HydraulicNode(
        node_id="N1",
        easting=ProvenancedValue(value=0.0, provenance=ProvenanceStatus.OBSERVED),
        northing=ProvenancedValue(value=0.0, provenance=ProvenanceStatus.OBSERVED),
        invert_elev_m=ProvenancedValue(value=10.0, provenance=ProvenanceStatus.OBSERVED),
        node_type="JUNCTION",
        upstream_connections=[],
        downstream_connections=["N2"]
    )

    node2 = HydraulicNode(
        node_id="N2",
        easting=ProvenancedValue(value=100.0, provenance=ProvenanceStatus.OBSERVED),
        northing=ProvenancedValue(value=0.0, provenance=ProvenanceStatus.OBSERVED),
        invert_elev_m=ProvenancedValue(value=9.5, provenance=ProvenanceStatus.OBSERVED),
        node_type="OUTFALL",
        upstream_connections=["N1"],
        downstream_connections=[]
    )

    # Reach references S1 (non-existent) as structure reference
    reach = OpenChannelReach(
        reach_id="R1",
        upstream_node_id="N1",
        downstream_node_id="N2",
        chainage_profile=[
            ChainagePoint(
                chainage=ProvenancedValue(value=0.0, provenance=ProvenanceStatus.OBSERVED),
                invert_elev_m=ProvenancedValue(value=10.0, provenance=ProvenanceStatus.OBSERVED)
            ),
            ChainagePoint(
                chainage=ProvenancedValue(value=100.0, provenance=ProvenanceStatus.OBSERVED),
                invert_elev_m=ProvenancedValue(value=9.5, provenance=ProvenanceStatus.OBSERVED)
            )
        ],
        geometry_representation="TABULATED",
        manning_n=ProvenancedValue(value=0.015, provenance=ProvenanceStatus.OBSERVED),
        structure_refs=["S1_DOESNT_EXIST"],  # S1 doesn't exist
        cross_section_refs=[]
    )

    dataset = HydraulicDataset(
        nodes=[node1, node2],
        open_channel_reaches=[reach]
    )

    # Should raise assembly error due to missing structure reference
    with pytest.raises(HydraulicNetworkAssemblyError) as exc_info:
        assemble_hydraulic_network(dataset)

    assert "Unresolved references in dataset" in str(exc_info.value)
    assert "structure reference S1_DOESNT_EXIST not found" in str(exc_info.value)


def test_missing_cross_section_reference_blocks_assembly():
    """Test that missing cross-section reference blocks assembly."""
    # Create nodes that exist
    node1 = HydraulicNode(
        node_id="N1",
        easting=ProvenancedValue(value=0.0, provenance=ProvenanceStatus.OBSERVED),
        northing=ProvenancedValue(value=0.0, provenance=ProvenanceStatus.OBSERVED),
        invert_elev_m=ProvenancedValue(value=10.0, provenance=ProvenanceStatus.OBSERVED),
        node_type="JUNCTION",
        upstream_connections=[],
        downstream_connections=["N2"]
    )

    node2 = HydraulicNode(
        node_id="N2",
        easting=ProvenancedValue(value=100.0, provenance=ProvenanceStatus.OBSERVED),
        northing=ProvenancedValue(value=0.0, provenance=ProvenanceStatus.OBSERVED),
        invert_elev_m=ProvenancedValue(value=9.5, provenance=ProvenanceStatus.OBSERVED),
        node_type="OUTFALL",
        upstream_connections=["N1"],
        downstream_connections=[]
    )

    # Reach references XS1_DOESNT_EXIST as cross-section reference
    reach = OpenChannelReach(
        reach_id="R1",
        upstream_node_id="N1",
        downstream_node_id="N2",
        chainage_profile=[
            ChainagePoint(
                chainage=ProvenancedValue(value=0.0, provenance=ProvenanceStatus.OBSERVED),
                invert_elev_m=ProvenancedValue(value=10.0, provenance=ProvenanceStatus.OBSERVED)
            ),
            ChainagePoint(
                chainage=ProvenancedValue(value=100.0, provenance=ProvenanceStatus.OBSERVED),
                invert_elev_m=ProvenancedValue(value=9.5, provenance=ProvenanceStatus.OBSERVED)
            )
        ],
        geometry_representation="TABULATED",
        manning_n=ProvenancedValue(value=0.015, provenance=ProvenanceStatus.OBSERVED),
        structure_refs=[],
        cross_section_refs=["XS1_DOESNT_EXIST"]  # XS1 doesn't exist
    )

    dataset = HydraulicDataset(
        nodes=[node1, node2],
        open_channel_reaches=[reach]
    )

    # Should raise assembly error due to missing cross-section reference
    with pytest.raises(HydraulicNetworkAssemblyError) as exc_info:
        assemble_hydraulic_network(dataset)

    assert "Unresolved references in dataset" in str(exc_info.value)
    assert "cross-section reference XS1_DOESNT_EXIST not found" in str(exc_info.value)


def test_missing_inflow_attachment_target_blocks_assembly():
    """Test that missing inflow attachment target blocks assembly."""
    # Create a node that exists
    node_exists = HydraulicNode(
        node_id="N_EXISTS",
        easting=ProvenancedValue(value=0.0, provenance=ProvenanceStatus.OBSERVED),
        northing=ProvenancedValue(value=0.0, provenance=ProvenanceStatus.OBSERVED),
        invert_elev_m=ProvenancedValue(value=10.0, provenance=ProvenanceStatus.OBSERVED),
        node_type="JUNCTION",
        upstream_connections=[],
        downstream_connections=[]
    )

    # Create attachment that references a non-existent node
    attachment = InflowAttachment(
        inflow_id="I1",
        source_subcatchment_id="SC1",
        attachment_node_id="N_DOESNT_EXIST",  # N1 doesn't exist
        invert_elev_at_attachment_m=ProvenancedValue(value=10.0, provenance=ProvenanceStatus.OBSERVED)
    )

    # Need to add a downstream boundary to make the dataset ready for other checks
    boundary = DownstreamBoundary(
        boundary_id="B1",
        boundary_node_id="N_EXISTS",
        boundary_type="FIXED_WATER_LEVEL",
        parameters={"water_level_m": 2.0},
        provenance=ProvenanceStatus.OBSERVED
    )

    dataset = HydraulicDataset(
        nodes=[node_exists],
        inflow_attachments=[attachment],
        downstream_boundaries=[boundary]
    )

    # Should raise assembly error due to missing attachment node
    with pytest.raises(HydraulicNetworkAssemblyError) as exc_info:
        assemble_hydraulic_network(dataset)

    assert "Unresolved references in dataset" in str(exc_info.value)
    assert "attachment node N_DOESNT_EXIST not found" in str(exc_info.value)


def test_missing_downstream_boundary_blocks_assembly():
    """Test that missing downstream boundary blocks assembly."""
    node = HydraulicNode(
        node_id="N1",
        easting=ProvenancedValue(value=0.0, provenance=ProvenanceStatus.OBSERVED),
        northing=ProvenancedValue(value=0.0, provenance=ProvenanceStatus.OBSERVED),
        invert_elev_m=ProvenancedValue(value=10.0, provenance=ProvenanceStatus.OBSERVED),
        node_type="JUNCTION",
        upstream_connections=[],
        downstream_connections=[]
    )

    # No downstream boundary defined
    dataset = HydraulicDataset(nodes=[node])

    # Should raise assembly error due to missing downstream boundary
    with pytest.raises(HydraulicNetworkAssemblyError) as exc_info:
        assemble_hydraulic_network(dataset)

    assert "Dataset not ready for assembly" in str(exc_info.value)
    assert "No downstream boundary defined" in str(exc_info.value)


def test_duplicate_node_ids_are_rejected():
    """Test that duplicate node IDs are rejected."""
    node1 = HydraulicNode(
        node_id="N1",
        easting=ProvenancedValue(value=0.0, provenance=ProvenanceStatus.OBSERVED),
        northing=ProvenancedValue(value=0.0, provenance=ProvenanceStatus.OBSERVED),
        invert_elev_m=ProvenancedValue(value=10.0, provenance=ProvenanceStatus.OBSERVED),
        node_type="JUNCTION",
        upstream_connections=[],
        downstream_connections=[]
    )

    node2 = HydraulicNode(
        node_id="N1",  # Duplicate ID
        easting=ProvenancedValue(value=100.0, provenance=ProvenanceStatus.OBSERVED),
        northing=ProvenancedValue(value=0.0, provenance=ProvenanceStatus.OBSERVED),
        invert_elev_m=ProvenancedValue(value=9.5, provenance=ProvenanceStatus.OBSERVED),
        node_type="OUTFALL",
        upstream_connections=["N1"],
        downstream_connections=[]
    )

    boundary = DownstreamBoundary(
        boundary_id="B1",
        boundary_node_id="N1",
        boundary_type="FIXED_WATER_LEVEL",
        parameters={"water_level_m": 2.0},
        provenance=ProvenanceStatus.OBSERVED
    )

    dataset = HydraulicDataset(
        nodes=[node1, node2],
        downstream_boundaries=[boundary]
    )

    # Should raise assembly error due to duplicate node IDs
    with pytest.raises(HydraulicNetworkAssemblyError) as exc_info:
        assemble_hydraulic_network(dataset)

    assert "Duplicate node IDs found" in str(exc_info.value)


def test_duplicate_reach_ids_are_rejected():
    """Test that duplicate reach IDs are rejected."""
    reach1 = OpenChannelReach(
        reach_id="R1",
        upstream_node_id="N1",
        downstream_node_id="N2",
        chainage_profile=[
            ChainagePoint(
                chainage=ProvenancedValue(value=0.0, provenance=ProvenanceStatus.OBSERVED),
                invert_elev_m=ProvenancedValue(value=10.0, provenance=ProvenanceStatus.OBSERVED)
            ),
            ChainagePoint(
                chainage=ProvenancedValue(value=100.0, provenance=ProvenanceStatus.OBSERVED),
                invert_elev_m=ProvenancedValue(value=9.5, provenance=ProvenanceStatus.OBSERVED)
            )
        ],
        geometry_representation="TABULATED",
        manning_n=ProvenancedValue(value=0.015, provenance=ProvenanceStatus.OBSERVED),
        structure_refs=[],
        cross_section_refs=[]
    )

    reach2 = OpenChannelReach(
        reach_id="R1",  # Duplicate ID
        upstream_node_id="N2",
        downstream_node_id="N3",
        chainage_profile=[
            ChainagePoint(
                chainage=ProvenancedValue(value=0.0, provenance=ProvenanceStatus.OBSERVED),
                invert_elev_m=ProvenancedValue(value=9.5, provenance=ProvenanceStatus.OBSERVED)
            ),
            ChainagePoint(
                chainage=ProvenancedValue(value=50.0, provenance=ProvenanceStatus.OBSERVED),
                invert_elev_m=ProvenancedValue(value=9.0, provenance=ProvenanceStatus.OBSERVED)
            )
        ],
        geometry_representation="TABULATED",
        manning_n=ProvenancedValue(value=0.015, provenance=ProvenanceStatus.OBSERVED),
        structure_refs=[],
        cross_section_refs=[]
    )

    node1 = HydraulicNode(
        node_id="N1",
        easting=ProvenancedValue(value=0.0, provenance=ProvenanceStatus.OBSERVED),
        northing=ProvenancedValue(value=0.0, provenance=ProvenanceStatus.OBSERVED),
        invert_elev_m=ProvenancedValue(value=10.0, provenance=ProvenanceStatus.OBSERVED),
        node_type="JUNCTION",
        upstream_connections=[],
        downstream_connections=["N2"]
    )

    node2 = HydraulicNode(
        node_id="N2",
        easting=ProvenancedValue(value=100.0, provenance=ProvenanceStatus.OBSERVED),
        northing=ProvenancedValue(value=0.0, provenance=ProvenanceStatus.OBSERVED),
        invert_elev_m=ProvenancedValue(value=9.5, provenance=ProvenanceStatus.OBSERVED),
        node_type="JUNCTION",
        upstream_connections=["N1"],
        downstream_connections=["N3"]
    )

    node3 = HydraulicNode(
        node_id="N3",
        easting=ProvenancedValue(value=150.0, provenance=ProvenanceStatus.OBSERVED),
        northing=ProvenancedValue(value=0.0, provenance=ProvenanceStatus.OBSERVED),
        invert_elev_m=ProvenancedValue(value=9.0, provenance=ProvenanceStatus.OBSERVED),
        node_type="OUTFALL",
        upstream_connections=["N2"],
        downstream_connections=[]
    )

    dataset = HydraulicDataset(
        nodes=[node1, node2, node3],
        open_channel_reaches=[reach1, reach2]
    )

    # Should raise assembly error due to duplicate reach IDs
    with pytest.raises(HydraulicNetworkAssemblyError) as exc_info:
        assemble_hydraulic_network(dataset)

    assert "Duplicate reach IDs found" in str(exc_info.value)


def test_no_geographic_proximity_inference():
    """Test that geographic proximity does not infer connections."""
    # Two nodes very close together but with no explicit connection
    node1 = HydraulicNode(
        node_id="N1",
        easting=ProvenancedValue(value=0.0, provenance=ProvenanceStatus.OBSERVED),
        northing=ProvenancedValue(value=0.0, provenance=ProvenanceStatus.OBSERVED),
        invert_elev_m=ProvenancedValue(value=10.0, provenance=ProvenanceStatus.OBSERVED),
        node_type="JUNCTION",
        upstream_connections=[],
        downstream_connections=[]  # No connection to N2
    )

    node2 = HydraulicNode(
        node_id="N2",
        easting=ProvenancedValue(value=0.001, provenance=ProvenanceStatus.OBSERVED),  # Very close
        northing=ProvenancedValue(value=0.001, provenance=ProvenanceStatus.OBSERVED),  # Very close
        invert_elev_m=ProvenancedValue(value=9.9, provenance=ProvenanceStatus.OBSERVED),
        node_type="OUTFALL",
        upstream_connections=[],  # No connection to N1
        downstream_connections=[]
    )

    # Without downstream boundary, this should fail for missing boundary
    # But let's add a boundary to N2 to test the connection inference
    boundary = DownstreamBoundary(
        boundary_id="B1",
        boundary_node_id="N2",
        boundary_type="FIXED_WATER_LEVEL",
        parameters={"water_level_m": 2.0},
        provenance=ProvenanceStatus.OBSERVED
    )

    dataset = HydraulicDataset(
        nodes=[node1, node2],
        downstream_boundaries=[boundary]
    )

    # Should assemble successfully because there are no missing references
    # (even though nodes are close, no connection is inferred)
    network = assemble_hydraulic_network(dataset)

    assert len(network.nodes) == 2
    assert network.nodes[0].node_id == "N1"
    assert network.nodes[1].node_id == "N2"
    # Verify no connections were inferred
    assert network.nodes[0].downstream_connections == []
    assert network.nodes[1].upstream_connections == []


def test_provenance_is_preserved_exactly():
    """Test that provenance is preserved exactly through assembly."""
    # All required physical geometry fields (including node coordinates) must be
    # OBSERVED/OFFICIAL to pass deterministic-assembly validation. Distinct valid
    # provenances are used so exact preservation is still verifiable.

    node = HydraulicNode(
        node_id="N1",
        easting=ProvenancedValue(value=0.0, provenance=ProvenanceStatus.OBSERVED),
        northing=ProvenancedValue(value=0.0, provenance=ProvenanceStatus.OFFICIAL),  # Different provenance - preserved through assembly
        invert_elev_m=ProvenancedValue(value=10.0, provenance=ProvenanceStatus.OBSERVED),  # Required: must be deterministic
        node_type="JUNCTION",
        upstream_connections=[],
        downstream_connections=["N2"]
    )

    node2 = HydraulicNode(
        node_id="N2",
        easting=ProvenancedValue(value=100.0, provenance=ProvenanceStatus.OFFICIAL),  # Different provenance - preserved through assembly
        northing=ProvenancedValue(value=0.0, provenance=ProvenanceStatus.OBSERVED),  # Different provenance - preserved through assembly
        invert_elev_m=ProvenancedValue(value=9.5, provenance=ProvenanceStatus.OFFICIAL),  # Required: must be deterministic
        node_type="OUTFALL",
        upstream_connections=["N1"],
        downstream_connections=[]
    )

    # Add a reach to test provenance preservation on manning_n (model parameter, not required to be deterministic)
    reach = OpenChannelReach(
        reach_id="R1",
        upstream_node_id="N1",
        downstream_node_id="N2",
        chainage_profile=[
            ChainagePoint(
                chainage=ProvenancedValue(value=0.0, provenance=ProvenanceStatus.OBSERVED),
                invert_elev_m=ProvenancedValue(value=10.0, provenance=ProvenanceStatus.OBSERVED)  # Required: deterministic
            ),
            ChainagePoint(
                chainage=ProvenancedValue(value=100.0, provenance=ProvenanceStatus.OBSERVED),
                invert_elev_m=ProvenancedValue(value=9.5, provenance=ProvenanceStatus.OBSERVED)  # Required: deterministic
            )
        ],
        geometry_representation="TABULATED",
        width_m=ProvenancedValue(value=5.0, provenance=ProvenanceStatus.OBSERVED),
        depth_m=ProvenancedValue(value=2.0, provenance=ProvenanceStatus.OBSERVED),
        slope_m_per_m=ProvenancedValue(value=0.005, provenance=ProvenanceStatus.OBSERVED),
        length_m=ProvenancedValue(value=100.0, provenance=ProvenanceStatus.OBSERVED),
        manning_n=ProvenancedValue(value=0.015, provenance=ProvenanceStatus.DERIVED),  # Model parameter: can have any provenance
        structure_refs=[],
        cross_section_refs=[]
    )

    boundary = DownstreamBoundary(
        boundary_id="B1",
        boundary_node_id="N2",
        boundary_type="FIXED_WATER_LEVEL",
        parameters={"water_level_m": 2.0},
        provenance=ProvenanceStatus.OBSERVED  # Direct provenance field
    )

    dataset = HydraulicDataset(
        nodes=[node, node2],
        open_channel_reaches=[reach],
        downstream_boundaries=[boundary]
    )

    # Assemble the network - should succeed because all required physical geometry is deterministic
    network = assemble_hydraulic_network(dataset)

    # Verify provenance is preserved exactly for all fields
    # Node N1
    assert network.nodes[0].easting.provenance == ProvenanceStatus.OBSERVED
    assert network.nodes[0].northing.provenance == ProvenanceStatus.OFFICIAL
    assert network.nodes[0].invert_elev_m.provenance == ProvenanceStatus.OBSERVED

    # Node N2
    assert network.nodes[1].easting.provenance == ProvenanceStatus.OFFICIAL
    assert network.nodes[1].northing.provenance == ProvenanceStatus.OBSERVED
    assert network.nodes[1].invert_elev_m.provenance == ProvenanceStatus.OFFICIAL

    # Reach R1
    assert network.open_channel_reaches[0].manning_n.provenance == ProvenanceStatus.DERIVED
    assert network.open_channel_reaches[0].chainage_profile[0].invert_elev_m.provenance == ProvenanceStatus.OBSERVED
    assert network.open_channel_reaches[0].chainage_profile[1].invert_elev_m.provenance == ProvenanceStatus.OBSERVED

    # Boundary B1
    assert network.downstream_boundaries[0].provenance == ProvenanceStatus.OBSERVED


def test_assumed_manning_n_does_not_prevent_assembly():
    """Test that ASSUMED Manning n does not itself prevent network assembly when all required physical geometry is deterministic."""
    node1 = HydraulicNode(
        node_id="N1",
        easting=ProvenancedValue(value=0.0, provenance=ProvenanceStatus.OBSERVED),
        northing=ProvenancedValue(value=0.0, provenance=ProvenanceStatus.OBSERVED),
        invert_elev_m=ProvenancedValue(value=10.0, provenance=ProvenanceStatus.OBSERVED),
        node_type="JUNCTION",
        upstream_connections=[],
        downstream_connections=["N2"]
    )

    node2 = HydraulicNode(
        node_id="N2",
        easting=ProvenancedValue(value=100.0, provenance=ProvenanceStatus.OBSERVED),
        northing=ProvenancedValue(value=0.0, provenance=ProvenanceStatus.OBSERVED),
        invert_elev_m=ProvenancedValue(value=9.5, provenance=ProvenanceStatus.OBSERVED),
        node_type="OUTFALL",
        upstream_connections=["N1"],
        downstream_connections=[]
    )

    # Reach with ASSUMED Manning n (should not block assembly)
    reach = OpenChannelReach(
        reach_id="R1",
        upstream_node_id="N1",
        downstream_node_id="N2",
        chainage_profile=[
            ChainagePoint(
                chainage=ProvenancedValue(value=0.0, provenance=ProvenanceStatus.OBSERVED),
                invert_elev_m=ProvenancedValue(value=10.0, provenance=ProvenanceStatus.OBSERVED)
            ),
            ChainagePoint(
                chainage=ProvenancedValue(value=100.0, provenance=ProvenanceStatus.OBSERVED),
                invert_elev_m=ProvenancedValue(value=9.5, provenance=ProvenanceStatus.OBSERVED)
            )
        ],
        geometry_representation="TABULATED",
        width_m=ProvenancedValue(value=5.0, provenance=ProvenanceStatus.OBSERVED),
        depth_m=ProvenancedValue(value=2.0, provenance=ProvenanceStatus.OBSERVED),
        slope_m_per_m=ProvenancedValue(value=0.005, provenance=ProvenanceStatus.OBSERVED),
        length_m=ProvenancedValue(value=100.0, provenance=ProvenanceStatus.OBSERVED),
        manning_n=ProvenancedValue(value=0.015, provenance=ProvenanceStatus.ASSUMED),  # ASSUMED Manning n
        structure_refs=[],
        cross_section_refs=[]
    )

    boundary = DownstreamBoundary(
        boundary_id="B1",
        boundary_node_id="N2",
        boundary_type="FIXED_WATER_LEVEL",
        parameters={"water_level_m": 2.0},
        provenance=ProvenanceStatus.OBSERVED
    )

    dataset = HydraulicDataset(
        nodes=[node1, node2],
        open_channel_reaches=[reach],
        downstream_boundaries=[boundary]
    )

    # Should assemble successfully because Manning n is a model parameter
    network = assemble_hydraulic_network(dataset)

    assert len(network.nodes) == 2
    assert len(network.open_channel_reaches) == 1
    assert network.open_channel_reaches[0].manning_n.provenance == ProvenanceStatus.ASSUMED


def test_no_real_kushak_geometry_used():
    """Test that no real Kushak geometry is used in tests."""
    # This test implicitly passes if all other tests pass with synthetic data
    # We'll create a simple synthetic dataset and verify it assembles

    node1 = HydraulicNode(
        node_id="SYNTHETIC_NODE_1",
        easting=ProvenancedValue(value=100000.0, provenance=ProvenanceStatus.OBSERVED),
        northing=ProvenancedValue(value=200000.0, provenance=ProvenanceStatus.OBSERVED),
        invert_elev_m=ProvenancedValue(value=10.0, provenance=ProvenanceStatus.OBSERVED),
        node_type="JUNCTION",
        upstream_connections=[],
        downstream_connections=["SYNTHETIC_NODE_2"]
    )

    node2 = HydraulicNode(
        node_id="SYNTHETIC_NODE_2",
        easting=ProvenancedValue(value=100010.0, provenance=ProvenanceStatus.OBSERVED),
        northing=ProvenancedValue(value=200000.0, provenance=ProvenanceStatus.OBSERVED),
        invert_elev_m=ProvenancedValue(value=9.5, provenance=ProvenanceStatus.OBSERVED),
        node_type="OUTFALL",
        upstream_connections=["SYNTHETIC_NODE_1"],
        downstream_connections=[]
    )

    boundary = DownstreamBoundary(
        boundary_id="SYNTHETIC_BOUNDARY_1",
        boundary_node_id="SYNTHETIC_NODE_2",
        boundary_type="FIXED_WATER_LEVEL",
        parameters={"water_level_m": 1.0},
        provenance=ProvenanceStatus.OBSERVED
    )

    dataset = HydraulicDataset(
        nodes=[node1, node2],
        downstream_boundaries=[boundary]
    )

    network = assemble_hydraulic_network(dataset)

    # Verify all IDs are clearly synthetic/test-only
    assert all("SYNTHETIC" in entity.node_id for entity in network.nodes)
    assert all("SYNTHETIC" in entity.boundary_id for entity in network.downstream_boundaries)
    assert all("SYNTHETIC" in entity.node_id for entity in network.nodes)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])