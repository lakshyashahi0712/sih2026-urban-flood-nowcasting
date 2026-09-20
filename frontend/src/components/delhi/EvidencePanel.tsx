import { useEffect, useState } from 'react';
import {
  delhiApi,
  type DelhiStatus,
  type EnsembleResponse,
  type NetworkResponse,
} from '../../api/delhi';

const EvidencePanel = () => {
  const [status, setStatus] = useState<DelhiStatus | null>(null);
  const [network, setNetwork] = useState<NetworkResponse | null>(null);
  const [ensemble, setEnsemble] = useState<EnsembleResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const [s, n, e] = await Promise.all([
          delhiApi.getStatus(),
          delhiApi.getNetwork(),
          delhiApi.getEnsemble(),
        ]);
        setStatus(s);
        setNetwork(n);
        setEnsemble(e);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'failed to load evidence');
      }
    })();
  }, []);

  if (error) {
    return <div className="delhi-panel-status delhi-panel-error">{error}</div>;
  }
  if (!status || !network || !ensemble) {
    return <div className="delhi-panel-status">Loading model evidence…</div>;
  }

  return (
    <div className="delhi-evidence">
      {/* System identity + objective */}
      <div className="delhi-section flood-timeline-panel">
        <div className="delhi-section-head timeline-header timeline-header">
          <span className="delhi-section-title timeline-heading timeline-heading">SYSTEM</span>
        </div>
        <p className="delhi-objective">{status.objective}</p>
        <div className="delhi-capabilities">
          {status.capabilities.map((c) => (
            <div key={c} className="cap-row">
              <span className="cap-dot ok">●</span> {c}
            </div>
          ))}
        </div>
      </div>

      {/* Reach chain */}
      <div className="delhi-section flood-timeline-panel">
        <div className="delhi-section-head timeline-header timeline-header">
          <span className="delhi-section-title timeline-heading timeline-heading">
            KUSHAK REACH CHAIN ({(network.total_length_m / 1000).toFixed(2)} km)
          </span>
          <span className="delhi-prov-tag">EVIDENCE-TIERED</span>
        </div>
        <table className="delhi-table">
          <thead>
            <tr>
              <th>Reach</th>
              <th>Chainage (m)</th>
              <th>Type</th>
              <th>Tier</th>
              <th>Evidence status</th>
            </tr>
          </thead>
          <tbody>
            {network.reaches.map((r) => (
              <tr key={r.reach_id}>
                <td className="mono">{r.reach_id}</td>
                <td className="mono">
                  {r.start_chainage_m} – {r.end_chainage_m}
                </td>
                <td>{r.reach_type}</td>
                <td>{r.tier}</td>
                <td className="reach-status">{r.hydraulic_status}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <div className="delhi-note">{network.catchment_note}</div>
      </div>

      {/* Ensemble provenance */}
      <div className="delhi-section flood-timeline-panel">
        <div className="delhi-section-head timeline-header timeline-header">
          <span className="delhi-section-title timeline-heading timeline-heading">
            DETERMINISTIC ENSEMBLE ({ensemble.member_count} members)
          </span>
        </div>
        <div className="delhi-note">{ensemble.construction}</div>
        <table className="delhi-table">
          <thead>
            <tr>
              <th>Hydraulic scenario</th>
              <th>mult_box</th>
              <th>mult_open</th>
              <th>f_open_depot</th>
              <th>Provenance</th>
            </tr>
          </thead>
          <tbody>
            {ensemble.members
              .filter(
                (m, i, arr) =>
                  arr.findIndex((x) => x.hydraulic_scenario.id === m.hydraulic_scenario.id) === i,
              )
              .map((m) => (
                <tr key={m.member_id}>
                  <td className="mono">{m.hydraulic_scenario.id}</td>
                  <td className="mono">
                    {m.hydraulic_scenario.mult_box} [{m.hydraulic_scenario.mult_box_range.join('–')}]
                  </td>
                  <td className="mono">
                    {m.hydraulic_scenario.mult_open} [{m.hydraulic_scenario.mult_open_range.join('–')}]
                  </td>
                  <td className="mono">
                    {m.hydraulic_scenario.f_open_depot} [
                    {m.hydraulic_scenario.f_open_depot_range.join('–')}]
                  </td>
                  <td>INFERRED_EFFECTIVE (not surveyed/calibrated)</td>
                </tr>
              ))}
          </tbody>
        </table>
        <table className="delhi-table">
          <thead>
            <tr>
              <th>Catchment scenario</th>
              <th>Area</th>
              <th>Provenance</th>
              <th>Note</th>
            </tr>
          </thead>
          <tbody>
            {ensemble.members
              .filter(
                (m, i, arr) =>
                  arr.findIndex((x) => x.catchment_scenario.id === m.catchment_scenario.id) === i,
              )
              .map((m) => (
                <tr key={m.member_id}>
                  <td className="mono">{m.catchment_scenario.id}</td>
                  <td className="mono">{m.catchment_scenario.area_km2} km²</td>
                  <td>{m.catchment_scenario.provenance}</td>
                  <td>{m.catchment_scenario.note}</td>
                </tr>
              ))}
          </tbody>
        </table>
        <div className="delhi-note">
          Runoff coefficient C = 0.75 (ASSUMED). Historical ~35.4 km² catchment
          extent is UNKNOWN and is never silently substituted.
        </div>
      </div>

      {/* Explicit non-claims */}
      <div className="delhi-section flood-timeline-panel">
        <div className="delhi-section-head timeline-header timeline-header">
          <span className="delhi-section-title timeline-heading timeline-heading">WHAT THIS SYSTEM DOES NOT CLAIM</span>
          <span className="delhi-prov-tag prov-unavailable">SCIENTIFIC HONESTY</span>
        </div>
        <div className="delhi-nonclaims">
          {status.explicit_non_claims.map((c) => (
            <div key={c} className="nonclaim-row">
              <span className="nonclaim-x">✕</span> {c}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default EvidencePanel;
