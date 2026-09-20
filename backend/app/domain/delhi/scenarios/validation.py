"""SYNTHETIC VALIDATION — a SEPARATE category from real-event validation.

The controlled synthetic ground truth is an INDEPENDENT local (non-routed)
depression reference that shares the scenario forcing but uses a
different mechanism than the routed surface pass. Metrics therefore
compare two distinct model responses; they say NOTHING about real-world
accuracy and are labeled as such.

Report header is always:
    "SYNTHETIC VALIDATION - CONTROLLED TEST DATA"
Real-event accuracy metrics are untouched and separate.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from backend.app.domain.delhi.scenarios.config import depth_config
from backend.app.domain.delhi.science import metrics as M


def _flood_mask(depth_cm: "object") -> List[Optional[bool]]:
    import numpy as np

    shallow = depth_config()["thresholds_cm"]["SHALLOW"]
    arr = np.asarray(depth_cm, dtype=np.float64)
    return [bool(v >= shallow) if not np.isnan(v) else None for v in arr.ravel()]


def synthetic_validation(
    pipeline_steps: List[dict],   # each: {'max_depth_cm', 'depth_field_cm', ...}
    truth_steps: List[dict],      # each: {'max_truth_depth_cm', 'field', ...}
) -> dict:
    """Depth + extent + occurrence metrics: ROUTED pipeline vs CONTROLLED
    LOCAL reference, per step and aggregated."""
    assert len(pipeline_steps) == len(truth_steps)

    depth_pair_obs: List[Optional[float]] = []
    depth_pair_pred: List[Optional[float]] = []
    import numpy as np

    per_step: List[dict] = []
    for p, t in zip(pipeline_steps, truth_steps):
        pred = np.asarray(p.get("depth_field_cm"), dtype=np.float64).ravel()
        obs = np.asarray(t.get("field"), dtype=np.float64).ravel()
        n = min(pred.size, obs.size)
        depth_pair_obs.extend(list(obs[:n]))
        depth_pair_pred.extend(list(pred[:n]))

        obs_mask = _flood_mask(obs[:n])
        pred_mask = _flood_mask(pred[:n])
        step = {"timestep_index": p.get("timestep_index")}
        try:
            e = M.extent_metrics(obs_mask, pred_mask)
            step["extent"] = {k: (round(v, 4) if isinstance(v, float) else v) for k, v in e.items()}
        except ValueError:
            step["extent"] = {"status": "NOT_COMPUTABLE", "reason": "empty union after exclusions"}
        try:
            step["depth"] = {
                "mae_cm": round(M.mae(obs, pred), 3),
                "rmse_cm": round(M.rmse(obs, pred), 3),
                "bias_cm": round(M.bias(obs, pred), 3),
            }
        except ValueError:
            step["depth"] = {"status": "NOT_COMPUTABLE", "reason": "no valid pairs"}
        per_step.append(step)

    # Aggregated metrics.
    aggregated: Dict[str, object] = {}
    try:
        aggregated["depth"] = {
            "mae_cm": round(M.mae(depth_pair_obs, depth_pair_pred), 3),
            "rmse_cm": round(M.rmse(depth_pair_obs, depth_pair_pred), 3),
            "bias_cm": round(M.bias(depth_pair_obs, depth_pair_pred), 3),
            "n_cells": len([x for x in depth_pair_obs if x is not None]),
        }
    except ValueError as exc:
        aggregated["depth"] = {"status": "NOT_COMPUTABLE", "reason": str(exc)}
    try:
        # Occurrence metrics on cell-level flooded-vs-not (with None filter):
        # UNKNOWN cells are excluded, never counted as negatives.
        obs_lab = [bool(v >= depth_config()["thresholds_cm"]["SHALLOW"]) if v is not None else None for v in depth_pair_obs]
        pred_lab = [bool(p >= depth_config()["thresholds_cm"]["SHALLOW"]) if p is not None else None for p in depth_pair_pred]
        cls = M.classification_metrics(obs_lab, pred_lab)
        aggregated["occurrence"] = {
            "precision": round(cls["precision"], 4) if cls["precision"] is not None else None,
            "recall": round(cls["recall"], 4) if cls["recall"] is not None else None,
            "f1": round(cls["f1"], 4) if cls["f1"] is not None else None,
            "confusion_matrix": cls["confusion_matrix"],
        }
    except ValueError as exc:
        aggregated["occurrence"] = {"status": "NOT_COMPUTABLE", "reason": str(exc)}
    try:
        # Aggregated extent IoU over the pooled masks.
        all_obs = [bool(v >= depth_config()["thresholds_cm"]["SHALLOW"]) if v is not None else None for v in depth_pair_obs]
        all_pred = [bool(p >= depth_config()["thresholds_cm"]["SHALLOW"]) if p is not None else None for p in depth_pair_pred]
        e = M.extent_metrics(all_obs, all_pred)
        aggregated["extent"] = {k: (round(v, 4) if isinstance(v, float) else v) for k, v in e.items()}
    except ValueError as exc:
        aggregated["extent"] = {"status": "NOT_COMPUTABLE", "reason": str(exc)}

    return {
        "category": "SYNTHETIC VALIDATION - CONTROLLED TEST DATA",
        "note": (
            "Routed 2D surface pass vs the INDEPENDENT local (non-routed) "
            "reference on the same controlled forcing. This validates "
            "pipeline behaviour on synthetic data only; it says NOTHING "
            "about real-world accuracy and is completely separate from "
            "real-event validation."
        ),
        "per_step": per_step,
        "aggregated": aggregated,
    }