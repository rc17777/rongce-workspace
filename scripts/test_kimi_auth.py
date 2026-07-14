import requests
import json

# Test 1: Direct OpenAI format (no auth)
print("=== Test 1: No auth ===")
try:
    r = requests.post(
        'http://127.0.0.1:18790/coding/v1/chat/completions',
        json={
            'model': 'kimi-k2.7',
            'messages': [{'role': 'user', 'content': 'hi'}],
            'max_tokens': 10
        },
        headers={'Content-Type': 'application/json'},
        timeout=10
    )
    print(f"Status: {r.status_code}")
    print(f"Response: {r.text[:200]}")
except Exception as e:
    print(f"Error: {e}")

print()

# Test 2: With Bearer token
print("=== Test 2: With Bearer token ===")
try:
    r = requests.post(
        'http://127.0.0.1:18790/coding/v1/chat/completions',
        json={
            'model': 'kimi-k2.7',
            'messages': [{'role': 'user', 'content': 'hi'}],
            'max_tokens': 10
        },
        headers={
            'Content-Type': 'application/json',
            'Authorization': 'Bearer test-key'
        },
        timeout=10
    )
    print(f"Status: {r.status_code}")
    print(f"Response: {r.text[:200]}")
except Exception as e:
    print(f"Error: {e}")

print()

# Test 3: With x-api-key header
print("=== Test 3: With x-api-key header ===")
try:
    r = requests.post(
        'http://127.0.0.1:18790/coding/v1/chat/completions',
        json={
            'model': 'kimi-k2.7',
            'messages': [{'role': 'user', 'content': 'hi'}],
            'max_tokens': 10
        },
        headers={
            'Content-Type': 'application/json',
            'x-api-key': 'test-key'
        },
        timeout=10
    )
    print(f"Status: {r.status_code}")
    print(f"Response: {r.text[:200]}")
except Exception as e:
    print(f"Error: {e}")

print()

# Test 4: Anthropic format (no auth)
print("=== Test 4: Anthropic format (no auth) ===")
try:
    r = requests.post(
        'http://127.0.0.1:18790/coding/v1/messages',
        json={
            'model': 'kimi-k2.7',
            'messages': [{'role': 'user', 'content': 'hi'}],
            'max_tokens': 10
        },
        headers={'Content-Type': 'application/json'},
        timeout=10
    )
    print(f"Status: {r.status_code}")
    print(f"Response: {r.text[:200]}")
except Exception as e:
    print(f"Error: {e}")
