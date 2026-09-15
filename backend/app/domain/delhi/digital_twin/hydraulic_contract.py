"""Hydraulic data contracts for Phase 3D-2.

Data contracts only; no computational logic. Unknown values remain None
with UNKNOWN provenance and are never fabricated or defaulted.
"""

from __future__ import annotations

from typing import List, Optional, Union, Dict, Any
from datetime import datetime

from pydantic import BaseModel, Field, validator

from .models import ProvenanceStatus


class ProvenancedValue(BaseModel):
    """A value with provenance and uncertainty tracking."""
    value: Optional[Union[float, int, str]] = None
    provenance: ProvenanceStatus = ProvenanceStatus.UNKNOWN
    uncertainty: Optional[float] = None
    notes: Optional[str] = None

    @validator('value')
    def value_allow_none(cls, v):
        # Explicitly allow None to preserve UNKNOWN values
        return v


class HydraulicNode(BaseModel):
    """A node in the hydraulic network (e.g., junction, outfall)."""
    node_id: str
    easting: ProvenancedValue
    northing: ProvenancedValue
    invert_elev_m: ProvenancedValue
    node_type: str  # e.g., JUNCTION, OUTFALL, INLET
    upstream_connections: List[str] = Field(default_factory=list)
    downstream_connections: List[str] = Field(default_factory=list)


class ChainagePoint(BaseModel):
    """A point along a chainage with elevation."""
    chainage: ProvenancedValue
    invert_elev_m: ProvenancedValue


class OpenChannelReach(BaseModel):
    """An open channel reach between two nodes."""
    reach_id: str
    upstream_node_id: str
    downstream_node_id: str
    chainage_profile: List[ChainagePoint] = Field(default_factory=list)
    cross_section_refs: List[str] = Field(default_factory=list)
    geometry_representation: str  # e.g., IRREGULAR, TABULATED
    width_m: ProvenancedValue = Field(default_factory=ProvenancedValue)
    depth_m: ProvenancedValue = Field(default_factory=ProvenancedValue)
    slope_m_per_m: ProvenancedValue = Field(default_factory=ProvenancedValue)
    length_m: ProvenancedValue = Field(default_factory=ProvenancedValue)
    manning_n: ProvenancedValue
    structure_refs: List[str] = Field(default_factory=list)


class CoveredConduit(BaseModel):
    """A covered conduit (e.g., pipe, box culvert) between two nodes."""
    conduit_id: str
    upstream_node_id: str
    downstream_node_id: str
    invert_profile: List[ChainagePoint] = Field(default_factory=list)
    clear_width_m: ProvenancedValue
    clear_height_m: ProvenancedValue
    length_m: ProvenancedValue = Field(default_factory=ProvenancedValue)
    number_of_cells: int = 1
    soffit_elev_m: ProvenancedValue
    material: str  # e.g., CONCRETE, PVC, STEEL
    manning_n: ProvenancedValue
    structure_refs: List[str] = Field(default_factory=list)


class HydraulicStructure(BaseModel):
    """A hydraulic structure (e.g., culvert, bridge, junction chamber)."""
    structure_id: str
    structure_type: str  # CULVERT, BRIDGE, COVERED_TRANSITION, JUNCTION_CHAMBER, OTHER
    upstream_node_id: str
    downstream_node_id: str
    inlet_invert_elev_m: ProvenancedValue
    outlet_invert_elev_m: ProvenancedValue
    structure_geometry: Dict[str, Any] = Field(default_factory=dict)
    # Note: structure_geometry is a generic parameter object for structure-specific dimensions


class InflowAttachment(BaseModel):
    """Spatial attachment of an inflow to a node or reach."""
    inflow_id: str
    source_subcatchment_id: str
    attachment_node_id: Optional[str] = None
    attachment_reach_id: Optional[str] = None
    invert_elev_at_attachment_m: ProvenancedValue

    @validator('attachment_reach_id')
    def check_attachment(cls, v, values):
        # Ensure either node or reach attachment is specified, but not both
        attachment_node_id = values.get('attachment_node_id')
        if v is None and attachment_node_id is None:
            raise ValueError('Either attachment_node_id or attachment_reach_id must be specified')
        if v is not None and attachment_node_id is not None:
            raise ValueError('Cannot specify both attachment_node_id and attachment_reach_id')
        return v


class DownstreamBoundary(BaseModel):
    """Downstream boundary condition at a node."""
    boundary_id: str
    boundary_node_id: str
    boundary_type: str  # e.g., FIXED_WATER_LEVEL, FREE_OUTFALL, RATING_CURVE
    parameters: Dict[str, Any] = Field(default_factory=dict)
    outlet_geometry_ref: Optional[str] = None
    provenance: ProvenanceStatus = ProvenanceStatus.UNKNOWN
    uncertainty: Optional[float] = None
    notes: Optional[str] = None


