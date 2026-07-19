---
title: "8大领域专项 Skill 完全速查手册（上）"
source: "微信公众号"
url: "https://mp.weixin.qq.com/s/zA8WhDWED0sPrhKqQzTZzw"
date_fetched: "2026-07-19"
type: "AI工具"
tags: [审计, AI工具, 知识管理]
---

# 8大领域专项 Skill 完全速查手册（上）

覆盖 PPT 生成、文章写作、流程图、量化交易 4 大场景，每个 Skill 含简要说明和直接可访问的链接。
最后更新：2026-07-171. 幻灯片 / PPT 生成
2026 年共识："PPT 的未来是 HTML"——AI 用代码生成幻灯片比 PPTX 更可靠。以下按输出格式分 7 类，40+ 方案。原生 .pptx 输出
ppt-master ⭐29.7K — AI 从任意文档生成真正可编辑的 PPTX（SVG→DrawingML），20 套模板含麦肯锡/Google风，6000+ 图标，16:9/4:3/小红书/A4 全格式。工具免费，约 $0.08-20/份。
🔗 github.com/hugohe3/ppt-master
Anthropic 官方 pptx — python-pptx 直操 XML，创建/编辑/合并/图表/演讲者备注，可指定风格。
🔗 github.com/anthropics/skills
MiniMax pptx-generator — 4 阶段流程，Office 全系列（PDF/PPTX/XLSX/DOCX），97% 技能遵循率。
🔗 github.com/MiniMax-AI/skills
MBB Decks — 麦肯锡/BCG/贝恩咨询风格，Action Title + MECE 要点。
🔗 github.com/floflo11/mbb-decks
codepptx — MCP Server，JSON→.pptx，5 种主题，增量构建。
🔗 npm: codepptx
PPTAgent 4.8K — 反思式 Agent，多步规划→生成→修订。 pptx-manipulation — 全 python-pptx API 控制，兼容 Claude Code/Cursor/Cline/Codex。
🔗 explainx.ai
slidemind — PowerPoint 插件桥接，企业品牌模板自动匹配。
🔗 npm: slidemind
paper-analyst — 学术论文→提取 PDF 图表→组会 PPT。 presenton 8.5K — 开源 Gamma 替代+API。
🔗 github.com/presenton/presentonHTML/Web 输出（主流）
html-ppt-skill ⭐5.4K / 12K+安装 — 36 主题、15 模板、31 布局、47 动效。按 S 键演讲者模式（提词器+计时器）。安装：npx skills add lewislulu/html-ppt-skill
🎨 仓库 templates/ 目录含主题/布局/模板画廊
🔗 github.com/lewislulu/html-ppt-skill
Frontend Slides ⭐25K — 12 预设+34 Bold 模板，反 AI 塑料味，.pptx→HTML 转换，生成前 3 风格预览。
🔗 github.com/zarazhangrui/frontend-slides
Guizang PPT（归藏）⭐20.8K — 设计师歸藏之作。Style A 电子杂志×电子墨水（WebGL）+ Style B 瑞士国际主义（22 锁定版式）。
🔗 github.com/op7418/guizang-ppt-skill
Next Slide — 50+ 风格中英双语，按 E 浏览器内编辑。 open-slide — React 组件驱动，Inspector 点击评论。 slide-wright — reveal.js 每次新设计。 Casablanca — 增量添加不重建 Deck。 Slides AI Plugin — HTML+PPTX 双输出。 Claude Open Design — 31 Skills+72 品牌设计系统。Markdown → Deck
AlemTuzlak Slidev — 无头浏览器自验证，Mermaid→PNG 自动。Marp Slides — 22 套示例。content-designer — Slidev/Reveal/Spectacle 品牌一致性。图片优先型
NanoBanana — Gemini 3 Pro Image，文字渲染极强。banana-slides 15K。figma-slides-mcp — Figma 画布直控。PPT 快速选型需求推荐原生可编辑 .pptxppt-master（29.7K Stars）零依赖 HTML 演讲html-ppt-skill（演讲者模式）极致设计美感Frontend Slides 或 Guizang PPT咨询级 MBB 风MBB Decks投资人路演Felo Slides（54/60 分，AI 搜索+调研）找更多awesome-ai-ppt 分类索引2. 文章写作与内容创作
核心模式：Markdown 优先 → 文风提取 → 分阶段编辑 → 反 AI 痕迹检测 → 多平台发布。
claude-content-writer ⭐ — 5 阶段工作流（Discuss→Plan→Execute→Verify→Ship），Voice Profile 扫描你的 URL 检测文风，SEO 内置，反 AI 痕迹审计（检测~25 种 AI 写作标记并重写）。
🔗 npm: claude-content-writer
scribetronic — 23 个写作 Skill + 编辑日历，3 个编排器，反 Slop 检查。
🔗 npm: scribetronic
EveryDay Writer — 13 个子 Skill：Newsletter/LinkedIn/Twitter/网页文案/销售文案/剧本写作。
🔗 github.com/Deupaxx/EveryDay-Writer
content-writing-plugin — 草稿/校对/润色/版本管理/发布全流程。
🔗 github.com/danielrosehill/Claude-Content-Writing-Plugin
Ryan Doser Skills Stack V2 — 40+ Skill 跨 8 类别，>10 万美元收入验证，$99 终身。 claude-writing-skills — 5 个聚焦 Skill（研究/评分/中文平台发布）。发布管线
baoyu-post-to-wechat — 公众号 API 发布（grace/simple/modern 主题）。 baoyu-post-to-x / baoyu-post-to-weibo — Twitter/微博发布。 baoyu-format-markdown — 自动排版（中英文空格/标点/标题层级）。
🔗 github.com/JimLiu/baoyu-skills3. 流程图 / 图表 / 图解
趋势：从「AI 写 Mermaid」→「验证+渲染+导出+视觉自检自纠错」。
drawio-skill ⭐ — 自然语言→.drawio。7 种预设（ERD/UML/C4/架构/ML/流程图），读 PNG 自检+自动修复 6 类问题（重叠/裁切），最多 5 轮迭代，321 AI Logo，代码库→图表。
🔗 github.com/Agents365-ai/drawio-skill
VisualCave — Mermaid.js→交互 HTML，16 种图表，暗/亮模式，分步揭示（演讲用），一键导出 SVG/PNG/PDF/GIF。
🔗 github.com/varkart/visualcave
claude-mermaid — WebSocket 实时预览，修改即刷新，8 种主题，多图同时编辑。
🔗 npm: claude-mermaid
mermaid-skill — 验证优先，11+ 图表，双重渲染（本地 mmdc/Kroki API）。
🔗 github.com/Agents365-ai/mermaid-skill
multi-chart-draw-skills — 5 引擎合一：Mermaid / ECharts / Mindmap / DrawIO / GeoGebra，中文友好。
🔗 github.com/twwch/multi-chart-draw-skills
baoyu-diagram — SVG 技术图解。baoyu-infographic — 20 布局×17 风格信息图。Lumen — 9 图表+8 配色。Obsidian Visual — Excalidraw/Mermaid/Canvas 三合一。4. 量化交易与股票分析
常见架构：Skill 层→Agent 层（并行子代理）→工具层（Python+API）。
数据源：yfinance / FMP / FINVIZ / SEC EDGAR / Alpaca。
ai-berkshire ⭐4.2K — 复刻巴菲特/芒格/段永平/李录方法论，18 个 Skill，Python Decimal 防幻觉，4 大师 Agent 对抗辩论，CI 审计流水线。实盘：+69%（2024）/ +66%（2025）。
🔗 github.com/xbtlin/ai-berkshire
trading-agents-plugin — 7 子 Agent（技术面→新闻→基本面→宏观→多头→空头→风险→组合经理），/trading-analysis NVDA，yfinance 免费数据。
🔗 github.com/lucemia/trading-agents-plugin
stock-analyzer — A 股+港股+美股全覆盖，13 章报告+5 张技术图，多数据源容灾（yfinance→东方财富→新浪→搜索）。
🔗 github.com/luda66/stock-analyzer
Super Hedge Fund Skill — 8 Agent（基本面/技术面/估值/情绪 + 巴菲特/Wood/Burry/Lynch 4 人格），波动率分档仓位管理。
🔗 github.com/StanleyChanH/super-hedge-fund-skill
Alpha Skills Suite — 113 个精英交易 Skill，Druckenmiller 合成器，VCP/CANSLIM 筛选器。
🔗 github.com/mphinance/alpha-skills
Deep Research Machine — DAG 异步研究，37 任务依赖波次，7 研究员→7 写手+critic-optimizer 循环。
🔗 github.com/druce/deep-research-machine
Claude Trading Skills — 市场宽度/IBD 派发日/宏观制度检测，Alpaca MCP 实盘集成。
🔗 github.com/tradermonty/claude-trading-skills

          
        
                

                预览时标签不可点