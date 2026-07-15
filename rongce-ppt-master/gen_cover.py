"""gpt-image-2 封面主视觉生成 — 轻奢暗金风格"""
import json
import base64
import sys
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")

cfg = json.load(open(r"C:\Users\scrccpa\.openclaw\openclaw.json", encoding="utf-8"))
p = cfg["models"]["providers"]["custom-cbwyy-image"]
KEY = p["apiKey"]
BASE = p["baseUrl"].rstrip("/")

PROMPT = (
    "Abstract luxury business background, dark navy-charcoal gradient (#1A1A2E to #12121F), "
    "elegant champagne gold (#D4AF37) flowing light streams and thin geometric lines, "
    "subtle golden particles, premium corporate aesthetic, minimal, sophisticated, "
    "cinematic lighting, high-end financial services brand feel, "
    "wide 16:9 composition, empty center area for title text, no text, no letters, no logo"
)

def try_images_api():
    url = BASE + "/v1/images/generations"
    body = json.dumps({
        "model": "gpt-image-2",
        "prompt": PROMPT,
        "size": "1536x1024",
        "n": 1,
    }).encode()
    req = urllib.request.Request(url, data=body, headers={
        "Authorization": f"Bearer {KEY}",
        "Content-Type": "application/json",
    })
    with urllib.request.urlopen(req, timeout=300) as r:
        return json.loads(r.read())

try:
    data = try_images_api()
    item = data["data"][0]
    if "b64_json" in item and item["b64_json"]:
        img = base64.b64decode(item["b64_json"])
        out = r"C:\Users\scrccpa\.openclaw\workspace\rongce-ppt-master\cover_ai.png"
        open(out, "wb").write(img)
        print("SAVED b64:", out, len(img), "bytes")
    elif "url" in item and item["url"]:
        print("URL:", item["url"])
        urllib.request.urlretrieve(item["url"], r"C:\Users\scrccpa\.openclaw\workspace\rongce-ppt-master\cover_ai.png")
        print("SAVED from url")
    else:
        print("UNKNOWN RESPONSE:", json.dumps(data)[:500])
except Exception as e:
    print("IMAGES API FAILED:", repr(e)[:300])
    if hasattr(e, "read"):
        try:
            print("BODY:", e.read().decode()[:500])
        except Exception:
            pass
