"""Site domain model."""

from sqlalchemy import Column, Integer, String, Enum, JSON
from sqlalchemy.orm import relationship
from backend.app.db.base import Base
import enum


class SiteType(str, enum.Enum):
    """Site type enumeration."""
    AIRPORT = "airport"
    MILITARY = "military"
    POWER_PLANT = "power_plant"
    GOVERNMENT = "government"
    PRISON = "prison"
    STADIUM = "stadium"
    CRITICAL_INFRASTRUCTURE = "critical_infrastructure"
    OTHER = "other"


class Site(Base):
    """
    Site entity representing a location of interest (military base, airport, etc.).

    Attributes:
        id: Primary key
        name: Site name (e.g., "Volkel Air Base")
        type: Site type from SiteType enum
        country_code: ISO 3166-1 alpha-2 country code
        geom_wkt: Geometry as WKT string (Point, Polygon, etc.)
        site_metadata: JSONB field for flexible metadata storage
    """

    __tablename__ = "sites"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False, index=True)
    type = Column(Enum(SiteType), nullable=False, index=True)
    country_code = Column(String(2), index=True)  # e.g., "NL", "US", "GB"
    geom_wkt = Column(String, nullable=True)  # WKT format: "POINT(5.7 51.6)"
    site_metadata = Column(JSON, nullable=True)  # JSONB in PostgreSQL (renamed from 'metadata' which is reserved)

    # Relationships
    incidents = relationship("Incident", back_populates="site")

    def __repr__(self) -> str:
        return f"<Site(id={self.id}, name='{self.name}', type={self.type.value})>"
