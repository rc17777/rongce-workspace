# 融策 Agent 状态监控面板

> "谁干活灯就亮，谁卡住就报警。不盯屏幕也知道。" — 灵感来自陈磊历险记

## 快速启动

```bash
# 1. 启动监控面板
cd dashboard
python server.py

# 2. 浏览器打开
http://127.0.0.1:8765

# 3. 跑个演示看看效果
python demo.py
```

## 架构

```
dashboard/
├── server.py          # HTTP服务 + API (stdlib, 零依赖)
├── index.html         # 前端面板
├── report.py          # 状态上报CLI工具
├── demo.py            # 演示脚本
├── agent_state.json   # 持久化状态 (自动生成)
├── agent_activity.log # 活动日志 (自动生成)
└── start.bat          # Windows快速启动
```

## API

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/state` | GET | 全量状态 (agents + alerts + stats) |
| `/api/agent/{id}` | GET | 单个Agent详情 |
| `/api/agent/{id}/status` | POST | 更新状态 `{"status":"working","task":"..."}` |
| `/api/webhook` | POST | 设置告警推送URL `{"url":"钉钉webhook"}` |
| `/api/reset` | POST | 重置全部状态 |
| `/api/stats` | GET | 统计摘要 |
| `/api/alerts` | GET | 告警列表 |

## 状态上报

```bash
# 手动上报
python report.py --agent data_scout --status working --task "分析预算数据"
python report.py --agent data_scout --status completed --elapsed 5200
python report.py --agent data_scout --status error --error "API超时"

# 心跳检查
python report.py --heartbeat
```

## 集成到 OpenClaw

在 `HEARTBEAT.md` 中添加自动检查：

```markdown
## Agent 监控心跳
每30分钟：`python dashboard/report.py --heartbeat`
如有异常→ 自动推送告警到钉钉
```

## 钉钉/企微告警

在面板顶部输入 Webhook URL → 保存 → 自动推送告警。

钉钉机器人 Webhook 格式：`https://oapi.dingtalk.com/robot/send?access_token=xxx`

## 自动卡住检测

后台线程每10秒扫描：`working` 超过 5 分钟 → 自动标记 `stuck` + 触发告警。

## 18个Agent覆盖

| 分类 | Agent | 主力模型 | 层级 |
|------|-------|---------|------|
| 核心审计(7) | 数据侦察兵/合同猎犬/招投标猎手/法规检察官/底稿工匠/报告笔杆子/复核哨兵 | DeepSeek Pro / Sonnet-5 / Qwen 3.7 | T1 |
| 工程咨询(3) | 预算工程师/结算审计师/财政评审员 | DeepSeek Pro / Sonnet-5 | T1 |
| 绩效评价(1) | 绩效评价师 | DeepSeek Pro | T1 |
| 专项检测(2) | 评标偏离度/会议纪要分析 | DeepSeek Pro / Qwen 3.7 | T1 |
| 数据运维(4) | OCR预处理/数据分类员/数据脱敏/调整分录师 | Flash / Pro | T1/T4 |
| 方案撰写(1) | 方案撰写师 | Qwen 3.7 | T1 |
