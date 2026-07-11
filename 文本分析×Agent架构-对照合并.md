# 文本分析文章 × 融策审计智析Agent v2 — 架构对照合并

> 2026-07-03 | 将「数审派」《文本分析，审计提质增效的硬核工具》的知识体系映射到 v2 架构中
> 原文归档：`文本分析-审计提质增效-原文归档.md`
> 对照源：`融策审计智析Agent-v2-交易Agent架构借鉴.md`、`底稿指南×Agent架构-对照合并.md`

---

## 一、概念映射总表

| 文章概念 | v2 架构对应模块 | 映射关系 | 现有覆盖度 |
|---------|----------------|---------|-----------|
| 五大文本分析场景 | MCP工具层 / 数据分析层Agent | 场景→Agent能力 | ❌ v2未定义文本分析工具 |
| 场景一：TF-IDF热词分析 | 经济责任审计Agent / 审前调查 | Agent预分析能力 | ❌ 未设计 |
| 场景二：Jaccard相似度比对 | 医保/采购审计Agent | 模糊匹配→违规筛查 | ❌ 未设计 |
| 场景三：合同文本拆解 | 工程审计Agent / 合同审计模块 | 正则提取→合规校验 | ❌ 未设计 |
| 场景四：人员画像比对 | 民生资金审计Agent | 身份校验→补贴核查 | ❌ 未设计 |
| 场景五：预算文本合规校验 | 预算执行审计Agent | 规则引擎→文本筛查 | ❌ 未设计 |
| 4步标准化流程 | LangGraph工作流编排 | 流程→节点编排 | 🟡 有框架但未细化 |
| 「机器筛查+人工核验」双轮驱动 | Human-in-the-loop节点 | 已规划 | 🟡 需细化交互协议 |
| 4大实战避坑误区 | Agent设计约束/质量保障 | 误区→反模式约束 | ❌ 未纳入设计 |
| 数据归集+OCR转化 | data_collection节点 | 数据预处理 | 🟡 有节点但缺OCR工具 |
| 规则配置对标风险 | AGR知识库+审计准则专家群 | 规则→知识库检索 | 🟡 需补充文本规则类KB |

**覆盖率：完全覆盖 0/11，部分覆盖 5/11，未覆盖 6/11**

---

## 二、关键洞察

### 与前一篇「底稿编制指南」的定位差异

| 维度 | 底稿编制指南 | 本次文本分析文章 |
|------|------------|----------------|
| 关注层级 | 质量控制层（复核标准） | 工具执行层（分析手段） |
| 核心问题 | 底稿写得对不对 | 问题找不找得到 |
| 技术含量 | 方法论/标准 | 算法/代码/工具 |
| 对Agent的贡献 | 评分引擎+三级复核规范 | 五大工具集+编排流程 |
| 在v2架构的位置 | L1/L2/L3复核层 | 数据分析层+MCP工具层 |

**结论**：两篇文章一纵一横，底稿指南解决"复核质量"，文本分析解决"分析能力"——恰好是v2架构中目前最薄弱的两个层面。

---

## 三、架构增强方案

### 增强 1：新增「文本分析工具集」（MCP工具层）

**现状**：v2 架构中数据分析Agent有角色定义但无具体工具。

**增强方案**：为数据分析层配置5个标准化文本分析工具，以MCP接口封装。

```
工具清单：
┌─────────────────────────────────────────────────────┐
│  MCP 工具名                  对应场景   核心算法      │
├─────────────────────────────────────────────────────┤
│ text_hotword_analysis        场景一     TF-IDF       │
│ text_similarity_compare      场景二     Jaccard      │
│ contract_field_extract       场景三     正则+NER     │
│ personnel_profile_check      场景四     集合运算     │
│ budget_compliance_scan       场景五     关键词+规则  │
└─────────────────────────────────────────────────────┘
```

**工具1：text_hotword_analysis**
```json
{
  "tool": "text_hotword_analysis",
  "input": {
    "documents": ["文本数组或文件路径数组"],
    "doc_type": "meeting_minutes | policy | report",
    "top_n": 20,
    "custom_stopwords": ["可选自定义停用词"],
    "audit_focus": "economic_responsibility | budget | project | subsidy"
  },
  "output": {
    "hotwords": [{"word": "工程外包", "weight": 0.85}, ...],
    "wordcloud_url": "可视化图片URL",
    "suggested_audit_focus": ["测绘费", "资产处置", "补贴发放"]
  }
}
```

