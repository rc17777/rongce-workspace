"""
融策审计中台 - 统一 Audit API Gateway
======================================
统一入口，串联 RAG → LLM → Tool → Validate 全链路。
14模型智能路由 + 预算监控 + 工作流编排。

用法:
    python audit-blackboard/api_gateway.py --port 5002
"""

import os, sys, json, time, hashlib, traceback
import urllib.request
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

WORKSPACE = os.environ.get(
    'OPENCLAW_WORKSPACE',
    r'C:\Users\15528\.openclaw\workspace-main'
    if os.path.exists(r'C:\Users\15528\.openclaw\workspace-main')
    else r'C:\Users\scrccpa\.openclaw\workspace'
)
LOG_DIR = os.path.join(WORKSPACE, 'logs')
os.makedirs(LOG_DIR, exist_ok=True)

# ====== 模型路由配置 v5.0 ======
# 双层路由：Agent路由 > 场景路由 > 全局默认
# 参考：config/model_routing_v5.py

# Agent级路由（22个Agent各自偏好）
AGENT_MODEL_MAP = {
    # 核心审计
    'data_scout':       {'primary': 'custom-cbwyy-top-v1/deepseek-v4-pro',     'fallbacks': ['custom-cbwyy-top-v1/deepseek-v4-flash']},
    'contract_hound':   {'primary': 'custom-cbwyy-claude/claude-sonnet-5',     'fallbacks': ['custom-cbwyy-top-v1/deepseek-v4-pro', 'custom-cbwyy-qwen/qwen3.7-plus']},
    'bid_hunter':       {'primary': 'custom-cbwyy-top-v1/deepseek-v4-pro',     'fallbacks': ['custom-cbwyy-top-v1/deepseek-v4-flash', 'custom-cbwyy-kimi/kimi-k3']},
    'law_inspector':    {'primary': 'custom-cbwyy-claude/claude-sonnet-5',     'fallbacks': ['custom-cbwyy-qwen/qwen3.7-plus', 'custom-cbwyy-top-v1/deepseek-v4-pro']},
    'workpaper_crafter':{'primary': 'custom-cbwyy-qwen/qwen3.7-plus',          'fallbacks': ['custom-cbwyy-top-v1/deepseek-v4-pro', 'custom-cbwyy-gpt55/gpt-5.5']},
    'report_writer':    {'primary': 'custom-cbwyy-qwen/qwen3.7-plus',          'fallbacks': ['custom-cbwyy-claude/claude-sonnet-5', 'custom-cbwyy-gpt55/gpt-5.5']},
    'review_sentinel':  {'primary': 'custom-cbwyy-claude/claude-sonnet-5',     'fallbacks': ['custom-cbwyy-opus/claude-opus-4-8', 'custom-cbwyy-qwen/qwen3.7-plus']},
    # 工程咨询
    'budget_estimator': {'primary': 'custom-cbwyy-top-v1/deepseek-v4-pro',     'fallbacks': ['custom-cbwyy-top-v1/deepseek-v4-flash']},
    'settlement_auditor':{'primary': 'custom-cbwyy-top-v1/deepseek-v4-pro',    'fallbacks': ['custom-cbwyy-claude/claude-sonnet-5']},
    'fiscal_reviewer':  {'primary': 'custom-cbwyy-claude/claude-sonnet-5',     'fallbacks': ['custom-cbwyy-qwen/qwen3.7-plus', 'custom-cbwyy-top-v1/deepseek-v4-pro']},
    # 绩效评价
    'performance_evaluator': {'primary': 'custom-cbwyy-top-v1/deepseek-v4-pro','fallbacks': ['custom-cbwyy-claude/claude-sonnet-5']},
    # 专项检测
    'expert_bias_detector': {'primary': 'custom-cbwyy-top-v1/deepseek-v4-pro', 'fallbacks': ['custom-cbwyy-kimi/kimi-k3', 'custom-cbwyy-glm/glm-5.2']},
    'meeting_minutes_analyzer': {'primary': 'custom-cbwyy-qwen/qwen3.7-plus',  'fallbacks': ['custom-cbwyy-top-v1/deepseek-v4-pro']},
    # 数据运维
    'ocr_processor':    {'primary': 'custom-cbwyy-top-v1/deepseek-v4-flash',   'fallbacks': ['custom-cbwyy-qwen/qwen3.7-plus']},
    'data_classifier':  {'primary': 'custom-cbwyy-top-v1/deepseek-v4-flash',   'fallbacks': ['custom-cbwyy-top-v1/deepseek-v4-pro']},
    'data_desensitizer':{'primary': 'custom-cbwyy-top-v1/deepseek-v4-flash',   'fallbacks': ['custom-cbwyy-top-v1/deepseek-v4-pro']},
    'adjustment_scribe':{'primary': 'custom-cbwyy-top-v1/deepseek-v4-pro',     'fallbacks': ['custom-cbwyy-claude/claude-sonnet-5']},
    # 方案撰写
    'plan_writer':      {'primary': 'custom-cbwyy-qwen/qwen3.7-plus',          'fallbacks': ['custom-cbwyy-gpt55/gpt-5.5', 'custom-cbwyy-claude/claude-sonnet-5']},
}

