# TOOLS.md - Local Notes

Skills define _how_ tools work. This file is for _your_ specifics - the stuff that's unique to your setup.

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

### 数据目录(换电脑时需迁移)

- **杂志资料OCR**: `D:\杂志资料`(1086 MB / 1450文件,审计杂志文章OCR结果,knowledge/知识库的外部参考数据源)
- **备份规则**: 换新电脑时从旧D盘拷贝到新D盘根目录,路径保持一致

- Executable: `D:\dwaw\draw.io\draw.io.exe` (v30.0.1)
- CLI export: `& "D:\dwaw\draw.io\draw.io.exe" -x -f png -e -b 10 -o <output> <input.drawio>`
- Skill: `D:\openclaw-workspace\skills\drawio\SKILL.md`

## 微信文章爬取技巧

- **微信公众号文章必须用移动端User-Agent**,否则微信返回JS渲染空壳
- 推荐User-Agent:`Mozilla/5.0 (Linux; Android 13; SM-S9080) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.230 Mobile Safari/537.36 MicroMessenger/8.0.47`
- 使用方式:`python requests.get(url, headers={'User-Agent': '...'})`
- 只抓标题/描述:从HTML提取 `var msg_title`, `var msg_desc` 变量
- 抓全文:从HTML提取 `id="js_content"` 或 `class="rich_media_content"` 的innerHTML
- 注意:微信文章正文默认 `display:none`,需要JS渲染才能显示,但移动端User-Agent请求时服务器返回的HTML中内容已在`rich_media_content` div中

## 标书模板配置(已确认)

- **配色**:深蓝#0A1F3F + 青绿#1A5C6E + 铜金#C5955C + 暖灰#F5F2EC
- **封面**:A4 300dpi (2480x3508),Pillow逐像素绘制,微软雅黑字体
- **流程图**:draw.io scale 8 (≈350dpi, 2972x5816px)
- **字体**:标题微软雅黑、正文宋体、表格微软雅黑
- **页边距**:上2.5 下2 左2.8 右2.8 cm
- **表格**:深蓝表头+金字,暖灰隔行,金色边框
- **模板文件**:`D:\openclaw-workspace\bid_aba\融策标书模板_v2_高级版.docx`
- **生成脚本**:`D:\openclaw-workspace\scripts\标书模板生成_v2.py`

## dashi-ppt 技能（AI生成可编辑PPT）

- **技能路径**: `~/.openclaw/skills/dashi-ppt/`（v0.4.0）
- **运行时**: `skills/dashi-ppt/project/`，首次用 `npm install --include=dev`（必须带 dev，否则缺 tsx/esbuild/playwright-core，渲染报错）
- **⚠️ openssl 依赖（关键坑）**: 预览服务(preview:start)和导出(export:pptx)都要 HTTPS 自签证书，需要 openssl。本机 PATH 没有 openssl，但 miniconda 里有：
  - `C:\Users\scrccpa\miniconda3\envs\paddleocr\Library\bin\openssl.exe`（OpenSSL 3.5.7）
  - **必须设环境变量** `OPENSSL_PATH` 指向它，否则预览/导出全部失败（报 "Preview server exited before it became ready"）
