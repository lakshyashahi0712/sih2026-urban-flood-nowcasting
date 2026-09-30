import { useCallback, useEffect, useMemo, useState } from 'react';
import { delhiApi, type EventReplayResponse, type StreetsIntel } from '../../api/delhi';
import type { MapFlowState } from './DelhiMap';

// V2 historical replay controls — V1 parity, 24 hourly steps over the
// event day (V1's Step n/24 convention). Forcing comes from the backend's
// NWP-completed event-day series: documented catalog hours always win,
// the remaining hours are Open-Meteo HISTORICAL reanalysis values labeled
// NWP_HISTORICAL_COMPLETION (model, never observed). If the archive was
// unavailable, undocumented hours fall back to UNKNOWN — never invented,
// never zero-filled.
const REPLAY_EVENT_ID = 'EVT-2024-06-27';
const TOTAL_HOURS = 24;

const pad2 = (n: number) => String(n).padStart(2, '0');
const hhmm = (h: number) => `${pad2(((h % 24) + 24) % 24)}:00`;

const istParts = (iso: string) => {
  const d = new Date(iso);
  const hour = parseInt(
    new Intl.DateTimeFormat('en-GB', {
      timeZone: 'Asia/Kolkata',
      hour: '2-digit',
      hour12: false,
    }).format(d),
    10,
  ) % 24;
  const day = new Intl.DateTimeFormat('en-GB', {
    timeZone: 'Asia/Kolkata',
    day: '2-digit',
    month: 'short',
  }).format(d);
  return { hour, day };
};

