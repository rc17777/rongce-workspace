# 知识库自动入库 V2 — 三轮分类 + 辐射迭代 设计文档

> 版本: v1.1 | 日期: 2026-07-11 | 作者: 融策右护卫
> 对标需求: 12条主线为锚点，政策入库后自动辐射扩散，发现新业务领域时自动孵化
> 评审: 经11模型综合研判（opus-4-8终审），P0修复+P1强化已整合

---

## 一、设计原则

1. **12条线是锚，不是边界** — 每条新内容不是"选一个分类"，而是"从12个锚点出发，看它射到哪"
2. **三轮分级，成本递减** — 第一轮规则匹配（零成本）能判定的不交给AI；第二轮AI辐射（低成本flash）；第三轮AI嗅探（中成本pro）只在发现异常模式时触发
3. **新业务孵化需要证据链 + 快速通道** — 默认≥2篇独立来源触发提案（降为2，原3过于保守）。单篇置信度>0.85的强信号走快速通道直接推送人工审视。弱信号（单篇<0.85）进入信号看板积累观察
4. **业务线树带版本** — 每次变更可追溯，知识库索引关联业务线版本号
5. **前两轮宁错勿漏，第三轮宁漏勿错** — Round 1/2 降低阈值多抓关联（审计行业错过新规代价大），Round 3 孵化提案严格把关（避免业务线膨胀）
6. **所有API调用必须有异常处理和降级路径** — 任一轮失败不应阻塞入库流程

---

## 二、核心数据结构

### 2.1 业务线树 (business_lines.yaml)

