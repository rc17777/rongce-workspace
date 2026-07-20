# -*- coding: utf-8 -*-
from pathlib import Path
import json,statistics,collections
p=Path(__file__).resolve().parents[1]/'analysis/kb-review-11models-20260711'
r=json.loads((p/'results.json').read_text(encoding='utf8'))
s=(p/'sonnet-5.retry.raw.txt').read_text(encoding='utf8').strip();a=s.find('{');b=s.rfind('}');o=json.loads(s[a:b+1]);o['requested_model']='sonnet-5'
r=[x for x in r if x.get('requested_model')!='sonnet-5']+[o]
valid=[x for x in r if 'total'in x]
for x in valid:print(x['requested_model'],x['total'],x.get('decision'),x['scores'],'P0',x.get('p0'))
print('AVG',round(statistics.mean(x['total'] for x in valid),2),'N',len(valid))
for x in valid:
 print('\n##',x['requested_model']);print('\n'.join('- '+str(i) for i in x.get('improvements',[])))
(p/'results-final.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf8')
