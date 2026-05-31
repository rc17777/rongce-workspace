# TOOLS.md - Local Notes

Skills define _how_ tools work. This file is for _your_ specifics — the stuff that's unique to your setup.

## What Goes Here

Things like:

- Camera names and locations
- SSH hosts and aliases
- Preferred voices for TTS
- Speaker/room names
- Device nicknames
- Anything environment-specific

## Examples

```markdown
### Cameras

- living-room → Main area, 180° wide angle
- front-door → Entrance, motion-triggered

### SSH

- home-server → 192.168.1.100, user: admin

### TTS

- Preferred voice: "Nova" (warm, slightly British)
- Default speaker: Kitchen HomePod
```

## Why Separate?

Skills are shared. Your setup is yours. Keeping them apart means you can update skills without losing your notes, and share skills without leaking your infrastructure.

---

Add whatever helps you do your job. This is your cheat sheet.

<!-- clawx:begin -->
## ClawX Tool Notes

### uv (Python)

- `uv` is bundled with ClawX and on PATH. Do NOT use bare `python` or `pip`.
- Run scripts: `uv run python <script>` | Install packages: `uv pip install <package>`

### Browser

- `browser` tool provides full automation (scraping, form filling, testing) via an isolated managed browser.
- Flow: `action="start"` → `action="snapshot"` (see page + get element refs like `e12`) → `action="act"` (click/type using refs).
- Open new tabs: `action="open"` with `targetUrl`.
- To just open a URL for the user to view, use `shell:openExternal` instead.
<!-- clawx:end -->

---

## 技能分类速查表（2026-05-31）

### 审计工具（17个）🔧
- `audit-anomaly-detect`: 从大量数据中自动发现异常值
- `audit-benford`: 怀疑财务数据造假时检测数字分布异常
- `audit-capa-tracker`: 跟踪审计问题整改状态
- `audit-contract-analyze`: 分析招投标/采购合同合规性
- `audit-data-analyst`: 审计数据分析实战（SQL/Python/异常检测）
- `audit-data-quality`: 审计数据质量检查、清洗前评估
- `audit-evidence-three-point`: 检查审计问题证据是否充分完整
- `audit-knowledge-card`: 项目结束沉淀知识、生成知识卡片
- `audit-law-check`: 检查某项行为是否违反审计/财政法规
- `audit-policy-monitor`: 审计/财政领域最新政策变化监控
- `audit-pricing-monitor`: 两新补贴审计检查商家价格备案真实性
- `audit-report-structured`: 从审计发现汇总表自动生成标准审计报告
- `audit-report-writer`: 审计报告与咨询报告写作辅助
- `audit-scan-to-text`: 扫描件/照片/PDF取证材料转为可编辑文本
- `audit-sop-master`: 不确定底稿字段该怎么填时查SOP规范
- `audit-sql-patterns`: 用SQL对审计数据进行查询分析
- `audit-watchdog`: 快速判断某行为是否触碰审计红线

### 政府审计专项（4个）🏛️
- `bid-collusion-audit`: 串标围标审计（PDF元数据/设备指纹/关系图谱）
- `gov-audit-problem-classify`: 审计发现归类到标准问题类型
- `two-heavy-audit-checklist`: 两重建设项目审计清单
- `two-new-audit-checklist`: 家电以旧换新/数码购新补贴审计清单

### CNKI学术链（8个）📚
- `cnki-search`: 关键词搜索论文
- `cnki-advanced-search`: 高级搜索（作者/期刊/日期/来源类别）
- `cnki-paper-detail`: 提取论文完整详情
- `cnki-parse-results`: 解析搜索结果为结构化数据
- `cnki-navigate-pages`: 翻页/改排序
- `cnki-download`: 下载PDF/CAJ
- `cnki-export`: 导出到Zotero/RIS
- `cnki-journal-search/TOC/index`: 期刊搜索/目录/收录状态

### 企微操作（14个）💼
- `wecom-contact-lookup`: 联系人查找
- `wecom-doc-manager`: 文档管理
- `wecom-edit-todo`: 编辑待办
- `wecom-get-todo-list/detail`: 待办查询
- `wecom-meeting-create`: 会议创建
- `wecom-meeting-manage/query`: 会议管理/查询
- `wecom-msg`: 消息发送
- `wecom-schedule`: 日程管理
- `wecom-smartsheet-data/schema`: 智能表操作

