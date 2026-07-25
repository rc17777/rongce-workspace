# -*- coding: utf-8 -*-
"""
融策上下文压缩守卫 v1.0 — Context Guard
========================================
对标 ZLink M6 三级压缩，为融策子Agent提供上下文管理能力。

核心问题：子Agent spawn后独立运行，无压缩机制 → 长任务静默丢早期发现

三个模块：
  1. estimate_task_tokens()    — 任务前 token 消耗预估
  2. build_compression_rules() — 生成压缩规则（注入 spawn task）
  3. batch_plan()              — 超量任务自动分批

设计理念（与 ZLink M6 对齐）：
  L1 工具结果压缩（最高收益/最低风险）→ L2 自我摘要 → L3 保留最近N轮
  融策适配：审计发现不能像代码工具结果那样粗暴截断，需要保留关键数值

用法：
  from context_guard import estimate_task_tokens, build_compression_rules, batch_plan

  tokens = estimate_task_tokens("扫描500份合同并提取关键条款")
  rules = build_compression_rules(agent_name, estimated_tokens=80000, context_window=128000)
  batches = batch_plan("合同猎犬", task_desc, file_count=500)
"""

import sys, re
sys.stdout.reconfigure(encoding='utf-8')

# ═══════════════════════════════════════════
# 常量配置
# ═══════════════════════════════════════════

# 默认上下文窗口（融策常用模型）
MODEL_CONTEXT_WINDOWS = {
    'deepseek-v4-flash': 128000,
    'deepseek-v4-pro': 128000,
    'qwen3.7-plus': 131072,
    'claude-sonnet-5': 200000,
    'claude-opus-4-8': 200000,
    'claude-fable-5': 200000,
    'gemini-3.1-pro': 1048576,
    'gpt-5.5': 128000,
    'kimi-k3': 131072,
    'glm-5.2': 131072,
    'default': 128000,
}

# 每个文件类型估算的 token 消耗
TOKEN_ESTIMATES = {
    '合同': 3000,      # 每份合同平均
    '凭证': 800,       # 每张凭证
    '发票': 400,       # 每张发票
    '会议纪要': 2500,  # 每份纪要
    '招标文件': 8000,  # 每份招标文件
    '投标文件': 12000, # 每份投标文件（较长）
    '序时账_月': 15000, # 一个月序时账
    '科目余额表': 5000,
    '通用PDF': 5000,   # 通用 PDF/文档
    'Excel表': 3000,   # 单表
}

# 安全冗余比例（保留给压缩后上下文 + 输出空间）
SAFETY_MARGIN = 0.3  # 30% 给系统prompt + 输出
KEEP_RECENT_TOKENS = 8000  # 对标 ZLink，保留最近 8000 token

# 单Agent 建议的最大有效处理量（超过就分批）
MAX_EFFECTIVE_PER_AGENT = {
    'contract_hound': 80,       # 合同猎犬：一次处理不超过80份合同
    'bid_hunter': 30,           # 招投标猎手：不超过30份投标文件
    'data_scout': 200,          # 数据侦察兵：不超过200行序时账（每行=1条分录）
    'law_inspector': 100,       # 法规检察官：不超过100条法规比对
    'meeting_minutes_analyzer': 50,  # 会议纪要分析：不超过50份纪要
    'default': 100,
}


# ═══════════════════════════════════════════
# 模块 1: Token 预估
# ═══════════════════════════════════════════

