"""Adapter to convert hydrology SubcatchmentHydrograph to digital-twin HydrographEvent."""

from __future__ import annotations

from backend.app.domain.delhi.digital_twin.models import (
    HydrographEvent,
    HydrographStep,
    ProvenanceStatus,
)
from backend.app.domain.delhi.hydrology.models import SubcatchmentHydrograph


def adapt_subcatchment_hydrograph(hydrograph: SubcatchmentHydrograph) -> HydrographEvent:
    """Convert SubcatchmentHydrograph to HydrographEvent with provenance tracking.

    Maps scientifically justified fields only. Does not invent catchment area,
    geometry, invert, Manning n, rainfall provenance, observed discharge, or
    flood observations. Missing information remains None/UNKNOWN.

    Args:
        hydrograph: SubcatchmentHydrograph from kinematic wave computation.

    Returns:
        HydrographEvent with mapped fields and appropriate provenance.
    """
    return HydrographEvent(
        id=hydrograph.subcatchment_id,
        source="kinematic_wave",
        provenance=ProvenanceStatus.DERIVED,
        hydrograph=[
            HydrographStep(time_minutes=step.time_minutes, discharge_m3_s=step.discharge_m3_s)
            for step in hydrograph.hydrograph
        ],
        notes=None,
        drainage_area_km2=hydrograph.drainage_area_km2,
        drainage_area_provenance=ProvenanceStatus.UNKNOWN,
        zone_id=hydrograph.zone_id,
        peak_discharge_m3_s=hydrograph.peak_discharge_m3_s,
        peak_discharge_provenance=ProvenanceStatus.DERIVED,
        time_to_peak_minutes=hydrograph.time_to_peak_minutes,
        time_to_peak_provenance=ProvenanceStatus.DERIVED,
        total_volume_m3=hydrograph.total_volume_m3,
        total_volume_provenance=ProvenanceStatus.DERIVED,
    )