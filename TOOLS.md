# TOOLS.md - Local Notes

Skills define _how_ tools work. This file is for _your_ specifics — the stuff that's unique to your setup.

## 数据目录（换电脑时需迁移）

- **杂志资料OCR**: `D:\杂志资料`（1086MB/1450文件，审计杂志OCR结果）
- **审计书籍OCR**: 源 `E:\2026\审计方法&政策文件\审计相关书籍`（55本PDF，5.9GB）→ 输出 `E:\2026\审计方法&政策文件\_ocr_output`（96个md，14.5MB字，含 `_manifest.json` 索引）
- **备份规则**：换电脑时从旧D盘拷贝到新D盘根目录，路径保持一致；**E盘审计书籍OCR目录也要同步迁移**（含源PDF+输出）
- **manifest 重新生成**：`python scripts/regenerate_ocr_manifest.py`（自动统计页数/字数/覆盖率）

## 网络代理（Git push 依赖）

- **代理软件**：FlClash（`D:\Program Files\FlClash\FlClash.exe`），端口 `127.0.0.1:7890`
  - ⚠️ 要启动 **FlClash.exe（GUI）**，Core 会随 GUI 拉起；单独启动 FlClashCore.exe 不会监听代理端口
  - ⚠️ GUI 启动后若无节点监听，需手动在界面点连接/选节点
- **Git 已配置代理**：`http.proxy=http://127.0.0.1:7890`（workspace 仓库）
- **直连 GitHub 会被重置**（国内环境），push 必须走代理
- **故障特征**：`schannel: failed to receive handshake` / `curl 56 server closed abruptly` = 代理节点挂了/不稳，需在 FlClash 切节点或重启，**不是 Git 配置问题**
- ⚠️ 判断 push 是否成功别只看报错：报 `server closed abruptly` 时数据可能已到达，用 `git ls-remote origin HEAD` 对比本地 HEAD 验证
- 常见代理端口检查：7890/7891/7897/1080/10808/10809/8889/8118

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

## 模型路由方案 v7.0（三层路由）

> 完整配置 → **`config/model_routing_v7.py`**（v5/v6 已废弃，勿用）
> 路由优先级：**Agent路由 > 场景路由 > 全局默认**
> 敏感项目开关：**`SENSITIVE_FORCE_DOMESTIC_PRIMARY = True`**（默认开启：敏感项目下 Agent 路由 primary 也强制换国产；设为 False 恢复 v6 旧行为——仅 fallback 国产）
> 验证：`python scripts/test_routing_v7.py` + `python scripts/verify_routing.py`；生产决策轨迹见 `logs/routing_trajectory.jsonl`

### 第一层：场景速查

| 场景 | 主模型 | Fallback |
|:----|:------|:--------|
| 日常对话/查询 | v4-flash | v4-pro |
| 心跳/定时任务 | v4-flash | — |
| 数据核查/统计 | v4-pro | flash, kimi-k3 |
| 财务分析/异常 | v4-pro | sonnet-5, kimi-k3 |
| 合规审查 | **sonnet-5** | qwen, opus |
| 法律条文解读 | **sonnet-5** | qwen, v4-pro |
| 政府公文/方案 | **qwen3.7-plus** | sonnet, gemini |
| 审计报告撰写 | **qwen3.7-plus** | sonnet, gpt-5.5 |
| 创意/头脑风暴 | **luna** | sol, terra |
| 长文档(>128K) | **gemini** | qwen, v4-pro |
| 英文/国际 | **gpt-5.5** | sonnet |
| 终审/零容错 | **sonnet-5** | opus-4-8 |
| 国产推理 | **kimi-k3** | glm-5.2, v4-pro |
| 咨询顾问 | **fable-5** | sonnet, luna |
| 轻量任务 | v4-flash | v4-pro |

### 第二层：22 Agent分工路由

| Agent | 主模型 | 场景 | 原因 |
|:------|:------|:----|:----|
| 数据侦察兵 | v4-pro | 财务分析 | 数值精确优先 |
| 合同猎犬 | **sonnet-5** | 合规审查 | 条文严谨 |
| 招投标猎手 | v4-pro | 数据核查 | 模式检测 |
| 法规检察官 | **sonnet-5** | 法规解读 | 法律条文 |
| 底稿工匠 | **qwen3.7-plus** | 公文 | 中文公文 |
| 报告笔杆子 | **qwen3.7-plus** | 报告 | 中文公文 |
| 复核哨兵 | **sonnet-5** | 终审 | 零容错 |
| 预算工程师 | v4-pro | 数据核查 | 精确计算 |
| 结算审计师 | v4-pro | 财务分析 | 计算+合规 |
| 财政评审员 | **sonnet-5** | 合规审查 | 政策合规 |
| 绩效评价师 | v4-pro | 财务分析 | 指标打分 |
| 评标偏离度 | v4-pro | 数据核查 | 统计检测 |
| 会议纪要分析 | **qwen3.7-plus** | 公文 | 中文理解 |
| OCR预处理 | v4-flash | 轻量 | 低成本 |
| 数据分类员 | v4-flash | 轻量 | 低成本 |
| 数据脱敏 | v4-flash | 轻量 | 低成本 |
| 调整分录师 | v4-pro | 财务分析 | 财务精确 |
| 方案撰写师 | **qwen3.7-plus** | 公文 | 公文格式 |

### 第三层：全局Fallback

```
flash → v4-pro → gemini → qwen → fable → sonnet → gpt-5.5
→ luna → sol → terra → kimi-k3 → glm-5.2 → doubao → deepseek-direct
```

**核心原则**：不同Agent用最匹配的模型，不是所有任务都用同一把刀。
- 中文公文→qwen 3.7（原生中文，不翻译腔）
- 条文逻辑→sonnet-5（严谨，不幻觉）
- 数据计算→v4-pro（精确且免费）
- 轻量任务→v4-flash（快速低成本）
- 只有复核哨兵能触发opus（≤2次/项目）

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