def _detect_file_type(task_desc):
    """从任务描述自动推断文件类型"""
    desc_lower = task_desc.lower()
    if any(k in desc_lower for k in ['合同', 'contract']):
        return '合同', TOKEN_ESTIMATES['合同']
    if any(k in desc_lower for k in ['凭证', 'voucher', '记账']):
        return '凭证', TOKEN_ESTIMATES['凭证']
    if any(k in desc_lower for k in ['发票', 'invoice']):
        return '发票', TOKEN_ESTIMATES['发票']
    if any(k in desc_lower for k in ['会议纪要', '纪要', '会议']):
        return '会议纪要', TOKEN_ESTIMATES['会议纪要']
    if any(k in desc_lower for k in ['招标', '投标', 'bid', '标书']):
        return '投标文件', TOKEN_ESTIMATES['投标文件']
    if any(k in desc_lower for k in ['序时账', '日记账', '明细账']):
        return '序时账_月', TOKEN_ESTIMATES['序时账_月']
    if any(k in desc_lower for k in ['科目余额', '余额表']):
        return '科目余额表', TOKEN_ESTIMATES['科目余额表']
    if any(k in desc_lower for k in ['pdf', '文档', '报告']):
        return '通用PDF', TOKEN_ESTIMATES['通用PDF']
    if any(k in desc_lower for k in ['excel', '表格', 'xls']):
        return 'Excel表', TOKEN_ESTIMATES['Excel表']
    return '通用PDF', TOKEN_ESTIMATES['通用PDF']


def estimate_task_tokens(task_desc, file_count=0, agent_name=None, model_name=None):
    """
    预估任务 token 消耗

    返回: {
        'estimated_total': int,
        'context_window': int,
        'usable_window': int,   # 扣除安全冗余后的可用空间
        'keep_recent': int,
        'risk_level': 'safe' | 'warning' | 'critical',
        'risk_reason': str,
        'batch_recommendation': str,
        'per_file_tokens': int,
    }
    """
    file_type, per_file = _detect_file_type(task_desc)
    context_window = MODEL_CONTEXT_WINDOWS.get(model_name, MODEL_CONTEXT_WINDOWS['default']) if model_name else MODEL_CONTEXT_WINDOWS['default']
    usable = int(context_window * (1 - SAFETY_MARGIN))

    # 基础系统prompt消耗 ~5000 token（估）
    base_overhead = 5000
    # 回复输出预留 ~15000 token
    output_reserve = 15000
    effective_usable = usable - base_overhead - output_reserve

    if file_count > 0:
        estimated_total = base_overhead + output_reserve + file_count * per_file
    else:
        # 无法估计时给一个保守值
        estimated_total = effective_usable // 2

    # 风险评级
    ratio = estimated_total / effective_usable if effective_usable > 0 else 999
    if ratio <= 0.5:
        risk = 'safe'
        reason = f'预估 {estimated_total:,} token，占可用窗口 {ratio:.0%}，安全'
    elif ratio <= 0.85:
        risk = 'warning'
        reason = f'预估 {estimated_total:,} token，占可用窗口 {ratio:.0%}，建议启用压缩'
    else:
        risk = 'critical'
        reason = f'预估 {estimated_total:,} token，超过可用窗口 {ratio:.0%}，必须分批'

    # 分批建议
    if agent_name and agent_name in MAX_EFFECTIVE_PER_AGENT:
        max_per_batch = MAX_EFFECTIVE_PER_AGENT[agent_name]
    else:
        max_per_batch = MAX_EFFECTIVE_PER_AGENT['default']

    if risk == 'critical' and file_count > 0:
        batch_size = max(1, int(effective_usable * 0.5 / per_file))
        num_batches = (file_count + batch_size - 1) // batch_size
        batch_rec = f'建议分 {num_batches} 批，每批 {batch_size} 个文件（{file_type}）'
    elif risk == 'warning' and file_count > 0:
        batch_rec = f'可一次性处理，但需启用L1+L2压缩（{file_count}个{file_type}）'
    else:
        batch_rec = f'可安全处理（{file_count}个{file_type}）'

    return {
        'estimated_total': estimated_total,
        'context_window': context_window,
        'usable_window': effective_usable,
        'keep_recent': KEEP_RECENT_TOKENS,
        'risk_level': risk,
        'risk_reason': reason,
        'file_type': file_type,
        'per_file_tokens': per_file,
        'batch_recommendation': batch_rec,
    }


