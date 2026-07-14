"""Retry failed models from first round, with fixes:
- Remove temperature for Claude models
- Add retry logic for 504 timeouts
"""
import json, os, sys, time, requests, traceback

sys.stdout.reconfigure(encoding='utf-8')

DOC_PATH = r'C:\Users\scrccpa\.openclaw\workspace\knowledge\taxonomy\INGESTION_V2_DESIGN.md'
OUTPUT_DIR = r'C:\Users\scrccpa\.openclaw\workspace\knowledge\taxonomy\reviews'

with open(DOC_PATH, 'r', encoding='utf-8') as f:
    doc_content = f.read()

with open(r'C:\Users\scrccpa\.openclaw\openclaw.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

providers = config['models']['providers']
MODEL_MAP = {}
for pname, pcfg in providers.items():
    for m in pcfg.get('models', []):
        MODEL_MAP[m['id']] = (pname, pcfg, m['id'])

# Shortened doc for prompt
doc_short = doc_content[:12000]

# ============================================================
# Retry targets - only models that failed
# ============================================================
RETRY_TASKS = {
    'deepseek-v4-flash': {
        'system': """你是系统架构审查专家。阅读以下设计文档，从**结构完整性**角度评审：
审查：三轮分类流程的逻辑缺口、关键步骤遗漏、数据结构不一致、孵化→升级流程的潜在风险。
输出编号列表。"用中文回答。""",
        'api_type': 'openai',
        'provider': 'custom-cbwyy-top-v1',
        'needs_temperature': True,
    },
    'deepseek-v4-pro': {
        'system': """你是审计业务逻辑分析专家。深度审查以下设计文档的分类逻辑：
1. 三轮分类边界条件是否有矛盾？
2. Round 1 关键词策略是否大量误判？
3. relevance 三级够用吗？
4. Round 3 触发条件合理吗？
5. 审计行业该"宁漏勿错"还是"宁错勿漏"？
输出详细分析，给逻辑严密性评分(1-10)。用中文回答。""",
        'api_type': 'openai',
        'provider': 'custom-cbwyy-top-v1',
        'needs_temperature': True,
    },
    'qwen3.7-plus': {
        'system': """你是中国政府审计实务专家。请从中国政府审计实践角度评审以下知识库入库设计：
1. 12条业务线是否遗漏了中国政府审计实践中常见业务？
2. 在财政部/审计署/国资委实际流程中能落地吗？
3. 法规自动入库合规风险？
4. 是否符合金审工程等审计信息化方向？
5. 数据安全法对自动化采集的影响？
输出逐条分析，给可行性评分(1-10)。用中文回答。""",
        'api_type': 'openai',
        'provider': 'custom-cbwyy-qwen',
        'needs_temperature': True,
    },
    'claude-fable-5': {
        'system': """You are a senior consulting partner. Read this knowledge management design doc for a Chinese auditing firm. Give an advisory review: 1) Biggest strategic bet - is it right? 2) What would you do with unlimited budget vs bare-minimum? 3) Is incubation practical for a small firm? 4) Hidden organizational challenges? 5) One-sentence pitch + one-sentence warning. End with Go/Pivot/Kill recommendation. Be concise.""",
        'api_type': 'anthropic',
        'provider': 'custom-cbwyy-fable',
        'needs_temperature': False,  # FIXED
    },
    'claude-sonnet-5': {
        'system': """You are a legal and compliance risk auditor. Review this knowledge ingestion design. Provide: 1) Legal risks of automated scraping 2) Data quality risks of auto-classification 3) Liability if classification errors affect audit work 4) Failure modes of 3-round classification 5) Governance controls needed. Output as risk register, end with risk score (1-10). Be concise.""",
        'api_type': 'anthropic',
        'provider': 'custom-cbwyy-claude',
        'needs_temperature': False,  # FIXED
    },
    'gpt-5.5': {
        'system': """You are a communication expert. Review this design document for clarity and readability: 1) How readable for a non-technical business owner? 2) Hardest sections to understand? 3) Does it explain WHY or just WHAT? 4) How to restructure for executive buy-in? 5) Are diagrams effective? Rate clarity 1-10. Be concise.""",
        'api_type': 'openai',
        'provider': 'custom-cbwyy-gpt55',
        'needs_temperature': True,
    },
    'gpt-5.6-luna': {
        'system': """You are an innovation strategist. Review this knowledge base design: 1) What creative possibilities are missed? 2) Unconventional data sources? 3) Could this become a sellable product? 4) Gamification ideas? 5) ONE feature that would make it 10x more valuable. Bold ideas, don't worry about feasibility. Be concise.""",
        'api_type': 'openai',
        'provider': 'custom-cbwyy-luna',
        'needs_temperature': True,
    },
    'gpt-5.6-sol': {
        'system': """You are a quantitative analyst. Review numerical aspects: 1) Are thresholds justified (incubation=3, confidence<0.6, similarity>0.7, 180d window)? 2) Better ways to calibrate? 3) Cost estimation accuracy - hidden costs? 4) How to measure classification accuracy over time? 5) Metrics to track "evolution" vs "accumulation"? Propose alternative thresholds. Rate rigor 1-10. Be concise.""",
        'api_type': 'openai',
        'provider': 'custom-cbwyy-sol',
        'needs_temperature': True,
    },
    'gpt-5.6-terra': {
        'system': """You are a systems thinker. Review viability: 1) Ambition vs practicality balance? 2) Top 3 implementation risks (ranked)? 3) Edge cases (e.g., doc relevant to 8/12 lines)? 4) Human-in-the-loop placement correct? 5) What does day 1-30 after launch look like? Overall viability score 1-10. Be concise.""",
        'api_type': 'openai',
        'provider': 'custom-cbwyy-terra',
        'needs_temperature': True,
    },
    'doubao-seed-2.0-lite': {
        'system': """你是中国本土信息化建设专家。从信创合规角度评审此设计：1) 技术栈是否符信创环境？2) 依赖外部LLM API的数据安全风险？3) 审计行业涉及政府敏感数据是否合规？4) 向政府部门展示需哪些改造？5) 国产开源模型本地部署替代可行性？逐条分析，给信创评分(1-10)。用中文回答。""",
        'api_type': 'openai',
        'provider': 'custom-cbwyy-doubao',
        'needs_temperature': True,
    },
}


def call_with_retry(model_id, task, max_retries=3):
    """Call model API with retry logic"""
    pcfg = providers[task['provider']]
    api_key = pcfg.get('apiKey', '')
    base_url = pcfg['baseUrl']

    if task['api_type'] == 'openai':
        url = f"{base_url}/chat/completions"
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        payload = {
            'model': model_id,
            'messages': [
                {'role': 'system', 'content': task['system']},
                {'role': 'user', 'content': f"以下是需要评审的设计文档：\n\n```markdown\n{doc_short}\n```\n\n请按照你的审查角度给出评审意见。"}
            ],
            'max_tokens': 2048
        }
        if task['needs_temperature']:
            payload['temperature'] = 0.3
    else:
        # Anthropic format
        url = f"{base_url}/v1/messages"
        headers = {
            'x-api-key': api_key,
            'anthropic-version': '2023-06-01',
            'Content-Type': 'application/json'
        }
        payload = {
            'model': model_id,
            'system': task['system'],
            'messages': [
                {'role': 'user', 'content': f"以下是需要评审的设计文档：\n\n```markdown\n{doc_short}\n```\n\n请按照你的审查角度给出评审意见。"}
            ],
            'max_tokens': 2048
            # NO temperature for Claude!
        }

    for attempt in range(max_retries):
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=180)
            if resp.status_code == 200:
                data = resp.json()
                if task['api_type'] == 'openai':
                    content = data['choices'][0]['message']['content']
                else:
                    content = data['content'][0]['text']
                if content and len(content.strip()) > 50:
                    return True, content
                else:
                    print(f"  Attempt {attempt+1}: empty/short response ({len(content) if content else 0} chars), retrying...")
            elif resp.status_code == 504:
                print(f"  Attempt {attempt+1}: 504 timeout, retrying in 10s...")
                time.sleep(10)
            else:
                print(f"  Attempt {attempt+1}: HTTP {resp.status_code}: {resp.text[:200]}")
                if attempt < max_retries - 1:
                    time.sleep(5)
        except Exception as e:
            print(f"  Attempt {attempt+1}: {type(e).__name__}: {e}")
            if attempt < max_retries - 1:
                time.sleep(5)

    return False, f"FAILED after {max_retries} attempts"


os.makedirs(OUTPUT_DIR, exist_ok=True)
print(f"Retrying {len(RETRY_TASKS)} failed models...\n")

for model_id, task in RETRY_TASKS.items():
    print(f"[{model_id}] Calling...")
    ok, result = call_with_retry(model_id, task)
    status_icon = '✅' if ok else '❌'
    print(f"  {status_icon} {'OK' if ok else 'FAIL'} ({len(result) if result else 0} chars)")

    fpath = os.path.join(OUTPUT_DIR, f"{model_id.replace('/', '_')}.md")
    with open(fpath, 'w', encoding='utf-8') as f:
        f.write(f"# Review: {model_id}\n\n")
        f.write(f"Status: {'success' if ok else 'error'}\n\n")
        f.write(f"---\n\n{result}\n")

print("\nDone!")
