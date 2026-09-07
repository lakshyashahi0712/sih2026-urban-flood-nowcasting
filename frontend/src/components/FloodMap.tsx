import { useEffect, useRef, useState, useCallback } from 'react';
import { Map as MapLibreMap, GeoJSONSource, NavigationControl, Popup, setWorkerUrl } from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import workerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?worker&url';

setWorkerUrl(workerUrl);

type ForecastHorizon = 'NOW' | '+1h' | '+2h' | '+3h';
type AppMode = 'LIVE' | 'SCENARIO' | 'HISTORICAL';
type ScenarioValue = 20 | 40 | 50 | 70;
const SCENARIO_VALUES: ScenarioValue[] = [20, 40, 50, 70];

const DEMO_EVOLUTION_SEQUENCE: { horizon: ForecastHorizon; scenario: ScenarioValue; label: string }[] = [
  { horizon: 'NOW', scenario: 20, label: 'NOW' },
  { horizon: '+1h', scenario: 40, label: '+1h' },
  { horizon: '+2h', scenario: 50, label: '+2h' },
  { horizon: '+3h', scenario: 70, label: '+3h' },
];

const SCENARIO_TO_HORIZON: Record<ScenarioValue, ForecastHorizon> = {
  20: 'NOW',
  40: '+1h',
  50: '+2h',
  70: '+3h',
};

interface HistoricalTimestepAPI {
  timestep_index: number;
  replay_timestamp: string;
  time_display: string;
  rainfall_mm: number;
  rainfall_intensity_mm_per_hr: number;
  cumulative_rainfall_mm: number;
  boundary_level_m: number;
  peak_flood_depth_m: number;
  flooded_area_m2: number;
  flood_volume_m3: number;
  drainage_surcharge_volume_m3: number;
  features: any[];
  geojson: any;
  roads_geojson?: any;
  intersections_geojson?: any;
  street_risk?: StreetFloodIntelligenceAPI | null;
}

interface EventPeakStatisticAPI {
  value: number;
  unit: string;
  timestep_index: number;
  time_display: string;
  description: string;
}

interface EventSummaryAPI {
  peak_depth: EventPeakStatisticAPI;
  peak_surcharge: EventPeakStatisticAPI;
  peak_surface_volume: EventPeakStatisticAPI;
  peak_flooded_area: EventPeakStatisticAPI;
}

interface ValidationComparisonAPI {
  location_id: string;
  location_name: string;
  observed_depth_range?: string;
  minimum?: number;
  maximum?: number | null;
  observed_min_depth_m: number;
  observed_max_depth_m: number | null;
  exact_cell_depth_m: number | null;
  matched_depth_m: number | null;
  match_method: string;
  search_radius_m: number;
  matched_cell_distance_m: number | null;
  within_observed_range: boolean;
  absolute_difference_m: number | null;
  spatial_status: string;
  is_model_input?: boolean;
  notes: string;
}

interface HistoricalReplayAPIResponse {
  event_id: string;
  event_name: string;
  event_date: string;
  mode_label: string;
  event_subtitle: string;
  first_timestamp: string;
  last_timestamp: string;
  timestep_count: number;
  peak_modeled_depth_m: number;
  peak_flooded_area_m2: number;
  peak_flood_volume_m3: number;
  peak_surcharge_volume_m3: number;
  event_summary: EventSummaryAPI;
  provenance: Record<string, string>;
  benchmarks_geojson: any;
  validation_comparisons: ValidationComparisonAPI[];
  timesteps: HistoricalTimestepAPI[];
}

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

interface SnappedPointAPI {
  original_coords: [number, number];
  snapped_coords: [number, number];
  distance_to_road_m: number;
  nearest_road_name: string | null;
}

interface ShortestPathComparisonAPI {
  distance_m: number;
  max_flood_depth_m: number;
  has_flooded_roads: boolean;
  flooded_road_count: number;
}

