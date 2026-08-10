"""Stress test cbwyy.top /v1/responses streaming"""
import requests, time, sys

key = 'sk-bs4fgPtIHhh4kKTKIRh33HISbvxMJDcQQx2kRnlmWv4faesU'
headers = {'Authorization': f'Bearer {key}', 'Content-Type': 'application/json'}
body = {
    'model': 'gpt-5.5',
    'input': 'Say hi',
    'stream': True,
    'max_output_tokens': 100,
}

print('=== /v1/responses 流式压测 (50次) ===')
sys.stdout.flush()
results = []
start = time.time()

for i in range(50):
    try:
        r = requests.post('https://cbwyy.top/v1/responses',
            headers=headers, json=body, timeout=30, stream=True)
        chunks = sum(1 for _ in r.iter_lines(decode_unicode=True) if _)
        results.append((i+1, True, chunks))
    except Exception as e:
        results.append((i+1, False, str(e)[:100]))
    
    if (i+1) % 10 == 0:
        ok_sofar = sum(1 for r in results if r[1])
        print(f'  [{i+1}/50] success rate: {ok_sofar}/{i+1}')
        sys.stdout.flush()

total = time.time() - start
oks = sum(1 for r in results if r[1])
fails = [r for r in results if not r[1]]

print(f'\n=== 结果 ===')
print(f'成功: {oks}/50 ({oks/50*100:.0f}%)')
print(f'失败: {len(fails)}/50')
print(f'总耗时: {total:.1f}s')

if fails:
    print(f'\n失败详情:')
    for idx, _, err in fails:
        print(f'  #{idx}: {err}')
