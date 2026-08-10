"""Diagnose cbwyy.top proxy connectivity for Codex"""
import requests, time, socket, ssl

base = 'https://cbwyy.top'

# Test 1: Basic connectivity + latency
print('=== 1. 基础连通性 ===')
try:
    start = time.time()
    r = requests.get(f'{base}/v1/models', timeout=10)
    elapsed = (time.time() - start) * 1000
    print(f'GET /v1/models -> {r.status_code} ({elapsed:.0f}ms)')
    if r.status_code == 401:
        print('  -> 401=服务器在线，需认证(正常)')
except Exception as e:
    print(f'GET /v1/models -> FAILED: {e}')

# Test 2: DNS
print()
print('=== 2. DNS解析 ===')
try:
    ip = socket.gethostbyname('cbwyy.top')
    print(f'cbwyy.top -> {ip}')
except Exception as e:
    print(f'DNS FAILED: {e}')

# Test 3: TLS
print()
print('=== 3. TLS握手 ===')
try:
    ctx = ssl.create_default_context()
    sock = socket.create_connection(('cbwyy.top', 443), timeout=10)
    ssock = ctx.wrap_socket(sock, server_hostname='cbwyy.top')
    cert = ssock.getpeercert()
    cn = dict(cert.get('subject', [])).get('commonName', '?')
    not_after = cert.get('notAfter', '?')
    print(f'TLS OK, CN={cn}, 到期={not_after}')
    ssock.close()
except Exception as e:
    print(f'TLS FAILED: {e}')

# Test 4: TCP connection to port 443
print()
print('=== 4. TCP 443端口 ===')
try:
    sock = socket.create_connection(('cbwyy.top', 443), timeout=10)
    print(f'TCP 443 -> OK')
    sock.close()
except Exception as e:
    print(f'TCP 443 FAILED: {e}')

# Test 5: Try /v1/chat/completions (OpenAI compat)
print()
print('=== 5. 流式API端点可达性 ===')
for path in ['/v1/responses', '/v1/chat/completions', '/']:
    try:
        r = requests.get(f'{base}{path}', timeout=10)
        print(f'{path} -> {r.status_code}')
    except Exception as e:
        print(f'{path} -> FAILED: {e}')

# Test 6: Check if it's an SSL/TLS issue or HTTP2 issue
print()
print('=== 6. HTTP版本探测 ===')
try:
    # requests uses urllib3, try with explicit http1.1
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
    s = requests.Session()
    r = s.get(f'{base}/v1/models', timeout=10)
    print(f'Default HTTP version -> {r.status_code} (via {r.raw.version})')
except Exception as e:
    print(f'HTTP version check failed: {e}')

print()
print('=== 诊断完成 ===')
