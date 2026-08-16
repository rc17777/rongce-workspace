# 融策多Agent审计协作系统

## 架构概览

```
                        ┌─────────────────────┐
                        │   🧭 调度中心        │
                        │   (main agent)       │
                        │   识别场景→路由分发   │
                        └──────┬──────────────┘
                               │
        ┌──────────┬───────────┼───────────┬──────────┬──────────┬──────────┬──────────┐
        ▼          ▼           ▼           ▼          ▼          ▼          ▼          ▼
   ┌─────────┐┌─────────┐┌─────────┐┌─────────┐┌─────────┐┌─────────┐┌─────────┐┌─────────┐
   │经责审计 ││预算执行 ││专项资金 ││采购招投标││投资工程 ││两新补贴 ││报告撰写 ││知识管理 │
   │  Agent  ││  Agent  ││  Agent  ││  Agent  ││  Agent  ││  Agent  ││  Agent  ││  Agent  │
   │  pro    ││  flash  ││  flash  ││  pro    ││  pro    ││  flash  ││  flash  ││  flash  │
   └─────────┘└─────────┘└─────────┘└─────────┘└─────────┘└─────────┘└─────────┘└─────────┘
```

## 路由规则

### 规则1：按审计类型关键词路由

| 关键词 | 路由到 | Agent ID |
|--------|--------|----------|
| 经济责任、经责、离任、任期、领导干部、履职 | 经责审计Agent | `audit-econ-resp` |
| 预算执行、预算、决算、三公经费、财政拨款 | 预算执行Agent | `audit-budget` |
| 专项资金、补贴资金、转移支付、项目资金 | 专项资金Agent | `audit-fund` |
| 政府采购、招投标、招标、投标、串标、围标、评标 | 采购招投标Agent | `audit-procurement` |
| 工程、建设、施工、投资、基建、项目竣工 | 投资工程Agent | `audit-investment` |
| 以旧换新、购新补贴、消费补贴、两新 | 两新补贴Agent | `audit-subsidy` |
| 审计报告、报告撰写、审计建议、征求意见 | 报告撰写Agent | `audit-report` |
| 案例入库、知识卡片、政策监控、法规更新 | 知识管理Agent | `audit-knowledge` |

### 规则2：复合场景→多Agent并行

| 场景 | 主Agent | 辅助Agent | 协作方式 |
|------|---------|-----------|---------|
| 专项资金+绩效 | audit-fund | audit-report | fund分析→report写绩效部分 |
| 预算执行+经责 | audit-econ-resp | audit-budget | econ-resp主导,budget提供预算偏离度 |
| 采购+投资 | audit-investment | audit-procurement | investment主导,procurement查招投标环节 |
| 全流程项目 | audit-econ-resp | 全部相关 | 审前knowledge查案例→审中各专业并行→审后report汇总 |

### 规则3：明确调度指令（直接指定Agent）

用户可以直接指定：
- "用经责Agent审一下XX局的离任" → 强制路由到audit-econ-resp
- "让招投标Agent查一下这个项目的围标嫌疑" → 强制路由到audit-procurement
- "报告Agent，把前面的发现汇总成审计报告" → 强制路由到audit-report

### 规则4：不明确的请求→先确认再路由

- "帮我审一下这个单位" → 调度中心追问：什么审计类型？关注哪些方面？
- "这个数据有问题" → 调度中心追问：什么数据？什么项目类型？

---

## Agent清单

### 1. 经济责任审计Agent (`audit-econ-resp`)
- **模型**: deepseek-v4-pro
- **场景**: 离任/任中经责审计
- **核心技能**: eco-responsibility-audit, rongce-gov-audit, rongce-platform, audit-law-check, audit-watchdog, audit-evidence-three-point
- **辅助技能**: docx, xlsx, pdf, word-cn-format, writing-polish
- **核心模型**: M101(出差x考勤), M109(OA IPx出差), M111(凭证制单行为), M006(风险排序)
- **关键能力**: 审前三图（权力/资金/关联）、7环节检查、定责双链、亲属工商索引

### 2. 预算执行审计Agent (`audit-budget`)
- **模型**: deepseek-v4-flash
- **场景**: 部门预算执行审计
- **核心技能**: rongce-gov-audit, rongce-platform, audit-data-analyst, audit-sql-patterns, audit-anomaly-detect, audit-benford
- **辅助技能**: docx, xlsx, word-cn-format
- **核心模型**: M004(预算执行), M101(出差x考勤), M104(报价行为), M105(时间序列), M109(OA IP), M111(凭证制单)
- **关键能力**: 预算偏离度、三公经费、年末突击、科目串户

