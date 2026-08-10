import shutil, os, sys
sys.stdout.reconfigure(encoding='utf-8')

cleanup = {
    # (path, description, safe_to_delete)
    "playwright": ("C:/Users/scrccpa/AppData/Local/ms-playwright", "Playwright browsers", True),
    "discord_cache": ("C:/Users/scrccpa/AppData/Local/Discord/Cache", "Discord Cache", True),
    "discord_codecache": ("C:/Users/scrccpa/AppData/Local/Discord/Code Cache", "Discord Code Cache", True),
    "discord_gpucache": ("C:/Users/scrccpa/AppData/Local/Discord/GPUCache", "Discord GPU Cache", True),
    "discord_dawn": ("C:/Users/scrccpa/AppData/Local/Discord/DawnCache", "Discord DawnCache", True),
}

for key, (path, desc, safe) in cleanup.items():
    if os.path.exists(path):
        try:
            size = 0
            for root, dirs, files in os.walk(path):
                for f in files:
                    try:
                        size += os.path.getsize(os.path.join(root, f))
                    except:
                        pass
            shutil.rmtree(path, ignore_errors=True)
            print(f"[OK] {desc}: {size/1024/1024:.0f} MB freed")
        except Exception as e:
            print(f"[FAIL] {desc}: {e}")
    else:
        print(f"[SKIP] {desc}: not found")

# Also check if ms-playwright was already deleted
if not os.path.exists("C:/Users/scrccpa/AppData/Local/ms-playwright"):
    print("[OK] Playwright already gone")

# Qoder already cleaned, check
if not os.path.exists("C:/Users/scrccpa/AppData/Local/qoder-work-cn-updater"):
    print("[OK] Qoder updater already gone")

# Sougou already cleaned
for d in ["kzip_sogou", "kfastpic_sogou"]:
    p = f"C:/Users/scrccpa/AppData/Local/{d}"
    if not os.path.exists(p):
        print(f"[OK] {d} already gone")

# Show C drive status
import subprocess
result = subprocess.run(['powershell', '-Command', 'Get-PSDrive C | Select-Object Used,Free'], 
                       capture_output=True, text=True)
print(f"\n{result.stdout}")
