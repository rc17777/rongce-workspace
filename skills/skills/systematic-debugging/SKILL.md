---
name: systematic-debugging
description: "Four-phase systematic debugging — root cause investigation, pattern analysis, hypothesis testing, and evidence-based fix verification. Use when commands fail, scripts error, data mismatches, tools behave unexpectedly, or automation breaks. Never jump to solutions without understanding root cause. Triggers: 'debug', '报错', '排查', '哪里出问题了', '数据对不上', '脚本挂掉了', 'error', 'bug', '修复'."
---

# Systematic Debugging Skill

## Core Principle

**Never guess. Never jump to fixes.** The four-phase process ensures root cause investigation happens before any fix attempt.

## Four Phases of Debugging

### Phase 1: Gather Evidence (40% of effort)

Do NOT propose fixes. First do all of these:

1. **Reproduce the error** — Exact command, exact input, exact error message
2. **Check the obvious** — File paths exist? Permissions? Network? Disk space?
3. **Read the error** — Parse the full error stack. What line? What module? What exception type?
4. **Collect context** — Input data shape, system state, env variables, recent changes
5. **Check logs** — Application logs, system logs, debug mode output

Output: One-line summary of what failed + full error output captured

```
ERROR: ModuleNotFoundError at /script.py:12
├── Stack: ImportError -> numpy C-extensions
├── Context: Python 3.14a5, Windows, numpy 2.4.4
├── Recent: pip install matplotlib (added numpy deps)
└── Hypothesis: numpy wheel not compatible with alpha Python
```

### Phase 2: Root Cause Analysis (30% of effort)

Trace the chain:

```
Surface symptom → Direct cause → Root cause → Upstream cause
```

Use evidence triage:
- **排除法**: 变数隔离（刚改了什么？什么改了之后出问题的？）
- **二分法**: 从哪里开始能正常工作？切断链条找断点
- **类比法**: 之前类似的bug是怎么解决的？
- **最小化**: 能不能造一个最小复现案例？

### Phase 3: Fix & Verify (20% of effort)

- Propose 1 fix at a time (never shotgun fixes)
- State **why** this fix addresses the root cause
- Test the fix
- Verify: does the original error disappear?
- Verify: does anything else break?

### Phase 4: Systemic Fix (10% of effort)

- **为什么会发生？** — 系统/流程/工具的疏漏
- **怎么防止再发生？** — 自动化检查、日志增强、测试覆盖

## Debugging Commands Reference

| Scenario | Command |
|:---------|:--------|
| Check Python module path | `python -c "import sys; print('\n'.join(sys.path))"` |
| Python module version | `python -c "import X; print(X.__version__)"` |
| Node module resolve | `node -e "console.log(require.resolve('X'))"` |
| DLL dependencies | `dumpbin /dependents file.dll` |
| Disk space | `Get-PSDrive C \| Select-Object Used,Free` |
| File permission | `icacls file.txt` |
| Process list | `Get-Process -Name processname` |
| Network check | `Test-NetConnection -ComputerName host -Port port` |

## See references/debug-patterns.md for common fails and their fixes.
