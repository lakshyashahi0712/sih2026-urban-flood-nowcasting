"""Composite Rainfall Provider with strict provenance tracking.

Coordinates acquisition across:
1. Primary: IMD Doppler Weather Radar (quantitative observations)
2. Secondary: Mumbai Rain Mesonet (observed rainfall)
3. Fallback: Open-Meteo NWP Forecast (numerical weather prediction)

Guarantees:
- Never labels NWP forecast as radar or Mesonet observation.
- Automatically triggers fallback hierarchy when higher priority sources are unavailable.
- Transparently exposes fallback rationale and diagnostic details.
- Applies additive bounded correction to NWP when Mesonet observations are available.
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
    from backend.app.infrastructure.rainfall.mesonet import MesonetAdapter
except ImportError:
    from app.domain.rainfall.models import RainfallSeries, RainfallStatus, RainfallRecord
    from app.domain.rainfall.radar_models import (
        RainfallProvenance,
        SpatialRainfallGrid,
        MUMBAI_PILOT_BOUNDS_32643,
    )
    from app.infrastructure.rainfall.imd_radar import IMDRadarAdapter, IMDRadarProbeResult
    from app.infrastructure.rainfall.open_meteo import OpenMeteoAdapter
    from app.infrastructure.rainfall.mesonet import MesonetAdapter

logger = logging.getLogger(__name__)


class CompositeRainfallResult(BaseModel):
    """Result of composite rainfall acquisition with provenance and diagnostic metadata."""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    provenance: RainfallProvenance = Field(..., description="Authoritative provenance (RADAR, MESONET, NWP_FALLBACK, UNAVAILABLE)")
    status: RainfallStatus = Field(..., description="Data status (LIVE, STALE, UNAVAILABLE)")
    is_fallback: bool = Field(..., description="True if primary radar could not be used")
    fallback_reason: Optional[str] = Field(None, description="Detailed explanation why fallback was triggered")
    source_name: str = Field(..., description="Provider name (e.g. 'IMD Doppler Radar (Veravali)' or 'Mumbai Rain Mesonet' or 'Open-Meteo NWP')")
    acquired_at: datetime = Field(..., description="Acquisition timestamp (UTC)")
    series: Any = Field(None, description="Time series of rainfall records")
    spatial_grid: Optional[SpatialRainfallGrid] = Field(None, description="Spatial rainfall grid if quantitative radar is available")
    radar_diagnostics: Optional[Dict[str, Any]] = Field(None, description="Probe diagnostics from IMD radar service")
    mesonet_diagnostics: Optional[Dict[str, Any]] = Field(None, description="Diagnostic details from Mesonet service")


class CompositeRainfallProvider:
    """Orchestrator for multi-source rainfall data with radar -> Mesonet -> NWP fallback hierarchy."""

    def __init__(
        self,
        radar_adapter: Optional[IMDRadarAdapter] = None,
        mesonet_adapter: Optional[MesonetAdapter] = None,
        nwp_adapter: Optional[OpenMeteoAdapter] = None,
        max_correction_mm_per_hour: float = 20.0,
    ) -> None:
        self.radar_adapter = radar_adapter or IMDRadarAdapter()
        self.mesonet_adapter = mesonet_adapter or MesonetAdapter()
        self.nwp_adapter = nwp_adapter or OpenMeteoAdapter()
        self.max_correction_mm_per_hour = max_correction_mm_per_hour

    async def fetch_rainfall(
        self,
        target_bounds: Tuple[float, float, float, float] = MUMBAI_PILOT_BOUNDS_32643,
        use_cache: bool = True,
    ) -> CompositeRainfallResult:
        """Fetch precipitation data following the authoritative radar -> Mesonet -> NWP fallback hierarchy.

        1. Probes IMD Doppler Radar.
        2. If quantitative radar data is present and fresh -> returns RADAR provenance.
        3. If radar provides only non-quantitative GIF, is stale, or fails -> probes Mesonet.
        4. If Mesonet provides valid observed data -> returns MESONET provenance.
        5. If Mesonet fails or provides no data -> triggers NWP fallback with
           strict NWP_FALLBACK provenance tag.
        6. If NWP also fails -> returns UNAVAILABLE.
        """
        now_utc = datetime.now(timezone.utc)

        # Step 1: Probe IMD Radar
        radar_grid: Optional[SpatialRainfallGrid] = None
        probe_result: Optional[IMDRadarProbeResult] = None
        radar_error: Optional[Exception] = None
        try:
            radar_grid, probe_result = await self.radar_adapter.fetch_radar_grid(target_bounds=target_bounds)
        except Exception as ex:
            logger.warning(f"Error checking IMD radar: {ex}")
            radar_error = ex
            probe_result = None

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

        # Radar failed or non-quantitative, try Mesonet
        radar_fallback_reason = probe_result.diagnostic_message if probe_result else f"Radar unavailable ({radar_error})"
        logger.info(f"Triggering Mesonet attempt: {radar_fallback_reason}")

        mesonet_series: Optional[RainfallSeries] = None
        mesonet_error: Optional[Exception] = None
        mesonet_diagnostics: Optional[Dict[str, Any]] = None
        try:
            mesonet_series = await self.mesonet_adapter.fetch(use_cache=use_cache)
            # For Mesonet, we can create some basic diagnostics
            mesonet_diagnostics = {
                "station_count": len(mesonet_series.records) if mesonet_series else 0,
                "data_points": len(mesonet_series.records) if mesonet_series else 0,
                "source": "mumbai-mesonet",
                "attempted_at": now_utc.isoformat(),
            }
        except Exception as ex:
            logger.warning(f"Mesonet fetch failed: {ex}")
            mesonet_error = ex

        # If Mesonet data is available, also fetch NWP for correction
        if mesonet_series is not None and len(mesonet_series.records) > 0:
            # Guarantee provenance is explicitly stamped as MESONET on every record and series
            updated_records = []
            for rec in mesonet_series.records:
                updated_records.append(
                    rec.model_copy(update={"provenance": RainfallProvenance.MESONET})
                )
            mesonet_series = mesonet_series.model_copy(
                update={"records": updated_records, "provenance": RainfallProvenance.MESONET}
            )

            # Also fetch NWP data to apply correction
            try:
                nwp_series = await self.nwp_adapter.fetch(use_cache=use_cache)
                # Apply bounded correction to NWP using Mesonet observations
                corrected_nwp_series = self._apply_bounded_correction(nwp_series, mesonet_series)

                # Determine status (use the better of the two)
                nwp_status = nwp_series.records[0].status if nwp_series.records else RainfallStatus.LIVE
                mesonet_status = mesonet_series.records[0].status if mesonet_series.records else RainfallStatus.LIVE
                # Prefer Mesonet status if it's LIVE, otherwise use NWP status
                series_status = mesonet_status if mesonet_status == RainfallStatus.LIVE else nwp_status

                return CompositeRainfallResult(
                    provenance=RainfallProvenance.NWP_CORRECTED,
                    status=series_status,
                    is_fallback=True,  # Fallback from radar
                    fallback_reason=radar_fallback_reason,
                    source_name="Open-Meteo NWP Forecast (Corrected with Mumbai Rain Mesonet)",
                    acquired_at=now_utc,
                    series=corrected_nwp_series,
                    radar_diagnostics=probe_result.to_dict() if probe_result else None,
                    mesonet_diagnostics=mesonet_diagnostics,
                )
            except Exception as nwp_ex:
                logger.warning(f"NWP fetch failed for correction, using raw Mesonet: {nwp_ex}")
                # Fallback to raw Mesonet if NWP correction fails
                series_status = mesonet_series.records[0].status if mesonet_series.records else RainfallStatus.LIVE
                return CompositeRainfallResult(
                    provenance=RainfallProvenance.MESONET,
                    status=series_status,
                    is_fallback=True,  # Fallback from radar
                    fallback_reason=radar_fallback_reason,
                    source_name="Mumbai Rain Mesonet",
                    acquired_at=now_utc,
                    series=mesonet_series,
                    radar_diagnostics=probe_result.to_dict() if probe_result else None,
                    mesonet_diagnostics=mesonet_diagnostics,
                )

        # Step 3: Fallback to Open-Meteo NWP
        logger.info(f"Triggering NWP fallback: Radar failed ({radar_fallback_reason}), Mesonet failed ({mesonet_error})")
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
                fallback_reason=f"Radar unavailable ({radar_fallback_reason}); Mesonet unavailable ({mesonet_error})",
                source_name=f"Open-Meteo NWP Forecast (Fallback due to: Radar failure, Mesonet failure)",
                acquired_at=now_utc,
                series=nwp_series,
                radar_diagnostics=probe_result.to_dict() if probe_result else None,
                mesonet_diagnostics=mesonet_diagnostics,
            )

        except Exception as nwp_ex:
            logger.error(f"All rainfall sources failed: Radar, Mesonet, and NWP: {nwp_ex}")
            return CompositeRainfallResult(
                provenance=RainfallProvenance.UNAVAILABLE,
                status=RainfallStatus.UNAVAILABLE,
                is_fallback=True,
                fallback_reason=f"Radar unavailable ({radar_fallback_reason}); Mesonet unavailable ({mesonet_error}); NWP fallback failed ({nwp_ex})",
                source_name="None",
                acquired_at=now_utc,
                radar_diagnostics=probe_result.to_dict() if probe_result else None,
                mesonet_diagnostics=mesonet_diagnostics,
            )

    def _apply_bounded_correction(
        self,
        nwp_series: RainfallSeries,
        observed_series: RainfallSeries,
    ) -> RainfallSeries:
        """Apply bounded additive correction to NWP using Mesonet observations.

        Algorithm:
        1. Build a lookup: {timestamp -> observed_rainfall_mm} from observed records.
        2. For each NWP record:
           - If matching observation exists: apply clamped correction.
           - If no match: keep NWP value unchanged.
        3. Stamp NWP_CORRECTED provenance on every output record.
        4. Never extrapolate sparse gauge data across unmatched intervals.

        Args:
            nwp_series: NWP forecast series to correct.
            observed_series: Mesonet observation series.

        Returns:
            New RainfallSeries with corrected values and NWP_CORRECTED provenance.
        """
        if not nwp_series.records:
            return RainfallSeries(
                records=[],
                source=nwp_series.source,
                acquired_at=nwp_series.acquired_at,
                provenance=RainfallProvenance.NWP_CORRECTED,
            )

        # Build observation lookup by timestamp
        obs_lookup: dict = {}
        for rec in observed_series.records:
            obs_lookup[rec.timestamp] = rec.rainfall_mm

        corrected_records = []
        for nwp_rec in nwp_series.records:
            nwp_mm = nwp_rec.rainfall_mm

            if nwp_rec.timestamp in obs_lookup:
                obs_mm = obs_lookup[nwp_rec.timestamp]
                error = obs_mm - nwp_mm
                # Clamp correction to bounded range
                bounded_correction = max(
                    -self.max_correction_mm_per_hour,
                    min(self.max_correction_mm_per_hour, error)
                )
                corrected_mm = max(0.0, nwp_mm + bounded_correction)
            else:
                # No matching observation — keep NWP value unchanged
                corrected_mm = nwp_mm

            corrected_rec = nwp_rec.model_copy(
                update={
                    "rainfall_mm": corrected_mm,
                    "provenance": RainfallProvenance.NWP_CORRECTED,
                }
            )
            corrected_records.append(corrected_rec)

        return RainfallSeries(
            records=corrected_records,
            source=nwp_series.source,
            acquired_at=nwp_series.acquired_at,
            provenance=RainfallProvenance.NWP_CORRECTED,
        )


__all__ = [
    "CompositeRainfallResult",
    "CompositeRainfallProvider",
]