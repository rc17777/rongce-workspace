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

## 🏛️ 总书记审计语录（随时引用）

> 写报告/方案/投标/宣传册时，按场景摘取。完整手册见 `knowledge/references/总书记审计工作重要指示批示-引用手册.md`

### 定位（报告开篇/公司介绍）
- "审计是党和国家监督体系的重要组成部分。"（2018.5，中央审计委一次会议）
- "构建**集中统一、全面覆盖、权威高效**的审计监督体系。"（2018.5 / 2025.1 重申）
- "以高质量审计监督护航经济社会高质量发展。"（2025.1，最新指示）

### 三个立（质量承诺/团队）
- "以**审计精神立身**，以**创新规范立业**，以**自身建设立信**。"（2018.5）

### 三个如（方案总论）
- "**如臂使指**——指哪儿打哪儿，打哪儿成哪儿。"
- "**如影随形**——让审计对象感到审计像影子一样时时在身边。"
- "**如雷贯耳**——让审计监督顺畅实施、审计成果高效运用。"（2023.5，《求是》2023/21）

### 六个聚焦（审计重点）
1. 高质量发展·重大项目重大战略重大举措
2. 稳增长稳就业稳物价·财政资金
3. 实体经济·金融支持/助企纾困
4. 兜牢民生底线·群众最关心利益
5. **统筹发展和安全·地方债/金融/房地产/粮食/能源** ← 专项债审计引用
6. **权力规范运行·反腐治乱** ← 经责审计引用

### 科技强审（技术方案/AI审计）
- "要坚持**科技强审**，加强审计信息化建设。"（2018.5）
- "深化改革创新……不断提高审计监督质效。"（2025.1）

### 审计整改（报告建议段）
- "审计整改'**下半篇文章**'与审计揭示问题'上半篇文章'同样重要，必须一体推进。"（2023.5）

### 队伍建设（宣传册/投标）
- "打造经济监督的'**特种部队**'。"（2023.5）
- "**有问题没发现是失职、发现问题不报告是渎职**"（2023.5）
- "审计的'尚方宝剑'是党中央授予的。"（2023.5）

### 常用组合拳
| 场景 | 推荐引用 |
|:--|:--|
| 报告开篇 | 审计监督体系 + 三个如 |
| 审计重点 | 六个聚焦（选1-2条对口的）|
| 方案总论 | 三个如 + 科技强审 |
| 整改建议 | 上下半篇文章 |
| 技术方案 | 科技强审 + 研究型审计 |
| 公司介绍 | 三个立 + 特种部队 + 护航 |
| 质量承诺 | 失职/渎职 + 三个立 |
| 经责审计 | 聚焦权力规范运行 |
| 专项债 | 聚焦统筹发展和安全 |
| 绩效评价 | 聚焦兜牢民生底线 |

## 工作区配置

- **模型**: DeepSeek V4 Flash（默认免费）/ V4 Pro（复杂分析手动切）
- ⚠️ **心跳/定时任务必须用 v4-flash**（2026-06-26 用户指令确认），禁止用 V4 Pro/Kimi
- **2026-07-16 恢复**：v4-flash 403 故障已修复，心跳模型已从 deepseek-direct/deepseek-chat 切回 v4-flash
- **图片模型**: dashscope/qwen-vl-max（DeepSeek不支持image）
- ⚠️ **DashScope 调用规则**: 任何涉及 qwen-vl-max 的图片/PDF分析，**必须先询问用户确认**，不得自动调用
- **工作区**: D:\openclaw-workspace
- **插件**: 企业微信、微信
- **Python**: 3.14.0a5 / **Node**: v24.14.0
- **draw.io**: D:\dwaw\draw.io\draw.io.exe v30.0.1

## 用户偏好

- 直接高效，不废话 | 关注公司管理和业务发展 | 政府审计需求优先

## PPT工具矩阵（2026-07-08起，07-15新增dashi-ppt）
| 工具 | 定位 | 输出 | 场景 | 状态 |
|:--|:--|:--|:--|:--|
| guizang-ppt-skill | 瑞士风格HTML幻灯片 | 电子杂志级HTML | 汇报/演示 | ✅ 已装+融策深蓝定制 |
| ppt-master | 可编辑PPTX管线 | 原生.pptx | 正式交付/客户改稿 | ✅ 已装(缺tools依赖) |
| huashu-design | 全能设计skill | HTML+PPTX+MP4+原型 | 品牌/标书/动画 | ✅ 已装+品牌资产入库 |
| **dashi-ppt** | 模板编排器·每页带编辑控制台 | HTML(可浏览器逐页调)+可编辑PPTX+PDF | 行研/融资复盘/竞品/汇报/路演 | ✅ 已装v0.4.0 |

