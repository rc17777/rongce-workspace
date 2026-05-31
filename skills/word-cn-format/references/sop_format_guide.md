# 保格式SOP操作指南

> 基于 AI-Word-Skill （sgsss998/AI-Word-Skill）核心方法论，融策左护法整合。

## 核心心法

> **Copy 原档 → 在 copy 上改 run 级别的文字 → 格式自然保留。**

## OOXML 心智模型

.docx = ZIP 包裹的 OOXML。一个段落在 Word 里看起来是：

```
一个段落 w:p
  ├── run w:r (前一半，宋体)
  ├── run w:r (后一半，加粗)
  └── paragraph properties w:pPr (对齐/行距/样式引用)
```

每个 run 可以携带独立的 `w:rPr`（字体、字号、加粗、颜色、语言标签等）。
段落还有 `w:pPr`（对齐、段前段后间距、行距、样式引用等）。

### 为什么 paragraph.text = "..." 会出问题

python-docx 的 `paragraph.text =` 会删除所有 run，创建一个新 run。
结果：
- 段落级 pPr 可能幸存，但 run 级 rPr（尤其是中文字体）极容易丢失
- 修改后的段落不再匹配文档中其他手工排版的段落

### 为什么 Document() 新建会出问题

新建的段落默认是 Normal 样式，中英文字体可能回退到 Calibri/Arial，
段间距、编号等都会偏离模板。

## 四大核心技巧

### 1. 单 run 内替换（最安全）

```python
from scripts.preserve_format import replace_in_paragraph

for p in doc.paragraphs:
    replace_in_paragraph(p, "旧文字", "新文字")
```

适用：占位符替换、批量修正专有名词、多数 Word 没有拆分到多 run 的情况。

### 2. 跨 run 替换（进阶）

当 Word 把"某城市"拆成 run[0]="某城" + run[1]="市" 时：

```python
from scripts.preserve_format import replace_cross_runs

replace_cross_runs(paragraph, "某城市", "北京市")
```

经验法则：如果文字"明显存在"但替换就是找不着，优先怀疑跨 run。

### 3. 整段重写（保留首 run 格式）

```python
from scripts.preserve_format import rewrite_paragraph

rewrite_paragraph(doc.paragraphs[3], "完全不同的新内容")
```

保留 runs[0] 的 rPr（字体/字号），清空其余 run。
代价：如果原段落有"段落内部分加粗/变色"的格式，会被抹平。

### 4. deepcopy 插入新段落

```python
from scripts.preserve_format import insert_paragraph_deepcopy

# 用第 5 段作为格式模板，在 anchor 之后插入
insert_paragraph_deepcopy(doc, template_index=5, new_text="新段落内容", anchor=doc.paragraphs[3])
```

## 表格处理

表格单元格同样是 paragraph + run 结构。只改正文但忽略表格，会导致"段落完美、表格陈旧"。

```python
from scripts.preserve_format import replace_all, process_table_cells

# 方式一：全文替换自动覆盖表格
replace_all(doc, "旧", "新")

# 方式二：对表格单元格做自定义变换
process_table_cells(doc, lambda text: text.replace("2024年", "2025年"))
```

## 完整工作流

```
模板.docx
    │
    ▼ shutil.copy
输出.docx（副本）
    │
    ▼ Document('输出.docx')
    │
    ├── replace_all / replace_cross_runs（文字替换）
    ├── rewrite_paragraph（整段重写）
    ├── insert_paragraph_deepcopy（插入新段）
    ├── process_table_cells（表格编辑）
    │
    ▼ doc.save()
```

## 常见陷阱速查

| 陷阱 | 后果 | 正确做法 |
|------|------|----------|
| `doc.add_paragraph(text)` | 格式丢失 | `insert_paragraph_deepcopy` |
| `paragraph.text = new` | run 结构被毁 | `rewrite_paragraph` 或 `run.text =` |
| `Document()` 新建再拼 | 全部格式丢失 | `shutil.copy` 原档再改 |
| 表格只遍历段落 | 表格内文字没替换 | `replace_all` 或同时遍历 `doc.tables` |

## 验证清单

保存后应检查：

1. 全文检索旧关键词 → 确认已全部清除
2. 抽查前几段 runs[0] 的字体/字号是否与母版一致
3. 打开 Word，目视检查排版是否与模板一致
4. 检查表格、页眉页脚内容是否也已更新

## 与 Pandoc 的关系

Pandoc 导出 Word 时如果没有 `--reference-doc`，格式会回退到默认。
推荐工作流：先用 Word 手工排好一个母版，之后用本 SOP 在母版副列上改文字。
