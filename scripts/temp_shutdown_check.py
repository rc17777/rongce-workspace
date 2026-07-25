import urllib.request, json, sys
sys.stdout.reconfigure(encoding='utf-8')

# 1. DeepSeek 余额
print("=" * 50)
print("1. DeepSeek 余额检查")
print("=" * 50)
try:
    key = 'sk-dbc61b4ba6a64222a2621d646f15234c'
    req = urllib.request.Request('https://api.deepseek.com/user/balance', headers={'Authorization': f'Bearer {key}'})
    resp = urllib.request.urlopen(req, timeout=10)
    r = json.loads(resp.read())
    for b in r.get('balance_infos', []):
        print(f"  {b['currency']}: {b['total_balance']}")
except Exception as e:
    print(f"  ❌ 查询失败: {e}")

# 2. C盘空间
print("\n" + "=" * 50)
print("2. C盘空间检查")
print("=" * 50)
import shutil
total, used, free = shutil.disk_usage('C:\\')
print(f"  总计: {total // (1024**3)} GB")
print(f"  已用: {used // (1024**3)} GB")
print(f"  可用: {free // (1024**3)} GB")
if free < 10 * 1024**3:
    print("  ⚠️ 空间不足10GB，建议清理")
else:
    print("  ✅ 空间充足")

# 3. 端口占用检查
print("\n" + "=" * 50)
print("3. 关键端口占用检查")
print("=" * 50)
import subprocess
ports_to_check = [5000, 5001, 5002, 18789]
for port in ports_to_check:
    result = subprocess.run(['netstat', '-ano'], capture_output=True, text=True)
    lines = [l for l in result.stdout.split('\n') if f':{port}' in l and 'LISTENING' in l]
    if lines:
        print(f"  端口 {port}: 占用中")
        for l in lines[:2]:
            print(f"    {l.strip()}")
    else:
        print(f"  端口 {port}: 空闲")

# 4. 工作区 git 状态
print("\n" + "=" * 50)
print("4. 工作区 Git 状态")
print("=" * 50)
result = subprocess.run(['git', 'status', '--short'], capture_output=True, text=True, cwd=r'C:\Users\scrccpa\.openclaw\workspace')
if result.stdout.strip():
    print("  有未提交的变更:")
    for line in result.stdout.strip().split('\n')[:10]:
        print(f"    {line}")
    if len(result.stdout.strip().split('\n')) > 10:
        print(f"    ... 共 {len(result.stdout.strip().split('\n'))} 个文件")
else:
    print("  ✅ 工作区干净")
