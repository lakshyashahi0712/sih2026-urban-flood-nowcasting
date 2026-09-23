import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import DelhiMap, { type MapFlowState, type RoutePickPoint } from './DelhiMap';
import ReplayPanel from './ReplayPanel';
import EvidencePanel from './EvidencePanel';
import RoutePanel from './RoutePanel';
import ModelPanel from './ModelPanel';
import ScenarioPanel from './ScenarioPanel';
import LivePanel from './LivePanel';
import {
  delhiApi,
  type DrainageGraphResponse,
  type LiveStateResponse,
  type SafeRouteResponse,
  type SurfaceHotspot,
  type WhatIfResponse,
} from '../../api/delhi';

type Mode = 'LIVE' | 'SCENARIO' | 'REPLAY';
type Horizon = 'NOW' | '+1h' | '+2h' | '+3h';

const HORIZONS: Horizon[] = ['NOW', '+1h', '+2h', '+3h'];
const SCENARIO_PRESETS = [20, 40, 50, 70];

// V1 hero titles (FloodMap.tsx periodDisplays).
const HORIZON_TITLES: Record<Horizon, string> = {
  NOW: 'Current Hour Baseline',
  '+1h': '+1 Hour Outlook (T+1h)',
  '+2h': '+2 Hours Outlook (T+2h)',
  '+3h': '+3 Hours Outlook (T+3h)',
};

const EMPTY_FLOW: MapFlowState = {
  reachStates: {},
  timestamp: null,
  rainIntensityMmH: null,
  rainKnown: false,
};

// V1 flood-depth legend ramp (identical to the Mumbai FloodMap legend).
const DEPTH_LEGEND = [
  { color: '#ffeda0', range: '0.0 – 0.5 m', desc: 'Minor' },
  { color: '#feb24c', range: '0.5 – 1.0 m', desc: 'Moderate' },
  { color: '#f03b20', range: '1.0 – 2.0 m', desc: 'High' },
  { color: '#bd0026', range: '2.0+ m', desc: 'Severe' },
];

function riskBanner(maxDepthM: number | null): {
  text: string; bg: string; border: string; color: string; desc: string;
} {
  if (maxDepthM === null) {
    return { text: 'UNKNOWN', bg: '#f8fafc', border: '#cbd5e1', color: '#475569', desc: 'No defensible model state for this step' };
  }
  if (maxDepthM >= 1.0) return { text: 'SEVERE', bg: '#fef2f2', border: '#f87171', color: '#991b1b', desc: 'Major inundation • significant roadway disruption' };
  if (maxDepthM >= 0.5) return { text: 'HIGH', bg: '#fff7ed', border: '#fb923c', color: '#c2410c', desc: 'Curb overflow • street flooding in low-lying areas' };
  if (maxDepthM > 0.0) return { text: 'MODERATE', bg: '#fefce8', border: '#facc15', color: '#854d0e', desc: 'Localized waterlogging in terrain depressions' };
  return { text: 'NO INUNDATION', bg: '#f8fafc', border: '#cbd5e1', color: '#166534', desc: 'Runoff conveyed by drainage • no surface ponding' };
}

