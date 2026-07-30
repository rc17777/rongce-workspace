import json
with open(r'C:\Users\scrccpa\.openclaw\openclaw.json') as f:
    c = json.load(f)

for pid in ['custom-cbwyy-qwen', 'qwen-direct']:
    if pid in c['models']['providers']:
        pdata = c['models']['providers'][pid]
        print(f'Provider: {pid}')
        print(f'  type of pdata: {type(pdata)}')
        print(f'  keys: {list(pdata.keys())}')
        models = pdata.get('models', [])
        print(f'  type of models: {type(models)}')
        if isinstance(models, dict):
            print(f'  models keys: {list(models.keys())[:5]}')
            for k, v in models.items():
                print(f'    {k}: {v}')
                break
        elif isinstance(models, list):
            for m in models:
                print(f'  model: {m}')
        print()
