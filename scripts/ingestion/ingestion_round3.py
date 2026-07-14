"""
Round 3: 新领域嗅探 — 发现不在当前业务线树中的新服务方向 (P0-2/3/4)
"""
import json, re, sys, time
from typing import List, Dict, Optional
from dataclasses import dataclass, field

sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parent))
from taxonomy_manager import get_taxonomy


@dataclass
class NovelDomain:
    proposed_name: str
    description: str
    closest_existing_line: str
    target_clients: str
    confidence: float
    reasoning: str


@dataclass
class Round3Result:
    has_novel_domain: bool = False
    novel_domains: List[NovelDomain] = field(default_factory=list)
    cross_cutting_theme: Optional[str] = None
    raw_response: str = ''
    error: Optional[str] = None
    degraded: bool = False


def _should_trigger_round3(round1_hits: List[str],
                           round2_result) -> bool:
    """Determine if Round 3 should be triggered."""
    # Condition A: Round 1 zero hits AND Round 2 no high hits
    from ingestion_round2 import Round2Result
    if not round1_hits:
        high_hits = [h for h in round2_result.radiation_hits if h.relevance == 'high']
        if not high_hits:
            return True

    # Condition B: Round 2 has >= 3 low relevance hits (widespread weak association)
    # (This info is in the raw_response, which we can't parse here easily.
    #  We approximate by checking if radiation_hits is empty but raw_response exists)
    if not round2_result.radiation_hits and round2_result.raw_response:
        return True

    # Condition C: Always run for government_policy type documents
    # (handled by caller based on source type)

    return False


def _build_prompt(active_lines: List[dict], doc_text: str, doc_title: str) -> tuple:
    """Build prompt for novelty detection."""
    line_list = '\n'.join(
        f"- {l['id']} {l['name']}"
        + (f" ({', '.join(l.get('sub_types', []))})" if l.get('sub_types') else '')
        for l in active_lines
    )

    system = f"""你是审计咨询行业趋势分析师。融策目前有{len(active_lines)}条业务线：

{line_list}

请分析以下政策/文章，判断它是否揭示了**当前业务线覆盖不到的新服务方向**。

输出纯JSON（不要markdown代码块）：
{{
  "has_novel_domain": true/false,
  "novel_domains": [
    {{
      "proposed_name": "建议的业务线名称（简短，4-8字）",
      "description": "这个新方向解决什么问题（≤100字）",
      "closest_existing_line": "最接近的现有业务线ID（如 L7）",
      "target_clients": "目标客户类型",
      "confidence": 0.0-1.0,
      "reasoning": "判定依据（≤80字）"
    }}
  ],
  "cross_cutting_theme": "横切现有业务线的新主题名称，没有则填 null"
}}

判断原则：
- 宁漏勿错：confidence < 0.6 时视为 false
- 新领域 = 现有业务线无法直接覆盖的客户需求/政府要求
- 不要把"现有业务线的子类型"误判为新领域"""

    user = f"文档标题: {doc_title}\n\n文档内容:\n{doc_text[:8000]}"
    return system, user


def _call_llm(system_prompt: str, user_prompt: str, model: str,
              fallback_model: str, api_config: dict) -> str:
    """Call LLM with retry and fallback."""
    import requests

    base_url = api_config.get('baseUrl', 'https://cbwyy.top/v1')
    api_key = api_config.get('apiKey', '')
    url = f"{base_url}/chat/completions"

    models_to_try = [model, fallback_model] if fallback_model else [model]

    for m in models_to_try:
        payload = {
            'model': m,
            'messages': [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt},
            ],
            'temperature': 0.3,
            'max_tokens': 2048,
        }
        try:
            resp = requests.post(url,
                                 headers={'Authorization': f'Bearer {api_key}',
                                          'Content-Type': 'application/json'},
                                 json=payload, timeout=90)
            if resp.status_code == 200:
                data = resp.json()
                content = data['choices'][0]['message']['content']
                if content and len(content.strip()) > 20:
                    return content
            elif resp.status_code == 504:
                time.sleep(5)
                continue
            else:
                time.sleep(2)
                continue
        except Exception:
            time.sleep(3)
            continue

    return ''


