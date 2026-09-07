"""NWP vs Mesonet observation comparison and bias metrics.

Pure computation module — no I/O. Matches observed and NWP records
by timestamp, computes per-interval error, and aggregates bias metrics.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel, Field

try:
    from backend.app.domain.rainfall.models import RainfallSeries, RainfallRecord
except ImportError:
    from app.domain.rainfall.models import RainfallSeries, RainfallRecord


class NWPComparisonResult(BaseModel):
    """Per-interval comparison between observed and NWP rainfall."""
    timestamp: datetime = Field(..., description="Start of interval (UTC)")
    observed_mm: float = Field(..., ge=0.0, description="Observed rainfall [mm]")
    nwp_mm: float = Field(..., ge=0.0, description="NWP forecast rainfall [mm]")
    error_mm: float = Field(..., description="observed - nwp [mm] (positive = NWP underestimates)")
    relative_error: Optional[float] = Field(
        None,
        description="error / nwp (None if nwp == 0)"
    )


class NWPBiasMetrics(BaseModel):
    """Aggregated bias metrics for NWP vs observation comparison."""
    matched_intervals: int = Field(..., ge=0, description="Number of matched timestamp intervals")
    mean_error_mm: float = Field(0.0, description="Mean(observed - nwp) [mm]; positive = NWP underestimates")
    mean_absolute_error_mm: float = Field(0.0, description="Mean absolute error [mm]")
    max_error_mm: float = Field(0.0, description="Maximum absolute error [mm]")
    correction_applied: bool = Field(False, description="Whether bounded correction was applied")
    correction_bound_mm: float = Field(20.0, description="Max correction bound [mm/hr]")
    comparisons: List[NWPComparisonResult] = Field(default_factory=list, description="Per-interval comparisons")


class NWPComparisonService:
    """Service for comparing NWP forecasts against Mesonet observations.

    Matches records by timestamp and computes bias metrics.
    Pure computation — no network I/O.
    """

    @staticmethod
    def compare(
        observed: RainfallSeries,
        nwp: RainfallSeries,
        correction_bound_mm: float = 20.0,
        correction_applied: bool = False,
    ) -> NWPBiasMetrics:
        """Compare observed vs NWP rainfall and compute bias metrics.

        Matches records by timestamp. Only intervals where both observed
        and NWP data exist contribute to the metrics.

        Args:
            observed: Mesonet observation series.
            nwp: NWP forecast series.
            correction_bound_mm: The correction bound used (for reporting).
            correction_applied: Whether correction was actually applied.

        Returns:
            NWPBiasMetrics with per-interval comparisons and aggregate stats.
        """
        # Build lookup: timestamp -> observed rainfall_mm
        obs_lookup: dict[datetime, float] = {}
        for rec in observed.records:
            obs_lookup[rec.timestamp] = rec.rainfall_mm

        comparisons: list[NWPComparisonResult] = []
        for nwp_rec in nwp.records:
            if nwp_rec.timestamp in obs_lookup:
                obs_mm = obs_lookup[nwp_rec.timestamp]
                nwp_mm = nwp_rec.rainfall_mm
                error = obs_mm - nwp_mm
                rel_error = (error / nwp_mm) if nwp_mm > 0 else None

                comparisons.append(NWPComparisonResult(
                    timestamp=nwp_rec.timestamp,
                    observed_mm=obs_mm,
                    nwp_mm=nwp_mm,
                    error_mm=round(error, 6),
                    relative_error=round(rel_error, 6) if rel_error is not None else None,
                ))

        matched = len(comparisons)
        if matched == 0:
            return NWPBiasMetrics(
                matched_intervals=0,
                mean_error_mm=0.0,
                mean_absolute_error_mm=0.0,
                max_error_mm=0.0,
                correction_applied=correction_applied,
                correction_bound_mm=correction_bound_mm,
                comparisons=[],
            )

        errors = [c.error_mm for c in comparisons]
        abs_errors = [abs(e) for e in errors]

        return NWPBiasMetrics(
            matched_intervals=matched,
            mean_error_mm=round(sum(errors) / matched, 6),
            mean_absolute_error_mm=round(sum(abs_errors) / matched, 6),
            max_error_mm=round(max(abs_errors), 6),
            correction_applied=correction_applied,
            correction_bound_mm=correction_bound_mm,
            comparisons=comparisons,
        )


__all__ = [
    "NWPComparisonResult",
    "NWPBiasMetrics",
    "NWPComparisonService",
]
