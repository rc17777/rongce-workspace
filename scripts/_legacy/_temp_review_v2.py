# -*- coding: utf-8 -*-
import json
import urllib.request
import urllib.error
import time

# 只选择刚才验证过可用的模型
MODELS = {
    "claude-fable-5": {
        "provider": "custom-cbwyy-fable",
        "baseUrl": "https://cbwyy.top",
        "cost": "low"
    },
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

# 从 openclaw.json 读取 API keys
with open(r'C:\Users\scrccpa\.openclaw\openclaw.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

# 读取三份制度文本
with open('output/融策管理制度三件套.md', 'r', encoding='utf-8') as f:
    policies_text = f.read()

# 评审提示词
review_prompt = f"""你是一位资深的企业管理顾问和制度设计专家。现在需要你对以下三份管理制度进行专业评审：

{policies_text}

**评审维度（每项0-10分）：**
1. **科学性** — 制度设计是否符合管理学原理？利益机制是否合理？
2. **可执行性** — 条款是否足够具体？财务能不能算清楚？有没有操作难点？
3. **行业适配性** — 是否符合"政府审计+工程咨询"行业特征？是否考虑了To-G业务回款周期长、靠关系等行业特点？
4. **防漏洞能力** — 是否预设了常见纠纷和灰色地带？会不会被高管钻空子?
5. **变革阻力** — 从人性角度，这套制度推行会遇到多大阻力？

**输出要求**：
1. 按5个维度逐项打分（0-10分），并给出简要理由
2. 指出3-5个最大的风险点或漏洞
3. 给出2-3条优化建议
4. 最后给出总体评价（推荐实施/谨慎实施/不推荐）

请直接输出评审结果，格式：
```
【评审维度打分】
科学性：X/10 — 理由
可执行性：X/10 — 理由
行业适配性：X/10 — 理由
防漏洞能力：X/10 — 理由
变革阻力：X/10 — 理由

【风险点】
1. ...
2. ...

【优化建议】
1. ...
2. ...

【总体评价】推荐实施/谨慎实施/不推荐 — 理由
```
"""

opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

def call_model(model_id, meta):
    """调用单个模型进行评审"""
    provider_id = meta['provider']
    provider_cfg = config['models']['providers'][provider_id]
    api_key = provider_cfg['apiKey']
    
    # Claude 系列用 anthropic messages API
    if 'claude' in model_id:
        url = f"{meta['baseUrl']}/v1/messages"
        payload = {
            "model": model_id,
            "max_tokens": 4096,
            "messages": [{"role": "user", "content": review_prompt}]
        }
    else:
        # Gemini 用 OpenAI-compatible API
        url = f"{meta['baseUrl']}/chat/completions"
        payload = {
            "model": model_id,
            "messages": [{"role": "user", "content": review_prompt}],
            "max_tokens": 4096
        }
    
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode('utf-8'),
        headers={
            "Content-Type": "application/json",
            "x-api-key" if 'claude' in model_id else "Authorization": 
                api_key if 'claude' in model_id else f"Bearer {api_key}",
            "anthropic-version": "2023-06-01" if 'claude' in model_id else ""
        }
    )
    
    try:
        with opener.open(req, timeout=120) as resp:
            result = json.loads(resp.read().decode('utf-8'))
            
            # Claude API 返回格式
            if 'claude' in model_id:
                content = result['content'][0]['text']
                tokens = result.get('usage', {}).get('output_tokens', 0)
            else:
                content = result['choices'][0]['message']['content']
                tokens = result.get('usage', {}).get('total_tokens', 0)
            
            return {
                "status": "ok",
                "content": content,
                "tokens": tokens
            }
    except Exception as e:
        return {"status": "error", "error": str(e)[:300]}

# 主流程
print("🔬 4模型专业评审启动（Claude×3 + Gemini×1）...")
print("=" * 80)

results = {}
total_tokens = 0

for idx, (model_id, meta) in enumerate(MODELS.items(), 1):
    print(f"[{idx}/4] {model_id} ({meta['cost']})...", end=" ", flush=True)
    
    result = call_model(model_id, meta)
    results[model_id] = result
    
    if result['status'] == 'ok':
        print(f"✅ {result['tokens']} tokens")
        total_tokens += result['tokens']
    else:
        print(f"❌ {result['error']}")
    
    time.sleep(3)  # 避免触发限流

print("=" * 80)
print(f"✅ 评审完成，总Token消耗: {total_tokens}")

# 保存完整结果
with open('output/制度评审-4模型专业意见.md', 'w', encoding='utf-8') as f:
    f.write("# 融策管理制度三件套 — 4模型专业评审报告\n\n")
    f.write(f"**评审时间**: 2026-07-15 23:05\n")
    f.write(f"**参与模型**: Claude Fable-5 / Sonnet-5 / Opus-4-8 + Gemini 3.1 Pro Preview\n")
    f.write(f"**总Token消耗**: {total_tokens}\n\n")
    f.write("---\n\n")
    
    for model_id, result in results.items():
        f.write(f"## {model_id} ({MODELS[model_id]['cost']})\n\n")
        if result['status'] == 'ok':
            f.write(result['content'])
            f.write(f"\n\n**Token**: {result['tokens']}\n\n")
        else:
            f.write(f"**评审失败**: {result['error']}\n\n")
        f.write("---\n\n")

print("\n💾 完整评审报告已保存至: output/制度评审-4模型专业意见.md")
