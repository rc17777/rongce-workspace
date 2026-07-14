#!/usr/bin/env python3
import requests, time
time.sleep(2)

BASE = "http://127.0.0.1:5002/api"
p = f = 0

def t(label, method, path, payload=None, cf=None):
    global p, f
    try:
        u = BASE + path
        r = requests.get(u, timeout=10) if method == "GET" else requests.post(u, json=payload, timeout=10)
        d = r.json()
        ok = r.status_code == 200
        if isinstance(d, dict) and d.get("error"):
            ok = False
        if ok:
            p += 1
            print(f"  OK  {label:35s} {cf(d) if cf else ''}")
        else:
            f += 1
            detail = d.get("error", r.status_code) if isinstance(d, dict) else f"HTTP {r.status_code}"
            print(f"  FAIL {label:35s} {detail}")
    except Exception as e:
        f += 1
        print(f"  FAIL {label:35s} {str(e)[:60]}")

print("zhiXi v2.0 Final Verification")
print()

t("Status", "GET", "/status", cf=lambda d: "v" + d["version"])
t("DB types", "GET", "/collector/databases", cf=lambda d: "{} DB {} dom".format(len(d["supported"]), len(d["domestic"])))
t("Accounting", "GET", "/collector/accounting/software", cf=lambda d: "{} sw".format(len(d)))
t("Create task", "POST", "/collector/tasks", payload={"name": "t", "source_type": "api", "source_config": {"url": "http://x"}}, cf=lambda d: "ok")
t("Rules", "GET", "/validator/rules", cf=lambda d: "{} rules".format(len(d)))
t("Validate", "POST", "/validator/run", payload={"data": [{"code": "1001", "dr": 100, "cr": 100}], "key_cols": ["code"], "required_cols": ["code"]}, cf=lambda d: "ok")
t("Outliers", "POST", "/cleaner/outliers", payload={"data": [{"amount": 100}, {"amount": 200}, {"amount": 99999}], "col": "amount", "method": "iqr"}, cf=lambda d: "{} out".format(d["total_outliers"]))
t("Domains", "GET", "/standardizer/domains", cf=lambda d: "{} dom".format(len(d["domains"])))
t("Schema", "GET", "/standardizer/schema/financial", cf=lambda d: "{} fld".format(len(d)))
t("Contract", "POST", "/unstructured/extract", payload={"text": "甲方:融策 乙方:XX 金额:50万 日期:2026-06-01"}, cf=lambda d: d.get("doc_type", "?"))
t("Bidding", "POST", "/unstructured/extract", payload={"text": "项目:XX采购 方式:公开招标 预算:200万 中标:XX公司"}, cf=lambda d: d.get("doc_type", "?"))
t("Meeting", "POST", "/unstructured/extract", payload={"text": "会议纪要 时间:2026-05-30 参会:张三 主持:张局"}, cf=lambda d: d.get("doc_type", "?"))
t("Categories", "GET", "/models/categories", cf=lambda d: "{} cat".format(len(d)))
t("All models", "GET", "/models", cf=lambda d: "{} models".format(len(d)))
t("M001", "GET", "/models/M001", cf=lambda d: d["name"])
t("M015", "GET", "/models/M015", cf=lambda d: d["name"])
t("M030", "GET", "/models/M030", cf=lambda d: d["name"])
t("Search", "GET", "/models/search?q=%E6%8B%9B%E6%A0%87", cf=lambda d: "{} hit".format(len(d)))
t("Methods", "GET", "/models/analysis-methods", cf=lambda d: "{} methods".format(len(d)))
t("Fund flow", "POST", "/bigdata/graph/fund-flow", payload={"transactions": [{"from": "F", "to": "D", "amount": 1000000}]}, cf=lambda d: "{}n {}e".format(d["nodes"], d["edges"]))
t("Supplier", "POST", "/bigdata/graph/supplier", payload={"bid_data": [{"project": "P1", "bidder": "A", "ip": "1.1.1.1"}, {"project": "P1", "bidder": "B", "ip": "1.1.1.1"}]}, cf=lambda d: "{}n {}e".format(d["nodes"], d["edges"]))
t("WordFreq", "POST", "/bigdata/text/wordcloud", payload={"texts": ["专项资金挪用", "资金闲置", "审计发现"]}, cf=lambda d: "{} words".format(len(d)))
t("Chart", "POST", "/bigdata/visualize", payload={"type": "bar", "data": {"A": 85, "B": 62}, "title": "t"}, cf=lambda d: "ok")
t("CoT", "GET", "/knowledge/cot-chains", cf=lambda d: "{} chains".format(len(d)))
t("CoT detail", "GET", "/knowledge/cot-chains/procurement", cf=lambda d: d["name"])
t("Prompts", "GET", "/knowledge/prompts", cf=lambda d: "{} prompts".format(len(d)))
t("Prompt", "GET", "/knowledge/prompts/contract_review", cf=lambda d: d["name"])
t("DQ", "POST", "/knowledge/dq-check", payload={"columns": [{"name": "id", "type": "int"}], "pk": "id"}, cf=lambda d: "{} {}".format(d["score"], d["grade"]))
t("Method", "GET", "/knowledge/methodology", cf=lambda d: "{} frameworks".format(len(d)))
t("Recommend", "GET", "/knowledge/methodology/recommend/%E6%94%BF%E5%BA%9C%E9%87%87%E8%B4%AD", cf=lambda d: "{} rec".format(len(d)))

print()
print("=" * 50)
print("  PASS: {}  |  FAIL: {}  |  TOTAL: {}".format(p, f, p + f))
print("=" * 50)
