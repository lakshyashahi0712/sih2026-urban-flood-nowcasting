"""Delhi/Kushak 0-3h operational nowcast service (V2 product surface).

Composes the EXISTING canonical runtime path — rainfall_to_inflow ->
run_hydrograph_simulation (via run_integrated_simulation), then
advance_chain_series and classify_chain_timestep over the locked reach
chain — with an NWP rainfall forecast for the documented Safdarjung
reference point.

CORE SCIENTIFIC RULES (mirroring the Phase 8A/15.5 evidence contracts):

- The NWP forecast is a MODEL-FORECAST input, provenance DERIVED with
  explicit source reference. It is never labeled observed.
- Forecast hours become exactly one runtime timestep each (resolution
  preserved). A missing forecast hour stays UNKNOWN (None depth) and
  propagates as a blocked timestep — no zero-fill, no interpolation.
- The deterministic 6-member ensemble (build_kushak_ensemble) is executed
  through the same boundary conventions as the Phase 15.5 historical
  replay: explicit zero outflow (ASSUMED) on UG-01/OC-01/CD-01 with the
  mandatory Tier-B effective-scenario declaration on UG-01; OC-02 is
  terminal with NO outflow decision (no Yamuna/free-outfall assumption).
- Reach stage stays UNKNOWN (no storage-stage relation exists); capacity
  comparisons without stage are BLOCKED by the existing contract and are
  never invented here. The nowcast therefore reports inflow/storage
  envelopes (MODEL_DERIVED) and honest UNKNOWN states — never depth
  predictions.
- Everything is labeled: FORECAST (input), MODEL_DERIVED (runtime), or
  UNKNOWN. A failed or stale fetch yields an explicit operational state,
  never a fabricated nowcast.
"""

from __future__ import annotations

import os
import statistics
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Sequence, Tuple

from .digital_twin.kushak_evidence_model import (
    backbone_slope_m_per_m,
    covered_effective_profile,
)
from .digital_twin.kushak_scenario_ensemble import (
    KushakEnsembleMember,
    build_kushak_ensemble,
)
from .digital_twin.kushak_continuity_routing import (
    ChainStepSpec,
    advance_chain_series,
)
from .digital_twin.kushak_evidence_model import (
    CATCHMENT_SCENARIOS,
    KUSHAK_HYDRAULIC_SCENARIOS,
)
from .digital_twin.kushak_hydraulic_state_classification import (
    classify_chain_timestep,
)
from .digital_twin.kushak_serial_routing import OutflowRule, ReachOutflowDecision
from .digital_twin.hydraulic_integrated_orchestrator import run_integrated_simulation
from .digital_twin.hydraulic_time_state import (
    SimulationState,
    SimulationStateStatus,
    SimulationTimestep,
)
from .digital_twin.models import ProvenanceStatus

# IST = UTC+05:30 — the forcing catalog's documented observation timezone.
IST = timezone(timedelta(hours=5, minutes=30))

# Documented rainfall reference point for the Kushak evidence lineage
# (Safdarjung — the same station the historical forcing catalog cites).
# The NWP grid point is taken at this reference; it is NOT a gauge
# observation of the catchment.
SAFDARJUNG_LAT = 28.5862
SAFDARJUNG_LON = 77.2090
SAFDARJUNG_REFERENCE = "Safdarjung (documented Kushak forcing reference station)"

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"

# Phase 8A evidence-scenario initial-state convention (mirrored from the
# Phase 15.5 replay harness, not redefined).
INITIAL_STORAGE_M3 = 10000.0
INITIAL_DEPTH_M = 1.0

# Operational refresh policy for the NWP fetch.
CACHE_TTL_MINUTES = 15.0
FETCH_TIMEOUT_SECONDS = 10.0
NOWCAST_HORIZON_HOURS = 4  # t+0..t+3 hourly bins


# ---------------------------------------------------------------------------
# NWP forecast fetch (explicit operational states, no fabrication)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ForecastBin:
    """One forecast hour. depth_mm None = UNKNOWN (missing forecast hour)."""

    time_start: datetime
    time_end: datetime
    depth_mm: Optional[float]
    provenance: str  # DERIVED (NWP model value) or UNKNOWN


