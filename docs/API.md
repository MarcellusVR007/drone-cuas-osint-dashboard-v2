# API Documentation

## Incident Intelligence Endpoint

**Endpoint**: `GET /incidents/{id}/intelligence`

**Purpose**: Returns comprehensive intelligence analysis for a drone incident, combining OSINT evidence aggregation, LLM-based analysis, and operator location prediction.

### Response Structure

The response follows an explicit JSON contract defined in `backend/app/api/schemas/intelligence.py`:

- **incident**: Basic incident information (ID, title, location, coordinates, timestamp)
- **drone_profile**: Analyzed drone characteristics
  - Primary type classification with confidence
  - Alternative types
  - Physical characteristics (size, sound, visual description)
  - Lighting observations
- **flight_dynamics**: Flight behavior and trajectory
  - Approach/exit vectors
  - Flight pattern (hovering/circling/straight line/erratic)
  - Altitude range with confidence
  - Speed and maneuverability estimates
- **operator_hotspots**: List of 1-3 predicted operator launch sites
  - Each hotspot includes: coordinates, distance to target, composite score
  - Score breakdown: cover, distance, exfil, OPSEC, terrain
  - Cover type and terrain suitability classifications
  - Human-readable reasoning
- **evidence_summary**: Statistics about collected evidence
  - Total items, average credibility, duplicates removed
  - Breakdown by source type (news, social media, Telegram, etc.)
  - Temporal bounds (earliest/latest evidence timestamps)
- **evidence**: List of top 10 most credible evidence items
  - Source information, text preview, language
  - Credibility, locality, and adversary intent scores
- **meta**: Analysis metadata
  - Analysis timestamp
  - LLM mode (mock/live)
  - Search parameters (radius, perimeter)

### Example Response (abbreviated)

```json
{
  "incident": {
    "id": 1,
    "title": "Drone sighting near Volkel Air Base",
    "location_name": "Volkel Air Base",
    "country_code": "NL",
    "occurred_at": "2024-12-03T21:30:00Z",
    "latitude": 51.6564,
    "longitude": 5.7083
  },
  "drone_profile": {
    "type_primary": "unknown",
    "type_confidence": 0.0,
    "type_alternatives": [],
    "lights_observed": false,
    "summary": "LLM enrichment unavailable (no API key configured)"
  },
  "flight_dynamics": {
    "approach_vector": null,
    "pattern": null,
    "altitude_min_m": null,
    "altitude_max_m": null,
    "altitude_confidence": 0.0
  },
  "operator_hotspots": [
    {
      "rank": 1,
      "latitude": 51.6437,
      "longitude": 5.6878,
      "distance_to_target_m": 2000.0,
      "total_score": 0.890,
      "cover_type": "urban_building",
      "terrain_suitability": "excellent",
      "reasoning": "Optimal distance (2000m) for drone control. ..."
    }
  ],
  "evidence_summary": {
    "total_items": 1,
    "avg_credibility": 0.85,
    "news_articles_count": 1
  },
  "evidence": [
    {
      "source_type": "verified_news",
      "source_name": "NOS",
      "text_preview": "Een drone met verlichting werd gezien...",
      "credibility_score": 0.85
    }
  ],
  "meta": {
    "analyzed_at": "2025-12-04T21:55:23Z",
    "llm_mode": "mock",
    "search_radius_m": 4000.0
  }
}
```

### Notes

- LLM mode is "mock" when `ANTHROPIC_API_KEY` is not configured
- In mock mode, drone profile and flight dynamics fields will be null/unknown
- Operator hotspots are always generated using rule-based OPSEC-TTP analysis
- Evidence is sorted by credibility score (highest first)
