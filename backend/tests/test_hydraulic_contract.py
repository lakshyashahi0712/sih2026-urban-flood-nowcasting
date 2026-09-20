"""Tests for hydraulic data contracts."""

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
    HydraulicReadinessResult,
    validate_hydraulic_dataset,
)
from backend.app.domain.delhi.digital_twin.models import ProvenanceStatus


def test_canonical_provenancestatus_reused():
    """Test that the canonical ProvenanceStatus is reused."""
    # Ensure we're using the same enum from models.py
    pv = ProvenancedValue(
        value=1.5,
        provenance=ProvenanceStatus.OBSERVED,
        uncertainty=0.1
    )
    assert pv.provenance == ProvenanceStatus.OBSERVED
    assert pv.provenance.value == "OBSERVED"


def test_valid_node_model():
    """Test that a valid node model can be created."""
    node = HydraulicNode(
        node_id="N1",
        easting=ProvenancedValue(value=100.0, provenance=ProvenanceStatus.OBSERVED),
        northing=ProvenancedValue(value=200.0, provenance=ProvenanceStatus.OBSERVED),
        invert_elev_m=ProvenancedValue(value=5.0, provenance=ProvenanceStatus.OBSERVED),
        node_type="JUNCTION",
        upstream_connections=[],
        downstream_connections=[]
    )
    assert node.node_id == "N1"
    assert node.invert_elev_m.value == 5.0
    assert node.invert_elev_m.provenance == ProvenanceStatus.OBSERVED


def test_unknown_invert_blocks_readiness():
    """Test that UNKNOWN invert blocks readiness."""
    node = HydraulicNode(
        node_id="N1",
        easting=ProvenancedValue(value=100.0, provenance=ProvenanceStatus.OBSERVED),
        northing=ProvenancedValue(value=200.0, provenance=ProvenanceStatus.OBSERVED),
        invert_elev_m=ProvenancedValue(provenance=ProvenanceStatus.UNKNOWN),  # value is None
        node_type="JUNCTION",
        upstream_connections=[],
        downstream_connections=[]
    )

    dataset = HydraulicDataset(nodes=[node])
    result = validate_hydraulic_dataset(dataset)

    assert result.status == "BLOCKED"
    assert any("invert_elev_m missing or not deterministic" in msg for msg in result.missing_required_fields)


def test_observed_invert_qualifies():
    """Test that OBSERVED invert qualifies for readiness."""
    node = HydraulicNode(
        node_id="N1",
        easting=ProvenancedValue(value=100.0, provenance=ProvenanceStatus.OBSERVED),
        northing=ProvenancedValue(value=200.0, provenance=ProvenanceStatus.OBSERVED),
        invert_elev_m=ProvenancedValue(value=5.0, provenance=ProvenanceStatus.OBSERVED),
        node_type="JUNCTION",
        upstream_connections=[],
        downstream_connections=[]
    )

    dataset = HydraulicDataset(nodes=[node])
    result = validate_hydraulic_dataset(dataset)

    # Should be ready if we also add a downstream boundary
    boundary = DownstreamBoundary(
        boundary_id="B1",
        boundary_node_id="N1",
        boundary_type="FIXED_WATER_LEVEL",
        parameters={"water_level_m": 2.0},
        provenance=ProvenanceStatus.OBSERVED
    )
    dataset_with_boundary = HydraulicDataset(nodes=[node], downstream_boundaries=[boundary])
    result = validate_hydraulic_dataset(dataset_with_boundary)

    assert result.status == "READY"


def test_official_physical_geometry_qualifies():
    """Test that OFFICIAL physical geometry qualifies."""
    node = HydraulicNode(
        node_id="N1",
        easting=ProvenancedValue(value=100.0, provenance=ProvenanceStatus.OFFICIAL),
        northing=ProvenancedValue(value=200.0, provenance=ProvenanceStatus.OFFICIAL),
        invert_elev_m=ProvenancedValue(value=5.0, provenance=ProvenanceStatus.OFFICIAL),
        node_type="JUNCTION",
        upstream_connections=[],
        downstream_connections=[]
    )

    boundary = DownstreamBoundary(
        boundary_id="B1",
        boundary_node_id="N1",
        boundary_type="FIXED_WATER_LEVEL",
        parameters={"water_level_m": 2.0},
        provenance=ProvenanceStatus.OFFICIAL
    )
    dataset = HydraulicDataset(nodes=[node], downstream_boundaries=[boundary])
    result = validate_hydraulic_dataset(dataset)

    assert result.status == "READY"


