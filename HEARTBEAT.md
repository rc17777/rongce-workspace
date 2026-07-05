# HEARTBEAT.md - 定期检查任务

<<<<<<< HEAD
> ⚠️ **吞金兽警报**：心跳必须用 `custom-cbwyy-top-v1/deepseek-v4-flash`（免费/低成本）！禁止用 GPT-5.5、V4 Pro、Kimi 等高成本模型做心跳任务！
> 心跳前先检查当前模型；如果不是 `custom-cbwyy-top-v1/deepseek-v4-flash`，必须先切回来。
> 理由：6/25凌晨3点心跳烧了43k token + 6万缓存，纯浪费。模型贵起来，比打印店彩打还离谱。
=======
> ⚠️ **吞金兽警报**：心跳必须用 `deepseek/deepseek-v4-flash`（免费）！禁止用 V4 Pro 做心跳任务！
> 当前模型已经是 v4-flash → 保持不动。如果切过其他模型，心跳前务必先切回来。
> 理由：6/25凌晨3点心跳烧了43k token + 6万缓存，纯浪费。
>>>>>>> c3097c346e456e55f12e02c4d4e7b612d0fc2140

## 日常检查（每2-4小时轮换）

### 任何时候
<<<<<<< HEAD
- 所有自动监控已取消

### 上午检查（约9:00-10:00）
- [ ] 审计情报采集：运行 `python scripts/audit_intel_collector.py`，有新条目时推送

### 下午检查（约14:00-15:00）
- [ ] 跟进上午未完成事项
- [ ] 检查当前模型是否为 `custom-cbwyy-top-v1/deepseek-v4-flash`（如果切过先切回来）

### 晚间检查（约20:00-21:00）
- [ ] 更新 memory 文件（当日事件记录）
- [ ] **Token 日报**：运行 `python scripts/token_tracker.py today` 生成当日用量报告，如 >5万 tokens 则备注告知用户
- [ ] **费用日报**：运行 `python scripts/deepseek_cost_guard.py check` 检查当日费用
=======
- [ ] **模型检查**：先确认当前是 `zhipu/glm-4-flash`，如果不是则切换
- [ ] **Token 用量快照**：调用 `session_status` 获取当前 context 使用量，然后运行 `python scripts/token_tracker.py snapshot -c <使用量> -l <上限> -s <session> -n "heartbeat"`，记录到 `logs/token_usage.jsonl`
- [ ] OpenRouter 免费模型监控：运行 `python scripts/openrouter_monitor.py`，如有变化（新增/下架/变更）推送给用户
- [ ] **智谱模型检查**（存状态文件 `config/zhipu_model_last_check.txt`，距上次检查≥7天则触发）：运行 `python scripts/zhipu_model_check.py`，退出码 2 时推送

### 上午检查（约9:00-10:00）
- [ ] 审计情报采集：工作日 cron 自动执行，有新条目时推送

### 下午检查（约14:00-15:00）
- [ ] 跟进上午未完成事项
- [ ] 检查当前模型是否为 `zhipu/glm-4-flash`（如果切过先切回来）

### 晚间检查（约20:00-21:00）
- [ ] 更新 memory 文件（当日事件记录）
- [ ] **Token 日报**：运行 `python scripts/token_tracker.py report` 生成当日用量报告，如 >5万 tokens 则备注告知用户
- [ ] **费用日报**：（DeepSeek 已停用，暂无需检查）
>>>>>>> c3097c346e456e55f12e02c4d4e7b612d0fc2140

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

<<<<<<< HEAD
- [ ] 🔑 **模型健康检查**（周一执行）：运行 `python scripts/deepseek_model_check.py`，退出码 2 时立即推送报告给用户
- [ ] **费用守卫健康检查**：运行 `python scripts/deepseek_cost_guard.py limit` 确认熔断阈值生效
=======
- [ ] 🔑 **DeepSeek 模型健康检查**（周一执行）：运行 `python scripts/deepseek_model_check.py`，退出码 2 时立即推送报告给用户
>>>>>>> c3097c346e456e55f12e02c4d4e7b612d0fc2140
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
