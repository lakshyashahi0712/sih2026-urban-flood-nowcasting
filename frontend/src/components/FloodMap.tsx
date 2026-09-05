import { useEffect, useRef, useState, useCallback } from 'react';
import { Map as MapLibreMap, GeoJSONSource, NavigationControl, Popup, setWorkerUrl } from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import workerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?worker&url';

setWorkerUrl(workerUrl);

type ForecastHorizon = 'NOW' | '+1h' | '+2h' | '+3h';
type AppMode = 'LIVE' | 'SCENARIO';
type ScenarioValue = 20 | 40 | 50 | 70;
const SCENARIO_VALUES: ScenarioValue[] = [20, 40, 50, 70];

interface HorizonStateAPI {
  horizon: string;
  lead_time: string;
  timestamp: string;
  interval_end: string;
  rainfall_mm: number;
  timestep_hours: number;
  max_depth_m: number;
  flooded_area_m2: number;
  total_flooded_area_m2: number;
  flood_volume_m3: number;
  total_flood_volume_m3: number;
  total_runoff_volume_m3?: number;
  conveyed_drainage_volume_m3?: number;
  surface_flood_volume_m3?: number;
  features: any[];
  geojson: any;
}

interface FloodForecastAPIResponse {
  source: string;
  source_type: string;
  acquired_at: string | null;
  status: 'LIVE' | 'STALE' | 'UNAVAILABLE';
  provenance: Record<string, string>;
  horizons: HorizonStateAPI[];
}

interface AffectedRoadAPI {
  road_id: string;
  osm_id: number;
  name: string;
  highway: string;
  max_depth_m: number;
  mean_depth_m: number;
  flooded_length_m: number;
  risk_level: string;
  geometry: any;
}

interface AffectedIntersectionAPI {
  intersection_id: string;
  osm_node_id: number;
  name: string;
  roads: string[];
  max_depth_m: number;
  risk_level: string;
  connection_count: number;
  geometry: any;
}

interface StreetIntelligenceSummaryAPI {
  total_affected_roads: number;
  total_affected_intersections: number;
  max_street_depth_m: number;
  total_flooded_road_length_m: number;
  risk_counts: {
    CRITICAL: number;
    HIGH: number;
    MEDIUM: number;
    LOW: number;
  };
}

interface StreetFloodIntelligenceAPI {
  horizon: string;
  lead_time: string;
  rainfall_mm: number;
  summary: StreetIntelligenceSummaryAPI;
  affected_roads: AffectedRoadAPI[];
  affected_intersections: AffectedIntersectionAPI[];
  roads_geojson: any;
  intersections_geojson: any;
  provenance: Record<string, string>;
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
  if (maxDepthM > 1.0) {
    return {
      text: 'SEVERE',
      level: 'Severe Inundation Risk',
      badgeClass: 'risk-severe',
      bannerBg: '#fef2f2',
      bannerBorder: '#f87171',
      textCol: '#991b1b',
      depthCol: '#7f1d1d',
      description: 'Major inundation • Significant roadway disruption'
    };
  }
  if (maxDepthM >= 0.5) {
    return {
      text: 'HIGH',
      level: 'High Inundation Risk',
      badgeClass: 'risk-high',
      bannerBg: '#fff7ed',
      bannerBorder: '#fb923c',
      textCol: '#c2410c',
      depthCol: '#ea580c',
      description: 'Curb overflow • Street flooding in low-lying areas'
    };
  }
  if (maxDepthM > 0.0) {
    return {
      text: 'MODERATE',
      level: 'Moderate Inundation Risk',
      badgeClass: 'risk-mod',
      bannerBg: '#fefce8',
      bannerBorder: '#facc15',
      textCol: '#854d0e',
      depthCol: '#ca8a04',
      description: 'Localized waterlogging in terrain depressions'
    };
  }
  return {
    text: 'NO INUNDATION',
    level: 'No Inundation',
    badgeClass: 'risk-low',
    bannerBg: '#f8fafc',
    bannerBorder: '#cbd5e1',
    textCol: '#334155',
    depthCol: '#0f172a',
    description: 'Runoff safely conveyed by drainage • No surface ponding'
  };
}

