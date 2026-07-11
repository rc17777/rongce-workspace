# AI自动化工作流 (ai-workflow)

> 🏭 融策AI自动化工厂 — 连续运行中（自2026-07-05）

## 架构

```
ai-workflow/
├── config.yaml           # 工作流配置（Agent定义/调度/知识库）
├── engine.py             # 核心调度引擎（大脑）
├── state.json            # 运行状态（自动维护）
├── agents/               # Agent规格（未来扩展）
├── tasks/                # 任务队列
│   ├── pending/          # 待执行
│   └── done/             # 已完成（保留7天）
├── knowledge/            # 工作流专属知识库
└── logs/                 # 运行日志
```

## 5个Agent工位

| Agent | 职责 | 调度 | 工具 |
|:--|:--|:--|:--|
| 📡 数据侦察兵 | 审计情报采集 | 每日08:00 | `scripts/audit_intel_collector.py` |
| 📚 知识管理员 | 僵尸文件清理+RAG同步 | 每日14:00 | `scripts/prune_knowledge.py` |
| 🎯 招标猎手 | 政府采购网招标采集 | 周一三五09:00 | HEARTBEAT §招标采集 |
| 🏥 模型医生 | 12模型健康检查 | 每日10:00 | `scripts/deepseek_model_check.py` |
| 💰 Token监察员 | 每日Token用量报告 | 每日20:00 | `scripts/token_tracker.py` |

## 监工巡检

每4小时自动检查：
- Agent状态异常（连续失败→升级）
- 长期未运行的Agent
- 待人工介入的升级项

## 驱动方式

**心跳驱动**（主方案）：每次心跳触发 `python ai-workflow/engine.py run`，引擎内部判断当前时间该运行哪些Agent。

**手动命令**：

```bash
# 查看状态面板
python ai-workflow/engine.py status

# 运行一次调度周期
python ai-workflow/engine.py run

# 监工巡检
python ai-workflow/engine.py overseer

# 生成运行日报
python ai-workflow/engine.py report
```

## 设计原则

1. **错误代价路由** — 所有定时任务用免费模型(v4-flash)
2. **熔断机制** — 连续失败3次自动升级
3. **人类兜底** — 无法自动处理的问题升级给平头哥
4. **静默时间** — 23:00-08:00跳过常规任务