# 场景路由（按任务类型）
MODEL_ROUTES = {
    'daily_chat':       {'primary': 'custom-cbwyy-top-v1/deepseek-v4-flash', 'fallbacks': ['custom-cbwyy-top-v1/deepseek-v4-pro']},
    'heartbeat_task':   {'primary': 'custom-cbwyy-top-v1/deepseek-v4-flash', 'fallbacks': []},
    'data_check':       {'primary': 'custom-cbwyy-top-v1/deepseek-v4-pro',   'fallbacks': ['custom-cbwyy-top-v1/deepseek-v4-flash', 'custom-cbwyy-kimi/kimi-k3']},
    'financial_analysis':{'primary': 'custom-cbwyy-top-v1/deepseek-v4-pro',  'fallbacks': ['custom-cbwyy-claude/claude-sonnet-5', 'custom-cbwyy-kimi/kimi-k3']},
    'compliance_check': {'primary': 'custom-cbwyy-claude/claude-sonnet-5',   'fallbacks': ['custom-cbwyy-qwen/qwen3.7-plus', 'custom-cbwyy-opus/claude-opus-4-8']},
    'law_interpretation':{'primary': 'custom-cbwyy-claude/claude-sonnet-5',  'fallbacks': ['custom-cbwyy-qwen/qwen3.7-plus', 'custom-cbwyy-top-v1/deepseek-v4-pro']},
    'gov_document':     {'primary': 'custom-cbwyy-qwen/qwen3.7-plus',        'fallbacks': ['custom-cbwyy-claude/claude-sonnet-5', 'custom-cbwyy-gemini/gemini-3.1-pro-preview']},
    'report_writing':   {'primary': 'custom-cbwyy-qwen/qwen3.7-plus',        'fallbacks': ['custom-cbwyy-claude/claude-sonnet-5', 'custom-cbwyy-gpt55/gpt-5.5']},
    'creative':         {'primary': 'custom-cbwyy-luna/gpt-5.6-luna',        'fallbacks': ['custom-cbwyy-sol/gpt-5.6-sol', 'custom-cbwyy-terra/gpt-5.6-terra']},
    'long_document':    {'primary': 'custom-cbwyy-gemini/gemini-3.1-pro-preview','fallbacks': ['custom-cbwyy-qwen/qwen3.7-plus', 'custom-cbwyy-top-v1/deepseek-v4-pro']},
    'english':          {'primary': 'custom-cbwyy-gpt55/gpt-5.5',            'fallbacks': ['custom-cbwyy-claude/claude-sonnet-5']},
    'final_review':     {'primary': 'custom-cbwyy-claude/claude-sonnet-5',   'fallbacks': ['custom-cbwyy-opus/claude-opus-4-8']},
    'china_reasoning':  {'primary': 'custom-cbwyy-kimi/kimi-k3',             'fallbacks': ['custom-cbwyy-glm/glm-5.2', 'custom-cbwyy-top-v1/deepseek-v4-pro']},
    'lightweight':      {'primary': 'custom-cbwyy-top-v1/deepseek-v4-flash', 'fallbacks': ['custom-cbwyy-top-v1/deepseek-v4-pro']},
}

