import os, sys
sys.stdout.reconfigure(encoding='utf-8')
out = r'D:\openclaw-workspace\教科院内控分析'

def extract_section_content(filepath, section_name):
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    capturing = False
    content = []
    for line in lines:
        stripped = line.strip()
        if stripped == f'## {section_name}':
            capturing = True
            content.append(line)
            continue
        if capturing:
            if stripped.startswith('## ') and stripped != f'## {section_name}':
                break
            content.append(line)
    return ''.join(content) if content else None

key_sections = [
    '预算管理制度', '费用报销流程及规定', '政府采购管理制度',
    '一般采购管理制度', '资产管理制度', '合同管理制度',
    '风险评估制度', '内部审计管理制度', '收支管理制度',
    '财务管理制度', '建设项目实施管理办法', '票据管理办法',
    '教育收费管理制度',
]

v1 = os.path.join(out, '内控制度2024.6.14-11.18.md')
v10 = os.path.join(out, '2026.3.13至今.md')

with open(os.path.join(out, 'section_comparison.md'), 'w', encoding='utf-8') as rpt:
    rpt.write('# 核心制度章节对比 (V1 vs V10)\n\n')
    
    for sec in key_sections:
        c1 = extract_section_content(v1, sec)
        c10 = extract_section_content(v10, sec)
        
        rpt.write(f'## {sec}\n\n')
        
        if c1 is None and c10 is None:
            rpt.write('**状态:** 两个版本均不存在\n\n')
        elif c1 is None:
            rpt.write(f'**状态:** V10新增 (V1中不存在)\n\n')
            rpt.write(f'**V10内容:** ({len(c10.splitlines())}行)\n\n')
            # Show first 15 lines
            for line in c10.splitlines()[:20]:
                rpt.write(f'> {line}\n')
            rpt.write('\n---\n\n')
        elif c10 is None:
            rpt.write(f'**状态:** V1中存在但V10中已删除\n\n')
            rpt.write(f'**V1内容:** ({len(c1.splitlines())}行)\n\n')
            for line in c1.splitlines()[:20]:
                rpt.write(f'> {line}\n')
            rpt.write('\n---\n\n')
        else:
            lines1 = len(c1.splitlines())
            lines10 = len(c10.splitlines())
            if lines1 == lines10 and c1 == c10:
                rpt.write(f'**状态:** 未变化 ({lines1}行)\n\n')
            else:
                rpt.write(f'**状态:** 有修改 (V1: {lines1}行, V10: {lines10}行)\n\n')
                # Show first 10 lines of each for comparison
                rpt.write('**V1开头:**\n')
                for line in c1.splitlines()[:8]:
                    rpt.write(f'> {line}\n')
                rpt.write('\n**V10开头:**\n')
                for line in c10.splitlines()[:8]:
                    rpt.write(f'> {line}\n')
            rpt.write('\n---\n\n')
    
    rpt.write('\n## 其他关键差异点\n\n')
    
    # Check for 党组织会议 rules change
    old_name = '党组织会议和党政联席会（行政会）议事规则'
    new_name = '党组织会议和校长办公会（行政会）议事规则'
    
    c_old = extract_section_content(v1, old_name)
    c_new = extract_section_content(v10, new_name)
    
    rpt.write(f'### 议事规则名称变更\n')
    rpt.write(f'- V1: "{old_name}"\n')
    rpt.write(f'- V10: "{new_name}"\n')
    if c_old and c_new:
        rpt.write(f'- 旧版行数: {len(c_old.splitlines())}\n')
        rpt.write(f'- 新版行数: {len(c_new.splitlines())}\n')
    rpt.write('\n---\n\n')
    
    # Check for 党政联席会议提交 vs 校长办公会议提交
    old_submit = '党政联席会议（行政会）提交党组织委员会讨论决定事项清单'
    new_submit = '校长办公会议（行政会）提交党组织委员会讨论决定事项清单'
    
    rpt.write(f'### 提交事项清单变更\n')
    rpt.write(f'- V1: "{old_submit}"\n')
    rpt.write(f'- V10: 已删除（V10不存在）\n')
    rpt.write('\n')

print("Section comparison written.")