- **导出浏览器**: Edge 已装，playwright 用 `channel: 'msedge'` 可截图/导出
- **无 bash/git**: 官方 `render_goal_deck.sh` 跑不了，用 npm 脚本手动串（见下）
- **端到端流程**（本机验证可用 2026-07-15）:
  ```
  # 1. 选页
  node <skill>/project/scripts/layout-query.mjs --theme theme07 --limit 16
  node <skill>/project/scripts/inspect-layout.mjs --compact <layout...>
  # 2. 写 output/<deck>/goal.json（slides[].layout+props，封面只从 page001-005 选1个，layout不重复）
  # 3. props安全化 + 校验 + 渲染
  npm --prefix <skill>/project run props:safe -- --goal <goal.json> --write
  npm --prefix <skill>/project run validate:goal-spec -- <goal.json>
  npm --prefix <skill>/project run render:goal -- <goal.json> <deck>/ppt/index.html
  npm --prefix <skill>/project run validate:swiss -- <deck>/ppt/index.html
  npm --prefix <skill>/project run validate:goal-copy -- <goal.json> <deck>/ppt/index.html
  # 4. 预览（要 OPENSSL_PATH）→ http://127.0.0.1:<5200-5999>/
  npm --prefix <skill>/project run preview:start -- <deck>/ppt 5273
  # 5. 导出可编辑PPTX（要 OPENSSL_PATH，脚本直调不需先起预览）
  node <skill>/project/scripts/export-pptx.mjs <deck>/ppt <out.pptx>
  ```
- **实测成本参考**: 8页 theme07 → HTML 456KB / PPTX 2.26MB / 241个可编辑文本run
- **主题**: theme01-12，审计/调研类用 theme07冷白调研风、theme05色谱图表风、theme06深色图谱风

## Token预算工具

- **预算估算**: `scripts/token_budget.py`
  ```bash
  # 估算单个文件
  python scripts/token_budget.py --files "报告.docx" --task "分析" --reasoning
  
  # 估算整个目录
  python scripts/token_budget.py --dir "projects/某项目/raw_data/" --task "生成报告"
  
  # 超阈值交互确认
  python scripts/token_budget.py --dir "raw_data/" --task "ocr" --confirm --threshold 50000
  
  # JSON输出（给其他脚本调用）
  python scripts/token_budget.py --files "1.pdf" --json
  ```

- **费用守卫**: `scripts/deepseek_cost_guard.py`
  ```bash
  # 初始化配置
  python scripts/deepseek_cost_guard.py init
  
  # 检查今日费用（每次心跳自动执行）
  python scripts/deepseek_cost_guard.py check
  
  # 查看昨日日报
  python scripts/deepseek_cost_guard.py daily
  
  # 查看限额配置
  python scripts/deepseek_cost_guard.py limit
  ```
  配置: `config/cost_guard.json`（¥100/天, 70%预警, 90%熔断）

- **Token 追踪**: `scripts/token_tracker.py`
  ```bash
  python scripts/token_tracker.py today
  python scripts/token_tracker.py summary --days 7
  python scripts/token_tracker.py snapshot -c 15000 -n "任务名"
  ```
  存储: `logs/token_usage.jsonl`

- **API 限流**: `scripts/api_guard.py`
  ```python
  from api_guard import guarded_chat_completion, batch_process
  
  # 带熔断的单次调用
  response = guarded_chat_completion(model="deepseek-v4-flash", messages=[...])
  
  # 带限流的批量处理
  results = batch_process(items, processor_func, model="flash", batch_size=10, delay_sec=1)
  ```

- **Spawn 安全**: `scripts/spawn_guard.py`
  ```python
  from spawn_guard import safe_spawn, validate_spawn_params
  
  # 自动设置超时
  params = safe_spawn(task="OCR分析", model="deepseek-v4-flash")
  # → 自动设置 runTimeoutSeconds=600, cleanup="delete"
  
  # 参数验证
  ok, msg = validate_spawn_params(kwargs)
  ```

