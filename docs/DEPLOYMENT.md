# Deployment Guide

## Local development (recommended for operation)

```bash
python -m venv venv && venv\Scripts\activate     # Windows
pip install -r backend/requirements.txt
python main.py                                   # backend :8000

cd frontend && npm install && npm run dev        # frontend :5173
```

The Vite dev server proxies API calls to `http://localhost:8000`
(configurable via `VITE_API_TARGET`).

## Production build (single host)

```bash
cd frontend && npm run build          # emits frontend/dist
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --workers 1
```

Serve `frontend/dist` with any static server that proxies
`/api /flood /rainfall /routing /health /ready` to the backend —
`frontend/nginx.conf` is a ready-made configuration.

## Docker Compose

```bash
docker compose up --build
# frontend  http://localhost:8080  (nginx, reverse-proxies the API)
# backend   http://localhost:8000  (FastAPI, healthcheck on /ready)
```

- `data/` (the locally-acquired evidence tree) is bind-mounted read-only
  into the backend. It is intentionally **not** baked into the image.
- If `data/` is absent, the backend still starts; `/ready` reports the
  affected Delhi components `NOT_READY` by name, and Delhi endpoints
  degrade explicitly (never with fabricated data).

## Configuration

| Setting | Where | Default |
| --- | --- | --- |
| Backend port | `python main.py` / uvicorn | `8000` |
| API proxy target (dev) | `VITE_API_TARGET` env | `http://localhost:8000` |
| Extra CORS origins | `FLOOD_EXTRA_ORIGINS` env (comma-separated) | localhost:5173/4173 |
| Nowcast reference point | `backend/app/domain/delhi/nowcast.py` (`SAFDARJUNG_LAT/LON`) | documented Safdarjung station |
| Forecast cache TTL | `nowcast.CACHE_TTL_MINUTES` | 15 min |
| Frontend dev port | Vite | `5173` |
| Compose frontend port | `docker-compose.yml` | `8080` |

## Health & readiness

- `GET /health` — liveness (`{"status": "ok"}`).
- `GET /ready` — named component checks: `delhi_router_import`,
  `delhi_event_catalog`, `delhi_geo_layers`, `mumbai_dem`, `database`.
  Overall `READY` only when all pass. Use this for orchestrator
  probes; it never collapses failures into a single anonymous boolean.

## Operational notes

- The nowcast endpoint polls Open-Meteo per request with a 15-minute
  server-side cache; failed refreshes fall back to the cached fetch
  marked `STALE`. No feed access → explicit `UNAVAILABLE`/`BLOCKED`
  responses (HTTP 200 with honest states, so dashboards can render
  them).
- The replay endpoints execute the deterministic runtime (~seconds);
  responses are cached in-process. `?refresh=true` forces re-execution.
- CORS is restricted to localhost dev origins plus `FLOOD_EXTRA_ORIGINS`
  (the previous `*` + credentials combination was invalid per spec).
- Logs: uvicorn access logs plus structured domain diagnostics; no
  secrets are involved (the app requires no API keys).
