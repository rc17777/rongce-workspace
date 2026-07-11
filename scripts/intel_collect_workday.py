#!/usr/bin/env python3
"""
审计情报工作日采集入口
被 cron 调用，尝试采集各政府网站审计政策文件
"""
import sys, os, json, datetime
sys.stdout.reconfigure(encoding='utf-8')

COLLECTOR = os.path.join(os.path.dirname(__file__), 'audit_intel_collector.py')

def main():
    print(f"=" * 50)
    print(f"  审计情报采集 - 工作日轮次")
    print(f"  时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"=" * 50)
    
    # Run collector
    import subprocess
    result = subprocess.run(
        [sys.executable, COLLECTOR],
        capture_output=True, text=True, timeout=180
    )
    
    status = "success" if result.returncode == 0 else "failed"
    lines = len(result.stdout.strip().split('\n'))
    
    summary = {
        "time": datetime.datetime.now().isoformat(),
        "status": status,
        "output_lines": lines,
        "has_stderr": bool(result.stderr.strip())
    }
    
    # Save status
    log_dir = os.path.join(os.path.dirname(__file__), '..', 'logs', 'audit_intel')
    os.makedirs(log_dir, exist_ok=True)
    status_file = os.path.join(log_dir, f"run_{datetime.datetime.now().strftime('%Y%m%d')}.json")
    with open(status_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    
    print(f"\n状态: {status}")
    print(f"输出: {lines} 行")
    if result.stderr.strip():
        print(f"错误: {result.stderr.strip()[:200]}")
    
    return 0 if status == "success" else 1

if __name__ == "__main__":
    sys.exit(main())
