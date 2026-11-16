#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test script for Unified Server - Test AI responses and API endpoints
"""
import requests
import json
import sys

BASE_URL = "http://localhost:8001"

def test_health():
    """Test health endpoint"""
    print("\n=== Testing /api/health ===")
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=5)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_tool_status():
    """Test Tool Open status endpoint"""
    print("\n=== Testing /api/tool-status ===")
    try:
        response = requests.get(f"{BASE_URL}/api/tool-status", timeout=5)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_socket_ping():
    """Test Socket API with PING request"""
    print("\n=== Testing /api/socket (PING) ===")
    try:
        payload = {"request": "PING"}
        response = requests.post(f"{BASE_URL}/api/socket", json=payload, timeout=5)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        return response.text == "PONG"
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_login():
    """Test login endpoint"""
    print("\n=== Testing /api/login ===")
    try:
        # Try default admin user
        payload = {
            "username": "admin",
            "password": "admin123"
        }
        response = requests.post(f"{BASE_URL}/api/login", json=payload, timeout=5)
        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
        return data.get('success', False)
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_get_users():
    """Test get users endpoint (requires auth)"""
    print("\n=== Testing /api/users (with token) ===")
    try:
        # Login first to get token
        login_payload = {"username": "admin", "password": "admin123"}
        login_resp = requests.post(f"{BASE_URL}/api/login", json=login_payload, timeout=5)
        if login_resp.status_code != 200:
            print("Login failed, cannot test GET_USERS")
            return False

        token = login_resp.json().get('token')
        headers = {"Authorization": f"Bearer {token}"}

        # Send GET_USERS request via socket API
        payload = {"request": "GET_USERS"}
        response = requests.post(f"{BASE_URL}/api/socket", json=payload, headers=headers, timeout=5)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_tool_search():
    """Test Tool Open search (AI integration)"""
    print("\n=== Testing /api/tool-search ===")
    try:
        # Test with a sample material code
        payload = {"code": "WLJ-001"}  # Example material code
        response = requests.post(f"{BASE_URL}/api/tool-search", json=payload, timeout=10)
        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"Response type: {data.get('type', 'unknown')}")
        print(f"Message: {data.get('message', 'No message')}")
        if data.get('type') == 'success':
            print(f"URLs found: {len(data.get('urls', []))}")
        elif data.get('type') == 'multiple':
            print(f"Matches: {len(data.get('matches', []))}")
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

def main():
    print("=" * 60)
    print("Unified Server API Test Suite")
    print("=" * 60)

    results = []

    # Test 1: Health check
    results.append(("Health Check", test_health()))

    # Test 2: Tool Status (shows AI/Tool Open availability)
    results.append(("Tool Open Status", test_tool_status()))

    # Test 3: Socket PING
    results.append(("Socket PING", test_socket_ping()))

    # Test 4: Login
    results.append(("Login", test_login()))

    # Test 5: Get Users
    results.append(("Get Users", test_get_users()))

    # Test 6: Tool Search (AI integration)
    results.append(("Tool Search (AI)", test_tool_search()))

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{name:.<40} {status}")

    passed_count = sum(1 for _, p in results if p)
    total_count = len(results)
    print(f"\nTotal: {passed_count}/{total_count} tests passed")

    return 0 if passed_count == total_count else 1

if __name__ == "__main__":
    sys.exit(main())