def test_official_model_value_does_not_qualify():
    """Test that OFFICIAL_MODEL_VALUE does not qualify as deterministic physical geometry."""
    node = HydraulicNode(
        node_id="N1",
        easting=ProvenancedValue(value=100.0, provenance=ProvenanceStatus.OFFICIAL_MODEL_VALUE),
        northing=ProvenancedValue(value=200.0, provenance=ProvenanceStatus.OFFICIAL_MODEL_VALUE),
        invert_elev_m=ProvenancedValue(value=5.0, provenance=ProvenanceStatus.OFFICIAL_MODEL_VALUE),
        node_type="JUNCTION",
        upstream_connections=[],
        downstream_connections=[]
    )

    boundary = DownstreamBoundary(
        boundary_id="B1",
        boundary_node_id="N1",
        boundary_type="FIXED_WATER_LEVEL",
        parameters={"water_level_m": 2.0},
        provenance=ProvenanceStatus.OFFICIAL_MODEL_VALUE
    )
    dataset = HydraulicDataset(nodes=[node], downstream_boundaries=[boundary])
    result = validate_hydraulic_dataset(dataset)

    # Should be blocked because OFFICIAL_MODEL_VALUE is not deterministic for physical geometry
    assert result.status == "BLOCKED"
    assert any("invert_elev_m missing or not deterministic" in msg for msg in result.missing_required_fields)


def test_derived_geometry_does_not_qualify():
    """Test that DERIVED geometry does not qualify as deterministic physical geometry."""
    node = HydraulicNode(
        node_id="N1",
        easting=ProvenancedValue(value=100.0, provenance=ProvenanceStatus.DERIVED),
        northing=ProvenancedValue(value=200.0, provenance=ProvenanceStatus.DERIVED),
        invert_elev_m=ProvenancedValue(value=5.0, provenance=ProvenanceStatus.DERIVED),
        node_type="JUNCTION",
        upstream_connections=[],
        downstream_connections=[]
    )

    boundary = DownstreamBoundary(
        boundary_id="B1",
        boundary_node_id="N1",
        boundary_type="FIXED_WATER_LEVEL",
        parameters={"water_level_m": 2.0},
        provenance=ProvenanceStatus.DERIVED
    )
    dataset = HydraulicDataset(nodes=[node], downstream_boundaries=[boundary])
    result = validate_hydraulic_dataset(dataset)

    # Should be blocked because DERIVED is not deterministic for physical geometry
    assert result.status == "BLOCKED"
    assert any("invert_elev_m missing or not deterministic" in msg for msg in result.missing_required_fields)


def test_undefined_topology_reference_blocks_readiness():
    """Test that undefined topology reference blocks readiness."""
    node = HydraulicNode(
        node_id="N1",
        easting=ProvenancedValue(value=100.0, provenance=ProvenanceStatus.OBSERVED),
        northing=ProvenancedValue(value=200.0, provenance=ProvenanceStatus.OBSERVED),
        invert_elev_m=ProvenancedValue(value=5.0, provenance=ProvenanceStatus.OBSERVED),
        node_type="JUNCTION",
        upstream_connections=["N2"],  # N2 doesn't exist
        downstream_connections=[]
    )

    boundary = DownstreamBoundary(
        boundary_id="B1",
        boundary_node_id="N1",
        boundary_type="FIXED_WATER_LEVEL",
        parameters={"water_level_m": 2.0},
        provenance=ProvenanceStatus.OBSERVED
    )
    dataset = HydraulicDataset(nodes=[node], downstream_boundaries=[boundary])
    result = validate_hydraulic_dataset(dataset)

    assert result.status == "BLOCKED"
    assert any("upstream connection N2 not found" in msg for msg in result.unresolved_topology)


def test_missing_downstream_boundary_blocks_readiness():
    """Test that missing downstream boundary blocks readiness."""
    node = HydraulicNode(
        node_id="N1",
        easting=ProvenancedValue(value=100.0, provenance=ProvenanceStatus.OBSERVED),
        northing=ProvenancedValue(value=200.0, provenance=ProvenanceStatus.OBSERVED),
        invert_elev_m=ProvenancedValue(value=5.0, provenance=ProvenanceStatus.OBSERVED),
        node_type="JUNCTION",
        upstream_connections=[],
        downstream_connections=[]
    )

    # No downstream boundary
    dataset = HydraulicDataset(nodes=[node])
    result = validate_hydraulic_dataset(dataset)

    assert result.status == "BLOCKED"
    assert any("No downstream boundary defined" in msg for msg in result.unresolved_boundary_conditions)


