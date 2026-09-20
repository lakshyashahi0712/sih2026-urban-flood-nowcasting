"""Historical replay event manifest (declarative event registry).

This is the 28E reusability contract: registering a NEW historical event
requires ONLY data entries here (plus, when available, a forcing profile
in ``kushak_historical_rainfall_catalog``) — never hydraulic-code
changes. Every declaration is machine-validated at import time so a
malformed event entry fails loudly instead of silently degrading.

A declaration states, per event:
- identity and canonical validation resolution
- the documented event window (UTC, cross-checked against the master
  catalogue CSV by the replay harness)
- forcing availability / resolution / source (availability is asserted
  against the actual runtime forcing catalog — a declaration that claims
  forcing which does not exist, or hides forcing which does, is an error)
- spatial attribution and observation status (from the Phase 14A
  evidence lineage)
- executable / replay status derived from the above

Replay status vocabulary (28B surface + 28A classes):
- EXECUTABLE             full documented forcing executable at native resolution
- PARTIALLY_EXECUTABLE   only a documented defensible portion is executable;
                         the remainder is explicitly UNKNOWN (never interpolated)
- NON_EXECUTABLE_MISSING_FORCING   no documented executable forcing
- NON_EXECUTABLE_CONTROL           documented non-flood control event
                                   (absent forcing never simulated)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

from .kushak_historical_rainfall_catalog import get_historical_rainfall_catalog

# ---------------------------------------------------------------------------
# Vocabularies (closed sets; validation fails on anything else)
# ---------------------------------------------------------------------------

EXECUTABLE_STATUSES = (
    "EXECUTABLE",
    "PARTIALLY_EXECUTABLE",
    "NON_EXECUTABLE_MISSING_FORCING",
    "NON_EXECUTABLE_CONTROL",
)

FORCING_AVAILABILITIES = ("FULL", "PARTIAL", "NONE")

FORCING_RESOLUTIONS = (
    "HOURLY",
    "SUBDAILY_3H",
    "DAILY",
    "MIXED_HOURLY_AND_3H",
    "NONE",
)

SPATIAL_STATUSES = (
    "DOCUMENTED_LOCATIONS",   # observations carry usable location evidence
    "DATE_ONLY",              # observations are date-anchored only
    "NONE",
)

OBSERVATION_STATUSES = (
    "FLOOD_YES_HIGH_CONFIDENCE",
    "FLOOD_YES_MULTI_DAY",
    "CONTROL_NON_FLOOD",
    "CONDITIONAL_LOW_CONFIDENCE",
    "PRE_MONSOON_STORM_POINTS",
)


@dataclass(frozen=True)
class ReplayEventDeclaration:
    """One event's complete replay declaration (28E required fields)."""

    catalog_event_id: str
    canonical_event_id: Optional[str]
    event_window_utc: str
    forcing_source: Optional[str]
    forcing_resolution: str
    forcing_availability: str
    spatial_attribution_status: str
    observation_status: str
    executable_status: str
    # What the replay may claim for this event (28D discipline).
    replay_claim: str
    evidence_notes: str

    def validate(self) -> None:
        """Machine-validate this declaration (28E automated validation)."""
        errors = []
        if not self.catalog_event_id:
            errors.append("catalog_event_id is required")
        for field_name in (
            "event_window_utc", "forcing_resolution", "forcing_availability",
            "spatial_attribution_status", "observation_status",
            "executable_status", "replay_claim", "evidence_notes",
        ):
            if not getattr(self, field_name):
                errors.append(f"{field_name} must be declared")
        if self.forcing_resolution not in FORCING_RESOLUTIONS:
            errors.append(f"unknown forcing_resolution {self.forcing_resolution!r}")
        if self.forcing_availability not in FORCING_AVAILABILITIES:
            errors.append(f"unknown forcing_availability {self.forcing_availability!r}")
        if self.spatial_attribution_status not in SPATIAL_STATUSES:
            errors.append(
                f"unknown spatial_attribution_status {self.spatial_attribution_status!r}"
            )
        if self.observation_status not in OBSERVATION_STATUSES:
            errors.append(f"unknown observation_status {self.observation_status!r}")
        if self.executable_status not in EXECUTABLE_STATUSES:
            errors.append(f"unknown executable_status {self.executable_status!r}")

        # Cross-field consistency: forcing claims must match executability.
        has_forcing = self.forcing_availability in ("FULL", "PARTIAL")
        if has_forcing and not (
            self.executable_status in ("EXECUTABLE", "PARTIALLY_EXECUTABLE")
            and self.forcing_source
            and self.canonical_event_id
        ):
            errors.append(
                "declared forcing requires EXECUTABLE/PARTIALLY_EXECUTABLE "
                "status, a forcing_source, and a canonical event id"
            )
        if not has_forcing and self.executable_status in (
            "EXECUTABLE", "PARTIALLY_EXECUTABLE"
        ):
            errors.append(
                "executable status declared without forcing availability"
            )
        if self.executable_status == "PARTIALLY_EXECUTABLE" and (
            self.forcing_availability != "PARTIAL"
        ):
            errors.append(
                "PARTIALLY_EXECUTABLE requires forcing_availability=PARTIAL"
            )
        if self.executable_status == "EXECUTABLE" and (
            self.forcing_availability != "FULL"
        ):
            errors.append(
                "EXECUTABLE requires forcing_availability=FULL"
            )
        if errors:
            raise ValueError(
                f"invalid replay declaration for {self.catalog_event_id}: "
                + "; ".join(errors)
            )


