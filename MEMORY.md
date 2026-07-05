# MEMORY.md - 长期记忆（精简版）

> 融策右护卫（OpenClaw AI助手）的长期记忆文件。仅主会话加载。
> 详细技术档案见 `memory/archive/`，项目历史见各项目 `README.md`。

## 核心信息

- **用户**: 融策平头哥 | 四川·成都 | Asia/Shanghai (GMT+8)
- **公司**: 四川融策会计师事务所 / 四川融策工程咨询公司
- **Git Push**: GitHub 直连不通（443超时），需要开代理才能 push。push前提醒平头哥开代理

## 业务范围（12大类）

| # | 业务线 | 简称 | 子类型 |
|:--|------|------|------|
| 1 | 经济责任审计 | 经责 | 任中/离任/自然资源 |
| 2 | 收支审计 | 收支 | |
| 3 | 预算执行审计 | 预算 | |
| 4 | 专项资金审计 | 专项 | 社保/营养餐等 |
| 5 | 往来款清理 | 往来款 | 含资金清理 |
| 6 | 招投标审计 | 招投标 | |
| 7 | 国企审计 | 国企 | |
| 8 | 成本效益审计 | 成本 | |
| 9 | 能源审计 | 能源 | 含碳中和 |
| 10 | 工程竣工决算财务审计 | 工程 | |
| 11 | 预算绩效管理 | 绩效 | 目标设置/事前评估/事中监控/评价 |
| 12 | 政府补贴审计 | 补贴 | |

工程咨询：预算编制 / 财政评审 / 全过程工程咨询 / 工程结算

## 工作区配置

- **模型**: DeepSeek V4 Flash（默认免费）/ V4 Pro（复杂分析手动切）
- ⚠️ **心跳/定时任务必须用 v4-flash**（2026-06-26 用户指令确认），禁止用 V4 Pro/Kimi
- **图片模型**: dashscope/qwen-vl-max（DeepSeek不支持image）
- ⚠️ **DashScope 调用规则**: 任何涉及 qwen-vl-max 的图片/PDF分析，**必须先询问用户确认**，不得自动调用
- **工作区**: D:\openclaw-workspace
- **插件**: 企业微信、微信
- **Python**: 3.14.0a5 / **Node**: v24.14.0
- **draw.io**: D:\dwaw\draw.io\draw.io.exe v30.0.1

## 用户偏好

- 直接高效，不废话 | 关注公司管理和业务发展 | 政府审计需求优先

## 核心高频技能（Top 20）

| 技能 | 用途 |
|------|------|
| perf-audit-checklist | 绩效审计发现逻辑检查清单（事前/事中/事后） |
| audit-report-review | 审计报告AI复核15维检查 |
| audit-jingze | 经责审计四道关 |
| procurement-audit-models | 采购审计/围标串标检测 |
| data-analyst-cn | 数据分析助手 |
| financial-fraud-detection | Benford定律财务造假检测 |
| bid-document | 标书撰写 |
| drawio | 流程图/架构图 |
| deepseek-charting | 零代码画图表 |
| audit-data-analysis-methods | 7大审计分析方法 |
| digital-audit-methodology | 数字化审计10大框架 |
| spatial-audit-analysis | 审计空间分析 |
| audit-knowledge-graph | 审计知识图谱 |
| unstructured-audit-data | 非结构化审计数据 |
| apriori-audit | Apriori关联规则审计 |
| cot-capture | 审计思维链沉淀 |
| prompt-librarian | 提示词资产管理 |
| agent-data-standard | Agent友好数据标准 |
| workflow-embedder | 审计作业流AI嵌入 |
| gov-doc-formatting | 政府公文GB/T9704排版 |
| audit-meeting-review | 望闻问切会议记录诊断 |

> 完整72技能清单见各SKILL.md触发条件

## RAG审计知识库（2026-06-24搭建）

**架构**: TF-IDF + sklearn + DeepSeek API
**数据源**: knowledge/ + obsidian-vault/（1,235个.md文件，13,635个chunk）
**Web界面**: Flask @ `http://localhost:5000`
**API Key**: DeepSeek `sk-dbc61b4ba6a64222a2621d646f15234c`

### 同步方案
- A: 桌面`更新知识库.bat` — 双击一键重建索引
- B: `scripts/rag_watcher.py` — 15秒轮询自动重建
- C: Cron每日凌晨3:00自动重建

### 启动方式
桌面双击`启动RAG知识库.bat` → 浏览器打开 http://localhost:5000

### 核心脚本
| 文件 | 用途 |
|:----|:----|
| `scripts/rag_rebuild.py` | 重建索引（knowledge+obsidian） |
| `scripts/rag_query.py` | CLI问答（含DeepSeek生成） |
| `scripts/rag_server.py` | Flask Web服务（localhost:5000） |
| `scripts/rag_watcher.py` | 文件监控自动重建 |

## 多Agent审计平台（2026-06-21建立）

```
audit-blackboard/
├── orchestrate.py       ← 调度中枢（create/prepare/collect/report）
├── launch.py            ← 一键启动（python launch.py "项目名" --type 简称）
├── agent_specs/         ← 7个Agent规格（含取数规范）
├── schemas/             ← finding_schema.json统一格式
├── playbooks/           ← 按业务线的取数深度指南
├── DATA_SPEC.md         ← 12业务线取数规范
└── projects/            ← 项目工作区
    └── <项目名>/
        ├── raw_data/    ← 原始数据放这里
        ├── findings/    ← 各Agent发现JSON
        ├── collision/   ← 交叉碰撞结果
        └── status.json  ← 进度看板
```

