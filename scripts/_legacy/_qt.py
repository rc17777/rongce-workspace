import os,json,requests,sys,io
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8')
key=os.environ.get("OC_KEY_FABLE","")
print(f"Key exists: {bool(key)}")
print(f"Key preview: {key[:15]}...")
r=requests.post('https://cbwyy.top/v1/chat/completions',
    headers={'Authorization':f'Bearer {key}','Content-Type':'application/json'},
    json={'model':'claude-fable-5','messages':[{'role':'user','content':'Say OK'}],'max_tokens':5},
    timeout=30)
print(f"HTTP {r.status_code}")
if r.status_code==200:
    d=r.json()
    usage=d.get('usage',{})
    print(f"OK [{d['choices'][0]['message']['content'].strip()}] in:{usage.get('prompt_tokens','?')} out:{usage.get('completion_tokens','?')}")
else:
    print(r.text[:200])
