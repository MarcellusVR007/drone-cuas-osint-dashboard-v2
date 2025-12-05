"""
OSINT Fusion Layer

Integrates evidence from multiple sources to inform operator hideout prediction.
Uses enriched evidence fields like approach vectors, witness statements, etc.
"""

from .vector_alignment import (
    score_vector_alignment,
    score_exit_alignment,
    compute_vector_consistency
)
from .evidence_weighting import (
    compute_evidence_weight,
    extract_locality_cues,
    compute_witness_confidence
)
from .confidence_model import (
    compute_confidence_level,
    generate_confidence_reasoning
)

__all__ = [
    "score_vector_alignment",
    "score_exit_alignment",
    "compute_vector_consistency",
    "compute_evidence_weight",
    "extract_locality_cues",
    "compute_witness_confidence",
    "compute_confidence_level",
    "generate_confidence_reasoning",
]
