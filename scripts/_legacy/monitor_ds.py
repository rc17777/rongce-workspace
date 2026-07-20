# -*- coding: utf-8 -*-
"""DeepSeek API connection monitor - resolves IP first, then tracks connections"""
import sys, os, time, subprocess, socket
sys.stdout.reconfigure(encoding='utf-8')

print("DeepSeek API Real-time Monitor (10min, 10s interval)", flush=True)
print("=" * 60, flush=True)

# Resolve DeepSeek API IPs
print("Resolving api.deepseek.com...", flush=True)
try:
    addrs = socket.getaddrinfo("api.deepseek.com", 443, socket.AF_INET, socket.SOCK_STREAM)
    target_ips = list(set(a[4][0] for a in addrs))
    print(f"IPs: {target_ips}", flush=True)
except Exception as e:
    print(f"DNS resolve failed: {e}", flush=True)
    target_ips = []

print("=" * 60, flush=True)

DURATION = 600
INTERVAL = 10

start = time.time()
total = 0
iteration = 0

try:
    while time.time() - start < DURATION:
        iteration += 1
        elapsed = int(time.time() - start)
        remaining = DURATION - elapsed
        ts = time.strftime("%H:%M:%S")

        r = subprocess.run("netstat -ano", shell=True, capture_output=True, text=True)
        lines = []
        for line in r.stdout.split('\n'):
            l = line.strip()
            if not l or 'ESTABLISHED' not in l:
                continue
            # Check if remote IP matches any target IP
            parts = l.split()
            if len(parts) >= 3:
                remote = parts[2]
                remote_ip = remote.rsplit(':', 1)[0] if ':' in remote else remote
                if remote_ip in target_ips:
                    lines.append(l)

        if lines:
            print(f"[{ts}] {len(lines)} connection(s) | {remaining//60}m{remaining%60}s left", flush=True)
            for l in lines:
                parts = l.split()
                if len(parts) >= 5:
                    pid = parts[-1]
                    try:
                        r2 = subprocess.run(
                            f'tasklist /FI "PID eq {pid}" /FO CSV /NH',
                            shell=True, capture_output=True, text=True
                        )
                        if r2.stdout.strip():
                            pname = r2.stdout.strip().strip('"').split('","')[0]
                        else:
                            pname = f"PID:{pid}"
                    except:
                        pname = f"PID:{pid}"
                    print(f"  -> {pname} (remote: {parts[2]})", flush=True)
            total += len(lines)
        elif iteration % 6 == 0:
            print(f"[{ts}] no connection | {remaining//60}m{remaining%60}s left", flush=True)

        time.sleep(INTERVAL)
except KeyboardInterrupt:
    print("\nStopped by user.", flush=True)

print("", flush=True)
print("=" * 60, flush=True)
print(f"Done. Total connections detected: {total}", flush=True)
if total == 0:
    print("No process connected to DeepSeek API. Leak is plugged.", flush=True)
