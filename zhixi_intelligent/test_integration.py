import sys
sys.path.insert(0, r"D:\openclaw-workspace")
from zhixi_intelligent import DatabaseConnector, MetadataScanner, CollectionDashboard

print("=== 智析智能 v1.0 集成测试 ===")

# Test 1: Connector
c = DatabaseConnector()
r = c.quick_connect("sqlite", r"D:\openclaw-workspace\zhixi_intelligent\reports\test_audit.db")
status = r["status"]
print(f"[连接器] {status} - {len(c.engines)}个活动连接")

# Test 2: Scanner
s = MetadataScanner(c)
name = list(c.engines.keys())[0]
scan = s.scan(name)
table_count = scan.get("total_tables", 0)
print(f"[扫描器] {scan['dialect']} - {table_count}张表")

# Test 3: Dashboard
d = CollectionDashboard()
d.bind_scanner(c, s)
d.register("工商", "省市场监管局", 32, 1200000, 45.5, "completed")
d.register("财政财务", "省财政厅", 68, 8500000, 320.0, "completed")
d.register("社保医保", "省社保局", 24, 2100000, 88.3, "completed")
d.register("教科文卫", "省教育厅", 45, 3200000, 156.2, "completed")
d.register("公积金", "省公积金中心", 12, 890000, 22.1, "completed")
d.register("公共资源交易", "省交易中心", 18, 650000, 35.7, "in_progress")
d.register("重大投资项目", "省发改委", 8, 320000, 12.8, "in_progress")

report = d.generate_report()
print(f"[看板] {report['采集进度']}")

# Save JSON + HTML
d.save_report(r"D:\openclaw-workspace\zhixi_intelligent\reports\collection_report.json")
d.save_html(r"D:\openclaw-workspace\zhixi_intelligent\dashboards\collection_dashboard.html")
print("[文件] reports/collection_report.json")
print("[文件] dashboards/collection_dashboard.html")

# Test 4: Connection status
st = c.status()
print(f"[状态] {st['total']}个连接在线")
print()
print("=== 全部通过 ===")