class CrossSection(BaseModel):
    """A surveyed or modeled cross-section for hydraulic characterization."""
    cross_section_id: str
    geometry_reference: str  # Reference to actual geometry data (file, table, etc.)
    geometry_representation: str  # e.g., IRREGULAR, TABULATED, POINTS
    provenance: ProvenanceStatus = ProvenanceStatus.UNKNOWN
    uncertainty: Optional[float] = None
    notes: Optional[str] = None


class HydraulicObservation(BaseModel):
    """An observation of hydraulic state (e.g., water level, flow)."""
    observation_id: str
    event_id: str
    observation_type: str  # e.g., WATER_LEVEL, FLOW_VELOCITY
    timestamp: datetime
    location_ref: str  # References node_id, reach_id, or structure_id
    measured_value: ProvenancedValue
    units: str
    provenance: ProvenanceStatus = ProvenanceStatus.UNKNOWN
    uncertainty: Optional[float] = None
    notes: Optional[str] = None


class HydraulicDataset(BaseModel):
    """Container for all hydraulic domain entities."""
    nodes: List[HydraulicNode] = Field(default_factory=list)
    chainage_points: List[ChainagePoint] = Field(default_factory=list)
    open_channel_reaches: List[OpenChannelReach] = Field(default_factory=list)
    covered_conduits: List[CoveredConduit] = Field(default_factory=list)
    hydraulic_structures: List[HydraulicStructure] = Field(default_factory=list)
    inflow_attachments: List[InflowAttachment] = Field(default_factory=list)
    downstream_boundaries: List[DownstreamBoundary] = Field(default_factory=list)
    cross_sections: List[CrossSection] = Field(default_factory=list)
    hydraulic_observations: List[HydraulicObservation] = Field(default_factory=list)


class HydraulicReadinessResult(BaseModel):
    """Result of hydraulic dataset readiness validation."""
    status: str  # READY | BLOCKED
    ready_for_topology: bool = False
    ready_for_hydraulic_solve: bool = False
    ready_for_calibrated_depth_claims: bool = False
    missing_required_fields: List[str] = Field(default_factory=list)
    invalid_fields: List[str] = Field(default_factory=list)
    provenance_violations: List[str] = Field(default_factory=list)
    unresolved_topology: List[str] = Field(default_factory=list)
    unresolved_geometry: List[str] = Field(default_factory=list)
    unresolved_boundary_conditions: List[str] = Field(default_factory=list)
    provenance_summary: Dict[str, int] = Field(default_factory=dict)


