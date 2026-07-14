# OpenClaw 重装前后差异分析报告

## 基本信息
- **备份配置**: 2026-06-19 05:23:07 (旧配置，备份于 .openclaw_bak)
- **当前配置**: 2026-06-23 16:18:47 (新配置，当前运行)
- **分析时间**: 2026-06-24 00:31

---

## 🔴 重大差异

### 1. 模型配置完全重构

#### 旧配置 (6月19日备份)
| 提供商 | 模型 | API Key |
|--------|------|---------|
| deepseek | deepseek-chat, deepseek-v4-pro, deepseek-v4-flash | sk-88b3f67de2aa44098176e57a990ec15d |
| dashscope | qwen-vl-max (图片) | sk-9868405445c84e07893acfdddc36f8a1 |
| openrouter | Nemotron 120B, GPT-OSS 120B, Gemma 4 31B, Nex N2 Pro, Nemotron VL 12B | sk-or-v1-5ed2a414... |
| custom-www-aigeek-life | Gemini 3.5 Flash | sk-4FXV7kfMxi5... |

#### 当前配置 (6月23日)
| 提供商 | 模型 | API Key |
|--------|------|---------|
| deepseek | deepseek-v4-Pro (仅1个) | sk-9a42c43969294b099218440cb37ef6db |
| kimi-coding | kimi-for-coding, kimi k2.7 | proxy-managed |

**⚠️ 丢失的模型**: dashscope(qwen-vl-max), openrouter(5个免费模型), custom-aigeek-life(Gemini)
**⚠️ 丢失的API Key**: 旧deepseek key, dashscope key, openrouter key, aigeek-life key

---

### 2. Agent配置丢失

#### 旧配置
- **主助手**: workspace = D:\openclaw-workspace
- **审计数据分析师**: audit-data-analyst, 专用模型 deepseek-chat, 绑定5个技能
- **模型别名**: DeepSeek, DeepSeek V4 Pro, DeepSeek V4 Flash, Nemotron 120B Free, GPT-OSS 120B Free, Gemma 4 31B Free
- **图片模型**: dashscope/qwen-vl-max
- **PDF模型**: dashscope/qwen-vl-max

#### 当前配置
- **主助手**: 无workspace配置
- **审计数据分析师**: ❌ 丢失
- **模型别名**: ❌ 全部丢失
- **图片模型**: ❌ 未配置
- **PDF模型**: ❌ 未配置

---

### 3. 插件配置变化

#### 旧配置
- browser: ✅ enabled
- deepseek: ✅ enabled
- google: ❌ disabled
- openclaw-weixin: ✅ enabled
- openrouter: ✅ enabled
- **slots**: contextEngine = "legacy"

#### 当前配置
- browser: ❌ disabled (注意：从enabled变成disabled)
- deepseek: ✅ enabled
- kimi: ✅ enabled (新增)
- kimi-search: ✅ enabled (新增)
- openclaw-weixin: ✅ enabled
- openrouter: ❌ 丢失
- google: ❌ 丢失
- **slots**: ❌ 丢失

---

### 4. 工具配置丢失

#### 旧配置
- elevated权限: ✅ enabled, 允许特定用户
- media图片: ✅ enabled, dashscope/qwen-vl-max
- profile: full

#### 当前配置
- elevated权限: ❌ 丢失
- media图片: ❌ 丢失
- profile: full

---

### 5. Gateway配置变化

#### 旧配置
- port: 18789
- bind: lan
- auth token: 98a0501b693705ae7851c48175f09e702bbf3e70f3e9c73e
- tailscale: off
- nodes: denyCommands = []
- controlUi: allowInsecureAuth = true

#### 当前配置
- port: ❌ 未配置 (默认)
- bind: ❌ 未配置 (默认)
- auth token: af9c552ecebf7232ca4649be1a288aa7
- tailscale: ❌ 丢失
- nodes: ❌ 丢失
- controlUi: ❌ allowInsecureAuth丢失

---

### 6. 环境变量丢失

#### 旧配置
- OPENROUTER_API_KEY: sk-or-v1-5ed2a414...
- SILICONFLOW_API_KEY: sk-kebaysavoefufudnqvioprgdiegtugylsgzieswpeulivcjo

#### 当前配置
- ❌ 所有环境变量丢失

---

### 7. 技能配置变化

