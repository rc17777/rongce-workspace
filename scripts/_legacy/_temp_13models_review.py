# -*- coding: utf-8 -*-
import json
import urllib.request
import urllib.error
import time

# 从 openclaw.json 读取配置
with open(r'C:\Users\scrccpa\.openclaw\openclaw.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

# 13个模型配置（所有可用模型）
MODELS = {
    "deepseek-v4-flash": {"provider": "custom-cbwyy-top-v1", "cost": "free"},
    "deepseek-v4-pro": {"provider": "custom-cbwyy-top-v1", "cost": "low"},
    "qwen3.7-plus": {"provider": "custom-cbwyy-qwen", "cost": "low"},
    "claude-fable-5": {"provider": "custom-cbwyy-fable", "cost": "low"},
    "claude-sonnet-5": {"provider": "custom-cbwyy-claude", "cost": "medium"},
    "claude-opus-4-8": {"provider": "custom-cbwyy-opus", "cost": "high"},
    "gpt-5.5": {"provider": "custom-cbwyy-gpt55", "cost": "medium"},
    "gpt-5.6-luna": {"provider": "custom-cbwyy-luna", "cost": "medium"},
    "gpt-5.6-sol": {"provider": "custom-cbwyy-sol", "cost": "medium"},
    "gpt-5.6-terra": {"provider": "custom-cbwyy-terra", "cost": "medium"},
    "gemini-3.1-pro-preview": {"provider": "custom-cbwyy-gemini", "cost": "preview"},
    "gpt-image-2": {"provider": "custom-cbwyy-image", "cost": "special"},  # 跳过
    "doubao-seed-2.0-lite": {"provider": "custom-cbwyy-doubao", "cost": "low"}
}

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

def call_model(model_id, provider_id):
    """调用单个模型进行评审"""
    provider_cfg = config['models']['providers'][provider_id]
    api_key = provider_cfg['apiKey']
    base_url = provider_cfg['baseUrl']
    
    # gpt-image-2 跳过（只能生图）
    if model_id == "gpt-image-2":
        return {"status": "skipped", "reason": "生图专用模型，不参与文本评审"}
    
    payload = {
        "model": model_id,
        "messages": [{"role": "user", "content": review_prompt}],
        "max_tokens": 2000,
        "temperature": 0.5
    }
    
    # gemini 需要特殊处理 baseUrl
    if provider_id == "custom-cbwyy-gemini":
        url = f"{base_url}/chat/completions"
    else:
        url = f"{base_url}/v1/chat/completions"
    
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode('utf-8'),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
    )
    
    try:
        with opener.open(req, timeout=90) as resp:
            result = json.loads(resp.read().decode('utf-8'))
            content = result['choices'][0]['message']['content']
            usage = result.get('usage', {})
            return {
                "status": "ok",
                "content": content,
                "tokens": usage.get('total_tokens', 0)
            }
    except Exception as e:
        return {"status": "error", "error": str(e)[:200]}

# 主流程
print("🔬 13模型联合评审启动...")
print("=" * 80)

results = {}
total_tokens = 0

for idx, (model_id, meta) in enumerate(MODELS.items(), 1):
    print(f"[{idx}/13] {model_id} ({meta['cost']})...", end=" ", flush=True)
    
    result = call_model(model_id, meta['provider'])
    results[model_id] = result
    
    if result['status'] == 'ok':
        print(f"✅ {result['tokens']} tokens")
        total_tokens += result['tokens']
    elif result['status'] == 'skipped':
        print(f"⏭️  {result['reason']}")
    else:
        print(f"❌ {result['error']}")
    
    time.sleep(2)  # 避免触发限流

print("=" * 80)
print(f"✅ 评审完成，总Token消耗: {total_tokens}")

# 保存完整结果
with open('output/制度评审-13模型联合意见.md', 'w', encoding='utf-8') as f:
    f.write("# 融策管理制度三件套 — 13模型联合评审报告\n\n")
    f.write(f"**评审时间**: 2026-07-15 22:40\n")
    f.write(f"**参与模型**: 13个（12个文本模型 + 1个跳过）\n")
    f.write(f"**总Token消耗**: {total_tokens}\n\n")
    f.write("---\n\n")
    
    for model_id, result in results.items():
        f.write(f"## {model_id} ({MODELS[model_id]['cost']})\n\n")
        if result['status'] == 'ok':
            f.write(result['content'])
            f.write(f"\n\n**Token**: {result['tokens']}\n\n")
        elif result['status'] == 'skipped':
            f.write(f"*{result['reason']}*\n\n")
        else:
            f.write(f"**评审失败**: {result['error']}\n\n")
        f.write("---\n\n")

print("\n💾 完整评审报告已保存至: output/制度评审-13模型联合意见.md")
