"""
微信文章抓取 + 溯源查询
"""
import sys, re, requests
sys.stdout.reconfigure(encoding='utf-8')

url = 'https://mp.weixin.qq.com/s/zY45HqTpqys2FprA-S0mjg'
headers = {
    'User-Agent': 'Mozilla/5.0 (Linux; Android 13; SM-S9080) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.230 Mobile Safari/537.36 MicroMessenger/8.0.47',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
}
r = requests.get(url, headers=headers, timeout=15)
html = r.text

# 标题
title = ''
m = re.search(r'var msg_title\s*=\s*[\'"]?(.+?)[\'"]?\s*;', html)
if m: title = m.group(1).strip('\'" ')
print(f'标题: {title}')

# 公众号
nickname = ''
m = re.search(r'var nickname\s*=\s*[\'"]?(.+?)[\'"]?\s*;', html)
if m: nickname = m.group(1).strip('\'" ')
print(f'公众号: {nickname}')

# 发布时间
ct = ''
m = re.search(r'var ct\s*=\s*[\'"]?(\d+)[\'"]?\s*;', html)
if m: ct = m.group(1)
print(f'发布时间戳: {ct}')

# 正文
content = ''
m = re.search(r'id="js_content"[^>]*>(.*?)</div>\s*<script', html, re.DOTALL)
if m:
    content = re.sub(r'<[^>]+>', '', m.group(1)).strip()
    content = re.sub(r'\s+', ' ', content)
    print(f'正文长度: {len(content)} 字')
    print(f'正文前300字: {content[:300]}')
else:
    print('正文提取失败')

# 搜索原始出处关键词
print()
print('='*50)
print('搜索原始出处...')
print('='*50)