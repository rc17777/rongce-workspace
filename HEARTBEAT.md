# HEARTBEAT.md - 定期检查任务

> ⚠️ **吞金兽警报**：心跳必须用 `custom-cbwyy-top-v1/deepseek-v4-flash`（免费/低成本）！禁止用 GPT-5.5、V4 Pro、Claude 等高成本模型做心跳任务！
> 心跳前先检查当前模型；如果不是 `custom-cbwyy-top-v1/deepseek-v4-flash`，必须先切回来。
> 理由：6/25凌晨3点心跳烧了43k token + 6万缓存，纯浪费。模型贵起来，比打印店彩打还离谱。

## 日常检查（每2-4小时轮换）

### 任何时候
- 所有自动监控已取消

### 上午检查（约9:00-10:00）
- [ ] 审计情报采集：运行 `python scripts/audit_intel_collector.py`，有新条目时推送

### 下午检查（约14:00-15:00）
- [ ] 跟进上午未完成事项
- [ ] 检查当前模型是否为 `custom-cbwyy-top-v1/deepseek-v4-flash`（如果切过先切回来）

### 晚间检查（约20:00-21:00）
- [ ] 更新 memory 文件（当日事件记录）
- [ ] **Token 日报**：运行 `python scripts/token_tracker.py today` 生成当日用量报告，如 >5万 tokens 则备注告知用户
- [ ] **费用日报**：（DeepSeek 通过 cbwyy.top 中转，无独立计费，跳过）

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

**原理**：基于 session_status 的 context 增量估算。同一 session 内相邻快照的 context 上升量累加即为消耗。context 下降（compaction/restart）时自动标记 reset。

## 定期维护（每周1-2次）

- [ ] 🔑 **模型健康检查**（周一执行）：运行 `python scripts/deepseek_model_check.py`，退出码 2 时立即推送报告给用户
- [ ] 审查 MEMORY.md 是否需要更新
- [ ] 清理过期临时文件
- [ ] 检查 OpenClaw 更新
- [ ] 审查 TOOLS.md 配置

## 技能维护（每月1次）

- [ ] 审视 SKILLS.md，标记长期不用的技能
- [ ] 更新 Prompt库（`knowledge/prompt-library/`）
- [ ] 更新 CoT 思维链数据集（`knowledge/cot-dataset/`）
- [ ] 审计流程嵌入效果回顾

## 静默时间
- 23:00-08:00 不主动打扰（除非紧急）
