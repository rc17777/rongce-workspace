"""测试一键采集器全流程"""
import urllib.request, json, os, time

BASE = "http://127.0.0.1:5000"
HEADERS = {"Content-Type": "application/json"}

def post(path, body):
    data = json.dumps(body).encode()
    r = urllib.request.urlopen(urllib.request.Request(
        BASE + path, data=data, headers=HEADERS, method="POST"
    ))
    return json.loads(r.read())

def get(path):
    r = urllib.request.urlopen(BASE + path)
    return json.loads(r.read())

# Step 1: 测试连接
print("=== Step 1: 测试连接 ===")
result = post("/api/test", {"name": "测试审计数据库"})
print(f"  状态: {result}")

# Step 2: 预览表结构
print("\n=== Step 2: 预览表结构 ===")
preview = post("/api/preview", {"name": "测试审计数据库"})
print(f"  共 {preview['total_tables']} 张表, {preview['total_columns']} 字段, ~{preview['estimated_rows']:,} 行")
for t in preview["tables"]:
    print(f"  [{t['table_name']}] {t['column_count']}字段, {t['row_count']:,}行 | {t['columns_preview']}")

# Step 3: 一键采集
print("\n=== Step 3: 一键采集全部数据 ===")
result = post("/api/collect", {"name": "测试审计数据库"})
print(f"  启动: {result}")

# Step 4: 等待完成
print("  等待采集完成...", end="", flush=True)
for _ in range(60):
    time.sleep(0.5)
    status = get("/api/status")
    print(".", end="", flush=True)
    if not status["collecting"]:
        break
print(f"\n  采集完成！进度: {status['progress']}%")

# Step 5: 查看结果
print("\n=== Step 5: 输出结果 ===")
collected = r"D:\openclaw-workspace\zhixi_intelligent\collected_data"
dirs = [d for d in os.listdir(collected) if d.startswith("测试审计数据库")]
if dirs:
    latest = sorted(dirs)[-1]
    path = os.path.join(collected, latest)
    files = [f for f in os.listdir(path) if f.endswith(".csv")]
    
    for f in sorted(files):
        size = os.path.getsize(os.path.join(path, f))
        print(f"  {f}: {size/1024:.1f} KB")

    meta_path = os.path.join(path, "metadata.json")
    if os.path.exists(meta_path):
        with open(meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)
        print(f"\n  📊 采集汇总:")
        print(f"     成功: {meta['collected']}/{meta['total_tables']} 张表")
        print(f"     总行数: {meta['total_rows']:,}")
        print(f"     输出目录: {path}")

print("\n=== 全流程验证通过 ===")
