"""Tests for Digital Twin canonical models for Delhi/Kushak.

Verifies that models correctly implement provenance tracking,
handle unknown values without substitution, and maintain
strict separation as data contracts.
"""

from __future__ import annotations

import pytest
from datetime import datetime, timedelta

from backend.app.domain.delhi.digital_twin.models import (
    BoundaryCondition,
    Catchment,
    DrainageReach,
    HydraulicParameters,
    ProvenanceStatus,
    RainfallEvent,
)


def test_provenance_status_enum_complete():
    """Verify all required provenance status values are present."""
    assert ProvenanceStatus.OBSERVED == "OBSERVED"
    assert ProvenanceStatus.OFFICIAL == "OFFICIAL"
    assert ProvenanceStatus.OFFICIAL_MODEL_VALUE == "OFFICIAL_MODEL_VALUE"
    assert ProvenanceStatus.DERIVED == "DERIVED"
    assert ProvenanceStatus.ASSUMED == "ASSUMED"
    assert ProvenanceStatus.PROVISIONAL == "PROVISIONAL"
    assert ProvenanceStatus.UNKNOWN == "UNKNOWN"


def test_catchment_unknown_representation():
    """Verify Catchment preserves unknown values without substitution."""
    # Test with all unknown values
    catchment = Catchment(
        id="test_catchment",
        name="Test Catchment"
    )

    assert catchment.area_km2 is None
    assert catchment.area_provenance == ProvenanceStatus.UNKNOWN
    assert catchment.area_uncertainty_km2 is None
    assert catchment.notes is None

    # Test with known values
    catchment_known = Catchment(
        id="test_catchment_2",
        name="Test Catchment 2",
        area_km2=5.5,
        area_provenance=ProvenanceStatus.OBSERVED,
        area_uncertainty_km2=0.2,
        notes="Surveyed area"
    )

    assert catchment_known.area_km2 == 5.5
    assert catchment_known.area_provenance == ProvenanceStatus.OBSERVED
    assert catchment_known.area_uncertainty_km2 == 0.2
    assert catchment_known.notes == "Surveyed area"


def test_drainage_reach_unknown_geometry():
    """Verify DrainageReach preserves unknown geometry without zero substitution."""
    # Test with all unknown geometry
    reach = DrainageReach(
        id="test_reach",
        name="Test Reach"
    )

    assert reach.length_m is None
    assert reach.length_provenance == ProvenanceStatus.UNKNOWN
    assert reach.slope_m_per_m is None
    assert reach.slope_provenance == ProvenanceStatus.UNKNOWN
    assert reach.width_m is None
    assert reach.width_provenance == ProvenanceStatus.UNKNOWN
    assert reach.depth_m is None
    assert reach.depth_provenance == ProvenanceStatus.UNKNOWN
    assert reach.notes is None

    # Test with known geometry
    reach_known = DrainageReach(
        id="test_reach_2",
        name="Test Reach 2",
        length_m=100.0,
        length_provenance=ProvenanceStatus.OFFICIAL,
        slope_m_per_m=0.001,
        slope_provenance=ProvenanceStatus.DERIVED,
        width_m=2.5,
        width_provenance=ProvenanceStatus.ASSUMED,
        depth_m=1.2,
        depth_provenance=ProvenanceStatus.PROVISIONAL,
        notes="Surveyed cross-section"
    )

    assert reach_known.length_m == 100.0
    assert reach_known.length_provenance == ProvenanceStatus.OFFICIAL
    assert reach_known.slope_m_per_m == 0.001
    assert reach_known.slope_provenance == ProvenanceStatus.DERIVED
    assert reach_known.width_m == 2.5
    assert reach_known.width_provenance == ProvenanceStatus.ASSUMED
    assert reach_known.depth_m == 1.2
    assert reach_known.depth_provenance == ProvenanceStatus.PROVISIONAL
    assert reach_known.notes == "Surveyed cross-section"


def test_hydraulic_parameters_no_defaults():
    """Verify HydraulicParameters provides no default Manning n values."""
    # Test with unknown Manning n
    params = HydraulicParameters()

    assert params.manning_n is None
    assert params.manning_n_provenance == ProvenanceStatus.UNKNOWN
    assert params.manning_n_uncertainty is None
    assert params.notes is None

    # Test with known Manning n
    params_known = HydraulicParameters(
        manning_n=0.025,
        manning_n_provenance=ProvenanceStatus.OBSERVED,
        manning_n_uncertainty=0.002,
        notes="Field measured"
    )

    assert params_known.manning_n == 0.025
    assert params_known.manning_n_provenance == ProvenanceStatus.OBSERVED
    assert params_known.manning_n_uncertainty == 0.002
    assert params_known.notes == "Field measured"