const DelhiApp = () => {
  const [mode, setMode] = useState<Mode>('LIVE');
  const [horizon, setHorizon] = useState<Horizon>('+1h');
  const [scenarioMm, setScenarioMm] = useState<number>(40);

  // LIVE: per-horizon states from /api/delhi/live-state (V1 parity).
  const [liveState, setLiveState] = useState<LiveStateResponse | null>(null);
  const [liveLoading, setLiveLoading] = useState(true);
  const [liveError, setLiveError] = useState<string | null>(null);
  const [scenarioState, setScenarioState] = useState<WhatIfResponse | null>(null);
  const [scenarioLoading, setScenarioLoading] = useState(false);

  // Shared map state pushed up by the active panel (model data only).
  const [mapFlow, setMapFlow] = useState<MapFlowState>(EMPTY_FLOW);
  const mapFlowRef = useRef<MapFlowState>(EMPTY_FLOW);
  mapFlowRef.current = mapFlow;

  // Safe-routing shared state (map <-> panel).
  const [routePick, setRoutePick] = useState<'origin' | 'destination' | null>(null);
  const [routePicks, setRoutePicks] = useState<{
    origin: RoutePickPoint | null;
    destination: RoutePickPoint | null;
  }>({ origin: null, destination: null });
  const [routeResult, setRouteResult] = useState<SafeRouteResponse | null>(null);
  const [routeHudOpen, setRouteHudOpen] = useState(false);
  const [routeLoading, setRouteLoading] = useState(false);
  const [routeError, setRouteError] = useState<string | null>(null);
  const [drainageGraph, setDrainageGraph] = useState<DrainageGraphResponse | null>(null);
  const [surfaceHotspots, setSurfaceHotspots] = useState<SurfaceHotspot[]>([]);
  const [depthCells, setDepthCells] = useState<
    { lon: number; lat: number; depth_cm: number; flood_state: string; provenance: string }[]
  >([]);
  const [depthPolygons, setDepthPolygons] = useState<{ type: string; features: unknown[] } | null>(null);
  const [scenarioRoadDepths, setScenarioRoadDepths] = useState<
    Record<string, { depth_cm: number; depth_m: number; flood_state: string }> | null
  >(null);
  const [evidenceOpen, setEvidenceOpen] = useState(false);
  const [mobileDrawerExpanded, setMobileDrawerExpanded] = useState<boolean>(true);

  useEffect(() => {
    delhiApi.getDrainageGraph().then(setDrainageGraph).catch(() => setDrainageGraph(null));
  }, []);

  // LIVE forecast states: fetched once, cached; independent per-horizon
  // switching is instant (no refetch on horizon change).
  const loadLive = useCallback((refresh = false) => {
    setLiveLoading(true);
    setLiveError(null);
    delhiApi
      .getLiveState(refresh)
      .then(setLiveState)
      .catch((err) => setLiveError(err instanceof Error ? err.message : 'live state unavailable'))
      .finally(() => setLiveLoading(false));
  }, []);

  useEffect(() => {
    loadLive(false);
  }, [loadLive]);

  // MODEL SCENARIO: real backend computation per intensity (cached server-side).
  useEffect(() => {
    if (mode !== 'SCENARIO') return;
    setScenarioLoading(true);
    delhiApi
      .getWhatIf(scenarioMm)
      .then(setScenarioState)
      .catch(() => setScenarioState(null))
      .finally(() => setScenarioLoading(false));
  }, [mode, scenarioMm]);

  const activeHorizonState = useMemo(
    () => liveState?.horizons.find((h) => h.horizon === horizon) ?? null,
    [liveState, horizon],
  );

  // Reset map overlays when switching workflows.
  const switchMode = (next: Mode) => {
    setMode(next);
    setMapFlow(EMPTY_FLOW);
    setRoutePick(null);
    setDepthCells([]);
    setDepthPolygons(null);
    setSurfaceHotspots([]);
    setScenarioRoadDepths(null);
    if (next !== 'LIVE') {
      setRouteResult(null);
      setRoutePicks({ origin: null, destination: null });
      setRouteHudOpen(false);
      setRouteLoading(false);
      setRouteError(null);
    }
    if (next === 'LIVE') setRouteHudOpen(routePicks.origin !== null);
  };

  const fetchSafeRoute = useCallback(
    async (origin: [number, number], destination: [number, number]) => {
      setRouteLoading(true);
      setRouteError(null);
      try {
        const departureHour = Math.max(0, HORIZONS.indexOf(horizon));
        const res = await delhiApi.getSafeRoute({
          origin,
          destination,
          mode: 'live',
          departure_hour: departureHour,
        });
        setRouteResult(res);
      } catch (err) {
        const msg = err instanceof Error ? err.message : 'Route calculation failed';
        setRouteError(msg);
        setRouteResult(null);
      } finally {
        setRouteLoading(false);
      }
    },
    [horizon],
  );

  const handleExitRouting = useCallback(() => {
    setRouteHudOpen(false);
    setRoutePick(null);
    setRouteResult(null);
    setRouteError(null);
    setRouteLoading(false);
    setRoutePicks({ origin: null, destination: null });
  }, []);

  const handleMapClick = (lonlat: [number, number]) => {
    if (!routePick) return;
    if (routePick === 'origin') {
      const newOrigin = { coords: lonlat };
      setRoutePicks((prev) => ({ ...prev, origin: newOrigin }));
      if (routePicks.destination) {
        setRoutePick(null);
        void fetchSafeRoute(lonlat, routePicks.destination.coords);
      } else {
        setRoutePick('destination');
      }
    } else if (routePick === 'destination') {
      const newDest = { coords: lonlat };
      setRoutePicks((prev) => ({ ...prev, destination: newDest }));
      setRoutePick(null);
      if (routePicks.origin) {
        void fetchSafeRoute(routePicks.origin.coords, lonlat);
      } else {
        setRoutePick('origin');
      }
    }
  };

  // The active model state driving the hero card + map overlays.
  const activeState = mode === 'LIVE' ? activeHorizonState : mode === 'SCENARIO' ? scenarioState : null;
  const maxDepthM = activeState?.max_depth_m ?? null;
  const floodedAreaM2 = activeState?.flooded_area_m2 ?? null;
  const streets = activeState?.streets ?? null;
  const banner = riskBanner(maxDepthM);

  const rainfallMetricLabel =
    mode === 'LIVE' ? 'FORECAST RAINFALL' : mode === 'SCENARIO' ? 'SCENARIO INTENSITY' : 'HISTORICAL RAIN RATE';
  const rainfallMetricVal =
    mode === 'LIVE'
      ? activeHorizonState?.rainfall_mm !== null && activeHorizonState?.rainfall_mm !== undefined
        ? activeHorizonState.rainfall_mm.toFixed(1)
        : '--'
      : mode === 'SCENARIO'
        ? scenarioMm.toFixed(1)
        : '--';
  const rainfallMetricSub =
    mode === 'LIVE'
      ? activeHorizonState?.rainfall_provenance === 'SYNTHETIC_FALLBACK'
        ? 'SYNTHETIC FALLBACK (demo series)'
        : 'Open-Meteo NWP hourly (model value)'
      : mode === 'SCENARIO'
        ? 'Hypothetical model input (What-If)'
        : 'Documented event forcing';

  const syntheticFallback = liveState?.rainfall_status === 'SYNTHETIC_FALLBACK';

  return (
    <div className="flood-app">
      {/* 1. TOP BAR: V1 identity hierarchy */}
      <header className="app-topbar">
        <div className="topbar-left">
          <div className="system-identity">
            <span className="system-mark">øy</span>
            <span className="system-title">URBAN FLOOD NOWCAST</span>
          </div>
          <span className="topbar-sep">|</span>
          <div className="system-location">
            <span className="loc-label text-base font-bold">DELHI</span>
          </div>
          <span className="topbar-sep">|</span>
          <div className="system-subtitle text-sm font-normal">
            <span>
              {mode === 'REPLAY'
                ? 'RETROSPECTIVE EVENT REPLAY'
                : mode === 'SCENARIO'
                  ? 'WHAT-IF FLOOD SCENARIO'
                  : '0–3 HOUR FLOOD OUTLOOK'}
            </span>
          </div>
          <div
            className="prototype-status-pill"
            style={
              mode === 'REPLAY'
                ? { background: '#78350f', borderColor: '#d97706' }
                : mode === 'SCENARIO'
                  ? { background: '#0284c7', borderColor: '#38bdf8' }
                  : syntheticFallback
                    ? { background: '#7c2d12', borderColor: '#ea580c' }
                    : undefined
            }
          >
            <span
              className="status-dot"
              style={
                mode === 'REPLAY'
                  ? { background: '#fef3c7' }
                  : mode === 'SCENARIO'
                    ? { background: '#e0f2fe' }
                    : undefined
              }
            />
            <span>
              {mode === 'REPLAY'
                ? 'HISTORICAL REPLAY'
                : mode === 'SCENARIO'
                  ? 'MODEL SCENARIO'
                  : syntheticFallback
                    ? 'LIVE · SYNTHETIC FALLBACK'
                    : 'PROTOTYPE SCENARIO'}
            </span>
          </div>
        </div>
        <div className="topbar-right">
          <button
            className={`evidence-toggle ${evidenceOpen ? 'active' : ''}`}
            onClick={() => setEvidenceOpen((v) => !v)}
          >
            EVIDENCE
          </button>
          <div className="telemetry-info">
            <span className="meta-tag text-xs font-normal tracking-wide">60-MIN TIMESTEP</span>
            <span className="meta-divider">•</span>
            {mode === 'REPLAY' ? (
              <>
                <span
                  className="meta-tag text-xs font-normal tracking-wide"
                  style={{ background: '#78350f', borderColor: '#d97706', color: '#fef3c7' }}
                >
                  24-HR REPLAY
                </span>
                <span className="meta-divider">•</span>
                <span className="meta-label text-xs font-normal">DEPTH:</span>
                <span className="meta-val text-sm font-medium">MODELLED</span>
              </>
            ) : mode === 'SCENARIO' ? (
              <>
                <span className="meta-label text-xs font-normal">INPUT:</span>
                <span className="meta-val text-sm font-medium" style={{ color: '#38bdf8' }}>
                  Hypothetical rainfall input ({scenarioMm} mm/h)
                </span>
                <span className="meta-divider">•</span>
                <span className="meta-label text-xs font-normal">MODE:</span>
                <span className="meta-val text-sm font-medium" style={{ color: '#e2e8f0' }}>
                  MODEL SCENARIO
                </span>
              </>
            ) : (
              <>
                <span className="meta-label text-xs font-normal">SOURCE:</span>
                <span
                  className="meta-val text-sm font-medium"
                  style={syntheticFallback ? { color: '#fb923c' } : undefined}
                >
                  Open-Meteo NWP ({syntheticFallback ? 'SYNTHETIC_FALLBACK' : (liveState?.rainfall_status ?? '…')})
                </span>
                <span className="meta-divider">•</span>
                <span className="meta-label text-xs font-normal">ACQUIRED:</span>
                <span className="meta-val text-sm font-medium">
                  {liveState?.rainfall_acquired_at
                    ? new Date(liveState.rainfall_acquired_at).toLocaleTimeString('en-IN', {
                        hour: '2-digit',
                        minute: '2-digit',
                        timeZone: 'Asia/Kolkata',
                      }) + ' IST'
                    : 'Connecting...'}
                </span>
              </>
            )}
          </div>
        </div>
      </header>

      {/* 2. MAP WORKSPACE */}
      <div className="map-workspace">
        <DelhiMap
          flowState={mapFlow}
          routeResult={mode === 'LIVE' ? routeResult : null}
          routePicks={routePicks}
          pickTarget={mode === 'LIVE' ? routePick : null}
          onMapClick={handleMapClick}
          drainageGraph={drainageGraph}
          surfaceHotspots={surfaceHotspots}
          depthCells={mode !== 'LIVE' ? depthCells : []}
          depthPolygons={
            mode === 'LIVE'
              ? activeHorizonState?.depth_polygons ?? null
              : mode === 'SCENARIO'
                ? scenarioState?.depth_polygons ?? null
                : depthPolygons
          }
          scenarioRoadDepths={mode === 'SCENARIO' ? scenarioRoadDepths : null}
          streetRisk={
            mode === 'LIVE'
              ? activeHorizonState?.streets ?? null
              : mode === 'SCENARIO'
                ? scenarioState?.streets ?? null
                : null
          }
        />

        {/* LEFT WORKSPACE OVERLAY: V1 control stack */}
        <div className={`map-left-overlay delhi-overlay ${mobileDrawerExpanded ? 'drawer-expanded' : 'drawer-collapsed'}`}>
          {/* Mobile Drawer Handle / Sticky Header */}
          <div
            className="drawer-handle-bar"
            onClick={() => setMobileDrawerExpanded(prev => !prev)}
            role="button"
            tabIndex={0}
            aria-expanded={mobileDrawerExpanded}
            aria-label={mobileDrawerExpanded ? 'Collapse dashboard insights drawer' : 'Expand dashboard insights drawer'}
            onKeyDown={(e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                setMobileDrawerExpanded(prev => !prev);
              }
            }}
          >
            <div className="drawer-pill-handle" />
            <div className="drawer-title-row">
              <span className="drawer-summary-text">
                <span className="drawer-risk-dot" style={{ backgroundColor: banner.border || '#0284c7' }} />
                {banner.text} • {maxDepthM !== null ? `${maxDepthM.toFixed(2)}m` : '0.00m'} Peak
              </span>
              <span className="drawer-toggle-btn">
                {mobileDrawerExpanded ? 'Collapse ▾' : 'Insights ▴'}
              </span>
            </div>
          </div>
          <div className="delhi-panel-scroll">
          {/* CONTROL CARD (V1): mode switcher + outlook controls in ONE card */}
          <div className="flood-timeline-panel">
            <div className="mode-toggle-group">
            <button
              type="button"
              className={`mode-toggle-btn ${mode === 'LIVE' ? 'active' : ''}`}
              onClick={() => switchMode('LIVE')}
            >
              LIVE FORECAST
            </button>
            <button
              type="button"
              className={`mode-toggle-btn ${mode === 'SCENARIO' ? 'scenario-active' : ''}`}
              onClick={() => switchMode('SCENARIO')}
            >
              MODEL SCENARIO
            </button>
            <button
              type="button"
              className={`mode-toggle-btn ${mode === 'REPLAY' ? 'historical-active' : ''}`}
              onClick={() => switchMode('REPLAY')}
            >
              HISTORICAL REPLAY
            </button>
            </div>

            {/* FORECAST / SCENARIO TIMELINE (V1 horizon stepper) */}
            {mode === 'LIVE' && (
              <>
                <div className="timeline-header">
                  <span className="timeline-heading">FLOOD OUTLOOK</span>
                  <span className="timeline-active-tag">
                    Active: {horizon}
                    {syntheticFallback ? ' · SYNTHETIC FALLBACK' : ''}
                  </span>
                </div>
                <div className="timeline-stepper">
                  {HORIZONS.map((h) => {
                    const hs = liveState?.horizons.find((x) => x.horizon === h);
                    const rain = hs?.rainfall_mm;
                    const rainTag =
                      rain !== null && rain !== undefined
                        ? `${rain.toFixed(1)}mm`
                        : hs
                          ? '--mm'
                          : '…';
                    return (
                      <button
                        key={h}
                        type="button"
                        className={`timeline-step-btn ${horizon === h ? 'selected' : ''}`}
                        onClick={() => setHorizon(h)}
                      >
                        <span className="step-time">{h}</span>
                        <span className="step-rain-tag">{rainTag}</span>
                      </button>
                    );
                  })}
                </div>
                {liveLoading && <div className="delhi-note">Acquiring forecast and evaluating horizons…</div>}
                {liveError && (
                  <div className="delhi-panel-error route-error">
                    {liveError}{' '}
                    <button className="delhi-btn" onClick={() => loadLive(true)}>
                      Retry
                    </button>
                  </div>
                )}
                {syntheticFallback && (
                  <div className="scenario-explanatory-note" style={{ color: '#b45309' }}>
                    Live NWP forecast unavailable — running the labeled SYNTHETIC_FALLBACK demo rainfall
                    series. Not observed, not a forecast.
                  </div>
                )}
              </>
            )}

            {mode === 'SCENARIO' && (
              <>
                <div className="timeline-header">
                  <span className="timeline-heading" style={{ color: '#0369a1' }}>
                    MODEL SCENARIO (WHAT-IF)
                  </span>
                  <span className="timeline-active-tag" style={{ background: '#e0f2fe', color: '#0369a1' }}>
                    {scenarioMm} mm/h uniform
                  </span>
                </div>
                <div className="scenario-direct-row">
                  <span className="direct-label">INTENSITY:</span>
                  <div className="direct-buttons">
                    {SCENARIO_PRESETS.map((sc) => (
                      <button
                        key={sc}
                        type="button"
                        className={`scenario-rate-pill ${scenarioMm === sc ? 'active' : ''}`}
                        onClick={() => setScenarioMm(sc)}
                        title={`Evaluate ${sc} mm/h through the modelled pipeline`}
                      >
                        {sc} mm/h
                      </button>
                    ))}
                  </div>
                </div>
                {scenarioLoading && <div className="delhi-note">Evaluating scenario through the modelled pipeline…</div>}
                <div className="scenario-explanatory-note">
                  WHAT-IF: hypothetical uniform rainfall evaluated by real backend computation — not live
                  weather, not a forecast.
                </div>
              </>
            )}
          </div>

            {/* MAP EXTENT CONTROLS (V1: inside the left stack) */}
            <div className="map-extent-tools">
              <button
                type="button"
                className="extent-btn"
                onClick={() =>
                  (window as any).map?.flyTo({ center: [77.2265, 28.5595], zoom: 11.6, duration: 900 })
                }
                title="Reset to the full Delhi region"
              >
                FULL EXTENT · DELHI
              </button>
              <button
                type="button"
                className="extent-btn highlight"
                onClick={() =>
                  (window as any).map?.flyTo({ center: [77.2265, 28.5595], zoom: 13.6, duration: 900 })
                }
                title="Center on the Kushak-Barapullah corridor window"
              >
                TARGET ZONE · KUSHAK
              </button>
              <button
                type="button"
                className={`extent-btn routing-btn ${mode === 'LIVE' && routeHudOpen ? 'active' : ''}`}
                onClick={() => {
                  if (mode !== 'LIVE') switchMode('LIVE');
                  setRouteHudOpen((open) => {
                    const next = mode === 'LIVE' ? !open : true;
                    if (next) {
                      setMobileDrawerExpanded(false);
                      if (!routePicks.origin) {
                        setRoutePick('origin');
                      } else if (!routePicks.destination) {
                        setRoutePick('destination');
                      }
                    } else {
                      handleExitRouting();
                    }
                    return next;
                  });
                }}
                title="Toggle Flood-Safe Route Finder (click map origin & destination)"
              >
                SAFE ROUTE {mode === 'LIVE' && routeHudOpen ? '●' : ''}
              </button>
            </div>

            {/* HERO RISK CARD (V1 peak-depth summary) — LIVE & SCENARIO */}
            {(mode === 'LIVE' || mode === 'SCENARIO') && (
              <div className="flood-status-panel">
                <div className="status-panel-top">
                  <div className="status-horizon-kicker text-xs font-medium uppercase tracking-widest text-gray-500">
                    {mode === 'LIVE' ? 'PREDICTED CONDITIONS' : 'SCENARIO RISK'}
                  </div>
                  <div className="status-horizon-title text-xl font-bold tracking-tight">
                    {mode === 'LIVE'
                      ? HORIZON_TITLES[horizon]
                      : `What-If: ${scenarioMm} mm/h`}
                  </div>
                </div>
                <div
                  className="status-hero-card"
                  style={{ backgroundColor: banner.bg, borderColor: banner.border }}
                >
                  <div className="hero-risk-header">
                    <span className="hero-risk-kicker" style={{ color: banner.color }}>
                      {mode === 'LIVE' ? 'PREDICTED RISK' : 'SCENARIO RISK'}
                    </span>
                    <span className="hero-risk-badge" style={{ background: banner.color, color: '#fff' }}>
                      {banner.text}
                    </span>
                  </div>
                  <div className="hero-depth-row">
                    <div className="depth-digit-group">
                      <span className="depth-large" style={{ color: banner.color }}>
                        {maxDepthM === null ? '--' : maxDepthM.toFixed(2)}
                      </span>
                      <span className="depth-metric-unit">m</span>
                    </div>
                    <div className="depth-context-label">
                      <div className="context-primary">Peak Inundation</div>
                      <div className="context-secondary">
                        {maxDepthM === null ? 'depth unknown' : `${Math.round(maxDepthM * 100)} cm depth`}
                      </div>
                    </div>
                  </div>
                  <div className="hero-impact-note" style={{ color: banner.color }}>
                    {banner.desc}
                  </div>
                </div>
                <div className="status-metric-grid grid grid-cols-2 gap-4 mt-4">
                  <div className="grid-metric-box bg-gray-50 p-3 rounded-md">
                    <span className="metric-box-label text-xs font-semibold uppercase tracking-wider text-gray-500">
                      {rainfallMetricLabel}
                    </span>
                    <span className="metric-box-val block text-2xl font-bold tracking-tight">
                      {rainfallMetricVal} <span className="sub-unit text-sm font-medium text-gray-400">mm</span>
                    </span>
                    <span className="metric-box-sub block text-xs font-normal text-gray-600">
                      {rainfallMetricSub}
                    </span>
                  </div>
                  <div className="grid-metric-box bg-gray-50 p-3 rounded-md">
                    <span className="metric-box-label text-xs font-semibold uppercase tracking-wider text-gray-500">
                      INUNDATED AREA
                    </span>
                    <span className="metric-box-val block text-2xl font-bold tracking-tight">
                      {floodedAreaM2 === null ? '--' : Math.round(floodedAreaM2).toLocaleString()}{' '}
                      <span className="sub-unit text-sm font-medium text-gray-400">m²</span>
                    </span>
                    <span className="metric-box-sub block text-xs font-normal text-gray-600">30m DEM grid</span>
                  </div>
                </div>
                <div className="status-panel-footer">
                  <div className="footer-engine-title text-sm font-semibold uppercase tracking-wider text-gray-700">
                    MODEL PIPELINE
                  </div>
                  <div className="footer-engine-desc text-xs font-normal text-gray-500 mb-2">
                    Rainfall–runoff + inlet conveyance + surface routing (V1 reference model)
                  </div>
                  <div className="footer-engine-param text-xs font-medium text-gray-600 bg-gray-100 p-2 rounded">
                    Runoff C = 0.75 • 60-minute horizon step • SIMULATED MODEL OUTPUT
                  </div>
                </div>
              </div>
            )}

            {/* MODE PANELS */}
            {evidenceOpen ? (
              <>
                <EvidencePanel />
                <ModelPanel />
              </>
            ) : mode === 'LIVE' && (
              <>
                <LivePanel
                  liveState={liveState}
                  horizon={horizon}
                  onSurfaceHotspots={setSurfaceHotspots}
                />
                {streets && (
                  <StreetIntelCard streets={streets} modeLabel={mode} />
                )}
                <RoutePanel
                  onMapState={setMapFlow}
                  pickTarget={routePick}
                  setPickTarget={setRoutePick}
                  picks={routePicks}
                  setPicks={setRoutePicks}
                  routeResult={routeResult}
                  setRouteResult={setRouteResult}
                />
              </>
            )}
            {evidenceOpen && mode !== 'LIVE' && (
              <div className="delhi-note" style={{ padding: '0 4px' }}>
                Evidence surfaces are shown alongside the map. Switch to LIVE FORECAST for the operational
                view, or return to SCENARIO/REPLAY panels.
              </div>
            )}
            {!evidenceOpen && mode === 'SCENARIO' && (
              <>
                {streets && <StreetIntelCard streets={streets} modeLabel="SCENARIO" />}
                <ScenarioPanel
                  onMapState={setMapFlow}
                  onSurfaceHotspots={setSurfaceHotspots}
                  onDepthCells={setDepthCells}
                  onDepthPolygons={setDepthPolygons}
                  onRoadDepths={setScenarioRoadDepths}
                />
              </>
            )}
            {!evidenceOpen && mode === 'REPLAY' && (
              <ReplayPanel
                onMapState={setMapFlow}
                onDepthCells={setDepthCells}
                onDepthPolygons={setDepthPolygons}
              />
            )}

            {/* PROVENANCE CARD (V1 data status & provenance — inside the left stack) */}
            <ProvenanceCard
              mode={mode}
              syntheticFallback={syntheticFallback}
              rainfallStatus={liveState?.rainfall_status ?? null}
              acquiredAt={liveState?.rainfall_acquired_at ?? null}
            />
          </div>
        </div>

        {/* SAFE-ROUTE HUD (V1 floating panel; LIVE mode) */}
        {mode === 'LIVE' && routeHudOpen && (
          <SafeRouteHud
            picks={routePicks}
            routeResult={routeResult}
            pickTarget={routePick}
            loading={routeLoading}
            error={routeError}
            onExit={handleExitRouting}
            onPick={(t) => setRoutePick(t)}
            onPreset={(o, d) => {
              setRoutePicks({ origin: { coords: o }, destination: { coords: d } });
              setRoutePick(null);
              void fetchSafeRoute(o, d);
            }}
            onRetry={() => {
              if (routePicks.origin && routePicks.destination) {
                void fetchSafeRoute(routePicks.origin.coords, routePicks.destination.coords);
              }
            }}
          />
        )}
        {/* FLOOD DEPTH LEGEND (V1, always visible) */}
        <div className="flood-legend-card">
          <div className="legend-heading">Modelled flood depth</div>
          <div className="legend-scale">
            {DEPTH_LEGEND.map((g) => (
              <div className="legend-grade" key={g.range}>
                <span className="grade-color" style={{ backgroundColor: g.color }} />
                <span className="grade-range">{g.range}</span>
                <span className="grade-desc">{g.desc}</span>
              </div>
            ))}
          </div>
        </div>

      </div>
    </div>
  );
};