def test_assumed_manning_n_does_not_itself_block_readiness():
    """Test that ASSUMED Manning n does not by itself block readiness."""
    node = HydraulicNode(
        node_id="N1",
        easting=ProvenancedValue(value=100.0, provenance=ProvenanceStatus.OBSERVED),
        northing=ProvenancedValue(value=200.0, provenance=ProvenanceStatus.OBSERVED),
        invert_elev_m=ProvenancedValue(value=5.0, provenance=ProvenanceStatus.OBSERVED),
        node_type="JUNCTION",
        upstream_connections=[],
        downstream_connections=[]
    )

    # Reach with ASSUMED Manning n
    reach = OpenChannelReach(
        reach_id="R1",
        upstream_node_id="N1",
        downstream_node_id="N1",  # Simplified for test - same node
        chainage_profile=[
            ChainagePoint(
                chainage=ProvenancedValue(value=0.0, provenance=ProvenanceStatus.OBSERVED),
                invert_elev_m=ProvenancedValue(value=5.0, provenance=ProvenanceStatus.OBSERVED)
            ),
            ChainagePoint(
                chainage=ProvenancedValue(value=10.0, provenance=ProvenanceStatus.OBSERVED),
                invert_elev_m=ProvenancedValue(value=4.9, provenance=ProvenanceStatus.OBSERVED)
            )
        ],
        geometry_representation="TABULATED",
        width_m=ProvenancedValue(value=5.0, provenance=ProvenanceStatus.OBSERVED),
        depth_m=ProvenancedValue(value=2.0, provenance=ProvenanceStatus.OBSERVED),
        slope_m_per_m=ProvenancedValue(value=0.005, provenance=ProvenanceStatus.OBSERVED),
        length_m=ProvenancedValue(value=10.0, provenance=ProvenanceStatus.OBSERVED),
        manning_n=ProvenancedValue(value=0.015, provenance=ProvenanceStatus.ASSUMED),  # ASSUMED Manning n
        structure_refs=[]
    )

    boundary = DownstreamBoundary(
        boundary_id="B1",
        boundary_node_id="N1",
        boundary_type="FIXED_WATER_LEVEL",
        parameters={"water_level_m": 2.0},
        provenance=ProvenanceStatus.OBSERVED
    )
    dataset = HydraulicDataset(
        nodes=[node],
        open_channel_reaches=[reach],
        downstream_boundaries=[boundary]
    )
    result = validate_hydraulic_dataset(dataset)

    # Should be READY because Manning n is a model parameter, not required to be deterministic for physical geometry
    assert result.status == "READY"


def test_unknown_remains_none_and_is_never_converted_to_zero():
    """Test that UNKNOWN remains None and is never converted to zero."""
    pv = ProvenancedValue(provenance=ProvenanceStatus.UNKNOWN)
    assert pv.value is None
    assert pv.provenance == ProvenanceStatus.UNKNOWN


def test_completely_synthetic_test_only_dataset_can_reach_ready():
    """Test that a completely synthetic TEST-ONLY dataset can reach READY."""
    # Create synthetic test data with OBSERVED provenance (simulating surveyed data)
    node1 = HydraulicNode(
        node_id="TEST_NODE_1",
        easting=ProvenancedValue(value=100000.0, provenance=ProvenanceStatus.OBSERVED),
        northing=ProvenancedValue(value=200000.0, provenance=ProvenanceStatus.OBSERVED),
        invert_elev_m=ProvenancedValue(value=10.0, provenance=ProvenanceStatus.OBSERVED),
        node_type="JUNCTION",
        upstream_connections=[],
        downstream_connections=["TEST_NODE_2"]
    )

    node2 = HydraulicNode(
        node_id="TEST_NODE_2",
        easting=ProvenancedValue(value=100010.0, provenance=ProvenanceStatus.OBSERVED),
        northing=ProvenancedValue(value=200000.0, provenance=ProvenanceStatus.OBSERVED),
        invert_elev_m=ProvenancedValue(value=9.5, provenance=ProvenanceStatus.OBSERVED),
        node_type="OUTFALL",
        upstream_connections=["TEST_NODE_1"],
        downstream_connections=[]
    )

    reach = OpenChannelReach(
        reach_id="TEST_REACH_1",
        upstream_node_id="TEST_NODE_1",
        downstream_node_id="TEST_NODE_2",
        chainage_profile=[
            ChainagePoint(
                chainage=ProvenancedValue(value=0.0, provenance=ProvenanceStatus.OBSERVED),
                invert_elev_m=ProvenancedValue(value=10.0, provenance=ProvenanceStatus.OBSERVED)
            ),
            ChainagePoint(
                chainage=ProvenancedValue(value=10.0, provenance=ProvenanceStatus.OBSERVED),
                invert_elev_m=ProvenancedValue(value=9.5, provenance=ProvenanceStatus.OBSERVED)
            )
        ],
        geometry_representation="TABULATED",
        width_m=ProvenancedValue(value=5.0, provenance=ProvenanceStatus.OBSERVED),
        depth_m=ProvenancedValue(value=2.0, provenance=ProvenanceStatus.OBSERVED),
        slope_m_per_m=ProvenancedValue(value=0.005, provenance=ProvenanceStatus.OBSERVED),
        length_m=ProvenancedValue(value=10.0, provenance=ProvenanceStatus.OBSERVED),
        manning_n=ProvenancedValue(value=0.015, provenance=ProvenanceStatus.OBSERVED),
        structure_refs=[]
    )

    boundary = DownstreamBoundary(
        boundary_id="TEST_BOUNDARY_1",
        boundary_node_id="TEST_NODE_2",
        boundary_type="FIXED_WATER_LEVEL",
        parameters={"water_level_m": 1.0},
        provenance=ProvenanceStatus.OBSERVED
    )

    # Explicitly label as TEST-ONLY in comments
    # This dataset contains only synthetic test values, not real Kushak values
    dataset = HydraulicDataset(
        nodes=[node1, node2],
        open_channel_reaches=[reach],
        downstream_boundaries=[boundary]
    )

    result = validate_hydraulic_dataset(dataset)

    # Should be READY with all deterministic physical geometry
    assert result.status == "READY"
    assert len(result.missing_required_fields) == 0
    assert len(result.invalid_fields) == 0
    assert len(result.provenance_violations) == 0
    assert len(result.unresolved_topology) == 0
    assert len(result.unresolved_geometry) == 0
    assert len(result.unresolved_boundary_conditions) == 0


