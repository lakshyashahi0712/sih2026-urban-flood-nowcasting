/**
 * Central API configuration for Vercel + Render deployments.
 * Reads VITE_API_BASE_URL (defaults to '' in development to use Vite dev proxy).
 */
export const API_BASE_URL: string = (
  (import.meta.env.VITE_API_BASE_URL as string | undefined) || ''
).replace(/\/+$/, '');

export function apiUrl(path: string): string {
  const normalizedPath = path.startsWith('/') ? path : `/${path}`;
  return `${API_BASE_URL}${normalizedPath}`;
}

/**
 * Fire the cheapest possible request so a sleeping backend starts booting while
 * the JS bundle and basemap are still downloading. Errors are ignored: this is
 * a wake-up nudge, not data.
 */
export function wakeBackend(): void {
  fetch(apiUrl('/health')).catch(() => {});
}
