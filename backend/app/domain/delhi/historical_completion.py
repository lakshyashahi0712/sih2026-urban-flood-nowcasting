"""Historical NWP completion of replay forcing from the Open-Meteo archive.

The Kushak catalog documents only the event's core hours; the 24-hour
replay clock needs an hourly rainfall value for every hour of the event
day. This module supplies those hours from REAL historical reanalysis
(Open-Meteo archive API, ERA5 family) — it never invents or decay-extraps
rainfall. Every value returned here is a MODEL value (reanalysis grid
point at the documented Safdarjung reference), never a gauge observation,
and is labeled NWP_HISTORICAL_COMPLETION wherever it is used.

Catalog-documented hours always take precedence: completion only fills
hours the catalog does not document (or documents as UNKNOWN). Archive
nulls stay UNKNOWN — never zero-filled.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Dict, Optional

from .nowcast import (
    FETCH_TIMEOUT_SECONDS,
    IST,
    SAFDARJUNG_LAT,
    SAFDARJUNG_LON,
    SAFDARJUNG_REFERENCE,
    _http_get,
)

ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"

# hour-of-day (IST) -> mm for the hour, None where the archive has no
# value. Historical archive days are immutable, so one fetch per day.
_DAY_CACHE: Dict[date, Dict[int, Optional[float]]] = {}


class ArchiveUnavailable(RuntimeError):
    """The historical archive could not supply a complete event day."""


def fetch_event_day_hourly(day: date) -> Dict[int, Optional[float]]:
    """Hourly precipitation (mm per hour) for one full IST day.

    Raises ArchiveUnavailable unless all 24 hours are present; a partial
    day is never merged in silently.
    """
    cached = _DAY_CACHE.get(day)
    if cached is not None:
        return cached

    params = (
        f"?latitude={SAFDARJUNG_LAT}&longitude={SAFDARJUNG_LON}"
        f"&start_date={day.isoformat()}&end_date={day.isoformat()}"
        f"&hourly=precipitation&timezone=Asia%2FKolkata"
    )
    try:
        response = _http_get(ARCHIVE_URL + params, max(FETCH_TIMEOUT_SECONDS, 15.0))
        response.raise_for_status()
        payload = response.json()
    except Exception as exc:
        raise ArchiveUnavailable(f"Open-Meteo archive fetch failed: {exc}") from exc

    hourly = payload.get("hourly") or {}
    times = hourly.get("time") or []
    precip = hourly.get("precipitation") or []
    out: Dict[int, Optional[float]] = {}
    for t, v in zip(times, precip):
        try:
            dt = datetime.strptime(t, "%Y-%m-%dT%H:%M")
        except ValueError:
            continue
        if dt.date() != day:
            continue
        # Missing / negative / non-numeric values stay UNKNOWN, never clamped.
        out[dt.hour] = float(v) if isinstance(v, (int, float)) and v >= 0 else None
    if len(out) < 24:
        raise ArchiveUnavailable(
            f"archive returned {len(out)}/24 hours for {day.isoformat()}"
        )
    _DAY_CACHE[day] = out
    return out


def completion_reference() -> Dict[str, str]:
    return {
        "latitude": SAFDARJUNG_LAT,
        "longitude": SAFDARJUNG_LON,
        "reference_point": SAFDARJUNG_REFERENCE,
        "api": ARCHIVE_URL,
        "units_note": (
            "Open-Meteo archive hourly precipitation is a reanalysis MODEL "
            "value in mm per hour at the Safdarjung grid point - never a "
            "gauge observation of the catchment"
        ),
    }