```yaml
# knowledge/taxonomy/business_lines.yaml
schema_version: "2.0"
tree_version: 14          # 每次增/删/合并业务线 +1
last_updated: "2026-07-11"

# ===== 元数据 =====
llm_config:              # 模型版本固定（P1-2）
    round2_model: "deepseek-v4-flash"
    round2_fallback: "deepseek-v4-pro"
    round3_model: "deepseek-v4-pro"
    round3_fallback: "qwen3.7-plus"
    last_verified: "2026-07-11"

meta_tags:                # 跨业务线主题标签（P0-3）
  - id: MT1
    name: ESG合规
    description: 环境/社会/治理相关，横切多条业务线
    affected_lines: [L1, L7, L9, L11]
  - id: MT2
    name: 数字化转型
    description: 信息化/数据资产/系统审计，横切多条业务线
    affected_lines: [L1, L3, L6, L7, L10]

weak_signals:             # 弱信号看板（P1-1）
  - signal_id: WS-2026001
    proposed_domain: "数据资产审计"
    source_count: 1
    confidence: 0.72
    first_seen: "2026-07-01"
    status: accumulating

# ===== 活跃业务线 =====
nodes:
  - id: L1
    name: 经济责任审计
    status: active         # active | declining | merged | incubated
    parent: null
    created_at: "2025-01-01"
    source_policies:       # 这条业务线的法规依据
      - "《审计法》第二十六条"
      - "2019两办《党政主要领导干部和国有企事业单位主要领导人员经济责任审计规定》"
    sub_types:
      - 任中审计
      - 离任审计
      - 自然资源资产离任审计
    keywords:               # 第一轮规则匹配关键词
      primary: [经济责任, 经责, 领导干部, 任期, 离任, 自然资源资产]
      secondary: [履职, 权力运行, 三重一大, 廉政]
    detection_rules:        # 可选的更复杂匹配条件
      - pattern: "（经济责任|经责）.*审计"
      - pattern: "领导干部.*（任期|离任|任中）"
    radiation_signals:      # 被其他政策辐射到的标记
      - from_policy: "《预算绩效评价管理办法》"
        affected_aspect: "绩效目标完成情况纳入经责评价"

  - id: L2
    name: 收支审计
    status: active
    parent: null
    created_at: "2025-01-01"
    source_policies:
      - "《审计法》第十九条"
    sub_types: []
    keywords:
      primary: [收支审计, 财务收支, 收入支出, 收支两条线]
      secondary: [非税收入, 三公经费, 小金库]
    detection_rules: []
    radiation_signals: []

  - id: L3
    name: 预算执行审计
    status: active
    parent: null
    created_at: "2025-01-01"
    source_policies:
      - "《预算法》"
      - "《审计法》第十七条"
    sub_types: []
    keywords:
      primary: [预算执行, 预算编制, 决算, 部门预算, 预算调整]
      secondary: [结转结余, 超预算支出, 无预算支出, 预算绩效]
    detection_rules:
      - pattern: "预算.*（执行|编制|批复|调整|公开）"
    radiation_signals: []

  - id: L4
    name: 专项资金审计
    status: active
    parent: null
    created_at: "2025-01-01"
    source_policies:
      - "《审计法》第二十三条"
    sub_types:
      - 社保基金审计
      - 营养餐资金审计
      - 乡村振兴资金审计
      - 教育专项资金审计
    keywords:
      primary: [专项资金, 专款专用, 转移支付, 补助资金, 补贴资金]
      secondary: [截留, 挪用, 套取, 滞留, 配套资金]
    detection_rules:
      - pattern: "（专项|补助|补贴|转移支付）.*资金"
    radiation_signals: []

  - id: L5
    name: 往来款清理审计
    status: active
    parent: null
    created_at: "2025-01-01"
    source_policies: []
    sub_types: []
    keywords:
      primary: [往来款, 应收应付, 其他应收, 其他应付, 坏账, 呆账, 资金清理]
      secondary: [挂账, 长期未清, 借款清理, 对账]
    detection_rules: []
    radiation_signals: []

  - id: L6
    name: 招投标审计
    status: active
    parent: null
    created_at: "2025-01-01"
    source_policies:
      - "《招标投标法》"
      - "《政府采购法》"
    sub_types: []
    keywords:
      primary: [招投标, 招标, 投标, 政府采购, 围标, 串标, 评标]
      secondary: [中标, 招标文件, 投标人, 采购方式, 公开招标, 邀请招标]
    detection_rules:
      - pattern: "（招标|投标|评标|中标|政府采购|围标|串标）"
    radiation_signals: []

  - id: L7
    name: 国企审计
    status: active
    parent: null
    created_at: "2025-01-01"
    source_policies:
      - "《审计法》第二十二条"
      - "国资委15号文"
    sub_types: []
    keywords:
      primary: [国有企业, 国企, 国资委, 国有资产, 国有资本]
      secondary: [混合所有制, 国有股权, 出资人, 保值增值]
    detection_rules:
      - pattern: "（国有|国企|国资|国资委）"
    radiation_signals: []

  - id: L8
    name: 成本效益审计
    status: active
    parent: null
    created_at: "2025-01-01"
    source_policies: []
    sub_types: []
    keywords:
      primary: [成本效益, 投入产出, 成本控制, 效益分析, 经济性]
      secondary: [单价分析, 定额, 成本核算, ROI]
    detection_rules: []
    radiation_signals: []

  - id: L9
    name: 能源审计
    status: active
    parent: null
    created_at: "2025-01-01"
    source_policies: []
    sub_types:
      - 碳中和审计
    keywords:
      primary: [能源审计, 节能, 能耗, 碳排放, 碳中和, 碳达峰, 双碳]
      secondary: [能源管理, 节能减排, 绿色]
    detection_rules: []
    radiation_signals: []

  - id: L10
    name: 工程竣工决算财务审计
    status: active
    parent: null
    created_at: "2025-01-01"
    source_policies:
      - "《基本建设财务规则》"
    sub_types: []
    keywords:
      primary: [竣工决算, 工程财务, 基建财务, 工程审计, 建设项目]
      secondary: [待摊投资, 建安工程费, 征地拆迁, 工程款]
    detection_rules:
      - pattern: "（竣工|工程.*财务|基建.*财务|建设项目.*审计）"
    radiation_signals: []

  - id: L11
    name: 预算绩效管理
    status: active
    parent: null
    created_at: "2025-01-01"
    source_policies:
      - "《预算法》第五十七条"
      - "中发〔2018〕34号 全面实施预算绩效管理"
    sub_types:
      - 绩效目标设置
      - 事前绩效评估
      - 事中绩效监控
      - 绩效评价
    keywords:
      primary: [绩效评价, 绩效管理, 绩效目标, 绩效监控, 预算绩效]
      secondary: [指标体系, 绩效指标, 自评, 再评价, 花钱必问效]
    detection_rules:
      - pattern: "（绩效|绩效评价|绩效管理|绩效目标|预算绩效）"
    radiation_signals: []

  - id: L12
    name: 政府补贴审计
    status: active
    parent: null
    created_at: "2025-01-01"
    source_policies: []
    sub_types: []
    keywords:
      primary: [政府补贴, 财政补贴, 补贴资金, 补助资金, 惠企]
      secondary: [申报条件, 补贴发放, 虚报冒领, 重复补贴]
    detection_rules:
      - pattern: "（补贴|补助|奖补|惠企|稳岗）.*（资金|申报|发放）"
    radiation_signals: []

  - id: L13
    name: 监督检查
    status: active         # P1-6: 从绩效评价中独立出来
    parent: null
    created_at: "2026-07-11"
    source_policies:
      - "《财政部门监督办法》"
      - "财监〔2021〕4号"
    sub_types:
      - 财经纪律检查
      - 会计信息质量检查
      - 预决算公开检查
      - 直达资金监控
    keywords:
      primary: [监督检查, 财经纪律, 会计信息质量, 财务检查, 预决算公开]
      secondary: [财政监督, 会计监督, 资金监控, 直达资金, 违规问题]
    detection_rules:
      - pattern: "（监督|检查|监控|核查|督察）.*（财政|财务|会计|资金）"
    radiation_signals: []

  # ===== 孵化中业务线（政策触发自动创建） =====
  # 示例：
  # - id: L13
  #   name: 数据资产审计  # ← 暂定名，待人工确认
  #   status: incubated
  #   parent: L7           # 从国企审计衍生出
  #   created_at: "2026-07-11"
  #   trigger_policies:    # 哪些政策触发了这个孵化
  #     - policy_ref: "《企业数据资源相关会计处理暂行规定》"
  #       trigger_date: "2026-07-11"
  #       confidence: 0.72
  #     - policy_ref: "财政部数据资产入表通知"
  #       trigger_date: "2026-08-15"
  #       confidence: 0.81
  #   confirmation_threshold: 3  # 需要3个独立政策源
  #   confirmed_at: null
  #   keywords:
  #     primary: [数据资产, 数据入表, 数据确权, 数据要素]
  #     secondary: []
```

