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

## 模型路由方案 v4.0(2026-07-08 错误代价路由)

> 第一性原理:路由依据不是「做什么」(读/做/想/审),而是「错了要付出什么代价」。
> 跟审计风险导向方法论同构--不是每笔分录都查,而是风险高的重点查。

### 可用模型一览

| 模型 | provider | 角色 | 成本 | 能力标签 |
|:--|:--|:--|:--|:--|
| **deepseek-v4-flash** | cbwyy-top-v1 | 🔧 ~0代价执行 | 免费 | 快·日常·代码 |
| **qwen3.7-plus** | cbwyy-qwen | 🔧 低代价中文 | 低 | 中文原生·图片输入·公文 |
| **deepseek-v4-pro** | cbwyy-top-v1 | 🧠 中代价分析 | 低 | 深度推理·数据核查 |
| **claude-fable-5** | cbwyy-fable | 🟡 顾问·校验 | 低 | 方案评审·路线对比·快速反馈 |
| **claude-sonnet-5** | cbwyy-claude | 🎯 高代价审查 | 中 | 长文·细腻·合规·双签 |
| **gpt-5.5** | cbwyy-gpt55 | 🎯 高代价表达 | 中 | 英文原生·读者视角·视觉建议 |
| **gpt-5.6-luna** | cbwyy-luna | 🎯 高代价审查 | 中 | 文本·图片·长文·创意 |
| **gpt-5.6-sol** | cbwyy-sol | 🎯 高代价审查 | 中 | 文本·图片·分析·推理 |
| **gpt-5.6-terra** | cbwyy-terra | 🎯 高代价审查 | 中 | 文本·图片·综合·通用 |
| **claude-opus-4-8** | cbwyy-opus | 🔬 致命代价终审 | 高 | 压舱石·最终签字 |
| **gpt-image-2** | cbwyy-image | 🎨 生图 | 专用 | 封面·配图 |
| **doubao-seed-2.0-lite** | cbwyy-doubao | 📎 合规备选 | 低 | 国产·信创 |

### 错误代价六级路由

```
错误代价 ~0     错误代价低      [咨询层]       错误代价中       错误代价高         错误代价致命
(错了重来)    (改两行)      (方向选错)     (重跑一遍)     (改半天)          (吊销执照)
      │             │              │               │               │                  │
   v4-flash    qwen3.7-plus     fable-5        v4-pro        claude-sonnet-5    claude-sonnet-5
                                                                 + gpt-5.5/5.6   + gpt-5.5/5.6
                                                                 + opus-4-8 终审

咨询层说明:方向选错的代价比「改两行」大、比重跑一遍小。
          做决定之前先问 fable-5,比直接升 sonnet 便宜。
升级条件:只要判断「错误代价不确定」→ 向上一级,宁高勿低
`````



### 任务类型 → 默认模型 + 错误代价升级

> 任务类型给一个快速起点,错误代价决定最终路由。

#### 📖 读(默认 v4-flash)
| 场景 | 默认 | 错误代价升级条件 | 升到 |
|:--|:--|:--|:--|
| 普通文档/代码/日志/检索 | v4-flash | - | - |
| 图片/扫描件/表格截图 | **qwen3.7-plus** | 涉及关键证据 → | sonnet-5 |
| 合同/法规/政策 | claude-sonnet-5 | 重大合同条款纠纷 → | opus-4-8 |

#### ✍️ 做(默认 qwen3.7-plus)
| 场景 | 默认 | 错误代价升级条件 | 升到 |
|:--|:--|:--|:--|
| 数据整理/脚本/小工具 | v4-flash | - | - |
| 报告初稿/公文/标书 | **qwen3.7-plus** | 正式交付客户 → | gpt-5.5 表达审查 |
| 标书最终版 | qwen3.7-plus | 废标=丢项目 → | sonnet-5 逻辑 + gpt-5.5 表达 双签 |
| 审计报告正式出具 | qwen3.7-plus | 签字责任 → | sonnet-5 复核 + opus-4-8 终审 |
| 封面/PPT | guizang/huashu(本地)| 品牌形象 → | gpt-5.5 视觉建议 |
| 配图 | gpt-image-2 | - | - |
| 微信/日常回复 | v4-flash | - | - |

#### 🧠 想(默认 v4-pro)
| 场景 | 默认 | 错误代价升级条件 | 升到 |
|:--|:--|:--|:--|
| 探索性分析/试方向 | v4-flash | 方向不确定 → | fable-5 咨询层 |
| 审计分析/数据核查 | **v4-pro** | 定性结论 → | sonnet-5 交叉验证 |
| 串标围标分析 | v4-pro | 出具正式结论 → | sonnet-5 + opus-4-8 铁证确认 |
| 风险判断/合规研判 | claude-sonnet-5 | - | - |
| 方案对比/路线选择 | **fable-5 咨询层** | 影响项目方向 → | sonnet-5 判断 |
| 架构设计/工具选型 | **fable-5 咨询层** | 分歧大 → | sonnet-5 |
| 任务拆解/流程设计 | v4-pro / fable-5 咨询层先行 | - | - |

