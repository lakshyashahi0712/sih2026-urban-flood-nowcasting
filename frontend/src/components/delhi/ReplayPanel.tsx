import { useCallback, useEffect, useMemo, useState } from 'react';
import {
  delhiApi,
  type EventReplayResponse,
  type EventsResponse,
  type ReplaySummaryResponse,
  type ReplayStatus,
} from '../../api/delhi';
import EnvelopeChart from './EnvelopeChart';
import Explanation, { explainReachState } from './Explanation';
import type { MapFlowState } from './DelhiMap';

const ReplayPanel = ({
  onMapState,
  onDepthCells = () => {},
  onDepthPolygons = () => {},
}: {
  onMapState: (s: MapFlowState) => void;
  onDepthCells?: (
    cells: { lon: number; lat: number; depth_cm: number; flood_state: string; provenance: string }[],
  ) => void;
  onDepthPolygons?: (polygons: { type: string; features: unknown[] } | null) => void;
}) => {
  const [events, setEvents] = useState<EventsResponse | null>(null);
  const [summary, setSummary] = useState<ReplaySummaryResponse | null>(null);
  const [selected, setSelected] = useState<string>('EVT-2024-06-27');
  const [replay, setReplay] = useState<EventReplayResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [replayLoading, setReplayLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [stepIdx, setStepIdx] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [visibleMembers, setVisibleMembers] = useState<Set<string>>(new Set());
  const [explanationFor, setExplanationFor] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const [ev, sum] = await Promise.all([
          delhiApi.getEvents(),
          delhiApi.getReplaySummary(),
        ]);
        setEvents(ev);
        setSummary(sum);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'failed to load events');
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const loadReplay = useCallback(async (eventId: string) => {
    setReplayLoading(true);
    setError(null);
    try {
      const res = await delhiApi.getEventReplay(eventId);
      setReplay(res);
      setStepIdx(0);
      setPlaying(false);
      setVisibleMembers(new Set());
      setExplanationFor(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'replay failed');
      setReplay(null);
    } finally {
      setReplayLoading(false);
    }
  }, []);

  useEffect(() => {
    loadReplay(selected);
  }, [selected, loadReplay]);

  // Playback timer over forcing timesteps.
  useEffect(() => {
    if (!playing || !replay || replay.runtime_status === 'NOT_EXECUTED') return;
    const maxStep = replay.members?.[0]?.inflow_steps.length ?? 0;
    if (maxStep === 0) return;
    const t = setInterval(() => {
      setStepIdx((i) => {
        if (i + 1 >= maxStep) {
          setPlaying(false);
          return i;
        }
        return i + 1;
      });
    }, 1400);
    return () => clearInterval(t);
  }, [playing, replay]);

  const memberSeries = useMemo(() => {
    if (!replay || replay.runtime_status === 'NOT_EXECUTED' || !replay.members)
      return [];
    const palette = ['#0284c7', '#7c3aed', '#059669', '#d97706', '#dc2626', '#334155'];
    return replay.members
      .filter((m) => visibleMembers.size === 0 || visibleMembers.has(m.member_id))
      .map((m, i) => ({
        color: palette[i % palette.length],
        points: m.inflow_steps.map((s) => ({
          time: s.time,
          value: s.discharge_m3_s,
        })),
      }));
  }, [replay, visibleMembers]);

  // Synchronize the map with the current replay timestep (model data only).
  useEffect(() => {
    if (!replay || replay.runtime_status === 'NOT_EXECUTED' || !replay.members?.[0]) {
      onMapState({ reachStates: {}, timestamp: null, rainIntensityMmH: null, rainKnown: false });
      return;
    }
    const m0 = replay.members[0];
    const step = m0.chain_steps[stepIdx];
    if (!step) return;
    const reachStates: MapFlowState['reachStates'] = {};
    for (const r of step.reaches) {
      reachStates[r.reach_id] = r.hydraulic_status.startsWith('BLOCKED')
        ? 'BLOCKED'
        : r.storage_m3 !== null
          ? 'COMPUTED'
          : 'UNKNOWN';
    }
    // Rain intensity for THIS step: depth / documented duration. The step
    // provenance comes from the forcing bins; UNKNOWN -> no rain animation.
    const bin = replay.forcing?.bins[stepIdx];
    const rainKnown = bin != null && bin.depth_mm !== null;
    const binDurationH = 1; // catalog bins are 1 h unless declared otherwise
    const intensity = rainKnown && bin ? bin.depth_mm! / binDurationH : null;
    onMapState({
      reachStates,
      timestamp: step.time_start,
      rainIntensityMmH: intensity,
      rainKnown,
    });
  }, [replay, stepIdx, onMapState]);

  // Flood depth on the map follows the replay clock (V1-style historical
  // depth replay: the V1 reference model on the documented forcing bins).
  useEffect(() => {
    if (!replay || replay.runtime_status === 'NOT_EXECUTED') {
      onDepthCells([]);
      return;
    }
    let cancelled = false;
    delhiApi
      .getEventDepth(replay.event_id, stepIdx)
      .then((d) => {
        if (!cancelled) {
          onDepthCells(d.step?.depth_cells ?? []);
          onDepthPolygons(d.step?.depth_polygons ?? null);
        }
      })
      .catch(() => {
        if (!cancelled) onDepthCells([]);
      });
    return () => {
      cancelled = true;
    };
  }, [replay, stepIdx, onDepthCells, onDepthPolygons]);

  useEffect(() => { onDepthCells([]); onDepthPolygons(null); }, [selected, onDepthCells, onDepthPolygons]);

  const fmtTime = (iso: string) =>
    new Date(iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

  if (loading) return <div className="delhi-panel-status">Loading event catalogue…</div>;

  const currentMember = replay?.members?.[0];
  const currentStep = currentMember?.chain_steps[stepIdx];
  const currentStepClass = (reachId: string) =>
    currentStep?.classifications.find((c) => c.reach_id === reachId)?.classification ?? 'UNKNOWN';

  // Interval states for the timeline bar: computed / unknown per bin.
  const timelineBins =
    replay?.forcing?.bins.map((b) => ({
      known: b.depth_mm !== null,
      depth: b.depth_mm,
    })) ?? [];

  const statusClass = (s: ReplayStatus) =>
    s === 'EXECUTABLE' ? 'tag-ok' : s === 'PARTIAL' ? 'tag-partial' : s === 'CONTROL' ? 'tag-control' : 'tag-warn';

  const explainedReach = currentStep?.reaches.find(
    (r) => r.reach_id === explanationFor,
  );
  const explanationLines = explainedReach
    ? explainReachState({
        reachId: explainedReach.reach_id,
        hydraulicStatus: explainedReach.hydraulic_status,
        incomingFlowM3S: explainedReach.incoming_flow_m3_s,
        storageM3: explainedReach.storage_m3,
        transferredM3S: explainedReach.transferred_m3_s,
        capacityM3S: explainedReach.capacity_m3_s,
        balanceResidualM3S: explainedReach.balance_residual_m3_s,
        classification: currentStepClass(explainedReach.reach_id),
      })
    : [];

  return (
    <div className="delhi-replay">
      {/* Verdict banner */}
      {summary && (
        <div className="delhi-banner banner-ok">
          <div className="banner-main">
            <span className="banner-state">HISTORICAL REPLAY VERDICT: {summary.verdict}</span>
            <span className="banner-sub">{summary.claim_policy}</span>
          </div>
        </div>
      )}

      {/* Event selector */}
      <div className="delhi-section flood-timeline-panel">
        <div className="delhi-section-head timeline-header timeline-header">
          <span className="delhi-section-title timeline-heading timeline-heading">HISTORICAL EVENTS</span>
          <span className="delhi-section-hint">
            statuses from the validated event manifest
          </span>
        </div>
        <div className="delhi-event-grid">
          {events?.events.map((ev) => (
            <button
              key={ev.event_id}
              className={`delhi-event-card ${selected === ev.event_id ? 'selected' : ''}`}
              onClick={() => setSelected(ev.event_id)}
            >
              <div className="event-id mono">{ev.event_id}</div>
              <div className="event-window">{ev.event_window}</div>
              <div className={`event-tag ${statusClass(ev.replay_status)}`}>
                {ev.replay_status === 'EXECUTABLE'
                  ? 'REPLAY READY'
                  : ev.replay_status === 'PARTIAL'
                    ? 'PARTIAL REPLAY'
                    : ev.replay_status === 'CONTROL'
                      ? 'CONTROL (NO FORCING)'
                      : 'NO FORCING'}
              </div>
            </button>
          ))}
        </div>
      </div>

      {replayLoading && <div className="delhi-panel-status">Executing runtime replay…</div>}
      {error && <div className="delhi-panel-status delhi-panel-error">{error}</div>}

      {replay && !replayLoading && (
        <>
          {/* Event metadata + documented observations */}
          <div className="delhi-section flood-timeline-panel">
            <div className="delhi-section-head timeline-header timeline-header">
              <span className="delhi-section-title timeline-heading mono">{replay.event_id}</span>
              <span
                className={`delhi-prov-tag ${
                  replay.runtime_status === 'NOT_EXECUTED'
                    ? 'prov-unavailable'
                    : replay.runtime_status === 'PARTIAL_EXECUTED'
                      ? 'prov-partial'
                      : 'prov-computed'
                }`}
              >
                {replay.runtime_status}
              </span>
            </div>
            <div className="delhi-meta-grid">
              <div>
                <span className="meta-k">Window</span>
                <span className="meta-v">{replay.event_window}</span>
              </div>
              <div>
                <span className="meta-k">Rainfall resolution</span>
                <span className="meta-v">{replay.rainfall_resolution}</span>
              </div>
            </div>

            {/* OBSERVED evidence — clearly separated from model output */}
            <div className="obs-block obs-observed">
              <div className="obs-block-title">
                OBSERVED · DOCUMENTED EVIDENCE
                <span className="delhi-prov-tag prov-observed">OBSERVED</span>
              </div>
              <div className="obs-line">{replay.operational_state}</div>
              <div className="obs-line">{replay.observed_empirical_outcome}</div>
            </div>

            <div className="obs-block obs-model">
              <div className="obs-block-title">
                MODEL-RECONSTRUCTED STATE
                <span className="delhi-prov-tag prov-computed">MODEL-DERIVED</span>
              </div>
              <div className="obs-line">{replay.evidence_notes}</div>
            </div>
          </div>

          {replay.runtime_status === 'NOT_EXECUTED' ? (
            <div className="delhi-section flood-timeline-panel delhi-blocked-box">
              <div className="blocked-title">RUNTIME NOT EXECUTED</div>
              <div>{replay.reason}</div>
              <div className="delhi-note">
                Absent forcing is a structural barrier: the system never
                invents rainfall, zero-fills missing hours, or disaggregates
                coarse records.
              </div>
            </div>
          ) : (
            <>
              {/* Event timeline with interval states */}
              <div className="delhi-section flood-timeline-panel">
                <div className="delhi-section-head timeline-header timeline-header">
                  <span className="delhi-section-title timeline-heading timeline-heading">EVENT TIMELINE (FORCING INTERVALS)</span>
                </div>
                <div className="timeline-bar">
                  {timelineBins.map((b, i) => (
                    <button
                      key={i}
                      className={`timeline-seg ${b.known ? 'seg-known' : 'seg-unknown'} ${
                        i === stepIdx ? 'seg-active' : ''
                      } ${replay.members?.[0]?.chain_steps[i]?.reaches[0]?.hydraulic_status.startsWith('BLOCKED') ? 'seg-blocked' : ''}`}
                      onClick={() => setStepIdx(i)}
                      title={
                        b.known
                          ? `${b.depth} mm — computed`
                          : 'UNKNOWN forcing — blocked (never zero-filled)'
                      }
                    >
                      {b.known ? `${b.depth}` : '?'}
                    </button>
                  ))}
                </div>
                <div className="timeline-legend">
                  <span><i className="lg lg-known" /> documented forcing (computed)</span>
                  <span><i className="lg lg-blocked" /> step blocked downstream</span>
                  <span><i className="lg lg-unknown" /> UNKNOWN — never zero-filled</span>
                </div>
              </div>

              {/* Forcing bins */}
              <div className="delhi-section flood-timeline-panel">
                <div className="delhi-section-head timeline-header timeline-header">
                  <span className="delhi-section-title timeline-heading timeline-heading">EVENT FORCING (PRESERVED RESOLUTION)</span>
                </div>
                <div className="delhi-forecast-bins">
                  {replay.forcing?.bins.map((b) => (
                    <div key={b.lead_hour} className="delhi-forecast-bin">
                      <div className="bin-depth">
                        {b.depth_mm === null ? (
                          <span className="bin-unknown">UNKNOWN</span>
                        ) : (
                          <>
                            {b.depth_mm}
                            <span className="bin-unit"> {b.units}</span>
                          </>
                        )}
                      </div>
                      <div className="bin-time">t+{b.lead_hour}h</div>
                      <div className={`bin-prov prov-${b.provenance.toLowerCase()}`}>
                        {b.provenance}
                      </div>
                    </div>
                  ))}
                </div>
                <div className="delhi-note">{replay.forcing?.note}</div>
              </div>

              {/* Member hydrographs */}
              <div className="delhi-section flood-timeline-panel">
                <div className="delhi-section-head timeline-header timeline-header">
                  <span className="delhi-section-title timeline-heading timeline-heading">
                    MEMBER INFLOW HYDROGRAPHS ({replay.ensemble_size} members)
                  </span>
                </div>
                <EnvelopeChart series={memberSeries} />
                <div className="delhi-note">
                  Unknown forcing hours appear as gaps (UNKNOWN is preserved,
                  never zero-filled). Curves are modeled inflow, not observed
                  discharge.
                </div>
                <details className="delhi-details">
                  <summary>Toggle members</summary>
                  <div className="delhi-member-toggles">
                    {replay.members?.map((m) => (
                      <label key={m.member_id} className="delhi-layer-row">
                        <input
                          type="checkbox"
                          checked={visibleMembers.size === 0 || visibleMembers.has(m.member_id)}
                          onChange={(e) =>
                            setVisibleMembers((prev) => {
                              const next = new Set(
                                prev.size === 0
                                  ? replay.members!.map((x) => x.member_id)
                                  : prev,
                              );
                              if (e.target.checked) next.add(m.member_id);
                              else next.delete(m.member_id);
                              return next;
                            })
                          }
                        />
                        <span className="delhi-layer-label mono">{m.member_id}</span>
                      </label>
                    ))}
                  </div>
                </details>
              </div>

              {/* Timestep playback */}
              <div className="delhi-section flood-timeline-panel">
                <div className="delhi-section-head timeline-header timeline-header">
                  <span className="delhi-section-title timeline-heading timeline-heading">TIMESTEP PLAYBACK</span>
                  <span className="delhi-section-hint">map and charts follow the replay clock</span>
                </div>
                <div className="delhi-transport">
                  <button
                    className="delhi-btn"
                    onClick={() => setStepIdx((i) => Math.max(0, i - 1))}
                  >
                    Prev
                  </button>
                  <button
                    className="delhi-btn delhi-btn-primary"
                    onClick={() => setPlaying((p) => !p)}
                  >
                    {playing ? 'Pause' : 'Play'}
                  </button>
                  <button
                    className="delhi-btn"
                    onClick={() =>
                      setStepIdx((i) =>
                        Math.min((currentMember?.inflow_steps.length ?? 1) - 1, i + 1),
                      )
                    }
                  >
                    Next
                  </button>
                  <span className="transport-time mono">
                    {currentStep?.time_start
                      ? `${fmtTime(currentStep.time_start)} IST`
                      : '—'}
                  </span>
                  <span className="transport-step">
                    step {stepIdx + 1}/{currentMember?.inflow_steps.length ?? 0}
                  </span>
                </div>
                <table className="delhi-table">
                  <thead>
                    <tr>
                      <th>Reach</th>
                      <th>Inflow (m³/s)</th>
                      <th>Storage (m³)</th>
                      <th>Transferred (m³/s)</th>
                      <th>State</th>
                      <th>Balance</th>
                      <th aria-label="explanation" />
                    </tr>
                  </thead>
                  <tbody>
                    {currentStep?.reaches.map((r) => {
                      const cls = currentStepClass(r.reach_id);
                      return (
                        <tr key={r.reach_id} className={explanationFor === r.reach_id ? 'row-active' : ''}>
                          <td className="mono">{r.reach_id}</td>
                          <td>{r.incoming_flow_m3_s ?? '—'}</td>
                          <td>{r.storage_m3?.toLocaleString() ?? <span className="val-unknown">UNKNOWN</span>}</td>
                          <td>{r.transferred_m3_s ?? '—'}</td>
                          <td>
                            <span className={`state-chip state-${cls.toLowerCase()}`}>
                              {cls}
                            </span>
                          </td>
                          <td className="mono">
                            {r.balance_residual_m3_s === null
                              ? '—'
                              : Math.abs(r.balance_residual_m3_s) < 1e-9
                                ? '0'
                                : r.balance_residual_m3_s.toExponential(1)}
                          </td>
                          <td>
                            <button
                              className="why-btn"
                              title="Explain this state"
                              onClick={() =>
                                setExplanationFor((v) =>
                                  v === r.reach_id ? null : r.reach_id,
                                )
                              }
                            >
                              Why?
                            </button>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
                {explanationFor && explanationLines.length > 0 && (
                  <Explanation
                    lines={explanationLines}
                    onClose={() => setExplanationFor(null)}
                  />
                )}
              </div>

              {/* Integrity checks */}
              <div className="delhi-section flood-timeline-panel">
                <div className="delhi-section-head timeline-header timeline-header">
                  <span className="delhi-section-title timeline-heading timeline-heading">RUNTIME INTEGRITY CHECKS</span>
                </div>
                <div className="delhi-integrity">
                  {Object.entries(replay.integrity_checks ?? {}).map(([k, v]) => (
                    <div key={k} className="integrity-row">
                      <span className="integrity-key">{k.replace(/_/g, ' ')}</span>
                      <span className="integrity-val">{v}</span>
                    </div>
                  ))}
                </div>
              </div>
            </>
          )}

          <div className="delhi-claim-policy">{replay.claim_policy}</div>
        </>
      )}
    </div>
  );
};

export default ReplayPanel;
