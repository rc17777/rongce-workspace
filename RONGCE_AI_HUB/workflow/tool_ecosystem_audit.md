# 融策业务工具组成全景审计 v1.0

> 2026-07-17 | 融策右护卫

---

## 总况

| 维度 | 数量 | 健康度 |
|:--|:--|:--|
| 脚本文件 | **464** | 🟡 臃肿 |
| 其中版本迭代脚本 | **52** | 🔴 重复 |
| 其中临时/debug脚本 | **33** | 🔴 应清理 |
| Skills | **60** | 🟢 覆盖面好 |
| 实际高频活跃技能 | **16** | 🟢 集中 |
| 工作区一级目录 | **70+** | 🔴 严重膨胀 |
| Agent规格 | **16** | 🟢 够用 |
| 核心工作流脚本 | **5** | 🟢 新且干净 |

---

## 一、按7阶段工作流映射（只列活跃工具）

### ①a 项目初始化
| 工具 | 类型 | 状态 | 说明 |
|:--|:--|:--|:--|
| `workflow_engine.py` | 新脚本 | ✅ v1.1 | 7阶段引擎 |
| `launch.py` | 脚本 | ✅ | Agent一键启动 |
| `orchestrate.py` | 脚本 | ✅ | 多Agent调度 |

### ①b OCR预处理
| 工具 | 类型 | 状态 | 说明 |
|:--|:--|:--|:--|
| `paddleocr_audit_batch.py` | 脚本 | ✅ 主力 | PaddleOCR批量 |
| `ocr_intelligent_audit_v3.py` | 脚本 | ✅ | 智能审计OCR |
| `contract_ocr_v5.py` | 脚本 | ✅ | 合同专用OCR |
| `ocr_scoring.py` | 脚本 | 🟡 辅助 | OCR质量评估 |
| `ocr_easy.py` | 脚本 | 🟡 | 简单OCR |
| ⚠️ 缺失 | — | 🔴 | **发票专用OCR（发票API版）** |

### ①c 智能分类
| 工具 | 类型 | 状态 | 说明 |
|:--|:--|:--|:--|
| `data_classifier` | Agent | ✅ | 自动分类打标签 |
| ⚠️ 缺失 | — | 🔴 | **分类准确率校验脚本** |
| ⚠️ 缺失 | — | 🔴 | **数据质量检查（OCR后校验）** |

### ② 实施方案与资料清单
| 工具 | 类型 | 状态 | 说明 |
|:--|:--|:--|:--|
| `plan_writer` | Agent | ✅ | 方案+清单生成 |
| `plan_generator.py` | 脚本 | 🟡 | 旧版，应合并到Agent |
| `generate_audit_template.py` | 脚本 | 🟡 | 模板生成 |
| `generate_audit_workbook.py` | 脚本 | 🟡 | 工作簿生成 |
| ⚠️ 缺失 | — | 🔴 | **审计抽样方案生成**（风险导向/分层/金额抽样） |

### ③ 多Agent分析
| 工具 | 类型 | 状态 | 说明 |
|:--|:--|:--|:--|
| `issue_fusion.py` | 新脚本 | ✅ v1.0 | 疑点融合中枢 |
| `bid_hunter` | Agent | ✅ | 招投标23层检测 |
| `data_scout` | Agent | ✅ | 财务异常扫描 |
| `contract_hound` | Agent | ✅ | 合同审查 |
| `law_inspector` | Agent | ✅ | 法规匹配 |
| `performance_evaluator` | Agent | ✅ | 绩效验证 |
| 工程类Agent ×4 | Agent | ✅ | 预算/财评/结算/全咨 |
| `tfidf_bid_check.py` | 脚本 | ✅ | 投标文本雷同 |
| `bid_similarity_check.py` | 脚本 | ✅ | 投标相似度 |
| `bid_detail_match.py` | 脚本 | ✅ | 投标详情匹配 |
| `metadata_analysis.py` | 脚本 | ✅ | 元数据分析 |
| `cross_analysis.py` | 脚本 | 🟡 | 交叉分析 |
| `contract_nlp_ocr_v3.py` | 脚本 | 🟡 | 合同NLP |
| `audit_full_analysis.py` | 脚本 | 🟡 | 全量分析 |
| `deepseek-charting` | Skill | ✅ | 图表生成 |
| `data-analyst-cn` | Skill | ✅ | 数据分析 |
| `financial-fraud-detection` | Skill | ✅ | Benford造假检测 |
| `procurement-audit-models` | Skill | ✅ | 采购审计模型 |
| ⚠️ 缺失 | — | 🔴 | **审计调整分录生成器** |
| ⚠️ 缺失 | — | 🔴 | **会议纪要Agent**（经责审计核心） |
| ⚠️ 缺失 | — | 🔴 | **资金流向图生成** |

