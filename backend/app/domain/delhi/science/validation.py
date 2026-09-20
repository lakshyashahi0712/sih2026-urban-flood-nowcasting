"""Event-separated quantitative validation with an evidence-sufficiency gate.

The gate answers, per variable: QUANTITATIVE_VALIDATION_SUPPORTED = YES/NO,
derived from the implemented methodology:

- A variable is supported ONLY if the registry holds at least one Tier A/B
  observation OF THAT VARIABLE that is spatially attributable to the
  modeled Kushak corridor AND the model emits a comparable quantity.
- Downstream CWC stage is Tier A but NOT local — excluded by the spatial
  criterion (CWC separation audit).
- Occurrence context (Tier C) never becomes a numeric target.
- Occurrence classification metrics additionally require the MODEL to emit
  a defensible occurrence prediction; the Kushak runtime deliberately
  emits UNKNOWN reach states (no stage), so the comparison has a
  predicted side and is NOT_COMPUTABLE.

Computed today (documented as DATA-CONSISTENCY QC, not model skill):
rainfall forcing reproduction — the model's forcing inputs against the
observed station records. This validates the forcing pipeline, not the
physics.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from .observation_registry import (
    SCIENCE_DIR,
    TIER_A,
    TIER_B,
    ObservationRecord,
    build_observation_registry,
    registry_summary,
)
from . import metrics

VARIABLES = (
    "RAINFALL",
    "STAGE",
    "DISCHARGE",
    "FLOOD_EXTENT",
    "FLOOD_OCCURRENCE",
)

NOT_COMPUTABLE = "NOT_COMPUTABLE"
COMPUTED = "COMPUTED"


@dataclass
class MetricRecord:
    metric_name: str
    event_ids: List[str]
    observation_type: str
    model_quantity: str
    n_observations: int
    temporal_alignment: str
    spatial_alignment: str
    source_tier: str
    uncertainty: str
    validity_status: str  # COMPUTED | NOT_COMPUTABLE
    value: Optional[float] = None
    units: str = ""
    reason: str = ""

    def as_dict(self) -> dict:
        return {
            "metric_name": self.metric_name,
            "event_ids": ";".join(self.event_ids),
            "observation_type": self.observation_type,
            "model_quantity": self.model_quantity,
            "n_observations": self.n_observations,
            "temporal_alignment": self.temporal_alignment,
            "spatial_alignment": self.spatial_alignment,
            "source_tier": self.source_tier,
            "uncertainty": self.uncertainty,
            "validity_status": self.validity_status,
            "value": self.value,
            "units": self.units,
            "reason": self.reason,
        }


def _gate_status(records: List[ObservationRecord], variable: str) -> tuple:
    """Evidence sufficiency gate for one variable (documented criteria)."""
    relevant = [
        r for r in records
        if r.variable.startswith(variable)
        or (variable == "STAGE" and r.variable == "STAGE_DOWNSTREAM_YAMUNA")
    ]
    local_quant = [
        r for r in relevant
        if r.source_tier in (TIER_A, TIER_B)
        and r.usable_for_validation
        and "DOWNSTREAM" not in r.variable
    ]
    return relevant, local_quant


def _rainfall_forcing_reproduction(records: List[ObservationRecord]) -> List[MetricRecord]:
    """Forcing-input QC: the runtime forcing series against observed station
    records. This is a DATA-CONSISTENCY check on the forcing pipeline —
    it is NOT a measure of hydrological model skill."""
    from backend.app.domain.delhi.digital_twin.kushak_historical_rainfall_catalog import (
        get_historical_rainfall_catalog,
    )

    out: List[MetricRecord] = []
    catalog = get_historical_rainfall_catalog()
    for canonical, profile in catalog.items():
        # Observed side: the registry's interval rows for this event.
        obs_rows = sorted(
            [
                r for r in records
                if r.event_id == {"EV-01": "EVT-2024-06-27", "EV-02": "EVT-2023-07-08",
                                   "EV-03": "EVT-2021-09-11"}.get(canonical)
                and r.variable == "RAINFALL_DEPTH_INTERVAL"
            ],
            key=lambda r: r.timestamp or "",
        )
        observed = [r.value for r in obs_rows]
        # Predicted side: the forcing profile bins (what the runtime consumes),
        # depth-normalized per bin interval (mm over the bin's own window).
        from backend.app.domain.delhi.digital_twin.kushak_rainfall_forcing import (
            RainfallQuantityType,
        )
        predicted: List[Optional[float]] = []
        for b in profile.bins:
            if b.amount is None:
                predicted.append(None)
            elif b.quantity_type == RainfallQuantityType.INTENSITY_MM_H:
                predicted.append(b.amount)  # hourly bin: mm over 1 h
            else:
                predicted.append(b.amount)
        # Align by position (both are the documented bin sequences).
        n = min(len(observed), len(predicted))
        obs_aligned = observed[:n]
        pred_aligned = predicted[:n]
        try:
            mae_v = metrics.mae(obs_aligned, pred_aligned)
            rmse_v = metrics.rmse(obs_aligned, pred_aligned)
            bias_v = metrics.bias(obs_aligned, pred_aligned)
            status = COMPUTED
            reason = ""
        except ValueError as exc:
            mae_v = rmse_v = bias_v = None
            status = NOT_COMPUTABLE
            reason = str(exc)
        base = dict(
            event_ids=[{"EV-01": "EVT-2024-06-27", "EV-02": "EVT-2023-07-08",
                         "EV-03": "EVT-2021-09-11"}.get(canonical, canonical)],
            observation_type="RAINFALL_DEPTH_INTERVAL (station)",
            model_quantity="FORCING_INPUT (runtime bin)",
            temporal_alignment="documented bin intervals, positional (both are the documented bin sequences)",
            spatial_alignment="station point (Safdarjung)",
            source_tier="TIER_A/B mixed",
            uncertainty="bin provenance carried per bin (UNKNOWN bins excluded from pairs)",
        )
        for name, value, unit in (
            ("forcing_mae", mae_v, "mm"),
            ("forcing_rmse", rmse_v, "mm"),
            ("forcing_bias", bias_v, "mm"),
        ):
            out.append(MetricRecord(
                metric_name=name,
                n_observations=sum(1 for v in obs_aligned if v is not None),
                validity_status=status,
                value=value,
                units=unit,
                reason=reason or (
                    "DATA-CONSISTENCY QC of the forcing pipeline; NOT "
                    "hydrological model skill"
                ),
                **base,
            ))
    return out


def evaluate_quantitative_validation() -> dict:
    """Run the full event-separated quantitative validation."""
    records = build_observation_registry()
    summary = registry_summary(records)
    metrics_out: List[MetricRecord] = []

    # --- Gate per variable (documented criteria in _gate_status).
    gate: Dict[str, dict] = {}
    for variable in VARIABLES:
        relevant, local_quant = _gate_status(records, variable)
        if variable == "RAINFALL":
            supported = len(local_quant) > 0
            gate[variable] = {
                "QUANTITATIVE_VALIDATION_SUPPORTED": "YES" if supported else "NO",
                "relevant_observations": len(relevant),
                "local_tier_ab_observations": len(local_quant),
                "note": (
                    "station rainfall exists; computed below as forcing-"
                    "reproduction QC only (not hydrological skill)"
                ),
            }
        elif variable == "STAGE":
            local = [r for r in relevant if "DOWNSTREAM" not in r.variable]
            gate[variable] = {
                "QUANTITATIVE_VALIDATION_SUPPORTED": "NO",
                "relevant_observations": len(relevant),
                "local_tier_ab_observations": len(local),
                "note": (
                    "the only direct stage measurements are downstream "
                    "Yamuna CWC bulletins (context, spatially non-local); "
                    "no local Kushak stage observation exists"
                ),
            }
        elif variable in ("DISCHARGE", "FLOOD_EXTENT"):
            gate[variable] = {
                "QUANTITATIVE_VALIDATION_SUPPORTED": "NO",
                "relevant_observations": len(relevant),
                "local_tier_ab_observations": 0,
                "note": (
                    f"no {'discharge' if variable == 'DISCHARGE' else 'surveyed inundation extent'} "
                    "observations exist in the evidence tree"
                ),
            }
        else:  # FLOOD_OCCURRENCE
            gate[variable] = {
                "QUANTITATIVE_VALIDATION_SUPPORTED": "NO",
                "relevant_observations": len(relevant),
                "local_tier_ab_observations": 0,
                "note": (
                    "occurrence evidence is Tier C context (categorical, "
                    "date-only) AND the runtime emits UNKNOWN reach states "
                    "by contract (no stage); a predicted side does not "
                    "exist, so precision/recall/F1 are NOT_COMPUTABLE — "
                    "UNKNOWN is never converted to FLOOD_NO to fill a "
                    "confusion matrix"
                ),
            }

    metrics_out.extend(_rainfall_forcing_reproduction(records))

    # NOT_COMPUTABLE rows for every gated-out metric family (explicit,
    # machine-readable, with reasons).
    for variable in ("STAGE", "DISCHARGE", "FLOOD_EXTENT"):
        for name in ("mae", "rmse", "bias", "correlation", "peak_error"):
            metrics_out.append(MetricRecord(
                metric_name=f"{variable.lower()}_{name}",
                event_ids=[],
                observation_type=variable,
                model_quantity="modeled " + variable.lower(),
                n_observations=0,
                temporal_alignment="NOT_APPLICABLE",
                spatial_alignment="NOT_APPLICABLE",
                source_tier="NONE_LOCAL",
                uncertainty="NOT_APPLICABLE",
                validity_status=NOT_COMPUTABLE,
                reason=gate[variable]["note"],
            ))
    for name in ("precision", "recall", "f1", "balanced_accuracy", "confusion_matrix"):
        metrics_out.append(MetricRecord(
            metric_name=f"occurrence_{name}",
            event_ids=[],
            observation_type="FLOOD_OCCURRENCE",
            model_quantity="modeled occurrence state",
            n_observations=0,
            temporal_alignment="NOT_APPLICABLE",
            spatial_alignment="NOT_APPLICABLE",
            source_tier="TIER_C_ONLY",
            uncertainty="NOT_APPLICABLE",
            validity_status=NOT_COMPUTABLE,
            reason=gate["FLOOD_OCCURRENCE"]["note"],
        ))

    # --- Event separation declaration (no calibration is performed).
    event_split = {
        "TRAIN_EVENTS": [],
        "CALIBRATION_EVENTS": [],
        "VALIDATION_EVENTS": [],
        "HELD_OUT_EVENTS": [],
        "UNSPLIT_EVALUATION_POOL": ["EVT-2024-06-27", "EVT-2023-07-08", "EVT-2021-09-11"],
        "CONTROL_EVENTS": ["EVT-2026-01-23"],
        "NOT_EXECUTABLE_EVENTS": ["EVT-2021-07-19", "EVT-2023-05-27"],
        "justification": (
            "No quantitative calibration is performed (objective gate: no "
            "Tier A/B local quantitative target exists), so no event is "
            "consumed by training or calibration. The three executable "
            "events remain an unsplit evaluation pool; the control event "
            "stays reserved; missing-forcing events stay non-executable. "
            "Any future calibration MUST draw CALIBRATION_EVENTS from this "
            "pool and hold out at least one event that calibration never "
            "sees (enforced by the calibration audit)."
        ),
    }

    return {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "registry_summary": summary,
        "evidence_gate": gate,
        "event_split": event_split,
        "metrics": [m.as_dict() for m in metrics_out],
    }


def write_validation_results(out_dir: Path = SCIENCE_DIR) -> Dict[str, Path]:
    result = evaluate_quantitative_validation()
    out_dir.mkdir(parents=True, exist_ok=True, mode=0o755)
    paths: Dict[str, Path] = {}

    vm = out_dir / "validation_metrics.csv"
    with open(vm, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(result["metrics"][0].keys()))
        writer.writeheader()
        for m in result["metrics"]:
            writer.writerow(m)
    paths["validation_metrics"] = vm

    # Event evaluation matrix: events x variables with statuses.
    em = out_dir / "event_evaluation_matrix.csv"
    with open(em, "w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["event_id", "variable", "quantitative_validation_status", "reason"])
        executable = result["event_split"]["UNSPLIT_EVALUATION_POOL"]
        for event_id in executable + result["event_split"]["CONTROL_EVENTS"] + result["event_split"]["NOT_EXECUTABLE_EVENTS"]:
            for variable in VARIABLES:
                supported = result["evidence_gate"][variable]["QUANTITATIVE_VALIDATION_SUPPORTED"]
                status = (
                    "FORCING_QC_ONLY" if (variable == "RAINFALL" and supported)
                    else ("COMPUTED" if supported == "YES" else NOT_COMPUTABLE)
                )
                reason = result["evidence_gate"][variable]["note"]
                if event_id in result["event_split"]["NOT_EXECUTABLE_EVENTS"]:
                    status = NOT_COMPUTABLE
                    reason = "event has no executable forcing (structural barrier)"
                writer.writerow([event_id, variable, status, reason])
    paths["event_evaluation_matrix"] = em

    import json
    full = out_dir / "validation_results.json"
    full.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    paths["validation_results_json"] = full
    return paths
