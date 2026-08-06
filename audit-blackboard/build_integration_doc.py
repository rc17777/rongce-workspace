# -*- coding: utf-8 -*-
"""
build_integration_doc.py — 生成 ALGORITHM_INTEGRATION.md（从 algorithm_registry.json 实时生成，保证矩阵一致）
"""
import sys
import os
import json

sys.stdout.reconfigure(encoding="utf-8")

BASE = os.path.dirname(os.path.abspath(__file__))
REGISTRY = os.path.join(BASE, "algorithm_registry.json")
OUT = os.path.join(BASE, "ALGORITHM_INTEGRATION.md")

AGENT_NAMES = {
    "data_scout": "数据侦察兵", "bid_hunter": "招投标猎手",
    "performance_evaluator": "绩效评价师", "budget_estimator": "预算工程师",
    "settlement_auditor": "结算审计师", "fiscal_reviewer": "财政评审员",
    "contract_hound": "合同猎犬", "law_inspector": "法规检察官",
    "review_sentinel": "复核哨兵", "workpaper_crafter": "底稿工匠",
}

# 算法族 → 简述（用于架构图说明）
FAMILY_DESC = {
    "异常检测": "K-Means/Benford等无监督异常发现",
    "关联分析": "Apriori/FP-Growth/工商关联等关系挖掘",
    "预测模拟": "随机森林/LightGBM/线性回归等监督模型",
    "勾稽核对": "多源数据交叉勾稽、账实核对",
    "规则匹配": "语义相似度规则智能匹配",
    "信号检测": "多信号组合（小金库/差旅费/中间人）",
    "交叉验证": "多源交叉验证（套取资金/保险骗补）",
    "穿透分析": "资金/股权/业务全链路穿透",
    "外部核验": "外部数据核验（工商/材料真实性）",
    "多维复核": "工程决算多维度复核",
    "画像分析": "风险画像与预警",
    "比例分析": "工程支出比例合理性",
    "空间分析": "遥感/地理空间分析",
    "清单对照": "60条/20模式等清单化对照",
    "偏离度检测": "绩效指标偏离度检测",
    "全链路追踪": "转移支付全链路追踪",
    "模式识别": "SQL审计范式模式库",
}

REG = json.load(open(REGISTRY, encoding="utf-8"))
ALGOS = REG["algorithms"]
AGENT_MAP = REG["agent_algorithm_map"]


def agent_cn(agent_id):
    return AGENT_NAMES.get(agent_id, agent_id)


def build_matrix_rows():
    rows = []
    for sn in sorted(ALGOS, key=lambda x: (x.split("-")[0], x)):
        a = ALGOS[sn]
        agents = "、".join(f"{ag}({agent_cn(ag)})" for ag in a["assigned_agents"])
        rows.append(f"| {sn} | {a['name']} | {a['priority']} | {a['family']} | {agents} |")
    return rows


def build_agent_rows():
    rows = []
    for ag in sorted(AGENT_MAP, key=lambda x: -len(AGENT_MAP[x])):
        lst = AGENT_MAP[ag]
        sns = ", ".join(lst)
        rows.append(f"| `{ag}` | {agent_cn(ag)} | {len(lst)} | {sns} |")
    return rows


