import json
with open(r'D:\openclaw-workspace\scripts\wx_articles_batch1.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
t = type(data)
print(f"Type: {t}")
if isinstance(data, list):
    print(f"Entries: {len(data)}")
    for i, item in enumerate(data[:3]):
        print(f"{i}: {item.get('title','?')[:60]}")
    print("...")
elif isinstance(data, dict):
    keys = list(data.keys())
    print(f"Keys: {len(keys)}, first 5: {keys[:5]}")