### ④ 取证单与底稿
| 工具 | 类型 | 状态 | 说明 |
|:--|:--|:--|:--|
| `workpaper_crafter` | Agent | ✅ | 取证单+底稿 |
| `settlement_audit_template.py` | 脚本 | 🟡 | 结算底稿模板 |
| `audit_finding_processor.py` | 脚本 | 🟡 | 发现处理器 |
| ⚠️ 缺失 | — | 🔴 | **审计厅标准模板库**（取证单/底稿的Word模板） |

### ⑤ 报告撰写
| 工具 | 类型 | 状态 | 说明 |
|:--|:--|:--|:--|
| `report_writer` | Agent | ✅ | 报告撰写 |
| `review_sentinel` | Agent | ✅ | 15维复核 |
| `report_review_workflow.py` | 脚本 | ✅ | 复核工作流 |
| `report_review_rag_enhanced.py` | 脚本 | ✅ | RAG增强复核 |
| `audit_report_review.py` | 脚本 | ✅ | 报告复核 |
| `audit_doc_formatter.py` | 脚本 | ✅ | 公文格式化 |
| `audit-report-review` | Skill | ✅ | 复核方法论 |
| `doc-formatter` | Skill | ✅ | 文档格式 |
| `officecli-docx` | Skill | ✅ | Word操作 |
| `huashu-design` | Skill | ✅ | 设计排版 |
| `dashi-ppt` | Skill | 🟡 | PPT（成本高，慎用） |

### ⑥ 反馈闭环归档
| 工具 | 类型 | 状态 | 说明 |
|:--|:--|:--|:--|
| `ingest_laws.py` | 脚本 | ✅ | 法规入库 |
| `prune_knowledge.py` | 脚本 | ✅ | 知识库清理 |
| `rag_rebuild.py` | 脚本 | ✅ | RAG索引重建 |
| `rag_query.py` | 脚本 | ✅ | RAG查询 |
| `rag_bridge.py` | 脚本 | ✅ | RAG↔Obsidian桥接 |
| `build_links.py` | 脚本 | ✅ | 双向链接 |
| `build_skill_tree.py` | 脚本 | ✅ | 技能树 |
| `case_collector.py` | 脚本 | 🟡 | 案例采集 |
| `project_knowledge_feedback.py` | 脚本 | 🟡 | 项目反馈 |
| `zhixi-v2-enhanced` | Skill | ✅ | 智析v2 API |
| `rule-library/` | 中枢 | ✅ | 审计规则库 |
| ⚠️ 缺失 | — | 🔴 | **案例→规则自动化提取脚本**（case-to-rule） |

### 跨阶段基础设施
| 工具 | 类型 | 状态 | 说明 |
|:--|:--|:--|:--|
| `model_health_check.py` | 脚本 | ✅ | 14模型健康检查 |
| `token_tracker.py` | 脚本 | ✅ | Token追踪 |
| `token_budget.py` | 脚本 | ✅ | 预算估算 |
| `deepseek_cost_guard.py` | 脚本 | ✅ | 费用守卫 |
| `api_guard.py` | 脚本 | ✅ | API限流 |
| `spawn_guard.py` | 脚本 | ✅ | Spawn安全 |
| `skill_hub.py` | 脚本 | ✅ | 技能控制面板 |
| `skills_audit.py` | 脚本 | ✅ | 技能审计 |
| `task_trace.py` | 脚本 | ✅ | 任务追踪 |
| `workflow_with_budget.py` | 脚本 | ✅ | 工作流预算 |
| `literature_collector.py` | 脚本 | ✅ | 文献采集 |
| `audit_intel_collector.py` | 脚本 | ✅ | 审计情报 |
| `data_security_policy.md` | 文档 | ✅ | 数据安全分级 |

---

## 二、冗余与僵尸资产

### 🔴 应清理（52+33 = 85个文件）

**版本迭代垃圾（52个）**：
- `*_v2`, `*_v3`, `*_v4`, `*_v5` 模式——只要最新版，旧版进 `scripts/_legacy/`
- 典型：`hongboshi_*.py`（8个版本！）、`extract_pricing*.py`、`fix_v4_*.py`、`generate_charts*.py`

**临时/Debug脚本（33个）**：
- `tmp_*.py`（10个+）
- `debug_*.py`、`check_result*.py`、`verify_*.py`
- 一次性修复脚本 `fix_*.py`

**乱码文件名**：约10个（Windows GBK编码问题的产物）

### 🟡 应合并（功能性重叠）

