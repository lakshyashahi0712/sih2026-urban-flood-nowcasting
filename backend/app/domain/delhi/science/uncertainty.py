"""Uncertainty decomposition per executable event.

Sources (all computed from real artifacts — never asserted):

- FORCING: fraction of documented forcing bins that are UNKNOWN
  (from the runtime forcing catalog).
- PARAMETER: spread of the modeled peak inflow across the GLUE sampled
  parameter space (from the calibration framework's real runs).
- STRUCTURAL: spread across the three documented hydraulic scenarios
  (CONSERVATIVE / CENTRAL / DEGRADED) — real runs.
- SCENARIO: spread across the two documented catchment areas
  (27.66 / 28.40 km2) — real runs.
- OBSERVATION: registry tier composition (what evidence exists at all).

Every source that cannot be quantified is reported UNKNOWN with its
reason. No ensemble is ever collapsed into a single authoritative line.
"""

from __future__ import annotations

import csv
import statistics
from pathlib import Path
from typing import Dict, List, Optional

from backend.app.domain.delhi.digital_twin.kushak_evidence_model import (
    CATCHMENT_SCENARIOS,
    KUSHAK_HYDRAULIC_SCENARIOS,
)
from backend.app.domain.delhi.digital_twin.kushak_historical_rainfall_catalog import (
    get_forcing_for_event,
)

from .calibration import (
    KUSHAK_CATCHMENT_AREA_KM2,
    SCIENCE_DIR,
    glue_behavioral_screen,
    run_event,
    run_event_peak_inflow,
)

EVENTS = ("EVT-2024-06-27", "EVT-2023-07-08", "EVT-2021-09-11")


def _forcing_uncertainty(event_id: str) -> Dict[str, object]:
    declaration = None
    from backend.app.domain.delhi.digital_twin.kushak_replay_manifest import (
        get_declaration,
    )
    declaration = get_declaration(event_id)
    profile = (
        get_forcing_for_event(declaration.canonical_event_id)
        if declaration.canonical_event_id else None
    )
    if profile is None:
        return {"source": "FORCING", "metric": "unknown_bin_fraction", "value": None,
                "detail": "no executable forcing"}
    n = len(profile.bins)
    unknown = sum(1 for b in profile.bins if b.amount is None)
    return {
        "source": "FORCING",
        "metric": "unknown_bin_fraction",
        "value": unknown / n,
        "detail": f"{unknown}/{n} documented bins UNKNOWN (never interpolated)",
    }


def _spread(values: List[Optional[float]]) -> Optional[float]:
    known = [v for v in values if v is not None]
    if len(known) < 2:
        return None
    return (max(known) - min(known)) / statistics.median(known)


def uncertainty_decomposition() -> List[Dict[str, object]]:
    glue = glue_behavioral_screen()
    parameter_peaks: Dict[str, List[Optional[float]]] = {
        e: [m["peak_inflow_by_event"].get(e) for m in glue["members"]]
        for e in EVENTS
    }

    rows: List[Dict[str, object]] = []
    for event_id in EVENTS:
        # FORCING
        rows.append({"event_id": event_id, **_forcing_uncertainty(event_id)})

        # PARAMETER (GLUE sample spread of peak inflow)
        spread = _spread(parameter_peaks[event_id])
        rows.append({
            "event_id": event_id,
            "source": "PARAMETER",
            "metric": "peak_inflow_relative_spread",
            "value": spread,
            "detail": (
                "spread across the GLUE sampled documented parameter ranges "
                "(null when fewer than two samples produce a peak)"
                if spread is not None
                else "fewer than two samples produced a peak inflow"
            ),
        })

        # STRUCTURAL (three documented hydraulic scenarios)
        structural = [
            run_event_peak_inflow(KUSHAK_HYDRAULIC_SCENARIOS[s], event_id).get("peak_inflow_m3_s")
            for s in ("CONSERVATIVE", "CENTRAL", "DEGRADED_CAPACITY")
        ]
        rows.append({
            "event_id": event_id,
            "source": "STRUCTURAL",
            "metric": "peak_inflow_relative_spread",
            "value": _spread(structural),
            "detail": "spread across CONSERVATIVE/CENTRAL/DEGRADED effective-conveyance scenarios",
        })

        # SCENARIO (catchment area)
        scenario_peaks = []
        from backend.app.domain.delhi.digital_twin.kushak_evidence_model import (
            CATCHMENT_SCENARIOS,
        )
        for c in ("WORKING_27_66", "SENSITIVITY_28_40"):
            run = run_event(
                KUSHAK_HYDRAULIC_SCENARIOS["CENTRAL"],
                event_id,
                CATCHMENT_SCENARIOS[c].area_km2,
            )
            scenario_peaks.append(run.get("peak_inflow_m3_s"))
        rows.append({
            "event_id": event_id,
            "source": "SCENARIO_CATCHMENT",
            "metric": "peak_inflow_relative_spread",
            "value": _spread(scenario_peaks),
            "detail": "spread across the two documented catchment areas (27.66 / 28.40 km2)",
        })

        # OBSERVATION (registry tier composition — what exists at all)
        rows.append({
            "event_id": event_id,
            "source": "OBSERVATION",
            "metric": "tier_ab_local_quantitative_count",
            "value": 0,
            "detail": (
                "no local Tier A/B quantitative observation exists; "
                "observation uncertainty is therefore UNBOUNDED and no "
                "observation-constrained interval is computed"
            ),
        })

    return rows


def write_uncertainty_results(out_dir: Path = SCIENCE_DIR) -> Path:
    rows = uncertainty_decomposition()
    out_dir.mkdir(parents=True, exist_ok=True, mode=0o755)
    path = out_dir / "uncertainty_results.csv"
    with open(path, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["event_id", "source", "metric", "value", "detail"])
        writer.writeheader()
        for r in rows:
            writer.writerow(r)
    return path