# ═══════════════════════════════════════════
# 模块 2: 压缩规则生成（注入 spawn task）
# ═══════════════════════════════════════════

def build_compression_rules(agent_name, estimated_tokens=None, context_window=None):
    """
    生成三级压缩规则文本，注入到 Agent 的 spawn task 中。

    返回压缩规则字符串，可直接嵌入 system prompt。
    """
    cw = context_window or 128000
    ratio_str = f'预估任务量 {estimated_tokens:,} token（窗口 {cw:,}）' if estimated_tokens else '任务量未知'

    rules = f"""
## ⚠️ 上下文压缩规则（自动执行）

> {ratio_str}
> 为防止上下文溢出导致丢失早期发现，请严格遵守以下三级压缩策略。

### L1 — 工具结果精简（每次工具调用后自动执行）
- 每处理完一批数据（10条记录/10份文档），用以下格式**主动压缩**已处理内容：
  ```
  [批次压缩 #1-10]
  文件类型: （合同/凭证/纪要）
  关键发现: （每条≤50字，只保留异常信号和金额）
  排除项: （已确认无异常的条目编号）
  待深挖: （需要后续步骤验证的信号，编号+原因）
  ```
- 压缩后原文可从上下文中丢弃（已提取关键信息）
- 每批压缩最多保留 500 字符

### L2 — 阶段性自我摘要（每3批后执行一次）
- 当处理到第3批、第6批、第9批...时，生成跨批次摘要：
  ```
  [阶段摘要]
  已处理总数: N个文件
  异常发现: M个（P0: X, P1: Y, P2: Z）
  关键模式: （跨文件发现的共同异常特征）
  下一步重点: （哪些类型的文件需要加倍关注）
  ```
- 阶段摘要最多 800 字符

### L3 — 保留最近上下文
- 始终完整保留最近 3 批的详细分析
- 更早的内容用 L1/L2 压缩后的摘要替代
- 核心规则：**宁可压缩过程，绝不压缩发现编号和金额**

### 压缩触发条件
- 每处理 10 条记录：执行 L1
- 每 30 条记录（3批）：执行 L2
- 发现压缩后仍接近窗口上限：执行 L3，只保留最近3批+所有阶段摘要

### 反例（绝对禁止）
❌ "前面的分析太长了，我直接总结一下"（会丢掉发现编号）
❌ 压缩时把 P0/P1 发现降级为"似乎有问题"（会丢失严重度）
❌ 超过20条记录还没开始压缩（等发现问题时已经截断了）

### 正例（标准做法）
✅ 每10条主动执行批次压缩，保留 finding_id 和严重度
✅ 阶段摘要中列出所有异常编号，方便后续回溯
✅ 完成时确保所有发现的 finding_id 都出现在最终输出中
"""
    return rules


# ═══════════════════════════════════════════
# 模块 3: 超量任务分批
# ═══════════════════════════════════════════

def batch_plan(agent_name, task_desc, file_count=0, max_per_batch=None):
    """
    为大任务生成分批计划。

    返回: {
        'need_batching': bool,
        'total_files': int,
        'num_batches': int,
        'batch_size': int,
        'spawn_tasks': [str, ...],  # 每批的 spawn task
        'warning': str,
    }
    """
    if max_per_batch is None:
        max_per_batch = MAX_EFFECTIVE_PER_AGENT.get(agent_name, MAX_EFFECTIVE_PER_AGENT['default'])

    if file_count <= max_per_batch:
        return {
            'need_batching': False,
            'total_files': file_count,
            'num_batches': 1,
            'batch_size': file_count,
            'warning': '',
        }

    num_batches = (file_count + max_per_batch - 1) // max_per_batch

    plan = {
        'need_batching': True,
        'total_files': file_count,
        'num_batches': num_batches,
        'batch_size': max_per_batch,
        'warning': (
            f'⚠️ {agent_name} 任务量 {file_count} 超过单Agent上限 {max_per_batch}，'
            f'建议分 {num_batches} 批，每批 {max_per_batch} 个文件。'
            f'每批单独 spawn 一个子Agent，完成后 results 合并。'
        ),
    }
    return plan


