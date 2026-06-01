---
name: skill-vetter
version: 1.0.0
description: Security-first skill vetting for AI agents. Use before installing any skill from ClawdHub, GitHub, or other sources. Checks for red flags, permission scope, and suspicious patterns.
---

# Skill Vetter 🔒

Security-first vetting protocol for AI agent skills. **Never install a skill without vetting it first.**

## When to Use

- Before installing any skill from ClawdHub
- Before running skills from GitHub repos
- When evaluating skills shared by other agents
- Anytime you're asked to install unknown code

## Vetting Protocol

### Step 1: Source Check

```
Questions to answer:
- [ ] Where did this skill come from?
- [ ] Is the author known/reputable?
- [ ] How many downloads/stars does it have?
- [ ] When was it last updated?
- [ ] Are there reviews from other agents?
```

### Step 2: Code Review (MANDATORY)

Read ALL files in the skill. Check for these **RED FLAGS**:

```
🚨 REJECT IMMEDIATELY IF YOU SEE:
─────────────────────────────────────────
• curl/wget to unknown URLs
• Sends data to external servers
• Requests credentials/tokens/API keys
• Reads ~/.ssh, ~/.aws, ~/.config without clear reason
• Accesses MEMORY.md, USER.md, SOUL.md, IDENTITY.md
• Uses base64 decode on anything
• Uses eval() or exec() with external input
• Modifies system files outside workspace
• Installs packages without listing them
• Network calls to IPs instead of domains
• Obfuscated code (compressed, encoded, minified)
• Requests elevated/sudo permissions
• Accesses browser cookies/sessions
• Touches credential files
─────────────────────────────────────────
```

### Step 3: Permission Scope

```
Evaluate:
- [ ] What files does it need to read?
- [ ] What files does it need to write?
- [ ] What commands does it run?
- [ ] Does it need network access? To where?
- [ ] Is the scope minimal for its stated purpose?
```

### Step 4: Risk Classification

| Risk Level | Examples | Action |
|------------|----------|--------|
| 🟢 LOW | Notes, weather, formatting | Basic review, install OK |
| 🟡 MEDIUM | File ops, browser, APIs | Full code review required |
| 🔴 HIGH | Credentials, trading, system | Human approval required |
| ⛔ EXTREME | Security configs, root access | Do NOT install |

### Step 5: Professional Quality Check

> skill是容器，专业经验才是内容。安全检查只管有没有毒，不管有没有用。

等级：
- 专业级：有明确专家来源+质量标准+质量门（如deep-research）→ 优先采用
- 可用级：有清晰描述+步骤，但无严格质量门 → 安装使用
- 模板级：纯prompt包装，无专业判断注入 → 可用但不期待出彩
- 空壳级：描述模糊、步骤缺失 → 拒绝安装

审查清单：
1. 这个skill背后是谁的专业经验？
2. 质量标准有没有写进skill？
3. 有没有写死的质量门/人工停点？
4. 和已有skill有没有重叠？

核心判断：AI工具人人都在用的时候，"用AI"不是竞争力。
竞争力是：谁能告诉AI"做到什么程度才叫做好了"。

## Output Format

After vetting, produce this report:

```
SKILL VETTING REPORT
═══════════════════════════════════════
Skill: [name]
Source: [ClawdHub / GitHub / other]
Author: [username]
Version: [version]
───────────────────────────────────────
METRICS:
• Downloads/Stars: [count]
• Last Updated: [date]
• Files Reviewed: [count]
───────────────────────────────────────
RED FLAGS: [None / List them]

PERMISSIONS NEEDED:
• Files: [list or "None"]
• Network: [list or "None"]  
• Commands: [list or "None"]
───────────────────────────────────────
RISK LEVEL: [🟢 LOW / 🟡 MEDIUM / 🔴 HIGH / ⛔ EXTREME]

VERDICT: [✅ SAFE TO INSTALL / ⚠️ INSTALL WITH CAUTION / ❌ DO NOT INSTALL]

NOTES: [Any observations]
═══════════════════════════════════════
```

## Quick Vet Commands

For GitHub-hosted skills:
```bash
# Check repo stats
curl -s "https://api.github.com/repos/OWNER/REPO" | jq '{stars: .stargazers_count, forks: .forks_count, updated: .updated_at}'

# List skill files
curl -s "https://api.github.com/repos/OWNER/REPO/contents/skills/SKILL_NAME" | jq '.[].name'

# Fetch and review SKILL.md
curl -s "https://raw.githubusercontent.com/OWNER/REPO/main/skills/SKILL_NAME/SKILL.md"
```

## Trust Hierarchy

1. **Official OpenClaw skills** → Lower scrutiny (still review)
2. **High-star repos (1000+)** → Moderate scrutiny
3. **Known authors** → Moderate scrutiny
4. **New/unknown sources** → Maximum scrutiny
5. **Skills requesting credentials** → Human approval always

## Remember

- No skill is worth compromising security
- When in doubt, don't install
- Ask your human for high-risk decisions
- Document what you vet for future reference

---

*Paranoia is a feature.* 🔒🦀


## Audit Case Quality Standard

> 新建/更新审计案例时必须附带"逻辑链"

### 案例逻辑链格式（标准动作）

每个审计案例必须包含完整逻辑链：

```
数据异常 → 追问趋势 → 节点收敛 → 人物关联 → 证据闭环 → 违法事实
```

示例（丁某案）：
```
合同三不一致 → 追问真实项目 → 银行流水节点(关联公司) →
查工商信息人物关联(董事长=丁某) → 银行流水SQL比对(10笔未入账) →
询问笔录+银行打印件+合同复印件 → 挪用公款1800万
```

### 逻辑链评审标准

| 检查项 | 通过条件 |
|--------|---------|
| 每步有明确操作 | 不能只写"发现问题"，必须写怎么发现的 |
| 每步有明确数据 | 具体到字段/SQL/对比维度 |
| 节点收敛 | 从多个信号逐步收敛到一个具体的"坏人/坏行为" |
| 证据闭环 | 数据+现场+笔录三证齐全 |