@dataclass
class DelhiForecastFetch:
    """Outcome of one Open-Meteo forecast acquisition attempt.

    status is COMPUTED (fresh fetch), STALE (fallback to an older cached
    fetch), or UNAVAILABLE (no data; reason in diagnostics). The fetch is
    an input acquisition record — never itself a nowcast.
    """

    status: str
    reference_point: str
    latitude: float
    longitude: float
    acquired_at: Optional[datetime]
    bins: Tuple[ForecastBin, ...] = ()
    diagnostics: List[str] = field(default_factory=list)
    source: str = "Open-Meteo NWP hourly forecast (model value, not observed)"


class _ForecastCache:
    """In-process cache of the last successful fetch (freshness tracked)."""

    def __init__(self) -> None:
        self._fetch: Optional[DelhiForecastFetch] = None
        self._acquired: Optional[datetime] = None

    def put(self, fetch: DelhiForecastFetch, acquired: datetime) -> None:
        self._fetch = fetch
        self._acquired = acquired

    def get_fresh(self, now: datetime, ttl_minutes: float) -> Optional[DelhiForecastFetch]:
        if self._fetch is None or self._acquired is None:
            return None
        if now - self._acquired <= timedelta(minutes=ttl_minutes):
            return self._fetch
        return None

    def get_stale(self) -> Optional[Tuple[DelhiForecastFetch, datetime]]:
        if self._fetch is None or self._acquired is None:
            return None
        return self._fetch, self._acquired


_CACHE = _ForecastCache()


def _http_get(url: str, timeout: float):
    """Transport seam (module-level so tests can inject a deterministic
    client without network access)."""
    import httpx

    headers = {
        "User-Agent": "SIH2026-UrbanFloodNowcast/2.0 (sih2026-flood-nowcasting)",
        "Accept": "application/json",
    }
    return httpx.get(url, headers=headers, timeout=timeout)


def _parse_open_meteo_payload(payload: dict, requested_utc_now: datetime) -> Tuple[ForecastBin, ...]:
    """Convert the Open-Meteo hourly payload into contiguous IST bins.

    The response's hourly series is used as-is: each hour is one bin with
    its documented amount (mm per hour). Missing values stay UNKNOWN.
    Only the nowcast horizon window is returned.
    """
    hourly = payload.get("hourly") or {}
    times = hourly.get("time") or []
    precip = hourly.get("precipitation") or []
    if not times:
        raise ValueError("Open-Meteo payload has no hourly series")

    # The 0-3h window opens at the current hour's start (IST) and takes
    # four hourly bins in documented order. The series may begin on the
    # previous local day (provider day-boundary behavior), so the window
    # is located by timestamp, never by position.
    now_ist = requested_utc_now.astimezone(IST)
    current_hour_start = now_ist.replace(minute=0, second=0, microsecond=0)

    parsed: List[Tuple[datetime, Optional[float]]] = []
    for i, t in enumerate(times):
        try:
            t_ist = datetime.strptime(t, "%Y-%m-%dT%H:%M").replace(tzinfo=IST)
        except ValueError:
            continue
        value = precip[i] if i < len(precip) else None
        if value is None or not isinstance(value, (int, float)) or value < 0:
            parsed.append((t_ist, None))  # missing/unphysical -> UNKNOWN, never clamped
        else:
            parsed.append((t_ist, float(value)))

    start_index: Optional[int] = None
    for i, (t_ist, _) in enumerate(parsed):
        if t_ist >= current_hour_start:
            start_index = i
            break
    if start_index is None:
        raise ValueError("forecast series does not cover the current hour window")

    bins: List[ForecastBin] = []
    for offset in range(NOWCAST_HORIZON_HOURS):
        idx = start_index + offset
        if idx >= len(parsed):
            break  # honest short horizon; never padded
        t_start, amount = parsed[idx]
        bins.append(ForecastBin(
            time_start=t_start,
            time_end=t_start + timedelta(hours=1),
            depth_mm=amount,
            provenance="DERIVED" if amount is not None else "UNKNOWN",
        ))
    return tuple(bins)


