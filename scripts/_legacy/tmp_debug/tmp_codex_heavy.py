"""Test Codex-like heavy requests"""
import requests, json, time

key = 'sk-bs4fgPtIHhh4kKTKIRh33HISbvxMJDcQQx2kRnlmWv4faesU'
headers = {
    'Authorization': f'Bearer {key}',
    'Content-Type': 'application/json',
    'User-Agent': 'Codex/26.623',
}

# Simulate a realistic Codex request with tools, instructions, conversation
body_tools = {
    'model': 'gpt-5.5',
    'instructions': 'You are an AI coding assistant. Help the user with programming tasks, file operations, and system commands. Be concise and accurate.',
    'input': [
        {'role': 'user', 'content': 'Write a Python function that sorts a list of dictionaries by a given key.'}
    ],
    'tools': [
        {
            'type': 'function',
            'name': 'read_file',
            'description': 'Read a file from the filesystem',
            'parameters': {
                'type': 'object',
                'properties': {
                    'path': {'type': 'string', 'description': 'File path'}
                },
                'required': ['path']
            }
        },
        {
            'type': 'function', 
            'name': 'write_file',
            'description': 'Write content to a file',
            'parameters': {
                'type': 'object',
                'properties': {
                    'path': {'type': 'string'},
                    'content': {'type': 'string'}
                },
                'required': ['path', 'content']
            }
        },
        {
            'type': 'function',
            'name': 'execute_command',
            'description': 'Run a shell command',
            'parameters': {
                'type': 'object',
                'properties': {
                    'command': {'type': 'string'},
                    'workdir': {'type': 'string'}
                },
                'required': ['command']
            }
        }
    ],
    'stream': True,
    'reasoning': {'effort': 'high'},
    'max_output_tokens': 4096,
}

print(f'=== 重量级Codex模拟 ===')
print(f'Body size: {len(json.dumps(body_tools))} bytes')
print(f'Tools: {len(body_tools["tools"])} functions')
print()

start = time.time()
event_count = 0
error_events = []

try:
    r = requests.post('https://cbwyy.top/v1/responses',
        headers=headers, json=body_tools, timeout=180, stream=True)
    print(f'Status: {r.status_code} (TTFB: {time.time()-start:.1f}s)')
    
    if r.status_code != 200:
        print(f'Error: {r.text[:500]}')
    else:
        for line in r.iter_lines(decode_unicode=True):
            if line:
                event_count += 1
                if event_count <= 5:
                    print(f'  [{event_count}] {line[:180]}')
                if '"error"' in line and '"error":null' not in line:
                    error_events.append(line[:300])
        
        total = time.time() - start
        print(f'COMPLETE: {event_count} events in {total:.1f}s')
        if error_events:
            print(f'ERROR EVENTS:')
            for e in error_events:
                print(f'  {e}')
                
except requests.exceptions.ChunkedEncodingError as e:
    print(f'STREAM BROKEN at event {event_count}, {time.time()-start:.1f}s: {e}')
except Exception as e:
    print(f'FAILED at {time.time()-start:.1f}s: {type(e).__name__}: {e}')
