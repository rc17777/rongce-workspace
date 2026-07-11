import requests, re, sys

url = sys.argv[1]
s = requests.Session()
s.trust_env = False
r = s.get(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}, timeout=15)
print(f"Status: {r.status_code}, length: {len(r.text)}")

# Find js_content
m = re.search(r'id="js_content"[^>]*>(.*?)</div>\s*<script', r.text, re.DOTALL)
if m:
    content = m.group(1)
    # Strip HTML tags
    content = re.sub(r'<[^>]+>', '', content)
    content = re.sub(r'&nbsp;', ' ', content)
    content = re.sub(r'&amp;', '&', content)
    content = re.sub(r'&lt;', '<', content)
    content = re.sub(r'&gt;', '>', content)
    content = re.sub(r'&quot;', '"', content)
    content = re.sub(r'\n{2,}', '\n', content).strip()
    print(f"Content length: {len(content)}")
    print(content[:4000])
else:
    print("js_content NOT FOUND")
    # Try finding the title
    tm = re.search(r'<title>(.*?)</title>', r.text)
    if tm: print(f"Title: {tm.group(1)}")
    # Try activity-name
    am = re.search(r'activity-name[^>]*>(.*?)</', r.text)
    if am: print(f"Activity: {am.group(1)}")
