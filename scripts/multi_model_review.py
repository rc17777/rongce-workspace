"""Multi-model review of the ingestion V2 design document.
Calls all 11 configured models in parallel, each with a unique review angle.
"""
import json, os, sys, time, threading, traceback
import requests

sys.stdout.reconfigure(encoding='utf-8')

DOC_PATH = r'C:\Users\scrccpa\.openclaw\workspace\knowledge\taxonomy\INGESTION_V2_DESIGN.md'
CONFIG_PATH = r'C:\Users\scrccpa\.openclaw\openclaw.json'
OUTPUT_DIR = r'C:\Users\scrccpa\.openclaw\workspace\knowledge\taxonomy\reviews'

with open(DOC_PATH, 'r', encoding='utf-8') as f:
    doc_content = f.read()

with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
    config = json.load(f)

providers = config['models']['providers']

# Map model_id -> (provider_config, model_id)
MODEL_MAP = {}
for pname, pcfg in providers.items():
    for m in pcfg.get('models', []):
        MODEL_MAP[m['id']] = (pname, pcfg, m['id'])

# ============================================================
# Review prompts - 11 unique angles
# ============================================================
REVIEW_ANGLES = {
    'deepseek-v4-flash': """你是系统架构审查专家。阅读以下设计文档，从**结构完整性**角度评审：

审查要点：
1. 三轮分类流程是否有逻辑缺口？
2. 关键步骤是否有遗漏（比如去重、异常处理、回滚）？
3. 数据结构设计是否有不一致？
4. 孵化→升级流程是否有死循环或无限等待风险？

输出：编号列表，每条"问题+建议"。通过的方面直接说"通过"。""",

    'deepseek-v4-pro': """你是审计业务逻辑分析专家。阅读以下设计文档，从**分类逻辑严谨性**角度深度审查：

审查要点：
1. 三轮分类的边界条件是否清晰？有没有一篇文档同时触发矛盾分类的情况？
2. Round 1 关键词匹配策略是否会大量误判？举例分析哪些业务线关键词最容易打架
3. Round 2 的 relevance 三级（high/medium/low）在审计实务中是否够用？
4. Round 3 的触发条件是否合理？会漏掉什么？会过度触发什么？
5. "宁漏勿错"（confidence<0.6视为false）在审计行业是否应该反过来——"宁错勿漏"？

输出：每个要点的详细分析，最后给一个逻辑严密性评分（1-10）。""",

    'qwen3.7-plus': """你是中国政府审计实务专家。阅读以下设计文档，从**中国政府审计行业合规与实践**角度评审：

审查要点：
1. 12条业务线的分类是否符合中国审计行业的实际业务划分？有没有在中国政府审计实践中常见的业务线被遗漏？
2. 该设计在财政部/审计署/国资委等部门的实际工作流程中能否落地？有什么制度障碍？
3. 法规库自动入库涉及的"财政部官网爬取"在合规上有什么风险？
4. 从中国政府审计信息化建设的政策导向看，这个方案是否符合"金审工程"等国家审计信息化方向？
5. 数据安全法和个人信息保护法对自动化采集的影响？

输出：逐条分析，用中文。最后给一个"在政府审计场景下的可行性评分"（1-10）。""",

    'claude-fable-5': """You are a senior consulting partner reviewing a knowledge management system design for a Chinese auditing/consulting firm. Read the design document below.

Review from an **advisory/strategic** perspective:
1. What's the single biggest strategic bet in this design, and is it the right bet?
2. What would you do differently if you had unlimited budget? What about bare-minimum budget?
3. Is the "incubation→promotion" flow for new business lines practical in a real small-firm (not Big 4) setting?
4. What are the hidden organizational-change challenges this design doesn't address?
5. If you were presenting this to the firm's owner, what's your one-sentence pitch and your one-sentence warning?

Output: Structured advisory memo format. End with a "Go / Pivot / Kill" recommendation.""",

    'claude-sonnet-5': """You are a legal and compliance risk auditor. Read the following design document for an automated knowledge ingestion system.

Review from a **risk and compliance** perspective:
1. What legal risks arise from automated web scraping of Chinese government websites?
2. What are the data quality risks of automated classification (false positives with regulatory implications)?
3. If the system incorrectly classifies a policy and someone relies on it for audit work, what's the liability?
4. What are the failure modes of the 3-round classification that could have downstream consequences?
5. The design mentions "automatic SOP updates triggered by regulation changes" — what governance controls are needed?

Output: Risk register format (Risk ID | Risk | Likelihood | Impact | Mitigation). End with a risk score (1-10, where 10 is highest risk).""",

    'claude-opus-4-8': """You are the final authority reviewer — the last set of eyes before this design is approved for implementation.

Read the design document below and provide a **comprehensive verdict**.

Address:
1. Overall architectural coherence — does this hang together as a system?
2. The single most important thing that must be fixed before implementation
3. The single strongest element that should be preserved at all costs
4. Whether the cost estimates are realistic
5. Whether the 9-day implementation timeline is feasible
6. Any catastrophic blind spots the other 10 reviewers might miss

Output: Executive summary (3 paragraphs max) followed by a clear verdict: APPROVE / APPROVE WITH CONDITIONS / REJECT. If conditional, list non-negotiable conditions.""",

    'gpt-5.5': """You are a communication and technical writing expert. Read the design document below.

Review from an **expression, clarity, and reader experience** perspective:
1. How readable is this document for a non-technical business owner?
2. Which sections are the hardest to understand, and how would you rewrite them?
3. Does the document effectively communicate WHY each design choice was made, or just WHAT?
4. How would you restructure the document if the goal is to get buy-in from a busy executive?
5. Are the ASCII diagrams and YAML examples clear and effective?

Output: Communication audit report. Rate document clarity (1-10). Provide 3 specific rewrites of the weakest sections.""",

    'gpt-5.6-luna': """You are a creative innovation strategist. Read the design document below.

Review from an **innovative expansion** perspective:
1. What creative possibilities does this design enable that the authors haven't mentioned?
2. Beyond government policy ingestion, what unconventional data sources could feed this system?
3. How could this system evolve into a product/service the firm could sell to other audit firms?
4. What gamification or incentive mechanisms could encourage staff to contribute to the knowledge base?
5. If you were to add ONE unexpected feature that would make this system 10x more valuable, what would it be?

Output: Creative innovation brief. Bold, specific ideas. Don't worry about current feasibility.""",

    'gpt-5.6-sol': """You are a quantitative systems analyst. Read the design document below.

Review from an **analytical rigor** perspective:
1. Are the numerical thresholds well-justified? (threshold=3 for incubation, confidence<0.6, similarity>0.7, 180-day window, 90-day postpone)
2. What would be a better way to set these thresholds? (e.g., statistical calibration vs. intuition)
3. Is the cost estimation methodology sound? What hidden costs are missed?
4. How would you measure the system's classification accuracy over time?
5. What metrics should be tracked to know if this system is actually "evolving" vs. just "accumulating"?

Output: Quantitative analysis report. Include specific alternative threshold proposals with justification. Rate analytical rigor (1-10).""",

    'gpt-5.6-terra': """You are a generalist systems thinker evaluating a knowledge management design. Read the document below.

Review from a **comprehensive viability** perspective:
1. Does this design balance ambition with practicality?
2. What are the top 3 implementation risks ranked by severity?
3. How well does it handle edge cases (e.g., a document that's relevant to 8 out of 12 business lines)?
4. Is the "human in the loop" positioned correctly, or is it too much/too little human involvement?
5. What would the first 30 days after launch actually look like?

Output: Holistic assessment report. Give an overall viability score (1-10).""",

    'doubao-seed-2.0-lite': """你是中国本土信息化建设专家，请从**国产化、信创合规、本地化部署**角度评审以下设计文档。

审查要点：
1. 该方案的技术栈（Python、YAML、AC自动机、LLM API）是否符合中国信创环境要求？
2. 依赖外部LLM API（cbwyy.top代理）在数据安全方面的风险，是否需要本地化部署替代方案？
3. 审计行业涉及政府敏感数据——该方案的自动化采集和处理流程是否符合《数据安全法》《个人信息保护法》？
4. 如果要向政府部门/国企客户展示这个系统，需要做哪些合规改造？
5. 从成本角度看，用国产开源模型（如DeepSeek/通义千问）本地部署替代方案是否可行？

输出：逐条分析。最后给出信创合规评分（1-10）和改造建议清单。""",
}

