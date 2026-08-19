# -*- coding: utf-8 -*-
"""api_gateway v6 接入自测：影子模式 / 正式切换 / 关闭 v6"""
import sys, os, json
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'audit-blackboard'))

os.environ.setdefault('V6_ROUTER_ENABLED', '1')
os.environ.setdefault('V6_SHADOW_MODE', '1')

import importlib
import api_gateway as gw
importlib.reload(gw)

fails = 0

def check(name, cond, detail=""):
    global fails
    if cond:
        print(f"✅ {name}")
    else:
        fails += 1
        print(f"❌ {name} {detail}")

# 1. 影子模式（默认）：返回旧路由模型 + v6 建议字段
r = gw.route_model('qa', 3, 5000)
check("影子-返回旧模型", r['model'] == 'custom-cbwyy-claude/claude-sonnet-5', f"got={r['model']}")
check("影子-带v6建议", 'v6_suggestion' in r and r.get('shadow') is True, json.dumps(r, ensure_ascii=False))
check("影子-建议字段齐全", all(k in r for k in ('v6_suggestion', 'v6_tier', 'v6_method', 'v6_reason')))

# 2. 长文档影子
r2 = gw.route_model('qa', 0, 200000)
check("影子-长文档v6建议", r2.get('v6_tier') == 'long_context', f"tier={r2.get('v6_tier')}")
check("影子-长文档实际执行", r2['model'] == 'gemini-3.1-pro-preview', f"got={r2['model']}")

# 3. 高风险成本级
r3 = gw.route_model('qa', 5, 1000)
check("影子-最高成本级v6建议", r3.get('v6_method') == 'rule', f"method={r3.get('v6_method')}")

# 4. resolve_model v6 影子
rm = gw.resolve_model(agent_name='report_writer', scenario='report_writing')
check("resolve_model-影子回落旧逻辑", rm['primary'] == 'custom-cbwyy-qwen/qwen3.7-plus', f"got={rm.get('primary')}")

# 5. 关闭 v6
os.environ['V6_ROUTER_ENABLED'] = '0'
importlib.reload(gw)
r4 = gw.route_model('qa', 3, 5000)
check("关闭v6-旧逻辑", r4['model'] == 'custom-cbwyy-claude/claude-sonnet-5' and 'v6_suggestion' not in r4, json.dumps(r4, ensure_ascii=False))
r5 = gw.route_model('qa', 0, 200000)
check("关闭v6-长文档旧逻辑", r5['model'] == 'gemini-3.1-pro-preview', f"got={r5['model']}")

# 6. 正式切换模式
os.environ['V6_ROUTER_ENABLED'] = '1'
os.environ['V6_SHADOW_MODE'] = '0'
importlib.reload(gw)
r6 = gw.route_model('qa', 3, 5000)
check("正式切换-走v6决策", r6.get('shadow') is False and 'v6_method' in r6, json.dumps(r6, ensure_ascii=False))
r7 = gw.route_model('qa', 0, 200000)
check("正式切换-长文档v6", r7['model'] == 'custom-cbwyy-gemini/gemini-3.1-pro-preview', f"got={r7['model']}")

# 7. 轨迹日志落盘验证
logf = os.path.join(gw.LOG_DIR, 'routing_trajectory.jsonl')
check("轨迹日志已落盘", os.path.exists(logf))
if os.path.exists(logf):
    n_shadow = 0
    with open(logf, encoding='utf-8') as f:
        for line in f:
            try:
                if json.loads(line).get('decision', {}).get('shadow'):
                    n_shadow += 1
            except Exception:
                pass
    check("影子决策已记录", n_shadow >= 4, f"shadow_count={n_shadow}")

print(f"\n共测试 7 组，失败 {fails} 项")
sys.exit(1 if fails else 0)
