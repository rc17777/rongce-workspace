import os, sys
sys.stdout.reconfigure(encoding='utf-8')

def dir_size(path, max_depth=2):
    total = 0
    try:
        for entry in os.scandir(path):
            try:
                if entry.is_file(follow_symlinks=False):
                    total += entry.stat().st_size
                elif entry.is_dir(follow_symlinks=False) and max_depth > 0:
                    total += dir_size(entry.path, max_depth - 1)
            except (PermissionError, OSError):
                pass
    except (PermissionError, OSError):
        pass
    return total

# Quick scan - only 2 levels deep
targets = [
    ("C:/Users/scrccpa/AppData/Local", "AppData/Local subfolders"),
    ("C:/Users/scrccpa/AppData/Roaming", "AppData/Roaming subfolders"),
    ("C:/ProgramData", "ProgramData subfolders"),
    ("C:/Users/scrccpa/.openclaw", ".openclaw workspace"),
]

for base, label in targets:
    if not os.path.exists(base):
        continue
    print(f"\n=== {label} ===")
    results = []
    try:
        for entry in os.scandir(base):
            if entry.is_dir():
                size = dir_size(entry.path, max_depth=2)
                results.append((entry.name, size))
    except:
        pass
    results.sort(key=lambda x: x[1], reverse=True)
    for name, size in results[:15]:
        if size > 50 * 1024 * 1024:
            print(f"  {name:40s} {size/1e9:7.2f} GB")
        elif size > 1 * 1024 * 1024:
            print(f"  {name:40s} {size/1e6:7.0f} MB")

# Also scan the workspace dir on D drive just in case
ws = "D:/openclaw-workspace"
if os.path.exists(ws):
    print(f"\n=== D:/openclaw-workspace ===")
    results = []
    for entry in os.scandir(ws):
        if entry.is_dir():
            size = dir_size(entry.path, max_depth=2)
            results.append((entry.name, size))
    results.sort(key=lambda x: x[1], reverse=True)
    for name, size in results[:15]:
        if size > 10 * 1024 * 1024:
            print(f"  {name:40s} {size/1e9:7.2f} GB")

# Also the workspace on C drive
ws2 = "C:/Users/scrccpa/.openclaw/workspace"
if os.path.exists(ws2):
    print(f"\n=== {ws2} ===")
    size = dir_size(ws2, max_depth=3)
    print(f"  Total: {size/1e9:.2f} GB")
    results = []
    try:
        for entry in os.scandir(ws2):
            if entry.is_dir():
                s = dir_size(entry.path, max_depth=2)
                results.append((entry.name, s))
    except:
        pass
    results.sort(key=lambda x: x[1], reverse=True)
    for name, s in results[:20]:
        if s > 10 * 1024 * 1024:
            print(f"  {name:40s} {s/1e9:7.2f} GB")

# Check node_modules folders
print(f"\n=== Checking for node_modules ===")
import subprocess
result = subprocess.run(['cmd', '/c', 'dir /s /b /a:d node_modules 2>nul'], 
                       cwd='C:/', capture_output=True, text=True, timeout=30)
lines = result.stdout.strip().split('\n')
for l in lines[:10]:
    if l.strip():
        print(f"  Found: {l.strip()}")