def test_structure_unknown_inlet_invert_blocks():
    """Test that UNKNOWN inlet invert in structure blocks readiness."""
    struct = HydraulicStructure(
        structure_id="S1",
        structure_type="CULVERT",
        upstream_node_id="N1",
        downstream_node_id="N2",
        inlet_invert_elev_m=ProvenancedValue(provenance=ProvenanceStatus.UNKNOWN),  # value None
        outlet_invert_elev_m=ProvenancedValue(value=5.0, provenance=ProvenanceStatus.OBSERVED),
        structure_geometry={}
    )
    # Need nodes N1 and N2 with deterministic inverts for other checks
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
        node_id="N2",
        easting=ProvenancedValue(value=0.0, provenance=ProvenanceStatus.OBSERVED),
        northing=ProvenancedValue(value=0.0, provenance=ProvenanceStatus.OBSERVED),
        invert_elev_m=ProvenancedValue(value=9.5, provenance=ProvenanceStatus.OBSERVED),
        node_type="OUTFALL",
        upstream_connections=["N1"],
        downstream_connections=[]
    )
    # Downstream boundary needed for readiness (since we have a node as downstream)
    boundary = DownstreamBoundary(
        boundary_id="B1",
        boundary_node_id="N2",
        boundary_type="FIXED_WATER_LEVEL",
        parameters={"water_level_m": 2.0},
        provenance=ProvenanceStatus.OBSERVED
    )
    dataset = HydraulicDataset(
        nodes=[node1, node2],
        hydraulic_structures=[struct],
        downstream_boundaries=[boundary]
    )
    result = validate_hydraulic_dataset(dataset)
    assert result.status == "BLOCKED"
    assert any("inlet_invert_elev_m missing or not deterministic" in msg for msg in result.missing_required_fields)


def test_structure_unknown_outlet_invert_blocks():
    """Test that UNKNOWN outlet invert in structure blocks readiness."""
    struct = HydraulicStructure(
        structure_id="S1",
        structure_type="CULVERT",
        upstream_node_id="N1",
        downstream_node_id="N2",
        inlet_invert_elev_m=ProvenancedValue(value=5.0, provenance=ProvenanceStatus.OBSERVED),
        outlet_invert_elev_m=ProvenancedValue(provenance=ProvenanceStatus.UNKNOWN),  # value None
        structure_geometry={}
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
        easting=ProvenancedValue(value=0.0, provenance=ProvenanceStatus.OBSERVED),
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
        nodes=[node1, node2],
        hydraulic_structures=[struct],
        downstream_boundaries=[boundary]
    )
    result = validate_hydraulic_dataset(dataset)
    assert result.status == "BLOCKED"
    assert any("outlet_invert_elev_m missing or not deterministic" in msg for msg in result.missing_required_fields)


def test_structure_observed_inverts_pass():
    """Test that OBSERVED inlet/outlet inverts in structure pass those checks."""
    struct = HydraulicStructure(
        structure_id="S1",
        structure_type="CULVERT",
        upstream_node_id="N1",
        downstream_node_id="N2",
        inlet_invert_elev_m=ProvenancedValue(value=5.0, provenance=ProvenanceStatus.OBSERVED),
        outlet_invert_elev_m=ProvenancedValue(value=4.5, provenance=ProvenanceStatus.OBSERVED),
        structure_geometry={}
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
        easting=ProvenancedValue(value=0.0, provenance=ProvenanceStatus.OBSERVED),
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
        nodes=[node1, node2],
        hydraulic_structures=[struct],
        downstream_boundaries=[boundary]
    )
    result = validate_hydraulic_dataset(dataset)
    # Should be READY (assuming no other missing pieces)
    assert result.status == "READY"


