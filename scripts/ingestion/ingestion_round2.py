"""
Round 2: LLM 辐射分析 — 对12+条业务线逐条判断受影响程度 (P0-2 含异常降级)
"""
import json, re, sys, time
from typing import List, Dict, Optional
from dataclasses import dataclass, field

sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parent))
from taxonomy_manager import get_taxonomy


@dataclass
class RadiationHit:
    line_id: str
    aspect: str
    relevance: str  # high | medium | low
    reason: str


@dataclass
class Round2Result:
    radiation_hits: List[RadiationHit] = field(default_factory=list)
    raw_response: str = ''
    error: Optional[str] = None
    degraded: bool = False


def _build_prompt(active_lines: List[dict], doc_text: str, doc_title: str) -> tuple:
    """Build system and user prompts for radiation analysis."""
    line_list = '\n'.join(
        f"- {l['id']} {l['name']}"
        + (f" ({', '.join(l.get('sub_types', []))})" if l.get('sub_types') else '')
        for l in active_lines
    )

    system = f"""你是审计业务线影响分析专家。融策有以下业务线：

{line_list}

请阅读以下政策/文章，判断它对**每条**业务线的影响。

对每条业务线，输出：
- affected: true/false
- aspect: 影响的具体方面（一句话）
- relevance: high（直接影响方法/流程/标准）| medium（间接关联）| low（弱关联）
- reason: 影响说明（≤50字）

输出纯JSON数组，不要markdown代码块：
[
  {{"line_id": "L1", "affected": true, "aspect": "...", "relevance": "medium", "reason": "..."}},
  ...
]

判断标准：
- high: 该政策直接修改了这条业务线的审计对象/方法/标准/法律依据
- medium: 该政策涉及的资金/项目/流程间接被这条业务线覆盖
- low: 该政策的某个条款可能被这条业务线的审计工作引用
- 不确定时标 medium"""

    user = f"文档标题: {doc_title}\n\n文档内容:\n{doc_text[:6000]}"
    return system, user


def _call_llm(system_prompt: str, user_prompt: str, model: str,
              fallback_model: str, api_config: dict) -> str:
    """Call LLM with retry and fallback. Returns response text."""
    import requests

    # Use OpenAI-compatible endpoint through cbwyy.top proxy
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
                                 json=payload, timeout=60)
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


def run_round2(doc_text: str, doc_title: str = '',
               api_config: Optional[dict] = None) -> Round2Result:
    """
    Run Round 2 radiation analysis.
    P0-2: Degrades gracefully on API failure.
    """
    taxonomy = get_taxonomy()
    active_lines = taxonomy.get_active_lines()
    llm_config = taxonomy.get_llm_config()

    if api_config is None:
        api_config = {}

    result = Round2Result()
    system_prompt, user_prompt = _build_prompt(active_lines, doc_text, doc_title)

    try:
        raw = _call_llm(
            system_prompt, user_prompt,
            model=llm_config.get('round2_model', 'deepseek-v4-flash'),
            fallback_model=llm_config.get('round2_fallback', 'deepseek-v4-pro'),
            api_config=api_config,
        )
        result.raw_response = raw

        if not raw:
            result.error = 'API returned empty response'
            result.degraded = True
            return result

        # Parse JSON — handle code blocks
        clean = raw.strip()
        # Remove markdown code blocks if present
        clean = re.sub(r'^```(?:json)?\s*', '', clean)
        clean = re.sub(r'\s*```$', '', clean)

        try:
            hits = json.loads(clean)
        except json.JSONDecodeError:
            # Try to extract JSON array
            match = re.search(r'\[.*\]', clean, re.DOTALL)
            if match:
                try:
                    hits = json.loads(match.group(0))
                except json.JSONDecodeError:
                    result.error = 'JSON parse error'
                    result.degraded = True
                    return result
            else:
                result.error = 'JSON parse error'
                result.degraded = True
                return result

        for h in hits:
            if h.get('affected') and h.get('relevance') != 'low':
                result.radiation_hits.append(RadiationHit(
                    line_id=h.get('line_id', ''),
                    aspect=h.get('aspect', ''),
                    relevance=h.get('relevance', 'medium'),
                    reason=h.get('reason', ''),
                ))

        # Record low-relevance hits as radiation_signals
        for h in hits:
            if h.get('affected') and h.get('relevance') == 'low':
                lid = h.get('line_id', '')
                if lid:
                    taxonomy.add_radiation_signal(
                        lid, doc_title,
                        h.get('aspect', '') or h.get('reason', '')
                    )

    except Exception as e:
        result.error = f'{type(e).__name__}: {str(e)}'
        result.degraded = True

    return result
