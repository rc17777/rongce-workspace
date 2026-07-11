# -*- coding: utf-8 -*-
"""项目结束后的知识回流：扫描项目产出，生成待审核知识包；默认不自动写入正式知识库。
双人审批制：必须同时指定--reviewer和--co-reviewer，且不得为同一人，才能将状态改为approved。
"""
from pathlib import Path
from datetime import datetime
import argparse,json,re

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
            files.append({'path':str(p),'text':'','needs_extraction':True,'size':p.stat().st_size})
    return files

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('project_path')
    ap.add_argument('--business-line',default='待分类')
    ap.add_argument('--reviewer',default=None,help='审核人姓名，必填')
    ap.add_argument('--co-reviewer',default=None,help='复核人姓名，必填')
    ap.add_argument('--approve',action='store_true',help='仅配合--reviewer和--co-reviewer使用，单独使用无效')
    args=ap.parse_args()
    project=Path(args.project_path).resolve()
    if not project.exists(): raise SystemExit(f'项目不存在: {project}')

    # 双人审批核心校验
    if args.approve or args.reviewer or args.co_reviewer:
        if not args.reviewer or not args.co_reviewer:
            raise SystemExit('双人审批必须同时指定 --reviewer（审核人）和 --co-reviewer（复核人）')
        if args.reviewer == args.co_reviewer:
            raise SystemExit('审核人与复核人不能为同一人')
        if not args.approve:
            print('提示：已指定审核人和复核人，但未加 --approve，状态仍为 pending_human_review')
            print('确认无误后重新运行加 --approve 即可正式批准')

    pid=project.name; ts=datetime.now().strftime('%Y%m%d_%H%M%S')
    out=QUEUE/pid; out.mkdir(parents=True,exist_ok=True)
    files=collect(project)

    # 审批状态：必须双人同时指定+approve标志才通过
    if args.reviewer and args.co_reviewer and args.approve:
        status='approved'
        approval_record={
            'reviewer':args.reviewer,'co_reviewer':args.co_reviewer,
            'approved_at':datetime.now().isoformat(),
            'method':'双人命令行审批',
            'governance':'生产环境应替换为真实签名/身份认证服务'
        }
    else:
        status='pending_human_review'
        approval_record=None

    package={
        'project_id':pid,'business_line':args.business_line,
        'created_at':datetime.now().isoformat(),
        'status':status,
        'approval':approval_record,
        'safety':{
            'auto_redaction':True,'requires_human_review':True,
            'formal_conclusion_auto_publish':False,
            'governance_rule':'未经双人审批的知识候选包不得进入正式知识库'
        },
        'sources':[{'path':x['path'],'chars':len(x['text']),
                    'needs_extraction':x.get('needs_extraction',False),
                    'size':x.get('size')} for x in files],
        'candidate_types':['新问题','新规则','新法规案例','误报排除条件','可复用模板']
    }
    (out/f'package_{ts}.json').write_text(json.dumps(package,ensure_ascii=False,indent=2),encoding='utf-8')
    md=['---',f'type: knowledge_feedback',f'project: "{pid}"',
        f'business_line: "{args.business_line}"',f'status: "{status}"',
        f'created: {datetime.now().date()}','---',
        f'# {pid}｜项目知识回流候选包','',
        '> 双人审批制：审核人+复核人不得为同一人。默认待审核，不自动入库。','',
        '## 审批状态']
    if approval_record:
        md += [f'- 审核人：{approval_record["reviewer"]}',
               f'- 复核人：{approval_record["co_reviewer"]}',
               f'- 批准时间：{approval_record["approved_at"][:19]}']
    else:
        md += ['- 状态：待双人审批（需指定 --reviewer + --co-reviewer + --approve）']
    md += ['','## 数据安全检查','- [x] 自动遮盖手机号、身份证号、长账号',
           '- [ ] 项目负责人确认无客户敏感信息','- [ ] 复核人确认事实与法规有效性','',
           '## 候选知识','### 新问题','### 新规则','### 新法规/案例','### 误报与排除条件','### 可复用模板','',
           '## 来源文件']
    for x in files:
        desc='待受控提取办公文档' if x.get('needs_extraction') else f'{len(x["text"])}字符'
        md.append(f'- `{x["path"]}`（{desc}）')
    (out/f'review_{ts}.md').write_text('\n'.join(md),encoding='utf-8')
    print(json.dumps({
        'status':status,'queue':str(out),'source_files':len(files),
        'approval_system':'双人审批制','rule':'审核人与复核人不得为同一人'
    },ensure_ascii=False))

if __name__=='__main__': main()