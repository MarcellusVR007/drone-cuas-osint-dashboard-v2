"""
Cover and Concealment Analyzer

Computes cover and concealment scores based on terrain features.
Cover = physical protection from observation
Concealment = ability to hide/blend in
"""

from typing import Dict, Tuple
from .osm_loader import OSMData, get_landuse_at_point
from .elevation_loader import get_elevation_at_point
import logging

logger = logging.getLogger(__name__)


# Cover scores by landuse type (0.0-1.0)
LANDUSE_COVER_SCORES = {
    "forest": 0.95,              # Excellent cover - dense trees
    "wood": 0.95,
    "scrub": 0.75,               # Good cover - bushes
    "residential": 0.70,         # Urban cover - buildings, cars
    "industrial": 0.65,          # Industrial cover - structures
    "commercial": 0.65,
    "farmland": 0.30,            # Poor cover - open fields
    "grass": 0.20,
    "meadow": 0.20,
    "park": 0.25,
    "bare": 0.10,                # Very poor cover
    "water": 0.05,
    "unknown": 0.40,             # Default moderate
}

# Concealment multipliers by landuse
LANDUSE_CONCEALMENT_MULT = {
    "forest": 1.0,               # Best concealment
    "residential": 0.9,          # Good - blend with civilians
    "industrial": 0.7,           # Moderate - fewer people
    "farmland": 0.5,             # Poor - conspicuous
    "grass": 0.3,                # Very poor - exposed
    "water": 0.1,                # Terrible - highly visible
    "unknown": 0.6,
}


def compute_cover_score(lat: float, lon: float,
                       osm_data: OSMData,
                       elevation_map: Dict[Tuple[float, float], float]) -> float:
    """
    Compute cover score for a location.

    Cover = physical protection from observation (trees, buildings, terrain)

    Args:
        lat: Latitude
        lon: Longitude
        osm_data: OSM landuse data
        elevation_map: Elevation data

    Returns:
        Cover score 0.0-1.0 (higher = better cover)
    """
    # Get landuse-based cover
    landuse = get_landuse_at_point(lat, lon, osm_data)
    base_cover = LANDUSE_COVER_SCORES.get(landuse, 0.40)

    # Elevation bonus: higher ground = better vantage but maybe less cover
    # Lower ground (valleys) = better concealment
    elevation = get_elevation_at_point(lat, lon, elevation_map)
    center_elevation = get_elevation_at_point(osm_data.center_lat, osm_data.center_lon, elevation_map)
    elev_diff = elevation - center_elevation

    # Slight bonus for being in a depression (harder to spot)
    if elev_diff < -10:
        elevation_bonus = 0.10
    elif elev_diff < 0:
        elevation_bonus = 0.05
    else:
        elevation_bonus = 0.0

    # Building proximity bonus (from OSM buildings)
    building_bonus = 0.05 if osm_data.buildings else 0.0

    total_cover = min(1.0, base_cover + elevation_bonus + building_bonus)

    logger.debug(f"Cover at ({lat:.4f}, {lon:.4f}): {total_cover:.2f} "
                f"(landuse={landuse}, elev_bonus={elevation_bonus:.2f})")

    return total_cover


def compute_concealment_score(lat: float, lon: float,
                              osm_data: OSMData,
                              elevation_map: Dict[Tuple[float, float], float],
                              time_of_day: str = "day") -> float:
    """
    Compute concealment score for a location.

    Concealment = ability to blend in and avoid detection

    Args:
        lat: Latitude
        lon: Longitude
        osm_data: OSM landuse data
        elevation_map: Elevation data
        time_of_day: "day" or "night"

    Returns:
        Concealment score 0.0-1.0 (higher = better concealment)
    """
    # Get landuse-based concealment
    landuse = get_landuse_at_point(lat, lon, osm_data)
    base_concealment = LANDUSE_COVER_SCORES.get(landuse, 0.40) * \
                      LANDUSE_CONCEALMENT_MULT.get(landuse, 0.6)

    # Night operations: significant concealment boost
    if time_of_day == "night":
        night_bonus = 0.20
    else:
        night_bonus = 0.0

    # Terrain roughness: varied elevation = better concealment
    elevation = get_elevation_at_point(lat, lon, elevation_map)
    center_elevation = get_elevation_at_point(osm_data.center_lat, osm_data.center_lon, elevation_map)
    elev_variance = abs(elevation - center_elevation)

    # Moderate elevation variance is good for concealment
    if 5 < elev_variance < 30:
        terrain_bonus = 0.10
    else:
        terrain_bonus = 0.0

    total_concealment = min(1.0, base_concealment + night_bonus + terrain_bonus)

    logger.debug(f"Concealment at ({lat:.4f}, {lon:.4f}): {total_concealment:.2f} "
                f"(base={base_concealment:.2f}, night={night_bonus}, terrain={terrain_bonus:.2f})")

    return total_concealment


def compute_combined_cover_concealment(lat: float, lon: float,
                                       osm_data: OSMData,
                                       elevation_map: Dict[Tuple[float, float], float],
                                       time_of_day: str = "day") -> Dict[str, float]:
    """
    Compute both cover and concealment scores.

    Returns:
        Dict with 'cover', 'concealment', and 'combined' scores
    """
    cover = compute_cover_score(lat, lon, osm_data, elevation_map)
    concealment = compute_concealment_score(lat, lon, osm_data, elevation_map, time_of_day)

    # Combined score: weighted average (cover slightly more important)
    combined = 0.6 * cover + 0.4 * concealment

    return {
        "cover": cover,
        "concealment": concealment,
        "combined": combined,
        "landuse": get_landuse_at_point(lat, lon, osm_data),
    }
