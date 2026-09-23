import { useEffect, useRef, useState } from 'react';
import { Map as MapLibreMap, GeoJSONSource, NavigationControl, Popup } from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import {
  delhiApi,
  type DrainageGraphResponse,
  type GeoLayerResponse,
  type SafeRouteResponse,
  type SurfaceHotspot,
} from '../../api/delhi';
import RainOverlay from './RainOverlay';

// Kushak-Barapullah corridor, South Delhi.
const DELHI_CENTER: [number, number] = [77.2265, 28.5595];
const DELHI_ZOOM = 12.2;

// Live map state pushed up by the NOWCAST / REPLAY panels. Everything is
// derived from actual model data — never decorative invention.
export interface MapFlowState {
  reachStates: Record<string, 'COMPUTED' | 'BLOCKED' | 'UNKNOWN'>;
  timestamp: string | null;
  // Rainfall intensity for the active step (mm/h). null = UNKNOWN — the
  // rain overlay must then be OFF (never invent rainfall).
  rainIntensityMmH: number | null;
  rainKnown: boolean;
}

export interface RoutePickPoint {
  coords: [number, number];
  label?: string;
}

interface LayerSpec {
  id: string;
  label: string;
  type: 'line' | 'fill' | 'circle';
  color: string;
  opacity?: number;
  lineWidth?: number;
  radius?: number;
}

const LAYER_SPECS: LayerSpec[] = [
  {
    id: 'watershed',
    label: 'Catchment (27.66 km², provisional)',
    type: 'fill',
    color: '#38bdf8',
    opacity: 0.16,
  },
  {
    id: 'corridor_centerline',
    label: 'Modeled corridor (UG-01→OC-01→CD-01→OC-02)',
    type: 'line',
    color: '#0284c7',
    lineWidth: 3.5,
  },
  {
    id: 'cross_sections',
    label: 'Cross-sections (Appendix XII-derived)',
    type: 'line',
    color: '#7c3aed',
    lineWidth: 1.8,
  },
  {
    id: 'gsdl_occurrences',
    label: 'GSDL waterlogging occurrences (official)',
    type: 'circle',
    color: '#dc2626',
    radius: 3.2,
    opacity: 0.65,
  },
  {
    id: 'historical_landmarks',
    label: 'Historical network landmarks',
    type: 'circle',
    color: '#f59e0b',
    radius: 4.5,
  },
];

const SOURCE_PREFIX = 'delhi-geo-';
const EMPTY_FC = { type: 'FeatureCollection', features: [] } as const;

