# TROUBLESHOOTING.md — OpenClaw 故障应急卡

> 出问题先查这里，照单抓药。每次新故障解决后**当天补一条**。
> 创建: 2026-07-04 | 维护人: 融策右护卫

---

## 🚨 使用方法

1. 按症状找到对应卡片
2. 按「排查步骤」逐条执行
3. 恢复后如果是新情况，在文末「故障日志」加一行

---

## 卡片1：模型调用报 401（认证失败）

**症状**: 切换模型或发消息时报 401 Unauthorized

**根因**（2026-06-27 已验证）:
- 环境变量方式存 API key **不可靠** —— Gateway restart 只重载配置文件，不重读环境变量
- OpenClaw 进程继承的是启动时的环境

**排查步骤**:
1. 打开 `C:\Users\scrccpa\.openclaw\openclaw.json`
2. 确认 `models.providers.<provider>.apiKey` 是 **硬编码的真实 key**（sk-开头），不是环境变量名
3. 改完后执行 **完整重启**：`openclaw gateway restart`
4. ⚠️ 不要用 SIGUSR1 热重载 —— 热重载不加载新 key（2026-06-08 已验证）

**铁律**: 换 key = 硬编码进配置 + 完整 restart，两步缺一不可

---

## 卡片2：发图片报 400（Bad Request）

**症状**: 会话里有图片时，调用报 400

**根因**:
- DeepSeek 系模型（v4-flash / v4-pro）**不支持 image 输入**
- DeepSeek 只支持 image_url 在最后一条用户消息，**历史消息里的图片也会导致 400**

**排查步骤**:
1. 确认当前模型：`/status` 查看
2. 涉及图片 → 切到支持图片的模型：`claude-fable-5` / `claude-opus-4-8` / `dashscope/qwen-vl-max`
3. 如果历史消息有图片且必须用 DeepSeek → 开新会话（`/new`）

**铁律**: 图片任务永远不走 DeepSeek

---

## 卡片3：改了配置不生效

**症状**: 改了 openclaw.json，行为没变化

**根因**: SIGUSR1 热重载对部分配置（尤其 API key、provider）不生效

**排查步骤**:
1. 执行完整重启：`openclaw gateway restart`
2. 重启后 `/status` 确认模型和配置已更新
3. 还不行 → 检查 json 语法是否合法（多逗号/少括号）：
   `python -c "import json; json.load(open(r'C:\Users\scrccpa\.openclaw\openclaw.json', encoding='utf-8'))"`

---

## 卡片4：主模型挂了 / 中转站不通

**症状**: 消息发出去没回应、超时、5xx 错误

**背景**: 所有模型都走 cbwyy.top 中转，它挂 = 全挂（单点故障）

**排查步骤**:
1. 测试中转站连通性：
   `curl -s -o NUL -w "%{http_code}" https://cbwyy.top/v1/models --max-time 10`
2. 通（200）→ 是单个模型问题，`/model` 手动切换到其他模型
3. 不通 → 中转站故障，等待恢复或切备用渠道（DeepSeek 官方直连 key 见 MEMORY.md）
4. fallback 链已配置自动切换（2026-07-04 确定版）：
   gpt-5.5（主）→ claude-fable-5（备）→ gpt-5.5（兜底重试）
5. 2026-07-04 实测：两把 key 实际只授权了 gpt-5.5 和 claude-fable-5。
   deepseek-v4-pro / deepseek-v4-flash / claude-opus-4-8 及各种变体写法均 403，
   token 可见模型列表（GET /v1/models）只有 gpt-5.5。恢复 DeepSeek 需在 cbwyy.top 后台开权限或官方直连。

---

## 卡片5：子代理跑完不停 / 空转烧 token

**症状**: spawn 的子代理任务早就完成，但会话一直挂着消耗 token

**案例**: 2026年OCR任务空转78分钟，烧掉 41k token

**预防（铁律）**:
- spawn **必须带 `runTimeoutSeconds`**，按任务量估算（OCR类 600-1800，分析类 300-900）
- 大批量任务先跑 3 个样本确认质量再放量

**已发生时**:
1. `subagents list` 查看在跑的子代理
2. `subagents kill <target>` 杀掉空转的

---

## 卡片6：长报告输出被截断

**症状**: 生成长文档写到一半停了

**根因**: 所有模型 maxTokens 配置为 8192

**处理**:
1. 短期：分章生成再合并（每章 ≤ 5000 字），这是标准做法
2. 说"继续"让模型接着写（有丢失格式风险，不推荐用于正式文档）

---

## 卡片7：Git push 失败 / 超时

**症状**: push 卡住、443 超时

**根因**: GitHub 直连不通，需要代理

**处理**:
1. 开代理
2. 大文件 push（>20MB）需延长超时：
   `git config http.postBuffer 524288000`
3. push 前提醒：代理开了吗？

---

## 卡片8：DashScope（qwen-vl）调用规则

**规则**（用户指令，2026-06确认）:
- 任何涉及 qwen-vl-max 的图片/PDF 分析，**必须先询问用户确认**，不得自动调用
- OCR 批量任务前先确认 DeepSeek / DashScope 余额

---

## 卡片9：心跳/定时任务模型规则

**规则**（用户指令，2026-06-26 确认）:
- 心跳、cron 定时任务 **必须用 v4-flash**（免费）
- 禁止用 V4 Pro / Kimi / Claude 跑心跳

---

## 卡片10：后台服务悄悄烧钱

**症状**: API 余额异常下降

**根因**: Flask/WSGI 后台服务（RAG、智析Agent）没人盯着，无消费上限

**预防（铁律）**:
- 每个后台服务标配 `token_budget.py` 预算守卫
- 不同服务用不同 key，只充对应预算（小余额隔离）
- 新加服务第一件事：配预算守卫

---

## 卡片11：RAG / 智析 Agent 服务没起

**症状**: 浏览器打不开 localhost:5000

**处理**:
1. 桌面双击 `启动RAG知识库.bat`
2. 智析 Agent 重启后 session 会自动恢复已上传文件（2026-05-29 已修复 auto-recover）
3. 索引过期 → 桌面双击 `更新知识库.bat` 重建

---

## 📒 故障日志（新故障解决后当天补一行）

| 日期 | 症状 | 根因 | 解决 | 对应卡片 |
|------|------|------|------|---------|
| 2026-06-08 | 换 qwen-vl key 不生效 | 热重载不加载新 key | 完整 restart | 卡片3 |
| 2026-06-27 | DeepSeek 反复 401 | 环境变量不被 Gateway 重读 | key 硬编码进配置 | 卡片1 |
| 2026-07-04 | fallback 指向不存在的 provider | 配置错误（gpt/xxx 不存在） | 改为真实 provider 三级链 | 卡片4 |
| 2026-07-04 | deepseek-v4-pro 兜底不可用 | 当前 key 对该模型返回 403 | 临时改为 deepseek-v4-flash | 卡片4 |
| 2026-07-04 | deepseek-v4-flash 兜底不可用 | 当前 key 对 DeepSeek 系列返回 403 | 改兜底为 claude-opus-4-8 | 卡片4 |
| 2026-07-04 | claude-opus-4-8 兜底不可用 | 当前 key 对该模型返回 403 | 移除假兜底，仅保留实测可用 claude-fable-5 | 卡片4 |
| 2026-07-04 | DeepSeek 各种写法全 403 | token 只授权 gpt-5.5（/v1/models 实测） | 兜底改用 custom-cbwyy-top-v1/gpt-5.5，链为 gpt-5.5→fable-5→gpt-5.5 | 卡片4 |
