# SCENARIO-SKILL-MAP.md — 审计场景→技能→资料速查

> 每次会话启动时读取。触发规则：用户提到场景关键词 → 自动匹配对应技能+资料。
> 最后更新: 2026-06-21

---

## 使用方式

1. 用户描述需求 → 在本表查找匹配场景
2. 读取对应技能的 SKILL.md（如从未用过）
3. 读取对应资料的 INDEX 条目 → 命中后读取原文
4. 如用户说"查杂志"/"查案例" → 额外激活 `magazine-knowledge-bridge`
5. 告知用户"我调用了 X 技能，引用了 Y 资料 + Z 杂志案例"

---

## 一、按审计业务类型（12大类）

### 1. 经济责任审计
**触发词**: 经责审计、任中审计、离任审计、自然资源经济责任、领导干部审计
**技能**:
| 优先级 | 技能 | 用途 |
|:--:|------|------|
| 🔴 | `audit-jingze` | 经责审计四道关：立项/招投标/阴阳合同/控制价 |
| 🔴 | `audit-meeting-review` | 望闻问切阅记法：会议记录四步诊断 |
| 🔴 | `cot-capture` | 沉淀经责审计专家思维链 |
| 🟡 | `gov-audit-methodology` | 框架六「经济责任审计量化评价五维模型」 |
| 🟡 | `audit-text-mining` | 会议纪要/工作报告批量文本挖掘 |
| 🟢 | `audit-knowledge-graph` | 股权穿透/关联关系发现 |

**资料**:
- `knowledge/大型经责审计系列干货第1篇-一苇思-20260609.md`
- `knowledge/国资委2026-15号文-鹏盛所-中国注册会计师俱乐部20260327.md`
- `knowledge/串通投标罪证据认定-政策荟萃一点通20260603.md`
- `knowledge/references/经济责任审计全套量化评价指标-芮听柠说.md`

---

### 2. 收支审计
**触发词**: 收支审计、收支两条线、非税收入、财政收支
**技能**:
| 优先级 | 技能 | 用途 |
|:--:|------|------|
| 🔴 | `data-analyst-cn` | 收支数据摸底统计 |
| 🔴 | `audit-data-analysis-methods` | 7大分析方法（趋势/对比/异常） |
| 🟡 | `financial-fraud-detection` | Benford定律检测收入造假 |
| 🟡 | `forecast-simulation` | 收支趋势预测/缺口分析 |

**资料**: `knowledge/policies/`

---

### 3. 部门预算执行情况审计
**触发词**: 预算执行、部门预算、预算执行率、预算编制
**技能**:
| 优先级 | 技能 | 用途 |
|:--:|------|------|
| 🔴 | `data-analyst-cn` | 预算执行率统计/差异分析 |
| 🔴 | `bid-document` | 附录「审计SQL模型速查表」→ 预算执行审计SQL |
| 🟡 | `analysis-report` | 预算执行分析报告 |
| 🟢 | `forecast-simulation` | 年底预算执行预测 |

**资料**: 无专属资料，SQL模型内置于 bid-document 技能

---

### 4. 政府资金专项审计
**触发词**: 专项资金、社保资金、营养餐、补贴审计、资金拨付
**技能**:
| 优先级 | 技能 | 用途 |
|:--:|------|------|
| 🔴 | `data-analyst-cn` | 资金拨付/使用/结余全链路分析 |
| 🔴 | `audit-data-analysis-methods` | 时间序列/异常检测 |
| 🟡 | `spatial-audit-analysis` | 受益对象地理分布合理性 |
| 🟡 | `audit-text-mining` | 政策文件+验收报告批量检索 |
| 🟡 | `apriori-audit` | 频繁结队→发现骗补团伙 |
| 🟢 | `audit-knowledge-graph` | 受益人关联关系网络 |

**资料**:
- `knowledge/专项债专题-数据化审计/`
- `knowledge/references/专项债审计与投融资项目审查-数据化审计.md`

---

### 5. 往来款清理（含资金清理）
**触发词**: 往来款、应收账款、应付账款、资金清理、长期挂账
**技能**:
| 优先级 | 技能 | 用途 |
|:--:|------|------|
| 🔴 | `data-analyst-cn` | 往来款账龄分析/余额统计 |
| 🔴 | `financial-fraud-detection` | 异常挂账/Benford检测 |
| 🟡 | `gov-audit-methodology` | 往来款清理标准流程 |

**资料**: 无专属资料

---