**工具2：text_similarity_compare**
```json
{
  "tool": "text_similarity_compare",
  "input": {
    "mode": "global | local",
    "reference_texts": ["标准/合规文本数组"],
    "check_texts": ["待核查文本数组"],
    "threshold": 0.7,
    "audit_type": "medical_insurance | procurement | subsidy"
  },
  "output": {
    "matches": [{
      "ref": "维生素C咀嚼片",
      "check": "维生素C片",
      "similarity": 0.73,
      "risk": "疑似药品名称串换"
    }]
  }
}
```

**工具3：contract_field_extract**
```json
{
  "tool": "contract_field_extract",
  "input": {
    "contract_files": ["合同文件路径数组（PDF/图片/文本）"],
    "extract_fields": ["party", "sign_date", "period", "payment_terms", 
                       "penalty", "amendments", "amount"],
    "cross_check": {
      "payment_records": "财务支付数据路径",
      "project_ledger": "项目台账路径"
    }
  },
  "output": {
    "contracts": [{
      "file": "合同文件名",
      "fields": {"party": "...", "sign_date": "...", ...},
      "risk_flags": [{
        "type": "early_payment",
        "detail": "合同约定验收后付款，实际竣工前已全额支付",
        "severity": "high"
      }]
    }]
  }
}
```

**工具4：personnel_profile_check**
```json
{
  "tool": "personnel_profile_check",
  "input": {
    "applicants": [{"name": "张三", "subsidy_type": "惠农补贴", "year": "2024"}],
    "reference_lists": {
      "finance_staff": "财政供养人员名单路径",
      "deceased": "死亡人员名单路径",
      "supervisor_relatives": "监管对象亲属名单路径"
    },
    "check_rules": ["duplicate_claim", "ineligible_identity", "policy_mismatch"]
  },
  "output": {
    "violations": [{
      "name": "张三",
      "violation_type": "finance_staff_claim",
      "subsidy": "惠农补贴",
      "evidence": "张三出现在财政供养人员名单中"
    }]
  }
}
```

**工具5：budget_compliance_scan**
```json
{
  "tool": "budget_compliance_scan",
  "input": {
    "expense_texts": ["报销备注/凭证文本数组"],
    "rule_set": {
      "keywords": ["超标接待", "私车公养", "礼品采购", "挪用专项资金"],
      "limits": {"差旅费": 800, "办公耗材": 5000},
      "custom_rules": "可选自定义正则规则"
    }
  },
  "output": {
    "violations": [{
      "index": 3,
      "type": "keyword_hit",
      "keyword": "超标接待",
      "original_text": "2024年6月接待费用，超标接待餐饮开支",
      "severity": "high"
    }]
  }
}
```

### 增强 2：数据分析层Agent — 从「角色定义」到「工具分配」

**现状**：v2中定义了5个审计准则专家Agent（国家审计/CPA/内部审计/工程审计/数据审计），但未分配具体工具。

**增强方案**：将五大文本分析工具分配给各Agent，使其具备真实分析能力。

| Agent | 分配工具 | 适用审计项目 | 触发条件 |
|-------|---------|------------|---------|
| 经济责任审计Agent | hotword + contract | 经责审计、离任审计 | 会议纪要/决策文件>50份 |
| CPA审计Agent | similarity + compliance | 财务审计、采购审计 | 报销/采购文本>100条 |
| 内部审计Agent | contract + compliance | 内控审计、合规审计 | 合同/制度文件>30份 |
| 工程审计Agent | contract + hotword | 工程审计、造价审计 | 工程合同/变更单>20份 |
| 数据审计Agent | 全部5个工具 | 大数据审计项目 | 非结构化数据>1000条 |

**Agent系统提示增强**（以经济责任审计Agent为例）：

