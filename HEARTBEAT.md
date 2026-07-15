# HEARTBEAT.md - AI自动化工作流 + 定期检查

> ⚠️ **吞金兽警报**：心跳必须用低成本模型！
> 禁止用 GPT-5.5、V4 Pro、Claude 等高成本模型做心跳任务！
>
> 🚧 **临时切换（2026-07-16 起）**：`deepseek-v4-flash` 的 key 持续 403 故障，
> 心跳模型临时改用 **`deepseek-direct/deepseek-chat`**（直连，低成本）。
> 心跳前先检查当前模型；如果不是 `deepseek-direct/deepseek-chat`，必须先切回来。
> ✅ 待 v4-flash 换 key 恢复后（`python scripts/model_health_check.py` 显示 200），改回 `custom-cbwyy-top-v1/deepseek-v4-flash` 并删除本临时段。

## 🤖 AI自动化工作流（每次心跳执行）

### 第一步：运行工作流调度引擎（每次心跳必做）

```bash
python -X utf8 ai-workflow/engine.py run
```

引擎内部自动判断当前时间该运行哪些Agent：
- 📡 数据侦察兵：每日 08:00-08:30 → 采集审计情报（已手动验证 ✅）
- 📚 知识管理员：每日 14:00-14:30 → 清理僵尸文件+同步RAG+RAG每日精选
- 🎯 招标猎手：周一三五 09:00-09:30 → 招标信息采集
- 📖 文献采集员：每日 08:00-08:30 → OpenAlex审计文献自动采集（新增 2026-07-15）
- 🏥 模型医生：每日 10:00-10:30 → 12模型健康检查（已手动验证 ✅）
- 💰 Token监察员：每日 20:00-20:30 → Token日报
- 🔀 路由控制器：每日 06:00-06:30 → 模型路由配置更新

**手动触发指定Agent：**
```bash
python -X utf8 ai-workflow/engine.py status          # 查看状态
python -X utf8 ai-workflow/engine.py report          # 查看日报
python -X utf8 ai-workflow/engine.py trigger data_scout   # 手动触发数据侦察兵
python -X utf8 ai-workflow/engine.py trigger model_doctor # 手动触发模型医生
python -X utf8 ai-workflow/engine.py run --force           # 强制运行所有Agent

### 第二步：状态面板（每天一次，约09:00）

```bash
python -X utf8 ai-workflow/engine.py status
```

如有 🚨 升级项，推送给平头哥。

### 第三步：监工巡检（每4小时，09:00/13:00/17:00/21:00）

```bash
python -X utf8 ai-workflow/engine.py overseer
```

如有 ❌ 或 🚨，推送给平头哥。

---

## 常规心跳检查（引擎未覆盖的）

### 任何时候
- 如引擎报告Agent连续失败，标记升级并通知平头哥

### 上午补充（约9:00-10:00，引擎已自动跑数据侦察兵）
- [ ] 检查引擎日志 `ai-workflow/logs/` 有无异常
- [ ] 审计情报采集：如果引擎未自动执行（故障），手动运行 `python scripts/audit_intel_collector.py`

### 下午补充（约14:00-15:00，引擎已自动跑知识管理员）
- [ ] 跟进上午未完成事项
- [ ] 检查当前模型是否为 `custom-cbwyy-top-v1/deepseek-v4-flash`

### 晚间补充（约20:00-21:00，引擎已自动跑Token监察员）
- [x] 更新 memory 文件（当日事件记录）
- [x] 如引擎的Token日报 >5万tokens，备注告知用户

---

## 定期维护（每周1-2次）

- [ ] 🔑 **模型健康检查**（周一执行，引擎每日自动检查，此处为深度复检）：
  运行 `python scripts/deepseek_model_check.py`，退出码 2 时立即推送报告
- [ ] 📚 **知识库周维护**（周一/周四执行）：
  - [ ] 运行 `python scripts/prune_knowledge.py` 扫描僵尸文件
  - [ ] 删除/归档 ≥5 条无用笔记
  - [ ] 检查标签/分类是否膨胀
  - [ ] 检查 `knowledge/PARA-INDEX.md` 是否需要更新
  - [ ] commit 变更并 push（提醒平头哥开代理）
- [ ] 审查 MEMORY.md 是否需要更新
- [ ] 清理过期临时文件
- [ ] 检查 OpenClaw 更新

## 技能维护（每月1次）

- [ ] 审视 SKILLS.md，标记长期不用的技能
- [ ] 更新 Prompt库（`knowledge/prompt-library/`）
- [ ] 更新 CoT 思维链数据集（`knowledge/cot-dataset/`）

## 静默时间
- 23:00-08:00 不主动打扰（除非紧急）

## §招标采集（备用方案，引擎已自动执行）

引擎周一三五 09:00-09:30 自动触发。如果引擎未执行（检查日志），手动运行以下备用流程：

### 备用步骤

**Step 1 — 逐关键词采集（用 web_fetch）**

搜索关键词列表（15个咨询服务品类）：
```
审计服务 / 工程造价咨询 / 绩效评价 / 跟踪审计 / 竣工财务决算 / 资产清查 / 经济责任审计 / 全过程工程咨询 / 会计服务 / 资产评估 / 预算绩效管理 / 财政评审 / 内部控制 / 政府采购代理 / 监督检查
```

URL模板（近60天，bidType=1只查可投标公告）：
```
https://search.ccgp.gov.cn/bxsearch?searchtype=1&page_index=1&bidSort=0&kw={URL_ENCODED_KEYWORD}&start_time={60_DAYS_AGO}&end_time={TODAY}&timeType=6&dbselect=bidx&bidType=1
```

每个关键词：
- web_fetch 获取结果（maxChars=8000）
- 文本保存到 `knowledge/taxonomy/tender_data/{keyword}.md`
- 关键词间间隔≥3秒，避免触发反爬
- 如遇aborted，跳过该关键词继续下一个

**Step 2 — 解析入库**
```bash
python -X utf8 scripts/ingestion/tender_parser.py -i knowledge/taxonomy/tender_data/{keyword}.md -o knowledge/taxonomy/tenders.json -k {keyword}
```
（15个文件逐个执行）

**Step 3 — 四川筛选 + 业务线分类**
```bash
python -X utf8 scripts/ingestion/sichuan_collector.py filter -i knowledge/taxonomy/tenders.json -o knowledge/taxonomy/sichuan_tenders.json
```

**Step 4 — 推送报告**

如果四川有新招标：
- 按咨询服务品类分组列出
- 标注公告类型（招标/磋商/谈判）和发布日期
- 有投标截止时间的突出显示
- 四川=0条时静默（不推送）

### 状态追踪

采集完成后写入 `knowledge/taxonomy/.last_collection`:
```json
{"date": "2026-07-11", "total_national": 120, "total_sichuan": 8, "keywords_succeeded": 13}
```

## Token 追踪说明

追踪器路径：`scripts/token_tracker.py`
存储路径：`logs/token_usage.jsonl`

**手动使用**（大任务前后）：
```bash
# 任务开始前
python scripts/token_tracker.py snapshot -c 15000 -n "开始投标方案修改"

# 任务结束后
python scripts/token_tracker.py snapshot -c 65000 -n "投标方案修改完成"
```

**查看报告**：
```bash
python scripts/token_tracker.py today          # 今天
python scripts/token_tracker.py report -d 2026-06-25   # 指定日期
python scripts/token_tracker.py summary --days 7       # 近7天汇总
```