### dashi-ppt 使用要点（2026-07-15装）
- 路径：`~/.openclaw/skills/dashi-ppt/`（npx 默认还装了一份到 `~/.claude/skills/dashi-ppt/`）
- 装法：`npx --registry=https://registry.npmmirror.com dashi-ppt-skill@latest`（旧名dashiai-ppt已废弃）
- 12套主题、1020版式、8576控件；生成HTML后浏览器逐页拖调，再导可编辑PPTX
- ✅ 运行时依赖已装(npm install)，引擎实测可用；Edge已装可导出PPTX/PDF
- ⚠️ 成本：10页PPT≈10万token（贵，成本敏感场景慎用）
- ⚠️ 导出引擎html-deck-to-pptx闭源；自定义被有意收窄
- ⚠️ 本机无bash/git，官方`render_goal_deck.sh`跑不了——需按SKILL.md用npm脚本直接驱动(props:safe→validate→render:goal→preview:start)
- ⚠️ 每次完成后运行 `node <skill>/scripts/check_latest_version.mjs` 检查更新
- 端口段：预览默认5200-5999(避开4178/4300/4400用户保留端口)

### 融策品牌资产
- 路径: `~/.openclaw/skills/huashu-design/assets/rongce-brand/`
- 色板: 深蓝#0A1F3F / 青绿#1A5C6E / 铜金#C5955C / 暖灰#F5F2EC
- Logo: 融策logo.png（方形标，深蓝底+铜金字）
- 抬头图: 融策抬头.jpg（深蓝横幅）

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

## 多Agent审计平台 v3.0（2026-06-21建立，2026-07-21更新至v3.0）

### 架构
```
audit-blackboard/
├── orchestrate_v3.py    ← v3.0调度中枢：create→penetrate→spawn(并行)→collect→report
├── launch.py            ← 一键启动（python launch.py "项目名" --type 简称）
├── agent_router.py      ← 22 Agent路由调度：意图→Agent匹配（关键词+业务线+快捷词三层）
├── agent_registry.json  ← 22 Agent统一注册表
├── api_gateway.py       ← 统一API网关：14模型路由+预算监控+工作流编排
├── auto_trigger.py      ← 文件监控守护：raw_data/有新文件→自动触发Agent链
├── issue_fusion.py      ← 疑点融合中枢：accept→cluster→dedup→resolve→track→chain
├── handover_protocol.py ← ★新增 状态交接协议：标准化Agent间接力（H-packet）
├── handover_hook.py     ← 交接钩子：编排引擎集成
├── agent_specs/         ← 22个Agent规格
├── schemas/             ← finding_schema.json统一格式
├── playbooks/           ← 按业务线的取数深度指南
├── DATA_SPEC.md         ← 12业务线取数规范
└── projects/            ← 项目工作区
    └── <项目名>/
        ├── raw_data/    ← 原始数据放这里
        ├── findings/    ← 各Agent发现JSON
        ├── handovers/   ← ★ v1.0 交接包（H-packet）
        ├── collision/   ← 交叉碰撞结果
        └── status.json  ← 进度看板
```

### 22 Agent阵容

**核心审计（7）**: data_scout / contract_hound / bid_hunter / law_inspector / workpaper_crafter / report_writer / review_sentinel

**工程咨询（3）**: budget_estimator / settlement_auditor / fiscal_reviewer

**绩效评价（1）**: performance_evaluator

**专项检测（2）**: expert_bias_detector / 会议纪要分析师

**数据运维（4）**: OCR预处理员 / 数据分类员 / 数据脱敏 / 调整分录生成师

**方案撰写（1）**: 方案撰写师

**v3.0核心升级**:
- 5坐标系并行穿透引擎：时空×物理×社会关系×行为×时间序列 → 自动映射Agent
- 疑点融合中枢：三模型联合评审→cluster→dedup→冲突消解→证据链追踪
- ★状态交接协议 v1.0：Agent间标准化H-packet传递（Goal+事实+警告+产出）
- 14模型智能路由+预算监控+自动触发守护

**用法**: `python launch.py "项目名" --type 简称` → 我对你说"开始审计XX" → spawn Agent(并行) → `python handover_hook.py --project "XX" --agent "xxx"` → `python orchestrate_v3.py report`

### AgentDebugX 调试工具箱 v1.0（2026-07-23新增）

灵感来源：AgentDebugX 论文（UIUC/Stanford/Google/UofT, 2026.07）

| 模块 | 对标 | 功能 | 命令 |
|:-----|:-----|:-----|:-----|
| agent_debug_rules.py | Detect | 4类20条确定性规则检测（格式/逻辑/审计/交接异常），不调LLM | `python agent_debug_rules.py --project "XX" --agent "xxx"` |
| agent_deep_debug.py | Attribute | 三步DeepDebug根因定位（全局轨迹→结构探查→交叉验证），含8种已知根因模式 | `python agent_deep_debug.py --project "XX" --mode deepdebug` |
| agent_error_hub.py | Recover+Rerun | 错误共享库（脱敏→去重→标签→回归测试），跨项目对比 | `python agent_error_hub.py --action store --project "XX"` |
| agent_debug.py | 统一入口 | 一键四步闭环 | `python agent_debug.py run "XX项目"` |
| handover_hook.py v1.1 | 集成 | 交接后自动触发规则检测，`--debug` 参数启用 | `python handover_hook.py --project "XX" --agent "xxx" --debug` |

