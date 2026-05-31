# 非结构化审计数据处理 — 参考方法

> 来源: 黎强（重庆市九龙坡区审计局）《利用大数据技术处理非结构化审计数据的方法》，载《中国审计》2023年第8期

## 一、应用背景

非结构化数据（图片、文档、音频、视频）在企业数据中占比超80%，且以每年60%速度增长。审计人员在处理招投标电子资料时常面临：

- **数据体量庞大**: 某区公共资源交易中心招投标数据1.27TB
- **数据有效率低**: 7.37GB资料处理标准化后仅95.2MB，有效率~1.3%
- **处理技术复杂**: 需同时运用压缩批处理、OCR、文本查重等多种技术

## 二、四种核心技术

### 1. 压缩文件批处理

**用途**: 批量解压投标项目压缩包，自动定位和提取关键文件（招标公告、设计方案、施工组织方案、工程量清单等）

**实现路径**:
```csharp
// 原文用C#+.NET Framework 4.0+Aspose
// Python等效方案:
import zipfile, os

def batch_unzip_extract(zip_dir, target_patterns=['招标公告','施工组织','工程量清单','设计方案']):
    """批量解压并定位关键文件"""
    results = []
    for zip_file in os.listdir(zip_dir):
        if not zip_file.endswith('.zip'): continue
        with zipfile.ZipFile(os.path.join(zip_dir, zip_file)) as z:
            for name in z.namelist():
                if any(p in name for p in target_patterns):
                    content = z.read(name)
                    results.append({'project': zip_file, 'file': name, 'size': len(content)})
    return results
```

**效率**: 226个7GB项目压缩包，手动解压需2个工作日，批处理<3分钟

### 2. Word文件批处理

**用途**: 批量提取Word内容 → 关键词高亮标注 → 汇总成疑点表

**关键词库**（招标文件设限检测）:
- 资格限制: `业绩` `奖项` `专利` `规模` `资质等级` `注册资金` `特定品牌` `指定型号`
- 地域限制: `本地` `本市` `省内` `注册地` `纳税地`
- 时间限制: `成立年限` `经营年限` `从业经验`
- 其他: `唯一授权` `独家代理` `指定供应商`

**Python实现**:
```python
from docx import Document
from openpyxl import Workbook

def batch_word_keyword_scan(docx_dir, keywords):
    """批量扫描Word文件，标注含限制关键词的段落"""
    results = []
    for fname in os.listdir(docx_dir):
        if not fname.endswith('.docx'): continue
        doc = Document(os.path.join(docx_dir, fname))
        for i, para in enumerate(doc.paragraphs):
            for kw in keywords:
                if kw in para.text:
                    results.append({
                        'file': fname, 'para_no': i,
                        'keyword': kw, 'text_snippet': para.text[:200]
                    })
    return results
```

**效率**: 226份Word（每份~10万字），人工审阅3个工作日，批处理<1分钟

### 3. PDF文件批处理

**用途**: 提取PDF文本 → Simhash相似度计算 → 投标文件趋同性分析；提取表格 → 价格浮动率计算 → 规律性分析

**Simhash算法**（优于传统TF-IDF的海量文本去重）:
```python
from simhash import Simhash

def compute_similarity(text1, text2):
    """计算两个文本的Simhash海明距离"""
    h1 = Simhash(text1)
    h2 = Simhash(text2)
    distance = h1.distance(h2)
    # 海明距离≤3 → 高度相似; ≤6 → 中度相似
    return distance

def batch_pdf_similarity(pdf_dir, file_groups):
    """批量计算PDF文本趋同率
    file_groups: {project_id: [file1.pdf, file2.pdf, file3.pdf]}
    """
    results = {}
    for proj_id, files in file_groups.items():
        texts = {}
        for f in files:
            texts[f] = extract_text_from_pdf(f)  # fitz or pdfplumber
        # 两两对比
        for i, f1 in enumerate(files):
            for f2 in files[i+1:]:
                dist = compute_similarity(texts[f1], texts[f2])
                results[f'{f1} vs {f2}'] = dist
    return results
```

**价格浮动率分析**（从PDF表格提取后计算）:
```python
def detect_price_pattern(df):
    """检测投标价格浮动规律"""
    df['float_ratio'] = (df['bid_price'] - df['base_price']) / df['base_price']
    # 检查是否存在固定浮动比例（如全部上浮3%）
    ratios = df['float_ratio'].dropna()
    if len(ratios) > 0:
        std = ratios.std()
        mean = ratios.mean()
        if std < 0.01:  # 标准差极小=固定浮动比例
            return {'pattern': 'fixed_float', 'ratio': mean, 'std': std}
    return {'pattern': 'normal'}
```

**效率**: 3725份PDF（~300页/份），人工审查难以实现，批处理1天

### 4. OCR批量图文识别

**用途**: 处理图片格式的投标文件（JPG扫描件、PDF嵌入图片等）

**工具选择**:
- **PaddleOCR**: 百度开源，中文识别精度高，支持GPU加速，批量处理
- **pytesseract**: Google Tesseract封装，轻量但精度低于PaddleOCR

**PaddleOCR实现**:
```python
from paddleocr import PaddleOCR

def batch_ocr_images(image_dir, output_dir):
    """批量OCR识别图片并转文本"""
    ocr = PaddleOCR(lang='ch')
    for fname in os.listdir(image_dir):
        if not fname.lower().endswith(('.png','.jpg','.jpeg')): continue
        result = ocr.ocr(os.path.join(image_dir, fname))
        text = '\n'.join([line[1][0] for line in result[0]] if result[0] else [])
        # 保存为txt
        out_name = fname.rsplit('.',1)[0] + '.txt'
        with open(os.path.join(output_dir, out_name), 'w', encoding='utf-8') as f:
            f.write(text)
```

**关键**: OCR精度取决于训练模型，需选择识别精度高、速度快的中文训练模型。PaddleOCR的PP-OCRv4模型为当前SOTA。

## 三、完整审计流水线

```
原始数据(1.27TB压缩包)
  │
  ├── [压缩批处理] 解压→定位关键文件→字节流转换
  ├── [格式统一] PDF/JPG/DOCX → 统一为文本格式
  │
  ├── [Word批处理] 招标公告→限制关键词扫描→疑点表
  ├── [PDF批处理] 投标文件→Simhash趋同率→疑点表
  ├── [PDF批处理] 工程量清单→价格浮动率→疑点表
  └── [OCR识别] 图片文件→PaddleOCR→文本→Simhash→疑点表
```

**成果**: 1天内完成226个项目全覆盖，筛查出围标串标疑点并核实。

## 四、与我们现有工具链的整合

| 维度 | 文章方案 | 融策现有 | 升级方向 |
|:------|:--------|:--------|:--------|
| 文本趋同 | Simhash | TF-IDF余弦相似度 | 可互补：Simhash用于海量初筛，TF-IDF用于精细对比 |
| OCR引擎 | PaddleOCR | pytesseract | PaddleOCR精度更高，适合大批量生产 |
| 价格分析 | 清单单项浮动率 | 总报价规律性(L1) | 可扩展至清单级别价格分析 |
| 格式统一 | Aspose控件(.NET) | fitz+pdfplumber | 功能对等 |
| 自动化 | C#编译管线 | Python脚本 | Python更灵活 |
