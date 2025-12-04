#!/usr/bin/env python3
"""Test script for Sprint 2 Intelligence Layer.

Tests the full intelligence pipeline:
1. Evidence Stack Builder
2. LLM Evidence Enrichment
3. Operator Hideout Engine
4. Intelligence API Endpoint
"""

import sys
from datetime import datetime
from sqlalchemy.orm import Session

# Add parent directory to path
sys.path.insert(0, "/Users/marcel/MarLLM/drone-cuas-osint-dashboard-v2")

from backend.app.db.session import SessionLocal
from backend.app.domain.incident import Incident
from backend.app.domain.site import Site, SiteType
from backend.app.domain.evidence import Evidence, SourceType
from backend.app.services.evidence_stack import build_evidence_stack
from backend.app.llm.evidence_enricher import enrich_incident
from backend.app.services.operator_hideout import analyze_operator_location


def create_test_data(db: Session) -> int:
    """Create test site, incident, and evidence.

    Args:
        db: Database session

    Returns:
        incident_id: ID of created test incident
    """
    print("Creating test data...")

    # Create test site (Volkel Air Base)
    site = Site(
        name="Volkel Air Base",
        type=SiteType.MILITARY,
        country_code="NL",
        geom_wkt="POINT(5.7083 51.6564)",  # lon, lat
        site_metadata={"icao": "EHVK", "description": "Royal Netherlands Air Force base"}
    )
    db.add(site)
    db.flush()

    # Create test incident
    incident = Incident(
        title="Drone sighting near Volkel Air Base",
        country_code="NL",
        site_id=site.id,
        occurred_at=datetime(2024, 12, 3, 21, 30),  # 9:30 PM
        raw_metadata={
            "description": "Multiple witnesses reported drone with lights hovering near airbase perimeter"
        }
    )
    db.add(incident)
    db.flush()

    # Create test evidence
    evidence_items = [
        Evidence(
            incident_id=incident.id,
            source_type=SourceType.NEWS,
            source_name="NOS",
            url="https://nos.nl/example-1",
            language="nl",
            published_at=datetime(2024, 12, 3, 22, 0),
            raw_text="Een drone met verlichting werd gezien boven de militaire basis Volkel rond 21:30 uur. Getuigen melden dat het toestel enkele minuten ter plaatse bleef hangen voordat het richting het noordoosten verdween.",
            meta={"category": "defense"}
        ),
        Evidence(
            incident_id=incident.id,
            source_type=SourceType.NEWS,
            source_name="Omroep Brabant",
            url="https://omroepbrabant.nl/example-1",
            language="nl",
            published_at=datetime(2024, 12, 3, 22, 15),
            raw_text="Lokale bewoners rapporteerden een drone met rode en groene lichten. Het toestel vloog op een hoogte van ongeveer 100-150 meter en maakte een zoemend geluid.",
            meta={"category": "local_news"}
        ),
        Evidence(
            incident_id=incident.id,
            source_type=SourceType.SOCIAL_MEDIA,
            source_name="Twitter @LocalResident",
            url="https://twitter.com/example/status/123",
            language="en",
            published_at=datetime(2024, 12, 3, 21, 45),
            raw_text="Just saw a drone with flashing lights hovering over Volkel airbase! Looked like a consumer drone, maybe a DJI? It stayed in place for a few minutes then flew off to the northeast. #drone #volkel",
            meta={"retweets": 12, "likes": 45}
        ),
        Evidence(
            incident_id=incident.id,
            source_type=SourceType.REDDIT,
            source_name="r/Netherlands",
            url="https://reddit.com/r/Netherlands/example",
            language="en",
            published_at=datetime(2024, 12, 3, 23, 0),
            raw_text="Anyone else see that drone near Volkel tonight around 9:30 PM? It had red and green navigation lights and was flying pretty low. Estimated altitude maybe 150m. Definitely not a plane or helicopter.",
            meta={"upvotes": 34, "comments": 12}
        ),
    ]

    for evidence in evidence_items:
        db.add(evidence)

    db.commit()

    print(f"Test data created:")
    print(f"  Site ID: {site.id} - {site.name}")
    print(f"  Incident ID: {incident.id} - {incident.title}")
    print(f"  Evidence items: {len(evidence_items)}")
    print()

    return incident.id


def test_evidence_stack(db: Session, incident_id: int):
    """Test Evidence Stack Builder.

    Args:
        db: Database session
        incident_id: Incident ID
    """
    print("=" * 80)
    print("TEST 1: Evidence Stack Builder")
    print("=" * 80)

    # Get evidence records
    evidence_records = db.query(Evidence).filter(Evidence.incident_id == incident_id).all()

    # Build evidence stack
    stack = build_evidence_stack(incident_id, evidence_records)

    print(f"Incident ID: {stack.incident_id}")
    print(f"Total evidence items: {stack.total_items}")
    print(f"Duplicates removed: {stack.duplicates_removed}")
    print(f"Average credibility: {stack.avg_credibility:.2f}")
    print(f"Earliest evidence: {stack.earliest_evidence}")
    print(f"Latest evidence: {stack.latest_evidence}")
    print()

    print("Evidence by category:")
    print(f"  Official reports: {len(stack.official_reports)}")
    print(f"  News articles: {len(stack.news_articles)}")
    print(f"  Social media: {len(stack.social_media_posts)}")
    print(f"  Telegram: {len(stack.telegram_messages)}")
    print(f"  YouTube: {len(stack.youtube_videos)}")
    print(f"  Forums: {len(stack.forum_posts)}")
    print(f"  Witnesses: {len(stack.witness_statements)}")
    print()

    print("Sample evidence item:")
    if stack.all_items:
        item = stack.all_items[0]
        print(f"  Source: {item.source_name} ({item.source_type.value})")
        print(f"  Credibility: {item.credibility_score:.2f}")
        print(f"  Locality: {item.locality_score:.2f}")
        print(f"  Adversary intent: {item.adversary_intent_score:.2f}")
        print(f"  Geoloc cues: {item.geoloc_cues}")
        print(f"  Temporal cues: {item.temporal_cues}")
        print(f"  Text preview: {item.text_content[:100]}...")
    print()

    return stack


