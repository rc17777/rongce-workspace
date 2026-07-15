"""Download pygwalker and deps wheels to local dir, then pip install offline."""
import sys
sys.stdout.reconfigure(encoding='utf-8')

import subprocess
import os
import requests
from pathlib import Path

wheel_dir = Path(r'D:\openclaw-workspace\test_tools\wheels')
wheel_dir.mkdir(parents=True, exist_ok=True)

# Get download URLs for pygwalker and all deps
print("Step 1: Getting download URLs...")
result = subprocess.run(
    ['pip', 'install', '--dry-run', '--report', str(wheel_dir / 'report.json'),
     'pygwalker', '--proxy=""'],
    capture_output=True, text=True, timeout=120
)
print(result.stdout[-500:] if result.stdout else 'no stdout')
print(result.stderr[-500:] if result.stderr else 'no stderr')

# Parse the report
import json
report_path = wheel_dir / 'report.json'
if report_path.exists():
    with open(report_path) as f:
        report = json.load(f)
    
    urls = []
    for item in report.get('install', []):
        url = item.get('download_info', {}).get('url', '')
        if url:
            urls.append(url)
    
    print(f"\nStep 2: Downloading {len(urls)} packages...")
    session = requests.Session()
    session.headers.update({'User-Agent': 'pip'})
    
    for i, url in enumerate(urls):
        fname = url.split('/')[-1].split('#')[0]
        dest = wheel_dir / fname
        if dest.exists():
            print(f"  [{i+1}/{len(urls)}] SKIP (exists): {fname}")
            continue
        
        print(f"  [{i+1}/{len(urls)}] Downloading: {fname} ...", end=' ', flush=True)
        for attempt in range(5):
            try:
                r = session.get(url, timeout=60)
                r.raise_for_status()
                dest.write_bytes(r.content)
                print(f"OK ({len(r.content)} bytes)")
                break
            except Exception as e:
                if attempt < 4:
                    print(f"retry {attempt+1}...", end=' ', flush=True)
                else:
                    print(f"FAILED: {e}")
        
    print(f"\nStep 3: Installing from {wheel_dir}...")
    wheels = list(wheel_dir.glob('*.whl'))
    if wheels:
        result = subprocess.run(
            ['pip', 'install', '--no-index', '--find-links', str(wheel_dir), 'pygwalker'],
            capture_output=True, text=True, timeout=120
        )
        print(result.stdout[-1000:])
        if result.stderr:
            print(result.stderr[-1000:])
else:
    print("ERROR: report.json not generated")
    # Fallback: try direct pip install with extended timeout
    print("\nFallback: trying direct install...")
    result = subprocess.run(
        ['pip', 'install', 'pygwalker'],
        capture_output=True, text=True, timeout=300
    )
    print(result.stdout[-1000:])
    print(result.stderr[-1000:])
