# -*- coding: utf-8 -*-
"""Call gpt-5.6-sol with minimal prompt."""
import json, sys, urllib.request, urllib.error
sys.stdout.reconfigure(encoding='utf-8')

prompt = "政府审计宣传册v3，深蓝+金色，17页，已完成深海渐变/金色减量/字体层级/过渡页/品牌符号等改进。用户仍反馈不够高级。请列出3个核心问题和3个改进建议，每项一句话。不要超过300字。"

url = 'https://cbwyy.top/v1/chat/completions'
headers = {
    'Authorization': 'Bearer sk-eulyTfe7nRmr5ruwQH85kIfHkc8PPd88EoYGX0yadzlrkEpv',
    'Content-Type': 'application/json'
}
payload = json.dumps({
    'model': 'gpt-5.6-sol',
    'messages': [{'role': 'user', 'content': prompt}],
    'max_tokens': 512
})

print('Calling...', flush=True)
req = urllib.request.Request(url, data=payload.encode('utf-8'), headers=headers, method='POST')
try:
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read().decode('utf-8'))
        if 'choices' in data:
            print(data['choices'][0]['message']['content'], flush=True)
        else:
            print('Error: ' + json.dumps(data, ensure_ascii=False), flush=True)
except Exception as e:
    print('Error: ' + str(e)[:200], flush=True)