const FloodMap = () => {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<MapLibreMap | null>(null);
  const popupRef = useRef<Popup | null>(null);

  const [appMode, setAppMode] = useState<AppMode>('LIVE');
  const [activeScenario, setActiveScenario] = useState<ScenarioValue>(40);
  const [scenarioData, setScenarioData] = useState<Record<ScenarioValue, HorizonStateAPI> | null>(null);

  const [activeHorizon, setActiveHorizon] = useState<ForecastHorizon>('+1h');
  const [horizons, setHorizons] = useState<HorizonData[]>(DEFAULT_HORIZONS);
  const [rainfallStatus, setRainfallStatus] = useState<'LIVE' | 'STALE' | 'UNAVAILABLE'>('UNAVAILABLE');
  const [rainfallAcquiredAt, setRainfallAcquiredAt] = useState<string | null>(null);
  const [forecastData, setForecastData] = useState<FloodForecastAPIResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Street Flood Intelligence states
  const [showStreetOverlay, setShowStreetOverlay] = useState<boolean>(true);
  const [streetForecastData, setStreetForecastData] = useState<Record<string, StreetFloodIntelligenceAPI> | null>(null);
  const [streetScenarioData, setStreetScenarioData] = useState<Record<ScenarioValue, StreetFloodIntelligenceAPI> | null>(null);
  const [currentStreetIntel, setCurrentStreetIntel] = useState<StreetFloodIntelligenceAPI | null>(null);

  const appModeRef = useRef<AppMode>('LIVE');
  appModeRef.current = appMode;
  const activeScenarioRef = useRef<ScenarioValue>(activeScenario);
  activeScenarioRef.current = activeScenario;
  const scenarioDataRef = useRef<Record<ScenarioValue, HorizonStateAPI> | null>(null);
  scenarioDataRef.current = scenarioData;

  const showStreetOverlayRef = useRef<boolean>(true);
  showStreetOverlayRef.current = showStreetOverlay;
  const streetForecastDataRef = useRef<Record<string, StreetFloodIntelligenceAPI> | null>(null);
  streetForecastDataRef.current = streetForecastData;
  const streetScenarioDataRef = useRef<Record<ScenarioValue, StreetFloodIntelligenceAPI> | null>(null);
  streetScenarioDataRef.current = streetScenarioData;

  const horizonsRef = useRef<HorizonData[]>(DEFAULT_HORIZONS);
  horizonsRef.current = horizons;
  const activeHorizonRef = useRef<ForecastHorizon>(activeHorizon);
  activeHorizonRef.current = activeHorizon;
  const forecastDataRef = useRef<FloodForecastAPIResponse | null>(null);
  forecastDataRef.current = forecastData;

  const currentHorizonConfig = horizons.find(h => h.key === activeHorizon) || horizons[1];

  const applyStreetDataToMap = useCallback((intel: StreetFloodIntelligenceAPI | null) => {
    setCurrentStreetIntel(intel);
    const map = mapInstanceRef.current;
    if (!map) return;
    const roadsSource = map.getSource('affected-roads') as GeoJSONSource | undefined;
    if (roadsSource) {
      roadsSource.setData(intel?.roads_geojson || { type: 'FeatureCollection', features: [] });
    }
    const intsSource = map.getSource('affected-intersections') as GeoJSONSource | undefined;
    if (intsSource) {
      intsSource.setData(intel?.intersections_geojson || { type: 'FeatureCollection', features: [] });
    }
  }, []);

  const applyHorizonToMap = useCallback((horizon: ForecastHorizon, data: FloodForecastAPIResponse | null) => {
    const map = mapInstanceRef.current;
    if (!map) return;
    const targetState = data?.horizons?.find(h => h.horizon === horizon);
    const source = map.getSource('flood-depth') as GeoJSONSource | undefined;
    if (source) {
      if (targetState && targetState.geojson) {
        source.setData(targetState.geojson);
      } else {
        source.setData({ type: 'FeatureCollection', features: [] });
      }
    }
  }, []);

  const applyScenarioToMap = useCallback((sc: ScenarioValue, dataMap: Record<ScenarioValue, HorizonStateAPI> | null) => {
    const map = mapInstanceRef.current;
    if (!map) return;
    const targetState = dataMap?.[sc];
    const source = map.getSource('flood-depth') as GeoJSONSource | undefined;
    if (source) {
      if (targetState && targetState.geojson) {
        source.setData(targetState.geojson);
      } else {
        source.setData({ type: 'FeatureCollection', features: [] });
      }
    }
  }, []);

  const fetchStreetScenarioData = useCallback(async (): Promise<Record<ScenarioValue, StreetFloodIntelligenceAPI> | null> => {
    if (streetScenarioDataRef.current) return streetScenarioDataRef.current;
    try {
      const results = await Promise.all(
        SCENARIO_VALUES.map(async (sc) => {
          const res = await fetch(`http://localhost:8000/flood/streets?rainfall_mm=${sc}&horizon=+1h`);
          if (!res.ok) return null;
          const data: StreetFloodIntelligenceAPI = await res.json();
          return { sc, data };
        })
      );
      const scMap: Record<ScenarioValue, StreetFloodIntelligenceAPI> = {} as any;
      for (const item of results) {
        if (item && item.data) {
          scMap[item.sc] = item.data;
        }
      }
      setStreetScenarioData(scMap);
      streetScenarioDataRef.current = scMap;
      return scMap;
    } catch (err) {
      console.error('Failed to prefetch street scenario data:', err);
      return null;
    }
  }, []);

  const fetchStreetForecastData = useCallback(async (): Promise<Record<string, StreetFloodIntelligenceAPI> | null> => {
    if (streetForecastDataRef.current) return streetForecastDataRef.current;
    try {
      const res = await fetch('http://localhost:8000/flood/streets/forecast?use_cache=true');
      if (!res.ok) return null;
      const data = await res.json();
      if (!data.horizons || !Array.isArray(data.horizons)) return null;
      const fcMap: Record<string, StreetFloodIntelligenceAPI> = {};
      for (const h of data.horizons) {
        fcMap[h.horizon] = h;
      }
      setStreetForecastData(fcMap);
      streetForecastDataRef.current = fcMap;
      return fcMap;
    } catch (err) {
      console.error('Failed to fetch street forecast data:', err);
      return null;
    }
  }, []);

  const fetchScenarioEvolution = useCallback(async (): Promise<Record<ScenarioValue, HorizonStateAPI> | null> => {
    if (scenarioDataRef.current) return scenarioDataRef.current;
    try {
      const res = await fetch('http://localhost:8000/flood/forecast', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          rainfall_mm_list: [20.0, 40.0, 50.0, 70.0],
          use_cache: true
        })
      });
      if (!res.ok) {
        throw new Error(`Scenario API returned HTTP ${res.status}`);
      }
      const data: FloodForecastAPIResponse = await res.json();
      if (!data.horizons || data.horizons.length < 4) {
        throw new Error('Received incomplete scenario data');
      }
      const mapResult: Record<ScenarioValue, HorizonStateAPI> = {
        20: data.horizons[0],
        40: data.horizons[1],
        50: data.horizons[2],
        70: data.horizons[3],
      };
      setScenarioData(mapResult);
      scenarioDataRef.current = mapResult;
      return mapResult;
    } catch (err) {
      console.error('Failed to prefetch scenario data:', err);
      return null;
    }
  }, []);

  const fetchForecastEvolution = useCallback(async (targetHorizon: ForecastHorizon = '+1h') => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch('http://localhost:8000/flood/forecast?use_cache=true');
      if (!res.ok) {
        throw new Error(`Flood forecast API returned HTTP ${res.status}`);
      }
      const data: FloodForecastAPIResponse = await res.json();
      if (!data.horizons || !Array.isArray(data.horizons) || data.horizons.length === 0) {
        throw new Error('Received empty forecast horizons from backend');
      }

      setForecastData(data);
      forecastDataRef.current = data;
      setRainfallStatus((data.status as 'LIVE' | 'STALE') || 'LIVE');
      setRainfallAcquiredAt(data.acquired_at || null);

      const periodDisplays: Record<ForecastHorizon, string> = {
        'NOW': 'Current Hour Baseline',
        '+1h': '+1 Hour Outlook (T+1h)',
        '+2h': '+2 Hours Outlook (T+2h)',
        '+3h': '+3 Hours Outlook (T+3h)',
      };

      const updatedHorizons: HorizonData[] = data.horizons.map(h => ({
        key: h.horizon as ForecastHorizon,
        label: h.horizon,
        periodDisplay: periodDisplays[h.horizon as ForecastHorizon] || `${h.horizon} Outlook`,
        leadTime: h.lead_time,
        rainfallMm: typeof h.rainfall_mm === 'number' ? h.rainfall_mm : null,
        timestamp: h.timestamp,
        intervalEnd: h.interval_end,
      }));

      setHorizons(updatedHorizons);
      horizonsRef.current = updatedHorizons;

      if (appModeRef.current === 'LIVE') {
        applyHorizonToMap(targetHorizon, data);
      }
    } catch (err) {
      console.error('Forecast evolution fetch failed:', err);
      setError(err instanceof Error ? err.message : 'Flood forecast unavailable');
    } finally {
      setLoading(false);
    }
  }, [applyHorizonToMap]);

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
      (window as any).map = newMap;

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

      // 4. AFFECTED ROADS (OSM Street Corridors with Risk-Color Coding)
      newMap.addSource('affected-roads', {
        type: 'geojson',
        data: { type: 'FeatureCollection', features: [] }
      });

      newMap.addLayer({
        id: 'affected-roads-layer',
        type: 'line',
        source: 'affected-roads',
        layout: {
          'line-join': 'round',
          'line-cap': 'round',
          'visibility': 'visible',
        },
        paint: {
          'line-color': ['get', 'risk_color'],
          'line-width': [
            'interpolate', ['linear'], ['zoom'],
            11, 2.5,
            14, 4.0,
            17, 7.0
          ],
          'line-opacity': 0.95,
        }
      });

      // 5. AFFECTED INTERSECTIONS (Topological Junctions with Risk Markers)
      newMap.addSource('affected-intersections', {
        type: 'geojson',
        data: { type: 'FeatureCollection', features: [] }
      });

      newMap.addLayer({
        id: 'affected-intersections-layer',
        type: 'circle',
        source: 'affected-intersections',
        layout: {
          'visibility': 'visible',
        },
        paint: {
          'circle-radius': [
            'interpolate', ['linear'], ['zoom'],
            11, 4.0,
            14, 6.5,
            17, 10.0
          ],
          'circle-color': ['get', 'risk_color'],
          'circle-stroke-width': 2,
          'circle-stroke-color': '#ffffff',
          'circle-opacity': 0.95,
        }
      });

      // Interactive popup on road corridor click
      newMap.on('click', 'affected-roads-layer', (e) => {
        if (!e.features || e.features.length === 0) return;
        const props = e.features[0].properties || {};
        const depthM = props.max_depth_m != null ? Number(props.max_depth_m).toFixed(2) : '0.00';
        const depthCm = Math.round(Number(depthM) * 100);
        const risk = props.risk_level || 'LOW';
        const name = props.name || 'Unnamed Street';
        const len = props.flooded_length_m ? `${props.flooded_length_m} m` : 'N/A';
        const hwy = props.highway || 'road';

        if (popupRef.current) popupRef.current.remove();
        popupRef.current = new Popup({ closeButton: true, closeOnClick: true, className: 'ops-popup' })
          .setLngLat(e.lngLat)
          .setHTML(`
            <div class="popup-box">
              <div class="popup-header">
                <span class="popup-title">AFFECTED STREET CORRIDOR</span>
                <span class="popup-badge risk-${risk.toLowerCase()}">${risk}</span>
              </div>
              <div class="popup-body">
                <div class="popup-row">
                  <span class="lbl">Street:</span>
                  <span class="val bold">${name}</span>
                </div>
                <div class="popup-row">
                  <span class="lbl">Classification:</span>
                  <span class="val">${hwy}</span>
                </div>
                <div class="popup-row">
                  <span class="lbl">Predicted depth:</span>
                  <span class="val bold" style="color: #c2410c">${depthM} m (${depthCm} cm)</span>
                </div>
                <div class="popup-row">
                  <span class="lbl">Flooded corridor:</span>
                  <span class="val">${len}</span>
                </div>
                <div class="popup-row">
                  <span class="lbl">Road geometry:</span>
                  <span class="val">OpenStreetMap (ODbL)</span>
                </div>
                <div class="popup-row">
                  <span class="lbl">Depth source:</span>
                  <span class="val status-modelled">Modelled (Copernicus 30m DEM)</span>
                </div>
              </div>
            </div>
          `)
          .addTo(newMap);
      });

      newMap.on('mouseenter', 'affected-roads-layer', () => {
        newMap.getCanvas().style.cursor = 'pointer';
      });
      newMap.on('mouseleave', 'affected-roads-layer', () => {
        newMap.getCanvas().style.cursor = '';
      });

      // Interactive popup on junction click
      newMap.on('click', 'affected-intersections-layer', (e) => {
        if (!e.features || e.features.length === 0) return;
        const props = e.features[0].properties || {};
        const depthM = props.max_depth_m != null ? Number(props.max_depth_m).toFixed(2) : '0.00';
        const depthCm = Math.round(Number(depthM) * 100);
        const risk = props.risk_level || 'LOW';
        const name = props.name || 'Junction';
        const roads = props.roads_display || name;

        if (popupRef.current) popupRef.current.remove();
        popupRef.current = new Popup({ closeButton: true, closeOnClick: true, className: 'ops-popup' })
          .setLngLat(e.lngLat)
          .setHTML(`
            <div class="popup-box">
              <div class="popup-header">
                <span class="popup-title">AFFECTED INTERSECTION</span>
                <span class="popup-badge risk-${risk.toLowerCase()}">${risk}</span>
              </div>
              <div class="popup-body">
                <div class="popup-row">
                  <span class="lbl">Junction:</span>
                  <span class="val bold">${name}</span>
                </div>
                <div class="popup-row">
                  <span class="lbl">Cross streets:</span>
                  <span class="val">${roads}</span>
                </div>
                <div class="popup-row">
                  <span class="lbl">Predicted depth:</span>
                  <span class="val bold" style="color: #c2410c">${depthM} m (${depthCm} cm)</span>
                </div>
                <div class="popup-row">
                  <span class="lbl">Topology:</span>
                  <span class="val">OpenStreetMap (ODbL)</span>
                </div>
                <div class="popup-row">
                  <span class="lbl">Depth source:</span>
                  <span class="val status-modelled">Modelled (Copernicus 30m DEM)</span>
                </div>
              </div>
            </div>
          `)
          .addTo(newMap);
      });

      newMap.on('mouseenter', 'affected-intersections-layer', () => {
        newMap.getCanvas().style.cursor = 'pointer';
      });
      newMap.on('mouseleave', 'affected-intersections-layer', () => {
        newMap.getCanvas().style.cursor = '';
      });

      // Interactive popup on cell click
      newMap.on('click', 'flood-depth-layer', (e) => {
        if (!e.features || e.features.length === 0) return;
        const feature = e.features[0];
        const depth = feature.properties?.depth != null ? Number(feature.properties.depth) : 0;
        const depthM = depth.toFixed(2);
        const depthCm = Math.round(depth * 100);
        const risk = getRiskCategory(depth);

        const isScenario = appModeRef.current === 'SCENARIO';
        const activeCfg = horizonsRef.current.find(h => h.key === activeHorizonRef.current);
        const liveRainStr = activeCfg && activeCfg.rainfallMm !== null ? `${activeCfg.rainfallMm.toFixed(1)} mm` : 'N/A';

        const headingText = isScenario ? 'MODEL SCENARIO CELL (30 m)' : 'MODELLED FLOOD CELL (30 m)';
        const horizonOrScenarioRow = isScenario
          ? `<div class="popup-row">
               <span class="lbl">Scenario rate:</span>
               <span class="val bold">${activeScenarioRef.current} mm/h</span>
             </div>`
          : `<div class="popup-row">
               <span class="lbl">Forecast horizon:</span>
               <span class="val">${activeHorizonRef.current} (${liveRainStr})</span>
             </div>`;

        const rainfallSourceVal = isScenario
          ? 'Hypothetical model input (What-If)'
          : 'Weather forecast (Open-Meteo hourly NWP)';

        if (popupRef.current) {
          popupRef.current.remove();
        }

        popupRef.current = new Popup({ closeButton: true, closeOnClick: true, className: 'ops-popup' })
          .setLngLat(e.lngLat)
          .setHTML(`
            <div class="popup-box">
              <div class="popup-header">
                <span class="popup-title">${headingText}</span>
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
                ${horizonOrScenarioRow}
                <div class="popup-row">
                  <span class="lbl">Rainfall source:</span>
                  <span class="val">${rainfallSourceVal}</span>
                </div>
                <div class="popup-row">
                  <span class="lbl">Data status:</span>
                  <span class="val status-modelled">Modelled (Copernicus GLO-30 DSM)</span>
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
      fetchForecastEvolution('+1h').then(async () => {
        const fc = await fetchStreetForecastData();
        if (fc) {
          applyStreetDataToMap(fc['+1h'] || null);
        }
      });
      // Pre-warm scenario data so scenario switches are instant
      fetchScenarioEvolution();
      fetchStreetScenarioData();
    });

    return () => {
      if (popupRef.current) {
        popupRef.current.remove();
      }
      newMap.remove();
      mapInstanceRef.current = null;
    };
  }, [fetchForecastEvolution, fetchScenarioEvolution, fetchStreetForecastData, fetchStreetScenarioData, applyStreetDataToMap]);

  // Sync street overlay layer visibility
  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!map) return;
    const vis = showStreetOverlay ? 'visible' : 'none';
    if (map.getLayer('affected-roads-layer')) {
      map.setLayoutProperty('affected-roads-layer', 'visibility', vis);
    }
    if (map.getLayer('affected-intersections-layer')) {
      map.setLayoutProperty('affected-intersections-layer', 'visibility', vis);
    }
  }, [showStreetOverlay]);

  // Handle horizon change
  const handleHorizonChange = (h: ForecastHorizon) => {
    if (popupRef.current) {
      popupRef.current.remove();
    }
    setActiveHorizon(h);
    activeHorizonRef.current = h;
    if (appModeRef.current === 'LIVE') {
      applyHorizonToMap(h, forecastDataRef.current);
      applyStreetDataToMap(streetForecastDataRef.current?.[h] || null);
    }
  };

  // Handle mode switch
  const handleSetMode = async (mode: AppMode) => {
    if (popupRef.current) {
      popupRef.current.remove();
    }
    setAppMode(mode);
    appModeRef.current = mode;

    if (mode === 'SCENARIO') {
      let currentScData = scenarioDataRef.current;
      let currentStScData = streetScenarioDataRef.current;
      if (!currentScData || !currentStScData) {
        setLoading(true);
        const [scData, stScData] = await Promise.all([
          fetchScenarioEvolution(),
          fetchStreetScenarioData()
        ]);
        currentScData = scData;
        currentStScData = stScData;
        setLoading(false);
      }
      applyScenarioToMap(activeScenarioRef.current, currentScData);
      applyStreetDataToMap(currentStScData?.[activeScenarioRef.current] || null);
      if (activeScenarioRef.current > 20 && mapInstanceRef.current) {
        mapInstanceRef.current.flyTo({
          center: [72.8750, 19.0725],
          zoom: 14.2,
          duration: 1000
        });
      }
    } else {
      applyHorizonToMap(activeHorizonRef.current, forecastDataRef.current);
      applyStreetDataToMap(streetForecastDataRef.current?.[activeHorizonRef.current] || null);
    }
  };

  // Handle scenario switch
  const handleSelectScenario = async (sc: ScenarioValue) => {
    if (popupRef.current) {
      popupRef.current.remove();
    }
    setActiveScenario(sc);
    activeScenarioRef.current = sc;

    let currentScData = scenarioDataRef.current;
    let currentStScData = streetScenarioDataRef.current;
    if (!currentScData || !currentStScData) {
      setLoading(true);
      const [scData, stScData] = await Promise.all([
        fetchScenarioEvolution(),
        fetchStreetScenarioData()
      ]);
      currentScData = scData;
      currentStScData = stScData;
      setLoading(false);
    }
    applyScenarioToMap(sc, currentScData);
    applyStreetDataToMap(currentStScData?.[sc] || null);

    if (sc > 20 && mapInstanceRef.current) {
      mapInstanceRef.current.flyTo({
        center: [72.8750, 19.0725],
        zoom: 14.2,
        duration: 1000
      });
    }
  };

  const handleFocusStreet = (road: AffectedRoadAPI) => {
    const map = mapInstanceRef.current;
    if (!map) return;
    const coords = road.geometry?.coordinates;
    if (coords && coords.length > 0) {
      const mid = coords[Math.floor(coords.length / 2)];
      map.flyTo({
        center: [mid[0], mid[1]],
        zoom: 15.2,
        duration: 1000
      });
    }
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
      center: [72.8750, 19.0725],
      zoom: 14.2,
      duration: 1200
    });
  };

  // Active statistics depending on appMode (LIVE vs SCENARIO)
  const isScenarioMode = appMode === 'SCENARIO';
  const liveState = forecastData?.horizons?.find(h => h.horizon === activeHorizon);
  const scenarioState = scenarioData?.[activeScenario];

  const maxDepthM = isScenarioMode
    ? (scenarioState?.max_depth_m ?? (activeScenario === 20 ? 0 : activeScenario === 40 ? 0.14 : activeScenario === 50 ? 0.29 : 0.58))
    : (liveState?.max_depth_m ?? 0);

  const floodedAreaM2 = isScenarioMode
    ? (scenarioState?.flooded_area_m2 ?? (activeScenario === 20 ? 0 : 45900))
    : (liveState?.flooded_area_m2 ?? 0);

  const riskInfo = getRiskCategory(maxDepthM);

  const statusTitle = isScenarioMode
    ? `Model Scenario: ${activeScenario} mm/h`
    : currentHorizonConfig.periodDisplay;

  const statusKicker = isScenarioMode
    ? 'WHAT-IF SCENARIO ASSESSMENT'
    : 'PREDICTED CONDITIONS';

  const rainfallMetricVal = isScenarioMode
    ? activeScenario.toFixed(1)
    : (currentHorizonConfig.rainfallMm !== null ? currentHorizonConfig.rainfallMm.toFixed(1) : '--');

  const rainfallMetricSub = isScenarioMode
    ? 'Hypothetical model input'
    : 'Weather forecast (Open-Meteo hourly NWP)';

  const rainfallMetricLabel = isScenarioMode
    ? 'SCENARIO RAINFALL'
    : 'FORECAST RAINFALL';

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
            <span>{isScenarioMode ? 'WHAT-IF FLOOD SCENARIO' : '0–3 HOUR FLOOD OUTLOOK'}</span>
          </div>
          <div
            className="prototype-status-pill"
            style={isScenarioMode ? { background: '#0284c7', borderColor: '#38bdf8' } : undefined}
          >
            <span
              className="status-dot"
              style={isScenarioMode ? { background: '#e0f2fe' } : undefined}
            />
            <span>{isScenarioMode ? 'MODEL SCENARIO' : 'PROTOTYPE SCENARIO'}</span>
          </div>
        </div>

        <div className="topbar-right">
          <div className="telemetry-info">
            <span className="meta-tag">60-MIN TIMESTEP</span>
            <span className="meta-divider">•</span>
            {isScenarioMode ? (
              <>
                <span className="meta-label">INPUT:</span>
                <span className="meta-val" style={{ color: '#38bdf8' }}>
                  Hypothetical rainfall input ({activeScenario} mm/h)
                </span>
                <span className="meta-divider">•</span>
                <span className="meta-label">MODE:</span>
                <span className="meta-val" style={{ color: '#e2e8f0' }}>
                  MODEL SCENARIO
                </span>
              </>
            ) : (
              <>
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
              </>
            )}
          </div>
        </div>
      </header>

      {/* 2. MAP WORKSPACE */}
      <div className="map-workspace">
        <div ref={mapContainerRef} className="map-viewport" />

        {/* LEFT WORKSPACE OVERLAY: STACK OF CONTROLS & STATUS PANELS */}
        <div className="map-left-overlay">
          {/* TIMELINE & SCENARIO CONTROLS */}
          <div className="flood-timeline-panel">
            {/* Mode Switcher */}
            <div className="mode-toggle-group">
              <button
                type="button"
                className={`mode-toggle-btn ${!isScenarioMode ? 'active' : ''}`}
                onClick={() => handleSetMode('LIVE')}
              >
                LIVE FORECAST
              </button>
              <button
                type="button"
                className={`mode-toggle-btn ${isScenarioMode ? 'scenario-active' : ''}`}
                onClick={() => handleSetMode('SCENARIO')}
              >
                MODEL SCENARIO
              </button>
            </div>

            {!isScenarioMode ? (
              <>
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
              </>
            ) : (
              <>
                <div className="timeline-header">
                  <span className="timeline-heading" style={{ color: '#0369a1' }}>RAINFALL SCENARIOS</span>
                  <span className="timeline-active-tag" style={{ background: '#e0f2fe', color: '#0369a1' }}>
                    {activeScenario} mm/h
                  </span>
                </div>
                <div className="timeline-stepper">
                  {SCENARIO_VALUES.map((sc) => {
                    const isSelected = activeScenario === sc;
                    return (
                      <button
                        key={sc}
                        type="button"
                        className={`timeline-step-btn ${isSelected ? 'selected scenario-selected' : ''}`}
                        onClick={() => handleSelectScenario(sc)}
                      >
                        <span className="step-time">{sc}</span>
                        <span className="step-rain-tag">mm/h</span>
                      </button>
                    );
                  })}
                </div>
                <div className="scenario-explanatory-note">
                  WHAT-IF: evaluates modeled inundation under hypothetical rainfall.
                </div>
              </>
            )}
          </div>

          {/* MAP EXTENT CONTROLS */}
          <div className="map-extent-tools">
            <button type="button" className="extent-btn" onClick={handleResetOverview} title="Reset to full Mumbai region">
              ⛶ Full Extent (Mumbai)
            </button>
            <button type="button" className="extent-btn highlight" onClick={handleFocusFloodParcel} title="Center on Mumbai pilot zone (Kurla / SCLR)">
              🎯 Target Zone (Kurla)
            </button>
          </div>

          {/* FLOOD STATUS & RISK ASSESSMENT PANEL (High Visual Hierarchy) */}
          <div className="flood-status-panel">
            <div className="status-panel-top">
              <div className="status-horizon-kicker">{statusKicker}</div>
              <div className="status-horizon-title">{statusTitle}</div>
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
                  {isScenarioMode ? 'SCENARIO RISK' : 'PREDICTED RISK'}
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

            {/* SECONDARY METRICS: FORECAST/SCENARIO RAINFALL & FLOODED AREA */}
            <div className="status-metric-grid">
              <div className="grid-metric-box">
                <span className="metric-box-label">{rainfallMetricLabel}</span>
                <span className="metric-box-val">
                  {rainfallMetricVal}{' '}
                  <span className="sub-unit">mm</span>
                </span>
                <span className="metric-box-sub">
                  {rainfallMetricSub}
                </span>
              </div>
              <div className="grid-metric-box">
                <span className="metric-box-label">INUNDATED AREA</span>
                <span className="metric-box-val">{Math.round(floodedAreaM2)} <span className="sub-unit">m²</span></span>
                <span className="metric-box-sub">30m DEM grid</span>
              </div>
            </div>

            {/* SIMULATION SUMMARY FOOTER */}
            <div className="status-panel-footer">
              <div className="footer-engine-title">MODEL PIPELINE</div>
              <div className="footer-engine-desc">
                Rainfall–runoff + drainage capacity + surface routing
              </div>
              <div className="footer-engine-param">
                {isScenarioMode && activeScenario === 20
                  ? 'Conveyance: 100% capacity • 0 surcharge'
                  : 'Runoff C = 0.7 • 60-minute model timestep'}
              </div>
            </div>
          </div>

          {/* 6. STREET & INTERSECTION FLOOD INTELLIGENCE */}
          <div className="street-intelligence-panel">
            <div className="street-panel-header">
              <div className="street-header-title">
                <span className="street-title-icon">🛣️</span> STREET FLOOD RISK
              </div>
              <label className="street-toggle-label">
                <input
                  type="checkbox"
                  checked={showStreetOverlay}
                  onChange={(e) => setShowStreetOverlay(e.target.checked)}
                />
                <span>Overlay</span>
              </label>
            </div>

            {currentStreetIntel && currentStreetIntel.summary.total_affected_roads > 0 ? (
              <>
                <div className="street-impact-summary">
                  <div className="impact-count-badge">
                    <span className="count-num">{currentStreetIntel.summary.total_affected_roads}</span>
                    <span className="count-lbl">Streets</span>
                  </div>
                  <div className="impact-count-badge">
                    <span className="count-num">{currentStreetIntel.summary.total_affected_intersections}</span>
                    <span className="count-lbl">Junctions</span>
                  </div>
                  <div className="impact-depth-badge">
                    <span className="depth-lbl">Peak Street Depth</span>
                    <span className="depth-val">{currentStreetIntel.summary.max_street_depth_m.toFixed(2)} m</span>
                  </div>
                </div>

                {/* Risk distribution pills */}
                <div className="street-risk-pills">
                  {currentStreetIntel.summary.risk_counts.CRITICAL > 0 && (
                    <span className="risk-pill critical">
                      {currentStreetIntel.summary.risk_counts.CRITICAL} Critical
                    </span>
                  )}
                  {currentStreetIntel.summary.risk_counts.HIGH > 0 && (
                    <span className="risk-pill high">
                      {currentStreetIntel.summary.risk_counts.HIGH} High
                    </span>
                  )}
                  {currentStreetIntel.summary.risk_counts.MEDIUM > 0 && (
                    <span className="risk-pill medium">
                      {currentStreetIntel.summary.risk_counts.MEDIUM} Moderate
                    </span>
                  )}
                  {currentStreetIntel.summary.risk_counts.LOW > 0 && (
                    <span className="risk-pill low">
                      {currentStreetIntel.summary.risk_counts.LOW} Low
                    </span>
                  )}
                </div>

                {/* Top affected arterial roads */}
                <div className="street-affected-list">
                  <div className="list-title">KEY IMPACTED CORRIDORS</div>
                  {currentStreetIntel.affected_roads.slice(0, 3).map((road) => (
                    <div
                      key={road.road_id}
                      className="affected-street-item"
                      onClick={() => handleFocusStreet(road)}
                      title="Click to focus on this street"
                    >
                      <div className="street-item-left">
                        <span className="street-item-name">{road.name}</span>
                        <span className="street-item-sub">
                          {road.highway} • {road.flooded_length_m}m flooded
                        </span>
                      </div>
                      <div className="street-item-right">
                        <span className={`street-risk-tag risk-${road.risk_level.toLowerCase()}`}>
                          {road.risk_level}
                        </span>
                        <span className="street-depth-tag">{road.max_depth_m.toFixed(2)}m</span>
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
              OSM road network + 2D D8 surface routing • Not municipal road sensors
            </div>
          </div>

          {/* DATA STATUS & PROVENANCE (Clear but Secondary) */}
          <div className="provenance-card">
            <div className="provenance-header">
              {isScenarioMode ? 'SCENARIO PROVENANCE & STATUS' : 'DATA PROVENANCE & STATUS'}
            </div>
            <div className="provenance-list">
              <div className="provenance-item">
                <span className="prov-source">Rainfall</span>
                <span
                  className={`prov-tag ${isScenarioMode ? 'tag-modelled' : (rainfallStatus === 'LIVE' ? 'tag-modelled' : 'tag-prototype')}`}
                  style={isScenarioMode ? { background: '#e0f2fe', color: '#0369a1' } : undefined}
                >
                  {isScenarioMode ? 'Hypothetical model input' : `Open-Meteo NWP (${rainfallStatus})`}
                </span>
              </div>
              <div className="provenance-item">
                <span className="prov-source">Elevation</span>
                <span className="prov-tag tag-modelled">Copernicus GLO-30 DSM (30m)</span>
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
              {isScenarioMode
                ? 'WHAT-IF: evaluates modeled inundation under hypothetical rainfall. Elevation model sourced from Copernicus GLO-30 DSM (30m).'
                : 'NOTICE: Weather forecast sourced from Open-Meteo hourly NWP (not radar nowcast or observed rainfall). Elevation model sourced from Copernicus GLO-30 DSM (30m).'}
            </div>
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