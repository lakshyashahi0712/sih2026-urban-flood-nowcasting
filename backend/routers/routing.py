"""REST API endpoint for Flood-Safe Routing."""
from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, HTTPException, Query

try:
    from backend.app.domain.routing.models import SafeRouteResponse
    from backend.app.domain.routing.router import calculate_flood_safe_route
    from backend.routers.flood import get_street_flood_intelligence
except ImportError:
    from app.domain.routing.models import SafeRouteResponse
    from app.domain.routing.router import calculate_flood_safe_route
    from routers.flood import get_street_flood_intelligence

router = APIRouter(prefix="/routing", tags=["routing"])


@router.get("/safe-route", response_model=SafeRouteResponse)
async def get_flood_safe_route(
    start_lon: float = Query(..., description="Origin longitude in WGS84 (EPSG:4326)"),
    start_lat: float = Query(..., description="Origin latitude in WGS84 (EPSG:4326)"),
    end_lon: float = Query(..., description="Destination longitude in WGS84 (EPSG:4326)"),
    end_lat: float = Query(..., description="Destination latitude in WGS84 (EPSG:4326)"),
    horizon: str = Query("+1h", description="Forecast horizon: NOW, +1h, +2h, +3h"),
    rainfall_scenario_mm: Optional[float] = Query(None, ge=0, description="Optional override/scenario rainfall depth [mm]"),
):
    """
    Calculate an optimal flood-safe route between two coordinates in the Mumbai pilot area.
    
    Excludes impassable road segments (RiskLevel >= HIGH, depth >= 0.30m) and penalizes
    passable ponded roads (MEDIUM, LOW) using an operational depth-weighted cost function.
    """
    # 1. Fetch street flood intelligence for the requested horizon or scenario
    try:
        street_intel = await get_street_flood_intelligence(
            horizon=horizon,
            rainfall_mm=rainfall_scenario_mm,
            use_cache=True,
        )
        affected_roads = street_intel.affected_roads
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Street flood hazard assessment unavailable: {str(e)}"
        )

    # 2. Run flood-safe routing engine
    try:
        route_result = calculate_flood_safe_route(
            start_lon=start_lon,
            start_lat=start_lat,
            end_lon=end_lon,
            end_lat=end_lat,
            horizon=horizon,
            affected_roads=affected_roads,
        )
        return route_result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Routing calculation failed: {str(e)}")