```
你是经济责任审计专家Agent，具备以下文本分析能力：

1. 会议纪要热词分析：批量读取会议纪要，提取高频决策关键词，
   快速锁定测绘费、工程外包、补贴发放、资产处置等高危审计领域
   
2. 合同文本拆解：自动提取合同八大核心字段，与财务支付数据、
   项目台账交叉比对，识别付款违规、履约超期等疑点

输出要求：
- 每项分析必须输出"目标-过程-结论-索引"四段式
- 热词分析附带可视化词云
- 疑点标注风险等级（高/中/低）和涉及资料编号
```

### 增强 3：4步标准化流程 → LangGraph工作流细化

**原文4步流程**到LangGraph节点的映射：

```
原文流程                    LangGraph节点              增强内容
───────────────────────────────────────────────────────────────
第一步：数据归集统一格式  →  data_collection          + OCR子节点
                                                 + 格式标准化子节点
                                                 + 去重清洗子节点
───────────────────────────────────────────────────────────────
第二步：规则配置对标风险  →  rule_configuration       ← 新增节点
                            (连接AGR知识库)           + 按审计类型加载规则
                                                 + 规则版本管理
───────────────────────────────────────────────────────────────
第三步：批量分析疑点初筛  →  data_analysis            + 5个工具并行调用
                            (现有节点增强)            + 疑点聚合排序
                                                 + 风险等级标注
───────────────────────────────────────────────────────────────
第四步：人机核验固化证据  →  human_review             ← 新增节点
                            (Human-in-the-loop)       + 疑点确认/驳回/修正
                                                 + 证据链组装
                                                 + 反馈回模型（闭环学习）
```

**新增节点定义**：

```python
# 节点1：rule_configuration（规则配置）
def rule_configuration_node(state: AuditState) -> AuditState:
    """
    根据审计项目类型，从AGR知识库检索对应筛查规则
    """
    project_type = state["project_type"]  # 如: economic_responsibility
    
    # 从知识库检索
    rules = kb.search(
        query=f"{project_type} 文本筛查规则 关键词 限额",
        top_k=5
    )
    
    # 组装规则集
    rule_set = {
        "keywords": extract_keywords(rules),
        "limits": extract_limits(rules),
        "patterns": extract_regex_patterns(rules),
        "similarity_threshold": get_threshold(project_type)
    }
    
    state["rule_set"] = rule_set
    state["audit_focus"] = infer_focus_areas(project_type)
    return state

# 节点2：human_review（人机核验）
def human_review_node(state: AuditState) -> AuditState:
    """
    将机器初筛的疑点清单推送人工复核
    """
    findings = state["risk_findings"]  # 机器筛查结果
    
    # 按风险等级排序，高风险优先推送
    high_risk = [f for f in findings if f["severity"] == "high"]
    medium_risk = [f for f in findings if f["severity"] == "medium"]
    
    # 构造人工复核任务
    review_task = {
        "high_risk_items": high_risk,
        "medium_risk_items": medium_risk,
        "total_findings": len(findings),
        "estimated_review_hours": len(high_risk) * 0.5 + len(medium_risk) * 0.25
    }
    
    # 推送人工复核 → 等待反馈
    state["human_review"] = review_task
    state["next"] = "wait_human"  # Checkpoint中断点
    
    return state

# 节点3：feedback_loop（闭环学习）
def feedback_loop_node(state: AuditState) -> AuditState:
    """
    人工复核结果反馈回模型，调整规则参数
    """
    feedback = state["human_feedback"]  # 人工确认/驳回/修正
    
    for item in feedback:
        if item["decision"] == "confirmed":
            # 确认 → 固化为证据
            state["confirmed_evidence"].append(item)
        elif item["decision"] == "rejected":
            # 误报 → 记录误报模式，调整规则
            state["false_positives"].append(item)
            adjust_rules(state["rule_set"], item["pattern"])
        elif item["decision"] == "modified":
            # 修正 → 更新疑点描述
            state["confirmed_evidence"].append(item["modified"])
    
    return state
```

### 增强 4：四大避坑误区 → Agent设计约束

将文章的4个实战误区转化为Agent系统的设计约束和自检规则：

