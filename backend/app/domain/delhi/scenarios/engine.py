"""Synthetic scenario engine: run scenarios through the CANONICAL pipeline.

Flow (all steps reuse existing runtime abstractions — nothing is
frontend-only or hardcoded):

    Scenario -> spatial rainfall fields -> window-mean forcing depths
      -> run_integrated_simulation (rainfall_to_inflow + hydrograph run)
      -> advance_chain_series (corridor routing)
      -> surface_pass (2D D8 pass with the SPATIAL field)
      -> flood depth field (cm) + classification + hotspots
      -> road-segment depth (edge midpoint samples the surface field)
      -> drainage-graph loading (with optional scenario modifiers)
      -> synthetic telemetry (derived, internally consistent)
      -> controlled synthetic ground truth (independent local reference)
      -> safe-routing integration (road-hazard risk override)

Provenance discipline: every output carries source_type SIMULATED /
SIMULATED_MODEL_OUTPUT / SYNTHETIC_GROUND_TRUTH with scenario_id and
generation metadata; synthetic validation is a SEPARATE category.
Production/live mode never consumes synthetic data.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

from backend.app.domain.delhi.digital_twin.kushak_evidence_model import (
    KUSHAK_HYDRAULIC_SCENARIOS,
    backbone_slope_m_per_m,
    covered_effective_profile,
)
from backend.app.domain.delhi.digital_twin.kushak_continuity_routing import (
    ChainStepSpec,
    advance_chain_series,
)
from backend.app.domain.delhi.digital_twin.kushak_serial_routing import (
    OutflowRule,
    ReachOutflowDecision,
)
from backend.app.domain.delhi.digital_twin.hydraulic_integrated_orchestrator import (
    run_integrated_simulation,
)
from backend.app.domain.delhi.digital_twin.hydraulic_time_state import (
    SimulationState,
    SimulationStateStatus,
    SimulationTimestep,
)
from backend.app.domain.delhi.digital_twin.models import ProvenanceStatus
from backend.app.domain.delhi.digital_twin.kushak_scenario_ensemble import (
    SCENARIO_RUNOFF_C,
)
from backend.app.domain.delhi.drainage.graph import get_drainage_graph
from backend.app.domain.delhi.drainage.loading import (
    INITIAL_STORAGE_M3,
    channel_depth_estimate_cm,
)
from backend.app.domain.delhi.surface import get_surface_structure, surface_pass
from backend.app.domain.delhi.scenarios.config import (
    DEFAULT_DEMO_SCENARIO,
    classify_depth_cm,
    depth_config,
    get_scenario,
)
from backend.app.domain.delhi.scenarios.rainfall import (
    generate_scenario_forcing,
    member_scale_for,
)
from backend.app.domain.delhi.scenarios.depth_v1 import (
    V1DepthStep,
    depth_cells_from_v1,
    depth_polygons_from_v1,
    road_depths_from_v1,
    scenario_v1_depth_steps,
)

CHAIN_REACH_IDS = ("UG-01", "OC-01", "CD-01", "OC-02")
PUMP_THRESHOLD_M3_S = 8.0  # demo threshold (configurable)
SIM = "SIMULATED"
SIM_MODEL = "SIMULATED_MODEL_OUTPUT"
SIM_TRUTH = "SYNTHETIC_GROUND_TRUTH"

_RUN_REGISTRY: Dict[str, dict] = {}
_SCENARIO_PAYLOAD_CACHE: Dict[str, dict] = {}
_SCENARIO_RUN_ROOT = Path(__file__).resolve().parents[5] / "data" / "delhi" / "derived" / "scenarios"
_BUNDLED_SCENARIO_ROOT = Path(__file__).resolve().parents[3] / "data" / "scenarios"


# ---------------------------------------------------------------------------
# Run lifecycle (QUEUED -> RUNNING -> COMPLETED / FAILED)
# ---------------------------------------------------------------------------


def _chain_decisions() -> Dict[str, ReachOutflowDecision]:
    decisions: Dict[str, ReachOutflowDecision] = {}
    for reach_id in ("UG-01", "OC-01", "CD-01"):
        decisions[reach_id] = ReachOutflowDecision(
            reach_id=reach_id,
            rule=OutflowRule.EXPLICIT_SUPPLIED,
            explicit_outflow_m3_s=0.0,
            explicit_outflow_provenance=ProvenanceStatus.ASSUMED,
            effective_scenario_declared=(reach_id == "UG-01"),
        )
    return decisions


_CHAIN_DECISIONS = _chain_decisions()


def run_id_for(scenario_id: str, seed: int) -> str:
    digest = hashlib.sha256(f"synthetic:{scenario_id}:{seed}".encode()).hexdigest()[:12]
    return f"sim-{scenario_id}-{digest}"


def start_scenario_run(scenario_id: str, seed: int) -> dict:
    """Register/return the deterministic run lifecycle record."""
    run_id = run_id_for(scenario_id, seed)
    if run_id in _RUN_REGISTRY and _RUN_REGISTRY[run_id]["status"] == "COMPLETED":
        return _RUN_REGISTRY[run_id]
    _RUN_REGISTRY[run_id] = {
        "run_id": run_id,
        "scenario_id": scenario_id,
        "seed": seed,
        "status": "QUEUED",
        "timestamps": {"queued": datetime.now(timezone.utc).isoformat()},
    }
    return _RUN_REGISTRY[run_id]


def set_run_status(run_id: str, status: str) -> None:
    rec = _RUN_REGISTRY[run_id]
    rec["status"] = status
    rec["timestamps"][status.lower()] = datetime.now(timezone.utc).isoformat()


def get_run_status(run_id: str) -> Optional[dict]:
    return _RUN_REGISTRY.get(run_id)


# ---------------------------------------------------------------------------
# Canonical single-member execution
# ---------------------------------------------------------------------------


def _run_member(
    scenario_id: str,
    seed: int,
    member_index: int,
    depths: List[float],
    fields: List[np.ndarray],
) -> dict:
    scenario = get_scenario(scenario_id)
    timestep_min = scenario.timestep_min
    timesteps = [
        SimulationTimestep(
            start=datetime(2026, 9, 17, 0, 0, tzinfo=timezone.utc) + timedelta(minutes=i * timestep_min),
            end=datetime(2026, 9, 17, 0, 0, tzinfo=timezone.utc) + timedelta(minutes=(i + 1) * timestep_min),
        )
        for i in range(scenario.n_steps)
    ]

    # Scenario hydraulic basis: CENTRAL, with the experimental drainage
    # modifier applied to the capacity-class multipliers (SCN-05) and the
    # synthetic boundary backwater applied to the terminal edge (SCN-04).
    import dataclasses

    base = KUSHAK_HYDRAULIC_SCENARIOS["CENTRAL"]
    modifier = scenario.drainage_modifier
    if modifier is not None:
        base = dataclasses.replace(
            base,
            scenario_id=f"SCENARIO-{scenario_id}",
            mult_box=round(max(base.mult_box * modifier, 1e-4), 4),
            mult_open=round(max(base.mult_open * modifier, 1e-4), 4),
        )
    profile, profile_meta = covered_effective_profile(base)
    slope = backbone_slope_m_per_m()

    initial_state = SimulationState(
        timestamp=timesteps[0].start,
        location_id=f"SIM-{scenario_id}-m{member_index}",
        status=SimulationStateStatus.COMPUTED,
        stage_m=profile_meta["bed_elevation_m"] + 1.0,
        storage_m3=INITIAL_STORAGE_M3,
        provenance=ProvenanceStatus.DERIVED,
    )
    integrated = run_integrated_simulation(
        initial_state=initial_state,
        timesteps=timesteps,
        rainfall_depth_mm=depths,
        catchment_area_km2=27.66,  # documented working catchment
        runoff_coefficient=SCENARIO_RUNOFF_C,
        profile=profile,
        manning_n=base.effective_manning_n_box,
        slope=slope,
        catchment_area_provenance=ProvenanceStatus.PROVISIONAL,
        runoff_coefficient_provenance=ProvenanceStatus.ASSUMED,
        explicit_outflow_m3_s=0.0,
        explicit_outflow_provenance=ProvenanceStatus.ASSUMED,
        lateral_inflow_m3_s=0.0,
        lateral_inflow_provenance=ProvenanceStatus.ASSUMED,
        manning_n_provenance=ProvenanceStatus.ASSUMED,
        slope_provenance=ProvenanceStatus.DERIVED,
        source_id=f"synthetic:{scenario_id}:{seed}:m{member_index}",
    )
    hydrograph = integrated.rainfall_conversion.hydrograph

    # Corridor chain (storage trajectory) — canonical continuity.
    step_specs = []
    if hydrograph is not None:
        for i, ts in enumerate(timesteps):
            q = hydrograph.steps[i].discharge_m3_s if i < len(hydrograph.steps) else None
            step_specs.append(ChainStepSpec(
                timestep=ts,
                head_flow_m3_s=q,
                head_flow_provenance=(
                    ProvenanceStatus.DERIVED if q is not None else ProvenanceStatus.UNKNOWN
                ),
                laterals={rid: 0.0 for rid in CHAIN_REACH_IDS},
                lateral_provenances={rid: ProvenanceStatus.ASSUMED for rid in CHAIN_REACH_IDS},
                decisions=_CHAIN_DECISIONS,
            ))
    chain = advance_chain_series(
        tuple(step_specs),
        initial_storage={rid: INITIAL_STORAGE_M3 for rid in CHAIN_REACH_IDS},
        initial_storage_provenance={rid: ProvenanceStatus.ASSUMED for rid in CHAIN_REACH_IDS},
    )

    # FLOOD DEPTH: the V1 REFERENCE model (Mumbai/Kurla route_flood_depth
    # semantics) on the Delhi window — runoff distributed to drainage
    # inlets, capacity conveyed, surcharge routed to equilibrium depth.
    structure = get_surface_structure()
    graph = get_drainage_graph()
    modifier = scenario.drainage_modifier
    cap_scale = modifier if modifier is not None else 1.0
    capacity_by_edge = {
        e.edge_id: e.capacity_min_m3_s * cap_scale for e in graph.edges
    }
    import rasterio
    import rasterio.warp as rw

    edge_node_local: Dict[str, int] = {}
    edge_midpoints: Dict[str, Tuple[float, float]] = {}
    win_x, win_y = rasterio.transform.xy(
        structure.transform, structure.window_rows, structure.window_cols, offset="center"
    )
    win_x = np.asarray(win_x)
    win_y = np.asarray(win_y)
    for e in graph.edges:
        coords = e.geometry_wgs84
        mid = coords[len(coords) // 2]
        edge_midpoints[e.edge_id] = mid
        ux, uy = rw.transform("EPSG:4326", structure.crs, [mid[0]], [mid[1]])
        d = (win_x - ux[0]) ** 2 + (win_y - uy[0]) ** 2
        edge_node_local[e.edge_id] = int(np.argmin(d))

    scale = member_scale_for(scenario, member_index)
    v1_steps: List[V1DepthStep] = scenario_v1_depth_steps(
        scenario, scale, capacity_by_edge, fields
    )

    # Corridor lateral-inflow proxy (surface pass; separate product).
    surface = surface_pass(
        depths,
        [timestep_min / 60.0] * len(depths),
        spatial_fields=fields,
    )

    # Per-step depth products (V1 reference grid).
    steps: List[dict] = []
    max_depth_cm_track: List[float] = []
    _depth_fields_collector: List[np.ndarray] = []
    for i, ts in enumerate(timesteps):
        v1 = v1_steps[i]
        surf = surface["timesteps"][i]
        max_cm = v1.max_depth_m * 100.0
        max_depth_cm_track.append(max_cm)
        _depth_fields_collector.append(np.asarray(v1.depth_m * 100.0, dtype=np.float64))
        steps.append({
            "timestep_index": i,
            "depth_cells": depth_cells_from_v1(v1, structure),
            "depth_polygons": depth_polygons_from_v1(v1, structure),
            "time_start": ts.start.isoformat(),
            "time_end": ts.end.isoformat(),
            "max_depth_cm": round(max_cm, 1),
            "flooded_cells": v1.flooded_cells,
            "flood_state": classify_depth_cm(max_cm),
            "per_reach_surface_inflow_m3_s": surf["per_reach_surface_inflow_m3_s"],
            "v1_mass_balance": {
                "total_runoff_m3": round(v1.total_runoff_volume_m3, 1),
                "conveyed_m3": round(v1.conveyed_volume_m3, 1),
                "surcharged_m3": round(v1.surcharged_volume_m3, 1),
                "drained_out_m3": round(v1.drained_out_volume_m3, 1),
            },
            "source_type": SIM_MODEL,
        })

    # Drain-edge channel depth estimates + loading under the scenario.
    edges = get_drainage_graph().edges
    edge_depths: Dict[str, dict] = {}
    for edge in edges:
        storage = _storage_for_reach(chain, edge.reach_id)
        est = channel_depth_estimate_cm(edge, storage)
        edge_depths[edge.edge_id] = {
            "reach_id": edge.reach_id,
            "node_id": edge.downstream_node_id,
            **{k: v for k, v in est.items() if k in ("depth_min_cm", "depth_max_cm", "status", "reason")},
            "provenance": "ESTIMATED_UNDER_ASSUMED_GEOMETRY (synthetic scenario)",
            "scenario_id": scenario_id,
            "source_type": SIM_MODEL,
        }

    # Road-segment depth: V1-style spatial matching on the reference grid.
    road_depths = road_depths_from_v1(v1_steps[-1], structure, edge_midpoints)

    # Peak modeled inflow per reach across the chain (scenario-derived).
    inflow_by_reach: Dict[str, Optional[float]] = {rid: None for rid in CHAIN_REACH_IDS}
    blocked_reach = {rid: False for rid in CHAIN_REACH_IDS}
    for step in chain.steps:
        for r in step.results:
            rid = r.state.reach_id
            if r.state.hydraulic_status.value.startswith("BLOCKED") or r.state.incoming_flow_m3_s is None:
                blocked_reach[rid] = True
                continue
            q = r.state.incoming_flow_m3_s
            if inflow_by_reach[rid] is None or q > inflow_by_reach[rid]:
                inflow_by_reach[rid] = q
    for rid in CHAIN_REACH_IDS:
        if blocked_reach[rid] and inflow_by_reach[rid] is None:
            inflow_by_reach[rid] = None  # blocked: UNKNOWN, never zero
        elif inflow_by_reach[rid] is None:
            inflow_by_reach[rid] = 0.0  # computed but no positive inflow

    inflow_series = (
        [s.discharge_m3_s for s in hydrograph.steps] if hydrograph else []
    )
    telemetry = _build_telemetry(
        scenario_id=scenario_id,
        seed=seed,
        timesteps=timesteps,
        depths=depths,
        inflow=inflow_series,
        edge_depths=edge_depths,
        boundary=scenario.boundary_profile,
    )
    # Drainage loading: final-step inflow vs the documented capacity class
    # (with the scenario's experimental modifier applied when declared).
    graph = get_drainage_graph()
    scenario_loading = []
    for edge in graph.edges:
        inflow = inflow_by_reach.get(edge.reach_id)
        cap_lo = edge.capacity_min_m3_s * (modifier if modifier is not None else 1.0)
        cap_hi = edge.capacity_max_m3_s * (modifier if modifier is not None else 1.0)
        if inflow is None:
            status, reason = "UNKNOWN", "modeled state blocked/UNKNOWN at this step"
        elif inflow <= 0:
            status, reason = "NO_LOADING", "no modeled inflow under the scenario forcing"
        elif inflow <= cap_lo:
            status, reason = "WITHIN_CAPACITY_RANGE", (
                f"modeled inflow {inflow:.1f} m3/s within capacity class "
                f"[{cap_lo:.0f}, {cap_hi:.0f}] m3/s (scenario-derived)"
            )
        else:
            status, reason = "POTENTIAL_OVERLOAD", (
                f"modeled inflow {inflow:.1f} m3/s EXCEEDS the capacity-class "
                f"lower bound [{cap_lo:.0f}, {cap_hi:.0f}] m3/s - backflow/"
                "surcharge potential (scenario-derived, not observed)"
            )
        scenario_loading.append({
            "edge_id": edge.edge_id,
            "node_id": edge.downstream_node_id,
            "reach_id": edge.reach_id,
            "inflow_m3_s": round(inflow, 2) if inflow is not None else None,
            "capacity_min_m3_s": round(cap_lo, 1),
            "capacity_max_m3_s": round(cap_hi, 1),
            "status": status,
            "reason": reason,
        })

    return {
        "member_index": member_index,
        "telemetry": telemetry,
        "drainage_loading": scenario_loading,
        "_depth_fields": _depth_fields_collector,
        "member_scale": member_scale_for(scenario, member_index),
        "forcing_depths_mm": [round(d, 4) for d in depths],
        "inflow_m3_s": [round(q, 3) if q is not None else None for q in inflow_series],
        "steps": steps,
        "max_depth_cm_traj": [round(v, 1) for v in max_depth_cm_track],
        "edge_depths": edge_depths,
        "road_depths": road_depths,
        "source_type": SIM_MODEL,
        "scenario_id": scenario_id,
    }


def _depth_cells_for_display(depths_cm: np.ndarray, max_cells: int = 320) -> List[dict]:
    """Top depth cells for the MAP layer (real routed-field samples, WGS84).
    Reference-member only: these are the actual model-output cells, never
    fabricated values."""
    structure = get_surface_structure()
    shallow = depth_config()["thresholds_cm"]["SHALLOW"]
    cand = np.flatnonzero(depths_cm >= shallow)
    if cand.size == 0:
        return []
    cand = cand[np.argsort(depths_cm[cand])[::-1]][:max_cells]
    import rasterio
    import rasterio.warp as rw

    rows = structure.window_rows[cand]
    cols = structure.window_cols[cand]
    xs, ys = rasterio.transform.xy(structure.transform, rows, cols, offset="center")
    lons, lats = rw.transform(structure.crs, "EPSG:4326", [float(x) for x in xs], [float(y) for y in ys])
    out = []
    for j in range(len(cand)):
        cm = float(depths_cm[cand[j]])
        out.append({
            "lon": round(lons[j], 5),
            "lat": round(lats[j], 5),
            "depth_cm": round(cm, 1),
            "flood_state": classify_depth_cm(cm),
            "provenance": "SIMULATED_MODEL_OUTPUT (routed 2D surface field sample)",
        })
    return out


def _classify_field(depths_cm: np.ndarray) -> np.ndarray:
    out = np.full(depths_cm.shape, "UNKNOWN", dtype=object)
    for idx, v in np.ndenumerate(depths_cm):
        out[idx] = classify_depth_cm(float(v))
    return out


def _storage_for_reach(chain, reach_id: str) -> Optional[float]:
    vals = []
    for step in chain.steps:
        r = step.state_for(reach_id)
        if r.state.storage_m3 is not None:
            vals.append(r.state.storage_m3)
    return max(vals) if vals else None


@lru_cache(maxsize=1)
def _edge_midpoint_cells() -> Dict[str, int]:
    """Map each drainage-graph edge midpoint (UTM) to the nearest surface
    window cell local index (static; cached)."""
    structure = get_surface_structure()
    graph = get_drainage_graph()
    import rasterio

    out: Dict[str, int] = {}
    for edge in graph.edges:
        # Edge midpoint in UTM from the geometry (geometry is WGS84; project).
        coords = edge.geometry_wgs84
        mid = coords[len(coords) // 2]
        import rasterio.warp as rw

        xs, ys = rw.transform("EPSG:4326", structure.crs, [mid[0]], [mid[1]])
        # nearest window cell by distance
        win_x, win_y = rasterio.transform.xy(
            structure.transform, structure.window_rows, structure.window_cols, offset="center"
        )
        d = (np.asarray(win_x) - xs[0]) ** 2 + (np.asarray(win_y) - ys[0]) ** 2
        out[edge.edge_id] = int(np.argmin(d))
    return out


def _road_depths(final_field: np.ndarray) -> Dict[str, dict]:
    """Road-segment depth: the surface column at the segment's nearest
    window cell (from the LAST step's routed field)."""
    structure = get_surface_structure()
    cell_map = _edge_midpoint_cells()
    cols = structure.elev  # used silently? no: re-project columns to depth
    out: Dict[str, dict] = {}
    for edge_id, local_i in cell_map.items():
        cm = float(final_field[local_i])
        out[edge_id] = {
            "depth_cm": round(cm, 1),
            "depth_m": round(cm / 100.0, 3),
            "flood_state": classify_depth_cm(cm),
            "source_type": SIM_MODEL,
            "scenario_id": None,
            "uncertainty": "surface proxy (30 m DSM); UNKNOWN if the cell is invalid",
        }
    return out


# ---------------------------------------------------------------------------
# Synthetic ground truth (independent, controlled reference)
# ---------------------------------------------------------------------------


def _synthetic_truth(
    scenario_id: str, depths: List[float], fields: List[np.ndarray]
) -> List[dict]:
    """CONTROLLED SYNTHETIC TRUTH — an independent LOCAL (non-routed)
    reference: each cell accumulates its own excess into its depression,
    capped by local terrain. This deliberately uses a DIFFERENT mechanism
    than the routed surface pass, so validation compares two distinct
    model responses — the truth is NOT a copy of the displayed forecast.
    """
    scenario = get_scenario(scenario_id)
    structure = get_surface_structure()
    n = structure.cell_flat_idx.size
    cell_area = structure.cell_area_m2
    steps: List[dict] = []
    for i in range(scenario.n_steps):
        field = fields[i]
        excess_m = np.asarray(field, dtype=np.float64) / 1000.0 * SCENARIO_RUNOFF_C * 0.90
        cap_m = np.where(structure.depression_cap_m > 0.15, structure.depression_cap_m, 0.5)
        # Local reference: no D8 routing; each cell's own excess fills its
        # depression (the reference response is more "flashy" by design).
        accum_m = np.minimum(excess_m * cell_area, cap_m * cell_area)
        truth_cm = accum_m / cell_area * 100.0
        flooded = int(np.count_nonzero(truth_cm >= depth_config()["thresholds_cm"]["SHALLOW"]))
        steps.append({
            "timestep_index": i,
            "max_truth_depth_cm": round(float(np.max(truth_cm)) if truth_cm.size else 0.0, 1),
            "flooded_cells": flooded,
            "field": truth_cm,
            "source_type": SIM_TRUTH,
        })
    return steps


# ---------------------------------------------------------------------------
# Top-level scenario runner
# ---------------------------------------------------------------------------


def run_scenario(scenario_id: str, seed: Optional[int] = None, member_index: Optional[int] = None) -> dict:
    """Execute the scenario end-to-end (deterministic; cached by run_id).

    member_index None (default) runs the full ensemble (SCN-06) or the
    single member for others.
    """
    scenario = get_scenario(scenario_id)
    effective_seed = seed if seed is not None else scenario.seed
    run_id = run_id_for(scenario_id, effective_seed)

    # If default scenario configuration, return existing precomputed snapshot immediately
    if member_index is None and (seed is None or seed == scenario.seed):
        existing = load_scenario_result(run_id)
        if existing is not None:
            start_scenario_run(scenario_id, effective_seed)
            set_run_status(run_id, "COMPLETED")
            return existing

    start_scenario_run(scenario_id, effective_seed)
    set_run_status(run_id, "RUNNING")

    try:
        depths, fields = generate_scenario_forcing(scenario)
        if member_index is not None:
            scale = member_scale_for(scenario, member_index)
            depths_m = [d * scale for d in depths]
            fields_m = [f * scale for f in fields]
            result = _run_member(scenario_id, effective_seed, member_index, depths_m, fields_m)
            return _compose_result(scenario, effective_seed, run_id, [result], depths, fields,
                                   ensemble=False)
        members = []
        for m in range(scenario.ensemble_members):
            scale = member_scale_for(scenario, m)
            depths_m = [d * scale for d in depths]
            fields_m = [f * scale for f in fields]
            members.append(_run_member(scenario_id, seed, m, depths_m, fields_m))
        return _compose_result(scenario, seed, run_id, members, depths, fields,
                               ensemble=scenario.ensemble_members > 1)
    except Exception as exc:
        set_run_status(run_id, "FAILED")
        rec = _RUN_REGISTRY[run_id]
        rec["error"] = str(exc)[:400]
        raise
    finally:
        # success path sets COMPLETED inside _compose_result's caller wrapper
        pass


def _compose_result(
    scenario,
    seed: int,
    run_id: str,
    members: List[dict],
    depths: List[float],
    fields: List[np.ndarray],
    ensemble: bool,
) -> dict:
    truth = _synthetic_truth(scenario.scenario_id, depths, fields)
    n_steps = scenario.n_steps

    envelope: List[dict] = []
    for i in range(n_steps):
        vals = [m["max_depth_cm_traj"][i] for m in members if i < len(m["max_depth_cm_traj"])]
        envelope.append({
            "timestep_index": i,
            "mean_depth_cm": round(float(np.mean(vals)), 1),
            "min_depth_cm": round(float(np.min(vals)), 1),
            "max_depth_cm": round(float(np.max(vals)), 1),
            "spread_cm": round(float(np.max(vals) - np.min(vals)), 1),
            "note": "ensemble envelope from seeded synthetic members; NOT a confidence interval",
        })

    from .validation import synthetic_validation

    # Synthetic validation per member (each member's own N steps vs the N
    # truth steps): ROUTED surface depths vs the independent local truth
    # reference (separate from real-event validation).
    per_member_validation = []
    for m in members:
        fields = m.get("_depth_fields") or []
        member_steps = []
        for i, st in enumerate(m.get("steps", [])):
            member_steps.append({
                "timestep_index": st.get("timestep_index"),
                "depth_field_cm": fields[i] if i < len(fields) else None,
            })
        per_member_validation.append(synthetic_validation(member_steps, truth))
    validation = per_member_validation[0]  # reference member for the summary

    payload = {
        "synthetic_validation": validation,
        "synthetic_validation_per_member": per_member_validation,
        "run_id": run_id,
        "scenario_id": scenario.scenario_id,
        "scenario_name": scenario.name,
        "seed": seed,
        "status": "COMPLETED",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "generated_by": "backend.app.domain.delhi.scenarios.engine",
        "generation_method": (
            "seeded synthetic forcing through the canonical runtime pipeline "
            "(rainfall->inflow->chain->2D surface pass->depth->road depth)"
        ),
        "timestep_min": scenario.timestep_min,
        "n_steps": n_steps,
        "duration_min": scenario.duration_min,
        "source_type": SIM,
        "claim_policy": (
            "SIMULATED / SYNTHETIC SCENARIO: demonstrates system behaviour "
            "under controlled reproducible forcing. NOT real observations, "
            "NOT real-event accuracy, NOT a prediction for any city."
        ),
        "ensemble": ensemble,
        "members": [
            {
                k: v for k, v in m.items()
                if k in ("member_index", "member_scale", "forcing_depths_mm",
                         "inflow_m3_s", "steps", "max_depth_cm_traj",
                         "edge_depths", "road_depths", "source_type",
                         "scenario_id", "telemetry", "drainage_loading")
            }
            for m in members
        ],  # depth_cells live only on the reference member (member 0)
        "ensemble_envelope": envelope if ensemble else None,
        "truth": {
            "steps": [
                {k: v for k, v in t.items() if k != "field"} for t in truth
            ],
            "source_type": SIM_TRUTH,
            "generation_method": (
                "independent LOCAL (non-routed) depression-reference: each "
                "cell accumulates its own excess (0.90 x C) capped by local "
                "terrain — a deliberately different mechanism from the "
                "routed surface pass so validation is not circular"
            ),
            "scenario_id": scenario.scenario_id,
        },
        "provenance": {
            "source_type": SIM,
            "scenario_id": scenario.scenario_id,
            "seed": seed,
            "run_id": run_id,
            "depth_config": depth_config(),
            "timestamps": _RUN_REGISTRY.get(run_id, {}).get("timestamps", {}),
        },
    }
    set_run_status(run_id, "COMPLETED")
    _persist_result(payload)
    return payload


def _persist_result(payload: dict) -> None:
    _SCENARIO_PAYLOAD_CACHE[payload["run_id"]] = payload
    try:
        _SCENARIO_RUN_ROOT.mkdir(parents=True, exist_ok=True, mode=0o755)
        path = _SCENARIO_RUN_ROOT / f"{payload['run_id']}.json"
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass


def load_scenario_result(run_id: str) -> Optional[dict]:
    if run_id in _SCENARIO_PAYLOAD_CACHE:
        return _SCENARIO_PAYLOAD_CACHE[run_id]

    bundled_path = _BUNDLED_SCENARIO_ROOT / f"{run_id}.json"
    if bundled_path.exists():
        try:
            data = json.loads(bundled_path.read_text(encoding="utf-8"))
            _SCENARIO_PAYLOAD_CACHE[run_id] = data
            return data
        except Exception:
            pass

    path = _SCENARIO_RUN_ROOT / f"{run_id}.json"
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            _SCENARIO_PAYLOAD_CACHE[run_id] = data
            return data
        except Exception:
            pass
    return None

# Synthetic telemetry (internally consistent with scenario state; every
# reading carries source_type=SIMULATED and the scenario id).
def _build_telemetry(
    scenario_id: str,
    seed: int,
    timesteps: List[SimulationTimestep],
    depths: List[float],
    inflow: List[Optional[float]],
    edge_depths: Dict[str, dict],
    boundary,
) -> dict:
    # Sensor anchors: window cells nearest the documented subcatchment
    # centroids for the AWS rainfall sensors.
    structure = get_surface_structure()
    import rasterio

    aws_anchors = {
        "SIM-AWS-01": "SC-01",
        "SIM-AWS-02": "SC-03",
        "SIM-AWS-03": "SC-05",
    }
    from backend.app.domain.delhi.scenarios.rainfall import SUBCATCHMENT_CENTROIDS_UTM

    anchor_cells = {}
    for sensor, sub in aws_anchors.items():
        cx, cy = SUBCATCHMENT_CENTROIDS_UTM[sub]
        win_x, win_y = rasterio.transform.xy(
            structure.transform, structure.window_rows, structure.window_cols, offset="center"
        )
        d = (np.asarray(win_x) - cx) ** 2 + (np.asarray(win_y) - cy) ** 2
        anchor_cells[sensor] = int(np.argmin(d))

    drain_edges = {"SIM-DRAIN-01": "E00", "SIM-DRAIN-02": "E02", "SIM-DRAIN-03": "E05"}
    steps_out: List[dict] = []
    for i, ts in enumerate(timesteps):
        ts_iso = ts.start.isoformat()
        depth_mm = depths[i] if i < len(depths) else 0.0
        readings = []
        # AWS rainfall sensors: areal depth mapped to each anchor cell via
        # the scenario field (proxy intensity).
        for sensor, cell in anchor_cells.items():
            readings.append({
                "sensor_id": sensor,
                "timestamp": ts_iso,
                "value": round(depth_mm, 2),  # representative areal depth (mm)
                "unit": "mm",
                "source_type": SIM,
                "scenario_id": scenario_id,
                "derivation": "scenario areal rainfall mapped to the anchor subcatchment",
            })
        # Drain stage sensors: channel-depth estimate ranges at drain edges.
        for sensor, edge_id in drain_edges.items():
            est = edge_depths.get(edge_id, {})
            value = est.get("depth_max_cm") if est.get("status") == "ESTIMATED" else None
            readings.append({
                "sensor_id": sensor,
                "timestamp": ts_iso,
                "value": value,
                "unit": "cm",
                "source_type": SIM_MODEL,
                "scenario_id": scenario_id,
                "derivation": f"channel depth estimate at {edge_id} (ESTIMATED_UNDER_ASSUMED_GEOMETRY)",
                "uncertainty": None if value is None else "range [min,max] in edge_depths",
            })
        # Pump sensor: ON when UG-01 inflow exceeds the documented demo
        # threshold (8 m3/s configured in scenario config).
        q = inflow[i] if i < len(inflow) else None
        pump_on = bool(q is not None and q > PUMP_THRESHOLD_M3_S)
        readings.append({
            "sensor_id": "SIM-PUMP-01",
            "timestamp": ts_iso,
            "value": "ON" if pump_on else "OFF",
            "unit": "state",
            "source_type": SIM,
            "scenario_id": scenario_id,
            "derivation": f"derived from UG-01 modeled inflow vs demo threshold {PUMP_THRESHOLD_M3_S} m3/s",
        })
        gate_open = 1.0 - (boundary.backwater_factor if boundary else 0.0)
        readings.append({
            "sensor_id": "SIM-GATE-01",
            "timestamp": ts_iso,
            "value": round(gate_open, 2),
            "unit": "open_fraction",
            "source_type": SIM,
            "scenario_id": scenario_id,
            "derivation": (
                "synthetic downstream-boundary backwater: 1 - backwater_factor"
                if boundary else "no synthetic boundary (open fraction 1.0)"
            ),
        })
        steps_out.append({
            "timestep_index": i,
            "time_start": ts_iso,
            "readings": readings,
        })
    return {
        "sensors": {
            "SIM-AWS-01": "rainfall (anchor SC-01)",
            "SIM-AWS-02": "rainfall (anchor SC-03)",
            "SIM-AWS-03": "rainfall (anchor SC-05)",
            "SIM-DRAIN-01": "drain stage proxy (E00)",
            "SIM-DRAIN-02": "drain stage proxy (E02)",
            "SIM-DRAIN-03": "drain stage proxy (E05)",
            "SIM-PUMP-01": "pump state",
            "SIM-GATE-01": "synthetic boundary gate",
        },
        "steps": steps_out,
        "source_type": SIM,
        "scenario_id": scenario_id,
        "seed": seed,
        "note": "synthetic telemetry derived consistently from the scenario state; never presented as real sensor data",
    }
