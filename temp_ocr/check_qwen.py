import json
with open(r'C:\Users\scrccpa\.openclaw\openclaw.json') as f:
    c = json.load(f)

# Check ALL providers for any VL/Vision/Max models
for pid, pdata in c['models']['providers'].items():
    for m in pdata.get('models', []):
        mid = m.get('id', '')
        if any(x in mid.lower() for x in ['vl', 'vision', 'max', 'omni']):
            key = m.get('apiKey', '')
            print(f'Provider: {pid}')
            print(f'model: {mid}')
            print(f'baseUrl: {pdata.get("baseUrl")}')
            print(f'key: {key[:10]}...{key[-4:]}')
            print()

# Also print all model IDs to find any vision model
print('=== All model IDs ===')
for pid, pdata in c['models']['providers'].items():
    for m in pdata.get('models', []):
        print(f'  [{pid}] {m.get("id")}')
