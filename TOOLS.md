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

### 数据目录（换电脑时需迁移）

- **杂志资料OCR**: `D:\杂志资料`（1086 MB / 1450文件，审计杂志文章OCR结果，knowledge/知识库的外部参考数据源）
- **备份规则**: 换新电脑时从旧D盘拷贝到新D盘根目录，路径保持一致

- Executable: `D:\dwaw\draw.io\draw.io.exe` (v30.0.1)
- CLI export: `& "D:\dwaw\draw.io\draw.io.exe" -x -f png -e -b 10 -o <output> <input.drawio>`
- Skill: `D:\openclaw-workspace\skills\drawio\SKILL.md`

## 标书模板配置（已确认）

- **配色**：深蓝#0A1F3F + 青绿#1A5C6E + 铜金#C5955C + 暖灰#F5F2EC
- **封面**：A4 300dpi (2480x3508)，Pillow逐像素绘制，微软雅黑字体
- **流程图**：draw.io scale 8 (≈350dpi, 2972x5816px)
- **字体**：标题微软雅黑、正文宋体、表格微软雅黑
- **页边距**：上2.5 下2 左2.8 右2.8 cm
- **表格**：深蓝表头+金字，暖灰隔行，金色边框
- **模板文件**：`D:\openclaw-workspace\bid_aba\融策标书模板_v2_高级版.docx`
- **生成脚本**：`D:\openclaw-workspace\scripts\标书模板生成_v2.py`

<<<<<<< HEAD
## Token预算工具（守卫脚本在 scripts/guards/）

- **费用守卫** (已修复✅): `scripts/guards/deepseek_cost_guard.py`
  ```bash
  python scripts/guards/deepseek_cost_guard.py check    # 检查今日费用
  python scripts/guards/deepseek_cost_guard.py daily    # 昨日日报
  python scripts/guards/deepseek_cost_guard.py limit    # 查看限额
  ```
  配置: `config/cost_guard.json`（¥100/天, 70%预警, 90%熔断）
  快捷入口: `scripts/deepseek_cost_guard.py`

- **Token 追踪** (已修复✅): `scripts/guards/token_tracker.py`
  ```bash
  python scripts/guards/token_tracker.py today
  python scripts/guards/token_tracker.py summary --days 7
  python scripts/guards/token_tracker.py snapshot -c 15000 -n "任务名"
  ```
  存储: `logs/token_usage.jsonl` | 快捷入口: `scripts/token_tracker.py`

- **Spawn 安全**: `scripts/guards/spawn_guard.py`
  ```python
  from spawn_guard import safe_spawn
  params = safe_spawn(task="OCR分析", model="deepseek-v4-flash")
  # → 自动设置 runTimeoutSeconds=600, cleanup="delete"
  ```

- **API 限流**: `scripts/guards/api_guard.py`
  ```python
  from api_guard import guarded_chat_completion, batch_process
  ```

- **工作流集成**: `scripts/guards/workflow_with_budget.py`
  ```python
  from workflow_with_budget import check_budget, before_ocr, before_report
=======
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
  配置: `config/cost_guard.json`（预算/阈值/日限）

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
>>>>>>> c3097c346e456e55f12e02c4d4e7b612d0fc2140
  ```

- **审计黑板集成**: `audit-blackboard/launch.py` 和 `orchestrate.py` 已内置预算检查
  - `launch.py` Step 0: 自动检查 raw_data 目录token预算
  - `orchestrate.py` prepare: 检查数据目录预算
  - `orchestrate.py` collect: 大量findings时提示预算风险

<<<<<<< HEAD
### ⚠️ DeepSeek 直连 provider 已移除
旧key `sk-4253...31f7` 已失效(401)，现通过 `custom-cbwyy-top-v1`（cbwxy.top代理）走DeepSeek模型。如需直连DeepSeek，找平头哥要新key后加到 models.json。

### ⚠️ Qwen-VL 图片分析规则
涉及 `qwen-vl-max` 的图片/PDF分析，必须先询问用户确认，不得自动调用。

=======
>>>>>>> c3097c346e456e55f12e02c4d4e7b612d0fc2140
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

