"""
Evidence Weighting

Extracts and weights evidence for operator location prediction.
"""

from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


def compute_evidence_weight(evidence_items: List[Dict]) -> Dict:
    """
    Compute overall evidence weight and confidence.

    Args:
        evidence_items: List of evidence items with credibility scores

    Returns:
        Dict with 'total_weight', 'avg_credibility', 'source_diversity'
    """
    if not evidence_items:
        return {
            "total_weight": 0.0,
            "avg_credibility": 0.0,
            "source_diversity": 0.0,
            "num_sources": 0,
        }

    # Calculate average credibility
    credibilities = [e.get("credibility_score", 0.5) for e in evidence_items]
    avg_credibility = sum(credibilities) / len(credibilities)

    # Source diversity
    source_types = set(e.get("source_type", "unknown") for e in evidence_items)
    diversity = len(source_types) / max(len(evidence_items), 5)  # Normalize by 5

    # Total weight: more evidence = higher weight, but with diminishing returns
    num_sources = len(evidence_items)
    if num_sources == 1:
        count_factor = 0.7
    elif num_sources <= 3:
        count_factor = 0.85
    elif num_sources <= 5:
        count_factor = 0.95
    else:
        count_factor = 1.0

    total_weight = avg_credibility * count_factor * (1 + diversity * 0.2)

    return {
        "total_weight": min(1.0, total_weight),
        "avg_credibility": avg_credibility,
        "source_diversity": diversity,
        "num_sources": num_sources,
    }


def extract_locality_cues(evidence_items: List[Dict],
                          target_lat: float, target_lon: float) -> Dict:
    """
    Extract locality cues from evidence (mentions of nearby areas).

    Args:
        evidence_items: Evidence items
        target_lat, target_lon: Target location

    Returns:
        Dict with locality information
    """
    # Calculate average locality score
    locality_scores = [e.get("locality_score", 0.5) for e in evidence_items if evidence_items]

    if not locality_scores:
        return {
            "avg_locality": 0.5,
            "local_mentions": 0,
            "reasoning": "No locality data in evidence"
        }

    avg_locality = sum(locality_scores) / len(locality_scores)

    # Count high-locality sources (>0.7)
    local_mentions = sum(1 for s in locality_scores if s > 0.7)

    reasoning = f"Average locality score {avg_locality:.2f} from {len(locality_scores)} sources"
    if local_mentions > 0:
        reasoning += f", {local_mentions} highly local sources"

    return {
        "avg_locality": avg_locality,
        "local_mentions": local_mentions,
        "reasoning": reasoning,
    }


def compute_witness_confidence(evidence_items: List[Dict]) -> float:
    """
    Compute confidence from witness statement quality.

    Args:
        evidence_items: Evidence items

    Returns:
        Witness confidence score 0.0-1.0
    """
    witness_sources = [e for e in evidence_items
                      if e.get("source_type", "").lower() in ["witness_statement", "witness"]]

    if not witness_sources:
        return 0.5  # Neutral - no witness data

    # Average credibility of witness statements
    credibilities = [w.get("credibility_score", 0.5) for w in witness_sources]
    avg_credibility = sum(credibilities) / len(credibilities)

    # Boost for multiple witnesses
    if len(witness_sources) >= 3:
        multiple_witness_bonus = 0.15
    elif len(witness_sources) >= 2:
        multiple_witness_bonus = 0.10
    else:
        multiple_witness_bonus = 0.0

    return min(1.0, avg_credibility + multiple_witness_bonus)
