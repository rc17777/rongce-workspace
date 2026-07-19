---
title: "8大领域专项 Skill 完全速查手册（下）"
source: "微信公众号"
url: "https://mp.weixin.qq.com/s/GyIl5VXKo3g-cHJT79srHQ"
date_fetched: "2026-07-19"
type: "AI工具"
tags: [审计, AI工具, 知识管理]
---

# 8大领域专项 Skill 完全速查手册（下）

覆盖数据分析、图像设计、学术论文、音视频处理 4 大场景，每个 Skill 含简要说明和直接可访问的链接。
最后更新：2026-07-175. 数据分析与科学计算
SciPilot Figure Skill ⭐ — 8 步发表级科学图表：数据画像→选型→期刊规格→绘图→程序化+AI 双自检→导出。Okabe-Ito 色盲友好，7-9pt 字号，误差记录（SD/SEM/CI + n + 检验方法）。
🔗 github.com/Haojae/scipilot-figure-skill
scientific-agent-skills — 72 个科学计算 Skill：NumPy/SciPy/pandas/matplotlib/seaborn/plotly/scikit-learn/PyTorch/TensorFlow。
🔗 github.com/tondevrel/scientific-agent-skills
pandas-data-analysis — DataFrame 操作/清洗/GroupBy/可视化。data-analysis-jupyter — EDA/统计分析/发表级图表。data-analyst — 可复现工作流/自动报告。关键库选型库用途推荐场景PolarsRust 实现，10-100x 快大数据量替代 pandasDuckDB进程内 OLAP SQLCSV/Parquet 查询plotly交互式图表Web 展示seaborn统计可视化统计分析6. 图像 / 信息图 / 漫画 / 海报baoyu-skills 系列（最全视觉技能集）
安装：npx skills add jimliu/baoyu-skillsSkill用途核心参数baoyu-infographic专业信息图20 布局（桥接/漏斗/金字塔/思维导图/维恩/时间线/鱼骨）× 17 风格（手工/赛博朋克/像素/乐高/蓝图）baoyu-comic知识漫画5 画风×7 色调×6 分格布局，预设：OHMSHA/武侠/少女baoyu-cover-image文章封面5D 系统：Type×Palette×Rendering×Text×Mood = 54 组合baoyu-article-illustrator文章配图6 类型×8 风格，智能匹配内容baoyu-xhs-images小红书配图小红书风格图文生成
🔗 github.com/JimLiu/baoyu-skills
Nanobanana — Gemini 3 Pro Image 驱动，文字渲染极强（海报/标签/标题精准），1K/2K/4K，多种宽高比。
🔗 github.com/johnpsasser/nanobanana
AI Image Generator (jezweb) — 5 段 Prompt 框架+模型选择策略表：写实→Gemini Flash / 文字→GPT Image 2 / 透明→GPT Image 1.5 / 速出→Gemini Flash 免费。
🔗 github.com/jezweb/claude-skills
Art (DreamLab-AI) — 博客头图/流程图/时间线/手绘笔记，青蓝+焦橙手绘风。Design Image Studio — 火山引擎 Seedream，海报/产品图/教学图。7. 学术研究与论文写作
关键设计：引文幻觉验证（Semantic Scholar API+模糊匹配）、诚信门禁（Nature 7 大 AI 失败模式）、人机协作。
Academic Research Skills (ARS) ⭐6.4K — 最全面学术 Skill。26 Agent：13 研究员+12 写手+7 审稿人（含 Devil's Advocate），10 阶段编排器+诚信门禁，Semantic Scholar 引文验证，反谄媚协议。~$4-6/篇 1.5 万字。
🔗 github.com/Imbad0202/academic-research-skills
PaperOrchestra — Google 出品，5 Agent 流水线（大纲→图表 VLM critique→文献综述 Semantic Scholar 验证→章节写作→同行评审），文献质量领先基准 50-68%。
🔗 github.com/Ar9av/PaperOrchestra
Autonomous Paper XTS — 中文学术论文，6 阶段 75-95 分钟 1.5 万字：并行文献调研→两阶段写作→7 步自审→去 AI 痕迹（24 模式检测）→GB/T 7713 格式。
🔗 github.com/Marvisatron/autonomous-paper-xts
Research Skills (luwill) — 医学影像 7 阶段综述/论文 PPT（17 风格）/博士计划/5 Agent 协作。
🔗 github.com/luwill/research-skills
Philosophy Research Agents — 人文学科：research-design→literature-review→draft→peer-review，角色分饰。
🔗 github.com/Rlin1027/philosophy-research-agents
academic-skills-food-nutrition — 墨尔本大学出品，60+60 本食品/营养期刊，PRISMA 系统综述。
🔗 github.com/PangenomeAI/academic-skills-food-nutrition8. 音视频 / 播客处理
技术栈：ASR→Whisper/豆包/阿里百炼/Groq；翻译→LLM；配音→edge-tts/豆包；视频→ffmpeg。
onepod-Skill ⭐ — 6 Skill 播客全链路：YouTube 频道监控→字幕提取→4 阶段内容提炼→播客脚本生成→小宇宙→文章（Groq Whisper）。
🔗 github.com/SpaceZephyr/onepod-Skill
jianshuo/claude-skills ⭐ — 王建硕出品，13 个视频 Skill：转写（豆包/Whisper）→字幕翻译（断句重排）→TTS 配音→一条 ffmpeg 烧录+混音→视频本地化全流程→多机位自动剪辑→长视频切短视频。
🔗 github.com/jianshuo/claude-skills
baocut — 驱动 BaoCut macOS App CLI：转写/字幕/翻译/口播清理/导出。
🔗 github.com/JimLiu/baocut
pepys-mcp — 生产级转录，说话人标签+时间戳（diarization），SRT/VTT/TXT/MD/JSON，60 分钟免费。
🔗 npm: pepys-mcp
transcript-critic — 本地 whisper.cpp→批判性分析：时间轴摘要+证据笔记+逻辑谬误检测。
🔗 github.com/jftuga/transcript-critic
xiaoyuzhou-podcast-notes — 小宇宙→Markdown，阿里百炼 ASR（Paraformer-v2/Qwen3-ASR/Fun-ASR），¥0.43/90 分钟。
🔗 github.com/weisi-gu/xiaoyuzhou-podcast-notes
podcli MCP — 视频→爆款时刻→短视频+烧录字幕，人脸追踪，4 字幕样式。NarrateAI — 配音 11+ 语言，批量处理。附录：通用工具索引资源说明链接AgentSkillsHub117K+ Skill/MCP，10 维评分，8h 更新agentskillshub.topSkill of Skills945 Skill 排名，152 Curatedgithub.com/the911fund/skill-of-skillsAwesome Agent Skill598 SKILL.md 手册+安装 CLIgithub.com/charlieviettq/awesome-agent-skillClaude-Skills Library339 生产级 Skill，17 领域github.com/borghei/Claude-SkillsAgent LeaderboardAgent 生态排行榜，日更github.com/jaychempan/Agent-Leaderboardlinuxdo-awesome-skillsLinux.do 社区 Skills 导航github.com/jochne/linuxdo-awesome-skills

          
        
                

                预览时标签不可点