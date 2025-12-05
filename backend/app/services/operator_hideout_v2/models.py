"""
Operator Hideout Models

Shared models for V1 and V2 engines.
"""

from enum import Enum


class CoverType(str, Enum):
    """Types of cover for operator concealment."""
    FOREST = "forest"
    URBAN_BUILDING = "urban_building"
    PARKING_LOT = "parking_lot"
    RURAL_STRUCTURE = "rural_structure"
    VEHICLE = "vehicle"
    OPEN_FIELD = "open_field"
    UNKNOWN = "unknown"


class TerrainSuitability(str, Enum):
    """Terrain suitability for operator positioning."""
    EXCELLENT = "excellent"
    GOOD = "good"
    MODERATE = "moderate"
    POOR = "poor"
    UNSUITABLE = "unsuitable"
