# Skills 目录结构梳理报告

> 生成时间：2026-07-06 13:12 CST
> 扫描范围：`~/.openclaw/skills/` + `~/.openclaw/workspace/skills/` + `wecom-plugin`

## 总览

| 维度 | 数据 |
|------|------|
| 独立 Skill 总数 | **127** 个（去重后） |
| `~/.openclaw/skills/` | 103 个 |
| `workspace/skills/` | 9 个 |
| `wecom-plugin` | 15 个 |
| 已归档 `_archived/` | 6 个 |
| 总文件数 | 3,767 |
| 总大小 | 59.9 MB |

---

## 一、🔴 审计核心业务（22个）

| Skill | 文件 | 脚本 | 参考 | 描述 |
|-------|------|------|------|------|
| audit-card-generator | 2 | - | - | 审计卡片生成器 |
| audit-jingze | 1 | - | - | 经责审计四道关 |
| audit-meeting-review | 1 | - | - | 望闻问切会议记录诊断 |
| audit-project-selection | 1 | - | - | 审计立项精准化 |
| audit-rectification | 1 | - | - | 审计整改标准化 |
| audit-report-review | 2 | - | ✅ | 审计报告AI复核15+6维检查 |
| audit-risk-portrait | 2 | ✅ | - | 审计风险画像 |
| audit-text-mining | 6 | ✅ | ✅ | 非结构化文档文本挖掘 |
| bim-engineering-audit | 2 | ✅ | - | BIM工程审计 |
| budget-audit | 7 | ✅ | - | ⚠️ **缺描述** |
| dynamic-audit-alert | 2 | ✅ | - | 动态审计预警 |
| energy-audit | 5 | ✅ | - | ⚠️ **缺描述** |
| engineering-audit | 7 | ✅ | - | ⚠️ **缺描述** |
| fiscal-supervision-model | 4 | - | ✅ | 财政监督检查模型 |
| gov-subsidy-penetration-audit | 3 | - | ✅ | 政府补贴穿透式审计 |
| penetrating-audit | 2 | - | - | 穿透式审计方法论 |
| perf-audit-checklist | 1 | - | - | 绩效审计发现逻辑检查清单 |
| regulatory-audit-response | 1 | - | - | 监管指定审计应对 |
| rpa-audit-automation | 1 | - | - | RPA自动化审计 |
| special-bond-audit | 2 | - | - | 专项债全周期审计 |
| special-fund-audit | 7 | ✅ | - | ⚠️ **缺描述** |
| subsidy-audit | 6 | ✅ | - | ⚠️ **缺描述** |

## 二、🟡 审计方法/框架（15个）

| Skill | 文件 | 脚本 | 参考 | 描述 |
|-------|------|------|------|------|
| agent-data-standard | 3 | - | ✅ | Agent友好数据标准 |
| apriori-audit | 3 | ✅ | ✅ | Apriori关联规则 |
| audit-data-analysis-methods | 2,229 | ✅ | - | ⚠️ 含 node_modules！ |
| audit-knowledge-graph | 1 | - | - | Neo4j知识图谱 |
| cot-capture | 5 | - | ✅ | 审计思维链沉淀 |
| digital-audit-methodology | 1 | - | - | 数字化审计10大框架 |
| financial-fraud-detection | 5 | ✅ | - | Benford定律 |
| first-principles-audit | 3 | ✅ | ✅ | 第一性原理审计 |
| gov-audit-methodology | 15 | ✅ | ✅ | 政府审计方法论 |
| image-classifier-audit | 168 | ✅ | - | 审计图片离线分类器 |
| magazine-knowledge-bridge | 1 | - | - | 杂志资料检索桥 |
| procurement-audit-models | 23 | ✅ | - | 采购审计/围标串标 |
| spatial-audit-analysis | 1 | - | - | 空间分析(QGIS) |
| unstructured-audit-data | 6 | ✅ | ✅ | 非结构化数据处理 |
| workflow-embedder | 2 | - | ✅ | 审计作业流AI嵌入 |

## 三、🟢 数据分析工具（10个）

| Skill | 文件 | 脚本 | 参考 | 描述 |
|-------|------|------|------|------|
| aloudata-anomaly-detection | 2 | - | - | 异常检测 |
| analysis-report | 2 | - | - | 分析报告生成 |
| data-analyst-cn | 3 | - | - | 通用数据分析专家 |
| forecast-simulation | 2 | - | - | 预测仿真 |
| hv-analysis | 6 | ✅ | ✅ | 横向价值分析 |
| scheduled-report | 2 | - | - | 定时报告 |
| sql-dataviz | 27 | ✅ | ✅ | SQL数据可视化 |
| sql-master | 19 | ✅ | ✅ | SQL查询智能体 |
| sql-report-generator | 109 | ✅ | ✅ | SQL报告生成器 |
| sql-toolkit | 155 | ✅ | ✅ | SQL全链路工具集 |

