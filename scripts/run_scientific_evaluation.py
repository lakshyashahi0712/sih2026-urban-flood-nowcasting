"""Reproducible scientific evaluation runner.

Regenerates every machine-readable science artifact from source data:
observation registry, validation metrics + event matrix, calibration
results (GLUE screen + audit), parameter sensitivity, uncertainty
decomposition, and the ML gating + registry.

Usage:
    python scripts/run_scientific_evaluation.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
for _p in (str(_REPO_ROOT), str(_REPO_ROOT / "backend")):
    if _p not in sys.path:
        sys.path.insert(0, _p)


def main() -> None:
    from backend.app.domain.delhi.science.observation_registry import (
        build_observation_registry,
        write_registry,
    )
    from backend.app.domain.delhi.science.validation import write_validation_results
    from backend.app.domain.delhi.science.calibration import write_calibration_results
    from backend.app.domain.delhi.science.identifiability import (
        write_identifiability_results,
    )
    from backend.app.domain.delhi.science.uncertainty import write_uncertainty_results
    from backend.app.domain.delhi.science.ml_pipeline import (
        write_ml_registry,
        write_ml_registry_csvs,
    )

    records = build_observation_registry()
    path = write_registry(records)
    print(f"observation registry: {len(records)} records -> {path}")

    for name, path in write_validation_results().items():
        print(f"validation: {name} -> {path}")

    print(f"calibration: {write_calibration_results()}")
    print(f"identifiability: {write_identifiability_results()}")
    print(f"uncertainty: {write_uncertainty_results()}")
    print(f"ml registry: {write_ml_registry()}")
    for p in write_ml_registry_csvs():
        print(f"ml results: {p}")

    from backend.app.domain.delhi.science.gating import production_mode

    print(f"production mode: {production_mode()}")


if __name__ == "__main__":
    main()
