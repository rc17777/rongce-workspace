# 三台电脑 OpenClaw 同步指南

## 架构

```
GitHub: rc17777/rongce-workspace (私有仓库)
  ├── AGENTS.md / SOUL.md / USER.md / MEMORY.md    ← 身份与记忆
  ├── HEARTBEAT.md / TOOLS.md / IDENTITY.md         ← 心跳任务与配置
  ├── memory/*.md                                   ← 每日日志
  ├── skills/                                       ← 技能库
  ├── knowledge/ / references/ / articles/          ← 知识库
  ├── scripts/                                      ← 脚本
  ├── audit-plugin/                                 ← 审计插件
  ├── agents/                                       ← Agent 定义
  ├── config/openclaw-shared.yaml                   ← OpenClaw 共享配置
  └── ai-word-skill/                                ← AI Word 工具
```

## 新电脑初始化步骤

### 1. 安装 OpenClaw
```powershell
npm install -g openclaw
```

### 2. 克隆工作区
```powershell
cd D:\
git clone https://github.com/rc17777/rongce-workspace.git openclaw-workspace
```

### 3. 配置 API 密钥（每台电脑独立）
在 `D:\openclaw-workspace\.env` 中填入（此文件已加入 .gitignore）：

```
DEEPSEEK_API_KEY=sk-your-deepseek-key
DASHSCOPE_API_KEY=sk-your-dashscope-key
GEMINI_API_KEY=your-gemini-key
```

### 4. 合并共享配置
```powershell
# 将共享配置合并到 OpenClaw 配置
openclaw config apply D:\openclaw-workspace\config\openclaw-shared.yaml
```

> 注意：如果 workspace 路径不是 `D:\openclaw-workspace`，需先修改 `openclaw-shared.yaml` 中的路径。

### 5. 安装工作区技能依赖
```powershell
pip install -r D:\openclaw-workspace\requirements.txt
```

### 6. 启动
```powershell
openclaw gateway start
```

## 日常使用

- **自动同步**: cron 每4小时 + 重要操作后自动 git push
- **拉取更新**: 每台电脑启动前 `git pull`（或在 `config/` 下配置启动脚本）
- **冲突处理**: 如有冲突以 GitHub 版本为准

## 不同步的内容（每台电脑独立）

| 内容 | 原因 |
|------|------|
| API Keys (`.env`) | 安全，已 gitignore |
| `openclaw.json` 中的 token/auth | 安全 |
| `output/` | 大文件/项目产出 |
| `projects/` | 客户敏感数据 |
| `secrets/` | 凭证 |
| `node_modules/`, `__pycache__/`, `temp/` | 依赖/缓存 |

## 从其他电脑拉取最新数据

```powershell
cd D:\openclaw-workspace
git pull origin master
# 如有新技能，安装依赖
pip install -r requirements.txt
```