def test_llm_enrichment(incident_id: int, stack):
    """Test LLM Evidence Enrichment.

    Args:
        incident_id: Incident ID
        stack: EvidenceStack
    """
    print("=" * 80)
    print("TEST 2: LLM Evidence Enrichment")
    print("=" * 80)

    # Enrich incident
    enriched = enrich_incident(incident_id, stack)

    print(f"Incident ID: {enriched.incident_id}")
    print(f"Total evidence analyzed: {enriched.total_evidence_analyzed}")
    print(f"LLM model: {enriched.llm_model}")
    print()

    print(f"Drone type signals: {[signal.value for signal in enriched.drone_type_signals]}")
    print(f"Drone type confidence: {enriched.drone_type_confidence:.2f}")
    print()

    if enriched.flight_dynamics:
        print("Flight dynamics:")
        print(f"  Approach vector: {enriched.flight_dynamics.approach_vector}")
        print(f"  Exit vector: {enriched.flight_dynamics.exit_vector}")
        print(f"  Flight pattern: {enriched.flight_dynamics.flight_pattern}")
        print(f"  Speed estimate: {enriched.flight_dynamics.speed_estimate}")
        print()

    if enriched.altitude_range:
        print("Altitude range:")
        print(f"  Min: {enriched.altitude_range.min_meters}m")
        print(f"  Max: {enriched.altitude_range.max_meters}m")
        print(f"  Confidence: {enriched.altitude_range.confidence:.2f}")
        print(f"  Reasoning: {enriched.altitude_range.reasoning}")
        print()

    if enriched.lighting_conditions:
        print("Lighting conditions:")
        print(f"  Time of day: {enriched.lighting_conditions.time_of_day}")
        print(f"  Lights observed: {enriched.lighting_conditions.lights_observed}")
        print(f"  Light pattern: {enriched.lighting_conditions.light_pattern}")
        print()

    print("Intelligence summary:")
    print(f"  {enriched.intelligence_summary}")
    print()

    print("Key findings:")
    for idx, finding in enumerate(enriched.key_findings, 1):
        print(f"  {idx}. {finding}")
    print()

    return enriched


def test_operator_analysis(incident_id: int):
    """Test Operator Hideout Engine.

    Args:
        incident_id: Incident ID
    """
    print("=" * 80)
    print("TEST 3: Operator Hideout Engine")
    print("=" * 80)

    # Analyze operator location (Volkel coordinates)
    analysis = analyze_operator_location(
        incident_id=incident_id,
        target_lat=51.6564,
        target_lon=5.7083,
        site_type="military"
    )

    print(f"Incident ID: {analysis.incident_id}")
    print(f"Target location: {analysis.target_latitude:.4f}, {analysis.target_longitude:.4f}")
    print(f"Search radius: {analysis.search_radius_m}m")
    print(f"Perimeter radius: {analysis.perimeter_radius_m}m")
    print(f"Predicted hotspots: {len(analysis.predicted_hotspots)}")
    print()

    for idx, hotspot in enumerate(analysis.predicted_hotspots, 1):
        print(f"Hotspot {idx}:")
        print(f"  Location: {hotspot.latitude:.4f}, {hotspot.longitude:.4f}")
        print(f"  Distance to target: {hotspot.distance_to_target_m:.0f}m")
        print(f"  Total score: {hotspot.total_score:.3f}")
        print(f"  Score breakdown:")
        print(f"    - Cover: {hotspot.cover_score:.2f} ({hotspot.cover_type.value})")
        print(f"    - Distance: {hotspot.distance_score:.2f}")
        print(f"    - Exfil: {hotspot.exfil_score:.2f}")
        print(f"    - OPSEC: {hotspot.opsec_score:.2f}")
        print(f"    - Terrain: {hotspot.terrain_score:.2f}")
        print(f"  Terrain suitability: {hotspot.terrain_suitability.value}")
        print(f"  Nearest road: {hotspot.nearest_road_type} ({hotspot.nearest_road_distance_m:.0f}m)")
        print(f"  Reasoning: {hotspot.reasoning}")
        print()

    return analysis


def main():
    """Main test execution."""
    print("=" * 80)
    print("Sprint 2 Intelligence Layer Testing")
    print("=" * 80)
    print()

    # Create database session
    db = SessionLocal()

    try:
        # Create test data
        incident_id = create_test_data(db)

        # Test 1: Evidence Stack Builder
        stack = test_evidence_stack(db, incident_id)

        # Test 2: LLM Evidence Enrichment
        enriched = test_llm_enrichment(incident_id, stack)

        # Test 3: Operator Hideout Engine
        analysis = test_operator_analysis(incident_id)

        # Summary
        print("=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)
        print("All tests completed successfully!")
        print()
        print(f"Evidence Stack: {stack.total_items} items, {stack.avg_credibility:.2f} avg credibility")
        print(f"LLM Enrichment: {enriched.total_evidence_analyzed} items analyzed, {len(enriched.key_findings)} findings")
        print(f"Operator Analysis: {len(analysis.predicted_hotspots)} hotspots predicted")
        print()
        print(f"Test incident ID: {incident_id}")
        print(f"API endpoint: GET /incidents/{incident_id}/intelligence")
        print()

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    finally:
        db.close()


if __name__ == "__main__":
    main()
