"""Phase 9: Scenario ensemble contract (deterministic, evidence-constrained).

Defines the allowed ensemble axes and members based strictly on documented
Phase 8A/8B scenario parameters.

CORE SCIENTIFIC RULES:
- Deterministic ensemble construction ONLY.
- Axes restricted to documented ranges/scenarios:
    - hydraulic_scenario: CONSERVATIVE, CENTRAL, DEGRADED_CAPACITY
    - catchment: WORKING_27_66, SENSITIVITY_28_40
    - runoff_coefficient: Documented scenario assumptions ONLY.
- No probabilistic weighting, no Monte Carlo, no fabrication.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from .kushak_evidence_model import KUSHAK_HYDRAULIC_SCENARIOS, CATCHMENT_SCENARIOS
from .models import ProvenanceStatus

# Documented Runoff Coefficient C from Phase 8B documentation/code:
# Based on existing implementations, 0.75 is the standard ASSUMED
# parameter for the Kushak effective-scenario runoff formulation.
# No other C-range is documented as an allowed model input in the
# existing evidence inventory.
SCENARIO_RUNOFF_C = 0.75
SCENARIO_RUNOFF_PROVENANCE = ProvenanceStatus.ASSUMED


@dataclass(frozen=True)
class KushakEnsembleMember:
    """An immutable ensemble member defined by a unique combination of
    documented scenario axes."""
    member_id: str
    hydraulic_scenario_id: str
    catchment_scenario_id: str
    runoff_coefficient: float
    description: str

    def __post_init__(self) -> None:
        if self.hydraulic_scenario_id not in KUSHAK_HYDRAULIC_SCENARIOS:
            raise ValueError(f"Unknown hydraulic scenario: {self.hydraulic_scenario_id}")
        if self.catchment_scenario_id not in CATCHMENT_SCENARIOS:
            raise ValueError(f"Unknown catchment scenario: {self.catchment_scenario_id}")


def build_kushak_ensemble() -> Tuple[KushakEnsembleMember, ...]:
    """Build the deterministic ensemble from documented scenario axes."""
    members = []

    # Generate all combinations of documented scenarios.
    for h_id in KUSHAK_HYDRAULIC_SCENARIOS.keys():
        for c_id in CATCHMENT_SCENARIOS.keys():
            member_id = f"KUSHAK-{h_id}-{c_id}"
            members.append(KushakEnsembleMember(
                member_id=member_id,
                hydraulic_scenario_id=h_id,
                catchment_scenario_id=c_id,
                runoff_coefficient=SCENARIO_RUNOFF_C,
                description=(
                    f"Hydraulic: {h_id}; Catchment: {c_id}; "
                    f"Runoff C: {SCENARIO_RUNOFF_C} ({SCENARIO_RUNOFF_PROVENANCE.value})"
                )
            ))

    return tuple(members)