# ============================================================
# API call functions
# ============================================================
def call_openai_compatible(pcfg, model_id, system_prompt, user_content, api_key):
    """Call OpenAI-compatible API (cbwyy.top proxy)"""
    base = pcfg['baseUrl']
    url = f"{base}/chat/completions"
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    payload = {
        'model': model_id,
        'messages': [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_content}
        ],
        'temperature': 0.3,
        'max_tokens': 2048
    }
    resp = requests.post(url, headers=headers, json=payload, timeout=120)
    if resp.status_code == 200:
        return resp.json()['choices'][0]['message']['content']
    else:
        return f"ERROR {resp.status_code}: {resp.text[:500]}"

def call_anthropic_compatible(pcfg, model_id, system_prompt, user_content, api_key):
    """Call Anthropic-compatible API (cbwyy.top proxy)"""
    base = pcfg['baseUrl']
    url = f"{base}/v1/messages" if '/v1' not in base else f"{base.rstrip('/')}/messages"
    # Actually cbwyy.top proxy uses OpenAI-compatible endpoint for all, let's try
    # Fall back to OpenAI format
    url = f"{base}/v1/messages"
    headers = {
        'x-api-key': api_key,
        'anthropic-version': '2023-06-01',
        'Content-Type': 'application/json'
    }
    payload = {
        'model': model_id,
        'system': system_prompt,
        'messages': [
            {'role': 'user', 'content': user_content}
        ],
        'temperature': 0.3,
        'max_tokens': 2048
    }
    resp = requests.post(url, headers=headers, json=payload, timeout=120)
    if resp.status_code == 200:
        data = resp.json()
        return data['content'][0]['text']
    else:
        # Fallback: try OpenAI format
        url2 = f"{base}/v1/chat/completions"
        payload2 = {
            'model': model_id,
            'messages': [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_content}
            ],
            'temperature': 0.3,
            'max_tokens': 2048
        }
        headers2 = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        resp2 = requests.post(url2, headers=headers2, json=payload2, timeout=120)
        if resp2.status_code == 200:
            return resp2.json()['choices'][0]['message']['content']
        return f"ERROR (anthropic): {resp.status_code}: {resp.text[:300]} | (openai fallback): {resp2.status_code}: {resp2.text[:300]}"


