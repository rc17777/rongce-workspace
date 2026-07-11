# -*- coding: utf-8 -*-
"""为knowledge全量文件构建统一元数据目录，不破坏原文。"""
from pathlib import Path
from datetime import datetime
import json,re,hashlib
ROOT=Path(__file__).resolve().parents[1]/'knowledge'
OUT=ROOT/'knowledge_catalog.json'

def infer(p,text):
    rel=str(p.relative_to(ROOT)).replace('\\','/')
    mapping=[('采购','采购招投标审计'),('招投标','采购招投标审计'),('围标','采购招投标审计'),('绩效','绩效评价'),('经济责任','经济责任审计'),('经责','经济责任审计'),('专项债','专项债审计'),('补贴','政府补贴审计'),('工程','工程审计'),('医疗','医疗审计'),('医保','医疗审计'),('国企','国企审计'),('能源','能源审计')]
    hay=rel+' '+text[:1500]
    lines=[]
    for k,v in mapping:
        if k in hay and v not in lines: lines.append(v)
    if not lines: lines=['通用']
    if '/policies/' in '/'+rel or '政策法规' in rel: dtype='法规'
    elif '案例' in rel: dtype='案例'
    elif '模板' in rel or 'model' in rel.lower(): dtype='模板/模型'
    elif 'intel_raw' in rel: dtype='采集原文'
    elif 'intel_summaries' in rel: dtype='情报摘要'
    else: dtype='参考资料'
    stage='现场'
    if any(x in hay for x in ['投标','招标公告']): stage='投标'
    elif any(x in hay for x in ['报告','复核']): stage='报告'
    elif any(x in hay for x in ['整改']): stage='整改'
    elif any(x in hay for x in ['审前','资料清单','取数']): stage='审前'
    validity='待核验' if dtype=='法规' else '参考有效'
    return {'type':'knowledge_source','title':p.stem,'business_line':lines,'scene':lines,'audit_stage':stage,'document_type':dtype,'keywords':list(dict.fromkeys(re.findall(r'[\u4e00-\u9fff]{2,8}',p.stem)))[:8],'source':'原文或采集来源见正文','source_date':datetime.fromtimestamp(p.stat().st_mtime).strftime('%Y-%m-%d'),'effective_date':None,'validity':validity,'evidence_level':'法定依据待核验' if dtype=='法规' else '参考资料','source_path':rel,'updated':datetime.fromtimestamp(p.stat().st_mtime).isoformat(),'sha256':hashlib.sha256(text.encode()).hexdigest()}

def main():
 rows=[]
 for p in ROOT.rglob('*.md'):
  if p.name.startswith('_'): continue
  text=p.read_text(encoding='utf-8',errors='ignore')
  rows.append(infer(p,text))
 OUT.write_text(json.dumps({'generated_at':datetime.now().isoformat(),'count':len(rows),'schema_version':'1.0','records':rows},ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps({'catalog':str(OUT),'count':len(rows)},ensure_ascii=False))
if __name__=='__main__':main()
