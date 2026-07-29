---
title: "投标文件元数据交叉检测（Word属性+PDF溯源+格式指纹）"
type: "detection_method"
layer: "L5"
confidence_level: "铁证"
alias: "L5-元数据交叉"
business_line: "通用"
keywords: [元数据, Word属性, PDF溯源, 页边距, RGB, 格式指纹, 同源]
dataset_id: "DM-BID-0005"
---

# 投标文件元数据交叉检测（Word属性+PDF溯源+格式指纹）

## 方法描述
从投标文件中提取三组元数据：①Word属性（作者/公司/修订人/编辑时间，从docProps/core.xml提取）；②PDF溯源（Author/Creator/Producer）；③格式指纹（页边距到毫米级、字体RGB通道值、行距/缩进、表格样式、页码标签）。Word属性跨文件匹配→直接铁证。格式指纹5项中≥3项匹配→组合铁证。

## 检测逻辑
Word: 提取dc:creator/cp:lastModifiedBy/company，任一字段跨文件完全匹配→铁证。PDF: 提取Author/Creator/Producer。格式指纹: 四边页边距差值<0.5mm + RGB(R±1,G±1,B±1) + font+size+leading完全匹配→同模板。

## 输入数据
- 必须：投标文件电子版（DOCX/PDF）
- 可选：

## 技术参数
```python
from docx import Document
props = Document(f).core_properties
# props.author, props.last_modified_by
```

## 误报风险
- 同一招标代理机构统一转换格式→需排除代理机构统一处理的情况
- WPS存储.doc格式时SummaryInformation为空→.doc格式是元数据盲区

## 组合规则
- 与L3文本雷同组合→元数据+文本→铁证
- 与L4图片组合→元数据+图片→三杀定案
