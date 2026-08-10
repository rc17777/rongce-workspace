# HEARTBEAT.md — 融策 Agent 监控 + 告警 + 远程修复

## 每次心跳必做

### Step 1: Agent 状态检查
```bash
python dashboard/report.py heartbeat --format text
```

### Step 2: 根据结果处理

**无异常 → HEARTBEAT_OK**

**有异常 → 分时段：**

| 时段 | 行为 |
|------|------|
| 08:00-23:00 | 推送告警到企微 + 回复异常摘要 |
| 23:00-08:00 | 静默，不推送不回复 |

### Step 3: 推送告警
```bash
python dashboard/alert_push.py
```

### Step 4: 用户远程修复（手机微信/企微发指令）

收到告警 → 手机回复以下指令 → 自动修复：

| 指令 | 效果 |
|------|------|
| `状态` | 查看当前所有Agent状态 |
| `修复全部` | 一键重置所有异常Agent |
| `修复 <Agent名>` | 重置指定Agent（如 `修复 结算审计师`） |
| `重试 <Agent名>` | 重试失败任务 |
| `暂停 <Agent名>` | 暂停持续报错的Agent |
| `跳过 <Agent名>` | 标记完成，跳过 |
| `重启面板` | 重启监控面板服务 |

> 支持中文名或英文ID：`修复 data_scout` = `修复 数据侦察兵`

### 每日报告（09:00 一次）
```bash
python dashboard/report.py daily
```
