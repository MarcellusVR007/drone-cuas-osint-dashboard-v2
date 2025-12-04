"""Evidence Stack Builder - Aggregates and normalizes OSINT data for incidents.

This module collects, deduplicates, and scores all evidence related to an incident.
Evidence sources include: news articles, social media, Telegram, YouTube, forums, witness statements.

Architecture Layer: services/
Dependencies: domain.evidence, external OSINT APIs (future)
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class EvidenceSourceClassification(str, Enum):
    """Classification of evidence source reliability."""
    OFFICIAL_REPORT = "official_report"  # Government, military, airport authorities
    VERIFIED_NEWS = "verified_news"  # Established news outlets
    LOCAL_NEWS = "local_news"  # Regional news sources
    SOCIAL_MEDIA_VERIFIED = "social_media_verified"  # Verified accounts
    SOCIAL_MEDIA_UNVERIFIED = "social_media_unverified"  # Unverified accounts
    FORUM_POST = "forum_post"  # Forum discussions
    WITNESS_STATEMENT = "witness_statement"  # Direct eyewitness accounts
    TELEGRAM_CHANNEL = "telegram_channel"  # Telegram messages
    YOUTUBE_VIDEO = "youtube_video"  # YouTube content
    UNKNOWN = "unknown"


class EvidenceItem(BaseModel):
    """Single piece of evidence with scoring and metadata."""

    source_id: str = Field(..., description="Unique identifier for this evidence (URL or hash)")
    source_type: EvidenceSourceClassification
    source_name: str = Field(..., description="Name of source (e.g., 'NOS', 'Twitter User @foo')")

    # Content
    title: Optional[str] = None
    text_content: str = Field(..., description="Raw text content")
    language: str = Field(default="en", description="ISO 639-1 language code")

    # Temporal data
    published_at: Optional[datetime] = Field(None, description="When evidence was published")
    collected_at: datetime = Field(default_factory=datetime.utcnow, description="When we collected it")

    # Extracted signals
    geoloc_cues: List[str] = Field(default_factory=list, description="Geographic location mentions")
    temporal_cues: List[str] = Field(default_factory=list, description="Time-related mentions")

    # Scoring
    credibility_score: float = Field(default=0.5, ge=0.0, le=1.0, description="How credible is this source (0-1)")
    locality_score: float = Field(default=0.5, ge=0.0, le=1.0, description="How local/relevant is source (0-1)")
    adversary_intent_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Likelihood of adversarial info ops (0-1)")

    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata (hashtags, engagement, etc.)")


class EvidenceStack(BaseModel):
    """Aggregated and deduplicated evidence stack for an incident.

    This is the standardized output format for all OSINT data collection.
    """

    incident_id: int = Field(..., description="ID of the incident this stack belongs to")

    # Evidence items by category
    official_reports: List[EvidenceItem] = Field(default_factory=list)
    news_articles: List[EvidenceItem] = Field(default_factory=list)
    social_media_posts: List[EvidenceItem] = Field(default_factory=list)
    telegram_messages: List[EvidenceItem] = Field(default_factory=list)
    youtube_videos: List[EvidenceItem] = Field(default_factory=list)
    forum_posts: List[EvidenceItem] = Field(default_factory=list)
    witness_statements: List[EvidenceItem] = Field(default_factory=list)

    # Aggregate statistics
    total_items: int = Field(default=0, description="Total number of evidence items")
    duplicates_removed: int = Field(default=0, description="Number of duplicates filtered out")
    avg_credibility: float = Field(default=0.0, description="Average credibility score across all items")

    # Temporal bounds
    earliest_evidence: Optional[datetime] = Field(None, description="Earliest published evidence")
    latest_evidence: Optional[datetime] = Field(None, description="Latest published evidence")

    # Collection metadata
    collected_at: datetime = Field(default_factory=datetime.utcnow)

    @property
    def all_items(self) -> List[EvidenceItem]:
        """Return all evidence items combined."""
        return (
            self.official_reports +
            self.news_articles +
            self.social_media_posts +
            self.telegram_messages +
            self.youtube_videos +
            self.forum_posts +
            self.witness_statements
        )


class EvidenceStackBuilder:
    """Service for building evidence stacks from raw OSINT data.

    Responsibilities:
    - Collect evidence from database (Evidence model)
    - Extract temporal and geolocation cues
    - Calculate credibility, locality, and adversary intent scores
    - Deduplicate similar evidence
    - Aggregate into standardized EvidenceStack
    """

    def __init__(self):
        """Initialize the evidence stack builder."""
        # Future: Add OSINT API clients here (Twitter, Telegram, YouTube, etc.)
        pass

    def build_stack(
        self,
        incident_id: int,
        evidence_records: List[Any]  # List[Evidence] from domain
    ) -> EvidenceStack:
        """Build evidence stack from database evidence records.

        Args:
            incident_id: ID of the incident
            evidence_records: List of Evidence ORM objects from database

        Returns:
            EvidenceStack with categorized and scored evidence
        """
        stack = EvidenceStack(incident_id=incident_id)
        seen_sources = set()  # For deduplication

        for record in evidence_records:
            # Deduplicate by URL or content hash
            source_id = record.url or f"hash_{hash(record.raw_text)}"
            if source_id in seen_sources:
                stack.duplicates_removed += 1
                continue
            seen_sources.add(source_id)

            # Create evidence item
            item = self._create_evidence_item(record)

            # Categorize by source type
            self._categorize_item(stack, item)

        # Calculate aggregate statistics
        self._calculate_statistics(stack)

        return stack

    def _create_evidence_item(self, record: Any) -> EvidenceItem:
        """Convert database Evidence record to EvidenceItem with scoring.

        Args:
            record: Evidence ORM object

        Returns:
            Scored EvidenceItem
        """
        # Map source_type enum to classification
        classification = self._classify_source(record.source_type, record.source_name)

        # Extract cues from text
        geoloc_cues = self._extract_geoloc_cues(record.raw_text or "")
        temporal_cues = self._extract_temporal_cues(record.raw_text or "")

        # Calculate scores
        credibility = self._calculate_credibility(classification, record.source_name)
        locality = self._calculate_locality(record.source_name, geoloc_cues)
        adversary_intent = self._calculate_adversary_intent(record.raw_text or "", record.source_name)

        return EvidenceItem(
            source_id=record.url or f"evidence_{record.id}",
            source_type=classification,
            source_name=record.source_name or "Unknown",
            title=None,  # Future: extract from metadata
            text_content=record.raw_text or "",
            language=record.language or "en",
            published_at=record.published_at,
            collected_at=datetime.utcnow(),
            geoloc_cues=geoloc_cues,
            temporal_cues=temporal_cues,
            credibility_score=credibility,
            locality_score=locality,
            adversary_intent_score=adversary_intent,
            metadata=record.meta or {}
        )

    def _classify_source(self, source_type: str, source_name: Optional[str]) -> EvidenceSourceClassification:
        """Classify evidence source into reliability category.

        Args:
            source_type: Source type from Evidence.source_type enum
            source_name: Name of the source

        Returns:
            EvidenceSourceClassification
        """
        # Map Evidence.SourceType to EvidenceSourceClassification
        type_map = {
            "official_report": EvidenceSourceClassification.OFFICIAL_REPORT,
            "news": EvidenceSourceClassification.VERIFIED_NEWS,
            "social_media": EvidenceSourceClassification.SOCIAL_MEDIA_UNVERIFIED,
            "telegram": EvidenceSourceClassification.TELEGRAM_CHANNEL,
            "reddit": EvidenceSourceClassification.FORUM_POST,
            "forum": EvidenceSourceClassification.FORUM_POST,
        }

        classification = type_map.get(source_type, EvidenceSourceClassification.UNKNOWN)

        # Upgrade classification based on source name
        if source_name and classification == EvidenceSourceClassification.VERIFIED_NEWS:
            # Check if it's a local news source
            local_indicators = ["lokaal", "local", "regional", "gemeente"]
            if any(indicator in source_name.lower() for indicator in local_indicators):
                classification = EvidenceSourceClassification.LOCAL_NEWS

        return classification

    def _extract_geoloc_cues(self, text: str) -> List[str]:
        """Extract geographic location cues from text.

        Args:
            text: Raw text content

        Returns:
            List of location mentions
        """
        # Simple keyword extraction (Future: use NER)
        geoloc_keywords = []

        # Dutch/English location indicators
        location_indicators = [
            "airport", "luchthaven", "base", "basis",
            "near", "bij", "vlakbij", "nabij",
            "kilometers from", "km van"
        ]

        text_lower = text.lower()
        for indicator in location_indicators:
            if indicator in text_lower:
                # Extract context around indicator (simple implementation)
                idx = text_lower.index(indicator)
                context = text[max(0, idx-20):min(len(text), idx+50)]
                geoloc_keywords.append(context.strip())

        return geoloc_keywords[:5]  # Limit to top 5

    def _extract_temporal_cues(self, text: str) -> List[str]:
        """Extract temporal cues from text.

        Args:
            text: Raw text content

        Returns:
            List of time-related mentions
        """
        temporal_keywords = []

        # Temporal indicators
        time_indicators = [
            "night", "nacht", "evening", "avond",
            "morning", "ochtend", "afternoon", "middag",
            "yesterday", "gisteren", "today", "vandaag",
            "at", "om", "around", "ongeveer"
        ]

        text_lower = text.lower()
        for indicator in time_indicators:
            if indicator in text_lower:
                idx = text_lower.index(indicator)
                context = text[max(0, idx-10):min(len(text), idx+30)]
                temporal_keywords.append(context.strip())

        return temporal_keywords[:5]

    def _calculate_credibility(self, classification: EvidenceSourceClassification, source_name: str) -> float:
        """Calculate credibility score based on source classification.

        Args:
            classification: Source classification
            source_name: Name of the source

        Returns:
            Credibility score (0-1)
        """
        # Base credibility by classification
        credibility_map = {
            EvidenceSourceClassification.OFFICIAL_REPORT: 0.95,
            EvidenceSourceClassification.VERIFIED_NEWS: 0.85,
            EvidenceSourceClassification.LOCAL_NEWS: 0.80,
            EvidenceSourceClassification.SOCIAL_MEDIA_VERIFIED: 0.70,
            EvidenceSourceClassification.WITNESS_STATEMENT: 0.65,
            EvidenceSourceClassification.TELEGRAM_CHANNEL: 0.55,
            EvidenceSourceClassification.FORUM_POST: 0.50,
            EvidenceSourceClassification.SOCIAL_MEDIA_UNVERIFIED: 0.40,
            EvidenceSourceClassification.YOUTUBE_VIDEO: 0.45,
            EvidenceSourceClassification.UNKNOWN: 0.30,
        }

        return credibility_map.get(classification, 0.5)

    def _calculate_locality(self, source_name: str, geoloc_cues: List[str]) -> float:
        """Calculate locality/relevance score.

        Args:
            source_name: Name of the source
            geoloc_cues: Extracted geographic cues

        Returns:
            Locality score (0-1)
        """
        score = 0.5  # Base score

        # Boost if source is local
        if source_name:
            local_indicators = ["local", "lokaal", "regional", "gemeente"]
            if any(indicator in source_name.lower() for indicator in local_indicators):
                score += 0.3

        # Boost if geographic cues are present
        if geoloc_cues:
            score += 0.2

        return min(1.0, score)

    def _calculate_adversary_intent(self, text: str, source_name: str) -> float:
        """Calculate adversarial information operations likelihood.

        Args:
            text: Raw text content
            source_name: Name of the source

        Returns:
            Adversary intent score (0-1, higher = more likely adversarial)
        """
        score = 0.0

        # Red flags for info ops
        disinfo_indicators = [
            "hoax", "fake", "false flag", "conspiracy",
            "coverup", "cover-up", "government lies",
            "mainstream media", "msm", "propaganda"
        ]

        text_lower = text.lower()
        for indicator in disinfo_indicators:
            if indicator in text_lower:
                score += 0.15

        # Check source name for suspicious patterns
        if source_name:
            suspicious_patterns = ["anon", "truth", "patriot", "awakened", "woke"]
            for pattern in suspicious_patterns:
                if pattern in source_name.lower():
                    score += 0.10

        return min(1.0, score)

    def _categorize_item(self, stack: EvidenceStack, item: EvidenceItem) -> None:
        """Categorize evidence item into appropriate stack category.

        Args:
            stack: EvidenceStack to add item to
            item: EvidenceItem to categorize
        """
        category_map = {
            EvidenceSourceClassification.OFFICIAL_REPORT: stack.official_reports,
            EvidenceSourceClassification.VERIFIED_NEWS: stack.news_articles,
            EvidenceSourceClassification.LOCAL_NEWS: stack.news_articles,
            EvidenceSourceClassification.SOCIAL_MEDIA_VERIFIED: stack.social_media_posts,
            EvidenceSourceClassification.SOCIAL_MEDIA_UNVERIFIED: stack.social_media_posts,
            EvidenceSourceClassification.TELEGRAM_CHANNEL: stack.telegram_messages,
            EvidenceSourceClassification.YOUTUBE_VIDEO: stack.youtube_videos,
            EvidenceSourceClassification.FORUM_POST: stack.forum_posts,
            EvidenceSourceClassification.WITNESS_STATEMENT: stack.witness_statements,
        }

        category = category_map.get(item.source_type, stack.news_articles)
        category.append(item)

    def _calculate_statistics(self, stack: EvidenceStack) -> None:
        """Calculate aggregate statistics for evidence stack.

        Args:
            stack: EvidenceStack to calculate statistics for
        """
        all_items = stack.all_items
        stack.total_items = len(all_items)

        if all_items:
            # Average credibility
            stack.avg_credibility = sum(item.credibility_score for item in all_items) / len(all_items)

            # Temporal bounds
            published_dates = [item.published_at for item in all_items if item.published_at]
            if published_dates:
                stack.earliest_evidence = min(published_dates)
                stack.latest_evidence = max(published_dates)


# Factory function for easy instantiation
def build_evidence_stack(incident_id: int, evidence_records: List[Any]) -> EvidenceStack:
    """Build evidence stack for an incident.

    Args:
        incident_id: ID of the incident
        evidence_records: List of Evidence ORM objects

    Returns:
        EvidenceStack with all evidence categorized and scored
    """
    builder = EvidenceStackBuilder()
    return builder.build_stack(incident_id, evidence_records)
