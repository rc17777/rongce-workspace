# TOOLS.md - Local Notes

Skills define _how_ tools work. This file is for _your_ specifics — the stuff that's unique to your setup.

## 数据目录（换电脑时需迁移）

- **杂志资料OCR**: `D:\杂志资料`（1086MB/1450文件，审计杂志OCR结果）
- **备份规则**：换电脑时从旧D盘拷贝到新D盘根目录，路径保持一致

## 可执行文件

- **draw.io**：`D:\dwaw\draw.io\draw.io.exe` v30.0.1
  - CLI导出：`& "D:\dwaw\draw.io\draw.io.exe" -x -f png -e -b 10 -o <out> <input.drawio>`
- **openssl**：`C:\Users\scrccpa\miniconda3\envs\paddleocr\Library\bin\openssl.exe`
  - dashi-ppt 预览/导出需要，设 `OPENSSL_PATH` 指向此路径

## 微信文章爬取

- **必须用移动端 User-Agent**，否则微信返回 JS 渲染空壳
- UA：`Mozilla/5.0 (Linux; Android 13; SM-S9080) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.230 Mobile Safari/537.36 MicroMessenger/8.0.47`
- 标题/描述：从 HTML 提取 `var msg_title`、`var msg_desc`
- 全文：`id="js_content"` 或 `class="rich_media_content"`
- **注意**：正文 `display:none`，但移动端 UA 请求时内容已在 HTML 中

## 品牌配色（融策）

- 深蓝 `#0A1F3F` / 青绿 `#1A5C6E` / 铜金 `#C5955C` / 暖灰 `#F5F2EC`
- 封面：A4 300dpi (2480×3508)，Pillow 逐像素绘制，微软雅黑
- 字体：标题微软雅黑、正文宋体、表格微软雅黑
- 页边距：上2.5 下2 左2.8 右2.8 cm
- 模板：`D:\openclaw-workspace\bid_aba\融策标书模板_v2_高级版.docx`
- 脚本：`scripts\标书模板生成_v2.py`

## dashi-ppt 技能要点

- 路径：`~/.openclaw/skills/dashi-ppt/`（v0.4.0）
- 首次用 `npm install --include=dev`（必须带 dev，否则缺 tsx/esbuild/playwright-core）
- ⚠️ 预览/导出需要 `OPENSSL_PATH` 指向 miniconda 里的 openssl.exe
- 导出浏览器：Edge，playwright 用 `channel: 'msedge'`
- 端口段：5200-5999（避开 4178/4300/4400 保留端口）
- **端到端流程**（每次跑一遍）：
  ```
  # 选页
  node <skill>/project/scripts/layout-query.mjs --theme theme07 --limit 16
  node <skill>/project/scripts/inspect-layout.mjs --compact <layout...>
  # 构建 goal.json → 渲染
  npm --prefix <skill>/project run props:safe -- --goal <goal.json> --write
  npm --prefix <skill>/project run validate:goal-spec -- <goal.json>
  npm --prefix <skill>/project run render:goal -- <goal.json> <deck>/ppt/index.html
  # 预览（要 OPENSSL_PATH）→ http://127.0.0.1:<port>/
  npm --prefix <skill>/project run preview:start -- <deck>/ppt 5273
  # 导出PPTX（要 OPENSSL_PATH）
  node <skill>/project/scripts/export-pptx.mjs <deck>/ppt <out.pptx>
  ```
- 主题：theme01-12，审计类推荐 theme07（冷白调研）、theme05（色谱图表）、theme06（深色图谱）
- 成本：10页 ≈ 10万token（贵，成本敏感慎用）

## Token 预算 / 费用工具

| 脚本 | 用途 | 关键命令 |
|:--|:--|:--|
| `scripts/token_budget.py` | 任务前预算估算 | `python scripts/token_budget.py --files "报告.docx" --task "分析"` |
| `scripts/deepseek_cost_guard.py` | 每日费用监控（心跳自动执行） | `check`、`daily`、`limit` |
| `scripts/token_tracker.py` | Token 使用追踪 | `today`、`snapshot`、`summary --days 7` |
| `scripts/api_guard.py` | API 限流保护 | `guarded_chat_completion()`、`batch_process()` |
| `scripts/spawn_guard.py` | spawn 安全包装 | `safe_spawn()` 自动设超时 |
| `scripts/workflow_with_budget.py` | 工作流预算集成 | `check_budget()`、`before_ocr()`、`before_report()` |
| `scripts/model_health_check.py` | 每日模型健康检查（引擎自动，每日10:00） | `--json`、`--alert` |

费用守卫配置：`config/cost_guard.json`（¥100/天，70%预警，90%熔断）
Token 存储：`logs/token_usage.jsonl`（JSONL 格式）
审计黑板集成：`audit-blackboard/launch.py` + `orchestrate.py` 已内置预算检查

## 财政监督检查模型

- Skill：`fiscal-supervision-model`（`~/.openclaw/skills/fiscal-supervision-model/`）
- 核心引用：`references/data-standard.md`、`references/rule-library-v1.md`、`references/output-spec.md`
- 触发："调用财政监督检查模型"、"用财会监督模型跑疑点"等

## 模型路由方案（精简入口）

> 完整路由表 v4.2 → **`knowledge/references/模型路由方案_v4.2.md`**

**速查表**：
- **默认模型**：deepseek-v4-flash（免费/快/日常）
- **心跳/定时任务**：必须用 v4-flash
- **中文公文/图片**：qwen3.7-plus
- **数据核查**：v4-pro
- **合规审查/逻辑**：sonnet-5
- **英文润色**：gpt-5.5
- **创意**：gpt-5.6-luna
- **长文档(>128K)**：gemini-3.1-pro-preview
- **压舱石终审**：opus-4-8（≤2次/项目）
- **国产备胎**：doubao-seed-2.0-lite
- **国产推理**：kimi-k3（月之暗面，带 reasoning，支持 text+image）
- **生图**：gpt-image-2
- **咨询层**：fable-5（做决策前先问）

**Fallback链**：flash → v4-pro → gemini → qwen → fable → sonnet → gpt-5.5 → luna → sol → terra → deepseek-direct

**核心原则**：路由依据不是"做什么"，而是"错了要付出什么代价"。

## 环境注意事项

- ⚠️ **npm prefix** 被设为 `C:\Users\scrccpa\AppData\Local\Programs\OneClaw`（非默认）。装全局包前先 `npm config get prefix` 确认，避免装进 OneClaw 目录造成版本打架
- ⚠️ **换 key = 改两份**：openclaw.json + scripts/model_health_check.py（健康检查的独立副本）
- Windows GBK 编码是 Python 脚本的常驻坑，需 `sys.stdout.reconfigure(encoding='utf-8')`
- DeepSeek 只支持 image_url 在最后一条用户消息，历史图片会导致400错误
- Qwen-VL-Max 图片分析必须先询问用户确认，不得自动调用

## Sub2API 自建网关方案

> 详见：`knowledge/references/Sub2API自建AI网关部署方案.md`

美西VPS（搬瓦工CN2 GIA） + 国内Nginx反代/CDN回源，内置支付宝/微信收款。
核心项目: GitHub Wei-Shaw/sub2api（32k⭐），Go + Vue + PostgreSQL + Redis，Docker一键部署。