def test_rainfall_event_unknown_representation():
    """Verify RainfallEvent preserves unknown values without substitution."""
    start_time = datetime(2026, 9, 11, 10, 0, 0)
    end_time = datetime(2026, 9, 11, 12, 0, 0)

    # Test with unknown values
    event = RainfallEvent(
        id="test_event",
        start_time=start_time,
        end_time=end_time,
        source="IMD",
        provenance=ProvenanceStatus.UNKNOWN
    )

    assert event.id == "test_event"
    assert event.start_time == start_time
    assert event.end_time == end_time
    assert event.source == "IMD"
    assert event.provenance == ProvenanceStatus.UNKNOWN
    assert event.values is None
    assert event.uncertainty is None
    assert event.notes is None

    # Test with known values
    event_known = RainfallEvent(
        id="test_event_2",
        start_time=start_time,
        end_time=end_time,
        source="Radar",
        provenance=ProvenanceStatus.DERIVED,
        values=[5.0, 8.0, 12.0, 8.0, 3.0],  # mm/h over 5 timesteps
        uncertainty=[0.5, 0.8, 1.2, 0.8, 0.3],
        notes="Radar-derived rainfall event"
    )

    assert event_known.values == [5.0, 8.0, 12.0, 8.0, 3.0]
    assert event_known.uncertainty == [0.5, 0.8, 1.2, 0.8, 0.3]
    assert event_known.notes == "Radar-derived rainfall event"


def test_boundary_condition_unknown_representation():
    """Verify BoundaryCondition preserves unknown values without substitution."""
    # Test with unknown value
    bc = BoundaryCondition(
        id="test_bc",
        type="inflow"
    )

    assert bc.id == "test_bc"
    assert bc.type == "inflow"
    assert bc.value is None
    assert bc.provenance == ProvenanceStatus.UNKNOWN
    assert bc.uncertainty is None
    assert bc.notes is None

    # Test with known value
    bc_known = BoundaryCondition(
        id="test_bc_2",
        type="stage",
        value=25.5,
        provenance=ProvenanceStatus.OFFICIAL,
        uncertainty=0.1,
        notes="Official gauge reading"
    )

    assert bc_known.value == 25.5
    assert bc_known.provenance == ProvenanceStatus.OFFICIAL
    assert bc_known.uncertainty == 0.1
    assert bc_known.notes == "Official gauge reading"


def test_scientific_safety_unknown_not_zero():
    """Verify that UNKNOWN values are not substituted with zero or defaults."""
    # Catchment with UNKNOWN area should have None, not 0
    catchment = Catchment(id="test", name="Test")
    assert catchment.area_km2 is None  # Not 0.0
    assert catchment.area_provenance == ProvenanceStatus.UNKNOWN

    # DrainageReach with UNKNOWN geometry should have None, not 0
    reach = DrainageReach(id="test", name="Test")
    assert reach.length_m is None  # Not 0.0
    assert reach.width_m is None   # Not 0.0
    assert reach.depth_m is None   # Not 0.0
    assert reach.length_provenance == ProvenanceStatus.UNKNOWN
    assert reach.width_provenance == ProvenanceStatus.UNKNOWN
    assert reach.depth_provenance == ProvenanceStatus.UNKNOWN

    # HydraulicParameters with UNKNOWN Manning n should have None, not default
    params = HydraulicParameters()
    assert params.manning_n is None  # Not 0.013 or similar default
    assert params.manning_n_provenance == ProvenanceStatus.UNKNOWN

    # BoundaryCondition with UNKNOWN value should have None, not 0
    bc = BoundaryCondition(id="test", type="inflow")
    assert bc.value is None  # Not 0.0
    assert bc.provenance == ProvenanceStatus.UNKNOWN


def test_model_cannot_contain_computations():
    """Verify models contain only data fields, no computational logic."""
    # This test ensures we haven't accidentally added methods
    # that perform calculations, routing, or hydraulic solving

    catchment = Catchment(id="test", name="Test")

    # Verify no computational methods exist
    assert not hasattr(catchment, 'compute_area')
    assert not hasattr(catchment, 'calculate_centroid')
    assert not hasattr(catchment, 'runoff_volume')

    reach = DrainageReach(id="test", name="Test")
    assert not hasattr(reach, 'compute_capacity')
    assert not hasattr(reach, 'calculate_velocity')
    assert not hasattr(reach, 'route_flow')

    params = HydraulicParameters()
    assert not hasattr(params, 'compute_friction_loss')
    assert not hasattr(params, 'calculate_shear_stress')

    # Models should only have field accessors, not computational methods
    # Pydantic provides basic methods like __init__, dict(), etc. but no domain-specific computations