| 重叠组 | 涉及文件 | 建议 |
|:--|:--|:--|
| OCR相关 | 22个 | 保留3个核心（paddleocr_batch/contract_ocr/ocr_intelligent），其余归档 |
| 报告生成 | 54个 | 保留5个活跃的，整合到report_writer Agent |
| 招投标分析 | 16个 | 保留3个（tfidf/bid_similarity/bid_detail），Bid_hunter Agent已经做了很多 |
| 知识库管理 | 22个 | 保留核心RAG套件（rag_*.py），清理旧版kb_*.py |

### 🟡 应归档的工作区目录（70+ → 建议30个）

大量一次性项目目录可归入 `archive/`:
- `bid_aba/`, `chayu_analysis/`, `data-analysis-agent/`, `deep-research/`
- `rongce-ocr-agent/`, `rongce-ppt-master/`, `test_tools/`
- `paper_skill_verify/`, `paper-craft-skills/`
- 各种 `_tmp_*`, `temp*`, `tmp/`
- 乱码目录名

---

## 三、缺失工具（按优先级）

### 🔴 P0 — 应该立刻补

| # | 缺失工具 | 用途 | 位于阶段 | 工作量 |
|:--|------|------|:--|:--|
| 1 | **发票专用OCR** | PaddleOCR+发票API，替代qwen-vl-max | ①b | 1天 |
| 2 | **数据质量检查器** | OCR后字段校验、缺失检测、异常标记 | ①b→①c | 1天 |
| 3 | **审计抽样引擎** | 分层/金额/风险导向抽样，自动出抽样方案 | ② | 2天 |
| 4 | **会议纪要Agent** | 经责审计核心——党委会/办公会纪要分析 | ③ | 1天 |
| 5 | **审计调整分录生成器** | 发现问题→自动生成调整分录 | ③ | 1天 |

### 🟡 P1 — 中期应补

| # | 缺失工具 | 用途 | 工作量 |
|:--|------|------|:--|
| 6 | **审计厅模板库** | 标准取证单/底稿Word模板，供workpaper_crafter填充 | 1天 |
| 7 | **资金流向图谱** | 拨款→银行流水→用款单位的可视化追踪 | 2天 |
| 8 | **案例→规则自动化** | case-to-rule脚本化，Phase ⑥的核心 | 2天 |
| 9 | **客户反馈追踪器** | 征求意见→反馈→逐条处理→报告修订 | 1天 |
| 10 | **资料版本管理器** | 多批次资料→版本对比→差异标注 | 2天 |

### 🟢 P2 — 锦上添花

| # | 缺失工具 | 用途 |
|:--|------|------|
| 11 | 项目进度仪表盘（Web可视化） | HTML看板，7阶段进度一目了然 |
| 12 | 审计知识图谱可视化 | Neo4j→Web，关联关系探索 |
| 13 | 企业微信推送集成 | 项目进度推送到企微群 |

---

## 四、Skill使用率分析

| 状态 | 数量 | 占比 | 说明 |
|:--|:--|:--|:--|
| 高频活跃（每次审计都用） | 16 | 27% | 审计复核/PPT/OCR/数据分析/法规/图表 |
| 场景触发（特定业务线用） | 28 | 47% | 经责/招投标/绩效/工程/补贴 |
| 低频辅助 | 11 | 18% | 浏览器/Whisper/视频/系统调试 |
| 可能已死 | 5 | 8% | 长期未触发，待确认 |

---

## 五、本次迭代建议（7天执行计划）

| 天 | 行动 | 产出 |
|:--|------|------|
| Day 1 | **脚本大扫除** — 删除tmp/debug/旧版本，52个版本迭代进_legacy | 464→~280文件 |
| Day 2 | **补5个P0缺失** — 发票OCR / 数据质量检查 / 审计抽样 / 会议纪要Agent / 调整分录 | 5个新工具 |
| Day 3 | **Skill审计** — 标记5个已死技能，更新16个高频技能的触发文档 | skills_audit报告 |
| Day 4 | **目录归档** — 70+目录→30目录，乱码目录修复 | 清爽工作区 |
| Day 5 | **补P1缺失** — 审计厅模板库 / 资金流向图 / case-to-rule | 3个新工具 |
| Day 6 | **端到端集成测试** — 拿一个真实项目跑完整7阶段 | 实战验证 |
| Day 7 | **文档更新** — README/索引/SCENARIO-SKILL-MAP全面刷新 | 文档对齐 |

---

## 六、一言总结

**现状**：基础不错（工作流引擎/疑点中枢/模型路由/数据安全都建了），但被464个脚本和70个目录拖累——像一个堆满工具的车间，找扳手要翻三分钟。

**方向**：先清理（砍掉100+垃圾文件），再补缺（6个P0+P1缺失工具），最后归档（70目录→30目录）。

**一句话**：工具不在于多，在于每次审计你打开workspace，能一眼看到该用的那个。