/* ------------------------------------------------------------------ */
/* STREET & INTERSECTION INTELLIGENCE (V1 panel)                       */
/* ------------------------------------------------------------------ */

type StreetsSummary = NonNullable<
  LiveStateResponse['horizons'][number]['streets']
>['summary'];
type AffectedRoad = NonNullable<
  LiveStateResponse['horizons'][number]['streets']
>['affected_roads'][number];

const StreetIntelCard = ({
  streets,
  modeLabel,
}: {
  streets: {
    summary: StreetsSummary;
    affected_roads: AffectedRoad[];
    provenance: Record<string, string>;
  };
  modeLabel: 'LIVE' | 'SCENARIO';
}) => {
  const s = streets.summary;
  return (
    <div className="street-intelligence-panel">
      <div className="street-panel-header">
        <div className="street-header-title">
          <span className="street-title-icon">🛣️</span>{' '}
          {modeLabel === 'LIVE' ? 'STREET FLOOD RISK' : 'SCENARIO STREET RISK'}
        </div>
        <span className="prov-tag tag-modelled" style={{ fontSize: '9px', padding: '2px 6px', background: '#fef3c7', color: '#92400e' }}>
          Modelled (V1 depth grid)
        </span>
      </div>
      {s.total_affected_roads > 0 || s.total_affected_intersections > 0 ? (
        <>
          <div className="street-impact-summary">
            <div className="impact-count-badge">
              <span className="count-num">{s.total_affected_roads}</span>
              <span className="count-lbl">Streets</span>
            </div>
            <div className="impact-count-badge">
              <span className="count-num">{s.total_affected_intersections}</span>
              <span className="count-lbl">Junctions</span>
            </div>
            <div className="impact-depth-badge">
              <span className="depth-lbl">Peak Street Depth</span>
              <span className="depth-val">{s.max_street_depth_m.toFixed(2)} m</span>
            </div>
          </div>
          <div className="street-risk-pills">
            {s.risk_counts.CRITICAL > 0 && <span className="risk-pill critical">{s.risk_counts.CRITICAL} Critical</span>}
            {s.risk_counts.HIGH > 0 && <span className="risk-pill high">{s.risk_counts.HIGH} High</span>}
            {s.risk_counts.MEDIUM > 0 && <span className="risk-pill medium">{s.risk_counts.MEDIUM} Moderate</span>}
            {s.risk_counts.LOW > 0 && <span className="risk-pill low">{s.risk_counts.LOW} Low</span>}
          </div>
          <div className="street-affected-list">
            <div className="list-title">KEY IMPACTED CORRIDORS</div>
            {streets.affected_roads.slice(0, 3).map((r, i) => (
              <div key={`${r.road_id}-${i}`} className="affected-street-item">
                <div className="street-item-left">
                  <span className="street-item-name">{r.name}</span>
                  <span className="street-item-sub">
                    {r.highway} • {r.flooded_length_m}m flooded
                  </span>
                </div>
                <div className="street-item-right">
                  <span className={`street-risk-tag risk-${r.risk_level.toLowerCase()}`}>{r.risk_level}</span>
                  <span className="street-depth-tag">{r.max_depth_m.toFixed(2)}m</span>
                </div>
              </div>
            ))}
          </div>
        </>
      ) : (
        <div className="street-safe-state">
          <span className="safe-icon">✅</span>
          <div className="safe-text">
            <div className="safe-title">All Arterial Streets Passable</div>
            <div className="safe-sub">Zero surface ponding modelled on OSM street corridors</div>
          </div>
        </div>
      )}
      <div className="street-panel-provenance">
        OSM roads/junctions matched to the modelled depth grid • Not municipal road sensors • UNKNOWN
        beyond the match distance, never 0 m
      </div>
    </div>
  );
};

