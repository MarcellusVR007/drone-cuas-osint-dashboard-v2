"""
Terrain Intelligence Layer (TIL)

Provides terrain-aware intelligence for operator hideout prediction:
- OSM landuse data loading
- Elevation data loading
- Cover/concealment scoring
- Exfiltration route analysis
"""

from .osm_loader import load_osm_landuse, get_landuse_at_point
from .elevation_loader import load_elevation, get_elevation_at_point
from .cover_analyzer import (
    compute_cover_score,
    compute_concealment_score,
    compute_combined_cover_concealment,
)
from .exfil_analyzer import compute_exfil_routes, score_exfil_attractiveness
from .los_analyzer import (
    compute_line_of_sight,
    has_los_to_target,
    compute_los_quality_score,
)

__all__ = [
    "load_osm_landuse",
    "get_landuse_at_point",
    "load_elevation",
    "get_elevation_at_point",
    "compute_cover_score",
    "compute_concealment_score",
    "compute_combined_cover_concealment",
    "compute_exfil_routes",
    "score_exfil_attractiveness",
    "compute_line_of_sight",
    "has_los_to_target",
    "compute_los_quality_score",
]
