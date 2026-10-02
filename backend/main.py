"""AquaSense — real-time water quality monitoring & anomaly detection.

FastAPI backend that:
  * ingests readings from IoT sensors (REST + WebSocket),
  * flags anomalies with a hybrid threshold + Isolation Forest model,
  * streams live data to the React dashboard over WebSockets.

Run with:  uvicorn main:app --reload --host 0.0.0.0 --port 8000
"""
import os
import sys
import logging
import threading
import time
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
try:
    from backend.app.observability.memory_instrumentation import (
        RequestMemoryLogMiddleware,
    )
except ImportError:
    from app.observability.memory_instrumentation import RequestMemoryLogMiddleware


import logging
import threading
import time


def _warm_on_boot(env_var: str) -> bool:
    """Should this surface's caches be computed at startup?

    Evaluated when the app starts, NOT at import. pytest only sets
    ``PYTEST_CURRENT_TEST`` per test phase, so an import-time check answered
    "not testing" for the whole collection pass and any test that entered
    ``with TestClient(app)`` launched a real warm thread — which then called
    whatever pipeline that test had monkeypatched and appended phantom model
    runs into it. Production uvicorn imports no pytest and sets no such
    variable, so it still warms.
    """
    if "PYTEST_CURRENT_TEST" in os.environ or "pytest" in sys.modules:
        return False
    return os.environ.get(env_var, "1") != "0"


def _warm_mumbai_flood_caches() -> None:
    """Compute V1's two boot states once at startup so the first visitor is a cache hit."""
    import asyncio

    try:
        from backend.routers import flood as flood_router
    except ImportError:
        from routers import flood as flood_router

    async def _run():
        await flood_router.compute_flood_forecast_evolution(use_cache=True)
        await flood_router.get_streets_forecast(use_cache=True)

    try:
        started_at = time.monotonic()
        asyncio.run(_run())
        logging.getLogger("uvicorn.error").info(
            "Mumbai flood caches warmed in %.1fs", time.monotonic() - started_at
        )
    except Exception:
        logging.getLogger("uvicorn.error").warning(
            "Mumbai flood cache warm-up failed", exc_info=True
        )


def _warm_delhi_flood_caches() -> None:
    """Compute V2's boot live-state once at startup so the first Delhi visitor is a cache hit."""
    try:
        from backend.app.domain.delhi import live_state as delhi_live_state
    except ImportError:
        from app.domain.delhi import live_state as delhi_live_state

    try:
        started_at = time.monotonic()
        delhi_live_state.get_cached_live_states(use_cache=True)
        logging.getLogger("uvicorn.error").info(
            "Delhi flood caches warmed in %.1fs", time.monotonic() - started_at
        )
    except Exception:
        logging.getLogger("uvicorn.error").warning(
            "Delhi flood cache warm-up failed", exc_info=True
        )


_WARM_SWITCH_BY_SURFACE = {
    "mumbai": "FLOOD_WARM_ON_BOOT",
    "delhi": "DELHI_WARM_ON_BOOT",
}


def _warm_order() -> list:
    """Which surface builds first at boot — only one can have the CPU.

    Sequential because two parallel builds measured as an OOM on the 512 MB
    tier, and because the order is the whole question: the surface that warms
    second is the one whose first visitor queues behind the other's build. On
    Render's 0.1 CPU a cold ?delhi boot measured 99 s to the first live-state,
    ~51 s of which was Mumbai's build finishing before Delhi's started.

    V1 is the default launch surface, so mumbai-first stays the default;
    ``FLOOD_WARM_ORDER=delhi`` is what a Delhi capture wants set instead.
    """
    if os.environ.get("FLOOD_WARM_ORDER", "").strip().lower() == "delhi":
        return ["delhi", "mumbai"]
    return ["mumbai", "delhi"]


def _warm_flood_caches_at_boot() -> None:
    """Warm both city surfaces at startup, one at a time, in `_warm_order()`."""
    for surface in _warm_order():
        if not _warm_on_boot(_WARM_SWITCH_BY_SURFACE[surface]):
            continue
        if surface == "mumbai":
            _warm_mumbai_flood_caches()
        else:
            _warm_delhi_flood_caches()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    if _warm_on_boot("FLOOD_WARM_ON_BOOT") or _warm_on_boot("DELHI_WARM_ON_BOOT"):
        # One daemon thread, not a coroutine and not two threads: the model
        # runs are synchronous CPU work, so blocking the event loop would stall
        # /health and get the instance marked unresponsive, while two parallel
        # builds is exactly the cold stampede that blew the memory budget.
        threading.Thread(
            target=_warm_flood_caches_at_boot,
            name="flood-cache-warm",
            daemon=True,
        ).start()
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
        # Vercel production deployment
        "https://sih2026-urban-flood-nowcasting.vercel.app",
        *_EXTRA_ORIGINS,
    ],
    allow_origin_regex=r"^https:\/\/([a-zA-Z0-9_-]+\.)?vercel\.app$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Diagnostics only: logs VmRSS before/after the expensive route families
# (/api/delhi, /flood, /routing, /rainfall). Pure-ASGI pass-through, so it does
# not read, buffer or alter the response body. See
# backend/app/observability/memory_instrumentation.py
app.add_middleware(RequestMemoryLogMiddleware)

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