- **配色**：深蓝#0A1F3F + 青绿#1A5C6E + 铜金#C5955C + 暖灰#F5F2EC
- **封面**：A4 300dpi (2480x3508)，Pillow逐像素绘制，微软雅黑字体
- **流程图**：draw.io scale 8 (≈350dpi, 2972x5816px)
- **字体**：标题微软雅黑、正文宋体、表格微软雅黑
- **页边距**：上2.5 下2 左2.8 右2.8 cm
- **表格**：深蓝表头+金字，暖灰隔行，金色边框
- **模板文件**：`D:\openclaw-workspace\bid_aba\融策标书模板_v2_高级版.docx`
- **生成脚本**：`D:\openclaw-workspace\scripts\标书模板生成_v2.py`

<<<<<<< HEAD
## 财政监督检查模型 Skill

- **Skill**: `fiscal-supervision-model`
- **路径**: `C:\Users\scrccpa\.openclaw\skills\fiscal-supervision-model\SKILL.md`
- **用途**: 财政监督检查/财会监督专项检查数据标准、识别规则库、疑点分析、现场核查任务、资料补充清单、问题底稿初稿。
- **触发说法**: “调用财政监督检查模型”“用财会监督模型跑疑点”“按交通厅项目生成识别规则”“导入数据跑财政监督检查疑点”。
- **核心引用**:
  - `references/data-standard.md`：数据模板和字段标准
  - `references/rule-library-v1.md`：首批30条识别规则
  - `references/output-spec.md`：Excel输出物规范

=======
>>>>>>> c3097c346e456e55f12e02c4d4e7b612d0fc2140
## 模型路由方案（2026-07-05）

### 可用模型一览

| 模型 | provider key | 能力标签 | 优缺点 |
|:-----|:------------|:---------|:-------|
| **deepseek-v4-flash** | custom-cbwyy-top-v1 | ⚡免费·超快 | 日常主力，免费但无深度推理 |
| **deepseek-v4-pro** | custom-cbwyy-top-v1 | 🧠推理·分析 | 复杂分析核心，含 reasoning 链 |
| **gpt-5.5** | custom-cbwyy-gpt55 | ✍️润色·📷图片 | 全能型，支持图片输入 |
| **claude-sonnet-5** | custom-cbwyy-claude | 📖长文·细腻 | 长文档分析，遵循复杂指令 |
| **claude-opus-4-8** | custom-cbwyy-opus | 🔬最强推理 | 压舱石，重大研判才用 |
| **claude-fable-5** | custom-cbwyy-fable | 🟡快速Claude | Sonnet备用，缓存命中率极高 |
| **doubao-seed-2.0-lite** | custom-cbwyy-doubao | 🇨🇳国产·公文 | 合规备选，中文原生 |
| **gpt-image-2** | custom-cbwyy-image | 🎨生图 | 封面/配图专用 |

### 场景路由表

| 场景 | primary | fallback 1 | fallback 2 |
|:-----|:--------|:-----------|:-----------|
| 日常对话·心跳·简单查询 | V4 Flash | V4 Pro | — |
| 审计分析·数据核查·复杂推理 | V4 Pro | Claude Opus 4-8 | Claude Sonnet 5 |
| 报告润色·标书·公文 | GPT-5.5 | Claude Sonnet 5 | V4 Pro |
| 长文档分析（>50页） | Claude Sonnet 5 | GPT-5.5 | — |
| 图片分析·PDF扫描件 | ⚠️ 询问用户 → qwen-vl-max | — | — |
| 封面·配图 | GPT Image 2 | — | — |
| 国产/信创合规 | V4 Flash | V4 Pro | Doubao |

### Fallback 链配置（当前）
```
primary: custom-cbwyy-top-v1/deepseek-v4-flash
fallbacks: [deepseek-v4-pro, claude-sonnet-5]
```

### 注意
- ⚠️ qwen-vl-max（DashScope）需用户确认才调用，概不自动执行
- V4 Pro 是推理模型，含 reasoning tokens，注意 token 消耗
- cbwxy.top 代理偶有临时抽风（403），重试即可恢复

Add whatever helps you do your job. This is your cheat sheet.
