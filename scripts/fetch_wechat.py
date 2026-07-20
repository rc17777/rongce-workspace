import sys, re, html, subprocess

url = "https://mp.weixin.qq.com/s/zY45HqTpqys2FprA-S0mjg"
ua = "Mozilla/5.0 (Linux; Android 13; SM-S9080) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.230 Mobile Safari/537.36 MicroMessenger/8.0.47"

result = subprocess.run(
    ["curl", "-s", "-L", "-A", ua, url],
    capture_output=True, text=True, encoding="utf-8"
)
content = result.stdout

# Extract title
m = re.search(r'var\s+msg_title\s*=\s*["\x27](.*?)["\x27]', content)
title = html.unescape(m.group(1)) if m else "N/A"

# Extract content from js_content div
m2 = re.search(r'id=["\x27]js_content["\x27][^>]*>(.*?)</div>', content, re.DOTALL)
if not m2:
    m2 = re.search(r'class=["\x27]rich_media_content["\x27][^>]*>(.*?)</div>', content, re.DOTALL)

body = m2.group(1) if m2 else "N/A"
# Strip HTML tags
body = re.sub(r'<[^>]+>', '\n', body)
body = re.sub(r'\n{3,}', '\n\n', body).strip()
body = html.unescape(body)

print(f"TITLE: {title}")
print(f"LENGTH: {len(body)}")
print("---BODY---")
print(body[:12000])
