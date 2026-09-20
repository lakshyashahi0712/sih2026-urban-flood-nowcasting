"""Adapter to convert SubcatchmentHydrograph to HydraulicInflow.

This adapter maps the hydrology runoff output to the hydraulic inflow interface.
It preserves the time series and source identifier, and sets provenance to UNKNOWN
since the current pipeline does not propagate explicit provenance.
"""

from .hydrology.models import SubcatchmentHydrograph
from .hydraulic_boundary import HydraulicInflow, HydraulicInflowStep
from .digital_twin.models import ProvenanceStatus


def adapt_subcatchment_hydrograph(hydrograph: SubcatchmentHydrograph) -> HydraulicInflow:
    """
    Convert a SubcatchmentHydrograph to a HydraulicInflow.

    Parameters
    ----------
    hydrograph : SubcatchmentHydrograph
        The hydrograph from the hydrology subsystem.

    Returns
    -------
    HydraulicInflow
        The hydraulic inflow ready for simulation.
    """
    steps = [
        HydraulicInflowStep(
            time_minutes=step.time_minutes,
            discharge_m3_s=step.discharge_m3_s
        )
        for step in hydrograph.hydrograph
    ]

    return HydraulicInflow(
        source_id=hydrograph.subcatchment_id,
        steps=steps,
        provenance=ProvenanceStatus.UNKNOWN,
        uncertainty=None,
        notes="Inflow derived from SubcatchmentHydrograph via runoff transformation."
    )