**核心设计**：
- 20条确定性规则分4个包：格式协议(R0xx)、逻辑一致性(R1xx)、审计专项(R2xx)、多Agent交接(R3xx)
- 8种根因模式：交接上下文丢失/发现丢失/坐标系错误/过早终止/数据格式混乱/模型幻觉/工具调用错误/严重程度误判
- Error Hub 自动脱敏（金额→[金额]、企业→[企业]、日期→[日期]），指纹去重，自动标签
- 回归测试用例从错误库自动生成，支持 `--project` 对比最新检测结果
- handover_hook v1.1 已集成，`--debug` 参数交接后自动触检测→入库→回归

**已入库文章**：`knowledge/references/AgentDebugX-LLM-Agent调试框架.md`

## 场景-技能-资料三层调用体系

- **第一层**: `SCENARIO-SKILL-MAP.md` — 场景→技能→资料速查表
- **第二层**: `knowledge/INDEX.md` — 资料索引（来源/关键词/摘要）
- **第三层**: 技能SKILL.md触发条件（长期建设）

触发流程：用户需求 → SCENARIO-SKILL-MAP匹配 → 读技能SKILL.md → INDEX.md找资料 → 告知调用了什么

## 串标围标检测体系（摘要）

23层+9纵深检测体系（v3.6），技术详情见 `skills/procurement-audit-models/TECHNICAL-FOUNDATION.md`

| 层级 | 检测维度 | 数据源 | 爆炸力 |
|:--|:------|:-------|:--:|
| L1 | 报价规律 | 开标一览表 | 🔴铁证 |
| L2 | 投标IP/MAC | 代理后台日志 | 🔴铁证 |
| L3 | 文本雷同(TF-IDF) | 投标文件全文 | 🔴铁证 |
| L4 | 图片/资源哈希 | PDF嵌入图片→感知哈希 | 🔴铁证 |
| L5 | 元数据交叉 | core.xml/WPS GUID | 🔴铁证 |
| L7 | 打印机型号 | PDF Producer字段 | 🟡强信号 |
| L8 | 工商关联穿透 | 天眼查/企查查 | 🔴铁证 |
| L9 | 保证金资金链 | 银行汇款凭证 | 🔴铁证 |
| **L10** | **评标打分异常（倾向性照顾）** | **评委逐项打分表** | **🔴铁证** |
| L11 | 供应商伴随投标(FP-growth) | 3+项目历史数据 | 🔴铁证 |
| **L15** | **历史中标模式（陪标+中标专业户）** | **3年+招投标台账** | **🔴铁证** |
| **L18** | **投标设备电子指纹八项** ⭐v3.6 | **IP/MAC/CPU ID/硬盘SN/主板SN/机器码/文件GUID/图片哈希** | **🔴铁证** |
| L19 | 评标专家违规 | 专家库+社保缴费表 | 🔴铁证 |

**核心策略**: L3+L4+L5三杀即可定案，不依赖代理机构配合。

**v3.6更新（2026-07-13）**: L18全面升级为八项投标设备电子指纹检测，新增CPU ID/硬盘SN/主板SN/整机机器码/文件GUID等硬件级指纹，附Windows原生查看命令和投标留痕位置。来源：微信公众号「PaperSkill」《八项投标电子指纹证据》。

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

- **⚠️ npm prefix 陷阱**（2026-07-16）：本机 npm 全局 prefix 被设为 `C:\Users\scrccpa\AppData\Local\Programs\OneClaw`（非默认）。任何 `npm install -g` 都装进 OneClaw 目录，与桌面版自带 gateway.asar 版本打架 → protocol mismatch → 频繁掉线。**禁止 npm/update.run 更新 openclaw**，版本跟 OneClaw App 走；装其他全局包前先 `npm config get prefix` 确认

- **报告结论复核铁律**（2026-07-06 平头哥指令）：写完或复核任何报告后，必须逐项重新核算汇总数字和关键结论，并把计算依据写在复核说明里。不得凭心算手动填汇总行。依据格式：每条结论后附（数据来源+计算方法+交叉验证结果），方便平头哥独立判断。

- **spawn 必须带 runTimeoutSeconds**，否则子代理跑完后空转耗token。这次OCR任务跑了78分钟（totalTokens 41k）就是因为没设超时

- .doc格式是元数据盲区（WPS存.doc时SummaryInformation为空）
- PDF扫描件比.docx裸露更多信息（扫描仪型号写在Producer字段）
- TF-IDF要去噪（招标模板化承诺函会制造假阳性）
- 元数据清除行为本身即是审计证据
- Windows GBK编码是Python脚本的常驻坑（需 `sys.stdout.reconfigure(encoding='utf-8')`）

