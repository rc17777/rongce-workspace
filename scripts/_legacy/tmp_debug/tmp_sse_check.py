"""Check raw SSE framing from cbwyy.top responses API"""
import requests, time

key = 'sk-bs4fgPtIHhh4kKTKIRh33HISbvxMJDcQQx2kRnlmWv4faesU'
headers = {
    'Authorization': f'Bearer {key}',
    'Content-Type': 'application/json',
    'Accept': 'text/event-stream',
}

body = {
    'model': 'deepseek-v4-flash',
    'input': 'Say hi in one sentence.',
    'stream': True,
}

print('=== Raw HTTP Response (first 3KB) ===')
r = requests.post('https://cbwyy.top/v1/responses',
    headers=headers, json=body, timeout=30, stream=True)

# Print response headers
print(f'Status: {r.status_code}')
print(f'Headers:')
for k, v in r.headers.items():
    print(f'  {k}: {v}')

print(f'\n--- Raw body (first 3000 bytes) ---')
raw = r.raw.read(3000)
# Show as hex for first 200 bytes to check framing
print(f'First 200 bytes (hex): {raw[:200].hex()}')
print(f'\nDecoded (utf-8):')
print(raw.decode('utf-8', errors='replace'))
print(f'\nTotal raw bytes received: {len(raw)} (truncated at 3000)')

# Check for common SSE framing issues
text = raw.decode('utf-8', errors='replace')
lines = text.split('\n')
print(f'\n=== SSE framing analysis ===')
print(f'Total lines: {len(lines)}')
empty_lines = sum(1 for l in lines if l.strip() == '')
print(f'Empty lines (event separators): {empty_lines}')
data_lines = sum(1 for l in lines if l.startswith('data:'))
print(f'Lines starting with "data:": {data_lines}')
event_lines = sum(1 for l in lines if l.startswith('event:'))
print(f'Lines starting with "event:": {event_lines}')

# Check if each data line has valid JSON
import json
parse_errors = 0
for l in lines:
    if l.startswith('data:'):
        try:
            json.loads(l[5:].strip())
        except:
            parse_errors += 1
            if parse_errors <= 3:
                print(f'  JSON parse error: {l[:100]}')
if parse_errors == 0:
    print('All data lines parse as valid JSON: YES')

# Check for double newlines (proper SSE event termination)
print(f'\nDouble newline check:')
if '\n\n' in text[:1000]:
    print('  Has double newlines (proper SSE termination): YES')
else:
    print('  WARNING: No double newlines in first 1000 bytes!')

r.close()
