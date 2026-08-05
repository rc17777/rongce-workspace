# MEMORY.md - 长期记忆（精简版）

> 融策右护卫（OpenClaw AI助手）的长期记忆文件。仅主会话加载。
> 详细技术档案见 `memory/archive/`，历史事件归档见 `memory/archive/MEMORY_HISTORY.md`。

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

> 完整手册：`knowledge/references/总书记审计工作重要指示批示-引用手册.md`

| 场景 | 推荐引用 |
|:--|:--|
| 报告开篇 | 审计监督体系 + 三个如 |
| 审计重点 | 六个聚焦（选1-2条对口）|
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
- ⚠️ **心跳/定时任务必须用 v4-flash**，禁止用 V4 Pro/Kimi
- **图片模型**: dashscope/qwen-vl-max（DeepSeek不支持image），调用前需确认
- **工作区**: D:\openclaw-workspace
- **插件**: 微信（企业微信已禁用，bot凭据失效 853000）
- **Python**: 3.14.0a5 / **Node**: v24.14.0
- **draw.io**: D:\dwaw\draw.io\draw.io.exe v30.0.1

## 用户偏好

- 直接高效，不废话 | 关注公司管理和业务发展 | 政府审计需求优先

## PPT工具矩阵

| 工具 | 定位 | 输出 | 场景 |
|:--|:--|:--|:--|
| guizang-ppt-skill | 瑞士风格HTML | HTML | 汇报/演示 |
| ppt-master | 可编辑PPTX管线 | .pptx | 正式交付/改稿 |
| huashu-design | 全能设计 | HTML+PPTX+MP4 | 品牌/标书 |
| **dashi-ppt** | 模板编排器 | HTML+PPTX+PDF | 行研/汇报/路演 |

### dashi-ppt 要点
- 路径：`~/.openclaw/skills/dashi-ppt/` v0.4.0，12主题×1020版式
- 流程：props:safe → validate → render:goal → preview:start → export-pptx
- ⚠️ 成本高（10页≈10万token），需`OPENSSL_PATH`指 conda 里的 openssl.exe

### 融策品牌资产
- 路径: `~/.openclaw/skills/huashu-design/assets/rongce-brand/`
- 色板: 深蓝#0A1F3F / 青绿#1A5C6E / 铜金#C5955C / 暖灰#F5F2EC

## 核心高频技能

| 技能 | 用途 |
|------|------|
| perf-audit-checklist | 绩效审计发现逻辑检查清单 |
| audit-report-review | 审计报告AI复核15维检查 |
| audit-jingze | 经责审计四道关 |
| procurement-audit-models | 采购审计/围标串标检测 |
| data-analyst-cn | 数据分析助手 |
| financial-fraud-detection | Benford定律财务造假检测 |
| bid-document | 标书撰写 |
| drawio | 流程图/架构图 |
| deepseek-charting | 零代码画图表 |
| gov-doc-formatting | 政府公文GB/T9704排版 |

> 完整72技能清单见各SKILL.md触发条件

## RAG审计知识库

- 架构: TF-IDF + sklearn + DeepSeek API | Flask @ localhost:5000
- 数据源: knowledge/ + obsidian-vault/（1,235文件，13,635 chunk）
- 启动: 桌面双击`启动RAG知识库.bat`
- 核心脚本: `scripts/rag_rebuild.py` / `rag_query.py` / `rag_server.py` / `rag_watcher.py`

## 多Agent审计平台 v3.0

```
audit-blackboard/
├── orchestrate_v3.py  ← 调度中枢（5坐标系穿透引擎）
├── launch.py          ← 一键启动
├── agent_router.py    ← 22 Agent路由
├── issue_fusion.py    ← 疑点融合中枢
├── handover_protocol.py ← H-packet状态交接
├── agent_specs/       ← 22 Agent规格
└── projects/          ← 项目工作区
```

22 Agent（核心审计7 + 工程咨询3 + 绩效评价1 + 专项检测2 + 数据运维4 + 方案撰写1 + 其他4）
用法: `python launch.py "项目名" --type 简称`

### AgentDebugX 调试工具箱
- 4类20条确定性规则检测 / 三步DeepDebug根因定位 / Error Hub错误共享库
- 统一入口: `python agent_debug.py run "XX项目"`

## 串标围标检测体系（v3.6）

23层+9纵深检测体系，详情见 `skills/procurement-audit-models/TECHNICAL-FOUNDATION.md`

核心策略: L3(TF-IDF文本雷同)+L4(图片哈希)+L5(元数据交叉)三杀即可定案。
L18新增八项投标设备电子指纹检测（IP/MAC/CPU ID/硬盘SN/主板SN/机器码/文件GUID/图片哈希）。

## 公司战略方向：融策·审盾

**定位**: 用AI武装的政府财政资金安全与绩效智能守门人。
**品牌**: 融策·审盾 —— 让你敢签字。
**一期**: 绩效评价报告AI复核验证项目（30天实验验证）。

关键禁忌：不做大屏/SaaS/多业务线/自动出报告，不宣传"AI自动审计"，未经质控资料不入库。

## 重要规则

- DeepSeek只支持image_url在最后一条用户消息，历史图片→400错误
- 子代理访问不了桌面绝对路径，数据放 `projects/<项目>/raw_data/`
- 大Git push（>20MB）需开代理 + 延长超时
- OCR批量任务前确认DeepSeek余额
- ⚠️ **禁止 npm/update.run 更新 openclaw**，版本跟 OneClaw App 走
- **报告结论复核铁律**: 写/复核报告后必须逐项核算汇总数和关键结论，附计算依据
- **spawn 必须带 runTimeoutSeconds**（批量OCR 300-600s，轻量 120-180s）

## 关键教训

- npm prefix 陷阱（曾指向 OneClaw 目录→版本冲突→掉线），全球包前先 `npm config get prefix`
- Windows env:// 环境变量在 SIGUSR1 重启时不刷新→全部用明文
- .doc格式元数据盲区 / PDF扫描件比.docx露更多 / TF-IDF要去噪 / 元数据清除行为=证据
- Windows GBK编码→ `sys.stdout.reconfigure(encoding='utf-8')`

## 近期大事记

| 日期 | 事件 | 详情 |
|:--|:--|:--|
| 08-01 | 审盾Multi-Agent完整路线图 | `knowledge/strategy/融策审盾-MultiAgent平台完整路线图-20260801.md` |
| 07-31 | 郫都评审中心绩效指标体系交付 | `output/郫都评审中心绩效指标体系/` |
| 07-22 | 12业务线标准化指引手册立项 | `knowledge/strategy/四川注协2026三大指引-融策应对分析-20260722.md` |
| 07-21 | 十五五规划五维战略分析 | `knowledge/strategy/融策十五五战略分析-20260721.md` |
| 07-19 | 融策·审盾改革方向确立 | `knowledge/strategy/融策AI审计中台改革方向-20260719.md` |

> 更早历史事件见 `memory/archive/MEMORY_HISTORY.md`

*最后更新: 2026-08-05 | 详细档案: memory/archive/ | 项目历史: 各项目README*