# ---------------------------------------------------------------------------
# Declarations (data-only event registry; hydraulic code untouched)
# ---------------------------------------------------------------------------

REPLAY_EVENT_DECLARATIONS: Dict[str, ReplayEventDeclaration] = {
    "EVT-2024-06-27": ReplayEventDeclaration(
        catalog_event_id="EVT-2024-06-27",
        canonical_event_id="EV-01",
        event_window_utc="2024-06-27T18:30:00Z to 2024-06-28T03:00:00Z",
        forcing_source="FC-EV01-SAFDARJUNG",
        forcing_resolution="HOURLY",
        forcing_availability="FULL",
        spatial_attribution_status="DOCUMENTED_LOCATIONS",
        observation_status="FLOOD_YES_HIGH_CONFIDENCE",
        executable_status="EXECUTABLE",
        replay_claim=(
            "Full runtime replay of the documented hourly forcing; "
            "qualitative/directional consistency only - never accuracy."
        ),
        evidence_notes=(
            "Primary benchmark event EV-01. Hourly AWS telemetry available "
            "for the direct peak hour; subsequent hours preserve UNKNOWN "
            "provenance."
        ),
    ),
    "EVT-2023-07-08": ReplayEventDeclaration(
        catalog_event_id="EVT-2023-07-08",
        canonical_event_id="EV-02",
        event_window_utc="2023-07-08T03:00:00Z to 2023-07-10T03:00:00Z",
        forcing_source="FC-EV02-SAFDARJUNG",
        forcing_resolution="MIXED_HOURLY_AND_3H",
        forcing_availability="FULL",
        spatial_attribution_status="DOCUMENTED_LOCATIONS",
        observation_status="FLOOD_YES_MULTI_DAY",
        executable_status="EXECUTABLE",
        replay_claim=(
            "Full runtime replay of the documented forcing with 3-hour "
            "increments preserved at native resolution; qualitative "
            "consistency only."
        ),
        evidence_notes=(
            "Secondary benchmark event EV-02. CWC stage event-day "
            "separation verified (record 208.66 m on 13 Jul 2023 is NOT "
            "an event day)."
        ),
    ),
    "EVT-2021-09-11": ReplayEventDeclaration(
        catalog_event_id="EVT-2021-09-11",
        canonical_event_id="EV-03",
        event_window_utc="2021-09-11T00:00:00Z to 2021-09-11T09:00:00Z",
        forcing_source="FC-EV03-SAFDARJUNG",
        forcing_resolution="SUBDAILY_3H",
        forcing_availability="PARTIAL",
        spatial_attribution_status="DOCUMENTED_LOCATIONS",
        observation_status="FLOOD_YES_HIGH_CONFIDENCE",
        executable_status="PARTIALLY_EXECUTABLE",
        replay_claim=(
            "PARTIAL replay: only the documented verified 3-hour block "
            "(80.0 mm, 05:30-08:30 IST) is executed at its native "
            "interval. The remainder of the 117.9 mm daily total lacks "
            "documented intra-day timing and stays UNKNOWN - never "
            "interpolated, disaggregated, or zero-filled."
        ),
        evidence_notes=(
            "Convective burst event EV-03 (Safdarjung 117.9 mm/24h with "
            "verified 80 mm 05:30-08:30 IST 3-hour block). The defensible "
            "portion is executed at native 3-hour resolution; the "
            "remainder of the event window is explicitly UNKNOWN."
        ),
    ),
    "EVT-2026-01-23": ReplayEventDeclaration(
        catalog_event_id="EVT-2026-01-23",
        canonical_event_id=None,
        event_window_utc="2026-01-22T18:30:00Z to 2026-01-23T18:30:00Z",
        forcing_source=None,
        forcing_resolution="NONE",
        forcing_availability="NONE",
        spatial_attribution_status="DATE_ONLY",
        observation_status="CONTROL_NON_FLOOD",
        executable_status="NON_EXECUTABLE_CONTROL",
        replay_claim=(
            "Documented non-flood negative control. No forcing exists; "
            "absent forcing is never converted into a runtime simulation."
        ),
        evidence_notes=(
            "CONTROL_ONLY event (documented non-flood negative control). "
            "Absent forcing is never converted into a runtime simulation."
        ),
    ),
    "EVT-2021-07-19": ReplayEventDeclaration(
        catalog_event_id="EVT-2021-07-19",
        canonical_event_id=None,
        event_window_utc="2021-07-19T00:00:00Z to 2021-07-19T23:59:00Z",
        forcing_source=None,
        forcing_resolution="NONE",
        forcing_availability="NONE",
        spatial_attribution_status="DATE_ONLY",
        observation_status="CONDITIONAL_LOW_CONFIDENCE",
        executable_status="NON_EXECUTABLE_MISSING_FORCING",
        replay_claim=(
            "No documented executable forcing; tests the UNKNOWN forcing "
            "boundary (BLOCKED_MISSING_FORCING). Zero rainfall is never "
            "created."
        ),
        evidence_notes=(
            "Conditionally qualified event. No documented executable "
            "forcing; tests the UNKNOWN forcing boundary "
            "(BLOCKED_MISSING_FORCING)."
        ),
    ),
    "EVT-2023-05-27": ReplayEventDeclaration(
        catalog_event_id="EVT-2023-05-27",
        canonical_event_id=None,
        event_window_utc="2023-05-27T00:00:00Z to 2023-05-27T23:59:00Z",
        forcing_source=None,
        forcing_resolution="NONE",
        forcing_availability="NONE",
        spatial_attribution_status="DATE_ONLY",
        observation_status="PRE_MONSOON_STORM_POINTS",
        executable_status="NON_EXECUTABLE_MISSING_FORCING",
        replay_claim=(
            "No documented executable forcing; tests the UNKNOWN boundary "
            "propagation (BLOCKED_MISSING_FORCING)."
        ),
        evidence_notes=(
            "Pre-monsoon storm event. No documented executable forcing; "
            "tests the UNKNOWN boundary propagation "
            "(BLOCKED_MISSING_FORCING)."
        ),
    ),
}


