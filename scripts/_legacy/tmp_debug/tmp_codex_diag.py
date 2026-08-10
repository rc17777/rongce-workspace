"""Diagnose Codex config and connectivity"""
import subprocess, os, json

print("=== Codex 配置诊断 ===")

# Check config files
paths_to_check = [
    os.path.expanduser('~/.codex/.env'),
    os.path.expanduser('~/.codex/auth.json'),
    os.path.expanduser('~/.codex/credentials.json'),
]

for p in paths_to_check:
    if os.path.exists(p):
        print(f'Found: {p}')
        with open(p) as f:
            content = f.read()
            if 'sk-' in content:
                idx = content.index('sk-')
                print(f'  Contains API key (masked): sk-...{content[idx+10:idx+20]}...')
            else:
                print(f'  Content: {content[:200]}')
    else:
        print(f'Not found: {p}')

# Check env var
key_env = os.environ.get('OPENAI_API_KEY', '')
if key_env:
    print(f'OPENAI_API_KEY env: sk-...{key_env[10:20]}...')
else:
    print('OPENAI_API_KEY env: not set')

# Parse TOML config
print()
print("=== .codex.toml 关键配置 ===")
codex_toml = os.path.expanduser('~/.codex/.codex.toml')
if os.path.exists(codex_toml):
    with open(codex_toml) as f:
        raw = f.read()
    
    # Extract key sections without needing toml library
    for line in raw.split('\n'):
        line = line.strip()
        if any(k in line for k in ['base_url', 'wire_api', 'requires_openai_auth', 'model =', 'model_provider']):
            # Mask any keys
            if 'sk-' in line:
                idx = line.index('sk-')
                line = line[:idx+10] + '...MASKED...' + line[idx+30:] if len(line) > idx+30 else line[:idx+10] + '...'
            print(f'  {line}')
else:
    print('  .codex.toml not found!')

# Check Codex logs for recent errors
print()
print("=== Codex 最近日志 ===")
log_dir = os.path.expanduser('~/.codex/logs')
if os.path.exists(log_dir):
    logs = sorted(os.listdir(log_dir), reverse=True)[:3]
    for log in logs:
        logpath = os.path.join(log_dir, log)
        size = os.path.getsize(logpath)
        print(f'  {log} ({size} bytes)')
        if size < 50000:
            with open(logpath, errors='ignore') as f:
                content = f.read()
                # Find error lines
                for line in content.split('\n'):
                    if any(k in line.lower() for k in ['error', 'disconnect', 'timeout', 'fail', 'stream']):
                        print(f'    {line.strip()[:200]}')
else:
    print('  No logs directory found')

# Test streaming connectivity
print()
print("=== 流式连接模拟测试 ===")
import socket, ssl, time
try:
    sock = socket.create_connection(('cbwyy.top', 443), timeout=10)
    ctx = ssl.create_default_context()
    ssock = ctx.wrap_socket(sock, server_hostname='cbwyy.top')
    # Send a minimal streaming request
    req = (
        b'POST /v1/responses HTTP/1.1\r\n'
        b'Host: cbwyy.top\r\n'
        b'Content-Type: application/json\r\n'
        b'Connection: keep-alive\r\n'
        b'\r\n'
        b'{"model":"gpt-5.5","input":"hi"}'
    )
    ssock.send(req)
    ssock.settimeout(30)
    start = time.time()
    response = b''
    while True:
        try:
            chunk = ssock.recv(4096)
            if not chunk:
                elapsed = time.time() - start
                print(f'Connection closed by server after {elapsed:.1f}s')
                break
            response += chunk
            if b'\r\n\r\n' in response:
                header_end = response.index(b'\r\n\r\n')
                headers = response[:header_end].decode('utf-8', errors='ignore')
                print(f'Headers received (first response in {elapsed:.1f}s):')
                for h in headers.split('\r\n')[:15]:
                    print(f'  {h}')
                break
        except socket.timeout:
            print(f'Timeout after {time.time()-start:.1f}s')
            break
    ssock.close()
except Exception as e:
    print(f'Stream test failed: {e}')
