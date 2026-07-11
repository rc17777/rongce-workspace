# -*- coding: utf-8 -*-
"""项目结束后的知识回流：扫描项目产出，生成待审核知识包；默认不自动写入正式知识库。"""
from pathlib import Path
from datetime import datetime
import argparse,json,re,shutil

WS=Path(__file__).resolve().parents[1]
KB=WS/'knowledge'
QUEUE=KB/'feedback_queue'
TEXT_EXT={'.md','.txt','.json','.csv'}
OFFICE_EXT={'.docx','.doc','.xlsx','.xls','.pdf','.pptx'}

def redact(text):
    text=re.sub(r'(?<!\d)1[3-9]\d{9}(?!\d)','[手机号已脱敏]',text)
    text=re.sub(r'\b\d{17}[0-9Xx]\b','[身份证号已脱敏]',text)
    text=re.sub(r'(?<!\d)\d{12,19}(?!\d)','[账号已脱敏]',text)
    return text

def collect(project):
    files=[]
    for p in project.rglob('*'):
        if not p.is_file(): continue
        ext=p.suffix.lower()
        if ext in TEXT_EXT and p.stat().st_size<=2_000_000:
            try: txt=p.read_text(encoding='utf-8',errors='ignore')
            except: continue
            files.append({'path':str(p),'text':redact(txt)[:20000],'needs_extraction':False})
        elif ext in OFFICE_EXT:
            # 办公文档先登记，不在本脚本中自动上传或解析，避免敏感数据外泄。
            files.append({'path':str(p),'text':'','needs_extraction':True,'size':p.stat().st_size})
    return files

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('project_path')
    ap.add_argument('--business-line',default='待分类')
    ap.add_argument('--approve',action='store_true',help='人工审核后才允许进入正式归档')
    args=ap.parse_args()
    project=Path(args.project_path).resolve()
    if not project.exists(): raise SystemExit(f'项目不存在: {project}')
    pid=project.name; ts=datetime.now().strftime('%Y%m%d_%H%M%S')
    out=QUEUE/pid; out.mkdir(parents=True,exist_ok=True)
    files=collect(project)
    package={
      'project_id':pid,'business_line':args.business_line,'created_at':datetime.now().isoformat(),
      'status':'approved' if args.approve else 'pending_human_review',
      'safety':{'auto_redaction':True,'requires_human_review':True,'formal_conclusion_auto_publish':False},
      'sources':[{'path':x['path'],'chars':len(x['text']),'needs_extraction':x.get('needs_extraction',False),'size':x.get('size')} for x in files],
      'candidate_types':['新问题','新规则','新法规案例','误报排除条件','可复用模板']
    }
    (out/f'package_{ts}.json').write_text(json.dumps(package,ensure_ascii=False,indent=2),encoding='utf-8')
    md=['---',f'type: knowledge_feedback',f'project: "{pid}"',f'business_line: "{args.business_line}"',f'status: "{package["status"]}"',f'created: {datetime.now().date()}','---',f'# {pid}｜项目知识回流候选包','',
        '> 默认仅进入待审核队列，不自动进入正式知识库。','', '## 数据安全检查','- [x] 自动遮盖手机号、身份证号、长账号','- [ ] 项目负责人确认无客户敏感信息','- [ ] 复核人确认事实与法规有效性','',
        '## 候选知识','### 新问题','### 新规则','### 新法规/案例','### 误报与排除条件','### 可复用模板','', '## 来源文件']
    md += [f'- `{x["path"]}`（' + ('待受控提取办公文档' if x.get('needs_extraction') else f'{len(x["text"])}字符') + '）' for x in files]
    (out/f'review_{ts}.md').write_text('\n'.join(md),encoding='utf-8')
    print(json.dumps({'status':package['status'],'queue':str(out),'source_files':len(files)},ensure_ascii=False))

if __name__=='__main__': main()
