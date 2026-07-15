"""晚间改动后的环境检查"""
import json, os, sys, subprocess as sp
sys.stdout.reconfigure(encoding="utf-8")

print("=" * 55)
print("1️⃣  session.reset 配置（旧核心4.5是否识别）")
print("=" * 55)
p = os.path.expanduser(r"~\.openclaw\openclaw.json")
j = json.load(open(p, encoding="utf-8"))
sr = j.get("session", {}).get("reset", {})
print(f"   值: {sr}")
print(f"   ⏰ 凌晨4点自动重置：{'已设置' if sr else '未设置'}")

print("\n" + "=" * 55)
print("2️⃣  降级链完整性")
print("=" * 55)
fb = j.get("agents", {}).get("defaults", {}).get("model", {}).get("fallbacks", [])
for i, m in enumerate(fb, 1):
    print(f"   {i}. {m.split('/')[-1] if '/' in m else m}")
print(f"   共{len(fb)}个")
print(f"   gemini在链中：{'是' if any('gemini' in m for m in fb) else '❌ 不在!'}")

print("\n" + "=" * 55)
print("3️⃣  文件完整性")
print("=" * 55)
gc = os.path.expanduser(r"~\.openclaw\gateway.cmd")
print(f"   gateway.cmd: {'✅' if os.path.exists(gc) else '❌ 缺失!'}")
if os.path.exists(gc):
    with open(gc, encoding="utf-8") as f:
        print(f"     → {f.read().strip()}")

tsize = os.path.getsize(os.path.expanduser(r"~\.openclaw\workspace\TOOLS.md"))
print(f"   TOOLS.md:   {tsize} / ~20000 chars ({tsize/20000:.0%})")
print(f"   {'⚠️ 接近上限,考虑精简' if tsize > 18000 else '✅ 正常'}")

print(f"\n   MEMORY.md:  {'✅' if os.path.exists(os.path.expanduser(r'~\.openclaw\workspace\MEMORY.md')) else '❌'}")

print("\n" + "=" * 55)
print("4️⃣  计划任务")
print("=" * 55)
r = sp.run(["schtasks", "/query", "/tn", "\\OpenClaw Gateway", "/fo", "LIST"],
           capture_output=True, text=True, timeout=15)
if "找不到" in r.stderr or "ERROR" in r.stderr:
    print("   ❌ 计划任务 \OpenClaw Gateway 未找到")
else:
    for line in r.stdout.splitlines():
        if "运行状态" in line or "下次运行" in line:
            print(f"   {line.strip()}")

r2 = sp.run(["schtasks", "/query", "/tn", "\\OpenClawModelHealthcheck", "/fo", "LIST"],
           capture_output=True, text=True, timeout=15)
if "找不到" not in r2.stderr:
    for line in r2.stdout.splitlines():
        if "下次运行" in line:
            print(f"   模型健康检查: {line.strip()}")

print("\n" + "=" * 55)
print("5️⃣  npm/openclaw 残留")
print("=" * 55)
paths_to_check = [
    r"C:\Users\scrccpa\AppData\Roaming\npm\node_modules\openclaw",
    r"C:\Users\scrccpa\AppData\Roaming\npm\openclaw.cmd",
    r"C:\Users\scrccpa\AppData\Local\Programs\OneClaw\node_modules\openclaw",
]
for p in paths_to_check:
    exists = os.path.exists(p)
    print(f"   {'⚠️ 残留!' if exists else '✅ 已清除'}: {p}")

# 检查 npm prefix 并还原（这是个隐患）
r3 = sp.run(["npm", "config", "get", "prefix"], capture_output=True, text=True, timeout=15)
prefix = r3.stdout.strip()
print(f"\n   npm prefix: {prefix}")
default = r"C:\Users\scrccpa\AppData\Roaming\npm"
if prefix.lower() != default.lower():
    print(f"   ⚠️ prefix非默认值! 建议: npm config set prefix {default}")


print("\n" + "=" * 55)
print("6️⃣  gateway 当前状态")
print("=" * 55)
proc = sp.run(["netstat", "-ano"], capture_output=True, text=True, timeout=15)
for ln in proc.stdout.splitlines():
    if "18789" in ln and "LISTENING" in ln:
        pid = ln.strip().split()[-1]
        # 查进程名
        sp2 = sp.run(["tasklist", "/fi", f"PID eq {pid}", "/fo", "csv"],
                     capture_output=True, text=True, timeout=10)
        if "OneClaw" in sp2.stdout:
            print(f"   ✅ 端口18789: 进程PID={pid} (OneClaw Helper)")
        else:
            print(f"   端口18789: PID={pid}")
        break