def fetch_delhi_rainfall_forecast(
    use_cache: bool = True,
    client: Optional[Any] = None,
) -> DelhiForecastFetch:
    """Acquire the 0-3h NWP forecast for the documented reference point.

    `client` is injectable for deterministic tests (an object exposing
    ``get(url, timeout=...)`` returning an object with ``raise_for_status``
    and ``json()``), mirroring the existing Mumbai adapter's contract.
    Failure modes are explicit operational states — never synthetic data.
    """
    requested_utc_now = datetime.now(timezone.utc)

    if use_cache:
        fresh = _CACHE.get_fresh(requested_utc_now, CACHE_TTL_MINUTES)
        if fresh is not None:
            return fresh

    api_key = os.getenv("OPEN_METEO_API_KEY", "").strip()
    key_param = f"&apikey={api_key}" if api_key else ""
    params = (
        f"?latitude={SAFDARJUNG_LAT}&longitude={SAFDARJUNG_LON}"
        f"&hourly=precipitation&forecast_days=2&timezone=Asia%2FKolkata{key_param}"
    )
    try:
        if client is not None:
            response = client.get(OPEN_METEO_URL + params, timeout=FETCH_TIMEOUT_SECONDS)
            response.raise_for_status()
            payload = response.json()
        else:
            response = _http_get(OPEN_METEO_URL + params, FETCH_TIMEOUT_SECONDS)
            response.raise_for_status()
            payload = response.json()
        bins = _parse_open_meteo_payload(payload, requested_utc_now)
        if not bins:
            raise ValueError("no horizon bins could be parsed from the payload")
        fetch = DelhiForecastFetch(
            status="COMPUTED",
            reference_point=SAFDARJUNG_REFERENCE,
            latitude=SAFDARJUNG_LAT,
            longitude=SAFDARJUNG_LON,
            acquired_at=requested_utc_now,
            bins=bins,
        )
        _CACHE.put(fetch, requested_utc_now)
        return fetch
    except Exception as exc:  # explicit degraded state, never fake data
        diagnostics = [f"Open-Meteo forecast acquisition failed: {exc}"]
        stale = _CACHE.get_stale() if use_cache else None
        if stale is not None:
            fetch, acquired = stale
            return DelhiForecastFetch(
                status="STALE",
                reference_point=fetch.reference_point,
                latitude=fetch.latitude,
                longitude=fetch.longitude,
                acquired_at=acquired,
                bins=fetch.bins,
                diagnostics=diagnostics + [
                    f"serving cached forecast acquired {acquired.isoformat()}"
                ],
            )
        return DelhiForecastFetch(
            status="UNAVAILABLE",
            reference_point=SAFDARJUNG_REFERENCE,
            latitude=SAFDARJUNG_LAT,
            longitude=SAFDARJUNG_LON,
            acquired_at=None,
            bins=(),
            diagnostics=diagnostics,
        )


# ---------------------------------------------------------------------------
# Ensemble nowcast through the canonical runtime path
# ---------------------------------------------------------------------------


def _nowcast_chain_decisions() -> Dict[str, ReachOutflowDecision]:
    """Explicit outflow decisions mirroring the Phase 8A evidence-scenario
    boundary (same conventions as the Phase 15.5 replay): explicit zero
    outflow, ASSUMED provenance, closed boundary for non-terminal reaches;
    UG-01 carries the mandatory Tier-B effective-scenario declaration;
    OC-02 terminal gets NO decision."""
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


NOWCAST_CHAIN_DECISIONS: Dict[str, ReachOutflowDecision] = _nowcast_chain_decisions()

# Reach ids in the locked chain order.
CHAIN_REACH_IDS: Tuple[str, ...] = ("UG-01", "OC-01", "CD-01", "OC-02")


@dataclass
class MemberNowcast:
    """One ensemble member's runtime nowcast artifacts (MODEL_DERIVED)."""

    member_id: str
    hydraulic_scenario_id: str
    catchment_scenario_id: str
    runoff_coefficient: float
    inflow_status: str
    inflow_steps: Tuple[Tuple[datetime, Optional[float]], ...]
    reach_states: Dict[str, Tuple[Dict[str, Any], ...]]
    classifications: Tuple[Tuple[Dict[str, Any], ...], ...]
    diagnostics: List[str] = field(default_factory=list)


@dataclass
class NowcastResult:
    """Complete deterministic nowcast: members + envelope + provenance."""

    status: str  # COMPUTED | BLOCKED_MISSING_FORCING | UNAVAILABLE
    forecast: DelhiForecastFetch
    generated_at: datetime
    timesteps: Tuple[SimulationTimestep, ...]
    depths_mm: Tuple[Optional[float], ...]
    members: Tuple[MemberNowcast, ...] = ()
    diagnostics: List[str] = field(default_factory=list)
    horizon_note: str = (
        "0-3h ensemble nowcast under documented effective-scenario "
        "assumptions; behavioral inflow/storage envelopes only — stage and "
        "street-level depth are UNKNOWN and are never claimed."
    )