### 2.2 入库文档元数据 (document metadata)

```yaml
# 每个入库文档的 YAML front matter
---
ingestion_version: "2.0"
ingested_at: "2026-07-11T10:30:00+08:00"
source:
  url: "https://www.mof.gov.cn/..."
  type: government_policy  # government_policy | wechat_article | court_judgment | internal_case | academic_paper | industry_report
  publisher: "财政部"
  publish_date: "2026-07-01"
  title: "关于进一步加强XX资金管理的通知"
  doc_number: "财预〔2026〕XX号"  # 公文号

classification:
  round1:
    method: keyword_match
    direct_hits: [L4, L12]          # 直接命中：专项资金 + 政府补贴
    matched_by: ["专项资金", "补助资金"]
  round2:
    method: llm_radiation
    model: deepseek-v4-flash
    radiation_hits:                 # 辐射命中
      - line: L11                   # 绩效评价
        aspect: "资金使用绩效目标设置和评价标准调整"
        relevance: high
        reason: "新规要求增加XX绩效指标，直接影响绩效评价业务"
      - line: L10                   # 工程竣工决算
        aspect: "涉及XX工程类项目的资金结算口径变化"
        relevance: medium
        reason: "资金管理办法调整了工程类支出归集口径"
      - line: L1                    # 经责审计
        aspect: "领导干部管理该资金的责任边界重新界定"
        relevance: low
        reason: "间接影响：资金管理违规追责标准变更"
  round3:
    method: llm_novelty_detection
    model: deepseek-v4-pro
    novel_domains: []               # 未发现新业务领域
    note: null

tags:
  - 资金管理
  - 专项资金
  - 绩效评价
  - 财政部

summary: |
  财政部发布XX资金管理办法，核心变化是...
  
impact_assessment: |
  对融策业务影响：
  - L4 专项资金审计：XX方面审计重点调整
  - L11 绩效评价：绩效指标体系需更新
  - L10 工程类项目：结算口径有变化（中等影响）
---
```