- **工作流集成**: `scripts/workflow_with_budget.py`
  ```python
  from workflow_with_budget import check_budget, before_ocr, before_report
  
  # 通用检查
  ok, estimate = check_budget(
      files=["data.xlsx"],
      task="分析",
      reasoning=True,
      threshold=50000,
      auto_confirm=True
  )
  
  # 快捷函数
  if before_ocr(["scan1.pdf", "scan2.pdf"]):
      run_ocr()
  
  if before_report(["findings.json"], reasoning=True):
      generate_report()
  ```

  ```

- **审计黑板集成**: `audit-blackboard/launch.py` 和 `orchestrate.py` 已内置预算检查
  - `launch.py` Step 0: 自动检查 raw_data 目录token预算
  - `orchestrate.py` prepare: 检查数据目录预算
  - `orchestrate.py` collect: 大量findings时提示预算风险

### ⚠️ DeepSeek 直连 provider 已移除
旧key `sk-4253...31f7` 已失效(401)，现通过 `custom-cbwyy-top-v1`（cbwxy.top代理）走DeepSeek模型。如需直连DeepSeek，找平头哥要新key后加到 models.json。

### ⚠️ Qwen-VL 图片分析规则
涉及 `qwen-vl-max` 的图片/PDF分析，必须先询问用户确认，不得自动调用。

- **默认阈值配置**:
  | 任务类型 | 阈值(token) | 默认模型 |
  |---------|------------|---------|
  | OCR | 100,000 | deepseek-chat |
  | Embedding | 500,000 | deepseek-chat |
  | 生成报告 | 100,000 | deepseek-reasoner |
  | 分析 | 50,000 | deepseek-reasoner |
  | 翻译 | 50,000 | deepseek-chat |
  | 问答 | 30,000 | deepseek-chat |
  | 总结 | 30,000 | deepseek-chat |
  | 提取 | 20,000 | deepseek-chat |

- **配色**:深蓝#0A1F3F + 青绿#1A5C6E + 铜金#C5955C + 暖灰#F5F2EC
- **封面**:A4 300dpi (2480x3508),Pillow逐像素绘制,微软雅黑字体
- **流程图**:draw.io scale 8 (≈350dpi, 2972x5816px)
- **字体**:标题微软雅黑、正文宋体、表格微软雅黑
- **页边距**:上2.5 下2 左2.8 右2.8 cm
- **表格**:深蓝表头+金字,暖灰隔行,金色边框
- **模板文件**:`D:\openclaw-workspace\bid_aba\融策标书模板_v2_高级版.docx`
- **生成脚本**:`D:\openclaw-workspace\scripts\标书模板生成_v2.py`

## 财政监督检查模型 Skill

- **Skill**: `fiscal-supervision-model`
- **路径**: `C:\Users\scrccpa\.openclaw\skills\fiscal-supervision-model\SKILL.md`
- **用途**: 财政监督检查/财会监督专项检查数据标准、识别规则库、疑点分析、现场核查任务、资料补充清单、问题底稿初稿。
- **触发说法**: "调用财政监督检查模型""用财会监督模型跑疑点""按交通厅项目生成识别规则""导入数据跑财政监督检查疑点"。
- **核心引用**:
  - `references/data-standard.md`：数据模板和字段标准
  - `references/rule-library-v1.md`：首批30条识别规则
  - `references/output-spec.md`：Excel输出物规范

## 模型路由方案 v4.2(2026-07-15 14模型联合评审修订)

> v4.1 经 14 模型联合评审，路由逻辑自身无异议。修订集中在容灾架构和数据合规。

### v4.1 → v4.2 修订要点
| 修订 | 触发 | 严重程度 |
|:--|:--|:--|
| 代理单点故障方案升级 | 13/14 模型投票 | 🔴 |
| deepseek 直连逃生通道已配置 | 8/14 模型建议 | ✅ |
| 数据合规风险标注 | 5/14 模型指出 | 🔴 |
| 高风险任务证据链约束 | 3/14 模型建议 | 🟡 |
| 串标分析路由维持 v4-pro | 1/14 异议,13/14 同意 | ✅ 维持 |

### 14模型投票速查
| 共识项 | 投票比 | 结论 |
|:--|:--|:--|
| 代理单点故障是最致命问题 | 13/14 | ✅ 已配直连逃生(depseek-direct) |
| 政府数据通过第三方代理有合规风险 | 5/14 | ⚠️ 需平头哥判断 |
| 一个直连通道不够,关键模型也需直连 | 8/14 | 📋 需 Anthropic 官网 key |
| opus≤2次/项目配额合理 | 13/14 | ✅ 维持 |
| 串标用 v4-pro 合适 | 13/14 | ✅ 维持(v4-pro带推理链) |
| 路由逻辑(错误代价+上下文窗口)正确 | 14/14 | ✅ 无异议 |

> 第一性原理:路由依据不是「做什么」(读/做/想/审),而是「错了要付出什么代价」。
> 跟审计风险导向方法论同构--不是每笔分录都查,而是风险高的重点查。
> **三优先原则: 安全第一 → 稳定第二 → 效率第三**

### 13模型优劣势速查

| 模型 | 核心优势 | 核心劣势 | 审计场景定位 |
|:--|:------|:------|:----------|
| **deepseek-v4-flash** | 免费·快·代码·日常 | 深度不够·中文不细腻 | 🔧 日常工具人 |
| **qwen3.7-plus** | 中文原生最强·公文·图片 | 英文弱·创意一般 | 🇨🇳 中文笔杆子 |
| **deepseek-v4-pro** | 推理链·数据核查·可控 | 无图片·推理token消耗 | 🧮 数据核查员 |
| **claude-fable-5** | 顾问级建议·快·缓存高 | 不执行不终审 | 🟡 军师参谋 |
| **claude-sonnet-5** | 长文细腻·合规·逻辑严密 | 无图片·中价 | 🎯 合规审查官 |
| **gpt-5.5** | 英语母语·读者视角·表达 | 无图片·中价 | ✏️ 英文润色师 |
| **gpt-5.6-luna** | 创意·长文·图片·细腻 | 中价·定位泛 | 🌙 创意总监 |
| **gpt-5.6-sol** | 分析·推理·结构化·图片 | 中价·定位泛 | ☀️ 逻辑分析员 |
| **gpt-5.6-terra** | 综合·通用·全面·图片 | 中价·定位泛 | 🌍 全能审查员 |
| **claude-opus-4-8** | 压舱石·最可靠·致命纠错 | 高价·慢 | 🔬 最终签字人 |
| **gemini-3.1-pro-preview** | **1M+上下文**·多模态·推理强 | 预览版不稳定·中文略弱 | 🐘 长文档专家 |
| **gpt-image-2** | 生图专用 | 只能生图 | 🎨 画师 |
| **doubao-seed-2.0-lite** | 国产·信创·合规 | 能力弱 | 📎 合规备胎 |

### 关键决策依据：每个模型该做什么

**错误代价六级 + 上下文窗口双重路由**

v4.1 新增「上下文窗口」维度——1M+ 上下文的 gemini 能一次处理整本账套，这是独门优势。

```
错误代价 ~0     错误代价低      [咨询层]       错误代价中       错误代价高         错误代价致命
(错了重来)    (改两行)      (方向选错)     (重跑一遍)     (改半天)          (吊销执照)
      │             │              │               │               │                  │
   v4-flash    qwen3.7-plus     fable-5        v4-pro        claude-sonnet-5    claude-sonnet-5
                            ┌──────────────┤     + gemini        + gpt-5.5/5.6     + gpt-5.5/5.6
                            │ (长文档/大数据)│  (长文档推理)     + gemini(长文档)  + opus-4-8 终审
                          gemini预筛选      gemini批处理