## 2026-07-09 大事件：模型路由 v4.0 + 知识库三件套

### 模型路由 v3.0→v4.0 重构
- 路由依据从「任务类型」改为**「错了要付出什么代价」**（错误代价六级）
- GPT-5.5 从替补升级为表达审查双签人
- v4.0 混合架构：任务类型快速分类 + 错误代价精准调级
- 新增 qwen3.7-plus（中文原生·图片输入·公文）
- 创建测试套件 15 题（`knowledge/references/模型路由验证测试套件.md`）
- 跑题5验证：qwen 9/9 vs flash 7/9，确认中文路由决策正确

### 知识库三件套升级
- `scripts/prune_knowledge.py` — 内容清理扫描（343文件全部活跃）
- `knowledge/PARA-INDEX.md` — PARA四层分类 + 入库门槛 + 5分钟工作流
- `scripts/build_links.py` — TF-IDF双向链接（338篇/65%有链接/平均2.4关联）
- `scripts/rag_bridge.py` — RAG↔Obsidian桥接器
- `obsidian-vault/知识库控制面板.md` — Obsidian集成面板
- KEY: 文章10要素全部覆盖，知识库从被动存储升级为主动管理

### 其他
- 审计情报采集（4/5成功）
- 阿坝发展控股集团审计评估收费测算表（三指标对比版Excel）
- **07-22 更新**：控制价专项审核报告已出（征求意见稿07-14 + 正式版07-16）
  - 存放路径：`E:\2026\审计报告\审计、评估费用测算\意见征求稿=7.15\`
  - 含：预算控制价专项审核报告.docx / 征求意见稿.docx / 收费测算表=7.9二改.xlsx
- 宣传册final版（15页/53.5MB PDF）

## 2026-07-10 大事件：API Key 安全迁移 + 模型池扩展 + 路由全验证

### API Key 安全迁移（P0-P2 零成本加固）
- **P0**: 8 个 API Key 从 openclaw.json 明文 → Windows 环境变量（env://引用）
  - 映射：OC_KEY_TOP_V1 / GPT55 / CLAUDE / OPUS / FABLE / DOUBAO / IMAGE / QWEN
- **P1**: RAG Server 绑定 127.0.0.1 ✅（已确认）
- **P2**: .gitignore 加入 openclaw.json / *.json.bak / *.json.backup
- 备份：openclaw.json.bak（回滚：Copy-Item *.bak openclaw.json）

### 模型池扩展（8→12个）
- 新增：gpt-5.6-luna / gpt-5.6-sol / gpt-5.6-terra（均通过 cbwyy.top 代理）
- 支持 text+image 输入
- Key 直接迁移到环境变量（OC_KEY_LUNA / SOL / TERRA）

### 路由架构重构
- **五级→六级**：新增「咨询层」独立路由层
- fable-5 从高代价层校验员 → 独立顾问层（做决策之前先问）
- 错误代价升级规则优化：升级条件不变，新增咨询层升级路径
- fallback 链扩展：`[v4-pro, qwen3.7-plus, fable-5, sonnet-5, gpt-5.5, luna, sol, terra]`

### 全路由验证（12/12模型全部通过）
| 模型 | 状态 |
|:--|:--:|
| v4-flash, qwen3.7-plus, fable-5, v4-pro | ✅
| sonnet-5, gpt-5.5, gpt-5.6-luna/sol/terra | ✅
| opus-4-8, doubao | ✅

### TOOLS.md 路由表全面更新
- 可用模型一览表（12个模型×5字段）
- 错误代价六级路由图（新增咨询层）
- 任务路由表（咨询层引用）
- Fable-5 咨询层说明
- 模型清单表（API Type/baseUrl/Input）
- 环境变量 Key 映射表

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

## 2026-07-11 大事件：API Key 全明文化 + 调用环境稳定

### 背景
fable-5 换新 key 时发现 Windows 上 env:// 引用的致命缺陷：
- `setx` 写注册表 ✅
- Gateway 进程继承父进程环境块，不重读注册表 ❌
- SIGUSR1 重启不刷新环境变量 ❌
- 导致 2026-07-10 的 P0 安全迁移（env://）实际上对 fable-5 无效

### 修复方案（根本解法）
把所有 11 个 API Key 从 `env://` 引用**全部转回明文**写入 openclaw.json：
- 备份：`openclaw.json.bak`（回滚用）
- 安全前提：`.gitignore` 已包含 `openclaw.json` 和 `**/openclaw.json`
- 验证：11/11 健康检查全部通过

### 教训
- Windows 上 `env://` 只有在进程完全重启（taskkill + 重新启动）时才生效
- SIGUSR1 信号重启不刷新环境变量——这是 Windows 进程模型固有行为
- 文件落盘安全 < 功能稳定可靠时，优先选稳定
- 11 个注册表 OC_KEY_* 环境变量保留，不影响明文配置，可随时删除

