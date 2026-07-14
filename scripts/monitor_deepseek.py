# monitor_deepseek.py — 实时监控本机对 api.deepseek.com 的连接
import subprocess
import time
import json
from datetime import datetime
from collections import defaultdict

LOG_FILE = r"D:\openclaw-workspace\temp\deepseek_monitor.jsonl"

def get_connections():
    """获取所有443连接的PID和远程IP"""
    try:
        result = subprocess.run(
            ['netstat', '-ano'],
            capture_output=True, text=True, encoding='utf-8', errors='ignore'
        )
        lines = result.stdout.split('\n')
        connections = []
        for line in lines:
            if ':443' in line and ('ESTABLISHED' in line or 'CLOSE_WAIT' in line):
                parts = line.split()
                if len(parts) >= 5:
                    local = parts[1]
                    remote = parts[2]
                    state = parts[3]
                    pid = parts[4]
                    if '192.168.' not in remote and '127.0.0.1' not in remote:
                        connections.append({
                            'remote': remote,
                            'pid': pid,
                            'state': state,
                            'time': datetime.now().isoformat()
                        })
        return connections
    except Exception as e:
        print(f"Error: {e}")
        return []

def get_process_info(pid):
    """获取进程信息"""
    try:
        result = subprocess.run(
            ['tasklist', '/FI', f'PID eq {pid}', '/FO', 'CSV', '/NH'],
            capture_output=True, text=True, encoding='utf-8', errors='ignore'
        )
        line = result.stdout.strip()
        if line and ',' in line:
            parts = line.split(',')
            name = parts[0].strip('"')
            return name
    except:
        pass
    return "unknown"

def main():
    print("[*] DeepSeek API 连接监控启动...")
    print(f"[*] 日志保存到: {LOG_FILE}")
    print("[*] 按 Ctrl+C 停止\n")
    
    stats = defaultdict(int)
    
    try:
        while True:
            conns = get_connections()
            for c in conns:
                pname = get_process_info(c['pid'])
                c['process'] = pname
                
                # 只记录可疑IP（排除常见CDN/云服务）
                remote_ip = c['remote'].split(':')[0]
                
                # 写入日志
                with open(LOG_FILE, 'a', encoding='utf-8') as f:
                    f.write(json.dumps(c, ensure_ascii=False) + '\n')
                
                key = f"{pname}(PID:{c['pid']}) -> {remote_ip}"
                stats[key] += 1
            
            # 每10秒打印一次统计
            time.sleep(10)
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 过去10秒连接统计:")
            for k, v in sorted(stats.items(), key=lambda x: -x[1])[:10]:
                print(f"  {v:3d}次 | {k}")
            stats.clear()
            
    except KeyboardInterrupt:
        print("\n[*] 监控已停止")

if __name__ == '__main__':
    main()
