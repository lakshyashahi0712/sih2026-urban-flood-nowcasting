"""Adapter for using Manning capacity as explicit timestep outflow (Phase 7D-10).

Provides a helper to construct TimeStepFlowInputs from a computed Manning
capacity, preserving status and combining provenances. No hydraulic logic
is duplicated; the caller explicitly supplies the capacity result.
"""

from __future__ import annotations

from typing import Optional

from .hydraulic_manning_adapter import ManningCapacityResult
from .hydraulic_time_stepper import TimeStepFlowInputs
from .hydraulic_continuity import combine_provenance_weakest
from .models import ProvenanceStatus


def map_capacity_to_flows(
    capacity_result: ManningCapacityResult,
    inflow_m3_s: Optional[float] = None,
    inflow_provenance: ProvenanceStatus = ProvenanceStatus.UNKNOWN,
    lateral_inflow_m3_s: Optional[float] = None,
    lateral_inflow_provenance: ProvenanceStatus = ProvenanceStatus.UNKNOWN,
) -> TimeStepFlowInputs:
    """Build TimeStepFlowInputs using a Manning capacity as the outflow.

    - Q_out is set to capacity_result.capacity_m3_s ONLY if the result status
      is COMPUTED.
    - If the capacity result is blocked, outflow remains None (UNKNOWN),
      preserving the explicit blocked/UNKNOWN state.
    - Outflow provenance is the combined weakest link of the capacity result's
      inputs (geometry, n, slope).
    - No automatic capacity->outflow conversion is performed if the status
      is not COMPUTED.
    """
    outflow_m3_s = None
    outflow_prov = ProvenanceStatus.UNKNOWN

    if capacity_result.status == "COMPUTED":
        outflow_m3_s = capacity_result.capacity_m3_s
        outflow_prov = combine_provenance_weakest([
            capacity_result.geometry_provenance,
            capacity_result.n_provenance,
            capacity_result.slope_provenance
        ])

    return TimeStepFlowInputs(
        inflow_m3_s=inflow_m3_s,
        inflow_provenance=inflow_provenance,
        lateral_inflow_m3_s=lateral_inflow_m3_s,
        lateral_inflow_provenance=lateral_inflow_provenance,
        outflow_m3_s=outflow_m3_s,
        outflow_provenance=outflow_prov,
    )
