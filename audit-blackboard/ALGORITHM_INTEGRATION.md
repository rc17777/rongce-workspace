# 融策 22Agent 体系 × 政府审计算法资产库 v5.0（135个）集成说明

> 版本：v5.0 ｜ 生成时间：2026-08-06
> 注册表：`audit-blackboard/algorithm_registry.json`（135算法）
> 加载器：`audit-blackboard/algorithm_loader.py`
> 构建脚本：`audit-blackboard/build_algorithm_registry_v5.py`
> Agent规格更新：`audit-blackboard/update_agent_algorithms_v5.py`
> 辅助Agent补齐：`temp/update_aux_agents_v5.py`
> 来源：《政府审计算法资产库_v5.xlsx》（40旗舰 × 40要素 + 95骨架 × 15要素）

---

## 📂 按业务场景目录（场景维度入口，v1.0）

算法库除 Agent 维度外，另提供**业务场景维度**的组织与查询：

| 文件 | 用途 |
|:--|:--|
| `scene_taxonomy.json` | 标准业务场景体系（14 个一级场景 + 52 个二级细分 + 关键词规则） |
| `algorithms_by_scene.json` | 场景 → 算法映射（每算法含主场景 + 附加场景） |
| `ALGORITHMS_BY_SCENE.md` | 按业务场景目录文档（人读，含归属标注） |
| `build_scene_catalog.py` | 场景目录构建脚本（从 registry 重建） |

**14 个一级场景**：招投标与政府采购（21）｜ 农业农村审计（14）｜ 民生与社保医保（27）｜ 金融审计（12）｜ 工程与投资审计（22）｜ 资源环境审计（12）｜ 国企审计（25）｜ 财政与政府债务（20）｜ 预算执行与财政管理（24）｜ 绩效评价（13）｜ 经济责任审计（19）｜ 监督检查与经费舞弊（17）｜ 税务审计（6）｜ 全场景通用（5）

**查询示例**（场景目录优先，taxonomy 关键词 + 文本回退）：

```python
from algorithm_loader import list_scenes, list_algorithms_by_scene, get_scene_catalog_summary

list_scenes()                     # 全部场景 + 算法数
list_algorithms_by_scene("社保审计")  # 自动命中"民生与社保医保"（27个）
list_algorithms_by_scene("医院采购")  # 自动命中"招投标与政府采购"（21个）
list_algorithms_by_scene("小金库")    # 自动命中"监督检查与经费舞弊"（17个）
get_scene_catalog_summary()       # 135 算法 / 14 场景
```

重建：`python -X utf8 build_scene_catalog.py`（读取 registry，重新生成三个文件）

---

---

## 1. 集成架构图

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                      融策 22Agent 体系（审计编排层 v5.0）                        │
│                                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ 数据侦察兵     │  │ 预算工程师     │  │ 招投标猎手     │  │ 合同猎犬       │      │
│  │ data_scout   │  │budget_est    │  │ bid_hunter   │  │contract_hound│      │
│  │  98个(28旗舰)  │  │  35个(5旗舰)  │  │  18个(5旗舰)  │  │  18个(4旗舰)  │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                 │                 │                 │               │
│  ┌──────┴───────┐  ┌──────┴───────┐  ┌──────┴───────┐  ┌──────┴───────┐      │
│  │ 复核哨兵       │  │ 法规检察官     │  │ 财政评审员     │  │ 结算审计师     │      │
│  │review_sentinel│  │law_inspector │  │fiscal_review │  │settlement_aud│      │
│  │  17个(6旗舰)  │  │  16个(5旗舰)  │  │  15个(4旗舰)  │  │  11个(4旗舰)  │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                 │                 │                 │               │
│  ┌──────┴───────┐  ┌──────┴───────┐  ┌──────┴───────┐  ┌──────┴───────┐      │
│  │ 绩效评价师     │  │ 底稿工匠       │  │ 报告笔杆子     │  │  调整分录师    │      │
│  │perf_eval     │  │wpaper_crafter│  │report_writer │  │adj_scribe    │      │
│  │  10个(4旗舰)  │  │   3个(1旗舰)  │  │   3个(0旗舰)  │  │   2个(0旗舰)  │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                 │                 │                 │               │
│  ┌──────┴───────┐  ┌──────┴───────┐  ┌──────┴───────┐  ┌──────┴───────┐      │
│  │会议纪要分析    │  │数据分类员     │  │方案撰写师     │  │OCR预处理      │      │
│  │meeting_analy │  │data_classifier│  │plan_writer  │  │ocr_processor │      │
│  │   1个(0旗舰)  │  │   1个(0旗舰)  │  │   1个(0旗舰)  │  │   0个  🛠️    │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                 │                 │                 │               │
│  ┌──────┴───────┐  ┌──────┴───────┐  ┌──────┴───────┐  ┌──────┴───────┐      │
│  │数据脱敏       │  │评标偏离度     │  │覆盖率100%    │  │  135算法全集   │      │
│  │desensitizer  │  │expert_bias   │  │18/18 Agent已 │  │  249次分配    │      │
│  │   0个  🛠️    │  │   0个  ⚠️    │  │全部集成完毕   │  │               │      │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────┼──────────────────┼──────────────────┼─────────────────────────────┘
          │                  │                  │
          ▼                  ▼                  ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                algorithm_loader.py（v5.0 统一加载器）                             │
