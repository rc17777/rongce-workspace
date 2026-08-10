#!/usr/bin/env python3
"""
演示脚本：模拟 Agent 活动，展示监控面板效果
用法：python demo.py
"""
import urllib.request, json, time, random, sys
sys.stdout.reconfigure(encoding='utf-8')

API = "http://127.0.0.1:8765"

AGENTS = [
    "data_scout", "contract_hound", "bid_hunter", "law_inspector",
    "workpaper_crafter", "report_writer", "review_sentinel",
    "budget_estimator", "settlement_auditor", "fiscal_reviewer",
    "performance_evaluator", "expert_bias_detector", "meeting_minutes_analyzer",
    "ocr_processor", "data_classifier", "data_desensitizer",
    "adjustment_scribe", "plan_writer",
]

TASKS = [
    "分析2025年度预算执行数据",
    "审查高新区EPC总承包合同",
    "检测投标文件相似度(项目#24038)",
    "解读《招标投标法实施条例》第39条",
    "生成审计工作底稿-固定资产",
    "撰写经济责任审计报告初稿",
    "复核报告P0发现-金额一致性",
    "核算道路工程材料价差",
    "审计结算清单-变更项8-12",
    "评审2024年度财政资金使用合规性",
    "绩效评价-民生专项资金6项指标",
    "检测评标专家打分偏差度",
    "分析党组会议纪要-2025Q2",
    "OCR识别验收单批次#23",
    "分类归档审计取证单",
    "脱敏处理个人身份信息字段",
    "编制审计调整分录-收入确认",
    "撰写2026年度审计计划方案",
]

def post(path, data):
    try:
        req = urllib.request.Request(f"{API}{path}",
            data=json.dumps(data).encode('utf-8'),
            headers={"Content-Type": "application/json"},
            method="POST")
        urllib.request.urlopen(req, timeout=3)
    except:
        pass

def demo():
    print("🎬 开始模拟 Agent 活动...\n")

    # 阶段1: 批量启动一批 agent
    batch1 = random.sample(AGENTS, 6)
    for i, agent in enumerate(batch1):
        task = TASKS[i]
        print(f"  🟢 {agent} → working: {task}")
        post(f"/api/agent/{agent}/status", {"status": "working", "task": task})
        time.sleep(0.3)

    time.sleep(2)

    # 阶段2: 完成一部分
    for i, agent in enumerate(batch1[:4]):
        print(f"  ✅ {agent} → completed")
        post(f"/api/agent/{agent}/status", {
            "status": "completed",
            "elapsedMs": random.randint(2500, 15000)
        })
        time.sleep(0.3)

    time.sleep(2)

    # 阶段3: 再启动几个
    batch2 = random.sample([a for a in AGENTS if a not in batch1], 4)
    for i, agent in enumerate(batch2):
        task = TASKS[6 + i]
        print(f"  🟢 {agent} → working: {task}")
        post(f"/api/agent/{agent}/status", {"status": "working", "task": task})
        time.sleep(0.3)

    time.sleep(2)

    # 阶段4: 模拟一个异常
    error_agent = batch1[4] if len(batch1) > 4 else batch1[-1]
    print(f"  🔴 {error_agent} → ERROR: API速率限制")
    post(f"/api/agent/{error_agent}/status", {
        "status": "error",
        "error": "API响应429 Too Many Requests，重试3次后放弃"
    })

    time.sleep(2)

    # 阶段5: 完成剩余
    for agent in batch2:
        print(f"  ✅ {agent} → completed")
        post(f"/api/agent/{agent}/status", {
            "status": "completed",
            "elapsedMs": random.randint(2000, 12000)
        })
        time.sleep(0.3)

    for agent in batch1[5:]:
        if agent != error_agent:
            print(f"  ✅ {agent} → completed")
            post(f"/api/agent/{agent}/status", {
                "status": "completed",
                "elapsedMs": random.randint(3000, 10000)
            })
            time.sleep(0.3)

    print("\n🎉 演示完成！查看面板: http://127.0.0.1:8765\n")

if __name__ == "__main__":
    demo()
