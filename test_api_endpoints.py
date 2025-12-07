#!/usr/bin/env python3
"""
Test script for CONTINUUM API endpoints.

Tests all endpoints to verify they're working correctly.
"""

import requests
import json
import time
from typing import Dict, Any


BASE_URL = "http://localhost:8420"
API_KEY = None  # Will be created during testing


def print_test(name: str, passed: bool, details: str = ""):
    """Print test result"""
    status = "✓ PASS" if passed else "✗ FAIL"
    print(f"{status} | {name}")
    if details:
        print(f"       {details}")


def test_root():
    """Test root endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/")
        passed = response.status_code == 200 and "CONTINUUM" in response.json().get("service", "")
        print_test("GET /", passed, f"Status: {response.status_code}")
        return passed
    except Exception as e:
        print_test("GET /", False, f"Error: {e}")
        return False


def test_health():
    """Test health check endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/v1/health")
        data = response.json()
        passed = (
            response.status_code == 200 and
            data.get("status") == "healthy" and
            data.get("service") == "continuum"
        )
        print_test("GET /v1/health", passed, f"Status: {data.get('status')}")
        return passed
    except Exception as e:
        print_test("GET /v1/health", False, f"Error: {e}")
        return False


def test_create_api_key():
    """Test creating an API key"""
    global API_KEY
    try:
        response = requests.post(
            f"{BASE_URL}/v1/keys",
            json={
                "tenant_id": "test_tenant",
                "name": "Test API Key"
            }
        )
        data = response.json()
        passed = response.status_code == 200 and "api_key" in data
        if passed:
            API_KEY = data["api_key"]
        print_test("POST /v1/keys", passed, f"Created key: {API_KEY[:20]}..." if API_KEY else "Failed")
        return passed
    except Exception as e:
        print_test("POST /v1/keys", False, f"Error: {e}")
        return False


def test_recall():
    """Test memory recall endpoint"""
    if not API_KEY:
        print_test("POST /v1/recall", False, "Skipped: No API key")
        return False

    try:
        response = requests.post(
            f"{BASE_URL}/v1/recall",
            headers={"X-API-Key": API_KEY},
            json={
                "message": "Tell me about machine learning",
                "max_concepts": 10
            }
        )
        data = response.json()
        passed = response.status_code == 200 and "context" in data
        print_test(
            "POST /v1/recall",
            passed,
            f"Concepts found: {data.get('concepts_found', 0)}, Time: {data.get('query_time_ms', 0):.2f}ms"
        )
        return passed
    except Exception as e:
        print_test("POST /v1/recall", False, f"Error: {e}")
        return False


def test_learn():
    """Test learning endpoint"""
    if not API_KEY:
        print_test("POST /v1/learn", False, "Skipped: No API key")
        return False

    try:
        response = requests.post(
            f"{BASE_URL}/v1/learn",
            headers={"X-API-Key": API_KEY},
            json={
                "user_message": "What is quantum computing?",
                "ai_response": "Quantum computing uses quantum mechanics principles like superposition and entanglement to process information.",
                "metadata": {
                    "session_id": "test_session",
                    "timestamp": "2025-12-07T00:00:00Z"
                }
            }
        )
        data = response.json()
        passed = response.status_code == 200 and "concepts_extracted" in data
        print_test(
            "POST /v1/learn",
            passed,
            f"Concepts: {data.get('concepts_extracted', 0)}, Decisions: {data.get('decisions_detected', 0)}"
        )
        return passed
    except Exception as e:
        print_test("POST /v1/learn", False, f"Error: {e}")
        return False


def test_turn():
    """Test turn endpoint (combined recall + learn)"""
    if not API_KEY:
        print_test("POST /v1/turn", False, "Skipped: No API key")
        return False

    try:
        response = requests.post(
            f"{BASE_URL}/v1/turn",
            headers={"X-API-Key": API_KEY},
            json={
                "user_message": "Explain neural networks",
                "ai_response": "Neural networks are computational models inspired by biological neurons that learn patterns from data.",
                "max_concepts": 10,
                "metadata": {
                    "session_id": "test_session"
                }
            }
        )
        data = response.json()
        passed = response.status_code == 200 and "recall" in data and "learn" in data
        print_test(
            "POST /v1/turn",
            passed,
            f"Recall concepts: {data.get('recall', {}).get('concepts_found', 0)}, Learn concepts: {data.get('learn', {}).get('concepts_extracted', 0)}"
        )
        return passed
    except Exception as e:
        print_test("POST /v1/turn", False, f"Error: {e}")
        return False


def test_stats():
    """Test stats endpoint"""
    if not API_KEY:
        print_test("GET /v1/stats", False, "Skipped: No API key")
        return False

    try:
        response = requests.get(
            f"{BASE_URL}/v1/stats",
            headers={"X-API-Key": API_KEY}
        )
        data = response.json()
        passed = response.status_code == 200 and "entities" in data
        print_test(
            "GET /v1/stats",
            passed,
            f"Entities: {data.get('entities', 0)}, Messages: {data.get('messages', 0)}"
        )
        return passed
    except Exception as e:
        print_test("GET /v1/stats", False, f"Error: {e}")
        return False


