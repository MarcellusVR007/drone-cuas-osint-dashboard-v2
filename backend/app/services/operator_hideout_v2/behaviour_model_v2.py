"""
Operator Behaviour Model v2.0

Enhanced scoring model with terrain awareness, vector alignment, and confidence.
"""

from typing import Dict, Optional
from enum import Enum
import math
import logging

logger = logging.getLogger(__name__)


class DroneType(str, Enum):
    """Drone type classifications"""
    CONSUMER_DJI = "consumer_dji"
    CONSUMER_OTHER = "consumer_other"
    RACING_FPV = "racing_fpv"
    MILITARY_SMALL = "military_small"
    MILITARY_MEDIUM = "military_medium"
    DIY_CUSTOM = "diy_custom"
    COMMERCIAL = "commercial"
    UNKNOWN = "unknown"


# Drone type range profiles (in meters)
DRONE_RANGE_PROFILES = {
    DroneType.CONSUMER_DJI: {
        "min_range": 100,
        "optimal_range": 800,
        "max_range": 4000,
        "control_method": "radio",
    },
    DroneType.CONSUMER_OTHER: {
        "min_range": 100,
        "optimal_range": 600,
        "max_range": 3000,
        "control_method": "radio",
    },
    DroneType.RACING_FPV: {
        "min_range": 50,
        "optimal_range": 400,
        "max_range": 2000,
        "control_method": "fpv",
    },
    DroneType.MILITARY_SMALL: {
        "min_range": 200,
        "optimal_range": 2000,
        "max_range": 10000,
        "control_method": "encrypted_radio",
    },
    DroneType.MILITARY_MEDIUM: {
        "min_range": 500,
        "optimal_range": 5000,
        "max_range": 25000,
        "control_method": "satellite",
    },
    DroneType.DIY_CUSTOM: {
        "min_range": 100,
        "optimal_range": 1000,
        "max_range": 5000,
        "control_method": "custom",
    },
    DroneType.COMMERCIAL: {
        "min_range": 100,
        "optimal_range": 1500,
        "max_range": 8000,
        "control_method": "radio",
    },
    DroneType.UNKNOWN: {
        "min_range": 100,
        "optimal_range": 1000,
        "max_range": 4000,
        "control_method": "unknown",
    },
}


def get_drone_range_profile(drone_type: Optional[str]) -> Dict:
    """Get range profile for drone type"""
    if not drone_type:
        drone_type = DroneType.UNKNOWN

    try:
        dtype = DroneType(drone_type)
    except ValueError:
        dtype = DroneType.UNKNOWN

    return DRONE_RANGE_PROFILES[dtype]


def compute_range_score(distance_m: float, drone_type: Optional[str] = None) -> float:
    """
    Compute range score based on distance and drone type.

    Args:
        distance_m: Distance from hotspot to target
        drone_type: Type of drone

    Returns:
        Range score 0.0-1.0 (higher = better distance)
    """
    profile = get_drone_range_profile(drone_type)

    min_range = profile["min_range"]
    optimal_range = profile["optimal_range"]
    max_range = profile["max_range"]

    # Too close: penalize (operator too exposed)
    if distance_m < min_range:
        return 0.3 * (distance_m / min_range)

    # Optimal range: maximum score
    if distance_m <= optimal_range:
        # Linear increase from min to optimal
        return 0.3 + 0.7 * ((distance_m - min_range) / (optimal_range - min_range))

    # Beyond optimal: gradual decay
    if distance_m <= max_range:
        # Linear decay from 1.0 at optimal to 0.3 at max
        return 1.0 - 0.7 * ((distance_m - optimal_range) / (max_range - optimal_range))

    # Beyond max range: very low score
    return max(0.0, 0.3 - (distance_m - max_range) / max_range * 0.3)


def apply_night_operation_rules(base_score: float, time_of_day: str,
                                cover_score: float, concealment_score: float) -> float:
    """
    Apply night operation rules to adjust scoring.

    Night operations:
    - Concealment bonus (darkness helps)
    - Less need for physical cover
    - Detection risk reduced

    Args:
        base_score: Base hotspot score
        time_of_day: "day" or "night"
        cover_score: Cover score
        concealment_score: Concealment score

    Returns:
        Adjusted score
    """
    if time_of_day != "night":
        return base_score

    # Night bonus: concealment becomes more important than cover
    night_concealment_boost = concealment_score * 0.15

    # Night allows more exposed positions (less cover needed)
    if cover_score < 0.5:
        cover_penalty_reduction = 0.10
    else:
        cover_penalty_reduction = 0.0

    adjusted_score = base_score + night_concealment_boost + cover_penalty_reduction

    return min(1.0, adjusted_score)


def compute_opsec_penalty(distance_m: float, perimeter_radius_m: float) -> float:
    """
    Compute OPSEC penalty for being inside security perimeter.

    Args:
        distance_m: Distance from target
        perimeter_radius_m: Security perimeter radius

    Returns:
        OPSEC penalty (0.0-1.0, 0 = inside perimeter = bad)
    """
    if distance_m < perimeter_radius_m:
        # Inside perimeter: severe penalty
        # The closer to center, the worse
        penalty_factor = 1.0 - (distance_m / perimeter_radius_m)
        return 0.0  # Complete disqualification

    # Outside perimeter: no penalty
    return 1.0


def compute_composite_score_v2(
    cover_score: float,
    concealment_score: float,
    exfil_score: float,
    range_score: float,
    los_score: float,
    vector_alignment_score: float,
    locality_consistency_score: float,
    opsec_penalty: float,
    weights: Optional[Dict[str, float]] = None
) -> Dict:
    """
    Compute composite hotspot score with all v2 components.

    Args:
        cover_score: Physical cover quality (0-1)
        concealment_score: Concealment ability (0-1)
        exfil_score: Escape route quality (0-1)
        range_score: Distance suitability (0-1)
        los_score: Line-of-sight quality (0-1)
        vector_alignment_score: Vector alignment with evidence (0-1)
        locality_consistency_score: Consistency with local evidence (0-1)
        opsec_penalty: OPSEC compliance (0 or 1)
        weights: Optional custom weights

    Returns:
        Dict with 'total_score', 'components', 'weighted_components'
    """
    # Default weights (sum to 1.0)
    if weights is None:
        weights = {
            "cover": 0.20,
            "concealment": 0.15,
            "exfil": 0.15,
            "range": 0.15,
            "los": 0.10,
            "vector_alignment": 0.15,
            "locality_consistency": 0.10,
        }

    # Compute weighted components
    weighted_components = {
        "cover": cover_score * weights["cover"],
        "concealment": concealment_score * weights["concealment"],
        "exfil": exfil_score * weights["exfil"],
        "range": range_score * weights["range"],
        "los": los_score * weights["los"],
        "vector_alignment": vector_alignment_score * weights["vector_alignment"],
        "locality_consistency": locality_consistency_score * weights["locality_consistency"],
    }

    # Sum weighted scores
    total_before_opsec = sum(weighted_components.values())

    # Apply OPSEC penalty (multiplicative)
    total_score = total_before_opsec * opsec_penalty

    return {
        "total_score": total_score,
        "components": {
            "cover": cover_score,
            "concealment": concealment_score,
            "exfil": exfil_score,
            "range": range_score,
            "los": los_score,
            "vector_alignment": vector_alignment_score,
            "locality_consistency": locality_consistency_score,
            "opsec": opsec_penalty,
        },
        "weighted_components": weighted_components,
    }