def validate_manifest() -> None:
    """Validate every declaration AND reconcile each against the actual
    runtime forcing catalog (a declaration that disagrees with reality is
    an error, not a silent degrade)."""
    catalog = get_historical_rainfall_catalog()
    for event_id, declaration in REPLAY_EVENT_DECLARATIONS.items():
        declaration.validate()
        profile = (
            catalog.get(declaration.canonical_event_id)
            if declaration.canonical_event_id
            else None
        )
        if declaration.executable_status in (
            "EXECUTABLE", "PARTIALLY_EXECUTABLE"
        ):
            if profile is None:
                raise ValueError(
                    f"{event_id} declares executable forcing but the "
                    f"runtime catalog has no profile for "
                    f"{declaration.canonical_event_id}"
                )
            if profile.forcing_id != declaration.forcing_source:
                raise ValueError(
                    f"{event_id} forcing_source "
                    f"{declaration.forcing_source!r} disagrees with the "
                    f"runtime catalog profile {profile.forcing_id!r}"
                )
        else:
            if profile is not None:
                raise ValueError(
                    f"{event_id} declares no executable forcing but the "
                    f"runtime catalog provides {profile.forcing_id!r}"
                )


validate_manifest()


def get_declaration(event_id: str) -> ReplayEventDeclaration:
    """Declaration lookup; unknown catalog events are a caller error."""
    declaration = REPLAY_EVENT_DECLARATIONS.get(event_id)
    if declaration is None:
        raise KeyError(
            f"no replay declaration for {event_id}; every catalogued event "
            "must be declared in kushak_replay_manifest"
        )
    return declaration


def replay_status_label(event_id: str) -> str:
    """28B UI-facing status vocabulary."""
    status = get_declaration(event_id).executable_status
    return {
        "EXECUTABLE": "EXECUTABLE",
        "PARTIALLY_EXECUTABLE": "PARTIAL",
        "NON_EXECUTABLE_MISSING_FORCING": "UNKNOWN",
        "NON_EXECUTABLE_CONTROL": "CONTROL",
    }[status]
