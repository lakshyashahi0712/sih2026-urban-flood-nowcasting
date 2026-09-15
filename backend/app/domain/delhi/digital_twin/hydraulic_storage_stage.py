"""Storage-stage relation contract for Phase 7D-13.

A reusable, explicit storage-stage relationship: an ordered table of
(stage_m, storage_m3) pairs supplied by the caller, supporting lookup in
both directions:

    storage_m3 -> stage_m
    stage_m     -> storage_m3

Piecewise-linear interpolation inside the supplied valid domain —
deterministic, documented below. Outside the domain the lookup is an
explicit BLOCKED result: no extrapolation, ever. UNKNOWN (None) inputs
block, never become zero. Non-finite and physically invalid inputs are
rejected. Provenance is carried for the relationship itself and the
computed result (a computed value is DERIVED, never OBSERVED). No
geometry-to-storage calculation is built here; no stage solving,
normal-depth solving, Manning changes, routing, rainfall-runoff, conduit
hydraulics, structures, overflow, surface flooding, calibration, replay,
ML, or UI.

Interpolation behavior (deterministic):
- The table must have >= 2 pairs with strictly increasing stage values.
- Within the table, lookup is piecewise-linear between the two bracketing
  pairs (linear in both directions).
- Exact pair values return exactly the paired counterpart.
- Outside the table's stage/storage range the result is BLOCKED_INVALID_INPUT
  (no extrapolation beyond the supplied valid domain).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Optional, Tuple

from .hydraulic_calculations import HydraulicCalculationResult
from .models import ProvenanceStatus

# Weakest-link ordering (matches the conservative combination used by the
# 7C/7D-2 modules).
_PROV_WEAKNESS_ORDER = [
    ProvenanceStatus.UNKNOWN, ProvenanceStatus.PROVISIONAL,
    ProvenanceStatus.ASSUMED, ProvenanceStatus.DERIVED,
    ProvenanceStatus.OFFICIAL_MODEL_VALUE,
    ProvenanceStatus.OFFICIAL, ProvenanceStatus.OBSERVED,
]


def _is_finite_number(v) -> bool:
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        return False
    return math.isfinite(v)


def _weakest(provenances) -> ProvenanceStatus:
    return min(provenances, key=lambda p: _PROV_WEAKNESS_ORDER.index(p))


@dataclass
class StorageStagePair:
    """One explicit (stage_m, storage_m3) pair with provenance."""
    stage_m: float
    storage_m3: float
    provenance: ProvenanceStatus = ProvenanceStatus.UNKNOWN

    def __post_init__(self):
        if not _is_finite_number(self.stage_m):
            raise ValueError(
                f"stage_m must be a finite number (got {self.stage_m!r})"
            )
        if not _is_finite_number(self.storage_m3):
            raise ValueError(
                f"storage_m3 must be a finite number (got {self.storage_m3!r})"
            )
        if self.stage_m < 0:
            raise ValueError(
                f"stage_m must be non-negative (got {self.stage_m})"
            )
        if self.storage_m3 < 0:
            raise ValueError(
                f"storage_m3 must be non-negative (got {self.storage_m3})"
            )


@dataclass
class StorageStageRelation:
    """An explicit, ordered storage-stage relationship table.

    Pairs must be supplied by the caller (surveyed geometry, rating
    tables, etc. — the source is the caller's responsibility); they are
    never inferred or fabricated here. Stages must be strictly increasing
    (duplicates and backwards stages rejected); at least 2 pairs
    required. An empty relation represents UNKNOWN: every lookup returns
    an explicit blocked result.
    """
    pairs: List[StorageStagePair]
    provenance: Optional[ProvenanceStatus] = None

    def __post_init__(self):
        if not self.pairs:
            return  # UNKNOWN relation: lookups block explicitly.
        if len(self.pairs) < 2:
            raise ValueError(
                "a storage-stage relation needs at least 2 pairs "
                "(or none, for UNKNOWN)"
            )
        for a, b in zip(self.pairs, self.pairs[1:]):
            if b.stage_m <= a.stage_m:
                raise ValueError(
                    "relation stages must be strictly increasing "
                    "(duplicates/backwards stages rejected)"
                )
        if self.provenance is None:
            self.provenance = _weakest([p.provenance for p in self.pairs])

    @property
    def has_relation(self) -> bool:
        return bool(self.pairs)

    def _blocked(self, direction: str, reason: str) -> HydraulicCalculationResult:
        return HydraulicCalculationResult(
            status="BLOCKED_INVALID_INPUT",
            value=None,
            diagnostic=f"{direction} lookup blocked: {reason}",
        )

    def _interp(self, xs: List[float], ys: List[float], x: float) -> float:
        # Piecewise-linear between the bracketing pairs (deterministic).
        for i in range(len(xs) - 1):
            if x <= xs[i + 1] or i == len(xs) - 2:
                x0, y0, x1, y1 = xs[i], ys[i], xs[i + 1], ys[i + 1]
                if x1 == x0:
                    return y0
                return y0 + (y1 - y0) * (x - x0) / (x1 - x0)
        return ys[-1]

    def stage_to_storage(self, stage_m: Optional[float]) -> HydraulicCalculationResult:
        """stage_m -> storage_m3 (piecewise-linear inside the domain)."""
        if not self.has_relation:
            return HydraulicCalculationResult(
                status="BLOCKED_MISSING_GEOMETRY",
                value=None,
                diagnostic="Storage-stage relation is UNKNOWN (no pairs)",
            )
        if stage_m is None:
            return self._blocked(
                "stage->storage", "stage is UNKNOWN (None); no value substituted")
        if not _is_finite_number(stage_m):
            return self._blocked(
                "stage->storage", f"stage must be a finite number (got {stage_m!r})")
        if stage_m < 0:
            return self._blocked(
                "stage->storage", f"stage must be non-negative (got {stage_m})")
        stages = [p.stage_m for p in self.pairs]
        storages = [p.storage_m3 for p in self.pairs]
        if stage_m < stages[0] or stage_m > stages[-1]:
            return self._blocked(
                "stage->storage",
                f"stage {stage_m} is outside the relation's valid domain "
                f"[{stages[0]}, {stages[-1]}]; extrapolation is never performed",
            )
        return HydraulicCalculationResult(
            status="COMPUTED",
            value=self._interp(stages, storages, stage_m),
            diagnostic=(
                f"storage from piecewise-linear storage-stage relation "
                f"(stage {stage_m} m); relation provenance: {self.provenance.value}"
            ),
        )

    def storage_to_stage(self, storage_m3: Optional[float]) -> HydraulicCalculationResult:
        """storage_m3 -> stage_m (piecewise-linear inside the domain)."""
        if not self.has_relation:
            return HydraulicCalculationResult(
                status="BLOCKED_MISSING_GEOMETRY",
                value=None,
                diagnostic="Storage-stage relation is UNKNOWN (no pairs)",
            )
        if storage_m3 is None:
            return self._blocked(
                "storage->stage", "storage is UNKNOWN (None); no value substituted")
        if not _is_finite_number(storage_m3):
            return self._blocked(
                "storage->stage", f"storage must be a finite number (got {storage_m3!r})")
        if storage_m3 < 0:
            return self._blocked(
                "storage->stage", f"storage must be non-negative (got {storage_m3})")
        # Interpolate over (storage, stage) — the inverse direction. The
        # storage axis is not required to be monotonic, so its valid
        # domain is [min, max] of the supplied values (the stage axis is
        # strictly monotonic, so this matches its [first, last] domain).
        storages = [p.storage_m3 for p in self.pairs]
        stages = [p.stage_m for p in self.pairs]
        if storage_m3 < min(storages) or storage_m3 > max(storages):
            return self._blocked(
                "storage->stage",
                f"storage {storage_m3} is outside the relation's valid domain "
                f"[{min(storages)}, {max(storages)}]; extrapolation is never performed",
            )
        # The supplied table is a stage-ordered function; its storage
        # sequence is usable as an interpolation axis only if strictly
        # increasing. If it is not monotonic, the inverse is ambiguous:
        # block explicitly rather than guess.
        for s0, s1 in zip(storages, storages[1:]):
            if s1 <= s0:
                return self._blocked(
                    "storage->stage",
                    "storage sequence is not strictly increasing; the "
                    "inverse lookup is ambiguous for this relation",
                )
        return HydraulicCalculationResult(
            status="COMPUTED",
            value=self._interp(storages, stages, storage_m3),
            diagnostic=(
                f"stage from piecewise-linear storage-stage relation "
                f"(storage {storage_m3} m3); relation provenance: {self.provenance.value}"
            ),
        )
