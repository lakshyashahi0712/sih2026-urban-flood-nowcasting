"""
Lateral inflow coupling for Delhi/Kushak hydrologic model.
Couples subcatchment hydrographs to specific locations in the 1D hydraulic corridor.

NOTE: This module is not used in the rainfall→runoff pipeline of SIH V2 prototype.
It is deferred for hydraulic routing coupling (Phase 3+).
"""

from typing import List, Dict, Optional
from .models import (
    SubcatchmentHydrograph,
    LateralCouplingAssignment,
    HydrographStep
)

def couple_lateral_inflows(
    subcatchment_hydrographs: List[SubcatchmentHydrograph],
    # In a full implementation, this mapping would come from catchment discretization:
    # Dict[subcatchment_id, (zone_id, reach_id, chainage_start_m, chainage_end_m, is_point_source)]
    subcatchment_to_reach_mapping: Optional[Dict[str, tuple]] = None
) -> List[LateralCouplingAssignment]:
    """
    Couples subcatchment hydrographs to specific reaches in the 1D hydraulic corridor.

    For SIH V2 prototype, if no mapping is provided, we assume:
    - Each subcatchment belongs to a zone matching its subcatchment_id (e.g., SC-01 -> zone_SC-01)
    - Each subcatchment couples to a reach with the same ID as the subcatchment
    - All couplings are point sources at chainage 0 (simplified)

    In practice, this mapping should be provided based on:
    - Catchment delineation (which subcatchment drains to which point)
    - Hydraulic corridor discretization (reach definitions)
    - Spatial analysis of flow paths

    Args:
        subcatchment_hydrographs: List of hydrographs from subcatchments
        subcatchment_to_reach_mapping: Optional mapping from subcatchment ID to
            (zone_id, reach_id, chainage_start_m, chainage_end_m, is_point_source)

    Returns:
        List of LateralCouplingAssignment objects
    """
    assignments = []

    for hydro in subcatchment_hydrographs:
        subcatchment_id = hydro.subcatchment_id

        # Determine coupling parameters
        if subcatchment_to_reach_mapping and subcatchment_id in subcatchment_to_reach_mapping:
            # Use provided mapping
            zone_id, reach_id, chainage_start, chainage_end, is_point_source = subcatchment_to_reach_mapping[subcatchment_id]
        else:
            # Default mapping for SIH V2 prototype
            # Zone ID derived from subcatchment ID (e.g., SC-01 -> zone_SC-01)
            zone_id = f"zone_{subcatchment_id}"
            # Reach ID same as subcatchment ID (simplified)
            reach_id = subcatchment_id
            # Point source at chainage 0 (simplified - in reality would be distributed)
            chainage_start = 0.0
            chainage_end = 0.0
            is_point_source = True

        # Create the lateral coupling assignment
        assignment = LateralCouplingAssignment(
            zone_id=zone_id,
            subcatchment_id=subcatchment_id,
            reach_id=reach_id,
            chainage_start_m=chainage_start,
            chainage_end_m=chainage_end,
            is_point_source=is_point_source,
            distributed_hydrograph=hydro.hydrograph
        )
        assignments.append(assignment)

    return assignments

def aggregate_lateral_inflows_by_zone(
    assignments: List[LateralCouplingAssignment]
) -> Dict[str, List[HydrographStep]]:
    """
    Aggregates lateral inflow assignments by zone_id for use in hydraulic solver.

    Args:
        assignments: List of LateralCouplingAssignment objects

    Returns:
        Dictionary mapping zone_id to aggregated hydrograph (list of HydrographStep)
    """
    # Group assignments by zone_id
    zone_assignments: Dict[str, List[LateralCouplingAssignment]] = {}
    for assignment in assignments:
        zone_id = assignment.zone_id
        if zone_id not in zone_assignments:
            zone_assignments[zone_id] = []
        zone_assignments[zone_id].append(assignment)

    # For each zone, aggregate the hydrographs
    aggregated_hydrographs: Dict[str, List[HydrographStep]] = {}
    for zone_id, zone_assigns in zone_assignments.items():
        if not zone_assigns:
            continue

        # Collect all unique time steps
        time_set = set()
        for assign in zone_assigns:
            for step in assign.distributed_hydrograph:
                time_set.add(step.time_minutes)
        sorted_times = sorted(time_set)

        # Initialize aggregated discharge
        aggregated_discharge = [0.0] * len(sorted_times)

        # Sum discharges from all assignments in this zone
        for assign in zone_assigns:
            # Create time-to-discharge mapping for this assignment
            time_to_discharge = {
                step.time_minutes: step.discharge_m3_s
                for step in assign.distributed_hydrograph
            }
            # Add to aggregated discharge
            for i, t in enumerate(sorted_times):
                aggregated_discharge[i] += time_to_discharge.get(t, 0.0)

        # Build aggregated hydrograph for this zone
        aggregated_hydrographs[zone_id] = [
            HydrographStep(time_minutes=t, discharge_m3_s=q)
            for t, q in zip(sorted_times, aggregated_discharge)
        ]

    return aggregated_hydrographs