### 总结
| 时间 | 方案 | 问题 | 结论 |
|:--|:--|:--|:--|
| 07-10 | env:// 安全迁移 | fable key 换了，env:// 不生效 | Windows 进程模型不兼容 |
| 07-11 | 全部明文 + .gitignore 保护 | 已解决 | 稳定压倒一切 |

## 2026-07-13 新增：两个画图技能 + 微信爬取技巧

### 新装技能
1. **fireworks-tech-graph** — 技术架构图SVG生成器，8种风格（扁平/暗黑/蓝图/Notion/玻璃态/Claude风/OpenAI风/暗黑奢华），支持UML、AI架构模式
   - 路径：`~/.openclaw/skills/fireworks-tech-graph/`
   - GitHub：yizhiyanhua-ai/fireworks-tech-graph

2. **architecture-diagram-generator** — 暗黑风架构图HTML生成器，自带Copy/PNG/PDF按钮，语义配色
   - 路径：`~/.openclaw/skills/architecture-diagram-generator/`
   - GitHub：cocoon-ai/architecture-diagram-generator

### 微信爬取技巧
- 微信公众号文章必须用**移动端User-Agent**（Android浏览器+MicroMessenger头）
- 普通web_fetch只能拿到JS渲染空壳
- 详见TOOLS.md「微信文章爬取技巧」

## 2026-07-19 大事件：完整路由配置 + KIMI-K3 接入

### 路由配置全面重构
- 修复：主模型从 `deepseek-direct/deepseek-chat`（直连逃生）→ `v4-flash`（免费日常）
- 修复：`deepseek-direct` 在 fallback 链中重复出现（prmary + last）
- 新增：`kimi-k3` 和 `doubao` 加入 fallback 链（之前被遗漏）
- 完整 fallback 链：12层（v4-pro → gemini → qwen → fable → sonnet → gpt-5.5 → luna → sol → terra → kimi-k3 → doubao → deepseek-direct）
- 验证：config.patch 成功，Gateway SIGUSR1 重启生效，14模型健康检查全通过

### KIMI-K3（第15个模型）

### KIMI-K3 接入
- 模型ID：`custom-cbwyy-kimi/kimi-k3`
- 服务器：`https://cbwyy.top/v1`（OpenAI 兼容接口）
- API Key：`sk-PvqkSJ7p0AKyh2k6WXaO5YIYEAQFlnwgeetxdBmEleGhk38m`
- 支持输入：text + image
- 特征：带 reasoning 的国产推理模型，类似 DeepSeek 的 reasoning 风格
- 验证：HTTP 200，子代理 modelApplied: true
- 健康检查脚本已同步更新，TOOLS.md 路由表已追加

## 2026-07-15 大事件：文献自动采集管道搭建 + 14模型路由体系全面建立

### Part 1: 文献采集管道
产出物见 `scripts/literature_collector.py`, 220篇文献入库。

### Part 2: 14模型路由体系（重大）
- 新增 gemini-3.1-pro-preview → deepseek-direct 直连逃生
- 路由 v4.0→v4.2: 错误代价+上下文窗口双重路由，经14模型联合评审全票通过
- 模型池演变：12→14个(07-15)→15个(07-19)→16个(07-21新增glm-5.2)
- 容灾架构 L1-L4: 重试→降级→直连→人工
- 健康检查脚本: scripts/model_health_check.py（覆盖16模型）
- 14模型评审结论: 路由逻辑✅ 代理单点故障🔴 数据合规⚠️
- 待办（已决策）: opus/sonnet走代理 ✅ | 数据合规:海外为主,敏感项目限国内模型 ✅

*最后更新: 2026-07-23 | 详细档案: memory/archive/ | 项目历史: 各项目README*

## 2026-07-21 大事件：GLM-5.2接入 + 状态交接协议落地 + 知识库5篇入库

### GLM-5.2（第16个模型）
- 模型ID：`custom-cbwyy-glm/glm-5.2`
- 服务器：`https://cbwyy.top/v1`（OpenAI 兼容接口）
- 特征：带 reasoning 的国产大模型（智谱AI），支持 text 输入
- 上下文窗口：128K，最大输出：8192 tokens
- Fallback链位置：第11位（kimi-k3之后，doubao之前）
- 验证：HTTP 200，返回 reasoning_content 字段
- 模型池：15→16个（含1直连逃生+1生图专用）
- 完整 fallback 链（14层）：flash → v4-pro → gemini → qwen → fable → sonnet → gpt-5.5 → luna → sol → terra → kimi-k3 → glm-5.2 → doubao → deepseek-direct
- 健康检查脚本已同步更新（16模型）

