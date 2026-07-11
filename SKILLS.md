# 🛠️ SKILLS.md — 融策工作区技能清单

> 最后更新: 2026-05-28 | 总计: 56 个技能

---

## 📋 技能管理规范

### 目录结构

```
skills/
├── skill-name/          # 技能源文件夹（Git 版本控制）
│   ├── SKILL.md         # 技能定义文件
│   ├── references/      # 参考资料
│   └── scripts/         # 脚本（可选）
└── skill-name.skill     # 打包产物（.gitignore 排除，不上传 GitHub）
```

### 规则
- **源文件夹** (`skills/<name>/`) → Git 跟踪，保持版本控制
- **打包文件** (`*.skill`) → 自动忽略，是 ZIP 构建产物，不提交
- **新增技能**: 先创建文件夹 + SKILL.md，需要打包时用 `openclaw skills build`
- **删除技能**: 删除文件夹后，手动清理 `.skill` 打包文件

---

## 📊 技能分类清单

### 🔴 审计核心（12个）

| 技能 | 状态 | 说明 |
|------|:----:|------|
| `audit-data-analysis-methods` | ✅ 活跃 | 7大审计数据分析方法 |
| `procurement-audit-models` | ✅ 活跃 | 采购审计模型（24层围标串标检测） |
| `financial-fraud-detection` | ✅ 活跃 | 财务造假检测（Benford定律等） |
| `apriori-audit` | ✅ 活跃 | Apriori关联规则算法（跨领域通用） |
| `gov-audit-methodology` | ✅ 活跃 | 政府审计方法论 |
| `digital-audit-methodology` | ✅ 活跃 | 数字化审计方法论（10大框架） |
| `first-principles-audit` | 🆕 新增 | 审计第一性原理分析 |
| `unstructured-audit-data` | 🆕 新增 | 非结构化审计数据处理 |
| `spatial-audit-analysis` | 📦 备用 | 审计空间分析（QGIS+K-Means） |
| `audit-knowledge-graph` | 📦 备用 | 审计知识图谱（Neo4j+Cypher） |
| `audit-text-mining` | 📦 备用 | 审计文本挖掘 |
| `illustration-analysis` | 📦 备用 | 文档插图需求分析 |

### 🟡 数据分析（7个）

| 技能 | 状态 | 说明 |
|------|:----:|------|
| `data-analyst-cn` | ✅ 活跃 | 中文数据分析助手 |
| `hv-analysis` | ✅ 活跃 | 横纵分析法深度研究 |
| `aloudata-anomaly-detection` | 🆕 新增 | 3σ时序异常检测 |
| `forecast-simulation` | 🆕 新增 | 趋势预测+What-if模拟 |
| `sql-master` | 📦 备用 | SQL专家 |
| `sql-dataviz` | 📦 备用 | SQL数据可视化 |
| `sql-report-generator` | 📦 备用 | SQL报告生成器 |

### 🟢 文档与写作（8个）

| 技能 | 状态 | 说明 |
|------|:----:|------|
| `bid-document` | ✅ 活跃 | 标书撰写 |
| `khazix-writer` | ✅ 活跃 | 公众号长文写作 |
| `summarize-pro` | 📦 备用 | 专业摘要 |
| `copywriting` | 📦 备用 | 营销文案 |
| `copy-editing` | 📦 备用 | 文字润色校对 |
| `pdf` | ✅ 活跃 | PDF处理与分析 |
| `markdown-converter` | 📦 备用 | Markdown格式转换 |
| `analysis-report` | 🆕 新增 | 报告编排（调度子技能→串叙事线） |

### 🔵 可视化与图表（3个）

| 技能 | 状态 | 说明 |
|------|:----:|------|
| `drawio` | ✅ 活跃 | draw.io 流程图/架构图 |
| `arch-diagrammer` | ✅ 活跃 | 架构图/流程图生成（SVG输出） |
| `deepseek-charting` | 📦 备用 | DeepSeek零代码画图表 |

### 🟣 AI 基础设施（7个）

| 技能 | 状态 | 说明 |
|------|:----:|------|
| `cot-capture` | ✅ 活跃 | 审计思维链沉淀 |
| `prompt-librarian` | ✅ 活跃 | 审计提示词资产管理 |
| `agent-data-standard` | ✅ 活跃 | Agent友好数据标准检查（12项清单） |
| `workflow-embedder` | ✅ 活跃 | 审计作业流AI嵌入分析（6种模式） |
| `proactive-agent` | 📦 备用 | 主动式Agent |
| `xiucheng-self-improving-agent` | 📦 备用 | 自改进Agent |
| `agent-memory-1-0-0` | 📦 备用 | Agent记忆系统 |

### ⚪ 工具与自动化（9个）

| 技能 | 状态 | 说明 |
|------|:----:|------|
| `video-creator` | ✅ 活跃 | 图片幻灯片视频生成 |
| `video-frames` | 📦 备用 | 视频帧提取 |
| `brainstorming` | 📦 备用 | 结构化头脑风暴 |
| `systematic-debugging` | 📦 备用 | 系统调试 |
| `reflection` | 📦 备用 | 复盘反思 |
| `nano-banana-pro` | 📦 备用 | Nano Banana Pro |
| `tavily` | 📦 备用 | Tavily搜索 |
| `github` | 📦 备用 | GitHub操作 |
| `news-aggregator` | 📦 备用 | 新闻聚合 |

### ⚫ 其他/实验（10个）

| 技能 | 状态 | 说明 |
|------|:----:|------|
| `agent-browser-stagehand` | 📦 备用 | 浏览器自动化 |
| `humanizer` | 📦 备用 | 文本人性化 |
| `memory-setup` | 📦 备用 | 记忆配置 |
| `note` | 📦 备用 | 笔记管理 |
| `scheduled-report` | 🆕 新增 | 定时报告自动重跑 |
| `openai-whisper` | 📦 备用 | 语音转文字 |
| `skill-vetter` | 📦 备用 | 技能审查 |
| `openclaw-find-skills` | 📦 备用 | 技能发现 |
| `openclaw-skill-vetter` | 📦 备用 | OpenClaw技能审查 |
| `tender-analyzer-agent` | 📦 备用 | 招投标分析Agent |

---

## 📈 统计

| 状态 | 数量 | 占比 |
|:-----|:----:|-----|
| ✅ 活跃使用 | 19 | 34% |
| 🆕 新安装（待验证） | 6 | 11% |
| 📦 备用/低频 | 31 | 55% |
| **总计** | **56** | 100% |

---

## 🔧 维护命令

```powershell
# 列出所有技能
Get-ChildItem skills -Directory | Select-Object Name

# 检查技能是否有 SKILL.md
Get-ChildItem skills -Directory | ForEach-Object { 
    $has = Test-Path "$($_.FullName)\SKILL.md"
    if (-not $has) { Write-Host "⚠️ 缺少 SKILL.md: $($_.Name)" }
}

# 清理所有 .skill 打包文件
Remove-Item skills\*.skill -Force
```
