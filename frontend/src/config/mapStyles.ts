/**
 * Map basemap style configurations for SIH 2026 Urban Flood Nowcasting.
 *
 * Implements Prompt 1 of the dual-basemap system:
 * - LIGHT (Default): OpenFreeMap Liberty style, preserving existing appearance & behavior.
 * - DARK: CARTO Dark Matter style, specifically designed for emergency geospatial operations:
 *   - Very dark charcoal background (#0e0e0e)
 *   - Dark blue-gray water bodies (#2C353C) & waterways (rgba(63, 90, 109, 1))
 *   - Subdued dark/slate gray road hierarchy with brighter major arterials
 *   - Subtle low-contrast building footprints (rgba(57, 57, 57, 1))
 *   - Legible light gray labels with dark halos
 *   - Visually quiet backdrop ensuring flood depths, road risk, drainage, and routing remain primary.
 *
 * Prompt 2 will introduce the UI toggle control without requiring style refactoring.
 */

export type MapTheme = 'LIGHT' | 'DARK';

export interface BasemapConfig {
  id: MapTheme;
  label: string;
  name: string;
  url: string;
  description: string;
  backgroundColor: string;
  waterColor: string;
}

export const BASEMAP_STYLES: Record<MapTheme, BasemapConfig> = {
  LIGHT: {
    id: 'LIGHT',
    label: 'Light',
    name: 'OpenFreeMap Liberty',
    url: 'https://tiles.openfreemap.org/styles/liberty',
    description: 'High-clarity daytime street basemap for general reference and navigation.',
    backgroundColor: '#f8f4f0',
    waterColor: '#73b2ff',
  },
  DARK: {
    id: 'DARK',
    label: 'Dark',
    name: 'CARTO Dark Matter (Geospatial Ops)',
    url: 'https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json',
    description: 'Subdued charcoal basemap with dark blue-gray water and low-contrast infrastructure, optimized for emergency flood operations.',
    backgroundColor: '#0e0e0e',
    waterColor: '#2C353C',
  },
};

/**
 * Alternative OpenFreeMap Dark style URL for environments with restricted external CDNs.
 */
export const OFM_DARK_STYLE_URL = 'https://tiles.openfreemap.org/styles/dark';

export const DEFAULT_MAP_THEME: MapTheme = 'LIGHT';

/**
 * Resolves the initial map theme.
 * Checks URL query parameters (?theme=dark or ?theme=light) if available,
 * otherwise strictly defaults to DEFAULT_MAP_THEME ('LIGHT').
 */
export function getInitialMapTheme(): MapTheme {
  if (typeof window !== 'undefined') {
    const params = new URLSearchParams(window.location.search);
    const themeParam = params.get('theme')?.toUpperCase();
    if (themeParam === 'DARK') return 'DARK';
    if (themeParam === 'LIGHT') return 'LIGHT';
  }
  return DEFAULT_MAP_THEME;
}

/**
 * Returns the MapLibre style URL for the requested theme.
 * If theme is omitted or undefined, dynamically resolves via getInitialMapTheme()
 * so that ?theme=dark in URL works reliably across all map mounts.
 * Defaults strictly to the existing Light style (OpenFreeMap Liberty) when theme is LIGHT.
 */
export function getBasemapStyle(theme?: MapTheme): string {
  const resolvedTheme: MapTheme = (theme && BASEMAP_STYLES[theme]) ? theme : getInitialMapTheme();
  return BASEMAP_STYLES[resolvedTheme]?.url ?? BASEMAP_STYLES[DEFAULT_MAP_THEME].url;
}
