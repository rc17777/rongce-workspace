"""Generate brochure cover background via GPT-image-2. No text, atmosphere only."""
import os, sys, json, base64, time
sys.stdout.reconfigure(encoding='utf-8')
from openai import OpenAI

client = OpenAI(
    api_key="sk-KVp2E6u9FnnRA3BQxSNvbWKW6zd2JsDQa8YlmR4ZxGtVsXIQ",
    base_url="https://cbwyy.top/v1",
)

OUT = r"C:\Users\scrccpa\.openclaw\workspace\archive\huashu-demo\output\cover-bg-gpt-image-2.png"

prompt = """A premium, luxurious print brochure cover background for a Chinese government auditing and fiscal governance firm. 

Design language: sophisticated, authoritative, trustworthy, institutional. NOT tech-startup, NOT cyber-security, NOT sci-fi.

Color palette: deep navy blue (#0A1F3F dominant), warm copper/gold (#C5955C accents), subtle warm grey undertones.

Composition: abstract geometric composition suggesting protection, structure, evidence, governance. Elements could include:
- A subtle shield-like protective form emerging from the deep navy background
- Fine golden lines suggesting data flows, evidence chains, fiscal fund tracking
- Concentric ring motifs suggesting comprehensive coverage and oversight
- Subtle grid or architectural structural elements suggesting order, discipline, system
- Warm golden light gradient glowing from upper-right corner

Mood: calm authority, institutional gravitas, quiet competence. Like a luxury law firm or top-tier consulting firm brochure.

IMPORTANT: This is a BACKGROUND ONLY. No text, no Chinese characters, no letters, no numbers. Pure atmospheric abstract composition. Clean negative space in the center and top area where text will be placed later. A4 vertical proportions.

Style reference: premium consulting firm capability brochure covers, think McKinsey/BCG/Deloitte quality level, but abstracted to a background texture."""

for size in ["1024x1536", "1536x1024"]:
    try:
        resp = client.images.generate(
            model="gpt-image-2",
            prompt=prompt,
            n=1,
            size=size,
            response_format="b64_json",
        )
        b64 = resp.data[0].b64_json
        raw = base64.b64decode(b64)
        out_path = OUT.replace(".png", f"-{size.replace('x','x')}.png")
        with open(out_path, "wb") as f:
            f.write(raw)
        print(f"OK {size} -> {out_path} ({len(raw)} bytes)")
    except Exception as e:
        print(f"FAIL {size}: {e}")
