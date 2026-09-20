"""
Focused tests for Delhi/Kushak V2 digital twin domain types.
Tests provenance tracking, UNKNOWN/missing values, and scientific constraints.
"""

import unittest
from typing import List
from backend.app.domain.delhi.hydrology.models import (
    Catchment,
    DrainageReach,
    HydraulicParameters,
    RainfallEvent,
    BoundaryCondition,
    ProvenanceStatus,
    HyetographStep
)


class TestProvenanceStatus(unittest.TestCase):
    """Test ProvenanceStatus enum values."""

    def test_provenance_status_values(self):
        """Test that all expected provenance status values exist."""
        self.assertEqual(ProvenanceStatus.OBSERVED.value, "OBSERVED")
        self.assertEqual(ProvenanceStatus.OFFICIAL.value, "OFFICIAL")
        self.assertEqual(ProvenanceStatus.DERIVED.value, "DERIVED")
        self.assertEqual(ProvenanceStatus.ASSUMED.value, "ASSUMED")
        self.assertEqual(ProvenanceStatus.UNKNOWN.value, "UNKNOWN")


class TestCatchment(unittest.TestCase):
    """Test Catchment canonical type."""

    def test_catchment_creation_with_all_unknown(self):
        """Test creating a catchment with all values as UNKNOWN."""
        catchment = Catchment(id="CATCH-001")

        self.assertEqual(catchment.id, "CATCH-001")
        self.assertIsNone(catchment.name)
        self.assertIsNone(catchment.area_km2)
        self.assertEqual(catchment.area_provenance, ProvenanceStatus.UNKNOWN)
        self.assertIsNone(catchment.centroid_lat)
        self.assertEqual(catchment.centroid_lat_provenance, ProvenanceStatus.UNKNOWN)
        self.assertIsNone(catchment.centroid_lon)
        self.assertEqual(catchment.centroid_lon_provenance, ProvenanceStatus.UNKNOWN)

    def test_catchment_creation_with_observed_values(self):
        """Test creating a catchment with OBSERVED values."""
        catchment = Catchment(
            id="CATCH-002",
            name="Kushak Catchment",
            area_km2=25.5,
            area_provenance=ProvenanceStatus.OBSERVED,
            centroid_lat=28.6139,
            centroid_lat_provenance=ProvenanceStatus.OBSERVED,
            centroid_lon=77.2090,
            centroid_lon_provenance=ProvenanceStatus.OBSERVED
        )

        self.assertEqual(catchment.id, "CATCH-002")
        self.assertEqual(catchment.name, "Kushak Catchment")
        self.assertEqual(catchment.area_km2, 25.5)
        self.assertEqual(catchment.area_provenance, ProvenanceStatus.OBSERVED)
        self.assertEqual(catchment.centroid_lat, 28.6139)
        self.assertEqual(catchment.centroid_lat_provenance, ProvenanceStatus.OBSERVED)
        self.assertEqual(catchment.centroid_lon, 77.2090)
        self.assertEqual(catchment.centroid_lon_provenance, ProvenanceStatus.OBSERVED)


