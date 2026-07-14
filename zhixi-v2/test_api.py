#!/usr/bin/env python3
"""智析 v2.0 全模块API端到端验证"""
import requests, json, time

BASE = "http://127.0.0.1:5001/api"
passed = 0
failed = 0
results = []

def test(name, method, url, payload=None, checks=None):
    global passed, failed
    try:
        if method == "GET":
            r = requests.get(url, timeout=10)
        else:
            r = requests.post(url, json=payload, timeout=10)
        status = "✅" if r.status_code == 200 else "❌"
        if r.status_code == 200:
            passed += 1
        else:
            failed += 1
        detail = ""
        if checks and r.status_code == 200:
            try:
                detail = checks(r.json())
            except Exception as e:
                detail = f"check error: {e}"
        results.append(f"{status} [{method}] {name}")
        if detail:
            results[-1] += f" → {detail}"
    except Exception as e:
        failed += 1
        results.append(f"❌ [{method}] {name} → ERROR: {e}")

print("=" * 60)
print("  智析智能体 v2.0 全模块API验证")
print("=" * 60)
print()

# ==================== 系统状态 ====================
print("01. 系统状态")
test("系统状态", "GET", f"{BASE}/status", checks=lambda d: f"v{d['version']}, {len(d['modules'])} modules active")

# ==================== 数据采集 ====================
print("02. 数据采集")
test("数据库类型列表", "GET", f"{BASE}/collector/databases", 
     checks=lambda d: f"{len(d['supported'])} types, {len(d['domestic'])} domestic")
test("财务软件列表", "GET", f"{BASE}/collector/accounting/software",
     checks=lambda d: f"{len(d)} software")
test("创建采集任务", "POST", f"{BASE}/collector/tasks",
     payload={"name":"test","source_type":"api","source_config":{"url":"http://example.com"}},
     checks=lambda d: f"task_id={d.get('task_id','?')}")

# ==================== 数据校验 ====================
print("03. 数据校验清洗")
test("校验规则列表", "GET", f"{BASE}/validator/rules",
     checks=lambda d: f"{len(d)} rules")
test("执行数据校验", "POST", f"{BASE}/validator/run",
     payload={"data":[{"account_code":"1001","debit_amount":100,"credit_amount":100}],
              "key_cols":["account_code"],"required_cols":["account_code","debit_amount"]},
     checks=lambda d: f"passed={d['summary']['passed']}/{d['summary']['total']}")
test("异常值检测", "POST", f"{BASE}/cleaner/outliers",
     payload={"data":[{"amount":100},{"amount":200},{"amount":99999}],"col":"amount","method":"iqr"},
     checks=lambda d: f"{d['total_outliers']} outliers found")

# ==================== 标准化 ====================
print("04. 数据标准化")
test("标准域列表", "GET", f"{BASE}/standardizer/domains",
     checks=lambda d: f"{len(d['domains'])} domains")
test("财务标准schema", "GET", f"{BASE}/standardizer/schema/financial",
     checks=lambda d: f"{len(d)} fields")
test("标准库目录", "GET", f"{BASE}/standardizer/library",
     checks=lambda d: f"{len(d)} tables")

# ==================== 非结构化 ====================
print("05. 非结构化处理")
test("合同提取", "POST", f"{BASE}/unstructured/extract",
     payload={"text":"甲方：融策会计师事务所  乙方：XX科技有限公司\r\n合同金额：人民币伍拾万元整\r\n签订日期：2026年6月1日\r\n违约责任：逾期每日按合同总额千分之一支付违约金"},
     checks=lambda d: f"type={d['doc_type']}, parties={len(d.get('parties',[]))}")
test("招投标提取", "POST", f"{BASE}/unstructured/extract",
     payload={"text":"项目名称：XX县审计局数据分析服务采购项目\r\n采购方式：公开招标\r\n预算金额：200万元\r\n中标人：XX公司\r\n评标方法：综合评分法"},
     checks=lambda d: f"type={d['doc_type']}")