def test_structure_official_model_value_inverts_do_not_qualify():
    """Test that OFFICIAL_MODEL_VALUE inverts in structure do NOT qualify as deterministic."""
    struct = HydraulicStructure(
        structure_id="S1",
        structure_type="CULVERT",
        upstream_node_id="N1",
        downstream_node_id="N2",
        inlet_invert_elev_m=ProvenancedValue(value=5.0, provenance=ProvenanceStatus.OFFICIAL_MODEL_VALUE),
        outlet_invert_elev_m=ProvenancedValue(value=4.5, provenance=ProvenanceStatus.OFFICIAL_MODEL_VALUE),
        structure_geometry={}
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
        easting=ProvenancedValue(value=0.0, provenance=ProvenanceStatus.OBSERVED),
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
        nodes=[node1, node2],
        hydraulic_structures=[struct],
        downstream_boundaries=[boundary]
    )
    result = validate_hydraulic_dataset(dataset)
    assert result.status == "BLOCKED"
    assert any("inlet_invert_elev_m missing or not deterministic" in msg for msg in result.missing_required_fields)
    assert any("outlet_invert_elev_m missing or not deterministic" in msg for msg in result.missing_required_fields)


def test_reach_nonexistent_cross_section_blocks():
    """Test that referencing a nonexistent cross-section blocks readiness."""
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
                chainage=ProvenancedValue(value=10.0, provenance=ProvenanceStatus.OBSERVED),
                invert_elev_m=ProvenancedValue(value=9.5, provenance=ProvenanceStatus.OBSERVED)
            )
        ],
        geometry_representation="TABULATED",
        width_m=ProvenancedValue(value=5.0, provenance=ProvenanceStatus.OBSERVED),
        depth_m=ProvenancedValue(value=2.0, provenance=ProvenanceStatus.OBSERVED),
        slope_m_per_m=ProvenancedValue(value=0.005, provenance=ProvenanceStatus.OBSERVED),
        length_m=ProvenancedValue(value=10.0, provenance=ProvenanceStatus.OBSERVED),
        manning_n=ProvenancedValue(value=0.015, provenance=ProvenanceStatus.OBSERVED),
        structure_refs=[],
        cross_section_refs=["XS_UNKNOWN"]  # This cross-section does not exist
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
        easting=ProvenancedValue(value=0.0, provenance=ProvenanceStatus.OBSERVED),
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
    # No cross-sections defined at all
    dataset = HydraulicDataset(
        nodes=[node1, node2],
        open_channel_reaches=[reach],
        downstream_boundaries=[boundary],
        cross_sections=[]
    )
    result = validate_hydraulic_dataset(dataset)
    assert result.status == "BLOCKED"
    assert any("cross-section reference XS_UNKNOWN not found" in msg for msg in result.unresolved_topology)


def test_reach_existing_cross_section_passes():
    """Test that referencing an existing cross-section passes the existence check."""
    # Define a cross-section
    xs = CrossSection(
        cross_section_id="XS_1",
        geometry_reference="some/path/to/data.csv",
        geometry_representation="IRREGULAR",
        provenance=ProvenanceStatus.OBSERVED
    )
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
                chainage=ProvenancedValue(value=10.0, provenance=ProvenanceStatus.OBSERVED),
                invert_elev_m=ProvenancedValue(value=9.5, provenance=ProvenanceStatus.OBSERVED)
            )
        ],
        geometry_representation="TABULATED",
        width_m=ProvenancedValue(value=5.0, provenance=ProvenanceStatus.OBSERVED),
        depth_m=ProvenancedValue(value=2.0, provenance=ProvenanceStatus.OBSERVED),
        slope_m_per_m=ProvenancedValue(value=0.005, provenance=ProvenanceStatus.OBSERVED),
        length_m=ProvenancedValue(value=10.0, provenance=ProvenanceStatus.OBSERVED),
        manning_n=ProvenancedValue(value=0.015, provenance=ProvenanceStatus.OBSERVED),
        structure_refs=[],
        cross_section_refs=["XS_1"]  # This exists
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
        easting=ProvenancedValue(value=0.0, provenance=ProvenanceStatus.OBSERVED),
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
        nodes=[node1, node2],
        open_channel_reaches=[reach],
        downstream_boundaries=[boundary],
        cross_sections=[xs]
    )
    result = validate_hydraulic_dataset(dataset)
    # Should be READY (assuming no other missing pieces)
    assert result.status == "READY"


