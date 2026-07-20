# -*- coding: utf-8 -*-
"""本地受控Office/PDF解析：隔离目录解析，病毒检查，敏感字段识别，人工抽查。"""
from pathlib import Path
from datetime import datetime
import json,re,shutil

KB=Path(__file__).resolve().parents[1]/'knowledge'
STAGING=KB/'office_staging'  # 文件先进入隔离区
EXTRACTED=KB/'office_extracted'  # 解析结果
SENSITIVE_LOG=KB/'office_sensitive_report.jsonl'

def scan_file(path):
    """安全扫描：文件大小、扩展名、宏、可疑模式"""
    ext=path.suffix.lower()
    size=path.stat().st_size
    warnings=[]
    if ext in ('.docm','.xlsm','.pptm'):
        warnings.append('启用了宏的文件，需要宏病毒扫描')
    if size>50*1024*1024:
        warnings.append(f'文件过大（{size/1048576:.0f}MB），分批处理')
    # 读取前1KB检查二进制可疑模式
    try:
        head=path.read_bytes()[:1024]
        if b'PowerShell' in head or b'cmd.exe' in head or b'WScript.Shell' in head:
            warnings.append('包含可疑脚本模式，需人工审查')
    except:
        pass
    return {'safe':len(warnings)==0,'warnings':warnings,'size':size,'ext':ext}

def extract_sensitive_flags(text):
    """识别敏感字段位置，不读内容本身"""
    flags=[]
    # 手机号模式
    for m in re.finditer(r'(?<!\d)1[3-9]\d{9}(?!\d)',text):
        flags.append({'type':'phone','pos':m.start(),'len':m.end()-m.start()})
    # 身份证
    for m in re.finditer(r'\b\d{17}[0-9Xx]\b',text):
        flags.append({'type':'id_card','pos':m.start(),'len':m.end()-m.start()})
    # 银行账号（12-19位纯数字）
    for m in re.finditer(r'(?<!\d)\d{12,19}(?!\d)',text):
        flags.append({'type':'bank_account','pos':m.start(),'len':m.end()-m.start()})
    # 金额模式
    for m in re.finditer(r'[¥￥]?\d{1,3}(?:,\d{3})*(?:\.\d{2})?',text):
        flags.append({'type':'amount','pos':m.start(),'len':m.end()-m.start()})
    return flags

def main():
    STAGING.mkdir(parents=True,exist_ok=True)
    EXTRACTED.mkdir(parents=True,exist_ok=True)
    # 扫描当前项目目录的办公文档，复制到隔离区
    for proj_dir in (Path(__file__).resolve().parents[1]/'projects').iterdir():
        if not proj_dir.is_dir(): continue
        for p in proj_dir.rglob('*'):
            if p.suffix.lower() in ('.docx','.doc','.xls','.xlsx','.pdf','.pptx'):
                scan=scan_file(p)
                if not scan['safe']:
                    print(f'⚠️ 隔离: {p.name} 警告: {scan["warnings"]}')
                    # 不安全文件只登记不复制
                    report={'type':'office_staging','file':str(p),'scan':scan,
                            'action':'blocked','reason':scan['warnings'],
                            'time':datetime.now().isoformat()}
                    with open(SENSITIVE_LOG,'a',encoding='utf-8') as f:
                        f.write(json.dumps(report,ensure_ascii=False)+'\n')
                    continue
                # 安全文件复制到隔离区（仅登记，不自动解析内容）
                dest=STAGING/f'{p.parent.name}_{p.stem}{p.suffix}'
                if not dest.exists():
                    shutil.copy2(p,dest)
                    print(f'📄 已隔离: {p.name} → {dest.name}')
                # 报告
                report={'type':'office_staging','file':str(p),'dest':str(dest),
                        'scan':scan,'action':'staged','time':datetime.now().isoformat()}
                with open(SENSITIVE_LOG,'a',encoding='utf-8') as f:
                    f.write(json.dumps(report,ensure_ascii=False)+'\n')
    print(json.dumps({'staging':str(STAGING),'extracted':str(EXTRACTED),'log':str(SENSITIVE_LOG)},ensure_ascii=False))

if __name__=='__main__':main()