class TestDrainageReach(unittest.TestCase):
    """Test DrainageReach canonical type."""

    def test_drainage_reach_creation_with_all_unknown(self):
        """Test creating a drainage reach with all values as UNKNOWN."""
        reach = DrainageReach(id="REACH-001")

        self.assertEqual(reach.id, "REACH-001")
        self.assertIsNone(reach.length_m)
        self.assertEqual(reach.length_provenance, ProvenanceStatus.UNKNOWN)
        self.assertIsNone(reach.slope_m_per_m)
        self.assertEqual(reach.slope_provenance, ProvenanceStatus.UNKNOWN)
        self.assertIsNone(reach.manning_n)
        self.assertEqual(reach.manning_n_provenance, ProvenanceStatus.UNKNOWN)
        self.assertIsNone(reach.shape)
        self.assertEqual(reach.shape_provenance, ProvenanceStatus.UNKNOWN)
        self.assertIsNone(reach.width_m)
        self.assertEqual(reach.width_provenance, ProvenanceStatus.UNKNOWN)
        self.assertIsNone(reach.height_m)
        self.assertEqual(reach.height_provenance, ProvenanceStatus.UNKNOWN)
        self.assertIsNone(reach.bottom_width_m)
        self.assertEqual(reach.bottom_width_provenance, ProvenanceStatus.UNKNOWN)
        self.assertIsNone(reach.side_slope_z)
        self.assertEqual(reach.side_slope_z_provenance, ProvenanceStatus.UNKNOWN)

    def test_drainage_reach_creation_with_derived_values(self):
        """Test creating a drainage reach with DERIVED values."""
        reach = DrainageReach(
            id="REACH-002",
            length_m=150.0,
            length_provenance=ProvenanceStatus.DERIVED,
            slope_m_per_m=0.005,
            slope_provenance=ProvenanceStatus.DERIVED,
            manning_n=0.022,
            manning_n_provenance=ProvenanceStatus.DERIVED,
            shape="trapezoidal",
            shape_provenance=ProvenanceStatus.DERIVED,
            width_m=10.0,
            width_provenance=ProvenanceStatus.DERIVED,
            height_m=2.0,
            height_provenance=ProvenanceStatus.DERIVED,
            bottom_width_m=8.0,
            bottom_width_provenance=ProvenanceStatus.DERIVED,
            side_slope_z=1.5,
            side_slope_z_provenance=ProvenanceStatus.DERIVED
        )

        self.assertEqual(reach.id, "REACH-002")
        self.assertEqual(reach.length_m, 150.0)
        self.assertEqual(reach.length_provenance, ProvenanceStatus.DERIVED)
        self.assertEqual(reach.slope_m_per_m, 0.005)
        self.assertEqual(reach.slope_provenance, ProvenanceStatus.DERIVED)
        self.assertEqual(reach.manning_n, 0.022)
        self.assertEqual(reach.manning_n_provenance, ProvenanceStatus.DERIVED)
        self.assertEqual(reach.shape, "trapezoidal")
        self.assertEqual(reach.shape_provenance, ProvenanceStatus.DERIVED)
        self.assertEqual(reach.width_m, 10.0)
        self.assertEqual(reach.width_provenance, ProvenanceStatus.DERIVED)
        self.assertEqual(reach.height_m, 2.0)
        self.assertEqual(reach.height_provenance, ProvenanceStatus.DERIVED)
        self.assertEqual(reach.bottom_width_m, 8.0)
        self.assertEqual(reach.bottom_width_provenance, ProvenanceStatus.DERIVED)
        self.assertEqual(reach.side_slope_z, 1.5)
        self.assertEqual(reach.side_slope_z_provenance, ProvenanceStatus.DERIVED)


class TestHydraulicParameters(unittest.TestCase):
    """Test HydraulicParameters canonical type."""

    def test_hydraulic_parameters_creation_with_all_unknown(self):
        """Test creating hydraulic parameters with all values as UNKNOWN."""
        params = HydraulicParameters()

        self.assertIsNone(params.manning_n)
        self.assertEqual(params.manning_n_provenance, ProvenanceStatus.UNKNOWN)

    def test_hydraulic_parameters_creation_with_assumed_value(self):
        """Test creating hydraulic parameters with ASSUMED value."""
        params = HydraulicParameters(
            manning_n=0.015,
            manning_n_provenance=ProvenanceStatus.ASSUMED
        )

        self.assertEqual(params.manning_n, 0.015)
        self.assertEqual(params.manning_n_provenance, ProvenanceStatus.ASSUMED)