| 原文误区 | 设计约束 | 自检规则 | 触发节点 |
|---------|---------|---------|---------|
| 只看文本不结合业务 | 文本分析结果必须与资金流向/政策/行业规则交叉验证 | 分析结论是否引用了非文本数据源？ | 质疑方Agent |
| 过度依赖机器 | 所有high-risk疑点必须走human_review | human_review完成率是否100%？ | L1复核 |
| 数据归集不完整 | data_collection节点必须输出覆盖率报告 | 应归集资料N份，实归集M份，覆盖率？ | data_collection |
| 通用模型直接套用 | 每个审计项目必须执行rule_configuration | rule_set是否针对当前project_type定制？ | rule_configuration |

**实现为LangGraph条件边**：

```python
# 误区1：交叉验证检查
def check_cross_validation(state):
    """分析结果是否包含非文本数据交叉验证？"""
    for finding in state["risk_findings"]:
        if not finding.get("cross_refs"):
            return "back_to_analysis"  # 退回补充交叉验证
    return "continue"

builder.add_conditional_edges(
    "data_analysis",
    check_cross_validation,
    {
        "back_to_analysis": "data_analysis",  # 重做
        "continue": "debate_engine"
    }
)

# 误区4：规则定制检查
def check_rule_customization(state):
    """规则集是否针对当前项目定制？"""
    if state["rule_set"].get("source") == "default":
        return "rule_configuration"  # 退回定制规则
    return "data_collection"  # 继续

builder.add_conditional_edges(
    "start",
    check_rule_customization,
    {
        "rule_configuration": "rule_configuration",
        "data_collection": "data_collection"
    }
)
```

---

## 四、增强后的 LangGraph 完整工作流

```
                        ┌──────────────┐
                        │    START     │
                        └──────┬───────┘
                               │
                    ┌──────────▼──────────┐
                    │ rule_configuration   │  ← 新增：按项目类型加载规则
                    │ (连接AGR知识库)       │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │  data_collection     │
                    │ + OCR子节点          │  ← 增强：OCR识别+格式标准化
                    │ + 覆盖率报告         │  ← 增强：归集完整性检查
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │   data_analysis      │  ← 增强：5个文本分析工具
                    │ ┌──────────────────┐ │
                    │ │ hotword │similarity│ │
                    │ │ contract│personnel │ │
                    │ │ budget_compliance │ │
                    │ └──────────────────┘ │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │ 交叉验证检查          │  ← 新增：误区1防范
                    │ (文本∩资金∩政策)      │
                    └──────┬──────┬──────┘
                     通过    │    未通过→退回data_analysis
                            │
                    ┌───────▼───────┐
                    │  辩论引擎       │
                    │ trust↔challenge │
                    └───────┬───────┘
                            │
                    ┌───────▼───────┐
                    │  专家群推演     │
                    │ 5准则并行      │
                    └───────┬───────┘
                            │
                    ┌───────▼───────┐
                    │  conclusion    │
                    └───────┬───────┘
                            │
              ┌─────────────┼─────────────┐
              │             │             │
    ┌─────────▼──┐  ┌──────▼──────┐  ┌───▼──────────┐
    │  L1 复核    │  │ human_review │  │ feedback_loop │
    │ +评分引擎   │  │ (人机核验)    │  │ (闭环学习)    │
    │ ≥70分      │  │ ←新增节点    │  │ ←新增节点    │
    └─────────┬──┘  └──────┬──────┘  └───┬──────────┘
              │             │             │
              └─────────────┼─────────────┘
                            │
                    ┌───────▼───────┐
                    │  L2 复核       │
                    │ 关键事项≥80    │
                    └───────┬───────┘
                            │
                    ┌───────▼───────┐
                    │  L3 独立复核   │
                    │ 否决<0.85     │
                    │ +年度对比检测  │
                    └───────┬───────┘
                        ┌───┴───┐
                     ✅通过    ❌退回
                        │        │
                        ▼        ▼
                   report_gen  data_analysis
                              (带修正清单)
```

---

## 五、与前序增强方案的整合评估

### 已有增强（底稿指南篇）

