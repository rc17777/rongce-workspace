#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DeepSeek API 实时调用监控器
监控 10 分钟内连接到 api.deepseek.com 的进程和频率
"""
import sys, os, time, subprocess, json
from collections import defaultdict
sys.stdout.reconfigure(encoding='utf-8')

INTERVAL = 5        # 每5秒采样一次
DURATION = 600      # 监控10分钟
TARGET = "api.deepseek.com"

def resolve_ips(host):
    """解析域名到IP列表"""
    try:
        import socket
        ips = socket.getaddrinfo(host, 443, socket.AF_INET, socket.SOCK_STREAM)
        return list(set(ip[4][0] for ip in ips))
    except:
        return []

def get_process(pid):
    """获取进程名"""
    try:
        result = subprocess.run(
            f'tasklist /FI "PID eq {pid}" /FO CSV /NH',
            shell=True, capture_output=True, text=True, timeout=3
        )
        line = result.stdout.strip().strip('"')
        parts = line.split('","')
        if len(parts) >= 1:
            return parts[0].strip('"')
    except:
        pass
    return f"PID:{pid}"

def get_connections():
    """获取当前到目标IP的TCP连接"""
    conns = []
    try:
        result = subprocess.run(
            'netstat -ano | findstr ESTABLISHED',
            shell=True, capture_output=True, text=True, timeout=5
        )
        target_ips = set(resolve_ips(TARGET))
        
        for line in result.stdout.strip().split('\n'):
            if not line.strip():
                continue
            parts = line.split()
            if len(parts) < 5:
                continue
            
            # 找包含目标IP的行
            remote = parts[2] if len(parts) > 2 else ""
            pid_str = parts[-1]
            
            if not pid_str.isdigit():
                continue
            
            # 检查是否连接到目标IP
            remote_ip = remote.rsplit(':', 1)[0] if ':' in remote else remote
            
            # 也直接检查 netstat 里域名的情况
            if any(t in line.lower() for t in ['deepseek', 'api.deepseek']):
                conns.append({
                    'pid': int(pid_str),
                    'remote': remote,
                    'line': line.strip()
                })
            elif remote_ip in target_ips:
                conns.append({
                    'pid': int(pid_str),
                    'remote': remote,
                    'line': line.strip()
                })
    except Exception as e:
        pass
    
    # 去重：同一PID只算一次
    seen = set()
    unique = []
    for c in conns:
        if c['pid'] not in seen:
            seen.add(c['pid'])
            c['process'] = get_process(c['pid'])
            unique.append(c)
    return unique

def format_time(t):
    return time.strftime('%H:%M:%S', time.localtime(t))

def print_header():
    print("=" * 75)
    print("  DeepSeek API 实时调用监控")
    print("  目标: api.deepseek.com | 间隔: 5秒 | 时长: 10分钟")
    print("=" * 75)
    print()

if __name__ == "__main__":
    print_header()
    print(f"  正在解析 api.deepseek.com ...")
    ips = resolve_ips(TARGET)
    print(f"  解析到 {len(ips)} 个IP: {', '.join(ips)}")
    print()
    
    start = time.time()
    samples = []
    cumulative = defaultdict(lambda: {'count': 0, 'first_seen': None, 'last_seen': None})
    
    iteration = 0
    try:
        while time.time() - start < DURATION:
            iteration += 1
            elapsed = int(time.time() - start)
            remaining = DURATION - elapsed
            
            conns = get_connections()
            
            now = time.time()
            for c in conns:
                proc = c['process']
                cumulative[proc]['count'] += 1
                if cumulative[proc]['first_seen'] is None:
                    cumulative[proc]['first_seen'] = now
                cumulative[proc]['last_seen'] = now
            
            ts = format_time(now)
            
            if conns:
                procs = ', '.join(f"{c['process']}(PID:{c['pid']})" for c in conns)
                print(f"  [{ts}] ⚡ {len(conns)} 个进程正在连接 DeepSeek: {procs}")
            else:
                if iteration % 6 == 0:  # 每30秒打印一次"安静"状态
                    print(f"  [{ts}] 🟢 无连接 — 剩余 {remaining//60}分{remaining%60}秒")
            
            samples.append({
                'time': ts,
                'count': len(conns),
                'processes': [{'pid': c['pid'], 'name': c['process']} for c in conns]
            })
            
            time.sleep(INTERVAL)
    
    except KeyboardInterrupt:
        print("\n\n  ⚠️ 监控被用户中断")
    
    # ── 汇总 ──
    elapsed = time.time() - start
    print()
    print("=" * 75)
    print("  📊 监控汇总")
    print("=" * 75)
    print(f"  监控时长: {int(elapsed)}秒 ({int(elapsed/60)}分钟)")
    print(f"  采样次数: {len(samples)}")
    
    total_detections = sum(s['count'] for s in samples)
    active_samples = sum(1 for s in samples if s['count'] > 0)
    print(f"  检测到连接的采样: {active_samples}/{len(samples)} ({active_samples/len(samples)*100:.0f}%)")
    print(f"  连接检测总次数: {total_detections}")
    print()
    
    if cumulative:
        print(f"  {'进程':<30} {'检测次数':>8}  {'首次出现':>10}  {'最后出现':>10}")
        print(f"  {'-'*30} {'-'*8} {'-'*10} {'-'*10}")
        for proc, data in sorted(cumulative.items(), key=lambda x: -x[1]['count']):
            first = format_time(data['first_seen']) if data['first_seen'] else '—'
            last = format_time(data['last_seen']) if data['last_seen'] else '—'
            print(f"  {proc:<30} {data['count']:>8}  {first:>10}  {last:>10}")
            if data['first_seen'] and data['last_seen']:
                dur = data['last_seen'] - data['first_seen']
                if dur > 5:
                    print(f"    → 活跃窗口: {int(dur)}秒")
    else:
        print("  🟢 监控期间未检测到任何 DeepSeek API 连接")
        print("  → 没有程序在偷偷调用 DeepSeek")
        print()

    # 保存采样
    outfile = r"D:\openclaw-workspace\logs\deepseek_monitor.json"
    os.makedirs(os.path.dirname(outfile), exist_ok=True)
    with open(outfile, "w", encoding="utf-8") as f:
        json.dump(samples, f, indent=2, ensure_ascii=False)
    print(f"  采样数据已保存: {outfile}")
