"""Test module for HydraulicInflow and HydraulicInflowStep."""

from .hydraulic_boundary import HydraulicInflowStep, HydraulicInflow
from .digital_twin.models import ProvenanceStatus


def test_hydraulic_inflow_step_valid():
    """Test creating a valid HydraulicInflowStep."""
    step = HydraulicInflowStep(time_minutes=0.0, discharge_m3_s=1.5)
    assert step.time_minutes == 0.0
    assert step.discharge_m3_s == 1.5


def test_hydraulic_inflow_step_negative_time():
    """Test that negative time raises ValueError."""
    try:
        HydraulicInflowStep(time_minutes=-1.0, discharge_m3_s=1.5)
        assert False, "Expected ValueError for negative time"
    except ValueError as e:
        assert "time_minutes must be non-negative" in str(e)


def test_hydraulic_inflow_step_negative_discharge():
    """Test that negative discharge raises ValueError."""
    try:
        HydraulicInflowStep(time_minutes=0.0, discharge_m3_s=-1.5)
        assert False, "Expected ValueError for negative discharge"
    except ValueError as e:
        assert "discharge_m3_s must be non-negative" in str(e)


def test_hydraulic_inflow_valid():
    """Test creating a valid HydraulicInflow."""
    steps = [
        HydraulicInflowStep(time_minutes=0.0, discharge_m3_s=0.0),
        HydraulicInflowStep(time_minutes=10.0, discharge_m3_s=2.5),
        HydraulicInflowStep(time_minutes=20.0, discharge_m3_s=1.0),
    ]
    inflow = HydraulicInflow(
        source_id="subcatchment_1",
        steps=steps,
        provenance=ProvenanceStatus.OBSERVED,
        uncertainty=None,
        notes="Test inflow"
    )
    assert inflow.source_id == "subcatchment_1"
    assert inflow.steps == steps
    assert inflow.provenance == ProvenanceStatus.OBSERVED
    assert inflow.uncertainty is None
    assert inflow.notes == "Test inflow"


def test_hydraulic_inflow_source_id_empty():
    """Test that empty source_id raises ValueError."""
    steps = [HydraulicInflowStep(time_minutes=0.0, discharge_m3_s=1.0)]
    try:
        HydraulicInflow(
            source_id="",
            steps=steps,
            provenance=ProvenanceStatus.OBSERVED
        )
        assert False, "Expected ValueError for empty source_id"
    except ValueError as e:
        assert "source_id must be non-empty" in str(e)


def test_hydraulic_inflow_steps_not_time_ordered():
    """Test that non-ordered steps raise ValueError."""
    steps = [
        HydraulicInflowStep(time_minutes=20.0, discharge_m3_s=1.0),
        HydraulicInflowStep(time_minutes=10.0, discharge_m3_s=2.5),  # out of order
    ]
    try:
        HydraulicInflow(
            source_id="subcatchment_1",
            steps=steps,
            provenance=ProvenanceStatus.OBSERVED
        )
        assert False, "Expected ValueError for non-ordered steps"
    except ValueError as e:
        assert "steps must be in non-decreasing time order" in str(e)


def test_hydraulic_inflow_provenance_preserved():
    """Test that provenance is preserved and we are using the existing enum."""
    steps = [HydraulicInflowStep(time_minutes=0.0, discharge_m3_s=1.0)]
    inflow = HydraulicInflow(
        source_id="subcatchment_1",
        steps=steps,
        provenance=ProvenanceStatus.DERIVED
    )
    assert inflow.provenance == ProvenanceStatus.DERIVED
    # Ensure we are using the same enum as in digital_twin.models
    assert inflow.provenance.value == "DERIVED"


def test_hydraulic_inflow_optional_fields_absent():
    """Test that uncertainty and notes can be absent (None)."""
    steps = [HydraulicInflowStep(time_minutes=0.0, discharge_m3_s=1.0)]
    inflow = HydraulicInflow(
        source_id="subcatchment_1",
        steps=steps,
        provenance=ProvenanceStatus.OBSERVED
    )
    assert inflow.uncertainty is None
    assert inflow.notes is None


def test_hydraulic_inflow_step_preserves_semantics():
    """Test that the step preserves the timestep-average discharge and elapsed time."""
    # The step does not interpret the discharge; it just stores it.
    step = HydraulicInflowStep(time_minutes=5.0, discharge_m3_s=3.2)
    assert step.time_minutes == 5.0  # elapsed time from event start in minutes
    assert step.discharge_m3_s == 3.2  # timestep-average discharge in m3/s


if __name__ == "__main__":
    test_hydraulic_inflow_step_valid()
    test_hydraulic_inflow_step_negative_time()
    test_hydraulic_inflow_step_negative_discharge()
    test_hydraulic_inflow_valid()
    test_hydraulic_inflow_source_id_empty()
    test_hydraulic_inflow_steps_not_time_ordered()
    test_hydraulic_inflow_provenance_preserved()
    test_hydraulic_inflow_optional_fields_absent()
    test_hydraulic_inflow_step_preserves_semantics()
    print("All tests passed.")