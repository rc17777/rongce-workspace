# Nacos Skill Registry — AI Agent 团队协作的 Skill 共享仓库

**来源**: 微信公众号「Vibe With Agents」，作者：吃瓜的小V
**日期**: 2026-07-06
**原文**: https://mp.weixin.qq.com/s/CsWy8Oevzt0Py0FMY6uH6Q

---

## 核心论点

AI Agent 进入团队后，真正麻烦的不是"AI 会不会干活"，而是好的 Skill（提示词+工作流）怎么在团队里共享。复制粘贴"我发你一份"撑不了几天——版本混乱、安全审核缺失、新人拿不到、改了没人知道。

## Nacos Skill Registry

阿里 2018 年开源的 Nacos（服务发现+配置管理平台），在 3.x 版本扩展到 AI 管理：Skill、Agent、MCP Server、Prompt、AgentSpec 的统一仓库。

### 核心价值
- **团队共享**：一次创建，全队使用
- **版本控制**：draft → reviewing → online → offline
- **安全保障**：Pipeline 自动扫描 Prompt 注入/数据泄露/恶意代码
- **灵活分发**：CLI / API / SDK
- **可见性控制**：PUBLIC / PRIVATE

### 实操流程
1. 部署 Nacos Server（3.2.0+，单机/Docker/K8s）
2. 控制台 → AI 注册中心 → Skill 管理
3. 创建 Skill（手动/AI Copilot/上传 ZIP，标准目录含 SKILL.md + scripts/ + references/ + assets/）
4. 配置发布流程 + 安全扫描（skill-scanner 插件）
5. 安装 CLI：`npm install -g @nacos-group/cli` 或 `npx @nacos-group/cli`
6. 上传→审核→发布：`skill-upload` → `skill-review` → `skill-release`
7. 团队拉取同步：`skill-get` / `skill-sync` / `skill-sync --all`

### 平替方案

| 方案 | 优点 | 缺点 |
|------|------|------|
| Agent CLI 本地映射 | 快，零基础设施 | 依赖本地环境，缺版本管理，烧 token |
| Git 仓库 | 有版本历史，能 Review | 非 Skill 专用分发，仍需手动复制 |

## 关键启示

> "当每个人都在写 Prompt 时，团队真正需要的不是更多 Prompt，而是一套能被共用、被迭代、被审核、被分发的 Skills 体系。"

### 参考链接
- Nacos Skill 管理: https://nacos.io/docs/latest/manual/user/ai/skill-registry/
- Nacos 概览: https://nacos.io/docs/latest/overview/
- Nacos CLI 指南: https://nacos.io/docs/latest/manual/admin/nacos-cli/
- Nacos 单机部署: https://nacos.io/docs/latest/manual/admin/deployment/deployment-standalone/
