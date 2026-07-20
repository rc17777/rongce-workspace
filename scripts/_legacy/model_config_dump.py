"""Dump provider configs for multi-model review"""
import json

with open(r'C:\Users\scrccpa\.openclaw\openclaw.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

providers = config.get('models', {}).get('providers', {})
models_list = config.get('models', {}).get('models', [])

for k, v in providers.items():
    key = v.get('apiKey', '')
    print(f"provider: {k}")
    print(f"  baseUrl: {v.get('baseUrl', '?')}")
    print(f"  apiType: {v.get('apiType', '?')}")
    print(f"  key_len: {len(key) if key else 0}")

print("\n--- Models ---")
for m in models_list:
    print(f"  {m.get('id', '?')}: provider={m.get('provider', '?')}")