class TestRainfallEvent(unittest.TestCase):
    """Test RainfallEvent canonical type."""

    def test_rainfall_event_creation_with_all_unknown(self):
        """Test creating a rainfall event with all values as UNKNOWN."""
        hyetograph = [
            HyetographStep(time_minutes=0.0, rainfall_intensity_mm_hr=0.0, rainfall_depth_mm=0.0),
            HyetographStep(time_minutes=60.0, rainfall_intensity_mm_hr=5.0, rainfall_depth_mm=5.0)
        ]

        event = RainfallEvent(
            id="RAIN-001",
            start_time_minutes=0.0,
            end_time_minutes=120.0,
            hyetograph=hyetograph
        )

        self.assertEqual(event.id, "RAIN-001")
        self.assertEqual(event.start_time_minutes, 0.0)
        self.assertEqual(event.end_time_minutes, 120.0)
        self.assertIsNone(event.total_depth_mm)
        self.assertEqual(event.total_depth_provenance, ProvenanceStatus.UNKNOWN)
        self.assertIsNone(event.max_intensity_mm_hr)
        self.assertEqual(event.max_intensity_provenance, ProvenanceStatus.UNKNOWN)
        self.assertEqual(len(event.hyetograph), 2)
        self.assertEqual(event.hyetograph[0].time_minutes, 0.0)
        self.assertEqual(event.hyetograph[0].rainfall_intensity_mm_hr, 0.0)
        self.assertEqual(event.hyetograph[0].rainfall_depth_mm, 0.0)
        self.assertEqual(event.hyetograph[1].time_minutes, 60.0)
        self.assertEqual(event.hyetograph[1].rainfall_intensity_mm_hr, 5.0)
        self.assertEqual(event.hyetograph[1].rainfall_depth_mm, 5.0)

    def test_rainfall_event_creation_with_official_values(self):
        """Test creating a rainfall event with OFFICIAL values."""
        hyetograph = [
            HyetographStep(time_minutes=0.0, rainfall_intensity_mm_hr=0.0, rainfall_depth_mm=0.0),
            HyetographStep(time_minutes=30.0, rainfall_intensity_mm_hr=20.0, rainfall_depth_mm=10.0),
            HyetographStep(time_minutes=60.0, rainfall_intensity_mm_hr=5.0, rainfall_depth_mm=2.5)
        ]

        event = RainfallEvent(
            id="RAIN-002",
            start_time_minutes=0.0,
            end_time_minutes=60.0,
            total_depth_mm=25.0,
            total_depth_provenance=ProvenanceStatus.OFFICIAL,
            max_intensity_mm_hr=20.0,
            max_intensity_provenance=ProvenanceStatus.OFFICIAL,
            hyetograph=hyetograph
        )

        self.assertEqual(event.id, "RAIN-002")
        self.assertEqual(event.start_time_minutes, 0.0)
        self.assertEqual(event.end_time_minutes, 60.0)
        self.assertEqual(event.total_depth_mm, 25.0)
        self.assertEqual(event.total_depth_provenance, ProvenanceStatus.OFFICIAL)
        self.assertEqual(event.max_intensity_mm_hr, 20.0)
        self.assertEqual(event.max_intensity_provenance, ProvenanceStatus.OFFICIAL)
        self.assertEqual(len(event.hyetograph), 3)
        self.assertEqual(event.hyetograph[1].rainfall_intensity_mm_hr, 20.0)
        self.assertEqual(event.hyetograph[1].rainfall_depth_mm, 10.0)


class TestBoundaryCondition(unittest.TestCase):
    """Test BoundaryCondition canonical type."""

    def test_boundary_condition_creation_inflow_with_all_unknown(self):
        """Test creating an inflow boundary condition with all values as UNKNOWN."""
        bc = BoundaryCondition(
            id="BC-INFLOW-001",
            type="inflow"
        )

        self.assertEqual(bc.id, "BC-INFLOW-001")
        self.assertEqual(bc.type, "inflow")
        self.assertIsNone(bc.value)
        self.assertEqual(bc.value_provenance, ProvenanceStatus.UNKNOWN)
        self.assertEqual(len(bc.time_series), 0)

    def test_boundary_condition_creation_outflow_with_observed_value(self):
        """Test creating an outflow boundary condition with OBSERVED value."""
        time_series = [
            HyetographStep(time_minutes=0.0, rainfall_intensity_mm_hr=0.0, rainfall_depth_mm=0.0),
            HyetographStep(time_minutes=60.0, rainfall_intensity_mm_hr=2.5, rainfall_depth_mm=2.5)  # Using as flow rate m3/s
        ]

        bc = BoundaryCondition(
            id="BC-OUTFLOW-001",
            type="outflow",
            value=2.5,
            value_provenance=ProvenanceStatus.OBSERVED,
            time_series=time_series
        )

        self.assertEqual(bc.id, "BC-OUTFLOW-001")
        self.assertEqual(bc.type, "outflow")
        self.assertEqual(bc.value, 2.5)
        self.assertEqual(bc.value_provenance, ProvenanceStatus.OBSERVED)
        self.assertEqual(len(bc.time_series), 2)
        self.assertEqual(bc.time_series[0].time_minutes, 0.0)
        self.assertEqual(bc.time_series[0].rainfall_intensity_mm_hr, 0.0)  # Represents flow rate
        self.assertEqual(bc.time_series[0].rainfall_depth_mm, 0.0)
        self.assertEqual(bc.time_series[1].time_minutes, 60.0)
        self.assertEqual(bc.time_series[1].rainfall_intensity_mm_hr, 2.5)
        self.assertEqual(bc.time_series[1].rainfall_depth_mm, 2.5)

    def test_boundary_condition_creation_water_level_with_assumed_value(self):
        """Test creating a water level boundary condition with ASSUMED value."""
        bc = BoundaryCondition(
            id="BC-WL-001",
            type="water_level",
            value=215.5,  # Elevation in meters
            value_provenance=ProvenanceStatus.ASSUMED
        )

        self.assertEqual(bc.id, "BC-WL-001")
        self.assertEqual(bc.type, "water_level")
        self.assertEqual(bc.value, 215.5)
        self.assertEqual(bc.value_provenance, ProvenanceStatus.ASSUMED)


if __name__ == '__main__':
    unittest.main()