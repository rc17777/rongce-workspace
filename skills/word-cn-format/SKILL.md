---
name: Word中文格式标准化
description: 提供Word文档按中文格式标准化的功能，包括标题、正文、图片、图表等格式的统一处理。使用微软雅黑字体，设置标准化的字体大小、段前段后位置、行缩进等。**现已整合 python-docx 保格式 SOP**：模板副本 + run 级别编辑，避免 AI 编辑 Word 时排版格式丢失。适用于需要统一文档格式或基于模板生成内容的场景，如企业文档、学术论文、审计报告等。
---

# Word中文格式标准化

## 功能概述

本skill提供Word文档的中文格式标准化功能，确保文档符合中文排版规范。

**核心方法论（已整合 AI-Word-Skill SOP）：**

> **Copy 原档 → 在 copy 上改 run 级别的文字 → 格式自然保留。**

反模式：用 `Document()` 新建 → 常见后果是默认字体与段落样式漂移。
反模式：`paragraph.text = "..."` → 销毁所有 run 及其格式。

### 两大工作模式

| 模式 | 适用场景 | 核心原则 |
|------|---------|---------|
| **标准化模式** | 清理/统一已有文档的格式 | 遍历所有元素，设置样式 |
| **保格式编辑模式** | 基于模板生成内容（合同、报告、公文等） | 复制模板 → run级替换 → 保存 |

## 目录结构

```
sample_1/
├── SKILL.md
├── scripts/
│   ├── format_word.py          # 格式化脚本（标准化模式）
│   ├── preserve_format.py      # 保格式编辑工具库（核心SOP函数）
│   └── requirements.txt        # 依赖项
├── references/
│   ├── format_standard.md      # 格式标准说明
│   ├── usage_guide.md          # 使用指南
│   └── sop_format_guide.md     # 保格式SOP操作指南
└── assets/
    └── template.docx           # 模板文件
```

## 核心功能

### 标题格式
- 标题：微软雅黑，2号字体（22pt），加粗，居中，段前12磅，段后6磅
- 一级标题：微软雅黑，3号字体（16pt），加粗，左对齐，段前12磅，段后6磅
- 二级标题：微软雅黑，4号字体（14pt），加粗，左对齐，段前6磅，段后3磅
- 三级标题：微软雅黑，小4号字体（12pt），加粗，左对齐，段前3磅，段后3磅

### 正文格式
- 字体：微软雅黑，5号字体（10.5pt）
- 行距：1.5倍行距
- 段前：0磅，段后：0磅
- 首行缩进：2字符

### 图片和图表格式
- 图片居中显示
- 图片下方添加编号和说明
- 图表标题在图表上方，居中显示
- 图表数据标签清晰可见

## 使用方法

### 模式一：标准化已有文档

```bash
uv run python scripts/format_word.py <input_file> [output_file]
```

### 模式二：基于模板生成新文档（保格式编辑）

```python
from scripts.preserve_format import (
    copy_template,
    replace_all,
    replace_cross_runs,
    rewrite_paragraph,
    insert_paragraph_deepcopy,
    process_table_cells,
    PreserveDoc,
)

# 1. 从模板创建副本
doc = copy_template("template.docx", "output.docx")

# 2. 全文替换（单run内）
replace_all(doc, "{{公司名}}", "融策会计师事务所")

# 3. 跨run替换（Word拆到多个run的情况）
for p in doc.paragraphs:
    replace_cross_runs(p, "旧文字", "新文字")

# 4. 整段重写（保留首run格式）
rewrite_paragraph(doc.paragraphs[3], "新的段落内容")

# 5. 表格遍历编辑
process_table_cells(doc, lambda cell_text: cell_text.replace("旧", "新"))

# 6. 保存
doc.save("output.docx")
```

或使用 PreserveDoc 上下文管理器：

```python
from scripts.preserve_format import PreserveDoc

with PreserveDoc("template.docx", "output.docx") as doc:
    replace_all(doc, "{{占位符}}", "实际内容")
```

## 依赖

```
python-docx>=1.1.0
pillow>=10.0.0
```
