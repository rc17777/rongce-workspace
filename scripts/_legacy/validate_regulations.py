# -*- coding: utf-8 -*-
"""法规有效性批量核验：扫描knowledge目录，提取法规文件的效力状态；
标记为"待核验"的法规禁止进入正式定性规则，显示核验人、文号、废止信息、失效预警。"""
from pathlib import Path
from datetime import datetime, date
import json,re

KB=Path(__file__).resolve().parents[1]/'knowledge'
OUT=KB/'regulation_verification.json'
LOG=KB/'regulation_verification_log.jsonl'

def extract_regulation(text,path):
    rel=str(path.relative_to(KB))
    result={'path':rel,'title':path.stem,'status':'待核验','verification_date':None,'verifier':None,
            'doc_number':None,'issuer':None,'effective_date':None,'abolished_date':None,
            'replaced_by':None,'notes':None}
    matches=re.search(r'文号[：:]\s*([^\n\r，,。.]+)',text)
    if matches: result['doc_number']=matches.group(1).strip()
    matches=re.search(r'(（[^）]*）|国[^发]*发|财[^〔]*〔|审[^〔]*〔)',text)
    if matches: result['doc_number']=result.get('doc_number') or matches.group(0)
    matches=re.search(r'(发布|签发|印发)[单位机关：:]*\s*([^\n\r，,。.]+)',text)
    if matches: result['issuer']=matches.group(2).strip()
    matches=re.search(r'(\d{4})年(\d{1,2})月(\d{1,2})日.*施行',text)
    if matches: result['effective_date']=f'{matches.group(1)}-{int(matches.group(2)):02d}-{int(matches.group(3)):02d}'
    # 已废止检测
    if re.search(r'(已废止|废止|失效|已被.*取代|已作废|不再执行)',text):
        result['status']='已废止'
        result['notes']='文本中标记为已废止/失效'
    # 文号类自动标记为"待核验"（需人工确认效力）
    if result['doc_number']:
        if result['status']=='待核验':
            result['status']='待核验'
    # 无文号非正式文件标记为参考
    if not result['doc_number'] and not re.search(r'[国财审]|法|条例|规定|办法|通知|指引|意见',text[:200]):
        result['status']='参考文件'
    # 已超过5年未更新的文件标记为过期预警
    mtime=datetime.fromtimestamp(path.stat().st_mtime)
    if (datetime.now()-mtime).days>365*5:
        if result['status'] not in ('已废止','参考文件'):
            result['status']='待核验（>5年未更新）'
            result['notes']=f'最近文件修改时间：{mtime.strftime("%Y-%m-%d")}，建议人工核验时效性'
    return result

def main():
    records=[]
    for p in sorted(KB.rglob('*.md')):
        rel=str(p.relative_to(KB))
        if p.name.startswith('_'): continue
        if 'regulation_verification' in rel: continue
        text=p.read_text(encoding='utf-8',errors='ignore')
        # 只处理法规相关文件（含关键词或位于policies/政策法规目录）
        if any(x in rel for x in ['policy','法规','法','条例','规定','办法','通知','指引','意见']):
            records.append(extract_regulation(text,p))
        elif re.search(r'(文号|颁布|施行|废止|法令|条款|依据)',text[:500]):
            records.append(extract_regulation(text,p))
    summary={
        'generated_at':datetime.now().isoformat(),
        'total_candidates':len(records),
        'status_counts':{s:sum(1 for r in records if r['status']==s) for s in set(r['status'] for r in records)},
        'governance_rule':'标记为"待核验"的法规禁止用于正式问题定性和审计报告。需人工核验后更新状态。',
        'records':records
    }
    OUT.write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    # 写日志
    with open(LOG,'a',encoding='utf-8') as f:
        f.write(json.dumps({'time':datetime.now().isoformat(),'count':len(records),'statuses':summary['status_counts']},ensure_ascii=False)+'\n')
    print(json.dumps({'generated':str(OUT),'count':len(records),'statuses':summary['status_counts']},ensure_ascii=False))

if __name__=='__main__':main()