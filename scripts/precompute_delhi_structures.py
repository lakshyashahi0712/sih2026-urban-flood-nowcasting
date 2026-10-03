"""Write the Delhi static structures to disk so boot does not rebuild them.

Run this in the deploy build phase (or locally) — the three structures under
``backend/app/domain/delhi/structure_cache.py`` are pure functions of the
committed DEM and roads extract, so the expensive part of a cold Delhi boot
can be paid here instead of in front of the first visitor.

    python scripts/precompute_delhi_structures.py

Prints per-structure timings and the resulting artifact sizes. Re-running is
cheap and idempotent: a matching key means the artifact is already current.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from backend.app.domain.delhi import structure_cache  # noqa: E402
from backend.app.domain.delhi.live_state import _road_match_index  # noqa: E402
from backend.app.domain.delhi.scenarios.depth_v1 import inlet_cell_indices  # noqa: E402
from backend.app.domain.delhi.surface import get_surface_structure  # noqa: E402

# Order follows the dependency graph so each structure is built once. The road
# graph is not listed: it is not an artifact (see structure_cache) and the match
# index builds it internally only when it has to rebuild.
BUILDERS = (
    ("surface_structure", get_surface_structure),
    ("road_match_index", _road_match_index),
    ("inlet_cells", inlet_cell_indices),
)


def main() -> int:
    # The runtime never writes; this script is the one place that does.
    structure_cache._WRITES = True
    key = structure_cache.key()
    print(f"cache dir : {structure_cache.CACHE_DIR}")
    print(f"key       : {key[:16]}...")

    total = 0.0
    for name, builder in BUILDERS:
        t0 = time.perf_counter()
        builder()
        elapsed = time.perf_counter() - t0
        total += elapsed
        outcome = structure_cache.status().get(name, "?")
        path = structure_cache.CACHE_DIR / f"{name}.pkl"
        size = path.stat().st_size / 1e6 if path.exists() else 0.0
        print(f"{name:<18} {outcome:<7} {elapsed:6.2f}s  {size:6.1f} MB")

    print(f"{'TOTAL':<18} {'':<7} {total:6.2f}s")
    if not structure_cache.CACHE_DIR.exists():
        print("WARNING: nothing was written - check DELHI_STRUCTURE_CACHE_WRITE")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
