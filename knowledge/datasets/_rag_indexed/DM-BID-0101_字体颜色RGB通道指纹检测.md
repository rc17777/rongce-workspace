---
title: "字体颜色RGB通道指纹检测"
type: "detection_method"
layer: "L6a"
confidence_level: "强信号"
alias: "L6a-RGB指纹"
business_line: "通用"
keywords: [RGB, 字体颜色, 格式指纹, 软件默认色, 同源]
dataset_id: "DM-BID-0101"
---

# 字体颜色RGB通道指纹检测

## 方法描述
逐span提取字体RGB通道值。肉眼看到都是'黑色'，但RGB(0,0,0) vs RGB(26,26,26) vs RGB(1,1,1)来自于不同的软件默认配色。多份标书中同一非纯黑RGB值（如RGB(26,26,26)）跨文件匹配→同源软件/同模板。

## 检测逻辑
逐span提取font color的RGB三元组→排除(0,0,0)纯黑→对非纯黑RGB聚类→跨文件相同RGB匹配（R±1,G±1,B±1）→标记。

## 输入数据
- 必须：投标文件PDF/DOCX
- 可选：

## 技术参数
```python
import fitz
doc = fitz.open(f)
for page in doc:
    for span in page.get_text('dict')['blocks']: ...
```

## 误报风险
- 同一软件版本（如WPS Office 2024）可能有相同默认色→需结合其他维度

## 组合规则
- 与L5格式指纹(页边距/行距/表格)中≥3项同时命中→铁证