### 6. 招投标审计
**触发词**: 招投标、围标、串标、中标、投标异常、评标
**技能**:
| 优先级 | 技能 | 用途 |
|:--:|------|------|
| 🔴 | `procurement-audit-models` | 11层围标串标检测体系（L1-L11） |
| 🔴 | `bid-document` | 招标文件解读/标书撰写 |
| 🟡 | `unstructured-audit-data` | 批量解压标书/Word关键词扫描/TF-IDF相似度 |
| 🟡 | `tender-analyzer-agent` | 标书智能分析助手（投标须知/评标办法/风险识别） |
| 🟡 | `apriori-audit` | 频繁结队→围标团伙识别 |
| 🟡 | `audit-knowledge-graph` | 投标人→法人→股东多跳关系 |
| 🟢 | `image-classifier-audit` | 标书印章/资质证书自动归类 |
| 🟢 | `spatial-audit-analysis` | 供应商地址聚类→围标线索 |

**资料**:
- `knowledge/串通投标罪证据认定-政策荟萃一点通20260603.md`
- `knowledge/references/围标历史数据分析-数据化审计局.md`
- `knowledge/references/TF-IDF查处围标串标-数据化审计局实操.md`
- `knowledge/references/招投标审计-政府采购围标串标-审计太原法规科.md`
- `knowledge/references/政府采购投诉违法违规典型案例-企业反舞弊合规研究院.md`

---

### 7. 国企专项审计
**触发词**: 国企审计、国有企业、国资监管、三重一大
**技能**:
| 优先级 | 技能 | 用途 |
|:--:|------|------|
| 🔴 | `audit-jingze` | 控制价/阴阳合同审查 |
| 🟡 | `financial-fraud-detection` | 财务造假检测 |
| 🟡 | `audit-knowledge-graph` | 关联交易/股权穿透 |
| 🟡 | `first-principles-audit` | 国企审计任务分解→自动化策略 |
| 🟢 | `digital-audit-methodology` | 数字化审计框架 |

**资料**:
- `knowledge/国资委2026-15号文-鹏盛所-中国注册会计师俱乐部20260327.md`
- `knowledge/references/穿透式监管合规框架-国资委笔记.md`
- `knowledge/references/国企审计常用法规制度文件清单-幸福德昌所.md`

---

### 8. 成本效益审计
**触发词**: 成本效益、性价比、投入产出、效益分析
**技能**:
| 优先级 | 技能 | 用途 |
|:--:|------|------|
| 🔴 | `data-analyst-cn` | 成本/效益数据统计 |
| 🟡 | `forecast-simulation` | 成本效益预测/敏感性分析 |
| 🟡 | `hv-analysis` | 横向行业对标+纵向趋势分析 |

**资料**: `knowledge/references/造价成本监管合规指引-中国价格协会2026.md`

---

### 9. 能源审计（含碳中和）
**触发词**: 能源审计、碳中和、碳排放、节能
**技能**:
| 优先级 | 技能 | 用途 |
|:--:|------|------|
| 🟡 | `data-analyst-cn` | 能耗数据统计分析 |
| 🟡 | `forecast-simulation` | 碳排放趋势预测 |

**资料**: 无专属资料（业务开展较少）

---

### 10. 工程竣工决算财务审计
**触发词**: 竣工决算、工程决算、竣工财务、工程结算
**技能**:
| 优先级 | 技能 | 用途 |
|:--:|------|------|
| 🔴 | `data-analyst-cn` | 决算数据与预算/合同对比 |
| 🔴 | `audit-jingze` | 控制价合理性审查 |
| 🟡 | `gov-audit-methodology` | 工程审计标准流程 |
| 🟡 | `image-classifier-audit` | 工程现场照片分类（施工/质量/验收） |

**资料**: `knowledge/references/工程签证常见问题及审计对策.md`

---

### 11. 预算绩效管理
**触发词**: 绩效评价、绩效目标、事前评估、事中监控、绩效指标
**技能**:
| 优先级 | 技能 | 用途 |
|:--:|------|------|
| 🔴 | `data-analyst-cn` | 绩效指标量化统计 |
| 🔴 | `gov-audit-methodology` | 框架六「经济责任审计量化评价五维模型」 |
| 🔴 | `analysis-report` | 绩效评价报告生成 |
| 🟡 | `digital-audit-methodology` | 绩效数据采集与分析框架 |
| 🟢 | `spatial-audit-analysis` | 政策覆盖区域空间分析 |

**资料**:
- `knowledge/references/经济责任审计全套量化评价指标-芮听柠说.md`

---

