import requests
import json

BASE = "http://127.0.0.1:5002"

print("=" * 60)
print("智析v2.1 新技能API测试")
print("=" * 60)

# 1. 穿透式审计 - 资金穿透
print("\n=== 1. 资金穿透 ===")
try:
    r = requests.post(f"{BASE}/api/penetrating/fund", json={
        "transactions": [
            {"date": "2024-01-01", "from_account": "财政专户", "to_account": "项目A", "amount": 1000000, "purpose": "工程款"},
            {"date": "2024-01-02", "from_account": "项目A", "to_account": "供应商甲", "amount": 500000, "purpose": "材料款"},
            {"date": "2024-01-03", "from_account": "供应商甲", "to_account": "财政专户", "amount": 500000, "purpose": "退款"},
        ]
    }, timeout=5)
    print(f"Status: {r.status_code}")
    data = r.json()
    print(f"Anomalies: {data.get('anomaly_count', 0)}")
    if data.get('anomalies'):
        print(f"First: {data['anomalies'][0]['type']}")
except Exception as e:
    print(f"Error: {e}")

# 2. 专项债券 - 检查清单
print("\n=== 2. 专项债券检查清单 ===")
try:
    r = requests.get(f"{BASE}/api/special-bond/checklist", timeout=5)
    print(f"Status: {r.status_code}")
    data = r.json()
    print(f"Stages: {len(data)}")
except Exception as e:
    print(f"Error: {e}")

# 3. BIM - IFC解析
print("\n=== 3. BIM IFC解析 ===")
try:
    r = requests.post(f"{BASE}/api/bim/parse-ifc", json={
        "ifc_data": {
            "elements": [
                {"type": "IfcWall", "name": "外墙1", "properties": {"Volume": 50.5, "Area": 120.0}},
                {"type": "IfcSlab", "name": "楼板1", "properties": {"Volume": 80.0, "Area": 200.0}},
            ]
        }
    }, timeout=5)
    print(f"Status: {r.status_code}")
    data = r.json()
    print(f"Element types: {data.get('element_types', 0)}")
except Exception as e:
    print(f"Error: {e}")

# 4. 风险画像 - 维度定义
print("\n=== 4. 风险画像维度 ===")
try:
    r = requests.get(f"{BASE}/api/risk-portrait/dimensions", timeout=5)
    print(f"Status: {r.status_code}")
    data = r.json()
    print(f"Dimensions: {len(data)}")
except Exception as e:
    print(f"Error: {e}")

# 5. 动态预警 - 规则列表
print("\n=== 5. 动态预警规则 ===")
try:
    r = requests.get(f"{BASE}/api/alert/rules", timeout=5)
    print(f"Status: {r.status_code}")
    data = r.json()
    print(f"Rule categories: {len(data)}")
except Exception as e:
    print(f"Error: {e}")

print("\n" + "=" * 60)
print("测试完成")
print("=" * 60)
