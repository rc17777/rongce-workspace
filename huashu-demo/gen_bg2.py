import json, requests, base64, sys, io, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def try_gen(provider, api_key, model, url):
    print(f'\n=== Trying {model} ===')
    payload = {
        'model': model,
        'messages': [{
            'role': 'user',
            'content': 'Generate a classical Chinese ink-wash style background image, 16:9 wide. Dark deep background, warm gold and muted jade-green tones. Ancient silk scroll texture. No text or characters. Serene, contemplative, artisan craftsmanship mood. High resolution.'
        }],
        'max_tokens': 4096
    }
    try:
        r = requests.post(url, headers={
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }, json=payload, timeout=300)
        print(f'Status: {r.status_code}')
        data = r.json()
        
        out_path = r'C:\Users\scrccpa\.openclaw\workspace\huashu-demo\shared\back-cover-bg.png'
        
        content = data.get('choices', [{}])[0].get('message', {}).get('content', '')
        if isinstance(content, list):
            for item in content:
                if isinstance(item, dict) and item.get('type') == 'image_url':
                    img = item.get('image_url', {}).get('url', '')
                    if img.startswith('data:'):
                        b64 = img.split(',', 1)[1]
                        with open(out_path, 'wb') as f: f.write(base64.b64decode(b64))
                        print(f'DONE: {out_path} ({os.path.getsize(out_path)/1024:.0f} KB)')
                        return True
                    elif img.startswith('http'):
                        ir = requests.get(img, timeout=60)
                        with open(out_path, 'wb') as f: f.write(ir.content)
                        print(f'DONE: {out_path} ({os.path.getsize(out_path)/1024:.0f} KB)')
                        return True
        
        # Check for image in choices message images field
        msg = data.get('choices', [{}])[0].get('message', {})
        if 'images' in msg:
            for img_data in msg['images']:
                b64 = img_data if isinstance(img_data, str) else img_data.get('b64_json', img_data.get('url', ''))
                if b64 and not b64.startswith('http'):
                    with open(out_path, 'wb') as f: f.write(base64.b64decode(b64))
                    print(f'DONE from images: {out_path} ({os.path.getsize(out_path)/1024:.0f} KB)')
                    return True
        
        # Debug
        with open(r'C:\Users\scrccpa\.openclaw\workspace\huashu-demo\output\img_debug.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        if isinstance(content, str) and content:
            print(f'Text only: {content[:150]}...')
        else:
            print(f'Keys: {list(data.keys())}')
            if 'choices' in data:
                c0 = data['choices'][0]
                print(f'Choice keys: {list(c0.keys())}')
                msg = c0.get('message', {})
                print(f'Msg keys: {list(msg.keys())}')
                print(f'Msg content type: {type(msg.get("content",""))}')
        return False
    except Exception as e:
        print(f'Error: {e}')
        return False

# Try doubao
doubao_key = 'sk-8Up5r8WtFOQrckhQCxOxaRYES5KAWQqgKMdrJng1l0DJ9gix'
if try_gen('doubao', doubao_key, 'doubao-seed-2.0-lite', 'https://cbwyy.top/v1/chat/completions'):
    sys.exit(0)

# Try qwen
qwen_key = 'sk-9Jwqw4U5ahchjaLgVqzvfJQvm3itJEv2GHTV8KAofagQrf77'
if try_gen('qwen', qwen_key, 'qwen3.7-plus', 'https://cbwyy.top/v1/chat/completions'):
    sys.exit(0)

print('\nBoth failed to generate images.')