### 2.3 孵化提案记录

```yaml
# knowledge/taxonomy/incubation_queue.yaml
# 新业务线孵化提案，积累到阈值后推送人工确认

proposals:
  - candidate_id: INC-2026001
    proposed_name: "数据资产审计"
    status: accumulating       # accumulating | threshold_reached | rejected | promoted
    parent_business_line: L7   # 最接近的现有业务线
    trigger_policies:          # 累积的证据
      - policy: "《企业数据资源相关会计处理暂行规定》"
        source_url: "https://..."
        date: "2026-07-01"
        confidence: 0.72       # LLM判定"这是一条新业务方向"的置信度
        excerpt: "企业数据资源符合条件的可确认为无形资产或存货..."
      - policy: "某省财政厅数据资产入表实施方案"
        source_url: "https://..."
        date: "2026-08-15"
        confidence: 0.81
    evidence_count: 2
    threshold: 3               # 需要3条独立来源
    suggested_keywords: [数据资产, 数据入表, 数据确权]
    suggested_sub_types: [数据资产确认审计, 数据资产评估审计]
    target_clients: [国企, 地方政府数据局, 大数据公司]
    created_at: "2026-07-01"
    last_updated: "2026-08-15"
```

---

## 三、三轮分类规则详解

### 3.1 第一轮：规则匹配（Round 1 — Keyword + Pattern Match）

**目标**：零API成本完成80%的分类工作  
**执行时机**：文档入库后立即执行  
**输出**：`direct_hits` 数组（此文档直接命中的业务线ID）

#### 匹配策略（优先级从高到低）

```
Step 1: 精确匹配 detection_rules.pattern（正则）
  → 对每条活跃业务线，依次匹配其 detection_rules 中的所有正则
  → 命中即挂标，不参与后续模糊匹配

Step 2: primary keywords 精确短语匹配
  → 对每条活跃业务线的 primary keywords，使用双数组Trie（AC自动机）
    在文档标题+全文（前5000字）中扫描
  → 任意 primary keyword 命中 → 挂标

Step 3: secondary keywords 加权匹配
  → 对 secondary keywords 做同样扫描
  → 需要 ≥2 个 secondary keywords 同时命中才挂标
  → 单个 secondary 命中被忽略（避免噪声）

Step 4: 公文号前缀推断（政府公文专属）
  → "财预" → L3（预算）/ L11（绩效）
  → "财社" → L4（专项资金-社保）
  → "财建" → L10（工程）
  → "国资产权" → L7（国企）
  → ...（维护一个前缀映射表）
```

#### 规则匹配优先级处理

```
如果 Step 1 命中 → 直接采纳，不再跑 Step 2/3
如果 Step 2 命中 → 直接采纳，不再跑 Step 3
如果 Step 3 命中 → 需 ≥2 条 secondary 命中
如果 Step 4 命中 → 与前面的结果 union（不覆盖，追加）
```