#### 旧配置
- 大量系统技能: discord, gog, 1password, apple-notes, apple-reminders, bear-notes, blogwatcher, blucli, bluebubbles, camsnap, capability-evolver, coding-agent, eightctl, gemini, gh-issues, gifgrep, github, goplaces, himalaya, imsg, linkedin-autopilot, mcporter, model-usage, nano-pdf, notion, obsidian, openai-whisper, openai-whisper-api, openhue, oracle, ordercli, peekaboo, sag, session-logs, sherpa-onnx-tts, skill-vetter, slack, songsee, sonoscli, spotify-player, summarize, things-mac, tmux, trello, video-frames, voice-call, wacli, wecom-send-media, wecom-send-template-card, xurl
- 大多数为 disabled 状态

#### 当前配置
- 82个自定义审计技能: agent-browser-stagehand, agent-data-standard, aloudata-anomaly-detection, analysis-report, apriori-audit, arch-diagrammer, audit-card-generator, audit-data-analysis-methods, audit-jingze, audit-knowledge-graph, audit-meeting-review, audit-report-review, audit-text-mining, bid-document, brainstorming, browser, budget-audit, content-polish, copy-editing, copywriting, cot-capture, data-analyst-cn, deepseek-charting, digital-audit-methodology, disk-cleaner, doc-formatter, drawio, energy-audit, engineering-audit, financial-fraud-detection, first-principles-audit, forecast-simulation, github, gov-audit-methodology, humanizer, hv-analysis, illustration-analysis, image-classifier-audit, khazix-writer, magazine-knowledge, magazine-knowledge-bridge, markdown-converter, memory-manager, memory-setup, nano-banana-pro, news-aggregator, note, openai-whisper, openclaw-find-skills, openclaw-skill-vetter, patent-disclosure-skill, pdf, ppt-generator, proactive-agent, procurement-audit-models, prompt-librarian, reflection, regulatory-audit-response, scheduled-report, skill-manager, skill-vetter, spatial-audit-analysis, special-fund-audit, sql-dataviz, sql-master, sql-report-generator, sql-toolkit, subsidy-audit, summarize-pro, systematic-debugging, tavily, tender-analyzer-agent, unstructured-audit-data, video-creator, video-frames, video-toolkit, visual-toolkit, wiki-auto-ingest, workflow-embedder, xiucheng-self-improving-agent
- 全部为 enabled 状态

---

### 8. 新增配置 (当前有但旧配置没有)

- **memorySearch**: 启用，使用 bge_m3_embed 模型，远程服务
- **compaction**: safeguard 模式 (旧配置也有，但结构不同)
- **commands**: native, nativeSkills, restart, ownerDisplay
- **messages**: ackReactionScope
- **subagents**: maxConcurrent = 8

---

### 9. 会话配置丢失

#### 旧配置
- dmScope: per-channel-peer
- reset: mode = idle, idleMinutes = 43200

#### 当前配置
- ❌ 丢失

---

### 10. Browser配置丢失

#### 旧配置
- defaultProfile: "openclaw"

#### 当前配置
- ❌ 丢失

---

## 📊 总结

### 丢失的重要配置 (需要恢复)
1. **模型**: dashscope(qwen-vl-max), openrouter(5个免费模型), custom-aigeek-life
2. **API Keys**: 旧deepseek key, dashscope key, openrouter key, siliconflow key
3. **Agent**: 审计数据分析师助手
4. **Workspace路径**: D:\openclaw-workspace
5. **模型别名**: 6个别名配置
6. **图片/PDF模型**: qwen-vl-max
7. **插件**: openrouter, google, browser(从enabled变disabled)
8. **工具权限**: elevated权限, media图片
9. **Gateway**: port 18789, bind lan, tailscale, nodes, allowInsecureAuth
10. **环境变量**: OPENROUTER_API_KEY, SILICONFLOW_API_KEY
11. **会话**: dmScope, reset配置
12. **Browser**: defaultProfile

### 新增的配置 (已同步)
1. **kimi-coding**: kimi-for-coding, kimi k2.7
2. **kimi-search**: 搜索和fetch插件
3. **82个自定义审计技能**
4. **memorySearch**: 向量搜索
5. **subagents**: 并发配置

### 需要手动恢复的建议
1. 重新配置 dashscope (qwen-vl-max) 用于图片识别
2. 重新配置 openrouter 免费模型作为备用
3. 恢复审计数据分析师助手
4. 恢复环境变量
5. 恢复 gateway 端口和绑定配置
6. 启用 browser 插件
7. 恢复 elevated 权限配置

---

*报告生成时间: 2026-06-24 00:31*
