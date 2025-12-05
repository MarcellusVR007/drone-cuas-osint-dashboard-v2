"""
Vector Alignment Engine

Scores how well a predicted operator hotspot aligns with observed flight vectors.
If drone approached from NE, operator likely NE of target.
"""

from typing import Optional, Dict
import math
import logging

logger = logging.getLogger(__name__)


# Cardinal directions to degrees
DIRECTION_TO_DEGREES = {
    "N": 0,
    "NNE": 22.5,
    "NE": 45,
    "ENE": 67.5,
    "E": 90,
    "ESE": 112.5,
    "SE": 135,
    "SSE": 157.5,
    "S": 180,
    "SSW": 202.5,
    "SW": 225,
    "WSW": 247.5,
    "W": 270,
    "WNW": 292.5,
    "NW": 315,
    "NNW": 337.5,
}


def parse_direction(direction_str: Optional[str]) -> Optional[float]:
    """
    Parse direction string to degrees.

    Args:
        direction_str: Cardinal direction like "NE", "North", "SW"

    Returns:
        Degrees (0-360) or None
    """
    if not direction_str:
        return None

    # Normalize
    direction_str = direction_str.upper().strip()

    # Try exact match
    if direction_str in DIRECTION_TO_DEGREES:
        return DIRECTION_TO_DEGREES[direction_str]

    # Try partial matches
    for key, value in DIRECTION_TO_DEGREES.items():
        if key in direction_str or direction_str in key:
            return value

    # Try full names
    full_names = {
        "NORTH": 0,
        "NORTHEAST": 45,
        "EAST": 90,
        "SOUTHEAST": 135,
        "SOUTH": 180,
        "SOUTHWEST": 225,
        "WEST": 270,
        "NORTHWEST": 315,
    }

    for key, value in full_names.items():
        if key in direction_str:
            return value

    logger.warning(f"Could not parse direction: {direction_str}")
    return None