def main():
    matrix = build_matrix_rows()
    agent_rows = build_agent_rows()
    total_pairs = sum(len(v) for v in AGENT_MAP.values())

    md = f"""# 融策 22Agent 体系 × 政府审计算法资产库（40个）集成说明

> 版本：v1.0 ｜ 生成时间：{os.path.getmtime(REGISTRY) and '由 build_integration_doc.py 自动生成'}
> 注册表：`audit-blackboard/algorithm_registry.json`（40算法 × 40要素）
> 加载器：`audit-blackboard/algorithm_loader.py`
> 来源：《政府审计算法资产库_v4.xlsx》（v1论文13 + v2方法论10 + v3案例库8 + v4杂志9）

---

## 1. 集成架构图

```
┌────────────────────────────────────────────────────────────────────────────┐
│                        融策 22Agent 体系（审计编排层）                          │
│                                                                            │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐            │
│  │ 数据侦察兵   │  │ 招投标猎手   │  │ 绩效评价师   │  │ 预算工程师   │  ...      │
│  │ data_scout │  │ bid_hunter │  │perf_evl    │  │budget_est  │            │
│  │  26个算法   │  │  5个算法    │  │  4个算法    │  │  5个算法    │            │
│  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘            │
└────────┼────────────────┼──────────────┼──────────────┼────────────────────┘
         │                │              │              │
         ▼                ▼              ▼              ▼
┌────────────────────────────────────────────────────────────────────────────┐
│                    algorithm_loader.py（统一加载器）                            │
│  load_registry / get_algorithms_for_agent / get_agent_for_scene /            │
│  get_algorithm_detail / list_algorithms_by_scene / search_algorithms        │
└───────────────────────────────┬────────────────────────────────────────────┘
                                 │
                                 ▼
┌────────────────────────────────────────────────────────────────────────────┐
│              algorithm_registry.json（算法注册表：40算法 × 40要素）              │
│  ┌────────────┬────────────┬────────────┬────────────┬──────────────┐      │
│  │ 异常检测族   │ 关联分析族   │ 预测模拟族   │ 穿透分析族   │ 清单对照族 ...  │      │
│  │ PERF-OUTLIER│BID-PATTERN│ ENG-SAMPLE │FUND-SIPHON│BUD-CHECKLIST │      │
│  │ SUPV-ANOMALY│PROC-RELATED│ HR-RF-001  │CHK-LOSS   │ENV-CHECKLIST │      │
│  │   ...      │  ...       │  ...       │  ...       │  ...         │      │
│  └────────────┴────────────┴────────────┴────────────┴──────────────┘      │
└────────────────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌────────────────────────────────────────────────────────────────────────────┐
│              数据层：序时账/科目余额表/投标文件/工程台账/社保库/遥感影像 ...           │
└────────────────────────────────────────────────────────────────────────────┘
```

**调用链路**：Agent（业务编排）→ loader（统一入口）→ registry（算法要素/元数据）→ 数据层（执行）

---

## 2. Agent ↔ 算法 映射矩阵

### 2.1 按 Agent 聚合（10 个 Agent，共 {total_pairs} 条分配关系）

| Agent ID | 中文名 | 算法数 | 负责算法 |
|:--|:--|:--|:--|
{chr(10).join(agent_rows)}

### 2.2 按算法清单（40 个算法）

| 算法编号 | 算法名称 | 优先级 | 算法族 | 负责 Agent |
|:--|:--|:--|:--|:--|
{chr(10).join(matrix)}

---

## 3. 使用示例（Agent 如何调用算法）

### 3.1 Python 直调（推荐，Agent 工作流内使用）

```python
# 放在 audit-blackboard/ 同目录，或把 audit-blackboard 加入 sys.path
import sys; sys.path.insert(0, r"C:\\Users\\scrccpa\\.openclaw\\workspace\\audit-blackboard")
from algorithm_loader import (
    load_registry, get_algorithms_for_agent, get_agent_for_scene,
    get_algorithm_detail, list_algorithms_by_scene, search_algorithms,
)

# ① 数据侦察兵：查看自己负责的 26 个算法
algos = get_algorithms_for_agent("data_scout")

# ② 拿到算法细节（40要素摘要：审计目标/参数阈值/输入输出/结论边界/退役条件...）
detail = get_algorithm_detail("PERF-OUTLIER-001")
print(detail["name"], detail["priority"], detail["trigger"])
print(detail["card"]["parameters"])          # 参数与阈值
print(detail["card"]["conclusion_boundary"]) # 结论边界（防过度认定）

# ③ 按业务场景找负责 Agent（绩效评价 → performance_evaluator, data_scout）
agents = get_agent_for_scene("绩效评价")

# ④ 按场景列出算法（社保审计 → SOCIAL-MAT-001, FUND-FRAUD-001 ...）
lst = list_algorithms_by_scene("社保审计")

# ⑤ 关键词搜索
hits = search_algorithms("围标")
```

### 3.2 Agent 提示词内嵌（规格文件 `algorithms` 字段）

每个 Agent 规格 JSON 顶层已追加 `algorithms` 字段（示例）：

```json
"algorithms": {{
  "version": "v4.0",
  "registry": "audit-blackboard/algorithm_registry.json",
  "loader": "audit-blackboard/algorithm_loader.py",
  "assigned": ["PERF-OUTLIER-001", "REV-PREDICT-001"],
  "usage": "from algorithm_loader import get_algorithm_detail; algo = get_algorithm_detail('PERF-OUTLIER-001')"
}}
```

Agent 启动时读取自身 `assigned` 列表 → 对每个算法调 `get_algorithm_detail(sn)` 获取
**审计目标 / 计算公式 / 参数阈值 / 输出字段 / 结论边界 / 人工核查程序**，然后按要素执行。

### 3.3 典型编排示例（招投标专项）

```
1. data_scout      → SUPV-ANOMALY-001（Benford 报价异常）→ 输出疑点供应商
2. bid_hunter      → BID-PATTERN-005（Apriori 围标模式）→ 输出投标人频繁项集
3. bid_hunter      → PROC-RELATED-001（关联方13维）→ 工商穿透交叉
4. law_inspector   → RULE-MATCH-001（语义规则匹配）→ 法规定性
5. review_sentinel → CHK-RECON-001（多源勾稽）→ 交叉验证，输出 P0/P1/P2 分级
```

---

## 4. 算法版本管理策略

| 策略 | 说明 |
|:--|:--|
| **单一事实源** | `algorithm_registry.json` 是唯一事实源，由 `build_algorithm_registry.py` 从《政府审计算法资产库_v4.xlsx》自动重建（`python build_algorithm_registry.py`），禁止手工改 JSON |
| **Agent 规格自动同步** | `update_agent_algorithms.py` 根据注册表 `agent_algorithm_map` 批量重写 10 个 Agent 规格的 `algorithms.assigned`（只追加不删除，向后兼容） |
| **版本号** | 注册表 `version` 与算法卡 `版本/编制人/复核人`（当前 v4.0）双轨：资产库升版 → 重建注册表 → 重跑同步脚本 |
| **40要素完整性** | 每个算法卡含 42 个字段（审计目标/风险假设/参数阈值/结论边界/退役条件等），注册表结构化保留 33 个核心要素 + 全量触发器/依赖/输出 |
| **新增算法流程** | ① Excel 增加算法卡 → ② 重建注册表 → ③ 更新 `ASSIGNED_AGENTS` 映射（build 脚本）→ ④ 重跑 update_agent_algorithms.py → ⑤ 更新本文档 |
| **退役/降级** | 按算法卡"算法退役条件"执行（如连续3项目精确率<50%）；退役后在注册表标注 `retired: true`，不删除历史记录 |
| **权限与审计留痕** | 涉及敏感数据（身份证/工资）的算法按卡片"脱敏和权限"执行；算法版本+时间戳写入底稿页脚（模板 WP-ALG-xxx） |

---

## 5. 文件清单

| 文件 | 作用 |
|:--|:--|
| `audit-blackboard/algorithm_registry.json` | 算法注册表（40算法 × 40要素 + Agent映射） |
| `audit-blackboard/algorithm_loader.py` | 统一加载器（6个API） |
| `audit-blackboard/build_algorithm_registry.py` | 注册表重建脚本（读 Excel v4） |
| `audit-blackboard/update_agent_algorithms.py` | Agent 规格同步脚本 |
| `audit-blackboard/agent_specs/*.json` | 18+ 个 Agent 规格（10个已含 `algorithms` 字段） |
"""
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(md)
    print(f"✅ 已生成: {OUT}  ({len(md)} chars)")


if __name__ == "__main__":
    main()
