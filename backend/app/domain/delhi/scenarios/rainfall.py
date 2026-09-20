"""Seeded, physically plausible synthetic rainfall generator.

Produces a time series of SPATIAL rainfall fields (mm/h per surface-window
cell) from a ScenarioDefinition:

    rain(x, y, t) = base + amp(t) * core(x - xc(t), y - yc(t))

- amp(t): piecewise-linear hyetograph from the scenario's profile points.
- core: elliptical Gaussian (sigma_x, sigma_y) centered at the scenario's
  storm core, translated by the documented storm-movement vector.
- The storm center anchors to a DOCUMENTED subcatchment centroid when the
  scenario declares one (real geometry anchor; synthetic intensities).

Determinism: SCN-01..05 use NO randomness (pure functions). SCN-06 adds
seeded, deterministic multiplicative perturbations per member.

The window-mean depth per step is what the CANONICAL rainfall->inflow
interface consumes; the full spatial field feeds the 2D surface pass and
per-zone telemetry — the spatial pattern is never discarded.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Optional, Tuple

import numpy as np

from backend.app.domain.delhi.surface import get_surface_structure
from backend.app.domain.delhi.scenarios.config import ScenarioDefinition

# Documented subcatchment centroids (UTM 43N), from the DERIVED
# subcatchment inventory.
SUBCATCHMENT_CENTROIDS_UTM: dict = {
    "SC-01": (725975.0, 3163730.0),
    "SC-02": (724460.0, 3161830.0),
    "SC-03": (727430.0, 3164100.0),
    "SC-04": (728180.0, 3165300.0),
    "SC-05": (730050.0, 3165200.0),
}


def _amplitude(time_min: float, duration_min: int, profile) -> float:
    """Piecewise-linear interpolation of the scenario hyetograph."""
    f = time_min / max(duration_min, 1)
    pts = profile.points
    if f <= pts[0][0]:
        return pts[0][1]
    if f >= pts[-1][0]:
        return pts[-1][1]
    for (f0, a0), (f1, a1) in zip(pts, pts[1:]):
        if f0 <= f <= f1:
            if f1 == f0:
                return a1
            return a0 + (a1 - a0) * (f - f0) / (f1 - f0)
    return pts[-1][1]


def generate_storm_field(
    scenario: ScenarioDefinition,
    window_cells_utm: np.ndarray,  # (n, 2) UTM coords of the window cells
    timestep_index: int,
    member_scale: float = 1.0,  # SCN-06 seeded perturbation per member
) -> np.ndarray:
    """Field of rainfall depths (mm over the step) per window cell.

    Deterministic given (scenario, index, member_scale)."""
    timestep_min = scenario.timestep_min
    t_start = timestep_index * timestep_min
    t_end = t_start + timestep_min
    total_min = max(scenario.duration_min, 1)

    # Intensity (mm/h) at the step centroid, converted to depth over dt.
    t_mid = (t_start + t_end) / 2.0
    intensity_mm_h = (
        scenario.base_rainfall_mm_h
        + scenario.peak_mm_h * _amplitude(t_mid, total_min, scenario.storm_profile)
    ) * member_scale
    depth_mm = intensity_mm_h * timestep_min / 60.0  # areal (domain-mean) depth

    core = scenario.storm_core
    if core is None:
        return np.full(window_cells_utm.shape[0], depth_mm)

    # Storm center with translation.
    if core.center_utm is not None:
        cx, cy = core.center_utm
    else:
        cx, cy = SUBCATCHMENT_CENTROIDS_UTM.get(
            core.center_subcatchment or "SC-01",
            SUBCATCHMENT_CENTROIDS_UTM["SC-01"],
        )
    moved_x = cx + core.translation_m_per_s[0] * t_mid * 60.0
    moved_y = cy + core.translation_m_per_s[1] * t_mid * 60.0

    dx = (window_cells_utm[:, 0] - moved_x) / core.sigma_x_m
    dy = (window_cells_utm[:, 1] - moved_y) / core.sigma_y_m
    gaussian = np.exp(-0.5 * (dx * dx + dy * dy))
    # Window mean of the field is the forcing depth consumed by the
    # canonical rainfall->inflow interface; the spatial pattern is carried
    # separately into the surface pass.
    field = depth_mm * gaussian
    return field


def window_mean_depth_mm(field: np.ndarray) -> float:
    return float(np.mean(field))


def generate_scenario_forcing(
    scenario: ScenarioDefinition, member_scale: float = 1.0
) -> Tuple[List[float], List[np.ndarray]]:
    """Return (window_mean_depths_mm per step, spatial fields per step)."""
    structure = get_surface_structure()
    rows = structure.window_rows
    cols = structure.window_cols
    import rasterio

    xs, ys = rasterio.transform.xy(
        structure.transform, rows, cols, offset="center"
    )
    utm_cells = np.column_stack([np.asarray(xs), np.asarray(ys)])

    depths: List[float] = []
    fields: List[np.ndarray] = []
    for i in range(scenario.n_steps):
        field = generate_storm_field(scenario, utm_cells, i, member_scale)
        # The TEMPORAL PROFILE defines the domain-average (areal) rainfall
        # depth for the step; the (translated, elliptical) Gaussian
        # redistributes it spatially with the field's window mean equal to
        # the areal depth. Storm movement reshapes WHERE rain falls without
        # distorting the areal total.
        mean_f = float(np.mean(field))
        areal_depth = _areal_depth_mm(scenario, i, member_scale)
        if mean_f <= 1e-12:
            fields.append(np.full_like(field, areal_depth))
            depths.append(areal_depth)
            continue
        normalized = np.maximum(field / mean_f, 0.0) * areal_depth
        fields.append(normalized)
        depths.append(areal_depth)
    return depths, fields


def _areal_depth_mm(scenario, timestep_index: int, member_scale: float = 1.0) -> float:
    """The scenario areal rainfall depth over one timestep (mm)."""
    timestep_min = scenario.timestep_min
    t_mid = (timestep_index + 0.5) * timestep_min
    intensity_mm_h = (
        scenario.base_rainfall_mm_h
        + scenario.peak_mm_h * _amplitude(t_mid, max(scenario.duration_min, 1), scenario.storm_profile)
    ) * member_scale
    return round(intensity_mm_h * timestep_min / 60.0, 4)


def member_scale_for(scenario: ScenarioDefinition, member_index: int) -> float:
    """Deterministic seeded perturbation: member m scales peak intensity by
    1 +- perturbation_pct within a fixed bounding-grid (documented: the
    spread is a DEMO uncertainty envelope, not a confidence interval)."""
    if scenario.ensemble_members <= 1:
        return 1.0
    n = scenario.ensemble_members
    pct = scenario.ensemble_perturbation_pct / 100.0
    if n == 1:
        return 1.0
    # Member 0 = unperturbed reference; the rest spread across the bounds.
    if member_index == 0:
        return 1.0
    # Members spread evenly and symmetrically in [1-pct, 1+pct] about the
    # unperturbed reference (member 0 = the scenario truth baseline).
    if n == 2:
        return round(1.0 + pct, 4)
    # linspace(-1, 1, n-1): even including a possible 0 (a member identical
    # to the reference is an allowed deterministic member).
    offsets = [2.0 * i / (n - 2) - 1.0 for i in range(n - 1)] if n > 2 else [-1.0]
    if member_index == 0:
        return 1.0
    return round(1.0 + pct * offsets[member_index - 1], 4)