# ═══════════════════════════════════════════
# 模块 4: 压缩指令注入（一键调用）
# ═══════════════════════════════════════════

def inject_compression_to_task(spawn_task_text, agent_name,
                                file_count=0, model_name=None):
    """
    一键注入：估算 token → 生成压缩规则 → 追加到 spawn task。

    这是 orchestrate_v3.py 应该调用的主入口。
    """
    estimation = estimate_task_tokens(spawn_task_text, file_count, agent_name, model_name)
    compression_rules = build_compression_rules(
        agent_name,
        estimated_tokens=estimation['estimated_total'],
        context_window=estimation['context_window']
    )

    # 如果是 critical 级别且需要分批，附加分批警告
    batch_warning = ''
    if estimation['risk_level'] == 'critical' and file_count > 0:
        bp = batch_plan(agent_name, spawn_task_text, file_count)
        batch_warning = f"\n\n## 🚨 严重警告\n{estimation['risk_reason']}\n{bp.get('warning', '')}\n\n如果仍然单次执行，必须严格执行 L1+L2+L3 三级压缩，确保所有发现编号不丢失。"

    augmented_task = spawn_task_text + "\n\n" + compression_rules + batch_warning

    return {
        'augmented_task': augmented_task,
        'estimation': estimation,
        'compression_rules': compression_rules,
    }


# ═══════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════

if __name__ == '__main__':
    import argparse, json

    parser = argparse.ArgumentParser(description='融策上下文压缩守卫 v1.0')
    sub = parser.add_subparsers(dest='cmd')

    p_est = sub.add_parser('estimate', help='预估任务 token 消耗')
    p_est.add_argument('--task', required=True, help='任务描述')
    p_est.add_argument('--files', type=int, default=0, help='文件数量')
    p_est.add_argument('--agent', default=None, help='Agent名称')
    p_est.add_argument('--model', default=None, help='模型名称')
    p_est.add_argument('--json', action='store_true', help='JSON输出')

    p_batch = sub.add_parser('batch', help='生成分批计划')
    p_batch.add_argument('--agent', required=True, help='Agent名称')
    p_batch.add_argument('--task', required=True, help='任务描述')
    p_batch.add_argument('--files', type=int, required=True, help='文件数量')

    p_rules = sub.add_parser('rules', help='输出压缩规则文本')
    p_rules.add_argument('--agent', default='default', help='Agent名称')
    p_rules.add_argument('--tokens', type=int, default=None)

    args = parser.parse_args()

    if args.cmd == 'estimate':
        result = estimate_task_tokens(args.task, args.files, args.agent, args.model)
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(f'═══ Token预估 ═══')
            print(f'任务: {args.task}')
            print(f'文件数: {args.files}')
            print(f'文件类型: {result["file_type"]}（{result["per_file_tokens"]} token/个）')
            print(f'预估总量: {result["estimated_total"]:,} token')
            print(f'上下文窗口: {result["context_window"]:,}（可用 {result["usable_window"]:,}）')
            print(f'风险等级: {result["risk_level"]}')
            print(f'建议: {result["batch_recommendation"]}')

    elif args.cmd == 'batch':
        plan = batch_plan(args.agent, args.task, args.files)
        print(f'═══ 分批计划 ═══')
        print(f'Agent: {args.agent}')
        print(f'文件总数: {plan["total_files"]}')
        print(f'分批数: {plan["num_batches"]}')
        print(f'每批大小: {plan["batch_size"]}')
        if plan['warning']:
            print(f'\n{plan["warning"]}')

    elif args.cmd == 'rules':
        print(build_compression_rules(args.agent, args.tokens))

    else:
        parser.print_help()