咨询层:方向选错代价比「改两行」大、比重跑一遍小。做决定前先问 fable-5。
升级条件:错误代价不确定 → 向上一级,宁高勿低

上下文窗口补充:若文档 >128K token → 所有路由跳过中间层,直接走 gemini(1M+上下文独家)
```

### 任务类型 → 默认模型 + 错误代价升级

> 任务类型给快速起点,错误代价+上下文窗口决定最终路由。

#### 📖 读(默认 v4-flash)
| 场景 | 默认 | 错误代价升级条件 | 升到 |
|:--|:--|:--|:--|
| 普通文档/代码/日志/检索 | v4-flash | - | - |
| 图片/扫描件/表格截图 | **qwen3.7-plus** | 涉及关键证据 → | sonnet-5 |
| 英文图文/外文扫描件 | **gemini-3.1-pro-preview** | 涉及关键证据 → | sonnet-5 + gemini 交叉 |
| 超长文档(>128K token) | **gemini-3.1-pro-preview** | 致命级 → | gemini + opus-4-8 双签 |
| 合同/法规/政策 | claude-sonnet-5 | 超长合同(>128K) → | gemini-3.1-pro-preview 全文读 |
|  |  | 重大合同条款纠纷 → | opus-4-8 |

#### ✍️ 做(默认 qwen3.7-plus)
| 场景 | 默认 | 错误代价升级条件 | 升到 |
|:--|:--|:--|:--|
| 数据整理/脚本/小工具 | v4-flash | - | - |
| 报告初稿/公文/标书 | **qwen3.7-plus** | 正式交付客户 → | gpt-5.5 表达审查 |
| 标书最终版 | qwen3.7-plus | 废标=丢项目 → | sonnet-5 逻辑 + gpt-5.5 表达 双签 |
| 审计报告正式出具 | qwen3.7-plus | 签字责任 → | sonnet-5 复核 + opus-4-8 终审 |
| 创意文案/宣传内容 | **gpt-5.6-luna** | 品牌形象 → | gpt-5.5 视觉建议 |
| 封面/PPT | guizang/huashu(本地) | 品牌形象 → | gpt-5.5 视觉建议 |
| 配图 | gpt-image-2 | - | - |
| 微信/日常回复 | v4-flash | - | - |

#### 🧠 想(默认 v4-pro，深度分析直通海外大模型)
| 场景 | 默认 | 错误代价升级条件 | 升到 |
|:--|:--|:--|:--|
| 探索性分析/试方向 | v4-flash | 方向不确定 → | fable-5 咨询层 |
| 数据核查/金额追踪 | **v4-pro** | 定性结论 → | sonnet-5 交叉验证 |
| **深度分析/复杂业务** | **sonnet-5 🎯** | 审计报告级 → | sonnet + opus 双签 |
| 大数据量分析(一次塞入) | **gemini-3.1-pro** | 定性结论 → | sonnet + gemini 交叉 |
| 串标围标分析 | **v4-pro** | 正式结论 → | sonnet + opus 铁证 |
| 风险判断/合规研判 | **sonnet-5** | 超长法规 → | gemini 全文读 |
| 方案对比/路线选择 | **fable-5 咨询层** | 影响方向 → | sonnet-5 判断 |
| 架构设计/工具选型 | **fable-5 咨询层** | 分歧大 → | sonnet-5 |
| 任务拆解/流程设计 | v4-pro / fable-5 | - | - |

> ⚡ **深度分析直通规则**：定性判断、风险识别、模式发现、关联挖掘、多维度交叉分析、政策解读、方案设计 → **直接走 sonnet-5**，不经过 v4-flash 或 v4-pro 中转。理由：深度分析错了要重跑整条链路，代价本来就是「高」级。

#### 🔍 审(默认 sonnet-5 逻辑 + gpt-5.5 表达 双签)
| 场景 | 默认 | 错误代价升级条件 | 升到 |
|:--|:--|:--|:--|
| 中文错别字/格式检查 | **qwen3.7-plus** | - | - |
| 金额追踪/数据核验 | v4-pro | - | - |
| 细节审查(合规/逻辑/遗漏) | claude-sonnet-5 | - | - |
| 表达审查(可读性/说服力/英文) | gpt-5.5 / gpt-5.6-luna | - | - |
| 长文档复核(>50页) | **gemini-3.1-pro-preview** | 审计报告级别 → | sonnet-5 + gemini 交叉 |
| 跨文档交叉验证(多文件) | **gemini-3.1-pro-preview** | 致命级 → | gemini + opus-4-8 双签 |
| 关键结论验收 | claude-sonnet-5 / gpt-5.6-sol | 审计报告级别 → | opus-4-8 |
| 重大定稿终审 | opus-4-8 / gpt-5.6-terra | - | - |

### 双人复核制(审层核心机制, v4.1 加入 gemini 长文档复核)

```
                 提交物(报告/标书/结论)
                        │
          ┌─────────────┼─────────────┬──────────────┐
          ▼             ▼             ▼              ▼
   qwen3.7-plus   claude-sonnet-5   gpt-5.5    gemini-3.1-pro-preview
   错别字·格式      逻辑·合规·数据    表达·读者体验   长文档完整性·跨文档一致性
   (中文工具)     (细节审查)      (表达审查)     (大上下文扫描)
          │             │             │              │
          └─────────────┼─────────────┼──────────────┘
                        ▼             ▼
                   审查意见汇总     gemini长文档审查报告
                        │
                 ┌──────┴──────┐
                 ▼              ▼
            低代价交付      高/致命代价交付
           (日常报告)     (审计报告/标书)
                 │              │
            qwen 修正       + opus-4-8 终审签字
                            + gemini 交叉验证(超长文档)
