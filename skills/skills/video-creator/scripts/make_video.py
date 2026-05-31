#!/usr/bin/env python3
"""make_video.py - 一站式视频生成：图片 + 文字 + 音乐 → 视频

用法:
  python make_video.py --images ./slides --text captions.txt --audio bgm.mp3 --output demo.mp4
  python make_video.py --images ./slides --text captions.txt --output demo.mp4 --vertical
  python make_video.py --images ./slides --text captions.txt --output demo.mp4 --duration 4
"""

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path


def find_images(folder: Path) -> list[Path]:
    """按文件名排序找到所有图片"""
    exts = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}
    images = sorted(
        [f for f in folder.iterdir() if f.suffix.lower() in exts],
        key=lambda x: x.name,
    )
    return images


def load_captions(path: Path) -> list[str]:
    """加载文字内容文件，每行对应一张图"""
    if path.suffix == ".json":
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
        return data.get("captions", data.get("texts", []))
    with open(path, encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


def get_duration(path: Path) -> float:
    """获取媒体时长"""
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        capture_output=True, text=True,
    )
    return float(result.stdout.strip())


def make_slideshow(
    images: list[Path],
    text_lines: list[str],
    duration_per_image: float,
    resolution: tuple[int, int],
    fontfile: str,
    temp_dir: Path,
) -> Path:
    """生成带文字叠加的幻灯片视频"""
    w, h = resolution

    # Step 1: 生成每张图的视频片段
    segments = []
    for i, img in enumerate(images):
        caption = text_lines[i] if i < len(text_lines) else ""

        seg = temp_dir / f"seg_{i:03d}.mp4"
        vf_parts = [
            f"scale={w}:{h}:force_original_aspect_ratio=decrease",
            f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:black",
        ]

        if caption:
            # 把中文写到临时UTF-8文件，用textfile避免命令行编码问题
            textfile = temp_dir / f"text_{i:03d}.txt"
            textfile.write_text(caption, encoding="utf-8")

            escaped_font = fontfile.replace('\\', '/').replace(':', '\\:')
            escaped_textfile = str(textfile).replace('\\', '/').replace(':', '\\:')
            drawtext = (
                f"drawtext=textfile='{escaped_textfile}':"
                f"fontfile={escaped_font}:"
                f"fontsize=36:fontcolor=white:"
                f"x=(w-text_w)/2:y=h-text_h-80:"
                f"box=1:boxcolor=black@0.6:boxborderw=12:"
                f"line_spacing=8"
            )
            vf_parts.append(drawtext)

        filter_chain = ",".join(vf_parts)
        cmd = [
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", str(img),
            "-c:v", "libx264",
            "-t", str(duration_per_image),
            "-r", "30",
            "-pix_fmt", "yuv420p",
            "-vf", filter_chain,
            str(seg),
        ]
        subprocess.run(cmd, capture_output=True, check=True)
        segments.append(seg)

    # Step 2: 用 concat demuxer 拼接所有片段
    concat_list = temp_dir / "concat_list.txt"
    with open(concat_list, "w") as f:
        for seg in segments:
            f.write(f"file '{seg.as_posix()}'\n")

    slideshow = temp_dir / "slideshow.mp4"
    subprocess.run(
        ["ffmpeg", "-y", "-f", "concat", "-safe", "0",
         "-i", str(concat_list), "-c", "copy", str(slideshow)],
        capture_output=True, check=True,
    )
    return slideshow


def add_crossfade(video: Path, temp_dir: Path) -> Path:
    """给视频片段间添加交叉淡化转场（如片段 > 1个）"""
    # 简化版：不做逐段转场，直接返回原视频
    # 复杂转场可用 xfade filter，但需要逐段处理，这里保持简单
    return video