interface SafeRouteAPIResponse {
  status: 'SAFE' | 'CAUTION' | 'UNAVAILABLE' | 'NO_PATH_FOUND';
  total_distance_m: number;
  estimated_travel_cost: number;
  max_predicted_flood_depth_m: number;
  roads_avoided: string[];
  route_geometry: any;
  shortest_path_comparison?: ShortestPathComparisonAPI | null;
  start_snapped_to?: SnappedPointAPI | null;
  end_snapped_to?: SnappedPointAPI | null;
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
      depthCol: '#991b1b',
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
      depthCol: '#c2410c',
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
      depthCol: '#854d0e',
      description: 'Localized waterlogging in terrain depressions'
    };
  }
  return {
    text: 'NO INUNDATION',
    level: 'No Inundation',
    badgeClass: 'risk-low',
    bannerBg: '#f8fafc',
    bannerBorder: '#cbd5e1',
    textCol: '#166534',
    depthCol: '#166534',
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

  // Historical Replay states
  const [historicalData, setHistoricalData] = useState<HistoricalReplayAPIResponse | null>(null);
  const [historicalStep, setHistoricalStep] = useState<number>(5); // Step 6 peak index 5 (13:30 IST)
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [showBenchmarksOverlay, setShowBenchmarksOverlay] = useState<boolean>(true);
  const [showHistoricalRoadsOverlay, setShowHistoricalRoadsOverlay] = useState<boolean>(true);

  // Flood-Safe Routing states
  const [isRoutingActive, setIsRoutingActive] = useState<boolean>(false);
  const [routeOrigin, setRouteOrigin] = useState<[number, number] | null>(null);
  const [routeDestination, setRouteDestination] = useState<[number, number] | null>(null);
  const [routeResponse, setRouteResponse] = useState<SafeRouteAPIResponse | null>(null);
  const [routeLoading, setRouteLoading] = useState<boolean>(false);
  const [routeError, setRouteError] = useState<string | null>(null);

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

  const historicalDataRef = useRef<HistoricalReplayAPIResponse | null>(null);
  historicalDataRef.current = historicalData;
  const historicalStepRef = useRef<number>(5);
  historicalStepRef.current = historicalStep;
  const isPlayingRef = useRef<boolean>(false);
  isPlayingRef.current = isPlaying;
  const showBenchmarksOverlayRef = useRef<boolean>(true);
  showBenchmarksOverlayRef.current = showBenchmarksOverlay;
  const showHistoricalRoadsOverlayRef = useRef<boolean>(true);
  showHistoricalRoadsOverlayRef.current = showHistoricalRoadsOverlay;

  const isRoutingActiveRef = useRef<boolean>(false);
  isRoutingActiveRef.current = isRoutingActive;
  const routeOriginRef = useRef<[number, number] | null>(null);
  routeOriginRef.current = routeOrigin;
  const routeDestinationRef = useRef<[number, number] | null>(null);
  routeDestinationRef.current = routeDestination;

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

  const applyHistoricalStepToMap = useCallback((stepIdx: number, data: HistoricalReplayAPIResponse | null) => {
    const map = mapInstanceRef.current;
    if (!map) return;
    const targetStep = data?.timesteps?.[stepIdx];
    const source = map.getSource('flood-depth') as GeoJSONSource | undefined;
    if (source) {
      if (targetStep && targetStep.geojson) {
        source.setData(targetStep.geojson);
      } else {
        source.setData({ type: 'FeatureCollection', features: [] });
      }
    }
    const bmSource = map.getSource('historical-benchmarks') as GeoJSONSource | undefined;
    if (bmSource && data?.benchmarks_geojson) {
      bmSource.setData(data.benchmarks_geojson);
    }

    // Update affected OSM roads and intersections for historical timestep
    const roadsSource = map.getSource('affected-roads') as GeoJSONSource | undefined;
    if (roadsSource) {
      roadsSource.setData(targetStep?.roads_geojson || { type: 'FeatureCollection', features: [] });
    }
    const intsSource = map.getSource('affected-intersections') as GeoJSONSource | undefined;
    if (intsSource) {
      intsSource.setData(targetStep?.intersections_geojson || { type: 'FeatureCollection', features: [] });
    }
    setCurrentStreetIntel(targetStep?.street_risk || null);
  }, []);

  const updateRouteOnMap = useCallback((route: SafeRouteAPIResponse | null, origin: [number, number] | null, dest: [number, number] | null) => {
    const map = mapInstanceRef.current;
    if (!map) return;

    // Update safe route line
    const routeSource = map.getSource('safe-route') as GeoJSONSource | undefined;
    if (routeSource) {
      if (route && route.route_geometry) {
        routeSource.setData({
          type: 'FeatureCollection',
          features: [
            {
              type: 'Feature',
              properties: {
                status: route.status,
              },
              geometry: route.route_geometry,
            },
          ],
        });
      } else {
        routeSource.setData({ type: 'FeatureCollection', features: [] });
      }
    }

    // Update origin/destination pins
    const wpSource = map.getSource('route-waypoints') as GeoJSONSource | undefined;
    if (wpSource) {
      const features: any[] = [];
      if (origin) {
        const coords = route?.start_snapped_to?.snapped_coords || origin;
        features.push({
          type: 'Feature',
          properties: { point_type: 'origin', title: 'Origin' },
          geometry: { type: 'Point', coordinates: coords },
        });
      }
      if (dest) {
        const coords = route?.end_snapped_to?.snapped_coords || dest;
        features.push({
          type: 'Feature',
          properties: { point_type: 'destination', title: 'Destination' },
          geometry: { type: 'Point', coordinates: coords },
        });
      }
      wpSource.setData({ type: 'FeatureCollection', features });
    }
  }, []);

  const fetchSafeRoute = useCallback(async (
    start: [number, number],
    end: [number, number],
    horizonOverride?: ForecastHorizon,
    modeOverride?: AppMode,
    scenarioOverride?: ScenarioValue
  ) => {
    setRouteLoading(true);
    setRouteError(null);
    try {
      const hz = horizonOverride || activeHorizonRef.current;
      const mode = modeOverride || appModeRef.current;
      const sc = scenarioOverride || activeScenarioRef.current;

      let url = `http://localhost:8000/routing/safe-route?start_lon=${start[0]}&start_lat=${start[1]}&end_lon=${end[0]}&end_lat=${end[1]}&horizon=${encodeURIComponent(hz)}`;
      if (mode === 'SCENARIO') {
        url += `&rainfall_scenario_mm=${sc}`;
      }

      const res = await fetch(url);
      if (!res.ok) {
        const errJson = await res.json().catch(() => null);
        const msg = errJson?.detail || `Routing error (${res.status})`;
        throw new Error(msg);
      }
      const data: SafeRouteAPIResponse = await res.json();
      setRouteResponse(data);
      updateRouteOnMap(data, start, end);
    } catch (err: any) {
      console.error('Failed to calculate safe route:', err);
      setRouteError(err?.message || 'Failed to calculate safe route');
      setRouteResponse(null);
      updateRouteOnMap(null, start, end);
    } finally {
      setRouteLoading(false);
    }
  }, [updateRouteOnMap]);

  const handleClearRoute = useCallback(() => {
    setRouteOrigin(null);
    routeOriginRef.current = null;
    setRouteDestination(null);
    routeDestinationRef.current = null;
    setRouteResponse(null);
    setRouteError(null);
    updateRouteOnMap(null, null, null);
  }, [updateRouteOnMap]);

  const handleToggleRouting = useCallback(() => {
    setIsRoutingActive((prev) => {
      const next = !prev;
      isRoutingActiveRef.current = next;
      const map = mapInstanceRef.current;
      if (map) {
        map.getCanvas().style.cursor = next ? 'crosshair' : '';
      }
      if (!next) {
        handleClearRoute();
      }
      return next;
    });
  }, [handleClearRoute]);

  const handleSelectPresetRoute = useCallback((start: [number, number], end: [number, number]) => {
    setIsRoutingActive(true);
    isRoutingActiveRef.current = true;
    const map = mapInstanceRef.current;
    if (map) {
      map.getCanvas().style.cursor = 'crosshair';
      map.flyTo({
        center: [(start[0] + end[0]) / 2, (start[1] + end[1]) / 2],
        zoom: 13.5,
        essential: true,
      });
    }
    setRouteOrigin(start);
    routeOriginRef.current = start;
    setRouteDestination(end);
    routeDestinationRef.current = end;
    updateRouteOnMap(null, start, end);
    fetchSafeRoute(start, end);
  }, [fetchSafeRoute, updateRouteOnMap]);

  const fetchSafeRouteRef = useRef(fetchSafeRoute);
  fetchSafeRouteRef.current = fetchSafeRoute;
  const updateRouteOnMapRef = useRef(updateRouteOnMap);
  updateRouteOnMapRef.current = updateRouteOnMap;

  const fetchStreetScenarioData = useCallback(async (): Promise<Record<ScenarioValue, StreetFloodIntelligenceAPI> | null> => {
    if (streetScenarioDataRef.current) return streetScenarioDataRef.current;
    try {
      const results = await Promise.all(
        SCENARIO_VALUES.map(async (sc) => {
          const hz = encodeURIComponent(SCENARIO_TO_HORIZON[sc] || '+1h');
          const res = await fetch(`http://localhost:8000/flood/streets?rainfall_mm=${sc}&horizon=${hz}`);
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

  const fetchHistoricalReplay = useCallback(async (): Promise<HistoricalReplayAPIResponse | null> => {
    if (historicalDataRef.current) return historicalDataRef.current;
    setLoading(true);
    setError(null);
    try {
      const res = await fetch('http://localhost:8000/flood/historical/2017');
      if (!res.ok) {
        throw new Error(`Historical Replay API returned HTTP ${res.status}`);
      }
      const data: HistoricalReplayAPIResponse = await res.json();
      setHistoricalData(data);
      historicalDataRef.current = data;
      return data;
    } catch (err) {
      console.error('Failed to fetch historical replay:', err);
      setError(err instanceof Error ? err.message : 'Historical replay unavailable');
      return null;
    } finally {
      setLoading(false);
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

      // Outer boundary stroke (halo zeroed to prevent harsh checkerboard tile outlines)
      newMap.addLayer({
        id: 'flood-depth-halo',
        type: 'line',
        source: 'flood-depth',
        paint: {
          'line-color': '#0f172a',
          'line-width': 1.0,
          'line-opacity': 0.0
        }
      });

      // Subtle water perimeter edge
      newMap.addLayer({
        id: 'flood-depth-outline',
        type: 'line',
        source: 'flood-depth',
        paint: {
          'line-color': '#ffffff',
          'line-width': 0.75,
          'line-opacity': 0.35
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
          'line-color': [
            'match',
            ['get', 'risk_level'],
            'CRITICAL', '#dc2626',
            'HIGH', '#ea580c',
            'MEDIUM', '#f59e0b',
            'LOW', '#3b82f6',
            '#ffffff'
          ],
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
          'circle-color': [
            'match',
            ['get', 'risk_level'],
            'CRITICAL', '#dc2626',
            'HIGH', '#ea580c',
            'MEDIUM', '#f59e0b',
            'LOW', '#3b82f6',
            '#ffffff'
          ],
          'circle-stroke-width': 2,
          'circle-stroke-color': '#ffffff',
          'circle-opacity': 0.95,
        }
      });

      // 6. HISTORICAL BENCHMARKS (Observed 2017 Ground-Truth Hotspots)
      newMap.addSource('historical-benchmarks', {
        type: 'geojson',
        data: { type: 'FeatureCollection', features: [] }
      });

      newMap.addLayer({
        id: 'historical-benchmarks-halo',
        type: 'circle',
        source: 'historical-benchmarks',
        layout: {
          'visibility': 'none',
        },
        paint: {
          'circle-radius': [
            'interpolate', ['linear'], ['zoom'],
            11, 7.0,
            14, 11.0,
            17, 16.0
          ],
          'circle-color': '#0f172a',
          'circle-opacity': 0.85,
        }
      });

      newMap.addLayer({
        id: 'historical-benchmarks-layer',
        type: 'circle',
        source: 'historical-benchmarks',
        layout: {
          'visibility': 'none',
        },
        paint: {
          'circle-radius': [
            'interpolate', ['linear'], ['zoom'],
            11, 5.0,
            14, 8.0,
            17, 12.0
          ],
          'circle-color': '#d97706',
          'circle-stroke-width': 2.5,
          'circle-stroke-color': '#ffffff',
          'circle-opacity': 1.0,
        }
      });

      // 7. SAFE ROUTING SOURCES & LAYERS
      newMap.addSource('safe-route', {
        type: 'geojson',
        data: { type: 'FeatureCollection', features: [] }
      });

      // Dark casing line for contrast against all map styles
      newMap.addLayer({
        id: 'safe-route-halo',
        type: 'line',
        source: 'safe-route',
        layout: {
          'line-join': 'round',
          'line-cap': 'round',
          'visibility': 'visible',
        },
        paint: {
          'line-color': '#0f172a',
          'line-width': 9,
          'line-opacity': 0.85,
        }
      });

      // Status-colored route path
      newMap.addLayer({
        id: 'safe-route-line',
        type: 'line',
        source: 'safe-route',
        layout: {
          'line-join': 'round',
          'line-cap': 'round',
          'visibility': 'visible',
        },
        paint: {
          'line-color': [
            'match',
            ['get', 'status'],
            'SAFE', '#10b981',
            'CAUTION', '#f59e0b',
            'UNAVAILABLE', '#ef4444',
            'NO_PATH_FOUND', '#ef4444',
            '#10b981'
          ],
          'line-width': 5,
          'line-opacity': 1.0,
        }
      });

      // Origin & destination waypoint pins
      newMap.addSource('route-waypoints', {
        type: 'geojson',
        data: { type: 'FeatureCollection', features: [] }
      });

      newMap.addLayer({
        id: 'route-waypoints-layer',
        type: 'circle',
        source: 'route-waypoints',
        layout: {
          'visibility': 'visible',
        },
        paint: {
          'circle-radius': 7,
          'circle-color': [
            'match',
            ['get', 'point_type'],
            'origin', '#10b981',
            'destination', '#6366f1',
            '#3b82f6'
          ],
          'circle-stroke-width': 2.5,
          'circle-stroke-color': '#ffffff',
          'circle-opacity': 1.0,
        }
      });

      // Interactive popup on benchmark click
      newMap.on('click', 'historical-benchmarks-layer', (e) => {
        if (isRoutingActiveRef.current) return;
        if (!e.features || e.features.length === 0) return;
        const props = e.features[0].properties || {};
        const name = props.location_name || 'Benchmark Location';
        const minObs = props.observed_min_depth_m != null ? Number(props.observed_min_depth_m).toFixed(2) : '--';
        const maxObs = props.observed_max_depth_m != null ? Number(props.observed_max_depth_m).toFixed(2) : null;
        const obsRangeStr = props.observed_depth_range || props.descriptor || (maxObs ? `${minObs} – ${maxObs} m` : `>2.20 m`);
        const matchedDepth = props.matched_depth_m != null ? Number(props.matched_depth_m).toFixed(3) : '0.000';
        const inRange = Boolean(props.within_observed_range);
        const spatialStatus = props.spatial_status === 'OUTSIDE_PILOT_EXTENT'
          ? 'Outside Pilot'
          : (matchedDepth === '0.000' ? 'Dry Cell' : (inRange ? 'In Range' : 'Outside Range'));
        const matchMethod = props.match_method || 'Point comparison';
        const distanceM = props.matched_cell_distance_m != null ? `${Number(props.matched_cell_distance_m).toFixed(1)} m` : 'N/A';
        const notes = props.notes || '';

        if (popupRef.current) popupRef.current.remove();
        popupRef.current = new Popup({ closeButton: true, closeOnClick: true, className: 'ops-popup' })
          .setLngLat(e.lngLat)
          .setHTML(`
            <div class="popup-box">
              <div class="popup-header">
                <span class="popup-title">HISTORICAL FLOOD BENCHMARK</span>
                <span class="popup-badge ${inRange ? 'risk-low' : 'risk-high'}">${spatialStatus}</span>
              </div>
              <div class="popup-body">
                <div class="popup-row">
                  <span class="lbl">Location:</span>
                  <span class="val bold">${name}</span>
                </div>
                <div class="popup-row">
                  <span class="lbl">Observed Depth:</span>
                  <span class="val bold" style="color: #c2410c">${obsRangeStr}</span>
                </div>
                <div class="popup-row">
                  <span class="lbl">Modeled Depth:</span>
                  <span class="val bold" style="color: #0369a1">${matchedDepth} m</span>
                </div>
                <div class="popup-row">
                  <span class="lbl">Match Method:</span>
                  <span class="val">${matchMethod}</span>
                </div>
                <div class="popup-row">
                  <span class="lbl">Search Distance:</span>
                  <span class="val">${distanceM}</span>
                </div>
                <div class="popup-row">
                  <span class="lbl">Source Event:</span>
                  <span class="val">29 Aug 2017 (Observed)</span>
                </div>
                <div class="popup-row" style="margin-top: 4px; border-top: 1px solid #cbd5e1; padding-top: 4px;">
                  <span class="lbl" style="font-size: 9.5px; color: #64748b;">${notes}</span>
                </div>
              </div>
            </div>
          `)
          .addTo(newMap);
      });

      newMap.on('mouseenter', 'historical-benchmarks-layer', () => {
        if (isRoutingActiveRef.current) return;
        newMap.getCanvas().style.cursor = 'pointer';
      });
      newMap.on('mouseleave', 'historical-benchmarks-layer', () => {
        if (isRoutingActiveRef.current) {
          newMap.getCanvas().style.cursor = 'crosshair';
          return;
        }
        newMap.getCanvas().style.cursor = '';
      });

      // Interactive popup on road corridor click
      newMap.on('click', 'affected-roads-layer', (e) => {
        if (isRoutingActiveRef.current) return;
        if (!e.features || e.features.length === 0) return;
        const props = e.features[0].properties || {};
        const depthM = props.max_depth_m != null ? Number(props.max_depth_m).toFixed(2) : '0.00';
        const depthCm = Math.round(Number(depthM) * 100);
        const risk = props.risk_level || 'LOW';
        const name = props.name || 'Unnamed Street';
        const len = props.flooded_length_m ? `${props.flooded_length_m} m` : 'N/A';
        const hwy = props.highway || 'road';
        const isHist = appModeRef.current === 'HISTORICAL';
        const popupTitle = isHist ? 'MODELLED FLOODED CORRIDOR (2017)' : 'AFFECTED STREET CORRIDOR';
        const depthLbl = isHist ? 'Modelled depth:' : 'Predicted depth:';
        const depthSource = isHist ? 'Modelled Retrospective (D8 + Copernicus 30m)' : 'Modelled (Copernicus 30m DEM)';

        if (popupRef.current) popupRef.current.remove();
        popupRef.current = new Popup({ closeButton: true, closeOnClick: true, className: 'ops-popup' })
          .setLngLat(e.lngLat)
          .setHTML(`
            <div class="popup-box">
              <div class="popup-header">
                <span class="popup-title">${popupTitle}</span>
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
                  <span class="lbl">${depthLbl}</span>
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
                  <span class="val status-modelled">${depthSource}</span>
                </div>
              </div>
            </div>
          `)
          .addTo(newMap);
      });

      newMap.on('mouseenter', 'affected-roads-layer', () => {
        if (isRoutingActiveRef.current) return;
        newMap.getCanvas().style.cursor = 'pointer';
      });
      newMap.on('mouseleave', 'affected-roads-layer', () => {
        if (isRoutingActiveRef.current) {
          newMap.getCanvas().style.cursor = 'crosshair';
          return;
        }
        newMap.getCanvas().style.cursor = '';
      });

      // Interactive popup on junction click
      newMap.on('click', 'affected-intersections-layer', (e) => {
        if (isRoutingActiveRef.current) return;
        if (!e.features || e.features.length === 0) return;
        const props = e.features[0].properties || {};
        const depthM = props.max_depth_m != null ? Number(props.max_depth_m).toFixed(2) : '0.00';
        const depthCm = Math.round(Number(depthM) * 100);
        const risk = props.risk_level || 'LOW';
        const name = props.name || 'Junction';
        const roads = props.roads_display || name;
        const isHist = appModeRef.current === 'HISTORICAL';
        const popupTitle = isHist ? 'MODELLED FLOODED INTERSECTION (2017)' : 'AFFECTED INTERSECTION';
        const depthLbl = isHist ? 'Modelled depth:' : 'Predicted depth:';
        const depthSource = isHist ? 'Modelled Retrospective (D8 + Copernicus 30m)' : 'Modelled (Copernicus 30m DEM)';

        if (popupRef.current) popupRef.current.remove();
        popupRef.current = new Popup({ closeButton: true, closeOnClick: true, className: 'ops-popup' })
          .setLngLat(e.lngLat)
          .setHTML(`
            <div class="popup-box">
              <div class="popup-header">
                <span class="popup-title">${popupTitle}</span>
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
                  <span class="lbl">${depthLbl}</span>
                  <span class="val bold" style="color: #c2410c">${depthM} m (${depthCm} cm)</span>
                </div>
                <div class="popup-row">
                  <span class="lbl">Topology:</span>
                  <span class="val">OpenStreetMap (ODbL)</span>
                </div>
                <div class="popup-row">
                  <span class="lbl">Depth source:</span>
                  <span class="val status-modelled">${depthSource}</span>
                </div>
              </div>
            </div>
          `)
          .addTo(newMap);
      });

      newMap.on('mouseenter', 'affected-intersections-layer', () => {
        if (isRoutingActiveRef.current) return;
        newMap.getCanvas().style.cursor = 'pointer';
      });
      newMap.on('mouseleave', 'affected-intersections-layer', () => {
        if (isRoutingActiveRef.current) {
          newMap.getCanvas().style.cursor = 'crosshair';
          return;
        }
        newMap.getCanvas().style.cursor = '';
      });

      // Interactive popup on cell/waterbody click
      newMap.on('click', 'flood-depth-layer', (e) => {
        if (isRoutingActiveRef.current) return;
        if (!e.features || e.features.length === 0) return;
        const feature = e.features[0];
        const depth = feature.properties?.depth != null ? Number(feature.properties.depth) : 0;
        const cellCount = feature.properties?.cell_count != null ? Number(feature.properties.cell_count) : 1;
        const minDepth = feature.properties?.min_depth != null ? Number(feature.properties.min_depth) : depth;
        const maxDepth = feature.properties?.max_depth != null ? Number(feature.properties.max_depth) : depth;
        const meanDepth = feature.properties?.mean_depth != null ? Number(feature.properties.mean_depth) : depth;
        const depthBand = feature.properties?.depth_class as string | undefined;

        const depthM = depth.toFixed(2);
        const depthCm = Math.round(depth * 100);
        const risk = getRiskCategory(depth);

        const isHistorical = appModeRef.current === 'HISTORICAL';
        const isScenario = appModeRef.current === 'SCENARIO';
        const activeCfg = horizonsRef.current.find(h => h.key === activeHorizonRef.current);
        const liveRainStr = activeCfg && activeCfg.rainfallMm !== null ? `${activeCfg.rainfallMm.toFixed(1)} mm` : 'N/A';

        const currentHistStep = historicalDataRef.current?.timesteps?.[historicalStepRef.current];

        const headingText = isHistorical
          ? (cellCount > 1 ? `HISTORICAL FLOOD REGION (${cellCount} CONTIGUOUS CELLS)` : 'HISTORICAL SIMULATION CELL (30 m)')
          : isScenario
          ? 'MODEL SCENARIO CELL (30 m)'
          : 'MODELLED FLOOD CELL (30 m)';

        const depthDisplayRow = (isHistorical && cellCount > 1)
          ? `<div class="popup-row">
               <span class="lbl">Depth range:</span>
               <span class="val bold">${minDepth.toFixed(2)} – ${maxDepth.toFixed(2)} m (mean: ${meanDepth.toFixed(2)} m)</span>
             </div>
             <div class="popup-row">
               <span class="lbl">Depth band:</span>
               <span class="val">${depthBand || 'N/A'}</span>
             </div>
             <div class="popup-row">
               <span class="lbl">Contiguous area:</span>
               <span class="val">${cellCount} cells (~${(cellCount * 900).toLocaleString()} m²)</span>
             </div>`
          : `<div class="popup-row">
               <span class="lbl">Predicted depth:</span>
               <span class="val bold">${depthM} m (${depthCm} cm)</span>
             </div>`;

        const horizonOrScenarioRow = isHistorical
          ? `<div class="popup-row">
               <span class="lbl">Replay timestep:</span>
               <span class="val bold">${currentHistStep?.time_display || `Step ${historicalStepRef.current + 1}`}</span>
             </div>
             <div class="popup-row">
               <span class="lbl">Hourly rainfall:</span>
               <span class="val">${currentHistStep?.rainfall_mm?.toFixed(1) || '0.0'} mm</span>
             </div>`
          : isScenario
          ? `<div class="popup-row">
               <span class="lbl">Scenario rate:</span>
               <span class="val bold">${activeScenarioRef.current} mm/h</span>
             </div>`
          : `<div class="popup-row">
               <span class="lbl">Forecast horizon:</span>
               <span class="val">${activeHorizonRef.current} (${liveRainStr})</span>
             </div>`;

        const rainfallSourceVal = isHistorical
          ? 'Literature-calibrated historical forcing (Secondary-Report)'
          : isScenario
          ? 'Hypothetical model input (What-If)'
          : 'Weather forecast (Open-Meteo hourly NWP)';

        const dataStatusVal = isHistorical
          ? 'Retrospective Simulation (Copernicus GLO-30 DSM)'
          : 'Modelled (Copernicus GLO-30 DSM)';

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
                ${depthDisplayRow}
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
                  <span class="val status-modelled">${dataStatusVal}</span>
                </div>
              </div>
            </div>
          `)
          .addTo(newMap);
      });

      // Pointer cursor on hover over flooded cells
      newMap.on('mouseenter', 'flood-depth-layer', () => {
        if (isRoutingActiveRef.current) return;
        newMap.getCanvas().style.cursor = 'pointer';
      });
      newMap.on('mouseleave', 'flood-depth-layer', () => {
        if (isRoutingActiveRef.current) {
          newMap.getCanvas().style.cursor = 'crosshair';
          return;
        }
        newMap.getCanvas().style.cursor = '';
      });

      // Safe Route map click handler for selecting origin and destination
      newMap.on('click', (e) => {
        if (!isRoutingActiveRef.current) return;
        const coords: [number, number] = [
          Number(e.lngLat.lng.toFixed(5)),
          Number(e.lngLat.lat.toFixed(5))
        ];

        if (!routeOriginRef.current) {
          // 1st click: Set Origin
          setRouteOrigin(coords);
          routeOriginRef.current = coords;
          setRouteDestination(null);
          routeDestinationRef.current = null;
          setRouteResponse(null);
          setRouteError(null);
          updateRouteOnMapRef.current(null, coords, null);
        } else if (!routeDestinationRef.current) {
          // 2nd click: Set Destination and calculate
          const orig = routeOriginRef.current;
          setRouteDestination(coords);
          routeDestinationRef.current = coords;
          updateRouteOnMapRef.current(null, orig, coords);
          fetchSafeRouteRef.current(orig, coords);
        } else {
          // Subsequent click: Reset and start new Origin
          setRouteOrigin(coords);
          routeOriginRef.current = coords;
          setRouteDestination(null);
          routeDestinationRef.current = null;
          setRouteResponse(null);
          setRouteError(null);
          updateRouteOnMapRef.current(null, coords, null);
        }
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
      fetchHistoricalReplay();
    });

    return () => {
      if (popupRef.current) {
        popupRef.current.remove();
      }
      newMap.remove();
      mapInstanceRef.current = null;
    };
  }, [fetchForecastEvolution, fetchScenarioEvolution, fetchStreetForecastData, fetchStreetScenarioData, fetchHistoricalReplay, applyStreetDataToMap]);

  // Sync overlay layers visibility
  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!map) return;
    const isHist = appMode === 'HISTORICAL';

    const bmVis = isHist && showBenchmarksOverlay ? 'visible' : 'none';
    if (map.getLayer('historical-benchmarks-halo')) {
      map.setLayoutProperty('historical-benchmarks-halo', 'visibility', bmVis);
    }
    if (map.getLayer('historical-benchmarks-layer')) {
      map.setLayoutProperty('historical-benchmarks-layer', 'visibility', bmVis);
    }

    const streetVis = isHist
      ? (showHistoricalRoadsOverlay ? 'visible' : 'none')
      : (showStreetOverlay ? 'visible' : 'none');
    if (map.getLayer('affected-roads-layer')) {
      map.setLayoutProperty('affected-roads-layer', 'visibility', streetVis);
    }
    if (map.getLayer('affected-intersections-layer')) {
      map.setLayoutProperty('affected-intersections-layer', 'visibility', streetVis);
    }
  }, [appMode, showBenchmarksOverlay, showStreetOverlay, showHistoricalRoadsOverlay]);

  // Playback timer for Historical Replay
  useEffect(() => {
    if (!isPlaying || appMode !== 'HISTORICAL') return;

    const intervalId = setInterval(() => {
      setHistoricalStep((prev) => {
        const data = historicalDataRef.current;
        const maxStep = (data?.timesteps?.length ?? 24) - 1;
        if (prev >= maxStep) {
          setIsPlaying(false);
          return prev;
        }
        const next = prev + 1;
        if (historicalDataRef.current) {
          applyHistoricalStepToMap(next, historicalDataRef.current);
        }
        return next;
      });
    }, 1200);

    return () => clearInterval(intervalId);
  }, [isPlaying, appMode, applyHistoricalStepToMap]);

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
    if (routeOriginRef.current && routeDestinationRef.current) {
      fetchSafeRoute(routeOriginRef.current, routeDestinationRef.current, h);
    }
  };

  // Handle mode switch
  const handleSetMode = async (mode: AppMode) => {
    if (popupRef.current) {
      popupRef.current.remove();
    }
    setIsPlaying(false);
    setAppMode(mode);
    appModeRef.current = mode;

    if (mode === 'HISTORICAL') {
      let hData = historicalDataRef.current;
      if (!hData) {
        hData = await fetchHistoricalReplay();
      }
      if (hData) {
        applyHistoricalStepToMap(historicalStepRef.current, hData);
      }
      if (mapInstanceRef.current) {
        mapInstanceRef.current.flyTo({
          center: [72.8750, 19.0725],
          zoom: 13.8,
          duration: 1000
        });
      }
    } else if (mode === 'SCENARIO') {
      const syncHorizon = SCENARIO_TO_HORIZON[activeScenarioRef.current] || '+1h';
      setActiveHorizon(syncHorizon);
      activeHorizonRef.current = syncHorizon;
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

    if (routeOriginRef.current && routeDestinationRef.current) {
      fetchSafeRoute(routeOriginRef.current, routeDestinationRef.current, undefined, mode);
    }
  };

  // Handle scenario switch
  const handleSelectScenario = async (sc: ScenarioValue, targetHorizon?: ForecastHorizon) => {
    if (popupRef.current) {
      popupRef.current.remove();
    }
    const h = targetHorizon || SCENARIO_TO_HORIZON[sc] || '+1h';
    setActiveScenario(sc);
    activeScenarioRef.current = sc;
    setActiveHorizon(h);
    activeHorizonRef.current = h;

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

    if (routeOriginRef.current && routeDestinationRef.current) {
      fetchSafeRoute(routeOriginRef.current, routeDestinationRef.current, h, 'SCENARIO', sc);
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

  // Active statistics depending on appMode (LIVE vs SCENARIO vs HISTORICAL)
  const isScenarioMode = appMode === 'SCENARIO';
  const isHistoricalMode = appMode === 'HISTORICAL';
  const liveState = forecastData?.horizons?.find(h => h.horizon === activeHorizon);
  const scenarioState = scenarioData?.[activeScenario];
  const histStepState = historicalData?.timesteps?.[historicalStep];

  const maxDepthM = isHistoricalMode
    ? (histStepState?.peak_flood_depth_m ?? 0)
    : isScenarioMode
    ? (scenarioState?.max_depth_m ?? (activeScenario === 20 ? 0 : activeScenario === 40 ? 0.14 : activeScenario === 50 ? 0.29 : 0.58))
    : (liveState?.max_depth_m ?? 0);

  const floodedAreaM2 = isHistoricalMode
    ? (histStepState?.flooded_area_m2 ?? 0)
    : isScenarioMode
    ? (scenarioState?.flooded_area_m2 ?? (activeScenario === 20 ? 0 : 45900))
    : (liveState?.flooded_area_m2 ?? 0);

  const riskInfo = getRiskCategory(maxDepthM);

  const statusTitle = isHistoricalMode
    ? `Historical Replay: ${histStepState?.time_display ?? `Step ${historicalStep + 1}`}`
    : isScenarioMode
    ? `Demo Horizon: ${activeHorizon} (${activeScenario} mm/h)`
    : currentHorizonConfig.periodDisplay;

  const statusKicker = isHistoricalMode
    ? 'RETROSPECTIVE EVENT SIMULATION'
    : isScenarioMode
    ? '3-HOUR FLOOD EVOLUTION DEMO'
    : 'PREDICTED CONDITIONS';

  const rainfallMetricVal = isHistoricalMode
    ? (histStepState?.rainfall_intensity_mm_per_hr != null ? histStepState.rainfall_intensity_mm_per_hr.toFixed(1) : '--')
    : isScenarioMode
    ? activeScenario.toFixed(1)
    : (currentHorizonConfig.rainfallMm !== null ? currentHorizonConfig.rainfallMm.toFixed(1) : '--');

  const rainfallMetricSub = isHistoricalMode
    ? 'Literature forcing (Secondary-Report)'
    : isScenarioMode
    ? `Evolution step ${activeHorizon}`
    : 'Weather forecast (Open-Meteo hourly NWP)';

  const rainfallMetricLabel = isHistoricalMode
    ? 'HISTORICAL RAIN RATE'
    : isScenarioMode
    ? 'DEMO RAIN RATE'
    : 'FORECAST RAINFALL';

  return (
    <div className="flood-app">
      {/* 1. TOP BAR: IMMEDIATE 3-SECOND SYSTEM IDENTITY */}
      <header className="app-topbar">
        <div className="topbar-left">
          <div className="system-identity">
            <span className="system-mark">⛯</span>
            <span className="system-title text-2xl font-bold tracking-tight">URBAN FLOOD NOWCAST</span>
          </div>
          <span className="topbar-sep">|</span>
          <div className="system-location">
            <span className="loc-label text-base font-bold">MUMBAI</span>
          </div>
          <span className="topbar-sep">|</span>
          <div className="system-subtitle text-sm font-normal">
            <span>
              {isHistoricalMode
                ? 'RETROSPECTIVE EVENT REPLAY'
                : isScenarioMode
                ? 'WHAT-IF FLOOD SCENARIO'
                : '0–3 HOUR FLOOD OUTLOOK'}
            </span>
          </div>
          <div
            className="prototype-status-pill"
            style={
              isHistoricalMode
                ? { background: '#78350f', borderColor: '#d97706' }
                : isScenarioMode
                ? { background: '#0284c7', borderColor: '#38bdf8' }
                : undefined
            }
          >
            <span
              className="status-dot"
              style={
                isHistoricalMode
                  ? { background: '#fef3c7' }
                  : isScenarioMode
                  ? { background: '#e0f2fe' }
                  : undefined
              }
            />
            <span>
              {isHistoricalMode
                ? 'HISTORICAL REPLAY'
                : isScenarioMode
                ? 'MODEL SCENARIO'
                : 'PROTOTYPE SCENARIO'}
            </span>
          </div>
        </div>

        <div className="topbar-right">
          <div className="telemetry-info">
            <span className="meta-tag text-xs font-normal tracking-wide">60-MIN TIMESTEP</span>
            <span className="meta-divider">•</span>
            {isHistoricalMode ? (
              <>
                <span
                  className="meta-tag text-xs font-normal tracking-wide"
                  style={{ background: '#78350f', borderColor: '#d97706', color: '#fef3c7' }}
                >
                  24-HR REPLAY
                </span>
                <span className="meta-divider">•</span>
                <span className="meta-label text-xs font-normal">EVENT:</span>
                <span className="meta-val text-sm font-medium" style={{ color: '#f59e0b' }}>
                  29 AUG 2017 — MUMBAI DELUGE
                </span>
                <span className="meta-divider">•</span>
                <span className="meta-label text-xs font-normal">FORCING:</span>
                <span className="meta-val text-sm font-medium" style={{ color: '#cbd5e1' }}>
                  Secondary-Report (320 mm)
                </span>
              </>
            ) : isScenarioMode ? (
              <>
                <span className="meta-label text-xs font-normal">INPUT:</span>
                <span className="meta-val text-sm font-medium" style={{ color: '#38bdf8' }}>
                  Hypothetical rainfall input ({activeScenario} mm/h)
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
                <span className="meta-val text-sm font-medium">Open-Meteo NWP ({rainfallStatus})</span>
                <span className="meta-divider">•</span>
                <span className="meta-label text-xs font-normal">ACQUIRED:</span>
                <span className="meta-val text-sm font-medium">
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
                className={`mode-toggle-btn ${appMode === 'LIVE' ? 'active' : ''}`}
                onClick={() => handleSetMode('LIVE')}
              >
                LIVE FORECAST
              </button>
              <button
                type="button"
                className={`mode-toggle-btn ${appMode === 'SCENARIO' ? 'scenario-active' : ''}`}
                onClick={() => handleSetMode('SCENARIO')}
              >
                MODEL SCENARIO
              </button>
              <button
                type="button"
                className={`mode-toggle-btn ${appMode === 'HISTORICAL' ? 'historical-active' : ''}`}
                onClick={() => handleSetMode('HISTORICAL')}
              >
                HISTORICAL REPLAY
              </button>
            </div>

            {appMode === 'HISTORICAL' ? (
              <>
                <div className="timeline-header">
                  <span className="timeline-heading text-sm font-bold tracking-wide" style={{ color: '#b45309' }}>29 AUG 2017 REPLAY</span>
                  <span className="timeline-active-tag text-xs font-medium" style={{ background: '#fef3c7', color: '#b45309' }}>
                    Step {historicalStep + 1}/24
                  </span>
                </div>
                <div className="historical-time-banner">
                  <span className="hist-time-main">
                    {histStepState?.time_display || '2017-08-29 --:-- IST'}
                  </span>
                </div>
                {/* Transport Controls */}
                <div className="historical-transport-row">
                  <button
                    type="button"
                    className="transport-btn"
                    onClick={() => {
                      setIsPlaying(false);
                      setHistoricalStep(0);
                      if (historicalData) applyHistoricalStepToMap(0, historicalData);
                    }}
                    title="Jump to Start (08:30 IST)"
                  >
                    ⏮
                  </button>
                  <button
                    type="button"
                    className="transport-btn"
                    onClick={() => {
                      setIsPlaying(false);
                      const s = Math.max(0, historicalStep - 1);
                      setHistoricalStep(s);
                      if (historicalData) applyHistoricalStepToMap(s, historicalData);
                    }}
                    title="Previous Timestep"
                  >
                    ◀
                  </button>
                  <button
                    type="button"
                    className={`transport-btn play-btn ${isPlaying ? 'playing' : ''}`}
                    onClick={() => {
                      if (isPlaying) {
                        setIsPlaying(false);
                      } else {
                        if (historicalStep >= 23) {
                          setHistoricalStep(0);
                          if (historicalData) applyHistoricalStepToMap(0, historicalData);
                        }
                        setIsPlaying(true);
                      }
                    }}
                    title={isPlaying ? 'Pause Replay' : 'Play Replay'}
                  >
                    {isPlaying ? '⏸ Pause' : '▶ Play'}
                  </button>
                  <button
                    type="button"
                    className="transport-btn"
                    onClick={() => {
                      setIsPlaying(false);
                      const s = Math.min(23, historicalStep + 1);
                      setHistoricalStep(s);
                      if (historicalData) applyHistoricalStepToMap(s, historicalData);
                    }}
                    title="Next Timestep"
                  >
                    ▶
                  </button>
                  <button
                    type="button"
                    className="transport-btn peak-btn"
                    onClick={() => {
                      setIsPlaying(false);
                      setHistoricalStep(5);
                      if (historicalData) applyHistoricalStepToMap(5, historicalData);
                    }}
                    title="Jump to Cloudburst Peak (Step 6 / 13:30 IST)"
                  >
                    ⚡ Peak
                  </button>
                </div>
                {/* Timeline Slider */}
                <div className="timeline-slider-container">
                  <input
                    type="range"
                    min={0}
                    max={23}
                    step={1}
                    value={historicalStep}
                    onChange={(e) => {
                      setIsPlaying(false);
                      const s = Number(e.target.value);
                      setHistoricalStep(s);
                      if (historicalData) applyHistoricalStepToMap(s, historicalData);
                    }}
                    className="historical-slider"
                  />
                  <div className="slider-ticks">
                    <span>08:30</span>
                    <span style={{ color: '#d97706', fontWeight: 700 }}>13:30 (Peak)</span>
                    <span>07:30 (+1d)</span>
                  </div>
                </div>
                {/* Step Forcing Summary */}
                <div className="historical-forcing-row">
                  <div className="hist-forcing-box">
                    <span className="h-lbl">Rain Rate:</span>
                    <span className="h-val">
                      {(histStepState?.rainfall_intensity_mm_per_hr ?? 0).toFixed(1)} mm/h
                    </span>
                  </div>
                  <div className="hist-forcing-box">
                    <span className="h-lbl">Cumulative:</span>
                    <span className="h-val">
                      {(histStepState?.cumulative_rainfall_mm ?? 0).toFixed(1)} mm
                    </span>
                  </div>
                  <div className="hist-forcing-box">
                    <span className="h-lbl">Tide:</span>
                    <span className="h-val">
                      {(histStepState?.boundary_level_m ?? 0).toFixed(2)} m
                    </span>
                  </div>
                </div>
                {/* Historical Layer Toggles */}
                <div className="historical-layers-row">
                  <span className="hist-layers-title">REPLAY LAYERS:</span>
                  <label className="hist-layer-toggle" title="Show modelled flooded roads for this historical timestep">
                    <input
                      type="checkbox"
                      checked={showHistoricalRoadsOverlay}
                      onChange={(e) => setShowHistoricalRoadsOverlay(e.target.checked)}
                    />
                    <span>Flooded Roads</span>
                  </label>
                  <label className="hist-layer-toggle" title="Show 4 official observed ground-truth hotspots (2017 validation)">
                    <input
                      type="checkbox"
                      checked={showBenchmarksOverlay}
                      onChange={(e) => setShowBenchmarksOverlay(e.target.checked)}
                    />
                    <span>Observed Hotspots</span>
                  </label>
                </div>
              </>
            ) : !isScenarioMode ? (
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
                  <span className="timeline-heading" style={{ color: '#0369a1' }}>DEMO RAINFALL EVOLUTION</span>
                  <span className="timeline-active-tag" style={{ background: '#e0f2fe', color: '#0369a1' }}>
                    {activeHorizon} • {activeScenario} mm/h
                  </span>
                </div>
                <div className="timeline-stepper">
                  {DEMO_EVOLUTION_SEQUENCE.map((item) => {
                    const isSelected = activeScenario === item.scenario;
                    return (
                      <button
                        key={item.horizon}
                        type="button"
                        className={`timeline-step-btn ${isSelected ? 'selected scenario-selected' : ''}`}
                        onClick={() => handleSelectScenario(item.scenario, item.horizon)}
                        title={`Forecast Horizon ${item.horizon} (${item.scenario} mm/h)`}
                      >
                        <span className="step-time">{item.horizon}</span>
                        <span className="step-rain-tag">{item.scenario} mm/h</span>
                      </button>
                    );
                  })}
                </div>
                <div className="scenario-direct-row">
                  <span className="direct-label">INTENSITY:</span>
                  <div className="direct-buttons">
                    {SCENARIO_VALUES.map((sc) => {
                      const isSelected = activeScenario === sc;
                      return (
                        <button
                          key={sc}
                          type="button"
                          className={`scenario-rate-pill ${isSelected ? 'active' : ''}`}
                          onClick={() => handleSelectScenario(sc, SCENARIO_TO_HORIZON[sc])}
                          title={`Select ${sc} mm/h intensity`}
                        >
                          {sc} mm/h
                        </button>
                      );
                    })}
                  </div>
                </div>
                <div className="scenario-explanatory-note">
                  3-HOUR EVOLUTION: Evaluates modeled flood progression from NOW (20 mm/h) through +3h (70 mm/h).
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
            <button
              type="button"
              className={`extent-btn routing-btn ${isRoutingActive ? 'active' : ''}`}
              onClick={handleToggleRouting}
              title="Toggle Flood-Safe Route Finder (click map origin & destination)"
            >
              🧭 Safe Route {isRoutingActive ? '●' : ''}
            </button>
          </div>

          {/* FLOOD STATUS & RISK ASSESSMENT PANEL (High Visual Hierarchy) */}
          <div className="flood-status-panel">
            <div className="status-panel-top">
              <div className="status-horizon-kicker text-xs font-medium uppercase tracking-widest text-gray-500">{statusKicker}</div>
              <div className="status-horizon-title text-xl font-bold tracking-tight">{statusTitle}</div>
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
                  {isHistoricalMode ? 'SIMULATED RISK' : isScenarioMode ? 'SCENARIO RISK' : 'PREDICTED RISK'}
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
            <div className="status-metric-grid grid grid-cols-2 gap-4 mt-4">
              <div className="grid-metric-box bg-gray-50 p-3 rounded-md">
                <span className="metric-box-label text-xs font-semibold uppercase tracking-wider text-gray-500">{rainfallMetricLabel}</span>
                <span className="metric-box-val block text-2xl font-bold tracking-tight">
                  {rainfallMetricVal}{' '}
                  <span className="sub-unit text-sm font-medium text-gray-400">mm</span>
                </span>
                <span className="metric-box-sub block text-xs font-normal text-gray-600">
                  {rainfallMetricSub}
                </span>
              </div>
              <div className="grid-metric-box bg-gray-50 p-3 rounded-md">
                <span className="metric-box-label text-xs font-semibold uppercase tracking-wider text-gray-500">INUNDATED AREA</span>
                <span className="metric-box-val block text-2xl font-bold tracking-tight">
                  {Math.round(floodedAreaM2)} <span className="sub-unit text-sm font-medium text-gray-400">m²</span>
                </span>
                <span className="metric-box-sub block text-xs font-normal text-gray-600">30m DEM grid</span>
              </div>
            </div>

            {/* SIMULATION SUMMARY FOOTER */}
            <div className="status-panel-footer">
              <div className="footer-engine-title text-sm font-semibold uppercase tracking-wider text-gray-700">MODEL PIPELINE</div>
              <div className="footer-engine-desc text-xs font-normal text-gray-500 mb-2">
                Rainfall–runoff + drainage capacity + surface routing
              </div>
              <div className="footer-engine-param text-xs font-medium text-gray-600 bg-gray-100 p-2 rounded">
                {isHistoricalMode
                  ? 'Conveyance: 100% capacity • 78 inlets • Runoff C = 0.7'
                  : isScenarioMode && activeScenario === 20
                  ? 'Conveyance: 100% capacity • 0 surcharge'
                  : 'Runoff C = 0.7 • 60-minute model timestep'}
              </div>
            </div>
          </div>

          {/* HISTORICAL REPLAY: EVENT PEAK SUMMARY CARD */}
          {isHistoricalMode && historicalData?.event_summary && (
            <div className="event-summary-card p-4 bg-white rounded-lg border border-gray-200">
              <div className="event-summary-header flex justify-between items-center mb-4">
                <span className="summary-title text-sm font-bold uppercase tracking-wider text-gray-800">2017 EVENT PEAK METRICS</span>
                <span className="summary-badge text-xs font-semibold px-2 py-1 bg-gray-100 text-gray-600 rounded">SIMULATION</span>
              </div>
              <div className="event-summary-grid grid grid-cols-2 gap-4">
                <div className="event-stat-box">
                  <span className="stat-label block text-xs font-medium text-gray-500 mb-1">Peak Modeled Depth</span>
                  <span className="stat-val highlight block text-lg font-bold text-gray-900 tracking-tight">{historicalData.event_summary.peak_depth.value.toFixed(3)} m</span>
                  <span className="stat-sub block text-xs text-gray-400">{historicalData.event_summary.peak_depth.time_display}</span>
                </div>
                <div className="event-stat-box">
                  <span className="stat-label">Peak Flooded Area</span>
                  <span className="stat-val">{Math.round(historicalData.event_summary.peak_flooded_area.value).toLocaleString()} m²</span>
                  <span className="stat-sub">{historicalData.event_summary.peak_flooded_area.time_display}</span>
                </div>
                <div className="event-stat-box">
                  <span className="stat-label">Peak Drainage Surcharge</span>
                  <span className="stat-val">{Math.round(historicalData.event_summary.peak_surcharge.value).toLocaleString()} m³</span>
                  <span className="stat-sub">{historicalData.event_summary.peak_surcharge.time_display}</span>
                </div>
                <div className="event-stat-box">
                  <span className="stat-label">Peak Surface Volume</span>
                  <span className="stat-val">{Math.round(historicalData.event_summary.peak_surface_volume.value).toLocaleString()} m³</span>
                  <span className="stat-sub">{historicalData.event_summary.peak_surface_volume.time_display}</span>
                </div>
              </div>
              <div className="event-summary-timing-note">
                Notice: Peak depth and surcharge peak at Step 6 (13:30 IST cloudburst), while sheet flow area peaks early at Step 2 (09:30 IST) before channel pooling.
              </div>
            </div>
          )}

          {/* HISTORICAL REPLAY: OBSERVED HOTSPOTS VALIDATION CARD */}
          {isHistoricalMode && historicalData?.validation_comparisons && (
            <div className="validation-panel-card">
              <div className="validation-panel-header">
                <div className="validation-title-group">
                  <span className="validation-title">OBSERVED 2017 HOTSPOTS</span>
                  <span className="validation-count">4 BENCHMARKS</span>
                </div>
                <label className="validation-toggle-label">
                  <input
                    type="checkbox"
                    checked={showBenchmarksOverlay}
                    onChange={(e) => setShowBenchmarksOverlay(e.target.checked)}
                  />
                  <span>Show on Map</span>
                </label>
              </div>
              <div className="validation-table-container">
                <table className="validation-table">
                  <thead>
                    <tr>
                      <th>Location</th>
                      <th>Observed</th>
                      <th>Modeled</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {historicalData.validation_comparisons.map((comp) => {
                      const obsStr = comp.observed_depth_range || (comp.observed_max_depth_m
                        ? `${comp.observed_min_depth_m.toFixed(2)}–${comp.observed_max_depth_m.toFixed(2)} m`
                        : `>2.20 m`);
                      const modStr = comp.matched_depth_m != null ? `${comp.matched_depth_m.toFixed(3)} m` : 'None';
                      const statusInfo = (() => {
                        if (comp.spatial_status === 'OUTSIDE_PILOT_EXTENT') {
                          return { text: 'Outside Pilot', css: 'status-outside-pilot-extent' };
                        }
                        if (comp.matched_depth_m === 0 || comp.matched_depth_m === null) {
                          return { text: 'Dry Cell', css: 'status-dry-cell' };
                        }
                        if (!comp.within_observed_range) {
                          return { text: 'Outside Range', css: 'status-outside-range' };
                        }
                        return { text: 'In Range', css: 'status-in-range' };
                      })();
                      return (
                        <tr key={comp.location_id}>
                          <td className="loc-col" title={comp.location_name}>
                            <span className="loc-name-text">{comp.location_name}</span>
                          </td>
                          <td className="obs-col">{obsStr}</td>
                          <td className="mod-col">{modStr}</td>
                          <td className="status-col">
                            <span className={`val-status-pill ${statusInfo.css}`}>
                              {statusInfo.text}
                            </span>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
              <div className="validation-disclaimer-note">
                ⚠️ 30 m pilot DEM and clipped drainage extent limit point-level localization.
              </div>
            </div>
          )}

          {/* 6. STREET & INTERSECTION FLOOD INTELLIGENCE */}
          {((!isHistoricalMode) || (isHistoricalMode && showHistoricalRoadsOverlay)) && (
            <div className="street-intelligence-panel">
              <div className="street-panel-header">
                <div className="street-header-title">
                  <span className="street-title-icon">🛣️</span> {isHistoricalMode ? 'MODELLED ROAD IMPACT' : 'STREET FLOOD RISK'}
                </div>
                {isHistoricalMode ? (
                  <span className="prov-tag tag-modelled" style={{ fontSize: '9px', padding: '2px 6px', background: '#fef3c7', color: '#92400e' }}>
                    Modelled (D8 + OSM)
                  </span>
                ) : (
                  <label className="street-toggle-label">
                    <input
                      type="checkbox"
                      checked={showStreetOverlay}
                      onChange={(e) => setShowStreetOverlay(e.target.checked)}
                    />
                    <span>Overlay</span>
                  </label>
                )}
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
                {isHistoricalMode
                  ? 'Modelled Retrospective Impact (OSM + 2D D8 routing) • Not historical field road observations'
                  : 'OSM road network + 2D D8 surface routing • Not municipal road sensors'}
              </div>
            </div>
          )}

          {/* DATA STATUS & PROVENANCE (Clear but Secondary) */}
          <div className="provenance-card">
            <div className="provenance-header">
              {isHistoricalMode
                ? 'HISTORICAL DATA PROVENANCE'
                : isScenarioMode
                ? 'SCENARIO PROVENANCE & STATUS'
                : 'DATA PROVENANCE & STATUS'}
            </div>
            <div className="provenance-list">
              <div className="provenance-item">
                <span className="prov-source">Rainfall</span>
                <span
                  className="prov-tag tag-modelled"
                  style={
                    isHistoricalMode
                      ? { background: '#fef3c7', color: '#92400e' }
                      : isScenarioMode
                      ? { background: '#e0f2fe', color: '#0369a1' }
                      : undefined
                  }
                >
                  {isHistoricalMode
                    ? 'SECONDARY-REPORT (Literature)'
                    : isScenarioMode
                    ? 'Hypothetical model input'
                    : `Open-Meteo NWP (${rainfallStatus})`}
                </span>
              </div>
              <div className="provenance-item">
                <span className="prov-source">Boundary / Tide</span>
                <span
                  className="prov-tag tag-modelled"
                  style={isHistoricalMode ? { background: '#fef3c7', color: '#92400e' } : undefined}
                >
                  {isHistoricalMode ? 'DERIVED (Astronomical Tide)' : 'Static pilot boundary'}
                </span>
              </div>
              <div className="provenance-item">
                <span className="prov-source">Elevation</span>
                <span className="prov-tag tag-modelled">Copernicus GLO-30 DSM (30m)</span>
              </div>
              <div className="provenance-item">
                <span className="prov-source">Flood depth</span>
                <span className="prov-tag tag-modelled">
                  {isHistoricalMode ? 'RETROSPECTIVE SIMULATION' : 'Modelled'}
                </span>
              </div>
              <div className="provenance-item">
                <span className="prov-source">Benchmarks</span>
                <span
                  className="prov-tag tag-prototype"
                  style={isHistoricalMode ? { background: '#fef3c7', color: '#92400e' } : undefined}
                >
                  {isHistoricalMode ? 'OBSERVED (Validation only)' : 'DEM-derived / prototype'}
                </span>
              </div>
              <div className="provenance-item">
                <span className="prov-source">Surface routing</span>
                <span className="prov-tag tag-modelled">Modelled (D8)</span>
              </div>
            </div>
            <div className="provenance-disclaimer">
              {isHistoricalMode
                ? 'RETROSPECTIVE EVENT REPLAY: Evaluates physics simulation against documented 29 August 2017 observations. Model is not tuned to fit observations.'
                : isScenarioMode
                ? 'WHAT-IF: evaluates modeled inundation under hypothetical rainfall. Elevation model sourced from Copernicus GLO-30 DSM (30m).'
                : 'NOTICE: Weather forecast sourced from Open-Meteo hourly NWP (not radar nowcast or observed rainfall). Elevation model sourced from Copernicus GLO-30 DSM (30m).'}
            </div>
          </div>
        </div>

        {/* FLOOD-SAFE ROUTE HUD PANEL (Floating Top-Right) */}
        {isRoutingActive && (
          <div className="safe-route-hud-panel">
            <div className="route-hud-header">
              <div className="route-hud-title-group">
                <span className="route-hud-icon">🧭</span>
                <span className="route-hud-title">FLOOD-SAFE ROUTE</span>
              </div>
              <div className="route-hud-actions">
                {routeResponse && (
                  <span className={`route-status-badge status-${routeResponse.status.toLowerCase()}`}>
                    {routeResponse.status === 'SAFE' && '✓ SAFE'}
                    {routeResponse.status === 'CAUTION' && '⚠️ CAUTION'}
                    {routeResponse.status === 'UNAVAILABLE' && '⛔ UNAVAILABLE'}
                    {routeResponse.status === 'NO_PATH_FOUND' && '✕ NO PATH'}
                  </span>
                )}
                <button
                  type="button"
                  className="route-close-btn"
                  onClick={handleToggleRouting}
                  title="Exit Safe Routing Mode"
                >
                  ✕
                </button>
              </div>
            </div>

            {/* Waypoints / Step Instruction */}
            <div className="route-step-banner">
              {!routeOrigin ? (
                <div className="step-prompt">
                  <span className="step-pin origin-pin">📍</span>
                  <span>Click map to place <strong>Origin</strong></span>
                </div>
              ) : !routeDestination ? (
                <div className="step-prompt">
                  <span className="step-pin dest-pin">🎯</span>
                  <span>Origin set. Click map for <strong>Destination</strong></span>
                </div>
              ) : routeLoading ? (
                <div className="step-prompt loading">
                  <span className="banner-spinner small" />
                  <span>Evaluating flood risk & road topology...</span>
                </div>
              ) : (
                <div className="step-locations">
                  <div className="loc-item">
                    <span className="loc-dot origin" />
                    <span className="loc-text" title={routeResponse?.start_snapped_to?.nearest_road_name || 'Origin'}>
                      {routeResponse?.start_snapped_to?.nearest_road_name || `${routeOrigin[1].toFixed(4)}, ${routeOrigin[0].toFixed(4)}`}
                    </span>
                  </div>
                  <div className="loc-arrow">↓</div>
                  <div className="loc-item">
                    <span className="loc-dot dest" />
                    <span className="loc-text" title={routeResponse?.end_snapped_to?.nearest_road_name || 'Destination'}>
                      {routeResponse?.end_snapped_to?.nearest_road_name || `${routeDestination[1].toFixed(4)}, ${routeDestination[0].toFixed(4)}`}
                    </span>
                  </div>
                </div>
              )}
            </div>

            {/* Demo Corridor Presets (Instant 1-click test for Judges) */}
            <div className="route-presets-section">
              <div className="presets-label">DEMO CORRIDORS (KURLA PILOT)</div>
              <div className="presets-buttons">
                <button
                  type="button"
                  className="preset-btn"
                  onClick={() => handleSelectPresetRoute([72.8750, 19.0650], [72.8850, 19.0800])}
                  title="LBS Marg to Premier Road corridor"
                >
                  LBS Marg → Premier Rd
                </button>
                <button
                  type="button"
                  className="preset-btn"
                  onClick={() => handleSelectPresetRoute([72.8680, 19.0700], [72.8820, 19.0750])}
                  title="SCLR to CST Road Junction corridor"
                >
                  SCLR → CST Rd
                </button>
              </div>
            </div>

            {/* Route Metrics Grid */}
            {routeResponse && (
              <>
                <div className="route-metrics-grid">
                  <div className="route-metric-card">
                    <span className="m-label">SAFE ROUTE</span>
                    <span className="m-val">
                      {(routeResponse.total_distance_m / 1000).toFixed(2)} <span className="m-unit">km</span>
                    </span>
                    <span className="m-sub">{Math.round(routeResponse.total_distance_m)} m</span>
                  </div>

                  <div className="route-metric-card">
                    <span className="m-label">SHORTEST ROUTE</span>
                    <span className="m-val">
                      {routeResponse.shortest_path_comparison
                        ? `${(routeResponse.shortest_path_comparison.distance_m / 1000).toFixed(2)} km`
                        : '--'}
                    </span>
                    <span className="m-sub">
                      {routeResponse.shortest_path_comparison
                        ? `${Math.round(routeResponse.shortest_path_comparison.distance_m)} m direct`
                        : ''}
                    </span>
                  </div>

                  <div className="route-metric-card">
                    <span className="m-label">DETOUR DELTA</span>
                    <span className="m-val highlight">
                      {routeResponse.shortest_path_comparison
                        ? `+${Math.max(0, Math.round(routeResponse.total_distance_m - routeResponse.shortest_path_comparison.distance_m))} m`
                        : '--'}
                    </span>
                    <span className="m-sub">Safety penalty</span>
                  </div>

                  <div className="route-metric-card">
                    <span className="m-label">MAX FLOOD DEPTH</span>
                    <span className={`m-val ${routeResponse.max_predicted_flood_depth_m > 0 ? 'highlight-danger' : ''}`}>
                      {routeResponse.max_predicted_flood_depth_m.toFixed(2)} <span className="m-unit">m</span>
                    </span>
                    <span className="m-sub">
                      {Math.round(routeResponse.max_predicted_flood_depth_m * 100)} cm along path
                    </span>
                  </div>
                </div>

                {/* Avoided Roads List */}
                {routeResponse.roads_avoided && routeResponse.roads_avoided.length > 0 && (
                  <div className="route-avoided-section">
                    <div className="avoided-header">
                      <span className="avoided-icon">🛡️</span>
                      <span className="avoided-title">AVOIDED FLOODED CORRIDORS</span>
                    </div>
                    <div className="avoided-tags">
                      {routeResponse.roads_avoided.map((rd, i) => (
                        <span key={i} className="avoided-tag">
                          ⛔ {rd}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Shortest path traverse note */}
                {routeResponse.shortest_path_comparison?.has_flooded_roads && (
                  <div className="route-comparison-note">
                    ⚠️ Direct shortest path has {routeResponse.shortest_path_comparison.flooded_road_count} flooded road segment(s) (up to {routeResponse.shortest_path_comparison.max_flood_depth_m.toFixed(2)}m deep). Safe route detours to dry/passable streets.
                  </div>
                )}

                {routeResponse.status === 'UNAVAILABLE' && (
                  <div className="route-unavailable-warning">
                    ⛔ No dry or safely passable route exists for current flood inundation without crossing major flood barriers (depth ≥ 0.30 m).
                  </div>
                )}
              </>
            )}

            {/* Route Error Notice */}
            {routeError && (
              <div className="route-error-banner">
                ⚠️ {routeError}
              </div>
            )}

            {/* Action Footer */}
            <div className="route-hud-footer">
              <button
                type="button"
                className="route-clear-btn"
                onClick={handleClearRoute}
                disabled={!routeOrigin && !routeDestination && !routeResponse}
              >
                Clear Route
              </button>
              <button
                type="button"
                className="route-exit-btn"
                onClick={handleToggleRouting}
              >
                Exit
              </button>
            </div>
          </div>
        )}

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