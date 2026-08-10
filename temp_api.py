import urllib.request, json, sys
sys.stdout.reconfigure(encoding='utf-8')

url = 'https://www.douyin.com/aweme/v1/web/aweme/detail/?aweme_id=7670575694153866217'
headers = {
    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15',
    'Referer': 'https://www.douyin.com/',
}

req = urllib.request.Request(url, headers=headers)
try:
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode('utf-8'))
        aweme = data.get('aweme_detail', {})
        print('desc:', aweme.get('desc', 'N/A'))
        print('create_time:', aweme.get('create_time', 'N/A'))
        author = aweme.get('author', {})
        print('author nickname:', author.get('nickname', 'N/A'))
        print('author signature:', author.get('signature', 'N/A'))
        stats = aweme.get('statistics', {})
        print('stats:', json.dumps(stats, ensure_ascii=False))
        text_extra = aweme.get('text_extra', [])
        for t in text_extra:
            print('  tag:', t.get('hashtag_name', ''))
except Exception as e:
    print('API error:', e)

# Also try with different referer
url2 = 'https://www.iesdouyin.com/web/api/v2/aweme/iteminfo/?item_ids=7670575694153866217'
headers2 = {
    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15',
    'Referer': 'https://www.iesdouyin.com/',
}
try:
    req2 = urllib.request.Request(url2, headers=headers2)
    with urllib.request.urlopen(req2, timeout=15) as resp:
        data2 = json.loads(resp.read().decode('utf-8'))
        print('\n=== API v2 ===')
        items = data2.get('item_list', [])
        for item in items:
            print('desc:', item.get('desc', 'N/A'))
            author = item.get('author', {})
            print('nickname:', author.get('nickname', 'N/A'))
            print('signature:', author.get('signature', 'N/A'))
            stats = item.get('statistics', {})
            print('stats:', json.dumps(stats, ensure_ascii=False))
except Exception as e:
    print('API v2 error:', e)