**7 Agent**: data_scout / contract_hound / bid_hunter / law_inspector / workpaper_crafter / report_writer / review_sentinel

**用法**: 你跑 `python launch.py "项目名" --type 简称` → 对我说"开始审计XX" → 我spawn Agent → 你跑 `python orchestrate.py collect` → `python orchestrate.py report`

## 场景-技能-资料三层调用体系

- **第一层**: `SCENARIO-SKILL-MAP.md` — 场景→技能→资料速查表
- **第二层**: `knowledge/INDEX.md` — 资料索引（来源/关键词/摘要）
- **第三层**: 技能SKILL.md触发条件（长期建设）

触发流程：用户需求 → SCENARIO-SKILL-MAP匹配 → 读技能SKILL.md → INDEX.md找资料 → 告知调用了什么

## 串标围标检测体系（摘要）

11层检测体系，技术详情见 `memory/archive/bidding-technical-foundation.md`

| 层级 | 检测维度 | 数据源 | 无需外部数据 |
|:--|:------|:-------|:--:|
| L1 | 报价规律 | 开标一览表 | ✅ |
| L3 | 文本雷同(TF-IDF) | 投标文件.docx | ✅ |
| L4 | 图片哈希 | .docx解压word/media/ | ✅ |
| L5 | 元数据交叉 | core.xml/WPS GUID | ✅ |
| L7 | 打印机型号 | PDF Producer字段 | ✅ |
| L8 | 工商关联 | 天眼查 | ❌ |
| L9 | 保证金资金链 | 银行汇款凭证 | ❌ |
| L2 | 投标IP/MAC | 代理后台日志 | ❌ |
| L11 | 意思联络证据 | 微信/通话/协议 | ❌（司法专用） |

**核心策略**: L3+L4+L5三杀即可定案，不依赖代理机构配合。代理不给IP→见取数函Excel Sheet2的7层破解法。

## 经责审计量化评价（摘要）

v2.0整合模板，详见 `knowledge/references/经济责任审计-融策整合模板v2.0.md`

- 7+1套指标体系（工程项目/行政事业/商业竞争/公益功能/特定功能/金融/科创 + 自定义）
- 6种一票否决 | 四类调整因素 | 5条撰写红线
- Excel: `output/经济责任审计整合模板v2.0.xlsx`

## 审计报告AI复核（摘要）

15维度检查法：10维正文复核 + 5维三方交叉比对。详见 `audit-report-review` 技能
- 致命层（提交前必做）：⑪报告↔附表 ↔ ⑭取证单→报告完整闭环 ↔ ⑮全链路金额追踪
- Output分级: P0重大矛盾 / P1重大遗漏 / P2口径差异 / √通过

## 重要规则

- DeepSeek只支持image_url在最后一条用户消息，历史图片会导致400错误
- 子代理访问不了桌面绝对路径，真实数据放 `projects/<项目>/raw_data/`
- 大Git push（>20MB）需开代理 + 延长超时
- OCR批量任务前确认DeepSeek余额

## 关键教训

- **spawn 必须带 runTimeoutSeconds**，否则子代理跑完后空转耗token。这次OCR任务跑了78分钟（totalTokens 41k）就是因为没设超时

- .doc格式是元数据盲区（WPS存.doc时SummaryInformation为空）
- PDF扫描件比.docx裸露更多信息（扫描仪型号写在Producer字段）
- TF-IDF要去噪（招标模板化承诺函会制造假阳性）
- 元数据清除行为本身即是审计证据
- Windows GBK编码是Python脚本的常驻坑（需 `sys.stdout.reconfigure(encoding='utf-8')`）

---

## 2026-06-24 大事件：审计案例库整理+分类+技能树

### 批量OCR
- 桌面183个PDF（审计观察+经济责任审计）→ PaddleOCR本地识别
- 输出180篇Markdown + 130个Word文档到Obsidian
- OCR引擎: PaddleOCR 2.7.3（conda env paddleocr, Python 3.11.15）

### 内容级分类
- **180篇OCR文章**: AI深度分类 → scene + findings + recommendations + regulations + keywords
- **446篇杂志文章**: 关键词匹配分类 → scene字段写入YAML
- **314篇旧案例库**: 从tags迁移scene字段
- **总计944篇扫描，626篇已分类**（其余为索引文件）

### 台账体系
- `审计资料清单.md`: Obsidian MOC索引页（Dataview兼容）
- `审计资料清单.json`: 944条完整JSON索引
- `scripts/query_catalog.py/bat`: CLI查询工具

### 技能树
- `审计技能树.md`: 14场景×65种审计方法，附325条案例引用
- 用于审计人员查阅和大模型训练

### 关键教训
- PowerShell inline Python的中文引号问题导致不断SyntaxError → 全部改写成独立.py文件
- `审计资料清单.json` 需要 `--rebuild` 参数刷新才能反映YAML变更
- 桌面PDF已被挪走，3个失败文件无法补处理

*最后更新: 2026-06-24 | 详细档案: memory/archive/ | 项目历史: 各项目README*