const ReplayControls = ({
  onMapState,
  onDepthCells = () => {},
  onDepthPolygons = () => {},
  onStreets = () => {},
  onReplayContext,
}: {
  onMapState: (s: MapFlowState) => void;
  onDepthCells?: (
    cells: { lon: number; lat: number; depth_cm: number; flood_state: string; provenance: string }[],
  ) => void;
  onDepthPolygons?: (polygons: { type: string; features: unknown[] } | null) => void;
  // V1-parity replay roads: the timestep's street/intersection intelligence,
  // including each corridor's depth change vs the previous timestep.
  onStreets?: (streets: StreetsIntel | null) => void;
  // Reports the active (event, timestep) to the app so historical
  // safe-route computations follow the replay clock (V1 behaviour).
  onReplayContext?: (ctx: { eventId: string; timestepIndex: number }) => void;
}) => {
  const [replay, setReplay] = useState<EventReplayResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [hourIdx, setHourIdx] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [showDepthCells, setShowDepthCells] = useState(true);
  const [showDepthPolygons, setShowDepthPolygons] = useState(true);
  const [showRoads, setShowRoads] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const res = await delhiApi.getEventReplay(REPLAY_EVENT_ID, false, undefined, true);
        setReplay(res);
        setHourIdx(0);
        setPlaying(false);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'replay failed');
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const steps = replay?.members?.[0]?.chain_steps ?? [];
  const bins = replay?.forcing?.bins ?? [];
  const firstStepIso = steps[0]?.time_start ?? null;

  // Hour-of-day (IST) where documented forcing starts; the 24-h clock runs
  // from midnight of the event day.
  const docStartHour = firstStepIso ? istParts(firstStepIso).hour : 0;
  const eventDay = firstStepIso ? istParts(firstStepIso).day : '';

  // Backend NWP-completed event-day forcing (24 hourly bins).
  const completion =
    replay?.forcing_completion && replay.forcing_completion.status === 'COMPUTED'
      ? replay.forcing_completion
      : null;
  const hourBin = completion ? completion.bins[hourIdx] : null;
  const hourRain = hourBin?.depth_mm ?? null;
  const hourIsCatalog =
    hourBin != null && hourBin.source === 'DOCUMENTED_CATALOG' && hourRain !== null;

  // Map a clock hour to the documented chain-step index (null if the hour
  // carries no documented modelled state). Chain states exist only for
  // catalog hours — completion covers forcing + surface depth, not the
  // 1D reach chain.
  const docIdx = useCallback(
    (h: number): number | null => {
      const b = h - docStartHour;
      return b >= 0 && b < steps.length ? b : null;
    },
    [docStartHour, steps.length],
  )(hourIdx);
  const bin = docIdx !== null ? bins[docIdx] : null;

  const peakHour = useMemo(() => {
    if (completion) {
      let best = 0;
      completion.bins.forEach((b, i) => {
        const cur = b.depth_mm ?? -1;
        const bestv = completion.bins[best].depth_mm ?? -1;
        if (cur > bestv) best = i;
      });
      return best;
    }
    let best = 0;
    bins.forEach((b, i) => {
      if (b.depth_mm !== null && (bins[best].depth_mm === null || b.depth_mm > bins[best].depth_mm!)) {
        best = i;
      }
    });
    return docStartHour + best;
  }, [completion, bins, docStartHour]);

  const cumulativeMm = useMemo(() => {
    const values: number[] = completion
      ? completion.bins.slice(0, hourIdx + 1).map((b) => b.depth_mm).filter((v): v is number => v !== null)
      : hourIdx >= docStartHour
        ? bins
            .slice(0, hourIdx - docStartHour + 1)
            .filter((b) => b.depth_mm !== null)
            .map((b) => b.depth_mm!)
        : [];
    return values.length > 0 ? values.reduce((a, b) => a + b, 0) : null;
  }, [completion, bins, hourIdx, docStartHour]);

  const peakStorageM3 = useMemo(() => {
    let peak: number | null = null;
    for (const s of steps) {
      for (const r of s.reaches) {
        if (r.storage_m3 !== null && (peak === null || r.storage_m3 > peak)) {
          peak = r.storage_m3;
        }
      }
    }
    return peak;
  }, [steps]);

  const goTo = useCallback((h: number) => {
    setPlaying(false);
    setHourIdx(Math.max(0, Math.min(TOTAL_HOURS - 1, h)));
  }, []);

  // Playback timer, V1 style: one hour per tick, stops at the end.
  useEffect(() => {
    if (!playing || !replay || replay.runtime_status === 'NOT_EXECUTED') return;
    const t = setInterval(() => {
      setHourIdx((i) => {
        if (i + 1 >= TOTAL_HOURS) {
          setPlaying(false);
          return i;
        }
        return i + 1;
      });
    }, 900);
    return () => clearInterval(t);
  }, [playing, replay]);

  // Route against the nearest documented chain state when the clock sits
  // on an hour without one (pre-storm: dry step 0; post-window: last step).
  const routeStepIdx = docIdx ?? (hourIdx < docStartHour ? 0 : Math.max(0, steps.length - 1));
  useEffect(() => {
    onReplayContext?.({ eventId: REPLAY_EVENT_ID, timestepIndex: routeStepIdx });
  }, [routeStepIdx, onReplayContext]);

  // Map flow follows the clock. Reach states exist only for documented
  // chain hours; completed hours push their (model) rain value, hours with
  // no value from either source push UNKNOWN — never invented.
  useEffect(() => {
    if (!replay || replay.runtime_status === 'NOT_EXECUTED') {
      onMapState({ reachStates: {}, timestamp: null, rainIntensityMmH: null, rainKnown: false });
      return;
    }
    const step = docIdx !== null ? steps[docIdx] : null;
    const reachStates: MapFlowState['reachStates'] = {};
    for (const r of step?.reaches ?? []) {
      reachStates[r.reach_id] = r.hydraulic_status.startsWith('BLOCKED')
        ? 'BLOCKED'
        : r.storage_m3 !== null
          ? 'COMPUTED'
          : 'UNKNOWN';
    }
    const timestamp = firstStepIso
      ? new Date(new Date(firstStepIso).getTime() + (hourIdx - docStartHour) * 3600_000).toISOString()
      : null;
    const rainMm = completion ? hourRain : docIdx !== null && bin?.depth_mm != null ? bin.depth_mm : null;
    onMapState({
      reachStates,
      timestamp,
      rainIntensityMmH: rainMm,
      rainKnown: rainMm !== null,
    });
  }, [replay, hourIdx, docIdx, docStartHour, firstStepIso, onMapState, steps, bin, completion, hourRain]);

  // Flood depth layers follow the clock (V1 playback behaviour). With the
  // completed event day every hour has a modelled depth step; without it,
  // hours without a documented modelled state clear the layer instead of
  // pretending it is dry-by-computation.
  useEffect(() => {
    if (!replay || replay.runtime_status === 'NOT_EXECUTED') {
      onDepthCells([]);
      onDepthPolygons(null);
      onStreets(null);
      return;
    }
    const idx = completion ? hourIdx : docIdx;
    if (idx === null) {
      onDepthCells([]);
      onDepthPolygons(null);
      onStreets(null);
      return;
    }
    let cancelled = false;
    delhiApi
      .getEventDepth(replay.event_id, idx, completion != null)
      .then((d) => {
        if (!cancelled) {
          onDepthCells(showDepthCells ? d.step?.depth_cells ?? [] : []);
          onDepthPolygons(showDepthPolygons ? d.step?.depth_polygons ?? null : null);
          onStreets(showRoads ? d.step?.streets ?? null : null);
        }
      })
      .catch(() => {
        if (!cancelled) {
          onDepthCells([]);
          onDepthPolygons(null);
          onStreets(null);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [replay, hourIdx, docIdx, completion, showDepthCells, showDepthPolygons, showRoads,
      onDepthCells, onDepthPolygons, onStreets]);

  if (loading) {
    return <div className="delhi-panel-status">Loading historical replay…</div>;
  }
  if (error) {
    return <div className="delhi-panel-status delhi-panel-error">{error}</div>;
  }
  if (!replay || replay.runtime_status === 'NOT_EXECUTED' || steps.length === 0) {
    return (
      <div className="delhi-panel-status delhi-panel-error">
        Historical replay is not executable for {REPLAY_EVENT_ID}: documented
        forcing is absent, and absent forcing is never invented or zero-filled.
      </div>
    );
  }

  const shownRain = completion ? hourRain : docIdx !== null ? bin?.depth_mm ?? null : null;
  const rainKnown = shownRain !== null;
  const bannerTag = completion
    ? !rainKnown
      ? ' • NO DOCUMENTED STATE (UNKNOWN)'
      : hourIsCatalog
        ? ` • ${replay.rainfall_resolution} • OBSERVED`
        : ' • NWP HISTORICAL (MODEL)'
    : docIdx === null
      ? ' • NO DOCUMENTED STATE (UNKNOWN)'
      : ` • ${replay.rainfall_resolution}`;

  return (
    <>
      <div className="timeline-header">
        <span
          className="timeline-heading text-sm font-bold tracking-wide"
          style={{ color: '#b45309' }}
        >
          {eventDay.toUpperCase()} REPLAY
        </span>
        <span
          className="timeline-active-tag text-xs font-medium"
          style={{ background: '#fef3c7', color: '#b45309' }}
        >
          Step {hourIdx + 1}/{TOTAL_HOURS}
        </span>
      </div>

      <div className="historical-time-banner">
        <span className="hist-time-main">
          {hhmm(hourIdx)} IST{bannerTag}
        </span>
      </div>

      <div className="historical-transport-row">
        <button
          type="button"
          className="transport-btn"
          onClick={() => goTo(0)}
          title="Jump to Start (00:00 IST)"
          aria-label="Jump to start timestep"
        >
          ⏮
        </button>
        <button
          type="button"
          className="transport-btn"
          onClick={() => goTo(hourIdx - 1)}
          title="Previous Timestep"
          aria-label="Previous timestep"
        >
          ◀
        </button>
        <button
          type="button"
          className={`transport-btn play-btn ${playing ? 'playing' : ''}`}
          onClick={() => {
            if (playing) {
              setPlaying(false);
            } else {
              if (hourIdx >= TOTAL_HOURS - 1) setHourIdx(0);
              setPlaying(true);
            }
          }}
          title={playing ? 'Pause Replay' : 'Play Replay'}
          aria-label={playing ? 'Pause replay' : 'Play replay'}
        >
          {playing ? '⏸ Pause' : '▶ Play'}
        </button>
        <button
          type="button"
          className="transport-btn"
          onClick={() => goTo(hourIdx + 1)}
          title="Next Timestep"
          aria-label="Next timestep"
        >
          ▶
        </button>
        <button
          type="button"
          className="transport-btn peak-btn"
          onClick={() => goTo(peakHour)}
          title={`Jump to Peak Forcing (Step ${peakHour + 1} / ${hhmm(peakHour)} IST)`}
          aria-label="Jump to peak forcing"
        >
          ⚡ Peak
        </button>
      </div>

      <div className="timeline-slider-container">
        <input
          type="range"
          min={0}
          max={TOTAL_HOURS - 1}
          step={1}
          value={hourIdx}
          onChange={(e) => goTo(Number(e.target.value))}
          className="historical-slider"
          aria-label="Replay timestep"
        />
        <div className="slider-ticks">
          <span>00:00</span>
          <span style={{ color: '#d97706', fontWeight: 700 }}>{hhmm(peakHour)} (Peak)</span>
          <span>23:00</span>
        </div>
      </div>

      <div className="historical-forcing-row">
        <div className="hist-forcing-box">
          <span className="h-lbl">Rain Rate:</span>
          <span className="h-val">
            {rainKnown
              ? `${shownRain!.toFixed(1)} mm/h${completion && !hourIsCatalog ? ' (NWP)' : ''}`
              : 'UNKNOWN'}
          </span>
        </div>
        <div className="hist-forcing-box">
          <span className="h-lbl">Cumulative:</span>
          <span className="h-val">
            {cumulativeMm !== null ? `${cumulativeMm.toFixed(1)} mm` : 'UNKNOWN'}
          </span>
        </div>
        <div className="hist-forcing-box" title="Peak modelled reach storage across the replay (not an observed level)">
          <span className="h-lbl">Peak storage:</span>
          <span className="h-val">
            {peakStorageM3 !== null ? `${(peakStorageM3 / 1e6).toFixed(2)} ×10⁶ m³` : 'UNKNOWN'}
          </span>
        </div>
      </div>

      <div className="historical-layers-row">
        <span className="hist-layers-title">REPLAY LAYERS:</span>
        <label
          className="hist-layer-toggle"
          title="Show modelled 30 m flood depth grid for this replay timestep"
        >
          <input
            type="checkbox"
            checked={showDepthCells}
            onChange={(e) => setShowDepthCells(e.target.checked)}
          />
          <span>Flood Depth Grid</span>
        </label>
        <label
          className="hist-layer-toggle"
          title="Show modelled inundation extent polygons for this replay timestep"
        >
          <input
            type="checkbox"
            checked={showDepthPolygons}
            onChange={(e) => setShowDepthPolygons(e.target.checked)}
          />
          <span>Inundation Extent</span>
        </label>
        <label
          className="hist-layer-toggle"
          title="Show modelled flooded road corridors and junctions for this replay timestep, with the change vs the previous timestep"
        >
          <input
            type="checkbox"
            checked={showRoads}
            onChange={(e) => setShowRoads(e.target.checked)}
          />
          <span>Flooded Roads</span>
        </label>
      </div>

      <div className="scenario-explanatory-note">
        {completion
          ? `24-hour event-day replay (${eventDay} IST): catalog-documented hours keep their documented forcing (verified/observed values only); every other hour - including catalog hours documented as UNKNOWN - is completed from the Open-Meteo historical archive (NWP reanalysis - model values, never observations). The V1 depth model runs every hour and carries the previous hour's standing water forward minus an ASSUMED infiltration loss, so inundation rises and drains across the day instead of resetting. Road depths and their ▲/▼ change are measured against the previous replay timestep of the same model - never observed. Hours with no value from either source stay UNKNOWN - nothing invented, nothing zero-filled.`
          : `24-hour playback clock over the event day (${replay.event_window}). Modelled states exist only for the documented hours (${hhmm(docStartHour)}–${hhmm(
              docStartHour + steps.length,
            )} IST, incl. hourly recession); every other hour is UNKNOWN — no rainfall invented, nothing zero-filled. NWP completion unavailable: ${
              replay.forcing_completion?.diagnostics?.join('; ') ?? 'no completion block'
            }.`}
      </div>
    </>
  );
};

export default ReplayControls;
