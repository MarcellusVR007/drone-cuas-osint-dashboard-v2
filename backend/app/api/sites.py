"""Sites API endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from backend.app.db.session import get_db
from backend.app.domain.site import Site, SiteType

router = APIRouter()


# Pydantic schemas for request/response
class SiteResponse(BaseModel):
    """Response schema for Site."""
    id: int
    name: str
    type: SiteType
    country_code: Optional[str] = None
    geom_wkt: Optional[str] = None
    metadata: Optional[dict] = None

    class Config:
        from_attributes = True  # Allow ORM model conversion


class SiteListResponse(BaseModel):
    """Response schema for list of sites."""
    total: int
    sites: List[SiteResponse]


@router.get("/sites", response_model=SiteListResponse)
def list_sites(
    skip: int = 0,
    limit: int = 100,
    site_type: Optional[SiteType] = None,
    country_code: Optional[str] = None,
    db: Session = Depends(get_db)
) -> SiteListResponse:
    """
    List sites with optional filtering.

    Args:
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return
        site_type: Filter by site type (e.g., "military", "airport")
        country_code: Filter by country code (e.g., "NL")
        db: Database session (injected)

    Returns:
        SiteListResponse: List of sites with total count
    """
    query = db.query(Site)

    # Apply filters
    if site_type:
        query = query.filter(Site.type == site_type)
    if country_code:
        query = query.filter(Site.country_code == country_code.upper())

    # Get total count
    total = query.count()

    # Get paginated results
    sites = query.order_by(Site.name).offset(skip).limit(limit).all()

    return SiteListResponse(
        total=total,
        sites=[SiteResponse.model_validate(site) for site in sites]
    )