def mix_audio(video: Path, audio: Path, output: Path) -> None:
    """混入背景音乐（音量降低，循环到视频长度）"""
    video_dur = get_duration(video)
    audio_dur = get_duration(audio)

    # 如果音频比视频短，循环；否则裁剪
    if audio_dur < video_dur:
        # 用 stream_loop 循环音频
        cmd = [
            "ffmpeg", "-y",
            "-i", str(video),
            "-stream_loop", "-1",
            "-i", str(audio),
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", "128k",
            "-filter:a", "volume=0.3",
            "-shortest",
            "-map", "0:v:0",
            "-map", "1:a:0",
            str(output),
        ]
    else:
        cmd = [
            "ffmpeg", "-y",
            "-i", str(video),
            "-i", str(audio),
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", "128k",
            "-filter:a", "volume=0.3",
            "-shortest",
            "-map", "0:v:0",
            "-map", "1:a:0",
            str(output),
        ]
    subprocess.run(cmd, capture_output=True, check=True)


def to_vertical(video: Path, output: Path) -> None:
    """横版 → 竖版转换（中心裁剪 9:16）"""
    cmd = [
        "ffmpeg", "-y",
        "-i", str(video),
        "-vf", "crop=ih*9/16:ih,scale=1080:1920",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "128k",
        str(output),
    ]
    subprocess.run(cmd, capture_output=True, check=True)


def main():
    parser = argparse.ArgumentParser(description="一站式视频生成")
    parser.add_argument("--images", required=True, help="图片文件夹路径")
    parser.add_argument("--text", required=True, help="文字内容文件（每行=每图字幕，或 JSON）")
    parser.add_argument("--audio", help="背景音乐文件（mp3/m4a）")
    parser.add_argument("--output", default="output.mp4", help="输出视频路径")
    parser.add_argument("--vertical", action="store_true", help="输出竖版 9:16")
    parser.add_argument("--duration", type=float, default=3.0, help="每张图显示秒数 (默认3)")
    parser.add_argument("--font", default="C:/Windows/Fonts/simhei.ttf", help="中文字体路径 (默认SimHei)")
    parser.add_argument("--resolution", default="1920x1080", help="横版分辨率 WxH (默认1920x1080)")

    args = parser.parse_args()

    images_dir = Path(args.images)
    text_file = Path(args.text)
    audio_file = Path(args.audio) if args.audio else None
    output = Path(args.output)

    if not images_dir.is_dir():
        print(f"[ERROR] Images folder not found: {images_dir}")
        sys.exit(1)
    if not text_file.exists():
        print(f"[ERROR] Text file not found: {text_file}")
        sys.exit(1)
    if audio_file and not audio_file.exists():
        print(f"[ERROR] Audio file not found: {audio_file}")
        sys.exit(1)

    images = find_images(images_dir)
    if not images:
        print(f"[ERROR] No images found in: {images_dir}")
        sys.exit(1)

    text_lines = load_captions(text_file)
    if not text_lines:
        print(f"[ERROR] Text file is empty: {text_file}")
        sys.exit(1)

    print(f"[IMAGES] Found {len(images)} images")
    print(f"[TEXT] Loaded {len(text_lines)} lines")
    if audio_file:
        print(f"[AUDIO] BGM: {audio_file.name}")

    w, h = map(int, args.resolution.split("x"))
    if args.vertical:
        w, h = 1080, 1920

    with tempfile.TemporaryDirectory(prefix="vc_") as tmp:
        temp_dir = Path(tmp)

        print("[SLIDESHOW] Generating slideshow...")
        slideshow = make_slideshow(images, text_lines, args.duration, (w, h), args.font, temp_dir)

        if audio_file:
            print("[AUDIO] Mixing background music...")
            with_audio = temp_dir / "with_audio.mp4"
            mix_audio(slideshow, audio_file, with_audio)
            slideshow = with_audio

        if args.vertical:
            print("[VERTICAL] Converting to vertical 9:16...")
            to_vertical(slideshow, output)
        else:
            import shutil
            shutil.copy(slideshow, output)

        dur = get_duration(output)
        size_mb = output.stat().st_size / (1024 * 1024)
        print(f"[DONE] Output: {output} ({size_mb:.1f}MB, {dur:.0f}s)")


if __name__ == "__main__":
    main()
