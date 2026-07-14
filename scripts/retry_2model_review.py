# -*- coding: utf-8 -*-
import json,requests,re
from pathlib import Path
cfg=json.loads((Path.home()/'.openclaw'/'openclaw.json').read_text(encoding='utf8'))
out=Path(__file__).resolve().parents[1]/'analysis/kb-review-11models-20260711'
prompt='''独立验收知识库升级。事实：Obsidian 108篇、YAML错误0、断链0；建成采购/经责/绩效3个驾驶舱和预算编制/财政评审/工程结算/全过程咨询4个驾驶舱，每个6页；建立355条knowledge元数据目录；项目回流默认待人工审核，Office文件仅登记不解析；核心不足可能包括规则仍是标题级、调度未完整接通、法规有效性待核验。按结构15、业务20、治理15、自动化20、安全15、维护15评分。只输出JSON，字段：scores(structure,business,governance,automation,safety,maintainability)、total、decision、p0、p1、p2、strengths、improvements、summary。'''
for label,pid,mid in [('fable-5','custom-cbwyy-fable','claude-fable-5'),('sonnet-5','custom-cbwyy-claude','claude-sonnet-5')]:
 pr=cfg['models']['providers'][pid];url=pr['baseUrl'].rstrip('/')+'/v1/messages'
 try:
  r=requests.post(url,headers={'x-api-key':pr['apiKey'],'anthropic-version':'2023-06-01','content-type':'application/json'},json={'model':mid,'max_tokens':2000,'messages':[{'role':'user','content':prompt}]},timeout=180)
  print(label,r.status_code);print(r.text[:500])
  if r.status_code==200:
   raw=''.join(x.get('text','') for x in r.json().get('content',[]));(out/f'{label}.retry.raw.txt').write_text(raw,encoding='utf8')
 except Exception as e: print(label,'ERR',e)
