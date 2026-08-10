"""Verify DeepSeek official API key"""
import requests

headers = {'Authorization': 'Bearer sk-d0c4a018dad44f3e94eee4a0f0e4ee2b'}

# Test models endpoint
print('=== Testing DeepSeek Official API ===')
r = requests.get('https://api.deepseek.com/models', headers=headers, timeout=10)
print(f'Models endpoint: {r.status_code}')
if r.status_code == 200:
    models = r.json().get('data', [])
    ids = [m['id'] for m in models[:5]]
    print(f'Available models: {ids}')
else:
    print(f'Error: {r.text[:200]}')

# Test chat completion
print()
r2 = requests.post('https://api.deepseek.com/chat/completions',
    headers={**headers, 'Content-Type': 'application/json'},
    json={'model': 'deepseek-chat', 'messages': [{'role':'user','content':'Say hi in one word'}], 'stream': True},
    timeout=30, stream=True)
print(f'Chat completions: {r2.status_code}')
if r2.status_code == 200:
    chunks = sum(1 for _ in r2.iter_lines(decode_unicode=True) if _)
    print(f'Stream OK: {chunks} events received')
else:
    print(f'Error: {r2.text[:200]}')

# Test responses API (if supported)
print()
r3 = requests.post('https://api.deepseek.com/v1/responses',
    headers={**headers, 'Content-Type': 'application/json'},
    json={'model': 'deepseek-chat', 'input': 'hi', 'stream': True},
    timeout=30, stream=True)
print(f'Responses API: {r3.status_code}')
if r3.status_code == 200:
    chunks = sum(1 for _ in r3.iter_lines(decode_unicode=True) if _)
    print(f'Stream OK: {chunks} events')
elif r3.status_code == 404:
    print('  -> Not supported (expected, use chat/completions instead)')
else:
    print(f'Error: {r3.text[:200]}')
