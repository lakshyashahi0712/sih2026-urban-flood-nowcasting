"""Discrete continuity/storage update for Phase 7D-2.

Implements the single time-step storage balance and nothing else:

    V_next = V_current + dt * (Q_in + Q_lateral - Q_out)

SI units throughout: seconds, m3, m3/s. UNKNOWN inputs (None) are never
treated as zero; explicit zeros are valid and distinct. No routing,
stage calculation, cross-sections, conduits, structures, overflow,
wave equations, rainfall-runoff, replay, or ML.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional

from .hydraulic_time_state import SimulationStateStatus
from .models import ProvenanceStatus

# Weakest-link ordering for provenance combination (matches the
# conservative combination used by the Phase 7C network solver).
_PROV_WEAKNESS_ORDER = [
    ProvenanceStatus.UNKNOWN,
    ProvenanceStatus.PROVISIONAL,
    ProvenanceStatus.ASSUMED,
    ProvenanceStatus.DERIVED,
    ProvenanceStatus.OFFICIAL_MODEL_VALUE,
    ProvenanceStatus.OFFICIAL,
    ProvenanceStatus.OBSERVED,
]


def combine_provenance_weakest(provenances) -> ProvenanceStatus:
    """Conservative provenance combination: weakest present wins."""
    if not provenances:
        return ProvenanceStatus.UNKNOWN
    if len(set(provenances)) == 1:
        return provenances[0]
    ranks = {p: i for i, p in enumerate(_PROV_WEAKNESS_ORDER)}
    return min(provenances, key=lambda p: ranks.get(p, len(_PROV_WEAKNESS_ORDER)))


def _is_finite_number(v) -> bool:
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        return False
    return v == v and v not in (float("inf"), float("-inf"))


@dataclass
class ContinuityUpdateInput:
    """Inputs for one discrete continuity update.

    All numeric fields are Optional: None is a preserved UNKNOWN and is
    blocked, never treated as zero. Explicit 0.0 is a valid zero.
    provenance maps each input name to its ProvenanceStatus.
    """
    dt_seconds: Optional[float] = None
    storage_current_m3: Optional[float] = None
    inflow_m3_s: Optional[float] = None
    lateral_inflow_m3_s: Optional[float] = None
    outflow_m3_s: Optional[float] = None
    provenance: Dict[str, ProvenanceStatus] = field(default_factory=dict)


@dataclass
class ContinuityUpdateResult:
    """Result of one continuity update.

    provenance of the computed storage is always DERIVED (a calculation
    is never OBSERVED, regardless of input provenance); the combined
    input provenance is kept separately in input_provenance.
    """
    status: SimulationStateStatus = SimulationStateStatus.UNKNOWN
    storage_next_m3: Optional[float] = None
    mass_balance_m3: Optional[float] = None  # net volume added: dt*(Qin+Qlat-Qout)
    diagnostic: Optional[str] = None
    provenance: ProvenanceStatus = ProvenanceStatus.UNKNOWN
    input_provenance: ProvenanceStatus = ProvenanceStatus.UNKNOWN


def compute_continuity_update(inp: ContinuityUpdateInput) -> ContinuityUpdateResult:
    """Compute V_next = V + dt * (Q_in + Q_lateral - Q_out).

    Validation order: timestep, then each flow/storage input. Any None
    required input returns BLOCKED_MISSING_INPUT (never zero). Non-finite
    or negative values return BLOCKED_INVALID_INPUT. A negative resulting
    storage is an explicit BLOCKED_INVALID_INPUT — never clipped to zero.
    """
    prov = inp.provenance or {}

    # Timestep: required, positive, finite.
    if inp.dt_seconds is None:
        return ContinuityUpdateResult(
            status=SimulationStateStatus.BLOCKED_MISSING_INPUT,
            diagnostic="Missing timestep duration (dt_seconds)",
        )
    if not _is_finite_number(inp.dt_seconds) or inp.dt_seconds <= 0:
        return ContinuityUpdateResult(
            status=SimulationStateStatus.BLOCKED_INVALID_INPUT,
            diagnostic=f"dt_seconds must be a positive finite number (got {inp.dt_seconds})",
            input_provenance=prov.get("dt", ProvenanceStatus.UNKNOWN),
        )

    # Storage, inflow, lateral inflow, outflow: all required; UNKNOWN stays UNKNOWN.
    required = [
        ("storage_current_m3", inp.storage_current_m3, "storage_current"),
        ("inflow_m3_s", inp.inflow_m3_s, "inflow"),
        ("lateral_inflow_m3_s", inp.lateral_inflow_m3_s, "lateral_inflow"),
        ("outflow_m3_s", inp.outflow_m3_s, "outflow"),
    ]
    input_provs = [prov.get(key, ProvenanceStatus.UNKNOWN) for _, _, key in required]
    input_provs.append(prov.get("dt", ProvenanceStatus.UNKNOWN))

    for name, value, key in required:
        if value is None:
            return ContinuityUpdateResult(
                status=SimulationStateStatus.BLOCKED_MISSING_INPUT,
                diagnostic=f"Missing required input '{name}' (UNKNOWN is never treated as zero)",
                input_provenance=combine_provenance_weakest(input_provs),
            )
        if not _is_finite_number(value):
            return ContinuityUpdateResult(
                status=SimulationStateStatus.BLOCKED_INVALID_INPUT,
                diagnostic=f"'{name}' must be a finite number (got {value!r})",
                input_provenance=combine_provenance_weakest(input_provs),
            )
        if value < 0:
            return ContinuityUpdateResult(
                status=SimulationStateStatus.BLOCKED_INVALID_INPUT,
                diagnostic=f"'{name}' must be non-negative (got {value})",
                input_provenance=combine_provenance_weakest(input_provs),
            )

    # Discrete continuity update (exact arithmetic on the supplied values).
    net_flow_m3_s = inp.inflow_m3_s + inp.lateral_inflow_m3_s - inp.outflow_m3_s
    mass_balance_m3 = inp.dt_seconds * net_flow_m3_s
    storage_next = inp.storage_current_m3 + mass_balance_m3

    if storage_next < 0:
        return ContinuityUpdateResult(
            status=SimulationStateStatus.BLOCKED_INVALID_INPUT,
            diagnostic=(
                f"Continuity update would drive storage negative "
                f"(V={inp.storage_current_m3} + dt*({inp.inflow_m3_s} + "
                f"{inp.lateral_inflow_m3_s} - {inp.outflow_m3_s}) = {storage_next}); "
                f"not clipped to zero"
            ),
            mass_balance_m3=mass_balance_m3,
            input_provenance=combine_provenance_weakest(input_provs),
        )

    return ContinuityUpdateResult(
        status=SimulationStateStatus.COMPUTED,
        storage_next_m3=storage_next,
        mass_balance_m3=mass_balance_m3,
        diagnostic=(
            f"V_next = V + dt*(Q_in + Q_lateral - Q_out) = "
            f"{inp.storage_current_m3} + {inp.dt_seconds}*("
            f"{inp.inflow_m3_s} + {inp.lateral_inflow_m3_s} - {inp.outflow_m3_s}) "
            f"= {storage_next} m3 (net change {mass_balance_m3:+} m3)"
        ),
        provenance=ProvenanceStatus.DERIVED,  # a computed storage is never OBSERVED
        input_provenance=combine_provenance_weakest(input_provs),
    )
