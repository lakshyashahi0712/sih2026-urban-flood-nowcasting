"""Hydraulic network assembly for Phase 3D-3.

Assembles a validated hydraulic network graph from a HydraulicDataset.
No hydraulic calculations are performed.
"""

from __future__ import annotations

from typing import List, Dict, Set, Optional
from dataclasses import dataclass, field

from backend.app.domain.delhi.digital_twin.hydraulic_contract import (
    HydraulicDataset,
    HydraulicReadinessResult,
    validate_hydraulic_dataset,
    HydraulicNode,
    OpenChannelReach,
    CoveredConduit,
    HydraulicStructure,
    CrossSection,
    InflowAttachment,
    DownstreamBoundary,
    HydraulicObservation,
    ProvenancedValue,
)
from backend.app.domain.delhi.digital_twin.models import ProvenanceStatus


class HydraulicNetworkAssemblyError(Exception):
    """Raised when hydraulic network assembly fails due to validation issues."""
    pass


@dataclass
class HydraulicNetwork:
    """Container for assembled hydraulic network entities.

    This is a simple container that holds the entities from the dataset
    after validation. No additional geometry or hydraulic properties are
    computed.
    """
    nodes: List[HydraulicNode] = field(default_factory=list)
    open_channel_reaches: List[OpenChannelReach] = field(default_factory=list)
    covered_conduits: List[CoveredConduit] = field(default_factory=list)
    hydraulic_structures: List[HydraulicStructure] = field(default_factory=list)
    cross_sections: List[CrossSection] = field(default_factory=list)
    inflow_attachments: List[InflowAttachment] = field(default_factory=list)
    downstream_boundaries: List[DownstreamBoundary] = field(default_factory=list)
    hydraulic_observations: List[HydraulicObservation] = field(default_factory=list)


def _check_duplicate_ids(
    items: List,
    id_attr: str,
    entity_type: str
) -> Optional[str]:
    """Check for duplicate IDs in a list of items.

    Returns an error message if duplicates are found, otherwise None.
    """
    seen: Set[str] = set()
    duplicates: Set[str] = set()
    for item in items:
        item_id = getattr(item, id_attr)
        if item_id in seen:
            duplicates.add(item_id)
        else:
            seen.add(item_id)

    if duplicates:
        return f"Duplicate {entity_type} IDs found: {', '.join(sorted(duplicates))}"
    return None


def assemble_hydraulic_network(dataset: HydraulicDataset) -> HydraulicNetwork:
    """Assemble a hydraulic network from a dataset after validation.

    Args:
        dataset: The HydraulicDataset to assemble.

    Returns:
        A HydraulicNetwork instance containing the assembled entities.

    Raises:
        HydraulicNetworkAssemblyError: If the dataset has duplicate IDs,
            has missing references, or has no downstream boundary defined.
    """
    # Step 1: Check for duplicate IDs in each collection
    duplicate_checks = [
        (dataset.nodes, "node_id", "node"),
        (dataset.open_channel_reaches, "reach_id", "reach"),
        (dataset.covered_conduits, "conduit_id", "conduit"),
        (dataset.hydraulic_structures, "structure_id", "structure"),
        (dataset.cross_sections, "cross_section_id", "cross-section"),
        (dataset.inflow_attachments, "inflow_id", "inflow attachment"),
        (dataset.downstream_boundaries, "boundary_id", "downstream boundary"),
    ]

    for items, id_attr, entity_type in duplicate_checks:
        duplicate_msg = _check_duplicate_ids(items, id_attr, entity_type)
        if duplicate_msg:
            raise HydraulicNetworkAssemblyError(duplicate_msg)

    # Step 2: Validate the dataset for deterministic readiness
    readiness_result = validate_hydraulic_dataset(dataset)
    if readiness_result.status != "READY":
        # Handle specific error cases as expected by tests
        # Check for unresolved references (topology) first - should show as "Unresolved references in dataset"
        if readiness_result.unresolved_topology:
            raise HydraulicNetworkAssemblyError(
                f"Unresolved references in dataset: {'; '.join(readiness_result.unresolved_topology)}"
            )

        # Check for missing downstream boundary - should show as "Dataset not ready for assembly"
        # with the specific message included
        if (readiness_result.unresolved_boundary_conditions and
            any("No downstream boundary defined" in cond for cond in readiness_result.unresolved_boundary_conditions)):
            raise HydraulicNetworkAssemblyError(
                f"Dataset not ready for assembly: No downstream boundary defined"
            )

        # For other validation failures (like UNKNOWN physical geometry), use detailed message
        raise HydraulicNetworkAssemblyError(
            f"Dataset not ready for assembly: {readiness_result.status}. "
            f"Details: missing_required={readiness_result.missing_required_fields}, "
            f"invalid_fields={readiness_result.invalid_fields}, "
            f"provenance_violations={readiness_result.provenance_violations}, "
            f"unresolved_topology={readiness_result.unresolved_topology}, "
            f"unresolved_geometry={readiness_result.unresolved_geometry}, "
            f"unresolved_boundary_conditions={readiness_result.unresolved_boundary_conditions}"
        )

    # Step 3: If all checks pass, return the assembled network
    return HydraulicNetwork(
        nodes=list(dataset.nodes),
        open_channel_reaches=list(dataset.open_channel_reaches),
        covered_conduits=list(dataset.covered_conduits),
        hydraulic_structures=list(dataset.hydraulic_structures),
        cross_sections=list(dataset.cross_sections),
        inflow_attachments=list(dataset.inflow_attachments),
        downstream_boundaries=list(dataset.downstream_boundaries),
        hydraulic_observations=list(dataset.hydraulic_observations),
    )