### 文档写作（8个）✍️
- `word-cn-format`: Word中文格式标准化
- `writing-polish`: 中文写作润色
- `copywriting`: 英文营销文案（AIDA/PAS/FAB）
- `khazix-writer`: 公众号长文写作风格
- `academic-writing`: 学术论文写作
- `academic-writing-refiner`: CS顶会论文润色
- `china-contract-review`: 中国合同审查
- `article-illustrator`/`baoyu-article-illustrator`: 文章配图

### 数据分析（5个）📊
- `data-analysis`: 数据分析和可视化
- `aloudata-anomaly-detection`: 指标异常检测
- `analysis-report`: 编排完整数据分析报告
- `forecast-simulation`: 趋势预测/目标缺口/What-if模拟
- `scheduled-report`: 固化为定时报告

### 信息获取（4个）🌐
- `web-content-fetcher`: 网页内容获取（绕反爬）
- `wechat-article-fetcher`: 微信公众号文章抓取
- `pyzhihu-cli`: 知乎CLI操作
- `summarize`: URL/文件摘要

### AI研究辅助（5个）🔬
- `arxiv-search-collector`: arXiv论文收集
- `arxiv-summarizer-orchestrator`: arXiv定期收集+报告编排
- `paper-parse`: 学术论文双模式深度研读
- `paper-reading`: 学术论文深度分析
- `pdf-metadata-extractor`: PDF元数据深度提取

### 系统工具（8个）⚙️
- `clawhub`: 技能市场安装
- `coding-agent`: 编程代理
- `github`: GitHub CLI操作
- `healthcheck`: 系统健康检查
- `auto-updater`: 自动更新
- `skill-creator/vetter/hub-manager`: 技能创建/审查/发布
- `officecli-docx/pptx/xlsx`: Office文档操作（内置）

### 策略咨询（5个）💡
- `mbb-strategist`: McKinsey/BCG/Bain战略框架
- `strategy-advisor`: 战略决策建议
- `brainstorming`: 头脑风暴
- `multi-round-design`: 多轮迭代设计法
- `deep-research`: 深度研究五步工作流

### 待删除冗余（7个）🗑️
- `excel-xlsx` → 保留 `officecli-xlsx`
- `ws-excel` → 保留 `officecli-xlsx`
- `word-docx` → 保留 `officecli-docx`
- `powerpoint-pptx` → 保留 `officecli-pptx`
- `copy-editing` → 保留 `writing-polish`
- `paddle-ocr-audit` → 保留 `audit-scan-to-text`
- `csv-data-summarizer` → 保留 `data-analysis`

---

## 技能设计哲学（2026-05-31）

> 来源：老路《试了十几个AI做PPT的工具，能拿出手的只有一个》

### 核心原则：skill是容器，专业经验才是内容

- **容器谁都能做，里面装什么才决定能不能用。** 不是AI让skill变强，是skill背后的人的专业判断让它变强。
- 归藏的PPT skill厉害，不是因为AI用得好，是因为归藏本人做了十年设计。
- 别人用AI生成PPT → 八胞胎。他用AI按照设计师的标准去做 → 有审美的PPT。

### 四条创建/审核标准

1. **必须有专业经验注入。** 每个skill背后必须有一个明确的人在定义"好的标准长什么样"。
   - audit-data-analyst → 溪石的审计数据分析经验
   - deep-research → 小李的初级分析师方法论+质量门
   - rongce-gov-audit → 融策10+年政府审计经验
   - 纯prompt包装、无专业判断标准的skill → 删除或合并

2. **工具是放大器，你得先有个东西让它放大。** 
   同样的skill装到不同人手里，结果差距不在AI，在使用者有没有自己的专业判断。
   创建skill时同步写清楚"这个skill需要使用者具备什么专业能力"

3. **差异化来自定义标准的能力。** 
   当AI工具人人都在用的时候，"用AI"不是竞争力。
   竞争力是：谁能告诉AI"做到什么程度才叫做好了"。

4. **专业标准不能被AI替代。** 
   AI让执行变快了。但什么是好的，这个判断还得靠人自己长出来。

### 新建技能前必答5问

1. 这个skill背后是谁的专业经验？来源是哪篇文章/哪个专家？
2. "做好了长什么样"——这个标准有没有写进skill？
3. 有没有写死的质量门/人工停点？
4. 和现有技能有没有功能重叠？能不能合并？
5. 使用者需要具备什么基础才能用好这个skill？
