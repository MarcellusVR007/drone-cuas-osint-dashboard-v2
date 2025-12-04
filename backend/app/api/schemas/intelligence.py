"""Intelligence API contract - Pydantic schemas for /incidents/{id}/intelligence endpoint.

This module defines the EXPLICIT JSON contract for the intelligence endpoint,
designed to perfectly match the tactical detail page requirements.
"""

from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


# === INCIDENT SUMMARY ===

class IncidentSummary(BaseModel):
    """Basic incident information."""
    id: int
    title: str
    location_name: Optional[str] = None
    country_code: Optional[str] = None
    occurred_at: Optional[datetime] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


# === DRONE PROFILE ===

class DroneProfile(BaseModel):
    """Analyzed drone characteristics."""
    type_primary: str = Field(default="unknown", description="Primary drone type classification")
    type_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    type_alternatives: List[str] = Field(default_factory=list, description="Alternative drone types")

    # Physical characteristics
    size_estimate: Optional[str] = Field(None, description="small/medium/large/unknown")
    sound_signature: Optional[str] = Field(None, description="Description of sound if mentioned")
    visual_description: Optional[str] = Field(None, description="Visual appearance from eyewitnesses")

    # Lighting
    lights_observed: bool = Field(default=False)
    light_pattern: Optional[str] = Field(None, description="Navigation lights pattern")

    # Summary
    summary: Optional[str] = Field(None, description="Natural language summary of drone profile")


# === FLIGHT DYNAMICS ===

class FlightDynamics(BaseModel):
    """Flight behavior and trajectory."""
    # Vectors
    approach_vector: Optional[str] = Field(None, description="Direction of approach (e.g., 'from northwest')")
    exit_vector: Optional[str] = Field(None, description="Direction of exit")

    # Flight pattern
    pattern: Optional[str] = Field(None, description="hovering/circling/straight_line/erratic/unknown")
    altitude_min_m: Optional[int] = Field(None, description="Minimum estimated altitude in meters")
    altitude_max_m: Optional[int] = Field(None, description="Maximum estimated altitude in meters")
    altitude_confidence: float = Field(default=0.0, ge=0.0, le=1.0)

    # Speed and maneuverability
    speed_estimate: Optional[str] = Field(None, description="slow/moderate/fast/unknown")
    maneuverability: Optional[str] = Field(None, description="agile/steady/erratic/unknown")

    # Duration
    duration_seconds: Optional[int] = Field(None, description="How long the drone was observed")

    # Summary
    summary: Optional[str] = Field(None, description="Natural language summary of flight dynamics")


# === OPERATOR HOTSPOT ===

class OperatorHotspot(BaseModel):
    """Predicted operator launch site."""
    rank: int = Field(..., description="Ranking (1 = most likely)")
    latitude: float
    longitude: float
    distance_to_target_m: float

    # Composite score
    total_score: float = Field(..., ge=0.0, le=1.0)

    # Score breakdown
    cover_score: float = Field(..., ge=0.0, le=1.0)
    distance_score: float = Field(..., ge=0.0, le=1.0)
    exfil_score: float = Field(..., ge=0.0, le=1.0)
    opsec_score: float = Field(..., ge=0.0, le=1.0)
    terrain_score: float = Field(..., ge=0.0, le=1.0)

    # Details
    cover_type: str = Field(default="unknown", description="forest/urban_building/parking_lot/rural_structure/vehicle/open_field")
    terrain_suitability: str = Field(default="moderate", description="excellent/good/moderate/poor/unsuitable")
    nearest_road_type: Optional[str] = None
    nearest_road_distance_m: Optional[float] = None

    # Reasoning
    reasoning: str = Field(..., description="Human-readable explanation")


# === EVIDENCE ===

class EvidenceItem(BaseModel):
    """Single piece of evidence."""
    source_id: str
    source_type: str = Field(..., description="verified_news/local_news/social_media/telegram/reddit/official_report/etc")
    source_name: str
    url: Optional[str] = None

    # Content
    text_preview: str = Field(..., description="First 200 chars of content")
    language: str = "en"
    published_at: Optional[datetime] = None

    # Scoring
    credibility_score: float = Field(..., ge=0.0, le=1.0)
    locality_score: float = Field(..., ge=0.0, le=1.0)
    adversary_intent_score: float = Field(..., ge=0.0, le=1.0)


class EvidenceSummary(BaseModel):
    """Evidence collection statistics."""
    total_items: int = 0
    avg_credibility: float = 0.0
    duplicates_removed: int = 0

    # Breakdown by source type
    official_reports_count: int = 0
    news_articles_count: int = 0
    social_media_count: int = 0
    telegram_count: int = 0
    youtube_count: int = 0
    forum_posts_count: int = 0
    witness_statements_count: int = 0

    # Temporal bounds
    earliest_evidence: Optional[datetime] = None
    latest_evidence: Optional[datetime] = None


# === METADATA ===

class IntelligenceMeta(BaseModel):
    """Metadata about the intelligence analysis."""
    analyzed_at: datetime = Field(default_factory=datetime.utcnow)
    llm_mode: str = Field(default="mock", description="mock/live")
    llm_model: Optional[str] = None
    search_radius_m: float = Field(default=4000.0)
    perimeter_radius_m: float = Field(default=500.0)


# === TOP-LEVEL RESPONSE ===

class IntelligenceResponse(BaseModel):
    """Complete intelligence analysis response.

    This is the explicit contract for GET /incidents/{id}/intelligence
    matching the tactical detail page requirements.
    """
    # Incident basic info
    incident: IncidentSummary

    # Drone analysis (from LLM enrichment)
    drone_profile: DroneProfile
    flight_dynamics: FlightDynamics

    # Operator analysis (from hideout engine)
    operator_hotspots: List[OperatorHotspot]

    # Evidence (from evidence stack)
    evidence_summary: EvidenceSummary
    evidence: List[EvidenceItem]  # Top N most credible items

    # Metadata
    meta: IntelligenceMeta

    class Config:
        from_attributes = True