### 状态交接协议v1.0（Handover Protocol）
- 新文件：`audit-blackboard/handover_protocol.py`（H-packet 标准）
- 新文件：`audit-blackboard/handover_hook.py`（编排集成钩子）
- 背景：A2A多智能体通信协议三层架构分析后，发现融策v3.0在状态交接层最薄弱
- 核心功能：
  - `emit`：Agent完成后自动生成标准化交接包（Goal+事实+警告+发现摘要+产出文件清单）
  - `read`：下游Agent快速读取上下文，无需重读所有文件
  - `chain`：追溯完整交接链
  - `context`：下游Agent获取精简上下文摘要
- H-packet结构：handover_id / goal / confirmed_facts / excluded_items / completed_checks / pending_checks / findings_summary / context_snapshot / warnings / parent_handover
- 集成方式：collect阶段最后调用 `python handover_hook.py --project "XX" --agent "xxx"`

### A2A协议对比分析
- 对融策v3.0做了完整的三层对比分析（服务发现/能力对齐/状态交接）
- 结论：融策走黑板模式（适合审计溯源性）vs A2A走消息总线（适合高吞吐）
- 独特优势：5坐标系穿透引擎、三模型共识机制、证据链追溯、12业务线映射
- 改进路线图：P0状态交接标准化→P1健康检查→P2事前Schema校验→P3语义路由

### 知识库连续入库5篇文章
| # | 文章 | 来源 | 清单 |
|:--|:----|:----|:-----|
| 1 | 常态化帮扶资金审计重点更新 | 审天审地审空气 | 24条要点速查清单 |
| 2 | AI采购审计关联锁定与价格异常 | 审天审地审空气 | 8大能力+融策23层对照 |
| 3 | 三方合谋串通造假五招破局 | 审天审地审空气 | 五招核查步骤+约谈策略 |
| 4 | 无人机航测三维建模审计水利工程 | 审计案例2026年第6册 | 四步流程+设备参考 |
| 5 | A2A多智能体通信协议三层架构 | 审天审地审空气(转技术文) | 三层架构+融策启示 |
- RAG索引：17,436→17,933 chunks（+497）
- 新增脚本：`scripts/fetch_wechat.py`（微信文章移动端UA抓取）
- 公众号"审天审地审空气"确认为高质量可信源，后续可自动抓取入库

### 多Agent平台v3.0全面更新
- 平台从v1.0（7 Agent）→v3.0（22 Agent）的重大升级已在MEMORY.md完整记录
- 新增核心组件：agent_router.py / agent_registry.json / api_gateway.py / auto_trigger.py / issue_fusion.py
- 新增5坐标系并行穿透引擎（orchestrate_v3.py）
- MEMORY.md 已同步至当前状态

## 2026-07-14 大事件：Skill体系三件套治理

基于三篇微信文章启示（Skill管理技巧/Skill-insight平台/Agent异步架构），完成体系升级：

### 产出物
| 脚本 | 用途 | 来源 |
|:--|:--|:--|
| `scripts/skills_audit.py` | 扫描79技能→分类+重复检测+优化建议 | 第3篇 |
| `scripts/task_trace.py` | 执行追踪：start→step→finish→三维评分 | 第4篇 |
| `scripts/async_task.py` | 异步任务：慢操作后台化+通知注入 | 第5篇 |
| `scripts/skill_hub.py` | 统一控制面板 | 整合 |
| `config/skill_routing.json` | 场景路由配置（13场景×触发词） | 第3篇 |

### 关键发现
- 79个技能，7.1MB，常驻16个 + 13场景分组
- 4个超大技能（>500KB）：huashu-design/sql-toolkit/ppt-master/arch-diagram → 按需加载
- 场景路由实测：输入"绩效评价报告深度复核"→从79→25个（节省72个）
- wecom-* 15个技能名相似度高（前缀相同），自动去重需优化

### 设计理念（三篇联动）
1. Article 3（操作层）：按场景拆分目录，全局只留10-15个高频，避免token稀释
2. Article 4（架构层）：过程级评测（结果+路径+成本三维），靶向归因（Skill缺陷 vs 模型偏差）
3. Article 5（工程层）：慢操作异步化，模型显式background=true优先+关键词兜底

### 入库文章
- `knowledge/laws/_incoming/电子招投标串标蛛丝马迹-审计特种兵.md` — 7种电子串标信号+法条辨析

## 2026-07-31 郫都评审中心绩效指标体系

### 背景
受成都市郫都区政府投资项目评审中心委托，建立预算绩效指标与标准体系。该中心为区政府直属副局级事业单位，承担13项法定职能（政府投资项目全生命周期评审+PPP服务），2026年预算1,123万元，3个在编项目。

### 关键发现（14份资料研读）
- 2024年自评"绩效指标和标准体系建设"得**0分**——体系空白被官方自认
- 运行经费项目存在**严重指标错配**：日常保障类项目挂"项目评审金额≥50亿"等业务产出指标
- 党组织活动目标≥2次，实际7-12次——目标值严重低于实际
- PPP法定职能（物有所值评估等）在绩效目标中**完全空白**
- 核差率指标"≤-3%"导向有误：审减越多越好却用上限控制，实际8.43%

