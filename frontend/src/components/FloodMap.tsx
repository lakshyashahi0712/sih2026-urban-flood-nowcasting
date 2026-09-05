import { useEffect, useRef, useState } from 'react';
import { Map as MapLibreMap, GeoJSONSource, NavigationControl, setWorkerUrl } from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import workerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?worker&url';

setWorkerUrl(workerUrl);

const FloodMap = () => {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const [map, setMap] = useState<MapLibreMap | null>(null);
  const [floodData, setFloodData] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!mapContainerRef.current) return;

    const newMap = new MapLibreMap({
      container: mapContainerRef.current,
      style: 'https://tiles.openfreemap.org/styles/liberty',
      center: [72.8777, 19.0760],
      zoom: 10
    });

    newMap.addControl(new NavigationControl({ visualizePitch: true }), 'top-right');

    newMap.on('error', (e) => {
      console.error('MapLibre error:', e);
    });

    newMap.on('load', () => {
      setMap(newMap);
    });

    const fetchFloodData = async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await fetch('http://localhost:8000/flood/model', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            rainfall_mm: 25.0,
            contributing_area_m2: 5000.0,
            runoff_coefficient: 0.7,
            timestep_hours: 1.0,
            threshold_area_m2: 10.0
          })
        });

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        setFloodData(data);
      } catch (err) {
        console.error('Error fetching flood data:', err);
        setError(err instanceof Error ? err.message : 'Unknown error');
      } finally {
        setLoading(false);
      }
    };

    const timer = setTimeout(fetchFloodData, 1000);

    return () => {
      clearTimeout(timer);
      newMap.remove();
    };
  }, []);

  useEffect(() => {
    if (map && floodData) {
      if (map.getSource('flood-depth')) {
        (map.getSource('flood-depth') as GeoJSONSource).setData(floodData);
      } else {
        map.addSource('flood-depth', {
          type: 'geojson',
          data: floodData
        });

        map.addLayer({
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
            'fill-opacity': 0.7
          }
        });

        map.addLayer({
          id: 'flood-depth-outline',
          type: 'line',
          source: 'flood-depth',
          paint: {
            'line-color': '#ffffff',
            'line-width': 0.5,
            'line-opacity': 0.7
          }
        });
      }
    }
  }, [map, floodData]);

  const renderLegend = () => {
    if (!map) return null;

    return (
      <div className="map-legend">
        <div className="legend-title">Flood Depth (m)</div>
        <div className="legend-items">
          <div className="legend-item">
            <div className="legend-color" style={{ backgroundColor: '#ffeda0' }}></div>
            <span>0.0 - 0.5</span>
          </div>
          <div className="legend-item">
            <div className="legend-color" style={{ backgroundColor: '#feb24c' }}></div>
            <span>0.5 - 1.0</span>
          </div>
          <div className="legend-item">
            <div className="legend-color" style={{ backgroundColor: '#f03b20' }}></div>
            <span>1.0 - 2.0</span>
          </div>
          <div className="legend-item">
            <div className="legend-color" style={{ backgroundColor: '#bd0026' }}></div>
            <span>2.0+</span>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="map-container">
      <div ref={mapContainerRef} className="map" />
      {loading && <div className="loading">Loading flood data...</div>}
      {error && <div className="error">Error: {error}</div>}
      {renderLegend()}
    </div>
  );
};

export default FloodMap;