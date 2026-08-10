"""Stress test cbwyy.top proxy stability"""
import requests, json, time, concurrent.futures

key = 'sk-bs4fgPtIHhh4kKTKIRh33HISbvxMJDcQQx2kRnlmWv4faesU'
headers = {
    'Authorization': f'Bearer {key}',
    'Content-Type': 'application/json',
}

def single_request(i):
    try:
        r = requests.post('https://cbwyy.top/v1/responses',
            headers=headers,
            json={'model': 'gpt-5.5', 'input': 'Say hi', 'stream': True},
            timeout=30, stream=True)
        chunks = sum(1 for _ in r.iter_lines(decode_unicode=True) if _)
        return (i, True, r.status_code, chunks)
    except Exception as e:
        return (i, False, type(e).__name__, str(e)[:100])

print('=== cbwyy.top 稳定性压测 (50次, 顺序) ===')
start = time.time()
results = []
for i in range(50):
    idx, ok, info, detail = single_request(i+1)
    results.append((idx, ok, info, detail))
    if not ok:
        print(f'  #{idx}: FAIL [{info}] {detail}')
    elif (i+1) % 10 == 0:
        print(f'  #{idx}: OK')

total = time.time() - start
oks = sum(1 for r in results if r[1])
fails = len(results) - oks
print(f'\n结果: {oks}/{len(results)} 成功, {fails} 失败 ({fails/len(results)*100:.1f}% 故障率)')
print(f'总耗时: {total:.1f}s')

# Also test chat completions endpoint
print(f'\n=== /chat/completions 稳定性 (20次) ===')
cr = []
for i in range(20):
    try:
        r = requests.post('https://cbwyy.top/v1/chat/completions',
            headers=headers,
            json={'model': 'gpt-5.5', 'messages': [{'role':'user','content':'hi'}], 'stream': True},
            timeout=30, stream=True)
        chunks = sum(1 for _ in r.iter_lines(decode_unicode=True) if _)
        cr.append(True)
    except Exception as e:
        cr.append(False)
        print(f'  #{i+1}: FAIL [{type(e).__name__}]')

c_ok = sum(cr)
print(f'结果: {c_ok}/20 成功, {20-c_ok} 失败 ({(20-c_ok)/20*100:.1f}% 故障率)')
