"""Operator Hideout Engine - Predicts drone operator launch sites using OPSEC-TTP rules.

This module applies operational security (OPSEC) and tactics, techniques, and procedures (TTP)
analysis to predict likely drone operator locations.

Key principles:
1. Operators stay OUTSIDE security perimeters (not inside the target area)
2. Operators use natural cover (trees, buildings, terrain features)
3. Operators need exfiltration routes (roads, paths, escape vectors)
4. Operators stay within drone range (typically 0-4km for consumer drones)

Architecture Layer: services/
Dependencies: domain.incident, domain.site
"""

from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum
import math


class CoverType(str, Enum):
    """Types of cover for operator concealment."""
    FOREST = "forest"
    URBAN_BUILDING = "urban_building"
    PARKING_LOT = "parking_lot"
    RURAL_STRUCTURE = "rural_structure"
    VEHICLE = "vehicle"
    OPEN_FIELD = "open_field"  # Worst case - no cover
    UNKNOWN = "unknown"


class TerrainSuitability(str, Enum):
    """Terrain suitability for operator positioning."""
    EXCELLENT = "excellent"  # Hidden, good access, multiple exfil routes
    GOOD = "good"  # Decent cover, road access
    MODERATE = "moderate"  # Some cover, limited access
    POOR = "poor"  # Exposed, difficult access
    UNSUITABLE = "unsuitable"  # No cover, no access, or inside perimeter


class OperatorHotspot(BaseModel):
    """Predicted operator launch site with scoring breakdown.

    This represents a single predicted location where a drone operator might have been positioned.
    """
    latitude: float = Field(..., description="Latitude of predicted location")
    longitude: float = Field(..., description="Longitude of predicted location")

    # Scoring breakdown (all scores 0-1)
    cover_score: float = Field(..., ge=0.0, le=1.0, description="Cover/concealment quality (0-1)")
    distance_score: float = Field(..., ge=0.0, le=1.0, description="Distance penalty (1 = ideal, 0 = too far/close)")
    exfil_score: float = Field(..., ge=0.0, le=1.0, description="Exfiltration route quality (0-1)")
    opsec_score: float = Field(..., ge=0.0, le=1.0, description="OPSEC compliance (outside perimeter, etc.)")
    terrain_score: float = Field(..., ge=0.0, le=1.0, description="Terrain suitability (0-1)")

    # Final composite score
    total_score: float = Field(..., ge=0.0, le=1.0, description="Weighted composite score")

    # Metadata
    cover_type: CoverType = Field(default=CoverType.UNKNOWN)
    terrain_suitability: TerrainSuitability = Field(default=TerrainSuitability.MODERATE)
    distance_to_target_m: float = Field(..., description="Distance to target in meters")
    nearest_road_type: Optional[str] = Field(None, description="Type of nearest road (highway, street, path)")
    nearest_road_distance_m: Optional[float] = Field(None, description="Distance to nearest road in meters")

    # Reasoning
    reasoning: str = Field(..., description="Human-readable explanation of why this location was selected")


class OperatorAnalysis(BaseModel):
    """Complete operator analysis for an incident.

    Contains 1-3 predicted operator locations ranked by likelihood.
    """
    incident_id: int
    target_latitude: float = Field(..., description="Target incident location latitude")
    target_longitude: float = Field(..., description="Target incident location longitude")

    # Predicted hotspots (ranked by total_score)
    predicted_hotspots: List[OperatorHotspot] = Field(default_factory=list, description="1-3 predicted locations")

    # Analysis metadata
    analyzed_at: datetime = Field(default_factory=datetime.utcnow)
    search_radius_m: float = Field(default=4000.0, description="Search radius used (meters)")
    perimeter_radius_m: float = Field(default=500.0, description="Security perimeter radius (meters)")


