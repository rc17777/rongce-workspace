# 融策脚本资产治理方案（2026-07-03）

> 目标：把 `scripts/` 从“脚本堆”整理成可维护工具库。  
> 原则：先建目录和 README，先生成迁移清单，不直接大规模移动，避免破坏相对路径/import。

## 1. 当前脚本分类结果

| 分类 | 数量 | 状态判断 | 建议 |
|---|---:|---|---|
| `other` | 499 | 无法仅凭文件名可靠判断 | 人工复核，暂不移动 |
| `office_generation` | 75 | Word/Excel/PPT/文档生成类 | 可按项目/模板进一步细分 |
| `debug_or_cache` | 32 | 测试、修复、缓存类 | 优先归档或清理候选 |
| `ocr` | 31 | OCR、图片转文本、百度/ABBYY/Paddle 相关 | 建立 OCR 工具目录 |
| `bidding_analysis` | 21 | 招投标、串标、TF-IDF、元数据 | 建立招投标分析目录 |
| `guards` | 20 | Token、成本、API、spawn 守卫 | 建立守卫目录，优先保留 |
| `report_review` | 12 | 报告复核、审计复核 | 建立报告复核目录 |
| `rag` | 10 | 知识库重建、查询、服务 | 建立 RAG 目录 |
| `case_collection` | 4 | 案例采集、分类、归档 | 建立案例采集目录 |

对应台账：

- `asset_scripts_structured_candidates.csv`：可分层候选。
- `asset_scripts_review_needed.csv`：待人工复核脚本。

## 2. 推荐目录

```text
scripts/
├── README.md
├── rag/
├── ocr/
├── case_collection/
├── report_review/
├── bidding_analysis/
├── office_generation/
├── guards/
└── archive_debug/
```

## 3. 迁移策略

### 第一批：低风险迁移

可优先迁移：

- `rag` 类：通常入口独立，依赖少。
- `case_collection` 类：文件少且已有 README。
- `guards` 类：作为公共工具，迁移后需检查 import。
- `debug_or_cache` 类：归档，不作为主入口。

### 第二批：中风险迁移

需要先检查依赖：

- `ocr` 类：可能依赖模型、图片目录、第三方库和输出路径。
- `report_review` 类：可能依赖模板、Excel/Word 文件。
- `bidding_analysis` 类：可能依赖项目目录、投标文件路径、OCR 输出。

### 第三批：高风险迁移

暂不建议自动迁移：

- `office_generation` 类：大量脚本可能写死模板路径和输出路径。
- `other` 类：必须逐个识别用途。

## 4. 迁移前检查

移动脚本前至少检查：

1. 是否被其他脚本 import。
2. 是否写死相对路径，如 `../`、`output/`、`knowledge/`、`tmp/`。
3. 是否依赖当前工作目录。
4. 是否有对应成果文件，能否复跑。
5. 是否是最终版，还是旧版本/测试版。

## 5. 当前不建议做的事

- 不直接把 704 个脚本一次性搬目录。
- 不删除 `*.py`，即便看起来像临时脚本。
- 不清理 `output/` 页图，除非确认 OCR 文本和 Markdown 完整。
- 不删除 `.rag_index`，除非先跑通重建。

## 6. 下一步可执行动作

建议下一步执行“脚本低风险迁移预案”：

1. 扫描 `asset_scripts_structured_candidates.csv` 中 `rag`、`case_collection`、`guards`、`debug_or_cache` 四类。
2. 生成 `asset_scripts_migration_plan_lowrisk.csv`，列出源路径、目标路径、风险等级。
3. 对低风险类先复制或移动，并保留迁移日志。
4. 修改/补充 `scripts/README.md`。

## 7. 维护口径

以后新脚本不要直接扔 `scripts/` 根目录：

- 知识库相关 -> `scripts/rag/`
- OCR 相关 -> `scripts/ocr/`
- 案例采集 -> `scripts/case_collection/`
- 报告复核 -> `scripts/report_review/`
- 招投标/串标 -> `scripts/bidding_analysis/`
- Word/Excel/PPT 生成 -> `scripts/office_generation/`
- Token/API/成本控制 -> `scripts/guards/`
- 临时调试 -> `scripts/archive_debug/` 或 `tmp/`
