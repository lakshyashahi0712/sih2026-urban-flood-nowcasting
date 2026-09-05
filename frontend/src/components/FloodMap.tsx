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
        console.log('Flood data received:', data);

        // Verify 1: Confirm POST /flood/model returns the georeferenced polygon
        if (data.features && data.features.length > 0) {
          const feature = data.features[0];
          console.log('First flood feature:', feature);

          // Verify 2: Confirm the returned polygon is around [72.878, 19.075]
          if (feature.geometry && feature.geometry.coordinates) {
            const coords = feature.geometry.coordinates[0]; // Exterior ring of polygon
            if (coords.length > 0) {
              const firstCoord = coords[0];
              console.log('First coordinate pair:', firstCoord);

              // Check if coordinates are in Mumbai range (~72-73 longitude, 18-20 latitude)
              const [lon, lat] = firstCoord;
              const isInMumbaiRange = lon >= 72 && lon <= 73 && lat >= 18 && lat <= 20;
              console.log('Coordinate in Mumbai range (72-73, 18-20):', isInMumbaiRange, {lon, lat});

              // Calculate min/max bounds
              const lons = coords.map(c => c[0]);
              const lats = coords.map(c => c[1]);
              console.log('Longitude range:', Math.min(...lons), '-', Math.max(...lons));
              console.log('Latitude range:', Math.min(...lats), '-', Math.max(...lats));
            }
          }
        }

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
      console.log('Updating flood map with data:', floodData);

      if (map.getSource('flood-depth')) {
        console.log('Updating existing flood-depth source');
        (map.getSource('flood-depth') as GeoJSONSource).setData(floodData);
      } else {
        console.log('Adding new flood-depth source');
        map.addSource('flood-depth', {
          type: 'geojson',
          data: floodData
        });

        console.log('Adding flood-depth-layer');
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

        console.log('Adding flood-depth-outline');
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

        // Verify 3: Confirm the MapLibre source "flood-depth" exists after floodData loads
        const source = map.getSource('flood-depth');
        console.log('Source "flood-depth" exists:', !!source);

        // Verify 4: Confirm layers "flood-depth-layer" and "flood-depth-outline" exist
        const layer1 = map.getLayer('flood-depth-layer');
        const layer2 = map.getLayer('flood-depth-outline');
        console.log('Layer "flood-depth-layer" exists:', !!layer1);
        console.log('Layer "flood-depth-outline" exists:', !!layer2);

        // Verify 5: Log the flood layer's rendered feature count using queryRenderedFeatures if appropriate
        // Note: queryRenderedFeatures requires map to be rendered and visible
        // We'll use a small timeout to allow rendering
        setTimeout(() => {
          try {
            const features = map.queryRenderedFeatures({ layers: ['flood-depth-layer'] });
            console.log('Rendered feature count for flood-depth-layer:', features.length);

            // Verify 6: Temporarily zoom the map to approximately zoom 15 around the first flood feature
            if (features.length > 0 && floodData.features && floodData.features.length > 0) {
              const firstFeature = floodData.features[0];
              if (firstFeature.geometry && firstFeature.geometry.coordinates) {
                const coords = firstFeature.geometry.coordinates[0]; // Exterior ring
                if (coords.length > 0) {
                  const firstCoord = coords[0];
                  const [lon, lat] = firstCoord;
                  console.log('Zooming to first flood feature at:', [lon, lat]);
                  map.setCenter([lon, lat]);
                  map.setZoom(15);
                }
              }
            }
          } catch (e) {
            console.error('Error querying rendered features or zooming:', e);
          }
        }, 1000);
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