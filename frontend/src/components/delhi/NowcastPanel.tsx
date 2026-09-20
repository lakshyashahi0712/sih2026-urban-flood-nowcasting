import { useCallback, useEffect, useRef, useState } from 'react';
import { delhiApi, type NowcastResponse } from '../../api/delhi';
import EnvelopeChart from './EnvelopeChart';
import Explanation, { explainReachState } from './Explanation';
import type { MapFlowState } from './DelhiMap';

const NowcastPanel = ({
  onMapState,
  onSurfaceHotspots = () => {},
}: {
  onMapState: (s: MapFlowState) => void;
  onSurfaceHotspots?: (hotspots: { lon: number; lat: number; surface_water_cm_estimated: number; provenance: string }[]) => void;
}) => {
  const [data, setData] = useState<NowcastResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [explanationFor, setExplanationFor] = useState<string | null>(null);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const load = useCallback(async (refresh: boolean) => {
    setError(null);
    if (refresh) setRefreshing(true);
    try {
      const res = await delhiApi.getNowcast(refresh);
      setData(res);
      const surface = res.surface;
      if (surface && 'timesteps' in surface) {
        onSurfaceHotspots(
          surface.timesteps.flatMap((t) => t.hotspots ?? []),
        );
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'nowcast request failed');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    load(false);
    // Operational polling: refresh the nowcast every 10 minutes (matches
    // the backend forecast cache TTL window).
    timerRef.current = setInterval(() => load(false), 10 * 60 * 1000);
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [load]);

  // Synchronize the map with the live nowcast (model data only): rain
  // intensity comes from the CURRENT forecast hour; reach states from the
  // final ensemble member step. UNKNOWN rain -> no animation, ever.
  useEffect(() => {
    if (!data || data.status !== 'COMPUTED' || !data.members?.[0]) {
      onMapState({ reachStates: {}, timestamp: null, rainIntensityMmH: null, rainKnown: false });
      return;
    }
    const m0 = data.members[0];
    const lastCls = m0.classifications[m0.classifications.length - 1] ?? [];
    const reachStates: MapFlowState['reachStates'] = {};
    for (const c of lastCls) {
      reachStates[c.reach_id] = c.status.startsWith('BLOCKED')
        ? 'BLOCKED'
        : c.classification === 'UNKNOWN'
          ? 'UNKNOWN'
          : 'COMPUTED';
    }
    const firstBin = data.forecast.bins[0];
    const rainKnown = firstBin != null && firstBin.depth_mm !== null;
    onMapState({
      reachStates,
      timestamp: firstBin?.time_start ?? null,
      rainIntensityMmH: rainKnown && firstBin ? firstBin.depth_mm! : null,
      rainKnown,
    });
  }, [data, onMapState]);

  const fmtTime = (iso: string) =>
    new Date(iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

  if (loading) {
    return <div className="delhi-panel-status">Acquiring forecast and executing ensemble…</div>;
  }

  if (error) {
    return (
      <div className="delhi-panel-status delhi-panel-error">
        Nowcast unavailable: {error}
        <button className="delhi-btn" onClick={() => load(true)}>
          Retry
        </button>
      </div>
    );
  }

  if (!data) return null;

  const forecast = data.forecast;
  const computed = data.status === 'COMPUTED';
  const totalForecastMm = forecast.bins.reduce((a, b) => a + (b.depth_mm ?? 0), 0);
  const anyUnknownBin = forecast.bins.some((b) => b.depth_mm === null);

  return (
    <div className="delhi-nowcast">
      {/* Operational status banner */}
      <div className={`delhi-banner ${computed ? 'banner-ok' : 'banner-warn'}`}>
        <div className="banner-main">
          {computed ? (
            <>
              <span className="banner-state">NOWCAST COMPUTED</span>
              <span className="banner-sub">
                6-member deterministic ensemble • generated{' '}
                {new Date(data.generated_at).toLocaleTimeString()}
              </span>
            </>
          ) : (
            <>
              <span className="banner-state">NOWCAST {data.status}</span>
              <span className="banner-sub">
                {forecast.diagnostics[0] ??
                  'Forecast forcing unavailable — the system will not fabricate a nowcast.'}
              </span>
            </>
          )}
        </div>
        <button
          className="delhi-btn"
          disabled={refreshing}
          onClick={() => load(true)}
        >
          {refreshing ? 'Refreshing…' : 'Refresh'}
        </button>
      </div>

      {/* Forecast forcing strip */}
      <div className="delhi-section flood-timeline-panel">
        <div className="delhi-section-head timeline-header timeline-header">
          <span className="delhi-section-title timeline-heading timeline-heading">RAINFALL FORECAST INPUT</span>
          <span className={`delhi-prov-tag prov-${forecast.status.toLowerCase()}`}>
            {forecast.status}
          </span>
        </div>
        <div className="delhi-forecast-meta">
          {forecast.source} • reference point {forecast.reference_point} •
          acquired {forecast.acquired_at ? new Date(forecast.acquired_at).toLocaleTimeString() : '—'}
        </div>
        <div className="delhi-forecast-bins">
          {forecast.bins.map((b) => (
            <div key={b.time_start} className="delhi-forecast-bin">
              <div className="bin-depth">
                {b.depth_mm === null ? (
                  <span className="bin-unknown">UNKNOWN</span>
                ) : (
                  <>
                    {b.depth_mm.toFixed(1)}
                    <span className="bin-unit">mm</span>
                  </>
                )}
              </div>
              <div className="bin-time">{fmtTime(b.time_start)}</div>
              <div className={`bin-prov prov-${b.provenance.toLowerCase()}`}>
                {b.provenance}
              </div>
            </div>
          ))}
          {forecast.bins.length === 0 && (
            <div className="bin-unknown">No forecast bins acquired</div>
          )}
        </div>
        <div className="delhi-note">
          Horizon total {totalForecastMm.toFixed(1)} mm
          {anyUnknownBin ? ' (some hours UNKNOWN — no zero-fill)' : ''} • NWP
          model values, not gauge observations.
        </div>
      </div>

      {computed && (
        <>
          {/* Ensemble envelope chart */}
          <div className="delhi-section flood-timeline-panel">
            <div className="delhi-section-head timeline-header timeline-header">
              <span className="delhi-section-title timeline-heading timeline-heading">
                ENSEMBLE INFLOW ENVELOPE (MODEL-DERIVED)
              </span>
              <span className="delhi-prov-tag prov-computed">DERIVED</span>
            </div>
            <EnvelopeChart envelope={data.envelope_inflow} />
            <div className="delhi-note">
              Band = min–max across the 6 deterministic members; line = median.
              Inflow is the modeled catchment response, not measured discharge.
            </div>
          </div>

          {/* Reach state table */}
          <div className="delhi-section flood-timeline-panel">
            <div className="delhi-section-head timeline-header timeline-header">
              <span className="delhi-section-title timeline-heading timeline-heading">REACH STATES (MODEL-DERIVED)</span>
            </div>
            <table className="delhi-table">
              <thead>
                <tr>
                  <th>Reach</th>
                  <th>Storage @ final step</th>
                  <th>Stage</th>
                  <th>State</th>
                  <th aria-label="explanation" />
                </tr>
              </thead>
              <tbody>
                {data.members[0] &&
                  Object.entries(data.members[0].reach_states).map(
                    ([reachId, steps]) => {
                      const last = steps[steps.length - 1];
                      const finalClass =
                        data.members[0].classifications[
                          data.members[0].classifications.length - 1
                        ]?.find((c) => c.reach_id === reachId);
                      return (
                        <tr key={reachId} className={explanationFor === reachId ? 'row-active' : ''}>
                          <td className="mono">{reachId}</td>
                          <td>
                            {last.storage_m3 === null ? (
                              <span className="val-unknown">UNKNOWN</span>
                            ) : (
                              `${(last.storage_m3 / 1000).toFixed(1)}k m³`
                            )}
                          </td>
                          <td>
                            <span className="val-unknown">UNKNOWN</span>
                          </td>
                          <td>
                            <span
                              className={`state-chip state-${finalClass?.classification.toLowerCase()}`}
                            >
                              {finalClass?.classification ?? 'UNKNOWN'}
                            </span>
                          </td>
                          <td>
                            <button
                              className="why-btn"
                              title="Explain this state"
                              onClick={() =>
                                setExplanationFor((v) =>
                                  v === reachId ? null : reachId,
                                )
                              }
                            >
                              Why?
                            </button>
                          </td>
                        </tr>
                      );
                    },
                  )}
              </tbody>
            </table>
            {explanationFor && data.members[0] && (
              <Explanation
                lines={explainReachState({
                  reachId: explanationFor,
                  hydraulicStatus:
                    data.members[0].reach_states[explanationFor]?.slice(-1)[0]
                      ?.hydraulic_status ?? 'UNKNOWN',
                  incomingFlowM3S:
                    data.members[0].reach_states[explanationFor]?.slice(-1)[0]
                      ?.incoming_flow_m3_s ?? null,
                  storageM3:
                    data.members[0].reach_states[explanationFor]?.slice(-1)[0]
                      ?.storage_m3 ?? null,
                  transferredM3S:
                    data.members[0].reach_states[explanationFor]?.slice(-1)[0]
                      ?.transferred_downstream_m3_s ?? null,
                  capacityM3S: null,
                  balanceResidualM3S:
                    data.members[0].reach_states[explanationFor]?.slice(-1)[0]
                      ?.balance_residual_m3_s ?? null,
                  classification:
                    data.members[0].classifications[
                      data.members[0].classifications.length - 1
                    ]?.find((c) => c.reach_id === explanationFor)?.classification ??
                    'UNKNOWN',
                })}
                onClose={() => setExplanationFor(null)}
              />
            )}
            <div className="delhi-note">
              Stage is UNKNOWN by design: no storage–stage relation exists for
              Kushak, and capacity exceedance without stage is blocked by the
              model contract. Inflow/storage envelopes are the defensible
              signal.
            </div>
          </div>

          {data.drainage_loading && data.drainage_loading.length > 0 && (
            <div className="delhi-section flood-timeline-panel">
              <div className="delhi-section-head timeline-header timeline-header">
                <span className="delhi-section-title timeline-heading timeline-heading">DRAINAGE NODE LOADING (DERIVED GRAPH)</span>
                <span className="delhi-section-hint">scenario-derived, not observed</span>
              </div>
              <table className="delhi-table">
                <thead>
                  <tr>
                    <th>Edge</th>
                    <th>Node</th>
                    <th>Inflow (m³/s)</th>
                    <th>Capacity class</th>
                    <th>State</th>
                  </tr>
                </thead>
                <tbody>
                  {data.drainage_loading.map((edge) => (
                    <tr key={edge.edge_id}>
                      <td className="mono">{edge.edge_id}</td>
                      <td className="mono">{edge.node_id}</td>
                      <td>{edge.inflow_m3_s ?? '—'}</td>
                      <td className="mono">
                        {edge.capacity_min_m3_s.toFixed(0)}–{edge.capacity_max_m3_s.toFixed(0)}
                      </td>
                      <td>
                        <span
                          className={`state-chip ${
                            edge.status === 'POTENTIAL_OVERLOAD'
                              ? 'state-blocked'
                              : edge.status === 'UNKNOWN'
                                ? 'state-unknown'
                                : 'state-computed'
                          }`}
                        >
                          {edge.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <div className="delhi-note">
                POTENTIAL_OVERLOAD = modeled inflow breaches the lower bound
                of the documented capacity class (backflow/surcharge potential,
                not observed flooding, not a depth claim). Capacity classes are
                INFERRED_EFFECTIVE full-bore estimates from documented geometry.
              </div>
            </div>
          )}

          {data.depth_estimates && Object.keys(data.depth_estimates).length > 0 && (
            <div className="delhi-section flood-timeline-panel">
              <div className="delhi-section-head timeline-header timeline-header">
                <span className="delhi-section-title timeline-heading timeline-heading">ESTIMATED DEPTH (ASSUMED GEOMETRY)</span>
                <span className="delhi-prov-tag prov-partial">NOT OBSERVED</span>
              </div>
              <table className="delhi-table">
                <thead>
                  <tr>
                    <th>Edge</th>
                    <th>Depth range (cm)</th>
                    <th>Basis</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(data.depth_estimates).map(([edgeId, est]) => (
                    <tr key={edgeId}>
                      <td className="mono">{edgeId}</td>
                      <td className="mono">
                        {est.depth_min_cm === null
                          ? 'UNKNOWN'
                          : `${est.depth_min_cm} – ${est.depth_max_cm}`}
                      </td>
                      <td className="reason-cell">
                        {est.status === 'UNKNOWN' ? est.reason : est.caveat}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <div className="delhi-note">
                Single-store prism proxy under ESTIMATED_UNDER_ASSUMED_GEOMETRY —
                not hydraulic stage, not observed depth, not street depth.
              </div>
            </div>
          )}

          {data.surface && 'timesteps' in data.surface && (
            <div className="delhi-section flood-timeline-panel">
              <div className="delhi-section-head timeline-header timeline-header">
                <span className="delhi-section-title timeline-heading timeline-heading">2D SURFACE PASS (DEM PROXY)</span>
                <span className="delhi-section-hint">model-derived, not ponded depth</span>
              </div>
              <div className="obs-line">{data.surface.method}</div>
              <div className="delhi-note">{data.surface.caveat}</div>
              <table className="delhi-table">
                <thead>
                  <tr>
                    <th>Timestep</th>
                    <th>Peak surface (cm)</th>
                    <th>Hotspots</th>
                    <th>Corridor inflow proxy (m³/s)</th>
                  </tr>
                </thead>
                <tbody>
                  {data.surface.timesteps.map((t) => (
                    <tr key={t.timestep_index}>
                      <td className="mono">t+{t.timestep_index}</td>
                      <td className="mono">{t.peak_surface_cm ?? 'UNKNOWN'}</td>
                      <td className="mono">{t.hotspots?.length ?? 0}</td>
                      <td className="mono">
                        {Object.entries(t.per_reach_surface_inflow_m3_s ?? {})
                          .filter(([, q]) => q > 0)
                          .map(([r, q]) => `${r}: ${q}`)
                          .join(' · ') || '—'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Ensemble members detail */}
          <details className="delhi-details">
            <summary>Ensemble members ({data.members.length})</summary>
            <table className="delhi-table">
              <thead>
                <tr>
                  <th>Member</th>
                  <th>Hydraulic scenario</th>
                  <th>Catchment</th>
                  <th>Inflow volume (4h)</th>
                </tr>
              </thead>
              <tbody>
                {data.members.map((m) => (
                  <tr key={m.member_id}>
                    <td className="mono">{m.member_id}</td>
                    <td>{m.hydraulic_scenario_id}</td>
                    <td>{m.catchment_scenario_id}</td>
                    <td>
                      {m.inflow_volume_m3 === null
                        ? '—'
                        : `${(m.inflow_volume_m3 / 1000).toFixed(1)}k m³`}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </details>
        </>
      )}

      <div className="delhi-claim-policy">{data.claim_policy}</div>
    </div>
  );
};

export default NowcastPanel;
