# Word中文格式标准化使用指南

## 环境准备

```bash
uv pip install -r scripts/requirements.txt
```

## 模式一：标准化已有文档

用于清理/统一已有文档的格式。

```bash
uv run python scripts/format_word.py <input_file> [output_file]
```

示例：
```bash
uv run python scripts/format_word.py report.docx
uv run python scripts/format_word.py document.docx formatted.docx
```

## 模式二：基于模板生成文档（保格式编辑）

核心原则：复制模板 → run 级别编辑 → 保存。

### 快速上手

```python
from scripts.preserve_format import PreserveDoc, replace_all, rewrite_paragraph

with PreserveDoc("template.docx", "output.docx") as doc:
    # 全文替换
    replace_all(doc, "{{公司名}}", "融策会计师事务所")
    # 整段重写（保留格式）
    rewrite_paragraph(doc.paragraphs[5], "这是新的段落内容")
```

### 模拟对比：SOP 正确 vs paragraph.text 错误

```python
from scripts.preserve_format import copy_template, rewrite_paragraph

# 正确做法：保留格式
doc = copy_template("template.docx", "good.docx")
for i, text in {0: "标题", 2: "正文段落..."}.items():
    if i < len(doc.paragraphs):
        rewrite_paragraph(doc.paragraphs[i], text)
doc.save("good.docx")

# 错误做法：格式丢失
doc2 = copy_template("template.docx", "bad.docx")
for i, text in {0: "标题", 2: "正文段落..."}.items():
    if i < len(doc2.paragraphs):
        doc2.paragraphs[i].text = text  # ❌ 销毁 run 结构
doc2.save("bad.docx")
```

打开 good.docx 和 bad.docx 对比即可看到差异。

### API 速查

| 函数 | 作用 | 返回 |
|------|------|------|
| `copy_template(src, dst)` | 复制模板，返回 Document | Document |
| `PreserveDoc(tpl, out)` | 上下文管理器 | ContextManager |
| `replace_in_paragraph(p, old, new)` | 单 run 内替换 | bool |
| `replace_cross_runs(p, old, new)` | 跨 run 替换 | bool |
| `rewrite_paragraph(p, new)` | 整段重写保格式 | None |
| `replace_all(doc, old, new)` | 全文替换（段落+表格） | int (命中次数) |
| `insert_paragraph_deepcopy(doc, idx, text, anchor)` | deepcopy 插入新段 | None |
| `process_table_cells(doc, fn)` | 遍历表格单元格变换 | None |
| `verify_old_text_gone(doc, old)` | 验证旧文字已清除 | int (残留次数) |

## 常见问题

**格式化效果不理想**：检查文档中标题是否正确使用了 Word 内置样式（Title、Heading 1/2/3）。

**替换找不到文字**：可能被 Word 拆到了多个 run，尝试 `replace_cross_runs`。

**插入新段落后格式不对**：用 `insert_paragraph_deepcopy` 而非 `doc.add_paragraph()`。

**字体显示异常**：确保系统已安装微软雅黑字体。

**脚本兼容性**：仅支持 .docx 格式，不支持 .doc 格式。

## 注意事项

1. **先备份**：格式化/编辑前建议备份原文档
2. **模板优先**：生成性任务务必从模板副本出发，不要新建 Document()
3. **表格不遗漏**：全文替换用 `replace_all`，它会同时处理表格
