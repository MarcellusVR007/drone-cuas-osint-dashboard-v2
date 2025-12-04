"""Incidents API endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from backend.app.db.session import get_db
from backend.app.domain.incident import Incident
from backend.app.domain.evidence import Evidence
from backend.app.domain.site import Site
from backend.app.services.evidence_stack import build_evidence_stack
from backend.app.llm.evidence_enricher import enrich_incident
from backend.app.services.operator_hideout import analyze_operator_location
from backend.app.api.schemas.intelligence import (
    IntelligenceResponse,
    IncidentSummary,
    DroneProfile,
    FlightDynamics,
    OperatorHotspot,
    EvidenceSummary,
    EvidenceItem,
    IntelligenceMeta,
)

router = APIRouter()


# Pydantic schemas for request/response
class IncidentResponse(BaseModel):
    """Response schema for Incident."""
    id: int
    title: str
    country_code: Optional[str] = None
    site_id: Optional[int] = None
    occurred_at: Optional[datetime] = None
    raw_metadata: Optional[dict] = None

    class Config:
        from_attributes = True  # Allow ORM model conversion


class IncidentListResponse(BaseModel):
    """Response schema for list of incidents."""
    total: int
    incidents: List[IncidentResponse]


@router.get("/incidents", response_model=IncidentListResponse)
def list_incidents(
    skip: int = 0,
    limit: int = 100,
    country_code: Optional[str] = None,
    db: Session = Depends(get_db)
) -> IncidentListResponse:
    """
    List incidents with optional filtering.

    Args:
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return
        country_code: Filter by country code (e.g., "NL")
        db: Database session (injected)

    Returns:
        IncidentListResponse: List of incidents with total count
    """
    query = db.query(Incident)

    # Apply filters
    if country_code:
        query = query.filter(Incident.country_code == country_code.upper())

    # Get total count
    total = query.count()

    # Get paginated results
    incidents = query.order_by(Incident.id.desc()).offset(skip).limit(limit).all()

    return IncidentListResponse(
        total=total,
        incidents=[IncidentResponse.model_validate(inc) for inc in incidents]
    )


@router.get("/incidents/{incident_id}", response_model=IncidentResponse)
def get_incident(incident_id: int, db: Session = Depends(get_db)) -> IncidentResponse:
    """
    Get a single incident by ID.

    Args:
        incident_id: Incident ID
        db: Database session (injected)

    Returns:
        IncidentResponse: Incident details

    Raises:
        HTTPException: 404 if incident not found
    """
    incident = db.query(Incident).filter(Incident.id == incident_id).first()

    if not incident:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")

    return IncidentResponse.model_validate(incident)


@router.get("/incidents/{incident_id}/intelligence", response_model=IntelligenceResponse)
def get_incident_intelligence(
    incident_id: int,
    db: Session = Depends(get_db)
) -> IntelligenceResponse:
    """
    Get comprehensive intelligence analysis for an incident.

    This endpoint combines:
    1. Evidence Stack: Aggregated and scored OSINT evidence
    2. LLM Enrichment: AI-extracted intelligence signals
    3. Operator Analysis: Predicted operator launch sites using OPSEC-TTP rules

    Args:
        incident_id: Incident ID
        db: Database session (injected)

    Returns:
        IntelligenceResponse: Complete intelligence package following explicit contract

    Raises:
        HTTPException: 404 if incident not found
    """
    # 1. Get incident and verify it exists
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")

    # 2. Get site information for location
    site = None
    location_name = None
    target_lat = None
    target_lon = None
    site_type = None

    if incident.site_id:
        site = db.query(Site).filter(Site.id == incident.site_id).first()
        if site:
            location_name = site.name
            site_type = site.type.value if site.type else None

            # Parse WKT point: "POINT(lon lat)"
            if site.geom_wkt:
                try:
                    coords = site.geom_wkt.replace("POINT(", "").replace(")", "").split()
                    target_lon = float(coords[0])
                    target_lat = float(coords[1])
                except:
                    pass

    # Fallback to default coordinates if no site location
    if target_lat is None:
        target_lat = 51.6
        target_lon = 5.7

    # 3. Build evidence stack
    evidence_records = db.query(Evidence).filter(Evidence.incident_id == incident_id).all()
    evidence_stack = build_evidence_stack(incident_id, evidence_records)

    # 4. LLM enrichment
    enriched_analysis = enrich_incident(incident_id, evidence_stack)

    # 5. Operator analysis
    operator_analysis = analyze_operator_location(
        incident_id=incident_id,
        target_lat=target_lat,
        target_lon=target_lon,
        site_type=site_type
    )

    # 6. Map to contract schemas

    # Incident summary
    incident_summary = IncidentSummary(
        id=incident.id,
        title=incident.title,
        location_name=location_name,
        country_code=incident.country_code,
        occurred_at=incident.occurred_at,
        latitude=target_lat,
        longitude=target_lon,
    )

    # Drone profile from LLM enrichment
    drone_types = [dt.value for dt in enriched_analysis.drone_type_signals]
    drone_profile = DroneProfile(
        type_primary=drone_types[0] if drone_types else "unknown",
        type_confidence=enriched_analysis.drone_type_confidence,
        type_alternatives=drone_types[1:] if len(drone_types) > 1 else [],
        lights_observed=enriched_analysis.lighting_conditions.lights_observed if enriched_analysis.lighting_conditions else False,
        light_pattern=enriched_analysis.lighting_conditions.light_pattern if enriched_analysis.lighting_conditions else None,
        summary=enriched_analysis.intelligence_summary,
    )

    # Flight dynamics from LLM enrichment
    flight_dynamics = FlightDynamics(
        approach_vector=enriched_analysis.flight_dynamics.approach_vector if enriched_analysis.flight_dynamics else None,
        exit_vector=enriched_analysis.flight_dynamics.exit_vector if enriched_analysis.flight_dynamics else None,
        pattern=enriched_analysis.flight_dynamics.flight_pattern if enriched_analysis.flight_dynamics else None,
        altitude_min_m=enriched_analysis.altitude_range.min_meters if enriched_analysis.altitude_range else None,
        altitude_max_m=enriched_analysis.altitude_range.max_meters if enriched_analysis.altitude_range else None,
        altitude_confidence=enriched_analysis.altitude_range.confidence if enriched_analysis.altitude_range else 0.0,
        speed_estimate=enriched_analysis.flight_dynamics.speed_estimate if enriched_analysis.flight_dynamics else None,
        maneuverability=enriched_analysis.flight_dynamics.maneuverability if enriched_analysis.flight_dynamics else None,
        summary=None,  # Can be generated later
    )

    # Operator hotspots
    operator_hotspots = [
        OperatorHotspot(
            rank=idx + 1,
            latitude=h.latitude,
            longitude=h.longitude,
            distance_to_target_m=h.distance_to_target_m,
            total_score=h.total_score,
            cover_score=h.cover_score,
            distance_score=h.distance_score,
            exfil_score=h.exfil_score,
            opsec_score=h.opsec_score,
            terrain_score=h.terrain_score,
            cover_type=h.cover_type.value,
            terrain_suitability=h.terrain_suitability.value,
            nearest_road_type=h.nearest_road_type,
            nearest_road_distance_m=h.nearest_road_distance_m,
            reasoning=h.reasoning,
        )
        for idx, h in enumerate(operator_analysis.predicted_hotspots)
    ]

    # Evidence summary
    evidence_summary = EvidenceSummary(
        total_items=evidence_stack.total_items,
        avg_credibility=evidence_stack.avg_credibility,
        duplicates_removed=evidence_stack.duplicates_removed,
        official_reports_count=len(evidence_stack.official_reports),
        news_articles_count=len(evidence_stack.news_articles),
        social_media_count=len(evidence_stack.social_media_posts),
        telegram_count=len(evidence_stack.telegram_messages),
        youtube_count=len(evidence_stack.youtube_videos),
        forum_posts_count=len(evidence_stack.forum_posts),
        witness_statements_count=len(evidence_stack.witness_statements),
        earliest_evidence=evidence_stack.earliest_evidence,
        latest_evidence=evidence_stack.latest_evidence,
    )

    # Evidence items (top 10 most credible)
    all_evidence_sorted = sorted(
        evidence_stack.all_items,
        key=lambda x: x.credibility_score,
        reverse=True
    )
    evidence_items = [
        EvidenceItem(
            source_id=item.source_id,
            source_type=item.source_type.value,
            source_name=item.source_name,
            url=item.source_id if item.source_id.startswith("http") else None,
            text_preview=item.text_content[:200] if len(item.text_content) > 200 else item.text_content,
            language=item.language,
            published_at=item.published_at,
            credibility_score=item.credibility_score,
            locality_score=item.locality_score,
            adversary_intent_score=item.adversary_intent_score,
        )
        for item in all_evidence_sorted[:10]
    ]

    # Meta
    meta = IntelligenceMeta(
        analyzed_at=enriched_analysis.enriched_at,
        llm_mode="mock" if enriched_analysis.llm_model == "mock" else "live",
        llm_model=enriched_analysis.llm_model if enriched_analysis.llm_model != "mock" else None,
        search_radius_m=operator_analysis.search_radius_m,
        perimeter_radius_m=operator_analysis.perimeter_radius_m,
    )

    return IntelligenceResponse(
        incident=incident_summary,
        drone_profile=drone_profile,
        flight_dynamics=flight_dynamics,
        operator_hotspots=operator_hotspots,
        evidence_summary=evidence_summary,
        evidence=evidence_items,
        meta=meta,
    )
