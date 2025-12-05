"""
Operator Hideout Prediction

Predicts drone operator launch sites using OPSEC-TTP analysis.

V1: Rule-based engine (Sprint 2)
V2: Terrain-aware intelligence engine (Sprint 4)
"""

# Shared models
from .models import CoverType, TerrainSuitability

# V2 exports (preferred)
from .engine_v2 import (
    OperatorHideoutEngineV2,
    OperatorAnalysisV2,
    OperatorHotspotV2,
)

# Factory function for API compatibility
from .factory import analyze_operator_location

__all__ = [
    # V2 (Sprint 4)
    "OperatorHideoutEngineV2",
    "OperatorAnalysisV2",
    "OperatorHotspotV2",
    # Shared models
    "CoverType",
    "TerrainSuitability",
    # Factory function (for API compatibility)
    "analyze_operator_location",
]
