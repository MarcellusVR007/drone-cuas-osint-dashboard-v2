"""
Test that candidates inside site boundary are actually filtered.
"""

import sys
sys.path.insert(0, '/app')

from backend.app.services.operator_hideout_v2.site_boundary import get_site_boundary
from backend.app.services.operator_hideout_v2.engine_v2 import OperatorHideoutEngineV2


def test_candidate_filtering():
    """Test that candidates inside perimeter are filtered"""

    print("=" * 70)
    print("CANDIDATE FILTERING TEST")
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

    print(f"\nVolkel Air Base: {volkel_boundary.radius_m}m radius + {volkel_boundary.safety_buffer_m}m buffer")

    # Generate all candidate locations
    candidates = engine._generate_candidate_grid(51.6564, 5.7083)

    # Check which candidates are inside/outside boundary
    inside_candidates = []
    outside_candidates = []

    for candidate in candidates:
        if volkel_boundary.is_inside_boundary(candidate["lat"], candidate["lon"]):
            inside_candidates.append(candidate)
        else:
            outside_candidates.append(candidate)

    print(f"\nCandidate Grid Analysis:")
    print(f"  Total candidates: {len(candidates)}")
    print(f"  Inside perimeter: {len(inside_candidates)}")
    print(f"  Outside perimeter: {len(outside_candidates)}")

    # Show some examples of filtered candidates
    if inside_candidates:
        print(f"\nExample filtered candidates (inside perimeter):")
        for i, cand in enumerate(inside_candidates[:5], 1):
            print(f"  {i}. ({cand['lat']:.6f}, {cand['lon']:.6f}) "
                  f"- distance: {cand['distance_km']:.2f}km, bearing: {cand['bearing_deg']}°")

    # Run actual prediction
    print(f"\n{'=' * 70}")
    print("Running prediction with filtering...")
    print(f"{'=' * 70}\n")

    analysis = engine.predict_operator_locations(
        incident_id=1,
        target_lat=51.6564,
        target_lon=5.7083,
    )

    # Verify all returned hotspots are outside
    print(f"Returned hotspots: {len(analysis.predicted_hotspots)}")

    all_pass = True
    for idx, hotspot in enumerate(analysis.predicted_hotspots, 1):
        is_inside = volkel_boundary.is_inside_boundary(hotspot.latitude, hotspot.longitude)
        status = "✅" if not is_inside else "❌"

        print(f"  {status} Hotspot #{idx}: ({hotspot.latitude:.6f}, {hotspot.longitude:.6f}) "
              f"- Inside: {is_inside}")

        if is_inside:
            all_pass = False

    # Verify filtering happened
    print(f"\n{'=' * 70}")
    print("FILTERING VERIFICATION")
    print(f"{'=' * 70}")

    if len(inside_candidates) == 0:
        print("⚠️  Warning: No candidates were inside perimeter to filter")
        print("   (This may happen if target is on edge of base)")
    else:
        print(f"✅ {len(inside_candidates)} candidates were inside perimeter")
        print(f"✅ Filtering mechanism is active")

    if all_pass:
        print(f"✅ All returned hotspots are outside perimeter")
        print(f"✅ Hard constraint enforcement PASSED")
        return True
    else:
        print(f"❌ Some hotspots are inside perimeter!")
        print(f"❌ Hard constraint enforcement FAILED")
        return False


if __name__ == "__main__":
    success = test_candidate_filtering()
    sys.exit(0 if success else 1)
