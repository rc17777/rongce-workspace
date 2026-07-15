"""gpt-image-2 封面生成 v2 — chat completions 端点 + 重试"""
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
OUT = r"C:\Users\scrccpa\.openclaw\workspace\rongce-ppt-master\cover_ai.png"

PROMPT = (
    "Abstract luxury business background image, 16:9 widescreen. Dark navy-charcoal gradient "
    "from #1A1A2E to #12121F, elegant champagne gold #D4AF37 flowing light streams and thin "
    "geometric lines, subtle golden particles, premium corporate aesthetic, minimal and "
    "sophisticated, cinematic lighting, high-end financial services brand feel, "
    "keep the center area darker and empty for title text overlay. No text, no letters, no logo."
)

def post(url, body, timeout=280):
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={
        "Authorization": f"Bearer {KEY}",
        "Content-Type": "application/json",
    })
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())

def save_from_url(u):
    urllib.request.urlretrieve(u, OUT)
    print("SAVED from url:", OUT)

def try_chat():
    data = post(BASE + "/v1/chat/completions", {
        "model": "gpt-image-2",
        "messages": [{"role": "user", "content": PROMPT}],
    })
    msg = data["choices"][0]["message"]
    content = msg.get("content") or ""
    # look for image in content: markdown ![..](url) or data uri
    m = re.search(r"\((https?://[^)]+)\)", content)
    if m:
        save_from_url(m.group(1))
        return True
    m = re.search(r"data:image/\w+;base64,([A-Za-z0-9+/=]+)", content)
    if m:
        open(OUT, "wb").write(base64.b64decode(m.group(1)))
        print("SAVED b64 from chat:", OUT)
        return True
    # some proxies use images array in message
    imgs = msg.get("images") or []
    if imgs:
        u = imgs[0].get("image_url", {}).get("url", "")
        if u.startswith("data:"):
            b64 = u.split(",", 1)[1]
            open(OUT, "wb").write(base64.b64decode(b64))
            print("SAVED b64 images[]:", OUT)
            return True
        elif u:
            save_from_url(u)
            return True
    print("CHAT RESPONSE (no image):", content[:300])
    return False

def try_images(size):
    data = post(BASE + "/v1/images/generations", {
        "model": "gpt-image-2", "prompt": PROMPT, "size": size, "n": 1,
    })
    item = data["data"][0]
    if item.get("b64_json"):
        open(OUT, "wb").write(base64.b64decode(item["b64_json"]))
        print("SAVED b64:", OUT)
        return True
    if item.get("url"):
        save_from_url(item["url"])
        return True
    return False

for attempt in range(3):
    print(f"--- attempt {attempt+1} ---")
    try:
        if try_chat():
            break
    except Exception as e:
        print("chat failed:", repr(e)[:200])
    try:
        if try_images("1024x1024" if attempt else "1536x1024"):
            break
    except Exception as e:
        print("images failed:", repr(e)[:200])
    time.sleep(5)
else:
    print("ALL ATTEMPTS FAILED")
