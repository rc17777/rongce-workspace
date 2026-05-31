# HEARTBEAT.md

# Keep this file empty (or with only comments) to skip heartbeat API calls.

# Add tasks below when you want the agent to check something periodically.

---

## Periodic Checks (Rotate through these)

### 1. Weather Check (Every 4 hours)
- Check current weather for Shanghai
- useful if user might go out

### 2. System Status (Every 2 hours)
- Check OpenClaw gateway status
- Check session usage/time

### 3. Memory Maintenance (Every 3 days)
- Read recent memory/YYYY-MM-DD.md files
- Identify learnings worth keeping
- Update MEMORY.md with distilled insights

### 4. Self-Improving Review (Every 5 days)
- Read C:\Users\Admin\self-improving\memory.md
- Check C:\Users\Admin\self-improving\corrections.md for new entries
- Review recent learnings
- Update memory.md

---

## Active Tasks During Heartbeats

When polled, rotate through checks above. Track last check in `memory/heartbeat-state.json`.

**When to alert user:**
- System status abnormal
- Important weather changes
- Significant learnings to share

**Stay quiet when:**
- Late night (23:00-08:00) unless urgent
- Nothing new since last check
- Recent check (<30 min ago)