│  load_registry / get_algorithms_for_agent / get_agent_for_scene /              │
│  get_algorithm_detail / list_by_biz_line / get_algorithm_count /             │
│  list_algorithms_by_scene / search_algorithms / reload_registry              │
└─────────────────────────────────┬────────────────────────────────────────────┘
                                  │
                                  ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                    algorithm_registry.json（135算法 × 完整要素）                  │
│  version: 5.0 | 旗舰40 + 骨架95 | L3:106 L2:26 L4:2                          │
│  分配关系: 249条 Agent↔算法 | 18个Agent全覆盖                                  │
└─────────────────────────────────┬────────────────────────────────────────────┘
                                  │
                                  ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                    政府审计算法资产库_v5.xlsx（Excel 数据源）                      │
│  ☆算法资产库总览 (135行) | ☆算法详细卡片 (135张卡, 4164行)                      │
└──────────────────────────────────────────────────────────────────────────────┘
```

**数据流向：** Excel 总览 + 详细卡片 → `build_algorithm_registry_v5.py`（前缀规则 + v4 人工映射继承 + Agent映射提示）→ `algorithm_registry.json` → `algorithm_loader.py`（API层）→ `agent_specs/*.json`（Agent推理上下文）

---

## 2. Agent-算法映射矩阵（全量18 Agent）

### 2.1 主战Agent（10个，负责核心审计业务）

| Agent | ID | 算法数 | 旗舰P0 | 骨架P1 | 典型场景 |
|-------|-----|--------|--------|--------|----------|
| 数据侦察兵 | `data_scout` | **98** | 28 | 70 | 全场景数据扫描/异常检测 |
| 预算工程师 | `budget_estimator` | **35** | 5 | 30 | 预算执行/转移支付/政府债务 |
| 招投标猎手 | `bid_hunter` | **18** | 5 | 13 | 围标串标/供应商检测/采购审计 |
| 合同猎犬 | `contract_hound` | **18** | 4 | 14 | 合同履约/供应商关系/亏损穿透 |
| 复核哨兵 | `review_sentinel` | **17** | 6 | 11 | 勾稽核对/终审复核/证据闭环 |
| 法规检察官 | `law_inspector` | **16** | 5 | 11 | 合规审查/环保法规/自然资源 |
| 财政评审员 | `fiscal_reviewer` | **15** | 4 | 11 | 财政政策/转移支付/债务风险 |
| 结算审计师 | `settlement_auditor` | **11** | 4 | 7 | 工程结算/造价审计/GIS验证 |
| 绩效评价师 | `performance_evaluator` | **10** | 4 | 6 | 绩效偏离/成本效益/指标评价 |
| 底稿工匠 | `workpaper_crafter` | **3** | 1 | 2 | 底稿嵌入/往来科目/村级财务 |

### 2.2 辅助Agent（8个，补齐审查与集成链路）

| Agent | ID | 算法数 | 旗舰P0 | 骨架P1 | 典型场景 | 备注 |
|-------|-----|--------|--------|--------|----------|------|
| 报告笔杆子 | `report_writer` | **3** | 0 | 3 | 问题清单/废标报告/终身追溯 | 生成的报告嵌入算法分析结果 |
| 调整分录师 | `adjustment_scribe` | **2** | 0 | 2 | 资产入账/税款测算 | 从审计发现问题→标准化调整分录 |
| 会议纪要分析 | `meeting_minutes_analyzer` | **1** | 0 | 1 | 举报闭环/台账梳理 | WHISTLE-FLOW-001 举报流程分析 |
| 数据分类员 | `data_classifier` | **1** | 0 | 1 | 元数据扫描/指纹比对 | BID-DARKMARK-001 暗标围标指纹标记 |
| 方案撰写师 | `plan_writer` | **1** | 0 | 1 | 标准产出/方案撰写 | PERF-COST-001 绩效成本标准产出 |
| 评标偏离度 | `expert_bias_detector` | **0** | — | — | 评标偏离度检测 | ⚠️ 无算法依赖（待分配） |
| OCR预处理 | `ocr_processor` | **0** | — | — | 文档OCR/表格识别 | 🛠️ 纯工具Agent（预处理层） |
| 数据脱敏 | `data_desensitizer` | **0** | — | — | 敏感信息脱敏/匿名化 | 🛠️ 纯工具Agent（预处理层） |

> **注：**
> - 🛠️ **纯工具Agent**（OCR预处理、数据脱敏）：属于预处理/后处理层，不依赖算法资产库的审计推理算法。其"算法"为工程实现层面的OCR引擎（PaddleOCR/Tesseract）和规则脱敏，非`algorithm_registry.json`中的审计算法。
> - ⚠️ **评标偏离度检测**（`expert_bias_detector`）：registry 中无分配条目（`total_assigned=0`），工作流中作为评标专家的行为偏差检测节点存在，待后续版本分配独立算法。

### 2.3 汇总统计

| 维度 | 数值 |
|------|------|
| Agent总数 | 18（10主战 + 8辅助） |
| 算法总数 | 135（旗舰40 + 骨架95） |
| 分配总次数 | 249（平均 1.84 个Agent/算法） |
| 旗舰分配总次数 | 66（覆盖所有40个旗舰算法） |
| 骨架分配总次数 | 183 |
| 有算法分配的Agent | 15/18（83%） |
| 无算法分配的Agent | 3/18（expert_bias_detector, ocr_processor, data_desensitizer） |

---

## 3. Agent-算法分配规则

### 3.1 三层映射策略

每个算法的最终 Agent 分配由三层规则合成（优先级递减）：

```
┌─────────────────────────────────────────────────────┐
│ Layer 1: Excel "Agent映射" 列（人工工作流提示）         │  ← 最高优先级
│ 例："数据侦察兵（GIS叠加）→ 法规检察官（责任定性）→ ..."  │
└─────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────┐
│ Layer 2: v4.0 人工审核映射（40个旗舰算法的继承基线）      │
│ 例：FUND-FRAUD-001 → [data_scout, performance_eval] │
└─────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────┐
│ Layer 3: 前缀规则（专项 Agent 保底）                     │
│ BID-* → bid_hunter, BUDGET-* → budget_estimator...  │
└─────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────┐
│ Agent 数上限: 3（1个主Agent + 最多2个副Agent）          │
│ 十字交叉型（如 ENG-FINAL）自动获得多Agent协同              │
└─────────────────────────────────────────────────────┘
```

### 3.2 前缀规则明细

| 算法前缀 | 专项 Agent | 说明 |
|----------|-----------|------|
| `BID-*`, `PROC-*` | `bid_hunter` | 招投标/政府采购 |
| `BUDGET-*`, `BUD-*` | `budget_estimator` | 预算执行/财政 |
| `PERF-*` | `performance_evaluator` | 绩效评价 |
| `ENG-*` | `settlement_auditor` | 工程结算 |
| `SOE-*`, `CHK-LOSS-*` | `contract_hound` | 国企/合同/亏损穿透 |
| `ENV-*` | `law_inspector` | 资源环境/合规 |
| `SOCIAL-*`, `MED-*` | `data_scout` | 民生/医疗 |
| `TAX-*`, `FIN-*` | `data_scout` | 税务/金融 |
| `FUND-*`, `AGR-*` | `data_scout` | 资金/农业农村 |
| `BIGDATA-*`, `DATA-*`, `ITCOST-*` | `data_scout` | 大数据/信息化 |
| `POLICY-*`, `ECONRESP-*` | `fiscal_reviewer` | 财政政策/经责 |
| `HR-*`, `SUPV-*` | `data_scout` | 人力/监督检查 |
| `CHK-*` | `data_scout` + `review_sentinel` | 核对/勾稽 |
| 其余 | `data_scout` | 通用数据扫描兜底 |

> **注意：** 前缀匹配使用 `startswith`，可以正确匹配 `PERF2-001`、`ENV3-001`、`ECONRESP2-001` 等批次后缀编号。

---

## 4. 复杂度与类型统计

| 维度 | 分布 |
|------|------|
| **算法类型** | 旗舰 40（P0）/ 骨架 95（P1） |
| **复杂度** | L3: 106 | L2: 26 | L4: 2 | L3-ML: 1 |
| **风险机制 Top3** | 真实性 78 | 合规性 25 | 异常性 11 |
| **Agent 交叉度** | 单Agent: 48 | 双Agent: 60 | 三Agent: 27 |

---

## 5. 使用示例

### 5.1 加载指定Agent的算法

```python
from algorithm_loader import get_algorithms_for_agent

# 获取预算工程师的所有算法
algos = get_algorithms_for_agent("budget_estimator")
for a in algos[:3]:
    print(f"{a['sn']} {a['name'][:30]} [{a['type']}] [{a['complexity']}]")
# BOND-PENETRATE-001 专项债资金穿透式监测算法 [旗舰] [L3]
# BUD-CHECKLIST-001 预算执行60条违规清单对照算法 [旗舰] [L3]
# BUDGET-001 专项债券资金支出进度真实性核验算法 [骨架] [L3]
```

### 5.2 按场景查找Agent

```python
from algorithm_loader import get_agent_for_scene

agents = get_agent_for_scene("社保审计")
print(agents)
# ['data_scout', 'performance_evaluator', 'law_inspector', 'review_sentinel']
```

### 5.3 按业务线列出算法

```python
from algorithm_loader import list_by_biz_line

biz = list_by_biz_line("预算执行")
for b in biz[:3]:
    print(f"{b['sn']} {b['name'][:40]} [{b['priority']}]")
```

### 5.4 获取总体统计

```python
from algorithm_loader import get_algorithm_count

stats = get_algorithm_count()
print(f"算法总数: {stats['total']}")
print(f"旗舰: {stats['by_type']['旗舰']}, 骨架: {stats['by_type']['骨架']}")
print(f"Agent数: {stats['agent_count']}")
# 算法总数: 135
# 旗舰: 40, 骨架: 95
# Agent数: 18
```

### 5.5 多Agent协同编排（十字交叉型）

```python
from algorithm_loader import get_algorithm_detail, get_algorithms_for_agent

# ENG-FINAL-001 = 十字交叉型（结算审计师 + 复核哨兵 + 财政评审员）
detail = get_algorithm_detail("ENG-FINAL-001")
print(detail["assigned_agents"])
# ['settlement_auditor', 'review_sentinel', 'fiscal_reviewer']

# 编排逻辑：结算审计师先核算工程数据 → 财政评审员做政策合规检查 → 复核哨兵终审
```

### 5.6 辅助Agent算法查询

```python
from algorithm_loader import get_algorithms_for_agent, get_algorithm_detail

# 调整分录师：查询分配的算法
algos = get_algorithms_for_agent("adjustment_scribe")
for a in algos:
    print(f"{a['sn']}: {a['name']} [{a['type']}]")
# AGRI3-005: 涉农资金往来科目异常检测算法 [骨架]
# TAX-ESCAPE-001: 增值税进销项匹配差异算法 [骨架]

# 纯工具Agent：返回空列表
algos = get_algorithms_for_agent("ocr_processor")
print(algos)  # [] — OCR预处理层，无审计算法依赖
```

---

## 6. 文件清单

| 文件 | 用途 | 大小 |
|------|------|------|
| `algorithm_registry.json` | 135个算法完整注册表（JSON） | ~1MB |
| `algorithm_loader.py` | 加载器（7个查询API + 向后兼容） | ~7KB |
| `build_algorithm_registry_v5.py` | 从 Excel 重建注册表的构建脚本 | ~13KB |
| `update_agent_algorithms_v5.py` | 更新18个 Agent 规格的algorithms字段 | ~3KB |
| `temp/update_aux_agents_v5.py` | 补齐8个辅助Agent的algorithms字段 | ~2KB |
| `agent_specs/*.json` | 18个Agent规格（含algorithms块 + 标注） | vary |
| `ALGORITHM_INTEGRATION.md` | 本文档（集成说明） | — |

---

## 7. 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2025-Q1 | 初始集成：40个旗舰算法 → 10个Agent（v4 Excel） |
| v5.0 | 2026-08-06 | **重大升级**：135个算法（40旗舰 + 95骨架）→ 18个Agent ✅ |
|  |  | 前缀规则改为startswith匹配（修复PERF2/ENV3/ECONRESP2等批次后缀） |
|  |  | 新增 `list_by_biz_line`、`get_algorithm_count`、`list_algorithms_by_scene` API |
|  |  | Agent规格追加 `algorithms` 块（version/registry/total_assigned/assigned + quick_ref/usage） |
|  |  | 三层映射策略（Excel提示 → v4继承 → 前缀保底） |
|  |  | 算法数上限3（主Agent + 2副Agent） |
|  |  | 8个辅助Agent补齐（含3个纯工具/无算法Agent标注） |
|  |  | 全量校验：249次分配，18 Agent全覆盖，registry与spec数据一致性100% |

---

## 8. 已知差异说明

v5.0部分Agent的算法数超出了任务书 v4.0 时代预估：

| Agent | 预估 | 实际 | 原因 |
|-------|------|------|------|
| `bid_hunter` | 8-10 | 18 | BID-* + PROC-* 规则覆盖10个前缀算法，另有跨领域分配8个 |
| `budget_estimator` | 15-20 | 35 | BUDGET-001~020（20个）全部归入 + 转移支付/债务/县域风险等15个 |
| `contract_hound` | 5-6 | 18 | SOE-* 规则覆盖4个 + CHK-LOSS-* 1个 + 工作流提示交叉13个 |
| `review_sentinel` | 6-8 | 17 | CHK-*/CHK2-* 全部归入 + 工作流中复核哨兵作为终审节点频繁出现 |
| `law_inspector` | 5-6 | 16 | ENV-* 规则覆盖7个 + TAX/FIN/法规引用交叉9个 |
| `fiscal_reviewer` | 8-10 | 15 | ECONRESP-* + POLICY-* 全部归入（7个）+ 财政级算法交叉8个 |

**原因分析：** v4.0 仅有40个旗舰算法，v5.0 扩展到135个（新增95个骨架卡）。业务覆盖面大幅增长（从7条业务线扩展到30+），导致专项Agent的交叉分配显著增加。v5.0 的 Excel "Agent映射"列已由人工设计为工作流提示，忠实地反映了审计实务中的多Agent协同需求。

---

*文档自动生成于 2026-08-06 ｜ 维护者：融策算法工作组 ｜ 校验：registry-agent_map ↔ agent_specs 一致性100%*
