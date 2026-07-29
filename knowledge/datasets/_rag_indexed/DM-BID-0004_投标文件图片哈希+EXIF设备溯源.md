---
title: "投标文件图片哈希+EXIF设备溯源"
type: "detection_method"
layer: "L4"
confidence_level: "铁证"
alias: "L4-图片哈希+EXIF"
business_line: "通用"
keywords: [图片哈希, SHA256, pHash, EXIF, GPS, 设备溯源, 同人制作]
dataset_id: "DM-BID-0004"
---

# 投标文件图片哈希+EXIF设备溯源

## 方法描述
提取投标文件（PDF/DOCX）中嵌入的所有图片，计算SHA256+感知哈希（pHash）。SHA256相同→同一张图。pHash汉明距离<5→同一张图缩放/轻微修改。增强版新增EXIF溯源：如果3+字段（相机型号+GPS+软件+时间）跨文件匹配→同人同地同设备制作多份标书。

## 检测逻辑
SHA256: 精确匹配。pHash: 汉明距离<5判定为同图。EXIF: 提取271(Make)+272(Model)+34853(GPSInfo)+305(Software)+36867(DateTimeOriginal)，≥3字段跨文件匹配→铁证。

## 输入数据
- 必须：投标文件电子版（PDF/DOCX）
- 可选：

## 技术参数
```python
from PIL import Image
import imagehash
h = imagehash.phash(Image.open(img))
# EXIF: img._getexif() → tags 271/272/34853/305/36867
```

## 误报风险
- 投标人使用了同一来源的公共素材图片→排除公开来源图片
- 同一型号设备是市场主流（如iPhone 15 Pro）→需GPS+时间同时匹配

## 组合规则
- 与L3文本雷同组合→图片+文本都雷同→铁证
- 与L5元数据组合→图片同源+文件同源→铁证
