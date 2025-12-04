"""Incidents API endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from backend.app.db.session import get_db
from backend.app.domain.incident import Incident

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
