"""AquaSense — real-time water quality monitoring & anomaly detection.

FastAPI backend that:
  * ingests readings from IoT sensors (REST + WebSocket),
  * flags anomalies with a hybrid threshold + Isolation Forest model,
  * streams live data to the React dashboard over WebSockets.

Run with:  uvicorn main:app --reload --host 0.0.0.0 --port 8000
"""
import os
import sys
from datetime import datetime
from pathlib import Path

# Ensure both repository root and backend directory are on sys.path
_backend_dir = Path(__file__).resolve().parent
_repo_root = _backend_dir.parent
for _p in [str(_backend_dir), str(_repo_root)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

# Single-container mode (Hugging Face Spaces): serve the built frontend from
# this app when frontend/dist exists. API routes always take precedence; the
# SPA only receives paths no API route claimed.
_FRONTEND_DIST = _repo_root / "frontend" / "dist"
_SERVE_FRONTEND = (_FRONTEND_DIST / "index.html").exists()

from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

try:
    from backend.database import init_db
    from backend.routers import sensors, alerts, devices, dashboard, flood, routing, delhi, scenarios
except ImportError:
    from database import init_db
    from routers import sensors, alerts, devices, dashboard, flood, routing, delhi, scenarios
try:
    from backend.app.api import rainfall
except ImportError:
    from app.api import rainfall
try:
    from backend.websocket_manager import manager
except ImportError:
    from websocket_manager import manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Urban Flood Nowcasting API",
    description=(
        "Urban flood nowcasting backend. Mumbai V1 (Kurla pilot) legacy "
        "surface plus the Delhi/Kushak V2 evidence-constrained digital "
        "twin (events, historical replay, ensemble nowcast, provenance)."
    ),
    version="2.0.0",
    lifespan=lifespan,
)

# Allow the Vite dev server to call the API. `allow_origins=["*"]` with
# `allow_credentials=True` is invalid per the CORS spec (browsers reject
# the combination), so the local dev origins are listed explicitly and
# additional origins can be supplied via the FLOOD_EXTRA_ORIGINS env var.
_EXTRA_ORIGINS = [
    o.strip()
    for o in os.environ.get("FLOOD_EXTRA_ORIGINS", "").split(",")
    if o.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:4173",
        "http://127.0.0.1:4173",
        *_EXTRA_ORIGINS,
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(sensors.router)
app.include_router(alerts.router)
app.include_router(devices.router)
app.include_router(dashboard.router)
app.include_router(flood.router)
app.include_router(rainfall.router)
app.include_router(routing.router)
app.include_router(delhi.router)
app.include_router(scenarios.router)


@app.get("/")
def root():
    if _SERVE_FRONTEND:
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/index.html")
    return {
        "app": "Urban Flood Nowcasting API",
        "docs": "/docs",
        "health": "/health",
        "ready": "/ready",
        "delhi_v2": "/api/delhi/status",
    }


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/ready")
def ready():
    """Readiness probe: imports, dataset presence, and database state.

    Reports component-level readiness without collapsing problems into a
    single boolean: each check is named so operators can see WHAT is not
    ready, not just THAT something is not ready.
    """
    checks: dict = {}
    ok = True

    try:
        from backend.routers import delhi as _delhi  # noqa: F401
        checks["delhi_router_import"] = "READY"
    except Exception as exc:
        checks["delhi_router_import"] = f"NOT_READY: {exc}"
        ok = False

    try:
        catalog = _repo_root() / "data" / "delhi" / "derived" / "validation" / "kushak_historical_events.csv"
        checks["delhi_event_catalog"] = "READY" if catalog.exists() else f"MISSING: {catalog.name}"
        ok = ok and catalog.exists()
    except Exception as exc:
        checks["delhi_event_catalog"] = f"NOT_READY: {exc}"
        ok = False

    try:
        centerline = _repo_root() / "data" / "delhi" / "derived" / "hydraulic" / "kushak_corridor_centerline.geojson"
        checks["delhi_geo_layers"] = "READY" if centerline.exists() else f"MISSING: {centerline.name}"
        ok = ok and centerline.exists()
    except Exception as exc:
        checks["delhi_geo_layers"] = f"NOT_READY: {exc}"
        ok = False

    try:
        dem = _repo_root() / "backend" / "app" / "data" / "dem" / "mumbai_pilot_dem_30m.tif"
        checks["mumbai_dem"] = "READY" if dem.exists() else f"MISSING: {dem.name}"
        ok = ok and dem.exists()
    except Exception as exc:
        checks["mumbai_dem"] = f"NOT_READY: {exc}"
        ok = False

    try:
        init_db()
        checks["database"] = "READY"
    except Exception as exc:
        checks["database"] = f"NOT_READY: {exc}"
        ok = False

    return {
        "status": "READY" if ok else "NOT_READY",
        "checks": checks,
        "checked_at": datetime.utcnow().isoformat() + "Z",
    }


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Live stream of readings and alerts to connected dashboard clients."""
    await manager.connect(websocket)
    try:
        # We only push server->client; keep the socket open and ignore pings.
        await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)


# ---------------------------------------------------------------------------
# Optional single-container mode: serve the built frontend from this app.
# Used by deployments that run ONE container (e.g. Hugging Face Spaces).
# Local dev keeps using the Vite dev server + this API on :8000.
# Registered LAST so every API route above matches before the static mount.
# ---------------------------------------------------------------------------
if _SERVE_FRONTEND:
    from fastapi.staticfiles import StaticFiles

    app.mount("/", StaticFiles(directory=str(_FRONTEND_DIST), html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn
    app_target = "main:app" if Path.cwd().name == "backend" else "backend.main:app"
    uvicorn.run(app_target, host="0.0.0.0", port=8000, reload=True)