### 3. 专项资金审计Agent (`audit-fund`)
- **模型**: deepseek-v4-flash
- **场景**: 专项资金/转移支付审计
- **核心技能**: rongce-gov-audit, rongce-platform, audit-data-analyst, audit-sql-patterns, audit-data-quality, two-heavy-audit-checklist, gov-audit-problem-classify
- **辅助技能**: docx, xlsx
- **核心模型**: M102(受益重复), M103(进销存比对)
- **关键能力**: 资金流向追踪、受益对象验证、项目真实性

### 4. 政府采购/招投标审计Agent (`audit-procurement`)
- **模型**: deepseek-v4-pro
- **场景**: 政府采购/招投标专项
- **核心技能**: bid-collusion-audit, rongce-gov-audit, rongce-platform, audit-contract-analyze, audit-data-analyst, pdf-metadata-extractor
- **辅助技能**: docx, xlsx, pdf
- **核心模型**: M104(报价行为), M105(时间序列), M106(街景验证)
- **关键能力**: 9步串标检测、PDF元数据提取、合同三对照、报价规律分析

### 5. 投资/工程审计Agent (`audit-investment`)
- **模型**: deepseek-v4-pro
- **场景**: 政府投资/工程建设项目审计
- **核心技能**: rongce-gov-audit, rongce-platform, audit-data-analyst, audit-contract-analyze
- **辅助技能**: docx, xlsx, pdf
- **核心模型**: M106(街景验证), M107(卫星进度), M108(工程量反推), M113(材料进场x施工日志)
- **关键能力**: 隐蔽工程检测（4层递进）、工程量反推、进度-支付验证

### 6. 两新补贴审计Agent (`audit-subsidy`)
- **模型**: deepseek-v4-flash
- **场景**: 家电以旧换新/数码购新补贴审计
- **核心技能**: rongce-platform, two-new-audit-checklist, audit-pricing-monitor, audit-data-quality
- **辅助技能**: docx, xlsx
- **核心模型**: M102(受益重复), M103(进销存比对)
- **关键能力**: 进销存三向比对、价格备案核查、消费者真实性验证

### 7. 报告撰写Agent (`audit-report`)
- **模型**: deepseek-v4-flash
- **场景**: 审计报告/底稿/方案的文档生成
- **核心技能**: audit-report-writer, audit-report-structured, word-cn-format, writing-polish
- **辅助技能**: docx, xlsx, pptx, pdf, audit-knowledge-card
- **关键能力**: 标准化报告结构、法规自动引用、问题定性格式化、Word中文排版

### 8. 知识管理Agent (`audit-knowledge`)
- **模型**: deepseek-v4-flash
- **场景**: 案例入库、政策监控、知识沉淀
- **核心技能**: audit-knowledge-card, audit-policy-monitor, web-content-fetcher, wechat-article-fetcher, summarize, deep-research
- **辅助技能**: docx, xlsx
- **关键能力**: AuditKB五库维护、案例质量5标准筛选、政策变化监控

---

## 调度中心工作流

```
用户输入
    ↓
┌─────────────────────────────┐
│ 1. 关键词提取               │
│    审计类型？审计对象？数据？ │
├─────────────────────────────┤
│ 2. 场景匹配                 │
│    匹配规则1→确定主Agent    │
│    复合场景→规则2多Agent    │
├─────────────────────────────┤
│ 3. 执行决策                 │
│    简单任务→直接路由         │
│    复杂任务→拆解后并行派发   │
│    不确定→追问用户           │
├─────────────────────────────┤
│ 4. 结果汇总                 │
│    单Agent→直接返回         │
│    多Agent→主Agent汇总整合  │
│    报告需要→调report Agent  │
└─────────────────────────────┘
```

## 使用示例

```
用户: "审一下XX局张三局长的离任经责"
  → 调度中心: 识别"离任经责"→路由到audit-econ-resp
  → 经责Agent: 生成审前三图、13类资料清单、7环节SOP

用户: "XX路市政工程结算有问题，帮我分析"
  → 调度中心: 识别"工程"→路由到audit-investment
  → 投资Agent: 跑M108工程量反推+M113材料进场验证

用户: "这个采购项目怀疑有围标"
  → 调度中心: 识别"采购+围标"→路由到audit-procurement
  → 采购Agent: 跑bid-collusion 9步法+M104报价分析

用户: "把今天的审计发现汇总成报告"
  → 调度中心: 识别"报告"→路由到audit-report
  → 报告Agent: 整合发现、生成标准格式Word

用户: "最近审计署有什么新政策"
  → 调度中心: 识别"政策"→路由到audit-knowledge
  → 知识Agent: 抓取审计署网站最新发文+摘要
```
