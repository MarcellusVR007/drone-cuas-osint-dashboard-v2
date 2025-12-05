"""
OpenStreetMap Landuse Data Loader

Loads and caches OSM landuse data for terrain analysis.
Uses Overpass API for real data, with fallback to synthetic data.
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import math
import logging

logger = logging.getLogger(__name__)


@dataclass
class LanduseFeature:
    """OSM landuse feature"""
    landuse_type: str  # forest, residential, industrial, farmland, etc.
    geometry: List[Tuple[float, float]]  # polygon coordinates
    tags: Dict[str, str]
    center_lat: float
    center_lon: float


@dataclass
class OSMData:
    """Cached OSM data for a region"""
    center_lat: float
    center_lon: float
    radius_km: float
    landuse_features: List[LanduseFeature]
    roads: List[Dict]
    buildings: List[Dict]


# Simple in-memory cache
_osm_cache: Dict[Tuple[float, float, float], OSMData] = {}


def load_osm_landuse(lat: float, lon: float, radius_km: float) -> OSMData:
    """
    Load OSM landuse data for a region.

    Args:
        lat: Center latitude
        lon: Center longitude
        radius_km: Radius in kilometers

    Returns:
        OSMData with landuse features, roads, buildings
    """
    cache_key = (round(lat, 4), round(lon, 4), radius_km)

    if cache_key in _osm_cache:
        logger.debug(f"OSM cache hit for {cache_key}")
        return _osm_cache[cache_key]

    logger.info(f"Loading OSM data for ({lat}, {lon}) radius {radius_km}km")

    # TODO Sprint 4.1: Add real Overpass API integration
    # For now, use synthetic data based on distance patterns
    osm_data = _generate_synthetic_osm_data(lat, lon, radius_km)

    _osm_cache[cache_key] = osm_data
    return osm_data


def _generate_synthetic_osm_data(lat: float, lon: float, radius_km: float) -> OSMData:
    """
    Generate synthetic OSM-like data for testing.
    Real Overpass API integration coming in Sprint 4.1.
    """
    landuse_features = []

    # Create ring pattern: urban center, suburban, rural
    for angle in range(0, 360, 30):
        rad = math.radians(angle)

        # Inner ring (0-1km): Urban/residential
        dist_km = 0.5
        feat_lat = lat + (dist_km / 111.0) * math.cos(rad)
        feat_lon = lon + (dist_km / (111.0 * math.cos(math.radians(lat)))) * math.sin(rad)
        landuse_features.append(LanduseFeature(
            landuse_type="residential",
            geometry=_create_square_poly(feat_lat, feat_lon, 0.1),
            tags={"landuse": "residential", "name": f"Urban sector {angle}"},
            center_lat=feat_lat,
            center_lon=feat_lon
        ))

        # Middle ring (1-3km): Mixed (forest, farmland, industrial)
        for dist_km in [1.5, 2.5]:
            feat_lat = lat + (dist_km / 111.0) * math.cos(rad)
            feat_lon = lon + (dist_km / (111.0 * math.cos(math.radians(lat)))) * math.sin(rad)

            # Alternate forest and farmland
            if angle % 60 < 30:
                landuse_type = "forest"
            else:
                landuse_type = "farmland"

            landuse_features.append(LanduseFeature(
                landuse_type=landuse_type,
                geometry=_create_square_poly(feat_lat, feat_lon, 0.2),
                tags={"landuse": landuse_type},
                center_lat=feat_lat,
                center_lon=feat_lon
            ))

    # Create synthetic roads
    roads = [
        {"type": "primary", "distance_m": 50},
        {"type": "secondary", "distance_m": 150},
        {"type": "tertiary", "distance_m": 300},
    ]

    # Create synthetic buildings
    buildings = [
        {"type": "residential", "count": 20},
        {"type": "commercial", "count": 5},
    ]

    return OSMData(
        center_lat=lat,
        center_lon=lon,
        radius_km=radius_km,
        landuse_features=landuse_features,
        roads=roads,
        buildings=buildings
    )


def _create_square_poly(lat: float, lon: float, size_km: float) -> List[Tuple[float, float]]:
    """Create a square polygon around a center point"""
    offset = size_km / 111.0 / 2
    return [
        (lat - offset, lon - offset),
        (lat + offset, lon - offset),
        (lat + offset, lon + offset),
        (lat - offset, lon + offset),
        (lat - offset, lon - offset),
    ]


def get_landuse_at_point(lat: float, lon: float, osm_data: OSMData) -> Optional[str]:
    """
    Get landuse type at a specific point.

    Args:
        lat: Latitude
        lon: Longitude
        osm_data: Loaded OSM data

    Returns:
        Landuse type string or None
    """
    # Find closest landuse feature
    min_dist = float('inf')
    closest_type = None

    for feature in osm_data.landuse_features:
        dist = _haversine_distance(lat, lon, feature.center_lat, feature.center_lon)
        if dist < min_dist:
            min_dist = dist
            closest_type = feature.landuse_type

    # If within 500m of a feature, return it
    if min_dist < 0.5:  # km
        return closest_type

    return "unknown"


def _haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate haversine distance in kilometers"""
    R = 6371.0  # Earth radius in km

    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)

    a = (math.sin(delta_lat / 2) ** 2 +
         math.cos(lat1_rad) * math.cos(lat2_rad) *
         math.sin(delta_lon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c
