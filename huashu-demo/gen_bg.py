import json, requests, base64, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

url = 'https://cbwyy.top/v1/chat/completions'
headers = {
    'Authorization': 'Bearer sk-KVp2E6u9FnnRA3BQxSNvbWKW6zd2JsDQa8YlmR4ZxGtVsXIQ',
    'Content-Type': 'application/json'
}
payload = {
    'model': 'gpt-image-2',
    'messages': [{
        'role': 'user',
        'content': 'Generate a classical Chinese ink-wash style background image, 16:9 ratio. Theme: jade carving and polishing craftsmanship. Dark deep background, warm gold and muted jade-green tones. Ancient silk scroll texture. No text. Serene artisan atmosphere. Print quality.'
    }],
    'max_tokens': 4096
}

print('Sending request...')
try:
    r = requests.post(url, headers=headers, json=payload, timeout=300)
    print(f'Status: {r.status_code}')
    data = r.json()
    
    out_path = r'C:\Users\scrccpa\.openclaw\workspace\huashu-demo\shared\back-cover-bg.png'
    
    # Check for image in response
    content = data.get('choices', [{}])[0].get('message', {}).get('content', '')
    
    if isinstance(content, list):
        for item in content:
            if item.get('type') == 'image_url':
                img_url = item.get('image_url', {}).get('url', '')
                if img_url.startswith('data:'):
                    b64 = img_url.split(',', 1)[1]
                    with open(out_path, 'wb') as f:
                        f.write(base64.b64decode(b64))
                    import os
                    print(f'DONE: {out_path} ({os.path.getsize(out_path)/1024:.0f} KB)')
                elif img_url.startswith('http'):
                    ir = requests.get(img_url, timeout=60)
                    with open(out_path, 'wb') as f:
                        f.write(ir.content)
                    import os
                    print(f'DONE: {out_path} ({os.path.getsize(out_path)/1024:.0f} KB)')
                sys.exit(0)
    
    # Save full response for debug
    with open(r'C:\Users\scrccpa\.openclaw\workspace\huashu-demo\output\img_debug.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    if isinstance(content, str) and content:
        print(f'Content preview: {content[:200]}...')
    else:
        print('No image found in response')
        print(json.dumps(data, ensure_ascii=False, indent=2)[:500])
        
except Exception as e:
    print(f'Error: {e}')
