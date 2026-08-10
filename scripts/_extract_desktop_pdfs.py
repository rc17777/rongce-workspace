import fitz, os, sys, re
sys.stdout.reconfigure(encoding='utf-8')

desk = r'C:\Users\scrccpa\Desktop\文件'
out = r'D:\openclaw-workspace\knowledge'

KW_MAP = [
    (['医保', '医疗保险', '医疗保障', '医疗收费', '公立医院', '医改', '医药'], '04-专项资金'),
    (['大数据', '知识图谱', '数据分析', '数字化', '人工智能', 'AI', '信息化', '模型构建', '数据挖掘'], '11-数据化审计'),
    (['工程', '竣工', '建设', '投资审计'], '07-工程审计'),
    (['绩效', '评价'], '08-绩效评价'),
    (['补贴', '保险', '养老'], '09-政府补贴'),
    (['环境', '生态', '碳', '绿色', '能源'], '10-能源资源'),
    (['经责', '经济责任', '领导干部'], '01-经责审计'),
    (['采购', '招标', '投标', '串标'], '05-招投标采购'),
    (['预算', '财政'], '03-预算执行'),
    (['国企', '企业审计', '国有'], '06-国企审计'),
]

def classify(title, text_preview):
    combined = title + ' ' + text_preview[:3000]
    for kws, d in KW_MAP:
        if any(kw in combined for kw in kws):
            return d
    return '90-综合参考'

for f in sorted(os.listdir(desk)):
    if not f.endswith('.pdf'):
        continue
    fp = os.path.join(desk, f)
    title = f.replace('.pdf', '')
    
    print(f'Extracting: {title[:60]}...')
    doc = fitz.open(fp)
    pages = doc.page_count
    
    full_text = ''
    for page in doc:
        full_text += page.get_text() + '\n\n'
    doc.close()
    
    target_dir = classify(title, full_text[:5000])
    
    yaml = f'---\ntitle: "{title}"\nsource: "学术论文"\nbusiness_line: "{target_dir}"\npages: {pages}\n---\n'
    md_content = yaml + f'\n# {title}\n\n' + full_text[:50000]
    
    safe_name = re.sub(r'[\\/:*?"<>|]', '_', title)[:80]
    out_path = os.path.join(out, target_dir, f'{safe_name}.md')
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    
    with open(out_path, 'w', encoding='utf-8') as fw:
        fw.write(md_content)
    
    print(f'  -> {target_dir}/  ({len(full_text)} chars, {pages}p)')

print('\nDone!')
