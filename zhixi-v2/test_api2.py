#!/usr/bin/env python3
"""智析 v2.0 API验证 - 简化版"""
import requests, sys

BASE = "http://127.0.0.1:5002/api"
p = f = 0

def test(label, method, path, payload=None, check_fn=None):
    global p, f
    try:
        url = BASE + path
        r = requests.get(url, timeout=10) if method == "GET" else requests.post(url, json=payload, timeout=10)
        ok = r.status_code == 200
        if ok:
            p += 1
            detail = check_fn(r.json()) if check_fn else ""
            print(f"  OK  {label:40s} {detail}")
        else:
            f += 1
            print(f"  FAIL {label:40s} HTTP {r.status_code}")
    except Exception as e:
        f += 1
        print(f"  FAIL {label:40s} {e}")

print("=" * 60)
print("  zhiXi v2.0 E2E Test")
print("=" * 60)

# 1. System
print("\n[1/8] SYSTEM")
test("Status", "GET", "/status", check_fn=lambda d: "v"+d["version"])

# 2. Collector
print("\n[2/8] DATA COLLECTION")
test("DB types", "GET", "/collector/databases", check_fn=lambda d: "{} DB ({} domestic)".format(len(d["supported"]), len(d["domestic"])))
test("Accounting SW", "GET", "/collector/accounting/software", check_fn=lambda d: "{} software".format(len(d)))
test("Create task", "POST", "/collector/tasks",
     payload={"name":"test_task","source_type":"api","source_config":{"url":"http://example.com"}},
     check_fn=lambda d: "task_id=" + d.get("task_id","?"))

# 3. Validator
print("\n[3/8] DATA VALIDATION")
test("Rules list", "GET", "/validator/rules", check_fn=lambda d: "{} rules".format(len(d)))
test("Run validation", "POST", "/validator/run",
     payload={"data":[{"code":"1001","dr":100,"cr":100}],"key_cols":["code"],"required_cols":["code"]},
     check_fn=lambda d: "passed={}/{}".format(d["summary"]["passed"], d["summary"]["total"]))
test("Outlier detect", "POST", "/cleaner/outliers",
     payload={"data":[{"amount":100},{"amount":200},{"amount":99999}],"col":"amount","method":"iqr"},
     check_fn=lambda d: "{} outliers".format(d["total_outliers"]))

# 4. Standardizer
print("\n[4/8] DATA STANDARDIZATION")
test("Domains", "GET", "/standardizer/domains", check_fn=lambda d: "{} domains: {}".format(len(d["domains"]), ", ".join(d["domains"])))
test("Financial schema", "GET", "/standardizer/schema/financial", check_fn=lambda d: "{} fields".format(len(d)))

# 5. Unstructured
print("\n[5/8] UNSTRUCTURED PROCESSING")
test("Contract extract", "POST", "/unstructured/extract",
     payload={"text": "甲方：融策会计师事务所 乙方：XX科技 合同金额：50万元 签订日期：2026年6月1日"},
     check_fn=lambda d: "type={}".format(d["doc_type"]))
test("Bidding extract", "POST", "/unstructured/extract",
     payload={"text": "项目名称：XX县数据分析采购 采购方式：公开招标 预算金额：200万元 中标人：XX公司"},
     check_fn=lambda d: "type={}".format(d["doc_type"]))
test("Meeting extract", "POST", "/unstructured/extract",
     payload={"text": "XX县审计局会议纪要 时间：2026-05-30 参会：张三、李四 主持：张局长"},
     check_fn=lambda d: "type={}".format(d["doc_type"]))

# 6. Audit Models
print("\n[6/8] AUDIT MODELS")
test("Categories", "GET", "/models/categories", check_fn=lambda d: "{} categories".format(len(d)))
test("All models", "GET", "/models", check_fn=lambda d: "{} models".format(len(d)))
test("Model M001", "GET", "/models/M001", check_fn=lambda d: d["name"])
test("Model M007", "GET", "/models/M007", check_fn=lambda d: d["name"])
test("Model M015", "GET", "/models/M015", check_fn=lambda d: d["name"])
test("Model M030", "GET", "/models/M030", check_fn=lambda d: d["name"])
test("Search", "GET", "/models/search?q=%E6%8B%9B%E6%A0%87", check_fn=lambda d: "{} hits".format(len(d)))
test("Analysis methods", "GET", "/models/analysis-methods", check_fn=lambda d: "{} methods".format(len(d)))

# 7. Big Data
print("\n[7/8] BIG DATA ANALYTICS")
test("Fund flow graph", "POST", "/bigdata/graph/fund-flow",
     payload={"transactions":[{"from":"Finance","to":"Dept","amount":1000000},{"from":"Dept","to":"A","amount":500000}]},
     check_fn=lambda d: "{}n {}e".format(d["nodes"], d["edges"]))
test("Supplier network", "POST", "/bigdata/graph/supplier",
     payload={"bid_data":[{"project":"P1","bidder":"A","ip":"1.1.1.1"},{"project":"P1","bidder":"B","ip":"1.1.1.1"}]},
     check_fn=lambda d: "{}n {}e".format(d["nodes"], d["edges"]))
test("Word freq", "POST", "/bigdata/text/wordcloud",
     payload={"texts":["专项资金管理使用不规范","资金拨付进度缓慢","审计发现资金挪用"]},
     check_fn=lambda d: "{} words".format(len(d)))
test("Bar chart", "POST", "/bigdata/visualize",
     payload={"type":"bar","data":{"A":85,"B":62},"title":"test"},
     check_fn=lambda d: "chart OK")

# 8. Knowledge
print("\n[8/8] KNOWLEDGE ASSETS")
test("CoT chains", "GET", "/knowledge/cot-chains", check_fn=lambda d: "{} chains".format(len(d)))
test("CoT procurement", "GET", "/knowledge/cot-chains/procurement", check_fn=lambda d: "{} {} steps".format(d["name"], len(d["rules"])))
test("Prompt list", "GET", "/knowledge/prompts", check_fn=lambda d: "{} prompts".format(len(d)))
test("Prompt contract", "GET", "/knowledge/prompts/contract_review", check_fn=lambda d: d["title"])
test("DQ check", "POST", "/knowledge/dq-check",
     payload={"columns":[{"name":"id","type":"int"},{"name":"name","type":"str"}],"pk":"id","row_count":1000},
     check_fn=lambda d: "score={} grade={}".format(d["score"], d["grade"]))
test("Methodology", "GET", "/knowledge/methodology", check_fn=lambda d: "{} frameworks".format(len(d)))
test("Method recommend", "GET", "/knowledge/methodology/recommend/%E6%94%BF%E5%BA%9C%E9%87%87%E8%B4%AD",
     check_fn=lambda d: "{} recommended".format(len(d)))

print("\n" + "=" * 60)
print("  PASS: {} | FAIL: {} | TOTAL: {}".format(p, f, p+f))
print("=" * 60)
