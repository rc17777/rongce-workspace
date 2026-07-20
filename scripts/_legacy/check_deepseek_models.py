import urllib.request, json, ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# Check DeepSeek official models list
req = urllib.request.Request(
    'https://api.deepseek.com/models',
    headers={
        'Authorization': 'Bearer sk-4253399e4b624bee87b2b248d80731f7'
    }
)
try:
    with urllib.request.urlopen(req, context=ctx, timeout=15) as resp:
        data = json.loads(resp.read().decode('utf-8'))
        print('Available models:')
        for m in data.get('data', []):
            print(f"  - {m.get('id', 'unknown')}")
except Exception as e:
    print(f'Error: {e}')