def test_cwc_observation_alone_does_not_enable_calibrated_depth_claims():
    """Test that CWC/Yamuna WATER_LEVEL observation alone does NOT enable calibrated-depth-claim readiness."""
    # Create a dataset with hydraulic solver readiness true
    node1 = HydraulicNode(
        node_id="N1",
        easting=ProvenancedValue(value=100000.0, provenance=ProvenanceStatus.OBSERVED),
        northing=ProvenancedValue(value=200000.0, provenance=ProvenanceStatus.OBSERVED),
        invert_elev_m=ProvenancedValue(value=10.0, provenance=ProvenanceStatus.OBSERVED),
        node_type="JUNCTION",
        upstream_connections=[],
        downstream_connections=["N2"]
    )

    node2 = HydraulicNode(
        node_id="N2",
        easting=ProvenancedValue(value=100010.0, provenance=ProvenanceStatus.OBSERVED),
        northing=ProvenancedValue(value=200000.0, provenance=ProvenanceStatus.OBSERVED),
        invert_elev_m=ProvenancedValue(value=9.5, provenance=ProvenanceStatus.OBSERVED),
        node_type="OUTFALL",
        upstream_connections=["N1"],
        downstream_connections=[]
    )

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
                chainage=ProvenancedValue(value=10.0, provenance=ProvenanceStatus.OBSERVED),
                invert_elev_m=ProvenancedValue(value=9.5, provenance=ProvenanceStatus.OBSERVED)
            )
        ],
        geometry_representation="TABULATED",
        width_m=ProvenancedValue(value=5.0, provenance=ProvenanceStatus.OBSERVED),
        depth_m=ProvenancedValue(value=2.0, provenance=ProvenanceStatus.OBSERVED),
        slope_m_per_m=ProvenancedValue(value=0.005, provenance=ProvenanceStatus.OBSERVED),
        length_m=ProvenancedValue(value=10.0, provenance=ProvenanceStatus.OBSERVED),
        manning_n=ProvenancedValue(value=0.015, provenance=ProvenanceStatus.OBSERVED),
        structure_refs=[]
    )

    xs = CrossSection(
        cross_section_id="XS_1",
        geometry_reference="some/path/to/data.csv",
        geometry_representation="IRREGULAR",
        provenance=ProvenanceStatus.OBSERVED
    )

    boundary = DownstreamBoundary(
        boundary_id="B1",
        boundary_node_id="N2",
        boundary_type="FIXED_WATER_LEVEL",
        parameters={"water_level_m": 1.0},
        provenance=ProvenanceStatus.OBSERVED
    )

    # Add ONLY a CWC downstream river stage observation
    cwc_obs = HydraulicObservation(
        observation_id="OBS_CWC_1",
        event_id="EVT_1",
        observation_type="WATER_LEVEL",
        timestamp=datetime(2023, 1, 1, 12, 0, 0),
        location_ref="CWC_DELHI_RAILWAY_BRIDGE",  # CWC observation
        measured_value=ProvenancedValue(value=1.5, provenance=ProvenanceStatus.OBSERVED),
        units="m",
        provenance=ProvenanceStatus.OBSERVED
    )

    dataset = HydraulicDataset(
        nodes=[node1, node2],
        open_channel_reaches=[reach],
        downstream_boundaries=[boundary],
        cross_sections=[xs],
        hydraulic_observations=[cwc_obs]
    )

    result = validate_hydraulic_dataset(dataset)

    # Should have hydraulic solver readiness true (topology + deterministic geometry + boundary)
    assert result.ready_for_topology == True
    assert result.ready_for_hydraulic_solve == True

    # BUT calibrated depth claims should be FALSE because only CWC observation is present
    assert result.ready_for_calibrated_depth_claims == False

    # Status should still be READY because we only care about the flags
    assert result.status == "READY"


