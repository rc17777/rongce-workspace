# 融策脚本工具库

本目录存放融策 AI 工作区的可复用脚本。新脚本不要直接堆在 `scripts/` 根目录，按用途放入子目录。

## 目录分层

| 目录 | 用途 |
|---|---|
| `rag/` | 本地知识库索引、查询、Web 服务、RAG 配置 |
| `ocr/` | OCR、PDF/图片转文本、百度/ABBYY/Paddle 等识别流程 |
| `case_collection/` | 审计案例采集、分类、归档 |
| `report_review/` | 审计报告复核、质控、复核表生成 |
| `bidding_analysis/` | 招投标、串标、TF-IDF、元数据、图片哈希分析 |
| `office_generation/` | Word/Excel/PPT/模板生成 |
| `guards/` | Token、成本、API、spawn、模型健康检查等守卫脚本 |
| `archive_debug/` | 调试脚本、旧版本、缓存文件；不作为日常入口 |

## 使用原则

1. 项目型脚本优先放入项目目录，只有可复用脚本放入这里。
2. 新脚本必须在文件头或 README 里写明输入、输出、依赖和运行命令。
3. 不确定用途的脚本先留在根目录或 `archive_debug/`，不要混入主工具目录。
4. 移动旧脚本前检查相对路径、import 和硬编码文件路径。

## 迁移记录

- 2026-07-03：完成第一批低风险迁移，详见工作区根目录 `asset_scripts_migration_log_lowrisk_2026-07-03.csv`。
