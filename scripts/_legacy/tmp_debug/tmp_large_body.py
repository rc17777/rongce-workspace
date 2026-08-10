"""Test with increasingly large request bodies - simulate Codex"""
import requests, time, json, sys

key = 'sk-bs4fgPtIHhh4kKTKIRh33HISbvxMJDcQQx2kRnlmWv4faesU'
headers = {'Authorization': f'Bearer {key}', 'Content-Type': 'application/json'}

# Codex sends very large requests with tools, history, etc.
# Test at 10KB, 50KB, 100KB body sizes

for size_kb in [10, 50, 100]:
    # Generate padding to reach target size
    base_body = {
        'model': 'gpt-5.5',
        'instructions': 'You are an AI coding assistant with access to file system, shell, and browser tools.',
        'input': [
            {'role': 'user', 'content': f'This is a test message. {"padding " * 50}'}
        ],
        'stream': True,
        'max_output_tokens': 50,  # Keep response tiny
    }
    
    current_size = len(json.dumps(base_body))
    padding_needed = max(0, size_kb * 1024 - current_size)
    
    if padding_needed > 0:
        # Add padding as extra conversation turns
        extra_turns = []
        for i in range(padding_needed // 100):
            extra_turns.append({'role': 'user', 'content': f'Turn {i}: ' + 'x' * 80})
            extra_turns.append({'role': 'assistant', 'content': 'y' * 80})
        base_body['input'] = extra_turns + base_body['input']
    
    actual_size = len(json.dumps(base_body)) / 1024
    print(f'Testing {actual_size:.0f}KB body... ', end='')
    sys.stdout.flush()
    
    try:
        start = time.time()
        r = requests.post('https://cbwyy.top/v1/responses',
            headers=headers, json=base_body, timeout=60, stream=True)
        chunks = sum(1 for _ in r.iter_lines(decode_unicode=True) if _)
        elapsed = time.time() - start
        print(f'OK: {r.status_code}, {chunks} events, {elapsed:.1f}s')
    except Exception as e:
        print(f'FAIL: {type(e).__name__}: {e}')
    
    time.sleep(1)  # Don't hammer the server
