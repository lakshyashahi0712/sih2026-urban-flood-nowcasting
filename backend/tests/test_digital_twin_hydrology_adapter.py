"""Tests for the hydrology -> hydraulic boundary adapter.

The adapter converts a hydrology ``SubcatchmentHydrograph`` into the
hydraulic-runtime ``HydraulicInflow`` interface. The hydraulic inflow
provenance is deliberately UNKNOWN: the current hydrology pipeline does
not propagate per-step provenance, and the adapter must never silently
promote an assumed value to a stronger evidence class.
"""

from __future__ import annotations

from backend.app.domain.delhi.hydrology_to_hydraulic_adapter import (
    adapt_subcatchment_hydrograph,
)
from backend.app.domain.delhi.digital_twin.models import ProvenanceStatus
from backend.app.domain.delhi.hydrology.models import (
    HydrographStep,
    SubcatchmentHydrograph,
)


def _make_hydrograph() -> SubcatchmentHydrograph:
    return SubcatchmentHydrograph(
        subcatchment_id="SC-01",
        zone_id="ZONE-A",
        drainage_area_km2=2.5,
        peak_discharge_m3_s=10.0,
        time_to_peak_minutes=30.0,
        total_volume_m3=15000.0,
        hydrograph=[
            HydrographStep(time_minutes=0.0, discharge_m3_s=0.0),
            HydrographStep(time_minutes=30.0, discharge_m3_s=10.0),
            HydrographStep(time_minutes=60.0, discharge_m3_s=5.0),
        ],
    )


def test_adapter_preserves_time_series_exactly():
    """Steps must be copied 1:1 without re-sampling or interpolation."""
    result = adapt_subcatchment_hydrograph(_make_hydrograph())

    assert [(s.time_minutes, s.discharge_m3_s) for s in result.steps] == [
        (0.0, 0.0),
        (30.0, 10.0),
        (60.0, 5.0),
    ]


def test_adapter_uses_subcatchment_id_as_source_id():
    """zone_id is intentionally NOT used as source_id."""
    result = adapt_subcatchment_hydrograph(_make_hydrograph())

    assert result.source_id == "SC-01"


def test_adapter_marks_provenance_unknown():
    """The adapter must not fabricate stronger provenance for derived inflows."""
    result = adapt_subcatchment_hydrograph(_make_hydrograph())

    assert result.provenance == ProvenanceStatus.UNKNOWN


def test_adapter_steps_remain_time_ordered():
    """HydraulicInflow requires non-decreasing time ordering."""
    hydrograph = SubcatchmentHydrograph(
        subcatchment_id="SC-02",
        zone_id="ZONE-B",
        drainage_area_km2=1.0,
        peak_discharge_m3_s=4.0,
        time_to_peak_minutes=15.0,
        total_volume_m3=3000.0,
        hydrograph=[
            HydrographStep(time_minutes=0.0, discharge_m3_s=1.0),
            HydrographStep(time_minutes=5.0, discharge_m3_s=4.0),
            HydrographStep(time_minutes=15.0, discharge_m3_s=2.0),
        ],
    )

    result = adapt_subcatchment_hydrograph(hydrograph)

    times = [s.time_minutes for s in result.steps]
    assert times == sorted(times)


def test_adapter_zero_flow_steps_are_preserved():
    """Explicit zero discharge is valid data and must not be dropped or
    converted to UNKNOWN/None."""
    result = adapt_subcatchment_hydrograph(_make_hydrograph())

    assert result.steps[0].discharge_m3_s == 0.0


def test_adapter_uncertainty_left_none():
    """No uncertainty quantification exists yet; adapter must not invent one."""
    result = adapt_subcatchment_hydrograph(_make_hydrograph())

    assert result.uncertainty is None