def _forecast_timesteps_and_depths(
    forecast: DelhiForecastFetch,
) -> Tuple[List[SimulationTimestep], List[Optional[float]], List[str]]:
    diagnostics: List[str] = []
    timesteps: List[SimulationTimestep] = []
    depths: List[Optional[float]] = []
    for bin_ in forecast.bins:
        timesteps.append(SimulationTimestep(start=bin_.time_start, end=bin_.time_end))
        depths.append(bin_.depth_mm)
        if bin_.depth_mm is None:
            diagnostics.append(
                f"forecast hour {bin_.time_start.isoformat()} UNKNOWN — "
                "propagated as a blocked timestep (no zero-fill)"
            )
    return timesteps, depths, diagnostics


def _execute_member(
    member,
    timesteps: Sequence[SimulationTimestep],
    depths_mm: Sequence[Optional[float]],
) -> MemberNowcast:
    """Execute ONE member through the canonical runtime path (the same
    chain as the Phase 15.5 replay, with forecast forcing)."""
    scenario = KUSHAK_HYDRAULIC_SCENARIOS[member.hydraulic_scenario_id]
    catchment = CATCHMENT_SCENARIOS[member.catchment_scenario_id]
    profile, profile_meta = covered_effective_profile(scenario)
    slope = backbone_slope_m_per_m()

    initial_state = SimulationState(
        timestamp=timesteps[0].start,
        location_id=f"KUSHAK-NOWCAST-{member.member_id}",
        status=SimulationStateStatus.COMPUTED,
        stage_m=profile_meta["bed_elevation_m"] + INITIAL_DEPTH_M,
        storage_m3=INITIAL_STORAGE_M3,
        provenance=ProvenanceStatus.DERIVED,
    )

    integrated = run_integrated_simulation(
        initial_state=initial_state,
        timesteps=list(timesteps),
        rainfall_depth_mm=list(depths_mm),
        catchment_area_km2=catchment.area_km2,
        runoff_coefficient=member.runoff_coefficient,
        profile=profile,
        manning_n=scenario.effective_manning_n_box,
        slope=slope,
        catchment_area_provenance=ProvenanceStatus.PROVISIONAL,
        runoff_coefficient_provenance=ProvenanceStatus.ASSUMED,
        explicit_outflow_m3_s=0.0,
        explicit_outflow_provenance=ProvenanceStatus.ASSUMED,
        lateral_inflow_m3_s=0.0,
        lateral_inflow_provenance=ProvenanceStatus.ASSUMED,
        manning_n_provenance=ProvenanceStatus.ASSUMED,
        slope_provenance=ProvenanceStatus.DERIVED,
        source_id=f"nowcast:{member.member_id}",
    )

    diagnostics: List[str] = list(integrated.diagnostics)
    if integrated.rainfall_conversion.status != "COMPUTED" or integrated.rainfall_conversion.hydrograph is None:
        # Missing forecast bins block the conversion; the member's inflow
        # is honestly BLOCKED — never substituted.
        return MemberNowcast(
            member_id=member.member_id,
            hydraulic_scenario_id=member.hydraulic_scenario_id,
            catchment_scenario_id=member.catchment_scenario_id,
            runoff_coefficient=member.runoff_coefficient,
            inflow_status=integrated.rainfall_conversion.status,
            inflow_steps=tuple((ts.start, None) for ts in timesteps),
            reach_states={},
            classifications=(),
            diagnostics=diagnostics,
        )

    hydrograph = integrated.rainfall_conversion.hydrograph
    step_specs: List[ChainStepSpec] = []
    for i, ts in enumerate(timesteps):
        discharge = (
            hydrograph.steps[i].discharge_m3_s
            if i < len(hydrograph.steps)
            else None
        )
        step_specs.append(ChainStepSpec(
            timestep=ts,
            head_flow_m3_s=discharge,
            head_flow_provenance=(
                ProvenanceStatus.DERIVED if discharge is not None
                else ProvenanceStatus.UNKNOWN
            ),
            laterals={rid: 0.0 for rid in CHAIN_REACH_IDS},
            lateral_provenances={rid: ProvenanceStatus.ASSUMED for rid in CHAIN_REACH_IDS},
            decisions=NOWCAST_CHAIN_DECISIONS,
        ))
    chain = advance_chain_series(
        tuple(step_specs),
        initial_storage={rid: INITIAL_STORAGE_M3 for rid in CHAIN_REACH_IDS},
        initial_storage_provenance={rid: ProvenanceStatus.ASSUMED for rid in CHAIN_REACH_IDS},
    )

    # Honest classification: no stage is supplied (none may be invented),
    # so geometric states stay UNKNOWN — exactly as in the replay.
    classifications = tuple(
        tuple(
            {
                "reach_id": c.reach_id,
                "classification": c.classification.value,
                "status": c.status,
                "provenance": c.provenance.value,
                "tier": c.tier,
                "diagnostic": c.diagnostic,
            }
            for c in classify_chain_timestep(step, profiles={})
        )
        for step in chain.steps
    )

    reach_states: Dict[str, Tuple[Dict[str, Any], ...]] = {}
    for reach_id in CHAIN_REACH_IDS:
        per_step: List[Dict[str, Any]] = []
        for step in chain.steps:
            r = step.state_for(reach_id)
            per_step.append({
                "time_start": r.state.timestep.start.isoformat(),
                "time_end": r.state.timestep.end.isoformat(),
                "hydraulic_status": r.state.hydraulic_status.value,
                "storage_m3": r.state.storage_m3,
                "stage_m": r.state.stage_m,
                "incoming_flow_m3_s": r.state.incoming_flow_m3_s,
                "actual_outflow_m3_s": r.transfer.actual_outflow_m3_s,
                "transferred_downstream_m3_s": r.transfer.transferred_m3_s,
                "capacity_m3_s": r.transfer.capacity_m3_s,
                "balance_residual_m3_s": r.accounting.balance_residual_m3_s,
            })
        reach_states[reach_id] = tuple(per_step)

    inflow_steps = tuple(
        (ts.start, (
            hydrograph.steps[i].discharge_m3_s
            if i < len(hydrograph.steps) else None
        ))
        for i, ts in enumerate(timesteps)
    )

    return MemberNowcast(
        member_id=member.member_id,
        hydraulic_scenario_id=member.hydraulic_scenario_id,
        catchment_scenario_id=member.catchment_scenario_id,
        runoff_coefficient=member.runoff_coefficient,
        inflow_status="COMPUTED",
        inflow_steps=inflow_steps,
        reach_states=reach_states,
        classifications=classifications,
        diagnostics=diagnostics,
    )