class OperatorHideoutEngine:
    """Engine for predicting drone operator launch sites using OPSEC-TTP analysis.

    This is a rule-based engine that generates candidate locations and scores them
    based on operational security principles.
    """

    def __init__(
        self,
        search_radius_m: float = 4000.0,
        perimeter_radius_m: float = 500.0,
        min_distance_m: float = 100.0,
        max_distance_m: float = 4000.0,
    ):
        """Initialize the operator hideout engine.

        Args:
            search_radius_m: Maximum search radius from target (meters)
            perimeter_radius_m: Security perimeter around target (operators must be outside this)
            min_distance_m: Minimum distance from target (too close = detected)
            max_distance_m: Maximum effective drone range
        """
        self.search_radius_m = search_radius_m
        self.perimeter_radius_m = perimeter_radius_m
        self.min_distance_m = min_distance_m
        self.max_distance_m = max_distance_m

        # Scoring weights (must sum to 1.0)
        self.weights = {
            "cover": 0.25,
            "distance": 0.20,
            "exfil": 0.20,
            "opsec": 0.25,
            "terrain": 0.10,
        }

    def analyze_incident(
        self,
        incident_id: int,
        target_lat: float,
        target_lon: float,
        site_type: Optional[str] = None,
    ) -> OperatorAnalysis:
        """Analyze incident and predict operator launch sites.

        Args:
            incident_id: ID of the incident
            target_lat: Target latitude
            target_lon: Target longitude
            site_type: Type of site (airport, military, etc.) for perimeter estimation

        Returns:
            OperatorAnalysis with 1-3 predicted hotspots
        """
        # Generate candidate locations (grid-based search around target)
        candidates = self._generate_candidates(target_lat, target_lon)

        # Score each candidate
        scored_hotspots = []
        for lat, lon in candidates:
            hotspot = self._score_location(lat, lon, target_lat, target_lon, site_type)
            scored_hotspots.append(hotspot)

        # Sort by total score (descending)
        scored_hotspots.sort(key=lambda h: h.total_score, reverse=True)

        # Take top 3
        top_hotspots = scored_hotspots[:3]

        return OperatorAnalysis(
            incident_id=incident_id,
            target_latitude=target_lat,
            target_longitude=target_lon,
            predicted_hotspots=top_hotspots,
            search_radius_m=self.search_radius_m,
            perimeter_radius_m=self.perimeter_radius_m,
        )

    def _generate_candidates(self, target_lat: float, target_lon: float) -> List[Tuple[float, float]]:
        """Generate candidate operator locations around target.

        Uses a grid-based approach to sample locations at various distances and directions.

        Args:
            target_lat: Target latitude
            target_lon: Target longitude

        Returns:
            List of (lat, lon) tuples
        """
        candidates = []

        # Sample at different distances (in meters)
        distances = [200, 500, 1000, 1500, 2000, 2500, 3000, 3500, 4000]

        # Sample at different angles (in degrees, 0 = north)
        angles = [0, 45, 90, 135, 180, 225, 270, 315]

        for distance_m in distances:
            for angle_deg in angles:
                # Convert distance/bearing to lat/lon offset
                lat, lon = self._offset_location(target_lat, target_lon, distance_m, angle_deg)
                candidates.append((lat, lon))

        return candidates

    def _offset_location(
        self,
        lat: float,
        lon: float,
        distance_m: float,
        bearing_deg: float
    ) -> Tuple[float, float]:
        """Calculate new location at given distance and bearing.

        Args:
            lat: Starting latitude
            lon: Starting longitude
            distance_m: Distance in meters
            bearing_deg: Bearing in degrees (0 = north, 90 = east)

        Returns:
            (new_lat, new_lon)
        """
        # Earth radius in meters
        R = 6371000.0

        # Convert to radians
        lat_rad = math.radians(lat)
        lon_rad = math.radians(lon)
        bearing_rad = math.radians(bearing_deg)

        # Calculate new latitude
        new_lat_rad = math.asin(
            math.sin(lat_rad) * math.cos(distance_m / R) +
            math.cos(lat_rad) * math.sin(distance_m / R) * math.cos(bearing_rad)
        )

        # Calculate new longitude
        new_lon_rad = lon_rad + math.atan2(
            math.sin(bearing_rad) * math.sin(distance_m / R) * math.cos(lat_rad),
            math.cos(distance_m / R) - math.sin(lat_rad) * math.sin(new_lat_rad)
        )

        return math.degrees(new_lat_rad), math.degrees(new_lon_rad)

    def _score_location(
        self,
        lat: float,
        lon: float,
        target_lat: float,
        target_lon: float,
        site_type: Optional[str]
    ) -> OperatorHotspot:
        """Score a candidate location based on OPSEC-TTP rules.

        Args:
            lat: Candidate latitude
            lon: Candidate longitude
            target_lat: Target latitude
            target_lon: Target longitude
            site_type: Site type for perimeter estimation

        Returns:
            Scored OperatorHotspot
        """
        # Calculate distance to target
        distance_m = self._haversine_distance(lat, lon, target_lat, target_lon)

        # Score components
        cover_score = self._score_cover(lat, lon)
        distance_score = self._score_distance(distance_m)
        exfil_score = self._score_exfil(lat, lon)
        opsec_score = self._score_opsec(distance_m, site_type)
        terrain_score = self._score_terrain(lat, lon)

        # Calculate weighted composite score
        total_score = (
            self.weights["cover"] * cover_score +
            self.weights["distance"] * distance_score +
            self.weights["exfil"] * exfil_score +
            self.weights["opsec"] * opsec_score +
            self.weights["terrain"] * terrain_score
        )

        # Determine cover type and terrain suitability (mock for now)
        cover_type = self._infer_cover_type(lat, lon)
        terrain_suitability = self._infer_terrain_suitability(total_score)

        # Mock road data
        road_type = "secondary_road"
        road_distance = 50.0  # meters

        # Generate reasoning
        reasoning = self._generate_reasoning(
            distance_m, cover_score, exfil_score, opsec_score, cover_type
        )

        return OperatorHotspot(
            latitude=lat,
            longitude=lon,
            cover_score=cover_score,
            distance_score=distance_score,
            exfil_score=exfil_score,
            opsec_score=opsec_score,
            terrain_score=terrain_score,
            total_score=total_score,
            cover_type=cover_type,
            terrain_suitability=terrain_suitability,
            distance_to_target_m=distance_m,
            nearest_road_type=road_type,
            nearest_road_distance_m=road_distance,
            reasoning=reasoning,
        )

    def _score_cover(self, lat: float, lon: float) -> float:
        """Score cover/concealment quality at location.

        TODO: Integrate with terrain/land use data (OpenStreetMap, satellite imagery)

        Args:
            lat: Latitude
            lon: Longitude

        Returns:
            Cover score (0-1)
        """
        # Mock scoring based on lat/lon patterns
        # In production: query land use database, forest coverage, building density, etc.

        # Simple heuristic: vary score based on location hash
        location_hash = hash((round(lat, 4), round(lon, 4)))
        base_score = (location_hash % 100) / 100.0

        # Bias towards 0.4-0.8 range (most locations have some cover)
        return 0.4 + (base_score * 0.4)

    def _score_distance(self, distance_m: float) -> float:
        """Score distance from target (sweet spot: 500m - 2000m).

        Args:
            distance_m: Distance to target in meters

        Returns:
            Distance score (0-1)
        """
        # Penalty for too close (inside perimeter or easily detected)
        if distance_m < self.perimeter_radius_m:
            return 0.0  # Inside security perimeter = disqualified

        if distance_m < self.min_distance_m:
            return 0.2  # Too close, high detection risk

        # Sweet spot: 500m - 2000m (good balance of range and concealment)
        if 500 <= distance_m <= 2000:
            return 1.0

        # Gradual penalty for longer distances (signal degradation, harder control)
        if distance_m <= self.max_distance_m:
            # Linear decay from 2000m to 4000m: 1.0 -> 0.5
            return 1.0 - ((distance_m - 2000) / (self.max_distance_m - 2000)) * 0.5

        # Beyond max range: very low score
        return 0.1

    def _score_exfil(self, lat: float, lon: float) -> float:
        """Score exfiltration route quality.

        TODO: Integrate with road network data (OpenStreetMap)

        Args:
            lat: Latitude
            lon: Longitude

        Returns:
            Exfil score (0-1)
        """
        # Mock scoring
        # In production: calculate distance to nearest road, road type, multiple exit routes

        location_hash = hash((round(lat, 3), round(lon, 3)))
        base_score = (location_hash % 100) / 100.0

        # Most locations near roads in populated areas
        return 0.5 + (base_score * 0.5)

    def _score_opsec(self, distance_m: float, site_type: Optional[str]) -> float:
        """Score OPSEC compliance (outside perimeter, not in restricted area).

        Args:
            distance_m: Distance to target
            site_type: Site type (airport, military, etc.)

        Returns:
            OPSEC score (0-1)
        """
        # Critical rule: must be outside security perimeter
        if distance_m < self.perimeter_radius_m:
            return 0.0  # Absolute disqualifier

        # Adjust perimeter based on site type
        adjusted_perimeter = self.perimeter_radius_m
        if site_type in ["military", "airport"]:
            adjusted_perimeter = 1000.0  # Larger perimeter for high-security sites

        if distance_m < adjusted_perimeter:
            return 0.3  # Still too close to secure area

        # Good OPSEC compliance
        return 1.0

    def _score_terrain(self, lat: float, lon: float) -> float:
        """Score terrain suitability.

        TODO: Integrate with elevation data and line-of-sight analysis

        Args:
            lat: Latitude
            lon: Longitude

        Returns:
            Terrain score (0-1)
        """
        # Mock scoring
        # In production: check elevation, line of sight, terrain roughness

        location_hash = hash((round(lat, 5), round(lon, 5)))
        return (location_hash % 100) / 100.0

    def _infer_cover_type(self, lat: float, lon: float) -> CoverType:
        """Infer cover type at location.

        TODO: Integrate with land use database

        Args:
            lat: Latitude
            lon: Longitude

        Returns:
            CoverType
        """
        # Mock inference
        location_hash = hash((round(lat, 4), round(lon, 4)))
        cover_index = location_hash % 5

        cover_types = [
            CoverType.FOREST,
            CoverType.URBAN_BUILDING,
            CoverType.PARKING_LOT,
            CoverType.RURAL_STRUCTURE,
            CoverType.VEHICLE,
        ]

        return cover_types[cover_index]

    def _infer_terrain_suitability(self, total_score: float) -> TerrainSuitability:
        """Infer terrain suitability from composite score.

        Args:
            total_score: Total composite score

        Returns:
            TerrainSuitability
        """
        if total_score >= 0.8:
            return TerrainSuitability.EXCELLENT
        elif total_score >= 0.6:
            return TerrainSuitability.GOOD
        elif total_score >= 0.4:
            return TerrainSuitability.MODERATE
        elif total_score >= 0.2:
            return TerrainSuitability.POOR
        else:
            return TerrainSuitability.UNSUITABLE

    def _generate_reasoning(
        self,
        distance_m: float,
        cover_score: float,
        exfil_score: float,
        opsec_score: float,
        cover_type: CoverType
    ) -> str:
        """Generate human-readable reasoning for hotspot selection.

        Args:
            distance_m: Distance to target
            cover_score: Cover score
            exfil_score: Exfil score
            opsec_score: OPSEC score
            cover_type: Cover type

        Returns:
            Reasoning string
        """
        reasoning_parts = []

        # Distance reasoning
        if 500 <= distance_m <= 2000:
            reasoning_parts.append(f"Optimal distance ({distance_m:.0f}m) for drone control")
        elif distance_m > 2000:
            reasoning_parts.append(f"Moderate distance ({distance_m:.0f}m) - within drone range")
        else:
            reasoning_parts.append(f"Close distance ({distance_m:.0f}m) - high risk but doable")

        # Cover reasoning
        if cover_score >= 0.7:
            reasoning_parts.append(f"Excellent {cover_type.value} cover for concealment")
        elif cover_score >= 0.5:
            reasoning_parts.append(f"Good {cover_type.value} cover available")
        else:
            reasoning_parts.append(f"Limited {cover_type.value} cover - more exposed")

        # Exfil reasoning
        if exfil_score >= 0.7:
            reasoning_parts.append("Good road access for quick exfiltration")
        elif exfil_score >= 0.5:
            reasoning_parts.append("Moderate exfil routes available")
        else:
            reasoning_parts.append("Limited escape routes")

        # OPSEC reasoning
        if opsec_score == 1.0:
            reasoning_parts.append("Outside security perimeter - good OPSEC")
        elif opsec_score > 0:
            reasoning_parts.append("Marginal OPSEC compliance")
        else:
            reasoning_parts.append("OPSEC violation - inside restricted area")

        return ". ".join(reasoning_parts) + "."

    def _haversine_distance(
        self,
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float
    ) -> float:
        """Calculate haversine distance between two points.

        Args:
            lat1: Latitude of point 1
            lon1: Longitude of point 1
            lat2: Latitude of point 2
            lon2: Longitude of point 2

        Returns:
            Distance in meters
        """
        # Earth radius in meters
        R = 6371000.0

        # Convert to radians
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)

        # Haversine formula
        a = (
            math.sin(delta_lat / 2) ** 2 +
            math.cos(lat1_rad) * math.cos(lat2_rad) *
            math.sin(delta_lon / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return R * c


# Factory function for easy instantiation
def analyze_operator_location(
    incident_id: int,
    target_lat: float,
    target_lon: float,
    site_type: Optional[str] = None
) -> OperatorAnalysis:
    """Analyze incident and predict operator launch sites.

    Args:
        incident_id: ID of the incident
        target_lat: Target latitude
        target_lon: Target longitude
        site_type: Type of site (airport, military, etc.)

    Returns:
        OperatorAnalysis with 1-3 predicted hotspots
    """
    engine = OperatorHideoutEngine()
    return engine.analyze_incident(incident_id, target_lat, target_lon, site_type)