def test_kushak_water_level_observation_enables_calibrated_depth_claims():
    """Test that a suitable observed Kushak flood-depth/water-level observation can satisfy calibration evidence."""
    # Create a dataset with hydraulic solver readiness true
    node1 = HydraulicNode(
        node_id="N1",
        easting=ProvenancedValue(value=100000.0, provenance=ProvenanceStatus.OBSERVED),
        northing=ProvenancedValue(value=200000.0, provenance=ProvenanceStatus.OBSERVED),
        invert_elev_m=ProvenancedValue(value=10.0, provenance=ProvenanceStatus.OBSERVED),
        node_type="JUNCTION",
        upstream_connections=[],
        downstream_connections=["N2"]
    )

    node2 = HydraulicNode(
        node_id="N2",
        easting=ProvenancedValue(value=100010.0, provenance=ProvenanceStatus.OBSERVED),
        northing=ProvenancedValue(value=200000.0, provenance=ProvenanceStatus.OBSERVED),
        invert_elev_m=ProvenancedValue(value=9.5, provenance=ProvenanceStatus.OBSERVED),
        node_type="OUTFALL",
        upstream_connections=["N1"],
        downstream_connections=[]
    )

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
                chainage=ProvenancedValue(value=10.0, provenance=ProvenanceStatus.OBSERVED),
                invert_elev_m=ProvenancedValue(value=9.5, provenance=ProvenanceStatus.OBSERVED)
            )
        ],
        geometry_representation="TABULATED",
        width_m=ProvenancedValue(value=5.0, provenance=ProvenanceStatus.OBSERVED),
        depth_m=ProvenancedValue(value=2.0, provenance=ProvenanceStatus.OBSERVED),
        slope_m_per_m=ProvenancedValue(value=0.005, provenance=ProvenanceStatus.OBSERVED),
        length_m=ProvenancedValue(value=10.0, provenance=ProvenanceStatus.OBSERVED),
        manning_n=ProvenancedValue(value=0.015, provenance=ProvenanceStatus.OBSERVED),
        structure_refs=[]
    )

    xs = CrossSection(
        cross_section_id="XS_1",
        geometry_reference="some/path/to/data.csv",
        geometry_representation="IRREGULAR",
        provenance=ProvenanceStatus.OBSERVED
    )

    boundary = DownstreamBoundary(
        boundary_id="B1",
        boundary_node_id="N2",
        boundary_type="FIXED_WATER_LEVEL",
        parameters={"water_level_m": 1.0},
        provenance=ProvenanceStatus.OBSERVED
    )

    # Add a Kushak water level observation (not CWC)
    kushak_obs = HydraulicObservation(
        observation_id="OBS_KUSHAK_1",
        event_id="EVT_1",
        observation_type="WATER_LEVEL",
        timestamp=datetime(2023, 1, 1, 12, 0, 0),
        location_ref="KUSHAK_NODE_1",  # Kushak location, not CWC
        measured_value=ProvenancedValue(value=1.5, provenance=ProvenanceStatus.OBSERVED),
        units="m",
        provenance=ProvenanceStatus.OBSERVED
    )

    dataset = HydraulicDataset(
        nodes=[node1, node2],
        open_channel_reaches=[reach],
        downstream_boundaries=[boundary],
        cross_sections=[xs],
        hydraulic_observations=[kushak_obs]
    )

    result = validate_hydraulic_dataset(dataset)

    # Should have hydraulic solver readiness true
    assert result.ready_for_topology == True
    assert result.ready_for_hydraulic_solve == True

    # AND calibrated depth claims should be TRUE because we have a suitable Kushak observation
    assert result.ready_for_calibrated_depth_claims == True

    assert result.status == "READY"


def test_calibration_requires_observed_or_official_provenance():
    """Test that OBSERVED/OFFICIAL provenance is still required for calibration evidence."""
    # Create a dataset with hydraulic solver readiness true
    node1 = HydraulicNode(
        node_id="N1",
        easting=ProvenancedValue(value=100000.0, provenance=ProvenanceStatus.OBSERVED),
        northing=ProvenancedValue(value=200000.0, provenance=ProvenanceStatus.OBSERVED),
        invert_elev_m=ProvenancedValue(value=10.0, provenance=ProvenanceStatus.OBSERVED),
        node_type="JUNCTION",
        upstream_connections=[],
        downstream_connections=["N2"]
    )

    node2 = HydraulicNode(
        node_id="N2",
        easting=ProvenancedValue(value=100010.0, provenance=ProvenanceStatus.OBSERVED),
        northing=ProvenancedValue(value=200000.0, provenance=ProvenanceStatus.OBSERVED),
        invert_elev_m=ProvenancedValue(value=9.5, provenance=ProvenanceStatus.OBSERVED),
        node_type="OUTFALL",
        upstream_connections=["N1"],
        downstream_connections=[]
    )

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
                chainage=ProvenancedValue(value=10.0, provenance=ProvenanceStatus.OBSERVED),
                invert_elev_m=ProvenancedValue(value=9.5, provenance=ProvenanceStatus.OBSERVED)
            )
        ],
        geometry_representation="TABULATED",
        width_m=ProvenancedValue(value=5.0, provenance=ProvenanceStatus.OBSERVED),
        depth_m=ProvenancedValue(value=2.0, provenance=ProvenanceStatus.OBSERVED),
        slope_m_per_m=ProvenancedValue(value=0.005, provenance=ProvenanceStatus.OBSERVED),
        length_m=ProvenancedValue(value=10.0, provenance=ProvenanceStatus.OBSERVED),
        manning_n=ProvenancedValue(value=0.015, provenance=ProvenanceStatus.OBSERVED),
        structure_refs=[]
    )

    xs = CrossSection(
        cross_section_id="XS_1",
        geometry_reference="some/path/to/data.csv",
        geometry_representation="IRREGULAR",
        provenance=ProvenanceStatus.OBSERVED
    )

    boundary = DownstreamBoundary(
        boundary_id="B1",
        boundary_node_id="N2",
        boundary_type="FIXED_WATER_LEVEL",
        parameters={"water_level_m": 1.0},
        provenance=ProvenanceStatus.OBSERVED
    )

    # Add a Kushak water level observation with ASSUMED provenance (not sufficient)
    kushak_obs_assumed = HydraulicObservation(
        observation_id="OBS_KUSHAK_ASSUMED",
        event_id="EVT_1",
        observation_type="WATER_LEVEL",
        timestamp=datetime(2023, 1, 1, 12, 0, 0),
        location_ref="KUSHAK_NODE_1",
        measured_value=ProvenancedValue(value=1.5, provenance=ProvenanceStatus.ASSUMED),  # Not OBSERVED/OFFICIAL
        units="m",
        provenance=ProvenanceStatus.ASSUMED
    )

    dataset = HydraulicDataset(
        nodes=[node1, node2],
        open_channel_reaches=[reach],
        downstream_boundaries=[boundary],
        cross_sections=[xs],
        hydraulic_observations=[kushak_obs_assumed]
    )

    result = validate_hydraulic_dataset(dataset)

    # Should have hydraulic solver readiness true
    assert result.ready_for_topology == True
    assert result.ready_for_hydraulic_solve == True

    # BUT calibrated depth claims should be FALSE because provenance is not OBSERVED/OFFICIAL
    assert result.ready_for_calibrated_depth_claims == False

    assert result.status == "READY"


