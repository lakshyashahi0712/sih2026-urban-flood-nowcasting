"""AquaSense — real-time water quality monitoring & anomaly detection.

FastAPI backend that:
  * ingests readings from IoT sensors (REST + WebSocket),
  * flags anomalies with a hybrid threshold + Isolation Forest model,
  * streams live data to the React dashboard over WebSockets.

Run with:  uvicorn main:app --reload --host 0.0.0.0 --port 8000
"""
import os
import sys
from pathlib import Path

# Ensure both repository root and backend directory are on sys.path
_backend_dir = Path(__file__).resolve().parent
_repo_root = _backend_dir.parent
for _p in [str(_backend_dir), str(_repo_root)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from backend.database import init_db
from backend.routers import sensors, alerts, devices, dashboard, flood
try:
    from backend.websocket_manager import manager
except ImportError:
    from websocket_manager import manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="AquaSense Water Monitoring API",
    description="Real-time water quality monitoring with ML-based anomaly detection.",
    version="1.0.0",
    lifespan=lifespan,
)

# Allow the Vite dev server (and any other origin) to call the API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(sensors.router)
app.include_router(alerts.router)
app.include_router(devices.router)
app.include_router(dashboard.router)
app.include_router(flood.router)


@app.get("/")
def root():
    return {
        "app": "AquaSense Water Monitoring API",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
def health():
    return {"status": "ok"}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Live stream of readings and alerts to connected dashboard clients."""
    await manager.connect(websocket)
    try:
        while True:
            # We only push server->client; keep the socket open and ignore pings.
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
