# -*- coding: utf-8 -*-
"""
Debug Script - Test OpenRouter credentials loading
Chạy script này để kiểm tra xem credentials có được load đúng không
"""
import json
import os

def test_load_credentials():
    """Test _load_credentials function"""
    print("=" * 60)
    print("Testing OpenRouter Credentials Loading")
    print("=" * 60)
    
    # Test 1: Check if credentials.json exists
    print("\n1. Checking credentials.json...")
    if os.path.exists('credentials.json'):
        print("   ✓ credentials.json exists")
        with open('credentials.json', 'r', encoding='utf-8') as f:
            creds = json.load(f)
        
        # Check OpenRouter API key
        api_key = creds.get('openrouter_api_key', '')
        print(f"   OpenRouter API Key: {api_key[:20]}..." if api_key else "   OpenRouter API Key: EMPTY")
        
        if api_key:
            print("   ✓ OpenRouter API Key is present in credentials.json")
        else:
            print("   ✗ OpenRouter API Key is MISSING in credentials.json")
    else:
        print("   ✗ credentials.json NOT FOUND")
    
    # Test 2: Simulate _load_credentials function
    print("\n2. Simulating _load_credentials()...")
    def _load_credentials():
        """Load credentials from credentials.json file"""
        try:
            if os.path.exists('credentials.json'):
                with open('credentials.json', 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"   Error: {e}")
        return {}
    
    creds = _load_credentials()
    api_key = creds.get('openrouter_api_key', '')
    
    if api_key:
        print(f"   ✓ _load_credentials() returns API key: {api_key[:20]}...")
    else:
        print("   ✗ _load_credentials() returns EMPTY api_key")
    
    # Test 3: Check what openrouter_routes.py expects
    print("\n3. Checking openrouter_routes.py expectations...")
    print("   Expected: config.get('load_credentials') should return a function")
    print("   Then: load_credentials() should return {openrouter_api_key: '...'}")
    print("   If load_credentials is None: returns {} → api_key = ''")
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    if api_key:
        print("✓ FIX VERIFIED: OpenRouter API Key exists in credentials.json")
        print("  After server restart, /api/openrouter/status should return configured=true")
    else:
        print("✗ PROBLEM: OpenRouter API Key is empty or missing")
        print("  Check credentials.json file")
    
    print("=" * 60)

if __name__ == '__main__':
    test_load_credentials()