#### 🔍 审(默认 sonnet-5 逻辑 + gpt-5.5 表达 双签)
| 场景 | 默认 | 错误代价升级条件 | 升到 |
|:--|:--|:--|:--|
| 中文错别字/格式检查 | **qwen3.7-plus** | - | - |
| 金额追踪/数据核验 | v4-pro | - | - |
| 细节审查(合规/逻辑/遗漏)| claude-sonnet-5 | - | - |
| 表达审查(可读性/说服力/英文)| gpt-5.5 / gpt-5.6-luna | - | - |
| 关键结论验收 | claude-sonnet-5 / gpt-5.6-sol | 审计报告级别 → | opus-4-8 |
| 重大定稿终审 | opus-4-8 / gpt-5.6-terra | - | - |

### 双人复核制(审层核心机制)

```
                 提交物(报告/标书/结论)
                        │
          ┌─────────────┼─────────────┐
          ▼             ▼             ▼
   qwen3.7-plus   claude-sonnet-5   gpt-5.5
   错别字·格式      逻辑·合规·数据    表达·读者体验
   (中文工具)     (细节审查)      (表达审查)
          │             │             │
          └─────────────┼─────────────┘
                        ▼
                   审查意见汇总
                        │
                 ┌──────┴──────┐
                 ▼              ▼
            低代价交付      高/致命代价交付
           (日常报告)     (审计报告/标书)
                 │              │
            qwen 修正       + opus-4-8 终审签字
```

### Fable-5 咨询层(独立路由层)
- **定位**:独立顾问层,**不做执行,不做终审,只给建议**
- **错误代价**:介于「低」和「中」之间--方向选错了,代价比改两行大,比重跑一遍小
- **触发时机**:做决策**之前**,不是「写完了复核」
- **与 Sonnet 的区别**:Fable 给建议(「A方案比B好,因为...」),Sonnet 下判断(「A方案逻辑不成立」)
- **成本优势**:缓存命中率极高,重复评审场景几乎零成本
- **升级规则**:建议分歧大或影响项目方向 → 升 sonnet-5 做正式判断
- **典型场景**:方案对比、架构选型、路线选择、风险影响评估

### 升级规则速查

| 触发信号 | 动作 |
|:--|:--|
| flash 结果存疑 | → 升一级(qwen 中文方向 / v4-pro 推理方向) |
| v4-pro 推理链不完整 | → sonnet-5 |
| 结论将写入正式报告 | → sonnet-5 交叉验证 |
| 结论影响定案/行政处罚 | → sonnet-5 + opus-4-8 |
| 涉及法律/合规/重大资金 | → sonnet-5 起步,报告出具前 opus 签字 |
| 方案/架构/工具选择 | → fable-5 咨询层评审 |
| 错误代价不确定 | → **向上一级**(宁高勿低) |

### 成本控制底线

```
v4-flash + qwen3.7-plus              ≥ 80% 调用量(免费~极低)
v4-pro + fable-5                     ≤ 15% 调用量(低价)
sonnet-5 + gpt-5.5 + gpt-5.6系列    ≤ 5%  调用量(中价)
opus-4-8                             ≤ 3次/项目(高价)
```

### Fallback 链(会话默认)
```
primary: custom-cbwyy-top-v1/deepseek-v4-flash
fallbacks: [deepseek-v4-pro, claude-sonnet-5]
```

### 注意
- V4 Pro 含 reasoning tokens,注意 token 消耗
- cbwyy.top 代理偶有临时抽风(403),重试即可恢复
- 心跳/定时任务 必须用 v4-flash
- 错误代价路由的核心判断依据:**答错了,最坏结果是什么?**
  - ~0 → flash | 低 → qwen | 中 → pro | 高 → sonnet+gpt-5+gpt-5.6系列 | 致命 → opus

## 模型清单(已配置)

### config 路径
`C:\Users\scrccpa\.openclaw\openclaw.json`

| model id | provider id | API Type | baseUrl | Input |
|:--|:--|:--|:--|:--|
| deepseek-v4-flash / deepseek-v4-pro | custom-cbwyy-top-v1 | openai-completions | https://cbwyy.top/v1 | text |
| qwen3.7-plus | custom-cbwyy-qwen | openai-completions | https://cbwyy.top/v1 | text+image |
| claude-fable-5 | custom-cbwyy-fable | anthropic-messages | https://cbwyy.top | text |
| claude-sonnet-5 | custom-cbwyy-claude | anthropic-messages | https://cbwyy.top | text |
| claude-opus-4-8 | custom-cbwyy-opus | anthropic-messages | https://cbwyy.top | text |
| gpt-5.5 | custom-cbwyy-gpt55 | openai-completions | https://cbwyy.top/v1 | text |
| **gpt-5.6-luna** | **custom-cbwyy-luna** | **openai-completions** | **https://cbwyy.top/v1** | **text+image** |
| **gpt-5.6-sol** | **custom-cbwyy-sol** | **openai-completions** | **https://cbwyy.top/v1** | **text+image** |
| **gpt-5.6-terra** | **custom-cbwyy-terra** | **openai-completions** | **https://cbwyy.top/v1** | **text+image** |
| gpt-image-2 | custom-cbwyy-image | openai-completions | https://cbwyy.top/v1 | text+image |
| doubao-seed-2.0-lite | custom-cbwyy-doubao | openai-completions | https://cbwyy.top/v1 | text |

### 环境变量 Key 映射(已弃用,全部转为明文)

> i️ 2026-07-11 起所有 API Key 已从 env:// 引用转为 openclaw.json 明文。
> Windows 上 env:// 在进程重启时不刷新,为了稳定性放弃 env:// 方案。
> 安全保证:.gitignore 已排除 openclaw.json。
> 注册表 OC_KEY_* 环境变量保留,不影响明文配置。
