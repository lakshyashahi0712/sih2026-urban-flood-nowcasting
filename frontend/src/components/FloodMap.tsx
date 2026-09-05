import { useEffect, useRef, useState, useCallback } from 'react';
import { Map as MapLibreMap, GeoJSONSource, NavigationControl, Popup, setWorkerUrl } from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import workerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?worker&url';

setWorkerUrl(workerUrl);

type ForecastHorizon = 'NOW' | '+1h' | '+2h' | '+3h';

interface RainfallRecordAPI {
  timestamp: string;
  interval_end: string;
  rainfall_mm: number;
  source: string;
  source_type: string;
  resolution_minutes: number;
  acquired_at: string;
  forecast_lead_minutes: number;
  status: 'LIVE' | 'STALE' | 'UNAVAILABLE';
  average_intensity_mm_per_hour: number;
}

interface RainfallSeriesAPI {
  source: string;
  acquired_at: string;
  record_count: number;
  resolution_minutes: number;
  records: RainfallRecordAPI[];
}

interface HorizonData {
  key: ForecastHorizon;
  label: string;
  periodDisplay: string;
  leadTime: string;
  rainfallMm: number | null;
  timestamp?: string;
  intervalEnd?: string;
}

const DEFAULT_HORIZONS: HorizonData[] = [
  { key: 'NOW', label: 'NOW', periodDisplay: 'Current Hour Baseline', leadTime: '0h', rainfallMm: null },
  { key: '+1h', label: '+1h', periodDisplay: '+1 Hour Outlook', leadTime: '+1h', rainfallMm: null },
  { key: '+2h', label: '+2h', periodDisplay: '+2 Hours Outlook', leadTime: '+2h', rainfallMm: null },
  { key: '+3h', label: '+3h', periodDisplay: '+3 Hours Outlook', leadTime: '+3h', rainfallMm: null },
];

interface RiskInfo {
  text: string;
  level: string;
  badgeClass: string;
  bannerBg: string;
  bannerBorder: string;
  textCol: string;
  depthCol: string;
  description: string;
}

function getRiskCategory(maxDepthM: number): RiskInfo {
  if (maxDepthM >= 2.0) {
    return {
      text: 'SEVERE',
      level: 'Critical Flood Risk',
      badgeClass: 'risk-severe',
      bannerBg: '#fef2f2',
      bannerBorder: '#f87171',
      textCol: '#991b1b',
      depthCol: '#7f1d1d',
      description: 'Major inundation • Life-safety hazard'
    };
  }
  if (maxDepthM >= 1.0) {
    return {
      text: 'HIGH',
      level: 'High Inundation Risk',
      badgeClass: 'risk-high',
      bannerBg: '#fff7ed',
      bannerBorder: '#fb923c',
      textCol: '#c2410c',
      depthCol: '#9a3412',
      description: 'Underpass & low-lying street flooding'
    };
  }
  if (maxDepthM >= 0.5) {
    return {
      text: 'HIGH',
      level: 'Significant Flood Risk',
      badgeClass: 'risk-high',
      bannerBg: '#fff7ed',
      bannerBorder: '#fdba74',
      textCol: '#c2410c',
      depthCol: '#ea580c',
      description: 'Curb overflow • Roadway disruption'
    };
  }
  if (maxDepthM > 0.0) {
    return {
      text: 'MODERATE',
      level: 'Localized Waterlogging',
      badgeClass: 'risk-mod',
      bannerBg: '#fefce8',
      bannerBorder: '#facc15',
      textCol: '#854d0e',
      depthCol: '#ca8a04',
      description: 'Minor street pooling in depressions'
    };
  }
  return {
    text: 'LOW',
    level: 'Nominal Conditions',
    badgeClass: 'risk-low',
    bannerBg: '#f8fafc',
    bannerBorder: '#cbd5e1',
    textCol: '#334155',
    depthCol: '#0f172a',
    description: 'No significant surface ponding'
  };
}

