"""Geospatial mapping adapters."""
from abc import ABC, abstractmethod
from typing import List, Optional


class GeoMapper(ABC):
    """Abstract interface for geospatial operations."""

    @abstractmethod
    def point_in_circle(
        self,
        lat: Optional[float],
        lon: Optional[float],
        center_lat: float,
        center_lon: float,
        radius_deg: float,
    ) -> bool:
        """Return True if the point lies within the circle."""

    @abstractmethod
    def haversine_km(
        self,
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float,
    ) -> float:
        """Return the great-circle distance between two points in kilometres."""


class NoOpGeoMapper(GeoMapper):
    """No-op fallback used when USE_GEOSPATIAL=false."""

    def point_in_circle(
        self,
        lat: Optional[float],
        lon: Optional[float],
        center_lat: float,
        center_lon: float,
        radius_deg: float,
    ) -> bool:
        return False

    def haversine_km(
        self,
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float,
    ) -> float:
        return 0.0


class ShapelyGeoMapper(GeoMapper):
    """Shapely-backed geospatial mapper.

    Requires the optional `shapely` dependency.
    """

    def __init__(self) -> None:
        try:
            from shapely.geometry import Point
        except ImportError as exc:
            raise ImportError(
                "ShapelyGeoMapper requires shapely to be installed "
                "(pip install rag-risk-propagation[geo])."
            ) from exc
        self._Point = Point

    def point_in_circle(
        self,
        lat: Optional[float],
        lon: Optional[float],
        center_lat: float,
        center_lon: float,
        radius_deg: float,
    ) -> bool:
        if lat is None or lon is None:
            return False
        # Approximate degree-to-km conversion near the equator.
        distance_km = self.haversine_km(lat, lon, center_lat, center_lon)
        radius_km = radius_deg * 111.0
        return distance_km <= radius_km

    def haversine_km(
        self,
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float,
    ) -> float:
        import math

        R = 6371.0
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)
        a = (
            math.sin(dphi / 2) ** 2
            + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c