const DelhiMap = ({
  flowState,
  routeResult = null,
  routePicks = { origin: null, destination: null },
  pickTarget = null,
  onMapClick,
  onSegmentClick,
  drainageGraph = null,
  surfaceHotspots = [],
  depthCells = [],
  depthPolygons = null,
  scenarioRoadDepths = null,
  streetRisk = null,
}: {
  flowState: MapFlowState | null;
  routeResult?: SafeRouteResponse | null;
  routePicks?: { origin: RoutePickPoint | null; destination: RoutePickPoint | null };
  pickTarget?: 'origin' | 'destination' | null;
  onMapClick?: (lonlat: [number, number]) => void;
  onSegmentClick?: (segmentId: string) => void;
  drainageGraph?: DrainageGraphResponse | null;
  surfaceHotspots?: SurfaceHotspot[];
  depthCells?: { lon: number; lat: number; depth_cm: number; flood_state: string; provenance: string }[];
  depthPolygons?: { type: string; features: unknown[] } | null;
  scenarioRoadDepths?: Record<string, { depth_cm: number; depth_m: number; flood_state: string }> | null;
  streetRisk?: { roads_geojson: { type: string; features: unknown[] }; intersections_geojson: { type: string; features: unknown[] } } | null;
}) => {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<MapLibreMap | null>(null);
  const [mapReady, setMapReady] = useState(false);
  const [visible, setVisible] = useState<Record<string, boolean>>({
    watershed: true,
    corridor_centerline: true,
    cross_sections: false,
    gsdl_occurrences: true,
    historical_landmarks: true,
  });
  const [layerErrors, setLayerErrors] = useState<Record<string, string>>({});
  const [layersOpen, setLayersOpen] = useState(false);
  const flowRef = useRef<MapFlowState | null>(flowState);
  flowRef.current = flowState;
  const pickRef = useRef<{
    pickTarget: 'origin' | 'destination' | null;
    onMapClick?: (lonlat: [number, number]) => void;
  }>({ pickTarget, onMapClick });
  pickRef.current = { pickTarget, onMapClick };
  const segmentClickRef = useRef(onSegmentClick);
  segmentClickRef.current = onSegmentClick;

  useEffect(() => {
    if (!mapContainerRef.current || mapInstanceRef.current) return;

    const newMap = new MapLibreMap({
      container: mapContainerRef.current,
      style: 'https://tiles.openfreemap.org/styles/liberty',
      center: DELHI_CENTER,
      zoom: DELHI_ZOOM,
    });
    newMap.addControl(new NavigationControl({ showCompass: false }), 'top-right');
    mapInstanceRef.current = newMap;
    // V1 convention: expose the map instance for extent-control flyTo.
    (window as unknown as { map?: MapLibreMap }).map = newMap;
    newMap.on('error', (e) => {
      // Surface style/source errors instead of silently dropping layers.
      console.error('[delhi-map]', (e as unknown as { error?: Error }).error?.message || e);
    });

    newMap.on('load', async () => {
      for (const spec of LAYER_SPECS) {
        newMap.addSource(`${SOURCE_PREFIX}${spec.id}`, {
          type: 'geojson',
          data: { type: 'FeatureCollection', features: [] },
        });
        const sourceId = `${SOURCE_PREFIX}${spec.id}`;
        if (spec.type === 'fill') {
          newMap.addLayer({
            id: `layer-${spec.id}`,
            type: 'fill',
            source: sourceId,
            paint: {
              'fill-color': spec.color,
              'fill-opacity': spec.opacity ?? 0.2,
            },
          });
        } else if (spec.type === 'line') {
          newMap.addLayer({
            id: `layer-${spec.id}`,
            type: 'line',
            source: sourceId,
            paint: {
              'line-color': spec.color,
              'line-width': spec.lineWidth ?? 2,
              'line-opacity': spec.opacity ?? 0.9,
            },
          });
        } else {
          newMap.addLayer({
            id: `layer-${spec.id}`,
            type: 'circle',
            source: sourceId,
            paint: {
              'circle-color': spec.color,
              'circle-radius': spec.radius ?? 4,
              'circle-opacity': spec.opacity ?? 0.9,
              'circle-stroke-color': '#ffffff',
              'circle-stroke-width': 0.8,
            },
          });
        }
      }

      // V1 layer order: modelled flood DEPTH fill goes UNDER the street
      // corridors, junction markers and routes — never on top of them.
      newMap.addSource('flood-depth-polygons', { type: 'geojson', data: { ...EMPTY_FC } });
      newMap.addLayer({
        id: 'flood-depth-polygons',
        type: 'fill',
        source: 'flood-depth-polygons',
        paint: {
          'fill-color': ['get', 'color'],
          'fill-opacity': 0.85,
        },
      });
      // V1 water perimeter edge (subtle white outline above the fill).
      newMap.addLayer({
        id: 'flood-depth-outline',
        type: 'line',
        source: 'flood-depth-polygons',
        paint: {
          'line-color': '#ffffff',
          'line-width': 0.75,
          'line-opacity': 0.35,
        },
      });

      // Safe-routing layers (after evidence layers so routes sit on top).
      // Color-only is never the sole encoding: recommended is thick + white
      // cased, alternative is dashed, elevated solid amber, unknown dotted.
      newMap.addSource('route-recommended', { type: 'geojson', data: { ...EMPTY_FC } });
      newMap.addSource('route-alternative', { type: 'geojson', data: { ...EMPTY_FC } });
      newMap.addSource('route-risk-elevated', { type: 'geojson', data: { ...EMPTY_FC } });
      newMap.addSource('route-risk-unknown', { type: 'geojson', data: { ...EMPTY_FC } });
      newMap.addSource('street-risk-roads', { type: 'geojson', data: { ...EMPTY_FC } });
      newMap.addSource('street-risk-junctions', { type: 'geojson', data: { ...EMPTY_FC } });
      // V1 road-risk styling: risk-colored corridors + junction markers.
      newMap.addLayer({
        id: 'street-risk-roads',
        type: 'line',
        source: 'street-risk-roads',
        layout: { 'line-join': 'round', 'line-cap': 'round' },
        paint: {
          'line-color': [
            'match',
            ['get', 'risk_level'],
            'CRITICAL', '#dc2626',
            'HIGH', '#ea580c',
            'MEDIUM', '#f59e0b',
            'LOW', '#3b82f6',
            '#ffffff',
          ],
          'line-width': [
            'interpolate', ['linear'], ['zoom'],
            11, 2.5,
            14, 4.0,
            17, 7.0,
          ],
          'line-opacity': 0.95,
        },
      });
      newMap.addLayer({
        id: 'street-risk-junctions',
        type: 'circle',
        source: 'street-risk-junctions',
        paint: {
          'circle-radius': [
            'interpolate', ['linear'], ['zoom'],
            11, 4.0,
            14, 6.5,
            17, 10.0,
          ],
          'circle-color': [
            'match',
            ['get', 'risk_level'],
            'CRITICAL', '#dc2626',
            'HIGH', '#ea580c',
            'MEDIUM', '#f59e0b',
            'LOW', '#3b82f6',
            '#ffffff',
          ],
          'circle-stroke-width': 2,
          'circle-stroke-color': '#ffffff',
          'circle-opacity': 0.95,
        },
      });
      newMap.addSource('route-pins', { type: 'geojson', data: { ...EMPTY_FC } });
      newMap.addLayer({
        id: 'route-risk-elevated',
        type: 'line',
        source: 'route-risk-elevated',
        paint: { 'line-color': '#d97706', 'line-width': 7, 'line-opacity': 0.55 },
      });
      newMap.addLayer({
        id: 'route-risk-unknown',
        type: 'line',
        source: 'route-risk-unknown',
        paint: {
          'line-color': '#64748b',
          'line-width': 6,
          'line-opacity': 0.5,
          'line-dasharray': [1.5, 2],
        },
      });
      newMap.addLayer({
        id: 'route-alternative',
        type: 'line',
        source: 'route-alternative',
        layout: { 'line-cap': 'round', 'line-join': 'round' },
        paint: { 'line-color': '#475569', 'line-width': 4, 'line-dasharray': [2, 2] },
      });
      newMap.addLayer({
        id: 'route-recommended-casing',
        type: 'line',
        source: 'route-recommended',
        layout: { 'line-cap': 'round', 'line-join': 'round' },
        paint: { 'line-color': '#ffffff', 'line-width': 9, 'line-opacity': 0.9 },
      });
      newMap.addLayer({
        id: 'route-recommended',
        type: 'line',
        source: 'route-recommended',
        layout: { 'line-cap': 'round', 'line-join': 'round' },
        paint: { 'line-color': '#1d4ed8', 'line-width': 5 },
      });
      newMap.addSource('drainage-nodes', { type: 'geojson', data: { ...EMPTY_FC } });
      newMap.addSource('drainage-edges', { type: 'geojson', data: { ...EMPTY_FC } });
      newMap.addSource('surface-hotspots', { type: 'geojson', data: { ...EMPTY_FC } });
      newMap.addLayer({
        id: 'drainage-edges',
        type: 'line',
        source: 'drainage-edges',
        paint: {
          'line-color': '#94a3b8',
          'line-width': 2.5,
          'line-dasharray': [4, 3],
          'line-opacity': 0.75,
        },
      });
      newMap.addLayer({
        id: 'drainage-nodes',
        type: 'circle',
        source: 'drainage-nodes',
        paint: {
          'circle-radius': 4.5,
          'circle-color': '#475569',
          'circle-stroke-color': '#ffffff',
          'circle-stroke-width': 1.4,
        },
      });
      // Legacy scenario point/road layers removed: depth polygons (above,
      // under the street layer) are the single V1-style depth visualization,
      // and OSM street corridors carry the scenario road risk. The sources
      // stay registered so existing data pushes remain harmless.
      newMap.addSource('scenario-depth', { type: 'geojson', data: { ...EMPTY_FC } });
      newMap.addSource('scenario-roads', { type: 'geojson', data: { ...EMPTY_FC } });
      newMap.addLayer({
        id: 'surface-hotspots',
        type: 'circle',
        source: 'surface-hotspots',
        paint: {
          'circle-radius': ['*', 4, ['sqrt', ['get', 'surface_water_cm_estimated']]],
          'circle-color': '#0ea5e9',
          'circle-opacity': 0.55,
          'circle-stroke-color': '#164e63',
          'circle-stroke-width': 1,
        },
      });
      newMap.addLayer({
        id: 'route-pins',
        type: 'circle',
        source: 'route-pins',
        paint: {
          'circle-color': ['get', 'color'],
          'circle-radius': 7,
          'circle-stroke-color': '#ffffff',
          'circle-stroke-width': 2,
        },
      });
      setMapReady(true);
    });

    // V1-style popups on street/junction/depth layers.
    const popupRefLocal: { current: Popup | null } = { current: null };
    const showPopup = (e: any, html: (props: any) => string) => {
      if (!e.features || e.features.length === 0) return;
      const props = e.features[0].properties || {};
      if (popupRefLocal.current) popupRefLocal.current.remove();
      popupRefLocal.current = new Popup({ closeButton: true, closeOnClick: true, className: 'ops-popup' })
        .setLngLat(e.lngLat)
        .setHTML(html(props))
        .addTo(newMap);
    };

    newMap.on('click', 'street-risk-roads', (e) =>
      showPopup(e, (p) => `
        <div class="popup-box">
          <div class="popup-header">
            <span class="popup-title">AFFECTED STREET CORRIDOR</span>
            <span class="popup-badge risk-${String(p.risk_level || 'low').toLowerCase()}">${p.risk_level || ''}</span>
          </div>
          <div class="popup-body">
            <div class="popup-row"><span class="lbl">Street:</span><span class="val bold">${p.name || 'Unnamed'}</span></div>
            <div class="popup-row"><span class="lbl">Predicted depth:</span><span class="val bold" style="color:#c2410c">${Number(p.max_depth_m).toFixed(2)} m (${Math.round(Number(p.max_depth_m) * 100)} cm)</span></div>
            <div class="popup-row"><span class="lbl">Flooded corridor:</span><span class="val">${p.flooded_length_m} m</span></div>
            <div class="popup-row"><span class="lbl">Road geometry:</span><span class="val">OpenStreetMap (ODbL)</span></div>
            <div class="popup-row"><span class="lbl">Depth source:</span><span class="val status-modelled">Modelled (V1 depth grid, 30 m DSM)</span></div>
          </div>
        </div>`),
    );
    newMap.on('click', 'street-risk-junctions', (e) =>
      showPopup(e, (p) => `
        <div class="popup-box">
          <div class="popup-header">
            <span class="popup-title">AFFECTED INTERSECTION</span>
            <span class="popup-badge risk-${String(p.risk_level || 'low').toLowerCase()}">${p.risk_level || ''}</span>
          </div>
          <div class="popup-body">
            <div class="popup-row"><span class="lbl">Junction:</span><span class="val bold">${p.name || 'Junction'}</span></div>
            <div class="popup-row"><span class="lbl">Cross streets:</span><span class="val">${p.roads_display || p.name || ''}</span></div>
            <div class="popup-row"><span class="lbl">Predicted depth:</span><span class="val bold" style="color:#c2410c">${Number(p.max_depth_m).toFixed(2)} m (${Math.round(Number(p.max_depth_m) * 100)} cm)</span></div>
            <div class="popup-row"><span class="lbl">Topology:</span><span class="val">OpenStreetMap (ODbL)</span></div>
            <div class="popup-row"><span class="lbl">Depth source:</span><span class="val status-modelled">Modelled (V1 depth grid, 30 m DSM)</span></div>
          </div>
        </div>`),
    );
    newMap.on('click', 'flood-depth-polygons', (e) =>
      showPopup(e, (p) => `
        <div class="popup-box">
          <div class="popup-header">
            <span class="popup-title">MODELLED FLOOD CELL (30 m)</span>
            <span class="popup-badge risk-mod">${p.flood_state || ''}</span>
          </div>
          <div class="popup-body">
            <div class="popup-row"><span class="lbl">Predicted depth:</span><span class="val bold">${(Number(p.depth_cm) / 100).toFixed(2)} m (${Math.round(Number(p.depth_cm))} cm)</span></div>
            <div class="popup-row"><span class="lbl">Data status:</span><span class="val status-modelled">SIMULATED MODEL OUTPUT</span></div>
            <div class="popup-row"><span class="lbl">Basis:</span><span class="val">V1 reference model • enforced 30 m DSM</span></div>
          </div>
        </div>`),
    );

    // Map click -> route point picking; risk-segment clicks -> evidence.
    newMap.on('click', (e) => {
      const { pickTarget: target, onMapClick: click } = pickRef.current;
      if (target && click) {
        click([e.lngLat.lng, e.lngLat.lat]);
        return;
      }
      const feats = newMap.queryRenderedFeatures(e.point, {
        layers: ['route-risk-elevated', 'route-risk-unknown'],
      });
      if (feats.length > 0 && segmentClickRef.current) {
        const segId = feats[0].properties?.segment_id;
        if (typeof segId === 'string') segmentClickRef.current(segId);
      }
    });

    return () => {
      newMap.remove();
      mapInstanceRef.current = null;
    };
  }, []);

  // Fetch evidence layer data once the map is ready.
  useEffect(() => {
    if (!mapReady) return;
    const controller = new AbortController();
    const errors: Record<string, string> = {};

    (async () => {
      for (const spec of LAYER_SPECS) {
        try {
          const layer: GeoLayerResponse = await delhiApi.getGeoLayer(
            spec.id,
            controller.signal,
          );
          const map = mapInstanceRef.current;
          const source = map?.getSource(`${SOURCE_PREFIX}${spec.id}`) as
            | GeoJSONSource
            | undefined;
          if (map && source && map.getSource(`${SOURCE_PREFIX}${spec.id}`)) {
            source.setData(layer.geojson as never);
          }
        } catch (err) {
          errors[spec.id] = err instanceof Error ? err.message : 'load failed';
        }
      }
      setLayerErrors(errors);
    })();

    return () => controller.abort();
  }, [mapReady]);

  // Toggle evidence layer visibility.
  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!map || !mapReady) return;
    for (const spec of LAYER_SPECS) {
      const layerId = `layer-${spec.id}`;
      if (map.getLayer(layerId)) {
        map.setLayoutProperty(
          layerId,
          'visibility',
          visible[spec.id] ? 'visible' : 'none',
        );
      }
    }
  }, [visible, mapReady]);

  // Route layers + pins data push.
  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!map || !mapReady) return;
    const set = (src: string, data: unknown) => {
      const source = map.getSource(src) as GeoJSONSource | undefined;
      if (source) source.setData(data as never);
    };
    set('route-recommended', routeResult?.recommended_route?.geometry ?? EMPTY_FC);
    set('route-alternative', routeResult?.alternative_route?.geometry ?? EMPTY_FC);
    const elevated =
      routeResult?.recommended_route?.risk_segments?.features.filter(
        (f) => f.properties.risk_state === 'ELEVATED_RISK',
      ) ?? [];
    const unknown =
      routeResult?.recommended_route?.risk_segments?.features.filter(
        (f) => f.properties.risk_state === 'UNKNOWN',
      ) ?? [];
    set('route-risk-elevated', { type: 'FeatureCollection', features: elevated });
    set('route-risk-unknown', { type: 'FeatureCollection', features: unknown });

    const pinFeatures: object[] = [];
    if (routePicks.origin) {
      pinFeatures.push({
        type: 'Feature',
        properties: { color: '#1d4ed8', label: 'origin' },
        geometry: { type: 'Point', coordinates: routePicks.origin.coords },
      });
    }
    if (routePicks.destination) {
      pinFeatures.push({
        type: 'Feature',
        properties: { color: '#dc2626', label: 'destination' },
        geometry: { type: 'Point', coordinates: routePicks.destination.coords },
      });
    }
    set('route-pins', { type: 'FeatureCollection', features: pinFeatures });

    if (routeResult?.recommended_route?.geometry?.coordinates?.length) {
      const coords = routeResult.recommended_route.geometry.coordinates;
      let minLon = coords[0][0];
      let maxLon = coords[0][0];
      let minLat = coords[0][1];
      let maxLat = coords[0][1];
      for (let i = 1; i < coords.length; i++) {
        const [lon, lat] = coords[i];
        if (lon < minLon) minLon = lon;
        if (lon > maxLon) maxLon = lon;
        if (lat < minLat) minLat = lat;
        if (lat > maxLat) maxLat = lat;
      }
      const isMobile = typeof window !== 'undefined' && window.innerWidth <= 768;
      map.fitBounds(
        [[minLon, minLat], [maxLon, maxLat]],
        {
          padding: isMobile
            ? { top: 90, bottom: 270, left: 30, right: 30 }
            : { top: 70, bottom: 70, left: 450, right: 360 },
          maxZoom: 14.5,
          duration: 900,
        },
      );
    }
  }, [routeResult, routePicks, mapReady]);

  // Set map cursor to crosshair while picking points
  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!map || !mapReady) return;
    try {
      const canvas = map.getCanvas();
      if (canvas) {
        canvas.style.cursor = pickTarget ? 'crosshair' : '';
      }
    } catch {
      // ignore
    }
  }, [pickTarget, mapReady]);

  // Drainage graph + surface hotspot layers.
  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!map || !mapReady) return;
    const set = (src: string, data: unknown) => {
      const source = map.getSource(src) as GeoJSONSource | undefined;
      if (source) source.setData(data as never);
    };
    set('drainage-nodes', drainageGraph?.nodes ?? EMPTY_FC);
    set('drainage-edges', drainageGraph?.edges ?? EMPTY_FC);
    set('scenario-depth', {
      type: 'FeatureCollection',
      features: depthCells.map((c) => ({
        type: 'Feature',
        properties: { depth_cm: c.depth_cm, flood_state: c.flood_state },
        geometry: { type: 'Point', coordinates: [c.lon, c.lat] },
      })),
    });
    set('flood-depth-polygons', depthPolygons ?? EMPTY_FC);
    // Flooded roads: drainage graph edges recolored by scenario road depth.
    const roadFeatures = (drainageGraph?.edges?.features ?? []).map((f) => {
      const d = scenarioRoadDepths?.[f.properties.edge_id];
      return {
        ...f,
        properties: {
          ...f.properties,
          flood_state: d ? d.flood_state : 'DRY',
          depth_cm: d ? d.depth_cm : 0,
        },
      };
    });
    set('scenario-roads', { type: 'FeatureCollection', features: roadFeatures });
    set('surface-hotspots', {
      type: 'FeatureCollection',
      features: surfaceHotspots.map((h) => ({
        type: 'Feature',
        properties: { surface_water_cm_estimated: h.surface_water_cm_estimated },
        geometry: { type: 'Point', coordinates: [h.lon, h.lat] },
      })),
    });
    set('street-risk-roads', streetRisk?.roads_geojson ?? EMPTY_FC);
    set('street-risk-junctions', streetRisk?.intersections_geojson ?? EMPTY_FC);
  }, [drainageGraph, surfaceHotspots, depthCells, depthPolygons, scenarioRoadDepths, streetRisk, mapReady]);

  // Subtle corridor "live flow" pulse: only while the model reports a
  // computed flow state, and disabled under prefers-reduced-motion.
  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!map || !mapReady) return;
    const layerId = 'layer-corridor_centerline';
    if (!map.getLayer(layerId)) return;

    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const anyComputed = Object.values(flowState?.reachStates ?? {}).some(
      (s) => s === 'COMPUTED',
    );
    const anyBlocked = Object.values(flowState?.reachStates ?? {}).some(
      (s) => s === 'BLOCKED',
    );

    if (reduced || !anyComputed) {
      map.setPaintProperty(layerId, 'line-opacity', 0.9);
      map.setPaintProperty(
        layerId,
        'line-color',
        anyBlocked && !anyComputed ? '#b45309' : '#0284c7',
      );
      return;
    }

    let raf: number | null = null;
    const start = performance.now();
    const tick = (now: number) => {
      const t = ((now - start) / 2000) % 1; // 2 s gentle loop
      const opacity = 0.72 + 0.26 * (0.5 - 0.5 * Math.cos(2 * Math.PI * t));
      if (map.getLayer(layerId)) {
        map.setPaintProperty(layerId, 'line-opacity', opacity);
      }
      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => {
      if (raf !== null) cancelAnimationFrame(raf);
      if (map.getLayer(layerId)) map.setPaintProperty(layerId, 'line-opacity', 0.9);
    };
  }, [flowState?.reachStates, mapReady]);

  const anyComputedOuter = Object.values(flowState?.reachStates ?? {}).some(
    (s) => s === 'COMPUTED',
  );
  const anyBlockedOuter = Object.values(flowState?.reachStates ?? {}).some(
    (s) => s === 'BLOCKED',
  );
  const flowLabel = anyComputedOuter
    ? 'MODEL FLOW: COMPUTED'
    : anyBlockedOuter
      ? 'MODEL FLOW: BLOCKED (UNKNOWN FORCING)'
      : null;

  return (
    <div className="delhi-map-wrap">
      <div
        ref={mapContainerRef}
        className={`delhi-map-viewport ${pickTarget ? 'picking' : ''}`}
      />
      <RainOverlay intensityMmH={flowState?.rainIntensityMmH ?? null} />

      {/* Prominent replay/step timestamp */}
      {flowState?.timestamp && (
        <div className="map-time-chip" role="status">
          <span className="time-chip-label">REPLAY T</span>
          <span className="time-chip-value">
            {new Date(flowState.timestamp).toLocaleTimeString([], {
              hour: '2-digit',
              minute: '2-digit',
            })}
          </span>
          <span className="time-chip-tz">IST</span>
        </div>
      )}

      <div className="map-left-meta">
        {flowLabel && (
          <span className={`flow-chip ${anyComputedOuter ? 'ok' : 'warn'}`}>
            {flowLabel}
          </span>
        )}
        {flowState != null && !flowState.rainKnown && flowState.timestamp !== null && (
          <span className="flow-chip warn">RAIN: UNKNOWN — NO ANIMATION</span>
        )}
        {pickTarget && (
          <span className="flow-chip ok">
            CLICK MAP TO SET {pickTarget.toUpperCase()}
          </span>
        )}
      </div>

      {/* Route legend (style, not color alone) */}
      {routeResult && (
        <div className="route-legend">
          <div className="delhi-layers-title">ROUTE LEGEND</div>
          <span className="legend-row">
            <i className="lg-route recommended" /> recommended route
          </span>
          {routeResult.alternative_route && (
            <span className="legend-row">
              <i className="lg-route alternative" /> alternative (dashed)
            </span>
          )}
          <span className="legend-row">
            <i className="lg-route elevated" /> ELEVATED-RISK (model-derived loading)
          </span>
          <span className="legend-row">
            <i className="lg-route unknown" /> UNKNOWN (no model coverage — not safe)
          </span>
        </div>
      )}

      <div className={`delhi-map-layers ${layersOpen ? 'expanded' : 'collapsed'}`}>
        <div
          className="delhi-layers-header"
          onClick={() => setLayersOpen((v) => !v)}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => {
            if (e.key === 'Enter' || e.key === ' ') {
              e.preventDefault();
              setLayersOpen((v) => !v);
            }
          }}
          aria-expanded={layersOpen}
        >
          <div className="delhi-layers-title">
            LAYERS ({LAYER_SPECS.filter((s) => visible[s.id]).length}/{LAYER_SPECS.length})
          </div>
          <button
            type="button"
            className="delhi-layers-toggle-btn"
            aria-label={layersOpen ? 'Collapse layers list' : 'Expand layers list'}
          >
            {layersOpen ? '▾' : '▴'}
          </button>
        </div>
        <div className="delhi-layers-content">
          {LAYER_SPECS.map((spec) => (
            <label key={spec.id} className="delhi-layer-row">
              <input
                type="checkbox"
                checked={!!visible[spec.id]}
                onChange={(e) =>
                  setVisible((v) => ({ ...v, [spec.id]: e.target.checked }))
                }
              />
              <span
                className="delhi-layer-swatch"
                style={{
                  background:
                    spec.type === 'fill' ? `${spec.color}55` : spec.color,
                }}
              />
              <span className="delhi-layer-label">{spec.label}</span>
            </label>
          ))}
          {Object.keys(layerErrors).length > 0 && (
            <div className="delhi-layer-error">
              {Object.entries(layerErrors).map(([id, msg]) => (
                <div key={id}>
                  layer {id}: {msg}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
      <div className="delhi-map-provenance">
        All layers are derived or documented evidence — geometry provenance is
        labeled per layer. Catchment boundary is a PROVISIONAL model input, not
        an authoritative boundary.
      </div>
    </div>
  );
};

export default DelhiMap;