/* ------------------------------------------------------------------ */
/* SAFE-ROUTE HUD (V1 floating panel)                                  */
/* ------------------------------------------------------------------ */

const SafeRouteHud = ({
  picks,
  routeResult,
  pickTarget,
  loading,
  error,
  onExit,
  onPick,
  onPreset,
  onRetry,
}: {
  picks: { origin: RoutePickPoint | null; destination: RoutePickPoint | null };
  routeResult: SafeRouteResponse | null;
  pickTarget: 'origin' | 'destination' | null;
  loading: boolean;
  error: string | null;
  onExit: () => void;
  onPick: (t: 'origin' | 'destination') => void;
  onPreset: (o: [number, number], d: [number, number]) => void;
  onRetry: () => void;
}) => {
  const rec = routeResult?.recommended_route;
  return (
    <div className="safe-route-hud-panel">
      <div className="route-hud-header">
        <div className="route-hud-title-group">
          <span className="route-hud-icon">R</span>
          <span className="route-hud-title">FLOOD-SAFE ROUTE</span>
        </div>
        <div className="route-hud-actions">
          {rec && (
            <span className="route-status-badge status-safe">
              EVALUATED
            </span>
          )}
          <button type="button" className="route-close-btn" onClick={onExit} title="Exit safe routing">
            ✕
          </button>
        </div>
      </div>
      <div className="route-step-banner">
        {loading ? (
          <div className="step-prompt loading">
            <span className="route-loading-spinner" />
            <span>Computing flood-safe route along corridor…</span>
          </div>
        ) : !picks.origin ? (
          <div className="step-prompt">
            <span className="step-pin origin-pin">📍</span>
            <span>
              Click map to place <strong>Origin</strong>
            </span>
          </div>
        ) : !picks.destination ? (
          <div className="step-prompt">
            <span className="step-pin dest-pin">END</span>
            <span>
              Origin set. Click map for <strong>Destination</strong>
            </span>
          </div>
        ) : (
          <div className="step-locations">
            <button
              type="button"
              className={`loc-item clickable ${pickTarget === 'origin' ? 'picking' : ''}`}
              onClick={() => onPick('origin')}
              title="Click to re-pick origin on map"
            >
              <span className="loc-dot origin" />
              <span className="loc-text">
                {routeResult?.origin.snapped_road ||
                  `${picks.origin.coords[1].toFixed(4)}, ${picks.origin.coords[0].toFixed(4)}`}
              </span>
              <span className="loc-pick-hint">{pickTarget === 'origin' ? 'PICKING…' : 'CHANGE'}</span>
            </button>
            <div className="loc-arrow">↓</div>
            <button
              type="button"
              className={`loc-item clickable ${pickTarget === 'destination' ? 'picking' : ''}`}
              onClick={() => onPick('destination')}
              title="Click to re-pick destination on map"
            >
              <span className="loc-dot dest" />
              <span className="loc-text">
                {routeResult?.destination.snapped_road ||
                  `${picks.destination.coords[1].toFixed(4)}, ${picks.destination.coords[0].toFixed(4)}`}
              </span>
              <span className="loc-pick-hint">{pickTarget === 'destination' ? 'PICKING…' : 'CHANGE'}</span>
            </button>
          </div>
        )}
      </div>

      {error && !loading && (
        <div className="route-error-banner">
          <span>{error}</span>
          <button type="button" className="delhi-btn route-retry-btn" onClick={onRetry}>
            Retry
          </button>
        </div>
      )}

      <div className="route-presets-section">
        <div className="presets-label">
          {pickTarget ? `CLICK MAP TO PLACE ${pickTarget.toUpperCase()}` : 'OR CHOOSE CORRIDOR PRESET:'}
        </div>
        <div className="presets-buttons">
          <button
            type="button"
            className="preset-btn"
            onClick={() => onPreset([77.2055, 28.5685], [77.2435, 28.5715])}
            title="Africa Avenue (UG-01) to Corridor East preset"
          >
            Africa Ave → East
          </button>
          <button
            type="button"
            className="preset-btn"
            onClick={() => onPreset([77.2260, 28.5480], [77.2440, 28.5620])}
            title="Corridor South to Barapullah Junction preset"
          >
            South → Barapullah
          </button>
        </div>
      </div>
      {rec && (
        <>
          <div className="route-metrics-grid">
            <div className="route-metric-card">
              <span className="m-label">ROUTE DISTANCE</span>
              <span className="m-val">
                {rec.total_distance_km} <span className="m-unit">km</span>
              </span>
              <span className="m-sub">{rec.estimated_travel_time_min} min est.</span>
            </div>
            <div className="route-metric-card">
              <span className="m-label">ELEVATED-RISK</span>
              <span className={`m-val ${rec.flood_risk_summary.elevated_risk_segments > 0 ? 'highlight-danger' : ''}`}>
                {rec.flood_risk_summary.elevated_risk_segments}
              </span>
              <span className="m-sub">segments with modeled loading</span>
            </div>
            <div className="route-metric-card">
              <span className="m-label">UNKNOWN</span>
              <span className="m-val">{rec.flood_risk_summary.unknown_segments}</span>
              <span className="m-sub">no model coverage (not safe)</span>
            </div>
            <div className="route-metric-card">
              <span className="m-label">EVIDENCE</span>
              <span className="m-val">{routeResult?.evidence_state.route_state}</span>
              <span className="m-sub">weakest-link state</span>
            </div>
          </div>
          {routeResult?.explanation?.length ? (
            <div className="route-comparison-note">{routeResult.explanation[0]}</div>
          ) : null}
          <div className="route-unavailable-warning">
            LOW MODELED EXPOSURE ≠ SAFE: stage/depth remain UNKNOWN on the Kushak corridor. See the route
            panel for the full evidence trail.
          </div>
        </>
      )}
      <div className="route-hud-footer">
        <button type="button" className="route-clear-btn" onClick={onExit}>
          Exit Routing
        </button>
        <button
          type="button"
          className={`route-pick-btn ${pickTarget === 'origin' ? 'active' : ''}`}
          onClick={() => onPick('origin')}
        >
          {pickTarget === 'origin' ? '● Picking Origin' : 'Pick Origin'}
        </button>
        <button
          type="button"
          className={`route-pick-btn ${pickTarget === 'destination' ? 'active' : ''}`}
          onClick={() => onPick('destination')}
        >
          {pickTarget === 'destination' ? '● Picking Dest' : 'Pick Dest'}
        </button>
      </div>
    </div>
  );
};

