"""Flood-Safe Routing package."""
try:
    from backend.app.domain.routing.models import (
        RouteSafetyStatus,
        RouteSegment,
        ShortestPathComparison,
        SafeRouteResponse,
        SnappedPoint,
    )
    from backend.app.domain.routing.graph import RoadGraph, EdgeData
    from backend.app.domain.routing.router import calculate_flood_safe_route
except ImportError:
    from app.domain.routing.models import (
        RouteSafetyStatus,
        RouteSegment,
        ShortestPathComparison,
        SafeRouteResponse,
        SnappedPoint,
    )
    from app.domain.routing.graph import RoadGraph, EdgeData
    from app.domain.routing.router import calculate_flood_safe_route

__all__ = [
    "RouteSafetyStatus",
    "RouteSegment",
    "ShortestPathComparison",
    "SafeRouteResponse",
    "SnappedPoint",
    "RoadGraph",
    "EdgeData",
    "calculate_flood_safe_route",
]
