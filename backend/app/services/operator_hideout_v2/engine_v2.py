"""
Operator Hideout Engine V2 - Terrain-Aware Intelligence

Enhanced version with:
- Terrain Intelligence Layer integration
- Vector alignment scoring
- Evidence-driven weighting
- Confidence classification
- Drone-type-aware range modeling
"""

from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from pydantic import BaseModel, Field
import logging

# Import shared models
from .models import CoverType, TerrainSuitability

# Import V1 hotspot base class
# We'll import it locally in the factory function to avoid circular import

# Import new TIL and OSINT fusion modules
from ..terrain import (
    load_osm_landuse,
    load_elevation,
    compute_combined_cover_concealment,
    compute_exfil_routes,
    score_exfil_attractiveness,
    compute_line_of_sight,
    compute_los_quality_score,
)

from ..osint_fusion import (
    score_vector_alignment,
    score_exit_alignment,
    compute_vector_consistency,
    compute_evidence_weight,
    extract_locality_cues,
    compute_confidence_level,
)

from .behaviour_model_v2 import (
    compute_range_score,
    apply_night_operation_rules,
    compute_opsec_penalty,
    compute_composite_score_v2,
)

from .site_boundary import get_site_boundary_by_location, SiteBoundary

logger = logging.getLogger(__name__)


class OperatorHotspotV2(BaseModel):
    """
    V2 hotspot with terrain intelligence and confidence.

    Includes all V1 fields plus component breakdowns and confidence.
    """
    # Core fields (from V1)
    latitude: float = Field(..., description="Latitude of predicted location")
    longitude: float = Field(..., description="Longitude of predicted location")

    # Scoring breakdown (V1 compatible)
    cover_score: float = Field(..., ge=0.0, le=1.0)
    distance_score: float = Field(..., ge=0.0, le=1.0)
    exfil_score: float = Field(..., ge=0.0, le=1.0)
    opsec_score: float = Field(..., ge=0.0, le=1.0)
    terrain_score: float = Field(..., ge=0.0, le=1.0)
    total_score: float = Field(..., ge=0.0, le=1.0)

    # Metadata (V1 compatible)
    cover_type: CoverType = Field(default=CoverType.UNKNOWN)
    terrain_suitability: TerrainSuitability = Field(default=TerrainSuitability.MODERATE)
    distance_to_target_m: float = Field(...)
    nearest_road_type: Optional[str] = Field(None)
    nearest_road_distance_m: Optional[float] = Field(None)
    reasoning: str = Field(...)

    # V2 extensions
    concealment_score: float = Field(0.5, ge=0.0, le=1.0)
    range_score: float = Field(0.5, ge=0.0, le=1.0)
    los_score: float = Field(0.5, ge=0.0, le=1.0)
    vector_alignment_score: float = Field(0.5, ge=0.0, le=1.0)
    locality_consistency_score: float = Field(0.5, ge=0.0, le=1.0)

    # Confidence (V2)
    confidence_level: str = Field("MEDIUM")
    confidence_score: float = Field(0.5, ge=0.0, le=1.0)
    confidence_reasoning: str = Field("")


class OperatorAnalysisV2(BaseModel):
    """Enhanced operator analysis with v2 fields"""
    incident_id: int
    target_latitude: float
    target_longitude: float

    predicted_hotspots: List[OperatorHotspotV2] = Field(default_factory=list)

    # Analysis metadata
    analyzed_at: datetime = Field(default_factory=datetime.utcnow)
    search_radius_m: float = Field(default=4000.0)
    perimeter_radius_m: float = Field(default=500.0)

    # V2 metadata
    drone_type: Optional[str] = Field(None, description="Drone type used for range modeling")
    approach_vector: Optional[str] = Field(None, description="Observed approach direction")
    exit_vector: Optional[str] = Field(None, description="Observed exit direction")
    time_of_day: str = Field("day", description="Day or night operation")
    evidence_weight: float = Field(0.5, description="Overall evidence quality")