### 产出（V3.0 通用指标库版）
**路径**：`output/郫都评审中心绩效指标体系/`
- `郫都评审中心-预算绩效指标与标准体系.xlsx`（7 Sheet）
- `郫都评审中心-预算绩效指标与标准体系（报告）V3.0.docx`
- 旧版归档至 `_旧版归档/`

**架构**：通用指标库(32条) → 项目分类模板(A/B/C/D 4类) → 具体项目映射
- A类·业务服务：评审业务费 28条
- B类·运转保障：运行经费 17条（★已修复错配）
- C类·党建群团：党组织活动经费 11条（★已修正目标值）
- 部门整体：33条
- 新增项目只需选类型→勾指标→补特有，五步完成

### 状态
已交付平头哥审阅，等待业主反馈后决定是否扩展到7类通用库。

*最后更新: 2026-07-31 | 详细档案: memory/archive/ | 项目历史: 各项目README*

## 2026-07-19 公司改革方向：融策AI审计中台 / 融策·审盾

用户明确决定：以“融策AI审计中台”作为公司改革方向，用于转业务、拿项目、提效率、稳质量、建壁垒、做品牌。多模型评审后形成最终裁决：不要一开始做“大中台”，先做一个可验证的真实业务闭环。

核心定位：**用AI武装的政府财政资金安全与绩效智能守门人**。

对外品牌建议：**融策·审盾 —— 让你敢签字。**

第一阶段立项名称：**融策·审盾一期：绩效评价报告AI复核验证项目**。

30天唯一目标：验证AI能否在绩效评价报告复核中达到或超过融策审计经理平均水平，让报告复核更快、更准、更稳。

第一笔资源优先投：一个最懂绩效评价、写过最多报告、质量意识最强的业务骨干，全职30天；10份高质量历史绩效评价报告；现有RAG和大模型工具。

30天实验路径：
1. 第1-3天：选人、选10份报告、形成《绩效评价报告AI复核检查清单 v1.0》；
2. 第4-10天：构建最小复核器（上传报告→输出复核意见清单）；
3. 第11-20天：业务骨干逐条校验AI输出，统计命中率、误报率、漏报率、采纳率、耗时变化；
4. 第21-25天：AI复核 vs 3位审计经理人工复核盲测；
5. 第26-30天：形成《融策·审盾一期验证报告》。

通过标准：AI发现问题数量≥人工平均水平80%、误报率≤20%、重大错误漏检为0、报告复核时间减少30%以上、有效建议采纳率≥30%、项目经理愿意继续用≥2/3、至少形成1个投标展示案例。

关键禁忌：30天内不要做大屏、SaaS、多业务线、自动出报告、复杂多Agent编排，不对外宣传“AI自动审计”，未经质控的历史资料不得直接灌入知识库。

必要制度：AI输出留痕、人工确认、知识入库质控、项目闭环沉淀。人工必须确认问题定性、法规适用、金额结论、整改建议、责任归因、重大风险提示、对外报告表述。

后续所有公司AI改革、投标包装、团队转型、客户宣传和产品立项，均以此为基准方向。详细备忘录：`knowledge/strategy/融策AI审计中台改革方向-20260719.md`。

## 2026-07-21 十五五规划深度分析（公司改革风向标）

### 背景
财政部发布《注册会计师行业发展"十五五"规划（征求意见稿）》及起草说明，由Opus-4-8完成五维深度战略分析（定位/审盾重估/业务组合/品牌/三年路线图）。

### 核心判断
十五五规划对融策是"量身定做"：第一次把"数智化"提到与"规范化"并列，第一次明确支持"专精特新中小型事务所"，第一次提出"加强对西部地区人才培养"。融策政府审计业务=三者交集。

### 五化战略排序
🥇数智化（核心杠杆）→ 🥈品牌化（护城河）→ 🥉规范化（入场券）→ 标准化（基建）→ 国际化（放弃）

### 审盾定位升维
三层嵌套：内部质控工具 → 品牌信任锚点 → 行业基础设施。时间窗口18-24个月。

### 业务组合 & 三年路线图
- 重仓：预算绩效/专项资金/政府补贴/工程竣工决算
- 新方向储备：ESG审计/数据资产审计
- 2026基础建设年 → 2027影响力爆发年 → 2028生态位锁定年

### 立即执行（2026年7-9月）
1. 7月底前审盾一期白皮书 | 2. 8月中旬前省注协汇报 | 3. 9月底前审盾二期启动

### 详细文档
`knowledge/strategy/融策十五五战略分析-20260721.md`

### 规划原文
桌面：`注册会计师行业发展"十五五"规划.pdf`（16页）+ 起草说明.pdf（5页）

## 2026-07-22 重大立项：12业务线标准化指引手册

