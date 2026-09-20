"""Synthetic scenario API (/api/scenarios).

Conventions follow the existing Delhi router: explicit states, full
provenance, deterministic runs, no fabricated claims. Synthetic mode is
explicitly opt-in and NEVER feeds production/live mode.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query

from backend.app.domain.delhi.scenarios.config import (
    DEFAULT_DEMO_SCENARIO,
    depth_config,
    get_scenario,
    scenarios_meta,
)
from backend.app.domain.delhi.scenarios.engine import (
    get_run_status,
    load_scenario_result,
    run_id_for,
    run_scenario,
)

router = APIRouter(prefix="/api/scenarios", tags=["synthetic-scenarios"])


def _iso(dt: Optional[datetime]) -> Optional[str]:
    return dt.isoformat() if dt is not None else None


@router.get("")
def list_scenarios() -> Dict[str, Any]:
    return {
        "scenarios": scenarios_meta(),
        "default_demo_scenario": DEFAULT_DEMO_SCENARIO,
        "depth_config": depth_config(),
        "mode": "SYNTHETIC-SCENARIO (opt-in; never consumed by production/live)",
        "claim_policy": (
            "SIMULATED / SYNTHETIC SCENARIOS demonstrate system behaviour "
            "under controlled, reproducible forcing. They are NOT real "
            "observations, NOT real-event accuracy, and NOT a prediction "
            "for any city."
        ),
    }


@router.get("/config")
def get_scenario_config() -> Dict[str, Any]:
    """The ONE canonical configuration: depth classification thresholds,
    routing hazard thresholds. Backend, map legend, and routing consume
    exactly this (never hardcoded elsewhere)."""
    return depth_config()


@router.get("/{scenario_id}")
def scenario_meta(scenario_id: str) -> Dict[str, Any]:
    try:
        s = get_scenario(scenario_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"unknown scenario {scenario_id}")
    core = s.storm_core
    return {
        "scenario_id": s.scenario_id,
        "name": s.name,
        "description": s.description,
        "duration_min": s.duration_min,
        "timestep_min": s.timestep_min,
        "n_steps": s.n_steps,
        "seed": s.seed,
        "rainfall": {
            "base_mm_h": s.base_rainfall_mm_h,
            "peak_mm_h": s.peak_mm_h,
            "storm_profile": list(s.storm_profile.points),
            "spatial_core": (
                {
                    "center_subcatchment": core.center_subcatchment,
                    "sigma_x_m": core.sigma_x_m,
                    "sigma_y_m": core.sigma_y_m,
                    "translation_m_per_s": list(core.translation_m_per_s),
                }
                if core else None
            ),
        },
        "boundary_conditions": (
            {
                "label": s.boundary_profile.label,
                "level_m": s.boundary_profile.level_m,
                "backwater_factor": s.boundary_profile.backwater_factor,
                "note": "documented SYNTHETIC boundary; never a historical tide",
            }
            if s.boundary_profile else "NONE (default closed-boundary scenario)"
        ),
        "drainage_modifier": s.drainage_modifier,
        "initial_conditions": {"storage_m3": 10000.0, "note": "documented scenario convention"},
        "ensemble_members": s.ensemble_members,
        "ensemble_perturbation_pct": s.ensemble_perturbation_pct,
        "truth_note": s.truth_note,
        "provenance": {
            "source_type": "SIMULATED",
            "generated_by": "backend.app.domain.delhi.scenarios",
            "generation_method": "seeded synthetic forcing through the canonical runtime pipeline",
            "claim": "synthetic demonstration; not real observations or real-event accuracy",
        },
    }


@router.post("/{scenario_id}/run")
def run_scenario_endpoint(
    scenario_id: str,
    seed: Optional[int] = Query(None, description="Deterministic seed (default = scenario seed)"),
    member: Optional[int] = Query(None, description="Single member index (SCN-06) or None for the full ensemble"),
) -> Dict[str, Any]:
    """Execute the scenario through the canonical pipeline (deterministic;
    identical inputs reproduce identical results)."""
    try:
        get_scenario(scenario_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"unknown scenario {scenario_id}")
    try:
        result = run_scenario(scenario_id, seed=seed, member_index=member)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"scenario run failed: {str(exc)[:300]}")
    return {
        "run_id": result["run_id"],
        "scenario_id": scenario_id,
        "status": result["status"],
        "deterministic": True,
        "detail_url": f"/api/scenarios/{scenario_id}/results?run_id={result['run_id']}",
        "status_url": f"/api/scenarios/{scenario_id}/status?run_id={result['run_id']}",
    }


@router.get("/{scenario_id}/status")
def scenario_status(scenario_id: str, run_id: str) -> Dict[str, Any]:
    rec = get_run_status(run_id)
    if rec is None:
        # Fall back to the persisted deterministic result (completed).
        persisted = load_scenario_result(run_id)
        if persisted is not None:
            return {
                "run_id": run_id,
                "scenario_id": scenario_id,
                "status": "COMPLETED",
                "timestamps": {"queued": None, "running": None, "completed": persisted["generated_at"]},
            }
        raise HTTPException(status_code=404, detail=f"unknown run {run_id}")
    return {"run_id": run_id, "scenario_id": scenario_id, **rec}


@router.get("/{scenario_id}/results")
def scenario_results(
    scenario_id: str,
    run_id: str,
    timestep_index: Optional[int] = Query(None),
) -> Dict[str, Any]:
    """Full scenario results (deterministic; persisted). Optional
    timestep_index returns a compact per-timestep view."""
    result = load_scenario_result(run_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"unknown run {run_id}")
    if result.get("scenario_id") != scenario_id:
        raise HTTPException(status_code=409, detail="run/scenario mismatch")
    if timestep_index is None:
        return result
    if not 0 <= timestep_index < result["n_steps"]:
        raise HTTPException(status_code=400, detail=f"timestep_index must be in [0, {result['n_steps'] - 1}]")
    m0 = result["members"][0]
    return {
        "run_id": run_id,
        "scenario_id": scenario_id,
        "timestep_index": timestep_index,
        "step": m0["steps"][timestep_index] if timestep_index < len(m0["steps"]) else None,
        "telemetry": m0["telemetry"]["steps"][timestep_index] if timestep_index < len(m0["telemetry"]["steps"]) else None,
        "road_depths": m0.get("road_depths", {}),
        "edge_depths": m0.get("edge_depths", {}),
        "ensemble_envelope": result.get("ensemble_envelope"),
        "truth_step": result["truth"]["steps"][timestep_index] if timestep_index < len(result["truth"]["steps"]) else None,
        "provenance": {
            "source_type": result["source_type"],
            "scenario_id": scenario_id,
            "run_id": run_id,
            "claim_policy": result["claim_policy"],
        },
    }


@router.get("/{scenario_id}/validation")
def scenario_validation(scenario_id: str, run_id: str) -> Dict[str, Any]:
    result = load_scenario_result(run_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"unknown run {run_id}")
    validation = result.get("synthetic_validation")
    if validation is None:
        raise HTTPException(status_code=409, detail="run has no synthetic validation record")
    return {
        "run_id": run_id,
        "scenario_id": scenario_id,
        "category": validation["category"],
        "note": validation["note"],
        "aggregated": validation["aggregated"],
        "claim_policy": (
            "SYNTHETIC VALIDATION on CONTROLLED TEST DATA only. This is "
            "completely separate from real-event validation and says "
            "nothing about real-world accuracy."
        ),
    }