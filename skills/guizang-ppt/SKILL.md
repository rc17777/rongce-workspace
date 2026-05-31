---
name: guizang-ppt-skill
description: 生成横向翻页网页PPT（单HTML文件），含WebGL背景、章节幕封、数据大字报、图片网格、瑞士风/杂志风模板。当用户需要制作分享/演讲/发布会风格的网页PPT，或提到"杂志风PPT"、"瑞士风PPT"、"PPT skill"时使用。作者：歸藏，仓库：https://github.com/op7418/guizang-ppt-skill
---

# 歸藏 PPT Skill · 网页 PPT / 配图 / 封面

## 功能

- 生成**单文件 HTML** 横向翻页网页 PPT
- 生成 PPT 配图、多平台封面
- 支持两种风格：杂志风（Style A）和瑞士国际主义风（Style B）

## 风格选择

### 风格 A · 电子杂志 × 电子墨水（默认）
- WebGL 流体/等高线背景
- 衬线标题 (Noto Serif SC + Playfair Display) + 非衬线正文
- 适合：人文分享、行业观察、商业发布、Monocle风

### 风格 B · 瑞士国际主义（Swiss Style）
- WebGL 极细网格 + 点阵背景
- 全程无衬线 (Inter/Helvetica + Noto Sans SC)
- 高反差功能色：克莱因蓝/柠檬黄/柠檬绿/安全橙
- 适合：科技产品、数据汇报、设计/工程分享、年度总结

## 工作流

### Step 1 · 需求澄清
用7问对齐：风格(A/B)、受众、时长、素材有无、图片、主题色、硬约束

### Step 2 · 叙事弧（没大纲时）
钩子 → 定调 → 主体 → 转折 → 收束

### Step 3 · 生成 HTML PPT
- 模板文件在 assets/ 目录
- 布局规范在 references/layouts.md 或 references/layouts-swiss.md
- 主题色在 references/themes.md 或 references/themes-swiss.md

## 配图约定
- 路径：images/ 下，与 index.html 同级
- 命名：{页号}-{语义}.{ext}
- 规格：单张 ≥ 1600px 宽，总 ≤ 10MB

## 源仓库
- GitHub: https://github.com/op7418/guizang-ppt-skill
- 作者：歸藏 (Guizang)
- License: MIT
