import openpyxl
from collections import defaultdict
import re

PATH = r'C:\Users\scrccpa\Desktop\融策审计过程记录系统=项目经理版(6).xlsx'
wb = openpyxl.load_workbook(PATH, data_only=True)
ws = wb['2-审计过程']

records = []
for row in ws.iter_rows(min_row=3, values_only=True):
    vals = [str(v).strip() if v is not None else '' for v in row]
    if any(v for v in vals[:9]):  # skip fully empty rows
        records.append(vals)

# Classification tags
def classify_finding(text):
    if not text:
        return []
    tags = []
    t = text.lower()
    # 采购程序
    if any(kw in t for kw in ['比选需求', '比选', '询价', '报价单日期', '报价单未', '报价签署', '比价', '竞争性', '磋商', '询价登记']):
        tags.append('采购程序')
    # 验收问题
    if any(kw in t for kw in ['验收', '未盖章', '未签字', '签字盖章']):
        tags.append('验收手续')
    # 合同履约
    if any(kw in t for kw in ['合同约定', '履约', '实际服务', '未达到合同', '未按合同', '实际仅开展', '服务频次', '完成情况']):
        tags.append('合同履约')
    # 资料归档
    if any(kw in t for kw in ['归档', '资料缺失', '未留存', '未收集', '未见', '暂缺', '附件不齐', '未提供', '无老师资质', '教案', '签到', '花名册']):
        tags.append('资料缺失')
    # 签字审批
    if any(kw in t for kw in ['未签字', '签字不', '审批', '签字手续']):
        tags.append('签字审批')
    # 时间逻辑
    if any(kw in t for kw in ['时间逻辑', '日期没', '落款日期', '周末', '节假日', '时段', '学年']):
        tags.append('时间/逻辑矛盾')
    # 信息错配
    if any(kw in t for kw in ['错配', '矛盾', '不符', '不一致', '不规范', '错误']):
        tags.append('信息错配')
    # 课程真实性
    if any(kw in t for kw in ['真实性存疑', '是否周末', '放假通知']):
        tags.append('课程真实性')
    # 预算
    if '预算' in t:
        tags.append('预算审批')
    if not tags:
        tags.append('其他')
    return tags

out_path = r'D:\openclaw-workspace\output\audit_review_by_project.txt'
with open(out_path, 'w', encoding='utf-8') as f:
    f.write("=" * 70 + "\n")
    f.write("融策审计过程记录 — 复核报告：问题按项目归类\n")
    f.write("=" * 70 + "\n\n")
    
    # Stats
    total = len(records)
    with_findings = [r for r in records if r[6]]
    total_amount = 0  # rough
    f.write(f"【基本统计】\n")
    f.write(f"  有实质内容的记录: {total}条\n")
    f.write(f"  含审计发现的记录: {len(with_findings)}条\n\n")
    
    # Group by project
    proj_findings = defaultdict(list)
    for r in records:
        proj = r[3] if r[3] else '未归类'
        finding = r[6] if r[6] else ''
        content = r[4] if r[4] else ''
        date = r[1] if r[1] else ''
        proc = r[2] if r[2] else ''
        anomaly = r[8] if r[8] else ''
        seq = r[0] if r[0] else ''
        
        if finding:
            proj_findings[proj].append({
                'seq': seq,
                'date': date,
                'proc': proc,
                'finding': finding,
                'anomaly': anomaly,
                'content': content
            })
    
    # Merge similar projects
    def merge_key(proj_name):
        name = proj_name.strip()
        if '科创课程' in name and '建设' in name:
            return '科创课程建设(历年)'
        if '科创课程' in name and '火箭' in name:
            return '科创课程火箭模型(2022)'
        if '科创课程' in name:
            return '科创课程(其他年度)'
        if '科技服务' in name and '2025' in name:
            return '2025年科技服务项目'
        if '科技器材' in name:
            return '科技器材采购'
        if '科学院开放日' in name or '青少年科学院' in name:
            return '科学院开放日及课程展示'
        if '5街' in name:
            return '5街学生科创课程'
        if '创客' in name:
            return '创客作品/绿色能源小车'
        if '设施设备' in name or '硬件' in name:
            return '设施设备采购'
        return name
    
    merged = defaultdict(list)
    for proj, items in proj_findings.items():
        key = merge_key(proj)
        merged[key].extend(items)
    
    # PROBLEM TYPE SUMMARY
    f.write("=" * 70 + "\n")
    f.write("【问题类型总览】\n")
    f.write("=" * 70 + "\n\n")
    
    all_tags = defaultdict(int)
    for items in merged.values():
        for item in items:
            tags = classify_finding(item['finding'])
            for tag in tags:
                all_tags[tag] += 1
    
    for tag, cnt in sorted(all_tags.items(), key=lambda x: -x[1]):
        f.write(f"  ▸ {tag}: {cnt}次\n")
    
    # BY PROJECT
    f.write("\n" + "=" * 70 + "\n")
    f.write("【问题按项目归类详情】\n")
    f.write("=" * 70 + "\n")
    
    project_order = sorted(merged.items(), key=lambda x: -len(x[1]))
    
    for idx, (proj, items) in enumerate(project_order, 1):
        f.write(f"\n{'─' * 60}\n")
        f.write(f"项目{idx}: {proj}  ({len(items)}条发现)\n")
        f.write(f"{'─' * 60}\n")
        
        # Group findings within project by tag
        for i, item in enumerate(items, 1):
            tags = classify_finding(item['finding'])
            tag_str = ' | '.join(tags)
            f.write(f"\n  [{item['seq']}] {item['date']} | {item['proc']}\n")
            f.write(f"  类型: {tag_str}\n")
            f.write(f"  发现: {item['finding']}\n")
    
    # RECORDS WITHOUT FINDINGS but with notable content check
    no_finding = [r for r in records if not r[6] and r[4]]
    f.write(f"\n\n{'=' * 70}\n")
    f.write(f"【无审计发现但有操作内容的记录: {len(no_finding)}条(仅逐条查证,未形成发现)】\n")
    f.write(f"{'=' * 70}\n")

print(f"复核报告已写入 {out_path}")
