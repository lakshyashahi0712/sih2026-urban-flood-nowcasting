import { useEffect, useState } from 'react';
import { delhiApi, type ModelScienceResponse } from '../../api/delhi';

// Scientific model-performance surface. Presentation rules: every metric
// shows value + status + sample size + reason; unsupported metrics are
// NOT_COMPUTABLE with their reason — never hidden, never fabricated.

const ModelPanel = () => {
  const [data, setData] = useState<ModelScienceResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    delhiApi
      .getModelScience()
      .then(setData)
      .catch((err) =>
        setError(err instanceof Error ? err.message : 'failed to load model science'),
      );
  }, []);

  if (error) {
    return <div className="delhi-panel-status delhi-panel-error">{error}</div>;
  }
  if (!data) {
    return <div className="delhi-panel-status">Loading model performance evidence…</div>;
  }

  const v = data.quantitative_validation;

  return (
    <div className="delhi-model">
      {/* Production mode banner */}
      <div className="delhi-banner banner-ok">
        <div className="banner-main">
          <span className="banner-state">PRODUCTION MODE: {data.production_mode}</span>
          <span className="banner-sub">{data.ml_status} — {data.ml.reason}</span>
        </div>
      </div>

      {/* Readiness matrix */}
      <div className="delhi-section flood-timeline-panel">
        <div className="delhi-section-head timeline-header timeline-header">
          <span className="delhi-section-title timeline-heading timeline-heading">CAPABILITY READINESS</span>
          <span className="delhi-section-hint">implemented ≠ validated ≠ calibrated</span>
        </div>
        <table className="delhi-table">
          <thead>
            <tr>
              <th>Capability</th>
              <th>Status</th>
              <th>Basis</th>
            </tr>
          </thead>
          <tbody>
            {[
              ['Physics baseline', 'PRODUCTION_READY', 'the operational hydraulic runtime (this system)'],
              [
                'Quantitative validation',
                'PARTIALLY_SUPPORTED',
                'framework implemented; only forcing-reproduction QC computable today',
              ],
              [
                'Calibration',
                'BLOCKED_BY_DATA',
                'objective gate: no local quantitative target exists',
              ],
              [
                'Identifiability',
                'RESEARCH_READY (null result)',
                'parameters non-identifiable from occurrence-only evidence',
              ],
              [
                'Uncertainty',
                'RESEARCH_READY',
                'forcing/parameter/structural/scenario decomposition computed from real runs',
              ],
              [
                'Physics-guided ML',
                'BLOCKED_BY_DATA (NOT_DEPLOYED)',
                'pipeline implemented; dataset insufficient for any reported metric',
              ],
            ].map(([cap, status, basis]) => (
              <tr key={cap}>
                <td>{cap}</td>
                <td>
                  <span className={`state-chip ${status.startsWith('PRODUCTION') ? 'state-computed' : 'state-unknown'}`}>
                    {status}
                  </span>
                </td>
                <td className="reason-cell">{basis}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Observation registry */}
      <div className="delhi-section flood-timeline-panel">
        <div className="delhi-section-head timeline-header timeline-header">
          <span className="delhi-section-title timeline-heading timeline-heading">
            OBSERVATION REGISTRY ({data.observation_registry.record_count} records)
          </span>
        </div>
        <table className="delhi-table">
          <thead>
            <tr>
              <th>Variable</th>
              <th>Records</th>
              <th>Tier A/B</th>
              <th>Calibration-usable</th>
              <th>Validation-usable</th>
            </tr>
          </thead>
          <tbody>
            {Object.entries(data.observation_registry.summary).map(([variable, s]) => (
              <tr key={variable}>
                <td className="mono">{variable}</td>
                <td className="mono">{s.count}</td>
                <td className="mono">
                  {(s.tiers['TIER_A_DIRECT_MEASUREMENT'] ?? 0) +
                    (s.tiers['TIER_B_HIGH_CONFIDENCE_DERIVED'] ?? 0)}
                </td>
                <td className="mono">{s.usable_for_calibration}</td>
                <td className="mono">{s.usable_for_validation}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <div className="delhi-note">{data.observation_registry.gate_note}</div>
      </div>

      {/* Quantitative validation metrics */}
      <div className="delhi-section flood-timeline-panel">
        <div className="delhi-section-head timeline-header timeline-header">
          <span className="delhi-section-title timeline-heading timeline-heading">QUANTITATIVE VALIDATION</span>
          <span className="delhi-section-hint">
            computed: {' '}
            {v.metrics.filter((m) => m.validity_status === 'COMPUTED').length} ·
            not computable: {' '}
            {v.metrics.filter((m) => m.validity_status === 'NOT_COMPUTABLE').length}
          </span>
        </div>
        {v.metrics
          .filter((m) => m.validity_status === 'COMPUTED')
          .map((m) => (
            <div key={m.metric_name} className="metric-row">
              <span className="metric-name mono">{m.metric_name}</span>
              <span className="metric-value">
                {m.value?.toFixed(3)} {m.units}
              </span>
              <span className="metric-n">n={m.n_observations}</span>
              <span className="delhi-prov-tag prov-computed">{m.validity_status}</span>
            </div>
          ))}
        <div className="delhi-note">
          Computed rows are forcing-reproduction QC (forcing inputs vs station
          records) — a data-consistency check, NOT hydrological model skill.
        </div>
        <details className="delhi-details">
          <summary>
            Not-computable metrics ({v.metrics.filter((m) => m.validity_status !== 'COMPUTED').length}) — with reasons
          </summary>
          <div className="nc-list">
            {v.metrics
              .filter((m) => m.validity_status !== 'COMPUTED')
              .map((m) => (
                <div key={m.metric_name} className="metric-row">
                  <span className="metric-name mono">{m.metric_name}</span>
                  <span className="delhi-prov-tag prov-unavailable">NOT_COMPUTABLE</span>
                  <span className="metric-reason">{m.reason}</span>
                </div>
              ))}
          </div>
        </details>
        <div className="delhi-note">
          Event separation: {v.event_split['justification'] as string}
        </div>
      </div>

      {/* Calibration */}
      <div className="delhi-section flood-timeline-panel">
        <div className="delhi-section-head timeline-header timeline-header">
          <span className="delhi-section-title timeline-heading timeline-heading">CALIBRATION</span>
          <span className={`delhi-prov-tag ${data.calibration.performed ? 'prov-computed' : 'prov-unavailable'}`}>
            {data.calibration.performed ? 'PERFORMED' : 'GATED OFF'}
          </span>
        </div>
        <div className="obs-line">{data.calibration.objective_gate.reason}</div>
        <table className="delhi-table">
          <thead>
            <tr>
              <th>Parameter</th>
              <th>Baseline</th>
              <th>Documented bounds</th>
              <th>Identifiability</th>
            </tr>
          </thead>
          <tbody>
            {data.calibration.parameter_registry.map((p) => (
              <tr key={p.parameter_name}>
                <td className="mono">{p.parameter_name}</td>
                <td className="mono">{p.baseline_value}</td>
                <td className="mono">
                  {p.lower_bound === null ? 'none documented' : `[${p.lower_bound}, ${p.upper_bound}]`}
                </td>
                <td className="reason-cell">{p.identifiability_status}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <div className="obs-block obs-model">
          <div className="obs-block-title">GLUE-STYLE BEHAVIORAL SCREEN (REAL RUNS)</div>
          <div className="obs-line">
            {data.calibration.glue_screen.n_samples} seeded samples ·{' '}
            {data.calibration.glue_screen.n_behavioral} behavioral ·{' '}
            {data.calibration.glue_screen.method}
          </div>
          <div className="obs-line">{data.calibration.glue_screen.discrimination_finding}</div>
        </div>
        <div className="delhi-note">
          Audit: {data.calibration.audit.status} —{' '}
          {Object.entries(data.calibration.audit.checks)
            .map(([k, val]) => `${k}: ${val}`)
            .join(' · ')}
        </div>
      </div>

      {/* Identifiability */}
      <div className="delhi-section flood-timeline-panel">
        <div className="delhi-section-head timeline-header timeline-header">
          <span className="delhi-section-title timeline-heading timeline-heading">IDENTIFIABILITY</span>
        </div>
        <div className="obs-line">{data.identifiability.summary}</div>
      </div>

      {/* Uncertainty */}
      <div className="delhi-section flood-timeline-panel">
        <div className="delhi-section-head timeline-header timeline-header">
          <span className="delhi-section-title timeline-heading timeline-heading">UNCERTAINTY DECOMPOSITION</span>
          <span className="delhi-section-hint">from real runs; never collapsed</span>
        </div>
        <table className="delhi-table">
          <thead>
            <tr>
              <th>Event</th>
              <th>Source</th>
              <th>Value</th>
              <th>Detail</th>
            </tr>
          </thead>
          <tbody>
            {data.uncertainty.map((row, i) => (
              <tr key={i}>
                <td className="mono">{row.event_id}</td>
                <td>{row.source}</td>
                <td className="mono">{row.value === null ? 'UNKNOWN' : `${(row.value * 100).toFixed(1)}%`}</td>
                <td className="reason-cell">{row.detail}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* ML */}
      <div className="delhi-section flood-timeline-panel">
        <div className="delhi-section-head timeline-header timeline-header">
          <span className="delhi-section-title timeline-heading timeline-heading">PHYSICS-GUIDED ML</span>
          <span className="delhi-prov-tag prov-unavailable">{data.ml.ml_status}</span>
        </div>
        <div className="obs-line">{data.ml.strategy}</div>
        <div className="delhi-note">{data.ml.reason}</div>
        <table className="delhi-table">
          <tbody>
            <tr>
              <td>Residual target</td>
              <td>
                {data.ml.dataset.residual_target.status} —{' '}
                {data.ml.dataset.residual_target.reason}
              </td>
            </tr>
            <tr>
              <td>Occurrence target</td>
              <td>
                {data.ml.dataset.occurrence_target.status} ·{' '}
                {data.ml.dataset.occurrence_target.usable_events} usable events (
                {data.ml.dataset.occurrence_target.positives} positive /{' '}
                {data.ml.dataset.occurrence_target.negatives} negative)
              </td>
            </tr>
            <tr>
              <td>Event-grouped CV</td>
              <td>
                {data.ml.dataset.event_grouped_cv.strategy} — gate:{' '}
                {data.ml.dataset.event_grouped_cv.gate}
              </td>
            </tr>
          </tbody>
        </table>
        <div className="delhi-note">{data.ml.fallback_contract}</div>
      </div>

      <div className="delhi-claim-policy">{data.claim_policy}</div>
    </div>
  );
};

export default ModelPanel;