**零命中处理**：第一轮完全没命中的文档不丢弃，全量送入第二轮（既保护现有业务不被漏分，也为新领域发现留入口）。

---

### 3.2 第二轮：LLM 辐射扩散（Round 2 — AI Radiation Analysis）

**目标**：发现间接影响的业务线  
**成本**：flash 模型，~500 tokens/篇  
**执行时机**：Round 1 完成后（所有文档都跑，不限 Round 1 结果）  
**输出**：`radiation_hits` 数组（每条被辐射的业务线 + 影响方面 + 相关性等级）

#### Prompt 设计

```markdown
你是审计业务线影响分析专家。已知融策有以下12条业务线：

{从 business_lines.yaml 动态生成业务线列表，只含 id + name + sub_types}

请阅读以下政策/文章，判断它对每条业务线的影响：

---
{文档全文或前3000字摘要}
---

对**每条**业务线，输出：
- 是否受影响（yes/no）
- 如果是 yes：影响的具体方面（一句话）
- 相关程度：high（直接影响方法/流程/标准）| medium（间接关联）| low（弱关联）
- 影响说明（≤50字）

输出格式（JSON）：
[
  {"line_id": "L1", "affected": true, "aspect": "...", "relevance": "medium", "reason": "..."},
  ...
]

# 判断标准：
- high: 该政策直接修改了这条业务线的审计对象/方法/标准/法律依据
- medium: 该政策涉及的资金/项目/流程间接被这条业务线覆盖
- low: 该政策的某个条款可能被这条业务线的审计工作引用
- 不确定时标 medium
```

#### 后处理（含 P0-1 去重逻辑）

```
1. 过滤 relevance=low 的结果 → 不入库标签，存入 radiation_signals（仅做记录）
2. relevance=high/medium 的 → 写入文档 metadata.round2.radiation_hits
3. 同时反向更新 business_lines.yaml：
   → 在对应节点的 radiation_signals 数组追加本次辐射记录
   → 用于后续"某业务线被辐射N次→需要更新SOP"的自动判断
4. 【P0-1 去重】合并 Round 1 + Round 2 结果：
   → final_lines = list(set(direct_hits) ∪ {r.line for r in radiation_hits if r.relevance in [high, medium]})
   → 保留 provenance 来源标注（Round1/Round2），用于审计追溯
   → 避免同一业务线重复打标污染RAG检索
5. 如果文档 Round 1 零命中 + Round 2 也只有 low → 送入 Round 3
```

---

### 3.3 第三轮：新领域嗅探（Round 3 — Novelty Detection）

**目标**：发现不在当前业务线树中的新服务方向  
**成本**：pro 模型，~1500 tokens/篇（仅在触发条件满足时运行）  
**执行时机**：Round 1+2 均无 high/medium 命中，或 Round 2 标记了异常模式  
**输出**：`novel_domains` 数组 或 更新 `incubation_queue.yaml`

#### 触发条件（满足任一即触发）

```
条件A: Round 1 零命中 AND Round 2 无 high 命中
  → 这篇文档可能是全新领域

条件B: Round 2 中 ≥3 条业务线被标记为 relevance=low
  → 广泛弱关联 = 可能是一个横切所有业务线的新主题

条件C: 文档的 source.type 是 government_policy
  AND 标题包含 [管理办法, 暂行办法, 指导意见, 实施方案, 试点方案]
  → 新政策类型 = 高概率开辟新领域
```

#### Prompt 设计

