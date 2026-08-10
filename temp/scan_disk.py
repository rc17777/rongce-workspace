import os, sys
sys.stdout.reconfigure(encoding='utf-8')

def get_dir_size(path):
    total = 0
    try:
        for entry in os.scandir(path):
            try:
                if entry.is_file(follow_symlinks=False):
                    total += entry.stat().st_size
                elif entry.is_dir(follow_symlinks=False):
                    total += get_dir_size(entry.path)
            except (PermissionError, OSError):
                pass
    except (PermissionError, OSError):
        pass
    return total

def scan_dirs(base, min_mb=100):
    results = []
    try:
        for entry in os.scandir(base):
            if entry.is_dir():
                size = get_dir_size(entry.path)
                if size > min_mb * 1024 * 1024:
                    results.append((entry.name, size))
    except (PermissionError, OSError):
        pass
    results.sort(key=lambda x: x[1], reverse=True)
    return results

print("=" * 60)
print("C:\\ USERS FOLDERS (>100MB)")
print("=" * 60)
for name, size in scan_dirs("C:/Users/scrccpa", 100):
    print(f"  {name:40s} {size/1e9:8.2f} GB")

print("")
print("=" * 60)
print("C:\\ ROOT FOLDERS (>500MB)")
print("=" * 60)
for name, size in scan_dirs("C:/", 500):
    print(f"  {name:40s} {size/1e9:8.2f} GB")

print("")
print("=" * 60)
print("USER AppData SUBFOLDERS (>100MB)")
print("=" * 60)
for sub in ['Local', 'Roaming', 'LocalLow']:
    path = f"C:/Users/scrccpa/AppData/{sub}"
    if os.path.exists(path):
        for name, size in scan_dirs(path, 100):
            print(f"  AppData/{sub}/{name:30s} {size/1e9:8.2f} GB")
