import subprocess, sys
out = subprocess.check_output('wmic process where name="python.exe" get ProcessId,CommandLine /format:csv', shell=True)
lines = out.decode('gbk', errors='replace').strip().split('\n')
for l in lines:
    if 'ocr' in l.lower() or 'ruoergai' in l.lower() or 'full_ocr' in l.lower():
        print(l)
        parts = l.strip().split(',')
        pid = parts[-1].strip() if len(parts) >= 2 else ''
        if pid.isdigit():
            r = subprocess.run(['taskkill', '/F', '/PID', pid], capture_output=True, text=True)
            print(f'  Killed PID {pid}: {r.stdout.strip()}')
print('Cleanup done')
