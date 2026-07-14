#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试智析v2.0新API"""
import requests, json, sys
sys.stdout.reconfigure(encoding='utf-8')

base = 'http://127.0.0.1:5002'

print('=' * 60)
print('智析v2.0 新API测试')
print('=' * 60)

print('\n=== 测试1: RAG状态 ===')
r = requests.get(f'{base}/api/rag/status', timeout=10)
print(f'状态码: {r.status_code}')
print(f'响应: {r.json()}')

print('\n=== 测试2: RAG搜索 ===')
r = requests.get(f'{base}/api/rag/search?q=专项债券审计&k=3', timeout=10)
data = r.json()
print(f'状态码: {r.status_code}')
print(f'查询: {data.get("query")}')
print(f'结果数: {data.get("count")}')
for i, res in enumerate(data.get('results', [])[:2]):
    print(f'  [{i+1}] {res["source"]} ({int(res["score"]*100)}%)')

print('\n=== 测试3: 复核维度 ===')
r = requests.get(f'{base}/api/review/dimensions', timeout=10)
data = r.json()
print(f'状态码: {r.status_code}')
print(f'维度数: {data.get("count")}')
print(f'前3个: {[d["name"] for d in data.get("dimensions", [])[:3]]}')

print('\n=== 测试4: 快速规则检查 ===')
text = '审记发现，该单位帐目存在其它问题。'
r = requests.post(f'{base}/api/review/quick', json={'text': text}, timeout=10)
data = r.json()
print(f'状态码: {r.status_code}')
print(f'发现问题: {data.get("issues_found")}')
for issue in data.get('issues', []):
    print(f'  - {issue["message"]}')

print('\n=== 测试5: 串标L8本地检测 ===')
docs = [
    {'name': '公司A', 'contact': '13800138000', 'email': 'a@test.com'},
    {'name': '公司B', 'contact': '13800138000', 'email': 'b@test.com'},
]
r = requests.post(f'{base}/api/bid/l8/analyze', json={'bidders': ['公司A','公司B'], 'bidder_docs': docs, 'use_api': False}, timeout=10)
data = r.json()
print(f'状态码: {r.status_code}')
print(f'风险等级: {data.get("risk_level")}')
print(f'关联数: {data.get("relations_found")}')

print('\n' + '=' * 60)
print('全部API测试完成')
print('=' * 60)
