# 招投标审计工具箱 — 快速参考卡

> 融策会计师事务所 · 融策右护卫 · v1.0 (2026-05-27)

## 一键入口

```bash
# 方法1: Python命令行
python D:\openclaw-workspace\scripts\audit_pipeline.py --project "项目文件夹路径" --o "输出路径"

# 方法2: 拖拽项目文件夹到 audit.bat
D:\openclaw-workspace\scripts\audit.bat

# 方法3: 快速模式(仅元数据+相似度, 适合小项目)
python audit_pipeline.py -p "项目文件夹" --skip unzip,word,apriori,savings,entity
```

## 七步分析流程

| 步骤 | 内容 | 输入 | 输出 |
|:------|:-----|:-----|:-----|
| 1 | 压缩包处理 | .zip/.rar | extracted/ |
| 2 | Word关键词扫描 | .docx | word_关键词扫描.xlsx |
| 3 | PDF元数据提取 | .pdf (≥2个) | pdf_元数据.xlsx |
| 4 | PDF文本雷同 | .pdf (≥2个) | pdf_相似度.xlsx |
| 5 | Apriori关联规则 | .xlsx交易数据 | apriori_关联规则.xlsx |
| 6 | 节资率分析 | 招标台账.xlsx | 节资率分析.xlsx |
| 7 | 实体异常检测 | 项目数据.xlsx | 实体异常检测.xlsx |

## 可用子脚本 (独立运行)

### 非结构化数据处理
```bash
# 批量解压 + 定位关键文件
python skills/unstructured-audit-data/scripts/batch_unzip.py "压缩包目录" "输出目录"

# Word限制条款扫描
python skills/unstructured-audit-data/scripts/batch_word_scan.py "docx目录" 输出.xlsx

# PDF投标文件相似度
python skills/unstructured-audit-data/scripts/batch_pdf_similarity.py "pdf目录" --o 输出.xlsx

# 批量OCR (推荐PaddleOCR)
python skills/unstructured-audit-data/scripts/batch_ocr.py "图片目录" "文本输出目录" --engine paddle
```

### Apriori关联规则
```bash
# 频繁结队检测 (支持度≥2, 置信度≥0.6)
python skills/apriori-audit/scripts/apriori_analysis.py --i 数据.xlsx --mode frequent --min-support 2

# 缺失关联检测
python skills/apriori-audit/scripts/apriori_analysis.py --i 数据.xlsx --mode missing --min-support 0.8
```

### 采购审计专项
```bash
# 节资率 + 支持度/置信度
python skills/procurement-audit-models/scripts/12_savings_rate.py --i 招标台账.xlsx --o 输出.xlsx

# L15-L19 实体异常 (陪标专业户/保证金/经办人/硬件/专家)
python skills/procurement-audit-models/scripts/13_entity_anomalies.py --projects 项目表.xlsx --o 输出.xlsx
```

## 24层检测体系速查

```
L1  报价规律性      🔴铁证    需报价数据
L2  投标IP/MAC     🔴铁证    需代理机构
L3  文本雷同        🔴铁证    需文字层PDF
L4  图片哈希        🔴铁证    PyMuPDF+PIL
L5  元数据交叉      🔴铁证    PyMuPDF
L6  文档结构        🟡强信号   PyMuPDF
L7  扫描仪型号      🟡强信号   PDF Producer
L8  工商关联        🔴铁证    天眼查
L9  保证金/资金链    🔴铁证    银行数据
L10 评审得分        🔴铁证    评审报告
L11 伴随投标        🔴铁证    3+项目历史
L12 历史异常关联    🔴铁证    异常标记库
L13 节资率分析      🔴铁证    招标台账
L14 最优围标人数    🟡强信号   投标人数
L15 陪标专业户      🟡强信号   投标台账
L16 保证金同时缴    🔴铁证    保证金表
L17 经办人一致      🔴铁证    负责人表
L18 硬盘/MAC/IP    🔴铁证    硬件特征码
L19 评标专家违规    🔴铁证    专家库+社保

D1 WPS签名残留  D2 JPEG量化表  D3 文件完整性
D4 像素分布    D5 时间线      D6 节资率箱线图
D7 支持度矩阵  D8 提升度      D9 专家社交图谱
```

## 安装依赖

```bash
pip install pandas openpyxl PyMuPDF python-docx scikit-learn Pillow
# OCR (可选)
pip install paddleocr paddlepaddle
# Apriori加速 (可选)
pip install simhash
```
