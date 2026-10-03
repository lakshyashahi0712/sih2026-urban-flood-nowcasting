"""Disk cache for the deterministic Delhi structures that are worth shipping.

The Delhi boot warm rebuilds the D8 surface structure, the road-to-cell match
index and the curb-inlet index from the DEM and the roads extract on every
process start. All three are pure functions of committed inputs, so the result
— not the work — can be shipped: the Render build phase writes the pickles once
(`scripts/precompute_delhi_structures.py`) and boot loads them instead.

The road graph is deliberately NOT an artifact. Measured locally, its pickle
loads in 1.35-3.2 s against a 1.5-3.5 s rebuild — the artifact buys nothing and
costs 12.5 MB — so it stays a plain in-process build. `get_road_graph()` is only
ever called from inside the match index, so a loaded match index keeps the graph
off the boot path anyway.

Staleness is decided by a key over everything that can change an output:

- the bytes of every ``.py`` under ``backend/app/domain/delhi`` (this covers
  the builders themselves, the corridor and reach modules they call, and the
  documented ASSUMED constants they read),
- the data files each artifact declares (the DEM, the roads extract),
- the interpreter and the versions of the libraries whose objects end up
  inside the pickle,
- ``FORMAT_VERSION`` for when this scheme itself changes.

The code digest is deliberately over-inclusive: an unrelated edit inside the
Delhi tree costs one rebuild and can never serve a stale structure.
"""
from __future__ import annotations

import functools
import hashlib
import os
import pickle
import sys
from pathlib import Path
from typing import Callable, Optional

FORMAT_VERSION = 1

_DOMAIN_ROOT = Path(__file__).resolve().parent
CACHE_DIR = Path(
    os.environ.get("DELHI_STRUCTURE_CACHE_DIR")
    or _DOMAIN_ROOT.parents[2] / ".artifacts" / "delhi_structures"
)

# Objects in these pickles come from outside the standard library, so an
# upgrade must invalidate rather than risk loading an incompatible graph.
_VERSIONED_PACKAGES = ("numpy", "shapely", "scipy", "rasterio")

_ENABLED = os.environ.get("DELHI_STRUCTURE_CACHE", "1").strip().lower() != "0"
# Writing is OFF by default and belongs to the build phase
# (`scripts/precompute_delhi_structures.py`). A booting or tested process only
# ever reads: it must not spend a cold boot serializing 25 MB it will throw
# away, and the test suite must not dirty the tree.
_WRITES = os.environ.get("DELHI_STRUCTURE_CACHE_WRITE", "0").strip().lower() != "0"

_process_key: Optional[str] = None
_status: dict[str, str] = {}


def _file_digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _package_versions() -> str:
    from importlib.metadata import PackageNotFoundError, version

    parts = []
    for name in _VERSIONED_PACKAGES:
        try:
            parts.append(f"{name}={version(name)}")
        except PackageNotFoundError:
            parts.append(f"{name}=absent")
    return ",".join(parts)


def _data_files() -> tuple[Path, ...]:
    """The committed inputs the cached structures are built from.

    Imported inside the call, not at module scope: ``surface`` imports this
    module, so a module-level import of it here would be a cycle.
    """
    from backend.app.domain.delhi.routing.network import ROADS_PATH
    from backend.app.domain.delhi.surface import DEM_PATH

    return (DEM_PATH, ROADS_PATH)


def cache_key() -> str:
    """Digest of every input the Delhi structures are a function of."""
    h = hashlib.sha256()
    h.update(f"format={FORMAT_VERSION}\n".encode())
    h.update(f"python={sys.version.split()[0]}\n".encode())
    h.update(f"{_package_versions()}\n".encode())
    for src in sorted(_DOMAIN_ROOT.rglob("*.py")):
        h.update(f"{src.relative_to(_DOMAIN_ROOT)}\0".encode())
        h.update(_file_digest(src).encode())
    for data in sorted(_data_files()):
        h.update(f"{data}\0".encode())
        h.update(_file_digest(data).encode())
    return h.hexdigest()


def _artifact_path(name: str) -> Path:
    return CACHE_DIR / f"{name}.pkl"


def load(name: str, key: str) -> Optional[object]:
    path = _artifact_path(name)
    if not (_ENABLED and path.exists()):
        return None
    stamp = path.with_suffix(".key")
    if not stamp.exists() or stamp.read_text(encoding="utf-8").strip() != key:
        return None
    try:
        with path.open("rb") as fh:
            return pickle.load(fh)
    except Exception:  # noqa: BLE001 - a broken artifact must never boot-block
        return None


def store(name: str, key: str, obj: object) -> None:
    if not (_ENABLED and _WRITES):
        return
    path = _artifact_path(name)
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".pkl.tmp")
        with tmp.open("wb") as fh:
            pickle.dump(obj, fh, protocol=pickle.HIGHEST_PROTOCOL)
        os.replace(tmp, path)
        _artifact_path(name).with_suffix(".key").write_text(key, encoding="utf-8")
    except OSError:
        # Read-only or out-of-space disk: building in-process is still correct.
        pass


def key() -> str:
    """Process-wide memo of :func:`cache_key` (the digests do not change)."""
    global _process_key
    if _process_key is None:
        _process_key = cache_key()
    return _process_key


def disk_artifact(name: str) -> Callable:
    """Put a durable artifact under a ``single_flight_cached`` builder.

    Apply it *inside* the single-flight decorator so the lock and the
    ``lru_cache`` introspection surface stay outermost::

        @single_flight_cached
        @disk_artifact("surface_structure")
        def get_surface_structure(): ...
    """

    def deco(builder: Callable[[], object]) -> Callable[[], object]:
        @functools.wraps(builder)
        def wrapper():
            stamp = key()
            cached = load(name, stamp)
            if cached is not None:
                _status[name] = "loaded"
                return cached
            built = builder()
            store(name, stamp, built)
            _status[name] = "built"
            return built

        return wrapper

    return deco


def status() -> dict[str, str]:
    """Per-artifact outcome for the current process: 'loaded' or 'built'."""
    return dict(_status)
