"""Incidents API endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional, Any
from pydantic import BaseModel
from datetime import datetime
from backend.app.db.session import get_db
from backend.app.domain.incident import Incident
from backend.app.domain.evidence import Evidence
from backend.app.domain.site import Site
from backend.app.services.evidence_stack import build_evidence_stack, EvidenceStack
from backend.app.llm.evidence_enricher import enrich_incident, EnrichedIncident
from backend.app.services.operator_hideout import analyze_operator_location, OperatorAnalysis

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


class IntelligenceResponse(BaseModel):
    """Response schema for intelligence analysis."""
    incident: IncidentResponse
    evidence_stack: Any  # EvidenceStack (use Any to avoid circular imports)
    enriched_analysis: Any  # EnrichedIncident
    operator_analysis: Any  # OperatorAnalysis

    class Config:
        from_attributes = True


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
        IntelligenceResponse: Complete intelligence package

    Raises:
        HTTPException: 404 if incident not found
    """
    # 1. Get incident and verify it exists
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")

    # 2. Get site information for location
    site = None
    if incident.site_id:
        site = db.query(Site).filter(Site.id == incident.site_id).first()

    # Extract target location (from incident metadata or site)
    # For now, use mock coordinates if not available
    target_lat = 51.6  # Default: Netherlands center
    target_lon = 5.7
    site_type = None

    if site and site.geom_wkt:
        # Parse WKT point: "POINT(lon lat)"
        try:
            coords = site.geom_wkt.replace("POINT(", "").replace(")", "").split()
            target_lon = float(coords[0])
            target_lat = float(coords[1])
            site_type = site.type.value if site.type else None
        except:
            pass

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

    return IntelligenceResponse(
        incident=IncidentResponse.model_validate(incident),
        evidence_stack=evidence_stack.model_dump(),
        enriched_analysis=enriched_analysis.model_dump(),
        operator_analysis=operator_analysis.model_dump(),
    )
