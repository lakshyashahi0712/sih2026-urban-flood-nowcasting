"""Time-state / timestep contracts for Phase 7D-1.

Domain contracts only; no computational logic. Establishes the time
representation, simulation state, inflow-hydrograph interface, and
simulation-result container for a future time-dependent hydraulic engine
(Phase 7D-2+). No continuity integration, routing, stage calculation,
or resampling is implemented here.

Conventions carried over from the existing hydraulic contracts:
- UNKNOWN values remain None and are never defaulted to zero.
- Provenance is tracked per quantity via ProvenanceStatus.
- Blocked states are explicit, never silently converted to computed.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, validator

from .models import ProvenanceStatus


def _require_tz_aware(field_name: str, v: datetime) -> datetime:
    """Reject naive datetimes; never convert timezones implicitly."""
    if v.tzinfo is None or v.tzinfo.utcoffset(v) is None:
        raise ValueError(
            f"{field_name} must be timezone-aware (naive datetime rejected)"
        )
    return v


def _require_finite(field_name: str, v: Optional[float]) -> Optional[float]:
    """Reject non-finite numeric values where a value is supplied."""
    if v is None:
        return None
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        raise ValueError(f"{field_name} must be a number (got {type(v).__name__})")
    if v != v or v in (float("inf"), float("-inf")):
        raise ValueError(f"{field_name} must be finite (got {v})")
    return v


class SimulationStateStatus(str, Enum):
    """Status of a simulated state at a timestep.

    Existing hydraulic statuses (BLOCKED_MISSING_GEOMETRY, etc.) are plain
    strings in the 7B/7C solver; this enum follows the same naming family
    for the time-dependent layer. Blocked states are never converted to
    COMPUTED.
    """
    COMPUTED = "COMPUTED"
    BLOCKED_MISSING_INPUT = "BLOCKED_MISSING_INPUT"
    BLOCKED_INVALID_INPUT = "BLOCKED_INVALID_INPUT"
    BLOCKED_NUMERICAL = "BLOCKED_NUMERICAL"
    UNKNOWN = "UNKNOWN"


class SimulationTimestep(BaseModel):
    """A single simulation timestep: explicit start/end, timezone-aware.

    Represents start/end explicitly (duration is derived). Zero-duration
    and backwards timesteps are rejected. No implicit timezone conversion,
    no resampling.
    """
    start: datetime
    end: datetime

    @validator('start')
    def start_tz_aware(cls, v):
        return _require_tz_aware("start", v)

    @validator('end')
    def end_tz_aware(cls, v):
        return _require_tz_aware("end", v)

    @validator('end')
    def end_after_start(cls, v, values):
        start = values.get('start')
        if start is not None and v <= start:
            raise ValueError(
                "end must be strictly after start (zero-duration and "
                "backwards timesteps rejected)"
            )
        return v

    @property
    def duration_seconds(self) -> float:
        return (self.end - self.start).total_seconds()


class SimulationState(BaseModel):
    """Simulated hydraulic state at one timestep for one node/reach.

    storage/stage/discharge are all Optional: UNKNOWN remains None and is
    distinct from 0.0. provenance describes the provenance OF THIS STATE:
    a computed state is DERIVED, never OBSERVED, regardless of the
    provenance of its inputs.
    """
    timestamp: datetime
    location_id: str  # node_id or reach_id
    status: SimulationStateStatus = SimulationStateStatus.UNKNOWN
    storage_m3: Optional[float] = None
    stage_m: Optional[float] = None
    discharge_m3_s: Optional[float] = None
    provenance: ProvenanceStatus = ProvenanceStatus.UNKNOWN
    diagnostic: Optional[str] = None

    @validator('timestamp')
    def timestamp_tz_aware(cls, v):
        return _require_tz_aware("timestamp", v)

    @validator('storage_m3')
    def storage_valid(cls, v):
        v = _require_finite("storage_m3", v)
        if v is not None and v < 0:
            raise ValueError("storage_m3 must be non-negative (negative storage invalid)")
        return v

    @validator('discharge_m3_s')
    def discharge_valid(cls, v):
        # No signed-flow convention is documented in this project, so
        # negative discharge is rejected.
        v = _require_finite("discharge_m3_s", v)
        if v is not None and v < 0:
            raise ValueError("discharge_m3_s must be non-negative")
        return v

    @validator('stage_m')
    def stage_valid(cls, v):
        return _require_finite("stage_m", v)

    @validator('provenance')
    def computed_state_not_observed(cls, v, values):
        status = values.get('status')
        if status == SimulationStateStatus.COMPUTED and v == ProvenanceStatus.OBSERVED:
            raise ValueError(
                "a COMPUTED simulation state cannot be labelled OBSERVED; "
                "computed states are DERIVED regardless of input provenance"
            )
        return v


class HydrographTimeStep(BaseModel):
    """One explicit discharge value of an inflow hydrograph.

    discharge_m3_s is Optional: None is a preserved UNKNOWN (missing
    data), distinct from 0.0. No interpolation or filling is performed.
    """
    timestamp: datetime
    discharge_m3_s: Optional[float] = None

    @validator('timestamp')
    def timestamp_tz_aware(cls, v):
        return _require_tz_aware("timestamp", v)

    @validator('discharge_m3_s')
    def discharge_valid(cls, v):
        v = _require_finite("discharge_m3_s", v)
        if v is not None and v < 0:
            raise ValueError("discharge_m3_s must be non-negative")
        return v


class InflowHydrograph(BaseModel):
    """Explicit Q(t) inflow hydrograph contract (no rainfall-runoff here).

    Steps must be strictly time-ordered with no duplicates. Missing
    discharge values are exposed as None (UNKNOWN), never filled.
    """
    source_id: str
    steps: List[HydrographTimeStep] = Field(default_factory=list)
    units: str = "m3/s"
    provenance: ProvenanceStatus = ProvenanceStatus.UNKNOWN

    @validator('units')
    def units_supported(cls, v):
        if v != "m3/s":
            raise ValueError(
                f"unsupported units '{v}'; only 'm3/s' is accepted "
                "(convert upstream, never silently)"
            )
        return v

    @validator('steps')
    def steps_ordered(cls, v):
        for a, b in zip(v, v[1:]):
            if b.timestamp <= a.timestamp:
                raise ValueError(
                    "hydrograph steps must be strictly time-ordered with no "
                    "duplicates (backwards/duplicate timestamp rejected)"
                )
        return v

    @property
    def missing_step_count(self) -> int:
        """Number of steps with UNKNOWN (None) discharge."""
        return sum(1 for s in self.steps if s.discharge_m3_s is None)


class SimulationResultStatus(str, Enum):
    """Overall outcome of a simulation run. Partial/blocked runs are
    represented explicitly and never pretend to be complete."""
    COMPLETE = "COMPLETE"
    PARTIAL = "PARTIAL"
    BLOCKED = "BLOCKED"


class SimulationResult(BaseModel):
    """Container for a future simulation run's outputs.

    Holds states, diagnostics, mass-balance diagnostics (as a passive
    field; no mass-balance computation in this phase), overall status,
    and a provenance summary. A partial/blocked run is represented via
    status + diagnostics, not by an empty success.
    """
    simulation_status: SimulationResultStatus = SimulationResultStatus.BLOCKED
    states: List[SimulationState] = Field(default_factory=list)
    diagnostics: List[str] = Field(default_factory=list)
    mass_balance_diagnostics: List[str] = Field(default_factory=list)
    provenance_summary: Dict[str, int] = Field(default_factory=dict)
