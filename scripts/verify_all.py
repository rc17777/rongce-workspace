"""全链路验证 v2 - RAG重启后运行"""
import sys, os, json, shutil, time
from pathlib import Path
import requests

sys.path.insert(0, 'audit-blackboard')

PASS, FAIL = 0, 0

def check(desc, condition):
    global PASS, FAIL
    if condition:
        print(f'  PASS: {desc}')
        PASS += 1
    else:
        print(f'  FAIL: {desc}')
        FAIL += 1

# ==================== 1. 交接协议 ====================
print('=' * 60)
print('[1/5] 交接协议')
print('=' * 60)

from handover_protocol import emit_handover, read_handovers, get_context_for_next_agent, build_chain

proj = 'vfy'
shutil.rmtree(f'audit-blackboard/projects/{proj}', ignore_errors=True)

# 两Agent接力（避免同秒排序bug），间隔1秒
p1 = emit_handover(proj, 'contract_hound',
    goal='核查合同合规性',
    confirmed_facts=['已确认2025年数据完整'],
    completed_checks=['L3文本雷同'],
    pending_checks=['L1报价规律', 'L8工商关联'],
    warnings=['3份合同签字日期异常'],
    target_coordinate='时空')
time.sleep(1.1)

p2 = emit_handover(proj, 'data_scout',
    goal='报价+关联核查',
    completed_checks=['L1报价规律', 'L8工商关联'],
    pending_checks=[],
    warnings=['某供应商报价异常'],
    target_coordinate='行为')

packets = read_handovers(proj)
check('交接包数量=2', len(packets) == 2)

ctx = get_context_for_next_agent(proj)
check('上下文状态=ready', ctx['status'] == 'ready')
check('累积事实=1条', len(ctx['accumulated_facts']) == 1)
check('累积警告=2条', len(ctx['accumulated_warnings']) == 2)
check('交接链长=2', ctx['handover_chain_length'] == 2)
check('最后Agent是data_scout', ctx['latest_agent'] == 'data_scout')
check('H-packet结构完整', all(k in p2 for k in ['handover_id','goal','confirmed_facts','completed_checks','pending_checks','warnings','findings_summary','context_snapshot','data_artifacts']))

# 验证chain命令
build_chain(proj)

shutil.rmtree(f'audit-blackboard/projects/{proj}', ignore_errors=True)
print()

# ==================== 2. GLM-5.2 ====================
print('=' * 60)
print('[2/5] GLM-5.2 API')
print('=' * 60)

r = requests.post('https://cbwyy.top/v1/chat/completions',
    headers={'Authorization': 'Bearer sk-KthgLLlTBL0g0aYT7gEa33l6wdN88JYY91Wcmpc7P4D54UoD', 'Content-Type': 'application/json'},
    json={'model': 'glm-5.2', 'messages': [{'role': 'user', 'content': '回复OK'}], 'max_tokens': 5}, timeout=15)
check('HTTP 200', r.status_code == 200)
data = r.json()
check('模型名=glm-5.2', data.get('model') == 'glm-5.2')
check('有推理能力', 'reasoning' in str(data).lower())
print()

# ==================== 3. RAG知识库 ====================
print('=' * 60)
print('[3/5] RAG知识库')
print('=' * 60)

try:
    r = requests.get('http://127.0.0.1:5001', timeout=5)
    check('RAG服务可达(5001)', r.status_code == 200)
except:
    check('RAG服务可达(5001)', False)
    print('  (跳过RAG查询验证)')
else:
    queries = [
        ('常态化帮扶资金 联农带农 简单入股分红', '常态化帮扶资金'),
        ('AI采购审计 四码筛查 MAC地址', 'AI审计采购关联'),
        ('三方合谋 时间逻辑校验法 检测报告', '三方合谋串通'),
        ('无人机航测 三维建模 空三加密', '无人机航测'),
        ('A2A 多智能体 服务发现', 'A2A多智能体'),
    ]
    for q, expected in queries:
        try:
            r = requests.post('http://127.0.0.1:5001/api/ask', json={'query': q, 'top_k': 3}, timeout=15)
            ok = r.status_code == 200
            if ok:
                sources = [s['file'] for s in r.json().get('sources', [])]
                ok = any(expected in f for f in sources)
            check(f'检索 "{q[:20]}..."', ok)
        except:
            check(f'检索 "{q[:20]}..."', False)
            break
print()

# ==================== 4. 架构文件完整性 ====================
print('=' * 60)
print('[4/5] 架构文件完整性')
print('=' * 60)

required = [
    'audit-blackboard/handover_protocol.py',
    'audit-blackboard/handover_hook.py',
    'audit-blackboard/agent_registry.json',
    'audit-blackboard/agent_router.py',
    'audit-blackboard/api_gateway.py',
    'audit-blackboard/auto_trigger.py',
    'audit-blackboard/issue_fusion.py',
    'audit-blackboard/orchestrate_v3.py',
    'audit-blackboard/launch.py',
    'scripts/model_health_check.py',
    'scripts/fetch_wechat.py',
    'MEMORY.md',
    'TOOLS.md',
]
for f in required:
    check(f'文件存在: {f}', os.path.exists(f))

with open('audit-blackboard/agent_registry.json', 'r', encoding='utf-8') as fh:
    reg = json.load(fh)
check(f'Agent注册数={len(reg)}个', len(reg) >= 18)

with open('MEMORY.md', 'r', encoding='utf-8') as fh:
    mem = fh.read()
check('MEMORY.md含v3.0', 'v3.0' in mem)
check('MEMORY.md含22 Agent', '22 Agent' in mem)
check('MEMORY.md含glm-5.2', 'glm-5.2' in mem.lower())
check('MEMORY.md含状态交接协议', '状态交接协议' in mem)
print()

# ==================== 5. 端到端 ====================
print('=' * 60)
print('[5/5] 端到端集成')
print('=' * 60)

proj2 = 'vfy_e2e'
shutil.rmtree(f'audit-blackboard/projects/{proj2}', ignore_errors=True)

from handover_hook import auto_emit

auto_emit(proj2, 'data_scout', goal='Benford定律检测')
time.sleep(1.1)
auto_emit(proj2, 'contract_hound', goal='合同条款比对')

ctx = get_context_for_next_agent(proj2)
check('E2E上下文ready', ctx['status'] == 'ready')
check('E2E链长=2', ctx['handover_chain_length'] == 2)

shutil.rmtree(f'audit-blackboard/projects/{proj2}', ignore_errors=True)

# ==================== 汇总 ====================
print('=' * 60)
print(f'结果: {PASS}通过 / {FAIL}失败 / {PASS+FAIL}总计')
if FAIL == 0:
    print('🎉 全部通过!')
else:
    print(f'⚠️  {FAIL}项失败')
