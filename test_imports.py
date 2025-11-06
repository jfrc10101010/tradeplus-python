#!/usr/bin/env python3

print("=== TESTING IMPORTS ===")

try:
    from flask import Flask, jsonify
    from flask_cors import CORS
    print("✅ Flask imports OK")
except Exception as e:
    print(f"❌ Flask imports FAILED: {e}")
    exit(1)

try:
    import json
    import jwt
    import time
    import requests
    print("✅ Standard imports OK")
except Exception as e:
    print(f"❌ Standard imports FAILED: {e}")
    exit(1)

try:
    from cryptography.hazmat.primitives import serialization
    print("✅ Cryptography imports OK")
except Exception as e:
    print(f"❌ Cryptography imports FAILED: {e}")
    exit(1)

try:
    with open('apicoinbase1fullcdp_api_key.json', 'r') as f:
        cb_config = json.load(f)
        COINBASE_API_KEY = cb_config['name']
        COINBASE_PRIVATE_KEY = cb_config['privateKey']
    print(f"✅ JSON config loaded OK - API Key: {COINBASE_API_KEY[:50]}...")
except Exception as e:
    print(f"❌ JSON config FAILED: {e}")
    exit(1)

try:
    key = serialization.load_pem_private_key(
        COINBASE_PRIVATE_KEY.encode(),
        password=None
    )
    print("✅ Private key loaded OK")
except Exception as e:
    print(f"❌ Private key FAILED: {e}")
    exit(1)

print("🎯 ALL TESTS PASSED - Server should work!")