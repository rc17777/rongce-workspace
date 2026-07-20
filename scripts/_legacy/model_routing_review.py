#!/usr/bin/env python3
"""
14模型路由评审脚本 v1.0
用所有14个模型评审路由配置方案，收集专业意见。
"""
import json, time, urllib.request

PROMPT = """你是一个AI架构评审专家。请评审以下「审计事务所AI模型路由配置」。

背景：四川融策会计师事务所使用14个AI模型处理政府审计业务（绩效评价、资产清查、经济责任审计、工程咨询等）。

路由核心原则：按「错误代价」而非「任务类型」分配模型——答错了后果越严重，用越强越贵的模型。

配置：
- deepseek-v4-flash(免费): 日常/代码/心跳 — 错了重来~0代价
- qwen3.7-plus(低): 中文公文/错别字/图片 — 改两行就好
- fable-5(低): 咨询层独立顾问 — 方向选错代价
- deepseek-v4-pro(低): 推理/数据核查/串标分析
- gemini-3.1-pro-preview: 长文档专家(1M+上下文) — 独门优势
- sonnet-5(中): 合规审查/逻辑/细节
- gpt-5.5(中): 英文润色/读者视角
- gpt-5.6-luna/sol/terra(中): 创意/分析/综合审查
- opus-4-8(高): 压舱石/最终签字 ≤2次/项目
- gpt-image-2: 生图
- doubao: 信创合规备选
- deepseek-chat: 直连DeepSeek逃生通道(不经过代理)

成本: 75%免费调用, 中高价≤7%, opus≤2次/项目
容灾: 所有13个模型走cbwyy.top代理(单点故障风险), 1个直连deepseek逃生

请用一两句话给出你的评审结论：(1)这个方案最大的问题是什么？(2)如果只能改一件事,改什么？直接说,不要客套。"""

MODELS = [
    {"id": "deepseek-v4-flash", "url": "https://cbwyy.top/v1/chat/completions", "key": "sk-Bq4EalSwLmehZ3xXa55b7TzRX4HIlbTppgdKQ0ElOab09AZa", "cat": "free"},
    {"id": "qwen3.7-plus", "url": "https://cbwyy.top/v1/chat/completions", "key": "sk-9Jwqw4U5ahchjaLgVqzvfJQvm3itJEv2GHTV8KAofagQrf77", "cat": "low"},
    {"id": "claude-fable-5", "url": "https://cbwyy.top/v1/chat/completions", "key": "sk-V3KPfTqMi3x13gtbftyVH94pAA9YOLQXYAVElYV9WRabYDzh", "cat": "consult"},
    {"id": "deepseek-v4-pro", "url": "https://cbwyy.top/v1/chat/completions", "key": "sk-Bq4EalSwLmehZ3xXa55b7TzRX4HIlbTppgdKQ0ElOab09AZa", "cat": "mid"},
    {"id": "gemini-3.1-pro-preview", "url": "https://cbwyy.top/v1/chat/completions", "key": "sk-dxNjrEh4rXIinsnHVLAKE17e1yqf6XFhtWZuPrnyzg5lfISw", "cat": "preview"},
    {"id": "claude-sonnet-5", "url": "https://cbwyy.top/v1/chat/completions", "key": "sk-R0ndBzSRNP6GWAW82HspfjwKxJvPwBeoHPrkznz8rjCNL3SH", "cat": "high"},
    {"id": "gpt-5.5", "url": "https://cbwyy.top/v1/chat/completions", "key": "sk-bs4fgPtIHhh4kKTKIRh33HISbvxMJDcQQx2kRnlmWv4faesU", "cat": "high"},
    {"id": "gpt-5.6-luna", "url": "https://cbwyy.top/v1/chat/completions", "key": "sk-p3ynqetGeLU5T5TpzXFAFimCaTrvIT6kpqGkbP2SrpqvpbrJ", "cat": "high"},
    {"id": "gpt-5.6-sol", "url": "https://cbwyy.top/v1/chat/completions", "key": "sk-eulyTfe7nRmr5ruwQH85kIfHkc8PPd88EoYGX0yadzlrkEpv", "cat": "high"},
    {"id": "gpt-5.6-terra", "url": "https://cbwyy.top/v1/chat/completions", "key": "sk-9qOvtLFgtvohPegNNGiwPr7fye1SgSCIW1C2viiKFp1b8lzh", "cat": "high"},
    {"id": "claude-opus-4-8", "url": "https://cbwyy.top/v1/chat/completions", "key": "sk-1rL8MpWIH16CZ64xZLV6buNHS7dlmIdBk5HGOYs5hV0nOHcJ", "cat": "fatal"},
    {"id": "gpt-image-2", "url": "https://cbwyy.top/v1/chat/completions", "key": "sk-KVp2E6u9FnnRA3BQxSNvbWKW6zd2JsDQa8YlmR4ZxGtVsXIQ", "cat": "special"},
    {"id": "doubao-seed-2.0-lite", "url": "https://cbwyy.top/v1/chat/completions", "key": "sk-8Up5r8WtFOQrckhQCxOxaRYES5KAWQqgKMdrJng1l0DJ9gix", "cat": "compliance"},
    {"id": "deepseek-chat", "url": "https://api.deepseek.com/v1/chat/completions", "key": "sk-e766441b9f824223ac4f3949f19f6f7a", "cat": "escape"},
]

proxy_handler = urllib.request.ProxyHandler({})
opener = urllib.request.build_opener(proxy_handler)

results = []
print(f"{'模型':30s} {'状态':>4} {'耗时':>6}  {'类型':>10}  结论摘要")
print("=" * 90)

for m in MODELS:
    start = time.time()
    payload = {"model": m["id"], "messages": [{"role": "user", "content": PROMPT}], "max_tokens": 150}
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(m["url"], data=data,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {m['key']}"})
    try:
        with opener.open(req, timeout=60) as resp:
            body = json.loads(resp.read().decode())
            content = body.get("choices", [{}])[0].get("message", {}).get("content", "无回复")[:120]
            elapsed = time.time() - start
            results.append({"model": m["id"], "cat": m["cat"], "status": "OK", "elapsed": elapsed, "opinion": content})
            print(f"{m['id']:30s} {200:>4} {elapsed:>5.1f}s  {m['cat']:>10}   {content}")
    except Exception as e:
        elapsed = time.time() - start
        results.append({"model": m["id"], "cat": m["cat"], "status": "FAIL", "elapsed": elapsed, "opinion": str(e)[:100]})
        print(f"{m['id']:30s} {'FAIL':>4} {elapsed:>5.1f}s  {m['cat']:>10}   ❌ {str(e)[:80]}")

ok = sum(1 for r in results if r["status"] == "OK")
print("=" * 90)
print(f"通过: {ok}/{len(results)}")

# Save results
with open("output/14model_routing_review.json", "w", encoding="utf-8") as f:
    json.dump({"timestamp": time.strftime("%Y-%m-%d %H:%M:%S"), "results": results}, f, ensure_ascii=False, indent=2)
print("结果已保存: output/14model_routing_review.json")
