---
name: pdf-metadata-extractor
description: PDF元数据深度提取工具。提取PDF标准元数据（Author/Creator/Producer/CreationDate）、XMP扩展元数据、xref内部对象、嵌入文件信息。用于投标文件溯源分析、文档制作痕迹比对、串标围标审计等场景。依赖PyMuPDF(fitz)库。触发词：PDF元数据/提取PDF信息/标书制作人/Author溯源/文档指纹/谁做的PDF。
layer: atomic
depends_on: []
used_by:
  - bid-collusion-audit
extracted_from: "教科院附中串标审计PDF分析实战 (2026-05-17/19)"
---

# PDF元数据深度提取

## 快速开始

```bash
uv pip install PyMuPDF
```

```python
from pdf_metadata_extractor import extract_all_metadata

# 单个文件
result = extract_all_metadata("标书.pdf")
print(result["standard"]["author"])   # 谁做的
print(result["standard"]["creator"])   # 用什么工具

# 批量扫描（串标审计常用）
import os, json
from pathlib import Path
results = {}
for pdf in Path("投标文件/").glob("*.pdf"):
    results[pdf.name] = extract_all_metadata(str(pdf))
    
# 按Author分组，找跨公司相同Author
with open("元数据汇总.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
```

## 核心代码模板

```python
import fitz  # PyMuPDF

def extract_all_metadata(filepath: str) -> dict:
    """深度提取PDF所有元数据"""
    result = {
        "standard": {},     # 标准元数据
        "xref_objects": [], # 可疑内部对象
        "embedded": [],     # 嵌入文件
    }
    
    doc = fitz.open(filepath)
    
    # 1. 标准元数据（最重要）
    meta = doc.metadata
    result["standard"] = {
        "author": meta.get("author", ""),
        "creator": meta.get("creator", ""),
        "producer": meta.get("producer", ""),
        "creationDate": meta.get("creationDate", ""),
        "modDate": meta.get("modDate", ""),
        "format": meta.get("format", ""),
    }
    
    # 2. 遍历xref找可疑对象（搜索关键词）
    keywords = ['serial', 'mac', 'cpu', 'disk', 'machine', 
                'uuid', 'guid', 'hostname', '序列号', '物理地址']
    for i in range(1, doc.xref_length()):
        try:
            obj = doc.xref_object(i)
            for kw in keywords:
                if kw in obj.lower():
                    result["xref_objects"].append({
                        "id": i, "keyword": kw, "content": obj[:300]
                    })
                    break
        except:
            continue
    
    # 3. 嵌入文件
    try:
        for i in range(doc.embfile_count()):
            info = doc.embfile_info(i)
            result["embedded"].append(info.get("name", "unknown"))
    except:
        pass
    
    doc.close()
    return result
```

## 关键字段说明

| 字段 | 含义 | 串标审计价值 |
|------|------|-------------|
| author | 文档作者（WPS账户名/电脑用户名） | ⭐ 跨公司相同Author = 铁证 |
| creator | 创建工具（WPS文字/Chromium/Word） | 工具链比对 |
| producer | PDF生成引擎 | 区分浏览器打印 vs 原生导出 |
| creationDate | 创建时间（含时区） | 时间线重构 |
| modDate | 最后修改时间 | 修改痕迹追踪 |
| format | PDF版本 | 辅助判断 |

## 输出示例

```json
{
  "standard": {
    "author": "wwx",
    "creator": "WPS 文字",
    "producer": "",
    "creationDate": "D:20240930131112+08'00'",
    "modDate": "D:20240930131112+08'00'",
    "format": "PDF 1.7"
  },
  "xref_objects": [],
  "embedded": []
}
```

## 错误处理

```python
try:
    import fitz
except ImportError:
    print("❌ PyMuPDF 未安装，请运行: uv pip install PyMuPDF")
    exit(1)

def safe_extract(filepath: str) -> dict:
    """带错误处理的元数据提取"""
    if not os.path.exists(filepath):
        return {"error": f"文件不存在: {filepath}"}
    try:
        return extract_all_metadata(filepath)
    except Exception as e:
        return {"error": str(e)}
```

## 注意

- Chromium打印的PDF **没有author字段**，这是正常现象
- WPS文字导出的PDF author = 登录用户名（不是Windows用户名）
- 时间格式 `D:20240930131112+08'00'` = 2024-09-30 13:11:12 东八区
- `+00'00'` 是UTC时间，需要+8小时转北京时间
- xref中的 "DeviceRGB"/"DeviceGray" 是颜色空间，属于PDF内部术语，不是设备指纹
