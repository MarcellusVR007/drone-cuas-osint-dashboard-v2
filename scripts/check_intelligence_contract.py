#!/usr/bin/env python3
"""Contract validation for /incidents/{id}/intelligence endpoint.

Checks that the response conforms to the explicit JSON contract defined in
backend/app/api/schemas/intelligence.py
"""

import requests
import sys

def check_contract():
    """Check intelligence endpoint contract."""
    url = "http://localhost:8000/incidents/1/intelligence"

    print("=" * 80)
    print("INTELLIGENCE CONTRACT VALIDATION")
    print("=" * 80)
    print(f"\nChecking: {url}\n")

    try:
        response = requests.get(url, timeout=10)
    except requests.exceptions.ConnectionError:
        print("❌ CONTRACT BROKEN: Cannot connect to backend")
        print("   Make sure Docker Compose is running: docker-compose up -d")
        return False
    except Exception as e:
        print(f"❌ CONTRACT BROKEN: Request failed: {e}")
        return False

    # Check HTTP status
    if response.status_code != 200:
        print(f"❌ CONTRACT BROKEN: HTTP {response.status_code}")
        print(f"   Expected: HTTP 200")
        return False

    print(f"✅ HTTP Status: {response.status_code}")

    # Parse JSON
    try:
        data = response.json()
    except Exception as e:
        print(f"❌ CONTRACT BROKEN: Invalid JSON response")
        print(f"   Error: {e}")
        return False

    print("✅ Valid JSON response")

    # Check required top-level keys
    required_keys = [
        "incident",
        "drone_profile",
        "flight_dynamics",
        "operator_hotspots",
        "evidence_summary",
        "evidence",
        "meta"
    ]

    missing_keys = [key for key in required_keys if key not in data]
    if missing_keys:
        print(f"❌ CONTRACT BROKEN: Missing top-level keys: {missing_keys}")
        return False

    print(f"✅ All top-level keys present: {required_keys}")

    # Check operator_hotspots is a list
    if not isinstance(data["operator_hotspots"], list):
        print(f"❌ CONTRACT BROKEN: operator_hotspots is not a list")
        print(f"   Type: {type(data['operator_hotspots'])}")
        return False

    print(f"✅ operator_hotspots is a list ({len(data['operator_hotspots'])} items)")

    # Check evidence is a list
    if not isinstance(data["evidence"], list):
        print(f"❌ CONTRACT BROKEN: evidence is not a list")
        print(f"   Type: {type(data['evidence'])}")
        return False

    print(f"✅ evidence is a list ({len(data['evidence'])} items)")

    # Check incident fields
    incident = data["incident"]
    incident_required = ["id", "title"]
    missing_incident_fields = [f for f in incident_required if f not in incident]
    if missing_incident_fields:
        print(f"❌ CONTRACT BROKEN: incident missing fields: {missing_incident_fields}")
        return False

    print(f"✅ incident has required fields: {incident_required}")

    # Check drone_profile fields
    drone_profile = data["drone_profile"]
    drone_required = ["type_primary", "type_confidence", "type_alternatives", "lights_observed"]
    missing_drone_fields = [f for f in drone_required if f not in drone_profile]
    if missing_drone_fields:
        print(f"❌ CONTRACT BROKEN: drone_profile missing fields: {missing_drone_fields}")
        return False

    print(f"✅ drone_profile has required fields: {drone_required}")

    # Check meta fields
    meta = data["meta"]
    meta_required = ["analyzed_at", "llm_mode", "search_radius_m", "perimeter_radius_m"]
    missing_meta_fields = [f for f in meta_required if f not in meta]
    if missing_meta_fields:
        print(f"❌ CONTRACT BROKEN: meta missing fields: {missing_meta_fields}")
        return False

    print(f"✅ meta has required fields: {meta_required}")

    # Check operator hotspot structure (if any)
    if data["operator_hotspots"]:
        hotspot = data["operator_hotspots"][0]
        hotspot_required = ["rank", "latitude", "longitude", "total_score", "reasoning"]
        missing_hotspot_fields = [f for f in hotspot_required if f not in hotspot]
        if missing_hotspot_fields:
            print(f"❌ CONTRACT BROKEN: operator hotspot missing fields: {missing_hotspot_fields}")
            return False

        print(f"✅ operator hotspot has required fields: {hotspot_required}")

    print("\n" + "=" * 80)
    print("✅ CONTRACT OK - All validations passed!")
    print("=" * 80)
    return True


if __name__ == "__main__":
    success = check_contract()
    sys.exit(0 if success else 1)
