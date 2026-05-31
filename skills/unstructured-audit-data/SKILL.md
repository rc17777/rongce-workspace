---
name: unstructured-audit-data
description: Processing unstructured audit data (PDF scans, Word documents, compressed bid archives, images) for bid-rigging detection, document similarity analysis, and automated data extraction. Use when audit work involves (1) Batch processing compressed bid project files, (2) Scanning Word/PDF documents for restriction keywords, (3) Computing document similarity with Simhash or TF-IDF for collusion detection, (4) Batch OCR of scanned documents, (5) Extracting and analyzing price patterns from bid documents, or (6) Building automated audit data processing pipelines.
---

# 非结构化审计数据处理

四类核心批处理技术，覆盖招投标审计中非结构化数据的全链路处理。

## 快速参考

详见 [references/methodology.md](references/methodology.md) 获取完整的四类技术详解（含案例数据、效率指标、工具链对比）。

## 四类处理技术

### 1. 压缩文件批处理 (`scripts/batch_unzip.py`)

批解压投标项目压缩包，自动定位招标公告、施工方案、工程量清单等关键文件。

```bash
python scripts/batch_unzip.py <zip_dir> <output_dir>
# 自动扫描zip目录→解压→定位关键文件→输出报告
```

### 2. Word限制关键词扫描 (`scripts/batch_word_scan.py`)

批量提取Word内容，扫描限制性关键词（业绩、奖项、品牌、本地等），生成疑点汇总表。

```bash
python scripts/batch_word_scan.py <docx_dir> <output.xlsx>
```

关键词库：
- 资格类: `业绩` `奖项` `专利` `规模` `注册资金` `特定品牌`
- 地域类: `本地` `本市` `省内` `注册地`
- 时间类: `成立年限` `经营年限`

### 3. PDF相似度分析 (`scripts/batch_pdf_similarity.py`)

批量提取PDF文本 → Simhash / TF-IDF → 投标文件趋同率矩阵 → 疑点表。

```bash
python scripts/batch_pdf_similarity.py <pdf_dir> --method simhash|tfidf --output <result.xlsx>
```

- `simhash`: 海明距离≤3高度相似；内存友好，适合海量文件初筛
- `tfidf`: 余弦相似度≥80%高度可疑；更精细，适合确认

### 4. 批量OCR (`scripts/batch_ocr.py`)

PaddleOCR中文识别 → 文本转存 → 接入相似度分析流水线。

```bash
pip install paddleocr paddlepaddle  # 首次使用
python scripts/batch_ocr.py <image_dir> <output_dir>
```

PaddleOCR替代pytesseract的时机：大批量(>100页)、要求高精度、需要GPU加速。

## 完整流水线示例

```bash
# 1. 解压投标项目包→提取关键文件
python scripts/batch_unzip.py ./bid_zips/ ./extracted/

# 2. Word招标文件→设限关键词扫描
python scripts/batch_word_scan.py ./extracted/bidding_docs/ ./word_suspicion.xlsx

# 3. PDF投标文件→Simhash初筛→TF-IDF确认
python scripts/batch_pdf_similarity.py ./extracted/bid_files/ --method simhash -o ./simhash_result.xlsx

# 4. 图片格式文件→OCR→文本
python scripts/batch_ocr.py ./extracted/images/ ./ocr_texts/
```

## Simhash vs TF-IDF 选择

| 场景 | 推荐 | 原因 |
|:------|:-----|:-----|
| >1000份文件初筛 | Simhash | 内存O(1), 速度快 |
| ≤100份精细对比 | TF-IDF | 余弦相似度更直观 |
| 段落级雷同 | TF-IDF | 可定位具体匹配段落 |
| 全文趋同率 | Simhash | 海明距离阈值明确 |

## 工具依赖

- `fitz` (PyMuPDF): PDF文本/图片提取
- `paddleocr`: 中文OCR (可选，默认使用pytesseract)
- `python-docx`: Word处理
- `simhash`: Simhash算法
- `scikit-learn`: TF-IDF
- `openpyxl`: Excel输出