test("会议纪要提取", "POST", f"{BASE}/unstructured/extract",
     payload={"text":"XX县审计局会议纪要\r\n会议时间：2026年5月30日\r\n参会人员：张三、李四、王五\r\n主持人：张局长\r\n议题一：讨论年度审计计划"},
     checks=lambda d: f"type={d['doc_type']}")

# ==================== 审计模型 ====================
print("06. 审计模型工作台")
test("模型分类", "GET", f"{BASE}/models/categories",
     checks=lambda d: f"{len(d)} categories")
test("模型列表", "GET", f"{BASE}/models",
     checks=lambda d: f"{len(d)} models")
test("获取M001", "GET", f"{BASE}/models/M001",
     checks=lambda d: f"{d['name']}")
test("搜索模型", "GET", f"{BASE}/models/search?q=围标",
     checks=lambda d: f"{len(d)} hits")
test("分析方法", "GET", f"{BASE}/models/analysis-methods",
     checks=lambda d: f"{len(d)} methods")

# ==================== 大数据 ====================
print("07. 大数据分析")
test("资金流向图谱", "POST", f"{BASE}/bigdata/graph/fund-flow",
     payload={"transactions":[{"from":"财政局","to":"XX局","amount":1000000},
                               {"from":"XX局","to":"供应商A","amount":500000},
                               {"from":"XX局","to":"供应商B","amount":500000}]},
     checks=lambda d: f"{d['nodes']} nodes, {d['edges']} edges")
test("供应商关联网络", "POST", f"{BASE}/bigdata/graph/supplier",
     payload={"bid_data":[{"project":"项目1","bidder":"A公司","ip":"10.0.0.1"},
                          {"project":"项目1","bidder":"B公司","ip":"10.0.0.1"},
                          {"project":"项目2","bidder":"A公司","ip":"10.0.0.2"},
                          {"project":"项目2","bidder":"B公司","ip":"10.0.0.2"}]},
     checks=lambda d: f"{d['nodes']} nodes, {d['edges']} edges")
test("文本词频", "POST", f"{BASE}/bigdata/text/wordcloud",
     payload={"texts":["专项资金使用管理不规范","专项资金拨付进度缓慢","审计发现资金挪用问题"]},
     checks=lambda d: f"{len(d)} words")
test("可视化-柱状图", "POST", f"{BASE}/bigdata/visualize",
     payload={"type":"bar","data":{"预算执行":85,"专项资金":62,"政府采购":73},"title":"审计项目分布"},
     checks=lambda d: "series" in str(d))

# ==================== 知识资产 ====================
print("08. 知识资产")
test("思维链列表", "GET", f"{BASE}/knowledge/cot-chains",
     checks=lambda d: f"{len(d)} chains")
test("思维链-采购审计", "GET", f"{BASE}/knowledge/cot-chains/procurement",
     checks=lambda d: f"{d['name']}, {len(d['rules'])} steps")
test("提示词列表", "GET", f"{BASE}/knowledge/prompts",
     checks=lambda d: f"{len(d)} prompts")
test("提示词-合同审查", "GET", f"{BASE}/knowledge/prompts/contract_review",
     checks=lambda d: f"{d['title']}")
test("数据标准检查", "POST", f"{BASE}/knowledge/dq-check",
     payload={"columns":[{"name":"id","type":"int"},{"name":"name","type":"str"}],
              "pk":"id","row_count":1000},
     checks=lambda d: f"score={d['score']}, grade={d['grade']}")
test("方法论列表", "GET", f"{BASE}/knowledge/methodology",
     checks=lambda d: f"{len(d)} frameworks")
test("方法论推荐", "GET", f"{BASE}/knowledge/methodology/recommend/政府采购",
     checks=lambda d: f"{len(d)} recommended")

# ==================== 汇总 ====================
print()
print("=" * 60)
print(f"  验证完成: ✅ {passed} passed | ❌ {failed} failed | 总计 {passed+failed}")
print("=" * 60)