```

### Fable-5 咨询层(独立路由层)
- **定位**:独立顾问层,**不做执行,不做终审,只给建议**
- **错误代价**:介于「低」和「中」之间--方向选错了,代价比改两行大,比重跑一遍小
- **触发时机**:做决策**之前**,不是「写完了复核」
- **与 Sonnet 的区别**:Fable 给建议(「A方案比B好,因为...」),Sonnet 下判断(「A方案逻辑不成立」)
- **成本优势**:缓存命中率极高,重复评审场景几乎零成本
- **升级规则**:建议分歧大或影响项目方向 → 升 sonnet-5 做正式判断
- **典型场景**:方案对比、架构选型、路线选择、风险影响评估

### Gemini 长文档层(v4.1 新增独立路由层)
- **定位**:长文档/大数据量专用通道,**1M+上下文窗口独家优势**
- **触发时机**:文档 >128K token 或需要跨文档交叉验证时
- **与 Sonnet 的区别**:Sonnet 读不了 >200K token 的文档,gemini 能一次读完
- **成本**:预览版,注意 API 稳定性;正式结论仍需 sonnet/opus 交叉
- **升级规则**:
  - 长文档读完了仍有疑问 → sonnet-5 做局部重点审查
  - 长文档结论用于正式报告 → sonnet-5 + gemini 交叉验证
  - 长文档结论用于审计报告 → opus-4-8 终审签字
- **降级策略**(gemini 预览版不可用):
  - gemini 超时/403/404 → 自动降级到 **sonnet-5 分段读**
  - 分段策略:每 150K token 切一段,sonnet 逐段处理 → 拼接摘要
  - 降级时告知用户「已从 gemini 长文档降级为 sonnet 分段模式,完整性可能下降」
- **典型场景**:整本合同册、全套招标文件、全年账套、多期审计报告对比

### 升级规则速查

| 触发信号 | 动作 |
|:--|:--|
| flash 结果存疑 | → 升一级(qwen 中文方向 / v4-pro 推理方向) |
| v4-pro 推理链不完整 | → sonnet-5 / gemini(长文档场景) |
| 文档 >128K token | → **直接走 gemini 长文档层** |
| 结论将写入正式报告 | → sonnet-5 交叉验证 |
| 结论影响定案/行政处罚 | → sonnet-5 + opus-4-8 |
| 涉及法律/合规/重大资金 | → sonnet-5 起步,报告出具前 opus 签字 |
| 方案/架构/工具选择 | → fable-5 咨询层评审 |
| 长文档结论用于正式交付 | → gemini 初读 + sonnet 局部复核 + opus 终审 |
| 错误代价不确定 | → **向上一级**(宁高勿低) |

### 成本控制底线

```
v4-flash + qwen3.7-plus              ≥ 70% 调用量(免费~极低)
v4-pro + fable-5                     ≤ 15% 调用量(低价)
gemini-3.1-pro-preview               ≤ 5%  调用量(预览版,仅长文档场景)
sonnet-5 + gpt-5.5 + gpt-5.6系列    ≤ 8%  调用量(中价,含深度分析直通)
opus-4-8                             ≤ 2次/项目(高价)
```

### Fallback 链(会话默认,已加入 gemini)
```
primary: custom-cbwyy-top-v1/deepseek-v4-flash
fallbacks: [deepseek-v4-pro, gemini-3.1-pro-preview, claude-sonnet-5]
```

### 注意
- V4 Pro 含 reasoning tokens,注意 token 消耗
- cbwyy.top 代理偶有临时抽风(403),重试即可恢复
- 心跳/定时任务 必须用 v4-flash
- **gemini-3.1-pro-preview 是预览版**,API 可能不稳定,正式结论必须走 sonnet/opus 交叉验证
- 错误代价路由的核心判断依据:**答错了,最坏结果是什么?**
  - ~0 → flash | 低 → qwen | 中 → pro | 高 → sonnet+gpt-5+gpt-5.6系列 | 致命 → opus
  - 超长文档(>128K token) → **先走 gemini 长文档层**再按错误代价升级
- 每日模型健康检查: `python scripts/model_health_check.py`

### 安全·效率·稳定三优先规则（v4.3 新增）

#### 🔒 安全优先
| 规则 | 触发 | 动作 |
|:--|:--|:--|
| 敏感项目数据隔离 | 关键词「经责」「处级」「国企」「补贴」「纪检」+ 处理客户数据 | 仅 deepseek/qwen/doubao |
| 涉密数据不进云端 | 「涉密」「纪检移交」「国an」 | 离线模式，拒绝调用任何模型 |
| API Key 零外泄 | 任何请求 | 模型回复中不显示 API Key，仅用 `__REDACTED__` |
| 审计结论不可伪造 | 生成审计问题底稿 | 强制标注「AI辅助生成，需人工复核确认」 |

#### ⚡ 稳定优先
| 规则 | 触发 | 动作 |
|:--|:--|:--|
| 超时熔断 | 单次请求 >60 秒 | 自动重试 1 次 → 仍超时则降级到备选模型 |
| 连续故障隔离 | 同一模型连续 3 次失败 | 标记为故障，24 小时内跳过该模型 |
| Gemini 降级 | gemini 返回 403/404/超时 | 自动退到 sonnet-5 分段读 |
| 代理全挂逃生 | 所有 cbwyy.top 模型不可用 | 切 deepseek-direct 直连 |
| 健康检查告警 | 每日 10:00 | ≥3 模型故障 → 推送通知 |

#### 🚀 效率优先
| 规则 | 触发 | 动作 |
|:--|:--|:--|
| 探索阶段用最快 | 试方向/快速验证 | v4-flash，3 秒内返回 |
| 深度分析直通 | 定性判断/风险识别/复杂业务 | 直接 sonnet-5，不中转 |
| 同类任务缓存复用 | 重复评审场景 | 优先走 fable-5 缓存层 |
| 长文档不走分段 | >128K token | gemini 一次读完，不分段（除非降级） |

### 代理容灾与稳定性加固(v4.1.1)

**所有 13 个模型都通过 cbwyy.top 代理。代理一挂,全部瘫痪。**

#### 三级容灾

| 级别 | 场景 | 动作 |
|:--|:--|:--|
| **L1** | 代理瞬断(403/超时) | 重试 3 次 → fallback 链轮替（但都走同一代理,效用有限） |
| **L2** | gemini 预览版不可用 | 自动降级到 **sonnet-5 分段读**（每段 ≤150K token）→ 告知用户 |
| **L3** | 代理全面瘫痪 | **deepseek-direct 直连逃生（✅ 已配置）** |
| **L4** | 代理 + 直连全挂 | 🆘 人工介入 + 本地规则引擎（离线模式） |

#### 数据合规风险提醒（✅ 已决策）

**策略：海外模型为主，敏感项目数据限用国内模型**

| 数据类型 | 模型策略 | 可用模型 |
|:--|:--|:--|
| 日常工作（方案撰写/报告复核/投标方案/案例分析/知识库/案例库） | 海外模型为主 | 全14模型 |
| 常规审计项目数据（绩效评价/资产清查/工程咨询等） | 海外模型为主 | 全14模型 |
| 敏感审计项目数据（经责·县处级+/专项补贴/国企审计） | 限用国内模型 | deepseek-v4-flash/pro、qwen3.7-plus、doubao |
| 极端敏感（涉密/纪检移交数据） | 仅本地处理 | 离线模式，不调任何云端模型 |

关键区分：融策**自身**的分析、写作、研究 → 走海外模型不受限；被审计单位的**原始数据**在敏感项目中 → 限国内模型。

#### DeepSeek 直连逃生通道（✅ 已配置）
```
Provider: deepseek-direct | Model: deepseek-chat | Base: https://api.deepseek.com/v1
不经过 cbwyy.top 代理 | Fallback 链末位 | 代理全挂时启动
```

#### 健康检查
```bash
python scripts/model_health_check.py           # 全量 ping
python scripts/model_health_check.py --json    # JSON 输出
python scripts/model_health_check.py --alert   # 仅输出告警
```
- 频率: 每日 10:00 自动执行
- 告警: ≥10 模型失败 = 疑似代理故障 | gemini 连续3天失败 = 自动降级

## 模型清单(已配置)

### config 路径
`C:\Users\scrccpa\.openclaw\openclaw.json`

| model id | provider id | API Type | baseUrl | Input |
|:--|:--|:--|:--|:--|
| deepseek-v4-flash / deepseek-v4-pro | custom-cbwyy-top-v1 | openai-completions | https://cbwyy.top/v1 | text+image |
| qwen3.7-plus | custom-cbwyy-qwen | openai-completions | https://cbwyy.top/v1 | text+image |
| claude-fable-5 | custom-cbwyy-fable | anthropic-messages | https://cbwyy.top | text |
| claude-sonnet-5 | custom-cbwyy-claude | anthropic-messages | https://cbwyy.top | text |
| claude-opus-4-8 | custom-cbwyy-opus | anthropic-messages | https://cbwyy.top | text |
| gpt-5.5 | custom-cbwyy-gpt55 | openai-completions | https://cbwyy.top/v1 | text |
| **gpt-5.6-luna** | **custom-cbwyy-luna** | **openai-completions** | **https://cbwyy.top/v1** | **text+image** |
| **gpt-5.6-sol** | **custom-cbwyy-sol** | **openai-completions** | **https://cbwyy.top/v1** | **text+image** |
| **gpt-5.6-terra** | **custom-cbwyy-terra** | **openai-completions** | **https://cbwyy.top/v1** | **text+image** |
| gpt-image-2 | custom-cbwyy-image | openai-completions | https://cbwyy.top | text+image |
| doubao-seed-2.0-lite | custom-cbwyy-doubao | openai-completions | https://cbwyy.top/v1 | text |
| **gemini-3.1-pro-preview** | **custom-cbwyy-gemini** | **openai-completions** | **https://cbwyy.top/v1** | **text+image** |
| **deepseek-chat** 🔑 | **deepseek-direct** | **openai-completions** | **https://api.deepseek.com/v1** | text |

### 环境变量 Key 映射(已弃用,全部转为明文)

> i️ 2026-07-11 起所有 API Key 已从 env:// 引用转为 openclaw.json 明文。
> Windows 上 env:// 在进程重启时不刷新,为了稳定性放弃 env:// 方案。
> 安全保证:.gitignore 已排除 openclaw.json。
> 注册表 OC_KEY_* 环境变量保留,不影响明文配置。
