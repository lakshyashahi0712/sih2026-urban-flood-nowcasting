"""Urban Flood Nowcasting System - FastAPI Backend.

Rainfall nowcasting (0-3h) coupled with drainage network.
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import rainfall
from app.infrastructure.rainfall.open_meteo import OpenMeteoAdapter


# Module-level adapter instance
_adapter: OpenMeteoAdapter | None = None


def get_adapter() -> OpenMeteoAdapter:
    global _adapter
    if _adapter is None:
        _adapter = OpenMeteoAdapter()
    return _adapter


async def close_adapter() -> None:
    global _adapter
    if _adapter is not None:
        await _adapter.close()
        _adapter = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    # Adapter is initialized lazily
    yield
    # Shutdown
    await close_adapter()


app = FastAPI(
    title="Urban Flood Nowcasting System",
    description="Rainfall-drainage coupled nowcasting for Mumbai (0-3h lead time)",
    version="0.1.0-mvp",
    lifespan=lifespan,
)

# CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(rainfall.router)


@app.get("/")
def root():
    return {
        "app": "Urban Flood Nowcasting System",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)