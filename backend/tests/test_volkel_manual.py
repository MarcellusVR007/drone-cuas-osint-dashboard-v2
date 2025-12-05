"""
Manual test for Volkel Air Base boundary constraint.
"""

import sys
sys.path.insert(0, '/app')

from backend.app.services.operator_hideout_v2.site_boundary import get_site_boundary
from backend.app.services.operator_hideout_v2.engine_v2 import OperatorHideoutEngineV2
import math


def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate distance in meters"""
    R = 6371000  # Earth radius in meters
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)

    a = (math.sin(delta_lat / 2) ** 2 +
         math.cos(lat1_rad) * math.cos(lat2_rad) *
         math.sin(delta_lon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c


def test_volkel_constraint():
    """Test that NO hotspots are inside Volkel Air Base perimeter"""

    print("=" * 70)
    print("VOLKEL AIR BASE PERIMETER CONSTRAINT TEST")
    print("=" * 70)

    # Initialize engine
    engine = OperatorHideoutEngineV2(
        search_radius_m=4000,
        perimeter_radius_m=500,
        num_candidates=72,
    )

    # Get Volkel boundary
    volkel_boundary = get_site_boundary("Volkel Air Base")
    if not volkel_boundary:
        print("❌ ERROR: Volkel boundary not found!")
        return False

    print(f"\nVolkel Air Base Configuration:")
    print(f"  Center: ({volkel_boundary.center_lat:.6f}, {volkel_boundary.center_lon:.6f})")
    print(f"  Base radius: {volkel_boundary.radius_m}m")
    print(f"  Safety buffer: {volkel_boundary.safety_buffer_m}m")
    print(f"  Total perimeter: {volkel_boundary.radius_m + volkel_boundary.safety_buffer_m}m")

    # Run prediction for Volkel incident (incident 1)
    print(f"\n{'=' * 70}")
    print("Running operator prediction for Volkel incident...")
    print(f"{'=' * 70}\n")

    analysis = engine.predict_operator_locations(
        incident_id=1,
        target_lat=51.6564,
        target_lon=5.7083,
        drone_type='consumer_dji',
        approach_vector='NE',
        time_of_day='night',
    )

    # Check all hotspots
    print(f"\n{'=' * 70}")
    print(f"HOTSPOT ANALYSIS (Total: {len(analysis.predicted_hotspots)})")
    print(f"{'=' * 70}\n")

    all_pass = True
    min_required_distance = volkel_boundary.radius_m + volkel_boundary.safety_buffer_m

    for idx, hotspot in enumerate(analysis.predicted_hotspots, 1):
        # Check if inside boundary
        is_inside = volkel_boundary.is_inside_boundary(hotspot.latitude, hotspot.longitude)

        # Calculate distance from base center
        distance_m = haversine_distance(
            volkel_boundary.center_lat,
            volkel_boundary.center_lon,
            hotspot.latitude,
            hotspot.longitude
        )

        status = "❌ FAIL" if is_inside else "✅ PASS"

        print(f"Hotspot #{idx}: {status}")
        print(f"  Location: ({hotspot.latitude:.6f}, {hotspot.longitude:.6f})")
        print(f"  Distance from base center: {distance_m:.1f}m")
        print(f"  Required minimum: {min_required_distance:.1f}m")
        print(f"  Margin: {distance_m - min_required_distance:.1f}m")
        print(f"  Inside boundary: {is_inside}")
        print(f"  Total score: {hotspot.total_score:.4f}")
        print(f"  Confidence: {hotspot.confidence_level}")
        print()

        if is_inside:
            print(f"  ⚠️  ERROR: Hotspot is INSIDE base perimeter!")
            all_pass = False
        elif distance_m <= min_required_distance:
            print(f"  ⚠️  ERROR: Hotspot too close to base center!")
            all_pass = False

    # Summary
    print(f"{'=' * 70}")
    print("TEST RESULT")
    print(f"{'=' * 70}")

    if all_pass:
        print("✅ SUCCESS: All hotspots are outside Volkel Air Base perimeter")
        print("✅ Constraint enforcement is working correctly")
        return True
    else:
        print("❌ FAILURE: One or more hotspots violate perimeter constraint")
        print("❌ This is a CRITICAL security issue")
        return False


if __name__ == "__main__":
    success = test_volkel_constraint()
    sys.exit(0 if success else 1)
