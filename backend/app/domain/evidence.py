"""Evidence domain model."""

from sqlalchemy import Column, Integer, String, Enum, ForeignKey, TIMESTAMP, JSON
from sqlalchemy.orm import relationship
from backend.app.db.base import Base
import enum


class SourceType(str, enum.Enum):
    """Evidence source type enumeration."""
    NEWS = "news"
    SOCIAL_MEDIA = "social_media"
    OFFICIAL_REPORT = "official_report"
    FORUM = "forum"
    TELEGRAM = "telegram"
    REDDIT = "reddit"
    OTHER = "other"


class Evidence(Base):
    """
    Evidence entity representing a source document/article for an incident.

    Attributes:
        id: Primary key
        incident_id: Foreign key to Incident
        source_type: Type of source from SourceType enum
        source_name: Name of source (e.g., "Reuters", "Twitter")
        url: URL to original source
        language: ISO 639-1 language code (e.g., "en", "nl")
        published_at: When the evidence was published
        raw_text: Raw text content from source
        meta: JSONB field for flexible metadata storage
    """

    __tablename__ = "evidence"

    id = Column(Integer, primary_key=True, autoincrement=True)
    incident_id = Column(Integer, ForeignKey("incidents.id"), nullable=False, index=True)
    source_type = Column(Enum(SourceType), nullable=False, index=True)
    source_name = Column(String, nullable=True)  # e.g., "Reuters", "Twitter"
    url = Column(String, nullable=True, index=True)
    language = Column(String(2), nullable=True)  # ISO 639-1 code: "en", "nl"
    published_at = Column(TIMESTAMP(timezone=True), nullable=True, index=True)
    raw_text = Column(String, nullable=True)  # Full article text
    meta = Column(JSON, nullable=True)  # JSONB in PostgreSQL

    # Relationships
    incident = relationship("Incident", back_populates="evidence")

    def __repr__(self) -> str:
        return f"<Evidence(id={self.id}, incident_id={self.incident_id}, source={self.source_type.value})>"
