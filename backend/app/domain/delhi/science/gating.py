"""Production gating for model enhancements.

Single source of truth for the question "may any non-baseline model
component influence operational products?" Currently: NO — production
mode is PHYSICS_ONLY because no ML model passes the validation gates.

Every operational surface (status, nowcast, safe routing) reads the mode
from here so the UI can never claim an enhancement is active when it is
not.
"""

from __future__ import annotations

from typing import Dict

from .ml_pipeline import production_gate


def production_mode() -> Dict[str, str]:
    gate = production_gate()
    return {
        "production_mode": gate["production_mode"],
        "ml_status": gate["ml_status"],
        "reason": gate["reason"],
    }