## 四、🔵 文档/报告/标书（9个）

| Skill | 文件 | 脚本 | 参考 | 描述 |
|-------|------|------|------|------|
| bid-document | 5 | ✅ | - | 专业标书撰写 |
| doc-formatter | 3 | - | - | 文档格式转换 |
| markdown-converter | 2 | - | - | Markdown转换 |
| patent-disclosure-skill | 51 | - | - | 专利交底书生成 |
| pdf | 3 | - | - | PDF工具集 |
| powerpoint-pptx | 4 | - | - | PPT编辑 |
| ppt-generator | 245 | ✅ | ✅ | PPT生成(合并版) |
| ppt-maker | 7 | ✅ | - | PPT一键生成 |
| tender-analyzer-agent | 11 | - | - | ⚠️ **缺描述** |

## 五、🟣 图表/可视化（13个）

| Skill | 文件 | 脚本 | 参考 | 描述 |
|-------|------|------|------|------|
| arch-diagrammer | 3 | ✅ | ✅ | 架构图生成 |
| deepseek-charting | 1 | - | - | DeepSeek画图表 |
| drawio | 7 | ✅ | ✅ | draw.io流程图 |
| illustration-analysis | 3 | - | ✅ | 插图需求分析 |
| paper-analyzer | 10 | ✅ | - | 论文分析 |
| paper-comic | 4 | - | ✅ | 论文漫改 |
| paper-deck | 7 | ✅ | ✅ | 论文PPT |
| posterdesign | 7 | - | - | 海报设计 |
| v2.5 | 3 | - | - | 海报设计v2.5 |
| video-creator | 3 | ✅ | - | ⚠️ **缺描述** |
| video-frames | 3 | ✅ | - | 视频帧提取 |
| video-toolkit | 6 | ✅ | - | 视频工具集 |
| visual-toolkit | 4 | ✅ | ✅ | 可视化工具集 |

## 六、📱 企业微信（15个）

| Skill | 文件 | 脚本 | 参考 | 描述 |
|-------|------|------|------|------|
| wecom-contact-lookup | 1 | - | - | 通讯录查询 |
| wecom-doc-manager | 7 | - | ✅ | 文档管理 |
| wecom-edit-todo | 1 | - | - | 待办编辑 |
| wecom-get-todo-detail | 1 | - | - | 待办详情 |
| wecom-get-todo-list | 1 | - | - | 待办列表 |
| wecom-meeting-create | 4 | - | ✅ | 创建会议 |
| wecom-meeting-manage | 1 | - | - | 管理会议 |
| wecom-meeting-query | 1 | - | - | 查询会议 |
| wecom-msg | 5 | - | ✅ | 消息收发 |
| wecom-preflight | 1 | - | - | 前置检查 |
| wecom-schedule | 6 | - | ✅ | 日程管理 |
| wecom-send-media | 1 | - | - | 发送媒体文件 |
| wecom-send-template-card | 2 | - | ✅ | 发送模板卡片 |
| wecom-smartsheet-data | 3 | - | ✅ | 智能表格数据 |
| wecom-smartsheet-schema | 2 | - | ✅ | 智能表格结构 |

## 七、✍️ 内容/AI基础（17个）

| Skill | 文件 | 脚本 | 参考 | 描述 |
|-------|------|------|------|------|
| brainstorming | 2 | - | ✅ | 头脑风暴 |
| cbwxy-image-2 | 3 | ✅ | - | cbwxy图片生成 |
| content-polish | 6 | - | ✅ | 文字润色(合并版) |
| copy-editing | 2 | - | ✅ | 校对润色 |
| copywriting | 2 | - | ✅ | 文案写作 |
| gpt-image-2 | 2 | ✅ | - | GPT图片生成 |
| humanizer | 3 | - | - | AI痕迹去除 |
| khazix-writer | 3 | - | ✅ | Khazix写作 |
| kimi-webbridge | 2 | - | ✅ | Kimi网页桥 |
| memory-manager | 12 | - | - | 记忆管理(合并版) |
| memory-setup | 2 | - | - | 记忆配置 |
| nano-banana-pro | 4 | ✅ | - | Nano Banana生图 |
| news-aggregator | 3 | - | - | 新闻聚合 |
| note | 4 | ✅ | - | 笔记系统 |
| openai-whisper | 3 | - | - | 语音转文字 |
| reflection | 2 | - | ✅ | 自省反思 |
| summarize-pro | 2 | - | - | 摘要提炼 |

