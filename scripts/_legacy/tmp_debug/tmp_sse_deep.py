"""Deep SSE inspection with gpt-5.5"""
import requests, json, time

key = 'sk-bs4fgPtIHhh4kKTKIRh33HISbvxMJDcQQx2kRnlmWv4faesU'
headers = {
    'Authorization': f'Bearer {key}',
    'Content-Type': 'application/json',
}

# Simulate what Codex would send (with tools, instructions, etc.)
body = {
    'model': 'gpt-5.5',
    'instructions': 'You are an AI assistant.',
    'input': 'Say hello.',
    'stream': True,
    'max_output_tokens': 1024,
}

print('=== SSE Frame Analysis (gpt-5.5 via cbwyy.top) ===')
r = requests.post('https://cbwyy.top/v1/responses',
    headers=headers, json=body, timeout=60, stream=True)

print(f'HTTP Status: {r.status_code}')
print(f'Content-Type: {r.headers.get("Content-Type")}')
print(f'Transfer-Encoding: {r.headers.get("Transfer-Encoding")}')
print(f'Cache-Control: {r.headers.get("Cache-Control")}')
print()

# Read raw chunks and analyze SSE structure
raw_data = b''
chunk_count = 0
for chunk in r.iter_content(chunk_size=1):  # byte by byte for precision
    raw_data += chunk
    chunk_count += 1
    if chunk_count > 10000:  # safety limit
        break

# Analyze SSE structure
text = raw_data.decode('utf-8', errors='replace')

print(f'Total bytes: {len(raw_data)}')
print(f'Total SSE events (by double newline): {text.count(chr(10)+chr(10))}')
print()

# Find and analyze each SSE event
events = text.split('\n\n')
print(f'First 3 events:')
for i, event in enumerate(events[:3]):
    lines = event.strip().split('\n')
    fields = {}
    for line in lines:
        if ':' in line:
            k, v = line.split(':', 1)
            fields[k.strip()] = v.strip()
    event_type = fields.get('event', '(no event field)')
    data_len = len(fields.get('data', ''))
    print(f'  Event {i+1}: type={event_type}, data_len={data_len}')
    # Validate JSON if data field exists
    if 'data' in fields:
        try:
            parsed = json.loads(fields['data'])
            data_type = parsed.get('type', '?')
            print(f'    JSON type: {data_type}')
        except json.JSONDecodeError as e:
            print(f'    JSON ERROR: {e}')
            print(f'    Raw: {fields["data"][:200]}')

# Check for: 
# 1. Missing event field on data-only events
# 2. Extra whitespace in event field
# 3. Malformed JSON in data field
# 4. Missing final newline
print()
print('=== Potential issues ===')
if not text.endswith('\n\n'):
    print('WARNING: Stream does not end with double newline!')
    print(f'  Last 100 chars: {repr(text[-100:])}')

# Check if any data: field contains non-JSON
for i, event_text in enumerate(events):
    if not event_text.strip():
        continue
    for line in event_text.split('\n'):
        if line.startswith('data:'):
            try:
                json.loads(line[5:].strip())
            except json.JSONDecodeError:
                if '[DONE]' not in line:
                    print(f'  Non-JSON data in event {i}: {line[:150]}')

# Check if there are any lines without proper SSE field format
for i, line in enumerate(text.split('\n')):
    if line.strip() and ':' not in line[:50]:  # line has content but no colon
        print(f'  Line {i} missing colon separator: {repr(line[:100])}')

print()
print('=== Comparison with standard OpenAI SSE ===')
print('Standard: data: {...}\\n\\n')
print(f'This proxy: {repr(text[:200])}')

r.close()
