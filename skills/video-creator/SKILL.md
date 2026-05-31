# Video Creator Skill

用 Pillow 渲染中文 + FFmpeg 拼接，生成图片幻灯片短视频。

## 能力边界

✅ 能做：
- 图片序列 → 幻灯片视频（Pillow 预处理文字、FFmpeg 拼接）
- 中文/多语言字幕叠加（Pillow 渲染，无编码问题）
- 背景音乐混音
- 横版 ↔ 竖版转换
- 视频拼接、分辨率/码率控制

❌ 不能做：
- AI 生成图像/视频（需外部模型 API）
- 版权音乐自动获取（需手动提供音频文件）
- 复杂转场效果（当前仅硬切）

## 前置依赖

- Python: Pillow
- FFmpeg（已安装 8.1.1）
- 中文字体：C:/Windows/Fonts/simhei.ttf（默认）
- 输入素材：图片文件夹 + 字幕文件（txt 或 json）

## 脚本

### make_video_v2.py（主脚本，推荐）

```bash
# 横版 1920x1080
python skills/video-creator/scripts/make_video_v2.py \
  --images <图片文件夹> \
  --text <字幕文件.txt> \
  --audio <背景音乐.mp3> \
  --output output.mp4 \
  --duration 3

# 竖版 1080x1920
python skills/video-creator/scripts/make_video_v2.py \
  --images ./slides --text captions.txt --audio bgm.m4a \
  --output output.mp4 --vertical

# 自定义字体
python skills/video-creator/scripts/make_video_v2.py \
  --images ./slides --text captions.txt \
  --font C:/Windows/Fonts/simhei.ttf \
  --output output.mp4
```

### make_video.py（v1，FFmpeg drawtext方式，已废弃）

有命令行中文编码问题，不推荐使用。保留作为参考。

## 字幕文件格式

TXT（每行对应一张图）：
```
第一张图的字幕内容
第二张图的字幕内容
```

JSON：
```json
["caption 1", "caption 2"]
```

## 输出格式

- 横版 1920×1080 / 竖版 1080×1920
- 编码：H.264 + AAC
- 帧率：30fps
- 每图显示时长：默认 3 秒

## 技术要点

- **中文渲染**：用 Pillow + 中文字体在图片上预处理文字，避免 FFmpeg drawtext 的命令行编码问题
- **音频混合**：BGM 自动循环到视频长度，音量降至 30%
- **竖版转换**：从 16:9 中心裁剪为 9:16
