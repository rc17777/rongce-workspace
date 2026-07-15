"""Simple direct download of pygwalker wheel using urllib with retries."""
import sys, os, urllib.request, urllib.error, time

sys.stdout.reconfigure(encoding='utf-8')
wheel_dir = r'D:\openclaw-workspace\test_tools\wheels'
os.makedirs(wheel_dir, exist_ok=True)

# pygwalker direct wheel URL (from PyPI)
url = 'https://files.pythonhosted.org/packages/py3/p/pygwalker/pygwalker-0.5.0.1-py3-none-any.whl'
# Try mirror
mirrors = [
    'https://pypi.tuna.tsinghua.edu.cn/packages/py3/p/pygwalker/pygwalker-0.5.0.1-py3-none-any.whl',
    'https://mirrors.aliyun.com/pypi/packages/py3/p/pygwalker/pygwalker-0.5.0.1-py3-none-any.whl',
    url,
]

dest = os.path.join(wheel_dir, 'pygwalker-0.5.0.1-py3-none-any.whl')

for mirror in mirrors:
    print(f'Trying: {mirror[:60]}...')
    for attempt in range(3):
        try:
            req = urllib.request.Request(mirror, headers={'User-Agent': 'pip'})
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = resp.read()
                with open(dest, 'wb') as f:
                    f.write(data)
                print(f'OK! {len(data)} bytes downloaded.')
                
                # Now install
                import subprocess
                print('Installing...')
                r = subprocess.run(['pip', 'install', dest, '--no-deps'], 
                                 capture_output=True, text=True, timeout=120)
                print(r.stdout[-500:])
                if r.returncode == 0:
                    print('SUCCESS! Now installing dependencies...')
                    r2 = subprocess.run(['pip', 'install', 'pygwalker'],
                                      capture_output=True, text=True, timeout=300)
                    print(r2.stdout[-1000:])
                    if r2.stderr:
                        # Only show errors, not warnings
                        for line in r2.stderr.split('\n'):
                            if 'ERROR' in line or 'error' in line.lower():
                                print(line)
                    sys.exit(0)
                else:
                    print(r.stderr[-500:])
            break
        except Exception as e:
            print(f'  Attempt {attempt+1} failed: {e}')
            if attempt < 2:
                time.sleep(2)

print('All mirrors failed.')
