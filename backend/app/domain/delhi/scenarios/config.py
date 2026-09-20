"""Synthetic scenario engine — configuration (single canonical source).

SCIENTIFIC DISCIPLINE (mandate rules):
- Every synthetic artifact carries provenance:
    source_type = SIMULATED / SIMULATED_MODEL_OUTPUT / SYNTHETIC_GROUND_TRUTH
  with scenario_id, timestamp, generated_by, generation_method.
- Synthetic values are NEVER labeled observed/measured/official.
- Synthetic validation is a SEPARATE category from real-event validation.
- Production/live mode NEVER consumes synthetic data; synthetic mode is
  explicitly opt-in.
- No historical observation is fabricated; UNKNOWN stays UNKNOWN.

DEPTH THRESHOLDS are DEMO/UI classification thresholds (configurable,
labeled as such) — never hazard standards, never observed thresholds.
They are the ONE source consumed by backend classification, the map
legend, the routing hazard logic, and the frontend.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Canonical depth thresholds (DEMO/UI classification; configurable)
# ---------------------------------------------------------------------------

DEPTH_THRESHOLDS_CM: Dict[str, float] = {
    "SHALLOW": 2.0,    # above this: SHALLOW
    "MODERATE": 10.0,  # above: MODERATE
    "DEEP": 30.0,      # above: DEEP
    "SEVERE": 60.0,    # above: SEVERE
}
DEPTH_THRESHOLDS_LABEL = (
    "DEMO/UI classification thresholds for surface depth proxies — "
    "NOT hazard standards, NOT observed thresholds, NOT a safety claim"
)

# Routing hazard thresholds (canonical; consumed by the scenario routing path).
ROUTING_HAZARD_CM = 15.0   # segment at/above this depth becomes ELEVATED/EXCLUDED
ROUTING_EXCLUDE_CM = 45.0  # segment at/above this depth is excluded from candidate routes


def classify_depth_cm(depth_cm: Optional[float]) -> str:
    """Map a depth in cm to a flood state. None (UNKNOWN) is its own state
    and is NEVER collapsed into NO_FLOOD."""
    if depth_cm is None:
        return "UNKNOWN"
    if depth_cm <= 0:
        return "NO_FLOOD"
    if depth_cm < DEPTH_THRESHOLDS_CM["SHALLOW"]:
        return "NO_FLOOD"
    if depth_cm < DEPTH_THRESHOLDS_CM["MODERATE"]:
        return "SHALLOW"
    if depth_cm < DEPTH_THRESHOLDS_CM["DEEP"]:
        return "MODERATE"
    if depth_cm < DEPTH_THRESHOLDS_CM["SEVERE"]:
        return "DEEP"
    return "SEVERE"


# ---------------------------------------------------------------------------
# Scenario definitions (deterministic; all timing/amplitude is parameter)
# ---------------------------------------------------------------------------

DEFAULT_SEED = 20260917
DEFAULT_TIMESTEP_MIN = 15


@dataclass(frozen=True)
class StormTemporalProfile:
    """Piecewise-linear hyetograph: (fraction_of_duration, amplitude *
    peak_mm_h). Amplitude at any t interpolated linearly between points."""

    points: Tuple[Tuple[float, float], ...]  # (f, amp) with f in [0,1]


@dataclass(frozen=True)
class StormSpatialCore:
    """Elliptical Gaussian rainfall core in UTM (EPSG:32643)."""

    center_subcatchment: Optional[str]  # anchor to a documented centroid
    center_utm: Optional[Tuple[float, float]]  # explicit UTM center override
    sigma_x_m: float
    sigma_y_m: float
    translation_m_per_s: Tuple[float, float] = (0.0, 0.0)  # storm movement


@dataclass(frozen=True)
class SyntheticBoundaryProfile:
    """DOCUMENTED SYNTHETIC downstream boundary (never a historical tide
    presented as truth). Backwater factor 0..1 reduces terminal effective
    conveyance (higher downstream level -> lower effective capacity)."""

    label: str
    level_m: float  # synthetic downstream reference level (m, reference datum)
    backwater_factor: float  # applied to the capacity class (<=1)


@dataclass(frozen=True)
class ScenarioDefinition:
    scenario_id: str
    name: str
    description: str
    duration_min: int
    timestep_min: int = DEFAULT_TIMESTEP_MIN
    seed: int = DEFAULT_SEED
    base_rainfall_mm_h: float = 0.0
    peak_mm_h: float = 0.0
    storm_profile: StormTemporalProfile = StormTemporalProfile(((0.0, 0.0), (1.0, 1.0)))
    storm_core: Optional[StormSpatialCore] = None
    drainage_modifier: Optional[float] = None   # experimental multiplier (SCN-05)
    boundary_profile: Optional[SyntheticBoundaryProfile] = None
    ensemble_members: int = 1
    ensemble_perturbation_pct: float = 0.0
    truth_note: str = ""

    @property
    def n_steps(self) -> int:
        return int(self.duration_min / self.timestep_min)


def _profile(*points: Tuple[float, float]) -> StormTemporalProfile:
    return StormTemporalProfile(points)


SCENARIOS: Dict[str, ScenarioDefinition] = {
    "SCN-01": ScenarioDefinition(
        scenario_id="SCN-01",
        name="MODERATE MONSOON",
        description=(
            "Normal rainfall response: moderate, spatially distributed "
            "rainfall; drainage mostly below capacity; little/no surface "
            "inundation. Demonstrates the baseline pipeline."
        ),
        duration_min=180,
        timestep_min=15,
        base_rainfall_mm_h=2.0,
        peak_mm_h=18.0,
        storm_profile=_profile((0.0, 0.2), (0.3, 0.6), (0.5, 1.0), (0.7, 0.6), (1.0, 0.15)),
        storm_core=StormSpatialCore(
            center_subcatchment="SC-01", center_utm=None,
            sigma_x_m=4500.0, sigma_y_m=4500.0, translation_m_per_s=(0.6, 0.2),
        ),
        truth_note="controlled reference: local (non-routed) depression accumulation",
    ),
    "SCN-02": ScenarioDefinition(
        scenario_id="SCN-02",
        name="LOCALIZED CLOUD BURST",
        description=(
            "Rapid local flooding: intense rainfall concentrated over a "
            "small upstream area (SC-01 / Africa Avenue headwaters); quick "
            "runoff response; localized hydraulic exceedance and surface "
            "flooding."
        ),
        duration_min=120,
        timestep_min=15,
        base_rainfall_mm_h=0.5,
        peak_mm_h=72.0,
        storm_profile=_profile((0.0, 0.1), (0.2, 0.4), (0.35, 0.9), (0.45, 1.0), (0.55, 0.5), (1.0, 0.05)),
        storm_core=StormSpatialCore(
            center_subcatchment="SC-01", center_utm=None,
            sigma_x_m=1500.0, sigma_y_m=1000.0, translation_m_per_s=(0.30, 0.0),
        ),
        truth_note="controlled reference: local non-routed accumulation (intense core)",
    ),
    "SCN-03": ScenarioDefinition(
        scenario_id="SCN-03",
        name="EXTREME STORM",
        description=(
            "Severe event progression: sustained high intensity, broad "
            "spatial coverage, pronounced peak mid-event, significant "
            "depth growth across the corridor."
        ),
        duration_min=180,
        timestep_min=15,
        base_rainfall_mm_h=4.0,
        peak_mm_h=91.0,  # the documented observed Delhi extreme hour (EV-01 Safdarjung)
        storm_profile=_profile((0.0, 0.1), (0.2, 0.5), (0.45, 0.9), (0.55, 1.0), (0.8, 0.5), (1.0, 0.1)),
        storm_core=StormSpatialCore(
            center_subcatchment="SC-03", center_utm=None,
            sigma_x_m=6000.0, sigma_y_m=4000.0, translation_m_per_s=(0.5, 0.15),
        ),
        truth_note="controlled reference: local accumulation across the full corridor window",
    ),
    "SCN-04": ScenarioDefinition(
        scenario_id="SCN-04",
        name="HIGH-TIDE COMPOUND EVENT",
        description=(
            "Heavy rainfall with an elevated SYNTHETIC downstream boundary "
            "level: the terminal edge's effective conveyance is reduced by "
            "a documented backwater factor -> earlier/stronger overload "
            "potential and prolonged inundation. The boundary level is a "
            "clearly synthetic profile, never a historical tide truth."
        ),
        duration_min=180,
        timestep_min=15,
        base_rainfall_mm_h=3.0,
        peak_mm_h=60.0,
        storm_profile=_profile((0.0, 0.1), (0.25, 0.5), (0.5, 1.0), (0.75, 0.7), (1.0, 0.2)),
        storm_core=StormSpatialCore(
            center_subcatchment="SC-04", center_utm=None,
            sigma_x_m=5000.0, sigma_y_m=3500.0, translation_m_per_s=(0.4, 0.1),
        ),
        boundary_profile=SyntheticBoundaryProfile(
            label="SYNTHETIC COMPOUND BOUNDARY (SCN-04)",
            level_m=207.5,
            backwater_factor=0.55,
        ),
        truth_note="controlled reference; synthetic boundary is experimental forcing",
    ),
    "SCN-05": ScenarioDefinition(
        scenario_id="SCN-05",
        name="DRAINAGE CAPACITY CONSTRAINT",
        description=(
            "Sensitivity to drainage condition: rainfall comparable to "
            "SCN-02, but the documented capacity class is deliberately "
            "reduced (effective_conveyance_multiplier=0.65) -> overload "
            "potential appears earlier under the same rain. This is "
            "synthetic experimental forcing, NOT a claim about actual "
            "blockage."
        ),
        duration_min=120,
        timestep_min=15,
        base_rainfall_mm_h=0.5,
        peak_mm_h=72.0,
        storm_profile=_profile((0.0, 0.1), (0.2, 0.4), (0.35, 0.9), (0.45, 1.0), (0.55, 0.5), (1.0, 0.05)),
        storm_core=StormSpatialCore(
            center_subcatchment="SC-01", center_utm=None,
            sigma_x_m=1500.0, sigma_y_m=1000.0, translation_m_per_s=(0.30, 0.0),
        ),
        drainage_modifier=0.65,
        truth_note="controlled reference (same rainfall core as SCN-02)",
    ),
    "SCN-06": ScenarioDefinition(
        scenario_id="SCN-06",
        name="FORECAST UNCERTAINTY / ENSEMBLE",
        description=(
            "Same basic storm, six rainfall realizations perturbed within "
            "documented bounds (seeded, deterministic): an ensemble of "
            "flood-depth trajectories with a min/mean/max envelope. The "
            "envelope is NOT a confidence interval."
        ),
        duration_min=120,
        timestep_min=15,
        base_rainfall_mm_h=2.0,
        peak_mm_h=45.0,
        storm_profile=_profile((0.0, 0.1), (0.3, 0.6), (0.5, 1.0), (0.7, 0.5), (1.0, 0.1)),
        storm_core=StormSpatialCore(
            center_subcatchment="SC-02", center_utm=None,
            sigma_x_m=4000.0, sigma_y_m=3000.0, translation_m_per_s=(0.3, 0.1),
        ),
        ensemble_members=6,
        ensemble_perturbation_pct=15.0,
        truth_note="ensemble truth = the UNPERTURBED reference realization",
    ),
}

DEFAULT_DEMO_SCENARIO = "SCN-03"


def get_scenario(scenario_id: str) -> ScenarioDefinition:
    if scenario_id not in SCENARIOS:
        raise KeyError(f"unknown scenario {scenario_id}")
    return SCENARIOS[scenario_id]


def scenarios_meta() -> List[dict]:
    return [
        {
            "scenario_id": s.scenario_id,
            "name": s.name,
            "description": s.description,
            "duration_min": s.duration_min,
            "timestep_min": s.timestep_min,
            "n_steps": s.n_steps,
            "seed": s.seed,
            "ensemble_members": s.ensemble_members,
            "drainage_modifier": s.drainage_modifier,
            "boundary_profile": (
                s.boundary_profile.label if s.boundary_profile else None
            ),
            "default_demo": s.scenario_id == DEFAULT_DEMO_SCENARIO,
        }
        for s in SCENARIOS.values()
    ]


def depth_config() -> dict:
    return {
        "thresholds_cm": DEPTH_THRESHOLDS_CM,
        "thresholds_label": DEPTH_THRESHOLDS_LABEL,
        "routing_hazard_cm": ROUTING_HAZARD_CM,
        "routing_exclude_cm": ROUTING_EXCLUDE_CM,
    }