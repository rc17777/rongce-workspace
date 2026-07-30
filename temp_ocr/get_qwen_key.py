import json

with open(r'C:\Users\scrccpa\.openclaw\openclaw.json', 'r') as f:
    config = json.load(f)

for provider in config.get('models', {}).get('providers', []):
    for model in provider.get('models', []):
        mid = model.get('id', '')
        if 'qwen' in mid.lower():
            key = model.get('apiKey', '')
            print(f'baseUrl: {provider.get("baseUrl")}')
            print(f'model: {mid}')
            print(f'key_len: {len(key)}')
            break
