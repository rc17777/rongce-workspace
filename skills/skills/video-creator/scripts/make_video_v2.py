#!/usr/bin/env python3
"""make_video_v2.py - 改进版：Pillow渲染中文 -> FFmpeg纯拼接

用法:
  python make_video_v2.py --images ./slides --text captions.txt --audio bgm.mp3 --output demo.mp4
  python make_video_v2.py --images ./slides --text captions.txt --output demo.mp4 --vertical
"""

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def find_images(folder: Path) -> list[Path]:
    exts = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}
    return sorted([f for f in folder.iterdir() if f.suffix.lower() in exts], key=lambda x: x.name)


def load_captions(path: Path) -> list[str]:
    if path.suffix == ".json":
        import json
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
        return data.get("captions", data.get("texts", []))
    with open(path, encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


def get_duration(path: Path) -> float:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        capture_output=True, text=True,
    )
    return float(result.stdout.strip())


def overlay_text_on_image(img: Image.Image, text: str, font_path: str, w: int, h: int) -> Image.Image:
    """在图片底部叠加半透明黑底白字"""
    # Font sizes
    font_title = ImageFont.truetype(font_path, 42)
    font_body = ImageFont.truetype(font_path, 34)

    # 计算文字区域
    scale_factor = w / 1920.0

    # 自动换行
    max_width = int(w * 0.85)
    lines = []
    for paragraph in text.split("\n"):
        current = ""
        for char in paragraph:
            test = current + char
            bbox = font_body.getbbox(test)
            if bbox and bbox[2] > max_width:
                lines.append(current)
                current = char
            else:
                current = test
        if current:
            lines.append(current)

    # 文字区域背景高度
    line_height = int(50 * scale_factor)
    text_area_h = len(lines) * line_height + int(60 * scale_factor)
    y_start = h - text_area_h - int(40 * scale_factor)

    draw = ImageDraw.Draw(img)

    # 半透明黑底
    overlay = Image.new("RGBA", (max_width, text_area_h), (0, 0, 0, 180))
    img.paste(overlay, ((w - max_width) // 2, y_start), overlay)

    # 白色文字
    y = y_start + int(30 * scale_factor)
    for line in lines:
        bbox = font_body.getbbox(line)
        if bbox:
            x = (w - bbox[2]) // 2
            draw.text((x, y), line, font=font_body, fill="white")
        y += line_height

    return img


def make_slideshow(images: list[Path], captions: list[str], duration: float,
                   w: int, h: int, font_path: str, temp_dir: Path) -> list[Path]:
    """用Pillow渲染文字到图片 -> 保存为临时文件"""
    segments = []
    font_size = 42

    for i, img_path in enumerate(images):
        caption = captions[i] if i < len(captions) else ""

        # 打开图片，缩放到目标分辨率
        img = Image.open(img_path).convert("RGB")
        img = img.resize((w, h), Image.LANCZOS)

        # 叠加文字
        if caption:
            img = overlay_text_on_image(img, caption, font_path, w, h)

        # 保存带文字的图片
        out = temp_dir / f"slide_{i:03d}.png"
        img.save(out)

        # 生成视频片段
        seg = temp_dir / f"seg_{i:03d}.mp4"
        cmd = [
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", str(out),
            "-c:v", "libx264",
            "-t", str(duration),
            "-r", "30",
            "-pix_fmt", "yuv420p",
            str(seg),
        ]
        subprocess.run(cmd, capture_output=True, check=True)
        segments.append(seg)

    return segments


def concat_segments(segments: list[Path], output: Path) -> None:
    """拼接所有片段"""
    concat_list = output.parent / "concat_list.txt"
    with open(concat_list, "w") as f:
        for seg in segments:
            f.write(f"file '{seg.as_posix()}'\n")

    subprocess.run(
        ["ffmpeg", "-y", "-f", "concat", "-safe", "0",
         "-i", str(concat_list), "-c", "copy", str(output)],
        capture_output=True, check=True,
    )


def mix_audio(video: Path, audio: Path, output: Path) -> None:
    video_dur = get_duration(video)
    audio_dur = get_duration(audio)

    cmd = [
        "ffmpeg", "-y",
        "-i", str(video),
    ]
    if audio_dur < video_dur:
        cmd += ["-stream_loop", "-1"]
    cmd += [
        "-i", str(audio),
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "128k",
        "-filter:a", "volume=0.3",
        "-shortest",
        "-map", "0:v:0", "-map", "1:a:0",
        str(output),
    ]
    subprocess.run(cmd, capture_output=True, check=True)


def to_vertical(video: Path, output: Path) -> None:
    cmd = [
        "ffmpeg", "-y",
        "-i", str(video),
        "-vf", "crop=ih*9/16:ih,scale=1080:1920",
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "128k",
        str(output),
    ]
    subprocess.run(cmd, capture_output=True, check=True)


def main():
    parser = argparse.ArgumentParser(description="Video maker v2 - Pillow Chinese text + FFmpeg slideshow")
    parser.add_argument("--images", required=True)
    parser.add_argument("--text", required=True)
    parser.add_argument("--audio")
    parser.add_argument("--output", default="output.mp4")
    parser.add_argument("--vertical", action="store_true")
    parser.add_argument("--duration", type=float, default=3.0)
    parser.add_argument("--font", default="C:/Windows/Fonts/simhei.ttf")
    parser.add_argument("--resolution", default="1920x1080")
    args = parser.parse_args()

    images_dir = Path(args.images)
    text_file = Path(args.text)
    audio_file = Path(args.audio) if args.audio else None
    output = Path(args.output)

    images = find_images(images_dir)
    captions = load_captions(text_file)

    print(f"[IMAGES] {len(images)} images, [TEXT] {len(captions)} captions")

    w, h = map(int, args.resolution.split("x"))
    if args.vertical:
        w, h = 1080, 1920

    with tempfile.TemporaryDirectory(prefix="vc_") as tmp:
        temp_dir = Path(tmp)

        print("[RENDER] Overlaying text on images...")
        segments = make_slideshow(images, captions, args.duration, w, h, args.font, temp_dir)

        print("[CONCAT] Joining segments...")
        slideshow = temp_dir / "slideshow.mp4"
        concat_segments(segments, slideshow)
        print(f"  Slideshow: {get_duration(slideshow):.1f}s")

        if audio_file:
            print("[AUDIO] Mixing BGM...")
            mixed = temp_dir / "mixed.mp4"
            mix_audio(slideshow, audio_file, mixed)
            slideshow = mixed

        if args.vertical:
            print("[VERTICAL] Cropping to 9:16...")
            to_vertical(slideshow, output)
        else:
            import shutil
            shutil.copy(slideshow, output)

        dur = get_duration(output)
        size_mb = output.stat().st_size / (1024 * 1024)
        print(f"[DONE] {output}  ({size_mb:.1f}MB, {dur:.0f}s)")


if __name__ == "__main__":
    main()