def test_entities():
    """Test entities listing endpoint"""
    if not API_KEY:
        print_test("GET /v1/entities", False, "Skipped: No API key")
        return False

    try:
        response = requests.get(
            f"{BASE_URL}/v1/entities?limit=10",
            headers={"X-API-Key": API_KEY}
        )
        data = response.json()
        passed = response.status_code == 200 and "entities" in data and "total" in data
        print_test(
            "GET /v1/entities",
            passed,
            f"Total entities: {data.get('total', 0)}, Returned: {len(data.get('entities', []))}"
        )
        return passed
    except Exception as e:
        print_test("GET /v1/entities", False, f"Error: {e}")
        return False


def test_tenants():
    """Test tenants listing endpoint"""
    if not API_KEY:
        print_test("GET /v1/tenants", False, "Skipped: No API key")
        return False

    try:
        response = requests.get(
            f"{BASE_URL}/v1/tenants",
            headers={"X-API-Key": API_KEY}
        )
        data = response.json()
        passed = response.status_code == 200 and "tenants" in data
        print_test(
            "GET /v1/tenants",
            passed,
            f"Tenants: {len(data.get('tenants', []))}"
        )
        return passed
    except Exception as e:
        print_test("GET /v1/tenants", False, f"Error: {e}")
        return False


def test_billing_subscription():
    """Test billing subscription status endpoint"""
    if not API_KEY:
        print_test("GET /v1/billing/subscription", False, "Skipped: No API key")
        return False

    try:
        response = requests.get(
            f"{BASE_URL}/v1/billing/subscription",
            headers={"X-API-Key": API_KEY}
        )
        data = response.json()
        passed = response.status_code == 200 and "tier" in data
        print_test(
            "GET /v1/billing/subscription",
            passed,
            f"Tier: {data.get('tier')}, Status: {data.get('status')}"
        )
        return passed
    except Exception as e:
        print_test("GET /v1/billing/subscription", False, f"Error: {e}")
        return False


def test_billing_checkout():
    """Test billing checkout session creation"""
    if not API_KEY:
        print_test("POST /v1/billing/create-checkout-session", False, "Skipped: No API key")
        return False

    try:
        # This should fail with 400 because we're requesting free tier
        response = requests.post(
            f"{BASE_URL}/v1/billing/create-checkout-session",
            headers={"X-API-Key": API_KEY},
            json={
                "tier": "free",
                "success_url": "http://localhost:3000/success",
                "cancel_url": "http://localhost:3000/cancel"
            }
        )
        # We expect 400 error for free tier
        passed = response.status_code == 400
        print_test(
            "POST /v1/billing/create-checkout-session",
            passed,
            "Correctly rejected free tier checkout"
        )
        return passed
    except Exception as e:
        print_test("POST /v1/billing/create-checkout-session", False, f"Error: {e}")
        return False


def test_docs():
    """Test that API documentation is accessible"""
    try:
        response = requests.get(f"{BASE_URL}/docs")
        passed = response.status_code == 200
        print_test("GET /docs", passed, "Swagger UI accessible")
        return passed
    except Exception as e:
        print_test("GET /docs", False, f"Error: {e}")
        return False


def test_redoc():
    """Test that ReDoc documentation is accessible"""
    try:
        response = requests.get(f"{BASE_URL}/redoc")
        passed = response.status_code == 200
        print_test("GET /redoc", passed, "ReDoc accessible")
        return passed
    except Exception as e:
        print_test("GET /redoc", False, f"Error: {e}")
        return False


def main():
    """Run all tests"""
    print("=" * 70)
    print("CONTINUUM API ENDPOINT TESTS")
    print("=" * 70)
    print()

    # Wait for server to be ready
    print("Waiting for server to be ready...")
    max_retries = 30
    for i in range(max_retries):
        try:
            response = requests.get(f"{BASE_URL}/v1/health", timeout=1)
            if response.status_code == 200:
                print("Server is ready!")
                break
        except:
            pass
        time.sleep(1)
    else:
        print("ERROR: Server did not start in time")
        return

    print()

    # Run tests
    tests = [
        ("Core Endpoints", [
            test_root,
            test_health,
            test_docs,
            test_redoc,
        ]),
        ("Authentication", [
            test_create_api_key,
        ]),
        ("Memory Operations", [
            test_recall,
            test_learn,
            test_turn,
        ]),
        ("Statistics & Information", [
            test_stats,
            test_entities,
            test_tenants,
        ]),
        ("Billing", [
            test_billing_subscription,
            test_billing_checkout,
        ])
    ]

    total_tests = 0
    passed_tests = 0

    for category, category_tests in tests:
        print(f"\n{category}")
        print("-" * 70)
        for test_func in category_tests:
            total_tests += 1
            if test_func():
                passed_tests += 1

    # Summary
    print()
    print("=" * 70)
    print(f"SUMMARY: {passed_tests}/{total_tests} tests passed")
    print("=" * 70)

    return passed_tests == total_tests


if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