# 全局默认（终极兜底）
GLOBAL_FALLBACKS = [
    'custom-cbwyy-top-v1/deepseek-v4-pro',
    'custom-cbwyy-gemini/gemini-3.1-pro-preview',
    'custom-cbwyy-qwen/qwen3.7-plus',
    'custom-cbwyy-fable/claude-fable-5',
    'custom-cbwyy-claude/claude-sonnet-5',
    'custom-cbwyy-gpt55/gpt-5.5',
    'custom-cbwyy-luna/gpt-5.6-luna',
    'custom-cbwyy-sol/gpt-5.6-sol',
    'custom-cbwyy-terra/gpt-5.6-terra',
    'custom-cbwyy-kimi/kimi-k3',
    'custom-cbwyy-glm/glm-5.2',
    'custom-cbwyy-doubao/doubao-seed-2.0-lite',
    'deepseek-direct/deepseek-chat',
]

# ====== v6 路由接入（四信号×四方法，config/model_routing_v6.py）======
# 开关（环境变量可覆盖）：
#   V6_ROUTER_ENABLED=0  关闭 v6，完全走旧逻辑
#   V6_SHADOW_MODE=0     退出影子模式：v6 决策真正生效
V6_ROUTER_ENABLED = os.environ.get('V6_ROUTER_ENABLED', '1') == '1'
V6_SHADOW_MODE = os.environ.get('V6_SHADOW_MODE', '1') == '1'


def _load_v6_router():
    """加载 v6 路由模块；失败返回 None（不影响旧逻辑）"""
    try:
        if WORKSPACE not in sys.path:
            sys.path.insert(0, WORKSPACE)
        from config.model_routing_v6 import Router
        return Router(log_path=os.path.join(LOG_DIR, 'routing_trajectory.jsonl'))
    except Exception:
        return None


_v6_router = _load_v6_router()

# error_cost_level → v6 场景映射（影子对比和正式切换共用）
COST_LEVEL_TO_SCENARIO = {
    0: 'lightweight',
    1: 'data_check',
    2: 'gov_document',
    3: 'compliance_check',
    4: 'final_review',
    5: 'final_review',
    'consulting': 'consulting',
}

# 旧路由的错误代价 → 场景映射（修复：原代码引用不存在的 cost_* 键会 KeyError）
_LEGACY_LEVEL_MAP = {
    0: 'lightweight',
    1: 'data_check',
    2: 'gov_document',
    3: 'compliance_check',
    4: 'final_review',
    5: 'final_review',
}


def _legacy_route(task_type, error_cost_level, spent, context_length=0):
    """旧路由逻辑（v6 关闭或影子模式下的实际执行模型）"""
    # 长文档（v6 关闭时保留此能力）
    if context_length > 128000:
        return {'model': 'gemini-3.1-pro-preview', 'reason': 'long_context', 'budget_spent': spent}
    if error_cost_level == 'consulting':
        model = MODEL_ROUTES['consulting']['primary']
        reason = 'consulting'
    else:
        scenario = _LEGACY_LEVEL_MAP.get(error_cost_level, 'lightweight')
        cfg = MODEL_ROUTES.get(scenario, MODEL_ROUTES['lightweight'])
        model = cfg['primary']
        reason = 'standard'
    if spent > DAILY_BUDGET * BUDGET_WARN:
        reason = 'budget_warning'
        if error_cost_level in (0, 1):
            model = MODEL_ROUTES['lightweight']['primary']
    return {'model': model, 'reason': reason, 'budget_spent': spent}


def resolve_model(agent_name=None, scenario=None):
    """双层路由：Agent优先，场景兜底，全局保底（v6 启用时先问 v6）"""
    if _v6_router and V6_ROUTER_ENABLED:
        v6d = _v6_router.route({
            'task_id': f'gw-{int(time.time() * 1000)}',
            'agent': agent_name or None,
            'scenario': scenario or None,
            'shadow': V6_SHADOW_MODE,
        })
        if not V6_SHADOW_MODE:
            return {'primary': v6d['model'], 'fallbacks': v6d['chain'][1:],
                    'v6_method': v6d['method'], 'v6_reason': v6d['reason']}
    if agent_name:
        for key in AGENT_MODEL_MAP:
            if key in agent_name.lower() or agent_name.lower() in key:
                return AGENT_MODEL_MAP[key]
    if scenario and scenario in MODEL_ROUTES:
        return MODEL_ROUTES[scenario]
    return {'primary': None, 'fallbacks': GLOBAL_FALLBACKS}

# 预算控制
DAILY_BUDGET = 100  # ¥/天
BUDGET_WARN = 0.7
BUDGET_CUTOFF = 0.9

