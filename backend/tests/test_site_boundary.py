"""
Unit tests for Site Boundary constraints.

Tests that operator hotspots are NEVER inside protected site perimeters.
"""

import pytest
from backend.app.services.operator_hideout_v2.site_boundary import (
    SiteBoundary,
    get_site_boundary,
    get_site_boundary_by_location,
)
from backend.app.services.operator_hideout_v2.engine_v2 import OperatorHideoutEngineV2


class TestSiteBoundary:
    """Test site boundary models"""

    def test_circular_boundary_inside(self):
        """Test point inside circular boundary"""
        boundary = SiteBoundary(
            site_name="Test Site",
            center_lat=51.6564,
            center_lon=5.7083,
            radius_m=1000,
            safety_buffer_m=200,
        )

        # Point at center - definitely inside
        assert boundary.is_inside_boundary(51.6564, 5.7083) is True

        # Point very close to center - inside
        assert boundary.is_inside_boundary(51.6574, 5.7083) is True

    def test_circular_boundary_outside(self):
        """Test point outside circular boundary"""
        boundary = SiteBoundary(
            site_name="Test Site",
            center_lat=51.6564,
            center_lon=5.7083,
            radius_m=1000,
            safety_buffer_m=200,
        )

        # Point 2km away - outside
        assert boundary.is_inside_boundary(51.6744, 5.7083) is False

        # Point 3km away - definitely outside
        assert boundary.is_inside_boundary(51.6834, 5.7083) is False

    def test_circular_boundary_buffer(self):
        """Test safety buffer is respected"""
        boundary = SiteBoundary(
            site_name="Test Site",
            center_lat=51.6564,
            center_lon=5.7083,
            radius_m=1000,
            safety_buffer_m=200,
        )

        # Point at exactly 1100m (within radius + buffer) - inside
        # 1100m ≈ 0.0099 degrees latitude
        assert boundary.is_inside_boundary(51.6663, 5.7083) is True

        # Point at exactly 1300m (outside radius + buffer) - outside
        # 1300m ≈ 0.0117 degrees latitude
        assert boundary.is_inside_boundary(51.6681, 5.7083) is False

    def test_polygon_boundary_inside(self):
        """Test point inside polygon boundary"""
        # Square polygon around center
        vertices = [
            (51.66, 5.70),  # Bottom-left
            (51.66, 5.72),  # Bottom-right
            (51.68, 5.72),  # Top-right
            (51.68, 5.70),  # Top-left
        ]

        boundary = SiteBoundary(
            site_name="Test Site",
            center_lat=51.67,
            center_lon=5.71,
            polygon_vertices=vertices,
            safety_buffer_m=100,
        )

        # Point in center of polygon - inside
        assert boundary.is_inside_boundary(51.67, 5.71) is True

    def test_polygon_boundary_outside(self):
        """Test point outside polygon boundary"""
        # Square polygon around center
        vertices = [
            (51.66, 5.70),  # Bottom-left
            (51.66, 5.72),  # Bottom-right
            (51.68, 5.72),  # Top-right
            (51.68, 5.70),  # Top-left
        ]

        boundary = SiteBoundary(
            site_name="Test Site",
            center_lat=51.67,
            center_lon=5.71,
            polygon_vertices=vertices,
            safety_buffer_m=100,
        )

        # Point far outside polygon - outside
        assert boundary.is_inside_boundary(51.65, 5.69) is False
        assert boundary.is_inside_boundary(51.69, 5.73) is False

    def test_get_known_site_volkel(self):
        """Test retrieval of Volkel Air Base boundary"""
        boundary = get_site_boundary("Volkel Air Base")
        assert boundary is not None
        assert boundary.site_name == "Volkel Air Base"
        assert boundary.center_lat == 51.6564
        assert boundary.center_lon == 5.7083
        assert boundary.radius_m == 1500
        assert boundary.safety_buffer_m == 200

    def test_get_site_by_location_volkel(self):
        """Test finding Volkel boundary by nearby location"""
        # Location very close to Volkel center
        boundary = get_site_boundary_by_location(51.6564, 5.7083, radius_km=5.0)
        assert boundary is not None
        assert boundary.site_name == "Volkel Air Base"

    def test_get_site_by_location_not_found(self):
        """Test no site found for remote location"""
        # Location far from any known site (middle of ocean)
        boundary = get_site_boundary_by_location(52.0, 3.0, radius_km=5.0)
        assert boundary is None