def review_model(model_id, angle_prompt, results_dict):
    """Run a single model review and store result"""
    print(f"[START] {model_id}")
    try:
        pname, pcfg, mid = MODEL_MAP[model_id]
        api_key = pcfg.get('apiKey', '')
        api_type = pcfg.get('api', 'openai-completions')

        system_prompt = angle_prompt
        user_content = f"以下是需要评审的设计文档：\n\n```markdown\n{doc_content[:15000]}\n```\n\n请按照你的审查角度进行评审。"

        if api_type == 'anthropic-messages':
            result = call_anthropic_compatible(pcfg, model_id, system_prompt, user_content, api_key)
        else:
            result = call_openai_compatible(pcfg, model_id, system_prompt, user_content, api_key)

        results_dict[model_id] = {
            'status': 'success',
            'model': model_id,
            'output': result,
            'timestamp': time.time()
        }
        print(f"[DONE]  {model_id} ({len(result)} chars)")
    except Exception as e:
        results_dict[model_id] = {
            'status': 'error',
            'model': model_id,
            'output': f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}",
            'timestamp': time.time()
        }
        print(f"[FAIL]  {model_id}: {type(e).__name__}: {e}")

# ============================================================
# Main
# ============================================================
os.makedirs(OUTPUT_DIR, exist_ok=True)

print("=" * 60)
print("  Multi-Model Review: Ingestion V2 Design Document")
print(f"  Models to call: {len(REVIEW_ANGLES)}")
print(f"  Doc size: {len(doc_content)} chars")
print("=" * 60)

results = {}
threads = []

for model_id, angle_prompt in REVIEW_ANGLES.items():
    if model_id not in MODEL_MAP:
        print(f"[SKIP] {model_id}: not found in config")
        continue
    t = threading.Thread(target=review_model, args=(model_id, angle_prompt, results))
    t.start()
    threads.append(t)

print(f"\nLaunched {len(threads)} review threads, waiting...\n")

for t in threads:
    t.join()

print("\n" + "=" * 60)
print("  All reviews complete!")
print("=" * 60)

# Save individual results
for model_id, result in results.items():
    fname = f"{model_id.replace('/', '_')}.md"
    fpath = os.path.join(OUTPUT_DIR, fname)
    with open(fpath, 'w', encoding='utf-8') as f:
        f.write(f"# Review: {model_id}\n\n")
        f.write(f"Status: {result['status']}\n\n")
        f.write(f"---\n\n{result['output']}\n")

# Save consolidated
consolidated_path = os.path.join(OUTPUT_DIR, '_consolidated.json')
with open(consolidated_path, 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

# Print summary
success = sum(1 for r in results.values() if r['status'] == 'success')
print(f"\nResults: {success}/{len(results)} successful")
print(f"Individual reviews: {OUTPUT_DIR}/")
print(f"Consolidated: {consolidated_path}")

# Quick previews
for model_id, result in results.items():
    preview = result['output'][:200].replace('\n', ' ')
    status_icon = '✅' if result['status'] == 'success' else '❌'
    print(f"  {status_icon} {model_id}: {preview}...")
