# -*- coding: utf-8 -*-
"""直接调用已配置的11个模型，独立验收知识库升级。密钥只从openclaw.json读取，不写入输出。"""
from pathlib import Path
import json,requests,time,re,statistics
WS=Path(__file__).resolve().parents[1]
CFG=Path.home()/'.openclaw'/'openclaw.json'
OUT=WS/'analysis'/'kb-review-11models-20260711';OUT.mkdir(parents=True,exist_ok=True)
V=Path(r'D:\openclaw-workspace\obsidian-vault')
models=[
('v4-flash','custom-cbwyy-top-v1','deepseek-v4-flash'),('v4-pro','custom-cbwyy-top-v1','deepseek-v4-pro'),
('qwen3.7-plus','custom-cbwyy-qwen','qwen3.7-plus'),('fable-5','custom-cbwyy-fable','claude-fable-5'),
('sonnet-5','custom-cbwyy-claude','claude-sonnet-5'),('opus-4-8','custom-cbwyy-opus','claude-opus-4-8'),
('gpt-5.5','custom-cbwyy-gpt55','gpt-5.5'),('gpt-5.6-luna','custom-cbwyy-luna','gpt-5.6-luna'),
('gpt-5.6-sol','custom-cbwyy-sol','gpt-5.6-sol'),('gpt-5.6-terra','custom-cbwyy-terra','gpt-5.6-terra'),
('doubao','custom-cbwyy-doubao','doubao-seed-2.0-lite')]

def rd(p,n=9000):
 try:return Path(p).read_text(encoding='utf8',errors='ignore')[:n]
 except:return ''

def packet():
 files=[WS/'knowledge/knowledge-upgrade-implementation-20260711.md',WS/'scripts/upgrade_obsidian_kb.py',WS/'scripts/build_knowledge_catalog.py',WS/'scripts/project_knowledge_feedback.py',V/'index.md',V/'00-系统/元数据标准.md',V/'00-系统/知识源台账.md']
 for d in ['02-主题数据库/采购招投标审计','02-主题数据库/经济责任审计','02-主题数据库/绩效评价','工程咨询/预算编制','工程咨询/财政评审','工程咨询/工程结算','工程咨询/全过程工程咨询']:
  files += [V/d/'_index.md',V/d/'风险与识别规则.md',V/d/'资料清单.md']
 parts=[]
 for p in files: parts.append(f'\n===== {p} =====\n'+rd(p,5000))
 evidence='''\n===== 自动验收事实 =====
Obsidian Markdown=108；YAML解析错误=0；Wiki断链=0；三个审计驾驶舱及四个工程咨询驾驶舱均各6文件；knowledge_catalog=355条；Base YAML有效；回流冒烟识别4个办公文档并进入pending_human_review；项目Office文件仅登记不自动解析。\n'''
 return evidence+''.join(parts)

PROMPT='''你是独立验收专家。请根据下方“实际文件证据包”验收，不能只复述实施记录。评分总计100：结构完整性15、业务适配20、数据治理15、自动化可执行性20、安全合规15、可维护性15。重点识别“文件已建但功能未真正运行”“模板化内容过浅”“自动化名实不符”“审计责任风险”。严格只输出一个JSON对象，不要Markdown，结构：{"model":"","scores":{"structure":0,"business":0,"governance":0,"automation":0,"safety":0,"maintainability":0},"total":0,"decision":"通过/有条件通过/不通过","p0":[],"p1":[],"p2":[],"strengths":[三项],"improvements":[五项],"summary":"不超过200字"}。分项不能超过各自满分。\n\n实际文件证据包：\n'''

def extract_json(s):
 s=re.sub(r'^```(?:json)?\s*|\s*```$','',s.strip(),flags=re.S)
 a=s.find('{');b=s.rfind('}')
 return json.loads(s[a:b+1])

def call_openai(pr,mid,prompt):
 url=pr['baseUrl'].rstrip('/')+'/chat/completions'
 r=requests.post(url,headers={'Authorization':'Bearer '+pr['apiKey'],'Content-Type':'application/json'},json={'model':mid,'messages':[{'role':'user','content':prompt}],'temperature':0.2,'max_tokens':2500},timeout=180)
 r.raise_for_status();return r.json()['choices'][0]['message']['content']
def call_anthropic(pr,mid,prompt):
 url=pr['baseUrl'].rstrip('/')+'/v1/messages'
 r=requests.post(url,headers={'x-api-key':pr['apiKey'],'anthropic-version':'2023-06-01','content-type':'application/json'},json={'model':mid,'max_tokens':2500,'temperature':0.2,'messages':[{'role':'user','content':prompt}]},timeout=180)
 r.raise_for_status();return ''.join(x.get('text','') for x in r.json().get('content',[]))
def main():
 cfg=json.loads(CFG.read_text(encoding='utf8'));providers=cfg['models']['providers'];pkt=packet();(OUT/'evidence_packet.txt').write_text(pkt,encoding='utf8')
 results=[]
 for label,pid,mid in models:
  print('CALL',label,flush=True);pr=providers[pid];prompt=PROMPT+pkt
  try:
   raw=call_anthropic(pr,mid,prompt) if pr.get('api')=='anthropic-messages' else call_openai(pr,mid,prompt)
   (OUT/f'{label}.raw.txt').write_text(raw,encoding='utf8');obj=extract_json(raw);obj['requested_model']=label;results.append(obj);print('OK',label,obj.get('total'),flush=True)
  except Exception as e:
   results.append({'requested_model':label,'error':str(e)});print('ERR',label,e,flush=True)
  time.sleep(1)
 (OUT/'results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf8')
 valid=[x for x in results if 'total' in x];summary={'requested':11,'completed':len(valid),'failed':[x for x in results if 'error'in x],'average':round(statistics.mean(x['total'] for x in valid),2) if valid else None,'min':min((x['total'] for x in valid),default=None),'max':max((x['total'] for x in valid),default=None),'decisions':{d:sum(x.get('decision')==d for x in valid) for d in ['通过','有条件通过','不通过']}}
 (OUT/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(summary,ensure_ascii=False))
if __name__=='__main__':main()
