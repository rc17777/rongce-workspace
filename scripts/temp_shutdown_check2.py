import subprocess, sys
sys.stdout.reconfigure(encoding='utf-8')

# 端口占用检查（处理 GBK）
print("3. 关键端口占用检查")
print("=" * 50)
ports_to_check = [5000, 5001, 5002, 18789]
result = subprocess.run(['netstat', '-ano'], capture_output=True, encoding='gbk', errors='replace')
for port in ports_to_check:
    lines = [l for l in result.stdout.split('\n') if f':{port} ' in l and 'LISTENING' in l]
    if lines:
        print(f"  端口 {port}: 占用中")
        for l in lines[:2]:
            print(f"    {l.strip()}")
    else:
        print(f"  端口 {port}: 空闲")

# Git 状态
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