class TestVolkelAirBaseConstraint:
    """Test that Volkel Air Base perimeter is enforced"""

    def test_volkel_incident_no_hotspots_inside_base(self):
        """
        CRITICAL TEST: Ensure NO hotspots are inside Volkel Air Base perimeter.

        Test Volkel site (incident 1):
        - Center: 51.6564, 5.7083
        - Perimeter: 1500m radius + 200m buffer = 1700m total
        """
        engine = OperatorHideoutEngineV2(
            search_radius_m=4000,
            perimeter_radius_m=500,
            num_candidates=72,
        )

        # Run prediction for Volkel incident
        analysis = engine.predict_operator_locations(
            incident_id=1,
            target_lat=51.6564,
            target_lon=5.7083,
            drone_type='consumer_dji',
            approach_vector='NE',
            time_of_day='night',
        )

        # Get Volkel boundary
        volkel_boundary = get_site_boundary("Volkel Air Base")
        assert volkel_boundary is not None

        # Check all predicted hotspots
        assert len(analysis.predicted_hotspots) == 3, "Should return 3 hotspots"

        for idx, hotspot in enumerate(analysis.predicted_hotspots, 1):
            # CRITICAL: Hotspot must be OUTSIDE boundary
            is_inside = volkel_boundary.is_inside_boundary(hotspot.latitude, hotspot.longitude)

            # Compute distance from base center for debugging
            import math
            R = 6371.0
            lat1_rad = math.radians(volkel_boundary.center_lat)
            lat2_rad = math.radians(hotspot.latitude)
            delta_lat = math.radians(hotspot.latitude - volkel_boundary.center_lat)
            delta_lon = math.radians(hotspot.longitude - volkel_boundary.center_lon)
            a = (math.sin(delta_lat / 2) ** 2 +
                 math.cos(lat1_rad) * math.cos(lat2_rad) *
                 math.sin(delta_lon / 2) ** 2)
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
            distance_km = R * c
            distance_m = distance_km * 1000

            print(f"\nHotspot #{idx}:")
            print(f"  Location: ({hotspot.latitude:.6f}, {hotspot.longitude:.6f})")
            print(f"  Distance from base center: {distance_m:.1f}m")
            print(f"  Base perimeter + buffer: {volkel_boundary.radius_m + volkel_boundary.safety_buffer_m}m")
            print(f"  Inside boundary: {is_inside}")
            print(f"  Score: {hotspot.total_score:.4f}")

            # ASSERTION: Must be outside
            assert is_inside is False, (
                f"Hotspot #{idx} at ({hotspot.latitude:.6f}, {hotspot.longitude:.6f}) "
                f"is INSIDE Volkel Air Base perimeter! Distance: {distance_m:.1f}m, "
                f"Perimeter: {volkel_boundary.radius_m + volkel_boundary.safety_buffer_m}m"
            )

            # Additional check: distance must be > perimeter + buffer
            min_distance = volkel_boundary.radius_m + volkel_boundary.safety_buffer_m
            assert distance_m > min_distance, (
                f"Hotspot #{idx} too close to base center: {distance_m:.1f}m "
                f"(minimum: {min_distance}m)"
            )

    def test_volkel_all_candidates_filtered(self):
        """Test that candidates inside perimeter are actually filtered"""
        engine = OperatorHideoutEngineV2(
            search_radius_m=4000,
            perimeter_radius_m=500,
            num_candidates=72,
        )

        # Run prediction
        analysis = engine.predict_operator_locations(
            incident_id=1,
            target_lat=51.6564,
            target_lon=5.7083,
            drone_type='consumer_dji',
        )

        # Get Volkel boundary
        volkel_boundary = get_site_boundary("Volkel Air Base")

        # Generate all candidates to see what was filtered
        candidates = engine._generate_candidate_grid(51.6564, 5.7083)

        filtered_candidates = [
            c for c in candidates
            if volkel_boundary.is_inside_boundary(c["lat"], c["lon"])
        ]

        passed_candidates = [
            c for c in candidates
            if not volkel_boundary.is_inside_boundary(c["lat"], c["lon"])
        ]

        print(f"\nCandidate filtering statistics:")
        print(f"  Total candidates: {len(candidates)}")
        print(f"  Filtered (inside perimeter): {len(filtered_candidates)}")
        print(f"  Passed (outside perimeter): {len(passed_candidates)}")

        # Should have filtered some candidates
        assert len(filtered_candidates) > 0, "Expected some candidates to be inside perimeter"

        # All returned hotspots should be from passed candidates
        for hotspot in analysis.predicted_hotspots:
            assert not volkel_boundary.is_inside_boundary(hotspot.latitude, hotspot.longitude)

    def test_volkel_minimum_distance_maintained(self):
        """Test that all hotspots maintain minimum distance from base center"""
        engine = OperatorHideoutEngineV2()

        analysis = engine.predict_operator_locations(
            incident_id=1,
            target_lat=51.6564,
            target_lon=5.7083,
        )

        volkel_boundary = get_site_boundary("Volkel Air Base")
        min_required_distance = volkel_boundary.radius_m + volkel_boundary.safety_buffer_m

        for hotspot in analysis.predicted_hotspots:
            # Compute distance
            import math
            R = 6371000  # meters
            lat1_rad = math.radians(volkel_boundary.center_lat)
            lat2_rad = math.radians(hotspot.latitude)
            delta_lat = math.radians(hotspot.latitude - volkel_boundary.center_lat)
            delta_lon = math.radians(hotspot.longitude - volkel_boundary.center_lon)
            a = (math.sin(delta_lat / 2) ** 2 +
                 math.cos(lat1_rad) * math.cos(lat2_rad) *
                 math.sin(delta_lon / 2) ** 2)
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
            distance_m = R * c

            assert distance_m > min_required_distance, (
                f"Hotspot at ({hotspot.latitude:.6f}, {hotspot.longitude:.6f}) "
                f"too close: {distance_m:.1f}m (minimum: {min_required_distance:.1f}m)"
            )


class TestOtherSitesConstraint:
    """Test boundary constraints for other known sites"""

    def test_eindhoven_airport_constraint(self):
        """Test Eindhoven Airport perimeter enforcement"""
        engine = OperatorHideoutEngineV2()

        # Eindhoven Airport center
        analysis = engine.predict_operator_locations(
            incident_id=999,
            target_lat=51.4500,
            target_lon=5.3747,
        )

        eindhoven_boundary = get_site_boundary("Eindhoven Airport")
        if eindhoven_boundary:
            for hotspot in analysis.predicted_hotspots:
                assert not eindhoven_boundary.is_inside_boundary(hotspot.latitude, hotspot.longitude)

    def test_schiphol_airport_constraint(self):
        """Test Schiphol Airport perimeter enforcement"""
        engine = OperatorHideoutEngineV2()

        # Schiphol Airport center
        analysis = engine.predict_operator_locations(
            incident_id=999,
            target_lat=52.3105,
            target_lon=4.7683,
        )

        schiphol_boundary = get_site_boundary("Schiphol Airport")
        if schiphol_boundary:
            for hotspot in analysis.predicted_hotspots:
                assert not schiphol_boundary.is_inside_boundary(hotspot.latitude, hotspot.longitude)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
