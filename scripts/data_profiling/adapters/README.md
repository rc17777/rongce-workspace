# 审盾离线异构数据适配器（六入口→SDF）

> 依据：`knowledge/strategy/审盾-数据理解底座-离线异构适配器设计-20260804.md`
> 统一入口：`scripts/data_profiling/ingest.py`
> 统一输出：**SDF（审盾数据帧）**，保存到 `scripts/data_profiling/profiles/<project>/sdf/`

## 六入口一览

| 入口 | 适配器 | 依赖 | 状态 |
|:--|:--|:--|:--:|
| CSV/TSV | `csv_excel_adapter.py` | 标准库 | ✅ |
| Excel (.xlsx/.xls) | `csv_excel_adapter.py` | openpyxl | ✅ |
| PDF电子件 | `pdf_electronic.py` | pdfplumber | ✅ |
| PDF扫描件 | `pdf_scanned.py` + `pdf_ocr_worker.py` | pymupdf + PaddleOCR环境 | ✅ |
| SQL dump | `sql_dump.py` | 标准库 | ✅ |
| API | `api_adapter.py` | requests | ✅ |

## 快速开始

```bash
# 自动识别类型
python scripts/data_profiling/ingest.py --source "序时账.xlsx" --project pidou_2026 --label 运行经费

# 指定类型
python scripts/data_profiling/ingest.py --source "扫描发票.pdf" --type pdf_scanned --project xx --label 发票
python scripts/data_profiling/ingest.py --source "dump.sql" --type sql_dump --project xx --label 台账 --table 明细表
python scripts/data_profiling/ingest.py --source "https://api.xxx.com" --type api --api-config cfg.json --project xx --label 数据
```

## 各适配器要点

### PDF电子件（pdfplumber）
- 自动探测文本层：文本页占比 <10% → 判定扫描件，提示改用 `pdf_scanned`
- 有表格线 → 表格模式（跨页合并同构表）；无表格 → 文本模式（每行一条 `{page,line,text}`）
- 已装 pdfplumber 0.11.9（base 环境），无需装包

### PDF扫描件（PaddleOCR + 拆分）
- **PDF拆分**：大PDF按 `--chunk-pages`（默认25页）拆 chunk，控制单进程内存（336MB大文件场景验证过）
- **OCR**：子进程调用 paddleocr conda 环境（`C:\Users\scrccpa\miniconda3\envs\paddleocr\python.exe`），
  可设 `PADDLEOCR_PYTHON` 环境变量指定
- **断点续跑**：worker 每页输出独立 JSON，`--keep-chunks` 保留临时目录，重跑自动跳过已识别页
- **质量分层**（设计文档4.3）：conf≥95% 自动入库 / 85-95% 标记抽检 / <85% 提示人工确认
- 表格重建：OCR行按 y 中心聚类 → x 排序 → 单元格（仅多列行输出为表格行，单列行走文本模式）

### SQL dump
- 支持：`CREATE TABLE`（列名/类型/NOT NULL/PRIMARY KEY/AUTO_INCREMENT）+ `INSERT INTO` 多值批量
- 自动编码检测（utf-8/gbk/gb18030/latin-1），剥离 `--`/`#`/`/* */` 注释
- 字符串转义、NULL→None、数字自动转 int/float、hex 解码
- 多表 dump → 每表一个 SDF（`<label>_<表名>_sdf.json`），`--table` 过滤

### API
- 配置驱动（见 `api_adapter.py` 文档注释），支持 page/offset/none 三种分页
- `data_path` 点路径定位记录列表；`fields` 字段映射（缺省自动发现）
- 空页自动停止、重试3次、限速

## 测试

```bash
python scripts/data_profiling/adapters/make_testdata.py   # 生成测试夹具(testdata/)
# 然后逐个跑: 见各适配器 --help
```

## 后续（v1.5，阶段2）

- 增量更新（追加/替换/差异报告）— 设计文档 4.4
- 口径校验层接入 SDF（借贷平衡/日期连续性/勾稽关系）