def run_round3(doc_text: str, doc_title: str = '',
               source_type: str = '',
               round1_hits: Optional[List[str]] = None,
               round2_result=None,
               api_config: Optional[dict] = None) -> Round3Result:
    """
    Run Round 3 novelty detection.
    P0-2: Degrades gracefully. P0-3: Cross-cutting theme detection. P0-4: Lower threshold.
    """
    taxonomy = get_taxonomy()
    active_lines = taxonomy.get_active_lines()
    llm_config = taxonomy.get_llm_config()

    if api_config is None:
        api_config = {}

    if round1_hits is None:
        round1_hits = []

    result = Round3Result()

    # Check if Round 3 should be triggered
    if source_type == 'government_policy':
        should_run = True  # Always run for government policies
    elif round2_result is not None:
        should_run = _should_trigger_round3(round1_hits, round2_result)
    else:
        should_run = not bool(round1_hits)  # Run if no direct hits

    if not should_run:
        return result

    try:
        system_prompt, user_prompt = _build_prompt(active_lines, doc_text, doc_title)
        raw = _call_llm(
            system_prompt, user_prompt,
            model=llm_config.get('round3_model', 'deepseek-v4-pro'),
            fallback_model=llm_config.get('round3_fallback', 'qwen3.7-plus'),
            api_config=api_config,
        )
        result.raw_response = raw

        if not raw:
            result.error = 'API returned empty response'
            result.degraded = True
            return result

        # Parse JSON
        clean = raw.strip()
        clean = re.sub(r'^```(?:json)?\s*', '', clean)
        clean = re.sub(r'\s*```$', '', clean)

        try:
            data = json.loads(clean)
        except json.JSONDecodeError:
            match = re.search(r'\{.*\}', clean, re.DOTALL)
            if match:
                try:
                    data = json.loads(match.group(0))
                except json.JSONDecodeError:
                    result.error = 'JSON parse error'
                    result.degraded = True
                    return result
            else:
                result.error = 'JSON parse error'
                result.degraded = True
                return result

        result.has_novel_domain = data.get('has_novel_domain', False)

        # P0-3: Store cross-cutting theme
        cct = data.get('cross_cutting_theme')
        if cct and cct != 'null' and cct.strip():
            result.cross_cutting_theme = cct.strip()

        # Store novel domains
        for nd in data.get('novel_domains', []):
            conf = nd.get('confidence', 0)
            if conf < 0.6:
                continue  # 宁漏勿错
            result.novel_domains.append(NovelDomain(
                proposed_name=nd.get('proposed_name', ''),
                description=nd.get('description', ''),
                closest_existing_line=nd.get('closest_existing_line', ''),
                target_clients=nd.get('target_clients', ''),
                confidence=conf,
                reasoning=nd.get('reasoning', ''),
            ))

    except Exception as e:
        result.error = f'{type(e).__name__}: {str(e)}'
        result.degraded = True

    return result


def process_round3_results(result: Round3Result, doc_title: str,
                           source_url: str = '') -> List[dict]:
    """
    Process Round 3 results: update incubation queue and cross-cutting themes.
    P0-3: Cross-cutting theme storage. P0-4: Lower threshold + fast track. P1-1: Weak signals.

    Returns list of {'action': ..., 'detail': ...} for notification.
    """
    taxonomy = get_taxonomy()
    notifications = []

    # P0-3: Cross-cutting themes
    if result.cross_cutting_theme:
        # Simple extraction — affected_lines determined by which lines
        # the document already hits (handled upstream)
        taxonomy.add_or_update_meta_tag(
            name=result.cross_cutting_theme,
            description=f'Auto-detected from: {doc_title}',
            affected_lines=[],  # filled by caller
        )

    # P0-4 + P1-1: Novel domains → incubation queue
    for nd in result.novel_domains:
        action, prop = taxonomy.add_novel_evidence(
            proposed_name=nd.proposed_name,
            description=nd.description,
            closest_line=nd.closest_existing_line,
            target_clients=nd.target_clients,
            confidence=nd.confidence,
            policy_ref=doc_title,
            source_url=source_url,
            excerpt=nd.reasoning,
        )

        if action == 'fast_track':
            notifications.append({
                'action': 'fast_track',
                'level': 'urgent',
                'message': (f'🚨 快速通道: 单篇高置信度({nd.confidence:.0%})发现新业务方向'
                            f'「{nd.proposed_name}」，建议立即审视。'),
                'proposal_id': prop['candidate_id'] if prop else None,
            })
        elif action == 'threshold_reached':
            notifications.append({
                'action': 'threshold_reached',
                'level': 'info',
                'message': (f'📊 候选业务线「{nd.proposed_name}」已积累{prop["evidence_count"]}条'
                            f'独立证据，达到孵化门槛，请确认是否纳入正式业务线。'),
                'proposal_id': prop['candidate_id'] if prop else None,
            })
        elif action == 'weak_signal':
            notifications.append({
                'action': 'weak_signal',
                'level': 'low',
                'message': f'🔍 弱信号: 疑似新方向「{nd.proposed_name}」(置信度{nd.confidence:.0%})，已进入观察看板。',
            })

    return notifications
