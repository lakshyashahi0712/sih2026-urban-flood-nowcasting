"""June 28, 2024 real-event rainfall scenario (Phase 7D-19).

A research/scenario artifact — NOT production configuration — connecting
the existing verified benchmark forcing (kushak_forcing_hyetograph_
20240628_safdarjung.csv) through the Phase 7D-17 rainfall_to_inflow
conversion and the Phase 7D-12 hydraulic chain.

Provenance rules (strict):
- OVERLAP CORRECTION (Phase 7D-19 fix): the source CSV's derived hourly
  allocations (02:00-04:00 from the 02:30-05:30 block, 06:00-07:00 from
  the 05:30-08:30 residual block) both depend on intervals that OVERLAP
  the directly observed 91.0 mm peak hour (05:00-06:00 IST). The overlap
  cannot be uniquely allocated, so those derived hourly values are NOT
  usable: the separate block observations (148.5 mm cumulative,
  79.6 mm residual) stay preserved in `block_observations` and the CSV
  values stay verbatim in `documented_mm`, but the usable forcing
  series (`depths_mm`) holds UNKNOWN (None) for overlap-dependent hours
  — never a fabricated hourly reconstruction, never a silent
  double-count.
- The directly observed 91.0 mm hour keeps its OBSERVED_DIRECT /
  OFFICIAL_OBSERVED_HOURLY_PEAK classification and is the only non-zero
  rainfall in the usable series. Verified zero hours remain valid zero.
- No hourly event total is claimed. Mass-balance diagnostics refer to
  the actual source observations (the cumulative blocks and the direct
  hour), not to any hourly sum.
- Catchment area (27.66 km2 WORKING MODEL CATCHMENT per
  DELHI_KUSHAK_HYDROLOGIC_RUNOFF_SPEC, status PROVISIONAL) and the
  runoff coefficient are explicit caller-supplied SCENARIO parameters —
  neither is claimed observed or calibrated.
- Hydraulic geometry is SYNTHETIC/TEST-ONLY, completely separate from
  real Kushak geometry.
- Resulting discharge is RAINFALL_DERIVED / SCENARIO (the 7D-17 result
  provenance is DERIVED), never observed Kushak discharge.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .hydraulic_geometry import CrossSectionProfile, StationPoint
from .hydraulic_hydrograph_driver import HydrographRunResult, run_hydrograph_simulation
from .hydraulic_time_state import SimulationState, SimulationStateStatus, SimulationTimestep
from .models import ProvenanceStatus
from .rainfall_to_inflow import RainfallToInflowResult, rainfall_to_inflow

# Repo-rooted benchmark artifact (verified June 28, 2024 forcing).
FORCING_CSV = (
    Path(__file__).resolve().parents[5]
    / "data" / "delhi" / "derived" / "rainfall"
    / "kushak_forcing_hyetograph_20240628_safdarjung.csv"
)

# Scenario parameters — caller-supplied, NEVER observed or calibrated:
# - Area: the documented WORKING MODEL CATCHMENT (PROVISIONAL status) from
#   the governing runoff spec; a model value, not a surveyed boundary.
# - C: an explicit scenario assumption for the event-water-balance
#   formulation; no calibration is performed anywhere in this phase.
SCENARIO_AREA_KM2 = 27.66
SCENARIO_RUNOFF_C = 0.75
SCENARIO_AREA_PROVENANCE = ProvenanceStatus.OFFICIAL_MODEL_VALUE
SCENARIO_RUNOFF_PROVENANCE = ProvenanceStatus.ASSUMED

SYNTHETIC_PROFILE_ID = "synthetic-rect-scenario"
SYNTHETIC_MANNING_N = 0.015
SYNTHETIC_SLOPE = 0.005


@dataclass
class BlockObservation:
    """A source block observation preserved as observed (never hourly)."""
    label: str
    interval_ist: str
    depth_mm: float
    note: str


# Separate block observations from the source benchmark (each observed
# once as a block; overlapping intervals are NOT additive and are never
# allocated hourly).
BLOCK_OBSERVATIONS = [
    BlockObservation(
        label="synoptic block 02:30-05:30",
        interval_ist="2024-06-28T02:30-05:30",
        depth_mm=148.5,
        note="official cumulative block (148.5 mm / 3h = 49.5 mm/h)",
    ),
    BlockObservation(
        label="direct hour 05:00-06:00",
        interval_ist="2024-06-28T05:00-06:00",
        depth_mm=91.0,
        note="direct observed peak (OBSERVED_DIRECT, "
             "OFFICIAL_OBSERVED_HOURLY_PEAK)",
    ),
    BlockObservation(
        label="synoptic residual block 05:30-08:30",
        interval_ist="2024-06-28T05:30-08:30",
        depth_mm=79.6,
        note="official residual block (79.6 mm total); OVERLAPS the "
             "05:00-06:00 direct hour",
    ),
]


@dataclass
class ScenarioForcing:
    """The documented forcing, corrected for the overlapping observations.

    timesteps are the CSV's IST hour stamps. documented_mm is the CSV's
    hourly column verbatim (preserved, never used as forcing). depths_mm
    is the usable forcing series: the direct 91.0 mm hour and the
    verified zeros pass through; every overlap-dependent derived hour is
    UNKNOWN (None) — never fabricated, never double-counted.
    unusable_labels preserves the per-row quality flags for the hours
    excluded from the usable series.
    """
    timesteps: List[SimulationTimestep]
    documented_mm: List[Optional[float]]
    depths_mm: List[Optional[float]]
    unusable_labels: List[str] = field(default_factory=list)
    block_observations: List[BlockObservation] = field(
        default_factory=lambda: list(BLOCK_OBSERVATIONS))

    @property
    def documented_hourly_sum_mm(self) -> float:
        """The CSV column's sum — NOT a valid event total (overlap)."""
        return sum(v for v in self.documented_mm if v is not None)


