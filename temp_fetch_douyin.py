import urllib.request, re, json, sys
from urllib.parse import unquote

sys.stdout.reconfigure(encoding='utf-8')

video_id = '7670575694153866217'
video_url = f'https://www.douyin.com/video/{video_id}'

headers = {
    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1',
    'Accept': 'text/html,application/xhtml+xml',
    'Accept-Language': 'zh-CN,zh;q=0.9',
}

req = urllib.request.Request(video_url, headers=headers)
try:
    with urllib.request.urlopen(req, timeout=15) as resp:
        html = resp.read().decode('utf-8', errors='ignore')
        
        # Find RENDER_DATA
        scripts = re.findall(r'<script[^>]*id="RENDER_DATA"[^>]*>(.*?)</script>', html, re.DOTALL)
        print(f'RENDER_DATA scripts found: {len(scripts)}')
        
        if scripts:
            decoded = unquote(scripts[0])
            data = json.loads(decoded)
            
            # Deep search for description and content
            def deep_search_all(obj, target_keys, path='', depth=0, max_depth=12):
                results = []
                if depth > max_depth or not isinstance(obj, (dict, list)):
                    return results
                if isinstance(obj, dict):
                    for k, v in obj.items():
                        if k in target_keys:
                            results.append((f'{path}.{k}', v))
                        results.extend(deep_search_all(v, target_keys, f'{path}.{k}', depth+1, max_depth))
                elif isinstance(obj, list):
                    for i, item in enumerate(obj[:30]):
                        results.extend(deep_search_all(item, target_keys, f'{path}[{i}]', depth+1, max_depth))
                return results
            
            # Search broadly
            all_text = deep_search_all(data, 
                ['desc', 'videoDesc', 'textExtra', 'title', 'previewTitle', 
                 'shareDesc', 'caption', 'content', 'text', 'sentence',
                 'nickname', 'authorName', 'uniqueId', 'signature',
                 'hashtagName', 'tagName', 'musicTitle', 'musicAuthor'])
            
            for path, val in all_text:
                if isinstance(val, str) and len(val) > 1:
                    print(f'  {path}: {val[:500]}')
                elif isinstance(val, (int, float, bool)):
                    if val:
                        print(f'  {path}: {val}')
            
            # Also try to get the full video item structure
            def find_items(obj, depth=0):
                if depth > 8:
                    return
                if isinstance(obj, dict):
                    if 'aweme' in obj or 'video' in obj:
                        print(f'\n=== Found video/aweme at depth {depth} ===')
                        if 'desc' in obj:
                            print(f'desc: {obj["desc"]}')
                        for k in ['author', 'music', 'statistics', 'video']:
                            if k in obj:
                                v = obj[k]
                                if isinstance(v, dict):
                                    # Print key fields only
                                    sub = {sk: sv for sk, sv in v.items() 
                                           if isinstance(sv, (str, int, float, bool))}
                                    print(f'{k}: {json.dumps(sub, ensure_ascii=False)[:500]}')
                    for k, v in obj.items():
                        find_items(v, depth+1)

            find_items(data)
            
except Exception as e:
    print(f'Error: {e}')
