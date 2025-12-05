"""
Exfiltration Route Analyzer

Analyzes escape routes and exfiltration attractiveness for operator locations.
"""

from typing import List, Dict, Tuple
from .osm_loader import OSMData
import math
import logging

logger = logging.getLogger(__name__)


# Road quality scores for exfiltration
ROAD_QUALITY_SCORES = {
    "motorway": 1.0,
    "trunk": 0.95,
    "primary": 0.90,
    "secondary": 0.85,
    "tertiary": 0.75,
    "residential": 0.70,
    "unclassified": 0.60,
    "track": 0.40,
    "path": 0.20,
    "footway": 0.10,
}


def compute_exfil_routes(lat: float, lon: float, osm_data: OSMData) -> List[Dict]:
    """
    Compute exfiltration routes from a location.

    Args:
        lat: Latitude
        lon: Longitude
        osm_data: OSM data including roads

    Returns:
        List of exfil routes with quality scores
    """
    routes = []

    # Analyze available roads
    for road in osm_data.roads:
        road_type = road.get("type", "unclassified")
        distance_m = road.get("distance_m", 200)

        quality = ROAD_QUALITY_SCORES.get(road_type, 0.50)

        # Distance penalty: closer roads are better (up to a point)
        if distance_m < 50:
            distance_factor = 1.0
        elif distance_m < 100:
            distance_factor = 0.9
        elif distance_m < 200:
            distance_factor = 0.8
        elif distance_m < 500:
            distance_factor = 0.6
        else:
            distance_factor = 0.4

        routes.append({
            "type": road_type,
            "distance_m": distance_m,
            "quality": quality,
            "distance_factor": distance_factor,
            "score": quality * distance_factor,
        })

    # Sort by score
    routes.sort(key=lambda r: r["score"], reverse=True)

    logger.debug(f"Found {len(routes)} exfil routes at ({lat:.4f}, {lon:.4f})")

    return routes


def score_exfil_attractiveness(lat: float, lon: float, osm_data: OSMData) -> float:
    """
    Compute overall exfiltration attractiveness score.

    Args:
        lat: Latitude
        lon: Longitude
        osm_data: OSM data

    Returns:
        Exfil score 0.0-1.0 (higher = better escape routes)
    """
    routes = compute_exfil_routes(lat, lon, osm_data)

    if not routes:
        return 0.2  # Minimum score - always some escape possibility

    # Best route score
    best_route_score = routes[0]["score"]

    # Multiple routes bonus
    if len(routes) >= 3:
        multiple_routes_bonus = 0.15
    elif len(routes) >= 2:
        multiple_routes_bonus = 0.10
    else:
        multiple_routes_bonus = 0.0

    # Calculate diversity: different road types = better
    road_types = set(r["type"] for r in routes[:3])
    diversity_bonus = len(road_types) * 0.05

    total_score = min(1.0, best_route_score + multiple_routes_bonus + diversity_bonus)

    logger.debug(f"Exfil score at ({lat:.4f}, {lon:.4f}): {total_score:.2f} "
                f"(best={best_route_score:.2f}, routes={len(routes)}, diversity={len(road_types)})")

    return total_score


def compute_exfil_directions(lat: float, lon: float, osm_data: OSMData) -> List[str]:
    """
    Compute primary exfiltration directions (N, NE, E, etc.).

    Args:
        lat: Latitude
        lon: Longitude
        osm_data: OSM data

    Returns:
        List of cardinal directions (sorted by attractiveness)
    """
    routes = compute_exfil_routes(lat, lon, osm_data)

    # Group routes by direction
    direction_scores: Dict[str, float] = {}

    for route in routes:
        # Synthetic: assign directions based on road index
        # In real implementation, would use actual road geometries
        directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
        for direction in directions:
            if direction not in direction_scores:
                direction_scores[direction] = route["score"] * 0.3  # Synthetic

    # Sort by score
    sorted_directions = sorted(direction_scores.items(), key=lambda x: x[1], reverse=True)

    return [d[0] for d in sorted_directions[:3]]
