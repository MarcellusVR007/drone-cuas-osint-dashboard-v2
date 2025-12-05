"""
Factory function for operator location analysis.

Provides backward-compatible interface for API.
"""

from typing import Optional, List, Dict
import logging

# Import V1 models from sibling operator_hideout.py file
from backend.app.services.operator_hideout import (
    OperatorAnalysis,
    OperatorHotspot,
    OperatorHideoutEngine,
)

# Import V2 from local package
from .engine_v2 import OperatorHideoutEngineV2

logger = logging.getLogger(__name__)


def analyze_operator_location(
    incident_id: int,
    target_lat: float,
    target_lon: float,
    site_type: Optional[str] = None,
    use_v2: bool = True,  # Sprint 4: Enable V2 by default
    drone_type: Optional[str] = None,
    approach_vector: Optional[str] = None,
    exit_vector: Optional[str] = None,
    time_of_day: str = "day",
    evidence_items: Optional[List[Dict]] = None,
) -> OperatorAnalysis:
    """Analyze incident and predict operator launch sites.

    Args:
        incident_id: ID of the incident
        target_lat: Target latitude
        target_lon: Target longitude
        site_type: Type of site (airport, military, etc.)
        use_v2: Use V2 terrain-aware engine (default: True)
        drone_type: Drone type for range modeling (V2 only)
        approach_vector: Observed approach direction (V2 only)
        exit_vector: Observed exit direction (V2 only)
        time_of_day: "day" or "night" (V2 only)
        evidence_items: Evidence data (V2 only)

    Returns:
        OperatorAnalysis with 1-3 predicted hotspots
    """
    if use_v2:
        # Use V2 engine with terrain intelligence
        try:
            engine_v2 = OperatorHideoutEngineV2()
            analysis_v2 = engine_v2.predict_operator_locations(
                incident_id=incident_id,
                target_lat=target_lat,
                target_lon=target_lon,
                drone_type=drone_type,
                approach_vector=approach_vector,
                exit_vector=exit_vector,
                time_of_day=time_of_day,
                evidence_items=evidence_items,
            )

            # Convert V2 to V1 format for API compatibility
            v1_hotspots = []
            for v2_hotspot in analysis_v2.predicted_hotspots:
                v1_hotspot = OperatorHotspot(
                    latitude=v2_hotspot.latitude,
                    longitude=v2_hotspot.longitude,
                    cover_score=v2_hotspot.cover_score,
                    distance_score=v2_hotspot.distance_score,
                    exfil_score=v2_hotspot.exfil_score,
                    opsec_score=v2_hotspot.opsec_score,
                    terrain_score=v2_hotspot.terrain_score,
                    total_score=v2_hotspot.total_score,
                    cover_type=v2_hotspot.cover_type,
                    terrain_suitability=v2_hotspot.terrain_suitability,
                    distance_to_target_m=v2_hotspot.distance_to_target_m,
                    nearest_road_type=v2_hotspot.nearest_road_type,
                    nearest_road_distance_m=v2_hotspot.nearest_road_distance_m,
                    reasoning=f"{v2_hotspot.reasoning} [{v2_hotspot.confidence_level} confidence: {v2_hotspot.confidence_reasoning}]",
                )
                v1_hotspots.append(v1_hotspot)

            return OperatorAnalysis(
                incident_id=incident_id,
                target_latitude=target_lat,
                target_longitude=target_lon,
                predicted_hotspots=v1_hotspots,
                search_radius_m=analysis_v2.search_radius_m,
                perimeter_radius_m=analysis_v2.perimeter_radius_m,
            )
        except Exception as e:
            logger.warning(f"V2 engine failed, falling back to V1: {e}", exc_info=True)
            # Fall back to V1

    # Use V1 engine (backward compatibility)
    engine = OperatorHideoutEngine()
    return engine.analyze_incident(incident_id, target_lat, target_lon, site_type)