```markdown
你是审计咨询行业趋势分析师。融策目前有12条业务线：

{当前业务线树}

请分析以下政策/文章，判断它是否揭示了**当前业务线覆盖不到的新服务方向**。

---
{文档全文}
---

输出JSON：
{
  "has_novel_domain": true/false,
  "novel_domains": [
    {
      "proposed_name": "建议的业务线名称（简短，4-8字）",
      "description": "这个新方向解决什么问题（≤100字）",
      "closest_existing_line": "最接近的现有业务线ID（如 L7）",
      "target_clients": "目标客户类型",
      "confidence": 0.0-1.0,
      "reasoning": "判定依据（≤80字）"
    }
  ],
  "cross_cutting_theme": "如果这是一个横切现有业务线的新主题，描述它。否则填 null"
}

# 判断原则：
- 宁漏勿错：confidence < 0.6 时视为 false
- 新领域 = 现有12条线无法直接覆盖的客户需求/政府要求
- "专精特新企业审计""数据资产审计""ESG合规审计"等都是合理的候选
- 不要把"现有业务线的子类型"误判为新领域
  （如"社保基金审计"是 L4 的子类型，不是新领域）
```

#### 后处理（含 P0-3 跨业务线主题 + P0-4 降阈值 + 快速通道）

```
1. has_novel_domain = false → 标记文档为 "分类：待人工" → 结束

2. cross_cutting_theme 非空 → 写入文档 metadata.cross_cutting_theme
   → 同时与 business_lines.yaml 的 meta_tags 比对：
      - 如果是已有主题 → 更新 affected_lines
      - 如果是新主题 → 创建 meta_tag（MT{n}）

3. has_novel_domain = true → 执行以下：
   a. 与 incubation_queue.yaml 现有提案比对：
      - 如果 proposed_name 与现有提案相似度 > 0.7 → 追加证据到现有提案
      - 如果是全新提案 → 创建新孵化提案（status: accumulating）
   b. 检查 evidence_count：
      - evidence_count >= 2 → 状态改为 threshold_reached（P0-4: 降为2）
      - 触发通知："候选业务线《XX》已积累N条独立政策证据，待确认"
   c. 【P0-4 快速通道】单篇 confidence > 0.85 → 直接推送人工审视
      （不等待达到阈值，避免60-180天盲区）
   d. 【P1-1 弱信号】单篇 confidence 0.6-0.85 → 写入 weak_signals 看板
      → source_count 累加，达到2条后自动升级为正式孵化提案
   e. 更新 incubation_queue.yaml
```

---

## 四、入库流程总览

```
┌─────────────────────────────────────────────────────┐
│                    输入：新文档                        │
│         (政策/公众号/判决书/内部案例/行业报告)          │
└──────────────────────┬──────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────┐
│  Step 0: 预处理                                      │
│  - 去重（URL / content hash / 标题相似度 > 0.95）     │
│  - 格式标准化（HTML→MD / PDF→TXT / 图片→OCR）        │
│  - 提取元数据（来源/日期/类型/公文号）                  │
└──────────────────────┬──────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────┐
│  Round 1: 规则匹配 (零成本)                           │
│  - 正则 detection_rules → direct_hits                │
│  - primary keywords AC自动机 → direct_hits           │
│  - secondary keywords 加权 → direct_hits             │
│  - 公文号前缀推断 → direct_hits                       │
│  输出: [L4, L12]                                     │
└──────────────────────┬──────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────┐
│  Round 2: LLM 辐射分析 (flash, ~500t/篇)             │
│  - 对12条线逐条问：受影响？怎么受？程度？              │
│  输出: [{L11: high, L10: medium, L1: low}, ...]     │
│  - relevance=low → 记录但不挂标                       │
│  - relevance=high/medium → 挂 radiation 标签          │
└──────────────────────┬──────────────────────────────┘
                       ▼
              是否触发 Round 3？
        (零命中 | 全是low | 新政策类)
            ┌────────┴────────┐
            ▼ NO              ▼ YES
    ┌──────────────┐  ┌──────────────────────┐
    │ 直接入库      │  │  Round 3: 新领域嗅探   │
    │ 写 metadata   │  │  (pro, ~1500t/篇)     │
    └──────────────┘  │  → 对比孵化队列        │
                      │  → 创建/追加提案        │
                      │  → 达到阈值→通知用户    │
                      └──────────┬─────────────┘
                                 ▼
                      ┌──────────────────────┐
                      │  入库 + 孵化跟踪       │
                      └──────────────────────┘
```

