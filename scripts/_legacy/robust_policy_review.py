# -*- coding: utf-8 -*-
"""
稳健的制度评审脚本 v3.0
策略：场景化问答 + 重试 + 拒答检测 + 断点续跑
v3 修复（2026-07-16）:
  1. stdout 强制 UTF-8（Windows GBK 坑）
  2. 模型池瘦身 7→4（opus留作终审，遵守≤2次/项目；fable/sol剔除降本）
  3. 每次调用带2次重试+指数退避，超时60→120s
  4. 拒答检测（短回复+can't/cannot → 重试）
  5. 断点续跑：checkpoint JSON，跑挂了重启只补失败项
"""
import json
import os
import sys
import urllib.request
import urllib.error
import time
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

# 从 openclaw.json 读取配置
with open(r'C:\Users\scrccpa\.openclaw\openclaw.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

# 评审模型池 v3（opus 保留终审，不进池）
REVIEW_MODELS = [
    {"id": "deepseek-v4-pro", "provider": "custom-cbwyy-top-v1", "type": "openai", "cost": "low"},
    {"id": "claude-sonnet-5", "provider": "custom-cbwyy-claude", "type": "anthropic", "cost": "medium"},
    {"id": "gpt-5.6-sol", "provider": "custom-cbwyy-sol", "type": "openai", "cost": "medium"},  # gpt-5.5/qwen 都欠费403，换sol
    {"id": "gemini-3.1-pro-preview", "provider": "custom-cbwyy-gemini", "type": "openai", "cost": "preview"}
]

CHECKPOINT = 'output/制度评审-场景化问答结果.json'
REPORT = 'output/制度评审-综合意见报告.md'
MAX_RETRIES = 2
TIMEOUT = 120

def is_refusal(text):
    """检测拒答式废话回复"""
    if not text:
        return True
    t = text.strip().lower()
    return len(t) < 80 and ("can't" in t or "cannot" in t or "i'm unable" in t or "sorry" in t)

# 场景化评审问题（每份制度5个关键争议点）
REVIEW_QUESTIONS = {
    "项目独立核算与分润制度": [
        "项目净利润按「公司50% / 负责人20% / 组员30%」分配，这个比例是否合理？是否需要调整？",
        "亏损项目50%由负责人承担、从其他盈利项目分润中扣除，这个机制是否过于严苛？会不会打击积极性？",
        "「实际到账回款才分润」的规则，在审计行业（回款周期长）是否合理？",
        "公摊成本按回款额10%统一提取，这个比例是否科学？会不会导致成本核算不准确？",
        "中途离职员工的分润处理（未结项取消、已结项降至10%），是否公平？有无法律风险？"
    ],
    "跨部门协同与交叉营销奖励办法": [
        "引流项目按净利润10-15%奖励引荐人，这个比例对引荐人是否有足够吸引力？",
        "「客户主动找上门不算引流」的规则，如何防止抢单争议？",
        "线索报备保护期6个月，这个时长是否合理？太短还是太长？",
        "引流的项目如果亏损，协同奖为0但引荐人不承担连带责任——这样设计是否会导致「乱引流、不负责」？",
        "联合项目按合同金额拆分、各自独立核算，实际操作中如何界定「联合」和「纯引流」的边界？"
    ],
    "高管经营目标责任与绩效考核办法": [
        "高管考核「经营业绩50分 + 协同20分 + 管理质量30分」，这个权重分配是否合理？",
        "绩效系数0.6-1.2倍，这个区间是否足够拉开差距？会不会让优秀高管觉得激励不够？",
        "20%质量风险准备金冻结一年，这个比例会不会让高管觉得「赚到的钱拿不到手」而抵触？",
        "一票否决红线（重大质量事故 → 当季绩效直接0分），这个处罚是否过重？",
        "高管绩效考核按季度兑现，频率是否合适？是否应该月度考核、季度兑现？"
    ]
}

opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

def call_model_once(model_meta, policy_name, question):
    """用场景化问题评审（单个争议点，单次调用）"""
    provider_id = model_meta['provider']
    provider_cfg = config['models']['providers'][provider_id]
    api_key = provider_cfg['apiKey']
    base_url = provider_cfg['baseUrl']
    
    prompt = f"""你是一位资深的企业管理咨询专家，擅长制度设计和人力资源管理。

**背景**：四川融策是一家审计+工程咨询公司（20-30人规模），老板感觉高管各自为政、制度虚设、自己一个人在拼。现在设计了《{policy_name}》，希望通过利益机制改革激活团队。

**请评估以下争议点**：

{question}

**请从以下角度给出专业意见**（300字以内）：
1. 这个设计的合理性（是否符合管理学原理？）
2. 潜在风险（可能引发什么问题？）
3. 优化建议（如何改进？）
4. 推行难度（1-10分，10分=极难推行）
"""
    
    try:
        if model_meta['type'] == 'anthropic':
            url = f"{base_url}/v1/messages"
            payload = {
                "model": model_meta['id'],
                "max_tokens": 1024,
                "messages": [{"role": "user", "content": prompt}]
            }
            headers = {
                "Content-Type": "application/json",
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01"
            }
        else:
            url = f"{base_url}/chat/completions"
            payload = {
                "model": model_meta['id'],
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 1024
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
        
        with opener.open(req, timeout=TIMEOUT) as resp:
            result = json.loads(resp.read().decode('utf-8'))
            
            if model_meta['type'] == 'anthropic':
                content = result['content'][0]['text']
                tokens = result.get('usage', {}).get('output_tokens', 0)
            else:
                content = result['choices'][0]['message']['content']
                tokens = result.get('usage', {}).get('total_tokens', 0)
            
            if is_refusal(content):
                return {"status": "error", "error": f"拒答: {content[:100]}"}
            return {"status": "ok", "content": content, "tokens": tokens}
    
    except urllib.error.HTTPError as e:
        error_msg = f"HTTP {e.code}: {e.reason}"
        try:
            error_body = e.read().decode('utf-8')[:200]
            error_msg += f" | {error_body}"
        except:
            pass
        return {"status": "error", "error": error_msg}
    
    except Exception as e:
        return {"status": "error", "error": str(e)[:300]}

def call_model_scenario(model_meta, policy_name, question):
    """带重试的评审调用：2次重试 + 指数退避"""
    last = None
    for attempt in range(MAX_RETRIES + 1):
        if attempt > 0:
            time.sleep(5 * (2 ** (attempt - 1)))  # 5s, 10s
        last = call_model_once(model_meta, policy_name, question)
        if last['status'] == 'ok':
            return last
    return last

# 主流程
print("🔬 稳健制度评审启动 v3（场景化问答 + 重试 + 断点续跑）...")
print("=" * 80)

# 断点续跑：加载已有checkpoint
all_results = {}
if os.path.exists(CHECKPOINT):
    try:
        with open(CHECKPOINT, 'r', encoding='utf-8') as f:
            all_results = json.load(f)
        print(f"📂 发现checkpoint，续跑模式（已有 {sum(len(v) for v in all_results.values())} 个争议点记录）")
    except Exception:
        all_results = {}

def save_checkpoint():
    with open(CHECKPOINT, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)

total_tokens = 0
total_success = 0
total_failed = 0

for policy_name, questions in REVIEW_QUESTIONS.items():
    print(f"\n📋 评审《{policy_name}》（{len(questions)}个争议点）")
    all_results.setdefault(policy_name, {})
    
    for i, question in enumerate(questions, 1):
        q_key = f"Q{i}"
        print(f"\n  争议点 {i}/{len(questions)}: {question[:50]}...")
        all_results[policy_name].setdefault(q_key, {"question": question, "reviews": {}})
        
        for model_meta in REVIEW_MODELS:
            model_id = model_meta['id']
            
            # 断点续跑：已成功的跳过
            prev = all_results[policy_name][q_key]["reviews"].get(model_id)
            if prev and prev.get('status') == 'ok':
                print(f"    [{model_id}] ⏭️ 已完成，跳过")
                total_success += 1
                total_tokens += prev.get('tokens', 0)
                continue
            
            print(f"    [{model_id}]...", end=" ", flush=True)
            
            result = call_model_scenario(model_meta, policy_name, question)
            all_results[policy_name][q_key]["reviews"][model_id] = result
            save_checkpoint()  # 每次调用后落盘
            
            if result['status'] == 'ok':
                print(f"✅ {result['tokens']}t")
                total_tokens += result['tokens']
                total_success += 1
            else:
                print(f"❌ {result['error'][:80]}")
                total_failed += 1
            
            time.sleep(2)

print("\n" + "=" * 80)
print(f"✅ 评审完成")
print(f"  成功: {total_success} | 失败: {total_failed} | Token消耗: {total_tokens}")

# 生成人类可读报告
with open(REPORT, 'w', encoding='utf-8') as f:
    f.write("# 融策管理制度三件套 — 多模型综合评审报告\n\n")
    f.write(f"**评审时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
    f.write(f"**评审模型**: 4个（DeepSeek V4 Pro / Claude Sonnet-5 / GPT-5.6-Sol / Gemini 3.1 Pro）\n")
    f.write(f"**评审方式**: 场景化问答（每份制度5个关键争议点，每个争议点4个模型独立评估）\n")
    f.write(f"**总Token消耗**: {total_tokens} | 成功率: {total_success}/{total_success+total_failed}\n\n")
    f.write("---\n\n")
    
    for policy_name, qa_dict in all_results.items():
        f.write(f"# {policy_name}\n\n")
        
        for q_id, q_data in qa_dict.items():
            f.write(f"## {q_id}: {q_data['question']}\n\n")
            
            for model_id, result in q_data['reviews'].items():
                f.write(f"### {model_id} 评审意见\n\n")
                if result['status'] == 'ok':
                    f.write(result['content'])
                    f.write(f"\n\n*Token: {result['tokens']}*\n\n")
                else:
                    f.write(f"**评审失败**: {result['error']}\n\n")
                f.write("---\n\n")

print("\n💾 结果已保存:")
print(f"  - JSON: {CHECKPOINT}")
print(f"  - 报告: {REPORT}")
if total_failed:
    print(f"⚠️ 有 {total_failed} 项失败，重跑本脚本将自动只补失败项（断点续跑）")