def _envelope(values: Sequence[Optional[float]]) -> Dict[str, Any]:
    """UNKNOWN-aware min/median/max envelope. Members whose value is
    UNKNOWN (None) are counted separately — never zero-filled into the
    envelope."""
    known = [v for v in values if v is not None]
    return {
        "min": min(known) if known else None,
        "median": statistics.median(known) if known else None,
        "max": max(known) if known else None,
        "computed_members": len(known),
        "unknown_members": len(values) - len(known),
    }


def run_nowcast(forecast: DelhiForecastFetch) -> NowcastResult:
    """Execute the deterministic ensemble nowcast for an acquired forecast.

    A forecast with zero horizon bins, or an UNAVAILABLE acquisition,
    yields BLOCKED_MISSING_FORCING — never a synthetic nowcast.
    """
    generated_at = datetime.now(timezone.utc)

    if forecast.status == "UNAVAILABLE" or not forecast.bins:
        return NowcastResult(
            status="BLOCKED_MISSING_FORCING",
            forecast=forecast,
            generated_at=generated_at,
            timesteps=(),
            depths_mm=(),
            diagnostics=list(forecast.diagnostics) + [
                "no executable forecast forcing; ensemble not executed"
            ],
        )

    timesteps, depths, diagnostics = _forecast_timesteps_and_depths(forecast)
    ensemble = build_kushak_ensemble()
    members = tuple(_execute_member(m, timesteps, depths) for m in ensemble)

    return NowcastResult(
        status="COMPUTED" if any(m.inflow_status == "COMPUTED" for m in members) else "BLOCKED_MISSING_FORCING",
        forecast=forecast,
        generated_at=generated_at,
        timesteps=tuple(timesteps),
        depths_mm=tuple(depths),
        members=members,
        diagnostics=diagnostics,
    )
