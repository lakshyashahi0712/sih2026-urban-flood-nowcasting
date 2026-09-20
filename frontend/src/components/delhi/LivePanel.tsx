import { useEffect } from 'react';
import type { LiveStateResponse, SurfaceHotspot } from '../../api/delhi';

type Horizon = 'NOW' | '+1h' | '+2h' | '+3h';

/**
 * LIVE-mode context panel: the nowcast ensemble summary for the selected
 * horizon plus the modelled street intel for that SAME horizon state.
 * Map overlays (depth polygons) come from the same per-horizon state —
 * one model state drives map + panels (V1 coherence rule).
 */
const LivePanel = ({
  liveState,
  horizon,
  onSurfaceHotspots,
}: {
  liveState: LiveStateResponse | null;
  horizon: Horizon;
  onSurfaceHotspots?: (hotspots: SurfaceHotspot[]) => void;
}) => {
  const hs = liveState?.horizons.find((h) => h.horizon === horizon) ?? null;

  // The horizon state's geo is rendered by DelhiApp (single source of map
  // overlays); this panel clears surface hotspots while in LIVE mode.
  useEffect(() => {
    onSurfaceHotspots?.([]);
  }, [onSurfaceHotspots]);

  if (!liveState) {
    return (
      <div className="delhi-panel-status">Acquiring forecast and evaluating horizons…</div>
    );
  }

  const computed = hs?.status === 'COMPUTED';
  const rainProv = hs?.rainfall_provenance ?? 'UNKNOWN';

  return (
    <div className="delhi-nowcast">
      {/* Operational status banner */}
      <div className={`delhi-banner ${computed ? 'banner-ok' : 'banner-warn'}`}>
        <div className="banner-main">
          <span className="banner-state">
            {liveState.rainfall_status === 'SYNTHETIC_FALLBACK'
              ? 'SYNTHETIC FALLBACK ACTIVE'
              : computed
                ? `HORIZON ${horizon} COMPUTED`
                : `HORIZON ${horizon} ${hs?.status ?? '…'}`}
          </span>
          <span className="banner-sub">
            {liveState.rainfall_status === 'SYNTHETIC_FALLBACK'
              ? 'Labeled demo rainfall — NOT observed, NOT a forecast.'
              : hs?.time_start
                ? `Hour beginning ${new Date(hs.time_start).toLocaleTimeString([], {
                    hour: '2-digit',
                    minute: '2-digit',
                  })} · rainfall provenance ${rainProv}`
                : liveState.diagnostics[0] ?? 'Waiting for forecast acquisition.'}
          </span>
        </div>
      </div>

      {/* V1 mass-balance footer for the active horizon */}
      {hs?.v1_mass_balance && (
        <div className="delhi-section flood-timeline-panel">
          <div className="delhi-section-head timeline-header">
            <span className="delhi-section-title timeline-heading">HORIZON WATER BALANCE (MODELLED)</span>
            <span className="delhi-prov-tag prov-computed">SIMULATED</span>
          </div>
          <table className="delhi-table">
            <tbody>
              <tr>
                <td>Catchment runoff (1 h)</td>
                <td className="mono">{Math.round(hs.v1_mass_balance.total_runoff_m3).toLocaleString()} m³</td>
              </tr>
              <tr>
                <td>Conveyed by street inlets</td>
                <td className="mono">{Math.round(hs.v1_mass_balance.conveyed_m3).toLocaleString()} m³</td>
              </tr>
              <tr>
                <td>Surcharged to surface</td>
                <td className="mono">{Math.round(hs.v1_mass_balance.surcharged_m3).toLocaleString()} m³</td>
              </tr>
              <tr>
                <td>Overflow beyond depression caps</td>
                <td className="mono">{Math.round(hs.v1_mass_balance.overflow_m3).toLocaleString()} m³</td>
              </tr>
              <tr>
                <td>Drained out of the window</td>
                <td className="mono">{Math.round(hs.v1_mass_balance.drained_out_m3).toLocaleString()} m³</td>
              </tr>
            </tbody>
          </table>
          <div className="delhi-note">
            Every horizon is simulated independently with ONLY its own hour's rainfall (V1 rule). Volumes
            are MODELLED — never observed.
          </div>
        </div>
      )}

      <div className="delhi-claim-policy">{liveState.claim_policy}</div>
    </div>
  );
};

export default LivePanel;
