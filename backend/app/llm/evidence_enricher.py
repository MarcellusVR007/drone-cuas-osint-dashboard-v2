"""LLM Evidence Enrichment - Extracts intelligence signals from OSINT evidence.

This module uses LLM analysis to extract structured intelligence from raw evidence:
- Drone type signals and flight characteristics
- Flight dynamics (approach/exit vectors)
- Altitude range estimation
- Lighting conditions inference
- Eyewitness conflict resolution

Architecture Layer: llm/
Dependencies: services.evidence_stack, Anthropic Claude API
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum
import os
import json


class DroneTypeSignal(str, Enum):
    """Drone type classification from evidence."""
    CONSUMER_DJI = "consumer_dji"  # DJI Phantom, Mavic, etc.
    CONSUMER_OTHER = "consumer_other"  # Autel, Parrot, etc.
    RACING_FPV = "racing_fpv"  # Racing/FPV drones
    MILITARY_SMALL = "military_small"  # Small tactical UAS
    MILITARY_MEDIUM = "military_medium"  # Medium tactical UAS (e.g., Switchblade)
    DIY_CUSTOM = "diy_custom"  # Custom-built drones
    COMMERCIAL = "commercial"  # Industrial/commercial drones
    UNKNOWN = "unknown"


class FlightDynamics(BaseModel):
    """Flight characteristics and behavior."""
    approach_vector: Optional[str] = Field(None, description="Inferred approach direction (e.g., 'from northwest')")
    exit_vector: Optional[str] = Field(None, description="Inferred exit direction")
    flight_pattern: Optional[str] = Field(None, description="Observed pattern (hovering, circling, straight line, etc.)")
    speed_estimate: Optional[str] = Field(None, description="Speed description (slow, moderate, fast)")
    maneuverability: Optional[str] = Field(None, description="Maneuverability assessment (agile, steady, erratic)")


class AltitudeRange(BaseModel):
    """Estimated altitude from evidence."""
    min_meters: Optional[int] = Field(None, description="Minimum estimated altitude in meters")
    max_meters: Optional[int] = Field(None, description="Maximum estimated altitude in meters")
    confidence: float = Field(default=0.5, ge=0.0, le=1.0, description="Confidence in altitude estimate")
    reasoning: Optional[str] = Field(None, description="Basis for altitude estimate")


class LightingConditions(BaseModel):
    """Lighting and visibility conditions."""
    time_of_day: Optional[str] = Field(None, description="Dawn, day, dusk, night")
    visibility: Optional[str] = Field(None, description="Clear, cloudy, foggy, etc.")
    lights_observed: bool = Field(default=False, description="Were lights/strobes observed?")
    light_pattern: Optional[str] = Field(None, description="Description of light pattern if observed")


class EyewitnessConflicts(BaseModel):
    """Resolution of conflicting eyewitness accounts."""
    has_conflicts: bool = Field(default=False, description="Were there conflicting accounts?")
    conflict_areas: List[str] = Field(default_factory=list, description="Areas of disagreement")
    resolved_consensus: Optional[str] = Field(None, description="LLM-resolved consensus if possible")
    confidence: float = Field(default=0.5, ge=0.0, le=1.0, description="Confidence in resolution")


class EnrichedIncident(BaseModel):
    """LLM-enriched incident with extracted intelligence signals.

    This is the output of LLM analysis on an evidence stack.
    """
    incident_id: int

    # Extracted signals
    drone_type_signals: List[DroneTypeSignal] = Field(default_factory=list, description="Possible drone types")
    drone_type_confidence: float = Field(default=0.0, ge=0.0, le=1.0)

    flight_dynamics: Optional[FlightDynamics] = None
    altitude_range: Optional[AltitudeRange] = None
    lighting_conditions: Optional[LightingConditions] = None
    eyewitness_conflicts: Optional[EyewitnessConflicts] = None

    # Summary
    intelligence_summary: str = Field(..., description="Natural language summary of findings")
    key_findings: List[str] = Field(default_factory=list, description="Bullet point findings")

    # Metadata
    enriched_at: datetime = Field(default_factory=datetime.utcnow)
    llm_model: str = Field(default="claude-3-5-sonnet-20241022")
    total_evidence_analyzed: int = Field(default=0)


class EvidenceEnricher:
    """Service for enriching incidents with LLM-extracted intelligence.

    Uses Anthropic Claude API with structured prompting and anti-hallucination measures.
    """

    def __init__(self, api_key: Optional[str] = None):
        """Initialize the evidence enricher.

        Args:
            api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var)
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.model = "claude-3-5-sonnet-20241022"

        # Import Anthropic client only if API key is available
        if self.api_key:
            try:
                from anthropic import Anthropic
                self.client = Anthropic(api_key=self.api_key)
            except ImportError:
                self.client = None
        else:
            self.client = None

    def enrich_incident(
        self,
        incident_id: int,
        evidence_stack: Any,  # EvidenceStack from services.evidence_stack
    ) -> EnrichedIncident:
        """Enrich incident with LLM analysis of evidence stack.

        Args:
            incident_id: ID of the incident
            evidence_stack: EvidenceStack with all collected evidence

        Returns:
            EnrichedIncident with extracted intelligence signals
        """
        # If no LLM client available, return mock enrichment
        if not self.client:
            return self._mock_enrichment(incident_id, evidence_stack)

        # Build prompt from evidence stack
        prompt = self._build_analysis_prompt(evidence_stack)

        # Call LLM with function calling schema
        response = self._call_llm(prompt)

        # Parse structured response
        enriched = self._parse_llm_response(incident_id, response, evidence_stack)

        return enriched

    def _build_analysis_prompt(self, evidence_stack: Any) -> str:
        """Build analysis prompt from evidence stack.

        Args:
            evidence_stack: EvidenceStack with all evidence

        Returns:
            Structured prompt for LLM
        """
        all_items = evidence_stack.all_items

        # Group evidence by source type for clarity
        evidence_by_type = {
            "official_reports": evidence_stack.official_reports,
            "news_articles": evidence_stack.news_articles,
            "social_media": evidence_stack.social_media_posts,
            "telegram": evidence_stack.telegram_messages,
            "youtube": evidence_stack.youtube_videos,
            "forums": evidence_stack.forum_posts,
            "witnesses": evidence_stack.witness_statements,
        }

        prompt = f"""You are an intelligence analyst specializing in drone/UAS incident analysis. Analyze the following OSINT evidence and extract structured intelligence signals.

INCIDENT ID: {evidence_stack.incident_id}
TOTAL EVIDENCE ITEMS: {evidence_stack.total_items}
AVERAGE CREDIBILITY: {evidence_stack.avg_credibility:.2f}

EVIDENCE BY SOURCE TYPE:
"""

        for source_type, items in evidence_by_type.items():
            if items:
                prompt += f"\n### {source_type.upper()} ({len(items)} items):\n"
                for idx, item in enumerate(items, 1):
                    prompt += f"\n{idx}. SOURCE: {item.source_name} (credibility: {item.credibility_score:.2f})\n"
                    prompt += f"   PUBLISHED: {item.published_at or 'unknown'}\n"
                    prompt += f"   TEXT: {item.text_content[:500]}...\n"
                    if item.geoloc_cues:
                        prompt += f"   LOCATION CUES: {', '.join(item.geoloc_cues)}\n"
                    if item.temporal_cues:
                        prompt += f"   TIME CUES: {', '.join(item.temporal_cues)}\n"

        prompt += """

ANALYSIS TASKS:

1. DRONE TYPE SIGNALS
   - What type of drone is most likely based on evidence?
   - Consider: size descriptions, sound descriptions, flight characteristics, lighting
   - Provide confidence score (0-1)

2. FLIGHT DYNAMICS
   - Approach direction (if mentioned)
   - Exit direction (if mentioned)
   - Flight pattern (hovering, circling, straight line, etc.)
   - Speed estimate (slow, moderate, fast)
   - Maneuverability (agile, steady, erratic)

3. ALTITUDE RANGE
   - Estimate minimum and maximum altitude in meters
   - Provide reasoning based on evidence (visual angle, sound loudness, etc.)
   - Confidence score (0-1)

4. LIGHTING CONDITIONS
   - Time of day (dawn, day, dusk, night)
   - Visibility conditions
   - Were lights/strobes observed?
   - Light pattern description

5. EYEWITNESS CONFLICTS
   - Are there conflicting accounts between different witnesses?
   - What are the areas of disagreement?
   - Can you resolve to a consensus view?
   - Confidence in resolution

ANTI-HALLUCINATION RULES:
- ONLY extract information that is explicitly stated or strongly implied in the evidence
- Mark uncertainty clearly when evidence is ambiguous
- Do NOT invent details not present in the evidence
- If conflicting accounts exist, acknowledge them rather than forcing consensus
- Use lower confidence scores when evidence is weak or contradictory

OUTPUT FORMAT: Return a JSON object with the structure matching the EnrichedIncident schema.
"""

        return prompt

    def _call_llm(self, prompt: str) -> Dict[str, Any]:
        """Call LLM API with structured prompting.

        Args:
            prompt: Analysis prompt

        Returns:
            LLM response as dictionary
        """
        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                temperature=0.0,  # Low temperature for factual extraction
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            # Extract text content
            response_text = message.content[0].text

            # Try to parse as JSON
            try:
                return json.loads(response_text)
            except json.JSONDecodeError:
                # If not valid JSON, return as text
                return {"raw_text": response_text}

        except Exception as e:
            # Fallback: return error
            return {"error": str(e)}

    def _parse_llm_response(
        self,
        incident_id: int,
        response: Dict[str, Any],
        evidence_stack: Any
    ) -> EnrichedIncident:
        """Parse LLM response into EnrichedIncident.

        Args:
            incident_id: Incident ID
            response: LLM response dictionary
            evidence_stack: Original evidence stack

        Returns:
            EnrichedIncident
        """
        # Handle error responses
        if "error" in response:
            return EnrichedIncident(
                incident_id=incident_id,
                intelligence_summary=f"LLM enrichment failed: {response['error']}",
                key_findings=["Analysis unavailable due to LLM error"],
                total_evidence_analyzed=evidence_stack.total_items
            )

        # Parse drone type signals
        drone_types = []
        if "drone_type_signals" in response:
            for signal in response["drone_type_signals"]:
                try:
                    drone_types.append(DroneTypeSignal(signal))
                except ValueError:
                    pass

        # Parse flight dynamics
        flight_dynamics = None
        if "flight_dynamics" in response and response["flight_dynamics"]:
            flight_dynamics = FlightDynamics(**response["flight_dynamics"])

        # Parse altitude range
        altitude_range = None
        if "altitude_range" in response and response["altitude_range"]:
            altitude_range = AltitudeRange(**response["altitude_range"])

        # Parse lighting conditions
        lighting = None
        if "lighting_conditions" in response and response["lighting_conditions"]:
            lighting = LightingConditions(**response["lighting_conditions"])

        # Parse eyewitness conflicts
        conflicts = None
        if "eyewitness_conflicts" in response and response["eyewitness_conflicts"]:
            conflicts = EyewitnessConflicts(**response["eyewitness_conflicts"])

        return EnrichedIncident(
            incident_id=incident_id,
            drone_type_signals=drone_types,
            drone_type_confidence=response.get("drone_type_confidence", 0.0),
            flight_dynamics=flight_dynamics,
            altitude_range=altitude_range,
            lighting_conditions=lighting,
            eyewitness_conflicts=conflicts,
            intelligence_summary=response.get("intelligence_summary", "No summary available"),
            key_findings=response.get("key_findings", []),
            total_evidence_analyzed=evidence_stack.total_items,
            llm_model=self.model
        )

    def _mock_enrichment(self, incident_id: int, evidence_stack: Any) -> EnrichedIncident:
        """Create mock enrichment when LLM is unavailable.

        Args:
            incident_id: Incident ID
            evidence_stack: Evidence stack

        Returns:
            Mock EnrichedIncident
        """
        return EnrichedIncident(
            incident_id=incident_id,
            drone_type_signals=[DroneTypeSignal.UNKNOWN],
            drone_type_confidence=0.0,
            intelligence_summary="LLM enrichment unavailable (no API key configured)",
            key_findings=[
                f"Total evidence items collected: {evidence_stack.total_items}",
                f"Average credibility score: {evidence_stack.avg_credibility:.2f}",
                "LLM analysis requires ANTHROPIC_API_KEY environment variable"
            ],
            total_evidence_analyzed=evidence_stack.total_items,
            llm_model="mock"
        )


# Factory function for easy instantiation
def enrich_incident(incident_id: int, evidence_stack: Any) -> EnrichedIncident:
    """Enrich incident with LLM analysis.

    Args:
        incident_id: ID of the incident
        evidence_stack: EvidenceStack with all evidence

    Returns:
        EnrichedIncident with extracted intelligence signals
    """
    enricher = EvidenceEnricher()
    return enricher.enrich_incident(incident_id, evidence_stack)
