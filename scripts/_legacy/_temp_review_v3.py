# -*- coding: utf-8 -*-
import json
import urllib.request
import urllib.error
import time

# 从 openclaw.json 读取配置
with open(r'C:\Users\scrccpa\.openclaw\openclaw.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

# 可用模型
MODELS = {
    "claude-sonnet-5": {
        "provider": "custom-cbwyy-claude",
        "baseUrl": "https://cbwyy.top",
        "cost": "medium"
    },
    "claude-opus-4-8": {
        "provider": "custom-cbwyy-opus",
        "baseUrl": "https://cbwyy.top",
        "cost": "high"
    },
    "gemini-3.1-pro-preview": {
        "provider": "custom-cbwyy-gemini",
        "baseUrl": "https://cbwyy.top",
        "cost": "preview"
    }
}

# 读取完整制度文本并拆分
with open('output/融策管理制度三件套.md', 'r', encoding='utf-8') as f:
    full_text = f.read()

# 手动拆分三份制度（基于markdown标题）
policies = {
    "项目独立核算与分润制度": full_text.split("# 制度二：")[0].split("# 制度一：")[1],
    "跨部门协同与交叉营销奖励办法": full_text.split("# 制度三：")[0].split("# 制度二：")[1],
    "高管经营目标责任与绩效考核办法": full_text.split("# 制度三：")[1].split("---")[0]
}

opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

def call_model(model_id, meta, policy_name, policy_text):
    """调用单个模型评审单份制度"""
    provider_id = meta['provider']
    provider_cfg = config['models']['providers'][provider_id]
    api_key = provider_cfg['apiKey']
    
    review_prompt = f"""请对以下企业管理制度进行专业评审：

# {policy_name}

{policy_text}

**评审维度（每项0-10分）：**
1. 科学性 — 制度设计是否符合管理学原理？利益机制是否合理？
2. 可执行性 — 条款是否足够具体？财务能不能算清楚？
3. 行业适配性 — 是否符合政府审计+工程咨询行业特征？
4. 防漏洞能力 — 是否预设了常见纠纷和灰色地带？
5. 变革阻力 — 从人性角度，这套制度推行会遇到多大阻力？

请按以下格式输出：
【评审维度打分】
科学性：X/10 — 理由
可执行性：X/10 — 理由
行业适配性：X/10 — 理由
防漏洞能力：X/10 — 理由
变革阻力：X/10 — 理由

【风险点】
1. ...
2. ...
3. ...

【优化建议】
1. ...
2. ...

【总体评价】推荐实施/谨慎实施/不推荐 — 理由
"""
    
    # Claude 系列用 anthropic messages API
    if 'claude' in model_id:
        url = f"{meta['baseUrl']}/v1/messages"
        payload = {
            "model": model_id,
            "max_tokens": 4096,
            "messages": [{"role": "user", "content": review_prompt}]
        }
        headers = {
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01"
        }
    else:
        # Gemini 用 OpenAI-compatible API
        url = f"{meta['baseUrl']}/chat/completions"
        payload = {
            "model": model_id,
            "messages": [{"role": "user", "content": review_prompt}],
            "max_tokens": 4096
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
    
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode('utf-8'),
        headers=headers
    )
    
    try:
        with opener.open(req, timeout=120) as resp:
            result = json.loads(resp.read().decode('utf-8'))
            
            if 'claude' in model_id:
                content = result['content'][0]['text']
                tokens = result.get('usage', {}).get('output_tokens', 0)
            else:
                content = result['choices'][0]['message']['content']
                tokens = result.get('usage', {}).get('total_tokens', 0)
            
            return {"status": "ok", "content": content, "tokens": tokens}
    except Exception as e:
        return {"status": "error", "error": str(e)[:300]}

# 主流程
print("🔬 分制度评审启动（3份制度 × 3个模型）...")
print("=" * 80)

all_results = {}
total_tokens = 0

for policy_name, policy_text in policies.items():
    print(f"\n📋 评审《{policy_name}》")
    all_results[policy_name] = {}
    
    for model_id, meta in MODELS.items():
        print(f"  [{model_id}]...", end=" ", flush=True)
        
        result = call_model(model_id, meta, policy_name, policy_text)
        all_results[policy_name][model_id] = result
        
        if result['status'] == 'ok':
            print(f"✅ {result['tokens']} tokens")
            total_tokens += result['tokens']
        else:
            print(f"❌ {result['error']}")
        
        time.sleep(3)

print("=" * 80)
print(f"✅ 全部评审完成，总Token消耗: {total_tokens}")

# 保存结果
with open('output/制度评审-分制度详细意见.md', 'w', encoding='utf-8') as f:
    f.write("# 融策管理制度三件套 — 分制度专业评审报告\n\n")
    f.write(f"**评审时间**: 2026-07-15 23:11\n")
    f.write(f"**评审模型**: Claude Sonnet-5 / Opus-4-8 + Gemini 3.1 Pro Preview\n")
    f.write(f"**评审方式**: 逐份制度单独评审（避免长文本触发防御机制）\n")
    f.write(f"**总Token消耗**: {total_tokens}\n\n")
    f.write("---\n\n")
    
    for policy_name, results in all_results.items():
        f.write(f"# {policy_name}\n\n")
        for model_id, result in results.items():
            f.write(f"## {model_id} 评审意见\n\n")
            if result['status'] == 'ok':
                f.write(result['content'])
                f.write(f"\n\n**Token**: {result['tokens']}\n\n")
            else:
                f.write(f"**评审失败**: {result['error']}\n\n")
            f.write("---\n\n")

print("\n💾 完整评审报告已保存至: output/制度评审-分制度详细意见.md")