def compute_bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Compute bearing from point1 to point2 in degrees.

    Args:
        lat1, lon1: From point
        lat2, lon2: To point

    Returns:
        Bearing in degrees (0-360, 0=North)
    """
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lon_rad = math.radians(lon2 - lon1)

    y = math.sin(delta_lon_rad) * math.cos(lat2_rad)
    x = (math.cos(lat1_rad) * math.sin(lat2_rad) -
         math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(delta_lon_rad))

    bearing_rad = math.atan2(y, x)
    bearing_deg = math.degrees(bearing_rad)

    # Normalize to 0-360
    return (bearing_deg + 360) % 360


def angular_difference(angle1: float, angle2: float) -> float:
    """
    Compute smallest angular difference between two angles.

    Args:
        angle1, angle2: Angles in degrees

    Returns:
        Difference in degrees (0-180)
    """
    diff = abs(angle1 - angle2)
    if diff > 180:
        diff = 360 - diff
    return diff


def score_vector_alignment(hotspot_lat: float, hotspot_lon: float,
                           target_lat: float, target_lon: float,
                           approach_vector: Optional[str],
                           confidence_weight: float = 1.0) -> Dict:
    """
    Score how well a hotspot aligns with the observed approach vector.

    If drone approached from NE, operator should be NE of target.

    Args:
        hotspot_lat, hotspot_lon: Predicted operator location
        target_lat, target_lon: Incident target location
        approach_vector: Observed approach direction (e.g., "NE", "North")
        confidence_weight: Confidence in the approach vector (0-1)

    Returns:
        Dict with 'alignment_score', 'bearing_diff', 'expected_bearing', 'actual_bearing'
    """
    if not approach_vector:
        return {
            "alignment_score": 0.5,  # Neutral - no data
            "bearing_diff_deg": None,
            "expected_bearing_deg": None,
            "actual_bearing_deg": None,
            "reasoning": "No approach vector data available"
        }

    # Parse approach vector
    expected_bearing = parse_direction(approach_vector)
    if expected_bearing is None:
        return {
            "alignment_score": 0.5,
            "bearing_diff_deg": None,
            "expected_bearing_deg": None,
            "actual_bearing_deg": None,
            "reasoning": f"Could not parse approach vector: {approach_vector}"
        }

    # Compute actual bearing from hotspot to target
    # (This is where drone would come FROM if operator at hotspot)
    actual_bearing = compute_bearing(hotspot_lat, hotspot_lon, target_lat, target_lon)

    # Angular difference
    bearing_diff = angular_difference(expected_bearing, actual_bearing)

    # Score: Perfect match = 1.0, opposite direction = 0.0
    # Linear decay from 0-90 degrees
    if bearing_diff <= 30:
        alignment_score = 1.0
    elif bearing_diff <= 60:
        alignment_score = 1.0 - (bearing_diff - 30) / 30 * 0.3  # 1.0 → 0.7
    elif bearing_diff <= 90:
        alignment_score = 0.7 - (bearing_diff - 60) / 30 * 0.4  # 0.7 → 0.3
    else:
        alignment_score = 0.3 - (bearing_diff - 90) / 90 * 0.3  # 0.3 → 0.0

    # Apply confidence weight
    weighted_score = 0.5 + (alignment_score - 0.5) * confidence_weight

    logger.debug(f"Vector alignment: expected={expected_bearing:.0f}°, "
                f"actual={actual_bearing:.0f}°, diff={bearing_diff:.0f}°, "
                f"score={weighted_score:.2f}")

    return {
        "alignment_score": weighted_score,
        "bearing_diff_deg": bearing_diff,
        "expected_bearing_deg": expected_bearing,
        "actual_bearing_deg": actual_bearing,
        "reasoning": f"Approach from {approach_vector} (expected {expected_bearing:.0f}°), "
                    f"hotspot bearing {actual_bearing:.0f}°, diff {bearing_diff:.0f}°"
    }


def score_exit_alignment(hotspot_lat: float, hotspot_lon: float,
                        target_lat: float, target_lon: float,
                        exit_vector: Optional[str],
                        confidence_weight: float = 1.0) -> Dict:
    """
    Score how well a hotspot aligns with the observed exit vector.

    If drone exited to SW, operator likely SW of target.

    Args:
        hotspot_lat, hotspot_lon: Predicted operator location
        target_lat, target_lon: Incident target location
        exit_vector: Observed exit direction (e.g., "SW", "West")
        confidence_weight: Confidence in the exit vector (0-1)

    Returns:
        Dict with 'alignment_score', 'bearing_diff', etc.
    """
    # Same logic as approach, but for exit
    return score_vector_alignment(hotspot_lat, hotspot_lon, target_lat, target_lon,
                                  exit_vector, confidence_weight)


def compute_vector_consistency(approach_vector: Optional[str],
                               exit_vector: Optional[str]) -> Dict:
    """
    Compute consistency between approach and exit vectors.

    Args:
        approach_vector: Approach direction
        exit_vector: Exit direction

    Returns:
        Dict with 'consistency_score' and 'reasoning'
    """
    if not approach_vector or not exit_vector:
        return {
            "consistency_score": 0.5,
            "reasoning": "Insufficient vector data"
        }

    approach_deg = parse_direction(approach_vector)
    exit_deg = parse_direction(exit_vector)

    if approach_deg is None or exit_deg is None:
        return {
            "consistency_score": 0.5,
            "reasoning": "Could not parse vectors"
        }

    # Compute angular difference
    diff = angular_difference(approach_deg, exit_deg)

    # Similar vectors (within 45°) suggest same operator location
    if diff <= 45:
        consistency = 1.0
        reasoning = "Approach and exit vectors align well - same operator location likely"
    elif diff <= 90:
        consistency = 0.7
        reasoning = "Approach and exit vectors moderately aligned"
    elif diff <= 135:
        consistency = 0.4
        reasoning = "Approach and exit vectors diverge - possible repositioning"
    else:
        consistency = 0.2
        reasoning = "Approach and exit vectors opposite - operator likely moved"

    return {
        "consistency_score": consistency,
        "reasoning": reasoning,
        "approach_deg": approach_deg,
        "exit_deg": exit_deg,
        "angular_diff_deg": diff,
    }