# ====== 调用日志 ======
def log_call(model, task_type, tokens_in, tokens_out, cost_est, duration_ms):
    entry = {
        'timestamp': datetime.now().isoformat(),
        'model': model,
        'task_type': task_type,
        'tokens_in': tokens_in,
        'tokens_out': tokens_out,
        'cost_est': cost_est,
        'duration_ms': duration_ms,
    }
    logfile = os.path.join(LOG_DIR, 'api_gateway.jsonl')
    with open(logfile, 'a', encoding='utf-8') as f:
        f.write(json.dumps(entry, ensure_ascii=False) + '\n')

def daily_cost():
    """计算今日累计费用"""
    logfile = os.path.join(LOG_DIR, 'api_gateway.jsonl')
    if not os.path.exists(logfile):
        return 0.0
    today = datetime.now().strftime('%Y-%m-%d')
    total = 0.0
    with open(logfile, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                entry = json.loads(line)
                if entry['timestamp'].startswith(today):
                    total += entry.get('cost_est', 0)
            except:
                pass
    return total

# ====== 路由决策引擎 ======
def route_model(task_type, error_cost_level, context_length=0):
    """根据任务类型 + 错误代价 + 上下文长度 选择模型

    v6 启用时：先问 v6 Router（四信号：任务/轨迹/系统/风险）。
    影子模式（默认）：返回旧路由结果，附 v6 建议字段，只记录不切换；
    正式模式：直接采用 v6 决策。
    """
    # 预算检查
    spent = daily_cost()
    if spent > DAILY_BUDGET * BUDGET_CUTOFF:
        return {'model': MODEL_ROUTES['lightweight']['primary'],
                'reason': 'budget_cutoff', 'budget_spent': spent}

    # v6 四信号路由
    if _v6_router and V6_ROUTER_ENABLED:
        scenario = COST_LEVEL_TO_SCENARIO.get(error_cost_level, task_type)
        v6d = _v6_router.route({
            'task_id': f'gateway-{int(time.time() * 1000)}',
            'scenario': scenario if scenario in MODEL_ROUTES else task_type,
            'context_chars': context_length,
            'shadow': V6_SHADOW_MODE,
        })
        if V6_SHADOW_MODE:
            # 影子模式：实际执行仍用旧路由，v6 建议落盘并随响应返回供对比
            old = _legacy_route(task_type, error_cost_level, spent, context_length)
            old['v6_suggestion'] = v6d['model']
            old['v6_tier'] = v6d['tier']
            old['v6_method'] = v6d['method']
            old['v6_reason'] = v6d['reason']
            old['shadow'] = True
            return old
        return {'model': v6d['model'],
                'reason': f"v6:{v6d['method']}:{v6d['reason']}",
                'budget_spent': spent,
                'v6_tier': v6d['tier'], 'v6_method': v6d['method'],
                'v6_reason': v6d['reason'], 'shadow': False}

    # 旧路由（v6 关闭时）
    return _legacy_route(task_type, error_cost_level, spent, context_length)

# ====== RAG 上下文注入 ======
def inject_rag_context(query, top_k=5):
    """从向量RAG检索上下文"""
    try:
        req = urllib.request.Request(
            'http://127.0.0.1:5001/rag_query',
            data=json.dumps({'query': query, 'top_k': top_k}).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        resp = urllib.request.urlopen(req, timeout=10)
        return json.loads(resp.read().decode('utf-8'))
    except Exception:
        return {'contexts': [], 'sources': []}

# ====== 核心API: 审计问答 ======
def audit_qa(query, error_cost_level=1, with_rag=True, model_override=None):
    """
    统一审计问答入口
    
    Args:
        query: 用户提问
        error_cost_level: 错误代价 (0=免费找答案, 1=一般分析, 2=需图片/公文, 
                          3=合规审查, 4=双签关键结论, 5=最高标准, 'consulting'=决策咨询)
        with_rag: 是否注入RAG上下文
        model_override: 指定模型(跳过路由)
    """
    start_time = time.time()
    
    # Step 1: RAG 上下文注入
    rag_context = None
    if with_rag:
        rag_result = inject_rag_context(query)
        rag_context = '\n\n---\n\n'.join(rag_result.get('contexts', [])[:3])
    
    # Step 2: 模型路由
    if model_override:
        route = {'model': model_override, 'reason': 'manual', 'budget_spent': daily_cost()}
    else:
        ctx_len = len(query) + (len(rag_context) if rag_context else 0)
        route = route_model('qa', error_cost_level, ctx_len)
    
    # Step 3: 构建提示词
    system_prompt = """你是融策会计师事务所的AI审计助手。你的回答应该：
1. 基于提供的知识库内容（如有）
2. 引用具体法规条文
3. 给出可操作的审计建议
4. 标注数据来源和方法依据"""

    user_prompt = query
    if rag_context:
        user_prompt = f"""参考知识库内容：

{rag_context}

---
用户问题：{query}

请基于以上知识库内容，结合审计专业知识回答。如知识库内容不充分，请标注"以下建议基于通用审计知识"。"""

    result = {
        'query': query,
        'model': route['model'],
        'route_reason': route['reason'],
        'budget_spent_today': round(route['budget_spent'], 2),
        'rag_sources': rag_result.get('sources', []) if with_rag else [],
        'system_prompt': system_prompt,
        'user_prompt': user_prompt,
        'duration_ms': int((time.time() - start_time) * 1000),
    }
    # v6 影子对比字段（正式切换后无 v6_suggestion，仅有 v6_method/reason）
    if 'v6_suggestion' in route:
        result['v6_suggestion'] = route['v6_suggestion']
    if 'v6_tier' in route:
        result['v6_tier'] = route['v6_tier']
    if 'v6_method' in route:
        result['v6_method'] = route['v6_method']
    if 'v6_reason' in route:
        result['v6_reason'] = route['v6_reason']
    
    # Log
    log_call(route['model'], 'qa', len(user_prompt), 0, 0, result['duration_ms'])
    
    return result

# ====== 核心API: 报告复核 ======
def report_review(report_text, review_level='quick'):
    """
    报告复核入口
    
    Args:
        report_text: 报告全文
        review_level: 'quick'(快速规则检查) / 'deep'(15维全面检查) / 'rag'(RAG增强)
    """
    start_time = time.time()
    route = route_model('review', 3, len(report_text))  # 合规审查级
    
    results = {'report_length': len(report_text), 'review_level': review_level, 'model': route['model']}
    
    if review_level == 'quick':
        # 规则引擎: 错别字/金额单位/日期格式等
        checks = []
        # 金额单位检查
        import re
        if '万元' in report_text and '元' in report_text.replace('万元', ''):
            checks.append({'check': '金额单位混用', 'status': 'warning', 'detail': '报告中同时出现万元和元'})
        # 日期格式检查
        dates_cn = re.findall(r'\d{4}年\d{1,2}月\d{1,2}日', report_text)
        if len(dates_cn) == 0:
            checks.append({'check': '日期格式', 'status': 'info', 'detail': '未发现标准中文日期格式(YYYY年MM月DD日)'})
        # 合计校验(简化)
        numbers = re.findall(r'[\d,]+\.?\d*', report_text)
        checks.append({'check': '数值提取', 'status': 'info', 'detail': f'共提取{len(numbers)}个数值'})
        results['checks'] = checks
    elif review_level == 'rag':
        # RAG增强复核: 提取审计主题→检索法规→生成复核框架
        rag = inject_rag_context(f"审计报告复核要点 {report_text[:500]}", top_k=5)
        results['rag_contexts'] = len(rag.get('contexts', []))
        results['rag_sources'] = rag.get('sources', [])
    
    results['duration_ms'] = int((time.time() - start_time) * 1000)
    log_call(route['model'], f'review_{review_level}', len(report_text), 0, 0, results['duration_ms'])
    
    return results

# ====== API 服务 ======
def serve(port=5002):
    from flask import Flask, request, jsonify
    
    app = Flask(__name__)
    
    @app.route('/health')
    def health():
        return jsonify({
            'status': 'ok',
            'budget': {'daily': DAILY_BUDGET, 'spent': round(daily_cost(), 2)},
            'version': '1.0.0',
        })
    
    @app.route('/qa', methods=['POST'])
    def qa():
        data = request.get_json()
        query = data.get('query', '')
        if not query:
            return jsonify({'error': 'Missing query'}), 400
        
        result = audit_qa(
            query,
            error_cost_level=data.get('cost_level', 1),
            with_rag=data.get('with_rag', True),
            model_override=data.get('model'),
        )
        return jsonify(result)
    
    @app.route('/review', methods=['POST'])
    def review():
        data = request.get_json()
        text = data.get('text', '')
        if not text:
            return jsonify({'error': 'Missing text'}), 400
        
        result = report_review(text, data.get('level', 'quick'))
        return jsonify(result)
    
    @app.route('/route', methods=['POST'])
    def route():
        data = request.get_json()
        task = data.get('task', 'qa')
        cost = data.get('cost_level', 0)
        ctx = data.get('context_length', 0)
        result = route_model(task, cost, ctx)
        return jsonify(result)
    
    @app.route('/budget')
    def budget():
        spent = daily_cost()
        remaining = DAILY_BUDGET - spent
        return jsonify({
            'daily_limit': DAILY_BUDGET,
            'spent': round(spent, 2),
            'remaining': round(remaining, 2),
            'pct': round(spent / DAILY_BUDGET * 100, 1),
            'status': 'normal' if spent < DAILY_BUDGET * 0.7 else ('warning' if spent < DAILY_BUDGET * 0.9 else 'cutoff'),
        })
    
    @app.route('/tasks', methods=['POST'])
    def run_task():
        """
        审计任务工作流编排
        {
            "workflow": "bid_audit",  // 工作流名称
            "params": { ... },
            "steps": ["step1", "step2"]  // 指定步骤(可选)
        }
        """
        data = request.get_json()
        workflow = data.get('workflow', '')
        params = data.get('params', {})
        steps = data.get('steps', [])
        
        # 工作流定义
        workflows = {
            'bid_audit': {
                'name': '招投标审计全流程',
                'steps': [
                    {'id': 'pre_bid', 'desc': '标前审计(招标文件十必审)', 'tools': ['e25', 'e26', 'e34', 'e35']},
                    {'id': 'mid_bid', 'desc': '标中审计(围标串标检测)', 'tools': ['e05', 'e20', 'e21', 'e27']},
                    {'id': 'post_bid', 'desc': '标后审计(履约验收)', 'tools': ['e30', 'e31', 'e32']},
                ],
            },
            'perf_audit': {
                'name': '绩效评价全流程',
                'steps': [
                    {'id': 'pre_assess', 'desc': '事前评估(需求调研)', 'tools': ['survey_design']},
                    {'id': 'mid_monitor', 'desc': '事中监控', 'tools': ['e23', 'e15']},
                    {'id': 'post_eval', 'desc': '事后评价(满意度+效益)', 'tools': ['survey_analysis', 'e31']},
                ],
            },
        }
        
        wf = workflows.get(workflow)
        if not wf:
            return jsonify({'error': f'Unknown workflow: {workflow}', 'available': list(workflows.keys())}), 400
        
        selected = [s for s in wf['steps'] if not steps or s['id'] in steps]
        
        return jsonify({
            'workflow': workflow,
            'name': wf['name'],
            'steps': selected,
            'params': params,
            'message': f'工作流 {workflow} 已就绪，{len(selected)} 个步骤待执行',
        })
    
    v6_state = '影子模式(只建议不切换)' if (V6_SHADOW_MODE and V6_ROUTER_ENABLED and _v6_router) else \
               ('正式切换' if (V6_ROUTER_ENABLED and _v6_router) else 'v6未启用')
    print(f'\n╔══════════════════════════════════╗')
    print(f'║   融策 Audit API Gateway v1.1   ║')
    print(f'╚══════════════════════════════════╝')
    print(f'\n  http://127.0.0.1:{port}')
    print(f'  POST /qa         - 审计问答(RAG增强)')
    print(f'  POST /review      - 报告复核')
    print(f'  POST /route       - 模型路由查询')
    print(f'  GET  /budget      - 预算查询')
    print(f'  POST /tasks       - 工作流编排')
    print(f'  GET  /health      - 健康检查')
    print(f'\n  模型路由: v6 [{v6_state}]')
    print(f'  预算: ¥{DAILY_BUDGET}/天 | 已用: ¥{daily_cost():.2f}')
    app.run(host='127.0.0.1', port=port, debug=False)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='融策 Audit API Gateway')
    parser.add_argument('--port', type=int, default=5002, help='API端口')
    parser.add_argument('--query', type=str, help='快速测试: 审计问答')
    args = parser.parse_args()
    
    if args.query:
        result = audit_qa(args.query)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        serve(args.port)
