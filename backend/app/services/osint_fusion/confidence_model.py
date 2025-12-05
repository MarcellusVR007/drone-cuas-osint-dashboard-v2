"""
Confidence Model

Classifies prediction confidence as HIGH/MEDIUM/LOW and generates reasoning.
"""

from typing import Dict, List
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ConfidenceLevel(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


def compute_confidence_level(component_scores: Dict,
                             evidence_weight: float,
                             vector_alignment_score: float) -> Dict:
    """
    Compute overall confidence level for a hotspot prediction.

    Args:
        component_scores: Dict with cover, exfil, range, etc. scores
        evidence_weight: Overall evidence quality (0-1)
        vector_alignment_score: Vector alignment score (0-1)

    Returns:
        Dict with 'level' (HIGH/MEDIUM/LOW), 'score', 'reasoning'
    """
    # Extract component scores
    cover_score = component_scores.get("cover", 0.5)
    exfil_score = component_scores.get("exfil", 0.5)
    range_score = component_scores.get("range", 0.5)
    los_score = component_scores.get("los", 0.5)

    # Compute weighted confidence score
    confidence_score = (
        cover_score * 0.25 +
        exfil_score * 0.20 +
        range_score * 0.15 +
        los_score * 0.15 +
        evidence_weight * 0.15 +
        vector_alignment_score * 0.10
    )

    # Classify confidence level
    if confidence_score >= 0.75:
        level = ConfidenceLevel.HIGH
    elif confidence_score >= 0.55:
        level = ConfidenceLevel.MEDIUM
    else:
        level = ConfidenceLevel.LOW

    # Generate reasoning
    reasoning = generate_confidence_reasoning(level, component_scores, evidence_weight,
                                             vector_alignment_score, confidence_score)

    return {
        "level": level.value,
        "score": confidence_score,
        "reasoning": reasoning,
    }


def generate_confidence_reasoning(level: ConfidenceLevel,
                                 component_scores: Dict,
                                 evidence_weight: float,
                                 vector_alignment_score: float,
                                 confidence_score: float) -> str:
    """
    Generate human-readable reasoning for confidence level.

    Args:
        level: Confidence level
        component_scores: Component scores
        evidence_weight: Evidence quality
        vector_alignment_score: Vector alignment
        confidence_score: Overall confidence score

    Returns:
        Reasoning string
    """
    reasons = []

    # Analyze strong factors
    if level == ConfidenceLevel.HIGH:
        reasons.append(f"High confidence ({confidence_score:.2f})")

        if component_scores.get("cover", 0) > 0.75:
            reasons.append("excellent cover")
        if component_scores.get("exfil", 0) > 0.75:
            reasons.append("good escape routes")
        if vector_alignment_score > 0.75:
            reasons.append("strong vector alignment")
        if evidence_weight > 0.7:
            reasons.append("high-quality evidence")

    elif level == ConfidenceLevel.MEDIUM:
        reasons.append(f"Medium confidence ({confidence_score:.2f})")

        # Identify mixed factors
        strong_components = [k for k, v in component_scores.items() if v > 0.70]
        weak_components = [k for k, v in component_scores.items() if v < 0.40]

        if strong_components:
            reasons.append(f"strong {', '.join(strong_components[:2])}")
        if weak_components:
            reasons.append(f"weak {', '.join(weak_components[:2])}")

    else:  # LOW
        reasons.append(f"Low confidence ({confidence_score:.2f})")

        # Identify weak factors
        if component_scores.get("cover", 0) < 0.40:
            reasons.append("poor cover")
        if component_scores.get("exfil", 0) < 0.40:
            reasons.append("limited escape routes")
        if vector_alignment_score < 0.40:
            reasons.append("weak vector alignment")
        if evidence_weight < 0.40:
            reasons.append("limited evidence")

    return "; ".join(reasons)


def rank_hotspots_by_confidence(hotspots: List[Dict]) -> List[Dict]:
    """
    Rank hotspots by confidence level and score.

    Args:
        hotspots: List of hotspot dicts with confidence data

    Returns:
        Sorted list (HIGH first, then by score)
    """
    # Sort by confidence level (HIGH > MEDIUM > LOW), then by score
    confidence_order = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}

    sorted_hotspots = sorted(
        hotspots,
        key=lambda h: (
            confidence_order.get(h.get("confidence", {}).get("level", "LOW"), 0),
            h.get("confidence", {}).get("score", 0)
        ),
        reverse=True
    )

    return sorted_hotspots