## 八、⚙️ 开发/工具（20个）

| Skill | 文件 | 脚本 | 参考 | 描述 |
|-------|------|------|------|------|
| agent-browser-stagehand | 5 | - | - | 浏览器自动化(旧) |
| agent-memory-1-0-0 | 11 | ✅ | - | ⚠️ **缺描述，被memory-manager合并** |
| browser | 6 | - | - | 浏览器自动化(合并版) |
| deep-research-ecc | 6 | - | ✅ | 深度研究 |
| disk-cleaner | 65 | ✅ | ✅ | 磁盘清理 |
| github | 2 | - | - | GitHub CLI |
| openclaw-find-skills | 2 | - | - | 技能发现 |
| openclaw-skill-vetter | 3 | - | - | 技能安全审查 |
| proactive-agent | 30 | - | - | 主动Agent |
| prompt-librarian | 3 | - | ✅ | Prompt资产管理 |
| seedream-image-generation | 6 | ✅ | - | Seedream生图 |
| skill-manager | 4 | - | - | 技能管理(合并版) |
| skill-vetter | 2 | - | - | 技能安全审查(旧) |
| systematic-debugging | 2 | - | ✅ | 系统化调试 |
| tavily | 5 | ✅ | ✅ | Tavily搜索 |
| wiki-auto-ingest | 1 | - | - | ⚠️ **缺描述** |
| xiucheng-self-improving-agent | 5 | - | - | 自我改进Agent |
| zhixi-v2-enhanced | 2 | - | - | 智析v2.0(本地) |

## 九、❓ 杂项/归档（6个）

| Skill | 文件 | 状态 | 说明 |
|-------|------|------|------|
| audit-diagram-critic | 3 | ❓ | drawio子模块，缺描述 |
| gov-doc-formatting | 1 | 🗄️ 已归档 | 被 doc-formatter 合并 |
| html-ppt | 239 | 🗄️ 已归档 | 被 ppt-generator 合并 |
| lbbniu-skill-creator | 10 | 🗄️ 已归档 | Skill创建器旧版 |
| rongce-ppt | 4 | 🗄️ 已归档 | 被 ppt-generator 合并 |
| rongce-prompt-reverse | 3 | ✅ | 看图反推Prompt |

---

## ⚠️ 待处理问题

### 🔴 紧急
1. **`audit-data-analysis-methods` 含 2,229 文件** — 其中 `node_modules/` 占了 2,219 个，应清理或用 `.gitignore` 排除
2. **磁盘空间**: 59.9 MB 总量不大，但 `node_modules` (含在 audit-data-analysis-methods 内) 是纯浪费

### 🟡 重要
3. **5 个核心业务 Skill 缺描述**：`budget-audit`, `energy-audit`, `engineering-audit`, `special-fund-audit`, `subsidy-audit`, `tender-analyzer-agent`, `agent-memory-1-0-0`, `video-creator`, `wiki-auto-ingest`
4. **双源存在**：`~/.openclaw/skills/` 和 `workspace/skills/` 有大量同名 Skill，需确认 OpenClaw 读取优先级

### 🟢 优化
5. **合并冗余**：`copy-editing` + `copywriting` + `humanizer` + `summarize-pro` 已被 `content-polish` 合并，旧版可归档
6. **清理 `_archived/`**：确认无引用后删除 6 个归档目录
7. **wecom 15个 Skill 独立于业务体系**：考虑是否需要在业务 Skill 中引用 wecom Skill（如审计报告完成后自动发送）

---

## 📂 目录结构示意

```
~/.openclaw/
├── skills/                          ← 主 Skills 目录 (103个)
│   ├── audit-jingze/
│   ├── audit-report-review/
│   ├── drawio/                      ← 含 audit-diagram-critic 子模块
│   ├── ...
│   ├── _archived/                   ← 归档旧版 (6个)
│   │   ├── browser-act/
│   │   ├── copy-editing/
│   │   ├── copywriting/
│   │   ├── deepseek-charting/
│   │   ├── gov-doc-formatting/
│   │   ├── html-ppt/
│   │   ├── lbbniu-skill-creator_20260701/
│   │   └── rongce-ppt/
│   └── wecom-*/                     ← 企业微信 (15个)
├── workspace/
│   └── skills/                      ← Workspace Skills (9个, 与上面重复)
│       ├── browser/
│       ├── content-polish/
│       ├── doc-formatter/
│       ├── drawio/
│       ├── memory-manager/
│       ├── ppt-generator/
│       ├── skill-manager/
│       ├── video-toolkit/
│       └── visual-toolkit/
└── extensions/
    └── wecom-openclaw-plugin/
        └── skills/                  ← 企业微信插件 Skills (15个)
```
