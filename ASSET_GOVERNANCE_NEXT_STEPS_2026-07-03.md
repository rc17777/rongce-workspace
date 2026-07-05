# 融策 AI 资产治理后续清单（2026-07-03）

## 本次已完成

- 生成资产地图：`ASSET_MAP_2026-07-03.md`
- 生成脚本台账：`asset_inventory_scripts.csv`
- 生成输出成果台账：`asset_inventory_outputs.csv`
- 生成根目录清理候选台账：`asset_inventory_root_cleanup.csv`
- 完成根目录第一轮归档：
  - 13 个网页抓取/搜索中间文件 -> `archive/web_fetch/2026-07/root/`
  - 28 个根目录脚本 -> `archive/scripts/root_2026-07/`
  - 3 个磁盘清理记录 -> `logs/disk-cleanup/`
  - 1 个政策提取中间文件 -> `archive/policy_intermediate/2026-07/`
  - 2 个 Office 生成批处理配置 -> `archive/scripts/office_generation_2026-07/`
  - 业务/产品/管理类 Markdown -> `RONGCE_AI_HUB/products/` 或 `RONGCE_AI_HUB/company-management/`
- 合并迁移日志：`asset_migration_log_all_2026-07-03.csv`

## 当前根目录应保留文件

根目录现在主要保留三类文件：

1. OpenClaw/助手控制文件：`AGENTS.md`、`SOUL.md`、`USER.md`、`MEMORY.md`、`TOOLS.md`、`HEARTBEAT.md`、`IDENTITY.md`。
2. 资产治理文件：`ASSET_MAP_2026-07-03.md`、`asset_inventory_*.csv`、`asset_migration_log_*.csv`。
3. 总入口/框架文件：`SCENARIO-SKILL-MAP.md`、`SKILLS.md`、`audit_digital_framework.md`、`RESTORED_SOURCES.md`。

## 下一步建议

### P1：治理 `scripts/`（已完成主线）

目标：把 704 个脚本分层，让常用工具能找得到。

已完成：

- 已迁移并记录 200 个脚本/相关文件，日志见 `asset_scripts_migration_log_all_2026-07-03.csv`：
  - `rag` -> `scripts/rag/`：10 个
  - `ocr` -> `scripts/ocr/`：28 个
  - `case_collection` -> `scripts/case_collection/`：4 个
  - `report_review` -> `scripts/report_review/`：12 个
  - `bidding_analysis` -> `scripts/bidding_analysis/`：21 个
  - `office_generation` -> `scripts/office_generation/`：75 个
  - `guards` -> `scripts/guards/`：18 个
  - `debug_or_cache` -> `scripts/archive_debug/`：32 个
- 已为 `scripts/` 和主要子目录补 README。
- `scripts` 根目录还剩 225 个 `other` 类脚本，已导出 `asset_scripts_remaining_root_final.csv`，需要按项目/业务线进一步人工判定，不建议自动搬。

### P2：治理 `output/outputs`

目标：区分最终成果和中间文件。

建议动作：

- 最终成果：`.docx`、`.xlsx`、`.pptx`、`.pdf`、`.md` 进入项目成果目录。
- 结构化输出：`.json`、`.txt` 保留到项目目录，作为可复核证据。
- 页图/截图：`.png`、`.jpeg` 先按项目压缩归档，确认 Markdown/TXT 完整后再考虑删除。
- 缓存：`.pyc`、`.tmp` 可清理。

### P3：治理 `knowledge/`

目标：知识库只做索引和归类，不轻易删除。

建议动作：

- 按业务线补充资料索引。
- 对 OCR 案例统一命名，减少乱码目录影响。
- 对已入 RAG 的资料标记“已索引”。
- 对重复 PDF/Markdown 做去重候选清单，先不删。

### P4：更新入口文档

目标：以后不用靠记忆找工具。

建议动作：

- 更新 `RONGCE_AI_HUB/README.md`，加入新归档目录说明。
- 更新 `RONGCE_AI_HUB/ROUTING.md`，加入产品资料、公司管理资料入口。
- 给 `archive/` 写一个 README，说明归档不是垃圾桶。

## 风险提示

- 不建议现在删除 `output/` 里的图片页图，因为部分 OCR/报告复核可能还需要回看原图。
- 不建议删除 `.rag_index`，除非先确认 `scripts/rag_rebuild.py` 可稳定重建。
- 脚本移动前应先识别 import 依赖，避免相对路径失效。
