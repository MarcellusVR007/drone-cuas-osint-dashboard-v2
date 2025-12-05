"""
Site Boundary Model

Hard constraint enforcement: Operator hotspots MUST be outside site perimeters.
"""

from typing import List, Tuple, Optional
import math
import logging

logger = logging.getLogger(__name__)


class SiteBoundary:
    """
    Represents a protected site boundary.

    Can be either:
    - Circular (center point + radius)
    - Polygonal (list of lat/lon vertices)
    """

    def __init__(
        self,
        site_name: str,
        center_lat: float,
        center_lon: float,
        radius_m: Optional[float] = None,
        polygon_vertices: Optional[List[Tuple[float, float]]] = None,
        safety_buffer_m: float = 200.0,
    ):
        """
        Initialize site boundary.

        Args:
            site_name: Name of the site
            center_lat, center_lon: Center point of site
            radius_m: Radius for circular boundary (optional)
            polygon_vertices: List of (lat, lon) for polygon boundary (optional)
            safety_buffer_m: Additional buffer outside boundary (default: 200m)
        """
        self.site_name = site_name
        self.center_lat = center_lat
        self.center_lon = center_lon
        self.radius_m = radius_m
        self.polygon_vertices = polygon_vertices
        self.safety_buffer_m = safety_buffer_m

        # Validation
        if radius_m is None and polygon_vertices is None:
            raise ValueError("Must provide either radius_m or polygon_vertices")

        logger.info(f"Initialized SiteBoundary for {site_name} "
                   f"(center: {center_lat:.4f}, {center_lon:.4f}, "
                   f"buffer: {safety_buffer_m}m)")

    def is_inside_boundary(self, lat: float, lon: float) -> bool:
        """
        Check if a point is inside the site boundary (including safety buffer).

        Args:
            lat, lon: Point to check

        Returns:
            True if inside boundary + buffer, False otherwise
        """
        if self.radius_m is not None:
            # Circular boundary
            distance_m = self._haversine_distance(
                self.center_lat, self.center_lon, lat, lon
            ) * 1000

            # Inside if within radius + safety buffer
            return distance_m <= (self.radius_m + self.safety_buffer_m)

        elif self.polygon_vertices is not None:
            # Polygon boundary
            # First check if inside polygon
            if self._point_in_polygon(lat, lon, self.polygon_vertices):
                return True

            # Then check if within safety buffer of any polygon edge
            return self._distance_to_polygon(lat, lon, self.polygon_vertices) <= self.safety_buffer_m

        return False

    def _haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Haversine distance in kilometers"""
        R = 6371.0

        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)

        a = (math.sin(delta_lat / 2) ** 2 +
             math.cos(lat1_rad) * math.cos(lat2_rad) *
             math.sin(delta_lon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return R * c

    def _point_in_polygon(self, lat: float, lon: float, vertices: List[Tuple[float, float]]) -> bool:
        """
        Ray casting algorithm to check if point is inside polygon.

        Args:
            lat, lon: Point to check
            vertices: List of (lat, lon) polygon vertices

        Returns:
            True if inside polygon, False otherwise
        """
        n = len(vertices)
        inside = False

        p1_lat, p1_lon = vertices[0]
        for i in range(1, n + 1):
            p2_lat, p2_lon = vertices[i % n]

            if lon > min(p1_lon, p2_lon):
                if lon <= max(p1_lon, p2_lon):
                    if lat <= max(p1_lat, p2_lat):
                        if p1_lon != p2_lon:
                            x_intersect = (lon - p1_lon) * (p2_lat - p1_lat) / (p2_lon - p1_lon) + p1_lat
                        if p1_lat == p2_lat or lat <= x_intersect:
                            inside = not inside

            p1_lat, p1_lon = p2_lat, p2_lon

        return inside

    def _distance_to_polygon(self, lat: float, lon: float, vertices: List[Tuple[float, float]]) -> float:
        """
        Compute minimum distance from point to polygon edges.

        Args:
            lat, lon: Point to check
            vertices: List of (lat, lon) polygon vertices

        Returns:
            Minimum distance in meters
        """
        min_distance_km = float('inf')

        n = len(vertices)
        for i in range(n):
            v1 = vertices[i]
            v2 = vertices[(i + 1) % n]

            # Distance to edge segment
            distance_km = self._distance_to_segment(lat, lon, v1, v2)
            min_distance_km = min(min_distance_km, distance_km)

        return min_distance_km * 1000  # Convert to meters

    def _distance_to_segment(
        self,
        lat: float,
        lon: float,
        v1: Tuple[float, float],
        v2: Tuple[float, float]
    ) -> float:
        """
        Compute distance from point to line segment.

        Uses perpendicular projection if within segment bounds,
        otherwise distance to nearest endpoint.

        Returns:
            Distance in kilometers
        """
        v1_lat, v1_lon = v1
        v2_lat, v2_lon = v2

        # Vector from v1 to v2
        dx = v2_lon - v1_lon
        dy = v2_lat - v1_lat

        if dx == 0 and dy == 0:
            # v1 and v2 are the same point
            return self._haversine_distance(lat, lon, v1_lat, v1_lon)

        # Parameter t for projection onto line
        t = ((lon - v1_lon) * dx + (lat - v1_lat) * dy) / (dx * dx + dy * dy)

        if t < 0:
            # Closest to v1
            return self._haversine_distance(lat, lon, v1_lat, v1_lon)
        elif t > 1:
            # Closest to v2
            return self._haversine_distance(lat, lon, v2_lat, v2_lon)
        else:
            # Project onto segment
            proj_lat = v1_lat + t * dy
            proj_lon = v1_lon + t * dx
            return self._haversine_distance(lat, lon, proj_lat, proj_lon)


# Known site boundaries (can be extended)
KNOWN_SITES = {
    "Volkel Air Base": SiteBoundary(
        site_name="Volkel Air Base",
        center_lat=51.6564,
        center_lon=5.7083,
        radius_m=1500,  # Approximate radius of military airbase
        safety_buffer_m=200,
    ),
    "Eindhoven Airport": SiteBoundary(
        site_name="Eindhoven Airport",
        center_lat=51.4500,
        center_lon=5.3747,
        radius_m=1200,
        safety_buffer_m=200,
    ),
    "Schiphol Airport": SiteBoundary(
        site_name="Schiphol Airport",
        center_lat=52.3105,
        center_lon=4.7683,
        radius_m=2500,
        safety_buffer_m=200,
    ),
}


def get_site_boundary(site_name: str) -> Optional[SiteBoundary]:
    """
    Get site boundary by name.

    Args:
        site_name: Name of the site

    Returns:
        SiteBoundary object or None if not found
    """
    return KNOWN_SITES.get(site_name)


def get_site_boundary_by_location(lat: float, lon: float, radius_km: float = 5.0) -> Optional[SiteBoundary]:
    """
    Find a known site near the given location.

    Args:
        lat, lon: Location to check
        radius_km: Search radius in kilometers

    Returns:
        Nearest SiteBoundary within radius, or None
    """
    nearest_site = None
    min_distance = float('inf')

    for site in KNOWN_SITES.values():
        distance_km = site._haversine_distance(site.center_lat, site.center_lon, lat, lon)

        if distance_km <= radius_km and distance_km < min_distance:
            min_distance = distance_km
            nearest_site = site

    if nearest_site:
        logger.info(f"Found site '{nearest_site.site_name}' at {min_distance:.2f}km from target")

    return nearest_site
