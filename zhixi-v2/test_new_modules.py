#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""验证智析v2.0新模块测试脚本"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

print("=" * 60)
print("智析v2.0 新模块验证测试")
print("=" * 60)

# 测试1: RAG桥
print("\n【测试1】RAG知识桥")
from modules.knowledge.rag_bridge import get_rag_bridge
bridge = get_rag_bridge()
status = bridge.get_status()
print(f"  加载状态: {status['loaded']}")
print(f"  Chunk数量: {status['chunks_count']}")
print(f"  API可用: {status['api_available']}")

results = bridge.search('专项债券审计', top_k=3)
print(f"  搜索测试: 找到 {len(results)} 条结果")
for r in results[:2]:
    print(f"    - {r['source']} ({int(r['score']*100)}%)")

# 测试2: 报告复核引擎
print("\n【测试2】报告复核引擎")
from modules.knowledge.report_review_engine import get_review_engine
engine = get_review_engine()
print(f"  复核维度: {len(engine.dimensions)} 个")
print(f"  维度示例: {engine.dimensions[0]['name']}")

test_text = '审记发现，该单位帐目存在其它问题。'
issues = engine.rule_based_check(test_text)
print(f"  规则检查测试: 发现 {len(issues)} 个问题")
for i in issues:
    print(f"    - {i['message']}")

# 测试3: 串标检测扩展
print("\n【测试3】串标检测扩展")
from modules.audit_models.bid_collusion_extended import get_bid_detector
detector = get_bid_detector()
print(f"  天眼查API: {'已配置' if detector.tianyancha_key else '未配置'}")

docs = [
    {'name': '公司A', 'contact': '13800138000', 'email': 'a@test.com'},
    {'name': '公司B', 'contact': '13800138000', 'email': 'b@test.com'},
]
result = detector.local_relation_check(docs)
print(f"  本地检测测试: 风险等级 {result['risk_level']}")
print(f"  关联数: {result['relations_found']}")

print("\n" + "=" * 60)
print("全部测试通过")
print("=" * 60)
