import json, subprocess, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
result = subprocess.run(
    ["curl.exe", "-s", "https://api.github.com/repos/OneClaw/OneClaw/releases?per_page=5"],
    capture_output=True, text=True, timeout=15
)
try:
    data = json.loads(result.stdout)
    if "message" in data:
        print(f"API error: {data['message']}")
    else:
        for r in data:
            tag = r.get("tag_name", "?")
            pre = r.get("prerelease", False)
            print(f'{tag} {"(beta)" if pre else "(stable)"}')
except:
    print(f"No OneClaw repo found or JSON parse error")
    print(f"Response: {result.stdout[:200]}")
