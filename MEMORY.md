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

## PPT工具矩阵（2026-07-08起）
| 工具 | 定位 | 输出 | 场景 | 状态 |
|:--|:--|:--|:--|:--|
| guizang-ppt-skill | 瑞士风格HTML幻灯片 | 电子杂志级HTML | 汇报/演示 | ✅ 已装+融策深蓝定制 |
| ppt-master | 可编辑PPTX管线 | 原生.pptx | 正式交付/客户改稿 | ✅ 已装(缺tools依赖) |
| huashu-design | 全能设计skill | HTML+PPTX+MP4+原型 | 品牌/标书/动画 | ✅ 已装+品牌资产入库 |

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

*最后更新: 2026-07-14 | 详细档案: memory/archive/ | 项目历史: 各项目README*
