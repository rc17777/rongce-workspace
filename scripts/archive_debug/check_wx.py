import json
with open(r'D:\openclaw-workspace\scripts\wx_all_urls.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
for i, item in enumerate(data):
    if 47 <= i <= 55:
        print(f"Index {i}: {item.get('title','?')} | mark={item.get('mark','')}")
