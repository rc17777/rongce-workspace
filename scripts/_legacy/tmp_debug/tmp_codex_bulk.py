"""Test large request body and intermittent failures"""
import requests, json, time

key = 'sk-bs4fgPtIHhh4kKTKIRh33HISbvxMJDcQQx2kRnlmWv4faesU'
headers = {
    'Authorization': f'Bearer {key}',
    'Content-Type': 'application/json',
}

# Test with a VERY large input (simulating long conversation)
large_input = [
    {'role': 'user', 'content': f'This is message {i} in a long conversation. ' * 3}
    for i in range(50)
] + [
    {'role': 'user', 'content': 'Now summarize what we discussed about message patterns.'}
]

body_large = {
    'model': 'gpt-5.5',
    'input': large_input,
    'stream': True,
    'max_output_tokens': 2048,
}

size_kb = len(json.dumps(body_large)) / 1024
print(f'=== 超大请求体测试: {size_kb:.1f} KB ===')

for attempt in range(3):
    print(f'\n--- Attempt {attempt+1}/3 ---')
    start = time.time()
    event_count = 0
    try:
        r = requests.post('https://cbwyy.top/v1/responses',
            headers=headers, json=body_large, timeout=120, stream=True)
        print(f'Status: {r.status_code} (TTFB: {time.time()-start:.1f}s)')
        
        if r.status_code != 200:
            print(f'Error: {r.text[:300]}')
            break
        
        for line in r.iter_lines(decode_unicode=True):
            if line:
                event_count += 1
        
        total = time.time() - start
        print(f'COMPLETE: {event_count} events in {total:.1f}s')
        
    except Exception as e:
        print(f'FAILED at {time.time()-start:.1f}s: {type(e).__name__}: {e}')

print('\n=== 重复测试 (短请求, 10次) ===')
for i in range(10):
    try:
        r = requests.post('https://cbwyy.top/v1/responses',
            headers=headers,
            json={'model': 'gpt-5.5', 'input': 'Say hi', 'stream': True},
            timeout=30, stream=True)
        chunks = sum(1 for _ in r.iter_lines(decode_unicode=True) if _)
        print(f'  #{i+1}: {r.status_code} ({chunks} chunks)')
    except Exception as e:
        print(f'  #{i+1}: FAILED - {type(e).__name__}: {e}')
        break