### 4.1 异常处理路径 (P0-2)

```
每轮 API 调用必须有异常处理和降级：

Round 1 (纯本地计算):
  - AC自动机加载失败 → 降级为普通字符串匹配
  - business_lines.yaml 解析失败 → 终止入库，报错

Round 2 (LLM flash):
  - API 超时 (30s) → 重试1次 → 仍失败 → 跳过辐射标记，直接进入 Round 3 判断
  - API 返回非 JSON → 尝试修复格式 → 仍失败 → 标记 "radiation_analysis_failed"
  - 响应为空 → 跳过辐射标记

Round 3 (LLM pro):
  - API 超时 (60s) → 重试1次 → 仍失败 → 标记文档为 "分类：待人工复查"
  - API 返回非 JSON → 尝试修复 → 仍失败 → 同上
  - 响应为空 → 同上

全局:
  - business_lines.yaml 写入中断 → 事务性写入（先写 .tmp，校验通过后 rename）
  - incubation_queue.yaml 并发写入 → 文件锁
  - 磁盘空间不足 → 告警 + 暂停入库

降级级别:
  Level 0: 全部正常 → 完整三轮
  Level 1: Round 2 失败 → 仅 Round 1 结果入库，标记 "partial"
  Level 2: Round 3 失败 → Round 1+2 结果入库，标记 "partial_no_novelty"
  Level 3: 全部失败 → 文档标记为 "pending_review"，不丢弃
```

---

## 五、孵化→确认→升级流程

### 5.1 升级条件

| 条件 | 说明 |
|:--|:--|
| `evidence_count >= 2` (P0-4: 降为2) | 至少2篇独立来源锁定同一方向 |
| 来源多样性 | 不能2篇全是同一公众号；至少2种不同来源类型 |
| 时间窗口 | 最新证据在180天内（防止僵尸提案） |
| **快速通道** | 单篇 confidence > 0.85 直接推送人工审批，不等待第2篇 |
| **弱信号积累** | 单篇 confidence 0.6-0.85 进入弱信号看板，累计2篇后自动升级 |

### 5.2 用户交互

```
[主动推送]
"候选业务线《数据资产审计》已积累3条独立政策证据：
 1. 财政部《企业数据资源会计处理暂行规定》(2026-07-01)
 2. 某省数据资产入表实施方案 (2026-08-15)
 3. 审计署数据审计年度重点通知 (2026-09-01)
→ 建议纳入正式业务线。确认 / 拒绝 / 推迟90天再议？"

[用户操作]
- 确认 → 执行 §5.3 升级流程
- 拒绝 → 标记 rejected，180天内不再提案（除非新政策出现）
- 推迟 → 重置 accumulated_since 时间，90天后再次提示
```

### 5.3 升级执行

```
1. 从 incubation_queue 移除该提案
2. 在 business_lines.yaml 创建新节点:
   - id: L{auto_increment}
   - status: active
   - keywords.primary 从提案建议中取
   - source_policies 从 trigger_policies 取
3. tree_version += 1
4. 回溯更新：所有在孵化期间被标记为"疑似相关"的文档
   → 补充 Round 1/2 分类标签
5. 重建 RAG 索引（新增业务线关键词）
6. 更新 TOOLS.md/MEMORY.md 中的业务线列表
```

---

## 六、数据源与业务线发现路径

系统支持四种输入源，三轮分类共用：

| 数据源 | source_type | 信号权重 | 孵化阈值 | 说明 |
|:--|:--|:--|:--|:--|
| 政府政策 | government_policy | 方向信号 | 2篇政策 | 财政部/审计署/国资委等公文 |
| 微信公众号 | wechat_article | 方向信号 | 2篇 | 审计/咨询行业文章 |
| 裁判文书 | court_judgment | 验证信号 | 2篇 | 审计相关判决 |
| **招标公告** | **tender_announcement** | **市场验证** | **2条** | 🔥 真金白银 > 方向信号 |

