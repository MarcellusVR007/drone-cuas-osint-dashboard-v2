"""
Elevation Data Loader

Loads and caches elevation data for terrain analysis.
Uses synthetic data for now, real DEM integration coming later.
"""

from typing import Dict, Tuple
import math
import logging

logger = logging.getLogger(__name__)

# Simple in-memory cache
_elevation_cache: Dict[Tuple[float, float], float] = {}


def load_elevation(lat: float, lon: float, radius_km: float) -> Dict[Tuple[float, float], float]:
    """
    Load elevation data for a region.

    Args:
        lat: Center latitude
        lon: Center longitude
        radius_km: Radius in kilometers

    Returns:
        Dict mapping (lat, lon) to elevation in meters
    """
    logger.info(f"Loading elevation data for ({lat}, {lon}) radius {radius_km}km")

    # TODO Sprint 4.1: Add real DEM (Digital Elevation Model) integration
    # For now, use synthetic elevation based on distance and angle
    elevation_map = {}

    # Sample points in a grid
    samples_per_km = 4
    num_samples = int(radius_km * 2 * samples_per_km)

    for i in range(num_samples):
        for j in range(num_samples):
            sample_lat = lat - radius_km / 111.0 + (i * 2 * radius_km / 111.0 / num_samples)
            sample_lon = lon - radius_km / (111.0 * math.cos(math.radians(lat))) + \
                        (j * 2 * radius_km / (111.0 * math.cos(math.radians(lat))) / num_samples)

            elevation = _generate_synthetic_elevation(lat, lon, sample_lat, sample_lon)
            elevation_map[(round(sample_lat, 5), round(sample_lon, 5))] = elevation

    return elevation_map


def get_elevation_at_point(lat: float, lon: float, elevation_map: Dict[Tuple[float, float], float]) -> float:
    """
    Get elevation at a specific point.

    Args:
        lat: Latitude
        lon: Longitude
        elevation_map: Loaded elevation data

    Returns:
        Elevation in meters
    """
    # Round to cache precision
    rounded_key = (round(lat, 5), round(lon, 5))

    if rounded_key in elevation_map:
        return elevation_map[rounded_key]

    # Find nearest point in map
    if not elevation_map:
        return _generate_synthetic_elevation(lat, lon, lat, lon)

    nearest_key = min(elevation_map.keys(),
                     key=lambda k: _distance(lat, lon, k[0], k[1]))
    return elevation_map[nearest_key]


def _generate_synthetic_elevation(center_lat: float, center_lon: float,
                                  point_lat: float, point_lon: float) -> float:
    """
    Generate synthetic elevation for testing.
    Creates a varied terrain with hills and valleys.
    """
    # Base elevation around 50m
    base = 50.0

    # Distance from center
    dist = _distance(center_lat, center_lon, point_lat, point_lon)

    # Create rolling hills pattern
    angle = math.atan2(point_lat - center_lat, point_lon - center_lon)

    # Add sinusoidal variation based on angle and distance
    variation = 20.0 * math.sin(dist * 3 + angle * 2) + 15.0 * math.cos(angle * 3)

    return base + variation


def _distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate euclidean distance (good enough for small areas)"""
    return math.sqrt((lat2 - lat1)**2 + (lon2 - lon1)**2)


def compute_elevation_difference(lat1: float, lon1: float,
                                lat2: float, lon2: float,
                                elevation_map: Dict[Tuple[float, float], float]) -> float:
    """
    Compute elevation difference between two points.

    Args:
        lat1, lon1: First point
        lat2, lon2: Second point
        elevation_map: Loaded elevation data

    Returns:
        Elevation difference in meters (positive = uphill from point1 to point2)
    """
    elev1 = get_elevation_at_point(lat1, lon1, elevation_map)
    elev2 = get_elevation_at_point(lat2, lon2, elevation_map)
    return elev2 - elev1
