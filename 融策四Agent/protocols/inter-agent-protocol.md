# Agent间通信协议

> 版本：v1.0 | 2026-07-11
> 适用范围：融策审计 / 融策工程咨询 / 融策知识 / 融策监督

---

## 一、消息格式

所有Agent间消息使用统一JSON格式：

```json
{
  "header": {
    "msg_id": "uuid-v4",
    "from": "rongce-audit",
    "to": "rongce-engineering",
    "timestamp": "ISO-8601",
    "priority": "normal|high|critical",
    "reply_to": "msg_id or null"
  },
  "body": {
    "task_type": "cost_verification|quota_analysis|kb_query|kb_push|quality_review|data_request",
    "summary": "一句话任务描述",
    "payload": {},
    "context": {
      "parent_task_id": "原始用户任务ID",
      "history_summary": "截至此消息的任务进展摘要（≤200字）"
    },
    "deadline": "ISO-8601 or null",
    "output_format": "json|markdown|structured"
  }
}
```

---

## 二、消息类型定义

### 2.1 审计 → 工程咨询

| task_type | 含义 | payload示例 | 期望返回 |
|-----------|------|-------------|----------|
| `cost_verification` | 请求工程造价核算 | `{project_id, item_list, reference_period}` | 造价核算结果（量×价） |
| `quota_analysis` | 请求定额套用分析 | `{work_items, region, year}` | 适用定额编号+套用说明 |
| `data_request` | 请求工程基准数据 | `{data_type (五算/材料价/行业对标), scope}` | 结构化数据 |

### 2.2 工程咨询 → 审计

| task_type | 含义 | payload示例 | 期望返回 |
|-----------|------|-------------|----------|
| 被动响应 | 仅响应审计的请求 | — | — |

> 注：工程咨询不主动向审计发请求。审计的合规推演不需要工程来触发。

### 2.3 融策知识 → 所有Agent（广播）

| task_type | 含义 | payload示例 |
|-----------|------|-------------|
| `kb_update` | KB条目新增/更新 | `{domain, entry_id, summary, full_text_ref, effective_date}` |
| `kb_deprecation` | KB条目过期/废止 | `{domain, entry_id, reason, replacement_id or null}` |
| `kb_conflict` | KB条目冲突告警 | `{entry_id_a, entry_id_b, conflict_description}` |
| `trend_alert` | AI前沿动态 | `{source, summary, applicability_score, recommendation}` |

### 2.4 融策监督 → 所有Agent

| task_type | 含义 | payload示例 |
|-----------|------|-------------|
| `quality_review` | 输出评审结果 | `{target_msg_id, score, dimensions, issues, verdict}` |
| `task_status` | 任务状态通知 | `{task_id, status, eta, notes}` |
| `reroute` | 任务重新路由 | `{task_id, from_agent, to_agent, reason}` |

---

## 三、通信规则

### 同步 vs 异步

| 场景 | 模式 | 超时 |
|------|------|------|
| 审计调工程（同一任务链内） | 同步等待 | 120s |
| 知识推送KB更新 | 异步广播 | 无超时 |
| 监督分发评审结果 | 异步 | 无超时 |
| 监督重路由任务 | 同步 | 60s |

### 重试策略

- 同步请求超时 → 自动重试1次 → 仍失败 → 降级路由或人工介入
- 异步消息失败 → 记录失败日志 → 汇总到监督日报 → 每日批量重试

### 消息去重

- 每个 `msg_id` 全局唯一
- 收到重复 `msg_id` → 返回上次处理结果，不重新执行
- 超时重试使用相同 `msg_id`

---

## 四、安全

### 敏感数据处理

- 被审计单位名称、具体金额、个人身份信息在消息体中必须脱敏
- 脱敏格式：`{entity_type}_{hash前6位}`，如 `UNIT_A3F2C1`
- 原始敏感数据仅在Agent内部上下文保留，不跨Agent传输

### 消息加密

- Agent间消息不经过外部API，全部在本地消息队列传输
- 日志中记录的消息内容自动脱敏（替换敏感字段为 `[REDACTED]`）

### 审计轨迹

- 每个Agent间消息记录：发送方/接收方/时间/任务类型/payload摘要
- 至少保留90天
- 可被融策监督的日报引用

---

## 五、示例

### 示例1：审计请求工程造价核算

```json
{
  "header": {
    "msg_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "from": "rongce-audit",
    "to": "rongce-engineering",
    "timestamp": "2026-07-11T11:30:00+08:00",
    "priority": "high",
    "reply_to": null
  },
  "body": {
    "task_type": "cost_verification",
    "summary": "XXX项目竣工决算，土建部分实际支出超概算32%，请核实超量部分是否合理",
    "payload": {
      "project_id": "PROJ_D8F2A1",
      "scope": "土建工程",
      "budget_amount": "概算批复2800万",
      "actual_amount": "实际支出3696万",
      "overrun_rate": "32%",
      "reference_period": "2024-2025"
    },
    "context": {
      "parent_task_id": "TASK_20260711_001",
      "history_summary": "审计正在执行XXX项目竣工财务决算审核。L1合规检查通过，已发现概算超支异常。现需要工程专业判断超量部分的技术合理性。"
    },
    "deadline": "2026-07-11T14:00:00+08:00",
    "output_format": "structured"
  }
}
```

### 示例2：知识Agent推送法规更新

```json
{
  "header": {
    "msg_id": "k1b2c3d4-e5f6-7890-abcd-ef1234567891",
    "from": "rongce-knowledge",
    "to": "broadcast",
    "timestamp": "2026-07-11T09:00:00+08:00",
    "priority": "critical",
    "reply_to": null
  },
  "body": {
    "task_type": "kb_update",
    "summary": "财政部新发《专项债券项目资金绩效管理办法》修订版，即日施行",
    "payload": {
      "domain": "domain_1_audit",
      "entry_id": "KB-AUDIT-2026-0012",
      "summary": "专项债绩效管理办法新增'穿透式监控'和'全生命周期绩效管理'两个核心要求",
      "full_text_ref": "rag/audit/2026-07-11_专项债绩效管理办法.md",
      "effective_date": "2026-07-11",
      "conflicts_with": ["KB-AUDIT-2024-0003"], 
      "affected_agents": ["rongce-audit"]
    }
  }
}
```
