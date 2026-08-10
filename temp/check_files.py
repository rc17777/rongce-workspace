import os
base = r'C:\Users\scrccpa\.openclaw\workspace\audit-blackboard'
for f in ['algorithm_registry.json','algorithm_loader.py','ALGORITHM_INTEGRATION.md']:
    fp = os.path.join(base, f)
    size = os.path.getsize(fp) if os.path.exists(fp) else 0
    print(f'{f}: {size} bytes' if size else f'{f}: MISSING')
