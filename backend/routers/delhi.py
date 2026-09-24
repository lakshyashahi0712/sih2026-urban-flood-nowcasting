"""Delhi/Kushak V2 API — the operational product surface for the
evidence-constrained urban flood nowcasting system.

Every endpoint reuses the canonical domain/runtime modules (never a
parallel implementation) and exposes the repository's honest state
model: COMPUTED / UNKNOWN / BLOCKED / NOT_COMPUTED / NOT_COMPARABLE /
UNAVAILABLE. No endpoint fabricates data, promotes assumed values, or
collapses meaningful states into booleans.

Scientific claims policy for this API:
- Historical replay outputs are RUNTIME EXECUTION + qualitative
  consistency evidence. They are NOT accuracy, calibration, or depth-skill
  claims.
- Nowcast outputs are behavioral inflow/storage envelopes under documented
  effective-scenario assumptions with NWP model-forecast forcing. Stage
  and street-level depth are UNKNOWN and are never claimed.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from fastapi import APIRouter, HTTPException, Query

from backend.app.domain.delhi.digital_twin.kushak_evidence_model import (
    CATCHMENT_SCENARIOS,
    KUSHAK_HYDRAULIC_SCENARIOS,
)
from backend.app.domain.delhi.digital_twin.kushak_scenario_ensemble import (
    SCENARIO_RUNOFF_C,
    SCENARIO_RUNOFF_PROVENANCE,
    build_kushak_ensemble,
)
from backend.app.domain.delhi.digital_twin.kushak_reaches_tiered import (
    KUSHAK_MODEL_REACHES,
)
from backend.app.domain.delhi.digital_twin.kushak_event_validation import (
    VALIDATION_EVENTS,
    resolve_event_id,
)

# ---------------------------------------------------------------------------
# Phase 15.5 replay harness reuse (single source of truth — no duplication).
# The harness is a repo-root script module; it self-bootstraps its imports
# and executes nothing at import time (guarded by __main__).
# ---------------------------------------------------------------------------
_REPO_ROOT = Path(__file__).resolve().parents[2]
_SCRIPTS_DIR = _REPO_ROOT / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

try:
    import generate_phase15_replay as replay_harness
except Exception as _exc:  # pragma: no cover - surfaced as 503 at runtime
    replay_harness = None
    _HARNESS_IMPORT_ERROR = str(_exc)

from backend.app.domain.delhi.digital_twin.kushak_historical_rainfall_catalog import (
    get_forcing_for_event,
)
from backend.app.domain.delhi.digital_twin.kushak_replay_manifest import (
    get_declaration,
    replay_status_label,
)
from backend.app.domain.delhi.replay_artifacts import (
    ARTIFACTS_DIR,
    build_replay_artifact,
)
from backend.app.domain.delhi.digital_twin.kushak_event_validation import (
    TimestampPrecision,
    ValidationSourceClass,
)
from backend.app.domain.delhi.digital_twin.models import ProvenanceStatus
from backend.app.domain.delhi.nowcast import (
    SAFDARJUNG_LAT,
    SAFDARJUNG_LON,
    SAFDARJUNG_REFERENCE,
    fetch_delhi_rainfall_forecast,
    run_nowcast,
)
from backend.app.domain.delhi.routing.engine import compute_safe_route
from backend.app.domain.delhi.routing.network import get_road_graph
from backend.app.domain.delhi.routing.risk import (
    aggregate_reach_states,
    build_edge_reach_map,
    freshness_state,
    segment_evidence,
    translate_reach_to_road_risk,
)
from backend.app.domain.delhi.routing.state_source import (
    get_historical_reach_states,
    get_historical_timestep_count,
    get_live_reach_states,
)
from backend.app.domain.delhi.science.gating import production_mode
from backend.app.domain.delhi.science.ml_pipeline import production_gate
from backend.app.domain.delhi.science.validation import evaluate_quantitative_validation
from backend.app.domain.delhi.science.observation_registry import (
    build_observation_registry,
    registry_summary,
)
from backend.app.domain.delhi.science.calibration import run_calibration_framework
from backend.app.domain.delhi.science.identifiability import (
    identifiability_classification,
    oat_sensitivity,
)
from backend.app.domain.delhi.science.uncertainty import uncertainty_decomposition
from backend.app.domain.delhi.drainage.graph import (
    get_drainage_graph,
    graph_to_geojson,
)
from backend.app.domain.delhi.drainage.loading import (
    depth_estimates_for_reach_states,
    edge_loading_for_reach_states,
)
from backend.app.domain.delhi.surface import surface_pass
from backend.app.domain.delhi.radar import (
    delhi_rainfall_composite,
    probe_delhi_radar,
)
from backend.app.domain.delhi.scenarios.depth_v1 import (
    V1DepthStep,
    depth_cells_from_v1,
    depth_polygons_from_v1,
    scenario_v1_depth_steps,
)
from backend.app.domain.delhi.scenarios.config import ScenarioDefinition, StormTemporalProfile
from backend.app.domain.delhi.surface import get_surface_structure
from backend.app.domain.delhi.digital_twin.kushak_hydraulic_state_classification import (
    classify_chain_timestep,
)

router = APIRouter(prefix="/api/delhi", tags=["delhi-v2"])

DATA_DIR = _REPO_ROOT / "data" / "delhi" / "derived"

# ---------------------------------------------------------------------------
# Derived GeoJSON layers (allowlisted; served with explicit provenance)
# ---------------------------------------------------------------------------

GEO_LAYERS: Dict[str, Dict[str, str]] = {
    "corridor_centerline": {
        "path": "hydraulic/kushak_corridor_centerline.geojson",
        "label": "Kushak-Barapullah modeled corridor centerline",
        "provenance": "DERIVED (Appendix XII longitudinal backbone / GSDL alignment evidence)",
    },
    "watershed": {
        "path": "watershed/kushak_watershed.geojson",
        "label": "Working model catchment (~27.66 km2, PROVISIONAL)",
        "provenance": "DERIVED/PROVISIONAL (D8 project watershed; NOT authoritative)",
    },
    "cross_sections": {
        "path": "hydraulic/kushak_cross_sections.geojson",
        "label": "Cross-section locations",
        "provenance": "DERIVED (Appendix XII-derived geometry; not as-built survey)",
    },
    "gsdl_occurrences": {
        "path": "validation/gsdl_waterlogging/gsdl_waterlogging_normalized_occurrences.geojson",
        "label": "GSDL waterlogging occurrences (OFFICIAL observations)",
        "provenance": "OBSERVED/OFFICIAL (GSDL; date-only provenance)",
    },
    "historical_landmarks": {
        "path": "hydraulic/historical_reconciliation/kushak_historical_landmarks.geojson",
        "label": "Historical network landmarks",
        "provenance": "OFFICIAL (documented historical evidence)",
    },
}

# ---------------------------------------------------------------------------
# In-process deterministic caches. The replay and ensemble are deterministic,
# so cached responses are byte-identical to fresh runs; refresh=true forces
# recomputation.
# ---------------------------------------------------------------------------

_REPLAY_CACHE: Dict[str, Any] = {}
_NOWCAST_CACHE: Dict[str, Any] = {}


def _iso(dt: Optional[datetime]) -> Optional[str]:
    return dt.isoformat() if dt is not None else None


def _require_harness():
    if replay_harness is None:  # pragma: no cover
        raise HTTPException(
            status_code=503,
            detail=f"replay harness unavailable: {_HARNESS_IMPORT_ERROR}",
        )


# ---------------------------------------------------------------------------
# 1. System status
# ---------------------------------------------------------------------------


@router.get("/status")
def get_status() -> Dict[str, Any]:
    """Machine-readable system status: what is computed, what is evidence,
    what is unknown, and what this system does NOT claim."""
    ensemble = build_kushak_ensemble()
    executable_events = [
        eid for eid in replay_harness.REPLAY_EVENT_IDS
        if replay_harness.resolve_event_id(eid) in ("EV-01", "EV-02")
    ] if replay_harness is not None else []
    mode = production_mode()
    return {
        "system": "Delhi/Kushak V2 Urban Flood Nowcasting (evidence-constrained digital twin)",
        "generated_at": _iso(datetime.now(timezone.utc)),
        "production_mode": mode["production_mode"],
        "ml_status": mode["ml_status"],
        "objective": (
            "0-3 hour urban flood nowcasting for the Kushak nallah catchment "
            "(Delhi) coupling rainfall, terrain, and drainage evidence"
        ),
        "components": {
            "reach_chain": {
                "reach_ids": [r.reach_id for r in KUSHAK_MODEL_REACHES],
                "total_length_m": sum(
                    r.end_chainage_m - r.start_chainage_m for r in KUSHAK_MODEL_REACHES
                ),
                "order": "UG-01 -> OC-01 -> CD-01 -> OC-02 (OC-02 terminal)",
            },
            "ensemble": {
                "member_count": len(ensemble),
                "axes": {
                    "hydraulic": list(KUSHAK_HYDRAULIC_SCENARIOS.keys()),
                    "catchment": list(CATCHMENT_SCENARIOS.keys()),
                },
                "deterministic": True,
            },
            "historical_events": {
                "catalogued": len(replay_harness.REPLAY_EVENT_IDS) if replay_harness else None,
                "executable": executable_events,
                "canonical_validation_events": [e.event_id for e in VALIDATION_EVENTS],
            },
            "nowcast": {
                "reference_point": SAFDARJUNG_REFERENCE,
                "latitude": SAFDARJUNG_LAT,
                "longitude": SAFDARJUNG_LON,
                "forcing": "Open-Meteo NWP hourly forecast (model value, not observed)",
                "horizon_hours": 3,
            },
        },
        "capabilities": [
            "Genuine event-specific historical runtime replay (6-member deterministic ensemble)",
            "0-3h ensemble nowcast with behavioral inflow/storage envelopes",
            "Evidence/provenance-tracked outputs with UNKNOWN preservation",
            "Mass-balance verification on every computed reach-step",
        ],
        "explicit_non_claims": [
            "No calibrated or validated flood-depth accuracy",
            "No street-level depth truth from coarse terrain",
            "No observed stage: no storage-stage relation exists",
            "No synthetic disaggregation of coarse rainfall",
            "No invented drainage geometry labeled as official/as-built",
        ],
    }


# ---------------------------------------------------------------------------
# 2. Ensemble
# ---------------------------------------------------------------------------


@router.get("/ensemble")
def get_ensemble() -> Dict[str, Any]:
    """The deterministic 6-member ensemble with full parameter provenance."""
    members = []
    for m in build_kushak_ensemble():
        hyd = KUSHAK_HYDRAULIC_SCENARIOS[m.hydraulic_scenario_id]
        cat = CATCHMENT_SCENARIOS[m.catchment_scenario_id]
        members.append({
            "member_id": m.member_id,
            "hydraulic_scenario": {
                "id": hyd.scenario_id,
                "mult_box": hyd.mult_box,
                "mult_open": hyd.mult_open,
                "f_open_depot": hyd.f_open_depot,
                "mult_box_range": list(hyd.mult_box_range),
                "mult_open_range": list(hyd.mult_open_range),
                "f_open_depot_range": list(hyd.f_open_depot_range),
                "provenance": "INFERRED_EFFECTIVE (Phase 7D16 sampled ranges; not surveyed/calibrated)",
                "description": hyd.description,
            },
            "catchment_scenario": {
                "id": cat.scenario_id,
                "area_km2": cat.area_km2,
                "provenance": cat.provenance.value,
                "basis": cat.basis,
                "note": cat.note,
            },
            "runoff_coefficient": {
                "value": m.runoff_coefficient,
                "provenance": SCENARIO_RUNOFF_PROVENANCE.value,
            },
            "description": m.description,
        })
    return {
        "member_count": len(members),
        "deterministic": True,
        "construction": "3 hydraulic scenarios x 2 catchment scenarios (documented axes only; no probabilistic weighting, no Monte Carlo)",
        "members": members,
    }


# ---------------------------------------------------------------------------
# 3. Reach network (model contract, not survey geometry)
# ---------------------------------------------------------------------------


@router.get("/network")
def get_network() -> Dict[str, Any]:
    """The locked Kushak reach chain with explicit evidence status."""
    reaches = []
    for r in KUSHAK_MODEL_REACHES:
        reaches.append({
            "reach_id": r.reach_id,
            "start_chainage_m": r.start_chainage_m,
            "end_chainage_m": r.end_chainage_m,
            "length_m": r.end_chainage_m - r.start_chainage_m,
            "reach_type": r.reach_type.value if hasattr(r.reach_type, "value") else str(r.reach_type),
            "label": r.label,
            "tier": r.tier.value if hasattr(r.tier, "value") else str(r.tier),
            "provenance": r.provenance.value,
            "hydraulic_status": r.hydraulic_status,
            "profile_reference": r.profile_reference,
            "note": getattr(r, "note", None),
        })
    return {
        "order": [r.reach_id for r in KUSHAK_MODEL_REACHES],
        "terminal_reach": "OC-02",
        "total_length_m": sum(
            r.end_chainage_m - r.start_chainage_m for r in KUSHAK_MODEL_REACHES
        ),
        "catchment_note": (
            "Kushak Nallah is the western branch of the Barapullah system; "
            "continuity to the Yamuna is through Barapullah downstream. "
            "Qudesia Nallah is hydraulically separate and is NOT part of "
            "this network."
        ),
        "reaches": reaches,
    }


# ---------------------------------------------------------------------------
# 4. Historical event catalogue
# ---------------------------------------------------------------------------


def _event_catalog_rows() -> Dict[str, dict]:
    _require_harness()
    return replay_harness._load_event_catalog_rows()


@router.get("/events")
def get_events() -> Dict[str, Any]:
    """The historical event catalogue with forcing availability, replay
    status classification (EXECUTABLE / PARTIAL / UNKNOWN / CONTROL), and
    preserved evidence classifications. No runtime execution here."""
    _require_harness()
    rows = _event_catalog_rows()
    events = []
    for event_id in replay_harness.REPLAY_EVENT_IDS:
        row = rows.get(event_id)
        declaration = get_declaration(event_id)
        resolved = resolve_event_id(event_id)
        forcing_profile = get_forcing_for_event(resolved) if resolved else None
        executable = forcing_profile is not None
        events.append({
            "event_id": event_id,
            "canonical_event_id": resolved,
            "event_window": replay_harness.DOCUMENTED_EVENT_WINDOWS[event_id],
            "qualification": row["QUALIFICATION"] if row else "UNKNOWN",
            "rainfall_resolution": row["RAINFALL_RESOLUTION"] if row else "UNKNOWN",
            "operational_state": replay_harness.DOCUMENTED_OPERATIONAL_STATE[event_id],
            "evidence_notes": declaration.evidence_notes,
            "replay_status": replay_status_label(event_id),
            "executable_status": declaration.executable_status,
            "replay_claim": declaration.replay_claim,
            "observation_status": declaration.observation_status,
            "spatial_attribution_status": declaration.spatial_attribution_status,
            "forcing": {
                "available": executable,
                "availability": declaration.forcing_availability,
                "forcing_id": forcing_profile.forcing_id if forcing_profile else None,
                "bins": replay_harness.format_forcing_bins(forcing_profile) if forcing_profile else None,
            },
            "preserved_final_classification": (
                None if executable
                else replay_harness.PRESERVED_FINAL_CLASSIFICATION[event_id]
            ),
            "runtime_replay_available": executable,
        })
    return {
        "catalog_size": len(events),
        "executable_event_ids": [
            e["event_id"] for e in events if e["replay_status"] == "EXECUTABLE"
        ],
        "partial_event_ids": [
            e["event_id"] for e in events if e["replay_status"] == "PARTIAL"
        ],
        "events": events,
    }


# ---------------------------------------------------------------------------
# 5. Event replay (genuine runtime, per-member detail)
# ---------------------------------------------------------------------------


def _serialize_member_execution(ex, profile_meta_note: str = "") -> Dict[str, Any]:
    """Serialize one MemberRuntimeExecution into JSON-safe detail."""
    integrated = ex.integrated
    hydrograph = integrated.rainfall_conversion.hydrograph
    inflow_steps = []
    if hydrograph is not None:
        inflow_steps = [
            {"time": _iso(s.timestamp), "discharge_m3_s": s.discharge_m3_s}
            for s in hydrograph.steps
        ]

    chain_steps = []
    for step_idx, step in enumerate(ex.chain.steps):
        per_reach = []
        for r in step.results:
            per_reach.append({
                "reach_id": r.state.reach_id,
                "hydraulic_status": r.state.hydraulic_status.value,
                "storage_m3": r.state.storage_m3,
                "stage_m": r.state.stage_m,
                "incoming_flow_m3_s": r.state.incoming_flow_m3_s,
                "actual_outflow_m3_s": r.transfer.actual_outflow_m3_s,
                "transferred_m3_s": r.transfer.transferred_m3_s,
                "capacity_m3_s": r.transfer.capacity_m3_s,
                "balance_residual_m3_s": r.accounting.balance_residual_m3_s,
            })
        classifications = ex.classifications[step_idx] if step_idx < len(ex.classifications) else ()
        chain_steps.append({
            "time_start": _iso(step.results[0].state.timestep.start) if step.results else None,
            "time_end": _iso(step.results[0].state.timestep.end) if step.results else None,
            "reaches": per_reach,
            "classifications": [
                {
                    "reach_id": c.reach_id,
                    "classification": c.classification.value,
                    "status": c.status,
                    "provenance": c.provenance.value,
                    "tier": c.tier,
                }
                for c in classifications
            ],
        })

    v = ex.validation
    return {
        "member_id": ex.member_id,
        "inflow_conversion_status": integrated.rainfall_conversion.status,
        "inflow_steps": inflow_steps,
        "inflow_volume_m3": (
            sum(
                s.discharge_m3_s * 3600.0
                for s in hydrograph.steps
                if s.discharge_m3_s is not None
            )
            if hydrograph is not None else None
        ),
        "chain_steps": chain_steps,
        "validation": {
            "event_id": v.event_id,
            "source_class": v.source_class.value if hasattr(v.source_class, "value") else str(v.source_class),
            "validation_result": v.validation_result.value,
            "temporal_match": v.temporal_match.value,
            "spatial_match": v.spatial_match.value,
            "timestamp_precision": v.timestamp_precision.value,
            "result_provenance": v.result_provenance.value,
            "diagnostic": v.diagnostic,
        },
        "diagnostics": list(integrated.diagnostics),
    }


@router.get("/events/{event_id}/replay")
def get_event_replay(
    event_id: str,
    refresh: bool = Query(False, description="Force re-execution of the deterministic replay"),
) -> Dict[str, Any]:
    """Genuine event-specific runtime replay for ONE catalogue event.

    Executable events (EVT-2024-06-27/EV-01, EVT-2023-07-08/EV-02) run all
    6 ensemble members through the canonical runtime path with this event's
    own forcing (resolution preserved, no disaggregation). Non-executable
    events return their preserved evidence classification WITHOUT runtime
    execution (absent forcing is never converted into a simulation).
    """
    _require_harness()
    if event_id not in replay_harness.REPLAY_EVENT_IDS:
        raise HTTPException(status_code=404, detail=f"unknown event {event_id}")

    cache_key = f"detail:{event_id}"
    if not refresh and cache_key in _REPLAY_CACHE:
        return _REPLAY_CACHE[cache_key]

    rows = _event_catalog_rows()
    catalog_row = rows[event_id]
    resolved = resolve_event_id(event_id)
    forcing_profile = get_forcing_for_event(resolved) if resolved else None

    meta = replay_harness._catalog_metadata_fields(catalog_row, event_id)

    response: Dict[str, Any] = {
        "event_id": event_id,
        "canonical_event_id": resolved,
        "event_window": meta["event_window"],
        "rainfall_resolution": meta["rainfall_resolution"],
        "operational_state": meta["operational_state"],
        "observed_empirical_outcome": meta["observed_empirical_outcome"],
        "qualification": meta["qualification"],
        "evidence_notes": meta["evidence_notes"],
        "cwc_state": meta["cwc_state"],
        "generated_at": _iso(datetime.now(timezone.utc)),
    }

    declaration = get_declaration(event_id)
    response["replay_status"] = replay_status_label(event_id)
    response["executable_status"] = declaration.executable_status
    response["replay_claim"] = declaration.replay_claim

    if forcing_profile is None:
        response.update({
            "runtime_status": "NOT_EXECUTED",
            "reason": replay_harness.PRESERVED_FINAL_CLASSIFICATION[event_id],
            "forcing": None,
            "members": [],
            "counters": {},
            "claim_policy": (
                "No runtime execution: absent forcing is a structural "
                "barrier. No zero-fill, no synthetic disaggregation."
            ),
        })
        _REPLAY_CACHE[cache_key] = response
        return response

    forcing_series = replay_harness.build_event_forcing_series(
        catalog_event_id=event_id,
        canonical_event_id=resolved,
        forcing_profile=forcing_profile,
    )
    counters = replay_harness.EventRuntimeCounters()
    ensemble = build_kushak_ensemble()
    member_executions = [
        replay_harness.execute_member_for_event(member, forcing_series, counters)
        for member in ensemble
    ]

    is_partial = declaration.executable_status == "PARTIALLY_EXECUTABLE"
    response.update({
        "runtime_status": "PARTIAL_EXECUTED" if is_partial else "EXECUTED",
        "forcing": {
            "forcing_id": forcing_profile.forcing_id,
            "anchor_start": _iso(forcing_series.anchor_start),
            "bins": [
                {
                    "lead_hour": b.lead_hour,
                    "depth_mm": replay_harness._bin_depth_mm(b, replay_harness._bin_interval_hours(b)),
                    "units": b.units,
                    "provenance": b.provenance.value,
                }
                for b in forcing_profile.bins
            ],
            "resolution_preserved": True,
            "note": (
                "each catalog bin is exactly one timestep at its documented "
                "interval; no synthetic disaggregation"
                + (
                    " — only the documented defensible portion is executed"
                    if is_partial else ""
                )
            ),
        },
        "ensemble_size": len(member_executions),
        "members": [
            _serialize_member_execution(ex) for ex in member_executions
        ],
        "counters": {
            "ensemble_members_executed": counters.ensemble_members_executed,
            "forcing_bins_executed": counters.forcing_bins_executed,
            "hydrograph_timesteps_executed": counters.hydrograph_timesteps_executed,
            "chain_timesteps_executed": counters.chain_timesteps_executed,
            "chain_reach_timesteps_executed": counters.chain_reach_timesteps_executed,
            "reach_state_classifications": counters.reach_state_classifications,
            "validation_calls": counters.validation_calls,
        },
        "integrity_checks": {
            "mass_balance": replay_harness._derive_mass_balance_check(member_executions),
            "terminal_outfall": replay_harness._derive_terminal_outfall_check(member_executions),
            "unknown_propagation": replay_harness._derive_unknown_propagation_check(
                forcing_series, member_executions
            ),
            "runtime_consistency": replay_harness._derive_runtime_consistency_check(member_executions),
        },
        "claim_policy": (
            "PARTIAL replay: only the documented defensible forcing portion "
            "was executed at native resolution. Runtime execution integrity "
            "and qualitative/directional behavioral compatibility for the "
            "executed portion only. NOT an accuracy, calibration, or "
            "depth-skill claim."
            if is_partial else
            "Runtime execution integrity and qualitative/directional "
            "behavioral compatibility only. NOT an accuracy, calibration, "
            "or depth-skill claim."
        ),
    })
    _REPLAY_CACHE[cache_key] = response
    return response


@router.get("/events/{event_id}/depth")
def get_event_depth_grid(
    event_id: str,
    timestep_index: int = Query(0, ge=0, description="forcing bin index"),
) -> Dict[str, Any]:
    """V1-reference flood depth grid for a HISTORICAL event's documented
    forcing bin (like the Mumbai 2017 replay depth maps, ported to V2).

    The V1 model (inlet capture -> surcharge -> D8 equilibrium ponding)
    runs on the event's documented bin depths; the result is a
    HISTORICAL MODEL REPLAY depth product - SIMULATED_MODEL_OUTPUT
    provenance, never observed depth. Cached per event (deterministic)."""
    _require_harness()
    if event_id not in replay_harness.REPLAY_EVENT_IDS:
        raise HTTPException(status_code=404, detail=f"unknown event {event_id}")
    declaration = get_declaration(event_id)
    resolved = declaration.canonical_event_id
    profile = replay_harness.get_forcing_for_event(resolved) if resolved else None
    if profile is None:
        raise HTTPException(
            status_code=409,
            detail=f"event {event_id} has no executable forcing; depth replay is NOT_COMPUTABLE",
        )
    if timestep_index >= len(profile.bins):
        raise HTTPException(status_code=400, detail=f"timestep_index must be in [0, {len(profile.bins) - 1}]")

    cache_key = f"depthgrid:{event_id}"
    cached = _REPLAY_CACHE.get(cache_key)
    if cached is not None and cached["timestep_index"] == timestep_index:
        return cached

    # Pseudo-scenario: one timestep per documented bin (interval preserved).
    from datetime import timedelta as _td

    bins_meta = []
    intervals = []
    for b in profile.bins:
        h = replay_harness._bin_interval_hours(b)
        intervals.append(h)
        bins_meta.append(replay_harness._bin_depth_mm(b, h))
    pseudo = ScenarioDefinition(
        scenario_id=f"HIST-{event_id}",
        name=f"historical replay {event_id}",
        description="V1 reference depth replay on the documented historical forcing",
        duration_min=int(sum(intervals) * 60),
        timestep_min=60,  # replaced per-step below (variable intervals)
    )
    # Build variable-interval areal depths: each bin = one step at its own
    # interval (documented resolution preserved; no disaggregation).
    structure = get_surface_structure()
    graph = get_drainage_graph()
    capacity_by_edge = {e.edge_id: e.capacity_min_m3_s for e in graph.edges}

    from backend.app.domain.delhi.scenarios import depth_v1 as dv

    steps: List[Dict[str, Any]] = []
    for t, depth_mm in enumerate(bins_meta):
        if depth_mm is None:
            steps.append({
                "timestep_index": t,
                "status": "UNKNOWN_FORCING_SKIPPED",
                "max_depth_cm": None,
                "flooded_cells": 0,
                "flood_state": "UNKNOWN",
                "depth_cells": [],
                "source_type": "SIMULATED_MODEL_OUTPUT",
            })
            continue
        # One-off V1 coupling for this bin (areal depth over its interval).
        cell_area = structure.cell_area_m2
        n_cells = structure.cell_flat_idx.size
        total_runoff = depth_mm / 1000.0 * 0.75 * cell_area * n_cells
        from backend.app.domain.delhi.scenarios.depth_v1 import (
            inlet_cell_indices, _curb_inlet_capacity_m3, _v1_route,
        )
        import numpy as _np

        inlets = inlet_cell_indices()
        flat_to_win = {int(f): i for i, f in enumerate(structure.cell_flat_idx)}
        inlet_win = _np.array(
            [flat_to_win[int(f)] for f in inlets if int(f) in flat_to_win], dtype=_np.int64
        )
        curb_cap = _curb_inlet_capacity_m3(intervals[t], 1.0)
        runoff_at_inlets = _np.full(len(inlet_win), total_runoff / max(len(inlet_win), 1))
        conveyed_total = float(_np.minimum(runoff_at_inlets, curb_cap).sum())
        surcharge = _np.zeros(structure.cell_flat_idx.size)
        excess = _np.maximum(runoff_at_inlets - curb_cap, 0.0)
        if excess.any():
            surcharge[inlet_win] = excess
        water, drained_out = _v1_route(surcharge, structure)
        cap_m = _np.where(structure.depression_cap_m > 0.15, structure.depression_cap_m, 0.10)
        overflow_m3 = float(_np.maximum(water - cap_m * cell_area, 0.0).sum())
        water = _np.minimum(water, cap_m * cell_area)

        class _Step:
            pass

        st = _Step()
        st.timestep_index = t
        st.depth_m = water / cell_area
        st.flooded_cells = int(_np.count_nonzero(st.depth_m > 0.001))
        st.max_depth_m = float(st.depth_m.max()) if st.depth_m.size else 0.0
        st.total_flooded_area_m2 = st.flooded_cells * cell_area
        st.total_runoff_volume_m3 = total_runoff
        st.conveyed_volume_m3 = conveyed_total
        st.surcharged_volume_m3 = float(excess.sum())
        st.overflow_volume_m3 = overflow_m3
        st.drained_out_volume_m3 = drained_out

        steps.append({
            "timestep_index": t,
            "status": "COMPUTED",
            "max_depth_cm": round(st.max_depth_m * 100.0, 1),
            "flooded_cells": st.flooded_cells,
            "flood_state": "UNKNOWN",
            "flood_state": (
                "NO_FLOOD" if st.max_depth_m * 100.0 < 2.0
                else depth_cells_from_v1(st, structure)[0]["flood_state"] if st.flooded_cells else "NO_FLOOD"
            ),
            "depth_cells": depth_cells_from_v1(st, structure),
            "depth_polygons": depth_polygons_from_v1(st, structure),
            "v1_mass_balance": {
                "total_runoff_m3": round(total_runoff, 1),
                "conveyed_m3": round(conveyed_total, 1),
                "surcharged_m3": round(float(excess.sum()), 1),
                "overflow_m3": round(overflow_m3, 1),
                "drained_out_m3": round(drained_out, 1),
            },
            "source_type": "SIMULATED_MODEL_OUTPUT",
        })

    payload = {
        "event_id": event_id,
        "canonical_event_id": resolved,
        "timestep_index": timestep_index,
        "mode": "HISTORICAL MODEL REPLAY (V1 reference)",
        "claim_policy": (
            "HISTORICAL MODEL REPLAY: the V1 reference depth model on the "
            "documented historical forcing. SIMULATED_MODEL_OUTPUT - never "
            "observed depth, never real-event accuracy."
        ),
        "timestep_index": timestep_index,
        "step": steps[timestep_index],
        "steps_summary": [
            {k: v for k, v in st.items() if k != "depth_cells"} for st in steps
        ],
        "generated_at": _iso(datetime.now(timezone.utc)),
        "source_type": "SIMULATED_MODEL_OUTPUT",
    }
    _REPLAY_CACHE[cache_key] = payload
    return payload


@router.get("/events/{event_id}/artifact")
def get_event_artifact(
    event_id: str,
    refresh: bool = Query(False, description="Regenerate the deterministic artifact"),
) -> Dict[str, Any]:
    """The reproducible 28C replay artifact for one event (built from the
    genuine runtime execution; deterministic, revision-stamped)."""
    _require_harness()
    if event_id not in replay_harness.REPLAY_EVENT_IDS:
        raise HTTPException(status_code=404, detail=f"unknown event {event_id}")
    if not refresh:
        cached = _REPLAY_CACHE.get(f"artifact:{event_id}")
        if cached is not None:
            return cached
    try:
        artifact = build_replay_artifact(event_id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"artifact build failed: {exc}")
    _REPLAY_CACHE[f"artifact:{event_id}"] = artifact
    return artifact


@router.get("/replay/summary")
def get_replay_summary(
    refresh: bool = Query(False, description="Force re-execution of the deterministic replay"),
) -> Dict[str, Any]:
    """The full Phase 15.5 replay: per-event runtime records + system flags
    + verdict, derived from actual runtime executions."""
    _require_harness()
    if not refresh and "summary" in _REPLAY_CACHE:
        return _REPLAY_CACHE["summary"]

    result: replay_harness.ReplayRunResult = replay_harness.run_historical_replay()
    records = []
    for rec in result.records:
        records.append({
            "event_id": rec.event_id,
            "resolved_event_id": rec.resolved_event_id,
            "event_window": rec.event_window,
            "rainfall_resolution": rec.rainfall_resolution,
            "operational_state": rec.operational_state,
            "observed_empirical_outcome": rec.observed_empirical_outcome,
            "qualification": rec.qualification,
            "evidence_notes": rec.evidence_notes,
            "forcing_found": rec.forcing_found,
            "forcing_time_bins": rec.forcing_time_bins,
            "runtime_executed": rec.runtime_executed,
            "ensemble_members_executed": rec.ensemble_members_executed,
            "actual_member_ids": rec.actual_member_ids,
            "chain_timesteps_executed": rec.chain_timesteps_executed,
            "validation_calls": rec.validation_calls,
            "runtime_model_state": rec.runtime_model_state,
            "mass_balance_check": rec.mass_balance_check,
            "terminal_outfall_check": rec.terminal_outfall_check,
            "unknown_propagation_check": rec.unknown_propagation_check,
            "timestep_execution_check": rec.timestep_execution_check,
            "final_classification": rec.final_classification,
        })
    response = {
        "generated_at": _iso(datetime.now(timezone.utc)),
        "records": records,
        "system_flags": dict(result.system_flags),
        "verdict": result.verdict,
        "claim_policy": (
            "Runtime execution integrity + qualitative consistency. "
            "NOT an accuracy/calibration claim."
        ),
    }
    _REPLAY_CACHE["summary"] = response
    return response


# ---------------------------------------------------------------------------
# 6. 0-3h operational nowcast
# ---------------------------------------------------------------------------


def _serialize_nowcast(result) -> Dict[str, Any]:
    forecast = result.forecast
    member_payloads = []
    envelope_inflow: List[Dict[str, Any]] = []
    for t_idx, ts in enumerate(result.timesteps):
        values = [m.inflow_steps[t_idx][1] for m in result.members if t_idx < len(m.inflow_steps)]
        known = [v for v in values if v is not None]
        envelope_inflow.append({
            "time_start": _iso(ts.start),
            "time_end": _iso(ts.end),
            "forecast_depth_mm": result.depths_mm[t_idx],
            "min_m3_s": min(known) if known else None,
            "median_m3_s": (
                sorted(known)[len(known) // 2] if known else None
            ),
            "max_m3_s": max(known) if known else None,
            "computed_members": len(known),
            "unknown_members": len(values) - len(known),
        })
    for m in result.members:
        member_payloads.append({
            "member_id": m.member_id,
            "hydraulic_scenario_id": m.hydraulic_scenario_id,
            "catchment_scenario_id": m.catchment_scenario_id,
            "runoff_coefficient": m.runoff_coefficient,
            "inflow_status": m.inflow_status,
            "inflow_steps": [
                {"time": _iso(t), "discharge_m3_s": q} for t, q in m.inflow_steps
            ],
            "inflow_volume_m3": (
                sum(q * 3600.0 for _, q in m.inflow_steps if q is not None)
            ),
            "reach_states": {
                rid: [
                    {
                        "time_start": s["time_start"],
                        "time_end": s["time_end"],
                        "hydraulic_status": s["hydraulic_status"],
                        "storage_m3": s["storage_m3"],
                        "stage_m": s["stage_m"],
                        "incoming_flow_m3_s": s["incoming_flow_m3_s"],
                        "actual_outflow_m3_s": s["actual_outflow_m3_s"],
                        "transferred_downstream_m3_s": s["transferred_downstream_m3_s"],
                        "balance_residual_m3_s": s["balance_residual_m3_s"],
                    }
                    for s in steps
                ]
                for rid, steps in m.reach_states.items()
            },
            "classifications": [
                [
                    {
                        "reach_id": c["reach_id"],
                        "classification": c["classification"],
                        "status": c["status"],
                        "provenance": c["provenance"],
                    }
                    for c in step_classes
                ]
                for step_classes in m.classifications
            ],
            "diagnostics": m.diagnostics,
        })
    return {
        "status": result.status,
        "generated_at": _iso(result.generated_at),
        "forecast": {
            "status": forecast.status,
            "source": forecast.source,
            "reference_point": forecast.reference_point,
            "latitude": forecast.latitude,
            "longitude": forecast.longitude,
            "acquired_at": _iso(forecast.acquired_at),
            "bins": [
                {
                    "time_start": _iso(b.time_start),
                    "time_end": _iso(b.time_end),
                    "depth_mm": b.depth_mm,
                    "provenance": b.provenance,
                }
                for b in forecast.bins
            ],
            "diagnostics": forecast.diagnostics,
        },
        "envelope_inflow": envelope_inflow,
        "members": member_payloads,
        "diagnostics": result.diagnostics,
        "horizon_note": result.horizon_note,
        "claim_policy": (
            "Behavioral ensemble envelopes under documented effective-"
            "scenario assumptions with NWP model-forecast forcing. Stage, "
            "capacity exceedance, and street-level depth are UNKNOWN and "
            "are never claimed. NOT a validated depth prediction."
        ),
    }


@router.get("/nowcast")
def get_nowcast(
    refresh: bool = Query(False, description="Bypass the forecast cache and re-run"),
) -> Dict[str, Any]:
    """0-3h ensemble nowcast for the Kushak catchment.

    Acquires the Open-Meteo NWP hourly forecast for the documented
    Safdarjung reference point, then executes the deterministic 6-member
    ensemble through the canonical hydraulic runtime. If the forecast
    cannot be acquired, returns an explicit UNAVAILABLE/BLOCKED state —
    never a fabricated nowcast.
    """
    if not refresh:
        cached = _NOWCAST_CACHE.get("nowcast")
        if cached is not None:
            generated = datetime.fromisoformat(cached["generated_at"])
            if (datetime.now(timezone.utc) - generated).total_seconds() < 10 * 60:
                return cached

    forecast = fetch_delhi_rainfall_forecast(use_cache=not refresh)
    result = run_nowcast(forecast)
    payload = _serialize_nowcast(result)

    # Reconstruction products reported ALONGSIDE the physics (never
    # injected into it): per-node drainage loading, estimated-depth
    # ranges, and the 2D surface pass.
    try:
        states = get_live_reach_states(departure_hour=0)
        payload["drainage_loading"] = [
            l.__dict__ for l in edge_loading_for_reach_states(states)
        ]
        payload["depth_estimates"] = depth_estimates_for_reach_states(states)
        _surface = surface_pass(
            list(result.depths_mm), [1.0] * len(result.depths_mm)
        )
        for _ts in _surface.get("timesteps", []):
            _ts.pop("depth_field_cm", None)
        payload["surface"] = _surface
    except Exception as exc:  # degrade gracefully; nowcast stays intact
        payload["drainage_loading"] = []
        payload["depth_estimates"] = {}
        payload["surface"] = {"status": "UNAVAILABLE", "reason": str(exc)[:160]}
    if result.status == "COMPUTED":
        _NOWCAST_CACHE["nowcast"] = payload
    return payload


# ---------------------------------------------------------------------------
# 7. Derived GeoJSON layers (allowlisted)
# ---------------------------------------------------------------------------


@router.get("/geo/{layer_id}")
def get_geo_layer(layer_id: str) -> Dict[str, Any]:
    """Serve an allowlisted derived GeoJSON evidence layer verbatim, with
    explicit provenance metadata. Unknown layers are 404 — never guessed."""
    layer = GEO_LAYERS.get(layer_id)
    if layer is None:
        raise HTTPException(status_code=404, detail=f"unknown layer {layer_id}")
    path = DATA_DIR / layer["path"]
    if not path.exists():
        raise HTTPException(status_code=503, detail=f"layer data missing: {layer['path']}")
    try:
        geojson = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"layer unreadable: {exc}")
    return {
        "layer_id": layer_id,
        "label": layer["label"],
        "provenance": layer["provenance"],
        "source_path": str(layer["path"]),
        "feature_count": len(geojson.get("features", [])),
        "geojson": geojson,
    }


@router.get("/layers")
def get_layers() -> Dict[str, Any]:
    """The available map layers with provenance labels."""
    return {
        "layers": [
            {"layer_id": lid, "label": l["label"], "provenance": l["provenance"]}
            for lid, l in GEO_LAYERS.items()
        ]
    }


# ---------------------------------------------------------------------------
# 7b. Radar status + rainfall composite (Delhi)
# ---------------------------------------------------------------------------

_RADAR_CACHE: Dict[str, Any] = {}


@router.get("/rainfall/radar")
async def get_delhi_radar_status(
    refresh: bool = Query(False, description="Force a live re-probe"),
) -> Dict[str, Any]:
    """Live probe diagnostics of the IMD Delhi Doppler radar endpoints.
    Accessibility and format are reported; a visual GIF product is NEVER
    decoded into rainfall (no official calibration exists)."""
    if not refresh and "radar" in _RADAR_CACHE:
        return _RADAR_CACHE["radar"]
    results = await probe_delhi_radar()
    payload = {
        "generated_at": _iso(datetime.now(timezone.utc)),
        "station": {
            "station_id": "DLI",
            "station_name": "Delhi-Mausam (Aya Nagar) Doppler Weather Radar",
            "lat": 28.4739,
            "lon": 77.1324,
        },
        "quantitative_product_available": any(
            r.is_accessible and r.is_quantitative for r in results
        ),
        "results": [r.to_dict() for r in results],
    }
    _RADAR_CACHE["radar"] = payload
    return payload


@router.get("/rainfall/composite")
async def get_delhi_rainfall_composite(
    refresh: bool = Query(False),
) -> Dict[str, Any]:
    """The active rainfall-source decision with strict provenance:
    RADAR when a quantitative Delhi IMD product is available; otherwise
    NWP_FALLBACK (Open-Meteo is never called radar)."""
    if not refresh and "composite" in _RADAR_CACHE:
        return _RADAR_CACHE["composite"]
    forecast = fetch_delhi_rainfall_forecast(use_cache=True)
    results = await probe_delhi_radar()
    payload = delhi_rainfall_composite(
        nwp_status=forecast.status,
        nwp_acquired_at=forecast.acquired_at,
        radar_results=results,
    )
    payload["generated_at"] = _iso(datetime.now(timezone.utc))
    _RADAR_CACHE["composite"] = payload
    return payload


# ---------------------------------------------------------------------------
# 7c. DERIVED drainage graph + per-node loading
# ---------------------------------------------------------------------------


@router.get("/drainage-graph")
def get_drainage_graph_geo() -> Dict[str, Any]:
    """The DERIVED Delhi drainage graph (nodes from documented
    cross-sections + corridor endpoints; edges = chainage-ordered corridor
    segments with inferred-effective capacity ranges). Nothing here is
    as-built or surveyed."""
    graph = get_drainage_graph()
    geojson = graph_to_geojson(graph)
    return {
        "generated_at": _iso(datetime.now(timezone.utc)),
        "n_nodes": len(graph.nodes),
        "n_edges": len(graph.edges),
        "provenance": (
            "DERIVED (documented corridor centerline + Appendix XII "
            "cross-sections; capacity = full-bore Manning estimate over "
            "documented geometry class ranges, INFERRED_EFFECTIVE)"
        ),
        "nodes": geojson["nodes"],
        "edges": geojson["edges"],
    }


@router.get("/drainage-graph/loading")
def get_drainage_loading(
    mode: str = Query("live", pattern="^(live|historical)$"),
    departure_hour: int = Query(0, ge=0, le=3),
    event_id: Optional[str] = Query(None),
    timestep_index: int = Query(0, ge=0),
) -> Dict[str, Any]:
    """Per-edge/per-node loading from REAL model states (live nowcast
    at the departure hour, or the genuine historical replay at an event +
    timestep). POTENTIAL_OVERLOAD means the modeled inflow breaches the
    lower bound of the documented capacity class - scenario-consistent
    backflow/surcharge POTENTIAL, never observed and never a depth claim."""
    if mode == "live":
        states = get_live_reach_states(departure_hour)
        ctx = {"mode": "LIVE", "departure_hour": departure_hour}
    else:
        if event_id is None:
            raise HTTPException(status_code=400, detail="historical mode requires event_id")
        n_steps = get_historical_timestep_count(event_id)
        if n_steps == 0:
            raise HTTPException(status_code=409, detail=f"event {event_id} has no executable forcing")
        if not 0 <= timestep_index < n_steps:
            raise HTTPException(status_code=400, detail=f"timestep_index must be in [0, {n_steps - 1}]")
        states = get_historical_reach_states(event_id, timestep_index)
        ctx = {"mode": "HISTORICAL", "event_id": event_id, "timestep_index": timestep_index}
    if states.status not in ("COMPUTED", "EXECUTED") or not states.member_states:
        return {**ctx, "status": "UNKNOWN_RISK_STATE", "edges": []}
    edges = edge_loading_for_reach_states(states)
    return {
        **ctx,
        "status": "COMPUTED",
        "edges": [e.__dict__ for e in edges],
        "overloaded_edges": [
            e.edge_id for e in edges if e.status == "POTENTIAL_OVERLOAD"
        ],
        "unknown_edges": [e.edge_id for e in edges if e.status == "UNKNOWN"],
        "claim": (
            "POTENTIAL_OVERLOAD = scenario-derived capacity-class breach "
            "at the lower bound; NOT observed flooding, NOT a depth claim"
        ),
    }


# ---------------------------------------------------------------------------
# 7d. 2D surface routing products
# ---------------------------------------------------------------------------


@router.get("/surface")
def get_surface_products(
    mode: str = Query("live", pattern="^(live|historical)$"),
    departure_hour: int = Query(0, ge=0, le=3),
    event_id: Optional[str] = Query(None),
    timestep_index: int = Query(0, ge=0),
) -> Dict[str, Any]:
    """2D surface routing pass over the enforced DEM for the active
    forcing sequence (live forecast or historical event). Hotspots are
    MODEL-DERIVED SURFACE PROXIES (candidate ponding cells), not observed
    flooding; per-reach inflow is a lateral proxy, never injected into the
    replay."""
    if mode == "live":
        forecast = fetch_delhi_rainfall_forecast(use_cache=True)
        depths = [b.depth_mm for b in forecast.bins]
        ctx = {"mode": "LIVE", "departure_hour": departure_hour}
    else:
        if event_id is None:
            raise HTTPException(status_code=400, detail="historical mode requires event_id")
        states = get_historical_reach_states(event_id, timestep_index)
        if states.status != "EXECUTED":
            raise HTTPException(status_code=409, detail=f"event {event_id} has no executable forcing")
        decl = get_declaration(event_id)
        profile = replay_harness.get_forcing_for_event(decl.canonical_event_id)
        depths = [
            replay_harness._bin_depth_mm(b, replay_harness._bin_interval_hours(b))
            for b in profile.bins
        ]
        ctx = {"mode": "HISTORICAL", "event_id": event_id, "timestep_index": timestep_index}
    try:
        result = surface_pass(depths, [1.0] * len(depths))
        # Drop the per-cell arrays (used in-memory by the scenario engine);
        # the API exposes hotspots + summaries only.
        for ts in result.get("timesteps", []):
            ts.pop("depth_field_cm", None)
        return {**ctx, "status": "COMPUTED", **result}
    except Exception as exc:
        return {**ctx, "status": "UNAVAILABLE", "reason": str(exc)[:200]}


# ---------------------------------------------------------------------------
# 7e. Scientific model performance (validation/calibration/ML gating)
# ---------------------------------------------------------------------------

_SCIENCE_CACHE: Dict[str, Any] = {}


@router.get("/model-science")
def get_model_science(refresh: bool = Query(False)) -> Dict[str, Any]:
    """The complete scientific model performance surface: observation
    registry summary, evidence gates, quantitative validation metrics,
    calibration status (bounds + GLUE screen + audit), identifiability,
    uncertainty decomposition, and the ML production gating decision.

    Every unsupported metric is NOT_COMPUTABLE with its reason — the
    honest state of the evidence, never a fabricated number.
    """
    if not refresh and "model-science" in _SCIENCE_CACHE:
        return _SCIENCE_CACHE["model-science"]

    registry = build_observation_registry()
    validation = evaluate_quantitative_validation()
    calibration = run_calibration_framework()
    sensitivity = identifiability_classification(oat_sensitivity())
    uncertainty = uncertainty_decomposition()
    gate = production_gate()

    payload = {
        "generated_at": _iso(datetime.now(timezone.utc)),
        "production_mode": gate["production_mode"],
        "ml_status": gate["ml_status"],
        "claim_policy": (
            "IMPLEMENTED != VALIDATED != CALIBRATED != ML-TRAINED. No "
            "quantitative accuracy claim is made anywhere on this page: "
            "the observation registry holds no local quantitative hydraulic "
            "target, calibration is gated OFF, and ML is RESEARCH_ONLY. "
            "Physics-only outputs are the operational product."
        ),
        "observation_registry": {
            "record_count": len(registry),
            "summary": registry_summary(registry),
            "gate_note": (
                "0 observations are usable for calibration: no local "
                "stage/discharge/depth/extent measurement exists for the "
                "Kushak corridor. Downstream CWC stage is Tier A but "
                "spatially non-local (context only)."
            ),
        },
        "quantitative_validation": {
            "evidence_gate": validation["evidence_gate"],
            "event_split": validation["event_split"],
            "metrics": validation["metrics"],
        },
        "calibration": {
            "performed": calibration["calibration_performed"],
            "objective_gate": calibration["objective_gate"],
            "parameter_registry": calibration["parameter_registry"],
            "baseline_preserved": calibration["baseline_preserved"],
            "glue_screen": calibration["glue_screen"],
            "audit": calibration["audit"],
        },
        "identifiability": sensitivity,
        "uncertainty": uncertainty,
        "ml": {
            "strategy": "physics-guided residual/probability augmentation (physics remains the source of truth)",
            "production_mode": gate["production_mode"],
            "ml_status": gate["ml_status"],
            "gates": gate["gates"],
            "reason": gate["reason"],
            "dataset": gate["dataset"],
            "fallback_contract": (
                "ml_status UNAVAILABLE -> combined_prediction = "
                "physics_prediction (implemented and tested)"
            ),
        },
    }
    _SCIENCE_CACHE["model-science"] = payload
    return payload


# ---------------------------------------------------------------------------
# 8. Flood-aware safe routing (ONE engine: LIVE + HISTORICAL modes)
# ---------------------------------------------------------------------------


@router.get("/safe-route")
def get_safe_route(
    origin_lon: float = Query(..., description="Origin longitude (WGS84)"),
    origin_lat: float = Query(..., description="Origin latitude (WGS84)"),
    dest_lon: float = Query(..., description="Destination longitude (WGS84)"),
    dest_lat: float = Query(..., description="Destination latitude (WGS84)"),
    mode: str = Query("live", pattern="^(live|historical)$"),
    departure_hour: int = Query(0, ge=0, le=3, description="LIVE mode: 0-3h forecast hour"),
    event_id: Optional[str] = Query(None, description="HISTORICAL mode: catalogue event id"),
    timestep_index: int = Query(0, ge=0, description="HISTORICAL mode: replay timestep"),
) -> Dict[str, Any]:
    """Flood-aware route (recommended + alternative + comparison + evidence).

    ONE deterministic routing core serves both modes; the mode only
    selects the reach-state source (live nowcast ensemble vs genuine
    historical replay runtime). UNKNOWN segments are never treated as
    safe; the recommended route is the lowest supported MODELED exposure,
    never a guarantee.
    """
    try:
        if mode == "live":
            mode_states = get_live_reach_states(departure_hour)
            forecast = fetch_delhi_rainfall_forecast(use_cache=True)
            now = datetime.now(timezone.utc)
            freshness = freshness_state(forecast.acquired_at, now)
            mode_freshness_note = (
                f"rainfall/model freshness: {freshness} (forecast acquired "
                f"{_iso(forecast.acquired_at) or 'unknown'}); road network: "
                "static OSM pilot extract (see provenance)"
            )
            model_timestamp = mode_states.model_timestamp
            forcing_source = (
                f"Open-Meteo NWP hourly forecast (status {forecast.status})"
                if forecast.status != "UNAVAILABLE"
                else "Open-Meteo NWP hourly forecast (UNAVAILABLE — routing "
                "under all-UNKNOWN risk)"
            )
        else:
            if event_id is None:
                raise HTTPException(status_code=400, detail="historical mode requires event_id")
            if event_id not in replay_harness.REPLAY_EVENT_IDS:
                raise HTTPException(status_code=404, detail=f"unknown event {event_id}")
            n_steps = get_historical_timestep_count(event_id)
            if n_steps == 0:
                raise HTTPException(
                    status_code=409,
                    detail=(
                        f"event {event_id} has no executable historical "
                        "forcing; route reconstruction is NOT_COMPUTABLE "
                        "for this event (absent forcing is never simulated)"
                    ),
                )
            if not 0 <= timestep_index < n_steps:
                raise HTTPException(
                    status_code=400,
                    detail=f"timestep_index must be in [0, {n_steps - 1}] for {event_id}",
                )
            mode_states = get_historical_reach_states(event_id, timestep_index)
            declaration = get_declaration(event_id)
            mode_freshness_note = (
                "historical evidence timestamps: forcing anchor "
                f"{_iso(mode_states.data_timestamp_utc)}; this is EVENT "
                "data (not live data) — model execution time is separate "
                "and recorded in provenance"
            )
            model_timestamp = mode_states.model_timestamp
            forcing_source = declaration.forcing_source

        result = compute_safe_route(
            origin_lon=origin_lon,
            origin_lat=origin_lat,
            dest_lon=dest_lon,
            dest_lat=dest_lat,
            mode_states=mode_states,
            model_timestamp=model_timestamp,
            forcing_source=forcing_source,
            mode_freshness_note=mode_freshness_note,
        )
        result["provenance"]["generated_at_utc"] = result["generated_at"]
        result["provenance"]["model_mode"] = production_mode()["production_mode"]
        result["data_freshness"] = {
            "note": mode_freshness_note,
            "rainfall_updated_at": _iso(mode_states.data_timestamp_utc),
            "hydraulic_run_updated_at": model_timestamp,
            "road_network_updated_at": None,  # static committed extract; see provenance
            "observation_updated_at": None,
        }
        return result
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/safe-route/segments/{segment_id}")
def get_route_segment_evidence(
    segment_id: str,
    mode: str = Query("live", pattern="^(live|historical)$"),
    departure_hour: int = Query(0, ge=0, le=3),
    event_id: Optional[str] = Query(None),
    timestep_index: int = Query(0, ge=0),
) -> Dict[str, Any]:
    """Segment-level evidence for any road segment (route-agnostic).

    Exposes the full traceability chain: segment -> spatial mapping ->
    reach -> aggregated model state -> risk translation -> timestamps.
    Missing information is UNKNOWN, never inferred.
    """
    graph = get_road_graph()
    if segment_id not in graph.edge_index:
        raise HTTPException(status_code=404, detail=f"unknown segment {segment_id}")

    if mode == "live":
        mode_states = get_live_reach_states(departure_hour)
        model_timestamp = mode_states.model_timestamp
        forcing_source = mode_states.forcing_source
    else:
        if event_id is None:
            raise HTTPException(status_code=400, detail="historical mode requires event_id")
        n_steps = get_historical_timestep_count(event_id)
        if n_steps == 0:
            mode_states = get_historical_reach_states(event_id, 0)
        else:
            if not 0 <= timestep_index < n_steps:
                raise HTTPException(
                    status_code=400,
                    detail=f"timestep_index must be in [0, {n_steps - 1}] for {event_id}",
                )
            mode_states = get_historical_reach_states(event_id, timestep_index)
        model_timestamp = mode_states.model_timestamp
        forcing_source = mode_states.forcing_source

    if mode_states.status not in ("COMPUTED", "EXECUTED") or not mode_states.member_states:
        observations: Dict[str, Any] = {}
        risk_state, reason = "UNKNOWN", (
            "model state unavailable for this mode/timestep: "
            + "; ".join(mode_states.diagnostics[:1])
        )
        mapped_reach = build_edge_reach_map().get(segment_id)
        model_state: Optional[Dict[str, Any]] = None
    else:
        observations = aggregate_reach_states(mode_states.member_states)
        mapped_reach = build_edge_reach_map().get(segment_id)
        if mapped_reach is None:
            risk_state, reason = (
                "UNKNOWN",
                "outside the modeled Kushak corridor; no defensible road-model relationship",
            )
            model_state = None
        else:
            obs = observations[mapped_reach]
            risk_state, reason = translate_reach_to_road_risk(obs)
            model_state = {
                "reach_id": mapped_reach,
                "computed_members": obs.computed_members,
                "blocked_members": obs.blocked_members,
                "any_positive_loading": obs.any_positive_loading,
                "loading_basis": obs.loading_basis,
            }

    return segment_evidence(
        edge_key=segment_id,
        risk_state=risk_state,
        reason=reason,
        mapped_reach=mapped_reach,
        model_state=model_state,
        mode=mode,
        event_id=event_id,
        timestep_index=timestep_index if mode == "historical" else departure_hour,
        model_timestamp=model_timestamp,
        forcing_source=forcing_source,
    )


# ---------------------------------------------------------------------------
# 9. V1-PARITY LIVE STATE (NOW/+1h/+2h/+3h, streets, synthetic fallback)
# ---------------------------------------------------------------------------

from backend.app.domain.delhi.live_state import (  # noqa: E402
    HORIZON_LABELS,
    WHAT_IF_PRESETS_MM,
    get_cached_live_states,
    get_cached_what_if,
    get_cached_what_if_edge_depths,
    road_risk_override_from_depths,
)


@router.get("/live-state")
def get_live_state_v1(
    horizon: str = Query("ALL", description="NOW, +1h, +2h, +3h or ALL"),
    refresh: bool = Query(False, description="Re-acquire the rainfall forecast"),
    client_rainfall_mm: Optional[str] = Query(
        None,
        description="Optional comma-separated hourly rainfall mm (NOW,+1h,+2h,+3h) when cloud egress is rate-limited",
    ),
) -> Dict[str, Any]:
    """V1-style independent flood states for the forecast horizons.

    Each horizon (NOW/+1h/+2h/+3h) is simulated SEPARATELY through the
    shared V1-reference depth model using ONLY its own hour's rainfall
    (V1's per-horizon independence rule), with street & intersection
    intelligence matched to the depth grid. When the live NWP forecast
    cannot be acquired, a labeled SYNTHETIC_FALLBACK rainfall series keeps
    the system usable — never presented as observed or forecast weather.
    """
    # Client-side horizon labels use '+' which URL-decodes to a space in
    # query strings; normalize case-insensitively ('+1H', ' 1h', '+1h' all
    # resolve to the canonical '+1h').
    h_raw = horizon.strip()
    h_norm = h_raw.upper()
    if h_norm and not h_norm.startswith(("NOW", "ALL")):
        h_norm = "+" + h_norm.lstrip("+ ")
    canonical = {label.upper(): label for label in HORIZON_LABELS}
    canonical["ALL"] = "ALL"
    if h_norm not in canonical:
        raise HTTPException(status_code=400, detail=f"horizon must be one of {list(HORIZON_LABELS)} or ALL")
    h = canonical[h_norm]

    client_mm: Optional[List[float]] = None
    if client_rainfall_mm:
        try:
            parsed = [float(x.strip()) for x in client_rainfall_mm.split(",")]
            if len(parsed) >= 4 and all(v >= 0 for v in parsed[:4]):
                client_mm = parsed[:4]
        except Exception:
            client_mm = None

    states = get_cached_live_states(use_cache=not refresh, client_rainfall_mm=client_mm)
    if h == "ALL":
        return states
    for i, label in enumerate(HORIZON_LABELS):
        if label == h:
            single = dict(states["horizons"][i])
            single["rainfall_status"] = states["rainfall_status"]
            single["rainfall_source"] = states["rainfall_source"]
            single["claim_policy"] = states["claim_policy"]
            single["provenance"] = states["provenance"]
            return single
    raise HTTPException(status_code=400, detail="unreachable horizon lookup")


@router.get("/scenario/what-if")
def get_what_if_state(
    rainfall_mm_h: float = Query(..., ge=0, le=250, description="Uniform scenario intensity [mm/h]"),
) -> Dict[str, Any]:
    """MODEL SCENARIO / WHAT-IF: one uniform intensity through the SAME
    modelled pipeline as LIVE (real backend computation, cached per
    intensity). The response is labeled MODEL_SCENARIO / WHAT-IF
    throughout — never live weather, never a forecast."""
    try:
        return get_cached_what_if(rainfall_mm_h)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/scenario/what-if/presets")
def get_what_if_presets() -> Dict[str, Any]:
    """The V1 preset intensities (20/40/50/70 mm/h) for the UI stepper."""
    return {
        "presets_mm_h": list(WHAT_IF_PRESETS_MM),
        "mode": "MODEL_SCENARIO / WHAT-IF (hypothetical inputs, real computation)",
        "claim": (
            "Scenario intensities are hypothetical model inputs evaluated "
            "through the modelled pipeline — NOT live weather and NOT a "
            "forecast."
        ),
    }


@router.get("/scenario/safe-route")
def get_scenario_safe_route(
    origin_lon: float = Query(..., description="Origin longitude (WGS84)"),
    origin_lat: float = Query(..., description="Origin latitude (WGS84)"),
    dest_lon: float = Query(..., description="Destination longitude (WGS84)"),
    dest_lat: float = Query(..., description="Destination latitude (WGS84)"),
    rainfall_mm_h: float = Query(..., ge=0, le=250, description="Scenario intensity [mm/h]"),
) -> Dict[str, Any]:
    """Flood-aware route under a WHAT-IF scenario intensity.

    The ONE routing core (deterministic Dijkstra + risk penalties) runs
    with depth-derived road risk from the scenario's modelled street
    depths (canonical hazard/exclusion thresholds): V1's behavior — deep
    segments are hard-excluded, hazardous segments penalized. Labeled
    MODEL_SCENARIO / WHAT-IF throughout.
    """
    try:
        edge_depths = get_cached_what_if_edge_depths(rainfall_mm_h)
        risk_by_edge = road_risk_override_from_depths(edge_depths)

        from backend.app.domain.delhi.routing.engine import _build_candidate, _dijkstra, _explain
        from backend.app.domain.delhi.routing.network import road_network_provenance
        from backend.app.domain.delhi.routing.risk import route_evidence_state

        graph = get_road_graph()
        o_idx, o_dist, o_name = graph.snap(origin_lon, origin_lat)
        d_idx, d_dist, d_name = graph.snap(dest_lon, dest_lat)

        edges = _dijkstra(graph, o_idx, d_idx, risk_by_edge)
        if edges is None:
            raise HTTPException(status_code=404, detail="NO_ROUTE: origin and destination are not connected under this scenario")
        recommended = _build_candidate(edges, risk_by_edge)

        multiplier = {e.road_id: 4.0 for e in recommended.edges}
        alt_edges = _dijkstra(graph, o_idx, d_idx, risk_by_edge, multiplier)
        alternative = None
        no_alt_reason = None
        if alt_edges is None:
            no_alt_reason = "no connected alternative avoiding the recommended corridor"
        else:
            alt_candidate = _build_candidate(alt_edges, risk_by_edge)
            rec_roads = {e.road_id for e in recommended.edges}
            alt_roads = {e.road_id for e in alt_candidate.edges}
            shared = len(rec_roads & alt_roads)
            denom = max(len(rec_roads | alt_roads), 1)
            if 1.0 - (shared / denom) < 0.3:
                no_alt_reason = "the best alternative is not sufficiently distinct from the recommended route"
            else:
                alternative = alt_candidate

        covered = sum(
            1 for e in recommended.edges
            if recommended.risk_by_edge[e.edge_key][0] != "UNKNOWN"
        )
        evidence_state, evidence_reason = route_evidence_state(
            total_edges=len(recommended.edges),
            covered_edges=covered,
            has_unknown_on_route=any(
                recommended.risk_by_edge[e.edge_key][0] == "UNKNOWN"
                for e in recommended.edges
            ),
            member_disagreement=False,
        )

        def route_payload(c):
            cs = c.counts_summary()
            return {
                "edges": [e.edge_key for e in c.edges],
                "geometry": {
                    "type": "Feature",
                    "properties": {},
                    "geometry": {
                        "type": "LineString",
                        "coordinates": [
                            list(e.coords_4326[0]) for e in c.edges
                        ] + [list(c.edges[-1].coords_4326[1])],
                    },
                },
                "risk_segments": {
                    "type": "FeatureCollection",
                    "features": [
                        {
                            "type": "Feature",
                            "properties": {
                                "segment_id": e.edge_key,
                                "risk_state": c.risk_by_edge[e.edge_key][0],
                                "name": e.name,
                            },
                            "geometry": {
                                "type": "LineString",
                                "coordinates": [
                                    list(e.coords_4326[0]), list(e.coords_4326[1])
                                ],
                            },
                        }
                        for e in c.edges
                        if c.risk_by_edge[e.edge_key][0] in ("UNKNOWN", "ELEVATED_RISK", "BLOCKED")
                    ],
                },
                "total_distance_km": round(c.total_distance_m / 1000.0, 2),
                "estimated_travel_time_min": round(c.travel_time_s / 60.0, 1),
                "flood_risk_summary": {
                    "blocked_segments": cs["blocked"],
                    "elevated_risk_segments": cs["elevated_risk"],
                    "unknown_segments": cs["unknown"],
                    "low_risk_segments": cs["low_risk"],
                },
                "route_state": (
                    "CONDITIONAL_UNKNOWN_RISK_PORTION" if cs["unknown"] > 0
                    else "LOWER_MODELED_RISK"
                ),
                "risk_penalty_s": round(c.risk_penalty_s, 1),
            }

        return {
            "status": "COMPUTED",
            "mode": "SCENARIO",
            "scenario": {
                "kind": "MODEL_SCENARIO",
                "label": "WHAT-IF",
                "rainfall_mm_h": rainfall_mm_h,
            },
            "generated_at": _iso(datetime.now(timezone.utc)),
            "origin": {"coords": [origin_lon, origin_lat], "snapped_road": o_name, "snap_distance_m": round(o_dist, 1)},
            "destination": {"coords": [dest_lon, dest_lat], "snapped_road": d_name, "snap_distance_m": round(d_dist, 1)},
            "recommended_route": route_payload(recommended),
            "alternative_route": route_payload(alternative) if alternative else None,
            "no_alternative_reason": no_alt_reason,
            "evidence_state": {"route_state": evidence_state, "reason": evidence_reason},
            "explanation": _explain(
                recommended, alternative, evidence_state, evidence_reason, no_alt_reason
            ),
            "max_depth_on_route_m": round(
                max(
                    (edge_depths.get(e.edge_key) or 0.0 for e in recommended.edges),
                    default=0.0,
                ), 3
            ),
            "claim_policy": (
                "MODEL SCENARIO routing: routes evaluated under a WHAT-IF "
                "uniform intensity through the modelled depth pipeline. "
                "NOT live weather, NOT a guarantee of safety."
            ),
            "provenance": {
                "road_network_source": road_network_provenance().get("source"),
                "risk_mapping_method": "modelled segment depth vs canonical hazard/exclusion thresholds",
                "routing_core": "same deterministic Dijkstra as LIVE/HISTORICAL modes",
            },
        }
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
