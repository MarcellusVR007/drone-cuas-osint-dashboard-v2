# LLM Integration Rules

## Overview

ALL LLM interactions in V2 must go through the `backend/app/llm/` layer. No direct API calls from other layers.

## Core Principles

1. **Centralized:** All LLM logic lives in `backend/app/llm/`
2. **Structured:** Use Pydantic schemas for LLM output
3. **Testable:** Mock LLM calls in tests
4. **Observable:** Log all LLM requests/responses
5. **Resilient:** Handle errors, retries, rate limits

## Folder Structure

```
backend/app/llm/
├── __init__.py
├── client.py           # Anthropic/OpenAI client setup
├── prompts/
│   ├── enrichment.py   # Incident enrichment prompts
│   ├── operator.py     # Operator analysis prompts
│   └── evidence.py     # Evidence analysis prompts
├── schemas/
│   ├── enrichment.py   # Pydantic output schemas
│   └── operator.py
└── utils.py            # Retry logic, logging, helpers
```

## Usage Pattern

### 1. Define Output Schema

```python
# backend/app/llm/schemas/enrichment.py
from pydantic import BaseModel, Field

class LocationInference(BaseModel):
    """Inferred location from incident title."""
    location_name: str = Field(description="Name of location (e.g., 'Volkel Air Base')")
    country_code: str = Field(description="ISO 3166-1 alpha-2 code")
    latitude: float | None = Field(description="Latitude if known")
    longitude: float | None = Field(description="Longitude if known")
    confidence: float = Field(description="Confidence 0.0-1.0", ge=0.0, le=1.0)
    reasoning: str = Field(description="Why this location was inferred")
```

### 2. Define Prompt Function

```python
# backend/app/llm/prompts/enrichment.py
from anthropic import Anthropic
from backend.app.llm.schemas.enrichment import LocationInference
from backend.app.llm.client import get_anthropic_client

def infer_location_from_title(title: str) -> LocationInference:
    """
    Use Claude to infer location from incident title.

    Args:
        title: Incident title (e.g., "Drone spotted over Volkel")

    Returns:
        LocationInference with structured location data
    """
    client = get_anthropic_client()

    prompt = f"""
    Extract location information from this drone incident title:

    Title: {title}

    Return:
    - location_name: The specific site/location name
    - country_code: ISO 2-letter country code
    - latitude/longitude: If you can infer from name
    - confidence: How sure you are (0.0-1.0)
    - reasoning: Why you chose this
    """

    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}]
    )

    # Parse response into Pydantic schema
    return LocationInference.model_validate_json(response.content[0].text)
```

### 3. Call from Service Layer

```python
# backend/app/services/enrichment.py
from backend.app.llm.prompts.enrichment import infer_location_from_title
from backend.app.domain.incident import Incident

def enrich_incident_location(incident: Incident) -> Incident:
    """Enrich incident with inferred location data."""
    location = infer_location_from_title(incident.title)

    # Store in raw_metadata JSONB field
    incident.raw_metadata = incident.raw_metadata or {}
    incident.raw_metadata["inferred_location"] = location.model_dump()

    return incident
```

## LLM Client Setup

```python
# backend/app/llm/client.py
import os
from anthropic import Anthropic
from openai import OpenAI

def get_anthropic_client() -> Anthropic:
    """Get configured Anthropic client."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not set")
    return Anthropic(api_key=api_key)

def get_openai_client() -> OpenAI:
    """Get configured OpenAI client."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not set")
    return OpenAI(api_key=api_key)
```

## Error Handling

```python
# backend/app/llm/utils.py
import logging
from functools import wraps
from anthropic import AnthropicError

logger = logging.getLogger(__name__)

def retry_on_llm_error(max_retries=3):
    """Decorator to retry LLM calls on failure."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except AnthropicError as e:
                    logger.warning(f"LLM call failed (attempt {attempt+1}/{max_retries}): {e}")
                    if attempt == max_retries - 1:
                        raise
            return None
        return wrapper
    return decorator
```

## Logging

ALL LLM calls must be logged:

```python
logger.info(f"LLM call: {func_name}", extra={
    "prompt_length": len(prompt),
    "model": model,
    "max_tokens": max_tokens
})

logger.info(f"LLM response: {func_name}", extra={
    "tokens_used": response.usage.total_tokens,
    "latency_ms": latency
})
```

## Testing

Mock LLM calls in tests:

```python
# tests/test_enrichment.py
from unittest.mock import patch
from backend.app.llm.schemas.enrichment import LocationInference

def test_enrich_incident_location():
    mock_location = LocationInference(
        location_name="Volkel Air Base",
        country_code="NL",
        confidence=0.95,
        reasoning="Explicit mention in title"
    )

    with patch("backend.app.llm.prompts.enrichment.infer_location_from_title", return_value=mock_location):
        incident = Incident(title="Drone over Volkel")
        enriched = enrich_incident_location(incident)
        assert enriched.raw_metadata["inferred_location"]["location_name"] == "Volkel Air Base"
```

## Cost Tracking

Track LLM costs:

```python
# Store in database
class LLMCall(Base):
    __tablename__ = "llm_calls"
    id = Column(Integer, primary_key=True)
    function_name = Column(String)
    model = Column(String)
    prompt_tokens = Column(Integer)
    completion_tokens = Column(Integer)
    cost_usd = Column(Float)
    created_at = Column(TIMESTAMP)
```

## Prompt Engineering Guidelines

1. **Be specific:** Clear instructions, examples
2. **Use schemas:** Always define expected output structure
3. **Few-shot examples:** Include 2-3 examples in prompt
4. **Chain of thought:** Ask model to explain reasoning
5. **Constraints:** Specify limits (e.g., "max 100 words")

## Model Selection

- **Claude 3.5 Sonnet:** Complex reasoning (operator analysis, evidence correlation)
- **Claude 3 Haiku:** Simple extraction (location, dates, metadata)
- **GPT-4:** Fallback if Claude unavailable

## Rate Limits

- Implement exponential backoff
- Queue LLM jobs for batch processing
- Cache results to avoid redundant calls

## Security

- Never log API keys
- Sanitize user input before LLM prompts
- Validate LLM output before storing in DB
- Set max_tokens to prevent runaway costs