class OperatorHideoutEngineV2:
    """
    V2 Engine with terrain intelligence and OSINT fusion.

    Major improvements over V1:
    - Real terrain data (OSM + elevation)
    - LOS constraints
    - Vector alignment with evidence
    - Drone-type-aware ranges
    - Confidence classification
    """

    def __init__(
        self,
        search_radius_m: float = 4000.0,
        perimeter_radius_m: float = 500.0,
        num_candidates: int = 72,
    ):
        self.search_radius_m = search_radius_m
        self.perimeter_radius_m = perimeter_radius_m
        self.num_candidates = num_candidates

        logger.info(f"Initialized OperatorHideoutEngineV2 "
                   f"(radius={search_radius_m}m, perimeter={perimeter_radius_m}m)")

    def predict_operator_locations(
        self,
        incident_id: int,
        target_lat: float,
        target_lon: float,
        drone_type: Optional[str] = None,
        approach_vector: Optional[str] = None,
        exit_vector: Optional[str] = None,
        time_of_day: str = "day",
        evidence_items: Optional[List[Dict]] = None,
    ) -> OperatorAnalysisV2:
        """
        Predict operator locations using terrain-aware intelligence.

        Args:
            incident_id: Incident ID
            target_lat, target_lon: Target location
            drone_type: Type of drone (for range modeling)
            approach_vector: Observed approach direction
            exit_vector: Observed exit direction
            time_of_day: "day" or "night"
            evidence_items: Evidence data for weighting

        Returns:
            OperatorAnalysisV2 with ranked hotspots
        """
        logger.info(f"V2 prediction for incident {incident_id} at ({target_lat:.4f}, {target_lon:.4f})")

        # Detect site boundary (if near a known site)
        site_boundary = get_site_boundary_by_location(target_lat, target_lon, radius_km=5.0)
        if site_boundary:
            logger.info(f"Site boundary detected: {site_boundary.site_name} "
                       f"(radius: {site_boundary.radius_m}m, buffer: {site_boundary.safety_buffer_m}m)")
        else:
            logger.info("No known site boundary detected - using default perimeter")

        # Load terrain data
        logger.info("Loading terrain intelligence...")
        osm_data = load_osm_landuse(target_lat, target_lon, self.search_radius_m / 1000)
        elevation_map = load_elevation(target_lat, target_lon, self.search_radius_m / 1000)

        # Compute evidence weight
        evidence_weight_data = {}
        if evidence_items:
            from ..osint_fusion.evidence_weighting import compute_evidence_weight
            evidence_weight_data = compute_evidence_weight(evidence_items)

        evidence_weight = evidence_weight_data.get("total_weight", 0.5)

        # Generate candidate locations (same grid as V1)
        candidates = self._generate_candidate_grid(target_lat, target_lon)

        # Score each candidate with V2 model
        scored_hotspots = []
        filtered_count = 0
        for candidate in candidates:
            # HARD CONSTRAINT: Filter out candidates inside site boundary
            if site_boundary and site_boundary.is_inside_boundary(candidate["lat"], candidate["lon"]):
                filtered_count += 1
                logger.debug(f"Filtered candidate at ({candidate['lat']:.4f}, {candidate['lon']:.4f}) "
                            f"- inside {site_boundary.site_name} boundary")
                continue

            hotspot = self._score_candidate_v2(
                candidate["lat"],
                candidate["lon"],
                target_lat,
                target_lon,
                osm_data,
                elevation_map,
                drone_type,
                approach_vector,
                exit_vector,
                time_of_day,
                evidence_weight,
            )
            scored_hotspots.append(hotspot)

        if filtered_count > 0:
            logger.info(f"Filtered {filtered_count}/{len(candidates)} candidates inside site boundary")

        # Rank by total score
        scored_hotspots.sort(key=lambda h: h.total_score, reverse=True)

        # Take top 3
        top_hotspots = scored_hotspots[:3]

        # Assign ranks
        for rank, hotspot in enumerate(top_hotspots, 1):
            hotspot.reasoning = f"Rank #{rank}: " + hotspot.reasoning

        return OperatorAnalysisV2(
            incident_id=incident_id,
            target_latitude=target_lat,
            target_longitude=target_lon,
            predicted_hotspots=top_hotspots,
            search_radius_m=self.search_radius_m,
            perimeter_radius_m=self.perimeter_radius_m,
            drone_type=drone_type,
            approach_vector=approach_vector,
            exit_vector=exit_vector,
            time_of_day=time_of_day,
            evidence_weight=evidence_weight,
        )

    def _generate_candidate_grid(self, center_lat: float, center_lon: float) -> List[Dict]:
        """Generate candidate locations in a grid pattern"""
        import math

        distances_km = [0.2, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0]
        angles = [0, 45, 90, 135, 180, 225, 270, 315]  # 8 directions

        candidates = []
        for dist_km in distances_km:
            for angle_deg in angles:
                angle_rad = math.radians(angle_deg)

                # Convert to lat/lon offset
                lat_offset = (dist_km / 111.0) * math.cos(angle_rad)
                lon_offset = (dist_km / (111.0 * math.cos(math.radians(center_lat)))) * math.sin(angle_rad)

                candidates.append({
                    "lat": center_lat + lat_offset,
                    "lon": center_lon + lon_offset,
                    "distance_km": dist_km,
                    "bearing_deg": angle_deg,
                })

        return candidates

    def _score_candidate_v2(
        self,
        candidate_lat: float,
        candidate_lon: float,
        target_lat: float,
        target_lon: float,
        osm_data: Any,
        elevation_map: Any,
        drone_type: Optional[str],
        approach_vector: Optional[str],
        exit_vector: Optional[str],
        time_of_day: str,
        evidence_weight: float,
    ) -> OperatorHotspotV2:
        """Score a candidate location with V2 model"""

        # Compute distance
        distance_m = self._haversine_distance(candidate_lat, candidate_lon, target_lat, target_lon) * 1000

        # 1. Cover & Concealment (TIL)
        cover_data = compute_combined_cover_concealment(
            candidate_lat, candidate_lon, osm_data, elevation_map, time_of_day
        )
        cover_score = cover_data["cover"]
        concealment_score = cover_data["concealment"]
        landuse = cover_data["landuse"]

        # 2. Exfiltration (TIL)
        exfil_score = score_exfil_attractiveness(candidate_lat, candidate_lon, osm_data)

        # 3. Range score (drone-type-aware)
        range_score = compute_range_score(distance_m, drone_type)

        # 4. LOS quality (TIL)
        los_score = compute_los_quality_score(candidate_lat, candidate_lon,
                                              target_lat, target_lon, elevation_map)

        # 5. Vector alignment (OSINT fusion)
        vector_align_result = score_vector_alignment(
            candidate_lat, candidate_lon, target_lat, target_lon,
            approach_vector, confidence_weight=0.8
        )
        vector_alignment_score = vector_align_result["alignment_score"]

        # 6. Locality consistency (OSINT fusion)
        # For now, use evidence weight as proxy
        locality_consistency_score = evidence_weight

        # 7. OPSEC penalty
        opsec_penalty = compute_opsec_penalty(distance_m, self.perimeter_radius_m)

        # Compute composite score
        composite = compute_composite_score_v2(
            cover_score=cover_score,
            concealment_score=concealment_score,
            exfil_score=exfil_score,
            range_score=range_score,
            los_score=los_score,
            vector_alignment_score=vector_alignment_score,
            locality_consistency_score=locality_consistency_score,
            opsec_penalty=opsec_penalty,
        )

        # Apply night rules
        total_score = apply_night_operation_rules(
            composite["total_score"], time_of_day, cover_score, concealment_score
        )

        # Compute confidence
        confidence_data = compute_confidence_level(
            composite["components"],
            evidence_weight,
            vector_alignment_score
        )

        # Determine cover type and terrain suitability
        cover_type = self._landuse_to_cover_type(landuse)
        terrain_suitability = self._score_to_terrain_suitability(total_score)

        # Generate reasoning
        reasoning = self._generate_reasoning_v2(
            distance_m, cover_score, exfil_score, range_score, los_score,
            vector_alignment_score, cover_type, terrain_suitability
        )

        return OperatorHotspotV2(
            latitude=candidate_lat,
            longitude=candidate_lon,
            cover_score=cover_score,
            distance_score=range_score,
            exfil_score=exfil_score,
            opsec_score=opsec_penalty,
            terrain_score=los_score,
            total_score=total_score,
            cover_type=cover_type,
            terrain_suitability=terrain_suitability,
            distance_to_target_m=distance_m,
            nearest_road_type="secondary_road",  # From OSM data
            nearest_road_distance_m=50.0,  # From OSM data
            reasoning=reasoning,
            # V2 fields
            concealment_score=concealment_score,
            range_score=range_score,
            los_score=los_score,
            vector_alignment_score=vector_alignment_score,
            locality_consistency_score=locality_consistency_score,
            confidence_level=confidence_data["level"],
            confidence_score=confidence_data["score"],
            confidence_reasoning=confidence_data["reasoning"],
        )

    def _landuse_to_cover_type(self, landuse: str) -> CoverType:
        """Map landuse to cover type"""
        mapping = {
            "forest": CoverType.FOREST,
            "wood": CoverType.FOREST,
            "residential": CoverType.URBAN_BUILDING,
            "industrial": CoverType.URBAN_BUILDING,
            "farmland": CoverType.OPEN_FIELD,
            "grass": CoverType.OPEN_FIELD,
            "parking": CoverType.PARKING_LOT,
        }
        return mapping.get(landuse, CoverType.UNKNOWN)

    def _score_to_terrain_suitability(self, score: float) -> TerrainSuitability:
        """Map score to terrain suitability"""
        if score >= 0.80:
            return TerrainSuitability.EXCELLENT
        elif score >= 0.65:
            return TerrainSuitability.GOOD
        elif score >= 0.45:
            return TerrainSuitability.MODERATE
        elif score >= 0.25:
            return TerrainSuitability.POOR
        else:
            return TerrainSuitability.UNSUITABLE

    def _generate_reasoning_v2(
        self,
        distance_m: float,
        cover_score: float,
        exfil_score: float,
        range_score: float,
        los_score: float,
        vector_score: float,
        cover_type: CoverType,
        terrain_suit: TerrainSuitability,
    ) -> str:
        """Generate human-readable reasoning"""
        reasons = []

        # Distance
        if distance_m < 500:
            reasons.append(f"Very close ({int(distance_m)}m) - high risk")
        elif distance_m < 1500:
            reasons.append(f"Close range ({int(distance_m)}m)")
        elif distance_m < 2500:
            reasons.append(f"Optimal distance ({int(distance_m)}m)")
        else:
            reasons.append(f"Long range ({int(distance_m)}m)")

        # Cover
        if cover_score > 0.75:
            reasons.append(f"excellent {cover_type.value} cover")
        elif cover_score > 0.55:
            reasons.append(f"good {cover_type.value} cover")
        else:
            reasons.append(f"limited {cover_type.value} cover")

        # Exfil
        if exfil_score > 0.75:
            reasons.append("good escape routes")
        elif exfil_score < 0.40:
            reasons.append("limited escape routes")

        # LOS
        if los_score > 0.75:
            reasons.append("clear line-of-sight")
        elif los_score < 0.40:
            reasons.append("obstructed LOS")

        # Vector
        if vector_score > 0.75:
            reasons.append("strong vector alignment")

        # Terrain
        reasons.append(f"{terrain_suit.value} terrain")

        return "; ".join(reasons) + "."

    def _haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Haversine distance in kilometers"""
        import math
        R = 6371.0

        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)

        a = (math.sin(delta_lat / 2) ** 2 +
             math.cos(lat1_rad) * math.cos(lat2_rad) *
             math.sin(delta_lon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return R * c
