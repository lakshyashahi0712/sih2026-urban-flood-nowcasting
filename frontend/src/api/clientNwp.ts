import { apiUrl } from './config';

// Must match MUMBAI_LAT / MUMBAI_LON in backend/app/infrastructure/rainfall/open_meteo.py,
// otherwise the client and the server are forecasting different points.
const MUMBAI_LAT = 19.086115;
const MUMBAI_LON = 72.85291;

const IST_OFFSET_MS = 5.5 * 60 * 60 * 1000;

/** Hourly precipitation [mm] for NOW..+3h, fetched over the visitor's own connection. */
export async function fetchClientNwpRainfall(signal?: AbortSignal): Promise<number[] | null> {
  try {
    const res = await fetch(
      `https://api.open-meteo.com/v1/forecast?latitude=${MUMBAI_LAT}&longitude=${MUMBAI_LON}` +
        '&hourly=precipitation&forecast_days=2&timezone=Asia%2FKolkata',
      { signal },
    );
    if (!res.ok) return null;

    const data = await res.json();
    const times: string[] = data?.hourly?.time || [];
    const precip: (number | null)[] = data?.hourly?.precipitation || [];
    if (!times.length || !precip.length) return null;

    // Open-Meteo labels hours in Asia/Kolkata because we asked it to; shift "now" into that
    // clock and read it back with getUTC* so the string matches without a timezone library.
    const istNow = new Date(Date.now() + IST_OFFSET_MS);
    const pad = (n: number) => String(n).padStart(2, '0');
    const hourStr = `${istNow.getUTCFullYear()}-${pad(istNow.getUTCMonth() + 1)}-${pad(
      istNow.getUTCDate(),
    )}T${pad(istNow.getUTCHours())}:00`;

    let idx = times.indexOf(hourStr);
    if (idx === -1) idx = times.findIndex((t) => t >= hourStr);
    if (idx === -1) return null;

    const mm: number[] = [];
    for (let i = 0; i < 4; i++) {
      const value = idx + i < precip.length ? precip[idx + i] : 0;
      mm.push(typeof value === 'number' && value >= 0 ? Number(value.toFixed(2)) : 0);
    }
    return mm;
  } catch {
    return null;
  }
}

/** Hand the client-fetched series to the backend so it caches it instead of a stale snapshot. */
export async function postClientNwpIngest(mm: number[]): Promise<boolean> {
  try {
    const res = await fetch(apiUrl('/flood/nwp-ingest'), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ rainfall_mm: mm }),
    });
    return res.ok;
  } catch {
    return false;
  }
}
