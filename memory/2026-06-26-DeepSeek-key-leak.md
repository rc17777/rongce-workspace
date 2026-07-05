# DeepSeek API Key 更换记录
## 2026-06-26 11:00-12:00

### 问题
- 旧key `sk-dbc61...` 被泄露/盗用，3天（6/24-6/26）烧了¥1,213
- 其中约85%的调用量非OpenClaw主系统产生

### 已更换的Key

| 系统 | 旧Key | 新Key | 操作 |
|------|-------|-------|------|
| OpenClaw主配置 | sk-dbc61... | sk-7d5037... | ✅ 已更新 |
| RAG知识库 | sk-dbc61... | sk-7d5037... | ✅ 已更新 |
| 融策Agent | sk-88b3... | sk-7d5037... | ✅ 已更新+重启 |

### 更新的文件
- `~/.openclaw/openclaw.json`
- `scripts/rag_server.py`
- `scripts/rag_query.py`
- `scripts/rag_web.py`
- `projects/data-analysis-agent/LLM/llm_config.json`

### DeepSeek平台操作
- ✅ 已删除旧key `sk-dbc61...`
- ✅ 已删除旧key `sk-88b3...`

### 下一步监控
- 明天检查DeepSeek费用，应大幅降低到正常水平
- 如仍异常，继续排查其他程序
