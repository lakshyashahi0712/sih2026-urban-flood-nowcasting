import { useEffect, useMemo, useState } from 'react';
import {
  delhiApi,
  type ScenarioMeta,
  type ScenarioRunResult,
} from '../../api/delhi';
import type { MapFlowState } from './DelhiMap';

// Synthetic scenario workflow. Everything shown here is SIMULATED:
// numeric depths come from the real runtime pipeline (rainfall -> inflow ->
// chain -> 2D surface pass), never hardcoded frontend values.

type Status = 'idle' | 'running' | 'completed' | 'failed';

const ScenarioPanel = ({
  onMapState,
  onSurfaceHotspots = () => {},
  onDepthCells = () => {},
  onDepthPolygons = () => {},
  onRoadDepths = () => {},
}: {
  onMapState: (s: MapFlowState) => void;
  onSurfaceHotspots?: (
    hotspots: { lon: number; lat: number; surface_water_cm_estimated: number; provenance: string }[],
  ) => void;
  onDepthCells?: (
    cells: { lon: number; lat: number; depth_cm: number; flood_state: string; provenance: string }[],
  ) => void;
  onDepthPolygons?: (polygons: { type: string; features: unknown[] } | null) => void;
  onRoadDepths?: (
    depths: Record<string, { depth_cm: number; depth_m: number; flood_state: string }> | null,
  ) => void;
}) => {
  const [scenarios, setScenarios] = useState<ScenarioMeta[]>([]);
  const [claimPolicy, setClaimPolicy] = useState('');
  const [selected, setSelected] = useState<string>('SCN-03');
  const [result, setResult] = useState<ScenarioRunResult | null>(null);
  const [status, setStatus] = useState<Status>('idle');
  const [error, setError] = useState<string | null>(null);
  const [timestep, setTimestep] = useState(0);
  const [selectedRoad, setSelectedRoad] = useState<string | null>(null);

  useEffect(() => {
    delhiApi
      .scenarioList()
      .then((r) => {
        setScenarios(r.scenarios);
        setClaimPolicy(r.claim_policy);
      })
      .catch(() => setScenarios([]));
  }, []);

  const run = async () => {
    setStatus('running');
    setError(null);
    try {
      const r = await delhiApi.scenarioRun(selected);
      const full = await delhiApi.scenarioResults(selected, r.run_id);
      setResult(full);
      setTimestep(0);
      setSelectedRoad(null);
      setStatus('completed');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'scenario run failed');
      setStatus('failed');
    }
  };

  const currentStep = result?.members?.[0]?.steps[timestep];
  const traj = result?.members?.[0]?.max_depth_cm_traj ?? [];

  // Push map overlays: rain intensity = current areal depth; destination of
  // analytics = the scenario's surface hotspots at this timestep.
  useEffect(() => {
    if (!result || !currentStep) return;
    const depthMm = result.members[0].forcing_depths_mm[timestep] ?? 0;
    onMapState({
      reachStates: {},
      timestamp: currentStep.time_start,
      rainIntensityMmH: depthMm > 0 ? depthMm / (result.timestep_min / 60) : null,
      rainKnown: depthMm > 0,
    });
    onSurfaceHotspots(currentStep.hotspots ?? []);
    onDepthCells(currentStep.depth_cells ?? []);
    onDepthPolygons(currentStep.depth_polygons ?? null);
    onRoadDepths(result.members[0]?.road_depths ?? null);
  }, [result, timestep, currentStep, onMapState, onSurfaceHotspots, onDepthCells, onDepthPolygons, onRoadDepths]);

  useEffect(() => {
    onSurfaceHotspots([]);
    onDepthCells([]);
    onDepthPolygons(null);
    onRoadDepths(null);
  }, [selected, onSurfaceHotspots, onDepthCells, onDepthPolygons, onRoadDepths]);

  const currentMax = currentStep?.max_depth_cm ?? null;
  const currentState = currentStep?.flood_state ?? 'UNKNOWN';
  const selectedRoadDepth = selectedRoad
    ? result?.members?.[0]?.road_depths[selectedRoad]
    : null;
  const roadEntries = useMemo(
    () => Object.entries(result?.members?.[0]?.road_depths ?? {}),
    [result],
  );

  const fmtTime = (iso: string) =>
    new Date(iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

  return (
    <div className="delhi-scenarios">
      {/* Persistent SIMULATED banner */}
      <div className="delhi-banner banner-warn">
        <div className="banner-main">
          <span className="banner-state">SIMULATED SCENARIO MODE</span>
          <span className="banner-sub">
            {claimPolicy || 'Synthetic demonstration — NOT real observations, NOT real-event accuracy.'}
          </span>
        </div>
      </div>

      {/* Scenario selector */}
      <div className="delhi-section flood-timeline-panel">
        <div className="delhi-section-head timeline-header timeline-header">
          <span className="delhi-section-title timeline-heading timeline-heading">SYNTHETIC SCENARIOS</span>
          <span className="delhi-section-hint">deterministic, reproducible</span>
        </div>
        <div className="delhi-event-grid">
          {scenarios.map((s) => (
            <button
              key={s.scenario_id}
              className={`delhi-event-card ${selected === s.scenario_id ? 'selected' : ''}`}
              onClick={() => {
                setSelected(s.scenario_id);
                setResult(null);
                setStatus('idle');
              }}
            >
              <div className="event-id mono">{s.scenario_id}</div>
              <div className="event-window">{s.name}</div>
              <div className="event-tag tag-warn">
                {s.default_demo ? 'DEFAULT DEMO' : s.ensemble_members > 1 ? `${s.ensemble_members}-MEMBER ENSEMBLE` : 'SINGLE'}
              </div>
            </button>
          ))}
        </div>
        <button
          className="delhi-btn delhi-btn-primary route-run-btn"
          disabled={status === 'running'}
          onClick={run}
          style={{ marginTop: 10 }}
        >
          {status === 'running' ? 'Running simulation…' : result ? 'Re-run scenario' : 'Start simulation'}
        </button>
        {status === 'running' && (
          <div className="delhi-panel-status">Executing canonical pipeline (forcing → runoff → chain → 2D surface)…</div>
        )}
        {error && <div className="delhi-panel-error route-error">{error}</div>}
      </div>

      {result && status === 'completed' && currentStep && (
        <>
          {/* FLOOD DEPTH INDICATOR */}
          <div className="delhi-section flood-timeline-panel depth-widget">
            <div className="depth-widget-head">
              <span className="depth-widget-title">MAX FLOOD DEPTH</span>
              <span className={`state-chip state-${currentState.toLowerCase()}`}>{currentState}</span>
            </div>
            <div className="depth-widget-value">
              {currentMax !== null ? `${(currentMax / 100).toFixed(2)} m` : 'UNKNOWN'}
              <span className="depth-widget-cm"> = {currentMax !== null ? `${Math.round(currentMax)} cm` : '—'}</span>
            </div>
            <div className="depth-widget-meta">
              {result.scenario_id} • {fmtTime(currentStep.time_start)} • source: {currentStep.source_type}
            </div>
            {selectedRoadDepth && (
              <div className="depth-widget-selected">
                Selected road {selectedRoad}: {selectedRoadDepth.depth_m.toFixed(2)} m ({selectedRoadDepth.flood_state})
              </div>
            )}
            <div className="depth-widget-scale">
              <i className="lg-route unknown" /> 0 cm · 2 · 10 · 30 · 60+ cm (thresholds from /scenarios/config)
            </div>
          </div>

          {/* Timeline */}
          <div className="delhi-section flood-timeline-panel">
            <div className="delhi-section-head timeline-header timeline-header">
              <span className="delhi-section-title timeline-heading timeline-heading">SIMULATION TIMELINE (MODEL TIMESTEP)</span>
              <span className="transport-step">
                step {timestep + 1}/{result.n_steps} · {fmtTime(currentStep.time_start)}
              </span>
            </div>
            <div className="timeline-bar">
              {result.members[0].steps.map((s, i) => (
                <button
                  key={i}
                  className={`timeline-seg ${s.flood_state === 'NO_FLOOD' ? 'seg-known' : 'seg-blocked'} ${i === timestep ? 'seg-active' : ''}`}
                  onClick={() => setTimestep(i)}
                  title={`${s.max_depth_cm} cm · ${s.flood_state}`}
                >
                  {s.max_depth_cm >= 100 ? '>1m' : s.max_depth_cm.toFixed(0)}
                </button>
              ))}
            </div>
            <div className="timeline-legend">
              <span><i className="lg lg-known" /> rainfall peak / depth (legend shows depth cm)</span>
              {traj.length > 0 && (
                <span className="transport-step mono">
                  traj: {traj.map((v) => v?.toFixed(0)).join(' · ')} cm
                </span>
              )}
            </div>
          </div>

          {/* Scenario state summary */}
          <div className="delhi-section flood-timeline-panel">
            <div className="delhi-section-head timeline-header timeline-header">
              <span className="delhi-section-title timeline-heading timeline-heading">SCENARIO STATE @ {fmtTime(currentStep.time_start)}</span>
              <span className="delhi-prov-tag prov-partial">SIMULATED</span>
            </div>
            <div className="route-stat-row">
              <div className="route-stat">
                <span className="stat-value">{currentStep.max_depth_cm.toFixed(0)} cm</span>
                <span className="stat-label">max surface depth</span>
              </div>
              <div className="route-stat">
                <span className="stat-value">{currentStep.flooded_cells.toLocaleString()}</span>
                <span className="stat-label">flooded cells (30 m)</span>
              </div>
              <div className="route-stat">
                <span className="stat-value">
                  {Object.values(currentStep.per_reach_surface_inflow_m3_s ?? {})
                    .reduce((a, b) => a + b, 0)
                    .toFixed(1)}
                </span>
                <span className="stat-label">corridor inflow proxy (m³/s)</span>
              </div>
            </div>
            {result.ensemble_envelope && result.ensemble_envelope[timestep] && (
              <div className="obs-block obs-model">
                <div className="obs-block-title">ENSEMBLE ENVELOPE (SCN-06)</div>
                <div className="obs-line mono">
                  mean {result.ensemble_envelope[timestep].mean_depth_cm} cm · min{' '}
                  {result.ensemble_envelope[timestep].min_depth_cm} · max{' '}
                  {result.ensemble_envelope[timestep].max_depth_cm} · spread{' '}
                  {result.ensemble_envelope[timestep].spread_cm}
                </div>
                <div className="obs-line">NOT a confidence interval.</div>
              </div>
            )}
          </div>

          {/* Drainage network response */}
          {result.members[0].drainage_loading && (
            <div className="delhi-section flood-timeline-panel">
              <div className="delhi-section-head timeline-header timeline-header">
                <span className="delhi-section-title timeline-heading timeline-heading">DRAINAGE NETWORK RESPONSE</span>
                <span className="delhi-section-hint">scenario-derived, not observed</span>
              </div>
              <table className="delhi-table">
                <thead>
                  <tr>
                    <th>Edge</th>
                    <th>Reach</th>
                    <th>Peak inflow (m³/s)</th>
                    <th>Capacity class</th>
                    <th>State</th>
                  </tr>
                </thead>
                <tbody>
                  {result.members[0].drainage_loading.map((e) => (
                    <tr key={e.edge_id}>
                      <td className="mono">{e.edge_id}</td>
                      <td>{e.reach_id}</td>
                      <td className="mono">{e.inflow_m3_s ?? 'UNKNOWN'}</td>
                      <td className="mono">
                        {e.capacity_min_m3_s.toFixed(0)}–{e.capacity_max_m3_s.toFixed(0)}
                      </td>
                      <td>
                        <span
                          className={`state-chip ${
                            e.status === 'POTENTIAL_OVERLOAD'
                              ? 'state-blocked'
                              : e.status === 'UNKNOWN'
                                ? 'state-unknown'
                                : 'state-computed'
                          }`}
                        >
                          {e.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <div className="delhi-note">
                POTENTIAL_OVERLOAD = modeled inflow breaches the documented
                capacity-class lower bound — backflow/surcharge potential
                under the synthetic forcing, never observed flooding.
              </div>
            </div>
          )}

          {/* Rainfall + telemetry */}
          <div className="delhi-section flood-timeline-panel">
            <div className="delhi-section-head timeline-header timeline-header">
              <span className="delhi-section-title timeline-heading timeline-heading">RAINFALL FORCING (SIMULATED)</span>
            </div>
            <div className="delhi-forecast-bins">
              {result.members[0].forcing_depths_mm.slice(0, 8).map((d, i) => (
                <div key={i} className="delhi-forecast-bin">
                  <div className="bin-depth">{d.toFixed(1)}<span className="bin-unit"> mm</span></div>
                  <div className="bin-time">t+{(i + 1) * result.timestep_min}min</div>
                </div>
              ))}
            </div>
            <details className="delhi-details">
              <summary>Synthetic telemetry (internally consistent)</summary>
              <table className="delhi-table">
                <thead><tr><th>Sensor</th><th>Value @ step</th><th>Unit</th></tr></thead>
                <tbody>
                  {result.members[0].telemetry.steps[timestep]?.readings.map((r) => (
                    <tr key={r.sensor_id}>
                      <td className="mono">{r.sensor_id}</td>
                      <td className="mono">{r.value}</td>
                      <td>{r.unit}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <div className="delhi-note">synthetic telemetry derived consistently from the scenario state; never presented as real sensor data.</div>
            </details>
          </div>

          {/* Road flood depth */}
          <div className="delhi-section flood-timeline-panel">
            <div className="delhi-section-head timeline-header timeline-header">
              <span className="delhi-section-title timeline-heading timeline-heading">ROAD-SEGMENT FLOOD DEPTH</span>
              <span className="delhi-section-hint">click a row; UNKNOWN is never 0 m</span>
            </div>
            <div className="route-segment-list">
              {roadEntries.slice(0, 10).map(([rid, d]) => (
                <button
                  key={rid}
                  className={`route-segment-row ${selectedRoad === rid ? 'row-active' : ''}`}
                  onClick={() => setSelectedRoad(rid)}
                >
                  <span className="mono">{rid}</span>
                  <span className="mono">
                    {d.flood_state === 'UNKNOWN' ? 'UNKNOWN' : `${d.depth_m.toFixed(2)} m (${d.depth_cm.toFixed(0)} cm)`}
                  </span>
                  <span className={`state-chip state-${d.flood_state.toLowerCase()}`}>{d.flood_state}</span>
                </button>
              ))}
              {roadEntries.length > 10 && (
                <div className="delhi-note">…and {roadEntries.length - 10} more segments</div>
              )}
            </div>
          </div>

          {/* Synthetic validation */}
          <div className="delhi-section flood-timeline-panel">
            <div className="delhi-section-head timeline-header timeline-header">
              <span className="delhi-section-title timeline-heading timeline-heading">SYNTHETIC VALIDATION</span>
              <span className="delhi-prov-tag prov-partial">CONTROLLED TEST DATA</span>
            </div>
            <div className="obs-line">
              Routed 2D surface pass vs the independent local reference
              (different mechanism — validation is not circular).
            </div>
            {result.synthetic_validation && (
              <>
                <table className="delhi-table">
                  <tbody>
                    {Object.entries(result.synthetic_validation.aggregated).map(([k, v]) => (
                      <tr key={k}>
                        <td>{k}</td>
                        <td className="mono">{JSON.stringify(v)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                <div className="delhi-note">{result.synthetic_validation.note}</div>
              </>
            )}
            <div className="delhi-note">
              {result.provenance && (
                <span>
                  run {result.run_id} · seed {result.seed} · generated by {result.generated_by}
                </span>
              )}
            </div>
            <div className="delhi-claim-policy">{result.claim_policy}</div>
          </div>
        </>
      )}
    </div>
  );
};

export default ScenarioPanel;