### 6.1 招标信息流（第四数据源）

**定位**：不是抓所有招标，而是只抓与融策经营范围匹配的品类，从市场实际采购需求反向发现业务方向。

```
公共资源交易平台（中国政府采购网/省网/市网）
       ↓
 品类过滤：审计服务 | 工程咨询服务 | 会计服务 | 资产评估 | 财务咨询
          绩效评价 | 税务咨询 | 工程造价 | 招标代理 | 法律服务
       ↓
 排除：软件开发 | 系统集成 | 硬件采购 | 物业服务 | 保安保洁...
       ↓
 最低预算过滤：≥5万元
       ↓
 Round 1: 采购内容匹配13条业务线 → 市场机会追踪
 Round 2: 同政策入库辐射分析
 Round 3: 匹配不到的服务需求 → 新领域嗅探
       ↓
 累计≥2条同类型招标 → 直接推送（权重高于政策孵化）
```

**产出**：
- 市场机会追踪：哪个区域/部门在密集采购审计服务？预算在涨还是跌？
- 新业务方向：出现了什么现有业务线覆盖不到的采购需求？
- 竞品情报：谁中标了？中标价？出现了几次？

## 七、文件结构

```
knowledge/taxonomy/
├── business_lines.yaml          # 业务线树（主数据）
├── incubation_queue.yaml        # 孵化提案队列
├── business_lines_history.yaml  # 历史版本记录
│                                # [{version: 13, date: "2026-07-11", changes: [...]}]
├── keyword_ac_trie.pkl          # 序列化的AC自动机（加速Round 1）
├── docnum_prefix_map.yaml       # 公文号前缀→业务线映射
│  财预: [L3, L11]
│  财社: [L4]
│  财建: [L10]
│  国资产权: [L7]
│  ...
└── README.md                    # 本说明

scripts/ingestion/
├── ingestion_v2.py              # 入库主脚本
├── ingestion_round1.py          # Round 1: 规则匹配模块（已支持tender_announcement）
├── ingestion_round2.py          # Round 2: LLM辐射分析模块
├── ingestion_round3.py          # Round 3: 新领域嗅探模块
├── taxonomy_manager.py          # 业务线树管理
└── tender_scraper.py            # 招标信息采集（待开发）
```

---

## 八、成本估算

| 操作 | 模型 | 单篇消耗 | 频率 | 月成本 |
|:--|:--|:--|:--|:--|
| Round 1 规则匹配 | 无 | 0 | 每篇 | ¥0 |
| Round 2 辐射分析 | v4-flash | ~500t | 每篇 | ~¥0（免费） |
| Round 3 新领域嗅探 | v4-pro | ~1500t | 约20%的文档 | ~¥1/月 |
| 孵化提案汇总 | v4-flash | ~800t | 仅在提案变更时 | ~¥0 |
| **合计** | | | | **< ¥5/月** |

---

## 九、实施计划

| 阶段 | 内容 | 预计 |
|:--|:--|--:|
| Phase 1 | 完成 `business_lines.yaml` 数据填充 + AC自动机 + 公文号映射表 | 2天 |
| Phase 2 | 实现 Round 1 规则匹配脚本 + 单元测试 | 1天 |
| Phase 3 | 实现 Round 2 LLM辐射分析脚本 + Prompt调优 | 2天 |
| Phase 4 | 实现 Round 3 新领域嗅探 + 孵化队列管理 | 2天 |
| Phase 5 | 集成主脚本 + 端到端测试 | 1天 |
| Phase 6 | 回填历史文档（可选：对已有文档重跑分类） | 1天 |

---

*本文档为设计稿。实施时将根据实际情况调整阈值和Prompt。*