def test_no_synthetic_calibration_data_created():
    """Test that no synthetic calibration data is created - we only validate existing observations."""
    # Create a dataset with hydraulic solver readiness true but NO observations
    node1 = HydraulicNode(
        node_id="N1",
        easting=ProvenancedValue(value=100000.0, provenance=ProvenanceStatus.OBSERVED),
        northing=ProvenancedValue(value=200000.0, provenance=ProvenanceStatus.OBSERVED),
        invert_elev_m=ProvenancedValue(value=10.0, provenance=ProvenanceStatus.OBSERVED),
        node_type="JUNCTION",
        upstream_connections=[],
        downstream_connections=["N2"]
    )

    node2 = HydraulicNode(
        node_id="N2",
        easting=ProvenancedValue(value=100010.0, provenance=ProvenanceStatus.OBSERVED),
        northing=ProvenancedValue(value=200000.0, provenance=ProvenanceStatus.OBSERVED),
        invert_elev_m=ProvenancedValue(value=9.5, provenance=ProvenanceStatus.OBSERVED),
        node_type="OUTFALL",
        upstream_connections=["N1"],
        downstream_connections=[]
    )

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
                chainage=ProvenancedValue(value=10.0, provenance=ProvenanceStatus.OBSERVED),
                invert_elev_m=ProvenancedValue(value=9.5, provenance=ProvenanceStatus.OBSERVED)
            )
        ],
        geometry_representation="TABULATED",
        width_m=ProvenancedValue(value=5.0, provenance=ProvenanceStatus.OBSERVED),
        depth_m=ProvenancedValue(value=2.0, provenance=ProvenanceStatus.OBSERVED),
        slope_m_per_m=ProvenancedValue(value=0.005, provenance=ProvenanceStatus.OBSERVED),
        length_m=ProvenancedValue(value=10.0, provenance=ProvenanceStatus.OBSERVED),
        manning_n=ProvenancedValue(value=0.015, provenance=ProvenanceStatus.OBSERVED),
        structure_refs=[]
    )

    xs = CrossSection(
        cross_section_id="XS_1",
        geometry_reference="some/path/to/data.csv",
        geometry_representation="IRREGULAR",
        provenance=ProvenanceStatus.OBSERVED
    )

    boundary = DownstreamBoundary(
        boundary_id="B1",
        boundary_node_id="N2",
        boundary_type="FIXED_WATER_LEVEL",
        parameters={"water_level_m": 1.0},
        provenance=ProvenanceStatus.OBSERVED
    )

    # NO observations at all
    dataset = HydraulicDataset(
        nodes=[node1, node2],
        open_channel_reaches=[reach],
        downstream_boundaries=[boundary],
        cross_sections=[xs],
        hydraulic_observations=[]  # Empty observations list
    )

    result = validate_hydraulic_dataset(dataset)

    # Should have hydraulic solver readiness true
    assert result.ready_for_topology == True
    assert result.ready_for_hydraulic_solve == True

    # AND calibrated depth claims should be FALSE because no observations exist
    assert result.ready_for_calibrated_depth_claims == False

    assert result.status == "READY"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])