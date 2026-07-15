"""抓取 Wei-Shaw/sub2api README"""
import base64
import json
import sys
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")

def gh(url):
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/vnd.github+json",
    })
    return json.loads(urllib.request.urlopen(req, timeout=30).read())

data = gh("https://api.github.com/repos/Wei-Shaw/sub2api/readme")
content = base64.b64decode(data["content"]).decode("utf-8")
out = r"C:\Users\scrccpa\.openclaw\workspace\output\sub2api_readme.md"
open(out, "w", encoding="utf-8").write(content)
print("saved:", out, len(content), "chars")
print("=" * 60)
print(content[:3000])
