"""Composite Rainfall Provider with strict provenance tracking.

Coordinates acquisition across:
1. Primary: IMD Doppler Weather Radar (quantitative observations)
2. Fallback: Open-Meteo NWP Forecast (numerical weather prediction)

Guarantees:
- Never labels NWP forecast as radar observation.
- Automatically triggers NWP fallback when radar is non-quantitative (e.g. visual GIF),
  stale, or unreachable.
- Transparently exposes fallback rationale and diagnostic probe details.
"""
from __future__ import annotations

from datetime import datetime, timezone
import logging
from typing import Any, Dict, Optional, Tuple
from pydantic import BaseModel, ConfigDict, Field

try:
    from backend.app.domain.rainfall.models import RainfallSeries, RainfallStatus, RainfallRecord
    from backend.app.domain.rainfall.radar_models import (
        RainfallProvenance,
        SpatialRainfallGrid,
        MUMBAI_PILOT_BOUNDS_32643,
    )
    from backend.app.infrastructure.rainfall.imd_radar import IMDRadarAdapter, IMDRadarProbeResult
    from backend.app.infrastructure.rainfall.open_meteo import OpenMeteoAdapter
except ImportError:
    from app.domain.rainfall.models import RainfallSeries, RainfallStatus, RainfallRecord
    from app.domain.rainfall.radar_models import (
        RainfallProvenance,
        SpatialRainfallGrid,
        MUMBAI_PILOT_BOUNDS_32643,
    )
    from app.infrastructure.rainfall.imd_radar import IMDRadarAdapter, IMDRadarProbeResult
    from app.infrastructure.rainfall.open_meteo import OpenMeteoAdapter

logger = logging.getLogger(__name__)


class CompositeRainfallResult(BaseModel):
    """Result of composite rainfall acquisition with provenance and diagnostic metadata."""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    provenance: RainfallProvenance = Field(..., description="Authoritative provenance (RADAR, NWP_FALLBACK, UNAVAILABLE)")
    status: RainfallStatus = Field(..., description="Data status (LIVE, STALE, UNAVAILABLE)")
    is_fallback: bool = Field(..., description="True if primary radar could not be used")
    fallback_reason: Optional[str] = Field(None, description="Detailed explanation why fallback was triggered")
    source_name: str = Field(..., description="Provider name (e.g. 'IMD Doppler Radar (Veravali)' or 'Open-Meteo NWP')")
    acquired_at: datetime = Field(..., description="Acquisition timestamp (UTC)")
    series: Any = Field(None, description="Time series of rainfall records")
    spatial_grid: Optional[SpatialRainfallGrid] = Field(None, description="Spatial rainfall grid if quantitative radar is available")
    radar_diagnostics: Optional[Dict[str, Any]] = Field(None, description="Probe diagnostics from IMD radar service")


class CompositeRainfallProvider:
    """Orchestrator for multi-source rainfall data with radar priority and NWP fallback."""

    def __init__(
        self,
        radar_adapter: Optional[IMDRadarAdapter] = None,
        nwp_adapter: Optional[OpenMeteoAdapter] = None,
    ) -> None:
        self.radar_adapter = radar_adapter or IMDRadarAdapter()
        self.nwp_adapter = nwp_adapter or OpenMeteoAdapter()

    async def fetch_rainfall(
        self,
        target_bounds: Tuple[float, float, float, float] = MUMBAI_PILOT_BOUNDS_32643,
        use_cache: bool = True,
    ) -> CompositeRainfallResult:
        """Fetch precipitation data following the authoritative radar -> NWP fallback hierarchy.

        1. Probes IMD Doppler Radar.
        2. If quantitative radar data is present and fresh -> returns RADAR provenance.
        3. If radar provides only non-quantitative GIF, is stale, or fails -> triggers NWP fallback with
           strict NWP_FALLBACK provenance tag.
        4. If NWP also fails -> returns UNAVAILABLE.
        """
        now_utc = datetime.now(timezone.utc)

        # Step 1: Probe IMD Radar
        radar_grid: Optional[SpatialRainfallGrid] = None
        probe_result: Optional[IMDRadarProbeResult] = None
        try:
            radar_grid, probe_result = await self.radar_adapter.fetch_radar_grid(target_bounds=target_bounds)
        except Exception as ex:
            logger.warning(f"Error checking IMD radar: {ex}")
            fallback_reason = f"IMD radar probe exception: {type(ex).__name__} ({str(ex)})"
            probe_result = None
        else:
            fallback_reason = probe_result.diagnostic_message if probe_result else "Radar data unavailable"

        # If quantitative radar data is returned:
        if radar_grid is not None:
            return CompositeRainfallResult(
                provenance=RainfallProvenance.RADAR,
                status=RainfallStatus.LIVE,
                is_fallback=False,
                fallback_reason=None,
                source_name="IMD Doppler Weather Radar (Veravali)",
                acquired_at=now_utc,
                spatial_grid=radar_grid,
                radar_diagnostics=probe_result.to_dict() if probe_result else None,
            )

        # Step 2: Fallback to Open-Meteo NWP
        logger.info(f"Triggering NWP fallback: {fallback_reason}")
        try:
            nwp_series = await self.nwp_adapter.fetch(use_cache=use_cache)
            # Guarantee provenance is explicitly stamped as NWP_FALLBACK on every record and series
            updated_records = []
            for rec in nwp_series.records:
                updated_records.append(
                    rec.model_copy(update={"provenance": RainfallProvenance.NWP_FALLBACK})
                )
            nwp_series = nwp_series.model_copy(
                update={"records": updated_records, "provenance": RainfallProvenance.NWP_FALLBACK}
            )

            # Determine status
            series_status = nwp_series.records[0].status if nwp_series.records else RainfallStatus.LIVE

            return CompositeRainfallResult(
                provenance=RainfallProvenance.NWP_FALLBACK,
                status=series_status,
                is_fallback=True,
                fallback_reason=fallback_reason,
                source_name=f"Open-Meteo NWP Forecast (Fallback due to: {fallback_reason})",
                acquired_at=now_utc,
                series=nwp_series,
                radar_diagnostics=probe_result.to_dict() if probe_result else None,
            )

        except Exception as nwp_ex:
            logger.error(f"Both IMD radar and NWP fallback failed: {nwp_ex}")
            return CompositeRainfallResult(
                provenance=RainfallProvenance.UNAVAILABLE,
                status=RainfallStatus.UNAVAILABLE,
                is_fallback=True,
                fallback_reason=f"Radar unavailable ({fallback_reason}); NWP fallback failed ({nwp_ex})",
                source_name="None",
                acquired_at=now_utc,
                radar_diagnostics=probe_result.to_dict() if probe_result else None,
            )


__all__ = [
    "CompositeRainfallResult",
    "CompositeRainfallProvider",
]