| 增强编号 | 内容 | 状态 | 与本次关系 |
|---------|------|------|-----------|
| 增强1 | L1评分引擎集成 | 未实施 | 互补：评分检查"底稿质量"，文本分析提供"底稿素材" |
| 增强2 | Agent输出结构化 | 未实施 | 互补：结构化输出是文本分析结果的容器 |
| 增强3 | 索引子系统 | 未实施 | 互补：文本分析疑点需要索引到原始资料 |
| 增强4 | 年度对比检测 | 未实施 | 独立，不冲突 |
| 增强5 | 系统提示注入 | 未实施 | 需扩展：本次新增的规则配置也要注入 |

### 本次新增增强

| 增强编号 | 内容 | 预估工时 | 依赖 |
|---------|------|---------|------|
| 增强6 | 五大文本分析工具（MCP封装） | 10天 | 需Python环境（jieba/sklearn） |
| 增强7 | Agent工具分配+系统提示增强 | 2天 | 依赖增强6 |
| 增强8 | rule_configuration + human_review节点 | 5天 | 依赖AGR知识库 |
| 增强9 | 四大避坑设计约束（条件边） | 2天 | 依赖增强8 |

---

## 六、全局实施优先级（合并两篇文章后）

| 优先级 | 增强项 | 来源 | 理由 | 预估工时 |
|--------|--------|------|------|---------|
| **P0** | 增强6：文本分析工具集 | 本文 | 工具是Agent的"手"，没有工具只有角色是空壳 | 10天 |
| **P0** | 增强2：Agent输出结构化 | 底稿篇 | 结构化输出是评分的前提 | 2天 |
| **P0** | 增强1：L1评分引擎 | 底稿篇 | 底稿质量直接可见 | 3天 |
| P1 | 增强7：工具分配+提示增强 | 本文 | 需要工具先就绪 | 2天 |
| P1 | 增强8：规则配置+人机核验节点 | 本文 | 连接工作流的关键链路 | 5天 |
| P1 | 增强5：系统提示注入 | 底稿篇 | 低成本高收益 | 1天 |
| P1 | 增强9：避坑设计约束 | 本文 | 防御性设计 | 2天 |
| P1 | 增强4：年度对比检测 | 底稿篇 | 解决照抄痛点 | 2天 |
| P2 | 增强3：索引子系统 | 底稿篇 | 需完整归档体系 | 5天 |

**关键调整**：文本分析工具集（增强6）从原来的"未覆盖"跃升为**P0最高优先级**——因为它是所有文本类审计分析的执行基础，没有它，数据分析Agent就是空架子。

---

## 七、技术选型建议

基于文章中的代码示例，技术栈建议：

| 组件 | 推荐技术 | 理由 |
|------|---------|------|
| 中文分词 | jieba | 文章使用，生态成熟 |
| TF-IDF | sklearn TfidfVectorizer | 轻量，无需GPU |
| 文本相似度 | Jaccard（轻量）/ 余弦相似度（精准） | 分级使用 |
| 正则提取 | Python re + 审计专用规则库 | 可定制 |
| OCR | 百度OCR / 腾讯OCR / PaddleOCR | 高精度中文 |
| 可视化 | pyecharts / wordcloud | 词云+图表 |
| MCP封装 | Python MCP SDK | 标准化接口 |

---

## 八、与原文逐项验证

| 文章主张 | v2架构回应 | 验证结论 |
|---------|-----------|---------|
| 全量文本筛查替代抽样 | 5工具并行调用+全量数据导入 | ✅ 架构支持 |
| 机器筛查+人工核验双轮驱动 | Human-in-the-loop + feedback_loop | ✅ 已设计 |
| 按项目类型配置规则 | rule_configuration节点 | ✅ 新增覆盖 |
| 不只看文本要结合业务 | 交叉验证条件边 | ✅ 新增覆盖 |
| 数据归集完整性 | data_collection覆盖率报告 | ✅ 新增覆盖 |
| 4步标准化流程 | 4个LangGraph节点一一对应 | ✅ 完全映射 |

**总体结论**：本文提出的五大文本分析场景和4步操作流程，与v2 LangGraph工作流架构天然契合。最大的贡献是为"数据分析层"提供了具体可执行的技术方案——此前该层只有角色定义，缺少实际工具。**增强6（文本分析工具集）应作为下一阶段开发的最高优先级**。