### 12. 政府补贴审计
**触发词**: 补贴审计、补贴资金、骗取补贴、财政补贴
**技能**:
| 优先级 | 技能 | 用途 |
|:--:|------|------|
| 🔴 | `data-analyst-cn` | 补贴发放/领取数据摸底 |
| 🔴 | `financial-fraud-detection` | Benford+异常模式检测 |
| 🟡 | `apriori-audit` | 频繁结队→骗补团伙 |
| 🟡 | `spatial-audit-analysis` | 受益对象分布异常 |
| 🟡 | `audit-knowledge-graph` | 受益人关联关系 |
| 🟢 | `audit-text-mining` | 申报材料关键词批量检索 |

**资料**: `knowledge/references/骗取补贴识别分析-潍坊审计局.md`

---

## 二、按通用审计工作流

### 📋 审计准备阶段
| 场景 | 技能 | 资料 |
|------|------|------|
| 理解政策文件 | `gov-audit-methodology` | `knowledge/policies/` |
| 制定实施方案 | `first-principles-audit`（任务分解） | — |
| 文档快速摸底 | `audit-text-mining`（词云+关键词定位） | — |
| 行业背景调研 | `web_search` + `tavily` | — |
| 头脑风暴 | `brainstorming` | — |
| 图片批量分类 | `image-classifier-audit` | — |

### 🔍 审计实施阶段
| 场景 | 技能 | 资料 |
|------|------|------|
| 数据清洗 | `data-analyst-cn` | — |
| 异常检测 | `financial-fraud-detection` + `aloudata-anomaly-detection` | `knowledge/audit-models/` |
| 关联分析 | `apriori-audit` + `audit-knowledge-graph` | — |
| 空间分析 | `spatial-audit-analysis` | — |
| 散点分析 | `hv-analysis`（横纵对标法） | — |
| 围标串标 | `procurement-audit-models`（11层） | 见招投标审计 |
| 文档雷同检测 | `unstructured-audit-data`（TF-IDF/Simhash） | — |
| 元数据提取 | `unstructured-audit-data`（docx/PDF元数据） | — |
| 预测推演 | `forecast-simulation` | — |
| 会议记录审查 | `audit-meeting-review`（望闻问切） | — |
| 监管指定应对 | `regulatory-audit-response`（接审报） | — |
| 经责四道关 | `audit-jingze` | — |
| 图片检索 | `image-classifier-audit` | — |

### 📝 审计报告阶段
| 场景 | 技能 | 资料 |
|------|------|------|
| 报告撰写 | `analysis-report` + `gov-doc-formatting` | — |
| 报告复核 | `audit-report-review`（15维度） | `knowledge/cross-document-auditor-开源项目-20260611.md` |
| 文字润色 | `copy-editing` + `humanizer` | — |
| 去AI味 | `humanizer` | — |
| 标书撰写 | `bid-document` | — |
| 公众号文章 | `khazix-writer` | — |
| 营销文案 | `copywriting` | — |
| 公文排版 | `gov-doc-formatting`（GB/T9704） | — |

### 📊 可视化产出
| 场景 | 技能 | 资料 |
|------|------|------|
| 流程图/架构图 | `drawio`（可编辑矢量图） | — |
| 终端快速出图 | `arch-diagrammer`（SVG/PNG） | — |
| Mermaid/ECharts | `deepseek-charting` | — |
| PPT（融策定制） | `rongce-ppt`（受众蒸馏+导演规划+三审检查） | — |
| HTML演示文稿 | `html-ppt`（36主题/15模板/27动画） | — |
| 审计插画卡片 | `audit-card-generator`（Napkin风） | — |
| 图片生成/编辑 | `nano-banana-pro`（Gemini图像API） | — |
| 文档插图分析 | `illustration-analysis` | — |

### 🔄 知识管理
| 场景 | 技能 | 资料 |
|------|------|------|
| 沉淀思维链 | `cot-capture`（3模式/5阶段访谈） | `knowledge/cot-dataset/` |
| Prompt入库管理 | `prompt-librarian`（全生命周期） | — |
| 数据标准检查 | `agent-data-standard`（12项检查） | — |
| 流程嵌入设计 | `workflow-embedder`（6种嵌入模式） | — |
| 资料归档Wiki | `wiki-auto-ingest`（LLM Wiki方法论） | — |
| 记笔记 | `note` | — |
| 知识库索引 | `knowledge/INDEX.md` | — |

### 📋 方案编制 & 报告写作（杂志案例即时调取）

> **触发规则**：说"进场方案"/"投标方案"/"写报告" + 业务关键词，自动调取对应杂志案例+审计思路

