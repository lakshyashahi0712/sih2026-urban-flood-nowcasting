import { useEffect, useMemo, useState } from 'react';
import {
  delhiApi,
  type EventReplayResponse,
  type EventsResponse,
  type SafeRouteResponse,
  type SegmentEvidence,
} from '../../api/delhi';
import type { MapFlowState } from './DelhiMap';

type PickTarget = 'origin' | 'destination' | null;

interface PickPoint {
  coords: [number, number];
  label?: string;
}

const RoutePanel = ({
  onMapState,
  pickTarget,
  setPickTarget,
  picks,
  setPicks,
  routeResult,
  setRouteResult,
}: {
  onMapState: (s: MapFlowState) => void;
  pickTarget: PickTarget;
  setPickTarget: (t: PickTarget) => void;
  picks: { origin: PickPoint | null; destination: PickPoint | null };
  setPicks: React.Dispatch<React.SetStateAction<{ origin: PickPoint | null; destination: PickPoint | null }>>;
  routeResult: SafeRouteResponse | null;
  setRouteResult: (r: SafeRouteResponse | null) => void;
}) => {
  // setPicks is available for future inline-edit workflows; the panel
  // currently sets picks via the map click handler in DelhiApp.
  void setPicks;
  const [mode, setMode] = useState<'live' | 'historical'>('live');
  const [departureHour, setDepartureHour] = useState(0);
  const [events, setEvents] = useState<EventsResponse | null>(null);
  const [eventId, setEventId] = useState<string>('EVT-2024-06-27');
  const [timestepIndex, setTimestepIndex] = useState(0);
  const [replay, setReplay] = useState<EventReplayResponse | null>(null);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [segmentEvidence, setSegmentEvidence] = useState<SegmentEvidence | null>(null);

  useEffect(() => {
    delhiApi.getEvents().then(setEvents).catch(() => setEvents(null));
  }, []);

  // Historical timestep metadata from the (server-cached) replay detail.
  useEffect(() => {
    if (mode !== 'historical') return;
    setReplay(null);
    setTimestepIndex(0);
    delhiApi
      .getEventReplay(eventId)
      .then(setReplay)
      .catch(() => setReplay(null));
  }, [mode, eventId]);

  // Push route layers to the map; clear model-state overlays while routing.
  useEffect(() => {
    onMapState({ reachStates: {}, timestamp: null, rainIntensityMmH: null, rainKnown: false });
  }, [onMapState]);

  const nTimesteps = replay?.members?.[0]?.inflow_steps.length ?? 0;
  const timestepTimes = replay?.members?.[0]?.inflow_steps.map((s) => s.time) ?? [];

  const canRun =
    picks.origin !== null &&
    picks.destination !== null &&
    (mode === 'live' || (eventId && replay?.runtime_status !== 'NOT_EXECUTED'));

  const runRoute = async () => {
    if (!picks.origin || !picks.destination) return;
    setRunning(true);
    setError(null);
    setSegmentEvidence(null);
    try {
      const res = await delhiApi.getSafeRoute({
        origin: picks.origin.coords,
        destination: picks.destination.coords,
        mode,
        departure_hour: mode === 'live' ? departureHour : 0,
        event_id: mode === 'historical' ? eventId : undefined,
        timestep_index: mode === 'historical' ? timestepIndex : 0,
      });
      setRouteResult(res);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'routing failed';
      setError(message);
      setRouteResult(null);
    } finally {
      setRunning(false);
    }
  };

  const selectSegment = async (segmentId: string) => {
    if (!routeResult) return;
    try {
      const ev = await delhiApi.getSegmentEvidence(segmentId, {
        mode,
        departure_hour: mode === 'live' ? departureHour : 0,
        event_id: mode === 'historical' ? eventId : undefined,
        timestep_index: mode === 'historical' ? timestepIndex : 0,
      });
      setSegmentEvidence(ev);
    } catch {
      setSegmentEvidence(null);
    }
  };

  // Map risk segments of the recommended route for click-through.
  const riskFeatures = useMemo(
    () => routeResult?.recommended_route?.risk_segments?.features ?? [],
    [routeResult],
  );

  const fmtTime = (iso: string) =>
    new Date(iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

  return (
    <div className="delhi-route">
      {/* Mode */}
      <div className="delhi-section flood-timeline-panel">
        <div className="delhi-section-head timeline-header timeline-header">
          <span className="delhi-section-title timeline-heading timeline-heading">FLOOD-AWARE ROUTING</span>
          <span className="delhi-section-hint">one engine, two state sources</span>
        </div>
        <div className="route-mode-row">
          <button
            className={`delhi-btn ${mode === 'live' ? 'delhi-btn-primary' : ''}`}
            onClick={() => setMode('live')}
          >
            LIVE NOWCAST
          </button>
          <button
            className={`delhi-btn ${mode === 'historical' ? 'delhi-btn-primary' : ''}`}
            onClick={() => setMode('historical')}
          >
            HISTORICAL REPLAY
          </button>
        </div>

        {mode === 'live' ? (
          <div className="route-controls">
            <span className="meta-k">Departure hour (forecast)</span>
            <div className="route-hour-row">
              {[0, 1, 2, 3].map((h) => (
                <button
                  key={h}
                  className={`delhi-btn ${departureHour === h ? 'delhi-btn-primary' : ''}`}
                  onClick={() => setDepartureHour(h)}
                >
                  t+{h}h
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className="route-controls">
            <span className="meta-k">Historical event</span>
            <select
              className="route-select"
              value={eventId}
              onChange={(e) => setEventId(e.target.value)}
            >
              {events?.events
                .filter((ev) => ev.replay_status === 'EXECUTABLE' || ev.replay_status === 'PARTIAL')
                .map((ev) => (
                  <option key={ev.event_id} value={ev.event_id}>
                    {ev.event_id} ({ev.replay_status})
                  </option>
                ))}
            </select>
            {replay && replay.runtime_status !== 'NOT_EXECUTED' ? (
              <>
                <span className="meta-k">
                  Timestep {timestepIndex + 1}/{nTimesteps}
                </span>
                <input
                  type="range"
                  min={0}
                  max={Math.max(nTimesteps - 1, 0)}
                  value={timestepIndex}
                  onChange={(e) => setTimestepIndex(Number(e.target.value))}
                  className="route-slider"
                />
                <span className="transport-time mono">
                  {timestepTimes[timestepIndex]
                    ? `${fmtTime(timestepTimes[timestepIndex])} IST`
                    : '—'}
                </span>
              </>
            ) : (
              <div className="delhi-note">
                This event has no executable forcing — historical routing is
                NOT_COMPUTABLE for it.
              </div>
            )}
          </div>
        )}

        {/* Origin / destination */}
        <div className="route-points">
          <button
            className={`route-point-btn ${pickTarget === 'origin' ? 'picking' : ''}`}
            onClick={() => setPickTarget(pickTarget === 'origin' ? null : 'origin')}
          >
            <span className="meta-k">ORIGIN</span>
            <span className="meta-v">
              {picks.origin
                ? `${picks.origin.coords[1].toFixed(4)}, ${picks.origin.coords[0].toFixed(4)}`
                : 'click SET, then the map'}
            </span>
          </button>
          <button
            className={`route-point-btn ${pickTarget === 'destination' ? 'picking' : ''}`}
            onClick={() =>
              setPickTarget(pickTarget === 'destination' ? null : 'destination')
            }
          >
            <span className="meta-k">DESTINATION</span>
            <span className="meta-v">
              {picks.destination
                ? `${picks.destination.coords[1].toFixed(4)}, ${picks.destination.coords[0].toFixed(4)}`
                : 'click SET, then the map'}
            </span>
          </button>
        </div>

        <button
          className="delhi-btn delhi-btn-primary route-run-btn"
          disabled={!canRun || running}
          onClick={runRoute}
        >
          {running ? 'Computing…' : 'Find route'}
        </button>
        {error && <div className="delhi-panel-error route-error">{error}</div>}
        <div className="delhi-note">
          Pick origin and destination on the map, then compute. The result is
          the lowest supported MODELED flood exposure under the active
          evidence — never a guarantee of safety.
        </div>
      </div>

      {routeResult && !running && (
        <>
          {/* Recommended / alternative */}
          <div className="delhi-section flood-timeline-panel">
            <div className="delhi-section-head timeline-header timeline-header">
              <span className="delhi-section-title timeline-heading timeline-heading">RECOMMENDED ROUTE</span>
              <span className="delhi-prov-tag prov-computed">
                {routeResult.recommended_route.route_state}
              </span>
            </div>
            <div className="route-stat-row">
              <div className="route-stat">
                <span className="stat-value">
                  {routeResult.recommended_route.total_distance_km} km
                </span>
                <span className="stat-label">distance</span>
              </div>
              <div className="route-stat">
                <span className="stat-value">
                  {routeResult.recommended_route.estimated_travel_time_min} min
                </span>
                <span className="stat-label">est. travel time (ASSUMED speeds)</span>
              </div>
              <div className="route-stat">
                <span className={`stat-value ev-${routeResult.evidence_state.route_state.toLowerCase()}`}>
                  {routeResult.evidence_state.route_state}
                </span>
                <span className="stat-label">evidence state</span>
              </div>
            </div>
            <div className="route-risk-chips">
              {[
                ['elevated', routeResult.recommended_route.flood_risk_summary.elevated_risk_segments, 'ELEVATED-RISK'],
                ['unknown-chip', routeResult.recommended_route.flood_risk_summary.unknown_segments, 'UNKNOWN'],
                ['low', routeResult.recommended_route.flood_risk_summary.low_risk_segments, 'LOW-RISK'],
                ['blocked', routeResult.recommended_route.flood_risk_summary.blocked_segments, 'BLOCKED'],
              ].map(([cls, count, label]) => (
                <span key={label as string} className={`risk-chip chip-${cls}`}>
                  {count as number} {label as string}
                </span>
              ))}
            </div>
            {routeResult.alternative_route ? (
              <div className="alt-summary">
                <span className="meta-k">ALTERNATIVE (dashed on map)</span>
                <span className="meta-v">
                  {routeResult.alternative_route.total_distance_km} km ·{' '}
                  {routeResult.alternative_route.estimated_travel_time_min} min ·{' '}
                  {routeResult.alternative_route.flood_risk_summary.elevated_risk_segments} elevated ·{' '}
                  {routeResult.alternative_route.flood_risk_summary.unknown_segments} unknown
                </span>
              </div>
            ) : (
              <div className="alt-summary">
                <span className="meta-k">ALTERNATIVE</span>
                <span className="meta-v">{routeResult.no_alternative_reason}</span>
              </div>
            )}
          </div>

          {/* Why this route */}
          <div className="delhi-section flood-timeline-panel">
            <div className="delhi-section-head timeline-header timeline-header">
              <span className="delhi-section-title timeline-heading timeline-heading">WHY THIS ROUTE</span>
              <span className="delhi-prov-tag">STRUCTURED FACTS</span>
            </div>
            <ul className="route-why">
              {routeResult.explanation.map((line, i) => (
                <li key={i}>{line}</li>
              ))}
            </ul>
            <div className="route-compare-table">
              <table className="delhi-table">
                <thead>
                  <tr>
                    <th>Metric</th>
                    <th>Recommended</th>
                    <th>Alternative</th>
                  </tr>
                </thead>
                <tbody>
                  {[
                    ['Distance (km)', 'distance_km'],
                    ['Travel time (min)', 'travel_time_min'],
                    ['ELEVATED segments', 'elevated_risk'],
                    ['UNKNOWN segments', 'unknown'],
                    ['LOW-RISK segments', 'low_risk'],
                  ].map(([label, key]) => (
                    <tr key={key as string}>
                      <td>{label as string}</td>
                      <td className="mono">{String(routeResult.route_comparison.recommended[key as keyof typeof routeResult.route_comparison.recommended])}</td>
                      <td className="mono">
                        {routeResult.route_comparison.alternative
                          ? String(routeResult.route_comparison.alternative[key as keyof NonNullable<typeof routeResult.route_comparison.alternative>])
                          : '—'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Evidence + freshness */}
          <div className="delhi-section flood-timeline-panel">
            <div className="delhi-section-head timeline-header timeline-header">
              <span className="delhi-section-title timeline-heading timeline-heading">ROUTE EVIDENCE</span>
              <span className={`delhi-prov-tag ev-tag-${routeResult.evidence_state.route_state.toLowerCase()}`}>
                {routeResult.evidence_state.route_state}
              </span>
            </div>
            <div className="obs-line">{routeResult.evidence_state.reason}</div>
            <div className="delhi-note">{routeResult.evidence_state.derivation}</div>
            <table className="delhi-table">
              <tbody>
                <tr>
                  <td>Last rainfall / model update</td>
                  <td className="mono">
                    {routeResult.data_freshness.rainfall_updated_at
                      ? new Date(routeResult.data_freshness.rainfall_updated_at).toLocaleString()
                      : 'UNKNOWN'}
                  </td>
                </tr>
                <tr>
                  <td>Model timestep</td>
                  <td className="mono">
                    {routeResult.data_freshness.hydraulic_run_updated_at ?? '—'}
                  </td>
                </tr>
                <tr>
                  <td>Forcing source</td>
                  <td className="mono">{routeResult.provenance.forcing_source}</td>
                </tr>
                <tr>
                  <td>Road network</td>
                  <td className="mono">{routeResult.provenance.road_network_source}</td>
                </tr>
                <tr>
                  <td>Route run id (reproducible)</td>
                  <td className="mono">{routeResult.route_run_id}</td>
                </tr>
                <tr>
                  <td>Mode / event / timestep</td>
                  <td className="mono">
                    {routeResult.mode}
                    {routeResult.event_id ? ` · ${routeResult.event_id}` : ''}
                    {routeResult.timestep_index !== null ? ` · t${routeResult.timestep_index}` : ''}
                  </td>
                </tr>
              </tbody>
            </table>
            <details className="delhi-details">
              <summary>Risk mapping &amp; cost model</summary>
              <div className="obs-line">{routeResult.provenance.risk_mapping_method}</div>
              <div className="obs-line">
                Mapping threshold: {routeResult.provenance.risk_mapping_threshold_m} m (ASSUMED
                engineering constant). Cost weights are documented ASSUMED
                engineering defaults — see the route provenance payload.
              </div>
            </details>
            <div className="delhi-claim-policy">{routeResult.claim_policy}</div>
          </div>

          {/* Risk segments (click for evidence) */}
          {riskFeatures.length > 0 && (
            <div className="delhi-section flood-timeline-panel">
              <div className="delhi-section-head timeline-header timeline-header">
                <span className="delhi-section-title timeline-heading timeline-heading">
                  RISK SEGMENTS ON THE RECOMMENDED ROUTE ({riskFeatures.length})
                </span>
              </div>
              <div className="route-segment-list">
                {riskFeatures.slice(0, 12).map((f) => (
                  <button
                    key={f.properties.segment_id}
                    className={`route-segment-row seg-${f.properties.risk_state.toLowerCase()}`}
                    onClick={() => selectSegment(f.properties.segment_id)}
                  >
                    <span className={`risk-chip chip-${f.properties.risk_state === 'ELEVATED_RISK' ? 'elevated' : 'unknown-chip'}`}>
                      {f.properties.risk_state}
                    </span>
                    <span className="meta-v">{f.properties.name}</span>
                  </button>
                ))}
                {riskFeatures.length > 12 && (
                  <div className="delhi-note">
                    …and {riskFeatures.length - 12} more UNKNOWN segments (click
                    any highlighted segment on the map for its evidence).
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Segment evidence */}
          {segmentEvidence && (
            <div className="delhi-section flood-timeline-panel seg-evidence">
              <div className="delhi-section-head timeline-header timeline-header">
                <span className="delhi-section-title timeline-heading timeline-heading">SEGMENT EVIDENCE</span>
                <span className={`delhi-prov-tag ${segmentEvidence.risk_state === 'UNKNOWN' ? 'prov-unavailable' : 'prov-computed'}`}>
                  {segmentEvidence.risk_state}
                </span>
              </div>
              <table className="delhi-table">
                <tbody>
                  <tr><td>Segment</td><td className="mono">{segmentEvidence.segment_id}</td></tr>
                  <tr><td>Road</td><td>{segmentEvidence.name} ({segmentEvidence.highway})</td></tr>
                  <tr><td>Risk reason</td><td>{segmentEvidence.risk_reason}</td></tr>
                  <tr>
                    <td>Spatial mapping</td>
                    <td>
                      {segmentEvidence.spatial_mapping.method} ·{' '}
                      {segmentEvidence.spatial_mapping.status}
                      {segmentEvidence.spatial_mapping.mapped_reach
                        ? ` · ${segmentEvidence.spatial_mapping.mapped_reach}`
                        : ''}
                    </td>
                  </tr>
                  {segmentEvidence.hydraulic_state && (
                    <tr>
                      <td>Model state</td>
                      <td className="mono">
                        {JSON.stringify(segmentEvidence.hydraulic_state)}
                      </td>
                    </tr>
                  )}
                  <tr><td>Model timestamp</td><td className="mono">{segmentEvidence.model_timestamp ?? 'UNKNOWN'}</td></tr>
                  <tr><td>Forcing</td><td className="mono">{segmentEvidence.forcing_source ?? 'UNKNOWN'}</td></tr>
                  <tr><td>Evidence source</td><td>{segmentEvidence.geometry_source}</td></tr>
                </tbody>
              </table>
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default RoutePanel;
