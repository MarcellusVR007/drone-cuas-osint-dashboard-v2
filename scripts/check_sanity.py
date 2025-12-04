#!/usr/bin/env python3
"""
Sanity check script to verify API endpoints are working.

Tests:
- Health endpoint
- Incidents list endpoint
- Sites list endpoint
"""

import requests
import sys


def check_endpoint(name: str, url: str, expected_keys: list[str]) -> bool:
    """
    Check if an endpoint returns expected keys.

    Args:
        name: Endpoint name for logging
        url: URL to test
        expected_keys: List of keys expected in response

    Returns:
        bool: True if test passed, False otherwise
    """
    try:
        print(f"Testing {name}...", end=" ")
        response = requests.get(url, timeout=5)
        response.raise_for_status()

        data = response.json()

        # Check for expected keys
        missing_keys = [key for key in expected_keys if key not in data]
        if missing_keys:
            print(f"FAIL (missing keys: {missing_keys})")
            return False

        print("OK")
        return True

    except requests.RequestException as e:
        print(f"FAIL ({e})")
        return False


def main():
    """Run sanity checks."""
    print("=== CUAS Dashboard V2 - Sanity Check ===\n")

    base_url = "http://localhost:8000"
    tests = [
        ("Health", f"{base_url}/health", ["status", "api", "database"]),
        ("Incidents List", f"{base_url}/incidents", ["total", "incidents"]),
        ("Sites List", f"{base_url}/sites", ["total", "sites"]),
    ]

    passed = 0
    failed = 0

    for name, url, expected_keys in tests:
        if check_endpoint(name, url, expected_keys):
            passed += 1
        else:
            failed += 1

    print(f"\n=== Results ===")
    print(f"Passed: {passed}/{len(tests)}")
    print(f"Failed: {failed}/{len(tests)}")

    if failed > 0:
        print("\nSome tests failed. Check that:")
        print("1. Docker Compose services are running (docker-compose ps)")
        print("2. Migrations have been applied (docker-compose exec backend alembic upgrade head)")
        print("3. Backend is accessible (docker-compose logs backend)")
        sys.exit(1)
    else:
        print("\nAll tests passed!")
        sys.exit(0)


if __name__ == "__main__":
    main()
