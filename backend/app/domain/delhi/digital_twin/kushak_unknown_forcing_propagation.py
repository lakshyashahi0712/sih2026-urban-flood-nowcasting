"""Phase 9 Step 5: UNKNOWN forcing propagation (deterministic, evidence-constrained).

Propagates UNKNOWN/BLOCKED forcing through the model chain without imputation,
interpolation, smoothing, zero-substitution, or estimation. Existing Phase 8B
state/hydraulic contracts reused; no new thresholds, no new geometry.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple

from .models import ProvenanceStatus
from .rainfall_to_inflow import RainfallToInflowResult, rainfall_to_inflow
from .kushak_rainfall_scenario import ScenarioForcing, load_june_2024_forcing, BLOCK_OBSERVATIONS
from .hydraulic_time_state import SimulationTimestep


@dataclass(frozen=True)
class UnknownPropagationResult:
    """Immutable record of the UNKNOWN forcing propagation outcome.

    Keeps the forcing timestep identity and provenance intact.
    Never exposes a fabricated numeric value for an UNKNOWN timestep.
    """
    forcing_timesteps: Tuple[str, ...]
    forcing_statuses: Tuple[str, ...]  # per timestep: the forcing classification
    propagation_status: str  # "COMPUTED" or "BLOCKED" or "UNKNOWN"
    diagnostics: Tuple[str, ...]
    provenance: ProvenanceStatus = ProvenanceStatus.DERIVED
    underlying_forcing_remains: ProvenanceStatus = ProvenanceStatus.UNKNOWN


def propagate_unknown_forcing(
    forcing: Optional[ScenarioForcing] = None,
) -> UnknownPropagationResult:
    """Propagate UNKNOWN forcing explicitly without fabrication.

    Rules (strict):
    - If forcing has any UNKNOWN depth at a timestep, that timestep
      remains UNKNOWN (never interpolated, imputed, smoothed, zeroed,
      averaged, filled from neighbors, stations, or model output).
    - The propagation result is DERIVED as a record of the operation,
      but the underlying forcing stays UNKNOWN.
    - No new hydraulic parameters or thresholds are introduced.
    """
    if forcing is None:
        forcing = load_june_2024_forcing()

    statuses: List[str] = []
    diagnostics: List[str] = []
    timestep_labels: List[str] = []

    for i, ts in enumerate(forcing.timesteps):
        timestep_labels.append(str(ts.start))
        depth = forcing.depths_mm[i] if i < len(forcing.depths_mm) else None
        if depth is None:
            statuses.append("UNKNOWN")
            diagnostics.append(
                f"Timestep {i} ({str(ts.start)}): forcing UNKNOWN (None); "
                "no interpolation, no zero-substitution, no imputation"
            )
        elif depth == 0.0:
            statuses.append("VERIFIED_ZERO")
            diagnostics.append(
                f"Timestep {i} ({str(ts.start)}): forcing VERIFIED_ZERO"
            )
        else:
            # Positive finite rainfall is considered supported here.
            statuses.append("COMPUTED")
            diagnostics.append(
                f"Timestep {i} ({str(ts.start)}): forcing supported (value={depth})"
            )

    # The contract requires at least one UNKNOWN timestep to trigger
    # BLOCKED/UNKNOWN propagation. If any timestep is UNKNOWN, the result
    # reflects an UNKNOWN boundary, not a fabricated numerical output.
    has_unknown = any(s == "UNKNOWN" for s in statuses)
    propagation_status = "BLOCKED" if has_unknown else "COMPUTED"

    return UnknownPropagationResult(
        forcing_timesteps=tuple(timestep_labels),
        forcing_statuses=tuple(statuses),
        propagation_status=propagation_status,
        diagnostics=tuple(diagnostics),
        provenance=ProvenanceStatus.DERIVED,
        underlying_forcing_remains=ProvenanceStatus.UNKNOWN,
    )
