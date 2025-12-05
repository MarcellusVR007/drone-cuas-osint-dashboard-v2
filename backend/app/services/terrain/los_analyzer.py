"""
Line-of-Sight (LOS) Analyzer

Computes line-of-sight constraints for drone operations.
Determines if an operator location has clear LOS to target.
"""

from typing import Dict, Tuple, List
from .elevation_loader import get_elevation_at_point, compute_elevation_difference
import math
import logging

logger = logging.getLogger(__name__)


def compute_line_of_sight(operator_lat: float, operator_lon: float,
                          target_lat: float, target_lon: float,
                          elevation_map: Dict[Tuple[float, float], float],
                          num_samples: int = 10) -> Dict:
    """
    Compute line-of-sight analysis between operator and target.

    Args:
        operator_lat, operator_lon: Operator location
        target_lat, target_lon: Target location
        elevation_map: Elevation data
        num_samples: Number of elevation samples along the path

    Returns:
        Dict with 'has_los', 'blocked_by', 'obstruction_height', 'quality'
    """
    # Sample elevations along the path
    operator_elev = get_elevation_at_point(operator_lat, operator_lon, elevation_map)
    target_elev = get_elevation_at_point(target_lat, target_lon, elevation_map)

    # Check intermediate points
    max_obstruction = 0.0
    blocked = False

    for i in range(1, num_samples):
        t = i / num_samples
        sample_lat = operator_lat + t * (target_lat - operator_lat)
        sample_lon = operator_lon + t * (target_lon - operator_lon)
        sample_elev = get_elevation_at_point(sample_lat, sample_lon, elevation_map)

        # Expected elevation on straight line
        expected_elev = operator_elev + t * (target_elev - operator_elev)

        # Obstruction height
        obstruction = sample_elev - expected_elev

        if obstruction > max_obstruction:
            max_obstruction = obstruction

        # Significant obstruction (>10m above line)
        if obstruction > 10:
            blocked = True

    # LOS quality score
    if blocked:
        quality = max(0.0, 0.5 - (max_obstruction - 10) / 50)  # Penalty for height
    else:
        if max_obstruction < -10:
            quality = 1.0  # Perfect - looking down
        elif max_obstruction < 0:
            quality = 0.9  # Good - clear path
        else:
            quality = 0.8  # Acceptable - minor obstructions

    logger.debug(f"LOS from ({operator_lat:.4f}, {operator_lon:.4f}) to "
                f"({target_lat:.4f}, {target_lon:.4f}): "
                f"blocked={blocked}, quality={quality:.2f}, max_obst={max_obstruction:.1f}m")

    return {
        "has_los": not blocked,
        "blocked": blocked,
        "max_obstruction_m": max_obstruction,
        "quality": quality,
        "operator_elevation_m": operator_elev,
        "target_elevation_m": target_elev,
    }


def has_los_to_target(operator_lat: float, operator_lon: float,
                     target_lat: float, target_lon: float,
                     elevation_map: Dict[Tuple[float, float], float]) -> bool:
    """
    Simple check if operator has line-of-sight to target.

    Args:
        operator_lat, operator_lon: Operator location
        target_lat, target_lon: Target location
        elevation_map: Elevation data

    Returns:
        True if LOS exists, False otherwise
    """
    los_result = compute_line_of_sight(operator_lat, operator_lon,
                                       target_lat, target_lon,
                                       elevation_map)
    return los_result["has_los"]


def compute_los_quality_score(operator_lat: float, operator_lon: float,
                              target_lat: float, target_lon: float,
                              elevation_map: Dict[Tuple[float, float], float]) -> float:
    """
    Compute LOS quality score (0.0-1.0).

    Higher scores for:
    - Clear line of sight
    - Operator at higher elevation (better vantage)
    - Minimal obstructions

    Args:
        operator_lat, operator_lon: Operator location
        target_lat, target_lon: Target location
        elevation_map: Elevation data

    Returns:
        LOS quality score 0.0-1.0
    """
    los_result = compute_line_of_sight(operator_lat, operator_lon,
                                       target_lat, target_lon,
                                       elevation_map)

    base_quality = los_result["quality"]

    # Bonus for elevated position (better vantage point)
    elev_diff = los_result["operator_elevation_m"] - los_result["target_elevation_m"]
    if elev_diff > 20:
        elevation_bonus = 0.10
    elif elev_diff > 10:
        elevation_bonus = 0.05
    else:
        elevation_bonus = 0.0

    total_quality = min(1.0, base_quality + elevation_bonus)

    return total_quality