### 起因
- 省注协2026计划搞"全国首创"三项指引（经责报告模板/社会组织换届审计/司法会计鉴定）
- 平头哥决定：融策自己做12条线的标准化指引手册，对标并超越省注协

### 三模型评审
- Sonnet-5/Qwen 3.7+/Fable-5 三模型联合评审八章架构
- 结论：方向正确，但原架构需大改（P0级5项、P1级多项）
- 最终确定**v3.0架构**：前置通用卷 + 12分册业务卷 + 附录卷
- 新增：职业道德/业务承接/定性定责/访谈标准/典型案例分析独立成章
- AI嵌入每章而非独立成章；报告模板按12线×多委托方拆分

### 启动计划
- 第一批：经责审计 + 绩效评价 + 招投标审计
- 平头哥确认：业务手册作为后续重点工作
- 素材收集：每线需2-3个真实案例+1-2份报告+底稿+踩坑清单

### 关键文件
- `knowledge/strategy/四川注协2026三大指引-融策应对分析-20260722.md`
- 详细架构见 `memory/2026-07-22.md`

## 2026-08-01 审盾 Multi-Agent 平台完整路线图（重大战略共识）

### 背景
爬取两篇高价值微信文章并深度合成：
1. 腾讯内审《审计中信息与数据分析场景的Agent工程优化实践》— Agent Harness Engineering
2. 《一文看懂Multi-Agent：从任务分解到结果交付的18步全流程》— Multi-Agent协作框架

两篇合在一起 = 融策多Agent平台下一步完整路线图。

### 两篇文章的统一框架
- **文章1（Harness）**：回答「单个Agent怎么做才对」——数据理解底座 / 智能分类三步法 / 深度检索四环节 / 三层分工（审计师·Agent·工程链路）
- **文章2（Multi-Agent）**：回答「多个Agent怎么协作才对」——7角色 / 18步 / 5原则 / 8坑 / 虚线反馈回路
- **合在一起 = 审盾双引擎**：先给每个Agent搭Harness「外骨骼」，再用Multi-Agent框架组织成「项目组」

### 顶层设计原则（平头哥已确认）
1. **按工作性质分工**：模型做语义判断，工程链路做批量重复，审计师定口径
2. **执行不打分，打分不执行**：角色分离 = 对抗错误累积的结构解法
3. **闭环比单次生成更重要**：Plan→Execute→Review→Replan，不整体重跑
4. **先Harness后Multi**：先搭脚手架，再建组织——顺序不能反
5. **22 Agent → 7角色重映射**：管理Agent/Planner/研究Agent/执行Agent/Reviewer/运维组/工具层

### 现状差距（平头哥已确认：没补齐）
- **组织纪律** 🟡：orchestrate_v3.py 能调度但缺目标对齐；5坐标系穿透缺依赖图和并行调度
- **工程脚手架** 🔴：信源白名单=零，深度检索=零，数据底座=v0.1刚起步
- 12项能力对标：1🟢 + 5🟡 + 4🔴 + 2空白 → 最快3个月补齐

### 三阶段升级路线（平头哥已确认）
- **阶段1 v3.5（1个月）**：Harness基础设施 — 数据理解底座v1.0/智能分类v1.0/信源白名单/深度检索/工具标准化
- **阶段2 v4.0（2个月）**：组织化协作 — 管理Agent升级/Planner升级/H-packet v2.0/精准派单返工/退出条件
- **阶段3 v4.0+（1个月）**：业务闭环验证 — 绩效评价报告复核跑通完整18步

### 产出物（桌面+工作区）
- Excel：`桌面/融策审盾-MultiAgent路线图-20260801.xlsx`（5 Sheet：文章1摘要/文章2摘要/差距分析/升级路线/行动清单）
- 路线图文档：`knowledge/strategy/融策审盾-MultiAgent平台完整路线图-20260801.md`
- 抓取脚本：`scripts/fetch_wechat.py`（通用微信文章爬取，传URL即用）
- 文章1：`wechat_articles/agent_optimization_20260801/`（6,800字 + 8张图）
- 文章2：`wechat_articles/article_20260801_2/`（5,900字 + 1张流程图）
- 深度分析：`knowledge/strategy/腾讯内审Agent工程实践-深度分析与审盾映射-20260801.md`

### 第一周行动（P0优先）
1. **P0**：升级H-packet Schema至v2.0（Goal+事实+警告+产出+置信度+来源编号）
2. **P0**：Reviewer输出结构化为可执行返工指令
3. **P1**：设计信源白名单+来源编号绑定机制
4. **P1**：设计退出条件/最大轮次规范
5. **P1**：数据理解底座v0.1→v0.2（对接审盾现有项目）

### 关键判断
平头哥明确：这不是锦上添花的装饰品，是审盾能不能从「偶尔做对」走到「持续做好」的必经之路。两篇文章验证了审盾方向完全正确，差距在于执行。
