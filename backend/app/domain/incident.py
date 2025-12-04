"""Incident domain model."""

from sqlalchemy import Column, Integer, String, TIMESTAMP, ForeignKey, JSON
from sqlalchemy.orm import relationship
from backend.app.db.base import Base


class Incident(Base):
    """
    Incident entity representing a drone sighting or CUAS event.

    Attributes:
        id: Primary key
        title: Incident title/description
        country_code: ISO 3166-1 alpha-2 country code
        site_id: Foreign key to Site (optional)
        occurred_at: When the incident happened (optional)
        raw_metadata: JSONB field for flexible metadata storage
    """

    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String, nullable=False, index=True)
    country_code = Column(String(2), index=True)  # e.g., "NL", "US", "GB"
    site_id = Column(Integer, ForeignKey("sites.id"), nullable=True, index=True)
    occurred_at = Column(TIMESTAMP(timezone=True), nullable=True, index=True)
    raw_metadata = Column(JSON, nullable=True)  # JSONB in PostgreSQL

    # Relationships
    site = relationship("Site", back_populates="incidents")
    evidence = relationship("Evidence", back_populates="incident", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Incident(id={self.id}, title='{self.title[:50]}...', country={self.country_code})>"