const FloodMap = () => {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<MapLibreMap | null>(null);
  const popupRef = useRef<Popup | null>(null);

  const [activeHorizon, setActiveHorizon] = useState<ForecastHorizon>('+1h');
  const [horizons, setHorizons] = useState<HorizonData[]>(DEFAULT_HORIZONS);
  const [rainfallStatus, setRainfallStatus] = useState<'LIVE' | 'STALE' | 'UNAVAILABLE'>('UNAVAILABLE');
  const [rainfallAcquiredAt, setRainfallAcquiredAt] = useState<string | null>(null);
  const [floodData, setFloodData] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const horizonsRef = useRef<HorizonData[]>(DEFAULT_HORIZONS);
  horizonsRef.current = horizons;
  const activeHorizonRef = useRef<ForecastHorizon>(activeHorizon);
  activeHorizonRef.current = activeHorizon;

  const currentHorizonConfig = horizons.find(h => h.key === activeHorizon) || horizons[1];

  const runSimulationForHorizon = useCallback(async (horizon: ForecastHorizon, horizonList: HorizonData[]) => {
    const config = horizonList.find(h => h.key === horizon);
    if (!config) return;

    if (config.rainfallMm === null) {
      setError(`No rainfall forecast available for ${horizon}`);
      setFloodData(null);
      const map = mapInstanceRef.current;
      if (map) {
        const source = map.getSource('flood-depth') as GeoJSONSource | undefined;
        if (source) {
          source.setData({ type: 'FeatureCollection', features: [] });
        }
      }
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await fetch('http://localhost:8000/flood/model', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          rainfall_mm: config.rainfallMm,
          contributing_area_m2: 5000.0,
          runoff_coefficient: 0.7,
          timestep_hours: 1.0, // Fixed 60-min model timestep for simulation
          threshold_area_m2: 10.0
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error ${response.status}`);
      }

      const data = await response.json();
      setFloodData(data);

      const map = mapInstanceRef.current;
      if (map) {
        const source = map.getSource('flood-depth') as GeoJSONSource | undefined;
        if (source) {
          source.setData(data);
        }
      }
    } catch (err) {
      console.error('Error fetching flood data:', err);
      setError(err instanceof Error ? err.message : 'Unknown network error');
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchRainfallAndSimulate = useCallback(async (targetHorizon: ForecastHorizon) => {
    let updatedHorizons = horizonsRef.current;
    try {
      const res = await fetch('http://localhost:8000/rainfall/mumbai?use_cache=true');
      if (!res.ok) {
        throw new Error(`Rainfall API returned HTTP ${res.status}`);
      }
      const data: RainfallSeriesAPI = await res.json();
      if (!data.records || !Array.isArray(data.records) || data.records.length === 0) {
        throw new Error('Received empty or malformed rainfall records from Open-Meteo');
      }

      const rec0 = data.records[0];
      const status = (rec0?.status as 'LIVE' | 'STALE') || 'LIVE';
      setRainfallStatus(status);
      setRainfallAcquiredAt(data.acquired_at || null);

      const keys: ForecastHorizon[] = ['NOW', '+1h', '+2h', '+3h'];
      const periodDisplays = [
        'Current Hour Baseline',
        '+1 Hour Outlook (T+1h)',
        '+2 Hours Outlook (T+2h)',
        '+3 Hours Outlook (T+3h)',
      ];
      const leadTimes = ['0h', '+1h', '+2h', '+3h'];

      updatedHorizons = keys.map((key, idx) => {
        const rec = data.records[idx];
        return {
          key,
          label: key,
          periodDisplay: periodDisplays[idx],
          leadTime: leadTimes[idx],
          rainfallMm: rec != null && typeof rec.rainfall_mm === 'number' ? rec.rainfall_mm : null,
          timestamp: rec?.timestamp,
          intervalEnd: rec?.interval_end,
        };
      });

      setHorizons(updatedHorizons);
      horizonsRef.current = updatedHorizons;
    } catch (err) {
      console.error('Rainfall fetch failed:', err);
      setRainfallStatus('UNAVAILABLE');
      setError(err instanceof Error ? err.message : 'Rainfall API unavailable');
    }

    await runSimulationForHorizon(targetHorizon, updatedHorizons);
  }, [runSimulationForHorizon]);

  // Initialize Map
  useEffect(() => {
    if (!mapContainerRef.current) return;

    const newMap = new MapLibreMap({
      container: mapContainerRef.current,
      style: 'https://tiles.openfreemap.org/styles/liberty',
      center: [72.8777, 19.0760],
      zoom: 11
    });

    newMap.addControl(new NavigationControl({ visualizePitch: true }), 'top-right');

    newMap.on('error', (e) => {
      console.error('MapLibre runtime error:', e);
    });

    newMap.on('load', () => {
      mapInstanceRef.current = newMap;

      // Add flood source
      newMap.addSource('flood-depth', {
        type: 'geojson',
        data: { type: 'FeatureCollection', features: [] }
      });

      // Flood polygon fill with high visual prominence
      newMap.addLayer({
        id: 'flood-depth-layer',
        type: 'fill',
        source: 'flood-depth',
        paint: {
          'fill-color': [
            'interpolate',
            ['linear'],
            ['get', 'depth'],
            0, '#ffeda0',
            0.5, '#feb24c',
            1.0, '#f03b20',
            2.0, '#bd0026'
          ],
          'fill-opacity': 0.85
        }
      });

      // Outer dark contrast boundary
      newMap.addLayer({
        id: 'flood-depth-halo',
        type: 'line',
        source: 'flood-depth',
        paint: {
          'line-color': '#0f172a',
          'line-width': 2.5,
          'line-opacity': 0.8
        }
      });

      // Inner crisp white boundary
      newMap.addLayer({
        id: 'flood-depth-outline',
        type: 'line',
        source: 'flood-depth',
        paint: {
          'line-color': '#ffffff',
          'line-width': 1.2,
          'line-opacity': 0.95
        }
      });

      // Interactive popup on cell click
      newMap.on('click', 'flood-depth-layer', (e) => {
        if (!e.features || e.features.length === 0) return;
        const feature = e.features[0];
        const depth = feature.properties?.depth != null ? Number(feature.properties.depth) : 0;
        const depthM = depth.toFixed(2);
        const depthCm = Math.round(depth * 100);
        const risk = getRiskCategory(depth);
        const activeCfg = horizonsRef.current.find(h => h.key === activeHorizonRef.current);
        const rainStr = activeCfg && activeCfg.rainfallMm !== null ? `${activeCfg.rainfallMm.toFixed(1)} mm` : 'N/A';

        if (popupRef.current) {
          popupRef.current.remove();
        }

        popupRef.current = new Popup({ closeButton: true, closeOnClick: true, className: 'ops-popup' })
          .setLngLat(e.lngLat)
          .setHTML(`
            <div class="popup-box">
              <div class="popup-header">
                <span class="popup-title">PROTOTYPE FLOOD CELL (10 m)</span>
                <span class="popup-badge ${risk.badgeClass}">${risk.text}</span>
              </div>
              <div class="popup-body">
                <div class="popup-row">
                  <span class="lbl">Predicted depth:</span>
                  <span class="val bold">${depthM} m (${depthCm} cm)</span>
                </div>
                <div class="popup-row">
                  <span class="lbl">Risk classification:</span>
                  <span class="val">${risk.text}</span>
                </div>
                <div class="popup-row">
                  <span class="lbl">Forecast horizon:</span>
                  <span class="val">${activeHorizonRef.current} (${rainStr})</span>
                </div>
                <div class="popup-row">
                  <span class="lbl">Rainfall source:</span>
                  <span class="val">Weather forecast (Open-Meteo hourly NWP)</span>
                </div>
                <div class="popup-row">
                  <span class="lbl">Data status:</span>
                  <span class="val status-modelled">Modelled (Prototype DEM)</span>
                </div>
              </div>
            </div>
          `)
          .addTo(newMap);
      });

      // Pointer cursor on hover over flooded cells
      newMap.on('mouseenter', 'flood-depth-layer', () => {
        newMap.getCanvas().style.cursor = 'pointer';
      });
      newMap.on('mouseleave', 'flood-depth-layer', () => {
        newMap.getCanvas().style.cursor = '';
      });

      // Trigger initial data load
      fetchRainfallAndSimulate('+1h');
    });

    return () => {
      if (popupRef.current) {
        popupRef.current.remove();
      }
      newMap.remove();
      mapInstanceRef.current = null;
    };
  }, [fetchRainfallAndSimulate]);

  // Handle horizon change
  const handleHorizonChange = (h: ForecastHorizon) => {
    if (popupRef.current) {
      popupRef.current.remove();
    }
    setActiveHorizon(h);
    runSimulationForHorizon(h, horizonsRef.current);
  };

  // Operational view navigation
  const handleResetOverview = () => {
    if (!mapInstanceRef.current) return;
    mapInstanceRef.current.flyTo({
      center: [72.8777, 19.0760],
      zoom: 11,
      duration: 1000
    });
  };

  const handleFocusFloodParcel = () => {
    if (!mapInstanceRef.current) return;
    mapInstanceRef.current.flyTo({
      center: [72.8785, 19.0751],
      zoom: 17.5,
      duration: 1200
    });
  };

  // Extract statistics from floodData summary
  const maxDepthM = floodData?.summary?.max_depth_m ?? 0;
  const floodedAreaM2 = floodData?.summary?.total_flooded_area_m2 ?? 0;
  const riskInfo = getRiskCategory(maxDepthM);

  return (
    <div className="flood-app">
      {/* 1. TOP BAR: IMMEDIATE 3-SECOND SYSTEM IDENTITY */}
      <header className="app-topbar">
        <div className="topbar-left">
          <div className="system-identity">
            <span className="system-mark">⛯</span>
            <span className="system-title">URBAN FLOOD NOWCAST</span>
          </div>
          <span className="topbar-sep">|</span>
          <div className="system-location">
            <span className="loc-label">MUMBAI</span>
          </div>
          <span className="topbar-sep">|</span>
          <div className="system-subtitle">
            <span>0–3 HOUR FLOOD OUTLOOK</span>
          </div>
          <div className="prototype-status-pill">
            <span className="status-dot" />
            <span>PROTOTYPE SCENARIO</span>
          </div>
        </div>

        <div className="topbar-right">
          <div className="telemetry-info">
            <span className="meta-tag">60-MIN TIMESTEP</span>
            <span className="meta-divider">•</span>
            <span className="meta-label">SOURCE:</span>
            <span className="meta-val">Open-Meteo NWP ({rainfallStatus})</span>
            <span className="meta-divider">•</span>
            <span className="meta-label">ACQUIRED:</span>
            <span className="meta-val">
              {rainfallAcquiredAt
                ? new Date(rainfallAcquiredAt).toLocaleTimeString('en-IN', {
                    hour: '2-digit',
                    minute: '2-digit',
                    timeZone: 'Asia/Kolkata',
                  }) + ' IST'
                : 'Connecting...'}
            </span>
          </div>
        </div>
      </header>

      {/* 2. MAP WORKSPACE */}
      <div className="map-workspace">
        <div ref={mapContainerRef} className="map-viewport" />

        {/* FORECAST TIMELINE CONTROLS (Top Left Overlay) */}
        <div className="flood-timeline-panel">
          <div className="timeline-header">
            <span className="timeline-heading">FLOOD OUTLOOK</span>
            <span className="timeline-active-tag">Active: {currentHorizonConfig.label}</span>
          </div>
          <div className="timeline-stepper">
            {horizons.map((h) => {
              const isSelected = activeHorizon === h.key;
              const rainTag = h.rainfallMm !== null ? `${h.rainfallMm.toFixed(1)}mm` : '--mm';
              return (
                <button
                  key={h.key}
                  type="button"
                  className={`timeline-step-btn ${isSelected ? 'selected' : ''}`}
                  onClick={() => handleHorizonChange(h.key)}
                >
                  <span className="step-time">{h.label}</span>
                  <span className="step-rain-tag">{rainTag}</span>
                </button>
              );
            })}
          </div>
        </div>

        {/* MAP EXTENT CONTROLS */}
        <div className="map-extent-tools">
          <button type="button" className="extent-btn" onClick={handleResetOverview} title="Reset to full Mumbai region">
            ⛶ Full Extent (Mumbai)
          </button>
          <button type="button" className="extent-btn highlight" onClick={handleFocusFloodParcel} title="Center on 10m prototype flood cell">
            🎯 Target Zone (10m Cell)
          </button>
        </div>

        {/* FLOOD STATUS & RISK ASSESSMENT PANEL (High Visual Hierarchy) */}
        <div className="flood-status-panel">
          <div className="status-panel-top">
            <div className="status-horizon-kicker">PREDICTED CONDITIONS</div>
            <div className="status-horizon-title">{currentHorizonConfig.periodDisplay}</div>
          </div>

          {/* PRIMARY HERO CALLOUT: RISK & PEAK DEPTH */}
          <div
            className="status-hero-card"
            style={{
              backgroundColor: riskInfo.bannerBg,
              borderColor: riskInfo.bannerBorder
            }}
          >
            <div className="hero-risk-header">
              <span className="hero-risk-kicker" style={{ color: riskInfo.textCol }}>
                PREDICTED RISK
              </span>
              <span className={`hero-risk-badge ${riskInfo.badgeClass}`}>
                {riskInfo.text}
              </span>
            </div>
            <div className="hero-depth-row">
              <div className="depth-digit-group">
                <span className="depth-large" style={{ color: riskInfo.depthCol }}>
                  {Number(maxDepthM).toFixed(2)}
                </span>
                <span className="depth-metric-unit">m</span>
              </div>
              <div className="depth-context-label">
                <div className="context-primary">Peak Inundation</div>
                <div className="context-secondary">{Math.round(maxDepthM * 100)} cm depth</div>
              </div>
            </div>
            <div className="hero-impact-note" style={{ color: riskInfo.textCol }}>
              {riskInfo.description}
            </div>
          </div>

          {/* SECONDARY METRICS: FORECAST RAINFALL & FLOODED AREA */}
          <div className="status-metric-grid">
            <div className="grid-metric-box">
              <span className="metric-box-label">FORECAST RAINFALL</span>
              <span className="metric-box-val">
                {currentHorizonConfig.rainfallMm !== null
                  ? currentHorizonConfig.rainfallMm.toFixed(1)
                  : '--'}{' '}
                <span className="sub-unit">mm</span>
              </span>
              <span className="metric-box-sub">
                Weather forecast (Open-Meteo hourly NWP)
              </span>
            </div>
            <div className="grid-metric-box">
              <span className="metric-box-label">INUNDATED AREA</span>
              <span className="metric-box-val">{Math.round(floodedAreaM2)} <span className="sub-unit">m²</span></span>
              <span className="metric-box-sub">10m grid cell</span>
            </div>
          </div>

          {/* SIMULATION SUMMARY FOOTER */}
          <div className="status-panel-footer">
            <div className="footer-engine-title">MODEL PIPELINE</div>
            <div className="footer-engine-desc">
              Rainfall–runoff + drainage capacity + surface routing
            </div>
            <div className="footer-engine-param">
              Runoff C = 0.7 • 60-minute model timestep
            </div>
          </div>
        </div>

        {/* DATA STATUS & PROVENANCE (Bottom Left, Clear but Secondary) */}
        <div className="provenance-card">
          <div className="provenance-header">DATA PROVENANCE & STATUS</div>
          <div className="provenance-list">
            <div className="provenance-item">
              <span className="prov-source">Rainfall</span>
              <span className={`prov-tag ${rainfallStatus === 'LIVE' ? 'tag-modelled' : 'tag-prototype'}`}>
                Open-Meteo NWP ({rainfallStatus})
              </span>
            </div>
            <div className="provenance-item">
              <span className="prov-source">Flood depth</span>
              <span className="prov-tag tag-modelled">Modelled</span>
            </div>
            <div className="provenance-item">
              <span className="prov-source">Drainage</span>
              <span className="prov-tag tag-prototype">DEM-derived / prototype</span>
            </div>
            <div className="provenance-item">
              <span className="prov-source">Surface routing</span>
              <span className="prov-tag tag-modelled">Modelled (D8)</span>
            </div>
          </div>
          <div className="provenance-disclaimer">
            NOTICE: Weather forecast sourced from Open-Meteo hourly NWP (not radar nowcast or observed rainfall). Prototype DEM used for surface simulation.
          </div>
        </div>

        {/* FLOOD DEPTH LEGEND (Bottom Right) */}
        <div className="flood-legend-card">
          <div className="legend-heading">Modelled flood depth</div>
          <div className="legend-scale">
            <div className="legend-grade">
              <span className="grade-color" style={{ backgroundColor: '#ffeda0' }} />
              <span className="grade-range">0.0 – 0.5 m</span>
              <span className="grade-desc">Minor</span>
            </div>
            <div className="legend-grade">
              <span className="grade-color" style={{ backgroundColor: '#feb24c' }} />
              <span className="grade-range">0.5 – 1.0 m</span>
              <span className="grade-desc">Moderate</span>
            </div>
            <div className="legend-grade">
              <span className="grade-color" style={{ backgroundColor: '#f03b20' }} />
              <span className="grade-range">1.0 – 2.0 m</span>
              <span className="grade-desc">High</span>
            </div>
            <div className="legend-grade">
              <span className="grade-color" style={{ backgroundColor: '#bd0026' }} />
              <span className="grade-range">2.0+ m</span>
              <span className="grade-desc">Severe</span>
            </div>
          </div>
        </div>

        {/* LOADING & ERROR BANNERS */}
        {loading && (
          <div className="map-banner-status">
            <span className="banner-spinner" /> Simulating flood nowcast...
          </div>
        )}
        {error && (
          <div className="map-banner-error">
            Simulation Error: {error} (Backend :8000)
          </div>
        )}
      </div>
    </div>
  );
};

export default FloodMap;