| 工作场景 | 触发词示例 | 自动调取 |
|---------|-----------|---------|
| **进场方案** | "写进场方案 高标准农田" | 匹配业务场景 → 杂志方法论 + 核心审计逻辑 |
| **投标方案** | "投标方案 经责审计" | 匹配业务场景 → 案例支撑 + 审计思路 + 技术方法 |
| **审计报告** | "写报告 预算执行违规" | 匹配问题类型 → 类似案例处理方式 + 法规依据 |
| **实施方案** | "编制实施方案 专项债" | 匹配业务场景 → 审计重点 + 检查步骤 + 常见问题 |
| **技术标** | "技术标 招投标审计" | 匹配业务场景 → 审计方法体系 + 案例目录 |

**资料调用优先级**：
1. `skills/magazine-knowledge/` 精华文件（12篇，含方法论+案例摘要）
2. `knowledge/数据化审计/` 系列（71篇，数字化审计方法）
3. `knowledge/references/` 参考文章（38篇，专项深度）
4. 如用户说"查杂志原文"，走 `magazine-knowledge-bridge` 检索 Obsidian 原文

**示例回复格式**：
```
用户在写 [进场方案/投标方案/报告] 关于 [业务场景]

📋 匹配到：[场景名称]
📚 调取杂志案例：X篇
🔧 审计方法：方法A、方法B、方法C
📖 核心审计逻辑：
  1. ...
  2. ...
  3. ...
⚠️ 常见问题/风险点：...
💡 可复用模式：...
```

### 📄 文档处理
| 场景 | 技能 | 资料 |
|------|------|------|
| PDF处理 | `pdf` | — |
| 格式转换→MD | `markdown-converter`（markitdown） | — |
| Word/DOCX | `officecli-docx` | — |
| Excel/XLSX | `officecli-xlsx` | — |
| PPT/PPTX | `officecli-pptx` | — |
| 语音转文字 | `openai-whisper` | — |
| 视频帧提取 | `video-frames` | — |

### 🤖 智能体/自动化
| 场景 | 技能 | 资料 |
|------|------|------|
| 标书智能分析 | `tender-analyzer-agent` | — |
| 定时报告 | `scheduled-report`（编排层：录制→打包→调度） | — |
| 新闻监控 | `news-aggregator` | — |
| 自我改进 | `xiucheng-self-improving-agent` | — |

---

## 三、技能速查表（按使用频率）

### 🔴 高频核心（每次审计都可能用）
```
data-analyst-cn          — 数据摸底统计
audit-data-analysis-methods — 7大分析方法
financial-fraud-detection   — Benford+异常检测
procurement-audit-models    — 11层围标串标检测
drawio                      — 流程图/架构图
audit-report-review         — 15维度报告复核
copy-editing                — 文字润色校对
```

### 🟡 中频场景（特定项目类型触发）
```
audit-jingze              — 经责审计四道关
audit-meeting-review      — 会议记录望闻问切
regulatory-audit-response — 监管指定审计接审报
gov-audit-methodology     — 政府审计方法论
digital-audit-methodology — 数字化审计方法论
bid-document              — 标书撰写（含SQL模型速查表）
audit-text-mining         — 文本挖掘（词云/关键词定位）
unstructured-audit-data   — 非结构化数据批处理
apriori-audit             — Apriori关联规则
spatial-audit-analysis    — QGIS空间分析
forecast-simulation       — 预测推演
analysis-report           — 分析报告编排
gov-doc-formatting        — 公文批量排版（GB/T9704）
rongce-ppt                — 融策PPT全流程
image-classifier-audit    — 图片离线分类
```

### 🟢 低频/通用工具（偶尔用）
```
audit-knowledge-graph     — Neo4j知识图谱（需安装Neo4j）
audit-card-generator      — Napkin风插画卡片
aloudata-anomaly-detection — Aloudata异常检测
first-principles-audit    — 第一性原理任务分解
tender-analyzer-agent     — 标书智能分析助手
html-ppt                  — HTML演示文稿
nano-banana-pro           — AI图片生成
video-creator             — 短视频生成
video-frames              — 视频帧提取
scheduled-report          — 定时任务编排
news-aggregator           — 新闻聚合
sql-dataviz / sql-master / sql-report-generator — SQL三件套
```

### ⚪ 知识管理/流程类（不直接产出，养系统）
```
cot-capture               — 思维链沉淀
prompt-librarian          — Prompt资产管理
agent-data-standard       — 数据标准检查
workflow-embedder         — 流程嵌入分析
wiki-auto-ingest          — Wiki自动摄入
note                      — 笔记系统
```

