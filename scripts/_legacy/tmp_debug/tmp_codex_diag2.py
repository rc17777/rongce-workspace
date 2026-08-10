"""Deep diagnosis: test different API parameters and formats"""
import requests, json, time, sys

key = 'sk-bs4fgPtIHhh4kKTKIRh33HISbvxMJDcQQx2kRnlmWv4faesU'
headers = {'Authorization': f'Bearer {key}', 'Content-Type': 'application/json'}
base = 'https://cbwyy.top/v1'

def test(name, endpoint, body, timeout=60):
    print(f'\n{"="*60}')
    print(f'测试: {name}')
    print(f'端点: {endpoint}')
    print(f'参数: {json.dumps(body, ensure_ascii=False)[:200]}')
    start = time.time()
    try:
        r = requests.post(f'{base}{endpoint}',
            headers=headers, json=body, timeout=timeout, stream=('stream' in body and body['stream']))
        elapsed = time.time() - start
        
        if 'stream' in body and body['stream']:
            print(f'Status: {r.status_code} (TTFB: {elapsed:.1f}s)')
            event_count = 0
            error_seen = False
            try:
                for line in r.iter_lines(decode_unicode=True):
                    if line:
                        event_count += 1
                        if event_count <= 3:
                            print(f'  [{event_count}] {line[:150]}')
                        if '"error"' in line.lower() or '"type":"error"' in line:
                            print(f'  ERROR EVENT: {line[:300]}')
                            error_seen = True
            except Exception as e:
                print(f'  STREAM BROKEN at chunk {event_count}: {type(e).__name__}: {e}')
                return False
            total = time.time() - start
            print(f'  COMPLETE: {event_count} events, {total:.1f}s total')
        else:
            print(f'Status: {r.status_code} ({elapsed:.1f}s)')
            if r.status_code == 200:
                data = r.json()
                output = data.get('output', [])
                if output:
                    for o in output[:2]:
                        content = o.get('content', [])
                        for c in content[:2]:
                            print(f'  output: {c.get("text","")[:150]}')
            else:
                print(f'  Error body: {r.text[:400]}')
        return True
    except requests.exceptions.ConnectionError as e:
        print(f'  CONNECTION ERROR after {time.time()-start:.1f}s: {e}')
        return False
    except requests.exceptions.ReadTimeout:
        print(f'  READ TIMEOUT after {time.time()-start:.1f}s')
        return False
    except Exception as e:
        print(f'  FAILED after {time.time()-start:.1f}s: {type(e).__name__}: {e}')
        return False

# Test 1: responses API, NO reasoning, streaming
test('T1: /responses 流式, 无reasoning',
     '/responses',
     {'model': 'gpt-5.5', 'input': 'Explain TCP vs UDP briefly.', 'stream': True},
     timeout=60)

# Test 2: responses API, WITH reasoning=high, streaming  
test('T2: /responses 流式, reasoning=high',
     '/responses',
     {'model': 'gpt-5.5', 'input': 'Explain TCP vs UDP briefly.', 'reasoning': {'effort': 'high'}, 'stream': True},
     timeout=120)

# Test 3: chat completions API (compare)
test('T3: /chat/completions 流式',
     '/chat/completions',
     {'model': 'gpt-5.5', 'messages': [{'role': 'user', 'content': 'Explain TCP vs UDP briefly.'}], 'stream': True},
     timeout=60)

# Test 4: responses API, non-streaming, reasoning=high
test('T4: /responses 非流式, reasoning=high',
     '/responses',
     {'model': 'gpt-5.5', 'input': 'Explain TCP vs UDP briefly.', 'reasoning': {'effort': 'high'}},
     timeout=120)

# Test 5: responses API, reasoning=medium
test('T5: /responses 流式, reasoning=medium',
     '/responses',
     {'model': 'gpt-5.5', 'input': 'Explain TCP vs UDP briefly.', 'reasoning': {'effort': 'medium'}, 'stream': True},
     timeout=120)

print('\n\n诊断完成')