/* ------------------------------------------------------------------ */
/* PROVENANCE CARD (V1 data status & provenance)                       */
/* ------------------------------------------------------------------ */

const ProvenanceCard = ({
  mode,
  syntheticFallback,
  rainfallStatus,
  acquiredAt,
}: {
  mode: Mode;
  syntheticFallback: boolean;
  rainfallStatus: string | null;
  acquiredAt: string | null;
}) => (
  <div className="provenance-card">
    <div className="provenance-header">
      {mode === 'REPLAY'
        ? 'HISTORICAL DATA PROVENANCE'
        : mode === 'SCENARIO'
          ? 'SCENARIO PROVENANCE & STATUS'
          : 'DATA PROVENANCE & STATUS'}
    </div>
    <div className="provenance-list">
      <div className="provenance-item">
        <span className="prov-source">Rainfall</span>
        <span
          className="prov-tag tag-modelled"
          style={
            syntheticFallback
              ? { background: '#7c2d12', color: '#fed7aa' }
              : mode === 'SCENARIO'
                ? { background: '#e0f2fe', color: '#0369a1' }
                : undefined
          }
        >
          {mode === 'SCENARIO'
            ? 'MODEL_SCENARIO (hypothetical)'
            : syntheticFallback
              ? 'SYNTHETIC_FALLBACK (demo)'
              : `Open-Meteo NWP (${rainfallStatus ?? '…'})`}
        </span>
      </div>
      <div className="provenance-item">
        <span className="prov-source">Elevation</span>
        <span className="prov-tag tag-modelled">Copernicus GLO-30 DSM (30m, enforced)</span>
      </div>
      <div className="provenance-item">
        <span className="prov-source">Flood depth</span>
        <span className="prov-tag tag-modelled">
          {mode === 'REPLAY' ? 'SIMULATED (event replay)' : 'MODELLED (V1 reference)'}
        </span>
      </div>
      <div className="provenance-item">
        <span className="prov-source">Roads / junctions</span>
        <span className="prov-tag tag-modelled">OpenStreetMap (ODbL) + model matching</span>
      </div>
      <div className="provenance-item">
        <span className="prov-source">Drainage</span>
        <span className="prov-tag tag-modelled">DERIVED / INFERRED_EFFECTIVE (not as-built)</span>
      </div>
      <div className="provenance-item">
        <span className="prov-source">Observations</span>
        <span className="prov-tag tag-prototype">OBSERVED (GSDL events) — validation only</span>
      </div>
    </div>
    <div className="provenance-disclaimer">
      {mode === 'REPLAY'
        ? 'RETROSPECTIVE EVENT REPLAY: model execution against documented events. Never observed depth; observed evidence is labeled separately.'
        : mode === 'SCENARIO'
          ? 'WHAT-IF: hypothetical uniform rainfall through the modelled pipeline. Not live weather, not a forecast.'
          : syntheticFallback
            ? 'SYNTHETIC FALLBACK ACTIVE: the live NWP forecast is unavailable; a deterministic labeled demo series keeps the system usable. These are NOT observed measurements.'
            : 'Weather forecast from Open-Meteo hourly NWP (model value, not observed rainfall). Flood depth is MODELLED on a 30 m DSM — never observed.'}
      {acquiredAt && mode === 'LIVE' && !syntheticFallback
        ? ` Forecast acquired ${new Date(acquiredAt).toLocaleTimeString()}.`
        : ''}
    </div>
  </div>
);

export default DelhiApp;
