"""Delhi radar probe + rainfall composite provenance (mirrors the Mumbai
adapter pattern under Delhi provenance rules).

- Probes the IMD Delhi Doppler Weather Radar endpoints (quantitative
  gridded products vs visual GIFs). Quantitativeness is never assumed:
  only a documented quantitative product may be labeled RADAR; a
  visual GIF is never decoded into rainfall (no color calibration).
- The composite decision is honest: RADAR when a quantitative Delhi
  product is actually available, otherwise NWP_FALLBACK with the radar
  diagnostics attached. Open-Meteo is NEVER called radar.
"""

from __future__ import annotations

import logging
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

IMD_DELHI_RADAR_PAGE = "https://mausam.imd.gov.in/responsive/radar.php?id=Delhi"
IMD_DELHI_ENDPOINTS: Dict[str, str] = {
    "RADAR_PAGE": IMD_DELHI_RADAR_PAGE,
    "SRI_DLI": "https://mausam.imd.gov.in/Radar/sri_dli.gif",
    "PAC_DLI": "https://mausam.imd.gov.in/Radar/pac_dli.gif",
    "CAZ_DLI": "https://mausam.imd.gov.in/Radar/caz_dli.gif",
    "API_GATEWAY": "https://api.imd.gov.in/",
}

DELHI_RADAR_STATION = {
    "station_id": "DLI",
    "station_name": "Delhi-Mausam (Aya Nagar) Doppler Weather Radar",
    "lat": 28.4739,
    "lon": 77.1324,
    "radar_type": "C-band Doppler Weather Radar",
    "note": (
        "probed for availability only; quantitative decoding NEVER "
        "performed on visual GIF products (no color calibration exists)"
    ),
}

DEFAULT_RADAR_TIMEOUT = 10.0
MAX_STALENESS_MINUTES = 60

# Endpoint keys that can carry quantitative XYZ/NetCDF/HDF products.
_QUANTITATIVE_HINTS = (".nc", ".nc4", ".hdf", ".h5", ".xyz", ".tif", ".tiff")


@dataclass
class DelhiRadarProbeResult:
    endpoint_key: str
    endpoint_url: str
    http_status: int
    content_type: Optional[str] = None
    content_length_bytes: Optional[int] = None
    last_modified: Optional[datetime] = None
    age_minutes: Optional[float] = None
    is_accessible: bool = False
    is_quantitative: bool = False
    diagnostic_message: str = ""

    def to_dict(self) -> dict:
        return {
            "endpoint_key": self.endpoint_key,
            "endpoint_url": self.endpoint_url,
            "http_status": self.http_status,
            "content_type": self.content_type,
            "content_length_bytes": self.content_length_bytes,
            "age_minutes": self.age_minutes,
            "is_accessible": self.is_accessible,
            "is_quantitative": self.is_quantitative,
            "diagnostic_message": self.diagnostic_message,
        }


def _classify(
    url: str,
    content_type: Optional[str],
    content_length: Optional[int],
) -> tuple:
    """(is_quantitative, message). A GIF/JPG/PNG visual palette is never
    quantitative — decoding it would require official calibration."""
    if url.lower().endswith(_QUANTITATIVE_HINTS):
        return True, "Quantitative gridded product detected by extension"
    ctype = (content_type or "").lower()
    if any(k in ctype for k in ("netcdf", "hdf", "hdf5", "x-xyz", "tiff", "geotiff")):
        return True, "Quantitative gridded product detected by content type"
    if "gif" in ctype or url.lower().endswith((".gif", ".jpg", ".png")):
        return False, (
            "visual palette product (GIF/image); quantitative decoding "
            "refused without official calibration"
        )
    return False, "format not recognized as quantitative"


async def probe_delhi_radar(
    client: Optional[Any] = None,
    timeout: float = DEFAULT_RADAR_TIMEOUT,
) -> List[DelhiRadarProbeResult]:
    """Probe the IMD Delhi radar endpoints; returns diagnostics only."""
    results: List[DelhiRadarProbeResult] = []
    now = datetime.now(timezone.utc)

    for key, url in IMD_DELHI_ENDPOINTS.items():
        try:
            if client is not None:
                response = client.get(url, timeout=timeout)
            else:
                import httpx

                response = httpx.get(url, timeout=timeout, follow_redirects=True)
            ct = response.headers.get("content-type")
            length_raw = response.headers.get("content-length")
            length = int(length_raw) if length_raw and length_raw.isdigit() else None
            lm_raw = response.headers.get("last-modified")
            lm: Optional[datetime] = None
            if lm_raw:
                try:
                    lm = datetime.strptime(lm_raw, "%a, %d %b %Y %H:%M:%S GMT").replace(
                        tzinfo=timezone.utc
                    )
                except ValueError:
                    lm = None
            quant, message = _classify(url, ct, length)
            results.append(DelhiRadarProbeResult(
                endpoint_key=key,
                endpoint_url=url,
                http_status=response.status_code,
                content_type=ct,
                content_length_bytes=length,
                last_modified=lm,
                age_minutes=(
                    round((now - lm).total_seconds() / 60.0, 1)
                    if lm and now >= lm else None
                ),
                is_accessible=response.status_code == 200,
                is_quantitative=quant,
                diagnostic_message=message,
            ))
        except Exception as exc:  # degraded state, never fabricated
            results.append(DelhiRadarProbeResult(
                endpoint_key=key,
                endpoint_url=url,
                http_status=0,
                is_accessible=False,
                is_quantitative=False,
                diagnostic_message=f"probe failed: {str(exc)[:160]}",
            ))
    return results


def any_quantitative_delhi_radar(results: List[DelhiRadarProbeResult]) -> bool:
    return any(r.is_accessible and r.is_quantitative for r in results)


def delhi_rainfall_composite(
    nwp_status: str,
    nwp_acquired_at: Optional[datetime],
    radar_results: Optional[List[DelhiRadarProbeResult]] = None,
) -> dict:
    """The composite decision with strict provenance (mirrors Mumbai's
    hierarchy): RADAR when a quantitative Delhi product is available,
    otherwise NWP_FALLBACK. Never labels NWP as radar."""
    if radar_results is None:
        radar_results = []
    quantitative = any_quantitative_delhi_radar(radar_results)
    if quantitative:
        provenance = "RADAR"
        is_fallback = False
        source_name = f"IMD Doppler Weather Radar ({DELHI_RADAR_STATION['station_id']})"
        fallback_reason = None
    else:
        provenance = "NWP_FALLBACK" if nwp_status == "COMPUTED" else "UNAVAILABLE"
        is_fallback = True
        source_name = (
            "Open-Meteo NWP forecast (IMD radar unavailable or not "
            "quantitative)"
            if provenance == "NWP_FALLBACK"
            else "no rainfall source available"
        )
        fallback_reason = (
            "no quantitative IMD Delhi radar product detected; visual GIF "
            "products are never decoded into rainfall (no official "
            "calibration)" if provenance == "NWP_FALLBACK"
            else "NWP forecast failed to acquire"
        )
    return {
        "provenance": provenance,  # RADAR | NWP_FALLBACK | UNAVAILABLE
        "status": "LIVE" if quantitative else (
            "LIVE" if provenance == "NWP_FALLBACK" else "UNAVAILABLE"
        ),
        "is_fallback": is_fallback,
        "fallback_reason": fallback_reason,
        "source_name": source_name,
        "nwp_acquired_at": nwp_acquired_at.isoformat() if nwp_acquired_at else None,
        "radar_station": DELHI_RADAR_STATION,
        "radar_diagnostics": [r.to_dict() for r in radar_results],
    }