### ⚫ 几乎不用（可考虑清理）
```
disk-cleaner              — 磁盘清理（跟审计无关）
browser-act / browser-act-skill-forge / agent-browser-stagehand — 浏览器操作
openclaw-find-skills / skill-vetter — 技能发现/审查
github                    — GitHub操作
humanizer                 — 去AI味（copy-editing覆盖）
markdown-converter        — 格式转换（pdf技能覆盖）
openai-whisper            — 语音转文字（无实际场景）
tavily                    — 搜索（web_search内置工具覆盖）
memory-setup              — 记忆设置（一次性）
proactive-agent           — 主动性代理（HEARTBEAT覆盖）
xiucheng-self-improving-agent — 自我改进（太meta）
```

---

## 四、触发规则优先级

1. **精确匹配**：用户说"经责审计" → 直接匹配业务类型 1
2. **关键词匹配**：用户说"帮我看看这个投标有没有围标" → 匹配业务类型 6 + 关键词"围标" → 触发 procurement-audit-models
3. **工作流推断**：用户上传一堆 Word → 可能是审计准备阶段 → 推荐 audit-text-mining
4. **兜底**：无法匹配时，列出 TOP 10 常用技能让用户选

---

> 维护规则：每次新建技能或新增资料后，更新此文件对应条目。

---

## 五、杂志资料速查（magazine-knowledge）

> 来源：《中国审计》《审计案例》2024-2026 | 原始资料：Obsidian 杂志资料库（447PDF+1003MD）
> 精华提取版已同步到 `skills/magazine-knowledge/`（12篇）
> 检索桥：`magazine-knowledge-bridge` — 说"查杂志"或"查案例"自动检索 Obsidian 原文

### 按业务类型匹配

| 业务类型 | 杂志精华文件 | 行数 | 核心内容 |
|---------|-------------|:--:|------|
| 经济责任审计 | `econ-responsibility-methods-v2.md` | 591 | 审计事项清单管控/物业费收缴/车轮腐败SQL/政府采购Python |
| 收支/财政审计 | `fiscal-audit-logic.md` + `fiscal-batch3-methods.md` + `financial-audit-methods-v2.md` | 1,357 | 专项债/以旧换新/政府采购/公务支出/投资基金违规模式 |
| 招投标审计 | `bidding-batch4-methods.md` | 871 | 产权交易拍卖/围标新手法/跨年投标比对/招商引资合规/国企降本 |
| 国企专项审计 | `enterprise-audit-methods-v2.md` | 633 | 国企经营/混改/三重一大/薪酬管理审计方法 |
| 工程竣工决算 | `engineering-audit-logic.md` | 300 | 工程造价/征地拆迁/基建审计逻辑 |
| 预算绩效管理 | `perf-eval-logic.md` | 378 | 绩效目标/评价指标/结果应用 |
| 政府补贴/专项资金 | `livelihood-audit-methods.md` + `agriculture-audit-methods.md` + `investment-audit-methods-v2.md` | 1,215 | 涉农补贴/教育/医疗/食品安全/殡葬/养老/保障房/投资审计 |
| 能源/自然资源 | `resource-env-methods-v2.md` | 321 | 自然资源资产/碳排放/生态环境审计 |

### 一键触发方式

用户说以下任意触发词时，自动激活杂志检索：

| 触发词 | 行为 |
|--------|------|
| **"查杂志"** / **"查案例"** / **"杂志资料"** | → 先读 `magazine-knowledge-bridge` SKILL.md → 按场景匹配精华文件 |
| **"杂志案例"** + 业务关键词（如"高标准农田"） | → 直接检索对应 magazine-knowledge 文件 |
| **"千份杂志"** / **"Obsidian资料"** | → 走 bridge 检索 Obsidian 原文（需那台机器开机） |

---

## 六、数据化审计系列（knowledge/数据化审计/ 63篇）

> 来源：「数据化审计」公众号（小叶，SmartAudit）
> 已归档 63/85 篇，覆盖数字化审计全链路

### 主题分布

| 编号范围 | 主题 | 篇数 |
|---------|------|:--:|
| #1-7 | 数字化审计基础认知 | 7 |
| #8-17 | 技术方法（Neo4j/图分析/招投标异常/模型风险/空间技术） | 10 |
| #18-22 | 实践与工具（Python离线安装/应用价值/对公分析） | 5 |
| #34 | 前沿科技案例 | 1 |
| #49-85 | 数字化审计深度系列（含QGIS空间分析/计算机视觉/知识图谱） | 37 |
| 专题 | 人工智能+审计（含玉石专题） | 3 |

### 触发词
"数字化审计" / "数据化审计" / "数据分析方法" / "QGIS" / "Neo4j" / "Python审计"
