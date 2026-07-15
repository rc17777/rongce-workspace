"""gpt-image-2 封底主视觉生成"""
import json
import base64
import re
import sys
import time
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")

cfg = json.load(open(r"C:\Users\scrccpa\.openclaw\openclaw.json", encoding="utf-8"))
p = cfg["models"]["providers"]["custom-cbwyy-image"]
KEY = p["apiKey"]
BASE = p["baseUrl"].rstrip("/")
OUT = r"C:\Users\scrccpa\.openclaw\workspace\rongce-ppt-master\backcover_ai.png"

PROMPT = (
    "Abstract luxury business background image, 16:9 widescreen, ultra detailed, high resolution. "
    "Dark navy-charcoal gradient from #1A1A2E to #12121F, elegant champagne gold #D4AF37 thin "
    "light lines converging toward a subtle glowing horizon at the lower third, delicate golden "
    "particles rising, premium corporate aesthetic, calm and symmetrical composition, minimal, "
    "sophisticated, cinematic lighting, high-end financial services brand feel, keep the upper "
    "center area darker and empty for text overlay. No text, no letters, no logo, no watermark."
)

def post(url, body, timeout=280):
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={
        "Authorization": f"Bearer {KEY}",
        "Content-Type": "application/json",
    })
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())

def try_chat():
    data = post(BASE + "/v1/chat/completions", {
        "model": "gpt-image-2",
        "messages": [{"role": "user", "content": PROMPT}],
    })
    msg = data["choices"][0]["message"]
    content = msg.get("content") or ""
    m = re.search(r"data:image/\w+;base64,([A-Za-z0-9+/=]+)", content)
    if m:
        open(OUT, "wb").write(base64.b64decode(m.group(1)))
        print("SAVED b64:", OUT)
        return True
    m = re.search(r"\((https?://[^)]+)\)", content)
    if m:
        urllib.request.urlretrieve(m.group(1), OUT)
        print("SAVED url:", OUT)
        return True
    imgs = msg.get("images") or []
    if imgs:
        u = imgs[0].get("image_url", {}).get("url", "")
        if u.startswith("data:"):
            open(OUT, "wb").write(base64.b64decode(u.split(",", 1)[1]))
            print("SAVED b64 images[]:", OUT)
            return True
    print("NO IMAGE:", content[:200])
    return False

for attempt in range(3):
    print(f"--- attempt {attempt+1} ---")
    try:
        if try_chat():
            break
    except Exception as e:
        print("failed:", repr(e)[:200])
    time.sleep(5)
else:
    print("ALL FAILED")