def validate_hydraulic_dataset(dataset: HydraulicDataset) -> HydraulicReadinessResult:
    """Validate hydraulic dataset for deterministic readiness.

    Returns:
        HydraulicReadinessResult with status and details.
    """
    missing_required = []
    invalid_fields = []
    provenance_violations = []
    unresolved_topology = []
    unresolved_geometry = []
    unresolved_boundary_conditions = []

    # Helper to check if a ProvenancedValue is deterministic for physical geometry
    def is_deterministic_pv(pv: ProvenancedValue) -> bool:
        if pv.value is None:
            return False
        return pv.provenance in (ProvenanceStatus.OBSERVED, ProvenanceStatus.OFFICIAL)

    # Build lookup sets for existence checks
    node_ids = {node.node_id for node in dataset.nodes}
    structure_ids = {struct.structure_id for struct in dataset.hydraulic_structures}
    reach_ids = {reach.reach_id for reach in dataset.open_channel_reaches}
    cross_section_ids = {xs.cross_section_id for xs in dataset.cross_sections}

    # 1. Check nodes
    for node in dataset.nodes:
        # Check invert_elev_m is deterministic
        if not is_deterministic_pv(node.invert_elev_m):
            missing_required.append(f"Node {node.node_id}: invert_elev_m missing or not deterministic")
        # Easting/Northing must be deterministic for spatial topology
        if not is_deterministic_pv(node.easting):
            missing_required.append(f"Node {node.node_id}: easting missing or not deterministic")
        if not is_deterministic_pv(node.northing):
            missing_required.append(f"Node {node.node_id}: northing missing or not deterministic")
        # Check connections refer to existing nodes
        for conn in node.upstream_connections:
            if conn not in node_ids:
                unresolved_topology.append(f"Node {node.node_id}: upstream connection {conn} not found")
        for conn in node.downstream_connections:
            if conn not in node_ids:
                unresolved_topology.append(f"Node {node.node_id}: downstream connection {conn} not found")

    # 2. Check open channel reaches
    for reach in dataset.open_channel_reaches:
        # Check upstream/downstream nodes exist
        if reach.upstream_node_id not in node_ids:
            unresolved_topology.append(f"Reach {reach.reach_id}: upstream node {reach.upstream_node_id} not found")
        if reach.downstream_node_id not in node_ids:
            unresolved_topology.append(f"Reach {reach.reach_id}: downstream node {reach.downstream_node_id} not found")
        # Check physical geometry is deterministic
        if not is_deterministic_pv(reach.width_m):
            missing_required.append(f"Reach {reach.reach_id}: width_m missing or not deterministic")
        if not is_deterministic_pv(reach.depth_m):
            missing_required.append(f"Reach {reach.reach_id}: depth_m missing or not deterministic")
        if not is_deterministic_pv(reach.slope_m_per_m):
            missing_required.append(f"Reach {reach.reach_id}: slope_m_per_m missing or not deterministic")
        if not is_deterministic_pv(reach.length_m):
            missing_required.append(f"Reach {reach.reach_id}: length_m missing or not deterministic")
        # Check chainage points have deterministic invert_elev_m
        for i, point in enumerate(reach.chainage_profile):
            if not is_deterministic_pv(point.invert_elev_m):
                missing_required.append(f"Reach {reach.reach_id}: chainage point {i} invert_elev_m missing or not deterministic")
        # Check structure refs exist
        for struct_ref in reach.structure_refs:
            if struct_ref not in structure_ids:
                unresolved_topology.append(f"Reach {reach.reach_id}: structure reference {struct_ref} not found")
        # Check cross-section refs exist
        for xs_ref in reach.cross_section_refs:
            if xs_ref not in cross_section_ids:
                unresolved_topology.append(f"Reach {reach.reach_id}: cross-section reference {xs_ref} not found")
        # Manning n is a model parameter - check value exists even if non-deterministic
        if reach.manning_n.value is None:
            missing_required.append(f"Reach {reach.reach_id}: manning_n value is missing")

    # 3. Check covered conduits
    for conduit in dataset.covered_conduits:
        # Check upstream/downstream nodes exist
        if conduit.upstream_node_id not in node_ids:
            unresolved_topology.append(f"Conduit {conduit.conduit_id}: upstream node {conduit.upstream_node_id} not found")
        if conduit.downstream_node_id not in node_ids:
            unresolved_topology.append(f"Conduit {conduit.conduit_id}: downstream node {conduit.downstream_node_id} not found")
        # Check physical geometry is deterministic
        if not is_deterministic_pv(conduit.clear_width_m):
            missing_required.append(f"Conduit {conduit.conduit_id}: clear_width_m missing or not deterministic")
        if not is_deterministic_pv(conduit.clear_height_m):
            missing_required.append(f"Conduit {conduit.conduit_id}: clear_height_m missing or not deterministic")
        if not is_deterministic_pv(conduit.soffit_elev_m):
            missing_required.append(f"Conduit {conduit.conduit_id}: soffit_elev_m missing or not deterministic")
        if not is_deterministic_pv(conduit.length_m):
            missing_required.append(f"Conduit {conduit.conduit_id}: length_m missing or not deterministic")
        # Check invert profile points have deterministic invert_elev_m
        for i, point in enumerate(conduit.invert_profile):
            if not is_deterministic_pv(point.invert_elev_m):
                missing_required.append(f"Conduit {conduit.conduit_id}: invert profile point {i} invert_elev_m missing or not deterministic")
        # Check number of cells is positive integer
        if conduit.number_of_cells < 1:
            invalid_fields.append(f"Conduit {conduit.conduit_id}: number_of_cells must be >= 1")
        # Manning n is a model parameter - check value exists even if non-deterministic
        if conduit.manning_n.value is None:
            missing_required.append(f"Conduit {conduit.conduit_id}: manning_n value is missing")
        # Check structure refs exist
        for struct_ref in conduit.structure_refs:
            if struct_ref not in structure_ids:
                unresolved_topology.append(f"Conduit {conduit.conduit_id}: structure reference {struct_ref} not found")

    # 4. Check hydraulic structures
    for struct in dataset.hydraulic_structures:
        # Check upstream/downstream nodes exist
        if struct.upstream_node_id not in node_ids:
            unresolved_topology.append(f"Structure {struct.structure_id}: upstream node {struct.upstream_node_id} not found")
        if struct.downstream_node_id not in node_ids:
            unresolved_topology.append(f"Structure {struct.structure_id}: downstream node {struct.downstream_node_id} not found")
        # Check structure inlets/outlets are deterministic (physical geometry)
        if not is_deterministic_pv(struct.inlet_invert_elev_m):
            missing_required.append(f"Structure {struct.structure_id}: inlet_invert_elev_m missing or not deterministic")
        if not is_deterministic_pv(struct.outlet_invert_elev_m):
            missing_required.append(f"Structure {struct.structure_id}: outlet_invert_elev_m missing or not deterministic")
        # Structure geometry is generic - no provenance check required

    # 5. Check inflow attachments
    for attachment in dataset.inflow_attachments:
        # Check attachment refers to node or reach
        if attachment.attachment_node_id:
            if attachment.attachment_node_id not in node_ids:
                unresolved_topology.append(f"InflowAttachment {attachment.inflow_id}: attachment node {attachment.attachment_node_id} not found")
        if attachment.attachment_reach_id:
            if attachment.attachment_reach_id not in reach_ids:
                unresolved_topology.append(f"InflowAttachment {attachment.inflow_id}: attachment reach {attachment.attachment_reach_id} not found")
        # Check invert elevation at attachment is deterministic
        if not is_deterministic_pv(attachment.invert_elev_at_attachment_m):
            missing_required.append(f"InflowAttachment {attachment.inflow_id}: invert_elev_at_attachment_m missing or not deterministic")

    # 6. Check downstream boundaries
    if not dataset.downstream_boundaries:
        unresolved_boundary_conditions.append("No downstream boundary defined")
    else:
        for boundary in dataset.downstream_boundaries:
            # Check boundary node exists
            if boundary.boundary_node_id not in node_ids:
                unresolved_topology.append(f"DownstreamBoundary {boundary.boundary_id}: boundary node {boundary.boundary_node_id} not found")
            else:
                # Check that boundary node's invert_elev_m is deterministic
                node = next((n for n in dataset.nodes if n.node_id == boundary.boundary_node_id), None)
                if node and not is_deterministic_pv(node.invert_elev_m):
                    unresolved_boundary_conditions.append(
                        f"DownstreamBoundary {boundary.boundary_id}: boundary node {boundary.boundary_node_id} invert_elev_m not deterministic"
                    )
            # Check outlet geometry ref if present
            if boundary.outlet_geometry_ref:
                if boundary.outlet_geometry_ref not in structure_ids:
                    unresolved_topology.append(f"DownstreamBoundary {boundary.boundary_id}: outlet geometry ref {boundary.outlet_geometry_ref} not found")

    # 7. Check cross-sections
    for xs in dataset.cross_sections:
        if not xs.geometry_reference:
            missing_required.append(f"CrossSection {xs.cross_section_id}: geometry_reference missing")

    # 8. Check CWC observation constraints
    # CWC ORB must remain DOWNSTREAM RIVER STAGE only
    for obs in dataset.hydraulic_observations:
        if obs.location_ref.startswith("CWC"):
            if obs.observation_type != "WATER_LEVEL":
                invalid_fields.append(f"Observation {obs.observation_id}: CWC observation must be WATER_LEVEL (river stage)")

    # 9. Calculate Provenance Summary
    prov_summary = {}

    def collect_pv_provenance(obj: Any):
        if isinstance(obj, ProvenancedValue):
            prov = obj.provenance.value
            prov_summary[prov] = prov_summary.get(prov, 0) + 1
        elif isinstance(obj, list):
            for item in obj:
                collect_pv_provenance(item)
        elif isinstance(obj, BaseModel):
            for field_name in obj.__fields__:
                collect_pv_provenance(getattr(obj, field_name))

    collect_pv_provenance(dataset)

    # 10. Determine readiness flags
    ready_for_topology = not unresolved_topology

    # Solver readiness requires topology AND deterministic physical geometry AND boundary conditions
    # Manning n must have a value (even if ASSUMED)
    ready_for_hydraulic_solve = (
        ready_for_topology and
        not missing_required and
        not unresolved_boundary_conditions and
        not unresolved_geometry
    )

    # Calibration readiness requires solver readiness AND deterministic observations
    # that are relevant to the modeled Kushak flood system (not just downstream river stage)
    has_calibration_observations = any(
        obs.observation_type == "WATER_LEVEL" and
        obs.measured_value.provenance in (ProvenanceStatus.OBSERVED, ProvenanceStatus.OFFICIAL) and
        not obs.location_ref.startswith("CWC")  # Exclude CWC downstream river stage observations
        for obs in dataset.hydraulic_observations
    )
    ready_for_calibrated_depth_claims = ready_for_hydraulic_solve and has_calibration_observations

    has_issues = bool(
        missing_required or invalid_fields or provenance_violations or
        unresolved_topology or unresolved_geometry or unresolved_boundary_conditions
    )

    status = "BLOCKED" if has_issues else "READY"

    return HydraulicReadinessResult(
        status=status,
        ready_for_topology=ready_for_topology,
        ready_for_hydraulic_solve=ready_for_hydraulic_solve,
        ready_for_calibrated_depth_claims=ready_for_calibrated_depth_claims,
        missing_required_fields=missing_required,
        invalid_fields=invalid_fields,
        provenance_violations=provenance_violations,
        unresolved_topology=unresolved_topology,
        unresolved_geometry=unresolved_geometry,
        unresolved_boundary_conditions=unresolved_boundary_conditions,
        provenance_summary=prov_summary
    )