def _parse_ts(raw: str) -> datetime:
    ts = datetime.fromisoformat(raw)  # IST offset +05:30 preserved
    if ts.tzinfo is None:
        raise ValueError(f"forcing timestamp must be tz-aware (got {raw!r})")
    return ts


def load_june_2024_forcing(csv_path: Path = FORCING_CSV) -> ScenarioForcing:
    """Load the June 28, 2024 forcing, corrected for the overlap.

    - One hourly SimulationTimestep per CSV row (start = row stamp,
      end = row stamp + 1 h; duration preserved exactly).
    - documented_mm keeps the CSV hourly column verbatim (preserved,
      never used as forcing).
    - depths_mm is the usable series: ONLY the directly observed hour
      (OBSERVED_DIRECT classification) and the verified zeros pass
      through. Every DERIVED block-allocation/residual hour overlaps
      the direct hour or the block it was allocated from in a way that
      cannot be uniquely resolved, so it is UNKNOWN (None) in the usable
      series — never fabricated, never double-counted.
    - No interpolation across gaps; row order preserved.
    """
    timesteps: List[SimulationTimestep] = []
    documented: List[Optional[float]] = []
    depths: List[Optional[float]] = []
    unusable: List[str] = []
    with open(csv_path, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            ts = _parse_ts(row["timestamp_ist"])
            timesteps.append(SimulationTimestep(
                start=ts, end=ts + timedelta(hours=1)))
            raw = (row["rainfall_mm"] or "").strip()
            value = None
            if row.get("missing_flag", "").strip().lower() == "true" or raw == "":
                value = None  # preserved UNKNOWN, never filled
            else:
                value = float(raw)
            documented.append(value)
            # Overlap correction: only OBSERVED_DIRECT and VERIFIED_ZERO
            # classifications are usable; DERIVED rows are overlap-
            # dependent and stay UNKNOWN in the usable series.
            classification = row.get("observation_classification", "").strip()
            if classification in ("OBSERVED_DIRECT", "VERIFIED_ZERO"):
                depths.append(value)
            else:
                depths.append(None)
                unusable.append(row.get("quality_flag", ""))
    return ScenarioForcing(
        timesteps=timesteps,
        documented_mm=documented,
        depths_mm=depths,
        unusable_labels=unusable,
    )


def synthetic_scenario_profile() -> CrossSectionProfile:
    """Synthetic test-only cross-section (NOT real Kushak geometry).

    10 m wide rectangular channel with near-vertical walls; the same
    hand-checkable test geometry used across the 7D phases.
    """
    return CrossSectionProfile([
        StationPoint(-5.001, 104.0, ProvenanceStatus.ASSUMED),
        StationPoint(-5.0, 100.0, ProvenanceStatus.ASSUMED),
        StationPoint(5.0, 100.0, ProvenanceStatus.ASSUMED),
        StationPoint(5.001, 104.0, ProvenanceStatus.ASSUMED),
    ], cross_section_id=SYNTHETIC_PROFILE_ID)


@dataclass
class ScenarioRun:
    """Full scenario outcome (research artifact, not production)."""
    forcing: ScenarioForcing
    conversion: RainfallToInflowResult
    hydraulic: Optional[HydrographRunResult]
    scenario_parameters: Dict[str, str] = field(default_factory=dict)


def run_june_2024_scenario(
    catchment_area_km2: float = SCENARIO_AREA_KM2,
    runoff_coefficient: float = SCENARIO_RUNOFF_C,
    initial_storage_m3: float = 10000.0,
) -> ScenarioRun:
    """Run the corrected forcing through rainfall -> inflow -> hydraulics.

    - Area and C are explicit caller-supplied scenario parameters.
    - The usable series drives the chain: the direct 91.0 mm hour is
      the only non-zero rainfall; overlap-dependent derived hours are
      UNKNOWN and the run STOPS transparently at the first UNKNOWN
      timestep per the existing stop-on-first-block contract (PARTIAL,
      never zero-filled, no full-event accumulation claimed).
    - The hydraulic chain runs on the SYNTHETIC scenario profile with
      explicit zero outflow/lateral inflow (existing 7D-10/11/12
      contracts; capacity stays a reported artifact, never Q_out).
    """
    forcing = load_june_2024_forcing()
    conversion = rainfall_to_inflow(
        timesteps=forcing.timesteps,
        rainfall_depth_mm=forcing.depths_mm,
        catchment_area_km2=catchment_area_km2,
        runoff_coefficient=runoff_coefficient,
        catchment_area_provenance=SCENARIO_AREA_PROVENANCE,
        runoff_coefficient_provenance=SCENARIO_RUNOFF_PROVENANCE,
        source_id="kushak-june-2024-scenario",
    )
    hydraulic = None
    if conversion.status == "COMPUTED":
        initial = SimulationState(
            timestamp=forcing.timesteps[0].start,
            location_id="SCENARIO",
            status=SimulationStateStatus.COMPUTED,
            stage_m=102.0,
            storage_m3=initial_storage_m3,
            provenance=ProvenanceStatus.DERIVED,
        )
        hydraulic = run_hydrograph_simulation(
            initial_state=initial,
            timesteps=forcing.timesteps,
            hydrograph=conversion.hydrograph,
            profile=synthetic_scenario_profile(),
            manning_n=SYNTHETIC_MANNING_N,
            slope=SYNTHETIC_SLOPE,
            explicit_outflow_m3_s=0.0,
            explicit_outflow_provenance=ProvenanceStatus.ASSUMED,
            lateral_inflow_m3_s=0.0,
            lateral_inflow_provenance=ProvenanceStatus.ASSUMED,
        )
    return ScenarioRun(
        forcing=forcing,
        conversion=conversion,
        hydraulic=hydraulic,
        scenario_parameters={
            "catchment_area_km2": f"{catchment_area_km2} (WORKING MODEL CATCHMENT, "
                                  "PROVISIONAL — not observed/surveyed)",
            "runoff_coefficient": f"{runoff_coefficient} (ASSUMED scenario "
                                  "parameter — not calibrated)",
            "hydraulic_geometry": "SYNTHETIC test-only profile — not real Kushak geometry",
            "discharge_status": "RAINFALL_DERIVED / SCENARIO — never observed "
                                "Kushak discharge",
            "rainfall_basis": "OVERLAP-CORRECTED: only the direct 91.0 mm "
                              "hour (OBSERVED_DIRECT) and verified zeros are "
                              "usable; derived block-allocation hours are "
                              "UNKNOWN (overlapping evidence cannot be "
                              "uniquely allocated). Event mass balance refers "
                              "to the source block observations (148.5 mm "
                              "block, 91.0 mm direct hour, 79.6 mm residual "
                              "block), not to any hourly sum.",
        },
    )
