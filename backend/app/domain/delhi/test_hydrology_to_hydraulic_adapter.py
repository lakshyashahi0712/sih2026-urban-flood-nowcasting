"""Test module for hydrology to hydraulic inflow adapter."""

from .hydrology.models import SubcatchmentHydrograph, HydrographStep
from .hydrology_to_hydraulic_adapter import adapt_subcatchment_hydrograph
from .hydraulic_boundary import HydraulicInflow, HydraulicInflowStep
from .digital_twin.models import ProvenanceStatus


def test_adapter_basic_conversion():
    """Test that adapter converts SubcatchmentHydrograph to HydraulicInflow."""
    steps = [
        HydrographStep(time_minutes=0.0, discharge_m3_s=0.0),
        HydrographStep(time_minutes=5.0, discharge_m3_s=2.5),
        HydrographStep(time_minutes=10.0, discharge_m3_s=1.0),
    ]
    hydrograph = SubcatchmentHydrograph(
        subcatchment_id="sub_1",
        zone_id="zone_A",
        drainage_area_km2=0.5,
        peak_discharge_m3_s=2.5,
        time_to_peak_minutes=5.0,
        total_volume_m3=100.0,
        hydrograph=steps
    )

    inflow = adapt_subcatchment_hydrograph(hydrograph)

    assert isinstance(inflow, HydraulicInflow)
    assert inflow.source_id == "sub_1"
    assert len(inflow.steps) == 3
    assert inflow.provenance == ProvenanceStatus.UNKNOWN
    assert inflow.uncertainty is None
    assert inflow.notes == "Inflow derived from SubcatchmentHydrograph via runoff transformation."

    # Check each step mapping
    for i in range(len(steps)):
        assert inflow.steps[i].time_minutes == steps[i].time_minutes
        assert inflow.steps[i].discharge_m3_s == steps[i].discharge_m3_s


def test_adapter_preserves_time_series():
    """Test that time series is preserved exactly."""
    steps = [
        HydrographStep(time_minutes=0.0, discharge_m3_s=0.0),
        HydrographStep(time_minutes=1.0, discharge_m3_s=1.0),
        HydrographStep(time_minutes=2.0, discharge_m3_s=2.0),
        HydrographStep(time_minutes=3.0, discharge_m3_s=1.5),
    ]
    hydrograph = SubcatchmentHydrograph(
        subcatchment_id="test",
        zone_id="z",
        drainage_area_km2=0.1,
        peak_discharge_m3_s=2.0,
        time_to_peak_minutes=2.0,
        total_volume_m3=50.0,
        hydrograph=steps
    )

    inflow = adapt_subcatchment_hydrograph(hydrograph)

    for i in range(len(steps)):
        assert inflow.steps[i].time_minutes == steps[i].time_minutes
        assert inflow.steps[i].discharge_m3_s == steps[i].discharge_m3_s


def test_adapter_no_zone_id_mapping():
    """Ensure zone_id is not used for source_id."""
    hydrograph = SubcatchmentHydrograph(
        subcatchment_id="subcatchment_xyz",
        zone_id="some_zone",
        drainage_area_km2=0.2,
        peak_discharge_m3_s=1.0,
        time_to_peak_minutes=10.0,
        total_volume_m3=20.0,
        hydrograph=[HydrographStep(time_minutes=0.0, discharge_m3_s=0.0)]
    )

    inflow = adapt_subcatchment_hydrograph(hydrograph)
    assert inflow.source_id == "subcatchment_xyz"
    assert inflow.source_id != "some_zone"


def test_adapter_does_not_map_other_fields():
    """Ensure other SubcatchmentHydrograph fields are not mapped."""
    hydrograph = SubcatchmentHydrograph(
        subcatchment_id="sub_2",
        zone_id="zone_B",
        drainage_area_km2=1.23,
        peak_discharge_m3_s=4.56,
        time_to_peak_minutes=7.89,
        total_volume_m3=42.0,
        hydrograph=[HydrographStep(time_minutes=0.0, discharge_m3_s=0.0)]
    )

    inflow = adapt_subcatchment_hydrograph(hydrograph)
    # These fields are not in HydraulicInflow, but we can check that they are not accidentally included.
    # The adapter does not copy them, so they are absent from the HydraulicInflow object.
    # We can only check that the HydraulicInflow does not have these attributes.
    assert not hasattr(inflow, 'drainage_area_km2')
    assert not hasattr(inflow, 'zone_id')
    assert not hasattr(inflow, 'peak_discharge_m3_s')
    assert not hasattr(inflow, 'time_to_peak_minutes')
    assert not hasattr(inflow, 'total_volume_m3')


def test_adapter_empty_hydrograph():
    """Test behavior with empty hydrograph (should be invalid due to HydraulicInflow validation)."""
    hydrograph = SubcatchmentHydrograph(
        subcatchment_id="empty",
        zone_id="z",
        drainage_area_km2=0.0,
        peak_discharge_m3_s=0.0,
        time_to_peak_minutes=0.0,
        total_volume_m3=0.0,
        hydrograph=[]
    )
    # According to HydraulicInflow, steps must be a non-empty list? Let's see:
    # HydraulicInflow.steps is List[HydraulicInflowStep] with no explicit min_items, but the validator
    # for steps_must_be_time_ordered returns early if len(v) < 2, so empty or single-element list passes
    # the time order validation. However, the Field(...) means it's required, but can be empty list.
    # We'll test that the adapter produces an empty steps list, and HydraulicInflow accepts it.
    inflow = adapt_subcatchment_hydrograph(hydrograph)
    assert len(inflow.steps) == 0
    # Additional validation: source_id non-empty, provenance set, etc.
    assert inflow.source_id == "empty"
    assert inflow.provenance == ProvenanceStatus.UNKNOWN


def test_adapter_preserves_timestep_average_semantics():
    """Confirm that discharge values are not altered (they are timestep-average)."""
    # We cannot change the semantics, but we can check that the value is copied exactly.
    original_value = 3.14159
    steps = [HydrographStep(time_minutes=0.0, discharge_m3_s=original_value)]
    hydrograph = SubcatchmentHydrograph(
        subcatchment_id="sem",
        zone_id="z",
        drainage_area_km2=0.1,
        peak_discharge_m3_s=original_value,
        time_to_peak_minutes=0.0,
        total_volume_m3=0.0,
        hydrograph=steps
    )
    inflow = adapt_subcatchment_hydrograph(hydrograph)
    assert inflow.steps[0].discharge_m3_s == original_value


def test_adapter_source_id_non_empty():
    """Ensure source_id is non-empty (should be, as SubcatchmentHydrograph requires it)."""
    hydrograph = SubcatchmentHydrograph(
        subcatchment_id="valid_id",
        zone_id="z",
        drainage_area_km2=0.1,
        peak_discharge_m3_s=0.0,
        time_to_peak_minutes=0.0,
        total_volume_m3=0.0,
        hydrograph=[HydrographStep(time_minutes=0.0, discharge_m3_s=0.0)]
    )
    inflow = adapt_subcatchment_hydrograph(hydrograph)
    assert inflow.source_id == "valid_id"
    assert inflow.source_id.strip() != ""


if __name__ == "__main__":
    test_adapter_basic_conversion()
    test_adapter_preserves_time_series()
    test_adapter_no_zone_id_mapping()
    test_adapter_does_not_map_other_fields()
    test_adapter_empty_hydrograph()
    test_adapter_preserves_timestep_average_semantics()
    test_adapter_source_id_non_empty()
    print("All tests passed.")