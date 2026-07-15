"""升分辨率：Lanczos 放大到 3840 宽 + 轻锐化 + 轻降噪，打印友好"""
import sys
from PIL import Image, ImageFilter, ImageEnhance

sys.stdout.reconfigure(encoding="utf-8")

BASE = r"C:\Users\scrccpa\.openclaw\workspace\rongce-ppt-master"

def upscale(src, dst, target_w=3840):
    im = Image.open(src).convert("RGB")
    w, h = im.size
    scale = target_w / w
    new_size = (target_w, round(h * scale))
    # 轻微高斯模糊降噪（去 AI 生成的高频噪点），再 Lanczos 放大，再温和锐化
    im = im.filter(ImageFilter.GaussianBlur(0.4))
    im = im.resize(new_size, Image.LANCZOS)
    im = im.filter(ImageFilter.UnsharpMask(radius=2.2, percent=60, threshold=2))
    # 微降饱和抖动，减少打印色带
    im.save(dst, "PNG", optimize=False)
    print(f"{src} {w}x{h} -> {dst} {new_size[0]}x{new_size[1]}")

upscale(BASE + r"\cover_ai.png", BASE + r"\project\images\cover_ai.png")
upscale(BASE + r"\backcover_ai.png", BASE + r"\project\images\backcover_ai.png")
print("DONE")
