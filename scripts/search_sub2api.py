"""GitHub 搜索 sub2api 项目"""
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

data = gh("https://api.github.com/search/repositories?q=sub2api&sort=stars&order=desc&per_page=10")
print("total:", data.get("total_count"))
print("=" * 90)
for r in data.get("items", []):
    desc = (r.get("description") or "").replace("\n", " ")[:90]
    print(f"{r['full_name']:<40} ⭐{r['stargazers_count']:<6} {str(r.get('language')):<10} 更新:{r['updated_at'][:10]}")
    print(f"   {desc}")
    print(f"   {r['html_url']}")
    print("-" * 90)
